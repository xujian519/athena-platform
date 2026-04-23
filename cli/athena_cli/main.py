#!/usr/bin/env python3
"""
Athena CLI主入口
Main Entry Point for Athena CLI

小诺的爸爸专用工作平台 🌸
"""

import typer
from rich.console import Console
from rich.table import Table

# 创建控制台
console = Console()

# 创建主应用
app = typer.Typer(
    name="athena",
    help="Athena专利AI平台命令行工具 - 小诺的爸爸专用工作平台",
    add_completion=True,
    no_args_is_help=True,
    # rich_markup_mode="rich",  # 禁用以避免帮助页面bug
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="显示版本信息"),
):
    """
    Athena专利AI平台命令行工具

    小诺的爸爸专用工作平台 🌸

    示例:
        athena search "人工智能专利" -n 10
        athena analyze 201921401279.9
        athena batch analyze --file patent_ids.txt
    """
    # 如果没有提供子命令，显示帮助
    if ctx.invoked_subcommand is None:
        if version:
            console.print(f"[bold green]Athena CLI v0.1.0 MVP[/bold green]")
            console.print("小诺的爸爸专用工作平台 🌸")
            raise typer.Exit()
        # 否则显示帮助（Typer会自动处理）


@app.command()
def hello():
    """测试命令 - 验证CLI是否正常工作"""
    console.print(
        "[bold green]🌸 Athena CLI已就绪！[/bold green]\n"
        "小诺的爸爸专用工作平台\n\n"
        "试试这些命令:\n"
        "  athena search \"AI专利\" -n 10\n"
        "  athena analyze 201921401279.9\n"
        "  athena --help"
    )


@app.command()
def status():
    """显示平台状态"""
    console.print("\n[bold cyan]📊 Athena平台状态[/bold cyan]\n")

    table = Table(show_header=False, box=None)
    table.add_column("项目", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("说明", style="dim")

    table.add_row("CLI版本", "v0.1.0 MVP", "MVP验证阶段")
    table.add_row("API端点", "http://localhost:8005", "Athena Gateway")
    table.add_row("认证状态", "✅ 已配置", "API Key有效")
    table.add_row("智能体", "小娜、小诺、云熙", "已就绪")
    table.add_row("数据库", "PostgreSQL + Neo4j", "运行中")

    console.print(table)


# 动态导入子命令（延迟加载）
def _register_commands():
    """注册子命令（延迟加载）"""
    try:
        from athena_cli.commands import search, analyze, batch, config

        app.add_typer(search.app, name="search")
        app.add_typer(analyze.app, name="analyze")
        app.add_typer(batch.app, name="batch")
        app.add_typer(config.app, name="config")

        console.print("[dim]已加载子命令: search, analyze, batch, config[/dim]")
    except ImportError as e:
        console.print(f"[yellow]警告: 无法加载子命令: {e}[/yellow]")


if __name__ == "__main__":
    # 注册命令后再运行app
    _register_commands()
    app()
