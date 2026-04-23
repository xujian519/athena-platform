#!/usr/bin/env python3

"""
统一优化感知模块
Unified Optimized Perception Module

整合了所有优化版本的感知功能,包括:
- 增量OCR处理和文档分块
- 多级缓存策略
- 性能监控和优化
- 批处理和并发控制
- 内存优化

这是一个整合版本,替代了之前的多个分散的优化实现。

作者: Athena AI系统
创建时间: 2026-01-25
版本: 3.0.0-unified
"""

import asyncio
import gc
import hashlib
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from . import BaseProcessor, InputType, PerceptionResult
from .types import (
    CacheConfig,
    DocumentChangeType,
    DocumentChunk,
    DocumentMetadata,
    OCRCacheEntry,
    OptimizedPerceptionConfig,
)

logger = logging.getLogger(__name__)


class ProcessingStrategy(Enum):
    """处理策略枚举"""

    INCREMENTAL = "incremental"  # 增量处理(只处理变更部分)
    FULL = "full"  # 完整处理
    ADAPTIVE = "adaptive"  # 自适应(根据文档大小和变更程度选择)


@dataclass
class ProcessingStats:
    """处理统计"""

    total_documents: int = 0
    processed_chunks: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    incremental_saves: int = 0  # 增量处理节省的时间
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    memory_usage: int = 0  # 字节

    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / max(total, 1)

    @property
    def efficiency_gain(self) -> float:
        """效率提升(基于增量处理节省的时间)"""
        if self.total_documents == 0:
            return 0.0
        return (self.incremental_saves / self.total_documents) * 100


class UnifiedOptimizedProcessor(BaseProcessor):
    """统一优化处理器

    整合了所有优化功能:
    1. 增量OCR处理
    2. 文档分块
    3. 多级缓存
    4. 性能监控
    5. 内存优化
    """

    def __init__(self, processor_id: str, config: Optional[dict[str, Any]] = None):
        super().__init__(processor_id, config)

        # 配置
        self.config_dict = config or {}
        self.optimized_config = OptimizedPerceptionConfig(**self.config_dict.get("optimized", {}))

        # 文档处理状态
        self.document_registry: dict[str, DocumentMetadata] = {}
        self.chunk_registry: dict[str, DocumentChunk] = {}

        # 缓存系统
        self.ocr_cache: dict[str, OCRCacheEntry] = {}
        self.result_cache: dict[str, tuple[Any, datetime]] = {}

        # 性能统计
        self.stats = ProcessingStats()

        # 线程池(用于CPU密集型任务)
        max_workers = self.optimized_config.thread_pool_size or os.cpu_count() or 4
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # 锁(用于线程安全)
        self.cache_lock = threading.RLock()
        self.registry_lock = threading.RLock()

        logger.info(f"🚀 初始化统一优化处理器: {processor_id}")

    async def initialize(self):
        """初始化处理器"""
        if self.initialized:
            return

        logger.info(f"🔧 启动统一优化处理器: {self.processor_id}")

        try:
            # 加载注册表(如果存在持久化存储)
            await self._load_registries()

            # 初始化缓存
            await self._initialize_cache()

            # 启动后台任务
            asyncio.create_task(self._cache_cleanup_task())

            self.initialized = True
            logger.info(f"✅ 统一优化处理器启动完成: {self.processor_id}")

        except Exception as e:
            logger.error(f"❌ 统一优化处理器启动失败 {self.processor_id}: {e}")
            raise

    async def _load_registries(self) -> None:
        """加载文档和分块注册表"""
        # TODO: 从持久化存储加载注册表
        logger.debug("加载文档和分块注册表")

    async def _initialize_cache(self) -> None:
        """初始化缓存系统"""
        # 预热常用缓存
        logger.debug("初始化缓存系统")

    async def _cache_cleanup_task(self) -> None:
        """后台缓存清理任务"""
        while self.initialized:
            try:
                await asyncio.sleep(3600)  # 每小时清理一次
                self._cleanup_expired_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"缓存清理任务失败: {e}")

    def _cleanup_expired_cache(self) -> None:
        """清理过期缓存"""
        with self.cache_lock:
            current_time = datetime.now()
            cache_config = self.optimized_config.cache_config or CacheConfig()

            # 清理OCR缓存
            expired_keys = []
            for key, entry in self.ocr_cache.items():
                if current_time - entry.created_at > cache_config.ocr_cache_ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.ocr_cache[key]

            # 清理结果缓存
            expired_keys = []
            for key, (_, timestamp) in self.result_cache.items():
                if current_time - timestamp > cache_config.result_cache_ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.result_cache[key]

            if expired_keys:
                logger.debug(f"清理了 {len(expired_keys)} 个过期缓存项")

    async def process(
        self, data: Any, input_type: str, strategy: ProcessingStrategy = ProcessingStrategy.ADAPTIVE
    ) -> PerceptionResult:
        """处理输入数据(优化版本)"""
        if not self.initialized:
            raise RuntimeError("处理器未初始化")

        start_time = time.time()

        try:
            # 根据输入类型选择处理策略
            if input_type == "document" or isinstance(data, (str, Path)):
                result = await self._process_document(data, strategy)
            else:
                # 其他类型的处理
                result = await self._process_generic(data, input_type)

            # 更新统计
            processing_time = time.time() - start_time
            self.stats.total_processing_time += processing_time
            self.stats.total_documents += 1
            self.stats.average_processing_time = (
                self.stats.total_processing_time / self.stats.total_documents
            )

            return result

        except Exception as e:
            logger.error(f"❌ 处理失败 {self.processor_id}: {e}")
            raise

    async def _process_document(
        self, document_data: Any, strategy: ProcessingStrategy
    ) -> PerceptionResult:
        """处理文档(优化版本)"""
        # 获取文件路径
        if isinstance(document_data, str):
            file_path = Path(document_data)
        elif isinstance(document_data, Path):
            file_path = document_data
        else:
            # 假设是文档内容
            return await self._process_document_content(document_data)

        # 检查文件是否存在
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 获取或创建文档元数据
        metadata = await self._get_or_create_metadata(file_path)

        # 根据策略选择处理方式
        if (
            strategy == ProcessingStrategy.INCREMENTAL
            and metadata.change_type != DocumentChangeType.CREATED
        ):
            result = await self._process_incremental(file_path, metadata)
        elif strategy == ProcessingStrategy.ADAPTIVE:
            # 自适应策略:根据文档大小和变更程度选择
            if metadata.change_type == DocumentChangeType.CREATED or metadata.processed_chunks == 0:
                result = await self._process_full_document(file_path, metadata)
            else:
                result = await self._process_incremental(file_path, metadata)
        else:
            # 完整处理
            result = await self._process_full_document(file_path, metadata)

        return result

    async def _get_or_create_metadata(self, file_path: Path) -> DocumentMetadata:
        """获取或创建文档元数据"""
        with self.registry_lock:
            file_path_str = str(file_path)

            if file_path_str in self.document_registry:
                metadata = self.document_registry[file_path_str]
                # 检查文件是否变更
                current_mtime = file_path.stat().st_mtime
                if current_mtime > metadata.last_modified.timestamp():
                    # 文件已修改
                    old_hash = metadata.file_hash
                    new_hash = self._calculate_file_hash(file_path)
                    if new_hash != old_hash:
                        metadata.file_hash = new_hash
                        metadata.last_modified = datetime.fromtimestamp(current_mtime)
                        if metadata.change_type == DocumentChangeType.UNCHANGED:
                            metadata.change_type = DocumentChangeType.MODIFIED
                return metadata

            # 创建新的元数据
            file_stat = file_path.stat()
            file_hash = self._calculate_file_hash(file_path)

            # 检测文档类型
            doc_type = self._detect_document_type(file_path)

            metadata = DocumentMetadata(
                file_path=file_path_str,
                file_hash=file_hash,
                last_modified=datetime.fromtimestamp(file_stat.st_mtime),
                file_size=file_stat.st_size,
                document_type=doc_type,
                total_chunks=0,
                processed_chunks=0,
                change_type=DocumentChangeType.CREATED,
            )

            self.document_registry[file_path_str] = metadata
            return metadata

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希(用于变更检测)"""
        # 使用快速哈希算法
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            # 只读取文件开头和结尾的部分来计算哈希
            chunk_size = 8192
            for chunk in [f.read(chunk_size), f.read()[-chunk_size:]:
                if chunk:
                    hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _detect_document_type(self, file_path: Path) -> Any:
        """检测文档类型"""
        # 简化实现:基于文件扩展名
        ext = file_path.suffix.lower()
        mapping = {
            ".pdf": "DocumentType.PATENT",
            ".docx": "DocumentType.TECH_DISCLOSURE",
            ".doc": "DocumentType.TECH_MANUAL",
            ".dwg": "DocumentType.TECH_DRAWING",
        }
        return mapping.get(ext, "DocumentType.PATENT")

    async def _process_full_document(
        self, file_path: Path, metadata: DocumentMetadata
    ) -> PerceptionResult:
        """完整处理文档"""
        logger.info(f"🔄 完整处理文档: {file_path.name}")

        # 分块处理
        chunks = self._split_document(file_path, metadata)
        results = []

        for chunk in chunks:
            result = await self._process_chunk(chunk)
            results.append(result)

        # 合并结果
        final_result = self._merge_results(results, metadata)

        # 更新元数据
        with self.registry_lock:
            metadata.processed_chunks = len(chunks)
            metadata.change_type = DocumentChangeType.UNCHANGED

        return final_result

    async def _process_incremental(
        self, file_path: Path, metadata: DocumentMetadata
    ) -> PerceptionResult:
        """增量处理文档(只处理变更的部分)"""
        logger.info(f"⚡ 增量处理文档: {file_path.name}")

        # 识别变更的分块
        changed_chunks = self._identify_changed_chunks(file_path, metadata)

        if not changed_chunks:
            logger.info(f"✅ 文档无变更,跳过处理: {file_path.name}")
            # 返回缓存的结果
            return self._get_cached_result(str(file_path))

        # 只处理变更的分块
        results = []
        for chunk in changed_chunks:
            result = await self._process_chunk(chunk)
            results.append(result)

        # 合并结果
        final_result = self._merge_results(results, metadata)

        # 更新统计
        self.stats.incremental_saves += 1

        return final_result

    def _split_document(self, file_path: Path, metadata: DocumentMetadata) -> list[DocumentChunk]:
        """分块文档"""
        chunks = []
        chunk_size = self.optimized_config.chunk_size

        # 简化实现:基于文件大小均匀分块
        file_size = metadata.file_size
        num_chunks = max(1, (file_size + chunk_size - 1) // chunk_size)

        for i in range(num_chunks):
            start_pos = i * chunk_size
            end_pos = min(start_pos + chunk_size, file_size)

            chunk = DocumentChunk(
                chunk_id=f"{file_path.name}_chunk_{i}",
                start_pos=start_pos,
                end_pos=end_pos,
                content_hash="",  # 稍后计算
                processing_status="pending",
            )
            chunks.append(chunk)

        # 更新元数据
        with self.registry_lock:
            metadata.total_chunks = num_chunks

        return chunks

    def _identify_changed_chunks(
        self, file_path: Path, metadata: DocumentMetadata
    ) -> list[DocumentChunk]:
        """识别变更的分块"""
        # 简化实现:重新分块并比较哈希
        all_chunks = self._split_document(file_path, metadata)

        changed_chunks = []
        for chunk in all_chunks:
            # 计算分块哈希
            chunk.content_hash = self._calculate_chunk_hash(file_path, chunk)

            # 检查是否变更
            cache_key = self._get_chunk_cache_key(str(file_path), chunk.chunk_id)
            if cache_key not in self.ocr_cache:
                # 新分块或已变更
                chunk.processing_status = "pending"
                changed_chunks.append(chunk)

        return changed_chunks

    def _calculate_chunk_hash(self, file_path: Path, chunk: DocumentChunk) -> str:
        """计算分块哈希"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            f.seek(chunk.start_pos)
            data = f.read(chunk.end_pos - chunk.start_pos)
            hash_md5.update(data)
        return hash_md5.hexdigest()

    def _get_chunk_cache_key(self, file_path: str, chunk_id: str) -> str:
        """获取分块缓存键"""
        return f"chunk:{file_path}:{chunk_id}"

    async def _process_chunk(self, chunk: DocumentChunk) -> dict[str, Any]:
        """处理单个分块"""
        # 检查缓存
        cache_key = self._get_chunk_cache_key(chunk.chunk_id, "")

        with self.cache_lock:
            if cache_key in self.ocr_cache:
                self.stats.cache_hits += 1
                entry = self.ocr_cache[cache_key]
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                return entry.ocr_result

        # 处理分块(这里应该是实际的OCR处理)
        self.stats.cache_misses += 1

        # 模拟OCR处理
        ocr_result = {
            "chunk_id": chunk.chunk_id,
            "text": f"模拟OCR结果 for {chunk.chunk_id}",
            "confidence": 0.9,
        }

        # 缓存结果
        with self.cache_lock:
            cache_entry = OCRCacheEntry(
                content_hash=chunk.content_hash,
                ocr_result=ocr_result,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                chunk_size=chunk.end_pos - chunk.start_pos,
            )
            self.ocr_cache[cache_key] = cache_entry

        self.stats.processed_chunks += 1
        return ocr_result

    def _get_cached_result(self, file_path: str) -> PerceptionResult:
        """获取缓存的结果"""
        # 返回之前处理的结果
        return PerceptionResult(
            input_type=InputType.TEXT,
            raw_content=file_path,
            processed_content="缓存结果",
            features={},
            confidence=1.0,
            metadata={"cached": True},
            timestamp=datetime.now(),
        )

    def _merge_results(
        self, results: list[dict[str, Any], metadata: DocumentMetadata
    ) -> PerceptionResult:
        """合并处理结果"""
        # 合并所有分块的结果
        merged_text = "\n".join(r.get("text", "") for r in results)
        avg_confidence = sum(r.get("confidence", 0) for r in results) / max(len(results), 1)

        return PerceptionResult(
            input_type=InputType.TEXT,
            raw_content=metadata.file_path,
            processed_content=merged_text,
            features={
                "chunks_processed": len(results),
                "file_size": metadata.file_size,
                "document_type": metadata.document_type,
            },
            confidence=avg_confidence,
            metadata=metadata.__dict__,
            timestamp=datetime.now(),
        )

    async def _process_document_content(self, content: Any) -> PerceptionResult:
        """处理文档内容"""
        # 简化实现
        return PerceptionResult(
            input_type=InputType.TEXT,
            raw_content=content,
            processed_content=str(content),
            features={},
            confidence=0.8,
            metadata={},
            timestamp=datetime.now(),
        )

    async def _process_generic(self, data: Any, input_type: str) -> PerceptionResult:
        """处理通用数据"""
        # 简化实现
        return PerceptionResult(
            input_type=InputType.UNKNOWN,
            raw_content=data,
            processed_content=data,
            features={},
            confidence=0.5,
            metadata={},
            timestamp=datetime.now(),
        )

    async def cleanup(self):
        """清理处理器资源"""
        logger.info(f"🧹 清理统一优化处理器: {self.processor_id}")

        # 关闭线程池
        self.executor.shutdown(wait=True)

        # 清理缓存
        with self.cache_lock:
            self.ocr_cache.clear()
            self.result_cache.clear()

        # 清理注册表
        with self.registry_lock:
            self.document_registry.clear()
            self.chunk_registry.clear()

        # 强制垃圾回收
        gc.collect()

        self.initialized = False
        logger.info(f"✅ 统一优化处理器已清理: {self.processor_id}")

    def get_processing_stats(self) -> ProcessingStats:
        """获取处理统计"""
        # 更新内存使用
        self.stats.memory_usage = sum(sys.getsizeof(self) for _ in [1])  # 简化实现

        return self.stats

    def health_check(self) -> bool:
        """健康检查"""
        return self.initialized and self.executor is not None and not self.executor._shutdown


# 便捷函数
def create_unified_optimized_processor(
    processor_id: str = "unified_optimized", config: Optional[dict[str, Any]] = None
) -> UnifiedOptimizedProcessor:
    """创建统一优化处理器实例"""
    return UnifiedOptimizedProcessor(processor_id, config)


__all__ = [
    "ProcessingStats",
    "ProcessingStrategy",
    "UnifiedOptimizedProcessor",
    "create_unified_optimized_processor",
]

