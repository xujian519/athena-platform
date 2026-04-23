#!/usr/bin/env python3
"""
Qdrant客户端适配器
提供向后兼容的QdrantClient接口，内部使用稳定的HTTP API
"""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 尝试导入新的HTTP客户端
try:
    from core.vector.qdrant_client_helper import QdrantHTTPClient
    HTTP_CLIENT_AVAILABLE = True
except ImportError:
    HTTP_CLIENT_AVAILABLE = False
    logger.warning("QdrantHTTPClient不可用，将使用qdrant-client")

# 尝试导入原始的qdrant-client
try:
    from qdrant_client import QdrantClient as OriginalQdrantClient
    ORIGINAL_CLIENT_AVAILABLE = True
except ImportError:
    ORIGINAL_CLIENT_AVAILABLE = False
    logger.warning("qdrant-client不可用")


class QdrantClient:
    """
    Qdrant客户端适配器

    提供与原始qdrant-client兼容的接口，内部优先使用稳定的HTTP API。
    如果HTTP API不可用，则回退到原始客户端。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None, **kwargs):
        """
        初始化Qdrant客户端

        Args:
            config: 配置字典（兼容原始格式）
            **kwargs: 额外配置参数
        """
        self.config = config or {}
        self.config.update(kwargs)

        # 优先使用HTTP客户端
        if HTTP_CLIENT_AVAILABLE:
            try:
                self.http_client = QdrantHTTPClient(
                    host=self.config.get("host", "localhost"),
                    port=self.config.get("port", 6333),
                    timeout=self.config.get("timeout", 30)
                )
                self.client_type = "http"
                logger.info("✅ 使用Qdrant HTTP客户端")
                return
            except Exception as e:
                logger.warning(f"HTTP客户端初始化失败: {e}，尝试原始客户端")

        # 回退到原始客户端
        if ORIGINAL_CLIENT_AVAILABLE:
            self.original_client = OriginalQdrantClient(**self.config)
            self.client_type = "original"
            logger.info("✅ 使用原始qdrant-client")
        else:
            raise RuntimeError("无法初始化Qdrant客户端：HTTP和原始客户端都不可用")

    def get_collections(self) -> list[dict[str, Any]]:
        """获取所有集合"""
        if self.client_type == "http":
            return self.http_client.get_collections()
        else:
            return self.original_client.get_collections()

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        **kwargs
    ) -> list[dict[str, Any]]:
        """向量搜索"""
        if self.client_type == "http":
            return self.http_client.search(collection_name, query_vector, limit, **kwargs)
        else:
            # 转换参数格式
            search_result = self.original_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                **kwargs
            )
            # 转换返回格式
            return [{"id": r.id, "score": r.score, "payload": r.payload} for r in search_result]

    def count(self, collection_name: str) -> int:
        """获取集合中的点数量"""
        if self.client_type == "http":
            info = self.http_client.get_collection(collection_name)
            return info.get("points_count", 0)
        else:
            return self.original_client.count(collection_name)

    def close(self):
        """关闭客户端"""
        if self.client_type == "http":
            if hasattr(self, 'http_client'):
                self.http_client.close()
        elif hasattr(self, 'original_client'):
            if hasattr(self.original_client, 'close'):
                self.original_client.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()


# 便捷函数
def create_qdrant_client(config: Optional[dict[str, Any]] = None, **kwargs) -> QdrantClient:
    """
    创建Qdrant客户端（使用适配器）

    Args:
        config: 配置字典
        **kwargs: 额外配置参数

    Returns:
        QdrantClient实例
    """
    return QdrantClient(config, **kwargs)


# 向后兼容的导出
__all__ = ["QdrantClient", "create_qdrant_client"]
