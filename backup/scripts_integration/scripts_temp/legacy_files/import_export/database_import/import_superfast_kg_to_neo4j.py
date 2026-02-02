#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将超级快速处理的专利知识图谱导入Neo4j
作者：小娜
日期：2025-12-07
"""

import json
import logging
import os
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from neo4j import GraphDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'documentation/logs/superfast_kg_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SuperFastKGImporter:
    """超级快速知识图谱导入器"""

    def __init__(self):
        self.uri = 'bolt://localhost:7687'
        self.user = 'neo4j'
        self.password = 'password'
        self.driver = None
        self.source_dir = Path('/Users/xujian/Athena工作平台/data/patent_kg_superfast')
        self.batch_size = 50  # 每批处理50个文件
        self.max_workers = 8  # 8个并发线程

        # 统计信息
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_patents': 0,
            'total_triples': 0,
            'nodes_created': 0,
            'relationships_created': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

        # 线程锁
        self.stats_lock = threading.Lock()

    def connect(self):
        """连接到Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            # 测试连接
            with self.driver.session() as session:
                session.run('RETURN 1')
            logger.info('✅ Neo4j连接成功')
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            return False

    def create_constraints_and_indexes(self):
        """创建约束和索引"""
        constraints = [
            'CREATE CONSTRAINT patent_id_unique IF NOT EXISTS FOR (p:Patent) REQUIRE p.id IS UNIQUE',
            'CREATE INDEX patent_type_idx IF NOT EXISTS FOR (p:Patent) ON (p.type)',
            'CREATE INDEX patent_number_idx IF NOT EXISTS FOR (p:Patent) ON (p.patent_number)',
            'CREATE INDEX patent_processed_time_idx IF NOT EXISTS FOR (p:Patent) ON (p.processed_time)'
        ]

        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"✅ 创建约束/索引: {constraint.split()[:3]}...")
                except Exception as e:
                    logger.warning(f"⚠️ 约束/索引可能已存在: {e}")

    def import_batch_file(self, file_path):
        """导入单个批次文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)

            patents = batch_data.get('patents', [])
            triples = batch_data.get('all_triples', [])

            if not patents and not triples:
                return {'file': str(file_path), 'processed': 0, 'error': 'No data'}

            # 使用事务处理
            with self.driver.session() as session:
                with session.begin_transaction() as tx:
                    # 创建专利节点
                    nodes_created = 0
                    for patent in patents:
                        try:
                            tx.run("""
                                MERGE (p:Patent {id: $id})
                                SET p += $properties
                            """,
                            id=patent['id'],
                            properties={
                                'source_file': patent.get('source_file'),
                                'file_name': patent.get('file_name'),
                                'file_size': patent.get('file_size'),
                                'processed_time': patent.get('processed_time'),
                                'patent_number': patent.get('patent_number'),
                                'type': patent.get('type', 'unknown')
                            })
                            nodes_created += 1
                        except Exception as e:
                            logger.error(f"创建节点失败: {e}")

                    # 创建关系
                    relationships_created = 0
                    for triple in triples:
                        try:
                            # 简单的三元组处理
                            subject = triple.get('subject')
                            predicate = triple.get('predicate')
                            obj = triple.get('object')

                            if subject and predicate and obj:
                                # 如果是专利ID，创建到专利的关系
                                if subject.startswith('patent_'):
                                    if predicate == 'has_type':
                                        tx.run("""
                                            MATCH (p:Patent {id: $subject})
                                            MERGE (t:Type {name: $object})
                                            MERGE (p)-[:HAS_TYPE]->(t)
                                        """, subject=subject, object=obj)
                                        relationships_created += 1
                                    elif predicate == 'from_source':
                                        tx.run("""
                                            MATCH (p:Patent {id: $subject})
                                            MERGE (s:Source {path: $object})
                                            MERGE (p)-[:FROM_SOURCE]->(s)
                                        """, subject=subject, object=obj)
                                        relationships_created += 1
                                    elif predicate == 'patent_number':
                                        # 更新专利号属性
                                        tx.run("""
                                            MATCH (p:Patent {id: $subject})
                                            SET p.patent_number = $object
                                        """, subject=subject, object=obj)
                        except Exception as e:
                            logger.error(f"创建关系失败: {e}")

                    tx.commit()

            # 更新统计
            with self.stats_lock:
                self.stats['processed_files'] += 1
                self.stats['total_patents'] += len(patents)
                self.stats['total_triples'] += len(triples)
                self.stats['nodes_created'] += nodes_created
                self.stats['relationships_created'] += relationships_created

            return {
                'file': str(file_path),
                'processed': len(patents),
                'nodes_created': nodes_created,
                'relationships_created': relationships_created
            }

        except Exception as e:
            logger.error(f"导入文件失败 {file_path}: {e}")
            with self.stats_lock:
                self.stats['errors'] += 1
            return {'file': str(file_path), 'processed': 0, 'error': str(e)}

    def import_all_batches(self):
        """导入所有批次文件"""
        logger.info('开始导入所有批次文件...')

        # 获取所有批次文件
        batch_files = list(self.source_dir.glob('batch_*.json'))
        batch_files.sort()

        # 排除summary.json
        batch_files = [f for f in batch_files if f.name != 'summary.json']

        self.stats['total_files'] = len(batch_files)
        logger.info(f"找到 {self.stats['total_files']} 个批次文件")

        if not batch_files:
            logger.error('未找到批次文件')
            return False

        self.stats['start_time'] = time.time()

        # 使用线程池并行导入
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(self.import_batch_file, file_path): file_path
                for file_path in batch_files
            }

            # 处理完成的任务
            completed = 0
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result(timeout=60)
                    completed += 1

                    # 计算进度
                    progress = (completed / self.stats['total_files']) * 100
                    elapsed = time.time() - self.stats['start_time']
                    speed = completed / elapsed if elapsed > 0 else 0
                    eta = (self.stats['total_files'] - completed) / speed if speed > 0 else 0

                    logger.info(f"进度: {progress:.1f}% | "
                              f"已完成: {completed}/{self.stats['total_files']} | "
                              f"速度: {speed:.1f} 文件/秒 | "
                              f"ETA: {eta:.0f}秒 | "
                              f"节点: {self.stats['nodes_created']} | "
                              f"关系: {self.stats['relationships_created']}")

                except Exception as e:
                    logger.error(f"处理文件失败 {file_path}: {e}")
                    with self.stats_lock:
                        self.stats['errors'] += 1

        self.stats['end_time'] = time.time()

        # 最终统计
        total_time = self.stats['end_time'] - self.stats['start_time']
        logger.info('=' * 60)
        logger.info('超级快速知识图谱导入完成！')
        logger.info(f"总耗时: {total_time:.2f} 秒")
        logger.info(f"处理文件数: {self.stats['processed_files']:,}")
        logger.info(f"总专利数: {self.stats['total_patents']:,}")
        logger.info(f"总三元组: {self.stats['total_triples']:,}")
        logger.info(f"创建节点: {self.stats['nodes_created']:,}")
        logger.info(f"创建关系: {self.stats['relationships_created']:,}")
        logger.info(f"错误数: {self.stats['errors']}")
        logger.info(f"平均速度: {self.stats['processed_files']/total_time:.1f} 文件/秒")
        logger.info('=' * 60)

        return True

    def get_database_statistics(self):
        """获取数据库统计信息"""
        with self.driver.session() as session:
            result = session.run('MATCH (n) RETURN count(n) as total_nodes')
            total_nodes = result.single()['total_nodes']

            result = session.run('MATCH ()-[r]->() RETURN count(r) as total_relationships')
            total_relationships = result.single()['total_relationships']

            result = session.run('MATCH (p:Patent) RETURN count(p) as total_patents')
            total_patents = result.single()['total_patents']

            return {
                'total_nodes': total_nodes,
                'total_relationships': total_relationships,
                'total_patents': total_patents
            }

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            logger.info('Neo4j连接已关闭')

def main():
    """主函数"""
    importer = SuperFastKGImporter()

    # 连接数据库
    if not importer.connect():
        return

    try:
        # 创建约束和索引
        logger.info('创建约束和索引...')
        importer.create_constraints_and_indexes()

        # 导入所有批次
        importer.import_all_batches()

        # 获取数据库统计
        logger.info("\n获取数据库统计...")
        db_stats = importer.get_database_statistics()
        logger.info(f"数据库总节点数: {db_stats['total_nodes']:,}")
        logger.info(f"数据库总关系数: {db_stats['total_relationships']:,}")
        logger.info(f"专利节点数: {db_stats['total_patents']:,}")

    finally:
        importer.close()

if __name__ == '__main__':
    main()