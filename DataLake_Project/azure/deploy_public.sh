#!/usr/bin/env bash
set -euo pipefail

# This variant deploys without Azure Container Registry.
# It assumes your container image is already available in a PUBLIC registry
# (e.g., docker.io/<user>/tv-datalake:latest or ghcr.io/<user>/tv-datalake:latest).

# === Config (edit as needed) ===
RG="tv-datalake-fc"
LOC="francecentral"   # Students subscription allows: francecentral, spaincentral, switzerlandnorth, italynorth, norwayeast
SA_NAME="tvdatalakest$RANDOM"
ENV_NAME="tv-datalake-env"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Required: image reference in a public registry
# Example: IMAGE="docker.io/<dockerhub-user>/tv-datalake:latest"
IMAGE="${IMAGE:-}"
if [[ -z "${IMAGE}" ]]; then
  echo "ERROR: Please set IMAGE to a public image reference, e.g.:"
  echo "  export IMAGE=\"docker.io/<user>/tv-datalake:latest\""
  exit 1
fi

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

echo "[+] Resource group: $RG ($LOC)"
az group create -n "$RG" -l "$LOC" >/dev/null

echo "[+] Storage Account: $SA_NAME (Azure Files)"
az storage account create -g "$RG" -n "$SA_NAME" -l "$LOC" --sku Standard_LRS
echo "[+] Waiting for storage account to be ready..."
az storage account show -g "$RG" -n "$SA_NAME" --query provisioningState -o tsv >/dev/null
SA_KEY=$(az storage account keys list -g "$RG" -n "$SA_NAME" --query [0].value -o tsv)

az storage share-rm create --resource-group "$RG" --storage-account "$SA_NAME" --name "$SHARE_DATA" >/dev/null || true
az storage share-rm create --resource-group "$RG" --storage-account "$SA_NAME" --name "$SHARE_LOGS" >/dev/null || true

echo "[+] Initialize file shares"
AZURE_STORAGE_ACCOUNT="$SA_NAME" AZURE_STORAGE_KEY="$SA_KEY" \
az storage directory create -s "$SHARE_DATA" -n "bronze" >/dev/null || true
AZURE_STORAGE_ACCOUNT="$SA_NAME" AZURE_STORAGE_KEY="$SA_KEY" \
az storage directory create -s "$SHARE_DATA" -n "silver" >/dev/null || true

echo "[+] Log Analytics workspace"
LAW_NAME="tv-datalake-law$RANDOM"
az monitor log-analytics workspace create -g "$RG" -n "$LAW_NAME" -l "$LOC"
echo "[+] Waiting for Log Analytics workspace..."
sleep 10
LAW_ID=$(az monitor log-analytics workspace show -g "$RG" -n "$LAW_NAME" --query customerId -o tsv)
LAW_KEY=$(az monitor log-analytics workspace get-shared-keys -g "$RG" -n "$LAW_NAME" --query primarySharedKey -o tsv)

echo "[+] Container Apps environment"
az containerapp env create -g "$RG" -n "$ENV_NAME" -l "$LOC" \
  --logs-workspace-id "$LAW_ID" --logs-workspace-key "$LAW_KEY" >/dev/null

az containerapp env storage set -g "$RG" --name "$ENV_NAME" \
  --storage-name datafs \
  --azure-file-account-name "$SA_NAME" --azure-file-account-key "$SA_KEY" \
  --azure-file-share-name "$SHARE_DATA" --access-mode ReadWrite >/dev/null

az containerapp env storage set -g "$RG" --name "$ENV_NAME" \
  --storage-name logsfs \
  --azure-file-account-name "$SA_NAME" --azure-file-account-key "$SA_KEY" \
  --azure-file-share-name "$SHARE_LOGS" --access-mode ReadWrite >/dev/null

echo "[+] Create pull job (every minute)"
az containerapp job create -g "$RG" -n "$JOB_PULL" --environment "$ENV_NAME" \
  --trigger-type Schedule --replica-timeout 600 --replica-retry-limit 1 \
  --cron-expression "*/1 * * * *" \
  --image "$IMAGE" \
  --command "/usr/local/bin/python" \
  --args "-m" "scripts.now_playing_pull" \
  --cpu "0.25" --memory "0.5Gi" \
  --env-vars WAREHOUSE_PATH="$WAREHOUSE_PATH" TZ="Europe/Bratislava"

echo "[+] Attach storage to pull job"
az containerapp job update -g "$RG" -n "$JOB_PULL" \
  --set-env-vars WAREHOUSE_PATH="$WAREHOUSE_PATH" TZ="Europe/Bratislava"

# Storage mount via YAML patch (Container Apps CLI limitation workaround)
echo "[+] Create silver job (every 2 minutes)"
az containerapp job create -g "$RG" -n "$JOB_SILVER" --environment "$ENV_NAME" \
  --trigger-type Schedule --replica-timeout 600 --replica-retry-limit 1 \
  --cron-expression "*/2 * * * *" \
  --image "$IMAGE" \
  --command "bash" \
  --args "-c" "python3 -m scripts.now_playing_bronze_to_silver && python3 -m scripts.build_duckdb" \
  --cpu "0.25" --memory "0.5Gi" \
  --env-vars WAREHOUSE_PATH="$WAREHOUSE_PATH" TZ="Europe/Bratislava"

echo "[+] Run jobs once to warm up"
az containerapp job start -g "$RG" -n "$JOB_PULL" >/dev/null || true
az containerapp job start -g "$RG" -n "$JOB_SILVER" >/dev/null || true

cat <<EOF

Done (public image).
Resources in resource group: $RG
- Storage: $SA_NAME (shares: $SHARE_DATA, $SHARE_LOGS)
- Container Apps env: $ENV_NAME
- Jobs: $JOB_PULL (*/1 * * * *), $JOB_SILVER (*/2 * * * *)

Using public image: $IMAGE

To view job runs:
  az containerapp job execution list -g $RG -n $JOB_PULL -o table
  az containerapp job execution list -g $RG -n $JOB_SILVER -o table

To clean up:
  az group delete -n $RG --yes --no-wait
EOF
