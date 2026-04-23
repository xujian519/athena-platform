# test basic commands
from typer.testing import CliRunner

from athena_cli.main import app

runner = CliRunner()


def test_search_command():
    """测试检索命令"""
    result = runner.invoke(app, ["search", "patent", "AI专利", "-n", "5"])
    assert result.exit_code == 0
    assert "AI专利" in result.stdout


def test_analyze_command():
    """测试分析命令"""
    result = runner.invoke(app, ["analyze", "creativity", "201921401279.9"])
    assert result.exit_code == 0
    assert "创造性" in result.stdout


def test_batch_analyze_command():
    """测试批量分析命令"""
    result = runner.invoke(app, ["batch", "analyze", "--file", "test_ids.txt"])
    # 会失败因为文件不存在，这是预期的
    assert result.exit_code != 0 or "错误" in result.stdout


def test_config_list():
    """测试配置列表"""
    result = runner.invoke(app, ["config", "list"])
    assert result.exit_code == 0


def test_status_command():
    """测试状态命令"""
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Athena平台状态" in result.stdout
