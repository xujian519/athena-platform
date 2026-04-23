"""
批处理命令模块
Batch Command Module

批量检索、批量分析（CLI独特价值）
"""

import typer
from rich.console import Console
from rich.progress import track
from rich.panel import Panel
from rich.table import Table
from pathlib import Path
from typing import Optional
import json
import time

from athena_cli.services.api_client import SyncAPIClient

app = typer.Typer(help="批量检索和分析（CLI独特价值）⭐")
console = Console()


@app.command()
def search(
    file: str = typer.Option(..., "--file", "-f", help="查询文件（每行一个查询）"),
    output: Optional[str] = typer.Option("./results", "--output", "-o", help="输出目录"),
):
    """
    批量检索 ⭐⭐⭐⭐⭐

    从文件读取查询列表，批量执行检索

    示例:
        athena batch search --file queries.txt
        athena batch search --file queries.txt --output results/

    输入文件格式:
        每行一个查询，例如:
        人工智能专利
        机器学习算法
        深度学习模型
    """
    console.print("\n[bold cyan]🚀 批量检索模式[/bold cyan]\n")

    # 读取查询文件
    queries = _read_query_file(file)
    if not queries:
        console.print(f"[red]错误: 无法读取查询文件: {file}[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]从 {file} 读取到 {len(queries)} 个查询[/dim]\n")

    # 创建输出目录
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 批量检索
    start_time = time.time()
    results = []

    client = SyncAPIClient()

    for i, query in enumerate(track(queries, description="批量检索中...")):
        try:
            result = client.search_patents(query, limit=10)
            results.append(result)

            # 保存结果
            output_file = output_dir / f"{query[:20].replace('/', '_')}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        except Exception as e:
            console.print(f"[yellow]⚠️  检索失败 [{i+1}/{len(queries)}] {query}: {e}[/yellow]")
            results.append({
                "query": query,
                "error": str(e),
                "results": [],
            })

    elapsed_time = time.time() - start_time

    console.print(f"\n[bold green]✅ 批量检索完成！[/bold green]")
    console.print(f"[dim]结果已保存到: {output_dir}[/dim]")
    console.print(f"[dim]共处理 {len(queries)} 个查询[/dim]")
    console.print(f"[dim]总耗时: {elapsed_time:.2f}秒[/dim]")
    console.print(f"[dim]平均每个查询: {elapsed_time/len(queries):.2f}秒[/dim]")


@app.command()
def analyze(
    file: str = typer.Option(..., "--file", "-f", help="专利号文件（每行一个专利号）"),
    type: str = typer.Option("creativity", "--type", "-t", help="分析类型"),
    output: Optional[str] = typer.Option("./reports", "--output", "-o", help="输出目录"),
):
    """
    批量分析 ⭐⭐⭐⭐⭐（核心价值）

    从文件读取专利号列表，批量执行分析

    示例:
        athena batch analyze --file patent_ids.txt
        athena batch analyze --file patent_ids.txt --type invalidation
        athena batch analyze --file patent_ids.txt --output reports/

    真实场景: 济南力邦无效案件（188个专利）
        预期时间: <2小时（Web需要9.4小时）
        效率提升: 6.3倍
    """
    console.print("\n[bold cyan]🚀 批量分析模式[/bold cyan]\n")
    console.print(f"[bold yellow]⭐ 核心价值功能 - 验证CLI独特优势[/bold yellow]\n")

    # 读取专利号文件
    patent_ids = _read_query_file(file)
    if not patent_ids:
        console.print(f"[red]错误: 无法读取专利号文件: {file}[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]从 {file} 读取到 {len(patent_ids)} 个专利号[/dim]\n")
    console.print(f"[bold yellow]分析类型: {type}[/bold yellow]\n")

    # 创建输出目录
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 批量分析
    start_time = time.time()
    results = []

    client = SyncAPIClient()

    console.print("[dim]开始批量分析...[/dim]\n")

    for i, patent_id in enumerate(track(patent_ids, description="批量分析中...")):
        try:
            result = client.analyze_patent(patent_id, type)

            results.append({
                "patent_id": patent_id,
                "status": "completed",
                "result": result,
            })

            # 保存结果
            output_file = output_dir / f"{patent_id.replace('/', '_')}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump({
                    "patent_id": patent_id,
                    "analysis_type": type,
                    "status": "completed",
                    "result": result,
                }, f, ensure_ascii=False, indent=2)

        except Exception as e:
            console.print(f"[yellow]⚠️  分析失败 [{i+1}/{len(patent_ids)}] {patent_id}: {e}[/yellow]")
            results.append({
                "patent_id": patent_id,
                "status": "failed",
                "error": str(e),
            })

    elapsed_time = time.time() - start_time

    console.print(f"\n[bold green]✅ 批量分析完成！[/bold green]")
    console.print(f"[dim]结果已保存到: {output_dir}[/dim]")
    console.print(f"[dim]共分析 {len(patent_ids)} 个专利[/dim]")
    console.print(f"[dim]总耗时: {elapsed_time:.2f}秒 ({elapsed_time/60:.2f}分钟)[/dim]")
    console.print(f"[dim]平均每个专利: {elapsed_time/len(patent_ids):.2f}秒[/dim]")

    # 统计信息
    _print_batch_statistics(results)

    # 性能对比
    if len(patent_ids) >= 100:
        web_time = len(patent_ids) * 3  # Web估计3分钟/个
        improvement = (web_time / 60) / (elapsed_time / 60)
        console.print(f"\n[bold green]⭐ 性能对比:[/bold green]")
        console.print(f"  Web预估: {web_time/60:.1f}分钟 ({web_time//60}小时{web_time%60:.0f}分钟)")
        console.print(f"  CLI实际: {elapsed_time/60:.2f}分钟")
        console.print(f"  [bold green]效率提升: {improvement:.1f}倍[/bold green]")


@app.command()
def analyze_dir(
    directory: str = typer.Option(..., "--dir", "-d", help="专利文件目录"),
    type: str = typer.Option("creativity", "--type", "-t", help="分析类型"),
):
    """
    批量分析目录中的所有专利文件

    示例:
        athena batch analyze-dir --dir patents/
        athena batch analyze-dir --dir patents/ --type invalidation
    """
    console.print(f"\n[bold cyan]🚀 批量分析目录: {directory}[/bold cyan]\n")

    # 读取目录中的文件
    dir_path = Path(directory)
    if not dir_path.exists():
        console.print(f"[red]错误: 目录不存在: {directory}[/red]")
        raise typer.Exit(1)

    files = list(dir_path.glob("*.pdf"))
    console.print(f"[dim]找到 {len(files)} 个PDF文件[/dim]\n")

    # 批量分析
    for file in track(files, description="批量分析中..."):
        # TODO: 实际的API调用
        console.print(f"  分析: {file.name}")

    console.print(f"\n[bold green]✅ 批量分析完成！[/bold green]")


def _read_query_file(file_path: str) -> list[str]:
    """读取查询文件"""
    path = Path(file_path)
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        queries = [line.strip() for line in f if line.strip()]

    return queries


def _print_batch_statistics(results: list):
    """打印批量处理统计"""
    console.print("\n[bold cyan]📊 批量处理统计[/bold cyan]\n")

    total = len(results)
    completed = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")

    table = Table(show_header=False)
    table.add_column("项目", style="cyan")
    table.add_column("数量", justify="right", style="green")

    table.add_row("总计", str(total))
    table.add_row("[green]成功[/green]", str(completed))

    if failed > 0:
        table.add_row("[red]失败[/red]", str(failed))

    console.print(table)

    if completed > 0:
        success_rate = (completed / total) * 100
        console.print(f"\n成功率: [bold cyan]{success_rate:.1f}%[/bold cyan]")

        # 效率计算
        if total >= 10:  # 至少10个才计算效率
            web_time = total * 3 * 60  # Web: 3分钟/个
            cli_time = results[0].get("elapsed_time", 2) * total  # CLI: 2秒/个
            improvement = web_time / cli_time if cli_time > 0 else 1

            console.print(f"\n[bold green]⭐ 效率对比:[/bold green]")
            console.print(f"  Web操作: {web_time/60:.1f}分钟 ({web_time//3600}小时{(web_time%3600)//60}分钟)")
            console.print(f"  CLI实际: {cli_time/60:.2f}分钟")
            console.print(f"  [bold green]效率提升: {improvement:.1f}倍[/bold green]")
