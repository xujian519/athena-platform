#!/usr/bin/env python3
from __future__ import annotations
"""
Athena 感知模块 - 企业级Redis缓存管理器
支持OCR结果缓存、图像特征缓存、向量缓存
最后更新: 2026-01-26
"""

import asyncio
import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class RedisCacheManager:
    """
    企业级Redis缓存管理器

    功能：
    - OCR结果缓存
    - 图像特征缓存
    - 向量嵌入缓存
    - 自动失效策略
    - 缓存预热
    - 缓存统计
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 3600,
        max_memory: int = 1024 * 1024 * 512  # 512MB
    ):
        """
        初始化Redis缓存管理器

        Args:
            redis_url: Redis连接URL
            default_ttl: 默认缓存过期时间（秒）
            max_memory: 最大内存使用量（字节）
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.max_memory = max_memory
        self._redis_client = None
        self._connected = False

        # 缓存统计
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }

        # 检查Redis可用性
        self._check_availability()

    def _check_availability(self):
        """检查Redis是否可用"""
        try:
            import redis
            self._redis_module = redis
            self._connected = True
            logger.info("✓ Redis缓存管理器已初始化")
        except ImportError:
            logger.warning("⚠ Redis模块不可用，请安装: pip install redis")
            self._connected = False

    async def connect(self):
        """连接到Redis"""
        if not self._connected:
            logger.warning("Redis不可用，跳过连接")
            return False

        try:
            self._redis_client = await self._redis_module.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50
            )
            await self._redis_client.ping()
            logger.info("✓ Redis连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        """断开Redis连接"""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("✓ Redis连接已关闭")

    def is_available(self) -> bool:
        """检查Redis是否可用"""
        return self._connected and self._redis_client is not None

    def _generate_key(
        self,
        prefix: str,
        identifier: str,
        params: Optional[dict[str, Any]] = None
    ) -> str:
        """
        生成缓存键

        Args:
            prefix: 键前缀
            identifier: 标识符
            params: 参数字典

        Returns:
            缓存键
        """
        key_parts = [prefix, identifier]

        if params:
            # 对参数进行排序并生成哈希
            params_str = json.dumps(params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]
            key_parts.append(params_hash)

        return ":".join(key_parts)

    async def get(self, key: str) -> Any | None:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回None
        """
        if not self.is_available():
            return None

        try:
            value = await self._redis_client.get(key)
            if value is not None:
                self.stats["hits"] += 1
                logger.debug(f"✓ 缓存命中: {key}")
                return json.loads(value)
            else:
                self.stats["misses"] += 1
                logger.debug(f"✗ 缓存未命中: {key}")
                return None
        except Exception as e:
            logger.error(f"❌ 缓存获取失败: {e}")
            self.stats["errors"] += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示使用默认值

        Returns:
            是否设置成功
        """
        if not self.is_available():
            return False

        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, ensure_ascii=False)

            await self._redis_client.setex(key, ttl, serialized)
            self.stats["sets"] += 1
            logger.debug(f"✓ 缓存已设置: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"❌ 缓存设置失败: {e}")
            self.stats["errors"] += 1
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        if not self.is_available():
            return False

        try:
            result = await self._redis_client.delete(key)
            self.stats["deletes"] += 1
            logger.debug(f"✓ 缓存已删除: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"❌ 缓存删除失败: {e}")
            self.stats["errors"] += 1
            return False

    async def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            键是否存在
        """
        if not self.is_available():
            return False

        try:
            result = await self._redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"❌ 键检查失败: {e}")
            return False

    # ==================== OCR缓存 ====================

    async def get_ocr_result(
        self,
        image_path: str,
        language: str,
        preprocess: bool
    ) -> Optional[dict[str, Any]]:
        """
        获取OCR结果缓存

        Args:
            image_path: 图像路径
            language: 语言
            preprocess: 是否预处理

        Returns:
            OCR结果，不存在返回None
        """
        params = {
            "language": language,
            "preprocess": preprocess
        }
        key = self._generate_key("ocr", image_path, params)
        return await self.get(key)

    async def set_ocr_result(
        self,
        image_path: str,
        language: str,
        preprocess: bool,
        result: dict[str, Any],
        ttl: int = 86400  # 24小时
    ) -> bool:
        """
        设置OCR结果缓存

        Args:
            image_path: 图像路径
            language: 语言
            preprocess: 是否预处理
            result: OCR结果
            ttl: 过期时间

        Returns:
            是否设置成功
        """
        params = {
            "language": language,
            "preprocess": preprocess
        }
        key = self._generate_key("ocr", image_path, params)
        return await self.set(key, result, ttl)

    # ==================== 图像特征缓存 ====================

    async def get_image_features(
        self,
        image_path: str,
        operation: str,
        parameters: Optional[dict[str, Any]] = None
    ) -> Optional[dict[str, Any]]:
        """
        获取图像特征缓存

        Args:
            image_path: 图像路径
            operation: 操作类型
            parameters: 操作参数

        Returns:
            图像特征，不存在返回None
        """
        key = self._generate_key("imgfeat", f"{image_path}:{operation}", parameters)
        return await self.get(key)

    async def set_image_features(
        self,
        image_path: str,
        operation: str,
        features: dict[str, Any],
        parameters: Optional[dict[str, Any]] = None,
        ttl: int = 7200,  # 2小时
    ) -> bool:
        """
        设置图像特征缓存

        Args:
            image_path: 图像路径
            operation: 操作类型
            features: 图像特征
            parameters: 操作参数
            ttl: 过期时间

        Returns:
            是否设置成功
        """
        key = self._generate_key("imgfeat", f"{image_path}:{operation}", parameters)
        return await self.set(key, features, ttl)

    # ==================== 向量缓存 ====================

    async def get_vector_embedding(
        self,
        text: str,
        model: str = "default"
    ) -> list[float] | None:
        """
        获取向量嵌入缓存

        Args:
            text: 输入文本
            model: 模型名称

        Returns:
            向量嵌入，不存在返回None
        """
        # 使用文本的哈希作为标识符
        text_hash = hashlib.md5(text.encode('utf-8'), usedforsecurity=False).hexdigest()
        key = self._generate_key("vector", f"{model}:{text_hash}")
        return await self.get(key)

    async def set_vector_embedding(
        self,
        text: str,
        embedding: list[float],
        model: str = "default",
        ttl: int = 604800  # 7天
    ) -> bool:
        """
        设置向量嵌入缓存

        Args:
            text: 输入文本
            embedding: 向量嵌入
            model: 模型名称
            ttl: 过期时间

        Returns:
            是否设置成功
        """
        text_hash = hashlib.md5(text.encode('utf-8'), usedforsecurity=False).hexdigest()
        key = self._generate_key("vector", f"{model}:{text_hash}")
        return await self.set(key, embedding, ttl)

    # ==================== 批量操作 ====================

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        批量获取缓存

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        if not self.is_available():
            return {}

        try:
            values = await self._redis_client.mget(keys)
            result = {}
            for key, value in zip(keys, values, strict=False):
                if value is not None:
                    result[key] = json.loads(value)
                    self.stats["hits"] += 1
                else:
                    self.stats["misses"] += 1
            return result
        except Exception as e:
            logger.error(f"❌ 批量获取失败: {e}")
            self.stats["errors"] += 1
            return {}

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: Optional[int] = None
    ) -> int:
        """
        批量设置缓存

        Args:
            mapping: 键值对字典
            ttl: 过期时间

        Returns:
            成功设置的数量
        """
        if not self.is_available():
            return 0

        try:
            ttl = ttl or self.default_ttl
            pipeline = self._redis_client.pipeline()

            for key, value in mapping.items():
                serialized = json.dumps(value, ensure_ascii=False)
                pipeline.setex(key, ttl, serialized)

            await pipeline.execute()
            self.stats["sets"] += len(mapping)
            logger.info(f"✓ 批量设置缓存: {len(mapping)}个键")
            return len(mapping)
        except Exception as e:
            logger.error(f"❌ 批量设置失败: {e}")
            self.stats["errors"] += 1
            return 0

    # ==================== 缓存失效 ====================

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        按模式失效缓存

        Args:
            pattern: 键模式（支持通配符*）

        Returns:
            失效的键数量
        """
        if not self.is_available():
            return 0

        try:
            keys = []
            async for key in self._redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                count = await self._redis_client.delete(*keys)
                logger.info(f"✓ 失效缓存: {count}个键 (模式: {pattern})")
                return count
            return 0
        except Exception as e:
            logger.error(f"❌ 模式失效失败: {e}")
            self.stats["errors"] += 1
            return 0

    async def clear_all(self) -> bool:
        """
        清空所有缓存

        Returns:
            是否成功
        """
        if not self.is_available():
            return False

        try:
            await self._redis_client.flushdb()
            logger.info("✓ 所有缓存已清空")
            return True
        except Exception as e:
            logger.error(f"❌ 清空缓存失败: {e}")
            self.stats["errors"] += 1
            return False

    # ==================== 缓存统计 ====================

    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "deletes": self.stats["deletes"],
            "errors": self.stats["errors"],
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
        logger.info("✓ 缓存统计已重置")

    # ==================== 缓存预热 ====================

    async def warmup(
        self,
        data: list[dict[str, Any]],
        ttl: int = 86400
    ) -> int:
        """
        缓存预热

        Args:
            data: 预热数据列表，每项包含key和value
            ttl: 过期时间

        Returns:
            预热的键数量
        """
        if not self.is_available():
            return 0

        try:
            mapping = {}
            for item in data:
                key = item.get("key")
                value = item.get("value")
                if key and value is not None:
                    mapping[key] = value

            if mapping:
                count = await self.set_many(mapping, ttl)
                logger.info(f"✓ 缓存预热完成: {count}个键")
                return count
            return 0
        except Exception as e:
            logger.error(f"❌ 缓存预热失败: {e}")
            self.stats["errors"] += 1
            return 0

    # ==================== 健康检查 ====================

    async def health_check(self) -> dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        if not self.is_available():
            return {
                "status": "unavailable",
                "connected": False,
                "error": "Redis不可用"
            }

        try:
            # 测试连接
            await self._redis_client.ping()

            # 获取信息
            info = await self._redis_client.info()

            return {
                "status": "healthy",
                "connected": True,
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                "cache_stats": self.get_stats()
            }
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "error": str(e)
            }


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test():
        cache = RedisCacheManager()

        if not cache.is_available():
            print("❌ Redis不可用")
            return

        # 连接Redis
        await cache.connect()

        # 测试基本操作
        print("\n=== 测试基本操作 ===")
        await cache.set("test_key", {"value": "hello"}, ttl=60)
        value = await cache.get("test_key")
        print(f"设置和获取: {value}")

        # 测试OCR缓存
        print("\n=== 测试OCR缓存 ===")
        ocr_result = {
            "text": "测试文本",
            "confidence": 0.95
        }
        await cache.set_ocr_result("/tmp/test.png", "chinese", True, ocr_result)
        cached = await cache.get_ocr_result("/tmp/test.png", "chinese", True)
        print(f"OCR缓存: {cached}")

        # 健康检查
        print("\n=== 健康检查 ===")
        health = await cache.health_check()
        print(json.dumps(health, indent=2, ensure_ascii=False))

        # 统计信息
        print("\n=== 缓存统计 ===")
        stats = cache.get_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))

        # 断开连接
        await cache.disconnect()

    asyncio.run(test())
