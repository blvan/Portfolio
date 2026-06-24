# Azure deployment guide

This project is ready to run on Microsoft Azure using Container Apps Jobs with Azure Files for persistent storage.

## Prerequisites

- Azure CLI installed and logged in
- Subscription selected (replace with yours if needed)
- Bash shell

Optional but recommended:
- `az extension add --name containerapp --upgrade`
- `az provider register --namespace Microsoft.App`

## One-command deploy

```bash
# from repo root
bash azure/deploy.sh
```

What the script does:
- Creates a Resource Group, Azure Container Registry (ACR), Storage Account (Azure Files), and Log Analytics workspace
- Builds and pushes the Docker image via ACR Build
- Creates a Container Apps Environment
- Creates two scheduled Container Apps Jobs:
  - tv-pull-job: runs every minute to fetch sources and write bronze
  - tv-silver-job: runs every 2 minutes to build silver and (re)build DuckDB views
- Mounts Azure Files shares into the container at:
  - /app/data_lake (persisted lake; WAREHOUSE_PATH points to /app/data_lake/warehouse.duckdb)
  - /app/logs (logs)

After completion, the jobs will keep running on schedule without manual intervention.

## Adjust schedules

Edit `azure/deploy.sh` and change the `--cron-expression` values:
- Pull job: `*/1 * * * *` (every minute)
- Silver job: `*/2 * * * *` (every 2 minutes)

Re-run the relevant `az containerapp job update` command (or just re-run the script to recreate).

## Monitor runs and logs

```bash
# List executions
az containerapp job execution list -g tv-datalake-rg -n tv-pull-job -o table
az containerapp job execution list -g tv-datalake-rg -n tv-silver-job -o table

# Show details of the latest run (includes container events)
az containerapp job execution show -g tv-datalake-rg -n tv-pull-job --latest-execution \
  --query properties.template.containers[0].events
```

## Where data lives

- Azure Files share `datalake` is mounted at `/app/data_lake`:
  - bronze: `/app/data_lake/bronze/now_playing/...`
  - silver: `/app/data_lake/silver/now_playing/load_date=YYYY-MM-DD/part.parquet`
  - DuckDB: `WAREHOUSE_PATH=/app/data_lake/warehouse.duckdb`
- Logs share `logs` is mounted at `/app/logs`

## Clean up

```bash
# Delete all resources created by the script
az group delete -n tv-datalake-rg --yes --no-wait
```

## Notes

- The Dockerfile is optimized for both local cron-based runs and Azure jobs. In Azure we override the container command per job.
- Timezone is set to Europe/Bratislava inside the jobs; all timestamps are normalized to UTC without microseconds.
- You can change names/locations by editing variables at the top of `azure/deploy.sh`.

## Troubleshooting: Azure for Students and Storage Account

If Storage Account creation fails on an Azure for Students subscription, try these steps:

1) Check subscription status and credits

```bash
az account show --query "{name:name, state:state}"
```

Ensure the subscription state is Enabled and you still have credits. If disabled, reactivate from the Azure portal.

2) Register required resource providers

```bash
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
```

Optionally verify:

```bash
az provider show -n Microsoft.Storage --query registrationState -o tsv
```

3) Try a different region

Some student tenants restrict certain regions. Edit `LOC` at the top of `azure/deploy.sh` to `eastus` or `northeurope` and rerun:

```bash
# in azure/deploy.sh
LOC="eastus"   # or "northeurope"
```

4) Verify Storage Account name rules

Names must be globally unique, 3–24 chars, lowercase letters and numbers only. The script randomizes names, but if you modify them, follow the rules.

5) Policy restrictions

Some education tenants enforce policies that deny certain SKUs/locations. In the portal, check Policy assignments under your subscription. If you see Deny policies for Storage, either switch to an allowed region/SKU (`Standard_LRS`) or contact your admin.

6) Fallback options if Azure Files is blocked

- Run without persistent storage (data won’t survive between runs):
  - Temporarily remove storage mounts in the job creation part of `deploy.sh` and set `WAREHOUSE_PATH=/tmp/warehouse.duckdb`.
  - This is only suitable for basic testing.
- Use a different Azure subscription (e.g., Pay-As-You-Go) where Azure Files is allowed.

7) Manual creation (portal)

Try creating a Storage Account manually in the Azure Portal with:
- Region: the same you set in `LOC`
- Performance: Standard
- Redundancy: LRS

Then create two File shares (`datalake`, `logs`) and rerun only the job creation part of the script with your existing account name and key.

If you still hit errors, please share the exact error message (code and text) so we can suggest a targeted fix.
