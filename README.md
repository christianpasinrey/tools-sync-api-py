# Tools Sync API (Python)

Zero-knowledge encrypted vault backend built with **FastAPI** + **MongoDB**. Python port of [tools-sync-api](https://github.com/user/tools-sync-api) (Node.js/Express).

The server never sees unencrypted data — all encryption/decryption happens client-side.

## Tech Stack

- **FastAPI** — async web framework
- **Motor + Beanie** — async MongoDB ODM
- **bcrypt** — password & token hashing
- **python-jose** — JWT authentication
- **slowapi** — rate limiting
- **aiosmtplib** — async email (SMTP)
- **Pydantic** — data validation & settings

## Features

- JWT authentication with refresh token rotation (HttpOnly cookies)
- Zero-knowledge architecture (server stores only encrypted blobs)
- CRUD for vault items across 13 store types
- Multi-device sync with Last-Write-Wins conflict resolution
- Batch push/pull (up to 50 items)
- Deletion log for sync propagation
- Password reset via email with cryptographic tokens
- Rate limiting, security headers, CORS
- Auto-generated API docs (Swagger UI)

## Requirements

- Python 3.12+
- MongoDB 6+

## Setup

```bash
# Clone the repo
git clone https://github.com/user/tools-sync-api-py.git
cd tools-sync-api-py

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env file and configure
cp .env.example .env
```

## Configuration

Edit `.env` with your values:

```env
PORT=3002
MONGODB_URI=mongodb://127.0.0.1:27017/tools-sync-py
JWT_SECRET=your-random-secret-here
JWT_REFRESH_SECRET=your-other-random-secret-here
CORS_ORIGIN=http://localhost:5173
FRONTEND_URL=http://localhost:5173
```

For email (password reset):

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=465
SMTP_SECURE=true
SMTP_USER=user@example.com
SMTP_PASS=your-password
SMTP_FROM=noreply@example.com
```

## Run

```bash
# Development (with auto-reload)
uvicorn src.main:app --host 0.0.0.0 --port 3002 --reload

# Production
uvicorn src.main:app --host 0.0.0.0 --port 3002
```

API docs available at: `http://localhost:3002/docs`

## API Endpoints

### Authentication (`/auth`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | No | Register with email + password |
| POST | `/auth/login` | No | Login, returns JWT + refresh cookie |
| POST | `/auth/refresh` | Cookie | Rotate refresh token |
| POST | `/auth/change-password` | Bearer | Change password |
| POST | `/auth/logout` | Bearer | Invalidate refresh token |
| POST | `/auth/forgot-password` | No | Send reset email |
| POST | `/auth/verify-reset-token` | No | Verify reset token |
| POST | `/auth/reset-account` | No | Reset password + delete all data |

### Vault (`/vault`) — All require Bearer token

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/vault/sync-status?since=<timestamp>` | Items & deletions since timestamp |
| GET | `/vault/:storeName` | List items (metadata only) |
| GET | `/vault/:storeName/:itemId` | Get item with encrypted payload |
| PUT | `/vault/:storeName/:itemId` | Upsert item (LWW conflict resolution) |
| DELETE | `/vault/:storeName/:itemId` | Delete item + log deletion |
| POST | `/vault/batch-push` | Batch upsert (max 50) |
| POST | `/vault/batch-pull` | Batch fetch (max 50) |

### Allowed store names

`image-presets` · `svg-projects` · `three-scenes` · `pdf-documents` · `spreadsheet-workbooks` · `markdown-documents` · `color-palettes` · `devtools-snippets` · `api-collections` · `phone-configs` · `map-projects` · `invoice-configs` · `kanban-boards`

## Project Structure

```
src/
├── main.py                 # FastAPI app, middleware, routes
├── config/
│   ├── settings.py         # Environment config (pydantic-settings)
│   └── db.py               # MongoDB connection (Motor + Beanie)
├── models/
│   ├── user.py             # User document
│   ├── vault_item.py       # VaultItem document + EncryptedPayload
│   └── deletion_log.py     # DeletionLog document
├── controllers/
│   ├── auth_controller.py  # Auth logic (register, login, reset, etc.)
│   └── vault_controller.py # Vault logic (CRUD, sync, batch)
├── routes/
│   ├── auth.py             # /auth endpoints + request schemas
│   └── vault.py            # /vault endpoints + request schemas
├── middleware/
│   ├── auth.py             # JWT Bearer verification
│   ├── rate_limiter.py     # Rate limit config (slowapi)
│   ├── error_handler.py    # Global error handler
│   └── security_headers.py # Security headers (helmet equivalent)
└── utils/
    └── email.py            # SMTP email for password reset
```

## Testing

```bash
# With the server running:
python test_api.py
```

Runs 8 sequential tests: password validation, register, login, vault upsert, list, get, sync-status, and root health check.

## Security

| Feature | Implementation |
|---------|---------------|
| Password validation | Minimum 8 characters (enforced server-side via Pydantic) |
| Password hashing | bcrypt (12 rounds) |
| Token hashing | SHA-256 pre-hash + bcrypt (10 rounds) — handles tokens >72 bytes |
| Access token | JWT, 15 min, in-memory |
| Refresh token | JWT, 7 days, HttpOnly/Secure/SameSite cookie with rotation |
| Reset token | crypto random 64-char hex, bcrypt hashed, 1h expiry, single-use |
| Atomic registration | User rollback on token generation failure |
| Rate limiting | Auth: 10/15min, Forgot: 3/15min, API: 300/15min, Batch: 10/min |
| Headers | X-Content-Type-Options, X-Frame-Options, HSTS, CSP, Referrer-Policy |
| CORS | Configured origin only, credentials enabled |
| Payload limit | 10 MB per item |
| Logging | Structured logging (no sensitive data in logs) |
| Timezone-aware | All timestamps use `datetime.now(UTC)` |

## License

MIT
