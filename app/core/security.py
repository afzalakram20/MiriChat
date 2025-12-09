# import jwt
from fastapi import HTTPException, status
from .config import settings


class AuthContext:
    def __init__(self, user_id: str, tenant: str, role: str):
        self.user_id = user_id
        self.tenant = tenant
        self.role = role


# Dev-only simple verifier (HS256). Replace with DB-backed key lookup.


def verify_jwt(dev_token: str) -> AuthContext:
    # try:
    #     payload = jwt.decode(dev_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    # except jwt.PyJWTError:
    #   raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    payload={}
    user_id = str(payload.get("sub", "0"))
    tenant = payload.get("tenant", "default")
    role = payload.get("role", "user")
    return AuthContext(user_id=user_id, tenant=tenant, role=role)