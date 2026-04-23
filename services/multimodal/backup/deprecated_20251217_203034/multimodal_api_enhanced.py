#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena多模态文件系统API服务器（增强版）
Multimodal File System API Server - Enhanced Version

集成AI处理功能（OCR、图像分析等）
"""

import sys
from core.async_main import async_main
import os
from pathlib import Path
from datetime import datetime
import asyncio
import json
import hashlib
import uuid
import time
from typing import Dict, List, Any, Optional

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import aiofiles
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 导入AI处理器
from ai.ai_processor import AIProcessor, ProcessingType
# 导入Whisper音频处理器
from ai.audio_processor_enhanced import get_audio_processor

# 创建FastAPI应用
app = FastAPI(
    title="Athena多模态文件系统API (增强版)",
    description="集成AI处理的多模态文件处理平台",
    version="3.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    f"postgresql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# 存储配置
STORAGE_ROOT = "/Users/xujian/Athena工作平台/storage-system/data/documents/multimodal"
THUMBNAIL_ROOT = "/Users/xujian/Athena工作平台/storage-system/data/documents/thumbnails"

# 文件类型映射
FILE_TYPE_MAP = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff"],
    "document": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".pages", ".epub"],
    "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".amr"],
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
    processing_task_id: str | None = None

class FileListResponse(BaseModel):
    success: bool
    files: List[Dict[str, Any]
    total: int

class ProcessingTaskResponse(BaseModel):
    success: bool
    task_id: str
    status: str
    result: Optional[Dict[str, Any] = None
    error: str | None = None

# AI处理器实例
ai_processor = AIProcessor()

async def process_file_background(file_id: str, file_path: str, file_type: str):
    """后台处理文件"""
    try:
        # 启动AI处理器
        await ai_processor.start()

        # 根据文件类型选择处理方式
        if file_type == "image":
            # 图像分析
            task_id = await ai_processor.submit_processing_task(
                file_id=file_id,
                file_path=file_path,
                processing_type=ProcessingType.IMAGE_ANALYSIS,
                options={'analyze_colors': True, 'analyze_quality': True}
            )

            # OCR文字提取
            ocr_task_id = await ai_processor.submit_processing_task(
                file_id=f"{file_id}_ocr",
                file_path=file_path,
                processing_type=ProcessingType.CONTENT_EXTRACTION,
                options={'extract_text': True}
            )

        elif file_type == "audio":
            # 音频转录 - 使用Whisper
            audio_proc = get_audio_processor()
            print(f"开始转录音频文件: {file_path}")

            try:
                # 使用Whisper进行转录
                result = await audio_proc.transcribe_with_timestamps(file_path, "zh")

                if result["success"]:
                    print(f"音频转录成功: {result['text'][:100]}...")

                    # 更新数据库中的转录结果
                    with sync_engine.connect() as conn:
                        update_query = text("""
                            UPDATE multimodal_files
                            SET extracted_text = :text,
                                processing_status = 'completed',
                                processed = true,
                                processing_data = :data,
                                last_accessed = CURRENT_TIMESTAMP
                            WHERE id = :file_id
                        """)

                        conn.execute(update_query, {
                            "file_id": file_id,
                            "text": result["text"],
                            "data": {
                                "model": result.get("model", "whisper"),
                                "language": result.get("language", "zh"),
                                "duration": result.get("duration", 0),
                                "segments": result.get("segments", [])
                            }
                        })
                        conn.commit()

                        print(f"数据库更新完成: 文件ID {file_id}")
                else:
                    print(f"音频转录失败: {result.get('error')}")

            except Exception as e:
                print(f"Whisper转录异常: {e}")

        elif file_type == "document":
            # 文档解析
            task_id = await ai_processor.submit_processing_task(
                file_id=file_id,
                file_path=file_path,
                processing_type=ProcessingType.DOCUMENT_PARSING,
                options={}
            )

        elif file_type in ["txt", "md"]:
            # 文本分析
            task_id = await ai_processor.submit_processing_task(
                file_id=file_id,
                file_path=file_path,
                processing_type=ProcessingType.TEXT_ANALYSIS,
                options={'extract_keywords': True, 'tokenize': True}
            )

        # 等待处理完成（简化版本）
        await asyncio.sleep(5)

    except Exception as e:
        print(f"后台处理失败: {e}")

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    await ai_processor.start()
    print("✅ AI处理器已启动")

@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    await ai_processor.stop()
    print("✅ AI处理器已停止")

@app.get("/")
async def root():
    """API根路径"""
    return {
        "service": "🌐 Athena多模态文件系统API",
        "version": "3.0.0 (增强版)",
        "status": "running",
        "port": 8089,
        "storage_mode": "unified_storage",
        "database": "athena_business",
        "ai_features": [
            "🤖 OCR文字识别",
            "🖼️ 图像分析",
            "📄 文档解析",
            "📝 文本分析",
            "🏷️ 关键词提取",
            "🎨 颜色分析",
            "📊 质量评估"
        ],
        "message": "多模态文件系统已集成AI处理能力！",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """健康检查"""
    try:
        # 检查数据库连接
        with sync_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))

        # 检查存储目录
        storage_accessible = os.path.exists(STORAGE_ROOT)

        # 检查AI处理器
        ai_stats = ai_processor.get_statistics()

        return {
            "status": "healthy",
            "database": "connected",
            "storage": "accessible" if storage_accessible else "error",
            "ai_processor": "running",
            "supported_features": ai_stats.get('model_config', {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/files/upload", response_model=FileUploadResponse)
async def upload_file_enhanced(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    auto_process: bool = Form(True)
):
    """上传文件（增强版）"""
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

        # 提交后台AI处理任务
        processing_task_id = None
        if auto_process:
            background_tasks.add_task(
                process_file_background,
                file_id,
                storage_path,
                file_type
            )
            processing_task_id = f"bg_{file_id}"

        return FileUploadResponse(
            success=True,
            message=f"文件 {file.filename} 上传成功！{('AI处理已启动' if auto_process else '')}",
            file_id=file_id,
            filename=stored_filename,
            file_type=file_type,
            file_size=file_size,
            processing_task_id=processing_task_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@app.post("/api/files/{file_id}/analyze")
async def analyze_file(
    file_id: str,
    processing_type: str = Form("auto")
):
    """手动触发文件分析"""
    try:
        # 获取文件信息
        with sync_engine.connect() as conn:
            query = text("""
                SELECT storage_path, file_type FROM multimodal_files
                WHERE id = :file_id
            """)
            result = conn.execute(query, {"file_id": file_id})
            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="文件不存在")

            storage_path, file_type = row[0], row[1]

        # 确定处理类型
        if processing_type == "auto":
            if file_type == "image":
                proc_type = ProcessingType.IMAGE_ANALYSIS
            elif file_type == "document":
                proc_type = ProcessingType.DOCUMENT_PARSING
            elif file_type in ["txt", "md"]:
                proc_type = ProcessingType.TEXT_ANALYSIS
            else:
                proc_type = ProcessingType.CONTENT_EXTRACTION
        else:
            proc_type = ProcessingType(processing_type)

        # 提交处理任务
        task_id = await ai_processor.submit_processing_task(
            file_id=file_id,
            file_path=storage_path,
            processing_type=proc_type
        )

        return {
            "success": True,
            "message": f"文件分析已启动",
            "task_id": task_id,
            "processing_type": proc_type.value
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动分析失败: {str(e)}")

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取处理任务状态"""
    try:
        result = await ai_processor.get_processing_result(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="任务不存在")

        return {
            "success": True,
            "task_id": task_id,
            "status": result.status.value,
            "created_at": result.created_at.isoformat(),
            "started_at": result.started_at.isoformat() if result.started_at else None,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "result": result.result,
            "confidence": result.confidence,
            "error_message": result.error_message,
            "processing_time": result.processing_time
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

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
                "processed_files": 0,
                "ai_processing": ai_processor.get_statistics()
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
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")

if __name__ == "__main__":
    # 显示启动信息
    print("\n🌐 启动Athena多模态文件系统API（增强版）")
    print("=" * 50)
    print("📋 集成特性：")
    print("  ✅ 使用Athena统一存储系统")
    print("  ✅ PostgreSQL数据库 (athena_business)")
    print("  ✅ AI处理能力集成")
    print("    - OCR文字识别 (Tesseract)")
    print("    - 图像分析 (PIL + OpenCV)")
    print("    - 文档解析")
    print("    - 文本分析 (jieba)")
    print("  ✅ 自动后台处理")
    print("  ✅ 异步任务队列")
    print("")
    print("📍 服务端口: 8089")
    print("🌐 API地址: http://localhost:8089")
    print("📊 健康检查: http://localhost:8089/health")
    print("")
    print("💡 新增API端点：")
    print("  - POST /api/files/upload - 上传文件（支持自动处理）")
    print("  - POST /api/files/{file_id}/analyze - 手动触发分析")
    print("  - GET /api/tasks/{task_id} - 获取处理任务状态")
    print("")
    print("🚀 服务启动中...")

    # 启动服务
    uvicorn.run(app, host="0.0.0.0", port=8089)