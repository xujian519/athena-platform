#!/usr/bin/env python3
"""
山东大齐四课题专利下载脚本
从本地数据库检索并导出专利详情到指定目录
"""

import json
import os
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "patent_db",
    "user": "postgres"
}

# 输出目录
OUTPUT_DIR = "/Users/xujian/工作/01_客户管理/01_正式客户/山东大齐4件"

# 所有检索到的专利申请号列表
PATENT_NUMBERS = [
    # 课题一：管壳式换热器
    "CN201320508689.X",
    "CN201910818135.1",
    "CN201921189625.1",
    "CN201821113286.4",
    "CN201310587576.8",

    # 课题二：多功能反应釜
    "CN201210575269.3",
    "CN201220722067.2",
    "CN201110242333.1",
    "CN201220731804.5",
    "CN201220587642.2",
    "CN201320220578.9",
    "CN202410882450.1",
    "CN202022616673.3",
    "CN201220431536.5",
    "CN200320103388.5",
    "CN02222944.2",
    "CN201220546548.2",
    "CN201220579237.6",
    "CN201220731449.1",
    "CN201320478071.3",
    "CN201410843409.X",
    "CN201510938640.1",
    "CN200320126593.3",
    "CN200520094784.5",

    # 课题三：填料塔分离装置
    "CN201420099038.4",
    "CN201220709918.X",
    "CN201320846029.2",
    "CN201210212171.1",
    "CN201220300555.4",
    "CN201920603698.4",
    "CN201410112590.7",
    "CN201320681068.1",
    "CN202222842050.7",
    "CN202110601795.1",
    "CN202010455595.5",
    "CN201420714372.6",
    "CN201310660323.9",
    "CN201420542150.0",
    "CN201410684118.0",
    "CN202123275055.8",
    "CN201920181898.5",
    "CN202420522997.6",
    "CN202210576257.6",
    "CN201310694565.X",

    # 课题四：双层储罐
    "CN201720969758.5",
    "CN201210356732.5",
    "CN201320732384.7",
    "CN201921117397.7",
    "CN201810202573.0",
    "CN202110159126.3",
    "CN201910779372.1",
    "CN201720186137.X",
    "CN202121543748.8",
    "CN202121782596.7",
    "CN202122055941.3",
    "CN202123226115.7",
    "CN201310186132.3",
    "CN202411777319.5",
    "CN202421214299.6",
    "CN201710546024.0",
    "CN202311141046.0",
    "CN201820336025.2",
    "CN202411782747.7",
]

def export_patent_details():
    """从数据库导出专利详情"""

    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    print("=" * 70)
    print("📥 山东大齐专利下载 - 数据库导出版")
    print("=" * 70)
    print()

    # 创建课题子目录
    topic_dirs = {
        "topic1": os.path.join(OUTPUT_DIR, "课题一_管壳式换热器"),
        "topic2": os.path.join(OUTPUT_DIR, "课题二_多功能反应釜"),
        "topic3": os.path.join(OUTPUT_DIR, "课题三_填料塔分离装置"),
        "topic4": os.path.join(OUTPUT_DIR, "课题四_双层储罐"),
    }

    for dir_path in topic_dirs.values():
        os.makedirs(dir_path, exist_ok=True)

    # 按课题分组专利号
    topic_patents = {
        "topic1": PATENT_NUMBERS[0:5],
        "topic2": PATENT_NUMBERS[5:26],
        "topic3": PATENT_NUMBERS[26:46],
        "topic4": PATENT_NUMBERS[46:61],
    }

    exported_count = 0
    not_found = []

    for topic, patent_list in topic_patents.items():
        print(f"📁 处理 {topic}...")
        print("-" * 70)

        for app_num in patent_list:
            query = """
            SELECT
                patent_name,
                application_number,
                publication_number,
                authorization_number,
                applicant,
                application_date,
                publication_date,
                authorization_date,
                ipc_main_class,
                ipc_classification,
                abstract,
                claims_content,
                claims,
                patent_type,
                ipc_code
            FROM patents
            WHERE application_number = %s
            LIMIT 1;
            """

            cursor.execute(query, (app_num,))
            result = cursor.fetchone()

            if result:
                # 导出为JSON文件
                safe_name = result['patent_name'].replace('/', '_').replace('\\', '_')[:50]
                filename = f"{app_num}_{safe_name}.json"
                filepath = os.path.join(topic_dirs[topic], filename)

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(dict(result), f, ensure_ascii=False, indent=2, default=str)

                # 导出为文本摘要
                txt_filename = f"{app_num}_{safe_name}.txt"
                txt_filepath = os.path.join(topic_dirs[topic], txt_filename)

                with open(txt_filepath, 'w', encoding='utf-8') as f:
                    f.write("=" * 70 + "\n")
                    f.write(f"专利名称: {result['patent_name']}\n")
                    f.write("=" * 70 + "\n\n")
                    f.write(f"申请号: {result['application_number']}\n")
                    f.write(f"公开号: {result['publication_number'] or '待公开'}\n")
                    f.write(f"授权号: {result['authorization_number'] or '未授权'}\n")
                    f.write(f"申请人: {result['applicant']}\n")
                    f.write(f"申请日: {result['application_date']}\n")
                    f.write(f"公开日: {result['publication_date'] or '待公开'}\n")
                    f.write(f"IPC主分类: {result['ipc_main_class'] or '未分类'}\n")
                    f.write(f"IPC分类: {result['ipc_code'] or '-'}\n")
                    f.write(f"专利类型: {result['patent_type'] or '未知'}\n\n")
                    f.write("-" * 70 + "\n")
                    f.write("摘要:\n")
                    f.write("-" * 70 + "\n")
                    f.write(result['abstract'] or '无摘要')
                    f.write("\n\n")
                    if result['claims_content']:
                        f.write("-" * 70 + "\n")
                        f.write("权利要求:\n")
                        f.write("-" * 70 + "\n")
                        f.write(result['claims_content'][:1000])  # 截取前1000字符
                        f.write("\n\n")
                    if result['claims']:
                        f.write("-" * 70 + "\n")
                        f.write("权利要求(简):\n")
                        f.write("-" * 70 + "\n")
                        f.write(result['claims'][:1000])  # 截取前1000字符
                        f.write("\n\n")

                exported_count += 1
                print(f"  ✅ {app_num} - {result['patent_name'][:40]}")
            else:
                not_found.append(app_num)
                print(f"  ❌ {app_num} - 数据库中未找到")

        print()

    cursor.close()
    conn.close()

    # 生成汇总清单
    summary_file = os.path.join(OUTPUT_DIR, "专利下载清单_汇总.md")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# 山东大齐专利下载清单\n\n")
        f.write(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 导出统计\n\n")
        f.write(f"- 成功导出: {exported_count} 条\n")
        f.write(f"- 未找到: {len(not_found)} 条\n\n")
        f.write("## 文件目录\n\n")
        f.write("```\n")
        f.write("山东大齐4件/\n")
        f.write("├── 课题一_管壳式换热器/\n")
        f.write("├── 课题二_多功能反应釜/\n")
        f.write("├── 课题三_填料塔分离装置/\n")
        f.write("├── 课题四_双层储罐/\n")
        f.write("└── 专利下载清单_汇总.md\n")
        f.write("```\n\n")

        if not_found:
            f.write("## 未找到的专利\n\n")
            for num in not_found:
                f.write(f"- {num}\n")

    print("=" * 70)
    print("📊 导出完成")
    print("=" * 70)
    print(f"成功导出: {exported_count} 条")
    print(f"未找到: {len(not_found)} 条")
    print(f"导出目录: {OUTPUT_DIR}")
    print(f"汇总文件: {summary_file}")

if __name__ == "__main__":
    export_patent_details()
