#!/usr/bin/env python3
"""
Qdrant向量库集合初始化脚本

功能:
1. 连接到Qdrant服务
2. 创建7个标准集合,用于不同的向量搜索场景
3. 配置合理的索引参数和payload索引
4. 可选: 插入测试数据

作者: Agent 3 (问题分析优化者)
日期: 2026-04-18
"""

import sys
import logging
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PayloadSchemaType,
    PayloadSchemaParams,
    PointStruct,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QdrantCollectionInitializer:
    """Qdrant集合初始化器"""

    # 集合配置: 集合名 -> (向量维度, 距离度量, 描述)
    COLLECTION_CONFIGS = {
        "patent_rules_1024": (1024, Distance.COSINE, "专利规则向量库(1024维)"),
        "legal_main": (1024, Distance.COSINE, "法律主库向量(1024维)"),
        "patent_legal": (1024, Distance.COSINE, "专利法律向量(1024维)"),
        "technical_terms_1024": (1024, Distance.COSINE, "技术术语向量(1024维)"),
        "case_analysis": (1024, Distance.COSINE, "案例分析向量(1024维)"),
        "patent_fulltext": (1024, Distance.COSINE, "专利全文向量(1024维,BGE-M3)"),
        "legal_qa": (1024, Distance.COSINE, "法律问答向量(1024维)"),
    }

    def __init__(self, host: str = "localhost", port: int = 16333):
        """
        初始化Qdrant客户端

        Args:
            host: Qdrant服务器地址
            port: Qdrant服务器端口
        """
        self.client = QdrantClient(
            host=host,
            port=port,
            # 禁用版本检查,因为服务器1.7.4与客户端1.17.1版本不匹配
            prefer_grpc=False,
            check_compatibility=False
        )
        logger.info(f"已连接到Qdrant: {host}:{port}")

    def collection_exists(self, collection_name: str) -> bool:
        """
        检查集合是否存在

        Args:
            collection_name: 集合名称

        Returns:
            bool: 集合是否存在
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            return collection_name in collection_names
        except Exception as e:
            logger.error(f"检查集合失败: {e}")
            return False

    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance
    ) -> bool:
        """
        创建单个集合

        Args:
            collection_name: 集合名称
            vector_size: 向量维度
            distance: 距离度量

        Returns:
            bool: 是否创建成功
        """
        try:
            # 检查集合是否已存在
            if self.collection_exists(collection_name):
                logger.info(f"集合 {collection_name} 已存在,跳过创建")
                return True

            # 创建集合
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance,
                    # HNSW索引参数 (Qdrant 1.7.4支持)
                    hnsw_config={
                        "m": 16,  # 每个节点最多连接16个其他节点
                        "ef_construct": 100,  # 构建索引时的搜索深度
                    }
                    # 注意: indexing_threshold在Qdrant 1.7.4中不支持
                ),
            )
            logger.info(f"✓ 创建集合成功: {collection_name} ({vector_size}维)")
            return True

        except Exception as e:
            logger.error(f"✗ 创建集合失败 {collection_name}: {e}")
            return False

    def create_payload_index(
        self,
        collection_name: str,
        field_name: str,
        field_schema: PayloadSchemaType
    ) -> bool:
        """
        创建payload索引,加速查询

        Args:
            collection_name: 集合名称
            field_name: 字段名
            field_schema: 字段类型

        Returns:
            bool: 是否创建成功
        """
        try:
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=PayloadSchemaParams(
                    type=field_schema,
                )
            )
            logger.info(f"  ✓ 创建payload索引: {field_name} ({field_schema.value})")
            return True
        except Exception as e:
            logger.warning(f"  ⚠ 创建payload索引失败 {field_name}: {e}")
            return False

    def create_all_collections(self) -> dict:
        """
        创建所有标准集合

        Returns:
            dict: 创建结果统计
        """
        results = {
            "success": [],
            "failed": [],
            "skipped": []
        }

        logger.info("=" * 60)
        logger.info("开始创建Qdrant集合")
        logger.info("=" * 60)

        for collection_name, (vector_size, distance, description) in self.COLLECTION_CONFIGS.items():
            logger.info(f"\n处理集合: {collection_name}")
            logger.info(f"  描述: {description}")

            if self.create_collection(collection_name, vector_size, distance):
                results["success"].append(collection_name)

                # 创建payload索引
                self.create_payload_index(
                    collection_name,
                    "category",
                    PayloadSchemaType.KEYWORD
                )
                self.create_payload_index(
                    collection_name,
                    "created_at",
                    PayloadSchemaType.DATETIME
                )
            else:
                results["failed"].append(collection_name)

        logger.info("\n" + "=" * 60)
        logger.info("集合创建完成")
        logger.info("=" * 60)

        return results

    def insert_test_data(
        self,
        collection_name: str,
        num_points: int = 5
    ) -> bool:
        """
        插入测试向量数据

        Args:
            collection_name: 集合名称
            num_points: 插入的向量数量

        Returns:
            bool: 是否插入成功
        """
        try:
            if not self.collection_exists(collection_name):
                logger.warning(f"集合 {collection_name} 不存在,跳过插入测试数据")
                return False

            # 获取集合信息
            collection_info = self.client.get_collection(collection_name)
            vector_size = collection_info.config.params.vectors.size

            # 生成测试向量
            import random
            points = []
            for idx in range(num_points):
                # 生成随机向量(归一化)
                vector = [random.random() for _ in range(vector_size)]

                point = PointStruct(
                    id=idx + 1,
                    vector=vector,
                    payload={
                        "text": f"测试文本_{idx + 1}",
                        "category": f"category_{idx % 3}",
                        "created_at": "2026-04-18T00:00:00Z"
                    }
                )
                points.append(point)

            # 批量插入
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"  ✓ 插入测试数据: {num_points}条")
            return True

        except Exception as e:
            logger.error(f"  ✗ 插入测试数据失败: {e}")
            return False

    def print_summary(self, results: dict):
        """
        打印创建摘要

        Args:
            results: 创建结果统计
        """
        logger.info("\n" + "=" * 60)
        logger.info("创建摘要")
        logger.info("=" * 60)
        logger.info(f"✓ 成功: {len(results['success'])}个")
        logger.info(f"✗ 失败: {len(results['failed'])}个")
        logger.info(f"⊘ 跳过: {len(results['skipped'])}个")

        if results['success']:
            logger.info("\n成功创建的集合:")
            for col in results['success']:
                logger.info(f"  - {col}")

        if results['failed']:
            logger.warning("\n创建失败的集合:")
            for col in results['failed']:
                logger.warning(f"  - {col}")

        logger.info("=" * 60)

    def verify_collections(self) -> bool:
        """
        验证所有集合创建成功

        Returns:
            bool: 验证是否通过
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            logger.info("\n" + "=" * 60)
            logger.info("集合验证")
            logger.info("=" * 60)
            logger.info(f"当前集合总数: {len(collection_names)}")
            logger.info(f"预期集合总数: {len(self.COLLECTION_CONFIGS)}")

            missing = set(self.COLLECTION_CONFIGS.keys()) - set(collection_names)

            if missing:
                logger.warning(f"\n缺少的集合: {missing}")
                return False
            else:
                logger.info("\n✓ 所有预期集合均已创建")

                # 打印每个集合的详细信息
                for col_name in sorted(collection_names):
                    col_info = self.client.get_collection(col_name)
                    vectors_count = col_info.points_count
                    vector_size = col_info.config.params.vectors.size
                    logger.info(f"\n集合: {col_name}")
                    logger.info(f"  - 向量数量: {vectors_count}")
                    logger.info(f"  - 向量维度: {vector_size}")

                logger.info("\n" + "=" * 60)
                return True

        except Exception as e:
            logger.error(f"验证失败: {e}")
            return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="初始化Qdrant向量库集合")
    parser.add_argument(
        "--host",
        default="localhost",
        help="Qdrant服务器地址"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=16333,
        help="Qdrant服务器端口"
    )
    parser.add_argument(
        "--insert-test-data",
        action="store_true",
        help="插入测试数据"
    )
    parser.add_argument(
        "--test-points",
        type=int,
        default=5,
        help="每个集合插入的测试向量数量"
    )

    args = parser.parse_args()

    try:
        # 创建初始化器
        initializer = QdrantCollectionInitializer(
            host=args.host,
            port=args.port
        )

        # 创建所有集合
        results = initializer.create_all_collections()

        # 打印摘要
        initializer.print_summary(results)

        # 验证
        if not initializer.verify_collections():
            logger.error("集合验证失败")
            sys.exit(1)

        # 可选: 插入测试数据
        if args.insert_test_data:
            logger.info("\n开始插入测试数据...")
            for collection_name in results['success']:
                logger.info(f"\n处理集合: {collection_name}")
                initializer.insert_test_data(
                    collection_name,
                    args.test_points
                )

        logger.info("\n✓ Qdrant集合初始化完成!")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("\n用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"初始化失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
