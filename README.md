# StatelessVault

A stateless encryption/decryption API built on **Azure Functions (Python v2)**. The server never stores plaintext, ciphertext, secrets, sessions, or keys — every operation is fully ephemeral.

## Crypto stack
| Layer | Algorithm |
|---|---|
| Key derivation | Argon2id |
| Encryption | AES-256-GCM |

## Endpoints
| Method | Route | Description |
|---|---|---|
| `POST` | `/api/encrypt` | Encrypt plaintext with a caller-supplied secret |
| `POST` | `/api/decrypt` | Decrypt a ciphertext package with the original secret |

## Quick start
See [`statelessvault/README.md`](statelessvault/README.md) for local development setup, API usage examples, design notes, and security information.

## Deployment
See [`.github/DEPLOYMENT.md`](.github/DEPLOYMENT.md) for Azure deployment instructions and CI/CD configuration.

## Project layout
```
statelessvault/          # Azure Functions app (Python v2)
  app/                   # Crypto, models, rate limiter, error helpers
  tests/                 # Pytest test suite
  function_app.py        # Route definitions (encrypt / decrypt)
  requirements.txt       # Python dependencies
.github/
  workflows/             # GitHub Actions CI/CD pipeline
  DEPLOYMENT.md          # Azure deployment guide
```
