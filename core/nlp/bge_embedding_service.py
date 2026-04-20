#!/usr/bin/env python3
from __future__ import annotations
"""
BGE-M3 嵌入服务
BGE-M3 Embedding Service for Athena Platform

提供高性能的多语言文本嵌入服务,专门优化专利和法律领域

作者: 小诺·双鱼座
创建时间: 2025-12-16
更新时间: 2026-04-19 (迁移至BGE-M3)
"""
import asyncio
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


@dataclass
class EmbeddingResult:
    """嵌入结果"""

    embeddings: list[list[float]]  # 嵌入向量
    dimension: int  # 向量维度
    model_name: str  # 模型名称
    processing_time: float  # 处理时间
    batch_size: int  # 批处理大小
    metadata: dict[str, Any]  # 元数据


class BGEEmbeddingService:
    """BGE嵌入服务"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.name = "BGE-M3嵌入服务"
        self.version = "2.0.0"
        self.logger = logging.getLogger(self.name)

        # 配置
        self.config = config or {
            "model_path": "BAAI/bge-m3",  # 使用HuggingFace模型名称，自动检测本地缓存
            "device": "cpu",  # 使用CPU(避免MPS兼容性问题)
            "batch_size": 32,
            "max_length": 8192,  # BGE-M3支持8192长度
            "normalize_embeddings": True,
            "cache_enabled": True,
            "preload": True,
        }

        # 模型状态
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self.load_lock = threading.Lock()

        # 缓存
        self.embedding_cache: dict[str, Any] = {}
        self.cache_lock = threading.Lock()
        self.redis_cache = None  # Redis持久化缓存

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "total_texts": 0,
            "cache_hits": 0,
            "total_processing_time": 0.0,
            "avg_batch_size": 0.0,
        }

        print(f"🚀 {self.name} 初始化完成")

    def _load_model(self) -> Any:
        """加载BGE-M3模型"""
        with self.load_lock:
            if self.is_loaded:
                return

            try:
                from sentence_transformers import SentenceTransformer

                print("📦 正在加载BGE-M3模型...")
                start_time = time.time()

                # 加载模型
                self.model = SentenceTransformer(
                    self.config["model_path"], device=self.config["device"]
                )

                # 验证模型
                test_embedding = self.model.encode("测试", convert_to_numpy=True)
                assert len(test_embedding) == 1024, "BGE-M3向量维度应为1024"

                load_time = time.time() - start_time
                self.is_loaded = True

                print("✅ BGE-M3模型加载成功!")
                print(f"   - 加载时间: {load_time:.2f}秒")
                print(f"   - 向量维度: {len(test_embedding)}")
                print(f"   - 设备: {self.model.device}")

            except Exception as e:
                self.logger.error(f"BGE-M3模型加载失败: {e}")
                raise e

    async def initialize(self):
        """异步初始化"""
        # 初始化Redis缓存
        if self.config.get("cache_enabled", True):
            try:
                from ..cache.bge_redis_cache import get_bge_redis_cache

                self.redis_cache = await get_bge_redis_cache()
                self.logger.info("BGE Redis缓存已连接")
            except Exception as e:
                self.logger.warning(f"Redis缓存初始化失败: {e}")

        # 预加载模型
        if self.config.get("preload", True):
            # 在线程池中加载模型
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)

    def _get_cache_key(self, texts: list[str]) -> str:
        """生成缓存键"""
        import hashlib

        combined_text = "|||".join(texts)
        return hashlib.md5(combined_text.encode("utf-8"), usedforsecurity=False).hexdigest()

    async def _check_cache(
        self, texts: list[str], task_type: str = "default"
    ) -> list[list[float | None]]:
        """检查缓存(先检查Redis,再检查内存)"""
        if not self.config.get("cache_enabled", True):
            return None

        # 检查Redis缓存
        if self.redis_cache:
            for text in texts:
                cached = await self.redis_cache.get(text, task_type)
                if cached:
                    self.stats["cache_hits"] += 1
                    return [cached]

        # 检查内存缓存
        cache_key = self._get_cache_key(texts)
        with self.cache_lock:
            if cache_key in self.embedding_cache:
                self.stats["cache_hits"] += 1
                return self.embedding_cache[cache_key]

        return None

    def _save_to_cache(self, texts: list[str], embeddings: list[list[float]]) -> Any:
        """保存到缓存"""
        if not self.config.get("cache_enabled", True):
            return

        cache_key = self._get_cache_key(texts)
        with self.cache_lock:
            # 限制缓存大小
            if len(self.embedding_cache) >= 1000:
                # 删除最旧的一半
                items = list(self.embedding_cache.items())
                self.embedding_cache = dict(items[len(items) // 2 :])

            self.embedding_cache[cache_key] = embeddings

    async def encode(
        self,
        texts: str | list[str],
        task_type: str = "default",
        batch_size: int | None = None,
    ) -> EmbeddingResult:
        """
        文本编码

        Args:
            texts: 文本或文本列表
            task_type: 任务类型(用于优化)
            batch_size: 批处理大小

        Returns:
            EmbeddingResult: 嵌入结果
        """
        # 确保模型已加载
        if not self.is_loaded:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)

        # 标准化输入
        if isinstance(texts, str):
            texts = [texts]
            single_text = True
        else:
            single_text = False

        # 检查缓存
        cached_embeddings = await self._check_cache(texts, task_type)
        if cached_embeddings is not None and (
            not isinstance(cached_embeddings, list) or len(cached_embeddings) > 0
        ):
            return EmbeddingResult(
                embeddings=cached_embeddings[0] if single_text else cached_embeddings,
                dimension=1024,
                model_name="bge-m3",
                processing_time=0.001,
                batch_size=len(texts),
                metadata={"cache_hit": True, "task_type": task_type},
            )

        # 编码处理
        start_time = time.time()

        try:
            # 在线程池中执行编码
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, self._encode_batch, texts, batch_size or self.config["batch_size"]
            )

            processing_time = time.time() - start_time

            # 更新统计
            self.stats["total_requests"] += 1
            self.stats["total_texts"] += len(texts)
            self.stats["total_processing_time"] += processing_time
            self.stats["avg_batch_size"] = (
                self.stats["avg_batch_size"] * (self.stats["total_requests"] - 1) + len(texts)
            ) / self.stats["total_requests"]

            # 保存到缓存
            self._save_to_cache(texts, embeddings)

            # 转换为列表格式
            embedding_list = [
                emb.tolist() if isinstance(emb, np.ndarray) else emb for emb in embeddings
            ]

            return EmbeddingResult(
                embeddings=embedding_list[0] if single_text else embedding_list,
                dimension=1024,
                model_name="bge-m3",
                processing_time=processing_time,
                batch_size=len(texts),
                metadata={
                    "cache_hit": False,
                    "task_type": task_type,
                    "device": str(self.model.device),
                },
            )

        except Exception as e:
            self.logger.error(f"编码失败: {e}")
            raise e

    def _encode_batch(self, texts: list[str], batch_size: int) -> list[np.ndarray]:
        """批量编码(在线程池中执行)"""
        # 根据任务类型优化提示
        if self.config.get("normalize_embeddings", True):
            # BGE v1.5 的提示优化
            if texts and len(texts) == 1:
                # 单个文本的提示优化
                text = texts[0]
                if "专利" in text or "权利要求" in text:
                    text = f"为这个专利生成向量用于语义检索:{text}"
                elif "法律" in text or "条款" in text:
                    text = f"为这个法律文本生成向量用于分析:{text}"
                texts = [text]

        # 执行编码
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=self.config.get("normalize_embeddings", True),
            show_progress_bar=False,
        )

        return embeddings

    async def encode_with_cache(
        self, texts: str | list[str] | None, cache_key: str | None = None
    ) -> EmbeddingResult:
        """带缓存键的编码(用于持久化缓存)"""
        # TODO: 集成Redis缓存
        return await self.encode(texts)

    def get_model_info(self) -> dict[str, Any]:
        """获取模型信息"""
        return {
            "name": "BGE-M3",
            "dimension": 1024,
            "max_length": self.config.get("max_length", 8192),
            "device": str(self.model.device) if self.model else "not_loaded",
            "batch_size": self.config.get("batch_size", 32),
            "normalize_embeddings": self.config.get("normalize_embeddings", True),
            "cache_enabled": self.config.get("cache_enabled", True),
            "cache_size": len(self.embedding_cache),
        }

    def get_statistics(self) -> dict[str, Any]:
        """获取使用统计"""
        avg_time = (
            self.stats["total_processing_time"] / self.stats["total_requests"]
            if self.stats["total_requests"] > 0
            else 0
        )

        cache_hit_rate = (
            self.stats["cache_hits"] / self.stats["total_requests"]
            if self.stats["total_requests"] > 0
            else 0
        )

        return {
            "total_requests": self.stats["total_requests"],
            "total_texts": self.stats["total_texts"],
            "cache_hits": self.stats["cache_hits"],
            "cache_hit_rate": f"{cache_hit_rate:.2%}",
            "avg_processing_time": f"{avg_time:.3f}s",
            "avg_batch_size": f"{self.stats['avg_batch_size']:.1f}",
            "texts_per_second": f"{self.stats['total_texts'] / (self.stats['total_processing_time'] + 0.001):.1f}",
            "memory_cache_size": len(self.embedding_cache),
        }

    def clear_cache(self) -> None:
        """清理缓存"""
        with self.cache_lock:
            self.embedding_cache.clear()
        print("✅ BGE缓存已清理")

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        try:
            # 测试编码
            test_result = await self.encode("健康检查测试")

            return {
                "status": "healthy",
                "model_loaded": self.is_loaded,
                "test_encoding": True,
                "dimension": (
                    len(test_result.embeddings)
                    if isinstance(test_result.embeddings, list)
                    else test_result.dimension
                ),
                "response_time": test_result.processing_time,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "model_loaded": self.is_loaded}


# 全局实例
_bge_service = None


async def get_bge_service(config: dict[str, Any] | None = None) -> BGEEmbeddingService:
    """获取BGE服务实例"""
    global _bge_service
    if _bge_service is None:
        _bge_service = BGEEmbeddingService(config)
        await _bge_service.initialize()
    return _bge_service


# 导出
__all__ = ["BGEEmbeddingService", "EmbeddingResult", "get_bge_service"]
