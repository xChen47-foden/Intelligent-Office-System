# 数据库模型定义文件 - 定义用户、好友、群组等数据模型
import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Boolean

# 数据库配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, '../users.db')}"
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# ========== 数据模型定义 ==========
# 用户模型
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    contact = Column(String, unique=True, index=True)
    password = Column(String)
    real_name = Column(String, default="")
    nick_name = Column(String, default="")
    theme = Column(String, default="auto")
    language = Column(String, default="zh")
    avatar = Column(String, default="")
    department = Column(String, default="")

# 好友关系模型
class Friend(Base):
    __tablename__ = "friends"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    friend_id = Column(Integer, ForeignKey("users.id"))

# 群组模型
class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

# 群组成员模型
class GroupMember(Base):
    __tablename__ = "group_members"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

# 好友请求模型
class FriendRequest(Base):
    __tablename__ = "friend_requests"
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"))
    to_user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")  # pending/accepted/rejected
    created_at = Column(DateTime, default=func.now())

# 今日任务模型
class TodayTask(Base):
    __tablename__ = "today_tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # 用户ID，用于数据隔离
    content = Column(String)
    time = Column(String, default="待定")
    completed = Column(Boolean, default=False)
    date = Column(String)
    type = Column(String, default="bg-primary")
    end_date = Column(String, default="")  # 新增字段，支持任务结束日期 

# 消息模型
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, nullable=False)
    to_user_id = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    time = Column(DateTime, nullable=False, default=func.now()) 