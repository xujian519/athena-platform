#!/usr/bin/env python3
"""测试PostgreSQL全文搜索查询"""
import psycopg2
from psycopg2.extras import RealDictCursor

# 连接数据库
conn = psycopg2.connect(
    host='localhost',
    port=15432,
    database='athena',
    user='athena',
    password='athena_password_change_me'
)

# 测试全文搜索查询
query = "人工智能"
sql = """
SELECT
    p.patent_id,
    p.title,
    p.abstract,
    ts_rank_cd(
        setweight(to_tsvector('simple', p.title), 'A') ||
        setweight(to_tsvector('simple', p.abstract), 'B') ||
        setweight(to_tsvector('simple', p.claims), 'C') ||
        setweight(to_tsvector('simple', p.description), 'D'),
        plainto_tsquery('simple', %s)
    ) as title_rank
FROM patents p
WHERE
    to_tsvector('simple', p.title || ' ' || p.abstract || ' ' || p.claims || ' ' || p.description) @@ plainto_tsquery('simple', %s)
ORDER BY title_rank DESC
LIMIT %s;
"""

cursor = conn.cursor(cursor_factory=RealDictCursor)
cursor.execute(sql, (query, query, 5))
rows = cursor.fetchall()

print(f"找到 {len(rows)} 条结果:")
for row in rows:
    print(f"\n[{row['patent_id']}] {row['title']}")
    print(f"  排名分数: {row['title_rank']}")

cursor.close()
conn.close()
