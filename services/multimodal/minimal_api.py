#!/usr/bin/env python3
"""
Athena多模态文件系统 - 最小化API
精简版本，确保快速启动和稳定运行
"""

import hashlib
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

try:
    import uvicorn
    from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    from core.security.auth import ALLOWED_ORIGINS
    FASTAPI_AVAILABLE = True
except ImportError as e:
    logger.error(f"FastAPI导入失败: {e}")
    logger.error("请运行: pip install fastapi uvicorn aiofiles")
    FASTAPI_AVAILABLE = False

# 创建FastAPI应用
app = FastAPI(
    title="Athena多模态文件系统",
    description="企业级文件管理平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存存储（简化版）
files_db = {}
tasks_db = {}
sessions_db = {}
statistics = {
    "total_uploads": 0,
    "total_downloads": 0,
    "total_size": 0,
    "start_time": datetime.now().isoformat()
}

# 存储路径
STORAGE_PATH = Path("/Users/xujian/Athena工作平台/storage-system/data/multimodal_files")
STORAGE_PATH.mkdir(parents=True, exist_ok=True)

class SimpleAuthManager:
    """简化的认证管理器"""

    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY")
        if not self.secret_key:
            self.secret_key = "athena_multimodal_2024"  # 默认值
        self.sessions = {}

    def login(self, username: str, password: str) -> dict[str, Any]:
        """登录认证"""
        # 简化的认证逻辑
        if not username or not password:
            raise HTTPException(status_code=400, detail="用户名和密码不能为空")

        # 生成会话
        session_id = hashlib.sha256(f"{username}_{time.time()}".encode()).hexdigest()
        token = f"athena_token_{session_id[:16]}"

        sessions_db[session_id] = {
            "user_id": username,
            "token": token,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }

        return {
            "success": True,
            "token": token,
            "user_id": username,
            "expires_in": 86400
        }

    def verify_token(self, token: str) -> dict[str, Any | None]:
        """验证令牌"""
        for session in sessions_db.values():
            if session["token"] == token:
                # 检查过期
                expires_at = datetime.fromisoformat(session["expires_at"])
                if datetime.now() < expires_at:
                    return session
        return None

auth_manager = SimpleAuthManager()

class SimpleFileManager:
    """简化的文件管理器"""

    def __init__(self):
        self.storage_path = STORAGE_PATH
        self.supported_formats = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.md', '.json', '.xml', '.csv'],
            'audio': ['.mp3', '.wav', '.flac', '.aac'],
            'video': ['.mp4', '.avi', '.mkv', '.mov'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz']
        }

    def get_file_type(self, filename: str) -> str:
        """获取文件类型"""
        ext = Path(filename).suffix.lower()
        for file_type, extensions in self.supported_formats.items():
            if ext in extensions:
                return file_type
        return 'unknown'

    def save_file(self, file_content: bytes, filename: str) -> dict[str, Any]:
        """保存文件"""
        try:
            # 生成文件ID
            file_id = hashlib.sha256(file_content).hexdigest()[:16]
            file_type = self.get_file_type(filename)

            # 创建日期目录
            date_dir = datetime.now().strftime('%Y/%m')
            type_dir = self.storage_path / file_type / date_dir
            type_dir.mkdir(parents=True, exist_ok=True)

            # 保存文件
            file_path = type_dir / f"{file_id}_{filename}"
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # 保存元数据
            file_info = {
                "file_id": file_id,
                "filename": filename,
                "file_type": file_type,
                "size": len(file_content),
                "upload_time": datetime.now().isoformat(),
                "file_path": str(file_path),
                "hash": hashlib.sha256(file_content).hexdigest()
            }

            files_db[file_id] = file_info

            # 更新统计
            statistics["total_uploads"] += 1
            statistics["total_size"] += len(file_content)

            logger.info(f"文件保存成功: {filename} ({file_id})")
            return file_info

        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            raise

# 全局实例
file_manager = SimpleFileManager()

# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Athena多模态文件系统",
        "version": "1.0.0",
        "status": "running",
        "features": ["文件管理", "安全认证", "AI处理"],
        "statistics": statistics
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - time.mktime(datetime.strptime(statistics["start_time"], "%Y-%m-%d_t%H:%M:%S")),
        "files_count": len(files_db),
        "tasks_count": len(tasks_db),
        "storage_path": str(STORAGE_PATH),
        "statistics": statistics
    }

@app.post("/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """用户登录"""
    try:
        result = auth_manager.login(username, password)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), token: str = Form(...)):
    """文件上传"""
    try:
        # 验证令牌
        session = auth_manager.verify_token(token)
        if not session:
            raise HTTPException(status_code=401, detail="无效的认证令牌")

        # 读取文件内容
        content = await file.read()

        # 保存文件
        file_info = file_manager.save_file(content, file.filename)

        return JSONResponse(content={
            "success": True,
            "message": "文件上传成功",
            "file_info": file_info
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/files")
async def list_files():
    """列出所有文件"""
    files_list = list(files_db.values())
    files_list.sort(key=lambda x: x['upload_time'], reverse=True)

    return JSONResponse(content={
        "success": True,
        "total_files": len(files_list),
        "files": files_list
    })

@app.get("/files/{file_id}")
async def get_file_info(file_id: str):
    """获取文件信息"""
    file_info = files_db.get(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")

    return JSONResponse(content={
        "success": True,
        "file_info": file_info
    })

@app.get("/files/{file_id}/download")
async def download_file(file_id: str):
    """下载文件"""
    file_info = files_db.get(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")

    file_path = Path(file_info["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在于存储系统")

    return JSONResponse(content={
        "success": True,
        "download_url": f"/download/{file_id}",
        "file_info": file_info
    })

@app.get("/download/{file_id}")
async def download_file_content(file_id: str):
    """下载文件内容"""
    file_info = files_db.get(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")

    file_path = Path(file_info["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        with open(file_path, 'rb') as f:
            content = f.read()

        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={file_info['filename']}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件读取失败: {e}") from e

@app.get("/statistics")
async def get_statistics():
    """获取统计信息"""
    return JSONResponse(content={
        "success": True,
        "statistics": statistics,
        "storage_info": {
            "path": str(STORAGE_PATH),
            "exists": STORAGE_PATH.exists(),
            "free_space": 0  # 可以添加磁盘空间检查
        }
    })

# 添加CORS预检请求支持
@app.options("/{path:path}")
async def preflight_handler(path: str):
    return {"status": "ok"}

if __name__ == "__main__":
    if not FASTAPI_AVAILABLE:
        print("❌ 依赖检查失败，请安装必要的包")
        print("   pip install fastapi uvicorn aiofiles")
        sys.exit(1)

    print("🚀 启动 Athena多模态文件系统")
    print("=" * 50)
    print(f"📁 存储路径: {STORAGE_PATH}")
    print("🌐 服务地址: http://localhost:8001")
    print("📚 API文档: http://localhost:8001/docs")
    print("❤ 健康检查: http://localhost:8001/health")
    print("=" * 50)

    # 启动服务
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )
