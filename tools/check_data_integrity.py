#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据完整性和去重情况
Check Data Integrity and Deduplication
"""

import psycopg2
import json
import os
from collections import Counter

def check_data_integrity():
    """检查数据完整性"""

    # PostgreSQL配置
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "patent_archive",
        "user": "xujian",
        "password": ""
    }

    # 检查PostgreSQL路径
    postgres_path = "/opt/homebrew/opt/postgresql@17/bin"
    if postgres_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = postgres_path + ":" + os.environ.get("PATH", "")

    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    print("=" * 80)
    print("📊 数据完整性检查报告")
    print("=" * 80)

    # 1. 检查专利总数
    print("\n1. 专利数据统计:")
    cursor.execute("SELECT COUNT(*) FROM patents")
    total_patents = cursor.fetchone()[0]
    print(f"   总专利数: {total_patents:,}")

    # 2. 检查客户（申请人）去重情况
    print("\n2. 客户（申请人）去重情况:")
    cursor.execute("""
        SELECT
            patent_name,
            COUNT(*) as count
        FROM patents
        WHERE patent_name IS NOT NULL
        AND patent_name != ''
        AND patent_name != 'nan'
        GROUP BY patent_name
        ORDER BY count DESC
        LIMIT 10
    """)
    top_customers = cursor.fetchall()
    print("   前10名客户（按专利数量）:")
    for i, (name, count) in enumerate(top_customers, 1):
        print(f"   {i:2d}. {name:<50} {count:4d} 件")

    # 统计唯一客户数
    cursor.execute("""
        SELECT COUNT(DISTINCT patent_name)
        FROM patents
        WHERE patent_name IS NOT NULL
        AND patent_name != ''
        AND patent_name != 'nan'
    """)
    unique_customers = cursor.fetchone()[0]
    print(f"\n   唯一客户数: {unique_customers}")

    # 检查重复情况
    duplicate_count = total_patents - unique_customers
    duplication_rate = (duplicate_count / total_patents * 100) if total_patents > 0 else 0
    print(f"   重复记录: {duplicate_count:,} ({duplication_rate:.1f}%)")

    # 3. 检查相似客户名称（需要去重的）
    print("\n3. 可能需要合并的相似客户名称:")
    cursor.execute("""
        WITH normalized_names AS (
            SELECT
                REGEXP_REPLACE(REPLACE(patent_name, '有限公司', ''), '变更为.*$', '') as normalized,
                STRING_AGG(patent_name, '|') as original_names,
                COUNT(*) as count
            FROM patents
            WHERE patent_name IS NOT NULL
            AND patent_name != ''
            AND patent_name != 'nan'
            GROUP BY REGEXP_REPLACE(REPLACE(patent_name, '有限公司', ''), '变更为.*$', '')
            HAVING COUNT(*) > 1
        )
        SELECT * FROM normalized_names
        ORDER BY count DESC
        LIMIT 10
    """)

    similar_customers = cursor.fetchall()
    if similar_customers:
        print("   可能需要标准化的客户名称:")
        for i, (norm, originals, count) in enumerate(similar_customers, 1):
            print(f"   {i}. 标准名称: {norm}")
            print(f"      原始名称: {originals[:100]}...")
            print(f"      专利数: {count}")
    else:
        print("   没有发现明显需要合并的相似客户")

    # 4. 检查关联关系
    print("\n4. 关联关系检查:")

    # 检查案源人与专利的关联
    cursor.execute("""
        SELECT
            a.client_name as 案源人,
            COUNT(p.id) as 专利数,
            COUNT(DISTINCT p.patent_name) as 客户数
        FROM patent_agents a
        LEFT JOIN patents p ON a.id = p.agent_id
        GROUP BY a.id, a.client_name
        ORDER BY 专利数 DESC
        LIMIT 5
    """)
    agent_stats = cursor.fetchall()
    print("   案源人服务统计（前5名）:")
    for i, (agent, patents, customers) in enumerate(agent_stats, 1):
        print(f"   {i}. {agent:<20} 专利: {patents:>4}  客户: {customers:>3}")

    # 5. 检查缺失的关联
    print("\n5. 缺失关联检查:")
    # 没有关联案源人的专利
    cursor.execute("""
        SELECT COUNT(*)
        FROM patents
        WHERE agent_id IS NULL
    """)
    missing_agent = cursor.fetchone()[0]
    print(f"   没有关联案源人的专利: {missing_agent:,}")

    # 没有客户名称的专利
    cursor.execute("""
        SELECT COUNT(*)
        FROM patents
        WHERE patent_name IS NULL
        OR patent_name = ''
        OR patent_name = 'nan'
    """)
    missing_customer = cursor.fetchone()[0]
    print(f"   没有客户名称的专利: {missing_customer:,}")

    # 6. 检查联系方式覆盖率
    print("\n6. 联系方式覆盖率:")
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN contact_info IS NOT NULL AND contact_info != '' THEN 1 END) as has_contact,
            COUNT(CASE WHEN agency IS NOT NULL AND agency != '' THEN 1 END) as has_agency
        FROM patents
        WHERE patent_name IS NOT NULL
        AND patent_name != ''
        AND patent_name != 'nan'
    """)
    contact_stats = cursor.fetchone()
    contact_rate = (contact_stats[1] / contact_stats[0] * 100) if contact_stats[0] > 0 else 0
    agency_rate = (contact_stats[2] / contact_stats[0] * 100) if contact_stats[0] > 0 else 0
    print(f"   总记录: {contact_stats[0]:,}")
    print(f"   有联系信息: {contact_stats[1]:,} ({contact_rate:.1f}%)")
    print(f"   有代理机构: {contact_stats[2]:,} ({agency_rate:.1f}%)")

    # 7. 分析一个具体客户的完整信息
    print("\n7. 客户详细信息示例（山东艾迈泰克机械科技有限公司）:")
    cursor.execute("""
        SELECT
            p.patent_number,
            p.patent_name,
            p.patent_type,
            p.application_date,
            p.legal_status,
            p.contact_info,
            p.agency,
            a.client_name as 案源人
        FROM patents p
        LEFT JOIN patent_agents a ON p.agent_id = a.id
        WHERE p.patent_name = '山东艾迈泰克机械科技有限公司'
        LIMIT 5
    """)
    customer_details = cursor.fetchall()
    for i, detail in enumerate(customer_details, 1):
        print(f"   记录{i}:")
        print(f"     申请号: {detail[0]}")
        print(f"     专利类型: {detail[2]}")
        print(f"     申请日: {detail[3]}")
        print(f"     法律状态: {detail[4]}")
        print(f"     联系信息: {detail[5]}")
        print(f"     代理机构: {detail[6]}")
        print(f"     案源人: {detail[7]}")

    # 8. 生成数据质量报告
    print("\n8. 数据质量总结:")
    data_quality = {
        "total_patents": total_patents,
        "unique_customers": unique_customers,
        "duplicates": duplicate_count,
        "duplication_rate": duplication_rate,
        "missing_agent": missing_agent,
        "missing_customer": missing_customer,
        "contact_coverage": contact_rate,
        "agency_coverage": agency_rate
    }

    # 保存报告
    with open("data_integrity_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "检查时间": "2025-12-17",
            "数据质量": data_quality,
            "建议": [
                "建议1: 标准化相似客户名称，减少重复",
                "建议2: 为缺失案源人的专利补充关联",
                "建议3: 清理和验证联系信息",
                "建议4: 建立独立的客户表，将客户与专利分离管理"
            ]
        }, f, ensure_ascii=False, indent=2)

    print("\n   ✅ 详细报告已保存到: data_integrity_report.json")

    cursor.close()
    conn.close()

    return data_quality

def suggest_improvements(quality):
    """提出改进建议"""
    print("\n" + "=" * 80)
    print("💡 数据改进建议")
    print("=" * 80)

    suggestions = [
        {
            "问题": "客户名称需要标准化",
            "示例": "\"山东艾迈泰克机械科技有限公司\" 和 \"山东艾迈泰克\"",
            "解决方案": "建立客户标准化规则，去除公司后缀，统一名称格式",
            "SQL": """
-- 创建标准客户表
CREATE TABLE patent_customers (
    id SERIAL PRIMARY KEY,
    original_name VARCHAR(500),  -- 原始名称
    standard_name VARCHAR(200),  -- 标准名称
    entity_type VARCHAR(50),     -- 公司类型
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入标准化后的客户
INSERT INTO patent_customers (original_name, standard_name, entity_type)
SELECT
    patent_name,
    -- 标准化逻辑
    CASE
        WHEN patent_name LIKE '%有限公司%' THEN REPLACE(patent_name, '有限公司', '')
        WHEN patent_name LIKE '%股份%' THEN REPLACE(patent_name, '股份有限公司', '')
        ELSE patent_name
    END,
    CASE
        WHEN patent_name LIKE '%学院%' OR patent_name LIKE '%大学%' THEN '教育机构'
        WHEN patent_name LIKE '%公司%' OR patent_name LIKE '%集团%' THEN '企业'
        ELSE '其他'
    END
FROM patents
GROUP BY patent_name;
            """
        },
        {
            "问题": "专利表结构冗余",
            "现状": "客户信息重复存储在每条专利记录中",
            "解决方案": "分离客户信息，建立外键关联",
            "SQL": """
-- 在专利表中添加客户ID外键
ALTER TABLE patents ADD COLUMN customer_id INTEGER REFERENCES patent_customers(id);

-- 更新专利表的客户ID
UPDATE patents p
SET customer_id = (
    SELECT id
    FROM patent_customers c
    WHERE p.patent_name = c.original_name
);
            """
        },
        {
            "问题": "缺失关联关系",
            "现状": f"{quality['missing_agent']:,}个专利没有关联案源人",
            "解决方案": "根据名称模式或人工补充缺失的关联",
            "SQL": """
-- 尝试根据联系信息推断案源人
UPDATE patents p
SET agent_id = (
    SELECT a.id
    FROM patent_agents a
    WHERE a.client_name = (
        CASE
            WHEN p.contact_info LIKE '%徐健%' THEN '徐健'
            WHEN p.contact_info LIKE '%傅玉秀%' THEN '傅玉秀'
            -- 添加更多规则...
            ELSE NULL
        END
    )
)
WHERE agent_id IS NULL
AND p.contact_info IS NOT NULL;
            """
        }
    ]

    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n改进建议 {i}:")
        print(f"  问题: {suggestion['问题']}")
        print(f"  示例: {suggestion['示例']}")
        print(f"  解决方案: {suggestion['解决方案']}")

if __name__ == "__main__":
    print("🔍 开始检查数据完整性...")
    quality = check_data_integrity()
    suggest_improvements()

    print("\n✅ 检查完成！")
    print("\n主要发现:")
    print(f"- 专利总数: {quality['total_patents']:,}")
    print(f"- 唯一客户数: {quality['unique_customers']:,}")
    print(f"- 数据重复率: {quality['duplication_rate']:.1f}%")
    print(f"- 缺失案源人关联: {quality['missing_agent']:,} 件专利")
    print(f"- 联系信息覆盖率: {quality['contact_coverage']:.1f}%")