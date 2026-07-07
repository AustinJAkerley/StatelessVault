# StatelessVault (Azure Functions Python v2)

## Overview

StatelessVault is a stateless encryption and decryption API. It runs on Azure Functions Python v2, does its work, and then walks off into the desert without leaving a footprint.

There are two ways in:

- `POST /api/encrypt`
- `POST /api/decrypt`

The crypto underneath:

- Key derivation: Argon2id
- Encryption: AES-256-GCM

Here is the deal I made with myself when I wrote this. You bring the secret every single time. The service holds onto nothing. Not your plaintext, not your ciphertext, not your secret, not a session, not a key, not a scrap of your payload. If you want it remembered, you remember it. Freedom and responsibility are the same coin, and I am handing you both sides.

## Threat model

I built this for application-level confidentiality, for the case where a client needs encryption that is portable and stateless and beholden to no server's memory.

### What it protects

- The confidentiality and integrity of your plaintext, even when the ciphertext package is out in the open.
- Tamper detection, because AES-GCM notices when someone has been rummaging through your pack.
- Some real resistance to brute force, because Argon2id makes each guess cost the attacker sweat.

### What it does not protect

There is no magic here, and I will not pretend otherwise. This does nothing for:

- Weak or reused secrets. A bad secret is a screen door on a submarine.
- Endpoint abuse, if you put nothing upstream to guard the trail.
- A compromised client. If the machine holding the plaintext is already owned, the game was lost before it reached me.
- A forgotten secret. Lose it and the data is gone, as gone as a river swallowed by sand. I cannot bring it back. That is the promise, not a bug.

## Design notes

- **Stateless by design.** The server stores no secrets and no encrypted material. Nothing to steal because nothing is there.
- **You must remember the secret.** Decryption lives or dies on the secret you supply. There is no reset, no recovery, no back door I left cracked open for anybody.
- **The salt is public.** It is unique so precomputed attacks find nothing to chew on, and it is required to derive the key the same way twice.
- **The nonce is public.** An AES-GCM nonce was never meant to be a secret. It only needs to be unique per key.
- **AES-GCM.** Authenticated encryption. Confidentiality and integrity in one honest package.
- **Argon2id.** A memory-hard KDF, the right tool for turning a human's password into a key an attacker cannot cheaply guess.

## Rate limiting

There is a plain fixed-window limiter living inside each function instance:

- `10,000` requests per `60` seconds, counted for the whole instance, not per IP.

Cross the line and you get an HTTP `429`:

```json
{
  "error": "rate_limited",
  "message": "You are asking too fast. The vault is not going anywhere. Wait a moment and come back."
}
```

### A warning about serverless

I will be honest with you the way a good map is honest about a bad road. In-memory rate limiting is not globally accurate once Azure scales out into a herd of instances. Each one counts alone and none of them talk. If you want real spend protection and a global throttle you can trust, put **Azure API Management** in front of the Function App and enforce the policy there. Do not lean your whole weight on the fence I built inside a single instance.

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

1. Install Python 3.10 or newer and the Azure Functions Core Tools.
2. Make a virtual environment and activate it. Keep your workshop clean.
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the local settings:
   ```bash
   cp local.settings.json.example local.settings.json
   ```
5. Run it:
   ```bash
   func start
   ```

Local trailheads:

- `http://localhost:7071/api/encrypt`
- `http://localhost:7071/api/decrypt`

When you are ready to ship it, the deployment guide is at [`.github/DEPLOYMENT.md`](../.github/DEPLOYMENT.md).

## Security notes

A few rules I hold to, and you should too:

- Never log plaintext, secrets, ciphertext, or derived keys. What gets written down gets found.
- Salt and nonce come from secure randomness, from `os.urandom`. No shortcuts, no home-brewed dice.
- Authenticated encryption is done with the `cryptography` library's AES-GCM.
- I wrote no crypto primitives of my own, and neither should you. Stand on the shoulders of people who spent their lives on it.
