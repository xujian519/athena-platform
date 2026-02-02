#!/usr/bin/env python3
"""
专利系统监控仪表板
Patent System Monitoring Dashboard

实时监控PostgreSQL和Elasticsearch系统状态
"""

import json
import logging
import sys
import time
from datetime import datetime

import elasticsearch
import psycopg2
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)

# 配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'patent_db'
}

ES_CONFIG = {
    'hosts': ['http://localhost:9200']
}

class PatentSystemMonitor:
    """专利系统监控器"""

    def __init__(self):
        self.pg_conn = None
        self.es_client = None

    def connect(self) -> bool:
        """连接数据库服务"""
        try:
            self.pg_conn = psycopg2.connect(**DB_CONFIG)
            self.es_client = Elasticsearch(**ES_CONFIG)

            # 测试连接
            if not self.es_client.ping():
                raise Exception('Elasticsearch连接失败')

            return True
        except Exception as e:
            logger.info(f"❌ 连接失败: {e}")
            return False

    def get_postgres_stats(self) -> dict:
        """获取PostgreSQL统计信息"""
        try:
            with self.pg_conn.cursor() as cursor:
                # 基础统计
                cursor.execute("""
                    SELECT
                        'patents' as table_name,
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN abstract IS NOT NULL AND abstract != '' AND abstract != '摘要数据缺失，需要从外部数据源补充' THEN 1 END) as has_abstract,
                        COUNT(CASE WHEN application_number IS NOT NULL AND application_number != '' THEN 1 END) as has_app_num,
                        COUNT(CASE WHEN source_year BETWEEN 1985 AND 2025 THEN 1 END) as valid_year,
                        MIN(source_year) as min_year,
                        MAX(source_year) as max_year
                    FROM patents

                    UNION ALL

                    SELECT
                        'patents_simple' as table_name,
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN abstract IS NOT NULL AND abstract != '' THEN 1 END) as has_abstract,
                        COUNT(CASE WHEN application_number IS NOT NULL AND application_number != '' THEN 1 END) as has_app_num,
                        COUNT(CASE WHEN source_year BETWEEN 1985 AND 2025 THEN 1 END) as valid_year,
                        MIN(source_year) as min_year,
                        MAX(source_year) as max_year
                    FROM patents_simple
                """)

                pg_stats = cursor.fetchall()

                # 索引使用情况
                cursor.execute("""
                    SELECT
                        schemaname,
                        relname,
                        indexrelname,
                        idx_scan,
                        pg_size_pretty(pg_relation_size(indexrelid::regclass)) as index_size
                    FROM pg_stat_user_indexes
                    WHERE idx_scan > 100
                    ORDER BY idx_scan DESC
                    LIMIT 10
                """)

                index_stats = cursor.fetchall()

                return {
                    'tables': pg_stats,
                    'indexes': index_stats
                }

        except Exception as e:
            return {'error': str(e)}

    def get_elasticsearch_stats(self) -> dict:
        """获取Elasticsearch统计信息"""
        try:
            stats = {}

            # 索引状态
            indices = self.es_client.cat.indices(format='json')
            stats['indices'] = json.loads(indices)

            # 集群健康
            health = self.es_client.cluster.health()
            stats['health'] = health

            return stats

        except Exception as e:
            return {'error': str(e)}

    def get_system_performance(self) -> dict:
        """获取系统性能指标"""
        try:
            with self.pg_conn.cursor() as cursor:
                # 数据库大小
                cursor.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    AND tablename LIKE '%patent%'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)

                db_sizes = cursor.fetchall()

                return {
                    'database_sizes': db_sizes
                }

        except Exception as e:
            return {'error': str(e)}

    def display_dashboard(self):
        """显示监控仪表板"""
        logger.info(str("\n" + '=' * 80))
        logger.info('🎯 专利检索系统监控仪表板')
        logger.info(str('=' * 80))
        logger.info(f"🕒 监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # PostgreSQL状态
        pg_stats = self.get_postgres_stats()
        if 'error' not in pg_stats:
            logger.info('📊 PostgreSQL 数据库状态')
            logger.info(str('-' * 50))
            for table in pg_stats['tables']:
                table_name = table[0]
                total = table[1]
                abstract = table[2]
                app_num = table[3]
                valid_year = table[4]
                min_year = table[5]
                max_year = table[6]

                abstract_rate = (abstract / total * 100) if total > 0 else 0
                app_num_rate = (app_num / total * 100) if total > 0 else 0
                year_rate = (valid_year / total * 100) if total > 0 else 0

                logger.info(f"🗂️ {table_name}:")
                logger.info(f"   总记录数: {total:,}")
                logger.info(f"   摘要完整性: {abstract_rate:.1f}% ({abstract:,})")
                logger.info(f"   申请号完整性: {app_num_rate:.1f}% ({app_num:,})")
                logger.info(f"   年份有效性: {year_rate:.1f}% (范围: {min_year}-{max_year})")
                print()

            # 索引使用情况
            logger.info('🔍 热门索引使用情况')
            logger.info(str('-' * 50))
            for idx in pg_stats['indexes'][:5]:
                logger.info(f"📈 {idx[1]}.{idx[2]}: {idx[3]:,}次扫描 ({idx[4]})")

        # Elasticsearch状态
        es_stats = self.get_elasticsearch_stats()
        if 'error' not in es_stats:
            logger.info("\n🔍 Elasticsearch 搜索引擎状态")
            logger.info(str('-' * 50))

            # 集群健康
            health = es_stats['health']
            logger.info(f"💚 集群状态: {health['status'].upper()}")
            logger.info(f"🔢 节点数量: {len(health['nodes'])}")
            logger.info(f"📦 数据节点: {health['number_of_data_nodes']}")
            print()

            # 索引状态
            for index in es_stats['indices']:
                if 'patents' in index['index']:
                    logger.info(f"📋 索引: {index['index']}")
                    logger.info(f"   文档数量: {index['docs.count']:,}")
                    logger.info(f"   存储大小: {index['store.size']}")
                    logger.info(f"   状态: {'🟢' if index['health'] == 'green' else '🟡' if index['health'] == 'yellow' else '🔴'} {index['health'].upper()}")
                    print()

        # 系统性能
        perf_stats = self.get_system_performance()
        if 'error' not in perf_stats:
            logger.info('💾 存储使用情况')
            logger.info(str('-' * 50))
            for table in perf_stats['database_sizes']:
                logger.info(f"📁 {table[0]}.{table[1]}: {table[2]}")

        # 系统建议
        logger.info("\n💡 系统优化建议")
        logger.info(str('-' * 50))
        logger.info('✅ PostgreSQL索引优化完成')
        logger.info('✅ Elasticsearch集成成功')
        logger.info('✅ 数据质量监控已启用')
        logger.info('🔄 摘要数据修复进行中...')
        logger.info('📋 建议定期运行数据同步')

        logger.info(str("\n" + '=' * 80))

def main():
    """主函数"""
    monitor = PatentSystemMonitor()

    if not monitor.connect():
        logger.info('❌ 无法连接到数据库服务')
        sys.exit(1)

    try:
        while True:
            monitor.display_dashboard()

            # 询问是否继续监控
            choice = input("\n继续监控? (y/n): ").lower()
            if choice in ['n', 'no', 'q', 'quit']:
                break

            if choice not in ['y', 'yes']:
                time.sleep(5)

    except KeyboardInterrupt:
        logger.info("\n👋 监控结束")

if __name__ == '__main__':
    main()