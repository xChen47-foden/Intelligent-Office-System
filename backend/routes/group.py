from fastapi import APIRouter, Body, Query, Depends
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi_app.auth_utils import verify_token
from fastapi_app.db import Group, GroupMember, SessionLocal, User
from sqlalchemy import select
import json
from datetime import datetime

router = APIRouter()

GROUP_CHAT_DB = os.path.join(os.path.dirname(__file__), "../fastapi_app/group-chat-db.json")

def save_group_message(group_id, msg_obj):
    if os.path.exists(GROUP_CHAT_DB):
        with open(GROUP_CHAT_DB, "r", encoding="utf-8") as f:
            db = json.load(f)
    else:
        db = {}
    db.setdefault(str(group_id), []).append(msg_obj)
    with open(GROUP_CHAT_DB, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def load_group_messages(group_id):
    if os.path.exists(GROUP_CHAT_DB):
        with open(GROUP_CHAT_DB, "r", encoding="utf-8") as f:
            db = json.load(f)
        return db.get(str(group_id), [])
    return []

@router.get("/api/group/list")
async def get_groups(payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    async with SessionLocal() as session:
        result = await session.execute(
            select(GroupMember).where(GroupMember.user_id == user_id)
        )
        group_ids = [gm.group_id for gm in result.scalars().all()]
        groups = []
        for gid in group_ids:
            g = await session.get(Group, gid)
            if g:
                groups.append({"id": g.id, "name": g.name})
        return {"code": 0, "data": groups}

@router.post("/api/group/create")
async def create_group(data: dict = Body(...), payload: dict = Depends(verify_token)):
    name = data.get("name")
    members = data.get("members", [])
    owner_id = payload["userId"]
    async with SessionLocal() as session:
        group = Group(name=name, owner_id=owner_id)
        session.add(group)
        await session.flush()  # 获取group.id
        for uid in set(members + [owner_id]):
            session.add(GroupMember(group_id=group.id, user_id=uid))
        await session.commit()
    return {"code": 0, "msg": "群聊创建成功"}

@router.post("/api/group/delete")
async def delete_group(data: dict = Body(...), payload: dict = Depends(verify_token)):
    group_id = data.get("group_id")
    if not group_id:
        return {"code": 1, "msg": "缺少 group_id"}
    async with SessionLocal() as session:
        # 删除群成员
        await session.execute(
            GroupMember.__table__.delete().where(GroupMember.group_id == group_id)
        )
        # 删除群聊本身
        await session.execute(
            Group.__table__.delete().where(Group.id == group_id)
        )
        await session.commit()
    return {"code": 0, "msg": "群聊删除成功"}

@router.post("/api/group/send_message")
async def send_group_message(data: dict = Body(...), payload: dict = Depends(verify_token)):
    group_id = data.get("group_id")
    content = data.get("content")
    msg_type = data.get("type", "text")  # 支持消息类型
    file_name = data.get("file_name")  # 文件名
    file_size = data.get("file_size")  # 文件大小
    user_id = payload["userId"]
    # 查找用户信息
    async with SessionLocal() as session:
        user = await session.get(User, user_id)
        sender_name = user.real_name or user.username if user else ""
        avatar = user.avatar if user else ""
    msg_obj = {
        "group_id": group_id,
        "user_id": user_id,
        "content": content,
        "type": msg_type,
        "sender_name": sender_name,
        "avatar": avatar,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # 如果是文件类型，添加文件元数据
    if msg_type == "file":
        if file_name:
            msg_obj["file_name"] = file_name
        if file_size is not None:
            msg_obj["file_size"] = file_size
    save_group_message(group_id, msg_obj)
    return {"code": 0, "msg": "发送成功"} 

@router.get("/api/group/messages")
async def get_group_messages(group_id: int = Query(...), payload: dict = Depends(verify_token)):
    msgs = load_group_messages(group_id)
    return {"code": 0, "data": msgs} 