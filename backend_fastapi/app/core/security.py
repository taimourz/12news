from fastapi import Header, HTTPException
from app.config import settings

def validate_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")