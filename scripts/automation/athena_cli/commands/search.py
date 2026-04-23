"""
检索命令模块
Search Command Module

专利检索、文献检索、案例检索
"""


import typer
from rich.console import Console
from rich.table import Table

from athena_cli.services.api_client import SyncAPIClient

app = typer.Typer(help="检索专利、文献和案例")
console = Console()


@app.command()
def patent(
    query: str = typer.Argument(..., help="搜索查询字符串"),
    limit: int = typer.Option(10, "-n", "--limit", help="结果数量（默认: 10）"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json, markdown"),
):
    """
    检索专利

    示例:
        athena search patent "人工智能专利" -n 10
        athena search patent "机器学习" --format json
    """
    console.print(f"\n[bold cyan]🔍 正在检索专利: {query}[/bold cyan]\n")

    try:
        # 使用API客户端
        client = SyncAPIClient()
        results = client.search_patents(query, limit)

        # 显示结果
        if format == "json":
            import json
            console.print_json(json.dumps(results, ensure_ascii=False, indent=2))
        elif format == "markdown":
            _print_markdown(results)
        else:  # table
            _print_table(results)

        console.print(f"\n[dim]✓ 检索完成，耗时: {results.get('search_time', 0):.2f}秒[/dim]")

    except Exception as e:
        console.print(f"\n[red]❌ 检索失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def literature(
    query: str = typer.Argument(..., help="搜索查询字符串"),
    limit: int = typer.Option(10, "-n", "--limit", help="结果数量"),
):
    """检索学术文献"""
    console.print(f"\n[bold cyan]📚 正在检索文献: {query}[/bold cyan]")
    console.print("[yellow]此功能将在MVP后实现[/yellow]")


@app.command()
def case(
    query: str = typer.Argument(..., help="搜索查询字符串"),
    limit: int = typer.Option(10, "-n", "--limit", help="结果数量"),
):
    """检索法律案例"""
    console.print(f"\n[bold cyan]⚖️ 正在检索案例: {query}[/bold cyan]")
    console.print("[yellow]此功能将在MVP后实现[/yellow]")


def _mock_search_results(query: str, limit: int) -> dict:
    """模拟搜索结果（MVP阶段）"""
    return {
        "query": query,
        "total": limit,
        "results": [
            {
                "id": f"CN{1000+i}A",
                "title": f"{query}相关专利 - 实施例{i}",
                "applicant": "广东冠一机械科技有限公司",
                "date": "2024-01-01",
                "score": 0.95 - i * 0.05,
            }
            for i in range(min(limit, 5))
        ],
    }


def _print_table(results: dict):
    """打印表格格式结果"""
    table = Table(title=f"📊 检索结果: {results['query']}")
    table.add_column("专利号", style="cyan", no_wrap=False)
    table.add_column("标题", style="green")
    table.add_column("申请人", style="blue")
    table.add_column("日期", style="yellow")
    table.add_column("评分", justify="right", style="red")

    for r in results["results"]:
        table.add_row(
            r["id"],
            r["title"][:40] + "..." if len(r["title"]) > 40 else r["title"],
            r["applicant"],
            r["date"],
            f"{r['score']:.2f}",
        )

    console.print(table)
    console.print(f"\n[dim]共找到 {results['total']} 个结果[/dim]")


def _print_markdown(results: dict):
    """打印Markdown格式结果"""
    console.print(f"\n# 检索结果: {results['query']}\n")
    console.print("| 专利号 | 标题 | 申请人 | 日期 | 评分 |")
    console.print("|--------|------|--------|------|------|")

    for r in results["results"]:
        console.print(
            f"| {r['id']} | {r['title'][:30]} | {r['applicant']} | {r['date']} | {r['score']:.2f} |"
        )
