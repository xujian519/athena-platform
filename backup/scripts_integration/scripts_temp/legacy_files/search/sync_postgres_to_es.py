#!/usr/bin/env python3
"""
PostgreSQL到Elasticsearch数据同步脚本
Sync PostgreSQL Data to Elasticsearch

将专利数据从PostgreSQL同步到Elasticsearch，支持增量更新
"""

import json
import logging
import sys
import time
from datetime import datetime

import elasticsearch
import psycopg2
from elasticsearch import Elasticsearch
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'patent_db'
}

# Elasticsearch配置
ES_CONFIG = {
    'hosts': ['http://localhost:9200'],
    'timeout': 30
}

class PostgresToESSync:
    """PostgreSQL到ES同步工具"""

    def __init__(self):
        """初始化同步工具"""
        self.pg_conn = None
        self.es_client = None
        self.stats = {
            'total_processed': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'start_time': None,
            'end_time': None
        }

    def connect_postgresql(self) -> bool:
        """连接PostgreSQL"""
        try:
            self.pg_conn = psycopg2.connect(**DB_CONFIG)
            self.pg_conn.autocommit = True
            logger.info('✅ PostgreSQL连接成功')
            return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL连接失败: {e}")
            return False

    def connect_elasticsearch(self) -> bool:
        """连接Elasticsearch"""
        try:
            self.es_client = Elasticsearch(**ES_CONFIG)
            if self.es_client.ping():
                logger.info('✅ Elasticsearch连接成功')
                return True
            else:
                logger.error('❌ Elasticsearch连接失败')
                return False
        except Exception as e:
            logger.error(f"❌ Elasticsearch连接失败: {e}")
            return False

    def get_total_records(self) -> int:
        """获取总记录数"""
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM patents_simple
                    WHERE patent_name IS NOT NULL
                    AND patent_name != ''
                """)
                total = cursor.fetchone()[0]
                logger.info(f"📊 待同步记录总数: {total:,}")
                return total
        except Exception as e:
            logger.error(f"❌ 获取记录数失败: {e}")
            return 0

    def sync_batch(self, offset: int, batch_size: int = 1000) -> int:
        """同步一批数据"""
        try:
            # 从PostgreSQL获取数据
            with self.pg_conn.cursor() as cursor:
                sql = """
                SELECT
                    id,
                    COALESCE(application_number, '') as application_number,
                    COALESCE(patent_name, '') as patent_name,
                    COALESCE(abstract, '') as abstract,
                    COALESCE(applicant, '') as applicant,
                    COALESCE(patent_type, '') as patent_type,
                    COALESCE(source_year, 0) as source_year,
                    COALESCE(ipc_code, '') as ipc_code,
                    '' as current_assignee,
                    '' as applicant_region,
                    0 as citation_count,
                    0.8 as data_quality_score,
                    %s as sync_timestamp
                FROM patents_simple
                WHERE patent_name IS NOT NULL
                AND patent_name != ''
                ORDER BY id
                LIMIT %s OFFSET %s
                """

                cursor.execute(sql, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), batch_size, offset))
                records = cursor.fetchall()

                # 准备ES文档
                documents = []
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                for row in records:
                    doc = {
                        'id': row[0],
                        'application_number': row[1],
                        'patent_name': row[2],
                        'abstract': row[3],
                        'applicant': row[4],
                        'patent_type': row[5],
                        'source_year': row[6],
                        'ipc_main_class': row[7],  # 使用ipc_code映射到ipc_main_class
                        'current_assignee': row[8],
                        'applicant_region': row[9],
                        'citation_count': row[10],
                        'data_quality_score': row[11],
                        'sync_timestamp': row[12]
                    }
                    documents.append(doc)

                # 批量插入到Elasticsearch
                if documents:
                    success_count = self.bulk_insert_es(documents)
                    return success_count

                return 0

        except Exception as e:
            logger.error(f"❌ 同步批次失败: {e}")
            return 0

    def bulk_insert_es(self, documents: list) -> int:
        """批量插入到Elasticsearch"""
        try:
            from elasticsearch.helpers import bulk

            def generate_actions():
                for doc in documents:
                    yield {
                        '_index': 'patents_simple',
                        '_id': doc['id'],
                        '_source': doc
                    }

            success_count, failed_items = bulk(
                self.es_client,
                generate_actions(),
                stats_only=True,
                request_timeout=60
            )

            return success_count

        except Exception as e:
            logger.error(f"❌ ES批量插入失败: {e}")
            return 0

    def sync_all_data(self, batch_size: int = 1000, limit: int = None) -> bool:
        """同步所有数据"""
        logger.info('🚀 开始数据同步')

        self.stats['start_time'] = time.time()

        # 获取总记录数
        total_records = self.get_total_records()
        if total_records == 0:
            logger.warning('⚠️ 没有数据需要同步')
            return False

        # 限制同步数量（用于测试）
        if limit:
            total_records = min(total_records, limit)
            logger.info(f"🔧 测试模式：仅同步 {total_records:,} 条记录")

        # 分批同步
        with tqdm(total=total_records, desc='同步进度', unit='条') as pbar:
            offset = 0

            while offset < total_records:
                current_batch_size = min(batch_size, total_records - offset)

                # 同步当前批次
                synced_count = self.sync_batch(offset, current_batch_size)

                self.stats['total_processed'] += current_batch_size
                self.stats['successful_syncs'] += synced_count
                self.stats['failed_syncs'] += (current_batch_size - synced_count)

                pbar.update(current_batch_size)

                # 显示当前进度
                if offset % (batch_size * 10) == 0:
                    logger.info(f"📊 已处理: {self.stats['total_processed']:,}条, "
                              f"成功: {self.stats['successful_syncs']:,}条, "
                              f"失败: {self.stats['failed_syncs']:,}条")

                offset += current_batch_size

                # 短暂休息，避免过载
                time.sleep(0.1)

        self.stats['end_time'] = time.time()

        # 输出同步结果
        duration = self.stats['end_time'] - self.stats['start_time']
        success_rate = (self.stats['successful_syncs'] / self.stats['total_processed'] * 100) if self.stats['total_processed'] > 0 else 0

        logger.info(str("\n" + '=' * 60))
        logger.info('📊 数据同步完成报告')
        logger.info(str('=' * 60))
        logger.info(f"✅ 总处理记录: {self.stats['total_processed']:,}")
        logger.info(f"✅ 成功同步: {self.stats['successful_syncs']:,}")
        logger.info(f"❌ 失败记录: {self.stats['failed_syncs']:,}")
        logger.info(f"📈 成功率: {success_rate:.2f}%")
        logger.info(f"⏱️ 总耗时: {duration:.2f}秒")
        logger.info(f"⚡ 平均速度: {self.stats['total_processed']/duration:.1f}条/秒")

        return True

    def test_search(self) -> bool:
        """测试搜索功能"""
        logger.info('🧪 测试搜索功能...')

        try:
            # 等待ES索引刷新
            time.sleep(2)

            test_queries = ['人工智能', '机器学习', '传感器', '温室', '通风']

            for query in test_queries:
                search_body = {
                    'query': {
                        'multi_match': {
                            'query': query,
                            'fields': ['patent_name^3', 'abstract^2'],
                            'type': 'best_fields'
                        }
                    },
                    'size': 5
                }

                response = self.es_client.search(
                    index='patents_simple',
                    body=search_body
                )

                hits = response['hits']['hits']
                logger.info(f"🔍 搜索 '{query}': {len(hits)}条结果")

                # 显示前3个结果
                for i, hit in enumerate(hits[:3], 1):
                    title = hit['_source'].get('patent_name', 'N/A')
                    score = hit['_score']
                    logger.info(f"   {i}. [{score:.2f}] {title}")

            return True

        except Exception as e:
            logger.error(f"❌ 搜索测试失败: {e}")
            return False

    def run_sync(self, batch_size: int = 1000, limit: int = None, test_mode: bool = False) -> bool:
        """运行完整同步流程"""
        success = True

        # 连接数据库
        if not self.connect_postgresql():
            return False

        if not self.connect_elasticsearch():
            return False

        # 数据同步
        if test_mode:
            # 测试模式：只同步少量数据
            logger.info('🧪 测试模式：同步1000条记录')
            success = self.sync_all_data(batch_size=100, limit=1000)
        else:
            success = self.sync_all_data(batch_size=batch_size, limit=limit)

        # 搜索测试
        if success:
            self.test_search()

        return success

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='PostgreSQL到Elasticsearch数据同步')
    parser.add_argument('--batch-size', type=int, default=1000, help='批处理大小')
    parser.add_argument('--limit', type=int, help='限制同步记录数')
    parser.add_argument('--test', action='store_true', help='测试模式（同步1000条）')

    args = parser.parse_args()

    logger.info('🔄 PostgreSQL到Elasticsearch数据同步')
    logger.info(str('=' * 50))

    if args.test:
        logger.info('🧪 测试模式')
    else:
        logger.info('🚀 生产模式')

    sync_tool = PostgresToESSync()
    success = sync_tool.run_sync(
        batch_size=args.batch_size,
        limit=args.limit,
        test_mode=args.test
    )

    if success:
        logger.info("\n✅ 同步完成！")
        logger.info("\n🚀 后续建议:")
        logger.info('1. 检查Elasticsearch索引健康状态')
        logger.info('2. 进行搜索性能测试')
        logger.info('3. 配置定时增量同步')
        logger.info('4. 监控同步任务状态')
    else:
        logger.info("\n❌ 同步失败！")
        logger.info('请检查错误日志并重试')

    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)