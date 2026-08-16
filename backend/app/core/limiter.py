from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter configured to use remote IP address
limiter = Limiter(key_func=get_remote_address)