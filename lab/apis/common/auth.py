"""Shared token validation for the SIL lab services.

Kong already rejects missing, expired or wrongly signed tokens. Every service checks again
(defence in depth) and adds what the gateway cannot know: roles and which facility's
records the caller may see.
"""
import os

import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

ISSUER = os.environ["OIDC_ISSUER"]
AUDIENCE = os.environ.get("OIDC_AUDIENCE", "sil-api")
_jwks = PyJWKClient(os.environ["JWKS_URL"], cache_keys=True, lifespan=300)
_bearer = HTTPBearer(auto_error=False)


def facility_from_groups(groups: list[str]) -> int | None:
    """Keycloak puts group names in the 'groups' claim, e.g. ['facility-1']."""
    for group in groups or []:
        name = group.rsplit("/", 1)[-1]
        if name.startswith("facility-"):
            try:
                return int(name.split("-", 1)[1])
            except ValueError:
                continue
    return None


def get_current_user(cred: HTTPAuthorizationCredentials | None = Security(_bearer)) -> dict:
    if cred is None:
        raise HTTPException(status_code=401, detail="missing token")
    try:
        key = _jwks.get_signing_key_from_jwt(cred.credentials).key
        claims = jwt.decode(
            cred.credentials,
            key,
            algorithms=["RS256"],          # never accept 'none' or HS256 with a public key
            issuer=ISSUER,
            audience=AUDIENCE,
            options={"require": ["exp", "iat", "iss", "sub"]},
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid token")
    claims["roles"] = claims.get("realm_access", {}).get("roles", [])
    claims["facility_id"] = facility_from_groups(claims.get("groups", []))
    claims["username"] = claims.get("preferred_username", claims["sub"])
    return claims


def require_role(*allowed: str):
    """Dependency factory: the caller needs at least one of the allowed roles."""

    def check(user: dict = Depends(get_current_user)) -> dict:
        if not set(allowed) & set(user["roles"]):
            raise HTTPException(status_code=403, detail="forbidden")
        return user

    return check


def require_facility(user: dict) -> int:
    if user.get("facility_id") is None:
        raise HTTPException(status_code=403, detail="no facility assigned")
    return user["facility_id"]
