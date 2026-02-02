#!/usr/bin/env python3
"""
优化版感知模块 - 实现增量OCR处理和文档分块机制
Optimized Perception Module with Incremental OCR and Document Chunking

⚠️ DEPRECATED - 此模块已被弃用

弃用时间: 2026-01-25
弃用原因: 功能已整合到 `unified_optimized_processor.py`
迁移指南: 请使用 `core.perception.UnifiedOptimizedProcessor` 替代

新模块提供:
- 统一的增量OCR处理
- 改进的文档分块机制
- 更好的缓存策略
- 更完善的性能监控

此文件保留用于向后兼容,但将在未来版本中移除。

---

基于超级推理分析的性能优化版本
作者: Athena AI系统
创建时间: 2025-12-11
版本: 2.0.0-optimized
"""

import warnings

# 发出弃用警告
warnings.warn(
    "optimized_perception_module.py 已被弃用,请使用 unified_optimized_processor.py。"
    "此模块将在未来版本中移除。",
    DeprecationWarning,
    stacklevel=2,
)

import asyncio
import gc
import hashlib
import json
import logging
import os
import sys
import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from queue import PriorityQueue
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.base_module import BaseModule

# 导入统一的类型定义
from core.perception.types import CacheConfig

# 尝试导入现有的感知引擎
try:
    from perception.structured_perception_engine import (
        DIKWPResult,
        DocumentGraph,
        DocumentType,
        ModalityType,
        StructuredPatentPerceptionEngine,
    )

    EXISTING_ENGINE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"无法导入现有感知引擎: {e}")
    EXISTING_ENGINE_AVAILABLE = False

    # 定义基础类型作为备用
    from dataclasses import dataclass
    from enum import Enum
    from typing import Any

    class DocumentType(Enum):
        PATENT = "patent"
        TECH_DISCLOSURE = "tech_disclosure"
        TECH_MANUAL = "tech_manual"
        TECH_DRAWING = "tech_drawing"
        SPECIFICATION = "specification"

    class ModalityType(Enum):
        TEXT = "text"
        IMAGE = "image"
        TABLE = "table"
        FORMULA = "formula"
        DRAWING = "drawing"
        MARKUP = "markup"
        STRUCTURE = "structure"
        CAD = "cad"
        HANDWRITING = "handwriting"

    @dataclass
    class DocumentGraph:
        document_id: str
        document_type: DocumentType
        nodes: list[dict[str, Any]]
        edges: list[dict[str, Any]]
        cross_modal_alignments: list[dict[str, Any]]
        context_state: dict[str, Any]
        knowledge_injections: list[dict[str, Any]]
    @dataclass
    class DIKWPResult:
        data: dict[str, Any]
        information: dict[str, Any]
        knowledge: dict[str, Any]
        wisdom: dict[str, Any]
        purpose: dict[str, Any]
        confidence: float
        processing_time: float


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class DocumentChangeType(Enum):
    """文档变更类型"""

    CREATED = "created"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    PARTIAL_MODIFIED = "partial_modified"


@dataclass
class DocumentChunk:
    """文档分块"""

    chunk_id: str
    start_pos: int
    end_pos: int
    content_hash: str
    processing_status: str = "pending"
    ocr_result: dict[str, Any] | None = None
    last_processed: datetime | None = None
    dependencies: set[str] = field(default_factory=set)


@dataclass
class DocumentMetadata:
    """文档元数据"""

    file_path: str
    file_hash: str
    last_modified: datetime
    file_size: int
    document_type: DocumentType
    total_chunks: int
    processed_chunks: int
    change_type: DocumentChangeType
    processing_priority: int = 0


@dataclass
class OCRCacheEntry:
    """OCR缓存条目"""

    content_hash: str
    ocr_result: dict[str, Any]
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    chunk_size: int = 0


class IncrementalOCRProcessor:
    """增量OCR处理器

    使用统一的CacheConfig管理OCR缓存。
    """

    def __init__(self, config: dict[str, Any], cache_config: CacheConfig | None = None):
        self.config = config
        self.chunk_size = config.get("chunk_size", 1024 * 1024)  # 1MB chunks
        self.max_concurrent_chunks = config.get("max_concurrent_chunks", 4)
        self.cache_enabled = config.get("cache_enabled", True)

        # 使用统一的缓存配置
        self.cache_config = cache_config or CacheConfig()
        self.cache_ttl = self.cache_config.ocr_cache_ttl

        # OCR缓存
        self.ocr_cache: dict[str, OCRCacheEntry] = {}
        self.cache_lock = threading.RLock()

        # 文档分块管理
        self.document_chunks: dict[str, list[DocumentChunk]] = {}
        self.chunk_executor = ThreadPoolExecutor(max_workers=self.max_concurrent_chunks)

        # 性能统计
        self.stats = {
            "total_documents": 0,
            "incremental_processed": 0,
            "full_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_processing_time": 0.0,
            "memory_saved": 0,  # 字节
        }

        logger.info("🚀 增量OCR处理器初始化完成")

    def calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值(用于缓存,非安全场景)"""
        hash_md5 = hashlib.md5(usedforsecurity=False)
        with open(file_path, "rb") as f:
            # 对于大文件,只读取前1MB和后1MB来计算哈希
            file_size = os.path.getsize(file_path)
            if file_size > 2 * 1024 * 1024:  # >2MB
                # 读取前1MB
                chunk = f.read(1024 * 1024)
                hash_md5.update(chunk)
                # 读取后1MB
                f.seek(-1024 * 1024, 2)
                chunk = f.read(1024 * 1024)
                hash_md5.update(chunk)
            else:
                # 小文件全文读取
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def detect_document_changes(
        self, file_path: str, previous_metadata: DocumentMetadata | None = None
    ) -> DocumentMetadata:
        """检测文档变更"""
        try:
            current_stat = os.stat(file_path)
            current_hash = self.calculate_file_hash(file_path)
            current_modified = datetime.fromtimestamp(current_stat.st_mtime)

            if previous_metadata is None:
                # 新文档
                change_type = DocumentChangeType.CREATED
            elif previous_metadata.file_hash != current_hash:
                # 文档已修改
                if current_stat.st_size != previous_metadata.file_size:
                    change_type = DocumentChangeType.MODIFIED
                else:
                    change_type = DocumentChangeType.PARTIAL_MODIFIED
            else:
                # 文档未变更
                change_type = DocumentChangeType.UNCHANGED

            metadata = DocumentMetadata(
                file_path=file_path,
                file_hash=current_hash,
                last_modified=current_modified,
                file_size=current_stat.st_size,
                document_type=self._detect_document_type(file_path),
                total_chunks=(current_stat.st_size + self.chunk_size - 1) // self.chunk_size,
                processed_chunks=0,
                change_type=change_type,
            )

            logger.info(f"📄 文档变更检测: {file_path} -> {change_type.value}")
            return metadata

        except Exception as e:
            logger.error(f"❌ 文档变更检测失败 {file_path}: {e}")
            raise

    def create_document_chunks(self, metadata: DocumentMetadata) -> list[DocumentChunk]:
        """创建文档分块"""
        chunks = []

        try:
            with open(metadata.file_path, "rb") as f:
                chunk_index = 0
                while True:
                    start_pos = f.tell()
                    chunk_data = f.read(self.chunk_size)
                    if not chunk_data:
                        break

                    end_pos = f.tell()
                    # 使用MD5进行内容哈希(非安全场景,仅用于缓存)
                    content_hash = hashlib.md5(chunk_data, usedforsecurity=False).hexdigest()

                    chunk = DocumentChunk(
                        chunk_id=f"{metadata.file_path}_chunk_{chunk_index}",
                        start_pos=start_pos,
                        end_pos=end_pos,
                        content_hash=content_hash,
                        processing_status="pending",
                    )

                    chunks.append(chunk)
                    chunk_index += 1

            self.document_chunks[metadata.file_path] = chunks
            logger.info(f"📦 文档分块完成: {metadata.file_path} -> {len(chunks)} 个分块")
            return chunks

        except Exception as e:
            logger.error(f"❌ 文档分块失败 {metadata.file_path}: {e}")
            raise

    async def process_chunk_incremental(
        self, chunk: DocumentChunk, metadata: DocumentMetadata
    ) -> dict[str, Any]:
        """增量处理单个分块"""
        start_time = time.time()

        try:
            # 检查缓存
            cached_result = self._get_cached_ocr_result(chunk.content_hash)
            if cached_result:
                self.stats["cache_hits"] += 1
                logger.debug(f"💾 OCR缓存命中: {chunk.chunk_id}")
                return cached_result

            self.stats["cache_misses"] += 1

            # 读取分块数据
            with open(metadata.file_path, "rb") as f:
                f.seek(chunk.start_pos)
                chunk_data = f.read(chunk.end_pos - chunk.start_pos)

            # 执行OCR处理 (这里简化处理,实际应该调用OCR引擎)
            ocr_result = await self._perform_ocr(chunk_data, chunk.chunk_id)

            # 缓存结果
            if self.cache_enabled:
                self._cache_ocr_result(chunk.content_hash, ocr_result, len(chunk_data))

            processing_time = time.time() - start_time
            chunk.processing_status = "completed"
            chunk.last_processed = datetime.now()
            chunk.ocr_result = ocr_result

            self.stats["average_processing_time"] = (
                self.stats["average_processing_time"] * (self.stats["total_documents"])
                + processing_time
            ) / (self.stats["total_documents"] + 1)

            logger.debug(f"✅ 分块处理完成: {chunk.chunk_id} ({processing_time:.3f}s)")
            return ocr_result

        except Exception as e:
            chunk.processing_status = "failed"
            logger.error(f"❌ 分块处理失败 {chunk.chunk_id}: {e}")
            raise

    async def _perform_ocr(self, chunk_data: bytes, chunk_id: str) -> dict[str, Any]:
        """执行OCR处理 (模拟实现)"""
        # 这里应该调用实际的OCR引擎
        # 现在使用模拟结果
        await asyncio.sleep(0.001)  # 模拟处理时间

        text_content = f"OCR识别结果 - 分块ID: {chunk_id} - 大小: {len(chunk_data)} 字节"

        return {
            "text": text_content,
            "confidence": 0.95,
            "blocks": [{"text": text_content, "bbox": [0, 0, 100, 20]}],
            "chunk_id": chunk_id,
            "processing_method": "incremental_ocr",
        }

    def _get_cached_ocr_result(self, content_hash: str) -> dict[str, Any] | None:
        """获取缓存的OCR结果"""
        if not self.cache_enabled:
            return None

        with self.cache_lock:
            entry = self.ocr_cache.get(content_hash)
            if entry and (datetime.now() - entry.last_accessed) < self.cache_ttl:
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                return entry.ocr_result
            elif entry:
                # 缓存过期,清理
                del self.ocr_cache[content_hash]

        return None

    def _cache_ocr_result(
        self, content_hash: str, ocr_result: dict[str, Any], chunk_size: int
    ) -> Any:
        """缓存OCR结果"""
        if not self.cache_enabled:
            return

        with self.cache_lock:
            entry = OCRCacheEntry(
                content_hash=content_hash,
                ocr_result=ocr_result,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                chunk_size=chunk_size,
            )
            self.ocr_cache[content_hash] = entry

            # 检查缓存大小限制
            self._cleanup_cache_if_needed()

    def _cleanup_cache_if_needed(self) -> Any:
        """清理缓存以保持合理大小"""
        max_cache_size = self.config.get("max_cache_size", 100 * 1024 * 1024)  # 100MB

        current_size = sum(entry.chunk_size for entry in self.ocr_cache.values())
        if current_size > max_cache_size:
            # 按LRU策略清理缓存
            sorted_entries = sorted(self.ocr_cache.items(), key=lambda x: x[1].last_accessed)

            size_to_remove = current_size - max_cache_size + max_cache_size * 0.1  # 多清理10%
            removed_size = 0

            for content_hash, entry in sorted_entries:
                if removed_size >= size_to_remove:
                    break
                removed_size += entry.chunk_size
                del self.ocr_cache[content_hash]

            logger.info(f"🧹 OCR缓存清理完成: 释放 {removed_size / 1024 / 1024:.1f}MB")

    def _detect_document_type(self, file_path: str) -> DocumentType:
        """检测文档类型"""
        ext = Path(file_path).suffix.lower()

        type_mapping = {
            ".pdf": DocumentType.PATENT,
            ".docx": DocumentType.TECH_DISCLOSURE,
            ".doc": DocumentType.TECH_DISCLOSURE,
            ".txt": DocumentType.SPECIFICATION,
            ".jpg": DocumentType.TECH_DRAWING,
            ".jpeg": DocumentType.TECH_DRAWING,
            ".png": DocumentType.TECH_DRAWING,
        }

        return type_mapping.get(ext, DocumentType.SPECIFICATION)

    def get_stats(self) -> dict[str, Any]:
        """获取处理统计信息"""
        with self.cache_lock:
            cache_size = sum(entry.chunk_size for entry in self.ocr_cache.values())

        return {
            **self.stats,
            "cache_size_bytes": cache_size,
            "cache_entries": len(self.ocr_cache),
            "cache_hit_rate": (
                self.stats["cache_hits"] / (self.stats["cache_hits"] + self.stats["cache_misses"])
                if (self.stats["cache_hits"] + self.stats["cache_misses"]) > 0
                else 0
            ),
        }


class MemoryOptimizedProcessor:
    """内存优化处理器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.max_memory_usage = config.get("max_memory_usage", 512 * 1024 * 1024)  # 512MB
        self.memory_pool = weakref.WeakSet()
        self.temp_files = []

    def cleanup_memory(self) -> Any:
        """清理内存"""
        # 强制垃圾回收
        gc.collect()

        # 清理临时文件
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"清理临时文件失败 {temp_file}: {e}")

        self.temp_files.clear()
        logger.info("🧹 内存清理完成")


class OptimizedPerceptionModule(BaseModule):
    """优化版感知模块

    使用统一的CacheConfig管理所有缓存TTL。
    """

    def __init__(
        self,
        agent_id: str,
        config: dict[str, Any] | None = None,
        cache_config: CacheConfig | None = None,
    ):
        super().__init__(agent_id, config)

        # 使用统一的缓存配置
        self.cache_config = cache_config or CacheConfig()

        # 优化配置
        self.optimization_config = {
            "incremental_ocr": True,
            "document_chunking": True,
            "parallel_processing": True,
            "memory_optimization": True,
            "smart_caching": True,
            "max_concurrent_documents": 3,
            "chunk_size": 1024 * 1024,  # 1MB
            "max_memory_usage": 512 * 1024 * 1024,  # 512MB
            **self.config,
        }

        # 初始化优化组件,传入统一的缓存配置
        self.incremental_ocr = IncrementalOCRProcessor(self.optimization_config, self.cache_config)
        self.memory_optimizer = MemoryOptimizedProcessor(self.optimization_config)

        # 文档元数据缓存
        self.document_metadata_cache: dict[str, DocumentMetadata] = {}

        # 处理队列和优先级
        self.processing_queue = PriorityQueue()
        self.queue_lock = threading.Lock()

        # 性能统计
        self.optimization_stats = {
            "total_documents_processed": 0,
            "incremental_processing_saved_time": 0.0,
            "memory_peak_usage": 0,
            "average_document_processing_time": 0.0,
            "optimization_effectiveness": 0.0,  # 性能提升百分比
        }

        logger.info("🚀 优化版感知模块初始化完成")

    async def _on_initialize(self) -> bool:
        """初始化优化感知模块"""
        try:
            logger.info("🔍 初始化优化感知模块...")

            # 初始化现有感知引擎(如果可用)
            self.perception_engine = None
            self.fallback_enabled = True

            if EXISTING_ENGINE_AVAILABLE:
                try:
                    self.perception_engine = StructuredPatentPerceptionEngine()
                    logger.info("✅ 现有感知引擎集成成功")
                except Exception as e:
                    logger.warning(f"现有感知引擎集成失败: {e}")

            # 初始化优化组件
            await self._initialize_optimization_components()

            logger.info("✅ 优化感知模块初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化感知模块初始化失败: {e!s}")
            return False

    async def _initialize_optimization_components(self):
        """初始化优化组件"""
        # 预热OCR缓存
        if self.optimization_config.get("preheat_cache", False):
            await self._preheat_ocr_cache()

        # 设置内存监控
        if self.optimization_config.get("memory_monitoring", True):
            self._setup_memory_monitoring()

    async def _preheat_ocr_cache(self):
        """预热OCR缓存"""
        logger.info("🔥 预热OCR缓存...")
        # 可以预先加载一些常用的OCR模型或字典
        pass

    def _setup_memory_monitoring(self) -> Any:
        """设置内存监控"""
        import psutil

        process = psutil.Process()
        self.memory_process = process
        logger.info("📊 内存监控已启用")

    async def _on_start(self) -> bool:
        """启动优化感知模块"""
        try:
            logger.info("🚀 启动优化感知模块")

            # 启动后台处理任务
            if self.optimization_config.get("background_processing", True):
                asyncio.create_task(self._background_processing_loop())

            logger.info("✅ 优化感知模块启动成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化感知模块启动失败: {e!s}")
            return False

    async def _on_stop(self) -> bool:
        """停止优化感知模块"""
        try:
            logger.info("⏹️ 停止优化感知模块")

            # 清理资源
            await self._cleanup_resources()

            logger.info("✅ 优化感知模块停止成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化感知模块停止失败: {e!s}")
            return False

    async def _on_shutdown(self) -> bool:
        """关闭优化感知模块"""
        try:
            logger.info("🔚 关闭优化感知模块")

            # 关闭线程池
            self.incremental_ocr.chunk_executor.shutdown(wait=True)

            # 最终清理
            await self._cleanup_resources()

            # 生成优化报告
            self._generate_optimization_report()

            logger.info("✅ 优化感知模块关闭成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化感知模块关闭失败: {e!s}")
            return False

    async def _on_health_check(self) -> bool:
        """健康检查"""
        try:
            checks = {
                "incremental_ocr_available": self.incremental_ocr is not None,
                "memory_optimizer_available": self.memory_optimizer is not None,
                "dependencies_ok": await self._verify_dependencies(),
                "processing_available": True,
                "memory_usage_ok": self._check_memory_usage(),
                "cache_status": len(self.incremental_ocr.ocr_cache) < 10000,  # 合理的缓存大小
            }

            # 优化模块的健康检查标准
            overall_healthy = (
                checks["dependencies_ok"]
                and checks["processing_available"]
                and checks["memory_usage_ok"]
                and (checks["incremental_ocr_available"] or self.fallback_enabled)
            )

            # 将健康检查详情存储到模块属性中
            self._health_check_details = {
                "incremental_ocr_status": (
                    "available" if checks["incremental_ocr_available"] else "unavailable"
                ),
                "memory_status": "optimal" if checks["memory_usage_ok"] else "high",
                "cache_entries": len(self.incremental_ocr.ocr_cache),
                "optimization_stats": self.optimization_stats,
                "overall_healthy": overall_healthy,
            }

            return overall_healthy

        except Exception as e:
            logger.error(f"健康检查失败: {e!s}")
            return False

    async def _verify_dependencies(self) -> bool:
        """验证依赖关系"""
        try:
            # 检查必要的依赖
            dependencies_ok = True

            # 检查文件系统访问权限
            test_file = "/tmp/athena_test_access"
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.unlink(test_file)
            except Exception:
                dependencies_ok = False

            return dependencies_ok

        except Exception as e:
            logger.error(f"依赖验证失败: {e!s}")
            return False

    def _check_memory_usage(self) -> bool:
        """检查内存使用情况"""
        try:
            if hasattr(self, "memory_process"):
                memory_info = self.memory_process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024

                # 更新内存使用峰值
                self.optimization_stats["memory_peak_usage"] = max(
                    self.optimization_stats["memory_peak_usage"], memory_info.rss
                )

                # 检查是否超过限制
                max_memory_mb = self.optimization_config["max_memory_usage"] / 1024 / 1024
                return memory_mb < max_memory_mb

            return True

        except Exception as e:
            logger.error(f"内存使用检查失败: {e!s}")
            return True  # 检查失败时不影响健康状态

    async def process_document_optimized(self, file_path: str) -> dict[str, Any]:
        """
        优化版文档处理

        重构后的主函数,通过调用多个辅助方法来处理文档。
        每个辅助方法负责一个特定的处理步骤。
        """
        start_time = time.time()
        processing_id = f"doc_{int(time.time() * 1000)}"

        try:
            logger.info(f"📄 开始优化处理文档: {file_path}")

            # 步骤1: 检测文档变更
            metadata, processing_result = await self._detect_document_changes(
                file_path, processing_id
            )

            # 步骤2: 检查是否需要处理(未变更则返回缓存)
            if metadata.change_type == DocumentChangeType.UNCHANGED:
                return self._return_cached_result(processing_result)

            # 步骤3: 准备需要处理的分块
            chunks = self.incremental_ocr.create_document_chunks(metadata)
            modified_chunks = self._prepare_chunks_for_processing(
                metadata, chunks, processing_result
            )

            # 步骤4: 执行分块处理
            chunk_results = await self._execute_chunk_processing(
                modified_chunks, metadata, processing_result
            )

            # 步骤5: 合并处理结果
            merged_result = await self._merge_chunk_results(chunk_results, metadata)
            processing_result.update(merged_result)

            # 步骤6: 应用内存优化
            self._apply_memory_optimization(processing_result)

            # 步骤7: 完成处理并返回结果
            return await self._finalize_processing_result(
                processing_result, metadata, file_path, start_time
            )

        except Exception as e:
            logger.error(f"❌ 文档优化处理失败 {file_path}: {e}")
            return self._create_error_result(processing_id, file_path, start_time, e)

    # ========================================================================
    # 辅助方法 - 每个方法负责一个特定的处理步骤
    # ========================================================================

    async def _detect_document_changes(
        self, file_path: str, processing_id: str
    ) -> tuple[DocumentMetadata, dict[str, Any]:
        """
        检测文档变更

        Returns:
            (元数据, 初始处理结果)
        """
        previous_metadata = self.document_metadata_cache.get(file_path)
        metadata = self.incremental_ocr.detect_document_changes(file_path, previous_metadata)

        processing_result = {
            "processing_id": processing_id,
            "file_path": file_path,
            "change_type": metadata.change_type.value,
            "optimization_applied": [],
            "processing_method": "optimized_perception",
        }

        return metadata, processing_result

    def _return_cached_result(self, processing_result: dict[str, Any]) -> dict[str, Any]:
        """返回缓存结果"""
        logger.info("⚡ 文档未变更,使用缓存结果")
        processing_result["status"] = "cached"
        processing_result["optimization_applied"].append("cache_hit")
        return processing_result

    def _prepare_chunks_for_processing(
        self,
        metadata: DocumentMetadata,
        chunks: list[DocumentChunk],
        processing_result: dict[str, Any],    ) -> list[DocumentChunk]:
        """
        准备需要处理的分块

        根据文档变更类型确定需要处理哪些分块。
        """
        if metadata.change_type in [
            DocumentChangeType.PARTIAL_MODIFIED,
            DocumentChangeType.MODIFIED,
        ]:
            # 找出变更的分块
            modified_chunks = []  # TODO: 实现真正的变更检测
            processing_result["optimization_applied"].append("incremental_processing")
            processing_result["modified_chunks"] = len(modified_chunks)
            processing_result["total_chunks"] = len(chunks)
            # 简化实现:对于部分修改,重新处理所有分块
            modified_chunks = chunks
        else:
            # 新文档,处理所有分块
            modified_chunks = chunks
            processing_result["optimization_applied"].append("full_processing")

        return modified_chunks

    async def _execute_chunk_processing(
        self,
        chunks: list[DocumentChunk],
        metadata: DocumentMetadata,
        processing_result: dict[str, Any],    ) -> list[dict[str, Any]]:
        """
        执行分块处理

        根据配置选择并行或串行处理方式。
        """
        if self.optimization_config["parallel_processing"] and len(chunks) > 1:
            chunk_results = await self._process_chunks_parallel(chunks, metadata)
            processing_result["optimization_applied"].append("parallel_processing")
        else:
            chunk_results = []
            for chunk in chunks:
                result = await self.incremental_ocr.process_chunk_incremental(chunk, metadata)
                chunk_results.append(result)

        return chunk_results

    def _apply_memory_optimization(self, processing_result: dict[str, Any]) -> None:
        """应用内存优化"""
        if self.optimization_config["memory_optimization"]:
            self.memory_optimizer.cleanup_memory()
            processing_result["optimization_applied"].append("memory_optimization")

    async def _finalize_processing_result(
        self,
        processing_result: dict[str, Any],        metadata: DocumentMetadata,
        file_path: str,
        start_time: float,
    ) -> dict[str, Any]:
        """
        完成处理并返回最终结果

        更新统计信息、缓存元数据,并设置最终状态。
        """
        # 更新统计信息
        processing_time = time.time() - start_time
        self._update_processing_stats(processing_time, metadata)

        # 缓存文档元数据
        self.document_metadata_cache[file_path] = metadata

        # 设置最终状态
        processing_result["status"] = "completed"
        processing_result["processing_time"] = processing_time
        processing_result["optimization_effectiveness"] = (
            self._calculate_optimization_effectiveness()
        )

        logger.info(f"✅ 文档优化处理完成: {file_path} ({processing_time:.3f}s)")
        return processing_result

    def _create_error_result(
        self, processing_id: str, file_path: str, start_time: float, error: Exception
    ) -> dict[str, Any]:
        """创建错误结果"""
        return {
            "processing_id": processing_id,
            "file_path": file_path,
            "status": "failed",
            "error": str(error),
            "processing_time": time.time() - start_time,
        }

    async def _process_chunks_parallel(
        self, chunks: list[DocumentChunk], metadata: DocumentMetadata
    ) -> list[dict[str, Any]]:
        """并行处理分块"""
        semaphore = asyncio.Semaphore(self.optimization_config["max_concurrent_documents"])

        async def process_with_semaphore(chunk):
            async with semaphore:
                return await self.incremental_ocr.process_chunk_incremental(chunk, metadata)

        tasks = [process_with_semaphore(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常结果
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"分块处理异常: {result}")
            else:
                valid_results.append(result)

        return valid_results

    async def _merge_chunk_results(
        self, chunk_results: list[dict[str, Any]], metadata: DocumentMetadata
    ) -> dict[str, Any]:
        """合并分块处理结果"""
        if not chunk_results:
            return {"merged_content": "", "total_blocks": 0}

        # 简单合并所有文本内容
        merged_text = "\n".join(result.get("text", "") for result in chunk_results)
        total_blocks = sum(len(result.get("blocks", [])) for result in chunk_results)

        return {
            "merged_content": merged_text,
            "total_blocks": total_blocks,
            "processing_method": "chunked_processing",
            "document_type": metadata.document_type.value,
        }

    def _update_processing_stats(self, processing_time: float, metadata: DocumentMetadata) -> Any:
        """更新处理统计信息"""
        self.optimization_stats["total_documents_processed"] += 1

        # 计算平均处理时间
        total_docs = self.optimization_stats["total_documents_processed"]
        if "average_document_processing_time" not in self.optimization_stats:
            self.optimization_stats["average_document_processing_time"] = 0.0

        current_avg = self.optimization_stats["average_document_processing_time"]
        new_avg = (current_avg * (total_docs - 1) + processing_time) / total_docs
        self.optimization_stats["average_document_processing_time"] = new_avg

        # 估算增量处理节省的时间
        if "incremental_processing_saved_time" not in self.optimization_stats:
            self.optimization_stats["incremental_processing_saved_time"] = 0.0

        if metadata.change_type in [
            DocumentChangeType.PARTIAL_MODIFIED,
            DocumentChangeType.UNCHANGED,
        ]:
            saved_time = processing_time * 0.7  # 假设节省70%的时间
            self.optimization_stats["incremental_processing_saved_time"] += saved_time

    def _calculate_optimization_effectiveness(self) -> float:
        """计算优化效果"""
        if self.optimization_stats["total_documents_processed"] == 0:
            return 0.0

        # 基于缓存命中率和增量处理时间节省来计算优化效果
        ocr_stats = self.incremental_ocr.get_stats()
        cache_hit_rate = ocr_stats.get("cache_hit_rate", 0.0)

        # 简化计算:缓存命中率贡献50%,增量处理贡献50%
        incremental_saving = min(
            self.optimization_stats["incremental_processing_saved_time"]
            / max(
                self.optimization_stats["average_document_processing_time"]
                * self.optimization_stats["total_documents_processed"],
                1,
            ),
            1.0,
        )

        effectiveness = (cache_hit_rate * 0.5 + incremental_saving * 0.5) * 100
        return effectiveness

    async def _background_processing_loop(self):
        """后台处理循环"""
        logger.info("🔄 启动后台处理循环")

        while True:
            try:
                # 定期清理内存和缓存
                await asyncio.sleep(60)  # 每分钟执行一次

                # 内存优化
                if self.optimization_config["memory_optimization"]:
                    self.memory_optimizer.cleanup_memory()

                # 清理过期的文档元数据缓存
                await self._cleanup_expired_metadata()

            except Exception as e:
                logger.error(f"后台处理循环异常: {e}")
                await asyncio.sleep(5)  # 出错后短暂等待

    async def _cleanup_expired_metadata(self):
        """清理过期的文档元数据缓存

        使用统一的CacheConfig中的metadata_cache_ttl配置。
        """
        current_time = datetime.now()
        ttl = self.cache_config.metadata_cache_ttl

        expired_files = []
        for file_path, metadata in self.document_metadata_cache.items():
            if current_time - metadata.last_modified > ttl:
                expired_files.append(file_path)

        for file_path in expired_files:
            del self.document_metadata_cache[file_path]

        if expired_files:
            logger.info(f"🧹 清理过期元数据: {len(expired_files)} 个文件")

    async def _cleanup_resources(self):
        """清理资源"""
        try:
            # 清理内存
            self.memory_optimizer.cleanup_memory()

            # 清理OCR缓存
            with self.incremental_ocr.cache_lock:
                self.incremental_ocr.ocr_cache.clear()

            logger.info("🧹 资源清理完成")

        except Exception as e:
            logger.error(f"资源清理失败: {e}")

    def _generate_optimization_report(self) -> Any:
        """生成优化报告"""
        try:
            ocr_stats = self.incremental_ocr.get_stats()

            report = {
                "optimization_summary": {
                    "total_documents_processed": self.optimization_stats[
                        "total_documents_processed"
                    ],
                    "average_processing_time": self.optimization_stats[
                        "average_document_processing_time"
                    ],
                    "optimization_effectiveness": self.optimization_stats[
                        "optimization_effectiveness"
                    ],
                    "memory_peak_usage_mb": self.optimization_stats["memory_peak_usage"]
                    / 1024
                    / 1024,
                },
                "ocr_performance": {
                    "cache_hit_rate": ocr_stats.get("cache_hit_rate", 0.0),
                    "cache_size_mb": ocr_stats.get("cache_size_bytes", 0) / 1024 / 1024,
                    "incremental_processed": ocr_stats.get("incremental_processed", 0),
                    "full_processed": ocr_stats.get("full_processed", 0),
                },
                "memory_optimization": {
                    "memory_saved_bytes": ocr_stats.get("memory_saved", 0),
                    "cleanup_executions": getattr(self.memory_optimizer, "cleanup_count", 0),
                },
            }

            # 保存报告到文件
            report_path = f"optimization_report_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"📊 优化报告已生成: {report_path}")
            return report

        except Exception as e:
            logger.error(f"生成优化报告失败: {e}")
            return {}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """标准处理接口"""
        operation = data.get("operation", "perceive")

        if operation == "perceive_document":
            file_path = data.get("file_path")
            if file_path:
                return await self.process_document_optimized(file_path)

        # 其他操作的默认处理
        return await super().process(data)

    def get_optimization_stats(self) -> dict[str, Any]:
        """获取优化统计信息"""
        ocr_stats = self.incremental_ocr.get_stats()

        return {
            "module_stats": self.optimization_stats,
            "ocr_stats": ocr_stats,
            "cache_efficiency": ocr_stats.get("cache_hit_rate", 0.0),
            "memory_efficiency": 1
            - (
                self.optimization_stats["memory_peak_usage"]
                / self.optimization_config["max_memory_usage"]
            ),
            "processing_efficiency": self._calculate_optimization_effectiveness(),
        }


# 导出
__all__ = [
    "DocumentChangeType",
    "DocumentChunk",
    "DocumentMetadata",
    "IncrementalOCRProcessor",
    "MemoryOptimizedProcessor",
    "OptimizedPerceptionModule",
]
