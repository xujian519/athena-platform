#!/usr/bin/env python3
"""
PostgreSQL中文全文搜索配置脚本
配置chinese全文搜索配置以支持中文专利检索
"""

import logging
import sys

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

def setup_chinese_fulltext_search():
    """设置中文全文搜索配置"""
    conn = None
    try:
        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True  # 需要自动提交来创建配置
        cursor = conn.cursor()

        logger.info('开始配置中文全文搜索...')

        # 1. 检查是否已有chinese配置
        cursor.execute("""
            SELECT cfgname FROM pg_ts_config WHERE cfgname = 'chinese'
        """)
        if cursor.fetchone():
            logger.info('中文全文搜索配置已存在，跳过创建')
        else:
            logger.info('创建中文全文搜索配置...')
            # 创建中文全文搜索配置
            cursor.execute("""
                CREATE TEXT SEARCH CONFIGURATION chinese (COPY = simple);
            """)
            logger.info('✅ 中文全文搜索配置创建成功')

        # 2. 创建中文分词字典（如果需要）
        cursor.execute("""
            SELECT dictname FROM pg_ts_dict WHERE dictname = 'chinese_dict'
        """)
        if not cursor.fetchone():
            logger.info('创建中文分词字典...')
            cursor.execute("""
                CREATE TEXT SEARCH DICTIONARY chinese_dict (
                    TEMPLATE = simple,
                    STOPWORDS = chinese
                );
            """)
            logger.info('✅ 中文分词字典创建成功')

        # 3. 创建专利专用的全文搜索配置
        cursor.execute("""
            SELECT cfgname FROM pg_ts_config WHERE cfgname = 'patent_chinese'
        """)
        if not cursor.fetchone():
            logger.info('创建专利专用中文全文搜索配置...')
            cursor.execute("""
                CREATE TEXT SEARCH CONFIGURATION patent_chinese (
                    COPY = chinese
                );

                ALTER TEXT SEARCH CONFIGURATION patent_chinese
                ALTER MAPPING FOR asciiword, asciihword, hword_asciipart, word, hword, hword_part
                WITH chinese_dict;
            """)
            logger.info('✅ 专利专用中文全文搜索配置创建成功')

        # 4. 为专利表创建全文搜索索引（如果不存在）
        logger.info('检查专利表的全文搜索索引...')
        cursor.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'patents' AND indexname LIKE '%fulltext%'
        """)
        existing_indexes = cursor.fetchall()

        if not existing_indexes:
            logger.info('创建专利全文搜索索引...')

            # 创建专利名称的全文搜索索引
            try:
                cursor.execute("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_patent_name_fulltext
                    ON patents USING gin(to_tsvector('patent_chinese', patent_name));
                """)
                logger.info('✅ 专利名称全文搜索索引创建成功')
            except Exception as e:
                logger.warning(f"专利名称全文搜索索引创建失败: {e}")

            # 创建摘要的全文搜索索引
            try:
                cursor.execute("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_abstract_fulltext
                    ON patents USING gin(to_tsvector('patent_chinese', abstract));
                """)
                logger.info('✅ 摘要全文搜索索引创建成功')
            except Exception as e:
                logger.warning(f"摘要全文搜索索引创建失败: {e}")

            # 创建组合全文搜索索引
            try:
                cursor.execute("""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patents_combined_fulltext
                    ON patents USING gin(to_tsvector('patent_chinese',
                        COALESCE(patent_name, '') || ' ' || COALESCE(abstract, '')
                    ));
                """)
                logger.info('✅ 组合全文搜索索引创建成功')
            except Exception as e:
                logger.warning(f"组合全文搜索索引创建失败: {e}")

        # 5. 测试全文搜索功能
        logger.info('测试中文全文搜索功能...')
        test_queries = ['电子', '通信', '医疗', '人工智能']

        for query in test_queries:
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM patents
                    WHERE to_tsvector('patent_chinese',
                        COALESCE(patent_name, '') || ' ' || COALESCE(abstract, '')
                    ) @@ to_tsquery('patent_chinese', %s)
                """, (query,))
                count = cursor.fetchone()[0]
                logger.info(f"   查询'{query}': 找到 {count:,} 条结果")
            except Exception as e:
                logger.error(f"   查询'{query}'失败: {e}")

        # 6. 创建全文搜索函数
        logger.info('创建便捷的全文搜索函数...')
        cursor.execute("""
            CREATE OR REPLACE FUNCTION search_patents_chinese(search_term TEXT, limit_count INTEGER DEFAULT 20)
            RETURNS TABLE(
                application_number TEXT,
                patent_name TEXT,
                patent_type TEXT,
                applicant TEXT,
                abstract TEXT,
                relevance_score REAL
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    p.application_number,
                    p.patent_name,
                    p.patent_type,
                    p.applicant,
                    p.abstract,
                    ts_rank_cd(
                        to_tsvector('patent_chinese', COALESCE(p.patent_name, '') || ' ' || COALESCE(p.abstract, '')),
                        to_tsquery('patent_chinese', search_term)
                    ) as relevance_score
                FROM patents p
                WHERE to_tsvector('patent_chinese', COALESCE(p.patent_name, '') || ' ' || COALESCE(p.abstract, ''))
                      @@ to_tsquery('patent_chinese', search_term)
                ORDER BY relevance_score DESC, p.source_year DESC
                LIMIT limit_count;
            END;
            $$ LANGUAGE plpgsql;
        """)
        logger.info('✅ 全文搜索函数创建成功')

        cursor.close()
        logger.info('🎉 中文全文搜索配置完成！')
        return True

    except Exception as e:
        logger.error(f"配置中文全文搜索失败: {e}")
        return False

    finally:
        if conn:
            conn.close()

def test_chinese_search():
    """测试中文搜索功能"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        logger.info('🧪 测试中文全文搜索功能...')

        # 测试基础搜索
        test_terms = ['电子', '通信', '医疗', '人工智能', '新能源']

        for term in test_terms:
            logger.info(f"\n🔍 搜索: {term}")
            logger.info(str('-' * 40))

            # 使用全文搜索函数
            cursor.execute("""
                SELECT * FROM search_patents_chinese(%s, 3)
            """, (term,))

            results = cursor.fetchall()
            logger.info(f"找到 {len(results)} 条结果:")

            for i, row in enumerate(results, 1):
                app_num, patent_name, patent_type, applicant, abstract, score = row
                logger.info(f"{i}. {patent_name[:50]}... (得分: {score:.2f})")
                logger.info(f"   申请人: {applicant[:30]}...")
                print()

        cursor.close()
        return True

    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False

    finally:
        if conn:
            conn.close()

def main():
    """主函数"""
    logger.info('🚀 开始配置PostgreSQL中文全文搜索')
    logger.info(str('=' * 60))

    # 配置中文全文搜索
    success = setup_chinese_fulltext_search()

    if success:
        logger.info("\n✅ 中文全文搜索配置成功！")

        # 测试搜索功能
        test_chinese_search()

        logger.info("\n📋 配置总结:")
        logger.info('✅ 创建了 chinese 全文搜索配置')
        logger.info('✅ 创建了 patent_chinese 专利专用配置')
        logger.info('✅ 创建了全文搜索索引')
        logger.info('✅ 创建了便捷的搜索函数')
        logger.info("\n💡 使用方法:")
        logger.info("   SELECT * FROM search_patents_chinese('搜索词', 20);")

    else:
        logger.info("\n❌ 中文全文搜索配置失败")
        sys.exit(1)

if __name__ == '__main__':
    main()