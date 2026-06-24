#!/usr/bin/env bash
set -euo pipefail

# Simplified deployment without storage mounts (for testing)
# Data will NOT persist between runs - only for validation

RG="tv-norway"
LOC="norwayeast"
ENV_NAME="tv-lake-env"

IMAGE="${IMAGE:-}"
if [[ -z "${IMAGE}" ]]; then
  echo "ERROR: Set IMAGE to docker.io/blvan/tv-datalake:latest"
  exit 1
fi

JOB_PULL="tv-pull-job"
JOB_SILVER="tv-silver-job"

echo "[+] Resource group: $RG ($LOC)"
az group create -n "$RG" -l "$LOC" >/dev/null

echo "[+] Log Analytics workspace"
LAW_NAME="tv-law-simple"
az monitor log-analytics workspace create -g "$RG" -n "$LAW_NAME" -l "$LOC" >/dev/null
sleep 5
LAW_ID=$(az monitor log-analytics workspace show -g "$RG" -n "$LAW_NAME" --query customerId -o tsv)
LAW_KEY=$(az monitor log-analytics workspace get-shared-keys -g "$RG" -n "$LAW_NAME" --query primarySharedKey -o tsv)

echo "[+] Container Apps environment"
az containerapp env create -g "$RG" -n "$ENV_NAME" -l "$LOC" \
  --logs-workspace-id "$LAW_ID" --logs-workspace-key "$LAW_KEY" >/dev/null

echo "[+] Create pull job (every minute)"
az containerapp job create -g "$RG" -n "$JOB_PULL" --environment "$ENV_NAME" \
  --trigger-type Schedule --replica-timeout 300 --replica-retry-limit 0 \
  --cron-expression "*/1 * * * *" \
  --image "$IMAGE" \
  --cpu "0.25" --memory "0.5Gi" \
  --env-vars "WAREHOUSE_PATH=/tmp/warehouse.duckdb" "TZ=Europe/Bratislava" \
  --command "/usr/local/bin/python" \
  --args "-m" "scripts.now_playing_pull" >/dev/null

echo "[+] Create silver job (every 2 minutes)"
az containerapp job create -g "$RG" -n "$JOB_SILVER" --environment "$ENV_NAME" \
  --trigger-type Schedule --replica-timeout 300 --replica-retry-limit 0 \
  --cron-expression "*/2 * * * *" \
  --image "$IMAGE" \
  --cpu "0.25" --memory "0.5Gi" \
  --env-vars "WAREHOUSE_PATH=/tmp/warehouse.duckdb" "TZ=Europe/Bratislava" \
  --command "bash" \
  --args "-c" "python3 -m scripts.now_playing_bronze_to_silver && python3 -m scripts.build_duckdb" \
  >/dev/null

echo "[+] Run pull job once to test"
az containerapp job start -g "$RG" -n "$JOB_PULL" --no-wait

cat <<EOF

Done (simplified deployment without persistent storage).
Resources in resource group: $RG
- Jobs: $JOB_PULL (*/1 * * * *), $JOB_SILVER (*/2 * * * *)

NOTE: Data will NOT persist between runs (uses /tmp).

To view job runs:
  az containerapp job execution list -g $RG -n $JOB_PULL -o table
  az containerapp job execution list -g $RG -n $JOB_SILVER -o table

To see logs (wait ~30s for first run):
  az containerapp job execution logs show -g $RG -n $JOB_PULL --name <execution-name>

To clean up:
  az group delete -n $RG --yes --no-wait
EOF
