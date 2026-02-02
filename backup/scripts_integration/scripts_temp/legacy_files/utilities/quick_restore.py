#!/usr/bin/env python3
"""
快速恢复工作状态脚本
Quick Restore Script - 帮助爸爸快速恢复到工作状态
"""

import subprocess
import json
from pathlib import Path

def show_progress():
    """显示工作进度"""
    progress_file = Path(__file__).parent.parent / "WORK_PROGRESS.md"
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            print("=== 工作进度存档 ===")
            for i, line in enumerate(f.readlines()[:50], 1):
                if line.strip():
                    print(f"{i:2d}. {line.rstrip()}")
                if i >= 50:
                    print("... (更多内容请查看 WORK_PROGRESS.md)")
                    break

def check_services():
    """检查服务状态"""
    services = [
        ("Athena控制服务", 8001),
        ("诺诺控制中心", 8005),
        ("云熙系统", 8087),
    ]

    print("\n=== 服务状态检查 ===")
    for name, port in services:
        result = subprocess.run(
            f"curl -s http://localhost:{port}/ >/dev/null 2>&1",
            shell=True,
            capture_output=True
        )
        status = "✅ 运行中" if result.returncode == 0 else "❌ 未运行"
        print(f"{name} (端口{port}): {status}")

def show_version():
    """显示版本信息"""
    print("\n=== 版本信息 ===")
    try:
        result = subprocess.run(
            ["python3", "scripts/version_manager.py", "show"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            print(result.stdout)
    except:
        print("版本管理器未找到")

def show_next_tasks():
    """显示下一步任务"""
    print("\n=== 下一步待办任务 ===")
    print("1. 创建自媒体智能体")
    print("   - 支持小红书、知乎、抖音等平台")
    print("   - 内容创作和发布管理")
    print("")
    print("2. 创建商标和版权业务模块")
    print("   - 扩展云熙的IP服务范围")
    print("   - 商标查询和注册管理")
    print("")
    print("3. 创建统一知识库系统")
    print("   - 整合专利、商标、版权知识")
    print("   - AI驱动的知识检索")

def main():
    """主函数"""
    print("🌟 Athena工作平台 - 快速恢复工作状态")
    print("=" * 50)

    # 显示进度摘要
    show_progress()

    # 检查服务状态
    check_services()

    # 显示版本信息
    show_version()

    # 显示下一步任务
    show_next_tasks()

    print("\n" + "=" * 50)
    print("💖 永恒的使命：在行业寒冬中，我们用AI点燃希望的火炬！")

if __name__ == "__main__":
    main()