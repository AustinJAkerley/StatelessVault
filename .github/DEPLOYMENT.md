# Deployment Guide

This is how I get StatelessVault onto Azure Functions and how I wire up the pipeline that keeps it there. It is not complicated. Most deployment guides are long because the tools are afraid of you. Mine is short because I trust you to read.

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Azure Functions Core Tools v4](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)
- Python 3.10 or newer

## Azure deployment (Linux Python Functions)

Swap the placeholders below for names of your own choosing. Pick names you can live with, because you will be typing them a while.

| Placeholder | Description |
|---|---|
| `<resource-group>` | Azure resource group name |
| `<storage-account>` | Storage account name, 3 to 24 lowercase alphanumeric characters |
| `<function-app-name>` | Function App name, globally unique |
| `<location>` | Azure region, for example `eastus` |

### 1. Login

```bash
az login
```

### 2. Create the resource group

```bash
az group create --name <resource-group> --location <location>
```

### 3. Create the storage account

```bash
az storage account create \
  --name <storage-account> \
  --location <location> \
  --resource-group <resource-group> \
  --sku Standard_LRS
```

### 4. Create the Linux consumption Function App

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

### 5. Turn on Python v2 worker indexing

The decorator-based `function_app.py` model needs this to register its routes. Skip it and the app comes up empty, a trailhead with no trail:

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

Poke it and make sure it answers:

```bash
curl -X POST https://<function-app-name>.azurewebsites.net/api/encrypt \
  -H "Content-Type: application/json" \
  -d '{"plaintext":"hello","secret":"my secret"}'
```

## CI/CD (GitHub Actions)

The pipeline lives in `.github/workflows/main_statelessvault.yml`. It does the tedious parts so I do not have to remember them.

**Triggers:**

- Push to `main` builds, tests, and deploys to Azure.
- `workflow_dispatch` lets me run it by hand when I want to.

### Required GitHub secrets

| Secret | How to obtain |
|---|---|
| `AZURE_CLIENT_ID` | From your Azure AD app registration (OIDC) |
| `AZURE_TENANT_ID` | Your Azure tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Your Azure subscription ID |

The workflow signs in with [Azure OIDC login](https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure), so there are no long-lived credentials sitting around as secrets. A credential you never store is a credential nobody can steal. Same idea as the vault itself.

To set up OIDC:

1. Create an App Registration in Azure AD.
2. Add a federated credential for `repo:<org>/<repo>:ref:refs/heads/main`.
3. Grant the app **Contributor** access to the Function App's resource group.
4. Add the three secrets above to your GitHub repository settings.

If you ever rename the Function App, change `app-name` in the deploy step of the workflow file, or the pipeline will keep shouting into an empty canyon.
