#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终的Neo4j导入脚本（修复了语法错误）
作者：小娜
日期：2025-12-07
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from neo4j import GraphDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'documentation/logs/final_neo4j_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinalNeo4jImporter:
    """最终Neo4j导入器"""

    def __init__(self):
        self.uri = 'bolt://localhost:7687'
        self.user = 'neo4j'
        self.password = 'password'
        self.driver = None
        self.source_dir = Path('/Users/xujian/Athena工作平台/data/knowledge_graph_neo4j/raw_data/patent_kg_superfast')
        self.processed_count = 0
        self.error_count = 0

    def connect(self):
        """连接到Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50
            )
            with self.driver.session() as session:
                session.run('RETURN 1')
            logger.info('✅ Neo4j连接成功')
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            return False

    def setup_constraints(self):
        """创建约束（使用新版本语法）"""
        constraints = [
            # 使用新版本语法 FOR ... REQUIRE ...
            'CREATE CONSTRAINT patent_id_unique IF NOT EXISTS FOR (p:Patent) REQUIRE p.id IS UNIQUE',
            'CREATE INDEX patent_type_idx IF NOT EXISTS FOR (p:Patent) ON (p.type)',
            'CREATE INDEX patent_number_idx IF NOT EXISTS FOR (p:Patent) ON (p.patent_number)',
            'CREATE INDEX patent_processed_time_idx IF NOT EXISTS FOR (p:Patent) ON (p.processed_time)'
        ]

        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"✅ 约束/索引创建成功")
                except Exception as e:
                    if 'already exists' not in str(e):
                        logger.warning(f"⚠️ 约束/索引警告: {e}")

    def import_batch_file(self, batch_file, batch_num, total_batches):
        """导入单个批次文件"""
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)

            patents = batch_data.get('patents', [])
            if not patents:
                logger.warning(f"批次文件没有专利数据: {batch_file}")
                return

            # 分批处理，每批50个专利
            batch_size = 50
            for i in range(0, len(patents), batch_size):
                batch_patents = patents[i:i+batch_size]

                with self.driver.session() as session:
                    # 使用事务批量创建
                    with session.begin_transaction() as tx:
                        for patent in batch_patents:
                            try:
                                tx.run("""
                                    MERGE (p:Patent {id: $id})
                                    SET p.source_file = $source_file,
                                        p.file_name = $file_name,
                                        p.file_size = $file_size,
                                        p.processed_time = $processed_time,
                                        p.patent_number = $patent_number,
                                        p.type = $type
                                """,
                                id=patent.get('id'),
                                source_file=patent.get('source_file', ''),
                                file_name=patent.get('file_name', ''),
                                file_size=patent.get('file_size', 0),
                                processed_time=patent.get('processed_time', ''),
                                patent_number=patent.get('patent_number', ''),
                                type=patent.get('type', 'unknown'))
                            except Exception as e:
                                logger.error(f"创建专利节点失败: {e}")
                                self.error_count += 1

                        tx.commit()

                self.processed_count += len(batch_patents)

                # 显示进度
                progress = (batch_num * len(patents) + i + batch_size) / (total_batches * 500) * 100
                logger.info(f"进度: {progress:.1f}% | 批次 {batch_num+1}/{total_batches} | "
                          f"已处理: {self.processed_count:,} | 错误: {self.error_count}")

        except Exception as e:
            logger.error(f"导入批次文件失败 {batch_file}: {e}")
            self.error_count += 1

    def import_all_patents(self):
        """导入所有专利数据"""
        logger.info('开始导入所有专利数据到Neo4j...')

        # 检查源目录
        if not self.source_dir.exists():
            logger.error(f"源目录不存在: {self.source_dir}")
            return

        # 获取所有批次文件
        batch_files = sorted(self.source_dir.glob('batch_*.json'))
        total_batches = len(batch_files)

        if total_batches == 0:
            logger.error('未找到批次文件')
            return

        logger.info(f"找到 {total_batches} 个批次文件，开始导入...")

        # 记录开始时间
        start_time = time.time()

        # 逐个导入批次
        for idx, batch_file in enumerate(batch_files):
            self.import_batch_file(batch_file, idx, total_batches)

        # 计算统计信息
        elapsed_time = time.time() - start_time
        speed = self.processed_count / elapsed_time if elapsed_time > 0 else 0

        logger.info('=' * 60)
        logger.info('导入完成！')
        logger.info(f"总耗时: {elapsed_time:.2f} 秒")
        logger.info(f"成功导入: {self.processed_count:,} 个专利")
        logger.info(f"错误数量: {self.error_count}")
        logger.info(f"平均速度: {speed:.0f} 专利/秒")
        logger.info('=' * 60)

        # 验证导入结果
        self.verify_import()

    def verify_import(self):
        """验证导入结果"""
        logger.info("\n验证导入结果...")

        with self.driver.session() as session:
            # 获取专利总数
            result = session.run('MATCH (p:Patent) RETURN count(p) as count')
            patent_count = result.single()['count']
            logger.info(f"✅ 数据库中专利节点数: {patent_count:,}")

            # 获取类型统计
            result = session.run('MATCH (p:Patent) RETURN p.type, count(p) as count ORDER BY count DESC')
            logger.info("\n专利类型统计:")
            for record in result:
                logger.info(f"  - {record['p.type']}: {record['count']:,}")

            # 获取有专利号的统计
            result = session.run('MATCH (p:Patent) WHERE p.patent_number IS NOT NULL RETURN count(p) as count')
            patent_with_number = result.single()['count']
            logger.info(f"\n有专利号的专利: {patent_with_number:,}")

            # 显示示例
            result = session.run('MATCH (p:Patent) RETURN p.id, p.file_name LIMIT 5')
            logger.info("\n示例专利:")
            for record in result:
                logger.info(f"  - ID: {record['p.id']}, 文件: {record['p.file_name']}")

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            logger.info('Neo4j连接已关闭')

def main():
    """主函数"""
    logger.info('启动最终Neo4j导入系统...')

    # 创建导入器
    importer = FinalNeo4jImporter()

    # 连接数据库
    if not importer.connect():
        logger.error('无法连接到Neo4j，退出')
        sys.exit(1)

    try:
        # 设置约束
        logger.info('设置数据库约束...')
        importer.setup_constraints()

        # 导入数据
        importer.import_all_patents()

    except KeyboardInterrupt:
        logger.info("\n用户中断导入")
    except Exception as e:
        logger.error(f"导入过程发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        importer.close()
        logger.info('导入系统结束')

if __name__ == '__main__':
    main()