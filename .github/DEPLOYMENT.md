# Deployment Guide

This document covers deploying StatelessVault to Azure Functions and configuring the CI/CD pipeline.

## Prerequisites
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Azure Functions Core Tools v4](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)
- Python 3.10+

## Azure deployment (Linux Python Functions)

Replace the placeholder values below with your own names:

| Placeholder | Description |
|---|---|
| `<resource-group>` | Azure resource group name |
| `<storage-account>` | Storage account name (3–24 lowercase alphanumeric chars) |
| `<function-app-name>` | Function App name (globally unique) |
| `<location>` | Azure region (e.g. `eastus`) |

### 1. Login
```bash
az login
```

### 2. Create resource group
```bash
az group create --name <resource-group> --location <location>
```

### 3. Create storage account
```bash
az storage account create \
  --name <storage-account> \
  --location <location> \
  --resource-group <resource-group> \
  --sku Standard_LRS
```

### 4. Create Linux consumption Function App
```bash
az functionapp create \
  --resource-group <resource-group> \
  --consumption-plan-location <location> \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name <function-app-name> \
  --storage-account <storage-account> \
  --os-type Linux
```

### 5. Enable Python v2 worker indexing
Required for the decorator-based `function_app.py` model to register routes correctly:
```bash
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --settings AzureWebJobsFeatureFlags=EnableWorkerIndexing
```

### 6. Publish
```bash
cd statelessvault
func azure functionapp publish <function-app-name>
```

### 7. Verify
```bash
curl -X POST https://<function-app-name>.azurewebsites.net/api/encrypt \
  -H "Content-Type: application/json" \
  -d '{"plaintext":"hello","secret":"my secret"}'
```

---

## CI/CD (GitHub Actions)

The pipeline is defined in `.github/workflows/main_statelessvault.yml`.

**Triggers:**
- Push to `main` → build, test, and deploy to Azure
- `workflow_dispatch` → manual trigger

### Required GitHub secrets

| Secret | How to obtain |
|---|---|
| `AZURE_CLIENT_ID` | From your Azure AD app registration (OIDC) |
| `AZURE_TENANT_ID` | Your Azure tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Your Azure subscription ID |

The workflow uses [Azure OIDC login](https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure) — no long-lived credentials are stored as secrets.

To set up OIDC:
1. Create an App Registration in Azure AD.
2. Add a federated credential for `repo:<org>/<repo>:ref:refs/heads/main`.
3. Grant the app **Contributor** access to the Function App's resource group.
4. Add the three secrets above to your GitHub repository settings.

If you need to update the Function App name, change `app-name` in the deploy step of the workflow file.
