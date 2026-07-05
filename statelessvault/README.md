# StatelessVault (Azure Functions Python v2)

## Overview
StatelessVault is a stateless encryption/decryption API built with Azure Functions Python v2 using the decorator-based `function_app.py` model.

Endpoints:
- `POST /api/encrypt`
- `POST /api/decrypt`

> **Note on `functions.json`:** In the Azure Functions **Python v2** programming model,
> endpoints are declared with the `@app.route(...)` decorators in `function_app.py`.
> You do **not** author a `functions.json` per function — the host generates the function
> metadata automatically by indexing the worker at startup. The valid endpoints above are
> defined by the `encrypt` and `decrypt` routes in `function_app.py`.
>
> If the Function App shows the default welcome page but `/api/encrypt` returns `404`, the
> worker failed to index the v2 functions. Set the app setting
> `AzureWebJobsFeatureFlags=EnableWorkerIndexing` (see
> [Azure deployment](#azure-deployment-linux-python-functions)) and restart the app.

Crypto stack:
- Key derivation: Argon2id
- Encryption: AES-256-GCM

The caller provides the secret each time. The service does not persist plaintext, ciphertext, secrets, sessions, keys, or user payloads.

## Threat model
StatelessVault is intended for application-level confidentiality where clients need portable, stateless encryption.

### What this protects
- Confidentiality and integrity of plaintext when ciphertext package is exposed.
- Tamper detection using AES-GCM authentication.
- Brute-force resistance improvement via Argon2id key derivation.

### What this does not protect
- Weak or reused user secrets.
- Endpoint abuse without upstream controls.
- Compromised client environments.
- Data loss if the user forgets their secret.

## Design notes
- **Stateless API:** no server-side storage of secrets or encrypted material.
- **User must remember secret:** decryption depends entirely on caller-supplied secret.
- **Salt is public:** salt uniqueness prevents precomputed attacks and is required for deterministic key derivation.
- **Nonce is public:** AES-GCM nonce is not secret; uniqueness per key is required.
- **AES-GCM:** provides authenticated encryption (confidentiality + integrity).
- **Argon2id:** memory-hard KDF suitable for password-derived keys.

## Rate limiting
A simple in-memory fixed-window limiter is implemented inside the function instance:
- `10,000` requests per `60` seconds (instance total, not per IP).

If exceeded, the API returns HTTP `429`:

```json
{
  "error": "rate_limited",
  "message": "Global request limit exceeded. Try again later."
}
```

### Important serverless limitation
In-memory rate limiting is **not globally accurate** across scaled-out Azure Functions instances. For real spend protection and global throttling, place **Azure API Management** in front of the Function App and enforce a global policy there.

## API examples

### Encrypt
```bash
curl -X POST http://localhost:7071/api/encrypt \
  -H "Content-Type: application/json" \
  -d '{
    "plaintext": "Attack at dawn.",
    "secret": "correct horse battery staple"
  }'
```

### Decrypt
```bash
curl -X POST http://localhost:7071/api/decrypt \
  -H "Content-Type: application/json" \
  -d '{
    "version": 1,
    "algorithm": "Argon2id/AES-256-GCM",
    "salt": "<base64>",
    "nonce": "<base64>",
    "ciphertext": "<base64>",
    "tag": "<base64>",
    "secret": "correct horse battery staple"
  }'
```

## Local setup
1. Install Python 3.10+ and Azure Functions Core Tools.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy local settings:
   ```bash
   cp local.settings.json.example local.settings.json
   ```
5. Run locally:
   ```bash
   func start
   ```

Local URLs:
- `http://localhost:7071/api/encrypt`
- `http://localhost:7071/api/decrypt`

## Azure deployment (Linux Python Functions)
Azure Functions Python v2 uses decorator-based `function_app.py`.

1. Login:
   ```bash
   az login
   ```
2. Create resource group:
   ```bash
   az group create --name rg-statelessvault --location eastus
   ```
3. Create storage account:
   ```bash
   az storage account create \
     --name statelessvaultstorage123 \
     --location eastus \
     --resource-group rg-statelessvault \
     --sku Standard_LRS
   ```
4. Create Linux consumption Function App:
   ```bash
   az functionapp create \
     --resource-group rg-statelessvault \
     --consumption-plan-location eastus \
     --runtime python \
     --runtime-version 3.11 \
     --functions-version 4 \
     --name statelessvault-func-app \
     --storage-account statelessvaultstorage123 \
     --os-type Linux
   ```
5. Enable Python v2 worker indexing (required so `/api/encrypt` and `/api/decrypt`
   are registered — without it the app serves only the default welcome page and the
   routes return `404`):
   ```bash
   az functionapp config appsettings set \
     --name statelessvault-func-app \
     --resource-group rg-statelessvault \
     --settings AzureWebJobsFeatureFlags=EnableWorkerIndexing
   ```
6. Publish with Azure Functions Core Tools:
   ```bash
   func azure functionapp publish statelessvault-func-app
   ```
7. Test public endpoints:
   ```bash
   curl -X POST https://statelessvault-func-app.azurewebsites.net/api/encrypt \
     -H "Content-Type: application/json" \
     -d '{"plaintext":"hello","secret":"my secret"}'
   ```

## CI/CD (GitHub Actions)
A deployment pipeline is defined in `.github/workflows/deploy-azure-functions.yml`.

Behavior:
- On pull requests targeting `main`: installs dependencies and runs the test suite.
- On pushes to `main` (and manual `workflow_dispatch`): runs tests, then deploys to Azure Functions.

### Required configuration
1. Add a repository secret named `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` containing the Function App publish profile.
   - Download it from the Azure Portal (Function App → *Get publish profile*) or via CLI:
     ```bash
     az functionapp deployment list-publishing-profiles \
       --name statelessvault-func-app \
       --resource-group rg-statelessvault \
       --xml
     ```
2. If your Function App name differs, update `AZURE_FUNCTIONAPP_NAME` in the workflow `env` block.

## Security notes
- Never log plaintext, secrets, ciphertext, or derived keys.
- Random salt/nonce generation uses secure randomness (`os.urandom`).
- Authenticated encryption is implemented via `cryptography` AES-GCM.
- No custom crypto primitives are implemented.
