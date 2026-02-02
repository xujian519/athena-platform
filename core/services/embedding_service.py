#!/usr/bin/env python3
"""
统一嵌入服务
Unified Embedding Service

提供文本向量嵌入功能

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-12-25
版本: 1.0.0
"""

import asyncio
import logging



logger = logging.getLogger(__name__)


class EmbeddingService:
    """统一嵌入服务"""

    def __init__(self, config=None):
        self.config = config
        self._model = None
        self._stats = {
            "total_requests": 0,
            "total_texts": 0,
        }

    async def encode(
        self,
        texts: str | list[str],
        batch_size: int = 32,
    ) -> "EmbeddingResult":
        """
        将文本编码为向量

        Args:
            texts: 文本或文本列表
            batch_size: 批处理大小

        Returns:
            EmbeddingResult: 嵌入结果
        """
        import time

        start_time = time.time()

        # 标准化输入
        if isinstance(texts, str):
            texts = [texts]

        self._stats["total_requests"] += 1
        self._stats["total_texts"] += len(texts)

        try:
            # 使用BGE服务
            from core.nlp.bge_embedding_service import get_bge_service

            bge_service = await get_bge_service()
            result = await bge_service.encode(texts)

            response_time = (time.time() - start_time) * 1000

            return EmbeddingResult(
                embeddings=result.embeddings,
                model=result.model,
                dimension=result.dimension,
                count=len(texts),
                response_time_ms=response_time,
            )

        except Exception as e:
            logger.error(f"嵌入编码失败: {e}")
            # 降级到零向量
            dimension = 768
            return EmbeddingResult(
                embeddings=[np.zeros(dimension).tolist() for _ in texts],
                model="fallback",
                dimension=dimension,
                count=len(texts),
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )

    def get_stats(self) -> dict:
        """获取统计信息"""
        return self._stats.copy()


class EmbeddingResult:
    """嵌入结果"""

    def __init__(
        self,
        embeddings: list[list[float]],
        model: str,
        dimension: int,
        count: int,
        response_time_ms: float,
        error: str | None = None,
    ):
        self.embeddings = embeddings
        self.model = model
        self.dimension = dimension
        self.count = count
        self.response_time_ms = response_time_ms
        self.error = error

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "embeddings": self.embeddings,
            "model": self.model,
            "dimension": self.dimension,
            "count": self.count,
            "response_time_ms": round(self.response_time_ms, 2),
            "error": self.error,
        }


# 全局服务实例
_embedding_service: EmbeddingService = None


def get_embedding_service(config=None) -> EmbeddingService:
    """获取嵌入服务实例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(config)
    return _embedding_service


if __name__ == "__main__":
    # 测试嵌入服务
    async def test():
        service = get_embedding_service()

        texts = [
            "你好,我是小诺。",
            "Athena是一个智能工作平台。",
        ]

        result = await service.encode(texts)

        print("🔢 嵌入服务测试")
        print("=" * 60)
        print(f"模型: {result.model}")
        print(f"维度: {result.dimension}")
        print(f"数量: {result.count}")
        print(f"耗时: {result.response_time_ms:.2f}ms")
        print()
        print("📊 向量示例 (前10维):")
        for i, embedding in enumerate(result.embeddings):
            print(f"  文本{i+1}: {embedding[:10]}")
        print()
        print("📈 统计:")
        stats = service.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

    asyncio.run(test())
