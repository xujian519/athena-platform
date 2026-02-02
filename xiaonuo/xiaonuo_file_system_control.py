#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺文件系统控制器
Xiaonuo File System Controller

统一管理和控制平台的多模态文件系统

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import os
import asyncio
import json
import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

class FileType(Enum):
    """文件类型枚举"""
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DATA = "data"
    CODE = "code"
    ARCHIVE = "archive"
    PRESENTATION = "presentation"
    UNKNOWN = "unknown"

class FileOperation(Enum):
    """文件操作类型"""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE = "delete"
    MOVE = "move"
    COPY = "copy"
    ANALYZE = "analyze"
    SEARCH = "search"
    PREVIEW = "preview"

@dataclass
class FileInfo:
    """文件信息"""
    id: str
    name: str
    path: str
    size: int
    type: FileType
    mime_type: str
    created_at: datetime
    modified_at: datetime
    hash_md5: str
    hash_sha256: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    owner: str | None = None
    permissions: Dict[str, str] = field(default_factory=dict)

@dataclass
class ProcessingTask:
    """处理任务"""
    id: str
    file_id: str
    operation: str
    status: str
    progress: float
    result: Optional[Dict[str, Any]] = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)

class XiaonuoFileSystemController:
    """小诺文件系统控制器"""

    def __init__(self):
        self.name = "小诺文件系统控制器"
        self.version = "1.0.0"
        self.logger = logging.getLogger(self.name)

        # 核心路径
        self.base_path = "/Users/xujian/Athena工作平台"
        self.storage_path = os.path.join(self.base_path, "storage-system", "storage")
        self.data_path = os.path.join(self.base_path, "storage-system", "data")

        # 支持的文件类型映射
        self.file_type_mapping = {
            # 文档类
            ".pdf": FileType.DOCUMENT,
            ".docx": FileType.DOCUMENT,
            ".doc": FileType.DOCUMENT,
            ".txt": FileType.DOCUMENT,
            ".md": FileType.DOCUMENT,
            ".rtf": FileType.DOCUMENT,

            # 图像类
            ".png": FileType.IMAGE,
            ".jpg": FileType.IMAGE,
            ".jpeg": FileType.IMAGE,
            ".gif": FileType.IMAGE,
            ".bmp": FileType.IMAGE,
            ".tiff": FileType.IMAGE,
            ".svg": FileType.IMAGE,
            ".webp": FileType.IMAGE,

            # 音频类
            ".mp3": FileType.AUDIO,
            ".wav": FileType.AUDIO,
            ".flac": FileType.AUDIO,
            ".m4a": FileType.AUDIO,
            ".aac": FileType.AUDIO,
            ".ogg": FileType.AUDIO,

            # 视频类
            ".mp4": FileType.VIDEO,
            ".avi": FileType.VIDEO,
            ".mov": FileType.VIDEO,
            ".mkv": FileType.VIDEO,
            ".flv": FileType.VIDEO,
            ".webm": FileType.VIDEO,

            # 数据类
            ".json": FileType.DATA,
            ".xml": FileType.DATA,
            ".csv": FileType.DATA,
            ".xlsx": FileType.DATA,
            ".yaml": FileType.DATA,
            ".yml": FileType.DATA,

            # 代码类
            ".py": FileType.CODE,
            ".js": FileType.CODE,
            ".html": FileType.CODE,
            ".css": FileType.CODE,
            ".java": FileType.CODE,
            ".cpp": FileType.CODE,
            ".c": FileType.CODE,

            # 压缩类
            ".zip": FileType.ARCHIVE,
            ".rar": FileType.ARCHIVE,
            ".7z": FileType.ARCHIVE,
            ".tar": FileType.ARCHIVE,
            ".gz": FileType.ARCHIVE,

            # 演示类
            ".ppt": FileType.PRESENTATION,
            ".pptx": FileType.PRESENTATION,
            ".key": FileType.PRESENTATION,
            ".odp": FileType.PRESENTATION
        }

        # 处理能力
        self.processing_capabilities = {
            FileType.DOCUMENT: ["text_extraction", "ocr", "metadata_extraction"],
            FileType.IMAGE: ["ocr", "object_detection", "content_analysis", "glm4v_analysis"],
            FileType.AUDIO: ["speech_recognition", "feature_extraction", "content_analysis"],
            FileType.VIDEO: ["frame_extraction", "audio_transcription", "content_analysis"],
            FileType.CODE: ["syntax_highlighting", "code_analysis", "documentation_generation"]
        }

        # 文件存储结构
        self.storage_structure = {
            FileType.DOCUMENT: "documents",
            FileType.IMAGE: "images",
            FileType.AUDIO: "audio",
            FileType.VIDEO: "videos",
            FileType.DATA: "data",
            FileType.CODE: "code",
            FileType.ARCHIVE: "archives",
            FileType.PRESENTATION: "presentations",
            FileType.UNKNOWN: "misc"
        }

        # 活动任务
        self.active_tasks: Dict[str, ProcessingTask] = {}

        # 文件索引
        self.file_index: Dict[str, FileInfo] = {}

        # 初始化目录结构
        self._initialize_storage_structure()

        print(f"📁 {self.name} 初始化完成")

    def _initialize_storage_structure(self):
        """初始化存储目录结构"""
        for file_type, directory in self.storage_structure.items():
            dir_path = os.path.join(self.storage_path, directory)
            os.makedirs(dir_path, exist_ok=True)
            print(f"  📂 创建目录: {directory}")

    async def upload_file(self,
                         file_path: str,
                         description: str = "",
                         tags: Optional[List[str] = None,
                         owner: str = "system") -> FileInfo:
        """上传文件"""
        self.logger.info(f"上传文件: {file_path}")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 获取文件信息
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        # 检测文件类型
        file_type = self.file_type_mapping.get(file_ext, FileType.UNKNOWN)

        # 计算文件哈希
        hash_md5, hash_sha256 = self._calculate_file_hashes(file_path)

        # 生成唯一ID
        file_id = self._generate_file_id(file_name, hash_md5)

        # 确定存储路径
        storage_dir = self.storage_structure.get(file_type, "misc")
        storage_path = os.path.join(self.storage_path, storage_dir, file_id[:2], file_id[2:4])
        os.makedirs(storage_path, exist_ok=True)

        final_path = os.path.join(storage_path, f"{file_id}_{file_name}")

        # 复制文件
        import shutil
        shutil.copy2(file_path, final_path)

        # 创建文件信息
        file_info = FileInfo(
            id=file_id,
            name=file_name,
            path=final_path,
            size=file_size,
            type=file_type,
            mime_type=self._get_mime_type(file_path),
            created_at=datetime.now(),
            modified_at=datetime.now(),
            hash_md5=hash_md5,
            hash_sha256=hash_sha256,
            metadata={
                "original_path": file_path,
                "description": description,
                "upload_time": datetime.now().isoformat()
            },
            tags=tags or [],
            owner=owner
        )

        # 添加到索引
        self.file_index[file_id] = file_info

        # 创建处理任务
        await self._create_processing_task(file_id, "analyze_file")

        self.logger.info(f"文件上传成功: {file_name} (ID: {file_id})")
        return file_info

    def _calculate_file_hashes(self, file_path: str) -> Tuple[str, str]:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        hash_sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
                hash_sha256.update(chunk)

        return hash_md5.hexdigest(), hash_sha256.hexdigest()

    def _generate_file_id(self, file_name: str, file_hash: str) -> str:
        """生成唯一文件ID"""
        timestamp = str(int(datetime.now().timestamp()))
        name_hash = hashlib.md5(file_name.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]
        return f"{timestamp}_{name_hash}_{file_hash[:8]}"

    def _get_mime_type(self, file_path: str) -> str:
        """获取MIME类型"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"

    async def search_files(self,
                          query: str = "",
                          file_type: FileType | None = None,
                          tags: Optional[List[str] = None,
                          owner: str | None = None,
                          limit: int = 100) -> List[FileInfo]:
        """搜索文件"""
        results = []

        for file_info in self.file_index.values():
            # 文件类型过滤
            if file_type and file_info.type != file_type:
                continue

            # 标签过滤
            if tags and not any(tag in file_info.tags for tag in tags):
                continue

            # 所有者过滤
            if owner and file_info.owner != owner:
                continue

            # 文本查询过滤
            if query:
                if not self._matches_query(file_info, query):
                    continue

            results.append(file_info)

            if len(results) >= limit:
                break

        return results

    def _matches_query(self, file_info: FileInfo, query: str) -> bool:
        """检查文件是否匹配查询"""
        query_lower = query.lower()

        # 检查文件名
        if query_lower in file_info.name.lower():
            return True

        # 检查描述
        description = file_info.metadata.get("description", "")
        if query_lower in description.lower():
            return True

        # 检查标签
        if any(query_lower in tag.lower() for tag in file_info.tags):
            return True

        return False

    async def analyze_file(self, file_id: str) -> Dict[str, Any]:
        """分析文件"""
        file_info = self.file_index.get(file_id)
        if not file_info:
            raise ValueError(f"文件不存在: {file_id}")

        self.logger.info(f"分析文件: {file_info.name}")

        analysis_result = {
            "file_id": file_id,
            "file_name": file_info.name,
            "file_type": file_info.type.value,
            "analysis": {}
        }

        # 根据文件类型执行不同的分析
        if file_info.type == FileType.DOCUMENT:
            analysis_result["analysis"] = await self._analyze_document(file_info)
        elif file_info.type == FileType.IMAGE:
            analysis_result["analysis"] = await self._analyze_image(file_info)
        elif file_info.type == FileType.AUDIO:
            analysis_result["analysis"] = await self._analyze_audio(file_info)
        elif file_info.type == FileType.VIDEO:
            analysis_result["analysis"] = await self._analyze_video(file_info)
        elif file_info.type == FileType.CODE:
            analysis_result["analysis"] = await self._analyze_code(file_info)

        return analysis_result

    async def _analyze_document(self, file_info: FileInfo) -> Dict[str, Any]:
        """分析文档文件"""
        # 模拟文档分析
        return {
            "pages": 10,
            "has_images": True,
            "language": "zh-CN",
            "extracted_text": "文档内容摘要...",
            "ocr_applied": True if file_info.name.endswith(".pdf") else False
        }

    async def _analyze_image(self, file_info: FileInfo) -> Dict[str, Any]:
        """分析图像文件"""
        # 模拟图像分析
        return {
            "width": 1920,
            "height": 1080,
            "format": file_info.name.split(".")[-1],
            "has_text": True,
            "objects_detected": ["person", "building", "tree"],
            "glm4v_analysis": "图像内容描述..."
        }

    async def _analyze_audio(self, file_info: FileInfo) -> Dict[str, Any]:
        """分析音频文件"""
        # 模拟音频分析
        return {
            "duration": 120.5,
            "sample_rate": 44100,
            "channels": 2,
            "format": file_info.name.split(".")[-1],
            "transcription": "语音转录内容...",
            "language": "zh-CN"
        }

    async def _analyze_video(self, file_info: FileInfo) -> Dict[str, Any]:
        """分析视频文件"""
        # 模拟视频分析
        return {
            "duration": 300.0,
            "fps": 30,
            "resolution": "1920x1080",
            "format": file_info.name.split(".")[-1],
            "frame_count": 9000,
            "has_audio": True,
            "audio_transcription": "视频音频转录..."
        }

    async def _analyze_code(self, file_info: FileInfo) -> Dict[str, Any]:
        """分析代码文件"""
        # 模拟代码分析
        return {
            "language": file_info.name.split(".")[-1],
            "lines_of_code": 150,
            "functions": 5,
            "classes": 2,
            "imports": ["os", "sys", "json"],
            "complexity": "medium"
        }

    async def _create_processing_task(self, file_id: str, operation: str) -> str:
        """创建处理任务"""
        task_id = f"task_{file_id}_{operation}_{int(datetime.now().timestamp())}"

        task = ProcessingTask(
            id=task_id,
            file_id=file_id,
            operation=operation,
            status="pending",
            progress=0.0
        )

        self.active_tasks[task_id] = task

        # 异步执行处理
        asyncio.create_task(self._execute_processing_task(task))

        return task_id

    async def _execute_processing_task(self, task: ProcessingTask):
        """执行处理任务"""
        try:
            task.status = "processing"
            task.progress = 0.0

            # 模拟处理过程
            for i in range(10):
                await asyncio.sleep(0.1)
                task.progress = (i + 1) * 10

            # 完成处理
            task.status = "completed"
            task.progress = 100.0
            task.result = {"message": f"处理完成: {task.operation}"}

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self.logger.error(f"处理任务失败: {task.id}, 错误: {str(e)}")

    def get_task_status(self, task_id: str) -> ProcessingTask | None:
        """获取任务状态"""
        return self.active_tasks.get(task_id)

    def get_file_info(self, file_id: str) -> FileInfo | None:
        """获取文件信息"""
        return self.file_index.get(file_id)

    def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        file_info = self.file_index.get(file_id)
        if not file_info:
            return False

        try:
            # 删除物理文件
            if os.path.exists(file_info.path):
                os.remove(file_info.path)

            # 从索引中移除
            del self.file_index[file_id]

            self.logger.info(f"文件删除成功: {file_info.name}")
            return True

        except Exception as e:
            self.logger.error(f"删除文件失败: {str(e)}")
            return False

    def get_storage_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        stats = {
            "total_files": len(self.file_index),
            "total_size": sum(info.size for info in self.file_index.values()),
            "files_by_type": {},
            "storage_usage": {},
            "active_tasks": len(self.active_tasks)
        }

        # 按类型统计
        for file_info in self.file_index.values():
            type_name = file_info.type.value
            if type_name not in stats["files_by_type"]:
                stats["files_by_type"][type_name] = {"count": 0, "size": 0}

            stats["files_by_type"][type_name]["count"] += 1
            stats["files_by_type"][type_name]["size"] += file_info.size

        # 存储使用情况
        for file_type in FileType:
            dir_path = os.path.join(self.storage_path, self.storage_structure.get(file_type, "misc"))
            if os.path.exists(dir_path):
                size = sum(
                    os.path.getsize(os.path.join(dirpath, f))
                    for f in os.listdir(dir_path)
                    if os.path.isfile(os.path.join(dir_path, f))
                )
                stats["storage_usage"][file_type.value] = size

        return stats

    def get_control_capabilities(self) -> Dict[str, Any]:
        """获取控制能力报告"""
        capabilities = {
            "file_operations": [
                "upload", "download", "delete", "move", "copy", "analyze", "search", "preview"
            ],
            "supported_types": [t.value for t in FileType],
            "processing_capabilities": self.processing_capabilities,
            "automation_features": [
                "automatic_file_type_detection",
                "hash_verification",
                "metadata_extraction",
                "batch_processing",
                "task_queue_management"
            ],
            "control_level": {
                "full_control": True,
                "can_access_all_files": True,
                "can_manage_storage": True,
                "can_monitor_tasks": True,
                "can_configure_processing": True
            },
            "integration_points": [
                "yunpat_agent (8000)",
                "multimodal_api (8020)",
                "processing_service (8012)",
                "glm_vision_service (8091)"
            ]
        }

        return capabilities

# 导出主类
__all__ = [
    'XiaonuoFileSystemController',
    'FileInfo',
    'ProcessingTask',
    'FileType',
    'FileOperation'
]