from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Rate limit strings
AUTH_LIMIT = "10/15minutes"
API_LIMIT = "300/15minutes"
FORGOT_PASSWORD_LIMIT = "3/15minutes"
BATCH_LIMIT = "10/minute"
