#!/usr/bin/env python3
"""
修复事务问题并创建复合索引
Fix transaction issues and create composite indexes
"""

import logging
import time

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

def create_composite_indexes():
    """创建复合索引"""
    logger.info('🚀 开始创建复合索引...')

    try:
        # 连接数据库（设置自动提交）
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()

        logger.info('✅ 数据库连接成功，自动提交模式已启用')

        # 复合索引定义
        indexes = [
            {
                'name': 'idx_patents_type_year_date',
                'sql': '''
                    CREATE INDEX CONCURRENTLY idx_patents_type_year_date
                    ON patents (patent_type, source_year, application_date DESC NULLS LAST)
                    WHERE application_date IS NOT NULL
                ''',
                'description': '专利类型+年份+申请日期'
            },
            {
                'name': 'idx_patents_applicant_year_optimized',
                'sql': '''
                    CREATE INDEX CONCURRENTLY idx_patents_applicant_year_optimized
                    ON patents (applicant, source_year DESC)
                    WHERE applicant IS NOT NULL AND applicant != '' AND length(applicant) > 2
                ''',
                'description': '申请人+年份'
            },
            {
                'name': 'idx_patents_type_ipc_class',
                'sql': '''
                    CREATE INDEX CONCURRENTLY idx_patents_type_ipc_class
                    ON patents (patent_type, ipc_main_class, source_year DESC)
                    WHERE ipc_main_class IS NOT NULL AND ipc_main_class != ''
                ''',
                'description': '专利类型+IPC主分类'
            },
            {
                'name': 'idx_patents_recent_hot',
                'sql': '''
                    CREATE INDEX CONCURRENTLY idx_patents_recent_hot
                    ON patents (application_date DESC, patent_type, applicant)
                    WHERE application_date >= '2020-01-01' AND patent_type IS NOT NULL
                ''',
                'description': '近期专利热点索引'
            }
        ]

        # 创建每个索引
        for i, index_info in enumerate(indexes, 1):
            logger.info(f"🔧 创建复合索引 ({i}/4): {index_info['description']}")

            start_time = time.time()

            try:
                cursor.execute(index_info['sql'])
                elapsed = time.time() - start_time
                logger.info(f"✅ {index_info['name']} 创建完成，耗时 {elapsed:.2f}s")

            except Exception as e:
                if 'already exists' in str(e):
                    logger.info(f"⚠️ {index_info['name']} 已存在，跳过创建")
                else:
                    logger.error(f"❌ {index_info['name']} 创建失败: {e}")

        cursor.close()
        conn.close()

        logger.info('🎉 所有复合索引创建任务完成！')
        return True

    except Exception as e:
        logger.error(f"❌ 创建索引失败: {e}")
        return False

def check_existing_indexes():
    """检查现有索引"""
    logger.info('🔍 检查现有索引...')

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 检查目标索引是否存在
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = 'patents'
            AND indexname LIKE 'idx_patents_%'
            ORDER BY indexname
        """)

        indexes = cursor.fetchall()

        if indexes:
            logger.info(f"📋 找到 {len(indexes)} 个相关索引:")
            for idx in indexes:
                logger.info(f"   - {idx[0]}")
        else:
            logger.info('📋 未找到相关索引')

        cursor.close()
        conn.close()

        return len(indexes)

    except Exception as e:
        logger.error(f"❌ 检查索引失败: {e}")
        return 0

def main():
    """主函数"""
    logger.info('🔧 专利数据库复合索引创建工具')
    logger.info(str('=' * 50))

    # 检查现有索引
    existing_count = check_existing_indexes()

    if existing_count >= 4:
        logger.info("\n✅ 所有目标索引已存在！")
        return True

    # 创建缺失的索引
    success = create_composite_indexes()

    if success:
        logger.info("\n🎉 索引创建任务完成！")
        logger.info("\n下一步建议:")
        logger.info('1. 运行 ANALYZE 更新统计信息: ANALYZE patents;')
        logger.info('2. 测试查询性能')
        logger.info('3. 监控索引使用情况')
    else:
        logger.info("\n❌ 索引创建任务失败！")
        logger.info('请检查错误信息并重试')

    return success

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)