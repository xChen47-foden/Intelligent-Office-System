#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能助手图片上传接口
"""
import os
import uuid
import hashlib
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from PIL import Image
import aiofiles
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi_app.auth_utils import verify_token

router = APIRouter()

# 上传目录配置
UPLOAD_DIR = "backend/uploads/assistant"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_filename(original_filename: str) -> str:
    """生成唯一的文件名"""
    ext = original_filename.rsplit('.', 1)[1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"assistant_{timestamp}_{unique_id}.{ext}"

def validate_image(file_path: str) -> bool:
    """验证图片文件是否有效"""
    try:
        with Image.open(file_path) as img:
            # 验证图片格式
            img.verify()
            return True
    except Exception:
        return False

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token)
):
    """
    上传图片
    """
    try:
        # 验证文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="未选择文件")
        
        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="不支持的文件类型")
        
        # 读取文件内容
        content = await file.read()
        
        # 验证文件大小
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件大小超过5MB限制")
        
        # 创建上传目录
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # 生成唯一文件名
        filename = generate_filename(file.filename)
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # 验证图片有效性
        if not validate_image(file_path):
            os.remove(file_path)  # 删除无效文件
            raise HTTPException(status_code=400, detail="无效的图片文件")
        
        # 计算文件hash
        file_hash = hashlib.md5(content).hexdigest()
        
        # 返回成功响应
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "filename": filename,
                    "original_name": file.filename,
                    "url": f"/uploads/assistant/{filename}",
                    "size": len(content),
                    "hash": file_hash,
                    "upload_time": datetime.now().isoformat()
                },
                "message": "图片上传成功"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 清理可能创建的文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get("/images/{filename}")
async def get_image(filename: str):
    """
    获取上传的图片
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="图片不存在")
        
        # 返回图片文件
        from fastapi.responses import FileResponse
        return FileResponse(
            file_path,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=3600"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")

@router.delete("/images/{filename}")
async def delete_image(
    filename: str,
    current_user: dict = Depends(verify_token)
):
    """
    删除上传的图片
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="图片不存在")
        
        # 删除文件
        os.remove(file_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "图片删除成功"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除图片失败: {str(e)}") 