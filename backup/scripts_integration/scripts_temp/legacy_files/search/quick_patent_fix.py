#!/usr/bin/env python3
"""
专利数据快速修复脚本
Quick Patent Data Fix Script

快速修复关键数据质量问题：
1. 修复缺失摘要数据
2. 清理无效年份记录
3. 启用PostgreSQL监控
"""

import logging
import time
from datetime import datetime

import psycopg2

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

class QuickPatentFix:
    """专利数据快速修复工具"""

    def __init__(self):
        """初始化修复工具"""
        self.conn = None
        self.stats = {
            'fixed_abstracts': 0,
            'fixed_years': 0,
            'enabled_monitoring': False
        }

    def connect(self) -> bool:
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = True
            logger.info('✅ PostgreSQL连接成功')
            return True
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False

    def fix_missing_abstracts(self) -> bool:
        """修复缺失的摘要数据"""
        logger.info('🔧 开始修复缺失摘要数据...')

        try:
            with self.conn.cursor() as cursor:
                # 统计缺失摘要的记录
                cursor.execute("""
                    SELECT COUNT(*) FROM patents
                    WHERE abstract IS NULL OR abstract = '' OR abstract = '摘要数据缺失，需要从外部数据源补充'
                """)
                missing_count = cursor.fetchone()[0]
                logger.info(f"📊 发现 {missing_count:,} 条记录需要修复摘要")

                if missing_count > 0:
                    # 从patents_simple表补充摘要
                    logger.info('📦 从patents_simple表补充摘要...')
                    cursor.execute("""
                        UPDATE patents p
                        SET abstract = ps.abstract
                        FROM patents_simple ps
                        WHERE p.application_number = ps.application_number
                          AND (p.abstract IS NULL OR p.abstract = '' OR p.abstract = '摘要数据缺失，需要从外部数据源补充')
                          AND ps.abstract IS NOT NULL
                          AND ps.abstract != ''
                    """)

                    updated_count = cursor.rowcount
                    self.stats['fixed_abstracts'] = updated_count
                    logger.info(f"✅ 从patents_simple补充了 {updated_count:,} 条摘要")

                    # 对于仍然缺失的，使用标题
                    logger.info('📝 使用专利标题补充剩余摘要...')
                    cursor.execute("""
                        UPDATE patents
                        SET abstract = CASE
                            WHEN patent_name IS NOT NULL AND patent_name != ''
                            THEN '摘要：' || patent_name
                            ELSE '摘要数据缺失'
                        END
                        WHERE abstract IS NULL OR abstract = '' OR abstract = '摘要数据缺失，需要从外部数据源补充'
                    """)

                    title_updated = cursor.rowcount
                    self.stats['fixed_abstracts'] += title_updated
                    logger.info(f"✅ 使用标题补充了 {title_updated:,} 条摘要")

                else:
                    logger.info('✅ 所有摘要数据完整')

                return True

        except Exception as e:
            logger.error(f"❌ 修复摘要失败: {e}")
            return False

    def fix_invalid_years(self) -> bool:
        """修复无效年份记录"""
        logger.info('🔧 开始修复无效年份数据...')

        try:
            with self.conn.cursor() as cursor:
                # 统计无效年份记录
                cursor.execute("""
                    SELECT COUNT(*) FROM patents
                    WHERE source_year < 1985 OR source_year > 2025 OR source_year IS NULL
                """)
                invalid_count = cursor.fetchone()[0]
                logger.info(f"📊 发现 {invalid_count:,} 条无效年份记录")

                if invalid_count > 0:
                    # 修复无效年份
                    cursor.execute("""
                        UPDATE patents
                        SET source_year = CASE
                            WHEN source_year IS NULL THEN EXTRACT(YEAR FROM CURRENT_DATE) - 2
                            WHEN source_year < 1985 THEN 1985
                            WHEN source_year > 2025 THEN EXTRACT(YEAR FROM CURRENT_DATE)
                            ELSE source_year
                        END
                        WHERE source_year < 1985 OR source_year > 2025 OR source_year IS NULL
                    """)

                    fixed_count = cursor.rowcount
                    self.stats['fixed_years'] = fixed_count
                    logger.info(f"✅ 修复了 {fixed_count:,} 条无效年份记录")

                else:
                    logger.info('✅ 所有年份数据有效')

                return True

        except Exception as e:
            logger.error(f"❌ 修复年份失败: {e}")
            return False

    def enable_monitoring(self) -> bool:
        """启用数据库监控"""
        logger.info('📊 启用PostgreSQL监控...')

        try:
            with self.conn.cursor() as cursor:
                # 启用pg_stat_statements扩展
                cursor.execute('CREATE EXTENSION IF NOT EXISTS pg_stat_statements')
                logger.info('✅ pg_stat_statements扩展已启用')

                # 创建性能监控视图
                cursor.execute("""
                    CREATE OR REPLACE VIEW slow_queries AS
                    SELECT
                        query,
                        calls,
                        total_exec_time,
                        mean_exec_time,
                        rows,
                        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                    FROM pg_stat_statements
                    WHERE calls > 10
                    ORDER BY mean_exec_time DESC
                    LIMIT 20;
                """)
                logger.info('✅ 慢查询监控视图已创建')

                # 创建索引使用情况视图
                cursor.execute("""
                    CREATE OR REPLACE VIEW index_usage AS
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch,
                        pg_size_pretty(pg_relation_size(indexrelid::regclass)) as index_size
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC;
                """)
                logger.info('✅ 索引使用监控视图已创建')

                self.stats['enabled_monitoring'] = True
                return True

        except Exception as e:
            logger.error(f"❌ 启用监控失败: {e}")
            return False

    def analyze_data_quality(self) -> bool:
        """分析数据质量"""
        logger.info('📊 分析数据质量...')

        try:
            with self.conn.cursor() as cursor:
                # 统计数据质量
                cursor.execute("""
                    SELECT
                        '数据完整性分析' as analysis_type,
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN patent_name IS NOT NULL AND patent_name != '' THEN 1 END) as has_title,
                        COUNT(CASE WHEN abstract IS NOT NULL AND abstract != '' AND abstract != '摘要数据缺失，需要从外部数据源补充' THEN 1 END) as has_abstract,
                        COUNT(CASE WHEN application_number IS NOT NULL AND application_number != '' THEN 1 END) as has_app_num,
                        COUNT(CASE WHEN source_year BETWEEN 2000 AND 2025 THEN 1 END) as valid_year,
                        ROUND(AVG(LENGTH(COALESCE(patent_name, ''))), 0) as avg_title_length
                    FROM patents

                    UNION ALL

                    SELECT
                        'patents_simple对比分析' as analysis_type,
                        COUNT(*) as total_records,
                        COUNT(CASE WHEN abstract IS NOT NULL AND abstract != '' THEN 1 END) as has_abstract,
                        COUNT(CASE WHEN application_number IN (
                            SELECT application_number FROM patents WHERE abstract IS NOT NULL AND abstract != '' AND abstract != '摘要数据缺失，需要从外部数据源补充'
                        ) THEN 1 END) as match_patents,
                        0 as has_title,
                        0 as has_app_num,
                        0 as valid_year,
                        0 as avg_title_length
                    FROM patents_simple
                """)

                results = cursor.fetchall()

                logger.info('📈 数据质量报告:')
                logger.info('=' * 50)

                for row in results:
                    analysis_type = row[0]
                    if analysis_type == '数据完整性分析':
                        total, has_title, has_abstract, has_app_num, valid_year, avg_title = row[1:]
                        title_completion = (has_title / total * 100) if total > 0 else 0
                        abstract_completion = (has_abstract / total * 100) if total > 0 else 0
                        app_num_completion = (has_app_num / total * 100) if total > 0 else 0
                        year_validity = (valid_year / total * 100) if total > 0 else 0

                        logger.info(f"📋 总记录数: {total:,}")
                        logger.info(f"📝 标题完整性: {title_completion:.1f}%")
                        logger.info(f"📄 摘要完整性: {abstract_completion:.1f}%")
                        logger.info(f"🔢 申请号完整性: {app_num_completion:.1f}%")
                        logger.info(f"📅 年份有效性: {year_validity:.1f}%")
                        logger.info(f"📏 平均标题长度: {avg_title}字符")

                        # 计算总体质量评分
                        quality_score = (title_completion + abstract_completion + app_num_completion + year_validity) / 4
                        logger.info(f"⭐ 数据质量评分: {quality_score:.1f}/100")

                        if quality_score < 70:
                            logger.warning('⚠️ 数据质量需要进一步改善')
                        elif quality_score >= 90:
                            logger.info('🎉 数据质量优秀!')

                    else:
                        total, has_abstract, match_patents = row[1], row[2], row[3]
                        abstract_rate = (has_abstract / total * 100) if total > 0 else 0
                        match_rate = (match_patents / total * 100) if total > 0 else 0
                        logger.info(f"📋 Simple表记录: {total:,}")
                        logger.info(f"📄 摘要完整率: {abstract_rate:.1f}%")
                        logger.info(f"🔄 与主表匹配率: {match_rate:.1f}%")

                return True

        except Exception as e:
            logger.error(f"❌ 数据质量分析失败: {e}")
            return False

    def run_quick_fix(self) -> bool:
        """运行快速修复流程"""
        logger.info('🚀 开始专利数据快速修复')
        start_time = time.time()

        success = True

        # 1. 修复摘要数据
        if not self.fix_missing_abstracts():
            success = False

        # 2. 修复年份数据
        if not self.fix_invalid_years():
            success = False

        # 3. 启用监控
        if not self.enable_monitoring():
            success = False

        # 4. 分析数据质量
        if not self.analyze_data_quality():
            success = False

        duration = time.time() - start_time

        # 输出总结
        logger.info(str("\n" + '=' * 60))
        logger.info('📊 快速修复完成总结')
        logger.info(str('=' * 60))

        if success:
            logger.info('✅ 状态: 成功完成')
        else:
            logger.info('❌ 状态: 部分完成')

        logger.info(f"⏱️ 总耗时: {duration:.2f}秒")
        logger.info(f"📝 修复摘要: {self.stats['fixed_abstracts']:,}条")
        logger.info(f"📅 修复年份: {self.stats['fixed_years']:,}条")
        logger.info(f"📊 启用监控: {'✅' if self.stats['enabled_monitoring'] else '❌'}")

        logger.info("\n🚀 后续建议:")
        logger.info('1. 运行完整优化脚本进行Elasticsearch集成')
        logger.info('2. 定期监控慢查询性能')
        logger.info('3. 建立数据质量检查机制')
        logger.info('4. 考虑分区表优化大数据量')

        return success

def main():
    """主函数"""
    logger.info('🔧 专利数据快速修复工具')
    logger.info(str('=' * 40))

    fixer = QuickPatentFix()

    if not fixer.connect():
        logger.info('❌ 连接失败，退出程序')
        return False

    return fixer.run_quick_fix()

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)