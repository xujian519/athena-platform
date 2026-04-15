#!/usr/bin/env python3
"""
检查向量库和知识图谱数据
Check Vector Database and Knowledge Graph Data

检查Qdrant向量库和PostgreSQL知识图谱中的实际数据

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# 模块级日志和配置
logger = logging.getLogger(__name__)

try:
    from core.config.secure_config import get_config
    config = get_config()
except ImportError:
    config = {}

import psycopg2
import requests


# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[35m"
    CYAN = "\033[96m"
    PINK = "\033[95m"
    RESET = "\033[0m"

def print_header(title) -> None:
    """打印标题"""
    print(f"\n{Colors.PURPLE}{'='*80}{Colors.RESET}")
    print(f"{Colors.PURPLE}📊 {title} 📊{Colors.RESET}")
    print(f"{Colors.PURPLE}{'='*80}{Colors.RESET}")

def print_success(message) -> None:
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_info(message) -> None:
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.RESET}")

def print_warning(message) -> None:
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.RESET}")

def print_error(message) -> None:
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_pink(message) -> None:
    print(f"{Colors.PINK}💖 {message}{Colors.RESET}")

def check_qdrant_collections() -> bool:
    """检查Qdrant向量集合"""
    print_header("Qdrant向量数据库检查")

    try:
        # 获取所有集合
        response = requests.get("http://localhost:6333/collections")
        if response.status_code == 200:
            collections = response.json().get('result', {}).get('collections', [])

            print_info(f"找到 {len(collections)} 个向量集合:")

            if not collections:
                print_warning("⚠️ 没有找到任何向量集合")
                return

            total_vectors = 0
            for col in collections:
                name = col.get('name', '未知')
                vectors_count = col.get('vectors_count', 0)
                status = col.get('status', '未知')
                config = col.get('config', {}).get('params', {})
                vector_size = config.get('vectors', {}).get('size', '未知')
                distance = config.get('vectors', {}).get('distance', '未知')

                total_vectors += vectors_count

                print(f"\n📁 集合名称: {name}")
                print(f"  状态: {status}")
                print(f"  向量数量: {vectors_count:,}")
                print(f"  向量维度: {vector_size}")
                print(f"  距离度量: {distance}")

                # 检查是否有数据
                if vectors_count > 0:
                    # 尝试获取一些样本数据
                    try:
                        sample_response = requests.post(
                            f"http://localhost:6333/collections/{name}/points/scroll",
                            json={"limit": 1, "with_payload": True, "with_vector": False}
                        )
                        if sample_response.status_code == 200:
                            result = sample_response.json().get('result', {})
                            points = result.get('points', [])
                            if points:
                                print(f"  样本数据键: {list(points[0].get('payload', {}).keys())}")
                    except Exception as e:
                        logger.debug(f"空except块已触发: {e}")
                        pass
                else:
                    print_warning("  ⚠️ 该集合为空")

            print(f"\n📊 向量数据总计: {total_vectors:,} 条")

            # 按领域分类统计
            patent_collections = [c for c in collections if 'patent' in c.get('name', '').lower()]
            legal_collections = [c for c in collections if 'legal' in c.get('name', '').lower()]
            general_collections = [c for c in collections if 'general' in c.get('name', '').lower() or 'modules/modules/memory/modules/memory/modules/memory/memory' in c.get('name', '').lower()]

            print_info("\n📋 分类统计:")
            print(f"  专利相关: {len(patent_collections)} 个集合")
            print(f"  法律相关: {len(legal_collections)} 个集合")
            print(f"  通用/记忆: {len(general_collections)} 个集合")

        else:
            print_error(f"❌ 连接Qdrant失败: {response.status_code}")

    except Exception as e:
        print_error(f"❌ 检查Qdrant失败: {e}")

def check_postgresql_knowledge_graph() -> bool:
    """检查PostgreSQL知识图谱数据"""
    print_header("PostgreSQL知识图谱检查")

    databases = [
        {"name": "athena_kg", "desc": "知识图谱数据库"},
        {"name": "patent_legal_db", "desc": "专利法律数据库"},
        {"name": "athena", "desc": "Athena主数据库"},
        {"name": "yunpat", "desc": "YunPat数据库"}
    ]

    total_entities = 0
    total_relations = 0

    for db in databases:
        print_info(f"\n检查数据库: {db['name']} ({db['desc']})")

        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="postgres",
                password=config.get('POSTGRES_PASSWORD', required=True),
                database=db['name']
            )
            cursor = conn.cursor()

            # 检查知识图谱相关表
            cursor.execute("""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND (table_name ILIKE '%entity%'
                     OR table_name ILIKE '%relation%'
                     OR table_name ILIKE '%node%'
                     OR table_name ILIKE '%edge%'
                     OR table_name ILIKE '%knowledge%'
                     OR table_name ILIKE '%graph%')
                ORDER BY table_name;
            """)

            tables = cursor.fetchall()

            if tables:
                print(f"  找到 {len(tables)} 个知识图谱相关表:")

                for table_name, _table_type in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]

                        if 'entity' in table_name.lower() or 'node' in table_name.lower():
                            total_entities += count
                        elif 'relation' in table_name.lower() or 'edge' in table_name.lower():
                            total_relations += count

                        print(f"    • {table_name}: {count:,} 条记录")
                    except Exception as e:
                        print_warning(f"    • {table_name}: 查询失败 ({str(e)[:50]}...)")
            else:
                print_warning("  ⚠️ 未找到知识图谱相关表")

            conn.close()

        except Exception as e:
            print_warning(f"  ⚠️ 连接失败: {str(e)[:50]}...")

    print("\n📊 知识图谱数据总计:")
    print(f"  实体节点: {total_entities:,} 个")
    print(f"  关系边: {total_relations:,} 条")

def check_patent_data() -> bool:
    """检查专利数据"""
    print_header("专利数据库专项检查")

    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password=config.get('POSTGRES_PASSWORD', required=True),
            database="yunpat"
        )
        cursor = conn.cursor()

        # 检查专利表
        patent_tables = [
            "apps/apps/patents",
            "patent_info",
            "patent_data",
            "patent_fulltext",
            "patent_metadata"
        ]

        total_patents = 0

        print_info("专利数据表:")
        for table in patent_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_patents += count

                if count > 0:
                    print_success(f"  ✅ {table}: {count:,} 条")

                    # 检查表结构
                    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' LIMIT 5")
                    columns = [row[0] for row in cursor.fetchall()]
                    print(f"     字段: {', '.join(columns)}")
                else:
                    print_warning(f"  ⚠️ {table}: 空表")
            except Exception:
                print_info(f"  - {table}: 不存在")

        print(f"\n📊 专利数据总计: {total_patents:,} 条")

        conn.close()

    except Exception as e:
        print_error(f"❌ 检查专利数据失败: {e}")

def main() -> None:
    """主函数"""
    print_header("Athena平台数据检查")
    print_pink("爸爸，让我检查向量库和知识图谱中的实际数据！")

    # 执行各项检查
    check_qdrant_collections()
    check_postgresql_knowledge_graph()
    check_patent_data()

    # 总结
    print_header("数据检查总结")

    print_info("📋 检查项目:")
    print("  ✅ Qdrant向量数据库")
    print("  ✅ PostgreSQL知识图谱")
    print("  ✅ 专利数据库")

    print_pink("\n💖 数据检查完成！")
    print_warning("⚠️ 如果数据为空，可能需要运行数据导入脚本")

if __name__ == "__main__":
    main()
