"""Clerk authentication and JWT validation."""
import os
import jwt
import requests
from typing import Optional
from fastapi import HTTPException, Request
from functools import lru_cache


# Clerk configuration - JWKS URL and Issuer method (recommended)
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", "")
CLERK_ISSUER = os.getenv("CLERK_ISSUER", "")


@lru_cache(maxsize=1)
def get_clerk_jwks():
    """
    Fetch Clerk's JSON Web Key Set (JWKS) for JWT validation.
    Cached to avoid repeated requests.
    """
    if not CLERK_JWKS_URL:
        return None
    
    try:
        response = requests.get(CLERK_JWKS_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to fetch Clerk JWKS: {e}")
        return None


def verify_clerk_token(token: str) -> Optional[dict]:
    """
    Verify a Clerk JWT token using JWKS.
    
    Returns the decoded token payload if valid, None otherwise.
    """
    if not token:
        return None
    
    try:
        # For development, decode without verification if no Clerk config
        if not CLERK_JWKS_URL or not CLERK_ISSUER:
            print("Warning: Running without Clerk config - accepting all tokens in development mode")
            # In dev mode without Clerk, just decode without verification
            return jwt.decode(token, options={"verify_signature": False})
        
        # Decode header to get the key ID
        header = jwt.get_unverified_header(token)
        
        # Get JWKS
        jwks = get_clerk_jwks()
        if not jwks:
            raise Exception("Could not fetch JWKS")
        
        # Find the right key
        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == header.get("kid"):
                key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
                break
        
        if not key:
            raise Exception("Key not found in JWKS")
        
        # Verify and decode with issuer validation
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=CLERK_ISSUER,  # Validate issuer
            options={"verify_signature": True}
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Extract and validate user from request headers.
    Returns user info if authenticated, None otherwise.
    """
    # Get Authorization header
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        return None
    
    # Extract token
    token = auth_header.replace("Bearer ", "")
    
    # Verify token
    payload = verify_clerk_token(token)
    
    if not payload:
        return None
    
    # Extract user info from Clerk token
    return {
        "user_id": payload.get("sub"),  # Clerk user ID
        "email": payload.get("email"),
        "name": payload.get("name"),
        "username": payload.get("username"),
    }


async def require_auth(request: Request) -> dict:
    """
    Require authentication. Raises HTTPException if not authenticated.
    Use this for protected endpoints.
    """
    user = await get_current_user(request)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in."
        )
    
    return user

