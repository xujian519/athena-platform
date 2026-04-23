#!/usr/bin/env python3
"""
Qdrant客户端辅助模块
提供统一的Qdrant HTTP API访问接口
"""
import logging
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


class QdrantHTTPClient:
    """Qdrant HTTP API客户端（更稳定的连接方式）"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        timeout: int = 30,
        **kwargs
    ):
        """
        初始化Qdrant HTTP客户端

        Args:
            host: Qdrant主机
            port: Qdrant端口
            timeout: 请求超时时间（秒）
            **kwargs: 额外参数
        """
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.session = requests.Session()
        logger.info(f"✅ Qdrant HTTP客户端初始化成功: {self.base_url}")

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求体数据
            params: URL参数
            **kwargs: 额外参数

        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()

            result = response.json()

            if result.get("status") == "ok":
                return result.get("result", result)
            else:
                logger.error(f"Qdrant API错误: {result}")
                raise Exception(f"Qdrant API返回错误: {result}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Qdrant HTTP请求失败: {e}")
            raise

    def get_collections(self) -> list[dict[str, Any]]:
        """获取所有集合"""
        return self._request("GET", "/collections")

    def get_collection(self, collection_name: str) -> dict[str, Any]:
        """获取单个集合信息"""
        return self._request("GET", f"/collections/{collection_name}")

    def health_check(self) -> bool:
        """健康检查"""
        try:
            self._request("GET", "/", timeout=5)
            return True
        except Exception:
            return False

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        **kwargs
    ) -> list[dict[str, Any]]:
        """
        向量搜索

        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            limit: 返回结果数量
            **kwargs: 额外搜索参数

        Returns:
            搜索结果列表
        """
        data = {
            "vector": query_vector,
            "limit": limit,
            **kwargs
        }
        return self._request("POST", f"/collections/{collection_name}/points/search", data=data)

    def close(self):
        """关闭客户端"""
        self.session.close()


# 便捷函数
def get_qdrant_client(**kwargs) -> QdrantHTTPClient:
    """
    获取Qdrant客户端实例

    Args:
        **kwargs: 客户端配置参数

    Returns:
        QdrantHTTPClient实例
    """
    return QdrantHTTPClient(**kwargs)


# 向后兼容的别名
QdrantClientHelper = QdrantHTTPClient
