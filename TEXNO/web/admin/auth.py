from fastapi import HTTPException, Header
from typing import Optional
import os

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "max_bot_admin_secret_2024")

async def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"username": "admin"}