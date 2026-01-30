"""Quick test script for the API endpoints."""
import json
import urllib.request

BASE = "http://localhost:3002"


def post(path, data=None, token=None):
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE}{path}", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def put(path, data, token):
    body = json.dumps(data).encode()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


print("=" * 50)
print("TESTING TOOLS SYNC API (Python)")
print("=" * 50)

# 1. Register
print("\n[1] POST /auth/register")
status, data = post("/auth/register", {"email": "test2@test.com", "password": "testpassword123"})
print(f"  Status: {status}")
print(f"  Response: {json.dumps(data, indent=2)[:200]}")

token = data.get("token")

# 2. Login
print("\n[2] POST /auth/login")
status, data = post("/auth/login", {"email": "test2@test.com", "password": "testpassword123"})
print(f"  Status: {status}")
print(f"  Response: {json.dumps(data, indent=2)[:200]}")
token = data.get("token", token)

if not token:
    print("\n  No token obtained, stopping tests.")
    exit(1)

# 3. Vault - upsert item
print("\n[3] PUT /vault/color-palettes/palette-1")
status, data = put("/vault/color-palettes/palette-1", {
    "itemName": "My Palette",
    "encryptedPayload": {"salt": "dGVzdA==", "iv": "dGVzdA==", "data": "dGVzdA=="},
    "updatedAt": 1700000000000,
}, token)
print(f"  Status: {status}")
print(f"  Response: {json.dumps(data, indent=2)}")

# 4. Vault - list items
print("\n[4] GET /vault/color-palettes")
status, data = get("/vault/color-palettes", token)
print(f"  Status: {status}")
print(f"  Response: {json.dumps(data, indent=2)}")

# 5. Vault - get item
print("\n[5] GET /vault/color-palettes/palette-1")
status, data = get("/vault/color-palettes/palette-1", token)
print(f"  Status: {status}")
print(f"  Response: {json.dumps(data, indent=2)[:300]}")

# 6. Sync status
print("\n[6] GET /vault/sync-status?since=0")
status, data = get("/vault/sync-status?since=0", token)
print(f"  Status: {status}")
print(f"  Response: {json.dumps(data, indent=2)[:300]}")

# 7. Root
print("\n[7] GET /")
status, data = get("/")
print(f"  Status: {status}")
print(f"  Response: {json.dumps(data, indent=2)}")

print("\n" + "=" * 50)
print("ALL TESTS COMPLETED")
print("=" * 50)
