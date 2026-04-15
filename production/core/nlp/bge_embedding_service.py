#!/usr/bin/env python3
"""
BGE 嵌入服务（默认 bge-m3 API 模式）
BGE Embedding Service for Athena Platform

默认通过 OpenAI 兼容 API 调用 bge-m3 (localhost:8766)，
可降级到本地 SentenceTransformer 加载 bge-large-zh-v1.5。

作者: 小诺·双鱼座
创建时间: 2025-12-16
更新: 2026-04-14 - 切换默认为 bge-m3 API
"""
from __future__ import annotations
import asyncio
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import requests

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
    """BGE嵌入服务 - 默认使用 bge-m3 API"""

    # 默认配置: bge-m3 API 优先
    DEFAULT_API_CONFIG = {
        "mode": "api",
        "api_url": "http://127.0.0.1:8766/v1",
        "api_model": "bge-m3",
        "device": "api",
        "batch_size": 8,
        "max_length": 8192,
        "normalize_embeddings": True,
        "cache_enabled": True,
        "preload": False,  # API 模式不需要预加载
    }

    DEFAULT_LOCAL_CONFIG = {
        "mode": "local",
        "model_path": "/Users/xujian/.cache/huggingface/hub/models--BAAI--bge-large-zh-v1.5/snapshots/79e7739b6ab944e86d6171e44d24c997fc1e0116",
        "device": "cpu",
        "batch_size": 32,
        "max_length": 512,
        "normalize_embeddings": True,
        "cache_enabled": True,
        "preload": True,
    }

    def __init__(self, config: dict[str, Any] | None = None):
        self.name = "BGE嵌入服务"
        self.version = "2.0.0"
        self.logger = logging.getLogger(self.name)

        # 配置：默认 API 模式，可通过 config["mode"]="local" 降级
        if config and config.get("mode") == "local":
            self.config = {**self.DEFAULT_LOCAL_CONFIG, **config}
        else:
            self.config = {**self.DEFAULT_API_CONFIG, **(config or {})}

        # 模型状态
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self.load_lock = threading.Lock()

        # API 健康状态
        self._api_available: bool | None = None

        # 缓存
        self.embedding_cache: dict[str, Any] = {}
        self.cache_lock = threading.Lock()
        self.redis_cache = None

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "total_texts": 0,
            "cache_hits": 0,
            "total_processing_time": 0.0,
            "avg_batch_size": 0.0,
        }

        mode = self.config["mode"]
        self.logger.info(f"🚀 {self.name} v{self.version} 初始化 (模式: {mode})")

    @property
    def is_api_mode(self) -> bool:
        return self.config.get("mode") == "api"

    def _check_api_health(self) -> bool:
        """检查 API 服务是否可用"""
        try:
            api_url = self.config["api_url"]
            resp = requests.post(
                f"{api_url}/embeddings",
                json={"model": self.config.get("api_model", "bge-m3"), "input": ["health"]},
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def _encode_via_api(self, texts: list[str], batch_size: int) -> list[list[float]]:
        """通过 OpenAI 兼容 API 进行嵌入"""
        api_url = self.config["api_url"]
        model = self.config.get("api_model", "bge-m3")
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = requests.post(
                f"{api_url}/embeddings",
                json={"model": model, "input": batch},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            sorted_data = sorted(data["data"], key=lambda x: x["index"])
            for item in sorted_data:
                all_embeddings.append(item["embedding"])

        return all_embeddings

    def _load_model(self) -> Any:
        """加载本地BGE模型（降级模式）"""
        with self.load_lock:
            if self.is_loaded:
                return

            try:
                from sentence_transformers import SentenceTransformer

                print("📦 正在加载 BGE Large ZH v1.5 本地模型...")
                start_time = time.time()

                self.model = SentenceTransformer(
                    self.config["model_path"], device=self.config["device"]
                )

                test_embedding = self.model.encode("测试", convert_to_numpy=True)
                assert len(test_embedding) == 1024, "向量维度应为1024"

                load_time = time.time() - start_time
                self.is_loaded = True

                print(f"✅ BGE本地模型加载成功 ({load_time:.2f}s)")

            except Exception as e:
                self.logger.error(f"本地模型加载失败: {e}")
                raise e

    async def initialize(self):
        """异步初始化"""
        if self.is_api_mode:
            # API 模式：检查服务可用性
            self._api_available = await asyncio.get_event_loop().run_in_executor(
                None, self._check_api_health
            )
            if self._api_available:
                self.logger.info("✅ bge-m3 API 服务可用")
            else:
                self.logger.warning("⚠️ bge-m3 API 不可用，将降级到本地模型")
                self.config["mode"] = "local"
                self.config.update(self.DEFAULT_LOCAL_CONFIG)
        else:
            # 本地模式：预加载模型
            if self.config.get("preload", True):
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
            if len(self.embedding_cache) >= 1000:
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
        # 标准化输入：始终转为列表处理
        if isinstance(texts, str):
            texts = [texts]

        # 检查缓存
        cached_embeddings = await self._check_cache(texts, task_type)
        if cached_embeddings is not None and (
            not isinstance(cached_embeddings, list) or len(cached_embeddings) > 0
        ):
            model_name = "bge-m3" if self.is_api_mode else "bge-large-zh-v1.5"
            return EmbeddingResult(
                embeddings=cached_embeddings,
                dimension=1024,
                model_name=model_name,
                processing_time=0.001,
                batch_size=len(texts),
                metadata={"cache_hit": True, "task_type": task_type},
            )

        # 编码处理
        start_time = time.time()
        bs = batch_size or self.config.get("batch_size", 8)

        try:
            loop = asyncio.get_event_loop()

            if self.is_api_mode:
                # API 模式
                embeddings = await loop.run_in_executor(
                    None, self._encode_via_api, texts, bs
                )
            else:
                # 本地模式
                if not self.is_loaded:
                    await loop.run_in_executor(None, self._load_model)
                raw = await loop.run_in_executor(
                    None, self._encode_batch_local, texts, bs
                )
                embeddings = [
                    emb.tolist() if isinstance(emb, np.ndarray) else emb for emb in raw
                ]

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

            model_name = "bge-m3" if self.is_api_mode else "bge-large-zh-v1.5"
            device_info = "api" if self.is_api_mode else str(self.model.device)

            return EmbeddingResult(
                embeddings=embeddings,
                dimension=1024,
                model_name=model_name,
                processing_time=processing_time,
                batch_size=len(texts),
                metadata={
                    "cache_hit": False,
                    "task_type": task_type,
                    "device": device_info,
                },
            )

        except Exception as e:
            self.logger.error(f"编码失败: {e}")
            raise e

    def _encode_batch_local(self, texts: list[str], batch_size: int) -> list[np.ndarray]:
        """本地批量编码"""
        if self.config.get("normalize_embeddings", True):
            if texts and len(texts) == 1:
                text = texts[0]
                if "专利" in text or "权利要求" in text:
                    text = f"为这个专利生成向量用于语义检索:{text}"
                elif "法律" in text or "条款" in text:
                    text = f"为这个法律文本生成向量用于分析:{text}"
                texts = [text]

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
        """带缓存键的编码"""
        return await self.encode(texts)

    def get_model_info(self) -> dict[str, Any]:
        """获取模型信息"""
        model_name = "bge-m3" if self.is_api_mode else "bge-large-zh-v1.5"
        return {
            "name": model_name,
            "mode": self.config.get("mode", "api"),
            "dimension": 1024,
            "max_length": self.config.get("max_length", 8192),
            "device": "api" if self.is_api_mode else (str(self.model.device) if self.model else "not_loaded"),
            "batch_size": self.config.get("batch_size", 8),
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
            test_result = await self.encode("健康检查测试")

            return {
                "status": "healthy",
                "model_loaded": self.is_loaded or self.is_api_mode,
                "test_encoding": True,
                "mode": "api" if self.is_api_mode else "local",
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
