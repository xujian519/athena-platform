#!/usr/bin/env python3
"""
提示词系统快速启动
Quick Start for Prompt System

用法:
    python quick_start.py demo         # 查看演示
    python quick_start.py test         # 运行测试
    python quick_start.py prompt       # 获取提示词
    python quick_start.py stats        # 查看统计
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from production.services.unified_prompt_loader_v3 import (
    get_prompt,
)


def cmd_demo():
    """演示"""
    from production.scripts.demo_prompt_system import main
    main()


def cmd_test():
    """测试"""
    from production.tests.test_prompt_integration import run_all_tests
    run_all_tests()


def cmd_prompt(task_type: str = "general", complexity: str = "medium", mode: str = "progressive"):
    """获取提示词"""
    prompt = get_prompt(task_type, complexity, mode)
    print(prompt)
    print(f"\n---\nTokens: ~{len(prompt)//4:,}")


def cmd_stats():
    """查看统计"""
    from production.services.unified_prompt_loader_v3 import get_loader

    loader = get_loader()

    # 加载一些提示词来生成统计
    for task in ["general", "patent_writing", "office_action"]:
        loader.load(task, "medium")

    stats = loader.get_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "demo":
        cmd_demo()
    elif cmd == "test":
        cmd_test()
    elif cmd == "prompt":
        task = sys.argv[2] if len(sys.argv) > 2 else "general"
        complexity = sys.argv[3] if len(sys.argv) > 3 else "medium"
        mode = sys.argv[4] if len(sys.argv) > 4 else "progressive"
        cmd_prompt(task, complexity, mode)
    elif cmd == "stats":
        cmd_stats()
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
