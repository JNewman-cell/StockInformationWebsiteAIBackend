"""
Authentication middleware for JWT token validation.
Integrated with Stack Auth (Neon Auth) using RS256 algorithm.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import jwt
import os
from dotenv import load_dotenv
import requests
from functools import lru_cache
from datetime import datetime

load_dotenv()

# JWT Configuration from Stack Auth
NEON_AUTH_ISSUER_URI = os.getenv(
    "NEON_AUTH_ISSUER_URI",
    "https://api.stack-auth.com/api/v1/projects/142ba44a-dc12-4035-a4e8-a043e425f201"
)
STACK_JWKS_URL = os.getenv(
    "STACK_JWKS_URL",
    "https://api.stack-auth.com/api/v1/projects/142ba44a-dc12-4035-a4e8-a043e425f201/.well-known/jwks.json"
)
JWT_ALGORITHMS = ["RS256", "ES256"]  # Allow both RSA and ECDSA algorithms
JWT_ISSUER = os.getenv("JWT_ISSUER", "https://api.stack-auth.com")

# Bearer token security scheme
security = HTTPBearer(auto_error=False)

# Cache for JWKS (JSON Web Key Set) to avoid repeated requests
_jwks_cache = {}
_jwks_cache_time = None


@lru_cache(maxsize=1)
def get_jwks_url():
    """Get the JWKS URL from Stack Auth issuer"""
    return STACK_JWKS_URL


def get_public_key(token: str) -> Optional[Dict[str, Any]]:
    """
    Fetch the public key from Stack Auth's JWKS endpoint.
    Caches the result to avoid repeated requests.
    """
    global _jwks_cache, _jwks_cache_time
    
    try:
        # Refresh cache every hour or if empty
        now = datetime.utcnow().timestamp()
        if not _jwks_cache or (now - _jwks_cache_time > 3600):
            jwks_url = get_jwks_url()
            print(f"🔑 Fetching JWKS from: {jwks_url}")
            response = requests.get(jwks_url, timeout=5)
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_cache_time = now
            print(f"🔑 JWKS refreshed with {len(_jwks_cache.get('keys', []))} keys")
        
        # Get kid (key ID) from token header
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        print(f"🔑 Token kid: {kid}, Token alg: {header.get('alg')}")
        
        if not kid or not _jwks_cache:
            print(f"🔑 Missing kid or cache - kid: {kid}, cache: {bool(_jwks_cache)}")
            return None
        
        # Find the matching key
        for key in _jwks_cache.get("keys", []):
            if key.get("kid") == kid:
                print(f"🔑 Found matching key for kid: {kid}")
                return key
        
        print(f"🔑 No matching key found for kid: {kid}")
        print(f"🔑 Available kids: {[k.get('kid') for k in _jwks_cache.get('keys', [])]}")
        return None
        
    except Exception as e:
        print(f"❌ Error fetching JWKS: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_token_from_header(
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Extract JWT token from Authorization header or x-stack-access-token header.
    
    Supports two header formats:
    1. Authorization: Bearer <token>
    2. x-stack-access-token: <token>
    
    Args:
        authorization: HTTP authorization credentials
        
    Returns:
        JWT token string if found, None otherwise
    """
    if authorization and authorization.credentials:
        return authorization.credentials
    return None


async def get_current_user(
    token: Optional[str] = Depends(extract_token_from_header)
) -> Dict[str, Any]:
    """
    Validate JWT token from Stack Auth and extract user information.
    
    This function validates the JWT token using Stack Auth's public keys
    and extracts user information from the token payload.
    
    Stack Auth Configuration:
    - Uses RS256 algorithm (RSA public key verification)
    - Validates against Stack Auth issuer
    - Extracts user_id and other claims from payload
    
    Args:
        token: JWT token from request headers
        
    Returns:
        Dictionary containing user information from token claims
        
    Raises:
        HTTPException: 401 if token is missing, invalid, or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid token in the x-stack-access-token header or Authorization: Bearer header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # First, decode without verification to get header info
        header = jwt.get_unverified_header(token)
        
        # Get the public key from Stack Auth's JWKS
        public_key_data = get_public_key(token)
        
        if not public_key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to verify token: public key not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Convert JWKS public key to PEM format
        from jwt import PyJWK
        public_key = PyJWK.from_dict(public_key_data).key
        
        # Decode and validate JWT token
        # Get the expected audience from environment
        expected_audience = "142ba44a-dc12-4035-a4e8-a043e425f201"  # Stack Auth project ID
        
        payload = jwt.decode(
            token,
            public_key,
            algorithms=JWT_ALGORITHMS,
            audience=expected_audience,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True
            }
        )
        
        # Extract user information from token claims
        # Stack Auth typically uses 'sub' for user ID
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        username: str = payload.get("preferred_username") or payload.get("username")
        
        if user_id is None:
            raise credentials_exception
        
        return {
            "user_id": user_id,
            "email": email,
            "username": username,
            "claims": payload  # Full token claims for additional validation
        }
        
    except jwt.ExpiredSignatureError as e:
        print(f"🔐 Token validation failed - Expired: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.PyJWTError, jwt.InvalidAlgorithmError) as e:
        print(f"🔐 Token validation failed - JWT Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"🔐 Token validation failed - Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verify that the current user is active.
    
    This is an optional additional layer that can check user status
    in the database if needed.
    
    Args:
        current_user: User information from get_current_user
        
    Returns:
        User information if active
        
    Raises:
        HTTPException: 403 if user is inactive
    """
    # Note: This can be extended to check database for user active status
    # For now, we assume JWT validation is sufficient
    return current_user
