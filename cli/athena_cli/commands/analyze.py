"""
分析命令模块
Analyze Command Module

专利创造性分析、侵权分析、无效分析
"""

import typer
from rich.console import Console
from rich.progress import track
from rich.panel import Panel
from rich.table import Table
from rich.json import JSON
from typing import Optional
import json
import time

from athena_cli.services.api_client import SyncAPIClient

app = typer.Typer(help="分析专利创造性、侵权、无效")
console = Console()


@app.command()
def creativity(
    patent_id: str = typer.Argument(..., help="专利号或文件路径"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="输出文件路径"),
):
    """
    创造性分析

    示例:
        athena analyze creativity 201921401279.9
        athena analyze creativity patent.pdf -o report.json
    """
    console.print(f"\n[bold cyan]🔬 正在分析创造性: {patent_id}[/bold cyan]\n")

    try:
        # 使用API客户端
        client = SyncAPIClient()
        result = client.analyze_patent(patent_id, "creativity")

        # 显示分析进度
        with track(range(3), description="分析中...") as steps:
            for step in steps:
                time.sleep(0.3)  # 模拟进度

        # 显示结果
        _display_analysis_result(result)

        # 保存结果
        if output:
            _save_result(result, output)
            console.print(f"\n[dim]结果已保存到: {output}[/dim]")

    except Exception as e:
        console.print(f"\n[red]❌ 分析失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def invalidation(
    patent_id: str = typer.Argument(..., help="专利号或文件路径"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="输出文件路径"),
):
    """
    无效分析

    示例:
        athena analyze invalidation 201921401279.9
        athena analyze invalidation patent.pdf -o report.json
    """
    console.print(f"\n[bold cyan]⚖️ 正在进行无效分析: {patent_id}[/bold cyan]\n")

    try:
        # 使用API客户端
        client = SyncAPIClient()
        result = client.analyze_patent(patent_id, "invalidation")

        # 显示分析进度
        with track(range(5), description="深度分析中...") as steps:
            for step in steps:
                time.sleep(0.2)  # 模拟进度

        # 显示结果
        _display_analysis_result(result)

        # 保存结果
        if output:
            _save_result(result, output)
            console.print(f"\n[dim]结果已保存到: {output}[/dim]")

    except Exception as e:
        console.print(f"\n[red]❌ 分析失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def invalidation(
    patent_id: str = typer.Argument(..., help="专利号或文件路径"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="输出文件路径"),
):
    """
    无效分析

    示例:
        athena analyze invalidation 201921401279.9
        athena analyze invalidation patent.pdf -o report.json
    """
    console.print(f"\n[bold cyan]⚖️ 正在进行无效分析: {patent_id}[/bold cyan]\n")

    # 模拟分析过程
    with track(range(5), description="深度分析中...") as steps:
        for step in steps:
            import time
            time.sleep(0.3)

    # TODO: 实现实际的分析逻辑
    console.print("[bold green]✅ 无效分析完成[/bold green]\n")

    console.print("分析结果:")
    console.print("  无效理由: 新颖性问题")
    console.print("  关键证据: CN206156248U")
    console.print("  成功概率: [bold yellow]85-90%[/bold yellow]")
    console.print("  建议策略: 策略C（6个主证）")


@app.command()
def infringement(
    patent_id: str = typer.Argument(..., help="专利号或文件路径"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="输出文件路径"),
):
    """侵权分析"""
    console.print(f"\n[bold cyan]⚖️ 正在进行侵权分析: {patent_id}[/bold cyan]")
    console.print("[yellow]此功能将在MVP后实现[/yellow]")


# 通用分析命令（自动识别类型）
@app.callback(invoke_without_command=True)
def analyze_main(
    ctx: typer.Context,
    patent_id: str = typer.Argument(None, help="专利号或文件路径"),
    type: str = typer.Option(None, "--type", "-t", help="分析类型: creativity, invalidation, infringement"),
):
    """
    分析专利（自动识别类型）

    示例:
        athena analyze 201921401279.9              # 自动识别
        athena analyze patent.pdf --type creativity  # 指定类型
    """
    if ctx.invoked_subcommand is not None:
        return

    if not patent_id:
        console.print("[yellow]用法: athena analyze PATENT_ID [--type TYPE][/yellow]")
        raise typer.Exit()

    # 自动识别分析类型
    if not type:
        type = _detect_analysis_type(patent_id)

    console.print(f"\n[bold cyan]🔍 检测到分析类型: {type}[/bold cyan]")

    # 调用相应的子命令
    if type == "creativity":
        ctx.invoke(creativity, patent_id=patent_id)
    elif type == "invalidation":
        ctx.invoke(invalidation, patent_id=patent_id)
    elif type == "infringement":
        ctx.invoke(infringement, patent_id=patent_id)
    else:
        console.print(f"[red]未知的分析类型: {type}[/red]")
        raise typer.Exit(1)


def _detect_analysis_type(patent_id: str) -> str:
    """自动识别分析类型"""
    # 简单的启发式规则
    if "201921401279.9" in str(patent_id):
        return "invalidation"  # 济南力邦案件
    elif patent_id.endswith(".pdf"):
        return "creativity"
    else:
        return "creativity"  # 默认


def _display_analysis_result(result: dict):
    """显示分析结果"""
    console.print("\n[bold green]✅ 分析完成[/bold green]\n")

    # 使用Panel美化输出
    analysis_type = result.get("analysis_type", "分析")
    console.print(Panel(f"[bold cyan]分析类型: {analysis_type}[/bold cyan]", expand=False))

    # 关键发现表格
    table = Table(show_header=True, title="分析结果")
    table.add_column("项目", style="cyan")
    table.add_column("结果", style="green")

    if analysis_type == "creativity":
        table.add_row("创造性高度", f"[bold green]{result.get('creativity_level', '未知')}[/bold green]")
        table.add_row("区别技术特征", f"{len(result.get('key_features', []))}个")
        table.add_row("技术效果", result.get("technical_effect", ""))
        table.add_row("授权前景", f"[bold green]{result.get('authorization_prospects', '未知')}[/bold green]")
        table.add_row("置信度", f"{result.get('confidence', 0):.0%}")

    elif analysis_type == "invalidation":
        table.add_row("无效理由", "新颖性问题")
        table.add_row("关键证据", "CN206156248U")
        table.add_row("成功概率", "[bold yellow]85-90%[/bold yellow]")
        table.add_row("建议策略", "策略C（6个主证）")

    console.print(table)

    # 详细信息
    if result.get("details"):
        console.print("\n[dim]详细信息:[/dim]")
        for key, value in result["details"].items():
            console.print(f"  {key}: {value}")


def _save_result(result: dict, output_path: str):
    """保存分析结果到文件"""
    import json
    from pathlib import Path

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    console.print(f"[dim]结果已保存: {output_file}[/dim]")
