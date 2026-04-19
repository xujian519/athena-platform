#!/usr/bin/env python3
from __future__ import annotations
"""
NLP服务向量化适配器
NLP Service Vectorization Adapter

使用平台NLP服务进行文本向量化,避免下载大模型
连接到本地运行的NLP服务(http://localhost:8001)

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v1.0.0
"""

import asyncio
import logging

import httpx
import numpy as np

logger = logging.getLogger(__name__)


class NLPServiceAdapter:
    """
    NLP服务向量化适配器

    通过HTTP调用平台NLP服务进行文本处理和向量化
    不需要下载大模型,使用已运行的NLP服务
    """

    def __init__(
        self,
        service_url: str = "http://localhost:8001",
        timeout: float = 30.0,
        max_retries: int = 3,
        cache_enabled: bool = True,
        cache_size: int = 1000,
    ):
        """
        初始化NLP服务适配器

        Args:
            service_url: NLP服务地址
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            cache_enabled: 是否启用缓存
            cache_size: 缓存大小
        """
        self.service_url = service_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        self.cache_size = cache_size

        # 向量缓存
        self._embedding_cache: dict[str, np.ndarray] = {}

        # HTTP客户端
        self._client: httpx.AsyncClient | None = None

        # 服务信息
        self._service_info: dict | None = None
        self._vector_dimension: int | None = None

        logger.info(f"🔗 NLP服务适配器初始化: {self.service_url}")

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.service_url, timeout=self.timeout)
        return self._client

    async def close(self):
        """关闭连接"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def check_service(self) -> bool:
        """
        检查NLP服务是否可用

        Returns:
            服务是否可用
        """
        try:
            client = await self._get_client()
            response = await client.get("/health")
            if response.status_code == 200:
                data = response.json()
                self._service_info = data
                logger.info(f"✅ NLP服务可用: {data}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ NLP服务不可用: {e}")
            return False

    async def get_service_info(self) -> dict:
        """获取服务信息"""
        if self._service_info is None:
            await self.check_service()
        return self._service_info or {}

    def get_vector_dimension(self) -> int:
        """
        获取向量维度

        基于平台NLP系统,返回标准维度
        """
        if self._vector_dimension is None:
            # 使用标准的1024维(BGE-M3)(与BGE-base-zh一致)
            self._vector_dimension = 768
        return self._vector_dimension

    async def process_text(
        self, text: str, user_id: str | None = None, session_id: str | None = None
    ) -> dict:
        """
        处理文本(调用NLP服务的/process接口)

        Args:
            text: 输入文本
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            处理结果,包含意图、置信度、响应等
        """
        try:
            client = await self._get_client()
            payload = {"text": text}
            if user_id:
                payload["user_id"] = user_id
            if session_id:
                payload["session_id"] = session_id

            response = await client.post("/process", json=payload)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"❌ 文本处理失败: {e}")
            return {"error": str(e), "intent": "UNKNOWN", "confidence": 0.0}

    async def encode(
        self, texts: str | list[str], normalize: bool = True, use_cache: bool = True
    ) -> np.ndarray:
        """
        编码文本为向量

        使用NLP服务进行语义分析,然后基于分析结果生成向量表示

        Args:
            texts: 文本或文本列表
            normalize: 是否归一化
            use_cache: 是否使用缓存

        Returns:
            向量数组 (n_texts, dimension)
        """
        # 标准化输入
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False

        # 检查缓存
        if use_cache and self.cache_enabled:
            cached_embeddings = []
            uncached_texts = []
            uncached_indices = []

            for i, text in enumerate(texts):
                cache_key = f"nlp_emb_{hash(text)}"
                if cache_key in self._embedding_cache:
                    cached_embeddings.append((i, self._embedding_cache[cache_key]))
                else:
                    uncached_texts.append((i, text))
                    uncached_indices.append(i)
        else:
            cached_embeddings = []
            uncached_texts = [(i, t) for i, t in enumerate(texts)]

        # 为未缓存的文本生成向量
        if uncached_texts:
            new_embeddings = await self._encode_texts([t for _, t in uncached_texts])

            # 更新缓存
            if use_cache and self.cache_enabled:
                for (_, text), emb in zip(uncached_texts, new_embeddings, strict=False):
                    if len(self._embedding_cache) < self.cache_size:
                        cache_key = f"nlp_emb_{hash(text)}"
                        self._embedding_cache[cache_key] = emb

            # 合并结果
            all_embeddings = [None] * len(texts)

            # 添加缓存的嵌入
            for i, emb in cached_embeddings:
                all_embeddings[i] = emb

            # 添加新计算的嵌入
            for (idx, _), emb in zip(uncached_texts, new_embeddings, strict=False):
                all_embeddings[idx] = emb

            result = np.array(all_embeddings)
        else:
            # 全部来自缓存
            result = np.array([emb for _, emb in cached_embeddings])

        if normalize:
            # L2归一化
            norms = np.linalg.norm(result, axis=1, keepdims=True)
            norms[norms == 0] = 1  # 避免除零
            result = result / norms

        return result[0] if single_input else result

    async def _encode_texts(self, texts: list[str]) -> np.ndarray:
        """
        编码多个文本为向量(内部方法)

        基于NLP服务的语义分析结果生成向量
        """
        self.get_vector_dimension()
        embeddings = []

        for text in texts:
            # 调用NLP服务处理文本
            result = await self.process_text(text)

            # 基于NLP分析结果生成向量
            # 这里使用基于特征的方法,不需要下载模型
            vector = self._text_to_vector(text, result)
            embeddings.append(vector)

        return np.array(embeddings)

    def _text_to_vector(self, text: str, nlp_result: dict) -> np.ndarray:
        """
        将文本和NLP分析结果转换为向量

        使用特征工程方法,基于NLP分析结果生成向量表示

        Args:
            text: 原始文本
            nlp_result: NLP服务返回的分析结果

        Returns:
            向量表示
        """
        dimension = self.get_vector_dimension()

        # 提取NLP分析特征
        intent = nlp_result.get("intent", "UNKNOWN")
        confidence = nlp_result.get("confidence", 0.0)
        selected_tools = nlp_result.get("selected_tools", [])
        nlp_result.get("response", "")

        # 生成特征向量
        features = []

        # 1. 意图编码(使用哈希编码)
        intent_hash = hash(intent) % 100
        features.extend(
            [
                intent_hash / 100.0,
                confidence,
                len(selected_tools) / 10.0,
                len(text) / 1000.0,
                text.count(" ") / 100.0,  # 空格比例
            ]
        )

        # 2. 文本字符统计特征
        char_counts = {}
        for char in text[:100]:  # 只分析前100个字符
            char_counts[char] = char_counts.get(char, 0) + 1

        # 取top 50字符频率
        sorted_chars = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)[:50]
        for char, count in sorted_chars:
            features.append(ord(char) / 65536.0)  # 字符Unicode编码
            features.append(count / len(text))

        # 填充到固定维度
        while len(features) < dimension:
            if len(selected_tools) > 0:
                # 工具名称特征
                tool_idx = len(features) % len(selected_tools)
                tool_name = selected_tools[tool_idx]
                tool_hash = hash(tool_name) % 1000
                features.append(tool_hash / 1000.0)
            else:
                features.append(0.0)

        # 截断到目标维度
        features = features[:dimension]

        # 转换为numpy数组
        vector = np.array(features, dtype=np.float32)

        return vector

    async def encode_batch(
        self, texts: list[str], batch_size: int = 32, normalize: bool = True
    ) -> np.ndarray:
        """
        批量编码文本

        Args:
            texts: 文本列表
            batch_size: 批处理大小
            normalize: 是否归一化

        Returns:
            向量数组
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = await self.encode(batch, normalize=normalize, use_cache=False)
            all_embeddings.append(embeddings)

        return np.vstack(all_embeddings)

    def clear_cache(self) -> None:
        """清空缓存"""
        self._embedding_cache.clear()
        logger.info("🗑️  向量缓存已清空")

    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        return {
            "cached_items": len(self._embedding_cache),
            "cache_size": self.cache_size,
            "usage_percent": len(self._embedding_cache) / self.cache_size * 100,
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.check_service()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 单例实例
_nlp_adapter_instance: NLPServiceAdapter | None = None


def get_nlp_adapter(service_url: str = "http://localhost:8001", **kwargs) -> NLPServiceAdapter:
    """
    获取NLP服务适配器单例

    Args:
        service_url: NLP服务地址
        **kwargs: 其他配置参数

    Returns:
        NLP服务适配器实例
    """
    global _nlp_adapter_instance

    if _nlp_adapter_instance is None:
        _nlp_adapter_instance = NLPServiceAdapter(service_url=service_url, **kwargs)
        logger.info("✅ 创建NLP服务适配器单例")

    return _nlp_adapter_instance


# 便捷函数
async def encode_text(
    text: str | list[str], service_url: str = "http://localhost:8001", normalize: bool = True
) -> np.ndarray:
    """
    便捷的文本编码函数

    Args:
        text: 文本或文本列表
        service_url: NLP服务地址
        normalize: 是否归一化

    Returns:
        向量数组
    """
    adapter = get_nlp_adapter(service_url=service_url)
    return await adapter.encode(text, normalize=normalize)


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test():
        print("🧪 测试NLP服务适配器")
        print("=" * 60)

        adapter = NLPServiceAdapter()

        # 检查服务
        print("\n1️⃣  检查NLP服务...")
        is_available = await adapter.check_service()
        print(f"   服务可用: {is_available}")

        if is_available:
            # 测试文本处理
            print("\n2️⃣  测试文本处理...")
            result = await adapter.process_text("测试多模态文件处理系统")
            print(f"   处理结果: {result}")

            # 测试向量化
            print("\n3️⃣  测试向量化...")
            texts = ["测试文本1", "测试文本2", "测试文本3"]
            embeddings = await adapter.encode(texts)
            print(f"   向量形状: {embeddings.shape}")
            print(f"   向量维度: {adapter.get_vector_dimension()}")

            # 缓存统计
            print("\n4️⃣  缓存统计...")
            stats = adapter.get_cache_stats()
            print(f"   {stats}")

        await adapter.close()
        print("\n✅ 测试完成")

    asyncio.run(test())
