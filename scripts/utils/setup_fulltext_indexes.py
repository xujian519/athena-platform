#!/usr/bin/env python3
"""
为patents表建立完整的全文检索索引
"""
import psycopg2

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 15432,
    'database': 'athena',
    'user': 'athena',
    'password': 'athena_password_change_me'
}

def setup_fulltext_indexes():
    """建立完整的全文检索索引"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        print("📊 正在建立完整的全文检索索引...\n")

        # 1. 为claims字段创建单独的GIN索引
        print("1️⃣ 为claims字段创建索引...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patents_claims_gin
            ON patents USING GIN(to_tsvector('simple', claims));
        """)
        print("   ✅ claims索引创建成功")

        # 2. 为description字段创建单独的GIN索引
        print("\n2️⃣ 为description字段创建索引...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patents_description_gin
            ON patents USING GIN(to_tsvector('simple', description));
        """)
        print("   ✅ description索引创建成功")

        # 3. 创建组合全文索引（包含所有文本字段）
        print("\n3️⃣ 创建组合全文索引...")
        cursor.execute("""
            DROP INDEX IF EXISTS idx_patents_all_fields_gin;
        """)
        cursor.execute("""
            CREATE INDEX idx_patents_all_fields_gin
            ON patents USING GIN(
                to_tsvector('simple',
                    coalesce(title, '') || ' ' ||
                    coalesce(abstract, '') || ' ' ||
                    coalesce(claims, '') || ' ' ||
                    coalesce(description, '') || ' ' ||
                    coalesce(applicant, '') || ' ' ||
                    coalesce(inventor, '')
                )
            );
        """)
        print("   ✅ 组合全文索引创建成功")

        # 4. 验证索引
        print("\n📋 验证索引创建结果:")
        cursor.execute("""
            SELECT
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid::regclass)) as size
            FROM pg_indexes
            WHERE tablename = 'patents'
            ORDER BY indexname;
        """)

        indexes = cursor.fetchall()
        print(f"\n共创建 {len(indexes)} 个索引:")
        for idx_name, size in indexes:
            if 'gin' in idx_name.lower():
                print(f"  📚 {idx_name}: {size}")

        conn.commit()
        print("\n✅ 全文检索索引设置完成！")

    except Exception as e:
        print(f"\n❌ 设置失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def test_fulltext_search():
    """测试全文检索功能"""
    import psycopg2.extras

    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("🔍 测试全文检索功能")
    print("="*60)

    test_queries = [
        ("权利要求", "检索权利要求字段"),
        ("深度学习", "检索关键词"),
        ("卷积神经网络", "检索技术术语"),
        ("自动驾驶", "检索应用领域"),
    ]

    for query, description in test_queries:
        print(f"\n📝 {description}: '{query}'")

        # 使用全文索引检索
        cursor.execute("""
            SELECT
                patent_id,
                title,
                ts_headline('simple', title, plainto_tsquery('simple', %s)) as title_highlight,
                ts_headline('simple', abstract, plainto_tsquery('simple', %s)) as abstract_highlight,
                ts_headline('simple', claims, plainto_tsquery('simple', %s)) as claims_highlight
            FROM patents
            WHERE
                to_tsvector('simple', title || ' ' || abstract || ' ' || claims) @@ plainto_tsquery('simple', %s)
            LIMIT 3;
        """, (query, query, query, query))

        results = cursor.fetchall()
        print(f"   找到 {len(results)} 条结果")

        for i, row in enumerate(results[:2], 1):
            print(f"\n   {i}. [{row['patent_id']}] {row['title']}")
            if row['title_highlight'] and row['title_highlight'] != row['title']:
                print(f"      标题匹配: {row['title_highlight'][:80]}...")
            if row['abstract_highlight']:
                print(f"      摘要匹配: {row['abstract_highlight'][:80]}...")
            if row['claims_highlight']:
                claims_preview = row['claims_highlight'].replace('\n', ' ')[:100]
                print(f"      权利要求匹配: {claims_preview}...")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    setup_fulltext_indexes()
    test_fulltext_search()
