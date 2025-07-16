from fastapi import APIRouter, Body, Query, Depends
from sqlalchemy.future import select
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi_app.db import User, SessionLocal, Friend, FriendRequest, Message
from fastapi_app.auth_utils import verify_token
import json
from sqlalchemy import or_

router = APIRouter()

@router.get("/api/contact/list")
async def get_contacts(payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    async with SessionLocal() as session:
        # 查找所有你已添加的好友
        result = await session.execute(
            select(Friend).where(Friend.user_id == user_id)
        )
        friends = result.scalars().all()
        friend_ids = [f.friend_id for f in friends]
        if not friend_ids:
            return {"code": 0, "data": []}
        result = await session.execute(
            select(User).where(User.id.in_(friend_ids))
        )
        users = result.scalars().all()
        return {"code": 0, "data": [
            {"id": u.id, "username": u.username, "real_name": u.real_name, "avatar": u.avatar} for u in users
        ]}

@router.post("/api/contact/request")
async def send_request(data: dict = Body(...), payload: dict = Depends(verify_token)):
    to_user_id = data.get("to_user_id")
    msg_obj = {
        "type": "request",
        "from_user_id": payload["userId"],
        "to_user_id": to_user_id
    }
    for uid in [payload["userId"], to_user_id]:
        if uid in active_connections:
            await active_connections[uid].send_text(json.dumps(msg_obj))
    return {"code": 0, "msg": "好友申请已发送"}

@router.post("/api/contact/add")
async def add_contact(data: dict = Body(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    friend_id = data.get("contact_user_id")
    if not friend_id or friend_id == user_id:
        return {"code": 1, "msg": "参数错误"}
    async with SessionLocal() as session:
        # 检查是否已是好友
        result = await session.execute(
            select(Friend).where(Friend.user_id == user_id, Friend.friend_id == friend_id)
        )
        if result.scalar_one_or_none():
            return {"code": 1, "msg": "已添加该联系人"}
        # 检查是否已发起过申请且未处理
        result = await session.execute(
            select(FriendRequest).where(FriendRequest.from_user_id == user_id, FriendRequest.to_user_id == friend_id, FriendRequest.status == "pending")
        )
        if result.scalar_one_or_none():
            return {"code": 1, "msg": "已发起过申请，请等待对方处理"}
        # 写入好友申请
        session.add(FriendRequest(from_user_id=user_id, to_user_id=friend_id, status="pending"))
        await session.commit()
    return {"code": 0, "msg": "好友申请已发送"}

@router.get("/api/contact/requests")
async def get_friend_requests(payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    async with SessionLocal() as session:
        result = await session.execute(
            select(FriendRequest, User).join(User, FriendRequest.from_user_id == User.id)
            .where(FriendRequest.to_user_id == user_id, FriendRequest.status == "pending")
        )
        reqs = result.all()
    return {"code": 0, "data": [
            {"request_id": r.FriendRequest.id, "from_user_id": r.FriendRequest.from_user_id, "from_user_name": r.User.username, "from_user_real_name": r.User.real_name, "avatar": r.User.avatar}
            for r in reqs
    ]}

@router.get("/api/contact/my_requests")
async def get_my_friend_requests(payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    async with SessionLocal() as session:
        result = await session.execute(
            select(FriendRequest, User).join(User, FriendRequest.to_user_id == User.id)
            .where(FriendRequest.from_user_id == user_id, FriendRequest.status == "pending")
        )
        reqs = result.all()
    return {"code": 0, "data": [
            {"request_id": r.FriendRequest.id, "to_user_id": r.FriendRequest.to_user_id, "to_user_name": r.User.username, "to_user_real_name": r.User.real_name, "avatar": r.User.avatar}
            for r in reqs
    ]}

@router.post("/api/contact/handle_request")
async def handle_friend_request(data: dict = Body(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    request_id = data.get("request_id")
    action = data.get("action")  # accept/reject
    if action not in ["accept", "reject"]:
        return {"code": 1, "msg": "参数错误"}
    async with SessionLocal() as session:
        req = await session.get(FriendRequest, request_id)
        if not req or req.to_user_id != user_id or req.status != "pending":
            return {"code": 1, "msg": "无效的申请"}
        if action == "accept":
            # 双向加好友
            session.add(Friend(user_id=req.from_user_id, friend_id=req.to_user_id))
            session.add(Friend(user_id=req.to_user_id, friend_id=req.from_user_id))
            req.status = "accepted"
            # 新增：插入一条消息
            # 获取申请人用户名
            from_user = await session.get(User, req.from_user_id)
            to_user = await session.get(User, req.to_user_id)
            if from_user and to_user:
                msg = Message(
                    from_user_id=req.from_user_id,
                    to_user_id=req.to_user_id,
                    content=f"{from_user.username} 关注了你"
                )
                session.add(msg)
        else:
            req.status = "rejected"
        await session.commit()
    return {"code": 0, "msg": "操作成功"}

@router.post("/api/contact/delete")
async def delete_contact(data: dict = Body(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    friend_id = data.get("id")
    async with SessionLocal() as session:
        result = await session.execute(
            select(Friend).where(Friend.user_id == user_id, Friend.friend_id == friend_id)
        )
        friend = result.scalar_one_or_none()
        if not friend:
            return {"code": 1, "msg": "联系人不存在"}
        await session.delete(friend)
        await session.commit()
    return {"code": 0, "msg": "删除成功"}

@router.get("/api/user/available")
async def available_users(q: str = Query(""), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    async with SessionLocal() as session:
        stmt = select(User).where(
            (User.username.contains(q) | User.real_name.contains(q)) & (User.id != user_id)
        )
        result = await session.execute(stmt)
        users = result.scalars().all()
        return {"code": 0, "data": [
            {"id": u.id, "username": u.username, "realName": u.real_name, "avatar": u.avatar} for u in users
        ]}

@router.get("/api/contact/my")
async def my_contacts(payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    async with SessionLocal() as session:
        result = await session.execute(
            select(Friend).where(Friend.user_id == user_id)
        )
        friends = result.scalars().all()
        return {"code": 0, "data": [f.friend_id for f in friends]} 

@router.get("/api/contact/available")
async def get_available_contacts(payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    print("当前user_id:", user_id)
    async with SessionLocal() as session:
        result = await session.execute(select(Friend).where(Friend.user_id == user_id))
        friends = result.scalars().all()
        friend_ids = [f.friend_id for f in friends]
        print("已添加好友id:", friend_ids)
        result = await session.execute(
            select(User).where(User.id != user_id, ~User.id.in_(friend_ids))
        )
        users = result.scalars().all()
        print("可添加用户:", [u.id for u in users])
        return {"code": 0, "data": [
            {"id": u.id, "username": u.username, "real_name": u.real_name, "avatar": u.avatar} for u in users
        ]} 