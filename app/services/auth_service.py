# app/auth.py
import json
from urllib.request import urlopen
from jose import jwt, JWTError

class Auth0JWTBearerTokenValidator:
    def __init__(self, domain, audience):
        self.domain = domain
        self.audience = audience
        self.issuer = f"https://{domain}/"
        
        jwks_url = f"{self.issuer}.well-known/jwks.json"
        try:
            jwks = json.loads(urlopen(jwks_url).read())
            self.jwks = {key["kid"]: key for key in jwks["keys"]}
        except Exception as e:
            raise RuntimeError(f"Failed to fetch JWKS: {e}")

    def validate_token(self, id_token):
        """
        Validate the Auth0 ID token.
        Returns the decoded claims if valid.
        Raises Exception if invalid.
        """
        try:
            unverified_header = jwt.get_unverified_header(id_token)
        except JWTError:
            raise Exception("Invalid token header")

        kid = unverified_header.get("kid")
        if kid not in self.jwks:
            raise Exception("Public key not found in JWKS")

        rsa_key = self.jwks[kid]

        try:
            claims = jwt.decode(
                id_token,
                rsa_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
            )
            return claims
        except JWTError as e:
            raise Exception(f"Token verification failed: {e}")
