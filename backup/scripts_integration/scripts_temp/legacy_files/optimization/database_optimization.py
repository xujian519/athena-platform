#!/usr/bin/env python3
"""
Athena工作平台数据库性能优化脚本

功能:
- 自动创建和优化数据库索引
- 分析慢查询
- 优化表结构
- 生成性能报告

最后更新: 2025-12-13
"""

import os
import sys
import json
import time
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncpg
import yaml
import pandas as pd

class DatabaseOptimizer:
    """数据库优化器"""

    def __init__(self):
        # 加载配置
        config_file = project_root / 'config' / 'performance.yaml'
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.db_config = self.config['database']
        self.performance_config = self.config['monitoring']['benchmarks']

        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def create_connection(self) -> asyncpg.Connection:
        """创建数据库连接"""
        return await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB', 'athena_patent'),
            user=os.getenv('POSTGRES_USER', 'athena_admin'),
            password=os.getenv('POSTGRES_PASSWORD', 'Athena@2024#PatentSecure')
        )

    async def analyze_slow_queries(self, conn: asyncpg.Connection) -> List[Dict]:
        """分析慢查询"""
        self.logger.info("分析慢查询...")

        # 启用pg_stat_statements扩展
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")

        # 获取慢查询
        slow_queries_sql = """
        SELECT
            query,
            calls,
            total_exec_time,
            mean_exec_time,
            rows,
            100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
        FROM pg_stat_statements
        WHERE mean_exec_time > 100  -- 执行时间大于100ms
        ORDER BY mean_exec_time DESC
        LIMIT 20
        """

        return await conn.fetch(slow_queries_sql)

    async def create_optimal_indexes(self, conn: asyncpg.Connection):
        """创建优化的索引"""
        self.logger.info("创建优化索引...")

        index_definitions = self.db_config['postgresql']['indexes']

        for index_def in index_definitions['patents']:
            # 检查索引是否已存在
            index_exists_sql = """
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'patents' AND indexname = $1
            """
            exists = await conn.fetchval(index_exists_sql, index_def['name'])

            if not exists:
                # 创建索引
                if index_def['type'] == 'gin':
                    create_sql = f"""
                    CREATE INDEX CONCURRENTLY {index_def['name']}
                    ON patents USING {index_def['type']} ({index_def['with']}(title))
                    """
                else:
                    columns = ', '.join(index_def['columns'])
                    create_sql = f"""
                    CREATE INDEX CONCURRENTLY {index_def['name']}
                    ON patents USING {index_def['type']} ({columns})
                    """

                self.logger.info(f"创建索引: {index_def['name']}")
                try:
                    await conn.execute(create_sql)
                except Exception as e:
                    self.logger.error(f"创建索引失败 {index_def['name']}: {e}")

    async def update_table_statistics(self, conn: asyncpg.Connection):
        """更新表统计信息"""
        self.logger.info("更新表统计信息...")

        tables = ['patents', 'applications', 'applicants', 'agents']

        for table in tables:
            try:
                await conn.execute(f"ANALYZE {table}")
                self.logger.info(f"更新统计信息: {table}")
            except Exception as e:
                self.logger.error(f"更新统计信息失败 {table}: {e}")

    async def optimize_table_structure(self, conn: asyncpg.Connection):
        """优化表结构"""
        self.logger.info("优化表结构...")

        # 清理已删除的行
        vacuum_sql = """
        SELECT schemaname, tablename, n_dead_tup, n_live_tup,
               ROUND(n_dead_tup::numeric / (n_live_tup + n_dead_tup) * 100, 2) AS dead_tup_ratio
        FROM pg_stat_user_tables
        WHERE n_dead_tup > 1000
        ORDER BY dead_tup_ratio DESC
        """

        tables_to_vacuum = await conn.fetch(vacuum_sql)

        for table_info in tables_to_vacuum:
            if table_info['dead_tup_ratio'] > 10:  # 死元组比例超过10%
                self.logger.info(f"执行VACUUM: {table_info['tablename']}")
                try:
                    await conn.execute(f"VACUUM {table_info['tablename']}")
                except Exception as e:
                    self.logger.error(f"VACUUM失败 {table_info['tablename']}: {e}")

    async def analyze_index_usage(self, conn: asyncpg.Connection) -> List[Dict]:
        """分析索引使用情况"""
        self.logger.info("分析索引使用情况...")

        index_usage_sql = """
        SELECT
            schemaname,
            tablename,
            indexname,
            idx_scan,
            idx_tup_read,
            idx_tup_fetch,
            CASE
                WHEN idx_scan = 0 THEN 'UNUSED'
                WHEN idx_scan < 10 THEN 'LOW_USAGE'
                WHEN idx_scan < 100 THEN 'MEDIUM_USAGE'
                ELSE 'HIGH_USAGE'
            END as usage_level
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        ORDER BY idx_scan ASC
        """

        return await conn.fetch(index_usage_sql)

    async def create_partition_tables(self, conn: asyncpg.Connection):
        """创建分区表"""
        self.logger.info("创建分区表...")

        partitioning = self.db_config['postgresql']['partitioning']

        # 检查是否已有分区表
        check_partition_sql = """
        SELECT EXISTS (
            SELECT 1 FROM pg_tables
            WHERE tablename = 'patents'
            AND tableowner NOT IN ('postgres', 'athena_admin')
        )
        """

        has_partition = await conn.fetchval(check_partition_sql)

        if not has_partition:
            # 创建分区表（示例）
            create_partition_sql = f"""
            CREATE TABLE IF NOT EXISTS patents_partitioned (
                LIKE patents INCLUDING ALL
            ) PARTITION BY RANGE (application_date);
            """
            await conn.execute(create_partition_sql)

            # 创建分区
            for partition in partitioning['patents_table']['partitions']:
                create_part_sql = f"""
                CREATE TABLE IF NOT EXISTS {partition}
                PARTITION OF patents_partitioned
                FOR VALUES FROM ('2015-01-01') TO ('2025-01-01');
                """
                await conn.execute(create_part_sql)

    async def generate_performance_report(self,
                                         slow_queries: List[Dict],
                                         index_usage: List[Dict]) -> Dict:
        """生成性能报告"""
        self.logger.info("生成性能报告...")

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_slow_queries': len(slow_queries),
                'unused_indexes': len([i for i in index_usage if i['usage_level'] == 'UNUSED']),
                'low_usage_indexes': len([i for i in index_usage if i['usage_level'] == 'LOW_USAGE'])
            },
            'slow_queries': [dict(q) for q in slow_queries],
            'index_analysis': [dict(i) for i in index_usage],
            'recommendations': []
        }

        # 生成优化建议
        if report['summary']['total_slow_queries'] > 0:
            report['recommendations'].append(
                f"发现{report['summary']['total_slow_queries']}个慢查询，建议优化SQL语句或添加索引"
            )

        if report['summary']['unused_indexes'] > 0:
            report['recommendations'].append(
                f"发现{report['summary']['unused_indexes']}个未使用的索引，建议删除以提高写入性能"
            )

        # 保存报告
        report_file = project_root / 'reports' / 'database_performance_report.json'
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self.logger.info(f"性能报告已保存: {report_file}")

        return report

    async def run_optimization(self):
        """运行完整的优化流程"""
        self.logger.info("开始数据库性能优化...")

        conn = None
        try:
            conn = await self.create_connection()

            # 1. 分析慢查询
            slow_queries = await self.analyze_slow_queries(conn)

            # 2. 创建优化索引
            await self.create_optimal_indexes(conn)

            # 3. 更新统计信息
            await self.update_table_statistics(conn)

            # 4. 优化表结构
            await self.optimize_table_structure(conn)

            # 5. 分析索引使用
            index_usage = await self.analyze_index_usage(conn)

            # 6. 创建分区表
            await self.create_partition_tables(conn)

            # 7. 生成性能报告
            report = await self.generate_performance_report(slow_queries, index_usage)

            self.logger.info("数据库性能优化完成!")
            return report

        except Exception as e:
            self.logger.error(f"优化过程出错: {e}")
            raise
        finally:
            if conn:
                await conn.close()

    async def monitor_query_performance(self, duration: int = 60):
        """监控查询性能"""
        self.logger.info(f"开始监控查询性能，持续时间: {duration}秒...")

        conn = None
        try:
            conn = await self.create_connection()

            # 启用查询日志
            await conn.execute("ALTER SYSTEM SET log_min_duration_statement = 100")
            await conn.execute("SELECT pg_reload_conf()")

            # 监控期间收集指标
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'duration': duration,
                'queries': []
            }

            start_time = time.time()

            while time.time() - start_time < duration:
                # 获取当前活动查询
                active_queries_sql = """
                SELECT
                    pid,
                    now() - pg_stat_activity.query_start AS duration,
                    query,
                    state,
                    wait_event
                FROM pg_stat_activity
                WHERE state != 'idle'
                AND query != ''
                ORDER BY duration DESC
                """

                queries = await conn.fetch(active_queries_sql)

                for q in queries:
                    if q['duration'].total_seconds() > 1:  # 超过1秒的查询
                        metrics['queries'].append({
                            'timestamp': datetime.now().isoformat(),
                            'pid': q['pid'],
                            'duration': str(q['duration']),
                            'query': q['query'][:200],  # 限制查询长度
                            'state': q['state'],
                            'wait_event': q['wait_event']
                        })

                await asyncio.sleep(10)  # 每10秒检查一次

            # 保存监控报告
            report_file = project_root / 'reports' / 'query_monitoring_report.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, ensure_ascii=False, indent=2)

            self.logger.info(f"查询性能监控完成，报告已保存: {report_file}")

        except Exception as e:
            self.logger.error(f"监控过程出错: {e}")
            raise
        finally:
            if conn:
                await conn.close()

    async def generate_optimization_sql(self) -> str:
        """生成优化SQL脚本"""
        self.logger.info("生成优化SQL脚本...")

        sql_script = []

        # 添加索引
        for index_def in self.db_config['postgresql']['indexes']['patents']:
            sql_script.append(f"-- 创建索引: {index_def['name']}")

            if index_def['type'] == 'gin':
                sql_script.append(
                    f"CREATE INDEX CONCURRENTLY {index_def['name']} "
                    f"ON patents USING {index_def['type']} ({index_def['with']}(title));"
                )
            else:
                columns = ', '.join(index_def['columns'])
                sql_script.append(
                    f"CREATE INDEX CONCURRENTLY {index_def['name']} "
                    f"ON patents USING {index_def['type']} ({columns});"
                )
            sql_script.append("")

        # 更新统计信息
        sql_script.append("-- 更新表统计信息")
        sql_script.append("ANALYZE patents;")
        sql_script.append("ANALYZE applications;")
        sql_script.append("ANALYZE applicants;")
        sql_script.append("")

        # 性能配置
        sql_script.append("-- 性能优化配置")
        sql_script.append("ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';")
        sql_script.append("ALTER SYSTEM SET log_min_duration_statement = 1000;")
        sql_script.append("ALTER SYSTEM SET log_checkpoints = on;")
        sql_script.append("ALTER SYSTEM SET log_connections = on;")
        sql_script.append("ALTER SYSTEM SET log_disconnections = on;")
        sql_script.append("ALTER SYSTEM SET log_lock_waits = on;")
        sql_script.append("")

        # 重新加载配置
        sql_script.append("-- 重新加载配置")
        sql_script.append("SELECT pg_reload_conf();")

        script_content = '\n'.join(sql_script)

        # 保存脚本
        script_file = project_root / 'scripts' / 'optimization' / 'optimize_database.sql'
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)

        self.logger.info(f"优化SQL脚本已生成: {script_file}")

        return script_content

async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Athena数据库优化工具')
    parser.add_argument('--action', choices=['optimize', 'monitor', 'generate-sql'],
                       default='optimize', help='执行的操作')
    parser.add_argument('--duration', type=int, default=60,
                       help='监控持续时间（秒）')

    args = parser.parse_args()

    optimizer = DatabaseOptimizer()

    if args.action == 'optimize':
        await optimizer.run_optimization()
    elif args.action == 'monitor':
        await optimizer.monitor_query_performance(args.duration)
    elif args.action == 'generate-sql':
        optimizer.generate_optimization_sql()

if __name__ == '__main__':
    asyncio.run(main())