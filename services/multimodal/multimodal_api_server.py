#!/usr/bin/env python3
"""
Athena多模态文件系统API服务器（集成版）
Multimodal File System API Server - Integrated Version

使用Athena统一存储系统
"""

import hashlib
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入安全配置
import sys
from pathlib import Path

import aiofiles
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from core.security.auth import ALLOWED_ORIGINS

sys.path.append(str(Path(__file__).parent.parent / "core"))

# 创建FastAPI应用
app = FastAPI(
    title="Athena多模态文件系统API",
    description="集成统一存储的多模态文件处理平台",
    version="2.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库连接配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "athena_business",
    "username": "postgres",
    "password": "xj781102"
}

# 同步引擎用于初始化
sync_engine = create_engine(
    f"{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# 存储配置
STORAGE_ROOT = "/Users/xujian/Athena工作平台/storage-system/data/documents/multimodal"
THUMBNAIL_ROOT = "/Users/xujian/Athena工作平台/storage-system/data/documents/thumbnails"

# 文件类型映射
FILE_TYPE_MAP = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff"],
    "document": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".pages", ".epub"],
    "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "data": [".json", ".xml", ".csv", ".xlsx", ".yaml", ".yml", ".sql", ".db", ".sqlite"],
    "code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".php"],
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "presentation": [".ppt", ".pptx", ".key", ".odp"]
}

def get_file_type(filename: str) -> str:
    """根据文件扩展名获取文件类型"""
    ext = Path(filename).suffix.lower()
    for file_type, extensions in FILE_TYPE_MAP.items():
        if ext in extensions:
            return file_type
    return "unknown"

def calculate_file_hash(file_content: bytes) -> str:
    """计算文件SHA256哈希"""
    return hashlib.sha256(file_content).hexdigest()

# API响应模型
class FileUploadResponse(BaseModel):
    success: bool
    message: str
    file_id: str | None = None
    filename: str | None = None
    file_type: str | None = None
    file_size: int | None = None

class FileListResponse(BaseModel):
    success: bool
    files: list[dict[str, Any]]
    total: int

@app.get("/")
async def root():
    """API根路径"""
    return {
        "service": "🌐 Athena多模态文件系统API",
        "version": "2.0.0 (集成版)",
        "status": "running",
        "port": 8088,
        "storage_mode": "unified_storage",
        "database": "athena_business",
        "features": [
            "📁 统一文件存储",
            "🔍 智能文件检索",
            "🏷️ 自动分类标签",
            "📊 文件统计分析",
            "⚡ 异步处理",
            "🗂️ 多格式支持"
        ],
        "message": "多模态文件系统已集成到Athena统一存储平台！",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """健康检查"""
    try:
        # 检查数据库连接
        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # 检查存储目录
        storage_accessible = os.path.exists(STORAGE_ROOT)

        return {
            "status": "healthy",
            "database": "connected",
            "storage": "accessible" if storage_accessible else "error",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    tags: str | None = Form(None),
    category: str | None = Form(None)
):
    """上传文件"""
    try:
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)

        # 计算文件哈希
        file_hash = calculate_file_hash(file_content)

        # 获取文件类型
        file_type = get_file_type(file.filename)

        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        stored_filename = f"{file_id}{file_ext}"

        # 确定存储路径
        type_dir = os.path.join(STORAGE_ROOT, file_type)
        os.makedirs(type_dir, exist_ok=True)
        storage_path = os.path.join(type_dir, stored_filename)

        # 保存文件
        async with aiofiles.open(storage_path, 'wb') as f:
            await f.write(file_content)

        # 解析标签
        tag_list = tags.split(',') if tags else []

        # 保存到数据库
        with sync_engine.connect() as conn:
            insert_query = text("""
                INSERT INTO multimodal_files
                (id, filename, original_filename, file_type, file_size, mime_type,
                 storage_path, file_hash, tags, category, processed)
                VALUES
                (:id, :filename, :original_filename, :file_type, :file_size, :mime_type,
                 :storage_path, :file_hash, :tags, :category, :processed)
            """)

            conn.execute(insert_query, {
                "id": file_id,
                "filename": stored_filename,
                "original_filename": file.filename,
                "file_type": file_type,
                "file_size": file_size,
                "mime_type": file.content_type,
                "storage_path": storage_path,
                "file_hash": file_hash,
                "tags": tag_list,
                "category": category,
                "processed": False
            })
            conn.commit()

        return FileUploadResponse(
            success=True,
            message=f"文件 {file.filename} 上传成功！",
            file_id=file_id,
            filename=stored_filename,
            file_type=file_type,
            file_size=file_size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}") from e

@app.get("/api/files/list", response_model=FileListResponse)
async def list_files(
    file_type: str | None = None,
    limit: int = 20,
    offset: int = 0
):
    """获取文件列表"""
    try:
        with sync_engine.connect() as conn:
            query = text("""
                SELECT id, filename, original_filename, file_type, file_size,
                       mime_type, upload_time, processed, processing_status,
                       tags, category, access_count
                FROM multimodal_files
                WHERE (:file_type IS NULL OR file_type = :file_type)
                ORDER BY upload_time DESC
                LIMIT :limit OFFSET :offset
            """)

            result = conn.execute(query, {
                "file_type": file_type,
                "limit": limit,
                "offset": offset
            })

            files = []
            for row in result:
                files.append({
                    "id": str(row[0]),
                    "filename": row[1],
                    "original_filename": row[2],
                    "file_type": row[3],
                    "file_size": row[4],
                    "mime_type": row[5],
                    "upload_time": row[6].isoformat(),
                    "processed": row[7],
                    "processing_status": row[8],
                    "tags": row[9],
                    "category": row[10],
                    "access_count": row[11]
                })

            # 获取总数
            count_query = text("""
                SELECT COUNT(*) FROM multimodal_files
                WHERE (:file_type IS NULL OR file_type = :file_type)
            """)
            total_result = conn.execute(count_query, {"file_type": file_type})
            total = total_result.scalar()

            return FileListResponse(
                success=True,
                files=files,
                total=total
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}") from e

@app.get("/api/stats")
async def get_stats():
    """获取文件统计信息"""
    try:
        with sync_engine.connect() as conn:
            # 按类型统计
            type_stats = conn.execute(text("""
                SELECT file_type, COUNT(*) as count, SUM(file_size) as total_size
                FROM multimodal_files
                GROUP BY file_type
            """))

            stats = {
                "by_type": [],
                "total_files": 0,
                "total_size": 0,
                "processed_files": 0
            }

            for row in type_stats:
                stats["by_type"].append({
                    "type": row[0],
                    "count": row[1],
                    "total_size": row[2]
                })
                stats["total_files"] += row[1]
                stats["total_size"] += row[2] or 0

            # 处理状态统计
            processed_result = conn.execute(text("""
                SELECT processed, COUNT(*)
                FROM multimodal_files
                GROUP BY processed
            """))

            for row in processed_result:
                if row[0]:
                    stats["processed_files"] = row[1]

            stats["processing_rate"] = (
                stats["processed_files"] / stats["total_files"] * 100
                if stats["total_files"] > 0 else 0
            )

            return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}") from e

@app.get("/api/files/{file_id}")
async def get_file_info(file_id: str):
    """获取文件详细信息"""
    try:
        with sync_engine.connect() as conn:
            query = text("""
                SELECT * FROM multimodal_files
                WHERE id = :file_id
            """)

            result = conn.execute(query, {"file_id": file_id})
            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="文件不存在")

            # 更新访问计数
            conn.execute(text("""
                UPDATE multimodal_files
                SET access_count = access_count + 1,
                      last_accessed = CURRENT_TIMESTAMP
                WHERE id = :file_id
            """), {"file_id": file_id})
            conn.commit()

            file_info = {
                "id": str(row[0]),
                "filename": row[1],
                "original_filename": row[2],
                "file_type": row[3],
                "file_size": row[4],
                "mime_type": row[5],
                "storage_path": row[6],
                "uploaded_by": row[10],
                "upload_time": row[11].isoformat(),
                "processed": row[12],
                "processing_status": row[13],
                "metadata": row[15],
                "extracted_text": row[16][:200] + "..." if row[16] and len(row[16]) > 200 else row[16],
                "tags": row[17],
                "category": row[18],
                "access_count": row[19],
                "last_accessed": row[20].isoformat() if row[20] else None
            }

            return file_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}") from e

if __name__ == "__main__":
    # 显示启动信息
    print("\n🌐 启动Athena多模态文件系统API（集成版）")
    print("=" * 50)
    print("📋 集成特性：")
    print("  ✅ 使用Athena统一存储系统")
    print("  ✅ PostgreSQL数据库 (athena_business)")
    print("  ✅ 文件存储在 storage-system/data/documents/")
    print("  ✅ 支持多格式文件处理")
    print("  ✅ 自动分类和标签管理")
    print("")
    print("📍 服务端口: 8088")
    print("🌐 API地址: http://localhost:8088")
    print("📊 健康检查: http://localhost:8088/health")
    print("")
    print("💡 支持的API端点：")
    print("  - POST /api/files/upload - 上传文件")
    print("  - GET /api/files/list - 获取文件列表")
    print("  - GET /api/files/{file_id} - 获取文件信息")
    print("  - GET /api/stats - 获取统计信息")
    print("")
    print("🚀 服务启动中...")

    # 启动服务
    uvicorn.run(app, host="127.0.0.1", port=8088)  # 内网通信，通过Gateway访问
