# StatelessVault

I built StatelessVault because I wanted a place to hide my secrets that isn't a place at all. It is an encryption and decryption API that runs on **Azure Functions (Python v2)** and then forgets everything the instant it is done. No plaintext, no ciphertext, no secrets, no sessions, no keys. Nothing is kept. The server is a canyon wind. It carries your words across and leaves no tracks in the sand.

Most services want to remember you. They collect and store and index until the database is a landfill of other people's lives. I went the other way. The most private data is the data nobody wrote down. Every operation here is ephemeral, and that is the whole point.

## The crypto stack

| Layer | Algorithm |
|---|---|
| Key derivation | Argon2id |
| Encryption | AES-256-GCM |

I did not invent any of this. Rolling your own crypto is like drinking from a stagnant pool because you are too proud to walk to the river. Argon2id is memory hard, so it makes brute force expensive. AES-256-GCM keeps your secret confidential and also tells you if someone tampered with it. Old tools, sharp edges, no cleverness of mine to dull them.

## Endpoints

| Method | Route | Description |
|---|---|---|
| `POST` | `/api/encrypt` | Encrypt plaintext with a secret you supply |
| `POST` | `/api/decrypt` | Decrypt a package with the same secret you started with |

## Quick start

Read [`statelessvault/README.md`](statelessvault/README.md) for local setup, usage, the design notes, and what this thing does and does not protect you from.

## Deployment

Read [`.github/DEPLOYMENT.md`](.github/DEPLOYMENT.md) for how to put it on Azure and wire up the pipeline.

## Project layout

```
statelessvault/          # Azure Functions app (Python v2)
  app/                   # Crypto, models, rate limiter, error helpers
  tests/                 # Pytest suite
  function_app.py        # The two routes: encrypt and decrypt
  requirements.txt       # Python dependencies
.github/
  workflows/             # GitHub Actions pipeline
  DEPLOYMENT.md          # Azure deployment guide
```
