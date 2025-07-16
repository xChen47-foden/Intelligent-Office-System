# 后端服务说明

本目录包含三种后端服务示例：
- fastapi_app：主后端，负责聚合和调度
- node_service：Node.js 子服务
- java_service：Java 子服务

可根据实际业务扩展和联动。 

import redis
from fastapi import FastAPI
from pydantic import BaseModel
import random
import smtplib
from email.mime.text import MIMEText

# 连接本地 Redis，实际部署请配置密码和地址
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True) 

app = FastAPI()

class CaptchaRequest(BaseModel):
    contact: str
