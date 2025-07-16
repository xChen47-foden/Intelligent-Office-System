#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端打包脚本
使用 PyInstaller 将 FastAPI 应用打包成可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """执行命令"""
    print(f"执行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"命令执行失败: {result.stderr}")
        return False
    print(f"命令执行成功: {result.stdout}")
    return True

def install_dependencies():
    """安装打包依赖"""
    print("正在安装打包依赖...")
    dependencies = [
        "pyinstaller>=5.0",
        "fastapi",
        "uvicorn[standard]",
        "sqlalchemy",
        "aiosqlite",
        "redis",
        "bcrypt",
        "pyjwt",
        "python-multipart",
        "httpx",
        "requests",
        "python-docx",
        "python-pptx",
        "openpyxl"
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep}"):
            print(f"安装依赖 {dep} 失败")
            return False
    
    return True

def create_spec_file():
    """创建 PyInstaller 规格文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 分析主模块
a = Analysis(
    ['fastapi_app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('fastapi_app/*.py', 'fastapi_app'),
        ('routes/*.py', 'routes'),
        ('fastapi_app/db.py', '.'),
        ('fastapi_app/auth_utils.py', '.'),
        ('uploads', 'uploads'),
        ('meetings.db', '.'),
    ],
    hiddenimports=[
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.http.h11_impl',
        'fastapi',
        'sqlalchemy.ext.asyncio',
        'aiosqlite',
        'redis',
        'bcrypt',
        'jwt',
        'httpx',
        'requests',
        'docx',
        'pptx',
        'openpyxl'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 合并所有文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 创建可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='qxc-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('backend.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("已创建 backend.spec 文件")
    return True

def build_executable():
    """构建可执行文件"""
    print("正在构建可执行文件...")
    
    # 清理之前的构建文件
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # 使用 PyInstaller 构建
    if not run_command("pyinstaller backend.spec"):
        print("构建可执行文件失败")
        return False
    
    print("可执行文件构建完成")
    return True

def copy_dependencies():
    """复制依赖文件"""
    print("正在复制依赖文件...")
    
    dist_path = Path('dist')
    if not dist_path.exists():
        dist_path.mkdir(parents=True)
    
    # 复制数据库文件
    if os.path.exists('meetings.db'):
        shutil.copy2('meetings.db', dist_path)
    
    # 复制上传目录
    uploads_src = Path('uploads')
    uploads_dst = dist_path / 'uploads'
    if uploads_src.exists():
        if uploads_dst.exists():
            shutil.rmtree(uploads_dst)
        shutil.copytree(uploads_src, uploads_dst)
    else:
        uploads_dst.mkdir(parents=True, exist_ok=True)
    
    # 复制配置文件
    config_files = ['alembic.ini']
    for config_file in config_files:
        if os.path.exists(config_file):
            shutil.copy2(config_file, dist_path)
    
    # 创建启动脚本
    start_script_content = '''@echo off
echo 正在启动 QXC 智能办公后端服务...
echo 请不要关闭此窗口
qxc-backend.exe
pause
'''
    
    with open(dist_path / 'start_backend.bat', 'w', encoding='utf-8') as f:
        f.write(start_script_content)
    
    print("依赖文件复制完成")
    return True

def create_installer_script():
    """创建安装脚本"""
    installer_content = '''
import os
import sys
import sqlite3
from pathlib import Path

def init_database():
    """初始化数据库"""
    print("正在初始化数据库...")
    
    # 创建数据库文件
    db_path = "meetings.db"
    if not os.path.exists(db_path):
        # 这里可以添加数据库初始化代码
        conn = sqlite3.connect(db_path)
        conn.close()
        print("数据库初始化完成")
    else:
        print("数据库已存在")

def setup_directories():
    """设置必要的目录"""
    print("正在创建必要的目录...")
    
    directories = ["uploads", "uploads/avatar", "uploads/images", "uploads/recordings", "uploads/meetings"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("目录创建完成")

def main():
    print("QXC 智能办公后端服务 - 初始化")
    print("=" * 50)
    
    try:
        setup_directories()
        init_database()
        print("\\n初始化完成！")
        print("您现在可以启动应用程序了。")
    except Exception as e:
        print(f"\\n初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    dist_path = Path('dist')
    with open(dist_path / 'setup.py', 'w', encoding='utf-8') as f:
        f.write(installer_content)
    
    print("安装脚本创建完成")
    return True

def main():
    """主函数"""
    print("QXC 智能办公 - 后端打包工具")
    print("=" * 50)
    
    # 检查当前目录
    if not os.path.exists('fastapi_app/main.py'):
        print("错误: 找不到 fastapi_app/main.py 文件")
        print("请在 backend 目录下运行此脚本")
        sys.exit(1)
    
    try:
        # 步骤1: 安装依赖
        if not install_dependencies():
            print("安装依赖失败")
            sys.exit(1)
        
        # 步骤2: 创建规格文件
        if not create_spec_file():
            print("创建规格文件失败")
            sys.exit(1)
        
        # 步骤3: 构建可执行文件
        if not build_executable():
            print("构建可执行文件失败")
            sys.exit(1)
        
        # 步骤4: 复制依赖文件
        if not copy_dependencies():
            print("复制依赖文件失败")
            sys.exit(1)
        
        # 步骤5: 创建安装脚本
        if not create_installer_script():
            print("创建安装脚本失败")
            sys.exit(1)
        
        print("\\n" + "=" * 50)
        print("后端打包完成！")
        print("打包文件位于: dist/ 目录")
        print("可执行文件: dist/qxc-backend.exe")
        print("启动脚本: dist/start_backend.bat")
        print("=" * 50)
        
    except Exception as e:
        print(f"打包过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 