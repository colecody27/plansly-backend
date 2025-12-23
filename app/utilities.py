import requests
from jose import jwt
from flask import request, abort

AUTH0_DOMAIN = "your-tenant.us.auth0.com"
AUTH0_AUDIENCE = "https://api.yourapp.com"
AUTH0_ALGORITHMS = ["RS256"]

JWKS_URL = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
jwks = requests.get(JWKS_URL).json()


def get_auth0_token():
    auth = request.headers.get("Authorization", None)
    if not auth:
        abort(401, "Authorization header missing")

    parts = auth.split()
    if parts[0].lower() != "bearer" or len(parts) != 2:
        abort(401, "Authorization header malformed")

    return parts[1]


def verify_auth0_jwt():
    token = get_auth0_token()

    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception:
        abort(401, "Invalid token header")

    rsa_key = None
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }

    if not rsa_key:
        abort(401, "Unable to find signing key")

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=AUTH0_ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
        return payload

    except jwt.ExpiredSignatureError:
        abort(401, "Token expired")
    except jwt.JWTClaimsError:
        abort(401, "Invalid claims")
    except Exception:
        abort(401, "Invalid token")
