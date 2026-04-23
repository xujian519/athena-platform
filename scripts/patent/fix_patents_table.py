#!/usr/bin/env python3
"""
修复patents表结构，使其与检索器兼容
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

def fix_patents_table():
    """修复patents表结构"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # 添加description字段（如果不存在）
        cursor.execute("""
            ALTER TABLE patents
            ADD COLUMN IF NOT EXISTS description TEXT;
        """)
        print("✅ 添加description字段")

        # 将claims内容复制到description（作为临时解决方案）
        cursor.execute("""
            UPDATE patents
            SET description = claims
            WHERE description IS NULL;
        """)
        print(f"✅ 更新了{cursor.rowcount}条记录的description字段")

        # 创建中文全文搜索索引（使用simple配置作为替代）
        cursor.execute("""
            DROP INDEX IF EXISTS idx_patents_fulltext_gin;
        """)

        cursor.execute("""
            CREATE INDEX idx_patents_fulltext_gin
            ON patents USING GIN(
                to_tsvector('simple',
                    coalesce(title, '') || ' ' ||
                    coalesce(abstract, '') || ' ' ||
                    coalesce(claims, '') || ' ' ||
                    coalesce(description, '')
                )
            );
        """)
        print("✅ 创建全文搜索索引")

        conn.commit()
        print("\n✅ 表结构修复完成！")

        # 验证
        cursor.execute("SELECT COUNT(*) FROM patents;")
        count = cursor.fetchone()[0]
        print(f"📊 当前专利记录数: {count}")

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_patents_table()
