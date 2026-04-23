#!/usr/bin/env python3
"""
依赖验证脚本
验证Poetry配置的正确性和依赖安装状态
"""

import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple


def run_command(cmd: List[str], description: str = "") -> Tuple[bool, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        success = result.returncode == 0
        return success, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, f"命令超时: {' '.join(cmd)}"
    except Exception as e:
        return False, f"执行错误: {e}"


def check_poetry_installed() -> bool:
    """检查Poetry是否安装"""
    success, output = run_command(["poetry", "--version"], "检查Poetry版本")
    if success:
        print(f"✓ {output.strip()}")
        return True
    print("✗ Poetry未安装")
    return False


def check_pyproject_syntax() -> bool:
    """检查pyproject.toml语法"""
    print("\n检查 pyproject.toml 语法...")
    success, output = run_command(
        ["poetry", "check", "--no-interaction"],
        "检查pyproject.toml"
    )
    if success:
        print("✓ pyproject.toml 语法正确")
        return True
    print(f"✗ 语法错误:\n{output}")
    return False


def check_lock_file() -> bool:
    """检查poetry.lock是否存在"""
    lock_file = Path.cwd() / "poetry.lock"
    if lock_file.exists():
        print("✓ poetry.lock 存在")
        return True
    print("⚠ poetry.lock 不存在，运行 'poetry lock' 生成")
    return False


def get_dependency_stats() -> Dict[str, int]:
    """获取依赖统计信息"""
    stats = {
        "core": 0,
        "dev": 0,
        "groups": 0,
        "extras": 0
    }

    # 获取核心依赖
    success, output = run_command(["poetry", "show", "--no-dev"])
    if success:
        stats["core"] = len([line for line in output.split("\n") if line.strip()])

    # 获取开发依赖
    success, output = run_command(["poetry", "show", "--only", "dev"])
    if success:
        stats["dev"] = len([line for line in output.split("\n") if line.strip()])

    # 读取pyproject.toml获取组和extras
    pyproject = Path.cwd() / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        if "[tool.poetry.group." in content:
            stats["groups"] = content.count("[tool.poetry.group.")
        if "[tool.poetry.extras]" in content:
            # 统计extras中的依赖
            extras_section = content.split("[tool.poetry.extras]")[1].split("\n\n")[0]
            stats["extras"] = extras_section.count('"')

    return stats


def check_version_conflicts() -> bool:
    """检查版本冲突"""
    print("\n检查版本冲突...")
    success, output = run_command(
        ["poetry", "show", "--tree"],
        "显示依赖树"
    )

    if not success:
        print(f"⚠ 无法获取依赖树: {output}")
        return True

    # 检查是否有冲突标记
    has_conflict = "[warning:" in output.lower() or "conflict" in output.lower()
    if has_conflict:
        print("⚠ 发现潜在版本冲突，请检查输出")
        return False

    print("✓ 未发现版本冲突")
    return True


def check_orphaned_files() -> List[str]:
    """检查孤立的requirements.txt文件"""
    print("\n检查孤立的requirements.txt文件...")
    orphaned = []

    requirements_files = [
        "services/xiaonuo-agent-api/requirements.txt",
        "services/tool-registry-api/requirements.txt",
        "services/browser_automation_service/requirements.txt",
        "services/article-writer-service/requirements.txt",
        "deploy/requirements-multimodal.txt",
    ]

    for file_path in requirements_files:
        if (Path.cwd() / file_path).exists():
            orphaned.append(file_path)
            print(f"⚠ 发现孤立文件: {file_path}")

    if not orphaned:
        print("✓ 无孤立requirements.txt文件")

    return orphaned


def verify_imports() -> bool:
    """验证核心模块导入"""
    print("\n验证核心模块导入...")

    test_imports = [
        ("fastapi", "FastAPI"),
        ("uvicorn",),
        ("pydantic", "BaseModel"),
        ("httpx",),
        ("redis",),
        ("loguru", "logger"),
        ("numpy", "array"),
        ("pandas", "DataFrame"),
    ]

    failed = []
    for module_parts in test_imports:
        module = module_parts[0]
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} (未安装)")
            failed.append(module)

    return len(failed) == 0


def main():
    print("=" * 50)
    print("Athena依赖验证脚本")
    print("=" * 50)

    # 检查Poetry
    if not check_poetry_installed():
        print("\n请先安装Poetry: https://python-poetry.org/")
        sys.exit(1)

    # 检查语法
    if not check_pyproject_syntax():
        sys.exit(1)

    # 检查lock文件
    check_lock_file()

    # 依赖统计
    stats = get_dependency_stats()
    print(f"\n依赖统计:")
    print(f"  核心依赖: {stats['core']} 个")
    print(f"  开发依赖: {stats['dev']} 个")
    print(f"  依赖组: {stats['groups']} 个")
    print(f"  可选依赖: {stats['extras']} 个")

    # 检查版本冲突
    check_version_conflicts()

    # 检查孤立文件
    orphaned = check_orphaned_files()
    if orphaned:
        print(f"\n建议运行: ./scripts/cleanup_deps.sh")

    # 尝试验证导入（如果在虚拟环境中）
    try:
        import sys as sys_mod
        if "poetry" in sys_mod.prefix or "venv" in sys_mod.prefix:
            verify_imports()
    except Exception:
        pass

    print("\n" + "=" * 50)
    print("验证完成！")
    print("=" * 50)
    print("\n如需安装依赖，运行:")
    print("  poetry install          # 基础安装")
    print("  poetry install --with dev,browser,automation  # 包含服务和开发依赖")
    print("  poetry install --all-extras  # 包含所有可选依赖")


if __name__ == "__main__":
    main()
