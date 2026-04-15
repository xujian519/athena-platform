#!/usr/bin/env python3
"""
法律世界模型技能使用示例
Legal World Model Skill Usage Examples

展示如何在Python代码中使用法律世界模型技能。

作者: Athena平台团队
版本: v1.0.0
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from skills.legal_world_model.scripts.legal_qa_cli import LegalWorldModelClient


def example_1_basic_qa():
    """示例1: 基础问答"""
    print("=== 示例1: 基础问答 ===\n")

    client = LegalWorldModelClient()
    result = client.ask(
        question="专利法中关于新颖性的规定是什么？",
        query_type="statute_query"
    )

    print(client.format_answer(result))
    print()


def example_2_case_query():
    """示例2: 案例查询"""
    print("=== 示例2: 案例查询 ===\n")

    client = LegalWorldModelClient()
    result = client.ask(
        question="查找关于等同侵权的相关案例",
        query_type="case_query",
        options={
            "max_evidence": 10,
            "target_layers": ["layer3"]  # 司法案例层
        }
    )

    print(client.format_answer(result))
    print()


def example_3_reasoning_chain():
    """示例3: 启用推理链"""
    print("=== 示例3: 启用推理链 ===\n")

    client = LegalWorldModelClient()
    result = client.ask(
        question="分析这个技术方案是否具备创造性",
        query_type="semantic_qa",
        options={
            "enable_reasoning": True,
            "max_evidence": 15
        }
    )

    print(client.format_answer(result))
    print()


def example_4_json_output():
    """示例4: JSON格式输出"""
    print("=== 示例4: JSON格式输出 ===\n")

    import json

    client = LegalWorldModelClient()
    result = client.ask(
        question="专利复审程序中如何修改权利要求书？"
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()


def example_5_health_check():
    """示例5: 健康检查"""
    print("=== 示例5: 健康检查 ===\n")

    client = LegalWorldModelClient()
    health = client.health_check()

    print(f"服务状态: {health.get('status', 'unknown')}")
    print(f"版本: {health.get('version', 'unknown')}")
    print()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="法律世界模型使用示例")
    parser.add_argument(
        "example",
        nargs="?",
        choices=["1", "2", "3", "4", "5"],
        help="要运行的示例编号"
    )

    args = parser.parse_args()

    if not args.example:
        print("请选择要运行的示例:")
        print("  1 - 基础问答")
        print("  2 - 案例查询")
        print("  3 - 启用推理链")
        print("  4 - JSON格式输出")
        print("  5 - 健康检查")
        print("\n使用方法: python3 examples/usage_examples.py <1-5>")
        return 1

    # 运行选定的示例
    examples = {
        "1": example_1_basic_qa,
        "2": example_2_case_query,
        "3": example_3_reasoning_chain,
        "4": example_4_json_output,
        "5": example_5_health_check,
    }

    example_func = examples[args.example]
    try:
        example_func()
    except Exception as e:
        print(f"运行示例时出错: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
