#!/usr/bin/env python3
"""
商标规则数据库管理器
Trademark Rules Database Manager

统一管理PostgreSQL、Qdrant和NebulaGraph连接

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any

import psycopg2
from psycopg2.extras import execute_values

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrademarkDatabaseManager:
    """商标规则数据库管理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化数据库管理器

        Args:
            config: 配置字典，包含数据库连接信息
        """
        self.config = config or {}

        # PostgreSQL连接
        self.pg_conn = None
        self.pg_cursor = None

        # Qdrant客户端
        self.qdrant_client = None

        # NebulaGraph客户端
        self.nebula_client = None
        self.nebula_pool = None

        # 连接状态
        self.pg_connected = False
        self.qdrant_connected = False
        self.nebula_connected = False

    def connect_postgresql(self, connection_params: dict[str, Any]) -> bool:
        """
        连接PostgreSQL数据库

        Args:
            connection_params: 连接参数
                - host: 主机地址
                - port: 端口号
                - database: 数据库名
                - user: 用户名
                - password: 密码

        Returns:
            连接是否成功
        """
        try:
            from .models import CREATE_TABLES_SQL

            self.pg_conn = psycopg2.connect(**connection_params)
            self.pg_cursor = self.pg_conn.cursor()

            # 初始化表结构
            self.pg_cursor.execute(CREATE_TABLES_SQL)
            self.pg_conn.commit()

            self.pg_connected = True
            logger.info(f"✅ PostgreSQL连接成功: {connection_params['database']}")
            return True

        except Exception as e:
            logger.error(f"❌ PostgreSQL连接失败: {e}")
            return False

    def connect_qdrant(self, url: str = "http://localhost:6333", collection_name: str = "trademark_rules") -> bool:
        """
        连接Qdrant向量数据库

        Args:
            url: Qdrant服务地址
            collection_name: 集合名称

        Returns:
            连接是否成功
        """
        try:
            from qdrant_client import QdrantClient

            self.qdrant_client = QdrantClient(url=url)

            # 创建集合
            from .models import QDRANT_COLLECTION_CONFIG

            try:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    **QDRANT_COLLECTION_CONFIG
                )
                logger.info(f"✅ Qdrant集合已创建: {collection_name}")
            except Exception as e:
                if "already exists" not in str(e):
                    raise e
                logger.info(f"ℹ️  Qdrant集合已存在: {collection_name}")

            self.qdrant_connected = True
            logger.info(f"✅ Qdrant连接成功: {url}")
            return True

        except Exception as e:
            logger.error(f"❌ Qdrant连接失败: {e}")
            return False

    def connect_nebula(self, config: dict[str, Any]) -> bool:
        """
        连接NebulaGraph图数据库

        Args:
            config: NebulaGraph配置
                - hosts: 主机列表
                - port: 端口
                - username: 用户名
                - password: 密码
                - space_name: 空间名称

        Returns:
            连接是否成功
        """
        try:
            from nebula3.Config import Config
            from nebula3.gclient.net import ConnectionPool

            # 配置连接
            nebula_config = Config()
            nebula_config.max_connection_pool_size = config.get('max_connections', 10)

            # 创建连接池
            self.nebula_pool = ConnectionPool(
                config['hosts'],
                config['port'],
                nebula_config
            )

            # 获取会话
            self.nebula_client = self.nebula_pool.get_session(
                config['username'],
                config['password']
            )

            # 创建空间
            from .models import NEBULA_SPACE_CONFIG

            space_config = NEBULA_SPACE_CONFIG

            # 创建空间（如果不存在）
            create_space_sql = (
                f"CREATE SPACE IF NOT EXISTS {space_config['space_name']} "
                f"(partition_num={space_config['partition_num']}, "
                f"replica_factor={space_config['replica_factor']}, "
                f"vid_type={space_config['vid_type']});"
            )

            self.nebula_client.execute(create_space_sql)
            logger.info(f"✅ NebulaGraph空间已创建: {space_config['space_name']}")

            self.nebula_connected = True
            logger.info("✅ NebulaGraph连接成功")
            return True

        except Exception as e:
            logger.warning(f"⚠️  NebulaGraph连接失败（可选）: {e}")
            return False

    def insert_norm(self, norm_data: dict[str, Any]) -> bool:
        """
        插入法规记录

        Args:
            norm_data: 法规数据

        Returns:
            是否成功
        """
        try:
            query = """
                INSERT INTO trademark_norms (
                    id, name, document_number, issuing_authority,
                    issue_date, effective_date, status, document_type,
                    file_path, full_text
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    updated_at = NOW()
            """

            self.pg_cursor.execute(query, (
                norm_data['id'],
                norm_data['name'],
                norm_data.get('document_number'),
                norm_data.get('issuing_authority'),
                norm_data.get('issue_date'),
                norm_data.get('effective_date'),
                norm_data.get('status', '现行有效'),
                norm_data.get('document_type'),
                norm_data.get('file_path'),
                norm_data.get('full_text', '')[:10000]  # 限制长度
            ))

            self.pg_conn.commit()
            return True

        except Exception as e:
            logger.error(f"❌ 插入法规失败: {e}")
            self.pg_conn.rollback()
            return False

    def insert_articles_batch(self, articles: list[dict[str, Any]]) -> int:
        """
        批量插入条款

        Args:
            articles: 条款列表

        Returns:
            插入数量
        """
        try:
            query = """
                INSERT INTO trademark_articles (
                    id, norm_id, book_name, chapter_name, section_name,
                    article_number, clause_number, item_number,
                    original_text, hierarchy_path
                ) VALUES %s
                ON CONFLICT (id) DO NOTHING
            """

            values = [(
                a['id'],
                a['norm_id'],
                a.get('book_name'),
                a.get('chapter_name'),
                a.get('section_name'),
                a.get('article_number'),
                a.get('clause_number'),
                a.get('item_number'),
                a['original_text'],
                a.get('hierarchy_path')
            ) for a in articles]

            execute_values(self.pg_cursor, query, values)
            self.pg_conn.commit()

            return len(articles)

        except Exception as e:
            logger.error(f"❌ 批量插入条款失败: {e}")
            self.pg_conn.rollback()
            return 0

    def insert_vectors_batch(self, vectors: list[dict[str, Any]]) -> int:
        """
        批量插入向量文档

        Args:
            vectors: 向量文档列表

        Returns:
            插入数量
        """
        try:
            query = """
                INSERT INTO trademark_vectors (
                    id, norm_id, chunk_id, text, char_count, embedding_id
                ) VALUES %s
                ON CONFLICT (id) DO NOTHING
            """

            values = [(
                v['id'],
                v['norm_id'],
                v['chunk_id'],
                v['text'][:5000],  # 限制长度
                v['char_count'],
                v.get('embedding_id')
            ) for v in vectors]

            execute_values(self.pg_cursor, query, values)
            self.pg_conn.commit()

            return len(vectors)

        except Exception as e:
            logger.error(f"❌ 批量插入向量失败: {e}")
            self.pg_conn.rollback()
            return 0

    def close(self) -> Any:
        """关闭所有数据库连接"""
        if self.pg_cursor:
            self.pg_cursor.close()
        if self.pg_conn:
            self.pg_conn.close()
        if self.nebula_client:
            self.nebula_client.release()
        if self.nebula_pool:
            self.nebula_pool.close()

        logger.info("🔌 所有数据库连接已关闭")


async def main():
    """测试数据库连接"""
    # PostgreSQL配置（商标数据库端口5441）
    pg_config = {
        'host': 'localhost',
        'port': 5441,
        'database': 'trademark_database',
        'user': 'postgres',
        'password': 'your_password'
    }

    # Qdrant配置
    qdrant_url = "http://localhost:6333"

    # NebulaGraph配置
    nebula_config = {
        'hosts': ['127.0.0.1'],
        'port': 9669,
        'username': 'root',
        'password': 'nebula',
        'space_name': 'trademark_graph'
    }

    manager = TrademarkDatabaseManager()

    # 连接所有数据库
    manager.connect_postgresql(pg_config)
    manager.connect_qdrant(qdrant_url)
    manager.connect_nebula(nebula_config)

    print("✅ 数据库连接测试完成")

    manager.close()


if __name__ == "__main__":
    asyncio.run(main())
