# 认证工具模块 - 提供JWT Token验证功能
from fastapi import Request, HTTPException
import jwt

# JWT配置（与main.py保持一致）
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# 验证JWT Token的中间件函数
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
        raise HTTPException(401, "令牌已过期")
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, "无效令牌") 