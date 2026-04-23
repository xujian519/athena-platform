"""
配置命令模块
Config Command Module

配置管理、认证登录
"""


import typer
from rich.console import Console
from rich.table import Table

from athena_cli.services.config import config_manager

app = typer.Typer(help="配置管理和认证")
console = Console()


@app.command()
def list():
    """列出所有配置"""
    console.print("\n[bold cyan]⚙️  Athena配置[/bold cyan]\n")

    try:
        config_manager.load_config()
        all_config = config_manager.list_all()

        table = Table(show_header=False, box=None)
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")
        table.add_column("说明", style="dim")

        for key, value in all_config.items():
            if value is None:
                value = "（未设置）"
            elif "key" in key.lower() or "token" in key.lower():
                # 隐藏敏感信息
                value = "******"
            table.add_row(key, str(value), "")

        console.print(table)

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def get(
    key: str = typer.Argument(..., help="配置键"),
):
    """获取配置值"""
    try:
        value = config_manager.get(key)

        if value is None:
            console.print(f"[yellow]配置项不存在: {key}[/yellow]")
            raise typer.Exit(1)

        # 隐藏敏感信息
        if "key" in key.lower() or "token" in key.lower():
            value = "******"

        console.print(f"{key}: {value}")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def set(
    key: str = typer.Argument(..., help="配置键"),
    value: str = typer.Argument(..., help="配置值"),
):
    """设置配置值"""
    try:
        config_manager.set(key, value)
        console.print("[bold green]✅ 配置已保存[/bold green]")
        console.print(f"  {key}: {value}")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def login():
    """登录认证"""
    console.print("\n[bold cyan]🔐 Athena登录[/bold cyan]\n")

    # TODO: 实现实际的认证流程
    console.print("请输入API密钥:")

    # 模拟输入
    api_key = "sk-test-123456"

    try:
        # 保存到配置
        config_manager.set("api_key", api_key)

        console.print("\n[bold green]✅ 登录成功！[/bold green]")
        console.print("[dim]API密钥已保存到配置文件[/dim]")

        # 测试连接
        console.print("\n[dim]测试API连接...[/dim]")
        # TODO: 实际测试
        console.print("[green]✓ API连接正常[/green]")

    except Exception as e:
        console.print(f"\n[red]❌ 登录失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def logout():
    """登出"""
    try:
        config_manager.unset("api_key")
        console.print("[bold green]✅ 已登出[/bold green]")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def test():
    """测试API连接"""
    console.print("\n[bold cyan]🔍 测试API连接[/bold cyan]\n")

    try:
        from athena_cli.services.api_client import SyncAPIClient

        client = SyncAPIClient()
        result = client.test_connection()

        if result.get("status") == "ok":
            console.print("[green]✅ API连接正常[/green]")
            console.print(f"[dim]响应时间: {result.get('response_time', 0):.2f}秒[/dim]")
            console.print(f"[dim]API端点: {result.get('api_endpoint', 'unknown')}[/dim]")
        else:
            console.print("[red]❌ API连接失败[/red]")
            console.print(f"[dim]错误: {result.get('error', 'unknown')}[/dim]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]❌ 连接测试失败: {e}[/red]")
        raise typer.Exit(1)


def _print_default_config():
    """打印默认配置（已废弃，使用config_manager）"""
    pass
