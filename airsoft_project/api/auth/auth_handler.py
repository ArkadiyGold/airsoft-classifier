import jwt
from datetime import datetime, timedelta

SECRET_KEY = "2b21c3c691de38449e62b5fc17a515a466cd1c7c11d4077beef7fd51a6d82d27"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=24)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload if payload["exp"] > datetime.utcnow().timestamp() else None
    except:
        return None