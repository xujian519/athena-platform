#!/usr/bin/env python3
"""
PostgreSQL pgvector 到 Qdrant 数据同步脚本 (简化修复版)
将PostgreSQL中的向量嵌入数据同步到Qdrant向量数据库

用法:
    python3 scripts/sync_pgvector_to_qdrant.py --table legal_articles_v2_embeddings
    python3 scripts/sync_pgvector_to_qdrant.py --all
"""

import argparse
import logging
import time

import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PgvectorToQdrantSync:
    """PostgreSQL pgvector到Qdrant的同步器"""

    def __init__(self):
        """初始化连接"""
        # PostgreSQL连接配置
        self.pg_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'postgres'
        }

        # Qdrant连接配置
        self.qdrant_host = 'localhost'
        self.qdrant_port = 6333

        self.pg_conn = None
        self.qdrant_client = None

    def connect(self):
        """建立数据库连接"""
        try:
            # 连接PostgreSQL
            logger.info("🔗 连接PostgreSQL...")
            self.pg_conn = psycopg2.connect(**self.pg_config)
            logger.info("✅ PostgreSQL连接成功")

            # 连接Qdrant
            logger.info("🔗 连接Qdrant...")
            self.qdrant_client = QdrantClient(
                host=self.qdrant_host,
                port=self.qdrant_port,
                check_compatibility=False
            )
            logger.info("✅ Qdrant连接成功")

        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            raise

    def close(self):
        """关闭连接"""
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("✅ PostgreSQL连接已关闭")
        if self.qdrant_client:
            self.qdrant_client.close()
            logger.info("✅ Qdrant连接已关闭")

    def recreate_collection(self, collection_name: str, vector_size: int = 1024):
        """重建集合"""
        try:
            # 检查集合是否存在
            collections = self.qdrant_client.get_collections()
            existing_collections = [c.name for c in collections.collections]

            if collection_name in existing_collections:
                logger.info(f"   删除旧集合: {collection_name}")
                self.qdrant_client.delete_collection(collection_name)

            # 创建新集合
            logger.info(f"   创建集合: {collection_name} (vector_size={vector_size})")
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"   ✅ 集合 {collection_name} 创建成功")

        except Exception as e:
            logger.error(f"   ❌ 创建集合失败: {e}")
            raise

    def sync_table(self, table_name: str, batch_size: int = 500):
        """同步单个表"""

        logger.info(f"📊 开始同步表: {table_name}")

        # 使用默认1024维
        vector_dim = 1024
        logger.info(f"   向量维度: {vector_dim}")

        # 确定Qdrant集合名称
        collection_name = table_name.replace('_embeddings', '').replace('_vectors', '')
        logger.info(f"   目标集合: {collection_name}")

        # 重建集合
        self.recreate_collection(collection_name, vector_dim)

        # 获取总记录数 - 使用新cursor
        cursor = self.pg_conn.cursor()
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_count = cursor.fetchone()[0]
        finally:
            cursor.close()

        logger.info(f"   总记录数: {total_count}")

        if total_count == 0:
            logger.warning(f"   ⚠️ 表 {table_name} 为空，跳过")
            return

        # 构建查询 - 根据表名调整
        if table_name == 'legal_articles_v2_embeddings':
            query = """
            SELECT id, vector, article_id
            FROM legal_articles_v2_embeddings
            ORDER BY id
            """
        elif table_name == 'patent_invalid_embeddings':
            query = """
            SELECT id, vector, document_id
            FROM patent_invalid_embeddings
            ORDER BY id
            """
        elif table_name == 'judgment_embeddings':
            query = """
            SELECT id, vector, judgment_id::text
            FROM judgment_embeddings
            ORDER BY id
            """
        elif table_name == 'patent_judgment_vectors':
            query = """
            SELECT id, embedding, judgment_id
            FROM patent_judgment_vectors
            ORDER BY id
            """
        else:
            query = f"SELECT id, vector, id::text FROM {table_name} ORDER BY id"

        cursor = self.pg_conn.cursor()
        cursor.execute(query)

        # 批量导入
        imported = 0
        batch_points = []

        start_time = time.time()

        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break

            for row in rows:
                record_id = row[0]
                vector = row[1] if table_name != 'patent_judgment_vectors' else row[1]  # embedding vs vector
                text_id = row[2] if len(row) > 2 else str(record_id)

                # 转换向量为列表
                if vector is None:
                    continue

                if isinstance(vector, str):
                    vector_list = eval(vector)
                else:
                    vector_list = list(vector)

                # 创建Qdrant点
                point = PointStruct(
                    id=record_id,
                    vector=vector_list,
                    payload={
                        "text_id": text_id,
                        "source_table": table_name
                    }
                )
                batch_points.append(point)

            # 批量上传
            if batch_points:
                self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=batch_points
                )
                imported += len(batch_points)
                batch_points = []

                # 显示进度
                progress = (imported / total_count) * 100
                elapsed = time.time() - start_time
                speed = imported / elapsed if elapsed > 0 else 0
                eta = (total_count - imported) / speed if speed > 0 else 0

                logger.info(f"   进度: {imported}/{total_count} ({progress:.1f}%) | 速度: {speed:.0f}条/秒 | ETA: {eta:.0f}秒")

        cursor.close()

        elapsed = time.time() - start_time
        logger.info(f"✅ 表 {table_name} 同步完成，共 {imported} 条，耗时 {elapsed:.1f} 秒")

        # 验证
        collection_info = self.qdrant_client.get_collection(collection_name)
        logger.info(f"   Qdrant集合统计: {collection_info.points_count} points")

    def sync_all(self):
        """同步所有向量表"""
        tables = [
            'legal_articles_v2_embeddings',
            'patent_invalid_embeddings',
            'judgment_embeddings',
            'patent_judgment_vectors'
        ]

        logger.info("🚀 开始同步所有向量表")
        logger.info(f"   待同步表: {', '.join(tables)}")

        for table in tables:
            try:
                self.sync_table(table)
                logger.info("")
            except Exception as e:
                logger.error(f"❌ 同步表 {table} 失败: {e}")
                logger.info("")
                # 重置连接
                self.close()
                self.connect()
                continue

        logger.info("✅ 全部同步完成！")

    def verify_sync(self):
        """验证同步结果"""
        logger.info("🔍 验证同步结果...")

        # PostgreSQL统计
        cursor = self.pg_conn.cursor()

        tables_info = [
            ('legal_articles_v2_embeddings', 'legal_articles'),
            ('patent_invalid_embeddings', 'patent_invalid'),
            ('judgment_embeddings', 'judgments'),
            ('patent_judgment_vectors', 'patent_judgments')
        ]

        total_pg = 0
        total_qdrant = 0

        for pg_table, qdrant_collection in tables_info:
            try:
                # PostgreSQL统计
                cursor.execute(f"SELECT COUNT(*) FROM {pg_table}")
                pg_count = cursor.fetchone()[0]

                # Qdrant统计
                try:
                    collection_info = self.qdrant_client.get_collection(qdrant_collection)
                    qdrant_count = collection_info.points_count
                except:
                    qdrant_count = 0

                total_pg += pg_count
                total_qdrant += qdrant_count

                status = "✅" if pg_count == qdrant_count else "⚠️"
                logger.info(f"   {status} {pg_table}: PG={pg_count}, Qdrant={qdrant_count}")

            except Exception as e:
                logger.error(f"   ❌ {pg_table}: {e}")

        cursor.close()

        logger.info(f"   总计: PostgreSQL={total_pg}, Qdrant={total_qdrant}")
        logger.info("✅ 验证完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='同步PostgreSQL pgvector数据到Qdrant')
    parser.add_argument('--table', type=str, help='指定要同步的表名')
    parser.add_argument('--all', action='store_true', help='同步所有向量表')
    parser.add_argument('--verify', action='store_true', help='仅验证不同步')

    args = parser.parse_args()

    if not args.table and not args.all and not args.verify:
        parser.print_help()
        print("\n示例:")
        print("  python3 scripts/sync_pgvector_to_qdrant.py --table legal_articles_v2_embeddings")
        print("  python3 scripts/sync_pgvector_to_qdrant.py --all")
        print("  python3 scripts/sync_pgvector_to_qdrant.py --verify")
        return

    syncer = PgvectorToQdrantSync()

    try:
        syncer.connect()

        if args.verify:
            syncer.verify_sync()
        elif args.table:
            syncer.sync_table(args.table)
            syncer.verify_sync()
        elif args.all:
            syncer.sync_all()
            syncer.verify_sync()

    except Exception as e:
        logger.error(f"❌ 同步失败: {e}")
        raise
    finally:
        syncer.close()


if __name__ == "__main__":
    main()
