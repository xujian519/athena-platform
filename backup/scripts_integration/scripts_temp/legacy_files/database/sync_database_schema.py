#!/usr/bin/env python3
"""
同步数据库表结构
确保表结构与enhanced_patent_processor兼容
"""

import logging
import sqlite3

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def sync_database_schema(db_path='data/patents/processed/china_patents_enhanced.db'):
    """同步数据库表结构"""

    logger.info(f"同步数据库表结构: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取现有表结构
    cursor.execute('PRAGMA table_info(patents)')
    existing_columns = {row[1]: row[2] for row in cursor.fetchall()}

    logger.info(f"现有字段: {list(existing_columns.keys())}")

    # 定义需要的字段
    required_columns = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'patent_name': 'TEXT',
        'patent_type': 'TEXT',
        'applicant': 'TEXT',
        'applicant_type': 'TEXT',
        'applicant_address': 'TEXT',
        'applicant_region': 'TEXT',
        'applicant_city': 'TEXT',
        'applicant_district': 'TEXT',
        'application_number': 'TEXT',
        'application_date': 'TEXT',
        'application_year': 'INTEGER',
        'publication_number': 'TEXT',
        'publication_date': 'TEXT',
        'publication_year': 'INTEGER',
        'authorization_number': 'TEXT',
        'authorization_date': 'TEXT',
        'authorization_year': 'INTEGER',
        'ipc_code': 'TEXT',
        'ipc_main_class': 'TEXT',
        'ipc_classification': 'TEXT',
        'inventor': 'TEXT',
        'abstract': 'TEXT',
        'claims_content': 'TEXT',
        'claims': 'TEXT',
        'current_assignee': 'TEXT',
        'current_assignee_address': 'TEXT',
        'assignee_type': 'TEXT',
        'credit_code': 'TEXT',
        'citation_count': 'INTEGER',
        'cited_count': 'INTEGER',
        'self_citation_count': 'INTEGER',
        'other_citation_count': 'INTEGER',
        'cited_by_self_count': 'INTEGER',
        'cited_by_others_count': 'INTEGER',
        'family_citation_count': 'INTEGER',
        'family_cited_count': 'INTEGER',
        'source_year': 'INTEGER',
        'source_file': 'TEXT',
        'file_hash': 'TEXT',
        'indexed_at': 'TIMESTAMP',
        'created_at': 'TIMESTAMP',
        'updated_at': 'TIMESTAMP',
        'year': 'TEXT'
    }

    # 添加缺失的字段
    added_columns = []
    for col_name, col_type in required_columns.items():
        if col_name not in existing_columns:
            try:
                sql = f"ALTER TABLE patents ADD COLUMN {col_name} {col_type}"
                cursor.execute(sql)
                added_columns.append(col_name)
                logger.info(f"✅ 添加字段: {col_name}")
            except Exception as e:
                logger.error(f"❌ 添加字段失败 {col_name}: {str(e)}")

    # 更新year字段（从文件名提取）
    logger.info("\n更新year字段...")
    cursor.execute("""
        UPDATE patents
        SET year = CAST(substr(source_file, 8, 4) AS INTEGER)
        WHERE year IS NULL OR year = ''
    """)

    # 如果没有source_year，从year更新
    cursor.execute("""
        UPDATE patents
        SET source_year = CAST(year AS INTEGER)
        WHERE source_year IS NULL
        AND year IS NOT NULL
        AND year != ''
        AND length(year) = 4
    """)

    # 提交更改
    conn.commit()

    # 统计信息
    cursor.execute('SELECT COUNT(*) FROM patents')
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM patents WHERE year IS NOT NULL AND year != ''")
    has_year = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM patents WHERE source_year IS NOT NULL')
    has_source_year = cursor.fetchone()[0]

    logger.info(f"\n数据库统计:")
    logger.info(f"  总记录数: {total:,}")
    logger.info(f"  有year字段: {has_year:,}")
    logger.info(f"  有source_year字段: {has_source_year:,}")

    conn.close()

    logger.info("\n✅ 数据库表结构同步完成!")

    return len(added_columns) > 0

def create_indexes(db_path='data/patents/processed/china_patents_enhanced.db'):
    """创建必要的索引"""

    logger.info("\n创建索引...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    indexes = [
        ('idx_year', 'CREATE INDEX IF NOT EXISTS idx_year ON patents(year)'),
        ('idx_source_year', 'CREATE INDEX IF NOT EXISTS idx_source_year ON patents(source_year)'),
        ('idx_application_number', 'CREATE INDEX IF NOT EXISTS idx_application_number ON patents(application_number)'),
        ('idx_applicant', 'CREATE INDEX IF NOT EXISTS idx_applicant ON patents(applicant)'),
        ('idx_patent_name', 'CREATE INDEX IF NOT EXISTS idx_patent_name ON patents(patent_name)'),
        ('idx_ipc_classification', 'CREATE INDEX IF NOT EXISTS idx_ipc_classification ON patents(ipc_classification)'),
        ('idx_publication_number', 'CREATE INDEX IF NOT EXISTS idx_publication_number ON patents(publication_number)'),
        ('idx_authorization_number', 'CREATE INDEX IF NOT EXISTS idx_authorization_number ON patents(authorization_number)'),
        ('idx_application_date', 'CREATE INDEX IF NOT EXISTS idx_application_date ON patents(application_date)'),
        ('idx_year_applicant', 'CREATE INDEX IF NOT EXISTS idx_year_applicant ON patents(year, applicant)'),
    ]

    for idx_name, sql in indexes:
        try:
            cursor.execute(sql)
            logger.info(f"✅ 创建索引: {idx_name}")
        except Exception as e:
            logger.warning(f"⚠️  索引创建警告 {idx_name}: {str(e)}")

    conn.commit()
    conn.close()
    logger.info("\n✅ 索引创建完成!")

def main():
    db_path = 'data/patents/processed/china_patents_enhanced.db'

    # 检查数据库是否存在
    import os
    if not os.path.exists(db_path):
        logger.error(f"❌ 数据库不存在: {db_path}")
        return

    # 同步表结构
    schema_updated = sync_database_schema(db_path)

    # 创建索引
    create_indexes(db_path)

    # 优化数据库
    logger.info("\n优化数据库...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('ANALYZE')
    logger.info('✅ 分析完成')

    conn.close()

if __name__ == '__main__':
    main()