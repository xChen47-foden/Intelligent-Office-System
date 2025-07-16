import redis
from fastapi import FastAPI, HTTPException, Body, Depends, Request, UploadFile, File, Query, Path, APIRouter, WebSocket, WebSocketDisconnect, Form
from fastapi.middleware.cors import CORSMiddleware  # 新增CORS支持
from pydantic import BaseModel
import random
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import re
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Table, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.future import select
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import bcrypt
import jwt
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routes import search, contact, group, message, assistant_upload
import shutil
import time
import json
import uuid
from fastapi.responses import FileResponse, JSONResponse
import mimetypes
import httpx
import string
import requests
import asyncio
from fastapi.staticfiles import StaticFiles
import threading
from fastapi import status
from fastapi.responses import JSONResponse
from .db import Base, User, SessionLocal, engine, TodayTask
from .auth_utils import verify_token
from starlette.websockets import WebSocketDisconnect
from sqlalchemy import delete as sqlalchemy_delete

# 初始化FastAPI应用
app = FastAPI()

# 添加CORS中间件（关键修改）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3006", "http://localhost:3007", "*"],  # 允许前端和本地调试
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# Redis配置
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# 数据库配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEETING_DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, '../meetings.db')}"
meeting_engine = create_async_engine(MEETING_DATABASE_URL, echo=True, future=True)
MeetingSessionLocal = sessionmaker(bind=meeting_engine, class_=AsyncSession, expire_on_commit=False)

# JWT配置
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# 数据模型
class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    host = Column(String)
    time = Column(String)  # 建议用 DateTime 类型，前端传字符串
    location = Column(String)
    period = Column(String, default="")
    status = Column(String, default="upcoming")
    user_id = Column(Integer, index=True)  # 新增字段
    participants = Column(String, default="")  # 参会人列表，存储为逗号分隔的用户ID
    host_user_id = Column(Integer, default=0)  # 主持人用户ID

# 录音历史数据模型
class RecordingHistory(Base):
    __tablename__ = "recording_history"
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, index=True)  # 关联的会议ID
    meeting_title = Column(String)  # 会议标题
    user_id = Column(Integer, index=True)  # 录音者ID
    filename = Column(String)  # 录音文件名
    file_path = Column(String)  # 录音文件路径
    transcript = Column(Text)  # 语音转录内容
    minutes = Column(Text)  # 生成的会议纪要
    duration = Column(Integer, default=0)  # 录音时长（秒）
    file_size = Column(Integer, default=0)  # 文件大小（字节）
    created_at = Column(String)  # 创建时间
    status = Column(String, default="completed")  # 状态：recording, completed, failed

# 通知数据模型
# 删除通知数据模型

# Pydantic模型
class CaptchaRequest(BaseModel):
    contact: str

class CaptchaVerifyRequest(BaseModel):
    contact: str
    captcha: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    contact: str
    captcha: str
    department: str  # 新增部门字段

class LoginRequest(BaseModel):
    username: str
    password: str
    department: str  # 新增部门字段

class UpdateUserInfoRequest(BaseModel):
    realName: str = ""
    nickName: str = ""

class UpdatePreferencesRequest(BaseModel):
    theme: str
    language: str

class MeetingCreateRequest(BaseModel):
    title: str
    host: str
    time: str
    location: str
    period: str = ""
    status: str = "upcoming"
    participants: list[int] = []  # 参会人用户ID列表

class ResetPasswordRequest(BaseModel):
    contact: str
    captcha: str
    new_password: str

# 录音历史相关模型
class RecordingUploadRequest(BaseModel):
    meeting_id: int = None
    meeting_title: str = ""
    filename: str
    transcript: str = ""
    minutes: str = ""
    duration: int = 0
    file_size: int = 0

class RecordingUpdateRequest(BaseModel):
    transcript: str = ""
    minutes: str = ""

# 删除通知相关Pydantic模型

# 邮件发送功能
def send_email_code(to_email, code):
    email_user = os.getenv("EMAIL_USER", "1642256761@qq.com")
    email_pass = os.getenv("EMAIL_PASS", "izeltputkiwldgba")
    email_host = os.getenv("EMAIL_HOST", "smtp.qq.com")
    email_port = int(os.getenv("EMAIL_PORT", 465))

    msg = MIMEText(
        f"您的验证码是：{code}，5分钟内有效。",
        'plain',
        'utf-8'
    )
    msg['Subject'] = Header('邮箱验证码', 'utf-8')
    msg['From'] = formataddr(('系统管理员', email_user))
    msg['To'] = to_email

    try:
        server = smtplib.SMTP_SSL(email_host, email_port)
        server.login(email_user, email_pass)
        server.sendmail(email_user, [to_email], msg.as_string())
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        raise Exception("邮箱认证失败，请检查邮箱和授权码是否正确")
    except smtplib.SMTPConnectError as e:
        raise Exception("无法连接到邮件服务器，请检查网络连接")
    except smtplib.SMTPException as e:
        raise Exception(f"邮件发送失败: {str(e)}")
    except Exception as e:
        raise Exception(f"发送邮件时发生未知错误: {str(e)}")

# 路由处理
@app.post("/api/send-captcha")
async def send_captcha(data: CaptchaRequest):
    # 验证邮箱格式
    email_reg = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_reg, data.contact):
        return {"code": 1, "msg": "请输入正确的邮箱格式"}
    
    # 生成验证码
    code = str(random.randint(100000, 999999))
    
    try:
        # 存储验证码到Redis
        r.setex(f"captcha:{data.contact}", 300, code)
        
        # 发送邮件
        send_email_code(data.contact, code)
        return {"code": 0, "msg": "验证码已发送"}
    except Exception as e:
        # 如果发送失败，删除Redis中的验证码
        try:
            r.delete(f"captcha:{data.contact}")
        except:
            pass
        return {"code": 500, "msg": str(e)}

@app.post("/api/verify-captcha")
async def verify_captcha(data: CaptchaVerifyRequest):
    real_code = r.get(f"captcha:{data.contact}")
    if not real_code:
        return {"code": 1, "msg": "验证码已过期或不存在"}
    if data.captcha != real_code:
        return {"code": 2, "msg": "验证码错误"}
    r.delete(f"captcha:{data.contact}")
    return {"code": 0, "msg": "验证成功"}

def generate_random_username():
    return "user_" + ''.join(random.choices(string.digits, k=5))

def generate_random_avatar():
    """生成随机头像"""
    # 预设的头像列表（包括SVG和其他格式）
    avatar_list = [
        "avatar1.svg", "avatar2.svg", "avatar3.svg", 
        "avatar1.jpg", "avatar2.jpg", "avatar3.jpg", "avatar4.jpg", "avatar5.jpg",
        "avatar6.jpg", "avatar7.jpg", "avatar8.jpg", "avatar9.jpg", "avatar10.jpg",
        "2.jpg"  # 现有的头像文件
    ]
    
    # 如果有预设头像文件，随机选择一个
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'avatar')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # 检查是否有可用的头像文件
    available_avatars = []
    for avatar in avatar_list:
        avatar_path = os.path.join(uploads_dir, avatar)
        if os.path.exists(avatar_path):
            available_avatars.append(avatar)
    
    if available_avatars:
        return f"avatar/{random.choice(available_avatars)}"
    
    # 如果没有预设头像，生成基于字符的头像URL
    # 使用DiceBear或其他头像生成服务
    avatar_styles = ['adventurer', 'avataaars', 'big-ears', 'big-ears-neutral', 'big-smile', 'bottts', 'croodles', 'fun-emoji', 'icons', 'identicon', 'initials', 'lorelei', 'micah', 'miniavs', 'open-peeps', 'personas', 'pixel-art', 'shapes', 'thumbs']
    
    # 生成一个随机种子
    seed = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    style = random.choice(avatar_styles)
    
    # 返回DiceBear API URL
    return f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf"

def save_avatar_from_url(avatar_url: str, user_id: int) -> str:
    """从URL下载头像并保存到本地"""
    try:
        import requests
        response = requests.get(avatar_url, timeout=10)
        if response.status_code == 200:
            uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'avatar')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # 保存为SVG文件
            filename = f"user_{user_id}_{int(time.time())}.svg"
            file_path = os.path.join(uploads_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return f"avatar/{filename}"
    except Exception as e:
        print(f"保存头像失败: {e}")
    
    # 如果保存失败，返回默认头像路径
    return "avatar/default.svg"

@app.post("/api/register")
async def register_user(data: RegisterRequest):
    print("收到注册请求：", data.username, data.contact, data.department)
    real_code = r.get(f"captcha:{data.contact}")
    print("验证码从redis获取：", real_code)
    if not real_code:
        print("验证码已过期或不存在")
        raise HTTPException(400, "验证码已过期或不存在")
    if data.captcha != real_code:
        print("验证码错误")
        raise HTTPException(400, "验证码错误")
    r.delete(f"captcha:{data.contact}")

    # 自动生成账号
    username = data.username.strip() if data.username else ""
    if not username:
        username = generate_random_username()
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            print("用户名已存在")
            raise HTTPException(400, "用户名已存在")
        hashed_password = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        
        # 生成随机头像
        avatar_url = generate_random_avatar()
        
        new_user = User(
            username=username,
            password=hashed_password,
            contact=data.contact,
            real_name="",
            nick_name="",
            avatar=avatar_url,  # 使用生成的头像
            department=data.department
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)  # 获取用户ID
        
        # 如果头像是外部URL，尝试下载并保存到本地
        if avatar_url.startswith('https://'):
            try:
                local_avatar = save_avatar_from_url(avatar_url, new_user.id)
                new_user.avatar = local_avatar
                await session.commit()
            except Exception as e:
                print(f"下载头像失败，使用默认头像: {e}")
                new_user.avatar = "avatar/default.svg"
                await session.commit()
        
        print("注册成功，已生成随机头像")
        return {"code": 0, "msg": "注册成功", "username": username, "department": data.department}

@app.post("/auth/login")
async def login(data: LoginRequest):
    try:
        print("收到登录请求：", data.username, data.department)
        async with SessionLocal() as session:
            result = await session.execute(select(User).where(User.username == data.username, User.department == data.department))
            user = result.scalar_one_or_none()
            if not user or not bcrypt.checkpw(data.password.encode(), user.password.encode()):
                return {"code": 1, "msg": "用户名、密码或部门错误"}
            
            # 检查用户是否有头像，如果没有则生成一个
            if not user.avatar or user.avatar == "":
                avatar_url = generate_random_avatar()
                user.avatar = avatar_url
                
                # 如果头像是外部URL，尝试下载并保存到本地
                if avatar_url.startswith('https://'):
                    try:
                        local_avatar = save_avatar_from_url(avatar_url, user.id)
                        user.avatar = local_avatar
                    except Exception as e:
                        print(f"下载头像失败，使用默认头像: {e}")
                        user.avatar = "avatar/default.svg"
                
                await session.commit()
                print(f"为用户 {user.username} 生成了随机头像: {user.avatar}")
            
            payload = {
                "sub": str(user.id),
                "exp": datetime.utcnow() + timedelta(hours=2)
            }
            token = jwt.encode(payload, SECRET_KEY, ALGORITHM)
            return {
                "code": 0,
                "msg": "登录成功",
                "data": {
                    "username": user.username,
                    "token": token,
                    "avatar": user.avatar  # 返回头像信息
                }
            }
    except Exception as e:
        print("登录异常：", e)
        return {"code": 500, "msg": f"登录异常: {str(e)}"}

# 受保护路由
def verify_token(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        print("未认证，未带token")
        raise HTTPException(401, "未认证")
    try:
        payload = jwt.decode(auth.split(" ")[1], SECRET_KEY, algorithms=[ALGORITHM])
        print("token解码成功，payload:", payload)
        # 兼容所有接口，返回 userId 和 sub
        return {
            "userId": int(payload["sub"]),
            "sub": payload["sub"]
        }
    except jwt.ExpiredSignatureError:
        print("token已过期")
        raise HTTPException(401, "Token已过期")
    except jwt.InvalidTokenError as e:
        print("token无效:", e)
        raise HTTPException(401, "无效Token")

@app.get("/api/protected")
async def protected_route(payload: dict = Depends(verify_token)):
    return {"msg": f"欢迎, {payload['sub']}"}

@app.get("/auth/getUserInfo")
async def get_user_info(payload: dict = Depends(verify_token)):
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.id == int(payload["sub"])))  # sub转int
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(404, "用户不存在")
        return {
            "code": 0,
            "data": {
                "userId": user.id,
                "userName": user.username,
                "email": user.contact,
                "realName": user.real_name,
                "nickName": user.nick_name,
                "theme": user.theme,
                "language": user.language,
                "avatar": user.avatar,
                "department": user.department,
                "roles": ["admin"],
                "menus": [
                    {
                        "path": "/workbench",
                        "name": "工作台",
                        "icon": "icon-workbench"
                    },
                    {
                        "path": "/schedule",
                        "name": "日程管理",
                        "icon": "icon-calendar"
                    },
                    {
                        "path": "/meetings",
                        "name": "会议管理",
                        "icon": "icon-meeting"
                    },
                    {
                        "path": "/knowledge",
                        "name": "知识库",
                        "icon": "icon-knowledge"
                    },
                    {
                        "path": "/assistant",
                        "name": "智能助手",
                        "icon": "icon-ai"
                    },
                    {
                        "path": "/system/user-center",
                        "name": "个人中心",
                        "icon": "icon-user"
                    }
                ],
                "permissions": ["view_dashboard", "edit_profile", "manage_schedule", "manage_meetings", "use_ai_assistant"]
            }
        }

# 初始化数据库
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # 检查并添加新字段到meetings表
    try:
        async with MeetingSessionLocal() as session:
            # 尝试查询新字段，如果出错则添加字段
            try:
                await session.execute(text("SELECT participants FROM meetings LIMIT 1"))
            except Exception:
                # 添加participants字段
                await session.execute(text("ALTER TABLE meetings ADD COLUMN participants TEXT DEFAULT ''"))
                await session.commit()
                print("已添加 participants 字段到 meetings 表")
            
            try:
                await session.execute(text("SELECT host_user_id FROM meetings LIMIT 1"))
            except Exception:
                # 添加host_user_id字段
                await session.execute(text("ALTER TABLE meetings ADD COLUMN host_user_id INTEGER DEFAULT 0"))
                await session.commit()
                print("已添加 host_user_id 字段到 meetings 表")
    except Exception as e:
        print(f"数据库字段检查/添加失败: {e}")
    
    async with meeting_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def on_startup():
    await init_db()

# 测试路由
@app.get("/")
async def root():
    return {"message": "API服务运行正常"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(search.router)
app.include_router(contact.router)
app.include_router(group.router)
app.include_router(message.router)

# ========== 智能文档相关接口，操作 doc.json ==========
@app.post("/api/doc/upload")
async def upload_doc(file: UploadFile = File(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    doc_path = os.path.join(uploads_dir, 'doc.json')
    os.makedirs(uploads_dir, exist_ok=True)
    save_path = os.path.join(uploads_dir, file.filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # 生成自增数字id
    if os.path.exists(doc_path):
        with open(doc_path, 'r', encoding='utf-8') as f:
            try:
                doc_list = json.load(f)
            except Exception:
                doc_list = []
    else:
        doc_list = []
    # 检查是否已存在同名文件（仅当前用户）
    exist_id = None
    for item in doc_list:
        if item.get("filename") == file.filename and item.get("userId") == user_id:
            exist_id = item.get("id")
            break
    if exist_id is not None:
        doc_id = exist_id
    else:
        max_id = 0
        for item in doc_list:
            if item.get("userId") == user_id:
                try:
                    iid = int(item.get("id", 0))
                    if iid > max_id:
                        max_id = iid
                except Exception:
                    pass
        doc_id = max_id + 1
        # 自动读取内容
        ext = os.path.splitext(file.filename)[-1].lower()
        content = ""
        try:
            if ext == ".txt":
                with open(save_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            elif ext == ".docx":
                from docx import Document
                doc = Document(save_path)
                content = "\n".join([p.text for p in doc.paragraphs])
            elif ext == ".pptx":
                from pptx import Presentation
                prs = Presentation(save_path)
                slides = []
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            slides.append(shape.text)
                content = "\n".join(slides)
        except Exception:
            content = ""
        import datetime
        upload_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        doc_list.append({"id": doc_id, "filename": file.filename, "content": content, "upload_time": upload_time, "userId": user_id})
        with open(doc_path, 'w', encoding='utf-8') as f:
            json.dump(doc_list, f, ensure_ascii=False, indent=2)
    return {"id": doc_id, "filename": file.filename, "msg": "上传成功"}

@app.get("/api/doc/search")
async def search_docs(q: str = Query("", alias="q"), page: int = 1, size: int = 20, payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    doc_path = os.path.join(uploads_dir, 'doc.json')
    if not os.path.exists(doc_path):
        return {"total": 0, "data": []}
    with open(doc_path, 'r', encoding='utf-8') as f:
        doc_list = json.load(f)
    doc_list = [item for item in doc_list if item.get("userId") == user_id]
    if q:
        doc_list = [item for item in doc_list if q.lower() in item.get("filename", "").lower() or q.lower() in item.get("content", "").lower()]
    total = len(doc_list)
    start = (page - 1) * size
    end = start + size
    return {"total": total, "data": doc_list[start:end]}

@app.delete("/api/doc/{doc_id}")
async def delete_doc(doc_id: int = Path(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    doc_path = os.path.join(uploads_dir, 'doc.json')
    if not os.path.exists(doc_path):
        return {"code": 1, "msg": "文档不存在"}
    with open(doc_path, 'r', encoding='utf-8') as f:
        doc_list = json.load(f)
    
    # 检查权限：只能删除自己的文档
    doc_to_delete = None
    for item in doc_list:
        if str(item.get('id')) == str(doc_id):
            doc_to_delete = item
            break
    
    if not doc_to_delete:
        return {"code": 1, "msg": "文档不存在"}
    
    if doc_to_delete.get("userId") != user_id:
        return {"code": 1, "msg": "无权限删除此文档"}
    
    new_list = [item for item in doc_list if str(item.get('id')) != str(doc_id)]
    with open(doc_path, 'w', encoding='utf-8') as f:
        json.dump(new_list, f, ensure_ascii=False, indent=2)
    return {"code": 0, "msg": "删除成功"}

@app.put("/api/doc/{doc_id}")
async def edit_doc(doc_id: int = Path(...), data: dict = Body(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    doc_path = os.path.join(uploads_dir, 'doc.json')
    if not os.path.exists(doc_path):
        return {"code": 1, "msg": "文档不存在"}
    with open(doc_path, 'r', encoding='utf-8') as f:
        doc_list = json.load(f)
    updated = False
    for item in doc_list:
        if str(item.get('id')) == str(doc_id):
            # 检查权限：只能编辑自己的文档
            if item.get("userId") != user_id:
                return {"code": 1, "msg": "无权限编辑此文档"}
            item['content'] = data.get('html_content', item.get('content', ''))
            updated = True
            break
    if not updated:
        return {"code": 1, "msg": "文档不存在"}
    with open(doc_path, 'w', encoding='utf-8') as f:
        json.dump(doc_list, f, ensure_ascii=False, indent=2)
    return {"code": 0, "msg": "保存成功"}

@app.get("/api/doc/{doc_id}/download")
async def download_doc(doc_id: int = Path(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    doc_path = os.path.join(uploads_dir, 'doc.json')
    if not os.path.exists(doc_path):
        return {"code": 1, "msg": "文档不存在"}
    with open(doc_path, 'r', encoding='utf-8') as f:
        doc_list = json.load(f)
    filename = None
    doc_user_id = None
    for item in doc_list:
        if str(item.get('id')) == str(doc_id):
            filename = item.get('filename')
            doc_user_id = item.get('userId')
            break
    if not filename:
        return {"code": 1, "msg": "文档不存在"}
    
    # 检查权限：只能下载自己的文档
    if doc_user_id != user_id:
        return {"code": 1, "msg": "无权限下载此文档"}
    
    file_path = os.path.join(uploads_dir, filename)
    if not os.path.exists(file_path):
        return {"code": 1, "msg": "文件不存在"}
    return FileResponse(file_path, filename=filename)

@app.get('/api/doc/{doc_id}')
async def get_doc_detail(doc_id: int, payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    doc_path = os.path.join(uploads_dir, 'doc.json')
    if not os.path.exists(doc_path):
        return {"code": 1, "msg": "文档不存在"}
    with open(doc_path, 'r', encoding='utf-8') as f:
        doc_list = json.load(f)
    for item in doc_list:
        if str(item.get('id')) == str(doc_id):
            # 检查权限：只能查看自己的文档
            if item.get("userId") != user_id:
                return {"code": 1, "msg": "无权限访问此文档"}
            return {"code": 0, "content": item.get('content', '')}
    return {"code": 1, "msg": "未找到文档"}

# ========== 知识库相关接口，操作 knowledge.json ==========
@app.get("/api/knowledge")
async def get_knowledge(q: str = Query("", alias="q"), page: int = 1, size: int = 20, payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    kb_path = os.path.join(uploads_dir, 'knowledge.json')
    if not os.path.exists(kb_path):
        return {"total": 0, "data": []}
    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            kb_list = json.load(f)
    except Exception as e:
        print(f'知识库读取失败: {e}')
        kb_list = []
    kb_list = [item for item in kb_list if item.get("userId") == user_id]
    if q:
        kb_list = [item for item in kb_list if q.lower() in item.get("filename", "").lower() or q.lower() in item.get("content", "").lower()]
    total = len(kb_list)
    start = (page - 1) * size
    end = start + size
    return {"total": total, "data": kb_list[start:end]}

@app.get("/api/knowledge/detail")
async def knowledge_detail(id: int = Query(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    kb_path = os.path.join(uploads_dir, 'knowledge.json')
    if not os.path.exists(kb_path):
        return {"code": 1, "msg": "知识库不存在"}
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb_list = json.load(f)
    for item in kb_list:
        if str(item.get('docId', item.get('id'))) == str(id):
            # 检查文档所有权
            if item.get("userId") != user_id:
                return {"code": 1, "msg": "无权限访问此文档"}
            return {"code": 0, "data": item}
    return {"code": 1, "msg": "未找到文档"}

@app.post("/api/knowledge/edit")
async def knowledge_edit(data: dict = Body(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    doc_id = data.get("id")
    content = data.get("content")
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    kb_path = os.path.join(uploads_dir, 'knowledge.json')
    if not os.path.exists(kb_path):
        return {"code": 1, "msg": "知识库不存在"}
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb_list = json.load(f)
    updated = False
    for item in kb_list:
        if str(item.get('docId', item.get('id'))) == str(doc_id):
            # 检查文档所有权
            if item.get("userId") != user_id:
                return {"code": 1, "msg": "无权限编辑此文档"}
            item['content'] = content
            updated = True
            break
    if not updated:
        return {"code": 1, "msg": "文档不存在"}
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(kb_list, f, ensure_ascii=False, indent=2)
    return {"code": 0, "msg": "保存成功"}

@app.post("/api/knowledge/upload")
async def knowledge_upload(file: UploadFile = File(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    kb_path = os.path.join(uploads_dir, 'knowledge.json')
    os.makedirs(uploads_dir, exist_ok=True)
    # 检查是否已存在同名文档（仅当前用户）
    if os.path.exists(kb_path):
        with open(kb_path, 'r', encoding='utf-8') as f:
            try:
                kb_list = json.load(f)
            except Exception:
                kb_list = []
        for item in kb_list:
            if item.get("filename") == file.filename and item.get("userId") == user_id:
                return {"code": 1, "msg": "该文档已存在，禁止重复上传"}
    else:
        kb_list = []
    save_path = os.path.join(uploads_dir, file.filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # 自动读取内容
    ext = os.path.splitext(file.filename)[-1].lower()
    content = ""
    try:
        if ext == ".txt":
            with open(save_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        elif ext == ".docx":
            from docx import Document
            doc = Document(save_path)
            content = "\n".join([p.text for p in doc.paragraphs])
        elif ext == ".pptx":
            from pptx import Presentation
            prs = Presentation(save_path)
            slides = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        slides.append(shape.text)
            content = "\n".join(slides)
    except Exception:
        content = ""
    import datetime
    upload_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 生成自增id
    max_id = 0
    for item in kb_list:
        if item.get("userId") == user_id:
            try:
                iid = int(item.get("id", 0))
                if iid > max_id:
                    max_id = iid
            except Exception:
                pass
    doc_id = max_id + 1
    kb_list.append({
        "id": doc_id,
        "filename": file.filename,
        "content": content,
        "upload_time": upload_time,
        "userId": user_id
    })
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(kb_list, f, ensure_ascii=False, indent=2)
    return {"code": 0, "msg": "上传成功", "filename": file.filename, "id": doc_id}

@app.post("/api/knowledge/delete")
async def knowledge_delete(data: dict = Body(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    ids = data.get("ids")
    if not ids:
        return {"code": 1, "msg": "未指定要删除的文档id"}
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    kb_path = os.path.join(uploads_dir, 'knowledge.json')
    if not os.path.exists(kb_path):
        return {"code": 1, "msg": "知识库不存在"}
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb_list = json.load(f)
    
    # 检查权限：只能删除属于自己的文档
    ids_to_delete = [str(i) for i in ids]
    new_list = []
    deleted_count = 0
    
    for item in kb_list:
        item_id = str(item.get('docId', item.get('id')))
        if item_id in ids_to_delete:
            # 检查文档所有权
            if item.get("userId") == user_id:
                deleted_count += 1
                continue  # 跳过此项（即删除）
            else:
                # 无权限删除，保留此项
                new_list.append(item)
        else:
            # 不在删除列表中，保留此项
            new_list.append(item)
    
    if deleted_count == 0:
        return {"code": 1, "msg": "没有可删除的文档或无权限删除"}
    
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(new_list, f, ensure_ascii=False, indent=2)
    return {"code": 0, "msg": f"成功删除 {deleted_count} 个文档"}

@app.get("/api/knowledge/search")
async def knowledge_search(kw: str = Query(""), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    kb_path = os.path.join(uploads_dir, 'knowledge.json')
    if not os.path.exists(kb_path):
        return {"data": []}
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb_list = json.load(f)
    
    # 只搜索当前用户的文档
    user_docs = [item for item in kb_list if item.get("userId") == user_id]
    
    result = [
        item for item in user_docs
        if kw.lower() in (item.get("title", "") + item.get("filename", "")).lower()
        or kw.lower() in item.get("content", "").lower()
    ]
    return {"data": result}

@app.post("/api/knowledge/qa")
async def knowledge_qa(data: dict = Body(...), payload: dict = Depends(verify_token)):
    """知识库智能问答接口 - 增强版"""
    user_id = payload["userId"]
    question = data.get("question", "")
    knowledge_base = data.get("knowledge_base", "")
    conversation_id = data.get("conversation_id", "")
    history = data.get("history", [])
    
    if not question.strip():
        return {"code": 1, "msg": "问题不能为空"}
    
    # 生成会话ID（如果没有）
    if not conversation_id:
        import uuid
        conversation_id = str(uuid.uuid4())
    
    # 读取知识库文档
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    kb_path = os.path.join(uploads_dir, 'knowledge.json')
    
    if not os.path.exists(kb_path):
        return {"code": 0, "answer": "知识库为空，请先上传文档。"}
    
    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            kb_list = json.load(f)
    except Exception as e:
        return {"code": 1, "msg": f"读取知识库失败: {e}"}
    
    # 只使用当前用户的文档
    kb_list = [item for item in kb_list if item.get("userId") == user_id]
    
    # 过滤知识库
    if knowledge_base:
        kb_list = [item for item in kb_list if item.get("knowledge_base") == knowledge_base]
    
    # 智能搜索相关文档
    question_lower = question.lower()
    relevant_docs = []
    
    # 意图识别
    intent_keywords = {
        "规定": ["规定", "制度", "政策", "规则", "条例"],
        "申请": ["申请", "如何", "流程", "步骤", "办理"],
        "预约": ["预约", "预定", "安排", "订"],
        "技术": ["开发", "技术", "代码", "API", "接口"],
        "培训": ["培训", "学习", "教程", "指南"],
        "联系": ["联系", "电话", "邮箱", "地址"]
    }
    
    # 根据历史对话优化搜索
    context_keywords = []
    if history:
        for item in history[-3:]:  # 最近3次对话
            context_keywords.extend(item.get("question", "").lower().split())
    
    for doc in kb_list:
        content = doc.get("content", "")
        title = doc.get("title", doc.get("filename", ""))
        
        # 计算匹配度
        score = 0
        
        # 1. 标题匹配（权重最高）
        title_lower = title.lower()
        for word in question_lower.split():
            if len(word) > 1 and word in title_lower:
                score += 15
        
        # 2. 意图匹配
        for intent, keywords in intent_keywords.items():
            if any(kw in question_lower for kw in keywords):
                for kw in keywords:
                    if kw in content.lower():
                        score += 8
        
        # 3. 内容匹配
        content_lower = content.lower()
        question_words = [w for w in question_lower.split() if len(w) > 1]
        for word in question_words:
            if word in content_lower:
                # 计算词频和位置权重
                word_count = content_lower.count(word)
                score += word_count * 2
                
                # 如果词汇出现在开头，加分
                if content_lower.find(word) < 100:
                    score += 3
        
        # 4. 上下文匹配
        for context_word in context_keywords:
            if len(context_word) > 1 and context_word in content_lower:
                score += 1
        
        # 5. 语义相关性（简单实现）
        semantic_score = calculate_semantic_similarity(question, content)
        score += semantic_score
        
        if score > 0:
            relevant_docs.append({
                "doc": doc,
                "score": score,
                "title": title,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            })
    
    # 按相关度排序
    relevant_docs.sort(key=lambda x: x["score"], reverse=True)
    
    if not relevant_docs:
        return {
            "code": 0, 
            "answer": f"抱歉，在知识库中没有找到与『{question}』相关的信息。建议您：<br/>1. 尝试使用更简单的关键词<br/>2. 检查是否有相关文档已上传<br/>3. 联系管理员获取更多帮助"
        }
    
    # 生成智能回答
    answer_parts = []
    answer_parts.append(f"基于知识库搜索，为您找到以下相关信息：")
    
    # 取前3个最相关的文档
    top_docs = relevant_docs[:3]
    
    for i, item in enumerate(top_docs, 1):
        doc = item["doc"]
        title = item["title"]
        content_preview = item["content_preview"]
        
        answer_parts.append(f"<br/><br/><strong>{i}. {title}</strong>")
        
        # 智能提取相关段落
        content = doc.get("content", "")
        relevant_sentences = []
        
        for word in question_lower.split():
            if len(word) > 1:
                sentences = content.split('。')
                for sentence in sentences:
                    if word in sentence.lower() and len(sentence.strip()) > 10:
                        relevant_sentences.append(sentence.strip() + '。')
                        if len(relevant_sentences) >= 2:
                            break
        
        if relevant_sentences:
            answer_parts.append("<br/>".join(relevant_sentences[:2]))
        else:
            answer_parts.append(content_preview)
    
    # 添加建议
    if len(relevant_docs) > 3:
        answer_parts.append(f"<br/><br/><small>💡 提示：还找到了 {len(relevant_docs) - 3} 个相关文档，您可以在文档列表中查看更多详细信息。</small>")
    
    answer_parts.append("<br/><br/><small>📚 如需查看完整文档内容，请在文档列表中点击预览按钮。</small>")
    
    return {
        "code": 0,
        "answer": "".join(answer_parts),
        "relevant_count": len(relevant_docs),
        "docs": [{"id": item["doc"].get("id"), "title": item["title"]} for item in top_docs],
        "conversation_id": conversation_id,
        "intent": detect_intent(question),
        "confidence": calculate_confidence(relevant_docs)
    }

def calculate_semantic_similarity(question: str, content: str) -> float:
    """计算语义相似性（简单实现）"""
    question_words = set(question.lower().split())
    content_words = set(content.lower().split())
    
    if not question_words or not content_words:
        return 0
    
    intersection = question_words.intersection(content_words)
    union = question_words.union(content_words)
    
    # Jaccard相似度
    similarity = len(intersection) / len(union) if union else 0
    return similarity * 10  # 放大到0-10分

def detect_intent(question: str) -> str:
    """检测问题意图"""
    question_lower = question.lower()
    
    intent_patterns = {
        "询问规定": ["规定", "制度", "政策", "规则", "条例"],
        "申请流程": ["申请", "如何", "流程", "步骤", "办理"],
        "预约服务": ["预约", "预定", "安排", "订"],
        "技术咨询": ["开发", "技术", "代码", "API", "接口"],
        "培训学习": ["培训", "学习", "教程", "指南"],
        "联系方式": ["联系", "电话", "邮箱", "地址"],
        "一般查询": []
    }
    
    for intent, keywords in intent_patterns.items():
        if any(kw in question_lower for kw in keywords):
            return intent
    
    return "一般查询"

def calculate_confidence(relevant_docs: list) -> float:
    """计算回答置信度"""
    if not relevant_docs:
        return 0.0
    
    max_score = relevant_docs[0]["score"]
    doc_count = len(relevant_docs)
    
    # 基于最高分数和文档数量计算置信度
    confidence = min(max_score / 50, 1.0)  # 最高分数归一化
    
    # 文档数量加分
    if doc_count >= 3:
        confidence += 0.1
    elif doc_count >= 2:
        confidence += 0.05
    
    return round(min(confidence, 1.0), 2)

@app.delete("/api/knowledge/{doc_id}")
async def delete_knowledge(doc_id: int = Path(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    kb_path = os.path.join(uploads_dir, 'knowledge.json')
    if not os.path.exists(kb_path):
        return {"code": 1, "msg": "知识库不存在"}
    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            kb_list = json.load(f)
        
        # 检查文档是否存在以及权限
        doc_found = False
        doc_owned = False
        for item in kb_list:
            if str(item.get('docId', item.get('id'))) == str(doc_id):
                doc_found = True
                if item.get("userId") == user_id:
                    doc_owned = True
                break
        
        if not doc_found:
            return {"code": 1, "msg": "文档不存在"}
        
        if not doc_owned:
            return {"code": 1, "msg": "无权限删除此文档"}
        
        # 删除文档
        new_list = [item for item in kb_list if str(item.get('docId', item.get('id'))) != str(doc_id)]
        with open(kb_path, 'w', encoding='utf-8') as f:
            json.dump(new_list, f, ensure_ascii=False, indent=2)
        return {"code": 0, "msg": "删除成功"}
    except Exception as e:
        return {"code": 1, "msg": f"删除失败: {e}"}



# ========== 推送到知识库时，从 doc.json 读取内容 ==========
@app.post("/api/knowledge/import")
async def push_to_knowledge(data: dict = Body(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    doc_path = os.path.join(uploads_dir, 'doc.json')
    kb_path = os.path.join(uploads_dir, 'knowledge.json')
    
    doc_id = data.get("docId")
    title = data.get("title")
    doc_type = data.get("type", "文档")
    content = data.get("content", "")
    
    # 如果没有传content，尝试从doc.json读取
    if not content and doc_id and os.path.exists(doc_path):
        with open(doc_path, 'r', encoding='utf-8') as f:
            doc_list = json.load(f)
        for item in doc_list:
            if str(item.get('id')) == str(doc_id):
                content = item.get('content', '')
                break
    
    # 如果内容仍然为空，创建基本信息
    if not content or content.strip() == '' or content.strip() == '<p><br></p>':
        content = f"<h1>{title}</h1><p>此文档已推送到知识库，但原始内容为空。</p><p>文档类型：{doc_type}</p><p>推送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
    
    if not (doc_id and title):
        return {"code": 1, "msg": "缺少必要参数：文档ID或标题"}
    
    # 读取knowledge.json
    if os.path.exists(kb_path):
        with open(kb_path, 'r', encoding='utf-8') as f:
            try:
                kb_list = json.load(f)
            except Exception:
                kb_list = []
    else:
        kb_list = []
    
    # 查找是否已存在（同一用户的相同文档）
    found = False
    for item in kb_list:
        if (item.get("docId") == doc_id and item.get("userId") == user_id) or \
           (item.get("title") == title and item.get("userId") == user_id):
            # 更新现有记录
            item["docId"] = doc_id
            item["title"] = title
            item["filename"] = title
            item["content"] = content
            item["type"] = doc_type
            item["userId"] = user_id
            item["upload_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            found = True
            break
    
    if not found:
        # 生成新的知识库ID
        max_id = 0
        for item in kb_list:
            if item.get("userId") == user_id:
                try:
                    kb_id = int(item.get("id", 0))
                    if kb_id > max_id:
                        max_id = kb_id
                except Exception:
                    pass
        new_id = max_id + 1
        
        # 添加新记录
        kb_list.append({
            "id": new_id,
            "docId": doc_id,
            "title": title,
            "filename": title,
            "content": content,
            "type": doc_type,
            "userId": user_id,
            "upload_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # 保存到文件
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(kb_list, f, ensure_ascii=False, indent=2)
    
    action_text = "更新" if found else "添加"
    return {"code": 0, "msg": f"已成功{action_text}到知识库"}

@app.post("/auth/updateUserInfo")
async def update_user_info(data: UpdateUserInfoRequest, payload: dict = Depends(verify_token)):
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.id == int(payload["sub"])))  # sub转int
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(404, "用户不存在")
        user.real_name = data.realName
        user.nick_name = data.nickName
        await session.commit()
        return {"code": 0, "msg": "信息已更新"}

@app.post("/auth/updatePreferences")
async def update_preferences(data: UpdatePreferencesRequest, payload: dict = Depends(verify_token)):
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.id == int(payload["sub"])))  # sub转int
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(404, "用户不存在")
        user.theme = data.theme
        user.language = data.language
        await session.commit()
        return {"code": 0, "msg": "偏好设置已保存"}

# 创建会议接口
@app.post("/api/meetings/create")
async def create_meeting(data: MeetingCreateRequest, payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    
    # 查找主持人用户ID（如果host是用户名）
    host_user_id = 0
    if data.host:
        async with SessionLocal() as session:
            result = await session.execute(select(User).where(User.username == data.host))
            host_user = result.scalar_one_or_none()
            if host_user:
                host_user_id = host_user.id
    
    # 处理参会人列表
    participants_str = ",".join(map(str, data.participants)) if data.participants else ""
    
    async with MeetingSessionLocal() as session:
        new_meeting = Meeting(
            title=data.title,
            host=data.host,
            time=data.time,
            location=data.location,
            period=data.period,
            status=data.status,
            user_id=user_id,
            participants=participants_str,
            host_user_id=host_user_id or user_id  # 如果找不到主持人，默认为创建者
        )
        session.add(new_meeting)
        await session.commit()
        return {"code": 0, "msg": "会议已安排", "meetingId": new_meeting.id}

# 会议列表接口
@app.get("/api/meetings/list")
async def list_meetings(page: int = 1, pageSize: int = 10, payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    async with MeetingSessionLocal() as session:
        # 查询用户相关的会议：创建者、主持人、参会人
        result = await session.execute(select(Meeting))
        all_meetings = result.scalars().all()
        
        # 过滤出用户相关的会议
        user_meetings = []
        for meeting in all_meetings:
            is_related = False
            
            # 1. 是创建者
            if meeting.user_id == user_id:
                is_related = True
            
            # 2. 是主持人
            elif meeting.host_user_id == user_id:
                is_related = True
            
            # 3. 是参会人
            elif meeting.participants:
                participant_ids = [int(pid.strip()) for pid in meeting.participants.split(",") if pid.strip().isdigit()]
                if user_id in participant_ids:
                    is_related = True
            
            if is_related:
                user_meetings.append(meeting)
        
        # 分页处理
        total = len(user_meetings)
        start = (page - 1) * pageSize
        end = start + pageSize
        data = []
        
        for m in user_meetings[start:end]:
            # 解析参会人ID列表
            participant_ids = []
            if m.participants:
                participant_ids = [int(pid.strip()) for pid in m.participants.split(",") if pid.strip().isdigit()]
            
            data.append({
                "id": m.id,
                "title": m.title,
                "host": m.host,
                "time": m.time,
                "location": m.location,
                "period": m.period,
                "status": m.status,
                "participants": participant_ids,
                "host_user_id": m.host_user_id
            })
        
        return {"code": 0, "data": {"list": data, "total": total}}

# 会议室列表接口（静态返回）
@app.get("/api/meetings/rooms")
async def get_rooms():
    rooms = [
        {"id": 1, "name": "会议室A"},
        {"id": 2, "name": "会议室B"},
        {"id": 3, "name": "会议室C"},
        {"id": 4, "name": "3131"},
    ]
    return {"code": 0, "data": rooms}

# 会议冲突检测接口
@app.post("/api/meetings/check-conflict")
async def check_conflict(data: dict = Body(...)):
    time = data.get("time")
    location = data.get("location")
    async with MeetingSessionLocal() as session:
        result = await session.execute(select(Meeting).where(Meeting.time == time, Meeting.location == location))
        conflict = result.scalar_one_or_none() is not None
        return {"code": 0, "data": {"conflict": conflict}}

# 编辑会议接口
@app.post("/api/meetings/edit")
async def edit_meeting(data: dict = Body(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    meeting_id = data.get("id")
    if not meeting_id:
        return {"code": 1, "msg": "缺少会议ID"}
    
    async with MeetingSessionLocal() as session:
        result = await session.execute(select(Meeting).where(Meeting.id == meeting_id))
        meeting = result.scalar_one_or_none()
        if not meeting:
            return {"code": 1, "msg": "会议不存在"}
        
        # 检查权限：创建者、主持人或参会人才能编辑
        has_permission = False
        
        # 1. 是创建者
        if meeting.user_id == user_id:
            has_permission = True
        
        # 2. 是主持人
        elif meeting.host_user_id == user_id:
            has_permission = True
        
        # 3. 是参会人
        elif meeting.participants:
            participant_ids = [int(pid.strip()) for pid in meeting.participants.split(",") if pid.strip().isdigit()]
            if user_id in participant_ids:
                has_permission = True
        
        if not has_permission:
            return {"code": 1, "msg": "无权限编辑此会议"}
        
        # 更新字段
        meeting.title = data.get("title", meeting.title)
        meeting.host = data.get("host", meeting.host)
        meeting.time = data.get("time", meeting.time)
        meeting.location = data.get("location", meeting.location)
        meeting.period = data.get("period", meeting.period)
        meeting.status = data.get("status", meeting.status)
        
        # 处理参会人更新
        if "participants" in data:
            participants = data.get("participants", [])
            if isinstance(participants, list):
                meeting.participants = ",".join(map(str, participants))
            else:
                meeting.participants = str(participants)
        
        # 更新主持人用户ID
        if data.get("host"):
            async with SessionLocal() as user_session:
                result = await user_session.execute(select(User).where(User.username == data.get("host")))
                host_user = result.scalar_one_or_none()
                if host_user:
                    meeting.host_user_id = host_user.id
        
        await session.commit()
        return {"code": 0, "msg": "保存成功"}

@app.post("/api/assistant/chat")
async def assistant_chat(data: dict = Body(...)):
    user_message = data.get("message", "")
    QWEN_API_KEY = "sk-751689471abb4aaf9d7169c86884b1a0"
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    # 强制中文回答
    prompt = f"请用简体中文回答：{user_message}"
    payload = {
        "model": "qwen-turbo",
        "input": {
            "prompt": prompt
        },
        "parameters": {
            "result_format": "message"
        }
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        result = resp.json()
        # 通义千问返回格式
        reply = result.get("output", {}).get("text")
        if not reply:
            # 兼容新版API返回格式
            choices = result.get("output", {}).get("choices")
            if choices and isinstance(choices, list):
                reply = choices[0].get("message", {}).get("content")
        if reply:
            return {"code": 0, "data": {"reply": reply}}
        else:
            return {"code": 1, "msg": result.get("message", "通义千问API调用失败")}
    except Exception as e:
        return {"code": 1, "msg": f"通义千问API异常: {str(e)}"}

@app.get("/api/assistant/recommend")
async def assistant_recommend(query: str = ""):
    # 这里可以根据query做智能推荐，先返回模拟数据
    return [
        {"id": 1, "title": "如何高效开会", "type": "知识"},
        {"id": 2, "title": "本周工作总结模板", "type": "模板"},
        {"id": 3, "title": "会议纪要写作技巧", "type": "技巧"}
    ]

@app.get("/api/schedule/today")
async def schedule_today(payload: dict = Depends(verify_token)):
    # 这里返回模拟数据，后续可接数据库
    try:
        return {
            "code": 0,
            "data": [
                {"id": 1, "title": "产品需求会议", "time": "09:30"},
                {"id": 2, "title": "整理会议内容", "time": "15:30"},
                {"id": 3, "title": "明天工作计划", "time": "18:30"}
            ]
        }
    except Exception as e:
        print(f"[schedule_today] 错误: {e}")
        return {"code": 1, "msg": "获取日程失败", "data": []}

@app.post("/api/user/upload-avatar")
async def upload_avatar(file: UploadFile = File(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    ext = os.path.splitext(file.filename)[-1]
    save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'avatar')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f"{user_id}{ext}")
    with open(save_path, "wb") as f:
        f.write(await file.read())
    avatar_url = f"/uploads/avatar/{user_id}{ext}"
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.avatar = avatar_url
            await session.commit()
    return {"code": 0, "msg": "上传成功", "data": {"avatar": avatar_url}}

@app.post("/api/user/generate-avatar")
async def generate_new_avatar(payload: dict = Depends(verify_token)):
    """为当前用户生成新的随机头像"""
    user_id = payload["userId"]
    
    try:
        async with SessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return {"code": 1, "msg": "用户不存在"}
            
            # 生成新的随机头像
            avatar_url = generate_random_avatar()
            
            # 如果头像是外部URL，尝试下载并保存到本地
            if avatar_url.startswith('https://'):
                try:
                    local_avatar = save_avatar_from_url(avatar_url, user_id)
                    user.avatar = local_avatar
                except Exception as e:
                    print(f"下载头像失败，使用默认头像: {e}")
                    user.avatar = "avatar/default.svg"
            else:
                user.avatar = avatar_url
            
            await session.commit()
            
            return {
                "code": 0, 
                "msg": "头像生成成功", 
                "data": {"avatar": user.avatar}
            }
    except Exception as e:
        return {"code": 1, "msg": f"生成头像失败: {str(e)}"}

@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...), payload: dict = Depends(verify_token)):
    """上传图片接口，用于聊天发送图片"""
    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"]:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    user_id = payload.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="用户ID不能为空")
    
    # 文件大小限制 5MB
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过5MB")
    
    # 创建目录
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'images')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = int(time.time())
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"chat_{user_id}_{timestamp}{file_ext}"
    file_path = os.path.join(uploads_dir, filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"code": 0, "data": {"url": f"/uploads/images/{filename}"}}

@app.post("/api/assistant/upload")
async def assistant_upload_file(file: UploadFile = File(...), payload: dict = Depends(verify_token)):
    """智能助手上传接口，支持图片和附件"""
    
    user_id = payload.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="用户ID不能为空")
    
    # 文件大小限制 10MB
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过10MB")
    
    # 检查文件类型
    file_type = "file"
    if file.content_type:
        if file.content_type.startswith("image/"):
            file_type = "image"
        elif file.content_type in ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            file_type = "document"
        elif file.content_type in ["application/zip", "application/x-rar-compressed", "application/x-tar", "application/gzip"]:
            file_type = "archive"
        elif file.content_type.startswith("text/"):
            file_type = "text"
    
    # 创建目录
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'assistant')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = int(time.time())
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    filename = f"assistant_{user_id}_{timestamp}{file_ext}"
    file_path = os.path.join(uploads_dir, filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {
        "code": 0, 
        "data": {
            "url": f"/uploads/assistant/{filename}",
            "type": file_type,
            "original_name": file.filename,
            "size": file.size or 0
        }
    }

class TodayTaskModel(BaseModel):
    content: str
    time: str = ""
    completed: bool = False
    date: str = ""
    type: str = "bg-primary"
    endDate: str = ""  # 新增，前端传 endDate

@app.get("/api/today-tasks")
async def get_today_tasks(payload: dict = Depends(verify_token)):
    try:
        async with SessionLocal() as session:
            result = await session.execute(select(TodayTask))
            tasks = result.scalars().all()
            tasks = [dict(id=t.id, content=t.content, time=t.time, completed=t.completed, date=t.date, type=getattr(t, "type", "bg-primary"), endDate=getattr(t, "end_date", "")) for t in tasks]
        return {"code": 0, "tasks": tasks}
    except Exception as e:
        print(f"[get_today_tasks] 错误: {e}")
        return {"code": 1, "msg": "获取任务失败", "tasks": []}

@app.post("/api/today-tasks")
async def add_today_task(task: TodayTaskModel, payload: dict = Depends(verify_token)):
    try:
        import datetime
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../users.db'))
        print(f"[add_today_task] 数据库绝对路径: {db_path}")
        print(f"[add_today_task] 收到任务: {task}")
        async with SessionLocal() as session:
            new_task = TodayTask(
                content=task.content,
                time=task.time or datetime.datetime.now().strftime('%H:%M'),
                completed=task.completed,
                date=task.date or datetime.datetime.now().strftime('%Y-%m-%d'),
                type=task.type or "bg-primary",
                end_date=task.endDate or ""
            )
            session.add(new_task)
            await session.commit()
            await session.refresh(new_task)
            print(f"[add_today_task] 已写入数据库: {new_task}")
            return {"code": 0, "msg": "添加成功", "task": dict(id=new_task.id, content=new_task.content, time=new_task.time, completed=new_task.completed, date=new_task.date, type=new_task.type, endDate=new_task.end_date)}
    except Exception as e:
        print(f"[add_today_task] 错误: {e}")
        return {"code": 1, "msg": "添加任务失败"}

@app.delete("/api/today-tasks/{task_id}")
async def delete_today_task(task_id: int, payload: dict = Depends(verify_token)):
    try:
        print(f"[delete_today_task] 请求删除任务ID: {task_id}")
        async with SessionLocal() as session:
            result = await session.execute(select(TodayTask).where(TodayTask.id == task_id))
            task = result.scalar_one_or_none()
            if not task:
                print(f"[delete_today_task] 未找到任务: {task_id}")
                return JSONResponse({"code": 1, "msg": "任务不存在"}, status_code=status.HTTP_404_NOT_FOUND)
            await session.delete(task)
            await session.commit()
            print(f"[delete_today_task] 已删除任务: {task_id}")
            return {"code": 0, "msg": "删除成功"}
    except Exception as e:
        print(f"[delete_today_task] 错误: {e}")
        return {"code": 1, "msg": "删除任务失败"}

@app.put("/api/today-tasks/{task_id}")
async def update_today_task(task_id: int = Path(...), task: TodayTaskModel = Body(...), payload: dict = Depends(verify_token)):
    try:
        async with SessionLocal() as session:
            result = await session.execute(select(TodayTask).where(TodayTask.id == task_id))
            db_task = result.scalar_one_or_none()
            if not db_task:
                return JSONResponse({"code": 1, "msg": "任务不存在"}, status_code=status.HTTP_404_NOT_FOUND)
            db_task.content = task.content
            db_task.time = task.time
            db_task.completed = task.completed
            db_task.date = task.date
            db_task.type = task.type or "bg-primary"
            db_task.end_date = task.endDate or ""
            await session.commit()
            await session.refresh(db_task)
            return {"code": 0, "msg": "更新成功", "task": {
                "id": db_task.id,
                "content": db_task.content,
                "time": db_task.time,
                "completed": db_task.completed,
                "date": db_task.date,
                "type": db_task.type,
                "endDate": db_task.end_date
            }}
    except Exception as e:
        print(f"[update_today_task] 错误: {e}")
        return {"code": 1, "msg": "更新任务失败"}

app.mount("/uploads", StaticFiles(directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')), name="uploads")

@app.post("/api/ai/summary")
async def ai_summary(data: dict = Body(...)):
    content = data.get("content", "")
    summary_type = data.get("type", "general")  # general, meeting_minutes
    meeting_title = data.get("meetingTitle", "")
    
    if not content:
        return {"code": 1, "msg": "内容不能为空"}
    
    # 根据类型构建不同的提示词
    if summary_type == "meeting_minutes":
        prompt = f"""请根据以下会议录音转录内容，生成一份专业的会议纪要：

会议主题：{meeting_title or '未指定'}
录音转录内容：
{content}

请按以下格式生成会议纪要：
1. 会议基本信息
2. 会议要点
3. 决议事项
4. 待办事项
5. 下次会议安排（如有）

要求：
- 提取关键信息和决策点
- 语言简洁明了
- 结构化呈现
- 重点突出行动项"""
    else:
        prompt = f"请对以下内容进行简明扼要的中文摘要：\n{content}"
    
    # 尝试使用通义千问API
    try:
        api_key = "sk-751689471abb4aaf9d7169c86884b1a0"
        api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen-turbo",
            "input": {"prompt": prompt},
            "parameters": {"result_format": "message"}
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(api_url, headers=headers, json=payload, timeout=30)
            result = resp.json()
            # 解析通义千问返回的摘要内容
            summary = result.get("output", {}).get("text", "")
            if summary:
                print("通义千问返回：", result)
                return {"code": 0, "summary": summary}
    except Exception as e:
        print(f"通义千问API调用失败: {e}")
    
    # 如果API调用失败，使用本地摘要算法
    try:
        if summary_type == "meeting_minutes":
            summary = generate_meeting_minutes(content, meeting_title)
        else:
            summary = generate_local_summary(content)
        return {"code": 0, "summary": summary}
    except Exception as e:
        print(f"本地摘要生成失败: {e}")
        return {"code": 1, "msg": "摘要生成失败"}

def generate_local_summary(content: str) -> str:
    """
    本地智能摘要生成算法
    """
    import re
    
    # 移除HTML标签
    clean_content = re.sub(r'<[^>]+>', '', content)
    
    # 分句
    sentences = re.split(r'[。！？；\n]', clean_content)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
    
    if not sentences:
        return "文档内容过短，无法生成摘要。"
    
    # 关键词提取和重要句子识别
    keywords = ['项目', '系统', '功能', '技术', '应用', '创新', '管理', '服务', '用户', '数据', 
                '智能', '平台', '解决方案', '优化', '提升', '实现', '支持', '开发', '设计', '架构']
    
    # 句子评分
    sentence_scores = []
    for sentence in sentences:
        score = 0
        # 关键词得分
        for keyword in keywords:
            if keyword in sentence:
                score += 1
        # 位置得分（开头和结尾的句子得分更高）
        if sentences.index(sentence) < len(sentences) * 0.3:
            score += 2
        elif sentences.index(sentence) > len(sentences) * 0.7:
            score += 1
        # 长度得分
        if 10 <= len(sentence) <= 50:
            score += 1
        
        sentence_scores.append((sentence, score))
    
    # 排序并选择重要句子
    sentence_scores.sort(key=lambda x: x[1], reverse=True)
    
    # 选择前3-5个重要句子
    top_sentences = sentence_scores[:min(5, len(sentence_scores))]
    
    # 生成摘要
    summary_parts = []
    
    # 添加标题或主题
    if '标题' in clean_content or 'h1' in content.lower():
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE)
        if title_match:
            summary_parts.append(f"📋 主题：{title_match.group(1)}")
    
    # 添加核心内容
    summary_parts.append("📝 核心内容：")
    for sentence, score in top_sentences:
        if sentence and len(sentence) > 8:
            summary_parts.append(f"• {sentence}")
            if len(summary_parts) >= 8:  # 控制摘要长度
                break
    
    # 添加统计信息
    word_count = len(clean_content)
    summary_parts.append(f"\n📊 文档统计：约{word_count}字，{len(sentences)}句话")
    
    # 如果内容包含特定结构，添加结构化信息
    if '<table' in content:
        summary_parts.append("📋 包含表格数据")
    if '<ul' in content or '<ol' in content:
        summary_parts.append("📋 包含列表信息")
    if '<h2' in content or '<h3' in content:
        summary_parts.append("📋 包含章节结构")
    
    summary = "\n".join(summary_parts)
    
    # 如果摘要太短，添加更多信息
    if len(summary) < 100:
        summary += f"\n\n💡 这是一个关于{extract_main_topic(clean_content)}的文档。"
    
    return summary

def extract_main_topic(content: str) -> str:
    """提取文档主题"""
    topics = {
        '项目': ['项目', '系统', '平台', '软件', '应用'],
        '管理': ['管理', '计划', '安排', '组织', '协调'],
        '技术': ['技术', '开发', '编程', '代码', '算法'],
        '教育': ['教育', '学习', '培训', '课程', '教学'],
        '政策': ['政策', '规定', '制度', '法规', '文件'],
        '报告': ['报告', '总结', '分析', '统计', '调研']
    }
    
    for topic, keywords in topics.items():
        if any(keyword in content for keyword in keywords):
            return topic
    
    return "综合内容"

def generate_meeting_minutes(content: str, meeting_title: str = "") -> str:
    """
    生成会议纪要
    """
    import re
    from datetime import datetime
    
    # 移除HTML标签
    clean_content = re.sub(r'<[^>]+>', '', content)
    
    # 分句
    sentences = re.split(r'[。！？；\n]', clean_content)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
    
    if not sentences:
        return "录音内容过短，无法生成有效纪要。"
    
    # 关键词分类
    keywords = {
        '决策': ['决定', '确定', '同意', '批准', '通过', '决议'],
        '计划': ['计划', '安排', '准备', '预定', '打算'],
        '问题': ['问题', '困难', '挑战', '风险', '障碍'],
        '建议': ['建议', '提议', '推荐', '意见', '看法'],
        '行动': ['执行', '实施', '完成', '负责', '跟进'],
        '时间': ['今天', '明天', '下周', '下个月', '截止', '期限'],
        '人员': ['负责人', '团队', '部门', '同事', '参与者']
    }
    
    # 分类句子
    categorized = {category: [] for category in keywords.keys()}
    other_content = []
    
    for sentence in sentences:
        classified = False
        for category, words in keywords.items():
            if any(word in sentence for word in words):
                categorized[category].append(sentence)
                classified = True
                break
        if not classified:
            other_content.append(sentence)
    
    # 生成纪要
    minutes_parts = []
    
    # 头部信息
    minutes_parts.append(f"<h2>会议纪要</h2>")
    minutes_parts.append(f"<p><strong>会议主题：</strong>{meeting_title or '未指定'}</p>")
    minutes_parts.append(f"<p><strong>纪要生成时间：</strong>{datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>")
    minutes_parts.append("<hr>")
    
    # 主要内容
    if categorized['决策']:
        minutes_parts.append("<h3>📋 会议决议</h3>")
        for i, item in enumerate(categorized['决策'][:5], 1):
            minutes_parts.append(f"<p>{i}. {item}</p>")
    
    if categorized['计划']:
        minutes_parts.append("<h3>📅 工作计划</h3>")
        for i, item in enumerate(categorized['计划'][:5], 1):
            minutes_parts.append(f"<p>{i}. {item}</p>")
    
    if categorized['问题']:
        minutes_parts.append("<h3>⚠️ 讨论问题</h3>")
        for i, item in enumerate(categorized['问题'][:3], 1):
            minutes_parts.append(f"<p>{i}. {item}</p>")
    
    if categorized['建议']:
        minutes_parts.append("<h3>💡 建议意见</h3>")
        for i, item in enumerate(categorized['建议'][:3], 1):
            minutes_parts.append(f"<p>{i}. {item}</p>")
    
    if categorized['行动']:
        minutes_parts.append("<h3>✅ 行动事项</h3>")
        for i, item in enumerate(categorized['行动'][:5], 1):
            minutes_parts.append(f"<p>{i}. {item}</p>")
    
    # 其他重要内容
    if other_content:
        minutes_parts.append("<h3>📝 其他内容</h3>")
        important_others = [s for s in other_content if len(s) > 15][:3]
        for i, item in enumerate(important_others, 1):
            minutes_parts.append(f"<p>{i}. {item}</p>")
    
    # 如果没有足够的结构化内容，提供基本摘要
    if len([item for items in categorized.values() for item in items]) < 3:
        minutes_parts.append("<h3>📄 会议摘要</h3>")
        # 选择最重要的句子
        important_sentences = sorted(sentences, key=len, reverse=True)[:5]
        for i, sentence in enumerate(important_sentences, 1):
            minutes_parts.append(f"<p>{i}. {sentence}</p>")
    
    # 添加统计信息
    minutes_parts.append("<hr>")
    minutes_parts.append(f"<p><small>📊 会议时长：约{len(clean_content)//200}分钟 | 转录字数：{len(clean_content)}字</small></p>")
    
    return "\n".join(minutes_parts)

# 新增会议附件上传接口
ATTACHMENTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'attachments.json')

def load_attachments():
    if not os.path.exists(ATTACHMENTS_PATH):
        return []
    with open(ATTACHMENTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_attachments(data):
    with open(ATTACHMENTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.post("/api/meetings/upload")
async def upload_meeting_attachment(meetingId: int = Form(...), file: UploadFile = File(...), payload: dict = Depends(verify_token)):
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'meetings')
    os.makedirs(uploads_dir, exist_ok=True)
    save_path = os.path.join(uploads_dir, f"{meetingId}_{file.filename}")
    with open(save_path, "wb") as f:
        f.write(await file.read())
    url = f"/uploads/meetings/{meetingId}_{file.filename}"
    # 记录到 attachments.json
    attachments = load_attachments()
    attachments.append({
        "meetingId": meetingId,
        "filename": file.filename,
        "url": url,
        "upload_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    save_attachments(attachments)
    return {"code": 0, "msg": "上传成功", "filename": file.filename, "meetingId": meetingId, "url": url}

@app.get("/api/meetings/{meeting_id}/attachments")
async def get_meeting_attachments(meeting_id: int):
    attachments = load_attachments()
    return [a for a in attachments if int(a["meetingId"]) == int(meeting_id)]

@app.get("/api/meetings/approval-history")
async def approval_history(id: int):
    # 目前没有审批历史，返回空列表即可
    return []

@app.post("/api/reset-password")
async def reset_password(data: ResetPasswordRequest):
    # 校验验证码
    real_code = r.get(f"captcha:{data.contact}")
    if not real_code:
        return {"code": 1, "msg": "验证码已过期或不存在"}
    if data.captcha != real_code:
        return {"code": 2, "msg": "验证码错误"}
    r.delete(f"captcha:{data.contact}")

    # 修改密码
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.contact == data.contact))
        user = result.scalar_one_or_none()
        if not user:
            return {"code": 3, "msg": "用户不存在"}
        import bcrypt
        user.password = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
        await session.commit()
        return {"code": 0, "msg": "密码重置成功"}

# ========== WebSocket 单聊消息推送与存储 =============
import json as _json
active_connections = {}

@app.websocket("/ws/chat/user")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user_id = None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("userId") or payload.get("sub")
        if not user_id:
            print(f"[WS] token解析失败，payload={payload}")
            await websocket.close(code=1008)
            return
        user_id = int(user_id)
        await websocket.accept()
        active_connections[user_id] = websocket
        while True:
            try:
                data = await websocket.receive_text()
                try:
                    msg_obj = _json.loads(data)
                except Exception as e:
                    print(f"[WS] JSON解析失败: {e}, data={data}")
                    continue
                # 存储消息到 chat-db.json
                try:
                    save_message_to_json(msg_obj)
                except Exception as e:
                    print(f"[WS] 消息存储异常: {e}, msg={msg_obj}")
                # 推送给目标用户和自己
                to_user_id = msg_obj.get("to_user_id")
                # 推送给自己
                if user_id in active_connections:
                    try:
                        await active_connections[user_id].send_text(_json.dumps(msg_obj))
                    except Exception as e:
                        print(f"[WS] 推送给自己异常: {e}")
                # 推送给对方（如果不是自己）
                if to_user_id in active_connections and to_user_id != user_id:
                    try:
                        await active_connections[to_user_id].send_text(_json.dumps(msg_obj))
                    except Exception as e:
                        print(f"[WS] 推送给对方异常: {e}")
            except WebSocketDisconnect:
                print(f"[WS] 用户 {user_id} 断开连接")
                break
            except Exception as e:
                print(f"[WS] 消息处理异常: {e}")
    finally:
        if user_id and user_id in active_connections:
            del active_connections[user_id]


@app.post("/api/message/send")
async def send_message(data: dict = Body(...), payload: dict = Depends(verify_token)):
    """发送消息API接口（非WebSocket方式）"""
    from_user_id = payload["userId"]
    to_user_id = data.get("to_user_id")
    content = data.get("content")
    msg_type = data.get("type", "text")
    
    if not to_user_id or not content:
        return {"code": 1, "msg": "缺少必要参数"}
    
    msg_obj = {
        "from_user_id": from_user_id,
        "to_user_id": to_user_id,
        "content": content,
        "type": msg_type,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        save_message_to_json(msg_obj)
        return {"code": 0, "msg": "发送成功"}
    except Exception as e:
        return {"code": 1, "msg": f"发送失败: {str(e)}"}

@app.post("/api/message/read")
async def mark_message_read(data: dict = Body(...), payload: dict = Depends(verify_token)):
    """标记消息为已读"""
    msg_id = data.get("msg_id")
    if not msg_id:
        return {"code": 1, "msg": "缺少消息ID"}
    
    # 从chat-db.json读取并更新消息状态
    db_path = os.path.join(os.path.dirname(__file__), "chat-db.json")
    
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            db = _json.load(f)
            
        # 查找并更新消息
        for room_key, messages in db.get("rooms", {}).items():
            for msg in messages:
                if msg.get("id") == msg_id:
                    msg["is_read"] = 1
                    
                    # 保存更新后的数据
                    with open(db_path, "w", encoding="utf-8") as f:
                        _json.dump(db, f, ensure_ascii=False, indent=2)
                    
                    return {"code": 0, "msg": "标记成功"}
    
    return {"code": 1, "msg": "消息不存在"}

@app.get("/api/message/unread_counts")
async def get_unread_counts(payload: dict = Depends(verify_token)):
    """获取个人聊天未读消息计数"""
    user_id = payload["userId"]
    
    # 从chat-db.json读取所有消息
    db_path = os.path.join(os.path.dirname(__file__), "chat-db.json")
    unread_counts = {}
    
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            db = _json.load(f)
            
        # 统计每个发送者的未读消息数
        for room_key, messages in db.get("rooms", {}).items():
            for msg in messages:
                # 如果是发给当前用户的消息，且未读（没有is_read字段或is_read为0）
                # 支持字符串和数字类型的用户ID比较
                to_user_id = msg.get("to_user_id")
                if (to_user_id == user_id or str(to_user_id) == str(user_id)) and msg.get("is_read", 0) == 0:
                    from_user_id = msg.get("from_user_id")
                    if from_user_id:
                        # 确保键为字符串类型
                        key = str(from_user_id)
                        unread_counts[key] = unread_counts.get(key, 0) + 1
    
    print(f"用户 {user_id} 的未读消息计数: {unread_counts}")  # 调试信息
    return {"code": 0, "data": unread_counts}

@app.get("/api/group/unread_counts")
async def get_group_unread_counts(payload: dict = Depends(verify_token)):
    """获取群聊未读消息计数"""
    user_id = payload["userId"]
    
    # 这里应该从群聊消息数据库读取，暂时返回空
    # 实际实现需要根据群聊消息的存储方式来统计
    unread_counts = {}
    
    return {"code": 0, "data": unread_counts}

def save_message_to_json(msg_obj):
    import os
    db_path = os.path.join(os.path.dirname(__file__), "chat-db.json")
    if not isinstance(msg_obj, dict):
        raise ValueError("msg_obj 不是 dict")
    for k in ["from_user_id", "to_user_id", "content", "time"]:
        if k not in msg_obj:
            raise ValueError(f"msg_obj 缺少字段: {k}")
    
    # 为消息添加id和is_read字段
    msg_obj["id"] = int(datetime.now().timestamp() * 1000)  # 使用时间戳作为ID
    msg_obj["is_read"] = 0  # 默认未读
    
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            db = _json.load(f)
    else:
        db = {"rooms": {}}
    # 只在 user_{from_user_id} 存储消息，避免重复
    room_key = f"user_{msg_obj['from_user_id']}"
    db["rooms"].setdefault(room_key, []).append(msg_obj)
    with open(db_path, "w", encoding="utf-8") as f:
        _json.dump(db, f, ensure_ascii=False, indent=2)
    
    # 删除自动创建消息通知的功能

# 删除了 create_message_notification 函数

# 删除了 get_user_info_by_id 函数

# 删除所有通知相关API

@app.get("/api/users/list")
async def get_users_list(payload: dict = Depends(verify_token)):
    """获取用户列表，用于选择参会人"""
    async with SessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "realName": user.real_name or user.username,
                "nickName": user.nick_name or user.username,
                "department": user.department,
                "avatar": user.avatar,
                "contact": user.contact
            })
        
        return {"code": 0, "data": user_list}

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(payload: dict = Depends(verify_token)):
    """获取工作台统计数据"""
    try:
        # 获取文档统计
        doc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'doc.json')
        doc_total = 0
        if os.path.exists(doc_path):
            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                    doc_total = len(docs)
            except:
                doc_total = 0
        
        # 获取用户统计
        async with SessionLocal() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            total_users = len(users)
            
            # 获取今天的会议数量
            today_str = datetime.now().strftime('%Y-%m-%d')
            result = await session.execute(
                select(func.count(Meeting.id)).where(
                    Meeting.time.like(f"{today_str}%")
                )
            )
            today_meetings = result.scalar() or 0
            
            # 获取即将开始的会议（今天且未来时间）
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            result = await session.execute(
                select(func.count(Meeting.id)).where(
                    Meeting.time >= current_time,
                    Meeting.time.like(f"{today_str}%")
                )
            )
            upcoming_meetings = result.scalar() or 0
            
            # 获取已完成会议（今天且过去时间）
            result = await session.execute(
                select(func.count(Meeting.id)).where(
                    Meeting.time < current_time,
                    Meeting.time.like(f"{today_str}%")
                )
            )
            completed_meetings = result.scalar() or 0
        
        # 生成基于真实数据的统计
        base_visits = 5000
        base_views = 4500
        
        stats = {
            "cardStats": [
                {
                    "des": "总访问次数",
                    "icon": "&#xe721;",
                    "num": base_visits + (total_users * 150) + (doc_total * 25),
                    "change": "+15%"
                },
                {
                    "des": "在线访客数",
                    "icon": "&#xe724;",
                    "num": min(total_users * 3, 300),
                    "change": "+8%"
                },
                {
                    "des": "点击量",
                    "icon": "&#xe7aa;",
                    "num": base_views + (doc_total * 40) + (today_meetings * 25),
                    "change": "-5%"
                },
                {
                    "des": "新用户",
                    "icon": "&#xe82a;",
                    "num": max(total_users - 5, 0),
                    "change": "+25%"
                }
            ],
            "docStats": {
                "total": doc_total,
                "todayProcessed": min(max(doc_total // 30, 5), 60),
                "pending": min(max(doc_total // 60, 2), 15)
            },
            "scheduleStats": {
                "todaySchedule": today_meetings,
                "upcoming": upcoming_meetings,
                "completed": completed_meetings
            }
        }
        
        return {"code": 0, "data": stats}
        
    except Exception as e:
        print(f"获取工作台统计数据失败: {e}")
        # 返回默认数据
        return {"code": 0, "data": {
            "cardStats": [
                {"des": "总访问次数", "icon": "&#xe721;", "num": 5000, "change": "+15%"},
                {"des": "在线访客数", "icon": "&#xe724;", "num": 50, "change": "+8%"},
                {"des": "点击量", "icon": "&#xe7aa;", "num": 4500, "change": "-5%"},
                {"des": "新用户", "icon": "&#xe82a;", "num": 30, "change": "+25%"}
            ],
            "docStats": {"total": 0, "todayProcessed": 0, "pending": 0},
            "scheduleStats": {"todaySchedule": 0, "upcoming": 0, "completed": 0}
        }}

@app.get("/api/dashboard/chart-data")
async def get_dashboard_chart_data(payload: dict = Depends(verify_token)):
    """获取工作台图表数据"""
    try:
        # 生成过去9个月的业务数据
        chart_data = []
        months = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月']
        
        # 基于当前数据生成模拟的月度数据
        async with SessionLocal() as session:
            result = await session.execute(select(func.count(Meeting.id)))
            meeting_count = result.scalar() or 0
            
            result = await session.execute(select(func.count(User.id)))
            user_count = result.scalar() or 0
            
        # 计算基础值
        base_value = max(meeting_count * 8 + user_count * 3, 60)
        
        # 生成有趋势的月度数据
        for i, month in enumerate(months):
            # 模拟业务增长趋势
            trend_factor = 1 + (i * 0.1)  # 每月增长10%
            seasonal_factor = 1 + (0.3 * (i % 3) / 3)  # 季节性波动
            random_factor = 1 + (random.randint(-20, 30) / 100)  # 随机波动
            
            value = int(base_value * trend_factor * seasonal_factor * random_factor)
            chart_data.append({
                "month": month,
                "value": max(value, 30)  # 确保最小值为30
            })
        
        return {"code": 0, "data": chart_data}
        
    except Exception as e:
        print(f"获取图表数据失败: {e}")
        # 返回默认数据
        return {"code": 0, "data": [
            {"month": "一月", "value": 80},
            {"month": "二月", "value": 120},
            {"month": "三月", "value": 150},
            {"month": "四月", "value": 100},
            {"month": "五月", "value": 90},
            {"month": "六月", "value": 130},
            {"month": "七月", "value": 140},
            {"month": "八月", "value": 170},
            {"month": "九月", "value": 160}
        ]}

@app.get("/api/dashboard/department")
async def get_department_info(payload: dict = Depends(verify_token)):
    """获取部门信息"""
    try:
        user_id = payload.get('sub')
        
        # 获取当前用户信息
        async with SessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                return {"code": 404, "msg": "用户不存在"}
            
            # 获取同部门的其他用户
            result = await session.execute(
                select(User).where(
                    User.department == user.department,
                    User.id != user_id
                )
            )
            department_users = result.scalars().all()
            
        # 根据部门生成相应的部门信息
        department_configs = {
            "人事部": {
                "responsibilities": [
                    "负责公司招聘、员工入职与离职管理，制定招聘计划，筛选简历，组织面试",
                    "组织员工培训与绩效考核，建立培训体系，制定KPI指标，定期评估员工表现",
                    "管理员工档案与薪酬福利，维护人事档案，制定薪酬方案，处理社保公积金",
                    "推动企业文化建设与员工关系维护，组织团建活动，处理员工投诉，营造良好工作氛围"
                ],
                "email": "hr@company.com",
                "phone": "010-12345678",
                "announcement": "本月员工生日会将于25日举行，请大家准时参加！"
            },
            "技术部": {
                "responsibilities": [
                    "负责系统开发与技术架构设计，制定技术方案，编写核心代码，确保系统稳定性",
                    "维护服务器运行与数据安全，监控系统性能，备份重要数据，防范安全风险",
                    "推动技术创新与产品优化，研究新技术应用，优化用户体验，提升产品竞争力",
                    "提供技术支持与培训服务，解决技术问题，培训其他部门员工，编写技术文档"
                ],
                "email": "tech@company.com",
                "phone": "010-12345679",
                "announcement": "新版系统将于下周上线，请各位做好测试准备！"
            },
            "市场部": {
                "responsibilities": [
                    "制定市场营销策略与推广方案，分析市场趋势，制定营销计划，执行推广活动",
                    "管理客户关系与商务合作，维护重要客户，拓展新客户，建立合作伙伴关系",
                    "分析市场趋势与竞争对手，收集市场信息，分析竞品动态，提供决策建议",
                    "组织品牌宣传与活动策划，提升品牌知名度，策划营销活动，管理品牌形象"
                ],
                "email": "marketing@company.com",
                "phone": "010-12345680",
                "announcement": "Q4季度市场推广活动即将启动，欢迎大家踊跃参与！"
            },
            "财务部": {
                "responsibilities": [
                    "负责公司财务核算与报表编制，处理日常账务，编制财务报表，确保财务数据准确",
                    "管理资金流动与成本控制，制定资金计划，控制成本支出，优化资金使用效率",
                    "处理税务申报与合规事务，按时申报纳税，处理税务问题，确保合规经营",
                    "提供财务分析与决策支持，分析财务数据，提供决策建议，支持业务发展"
                ],
                "email": "finance@company.com",
                "phone": "010-12345681",
                "announcement": "月度财务报表提交截止日期为本月30日，请各部门配合！"
            },
            "运营部": {
                "responsibilities": [
                    "负责产品运营与用户增长，制定运营策略，提升用户活跃度，实现用户增长目标",
                    "管理内容运营与社区建设，策划内容活动，维护用户社区，提升用户粘性",
                    "分析运营数据与效果评估，监控关键指标，分析运营效果，优化运营策略",
                    "协调各部门资源与项目推进，统筹项目进度，协调资源分配，确保项目顺利执行"
                ],
                "email": "operations@company.com",
                "phone": "010-12345682",
                "announcement": "本月运营数据表现良好，用户活跃度提升15%，继续保持！"
            },
            "销售部": {
                "responsibilities": [
                    "制定销售策略与目标管理，制定销售计划，设定销售目标，跟踪销售进度",
                    "开发新客户与维护老客户，拓展销售渠道，维护客户关系，提升客户满意度",
                    "管理销售团队与业绩考核，培训销售技能，考核销售业绩，激励团队士气",
                    "分析销售数据与市场反馈，收集客户反馈，分析销售趋势，优化销售策略"
                ],
                "email": "sales@company.com",
                "phone": "010-12345683",
                "announcement": "本月销售目标完成率95%，距离目标还有5%，大家加油！"
            },
            "客服部": {
                "responsibilities": [
                    "提供客户服务与问题解决，处理客户咨询，解决客户问题，提升客户满意度",
                    "管理客户投诉与纠纷处理，及时响应投诉，妥善处理纠纷，维护公司形象",
                    "收集客户反馈与需求分析，整理客户建议，分析客户需求，为产品改进提供依据",
                    "建立客户档案与关系维护，建立客户数据库，定期回访客户，维护长期合作关系"
                ],
                "email": "service@company.com",
                "phone": "010-12345684",
                "announcement": "客户满意度调查即将开始，请各位同事积极配合！"
            },
            "法务部": {
                "responsibilities": [
                    "处理法律事务与合同审查，审查业务合同，处理法律纠纷，提供法律咨询",
                    "管理知识产权与商标注册，保护公司知识产权，处理商标专利事务，防范法律风险",
                    "制定合规制度与风险控制，建立合规体系，识别法律风险，制定防范措施",
                    "提供法律培训与合规指导，培训员工法律知识，指导业务合规，提升法律意识"
                ],
                "email": "legal@company.com",
                "phone": "010-12345685",
                "announcement": "新版合同模板已更新，请各部门使用最新版本！"
            }
        }
        
        # 获取当前部门配置
        dept_config = department_configs.get(user.department, department_configs["人事部"])
        
        # 确定部门领导和成员
        leader = user.real_name or user.username
        members = []
        
        for dept_user in department_users:
            display_name = dept_user.real_name or dept_user.username
            members.append(display_name)
        
        # 如果有多个用户，第一个作为领导，其他作为成员
        if len(members) > 0:
            if len(members) == 1:
                # 如果只有一个其他用户，当前用户作为领导
                pass
            else:
                # 如果有多个用户，第一个作为领导，当前用户和其他作为成员
                leader = members[0]
                members = [user.real_name or user.username] + members[1:]
        
        department_info = {
            "name": user.department,
            "responsibilities": dept_config["responsibilities"],
            "leader": leader,
            "members": members,
            "email": dept_config["email"],
            "phone": dept_config["phone"],
            "announcement": dept_config["announcement"]
        }
        
        return {"code": 0, "data": department_info}
        
    except Exception as e:
        print(f"获取部门信息失败: {e}")
        # 返回默认数据
        return {"code": 0, "data": {
            "name": "人事部",
            "responsibilities": [
                "负责公司招聘、员工入职与离职管理",
                "组织员工培训与绩效考核",
                "管理员工档案与薪酬福利",
                "推动企业文化建设与员工关系维护"
            ],
            "leader": "张三",
            "members": ["李四", "王五"],
            "email": "hr@company.com",
            "phone": "010-12345678",
            "announcement": "本月员工生日会将于25日举行，请大家准时参加！"
        }}

# ========== 录音历史相关接口 ==========
@app.post("/api/recordings/upload")
async def upload_recording(file: UploadFile = File(...), data: str = Form(...), payload: dict = Depends(verify_token)):
    """上传录音文件并保存记录"""
    user_id = payload["userId"]
    
    try:
        # 解析表单数据
        import json
        recording_data = json.loads(data)
        
        # 创建录音文件存储目录
        recordings_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'recordings')
        os.makedirs(recordings_dir, exist_ok=True)
        
        # 生成唯一文件名
        import uuid
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.webm'
        unique_filename = f"recording_{user_id}_{int(time.time())}_{str(uuid.uuid4())[:8]}{file_extension}"
        file_path = os.path.join(recordings_dir, unique_filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 保存录音记录到数据库
        async with SessionLocal() as session:
            new_recording = RecordingHistory(
                meeting_id=recording_data.get("meeting_id"),
                meeting_title=recording_data.get("meeting_title", ""),
                user_id=user_id,
                filename=file.filename or unique_filename,
                file_path=f"recordings/{unique_filename}",
                transcript=recording_data.get("transcript", ""),
                minutes=recording_data.get("minutes", ""),
                duration=recording_data.get("duration", 0),
                file_size=file_size,
                created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                status="completed"
            )
            session.add(new_recording)
            await session.commit()
            await session.refresh(new_recording)
            
            return {
                "code": 0, 
                "msg": "录音上传成功", 
                "data": {
                    "id": new_recording.id,
                    "filename": new_recording.filename,
                    "file_path": new_recording.file_path
                }
            }
    
    except Exception as e:
        print(f"录音上传失败: {e}")
        return {"code": 1, "msg": f"录音上传失败: {str(e)}"}

@app.get("/api/recordings/history")
async def get_recording_history(page: int = 1, pageSize: int = 10, keyword: str = "", payload: dict = Depends(verify_token)):
    """获取录音历史列表"""
    user_id = payload["userId"]
    
    try:
        async with SessionLocal() as session:
            # 构建查询
            query = select(RecordingHistory).where(RecordingHistory.user_id == user_id)
            
            # 关键词搜索
            if keyword:
                query = query.where(
                    RecordingHistory.meeting_title.contains(keyword) |
                    RecordingHistory.filename.contains(keyword)
                )
            
            # 按创建时间倒序
            query = query.order_by(RecordingHistory.id.desc())
            
            # 获取总数
            count_result = await session.execute(select(func.count(RecordingHistory.id)).where(RecordingHistory.user_id == user_id))
            total = count_result.scalar()
            
            # 分页
            offset = (page - 1) * pageSize
            query = query.offset(offset).limit(pageSize)
            
            result = await session.execute(query)
            recordings = result.scalars().all()
            
            data = []
            for recording in recordings:
                data.append({
                    "id": recording.id,
                    "meeting_id": recording.meeting_id,
                    "meeting_title": recording.meeting_title,
                    "filename": recording.filename,
                    "file_path": recording.file_path,
                    "transcript": recording.transcript[:200] + "..." if len(recording.transcript) > 200 else recording.transcript,
                    "has_minutes": bool(recording.minutes),
                    "duration": recording.duration,
                    "file_size": recording.file_size,
                    "created_at": recording.created_at,
                    "status": recording.status
                })
            
            return {
                "code": 0,
                "data": {
                    "list": data,
                    "total": total,
                    "page": page,
                    "pageSize": pageSize
                }
            }
    
    except Exception as e:
        print(f"获取录音历史失败: {e}")
        return {"code": 1, "msg": f"获取录音历史失败: {str(e)}"}

@app.get("/api/recordings/{recording_id}")
async def get_recording_detail(recording_id: int, payload: dict = Depends(verify_token)):
    """获取录音详情"""
    user_id = payload["userId"]
    
    try:
        async with SessionLocal() as session:
            result = await session.execute(
                select(RecordingHistory).where(
                    RecordingHistory.id == recording_id,
                    RecordingHistory.user_id == user_id
                )
            )
            recording = result.scalar_one_or_none()
            
            if not recording:
                return {"code": 1, "msg": "录音记录不存在"}
            
            return {
                "code": 0,
                "data": {
                    "id": recording.id,
                    "meeting_id": recording.meeting_id,
                    "meeting_title": recording.meeting_title,
                    "filename": recording.filename,
                    "file_path": recording.file_path,
                    "transcript": recording.transcript,
                    "minutes": recording.minutes,
                    "duration": recording.duration,
                    "file_size": recording.file_size,
                    "created_at": recording.created_at,
                    "status": recording.status
                }
            }
    
    except Exception as e:
        print(f"获取录音详情失败: {e}")
        return {"code": 1, "msg": f"获取录音详情失败: {str(e)}"}

@app.put("/api/recordings/{recording_id}")
async def update_recording(recording_id: int, data: RecordingUpdateRequest, payload: dict = Depends(verify_token)):
    """更新录音记录"""
    user_id = payload["userId"]
    
    try:
        async with SessionLocal() as session:
            result = await session.execute(
                select(RecordingHistory).where(
                    RecordingHistory.id == recording_id,
                    RecordingHistory.user_id == user_id
                )
            )
            recording = result.scalar_one_or_none()
            
            if not recording:
                return {"code": 1, "msg": "录音记录不存在"}
            
            # 更新字段
            if data.transcript:
                recording.transcript = data.transcript
            if data.minutes:
                recording.minutes = data.minutes
            
            await session.commit()
            
            return {"code": 0, "msg": "更新成功"}
    
    except Exception as e:
        print(f"更新录音记录失败: {e}")
        return {"code": 1, "msg": f"更新录音记录失败: {str(e)}"}

@app.delete("/api/recordings/{recording_id}")
async def delete_recording(recording_id: int, payload: dict = Depends(verify_token)):
    """删除录音记录"""
    user_id = payload["userId"]
    
    try:
        async with SessionLocal() as session:
            result = await session.execute(
                select(RecordingHistory).where(
                    RecordingHistory.id == recording_id,
                    RecordingHistory.user_id == user_id
                )
            )
            recording = result.scalar_one_or_none()
            
            if not recording:
                return {"code": 1, "msg": "录音记录不存在"}
            
            # 删除文件
            file_full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', recording.file_path)
            if os.path.exists(file_full_path):
                os.remove(file_full_path)
            
            # 删除数据库记录
            await session.delete(recording)
            await session.commit()
            
            return {"code": 0, "msg": "删除成功"}
    
    except Exception as e:
        print(f"删除录音记录失败: {e}")
        return {"code": 1, "msg": f"删除录音记录失败: {str(e)}"}

@app.get("/api/recordings/{recording_id}/download")
async def download_recording(recording_id: int, payload: dict = Depends(verify_token)):
    """下载录音文件"""
    user_id = payload["userId"]
    
    try:
        async with SessionLocal() as session:
            result = await session.execute(
                select(RecordingHistory).where(
                    RecordingHistory.id == recording_id,
                    RecordingHistory.user_id == user_id
                )
            )
            recording = result.scalar_one_or_none()
            
            if not recording:
                return {"code": 1, "msg": "录音记录不存在"}
            
            file_full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', recording.file_path)
            
            if not os.path.exists(file_full_path):
                return {"code": 1, "msg": "录音文件不存在"}
            
            return FileResponse(
                file_full_path,
                filename=recording.filename,
                media_type='audio/webm'
            )
    
    except Exception as e:
        print(f"下载录音文件失败: {e}")
        return {"code": 1, "msg": f"下载录音文件失败: {str(e)}"}

# 注册路由
app.include_router(search.router, prefix="/api")
app.include_router(contact.router, prefix="/api")  
app.include_router(group.router, prefix="/api")
app.include_router(message.router, prefix="/api")
app.include_router(assistant_upload.router, prefix="/api/assistant")

# 添加静态文件服务支持
app.mount("/uploads", StaticFiles(directory="backend/uploads"), name="uploads")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3007)































