#!/usr/bin/env python3
"""
Qdrant向量数据库客户端
Qdrant Vector Database Client for Patent Judgments

功能:
- 管理三层粒度向量集合(L1法条/L2焦点/L3论点)
- 向量插入、搜索、删除
- 批量操作支持
"""

from typing import Any, Dict, List, Optional

from core.logging_config import setup_logging

logger = setup_logging()


class QdrantClient:
    """Qdrant向量数据库客户端"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化Qdrant客户端

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.client = None
        self.is_connected = False

        # 从配置获取连接信息
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 6333)
        self.grpc_port = self.config.get("grpc_port", 6334)

        # 集合配置
        self.vector_size = self.config.get("vector_size", 1024)
        self.collections = {
            "L1": {
                "name": self.config.get("layer1", {}).get("collection_name", "patent_judgments_L1"),
                "description": "法律条文层向量",
            },
            "L2": {
                "name": self.config.get("layer2", {}).get("collection_name", "patent_judgments_L2"),
                "description": "争议焦点层向量",
            },
            "L3": {
                "name": self.config.get("layer3", {}).get("collection_name", "patent_judgments_L3"),
                "description": "论证逻辑层向量",
            },
        }

    def connect(self) -> bool:
        """
        连接到Qdrant服务器

        Returns:
            是否连接成功
        """
        try:
            from qdrant_client import QdrantClient as QdrantSyncClient

            logger.info(f"🔄 连接到Qdrant: {self.host}:{self.port}")

            self.client = QdrantSyncClient(host=self.host, port=self.port, timeout=30)

            # 测试连接
            collections = self.client.get_collections()
            self.is_connected = True

            logger.info("✅ Qdrant连接成功")
            logger.info(f"📊 现有集合数量: {len(collections.collections)}")

            return True

        except Exception as e:
            logger.error(f"❌ Qdrant连接失败: {e!s}")
            self.is_connected = False
            return False

    def initialize_collections(self) -> bool:
        """
        初始化三层粒度的向量集合

        Returns:
            是否成功
        """
        if not self.is_connected:
            logger.error("❌ 未连接到Qdrant")
            return False

        from qdrant_client.models import Distance, PointStruct, VectorParams

        success = True

        for _layer, config in self.collections.items():
            collection_name = config["name"]

            try:
                # 检查集合是否存在
                self.client.get_collection(collection_name)
                logger.info(f"✅ 集合已存在: {collection_name}")

            except Exception:
                # 集合不存在,创建新集合
                logger.info(f"📦 创建集合: {collection_name}")

                try:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=self.vector_size,
                            distance=Distance.COSINE,
                        ),
                    )
                    logger.info(f"✅ 集合创建成功: {collection_name}")

                except Exception as create_error:
                    logger.error(f"❌ 集合创建失败 {collection_name}: {create_error!s}")
                    success = False

        return success

    def insert_vectors(self, layer: str, vectors: list["VectorizedData"]) -> bool:
        """
        批量插入向量

        Args:
            layer: 层级(L1/L2/L3)
            vectors: 向量数据列表

        Returns:
            是否成功
        """
        if not self.is_connected:
            logger.error("❌ 未连接到Qdrant")
            return False

        if layer not in self.collections:
            logger.error(f"❌ 无效的层级: {layer}")
            return False

        collection_name = self.collections[layer]["name"]
        from qdrant_client.models import PointStruct

        # 构建点列表
        points = []
        for vec_data in vectors:
            # 使用hash生成全局唯一ID
            import hashlib

            unique_id = int(
                hashlib.md5(vec_data.vector_id.encode('utf-8'), usedforsecurity=False).hexdigest()[:8], 16
            )

            point = PointStruct(
                id=unique_id,
                vector=vec_data.embedding.tolist(),
                payload={
                    "vector_id": vec_data.vector_id,
                    "case_id": vec_data.content.get("case_id", ""),
                    **vec_data.metadata,
                },
            )
            points.append(point)

        try:
            # 批量插入
            self.client.upsert(collection_name=collection_name, points=points)

            logger.info(f"✅ 插入{len(points)}个向量到 {collection_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 插入向量失败: {e!s}")
            return False

    def search(
        self,
        layer: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float = 0.0,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        向量搜索

        Args:
            layer: 层级(L1/L2/L3)
            query_vector: 查询向量
            limit: 返回数量
            score_threshold: 分数阈值
            filters: 过滤条件

        Returns:
            搜索结果列表
        """
        if not self.is_connected:
            logger.error("❌ 未连接到Qdrant")
            return []

        if layer not in self.collections:
            logger.error(f"❌ 无效的层级: {layer}")
            return []

        collection_name = self.collections[layer]["name"]

        try:
            # 构建搜索过滤器
            search_filter = None
            if filters:
                # TODO: 实现过滤器逻辑
                pass

            # 执行搜索
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter,
            )

            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {"id": result.id, "score": result.score, "payload": result.payload}
                )

            logger.info(f"🔍 搜索完成: {len(formatted_results)}个结果")
            return formatted_results

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e!s}")
            return []

    def get_collection_info(self, layer: str) -> dict[str, Any] | None:
        """
        获取集合信息

        Args:
            layer: 层级(L1/L2/L3)

        Returns:
            集合信息字典
        """
        if not self.is_connected:
            return None

        if layer not in self.collections:
            return None

        collection_name = self.collections[layer]["name"]

        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "status": info.status,
                "config": info.config,
            }
        except Exception as e:
            logger.error(f"❌ 获取集合信息失败: {e!s}")
            return None

    def delete_collection(self, layer: str) -> bool:
        """
        删除集合

        Args:
            layer: 层级(L1/L2/L3)

        Returns:
            是否成功
        """
        if not self.is_connected:
            logger.error("❌ 未连接到Qdrant")
            return False

        if layer not in self.collections:
            logger.error(f"❌ 无效的层级: {layer}")
            return False

        collection_name = self.collections[layer]["name"]

        try:
            self.client.delete_collection(collection_name)
            logger.info(f"✅ 集合已删除: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 删除集合失败: {e!s}")
            return False

    def print_status(self) -> Any:
        """打印Qdrant状态"""
        if not self.is_connected:
            print("❌ 未连接到Qdrant")
            return

        print("\n" + "=" * 60)
        print("📊 Qdrant向量数据库状态")
        print("=" * 60)
        print(f"连接: {self.host}:{self.port}")

        for layer in ["L1", "L2", "L3"]:
            info = self.get_collection_info(layer)
            if info:
                print(f"\n{layer}层: {self.collections[layer]['description']}")
                print(f"  集合名: {info['name']}")
                print(f"  向量数: {info['vectors_count']}")
                print(f"  状态: {info['status']}")

        print("=" * 60 + "\n")


# 便捷函数
def get_qdrant_client(config: dict[str, Any] | None = None) -> QdrantClient | None:
    """
    获取Qdrant客户端单例

    Args:
        config: 配置字典

    Returns:
        Qdrant客户端实例
    """
    client = QdrantClient(config)
    if client.connect():
        return client
    return None


if __name__ == "__main__":
    # 测试代码
    # setup_logging()  # 日志配置已移至模块导入

    # 加载配置
    import yaml

    with open("/Users/xujian/Athena工作平台/config/judgment_vector_db_config.yaml") as f:
        config = yaml.safe_load(f)

    # 创建客户端
    client = get_qdrant_client(config["qdrant"])

    if client:
        # 初始化集合
        client.initialize_collections()

        # 打印状态
        client.print_status()
