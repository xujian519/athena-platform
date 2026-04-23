#!/usr/bin/env python3
"""
专利数据同步服务
Patent Data Synchronization Service

将PostgreSQL中的专利数据同步到Qdrant和Neo4j
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from real_patent_connector import RealPatentConnector
from sentence_transformers import SentenceTransformer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatentSyncService:
    """专利数据同步服务"""

    def __init__(
        self,
        batch_size: int = 1000,
        max_workers: int = 4,
        embedding_model: str = '/Users/xujian/Athena工作平台/models/BAAI/bge-large-zh-v1.5'
    ):
        """初始化同步服务

        Args:
            batch_size: 批处理大小
            max_workers: 最大工作线程数
            embedding_model: 向量化模型路径
        """
        self.batch_size = batch_size
        self.max_workers = max_workers

        # 数据库连接
        self.patent_connector = RealPatentConnector()

        # Qdrant客户端
        self.qdrant_client = QdrantClient(
            host='localhost',
            port=6333
        )

        # 向量化模型
        model_path = embedding_model if embedding_model.startswith('/') else '/Users/xujian/Athena工作平台/models/bge-large-zh-v1.5'
        self.embedding_model = SentenceTransformer(
            model_path,
            cache_folder='/Users/xujian/Athena工作平台/models'
        )
        self.embedding_dim = 1024

        # Neo4j驱动
        self.neo4j_driver = GraphDatabase.driver(
            'bolt://localhost:7687',
            auth=('neo4j', 'password')
        )

        # 同步状态
        self.sync_stats = {
            'total_processed': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'start_time': None,
            'last_sync_time': None
        }

    def initialize_collections(self):
        """初始化Qdrant集合"""
        try:
            # 专利向量集合
            collection_name = 'real_patents'
            if not self.qdrant_client.collection_exists(collection_name):
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"创建Qdrant集合: {collection_name}")

            # 为专利集合创建索引
            self.qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name='patent_id',
                field_schema='keyword'
            )
            self.qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name='patent_type',
                field_schema='keyword'
            )
            self.qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name='publication_date',
                field_schema='integer'
            )

            logger.info('Qdrant集合初始化完成')

        except Exception as e:
            logger.error(f"初始化Qdrant集合失败: {e}")
            raise

    def initialize_neo4j_constraints(self):
        """初始化Neo4j约束和索引"""
        try:
            with self.neo4j_driver.session() as session:
                # 创建约束
                constraints = [
                    'CREATE CONSTRAINT ON (p:Patent) ASSERT p.patent_id IS UNIQUE',
                    'CREATE CONSTRAINT ON (a:Applicant) ASSERT a.applicant_name IS UNIQUE',
                    'CREATE CONSTRAINT ON (i:IPC) ASSERT i.ipc_code IS UNIQUE'
                ]

                for constraint in constraints:
                    try:
                        session.run(constraint)
                        logger.info(f"创建约束: {constraint}")
                    except Exception:
                        logger.warning(f"约束可能已存在: {constraint}")

                # 创建索引
                indexes = [
                    'CREATE INDEX patent_title_index FOR (p:Patent) ON (p.title)',
                    'CREATE INDEX patent_publication_date_index FOR (p:Patent) ON (p.publication_date)',
                    'CREATE INDEX patent_type_index FOR (p:Patent) ON (p.patent_type)'
                ]

                for index in indexes:
                    try:
                        session.run(index)
                        logger.info(f"创建索引: {index}")
                    except Exception:
                        logger.warning(f"索引可能已存在: {index}")

            logger.info('Neo4j约束和索引初始化完成')

        except Exception as e:
            logger.error(f"初始化Neo4j失败: {e}")
            raise

    def embed_patent_batch(self, patents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """批量向量化专利

        Args:
            patents: 专利数据列表

        Returns:
            包含向量的专利数据列表
        """
        # 准备文本
        texts = []
        for patent in patents:
            text_parts = []
            if patent.get('title'):
                text_parts.append(f"标题: {patent['title']}")
            if patent.get('abstract'):
                text_parts.append(f"摘要: {patent['abstract']}")
            if patent.get('ipc_codes'):
                text_parts.append(f"分类: {patent['ipc_codes']}")
            # 可以添加更多字段
            texts.append(' '.join(text_parts))

        # 批量编码
        logger.info(f"向量化 {len(patents)} 条专利...")
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        # 添加向量到专利数据
        for i, patent in enumerate(patents):
            patent['vector'] = embeddings[i].tolist()
            patent['embedded_text'] = texts[i]

        return patents

    def sync_to_qdrant(self, patents: list[dict[str, Any]]) -> int:
        """同步专利数据到Qdrant

        Args:
            patents: 专利数据列表

        Returns:
            成功同步的数量
        """
        try:
            # 准备Qdrant点
            points = []
            for _i, patent in enumerate(patents):
                if 'vector' not in patent:
                    logger.warning(f"专利 {patent.get('patent_id', 'unknown')} 缺少向量")
                    continue

                point = PointStruct(
                    id=patent['patent_id'],
                    vector=patent['vector'],
                    payload={
                        'patent_id': patent['patent_id'],
                        'title': patent.get('title', ''),
                        'abstract': patent.get('abstract', ''),
                        'patent_type': patent.get('patent_type', ''),
                        'ipc_codes': patent.get('ipc_codes', ''),
                        'publication_date': patent.get('publication_date'),
                        'application_number': patent.get('application_number'),
                        'text': patent.get('embedded_text', '')
                    }
                )
                points.append(point)

            # 批量插入Qdrant
            if points:
                self.qdrant_client.upsert(
                    collection_name='real_patents',
                    points=points
                )
                logger.info(f"成功同步 {len(points)} 条专利到Qdrant")
                return len(points)

            return 0

        except Exception as e:
            logger.error(f"同步到Qdrant失败: {e}")
            return 0

    def sync_to_neo4j(self, patents: list[dict[str, Any]]) -> int:
        """同步专利数据到Neo4j

        Args:
            patents: 专利数据列表

        Returns:
            成功同步的数量
        """
        try:
            with self.neo4j_driver.session() as session:
                success_count = 0

                for patent in patents:
                    try:
                        # 创建专利节点
                        session.run("""
                            MERGE (p:Patent {patent_id: $patent_id})
                            SET p.title = $title,
                                p.abstract = $abstract,
                                p.patent_type = $patent_type,
                                p.publication_number = $publication_number,
                                p.publication_date = $publication_date,
                                p.application_number = $application_number,
                                p.created_at = datetime()
                        """, patent)

                        # 处理IPC分类
                        if patent.get('ipc_codes'):
                            ipc_list = patent['ipc_codes'].split(', ')
                            for ipc in ipc_list:
                                ipc = ipc.strip()
                                if ipc:
                                    # 创建IPC节点
                                    session.run("""
                                        MERGE (i:IPC {ipc_code: $ipc})
                                    """, {'ipc': ipc})

                                    # 创建关系
                                    session.run("""
                                        MATCH (p:Patent {patent_id: $patent_id})
                                        MATCH (i:IPC {ipc_code: $ipc})
                                        MERGE (p)-[:BELONGS_TO]->(i)
                                    """, {
                                        'patent_id': patent['patent_id'],
                                        'ipc': ipc
                                    })

                        # 处理申请人
                        if patent.get('applicant_name'):
                            session.run("""
                                MERGE (a:Applicant {applicant_name: $applicant_name})
                                ON CREATE SET a.created_at = datetime()
                                MERGE (p:Patent {patent_id: $patent_id})
                                MERGE (a)-[:APPLIES_FOR]->(p)
                            """, {
                                'applicant_name': patent['applicant_name'],
                                'patent_id': patent['patent_id']
                            })

                        success_count += 1

                    except Exception as e:
                        logger.error(f"同步专利 {patent.get('patent_id', 'unknown')} 到Neo4j失败: {e}")

                logger.info(f"成功同步 {success_count} 条专利到Neo4j")
                return success_count

        except Exception as e:
            logger.error(f"同步到Neo4j失败: {e}")
            return 0

    def process_batch(self, patents: list[dict[str, Any]]) -> dict[str, int]:
        """处理一个批次的专利数据

        Args:
            patents: 专利数据列表

        Returns:
            处理结果统计
        """
        batch_stats = {
            'total': len(patents),
            'vectorized': 0,
            'qdrant_synced': 0,
            'neo4j_synced': 0,
            'failed': 0
        }

        try:
            # 向量化
            logger.info(f"处理批次: {len(patents)} 条专利")
            patents = self.embed_patent_batch(patents)
            batch_stats['vectorized'] = len(patents)

            # 同步到Qdrant
            qdrant_count = self.sync_to_qdrant(patents)
            batch_stats['qdrant_synced'] = qdrant_count

            # 同步到Neo4j
            neo4j_count = self.sync_to_neo4j(patents)
            batch_stats['neo4j_synced'] = neo4j_count

            batch_stats['failed'] = batch_stats['total'] - min(qdrant_count, neo4j_count)

            return batch_stats

        except Exception as e:
            logger.error(f"处理批次失败: {e}")
            batch_stats['failed'] = batch_stats['total']
            return batch_stats

    def sync_all_patents(self, limit: Optional[int] = None) -> dict[str, Any]:
        """同步所有专利数据

        Args:
            limit: 限制同步数量

        Returns:
            同步结果统计
        """
        self.sync_stats['start_time'] = datetime.now()
        self.sync_stats['total_processed'] = 0
        self.sync_stats['successful_syncs'] = 0
        self.sync_stats['failed_syncs'] = 0

        logger.info('开始同步所有专利数据...')

        try:
            # 获取专利总数
            stats = self.patent_connector.get_patent_statistics()
            if 'error' in stats:
                logger.error(f"无法获取专利统计: {stats['error']}")
                return self.sync_stats

            total_patents = stats.get('total_patents', 0)
            if limit:
                total_patents = min(total_patents, limit)

            logger.info(f"待同步专利总数: {total_patents}")

            # 分批处理
            offset = 0
            batch_count = 0

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []

                while offset < total_patents:
                    # 获取一批专利
                    batch_patents = self.patent_connector.load_patents(
                        limit=self.batch_size,
                        include_abstract=True,
                        include_claims=True
                    )

                    if not batch_patents:
                        break

                    # 提交批次处理任务
                    future = executor.submit(self.process_batch, batch_patents)
                    futures.append((future, len(batch_patents)))

                    offset += len(batch_patents)
                    batch_count += 1

                    # 显示进度
                    logger.info(f"进度: {offset}/{total_patents} ({offset/total_patents*100:.1f}%)")

                    # 避免内存压力
                    if batch_count % 10 == 0:
                        time.sleep(1)

                # 收集结果
                for future, batch_size in futures:
                    try:
                        batch_result = future.result()
                        self.sync_stats['total_processed'] += batch_size
                        self.sync_stats['successful_syncs'] += min(
                            batch_result['qdrant_synced'],
                            batch_result['neo4j_synced']
                        )
                        self.sync_stats['failed_syncs'] += batch_result['failed']

                    except Exception as e:
                        logger.error(f"批次处理失败: {e}")
                        self.sync_stats['failed_syncs'] += batch_size

        except Exception as e:
            logger.error(f"同步过程出错: {e}")

        finally:
            self.sync_stats['last_sync_time'] = datetime.now()
            duration = self.sync_stats['last_sync_time'] - self.sync_stats['start_time']

            # 打印最终统计
            logger.info("\n同步完成！")
            logger.info(f"总耗时: {duration}")
            logger.info(f"处理总数: {self.sync_stats['total_processed']}")
            logger.info(f"成功同步: {self.sync_stats['successful_syncs']}")
            logger.info(f"失败数量: {self.sync_stats['failed_syncs']}")

            # 保存同步记录
            self.save_sync_record()

        return self.sync_stats

    def save_sync_record(self):
        """保存同步记录"""
        try:
            with self.neo4j_driver.session() as session:
                session.run("""
                    CREATE (s:SyncRecord {
                        timestamp: datetime(),
                        total_processed: $total_processed,
                        successful_syncs: $successful_syncs,
                        failed_syncs: $failed_syncs,
                        sync_duration: $sync_duration
                    })
                """, {
                    'total_processed': self.sync_stats['total_processed'],
                    'successful_syncs': self.sync_stats['successful_syncs'],
                    'failed_syncs': self.sync_stats['failed_syncs'],
                    'sync_duration': str(self.sync_stats['last_sync_time'] - self.sync_stats['start_time'])
                })
        except Exception as e:
            logger.error(f"保存同步记录失败: {e}")

    def incremental_sync(self, since_date: str = None):
        """增量同步

        Args:
            since_date: 起始日期（YYYY-MM-DD）
        """
        logger.info(f"执行增量同步，起始日期: {since_date or '上次同步'}")

        # TODO: 实现增量逻辑
        # 1. 查询上次同步时间
        # 2. 获取该时间后的新增或修改的专利
        # 3. 执行同步

    def cleanup(self):
        """清理资源"""
        if self.patent_connector:
            self.patent_connector.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()
        logger.info('资源清理完成')

# 测试函数
def test_sync():
    """测试同步服务"""
    logger.info('=== 测试专利数据同步服务 ===')

    # 创建同步服务
    sync_service = PatentSyncService(batch_size=10, max_workers=2)

    try:
        # 初始化
        logger.info("\n1. 初始化存储系统...")
        sync_service.initialize_collections()
        sync_service.initialize_neo4j_constraints()

        # 同步少量数据进行测试
        logger.info("\n2. 执行同步测试...")
        stats = sync_service.sync_all_patents(limit=50)

        logger.info("\n✅ 同步测试完成！")
        logger.info(f"   处理总数: {stats['total_processed']}")
        logger.info(f"   成功同步: {stats['successful_syncs']}")
        logger.info(f"   失败数量: {stats['failed_syncs']}")

    except Exception as e:
        logger.info(f"\n❌ 同步测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        sync_service.cleanup()

if __name__ == '__main__':
    test_sync()
