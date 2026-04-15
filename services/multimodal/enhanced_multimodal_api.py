#!/usr/bin/env python3
"""
增强的多模态文件系统API
Enhanced Multimodal File System API

新增功能：文件下载、基础搜索、缓存优化
"""

import hashlib
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))


import aiofiles
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel

from core.security.auth import ALLOWED_ORIGINS

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="Athena多模态文件系统API - 增强版",
    description="集成缓存、搜索、下载功能的多模态文件处理平台",
    version="2.1.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储配置
STORAGE_ROOT = "/Users/xujian/Athena工作平台/storage-system/data/multimodal_files"
METADATA_ROOT = "/Users/xujian/Athena工作平台/storage-system/data/metadata"
THUMBNAIL_ROOT = "/Users/xujian/Athena工作平台/storage-system/data/thumbnails"

# 确保目录存在
for path in [STORAGE_ROOT, METADATA_ROOT, THUMBNAIL_ROOT]:
    Path(path).mkdir(parents=True, exist_ok=True)

# 内存缓存（本地环境替代Redis）
class SimpleCache:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = {}

    def get(self, key: str) -> Any:
        if key in self.cache:
            if key in self.cache_timeout:
                if time.time() < self.cache_timeout[key]:
                    return self.cache[key]
                else:
                    del self.cache[key]
                    del self.cache_timeout[key]
            else:
                return self.cache[key]
        return None

    def set(self, key: str, value: Any, timeout: int = 3600) -> Any:
        self.cache[key] = value
        self.cache_timeout[key] = time.time() + timeout

    def delete(self, key: str) -> Any:
        self.cache.pop(key, None)
        self.cache_timeout.pop(key, None)

# 全局缓存实例
cache = SimpleCache()

# 文件类型映射
FILE_TYPE_MAP = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff"],
    "document": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".pages", ".epub"],
    "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "data": [".json", ".xml", ".csv", ".xlsx", ".yaml", ".yml", ".sql", ".db", ".sqlite"],
    "code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".php"],
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"]
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

def generate_thumbnail(image_path: str, save_path: str, size=(200, 200)):
    """生成缩略图"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size)
            img.save(save_path)
        return True
    except Exception as e:
        logger.error(f"生成缩略图失败: {e}")
        return False

# API响应模型
class FileUploadResponse(BaseModel):
    success: bool
    message: str
    file_id: str | None = None
    filename: str | None = None
    file_type: str | None = None
    file_size: int | None = None
    thumbnail_url: str | None = None

class FileInfo(BaseModel):
    file_id: str
    filename: str
    file_type: str
    file_size: int
    upload_time: str
    file_hash: str
    thumbnail_url: str | None = None
    metadata: dict[str, Any]

class SearchResponse(BaseModel):
    success: bool
    message: str
    total_count: int
    files: list[FileInfo]

# 存储管理器
class EnhancedStorageManager:
    def __init__(self):
        self.storage_root = Path(STORAGE_ROOT)
        self.metadata_root = Path(METADATA_ROOT)
        self.thumbnail_root = Path(THUMBNAIL_ROOT)

    async def save_file(self, file_content: bytes, filename: str,
                       metadata: dict[str, Any] = None) -> dict[str, Any]:
        """保存文件并生成元数据"""
        try:
            file_hash = calculate_file_hash(file_content)
            file_type = get_file_type(filename)

            # 生成唯一文件名
            file_ext = Path(filename).suffix
            stored_name = f"{uuid.uuid4()}{file_ext}"

            # 创建日期目录
            date_dir = datetime.now().strftime('%Y/%m')
            category_dir = self.storage_root / file_type / date_dir
            category_dir.mkdir(parents=True, exist_ok=True)

            # 保存文件
            file_path = category_dir / stored_name
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)

            # 生成缩略图（仅对图像）
            thumbnail_url = None
            if file_type == 'image':
                thumbnail_name = f"{stored_name}_thumb.jpg"
                thumbnail_path = self.thumbnail_root / thumbnail_name
                if generate_thumbnail(str(file_path), str(thumbnail_path)):
                    thumbnail_url = f"/thumbnails/{thumbnail_name}"

            # 保存元数据
            file_id = str(uuid.uuid4())
            file_metadata = {
                "file_id": file_id,
                "original_name": filename,
                "stored_name": stored_name,
                "file_path": str(file_path),
                "file_type": file_type,
                "file_size": len(file_content),
                "file_hash": file_hash,
                "upload_time": datetime.now().isoformat(),
                "thumbnail_url": thumbnail_url,
                "metadata": metadata or {}
            }

            metadata_file = self.metadata_root / f"{file_id}.json"
            async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(file_metadata, ensure_ascii=False, indent=2))

            # 缓存文件信息
            cache.set(f"file:{file_id}", file_metadata)
            cache.set(f"hash:{file_hash}", file_id)

            return file_metadata

        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_file_info(self, file_id: str) -> dict[str, Any | None]:
        """获取文件信息"""
        # 先检查缓存
        cached = cache.get(f"file:{file_id}")
        if cached:
            return cached

        try:
            metadata_file = self.metadata_root / f"{file_id}.json"
            if metadata_file.exists():
                async with aiofiles.open(metadata_file, encoding='utf-8') as f:
                    content = await f.read()
                    file_info = json.loads(content)
                    # 更新缓存
                    cache.set(f"file:{file_id}", file_info)
                    return file_info
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")

        return None

    async def get_file_path(self, file_id: str) -> str | None:
        """获取文件路径"""
        file_info = await self.get_file_info(file_id)
        if file_info:
            return file_info.get("file_path")
        return None

    async def search_files(self, query: str = None, file_type: str = None,
                          limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        """搜索文件"""
        search_key = f"search:{query}:{file_type}:{limit}:{offset}"
        cached = cache.get(search_key)
        if cached:
            return cached

        results = []

        try:
            metadata_files = list(self.metadata_root.glob("*.json"))

            for metadata_file in metadata_files:
                try:
                    async with aiofiles.open(metadata_file, encoding='utf-8') as f:
                        content = await f.read()
                        file_info = json.loads(content)

                    # 过滤条件
                    if file_type and file_info.get("file_type") != file_type:
                        continue

                    if query:
                        original_name = file_info.get("original_name", "").lower()
                        if query.lower() not in original_name:
                            continue

                    results.append(file_info)

                except Exception as e:
                    logger.warning(f"读取元数据失败 {metadata_file}: {e}")

            # 按上传时间排序
            results.sort(key=lambda x: x.get("upload_time", ""), reverse=True)

            # 分页
            start_idx = offset
            end_idx = start_idx + limit
            paginated_results = results[start_idx:end_idx]

            # 缓存结果
            cache.set(search_key, paginated_results, timeout=300)  # 5分钟缓存

            return paginated_results

        except Exception as e:
            logger.error(f"搜索文件失败: {e}")
            return []

# 全局存储管理器
storage = EnhancedStorageManager()

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    metadata: str = Form("{}")
):
    """上传文件"""
    try:
        # 读取文件内容
        file_content = await file.read()

        # 解析元数据
        try:
            file_metadata = json.loads(metadata)
        except (json.JSONDecodeError, TypeError, ValueError):
            file_metadata = {}

        # 保存文件
        result = await storage.save_file(
            file_content,
            file.filename,
            file_metadata
        )

        return FileUploadResponse(
            success=True,
            message="文件上传成功",
            file_id=result.get("file_id"),
            filename=result.get("original_name"),
            file_type=result.get("file_type"),
            file_size=result.get("file_size"),
            thumbnail_url=result.get("thumbnail_url")
        )

    except Exception as e:
        logger.error(f"上传文件失败: {e}")
        return FileUploadResponse(
            success=False,
            message=f"上传失败: {str(e)}"
        )

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """下载文件"""
    try:
        file_info = await storage.get_file_info(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")

        file_path = await storage.get_file_path(file_id)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        original_name = file_info.get("original_name", "download")

        return FileResponse(
            path=file_path,
            filename=original_name,
            media_type='application/octet-stream'
        )

    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}") from e

@app.get("/info/{file_id}", response_model=FileInfo)
async def get_file_info(file_id: str):
    """获取文件信息"""
    try:
        file_info = await storage.get_file_info(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileInfo(
            file_id=file_info.get("file_id"),
            filename=file_info.get("original_name"),
            file_type=file_info.get("file_type"),
            file_size=file_info.get("file_size"),
            upload_time=file_info.get("upload_time"),
            file_hash=file_info.get("file_hash"),
            thumbnail_url=file_info.get("thumbnail_url"),
            metadata=file_info.get("metadata", {})
        )

    except Exception as e:
        logger.error(f"获取文件信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取信息失败: {str(e)}") from e

@app.get("/search", response_model=SearchResponse)
async def search_files(
    query: str = Query(None, description="搜索关键词"),
    file_type: str = Query(None, description="文件类型"),
    limit: int = Query(20, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """搜索文件"""
    try:
        results = await storage.search_files(
            query=query,
            file_type=file_type,
            limit=limit,
            offset=offset
        )

        file_infos = []
        for result in results:
            file_infos.append(FileInfo(
                file_id=result.get("file_id"),
                filename=result.get("original_name"),
                file_type=result.get("file_type"),
                file_size=result.get("file_size"),
                upload_time=result.get("upload_time"),
                file_hash=result.get("file_hash"),
                thumbnail_url=result.get("thumbnail_url"),
                metadata=result.get("metadata", {})
            ))

        return SearchResponse(
            success=True,
            message="搜索完成",
            total_count=len(file_infos),
            files=file_infos
        )

    except Exception as e:
        logger.error(f"搜索文件失败: {e}")
        return SearchResponse(
            success=False,
            message=f"搜索失败: {str(e)}",
            total_count=0,
            files=[]
        )

@app.get("/stats")
async def get_stats():
    """获取存储统计信息"""
    try:
        stats = {}

        # 按文件类型统计
        for file_type in FILE_TYPE_MAP.keys():
            type_results = await storage.search_files(file_type=file_type, limit=1000)
            stats[file_type] = {
                "count": len(type_results),
                "total_size": sum(r.get("file_size", 0) for r in type_results)
            }

        # 总体统计
        all_results = await storage.search_files(limit=10000)
        stats["total"] = {
            "count": len(all_results),
            "total_size": sum(r.get("file_size", 0) for r in all_results)
        }

        return {"success": True, "stats": stats}

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/thumbnails/{thumbnail_name}")
async def get_thumbnail(thumbnail_name: str):
    """获取缩略图"""
    try:
        thumbnail_path = os.path.join(THUMBNAIL_ROOT, thumbnail_name)
        if not os.path.exists(thumbnail_path):
            raise HTTPException(status_code=404, detail="缩略图不存在")

        return FileResponse(
            path=thumbnail_path,
            media_type="image/jpeg"
        )

    except Exception as e:
        logger.error(f"获取缩略图失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缩略图失败: {str(e)}") from e

if __name__ == "__main__":
    uvicorn.run(
        "enhanced_multimodal_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
