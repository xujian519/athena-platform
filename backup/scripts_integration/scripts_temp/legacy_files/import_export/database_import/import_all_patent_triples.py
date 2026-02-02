#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量导入所有专利三元组到Neo4j数据库
"""

import glob
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from neo4j import GraphDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/patent_triples_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PatentTripleImporter:
    def __init__(self, uri='bolt://localhost:7687', user='neo4j', password='password'):
        """初始化导入器"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.stats = {
            'total_nodes': 0,
            'total_relationships': 0,
            'batches_processed': 0,
            'errors': 0,
            'start_time': None
        }
        self.lock = threading.Lock()

    def close(self):
        """关闭数据库连接"""
        self.driver.close()

    def setup_constraints(self):
        """设置数据库约束"""
        with self.driver.session() as session:
            # 创建专利节点约束
            try:
                session.run("""
                    CREATE CONSTRAINT FOR (p:Patent) REQUIRE p.id IS UNIQUE
                """)
                logger.info('创建专利ID约束成功')
            except Exception as e:
                logger.warning(f"专利约束已存在: {e}")

            # 创建实体节点约束
            try:
                session.run("""
                    CREATE CONSTRAINT FOR (e:Entity) REQUIRE e.name IS UNIQUE
                """)
                logger.info('创建实体名称约束成功')
            except Exception as e:
                logger.warning(f"实体约束已存在: {e}")

    def import_batch(self, batch_file, batch_id):
        """导入单个批次的三元组"""
        start_time = time.time()
        logger.info(f"开始导入批次 {batch_id}: {batch_file.name}")

        try:
            # 读取批次文件
            with open(batch_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            triples = data.get('all_triples', [])
            patents = data.get('patents', [])

            if not triples:
                logger.warning(f"批次 {batch_id} 没有三元组数据")
                return

            with self.driver.session() as session:
                # 1. 创建专利节点
                for patent in patents:
                    self._create_patent_node(session, patent)

                # 2. 创建三元组关系
                for triple in triples:
                    self._create_triple(session, triple)

            # 更新统计
            with self.lock:
                self.stats['batches_processed'] += 1
                self.stats['total_nodes'] += len(patents)
                self.stats['total_relationships'] += len(triples)

            elapsed = time.time() - start_time
            logger.info(f"批次 {batch_id} 导入完成: "
                       f"{len(patents)} 节点, {len(triples)} 关系, "
                       f"耗时 {elapsed:.2f} 秒")

        except Exception as e:
            logger.error(f"批次 {batch_id} 导入失败: {e}")
            with self.lock:
                self.stats['errors'] += 1

    def _create_patent_node(self, session, patent):
        """创建专利节点"""
        query = """
            MERGE (p:Patent {id: $id})
            SET p.source_file = $source_file,
                p.file_name = $file_name,
                p.file_size = $file_size,
                p.processed_time = $processed_time,
                p.patent_number = $patent_number,
                p.type = $type,
                p.created_at = datetime()
        """
        session.run(query,
                   id=patent.get('id'),
                   source_file=patent.get('source_file'),
                   file_name=patent.get('file_name'),
                   file_size=patent.get('file_size'),
                   processed_time=patent.get('processed_time'),
                   patent_number=patent.get('patent_number'),
                   type=patent.get('type'))

    def _create_triple(self, session, triple):
        """创建三元组关系"""
        subject = triple.get('subject')
        predicate = triple.get('predicate')
        object = triple.get('object')

        if not all([subject, predicate, object]):
            return

        # 根据谓词确定关系类型和节点标签
        if predicate in ['has_type', 'patent_number']:
            # 专利属性
            query = """
                MATCH (p:Patent {id: $subject})
                SET p.`%s` = $object
            """ % predicate
            session.run(query, subject=subject, object=object)

        elif predicate == 'from_source':
            # 源文件属性
            query = """
                MATCH (p:Patent {id: $subject})
                SET p.source_path = $object
            """
            session.run(query, subject=subject, object=object)

        else:
            # 创建实体关系
            # 主语是专利
            if subject.startswith('patent_'):
                query = """
                    MATCH (p:Patent {id: $subject})
                    MERGE (e:Entity {name: $object})
                    MERGE (p)-[r:%s]->(e)
                    SET r.created_at = datetime()
                """ % predicate.upper()
            # 宾语是专利
            elif object.startswith('patent_'):
                query = """
                    MERGE (e:Entity {name: $subject})
                    MATCH (p:Patent {id: $object})
                    MERGE (e)-[r:%s]->(p)
                    SET r.created_at = datetime()
                """ % predicate.upper()
            # 两者都是实体
            else:
                query = """
                    MERGE (s:Entity {name: $subject})
                    MERGE (o:Entity {name: $object})
                    MERGE (s)-[r:%s]->(o)
                    SET r.created_at = datetime()
                """ % predicate.upper()

            session.run(query, subject=subject, object=object)

    def import_all_batches(self, max_workers=4):
        """导入所有批次文件"""
        self.stats['start_time'] = time.time()

        # 获取所有批次文件
        batch_dir = Path('/Users/xujian/Athena工作平台/data/knowledge_graph_neo4j/raw_data/patent_kg_superfast')
        batch_files = sorted(batch_dir.glob('batch_*.json'))

        logger.info(f"找到 {len(batch_files)} 个批次文件")
        logger.info(f"使用 {max_workers} 个线程并行导入")

        # 设置约束
        self.setup_constraints()

        # 使用线程池并行导入
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, batch_file in enumerate(batch_files):
                future = executor.submit(self.import_batch, batch_file, i)
                futures.append(future)

            # 等待所有任务完成
            for i, future in enumerate(futures):
                try:
                    future.result()
                    logger.info(f"进度: {i+1}/{len(futures)} 批次完成")
                except Exception as e:
                    logger.error(f"批次 {i} 处理异常: {e}")

        # 打印最终统计
        self.print_stats()

    def print_stats(self):
        """打印导入统计信息"""
        elapsed = time.time() - self.stats['start_time']

        logger.info('=' * 80)
        logger.info('📊 专利三元组导入完成统计')
        logger.info('=' * 80)
        logger.info(f"✅ 批次文件数: {self.stats['batches_processed']}")
        logger.info(f"✅ 创建节点数: {self.stats['total_nodes']:,}")
        logger.info(f"✅ 创建关系数: {self.stats['total_relationships']:,}")
        logger.info(f"❌ 错误数量: {self.stats['errors']}")
        logger.info(f"⏱️  总耗时: {elapsed:.2f} 秒")

        if self.stats['total_relationships'] > 0:
            logger.info(f"🚀 平均速度: {self.stats['total_relationships']/elapsed:.1f} 关系/秒")

        logger.info('=' * 80)

        # 验证导入结果
        self.verify_import()

    def verify_import(self):
        """验证导入结果"""
        logger.info('🔍 验证导入结果...')

        with self.driver.session() as session:
            # 统计节点数
            result = session.run('MATCH (p:Patent) RETURN count(p) as count')
            patent_count = result.single()['count']

            # 统计关系数
            result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
            rel_count = result.single()['count']

            # 统计实体数
            result = session.run('MATCH (e:Entity) RETURN count(e) as count')
            entity_count = result.single()['count']

            logger.info(f"📈 Neo4j数据库验证:")
            logger.info(f"  • 专利节点: {patent_count:,}")
            logger.info(f"  • 实体节点: {entity_count:,}")
            logger.info(f"  • 关系总数: {rel_count:,}")

            # 查看一些示例
            result = session.run('MATCH (p:Patent) RETURN p.patent_number as num LIMIT 5')
            patents = [record['num'] for record in result if record['num']]
            if patents:
                logger.info(f"  • 示例专利号: {', '.join(patents[:3])}...")

def main():
    """主函数"""
    # 确保日志目录存在
    Path('logs').mkdir(exist_ok=True)

    logger.info('=' * 80)
    logger.info('🚀 开始导入专利三元组到Neo4j')
    logger.info('=' * 80)

    # 创建导入器
    importer = PatentTripleImporter()

    try:
        # 导入所有批次
        importer.import_all_batches(max_workers=6)  # 使用6个线程

    except KeyboardInterrupt:
        logger.info('⚠️  用户中断导入')
    except Exception as e:
        logger.error(f"❌ 导入失败: {e}")
    finally:
        # 关闭连接
        importer.close()
        logger.info('🔚 导入任务结束')

if __name__ == '__main__':
    main()