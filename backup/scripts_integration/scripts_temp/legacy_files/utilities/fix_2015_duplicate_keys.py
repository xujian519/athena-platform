#!/usr/bin/env python3
"""
解决2015年数据迁移中的重复键问题
分析并处理patents_simple和patents表中的重复申请号
"""

import logging
import sys
import time
from datetime import datetime

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_2015_duplicate_keys.log'),
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

def get_connection():
    """创建数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

def analyze_duplicates():
    """分析重复数据情况"""
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        # 1. 检查patents_simple中2015年的重复申请号
        logger.info('分析patents_simple中的重复申请号...')
        cursor.execute("""
            SELECT application_number, COUNT(*) as cnt
            FROM patents_simple
            WHERE source_year = 2015 AND application_number IS NOT NULL
            GROUP BY application_number
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
            LIMIT 10
        """)
        duplicates_in_simple = cursor.fetchall()

        if duplicates_in_simple:
            logger.warning(f"patents_simple中有 {len(duplicates_in_simple)} 个重复的申请号")
            for app_num, count in duplicates_in_simple[:5]:
                logger.warning(f"  申请号: {app_num}, 重复次数: {count}")

        # 2. 检查patents中2015年的重复申请号
        logger.info("\n分析patents中的重复申请号...")
        cursor.execute("""
            SELECT application_number, COUNT(*) as cnt
            FROM patents
            WHERE source_year = 2015 AND application_number IS NOT NULL
            GROUP BY application_number
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
            LIMIT 10
        """)
        duplicates_in_patents = cursor.fetchall()

        if duplicates_in_patents:
            logger.warning(f"patents中有 {len(duplicates_in_patents)} 个重复的申请号")
            for app_num, count in duplicates_in_patents[:5]:
                logger.warning(f"  申请号: {app_num}, 重复次数: {count}")

        # 3. 检查两个表之间的重复
        logger.info("\n分析两个表之间的重复申请号...")
        cursor.execute("""
            SELECT ps.application_number, COUNT(*) as cnt
            FROM patents_simple ps
            INNER JOIN patents p ON ps.application_number = p.application_number
            WHERE ps.source_year = 2015 AND p.source_year = 2015
            GROUP BY ps.application_number
            ORDER BY cnt DESC
            LIMIT 10
        """)
        duplicates_between_tables = cursor.fetchall()

        if duplicates_between_tables:
            logger.warning(f"两个表之间有 {len(duplicates_between_tables)} 个重复的申请号")
            for app_num, count in duplicates_between_tables[:5]:
                logger.warning(f"  申请号: {app_num}, 重复次数: {count}")

        # 4. 统计未迁移的数据
        cursor.execute("""
            SELECT COUNT(*) FROM patents_simple ps
            WHERE ps.source_year = 2015
            AND ps.application_number NOT IN (
                SELECT application_number FROM patents WHERE source_year = 2015
            )
        """)
        remaining_to_migrate = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM patents_simple WHERE source_year = 2015
        """)
        total_in_simple = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM patents WHERE source_year = 2015
        """)
        total_in_patents = cursor.fetchone()[0]

        logger.info(f"\n2015年数据统计:")
        logger.info(f"  patents_simple表总数: {total_in_simple:,}")
        logger.info(f"  patents表总数: {total_in_patents:,}")
        logger.info(f"  待迁移数据: {remaining_to_migrate:,}")
        logger.info(f"  迁移完成率: {(total_in_patents / total_in_simple * 100) if total_in_simple > 0 else 0:.1f}%")

        cursor.close()
        conn.close()

        return {
            'duplicates_in_simple': duplicates_in_simple,
            'duplicates_in_patents': duplicates_in_patents,
            'duplicates_between_tables': duplicates_between_tables,
            'remaining_to_migrate': remaining_to_migrate,
            'total_in_simple': total_in_simple,
            'total_in_patents': total_in_patents
        }

    except Exception as e:
        logger.error(f"分析失败: {e}")
        conn.close()
        return None

def clean_and_migrate():
    """清理重复数据并完成迁移"""
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # 1. 首先清理patents_simple表中的重复数据，保留ID最小的记录
        logger.info('清理patents_simple表中的重复数据...')
        cursor.execute("""
            DELETE FROM patents_simple
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM patents_simple
                WHERE source_year = 2015 AND application_number IS NOT NULL
                GROUP BY application_number
            ) AND source_year = 2015
        """)
        deleted_simple = cursor.rowcount
        logger.info(f"从patents_simple删除了 {deleted_simple:,} 条重复记录")
        conn.commit()

        # 2. 清理patents表中的重复数据，保留ID最小的记录
        logger.info('清理patents表中的重复数据...')
        cursor.execute("""
            DELETE FROM patents
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM patents
                WHERE source_year = 2015 AND application_number IS NOT NULL
                GROUP BY application_number
            ) AND source_year = 2015
        """)
        deleted_patents = cursor.rowcount
        logger.info(f"从patents删除了 {deleted_patents:,} 条重复记录")
        conn.commit()

        # 3. 查找之前失败的重复键（如CN201110086053.6）
        logger.info('检查特定的重复申请号...')
        cursor.execute("""
            SELECT application_number, COUNT(*)
            FROM patents_simple
            WHERE source_year = 2015 AND application_number = 'CN201110086053.6'
            GROUP BY application_number
        """)
        result = cursor.fetchone()

        if result:
            logger.info(f"发现问题申请号 CN201110086053.6 在patents_simple中有 {result[1]} 条记录")

            cursor.execute("""
                SELECT application_number, COUNT(*)
                FROM patents
                WHERE source_year = 2015 AND application_number = 'CN201110086053.6'
                GROUP BY application_number
            """)
            result = cursor.fetchone()

            if result:
                logger.info(f"发现问题申请号 CN201110086053.6 在patents中有 {result[1]} 条记录")

        # 4. 迁移剩余数据，使用LEFT JOIN避免重复
        logger.info('开始迁移剩余数据...')
        migrated_count = 0
        batch_size = 10000

        while True:
            # 查找未迁移的数据
            cursor.execute("""
                INSERT INTO patents (
                    patent_name, patent_type, application_number, application_date,
                    publication_number, publication_date, authorization_number, authorization_date,
                    applicant, applicant_type, applicant_address, applicant_region, applicant_city, applicant_district,
                    current_assignee, current_assignee_address, assignee_type, credit_code,
                    inventor, ipc_code, ipc_main_class, ipc_classification,
                    abstract, claims_content, claims,
                    citation_count, cited_count, self_citation_count, other_citation_count,
                    cited_by_self_count, cited_by_others_count, family_citation_count, family_cited_count,
                    source_year, source_file, file_hash
                )
                SELECT
                    ps.patent_name, ps.patent_type, ps.application_number, ps.application_date,
                    NULL, NULL, NULL, NULL,
                    ps.applicant, NULL, NULL, NULL, NULL, NULL,
                    NULL, NULL, NULL, NULL,
                    ps.inventor, ps.ipc_code,
                    CASE WHEN ps.ipc_code IS NOT NULL AND LENGTH(ps.ipc_code) >= 4
                         THEN SUBSTRING(ps.ipc_code, 1, 4) ELSE NULL END,
                    ps.ipc_code,
                    ps.abstract, NULL, NULL,
                    0, 0, 0, 0, 0, 0, 0, 0,
                    ps.source_year, '中国专利数据库2015年.csv', NULL
                FROM patents_simple ps
                LEFT JOIN patents p ON ps.application_number = p.application_number
                WHERE ps.source_year = 2015
                AND ps.application_number IS NOT NULL
                AND p.application_number IS NULL
                LIMIT %s
            """, (batch_size,))

            batch_count = cursor.rowcount
            if batch_count == 0:
                break

            conn.commit()
            migrated_count += batch_count
            logger.info(f"批次迁移完成: {batch_count:,} 条, 累计: {migrated_count:,} 条")

            # 短暂休息
            time.sleep(0.1)

        cursor.close()
        conn.close()

        logger.info(f"✅ 2015年数据迁移完成，共迁移 {migrated_count:,} 条记录")
        return True

    except Exception as e:
        logger.error(f"清理迁移失败: {e}")
        conn.rollback()
        conn.close()
        return False

def verify_migration():
    """验证迁移结果"""
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # 统计最终结果
        cursor.execute('SELECT COUNT(*) FROM patents_simple WHERE source_year = 2015')
        simple_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year = 2015')
        patents_count = cursor.fetchone()[0]

        # 检查是否还有未迁移的
        cursor.execute("""
            SELECT COUNT(*) FROM patents_simple ps
            WHERE ps.source_year = 2015
            AND ps.application_number NOT IN (
                SELECT application_number FROM patents WHERE source_year = 2015
            )
        """)
        remaining = cursor.fetchone()[0]

        completion_rate = (patents_count / simple_count * 100) if simple_count > 0 else 0

        logger.info("\n" + '='*60)
        logger.info('2015年数据迁移最终报告')
        logger.info('='*60)
        logger.info(f"patents_simple表: {simple_count:,} 条")
        logger.info(f"patents表: {patents_count:,} 条")
        logger.info(f"剩余未迁移: {remaining:,} 条")
        logger.info(f"完成率: {completion_rate:.2f}%")

        if remaining == 0:
            logger.info('✅ 所有数据已成功迁移！')
        else:
            logger.warning(f"⚠️  还有 {remaining:,} 条数据未迁移")

        cursor.close()
        conn.close()

        return remaining == 0

    except Exception as e:
        logger.error(f"验证失败: {e}")
        conn.close()
        return False

def main():
    """主函数"""
    logger.info('=' * 80)
    logger.info('开始解决2015年重复键问题')
    logger.info('=' * 80)

    # 1. 分析重复情况
    logger.info('第一步: 分析重复数据情况')
    analysis = analyze_duplicates()
    if not analysis:
        logger.error('分析失败，终止执行')
        return False

    # 如果有重复数据，进行清理
    if (analysis['duplicates_in_simple'] or
        analysis['duplicates_in_patents'] or
        analysis['duplicates_between_tables']):
        logger.info("\n发现重复数据，开始清理...")

        # 2. 清理并迁移
        logger.info("\n第二步: 清理重复数据并完成迁移")
        if not clean_and_migrate():
            logger.error('清理迁移失败')
            return False
    else:
        logger.info("\n未发现重复数据，直接进行迁移...")
        # 简单迁移
        if not clean_and_migrate():
            logger.error('迁移失败')
            return False

    # 3. 验证结果
    logger.info("\n第三步: 验证迁移结果")
    success = verify_migration()

    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)