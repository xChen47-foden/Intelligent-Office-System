from fastapi import Request, HTTPException
import jwt

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

def verify_token(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(401, "未认证")
    try:
        payload = jwt.decode(auth.split(" ")[1], SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "userId": int(payload["sub"]),
            "sub": payload["sub"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token已过期")
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, "无效Token") 