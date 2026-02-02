# TRON USDT (TRC-20) Private Payment Gateway

Production-focused FastAPI backend for USDT (TRC-20) payments on TRON, defaulting to Nile testnet. This service is designed for **private custody** and does **not** use third-party processors.

## Features
- Async FastAPI + PostgreSQL + SQLAlchemy
- HD wallet address derivation (BIP-44 for TRON)
- AES-256-GCM encryption for private keys
- TRC-20 transfer monitoring with 20+ confirmations
- JWT admin auth, HMAC webhooks, rate limiting, audit logs

## Folder Structure
```
app/
  api/routes/         # REST endpoints
  core/               # config, security, database, middleware
  models/             # SQLAlchemy models
  schemas/            # Pydantic schemas
  services/           # business logic
  tasks/              # background blockchain polling
```

## Setup
1. Create a virtual environment and install dependencies.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill values.
3. Ensure PostgreSQL is running and update `DATABASE_URL`.
4. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```

## Testnet Usage (Nile)
- Default network is Nile. Confirm your `TRON_*` endpoints point to Nile.
- USDT TRC-20 contract defaults to the official address on Nile.

## Deployment Precautions
- **HTTPS only**: deploy behind a TLS reverse proxy.
- Rotate `JWT_SECRET` and `WEBHOOK_SECRET` regularly.
- Store `ENCRYPTION_KEY_B64` and wallet secrets in a KMS.
- Keep cold wallet private keys offline.
- Use a dedicated TRON node or authenticated gateway in production.

## Example API Usage
### Create payment
**Request**
```bash
curl -X POST http://localhost:8000/api/payments/create \
  -H "Content-Type: application/json" \
  -d '{"amount": 12.5, "merchant_api_key": "merchant-key"}'
```

**Response**
```json
{
  "payment_id": 42,
  "address": "TXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "amount": 12.5,
  "expires_at": "2024-06-01T12:00:00Z",
  "status": "CREATED"
}
```

### Check payment status
```bash
curl http://localhost:8000/api/payments/status/42
```

### Admin sweep to cold wallet
```bash
curl -X POST http://localhost:8000/api/admin/sweep-to-cold-wallet \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"max_amount": 100.0}'
```

## Security Notes
- Private keys are encrypted with AES-256-GCM before DB storage.
- Webhooks require `X-Signature` HMAC-SHA256 header.
- Confirmations enforced via `TRON_CONFIRMATION_BLOCKS`.

