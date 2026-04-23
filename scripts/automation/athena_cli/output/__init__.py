"""
输出格式化模块
Output Formatter Module

支持表格、JSON、Markdown等多种输出格式
"""

import json

from rich.console import Console
from rich.json import JSON
from rich.table import Table

console = Console()


class OutputFormatter:
    """输出格式化器"""

    @staticmethod
    def print(data: dict, format: str = "table"):
        """
        智能输出格式化

        根据输出目标自动选择格式:
        - TTY终端: 表格格式
        - 管道: JSON格式
        """
        import sys

        if format == "json":
            console.print(JSON(json.dumps(data, ensure_ascii=False, indent=2)))
        elif format == "markdown":
            OutputFormatter._print_markdown(data)
        elif format == "table" or sys.stdout.isatty():
            OutputFormatter._print_table(data)
        else:
            # 默认JSON（管道）
            console.print(JSON(json.dumps(data, ensure_ascii=False, indent=2)))

    @staticmethod
    def _print_table(data: dict):
        """打印表格格式"""
        if "results" not in data:
            console.print(data)
            return

        table = Table(title=f"📊 {data.get('query', '结果')}")
        table.add_column("ID", style="cyan")
        table.add_column("标题", style="green")
        table.add_column("评分", justify="right", style="yellow")

        for item in data["results"][:10]:  # 最多显示10个
            table.add_row(
                item.get("id", ""),
                item.get("title", "")[:40],
                f"{item.get('score', 0):.2f}",
            )

        console.print(table)

    @staticmethod
    def _print_markdown(data: dict):
        """打印Markdown格式"""
        console.print(f"\n# {data.get('query', '结果')}\n")
        console.print("| ID | 标题 | 评分 |")
        console.print("|----|------|------|")

        for item in data.get("results", [])[:10]:
            console.print(
                f"| {item.get('id', '')} | {item.get('title', '')[:30]} | {item.get('score', 0):.2f} |"
            )
