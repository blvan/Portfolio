#!/usr/bin/env bash
set -euo pipefail

# === Config (edit as needed) ===
RG="tv-datalake-rg-neu"
LOC="northeurope"
ACR_NAME="tvdatalakeacr$RANDOM"
SA_NAME="tvdatalakest$RANDOM"
ENV_NAME="tv-datalake-env"
IMG_NAME="tv-datalake:latest"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Azure Container Apps Jobs names
JOB_PULL="tv-pull-job"
JOB_SILVER="tv-silver-job"

# File shares
SHARE_DATA="datalake"
SHARE_LOGS="logs"

# Paths in container (must match app expectations)
MNT_DATA="/app/data_lake"
MNT_LOGS="/app/logs"
WAREHOUSE_PATH="$MNT_DATA/warehouse.duckdb"

# === Prereqs ===
# az extension add --name containerapp --upgrade
# az provider register --namespace Microsoft.App
# az feature register --namespace Microsoft.App --name EnableWorkloadProfilesPreview

echo "[+] Resource group: $RG ($LOC)"
az group create -n "$RG" -l "$LOC" >/dev/null

echo "[+] Container Registry: $ACR_NAME"
az acr create -g "$RG" -n "$ACR_NAME" --sku Basic >/dev/null
ACR_LOGIN_SERVER=$(az acr show -g "$RG" -n "$ACR_NAME" --query loginServer -o tsv)
az acr update -g "$RG" -n "$ACR_NAME" --admin-enabled true >/dev/null
ACR_USER=$(az acr credential show -n "$ACR_NAME" --query username -o tsv)
ACR_PASS=$(az acr credential show -n "$ACR_NAME" --query passwords[0].value -o tsv)

echo "[+] Build & push image via ACR build"
# Requires Dockerfile in repo root
az acr build -r "$ACR_NAME" -t "$IMG_NAME" "$REPO_ROOT" >/dev/null

echo "[+] Storage Account: $SA_NAME (Azure Files)"
az storage account create -g "$RG" -n "$SA_NAME" -l "$LOC" --sku Standard_LRS >/dev/null
SA_KEY=$(az storage account keys list -g "$RG" -n "$SA_NAME" --query [0].value -o tsv)

az storage share-rm create --resource-group "$RG" --storage-account "$SA_NAME" --name "$SHARE_DATA" >/dev/null
az storage share-rm create --resource-group "$RG" --storage-account "$SA_NAME" --name "$SHARE_LOGS" >/dev/null

# Pre-create folders (optional):
echo "[+] Initialize file shares"
AZURE_STORAGE_ACCOUNT="$SA_NAME" AZURE_STORAGE_KEY="$SA_KEY" \
az storage directory create -s "$SHARE_DATA" -n "bronze" >/dev/null || true
AZURE_STORAGE_ACCOUNT="$SA_NAME" AZURE_STORAGE_KEY="$SA_KEY" \
az storage directory create -s "$SHARE_DATA" -n "silver" >/dev/null || true

echo "[+] Log Analytics workspace"
LAW_NAME="tv-datalake-law$RANDOM"
az monitor log-analytics workspace create -g "$RG" -n "$LAW_NAME" -l "$LOC" >/dev/null
LAW_ID=$(az monitor log-analytics workspace show -g "$RG" -n "$LAW_NAME" --query customerId -o tsv)
LAW_KEY=$(az monitor log-analytics workspace get-shared-keys -g "$RG" -n "$LAW_NAME" --query primarySharedKey -o tsv)

echo "[+] Container Apps environment"
az containerapp env create -g "$RG" -n "$ENV_NAME" -l "$LOC" \
  --logs-workspace-id "$LAW_ID" --logs-workspace-key "$LAW_KEY" >/dev/null

# Attach Azure Files storages to the environment
az containerapp env storage set -g "$RG" --name "$ENV_NAME" \
  --storage-name datafs \
  --azure-file-account-name "$SA_NAME" --azure-file-account-key "$SA_KEY" \
  --azure-file-share-name "$SHARE_DATA" --access-mode ReadWrite >/dev/null

az containerapp env storage set -g "$RG" --name "$ENV_NAME" \
  --storage-name logsfs \
  --azure-file-account-name "$SA_NAME" --azure-file-account-key "$SA_KEY" \
  --azure-file-share-name "$SHARE_LOGS" --access-mode ReadWrite >/dev/null

# Common registry args
REGISTRY_ARGS=(--registry-server "$ACR_LOGIN_SERVER" --registry-username "$ACR_USER" --registry-password "$ACR_PASS")

# === Create Jobs ===
# 1) Pull job: every 1 minute
echo "[+] Create pull job (every minute)"
az containerapp job create -g "$RG" -n "$JOB_PULL" --environment "$ENV_NAME" \
  --trigger-type Schedule --replica-timeout 600 --replica-retry-limit 1 \
  --cron-expression "*/1 * * * *" \
  --image "$ACR_LOGIN_SERVER/$IMG_NAME" \
  --command "/usr/local/bin/python" "-m" "scripts.now_playing_pull" \
  --cpu "0.25" --memory "0.5Gi" \
  --set-env-vars WAREHOUSE_PATH="$WAREHOUSE_PATH" TZ="Europe/Bratislava" \
  --secrets SA_KEY="$SA_KEY" ACR_PASS="$ACR_PASS" \
  --storage-mounts name=datafs,storage-name=datafs,path="$MNT_DATA" name=logsfs,storage-name=logsfs,path="$MNT_LOGS" \
  "${REGISTRY_ARGS[@]}" >/dev/null

# 2) Silver job: every 2 minutes
echo "[+] Create silver job (every 2 minutes)"
az containerapp job create -g "$RG" -n "$JOB_SILVER" --environment "$ENV_NAME" \
  --trigger-type Schedule --replica-timeout 600 --replica-retry-limit 1 \
  --cron-expression "*/2 * * * *" \
  --image "$ACR_LOGIN_SERVER/$IMG_NAME" \
  --command "bash" "-lc" \
  "/usr/local/bin/python -m scripts.now_playing_bronze_to_silver && /usr/local/bin/python -m scripts.build_duckdb" \
  --cpu "0.25" --memory "0.5Gi" \
  --set-env-vars WAREHOUSE_PATH="$WAREHOUSE_PATH" TZ="Europe/Bratislava" \
  --secrets SA_KEY="$SA_KEY" ACR_PASS="$ACR_PASS" \
  --storage-mounts name=datafs,storage-name=datafs,path="$MNT_DATA" name=logsfs,storage-name=logsfs,path="$MNT_LOGS" \
  "${REGISTRY_ARGS[@]}" >/dev/null

# === Kick off jobs once (optional warmup) ===
echo "[+] Run jobs once to warm up"
az containerapp job start -g "$RG" -n "$JOB_PULL" >/dev/null || true
az containerapp job start -g "$RG" -n "$JOB_SILVER" >/dev/null || true

cat <<EOF

Done.
Resources in resource group: $RG
- ACR: $ACR_NAME ($ACR_LOGIN_SERVER)
- Storage: $SA_NAME (shares: $SHARE_DATA, $SHARE_LOGS)
- Container Apps env: $ENV_NAME
- Jobs: $JOB_PULL (*/1 * * * *), $JOB_SILVER (*/2 * * * *)

Warehouse path used: $WAREHOUSE_PATH
Mounts:
- $MNT_DATA -> Azure Files share '$SHARE_DATA'
- $MNT_LOGS -> Azure Files share '$SHARE_LOGS'

To view job runs:
  az containerapp job execution list -g $RG -n $JOB_PULL -o table
  az containerapp job execution list -g $RG -n $JOB_SILVER -o table

To show logs (last run):
  az containerapp job execution show -g $RG -n $JOB_PULL --latest-execution --query properties.template.containers[0].events

To clean up:
  az group delete -n $RG --yes --no-wait
EOF
