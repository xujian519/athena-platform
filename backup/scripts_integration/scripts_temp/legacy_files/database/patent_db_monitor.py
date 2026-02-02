#!/usr/bin/env python3
"""
专利数据库监控和维护脚本
Patent Database Monitoring and Maintenance Script
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/patent_db_monitor.log'),
        logging.StreamHandler()
    ]
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

class PatentDatabaseMonitor:
    """专利数据库监控类"""

    def __init__(self):
        self.conn = None

    def get_connection(self):
        """获取数据库连接"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        if not self.conn:
            return {}

        cursor = self.conn.cursor()

        stats = {}

        try:
            # 基本统计
            cursor.execute("""
                SELECT
                    pg_size_pretty(pg_total_relation_size('patents')) as total_size,
                    pg_size_pretty(pg_relation_size('patents')) as data_size,
                    pg_size_pretty(pg_total_relation_size('patents') - pg_relation_size('patents')) as index_size,
                    COUNT(*) as total_records
                FROM patents
            """)
            result = cursor.fetchone()
            stats['storage'] = {
                'total_size': result[0],
                'data_size': result[1],
                'index_size': result[2],
                'total_records': result[3]
            }

            # 索引统计
            cursor.execute("""
                SELECT
                    COUNT(*) as index_count,
                    pg_size_pretty(SUM(pg_relation_size(indexrelid))) as total_index_size
                FROM pg_indexes
                WHERE tablename = 'patents'
            """)
            result = cursor.fetchone()
            stats['indexes'] = {
                'count': result[0],
                'total_size': result[1]
            }

            # 查询性能统计
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch
                FROM pg_stat_user_tables
                WHERE tablename = 'patents'
            """)
            result = cursor.fetchone()
            if result:
                stats['performance'] = {
                    'sequential_scans': result[2],
                    'sequential_reads': result[3],
                    'index_scans': result[4],
                    'index_fetches': result[5]
                }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
        finally:
            cursor.close()

        return stats

    def check_slow_queries(self) -> List[Dict[str, Any]]:
        """检查慢查询"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        slow_queries = []

        try:
            cursor.execute("""
                SELECT
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements
                WHERE mean_time > 1000
                ORDER BY mean_time DESC
                LIMIT 10
            """)

            results = cursor.fetchall()
            for row in results:
                slow_queries.append({
                    'query': row[0][:100] + '...' if len(row[0]) > 100 else row[0],
                    'calls': row[1],
                    'total_time': row[2],
                    'mean_time': row[3],
                    'rows': row[4]
                })

        except Exception as e:
            logger.error(f"检查慢查询失败: {e}")
        finally:
            cursor.close()

        return slow_queries

    def analyze_table_usage(self) -> Dict[str, Any]:
        """分析表使用情况"""
        if not self.conn:
            return {}

        cursor = self.conn.cursor()
        usage = {}

        try:
            # 分析表使用情况
            cursor.execute("""
                SELECT
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE tablename = 'patents'
            """)
            result = cursor.fetchone()

            if result:
                usage = {
                    'inserts': result[0],
                    'updates': result[1],
                    'deletes': result[2],
                    'live_tuples': result[3],
                    'dead_tuples': result[4],
                    'dead_tuple_ratio': result[4] / (result[3] + result[4]) * 100 if (result[3] + result[4]) > 0 else 0,
                    'last_vacuum': result[5],
                    'last_autovacuum': result[6],
                    'last_analyze': result[7],
                    'last_autoanalyze': result[8]
                }

        except Exception as e:
            logger.error(f"分析表使用情况失败: {e}")
        finally:
            cursor.close()

        return usage

    def generate_optimization_report(self) -> str:
        """生成优化报告"""
        stats = self.get_database_stats()
        slow_queries = self.check_slow_queries()
        usage = self.analyze_table_usage()

        report = []
        report.append('🔍 专利数据库优化报告')
        report.append('=' * 50)
        report.append(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append('')

        # 存储分析
        if 'storage' in stats:
            report.append('📊 存储分析:')
            report.append(f"  总大小: {stats['storage']['total_size']}")
            report.append(f"  数据大小: {stats['storage']['data_size']}")
            report.append(f"  索引大小: {stats['storage']['index_size']}")
            report.append(f"  记录数: {stats['storage']['total_records']:,}")

            # 索引效率分析
            data_gb = self._convert_size_to_gb(stats['storage']['data_size'])
            index_gb = self._convert_size_to_gb(stats['storage']['index_size'])
            if index_gb > data_gb * 0.5:
                report.append('  ⚠️  索引占用空间过多，建议优化')
            report.append('')

        # 性能分析
        if 'performance' in stats:
            report.append('⚡ 性能分析:')
            perf = stats['performance']
            total_scans = perf.get('sequential_scans', 0) + perf.get('index_scans', 0)
            if total_scans > 0:
                index_ratio = perf.get('index_scans', 0) / total_scans * 100
                report.append(f"  索引扫描比例: {index_ratio:.1f}%")

                if index_ratio < 80:
                    report.append('  ⚠️  索引使用率偏低，建议检查查询语句')

        # 表使用情况
        if usage:
            report.append('🔧 表维护状态:')
            report.append(f"  活跃记录: {usage.get('live_tuples', 0):,}")
            report.append(f"  死亡记录: {usage.get('dead_tuples', 0):,}")
            report.append(f"  死亡记录比例: {usage.get('dead_tuple_ratio', 0):.1f}%")

            if usage.get('dead_tuple_ratio', 0) > 5:
                report.append('  ⚠️  死亡记录过多，建议执行VACUUM')
            report.append('')

        # 慢查询
        if slow_queries:
            report.append('🐌 慢查询分析:')
            for i, query in enumerate(slow_queries[:5], 1):
                report.append(f"  {i}. 平均耗时: {query['mean_time']:.1f}ms")
                report.append(f"     调用次数: {query['calls']}")
                report.append(f"     查询: {query['query'][:80]}...")
            report.append('')

        # 优化建议
        report.append('💡 优化建议:')
        recommendations = []

        if usage and usage.get('dead_tuple_ratio', 0) > 5:
            recommendations.append('  • 执行 VACUUM ANALYZE patents;')

        if 'storage' in stats and self._convert_size_to_gb(stats['storage']['index_size']) > self._convert_size_to_gb(stats['storage']['data_size']):
            recommendations.append('  • 检查并优化冗余索引')

        if slow_queries:
            recommendations.append('  • 分析并优化慢查询语句')

        if not recommendations:
            recommendations.append('  • 当前数据库性能良好，继续保持')

        report.extend(recommendations)

        return "\n".join(report)

    def _convert_size_to_gb(self, size_str: str) -> float:
        """将大小字符串转换为GB"""
        if not size_str:
            return 0.0

        size_str = size_str.strip().upper()
        if 'GB' in size_str:
            return float(size_str.replace('GB', ''))
        elif 'MB' in size_str:
            return float(size_str.replace('MB', '')) / 1024
        elif 'KB' in size_str:
            return float(size_str.replace('KB', '')) / (1024 * 1024)
        elif 'TB' in size_str:
            return float(size_str.replace('TB', '')) * 1024
        return 0.0

    def run_maintenance(self):
        """执行维护任务"""
        if not self.conn:
            logger.error('数据库连接失败，无法执行维护')
            return False

        cursor = self.conn.cursor()

        try:
            logger.info('开始执行数据库维护...')

            # 更新表统计信息
            logger.info('更新表统计信息...')
            cursor.execute('ANALYZE patents;')

            # 清理死元组
            logger.info('清理死元组...')
            cursor.execute('VACUUM (ANALYZE, VERBOSE) patents;')

            # 重建索引（如果需要）
            logger.info('检查索引状态...')
            cursor.execute('REINDEX INDEX CONCURRENTLY idx_patents_search_vector;')

            self.conn.commit()
            logger.info('数据库维护完成')
            return True

        except Exception as e:
            logger.error(f"维护任务失败: {e}")
            self.conn.rollback()
            return False
        finally:
            cursor.close()

    def monitor_database(self, interval: int = 300):
        """持续监控数据库"""
        logger.info('开始数据库监控...')

        while True:
            try:
                # 重新连接（避免长时间连接超时）
                if self.conn:
                    self.conn.close()

                if not self.get_connection():
                    logger.error('重新连接失败，等待重试...')
                    time.sleep(30)
                    continue

                # 生成报告
                report = self.generate_optimization_report()
                logger.info("\n" + report)

                # 保存报告到文件
                with open(f"documentation/logs/db_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w') as f:
                    f.write(report)

                # 检查是否需要自动维护
                stats = self.analyze_table_usage()
                if stats and stats.get('dead_tuple_ratio', 0) > 10:
                    logger.warning('检测到大量死元组，执行自动维护...')
                    self.run_maintenance()

            except KeyboardInterrupt:
                logger.info('监控已停止')
                break
            except Exception as e:
                logger.error(f"监控过程中出错: {e}")

            time.sleep(interval)

def main():
    """主函数"""
    monitor = PatentDatabaseMonitor()

    # 单次检查
    if not monitor.get_connection():
        logger.error('无法连接到数据库')
        return

    logger.info(str(monitor.generate_optimization_report()))

    # 询问是否开始持续监控
    try:
        choice = input("\n是否开始持续监控? (y/n): ").lower()
        if choice == 'y':
            monitor.monitor_database()
    except KeyboardInterrupt:
        logger.info("\n监控已退出")

if __name__ == '__main__':
    main()