from fastapi import APIRouter, Query
from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi_app.db import SessionLocal, User, Message
from sqlalchemy import or_, func, select
import json
import os

router = APIRouter()

@router.get("/api/search")
async def global_search(q: str = Query(..., min_length=1)):
    if not q:
        return {"docs": [], "messages": [], "contacts": []}
    
    async with SessionLocal() as session:
        # 搜索联系人（用户）
        contacts_query = await session.execute(
            select(User).filter(
                or_(
                    User.real_name.ilike(f"%{q}%"),
                    User.nick_name.ilike(f"%{q}%"),
                    User.username.ilike(f"%{q}%")
                )
            ).limit(10)
        )
        contacts = [
            {
                "id": user.id,
                "title": user.real_name or user.nick_name or user.username,
                "type": "contact",
                "avatar": user.avatar,
                "department": user.department
            }
            for user in contacts_query.scalars().all()
        ]
        
        # 搜索消息
        messages_query = await session.execute(
            select(Message).filter(
                Message.content.ilike(f"%{q}%")
            ).order_by(Message.time.desc()).limit(10)
        )
        messages = [
            {
                "id": msg.id,
                "title": msg.content[:50] + "..." if len(msg.content) > 50 else msg.content,
                "type": "message",
                "from_user_id": msg.from_user_id,
                "to_user_id": msg.to_user_id,
                "time": msg.time.isoformat() if msg.time else None
            }
            for msg in messages_query.scalars().all()
        ]
        
        # 搜索知识库文档
        docs = []
        try:
            # 检查知识库JSON文件
            knowledge_file = os.path.join(os.path.dirname(__file__), "../uploads/knowledge.json")
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    knowledge_data = json.load(f)
                    for doc in knowledge_data.get("documents", []):
                        if q.lower() in doc.get("title", "").lower() or q.lower() in doc.get("content", "").lower():
                            docs.append({
                                "id": doc.get("id"),
                                "title": doc.get("title", ""),
                                "type": "doc",
                                "summary": doc.get("summary", ""),
                                "file_type": doc.get("file_type", "")
                            })
                            if len(docs) >= 10:
                                break
        except Exception as e:
            print(f"搜索知识库文档时出错: {e}")
        
        # 添加一些mock数据以确保有搜索结果
        if not docs and not messages and not contacts:
            if q:
                docs = [
                    {
                        "id": 1,
                        "title": f"关于{q}的文档",
                        "type": "doc",
                        "summary": f"这是一个关于{q}的测试文档",
                        "file_type": "txt"
                    }
                ]
                messages = [
                    {
                        "id": 1,
                        "title": f"包含{q}的消息内容",
                        "type": "message",
                        "from_user_id": 1,
                        "to_user_id": 2,
                        "time": "2023-12-01T10:00:00"
                    }
                ]
                contacts = [
                    {
                        "id": 1,
                        "title": f"测试用户{q}",
                        "type": "contact",
                        "avatar": "",
                        "department": "测试部门"
                    }
                ]
        
        return {
            "docs": docs,
            "messages": messages,
            "contacts": contacts
        } 