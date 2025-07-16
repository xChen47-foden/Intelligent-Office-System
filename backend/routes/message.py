from fastapi import APIRouter, Query, Depends
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi_app.auth_utils import verify_token
import json

router = APIRouter()

@router.get("/api/message/history")
async def get_message_history(to_user_id: int = Query(...), payload: dict = Depends(verify_token)):
    user_id = payload["userId"]
    db_path = os.path.join(os.path.dirname(__file__), "../fastapi_app/chat-db.json")
    if not os.path.exists(db_path):
        return {"code": 0, "data": []}
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)
    # 取出当前用户和对方的所有消息
    msgs = []
    for room_key in [f"user_{user_id}", f"user_{to_user_id}"]:
        msgs.extend(db.get("rooms", {}).get(room_key, []))
    # 只保留双方互发的消息
    msgs = [m for m in msgs if (m.get("from_user_id") == user_id and m.get("to_user_id") == to_user_id) or (m.get("from_user_id") == to_user_id and m.get("to_user_id") == user_id)]
    # 按时间排序
    msgs.sort(key=lambda m: m.get("time", ""))
    return {"code": 0, "data": msgs} 