#!/usr/bin/env python3
"""
专利检索命令行工具
Patent Search CLI Tool

从本地PostgreSQL专利数据库快速检索专利信息。
"""

import argparse
import sys
from typing import Any

# 添加项目路径
sys.path.insert(0, "/Users/xujian/Athena工作平台")

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ 请安装psycopg2: pip install psycopg2-binary")
    sys.exit(1)


class PatentSearchCLI:
    """专利检索命令行工具"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "patent_db",
        user: str = "postgres",
        password: str = "",
    ):
        """初始化检索工具"""
        self.config = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
        }
        self.conn = None

    def connect(self) -> bool:
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**self.config, cursor_factory=RealDictCursor)
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False

    def search_by_keyword(
        self, keyword: str, field: str = "all", limit: int = 10
    ) -> list[dict[str, Any]:
        """
        关键词检索

        Args:
            keyword: 关键词
            field: 搜索字段 (patent_name/abstract/applicant/all)
            limit: 返回数量

        Returns:
            检索结果列表
        """
        if not self.conn:
            if not self.connect():
                return []

        try:
            with self.conn.cursor() as cursor:
                if field == "all":
                    cursor.execute(
                        """
                        SELECT id, patent_name, abstract, applicant,
                               ipc_main_class, application_number
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
                        SELECT id, patent_name, abstract, applicant,
                               ipc_main_class, application_number
                        FROM patents
                        WHERE {field} ILIKE %s
                        LIMIT %s
                    """,
                        (f"%{keyword}%", limit),
                    )

                results = cursor.fetchall()
                return [dict(r) for r in results]

        except Exception as e:
            print(f"❌ 检索失败: {e}")
            return []

    def search_by_ipc(
        self, ipc_code: str, limit: int = 10
    ) -> list[dict[str, Any]:
        """
        IPC分类检索

        Args:
            ipc_code: IPC分类号
            limit: 返回数量

        Returns:
            检索结果列表
        """
        if not self.conn:
            if not self.connect():
                return []

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, patent_name, abstract, applicant,
                           ipc_main_class, ipc_classification,
                           application_number, application_date
                    FROM patents
                    WHERE ipc_main_class LIKE %s OR ipc_classification LIKE %s
                    ORDER BY application_date DESC
                    LIMIT %s
                """,
                    (f"{ipc_code}%", f"%{ipc_code}%", limit),
                )

                results = cursor.fetchall()
                return [dict(r) for r in results]

        except Exception as e:
            print(f"❌ 检索失败: {e}")
            return []

    def search_by_applicant(
        self, applicant: str, limit: int = 10
    ) -> list[dict[str, Any]:
        """
        申请人检索

        Args:
            applicant: 申请人名称
            limit: 返回数量

        Returns:
            检索结果列表
        """
        if not self.conn:
            if not self.connect():
                return []

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, patent_name, abstract, applicant,
                           ipc_main_class, application_number,
                           application_date, authorization_number
                    FROM patents
                    WHERE applicant ILIKE %s
                    ORDER BY application_date DESC
                    LIMIT %s
                """,
                    (f"%{applicant}%", limit),
                )

                results = cursor.fetchall()
                return [dict(r) for r in results]

        except Exception as e:
            print(f"❌ 检索失败: {e}")
            return []

    def fulltext_search(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]:
        """
        全文检索

        Args:
            query: 查询文本
            limit: 返回数量

        Returns:
            检索结果列表
        """
        if not self.conn:
            if not self.connect():
                return []

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, patent_name, abstract, applicant,
                           ipc_main_class, application_number,
                           ts_rank(search_vector, plainto_tsquery('simple', %s)) as rank
                    FROM patents
                    WHERE search_vector @@ plainto_tsquery('simple', %s)
                    ORDER BY rank DESC
                    LIMIT %s
                """,
                    (query, query, limit),
                )

                results = cursor.fetchall()
                return [dict(r) for r in results]

        except Exception as e:
            print(f"❌ 检索失败: {e}")
            return []

    def get_statistics(self) -> dict[str, Any]:
        """获取数据库统计信息"""
        if not self.conn:
            if not self.connect():
                return {}

        try:
            with self.conn.cursor() as cursor:
                # 总专利数
                cursor.execute("SELECT COUNT(*) as count FROM patents")
                total = cursor.fetchone()["count"]

                # 全文索引覆盖
                cursor.execute(
                    "SELECT COUNT(*) as count FROM patents WHERE search_vector IS NOT NULL"
                )
                indexed = cursor.fetchone()["count"]

                # 表大小
                cursor.execute(
                    """
                    SELECT pg_size_pretty(pg_total_relation_size('patents')) as size
                """
                )
                size = cursor.fetchone()["size"]

                return {
                    "total_patents": total,
                    "indexed_patents": indexed,
                    "table_size": size,
                }

        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


def format_result(result: dict[str, Any], index: int) -> str:
    """格式化单条检索结果"""
    output = []
    output.append(f"\n【{index}】{result.get('patent_name', 'N/A')}")

    if result.get("application_number"):
        output.append(f"  申请号: {result['application_number']}")

    if result.get("applicant"):
        output.append(f"  申请人: {result['applicant']}")

    if result.get("ipc_main_class"):
        output.append(f"  IPC分类: {result['ipc_main_class']}")

    if result.get("abstract"):
        abstract = result["abstract"]
        if len(abstract) > 100:
            abstract = abstract[:100] + "..."
        output.append(f"  摘要: {abstract}")

    if result.get("rank"):
        output.append(f"  相关度: {result['rank']:.4f}")

    return "\n".join(output)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Athena专利检索命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s keyword 人工智能              # 关键词检索
  %(prog)s ipc G06F                     # IPC分类检索
  %(prog)s applicant 腾讯               # 申请人检索
  %(prog)s fulltext "医疗 & 器械"       # 全文检索
  %(prog)s stats                        # 统计信息
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="检索命令")

    # 关键词检索
    keyword_parser = subparsers.add_parser("keyword", help="关键词检索")
    keyword_parser.add_argument("keyword", help="关键词")
    keyword_parser.add_argument(
        "-f", "--field", default="all",
        choices=["patent_name", "abstract", "applicant", "all"],
        help="搜索字段"
    )
    keyword_parser.add_argument("-l", "--limit", type=int, default=10, help="返回数量")

    # IPC分类检索
    ipc_parser = subparsers.add_parser("ipc", help="IPC分类检索")
    ipc_parser.add_argument("ipc_code", help="IPC分类号")
    ipc_parser.add_argument("-l", "--limit", type=int, default=10, help="返回数量")

    # 申请人检索
    applicant_parser = subparsers.add_parser("applicant", help="申请人检索")
    applicant_parser.add_argument("applicant", help="申请人名称")
    applicant_parser.add_argument("-l", "--limit", type=int, default=10, help="返回数量")

    # 全文检索
    fulltext_parser = subparsers.add_parser("fulltext", help="全文检索")
    fulltext_parser.add_argument("query", help="查询文本")
    fulltext_parser.add_argument("-l", "--limit", type=int, default=10, help="返回数量")

    # 统计信息
    subparsers.add_parser("stats", help="显示统计信息")

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 创建检索工具
    cli = PatentSearchCLI()

    try:
        # 执行检索
        if args.command == "keyword":
            print(f"\n🔍 关键词检索: {args.keyword}")
            results = cli.search_by_keyword(args.keyword, args.field, args.limit)

        elif args.command == "ipc":
            print(f"\n🔍 IPC分类检索: {args.ipc_code}")
            results = cli.search_by_ipc(args.ipc_code, args.limit)

        elif args.command == "applicant":
            print(f"\n🔍 申请人检索: {args.applicant}")
            results = cli.search_by_applicant(args.applicant, args.limit)

        elif args.command == "fulltext":
            print(f"\n🔍 全文检索: {args.query}")
            results = cli.fulltext_search(args.query, args.limit)

        elif args.command == "stats":
            print("\n📊 数据库统计信息")
            stats = cli.get_statistics()
            if stats:
                print(f"  总专利数: {stats.get('total_patents', 0):,} 条")
                print(f"  全文索引: {stats.get('indexed_patents', 0):,} 条")
                print(f"  表大小: {stats.get('table_size', 'N/A')}")
            results = []

        # 显示结果
        if args.command != "stats":
            if results:
                print(f"\n找到 {len(results)} 条结果:")
                for i, result in enumerate(results, 1):
                    print(format_result(result, i))
            else:
                print("\n❌ 未找到匹配结果")

    finally:
        cli.close()


if __name__ == "__main__":
    main()
