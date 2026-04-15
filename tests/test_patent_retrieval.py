#!/usr/bin/env python3
"""
专利检索功能验证脚本
验证从7500万专利数据库中检索的功能
"""

import os
import sys
import time
from typing import Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PatentRetriever:
    """专利检索器"""

    def __init__(self):
        """初始化专利检索器"""
        self.config = {
            "host": "localhost",
            "port": 5432,
            "database": "patent_db",
            "user": "postgres",
            "password": "",  # 本地开发环境可能不需要密码
        }
        self.conn = None

    def connect(self) -> bool:
        """连接到数据库"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            print(f"🔄 连接到PostgreSQL: {self.config['host']}:{self.config['port']}/{self.config['database']}")

            self.conn = psycopg2.connect(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
                cursor_factory=RealDictCursor,
            )

            print("✅ 数据库连接成功")
            return True

        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False

    def get_statistics(self) -> dict[str, Any]:
        """获取数据库统计信息"""
        if not self.conn:
            return {}

        try:
            with self.conn.cursor() as cursor:
                stats = {}

                # 总专利数
                cursor.execute("SELECT COUNT(*) as count FROM patents")
                stats["total_patents"] = cursor.fetchone()["count"]

                # 有全文索引的专利数
                cursor.execute("SELECT COUNT(*) as count FROM patents WHERE search_vector IS NOT NULL")
                stats["fulltext_indexed"] = cursor.fetchone()["count"]

                # 有向量的专利数
                cursor.execute("SELECT COUNT(*) as count FROM patents WHERE embedding_title IS NOT NULL")
                stats["vector_indexed"] = cursor.fetchone()["count"]

                # 按IPC分类统计
                cursor.execute("""
                    SELECT ipc_main_class, COUNT(*) as count
                    FROM patents
                    WHERE ipc_main_class IS NOT NULL
                    GROUP BY ipc_main_class
                    ORDER BY count DESC
                    LIMIT 10
                """)
                stats["top_ipc_classes"] = cursor.fetchall()

                # 按年份统计
                cursor.execute("""
                    SELECT source_year, COUNT(*) as count
                    FROM patents
                    GROUP BY source_year
                    ORDER BY source_year DESC
                    LIMIT 10
                """)
                stats["recent_years"] = cursor.fetchall()

                return stats

        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}

    def fulltext_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        全文检索专利

        Args:
            query: 查询文本
            limit: 返回数量

        Returns:
            检索结果列表
        """
        if not self.conn:
            return []

        try:
            with self.conn.cursor() as cursor:
                start_time = time.time()

                # 使用全文检索
                cursor.execute(
                    """
                    SELECT
                        id,
                        patent_name,
                        abstract,
                        ipc_main_class,
                        application_number,
                        applicant,
                        ts_rank(search_vector, plainto_tsquery('simple', %s)) as rank
                    FROM patents
                    WHERE search_vector @@ plainto_tsquery('simple', %s)
                    ORDER BY rank DESC
                    LIMIT %s
                """,
                    (query, query, limit),
                )

                results = cursor.fetchall()
                elapsed_time = (time.time() - start_time) * 1000

                print(f"🔍 全文检索完成: {len(results)}个结果, 耗时{elapsed_time:.2f}ms")
                return results

        except Exception as e:
            print(f"❌ 全文检索失败: {e}")
            return []

    def keyword_search(self, keyword: str, field: str = "patent_name", limit: int = 10) -> list[dict[str, Any]]:
        """
        关键词搜索专利

        Args:
            keyword: 关键词
            field: 搜索字段
            limit: 返回数量

        Returns:
            检索结果列表
        """
        if not self.conn:
            return []

        try:
            with self.conn.cursor() as cursor:
                start_time = time.time()

                # 使用LIKE进行简单关键词搜索
                if field == "all":
                    cursor.execute(
                        """
                        SELECT
                            id, patent_name, abstract, ipc_main_class,
                            application_number, applicant
                        FROM patents
                        WHERE patent_name ILIKE %s
                           OR abstract ILIKE %s
                           OR applicant ILIKE %s
                        LIMIT %s
                    """,
                        (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
                    )
                else:
                    cursor.execute(
                        f"""
                        SELECT
                            id, patent_name, abstract, ipc_main_class,
                            application_number, applicant
                        FROM patents
                        WHERE {field} ILIKE %s
                        LIMIT %s
                    """,
                        (f"%{keyword}%", limit),
                    )

                results = cursor.fetchall()
                elapsed_time = (time.time() - start_time) * 1000

                print(f"🔍 关键词搜索完成: {len(results)}个结果, 耗时{elapsed_time:.2f}ms")
                return results

        except Exception as e:
            print(f"❌ 关键词搜索失败: {e}")
            return []

    def ipc_search(self, ipc_code: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        按IPC分类号搜索专利

        Args:
            ipc_code: IPC分类号
            limit: 返回数量

        Returns:
            检索结果列表
        """
        if not self.conn:
            return []

        try:
            with self.conn.cursor() as cursor:
                start_time = time.time()

                cursor.execute(
                    """
                    SELECT
                        id, patent_name, abstract, ipc_main_class,
                        ipc_classification, application_number, applicant
                    FROM patents
                    WHERE ipc_main_class LIKE %s OR ipc_classification LIKE %s
                    LIMIT %s
                """,
                    (f"{ipc_code}%", f"%{ipc_code}%", limit),
                )

                results = cursor.fetchall()
                elapsed_time = (time.time() - start_time) * 1000

                print(f"🔍 IPC分类搜索完成: {len(results)}个结果, 耗时{elapsed_time:.2f}ms")
                return results

        except Exception as e:
            print(f"❌ IPC分类搜索失败: {e}")
            return []

    def applicant_search(self, applicant_name: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        按申请人搜索专利

        Args:
            applicant_name: 申请人名称
            limit: 返回数量

        Returns:
            检索结果列表
        """
        if not self.conn:
            return []

        try:
            with self.conn.cursor() as cursor:
                start_time = time.time()

                cursor.execute(
                    """
                    SELECT
                        id, patent_name, abstract, ipc_main_class,
                        application_number, applicant, application_date
                    FROM patents
                    WHERE applicant ILIKE %s
                    ORDER BY application_date DESC
                    LIMIT %s
                """,
                    (f"%{applicant_name}%", limit),
                )

                results = cursor.fetchall()
                elapsed_time = (time.time() - start_time) * 1000

                print(f"🔍 申请人搜索完成: {len(results)}个结果, 耗时{elapsed_time:.2f}ms")
                return results

        except Exception as e:
            print(f"❌ 申请人搜索失败: {e}")
            return []

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("✅ 数据库连接已关闭")


def print_statistics(stats: dict[str, Any]):
    """打印统计信息"""
    print("\n" + "=" * 60)
    print("📊 专利数据库统计信息")
    print("=" * 60)

    if "total_patents" in stats:
        print("\n📈 数据量统计:")
        print(f"  总专利数: {stats['total_patents']:,} 条")
        print(f"  全文索引: {stats['fulltext_indexed']:,} 条 ({stats['fulltext_indexed']/stats['total_patents']*100:.1f}%)")
        print(f"  向量索引: {stats['vector_indexed']:,} 条 ({stats['vector_indexed']/stats['total_patents']*100:.1f}%)")

    if "top_ipc_classes" in stats:
        print("\n🏷️  热门IPC分类 (Top 10):")
        for item in stats["top_ipc_classes"]:
            print(f"  {item['ipc_main_class']}: {item['count']:,} 条")

    if "recent_years" in stats:
        print("\n📅 近年专利数量:")
        for item in stats["recent_years"]:
            print(f"  {item['source_year']}: {item['count']:,} 条")

    print("=" * 60 + "\n")


def print_results(results: list[dict[str, Any]], title: str = "检索结果"):
    """打印检索结果"""
    print(f"\n{'=' * 60}")
    print(f"📋 {title}")
    print(f"{'=' * 60}\n")

    if not results:
        print("❌ 未找到匹配结果")
        return

    for i, result in enumerate(results, 1):
        print(f"【{i}】{result.get('patent_name', 'N/A')}")
        print(f"  申请号: {result.get('application_number', 'N/A')}")
        print(f"  申请人: {result.get('applicant', 'N/A')}")
        print(f"  IPC分类: {result.get('ipc_main_class', 'N/A')}")
        if result.get('abstract'):
            abstract = result['abstract'][:100] + "..." if len(result['abstract']) > 100 else result['abstract']
            print(f"  摘要: {abstract}")
        if result.get('rank'):
            print(f"  相关度: {result['rank']:.4f}")
        print()

    print(f"{'=' * 60}\n")


def main():
    """主函数"""
    print("🚀 Athena平台专利检索功能验证")
    print("=" * 60)

    # 创建检索器
    retriever = PatentRetriever()

    # 连接数据库
    if not retriever.connect():
        print("❌ 无法连接到数据库，退出")
        return

    try:
        # 获取统计信息
        print("\n📊 获取数据库统计信息...")
        stats = retriever.get_statistics()
        print_statistics(stats)

        # 测试1: 全文检索
        print("\n🔍 测试1: 全文检索 - '人工智能'")
        results = retriever.fulltext_search("人工智能", limit=5)
        print_results(results, "全文检索结果 - '人工智能'")

        # 测试2: 关键词搜索
        print("\n🔍 测试2: 关键词搜索 - '医疗'")
        results = retriever.keyword_search("医疗", field="patent_name", limit=5)
        print_results(results, "关键词搜索结果 - '医疗'")

        # 测试3: IPC分类搜索
        print("\n🔍 测试3: IPC分类搜索 - 'G06F'")
        results = retriever.ipc_search("G06F", limit=5)
        print_results(results, "IPC分类搜索结果 - 'G06F'")

        # 测试4: 申请人搜索
        print("\n🔍 测试4: 申请人搜索 - '腾讯'")
        results = retriever.applicant_search("腾讯", limit=5)
        print_results(results, "申请人搜索结果 - '腾讯'")

        # 测试5: 综合搜索
        print("\n🔍 测试5: 综合搜索 - '深度学习'")
        results = retriever.keyword_search("深度学习", field="all", limit=5)
        print_results(results, "综合搜索结果 - '深度学习'")

        print("\n" + "=" * 60)
        print("✅ 专利检索功能验证完成")
        print("=" * 60)

    finally:
        retriever.close()


if __name__ == "__main__":
    main()
