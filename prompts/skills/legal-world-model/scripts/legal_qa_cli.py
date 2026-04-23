#!/usr/bin/env python3
"""
法律世界模型命令行客户端
Legal World Model CLI

提供便捷的命令行接口来访问法律世界模型的智能问答能力。

作者: Athena平台团队
版本: v1.0.0
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import requests


class LegalWorldModelClient:
    """法律世界模型客户端"""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        timeout: int = 30,
    ):
        """
        初始化客户端

        Args:
            api_url: API服务地址
            timeout: 请求超时时间(秒)
        """
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.qa_endpoint = f"{self.api_url}/api/v1/qa/ask"
        self.health_endpoint = f"{self.api_url}/health"
        self.stats_endpoint = f"{self.api_url}/api/v1/qa/stats"

    def health_check(self) -> dict[str, Any]:
        """健康检查"""
        try:
            response = requests.get(self.health_endpoint, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def ask(
        self,
        question: str,
        query_type: str = "semantic_qa",
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        提问法律问题

        Args:
            question: 用户问题
            query_type: 查询类型 (statute_query, case_query, semantic_qa, etc.)
            options: 额外查询选项

        Returns:
            问答结果字典
        """
        payload = {"question": question, "query_type": query_type}

        if options:
            payload["options"] = options

        try:
            response = requests.post(
                self.qa_endpoint,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"请求超时(>{self.timeout}秒)",
                "question": question,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "question": question,
            }

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        try:
            response = requests.get(self.stats_endpoint, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def format_answer(self, result: dict[str, Any]) -> str:
        """格式化输出答案"""
        if not result.get("success", True):
            return f"❌ 错误: {result.get('error', '未知错误')}"

        answer = result.get("answer", "无答案")
        confidence = result.get("confidence", 0.0)
        query_intent = result.get("query_intent", {})
        references = result.get("references", [])

        output = []
        output.append(f"📝 答案: {answer}")
        output.append(f"📊 置信度: {confidence:.2%}")

        if query_intent:
            question_type = query_intent.get("question_type", "未知")
            output.append(f"🏷️ 问题类型: {question_type}")

        if references:
            output.append(f"\n📚 参考来源 ({len(references)} 条):")
            for i, ref in enumerate(references[:5], 1):
                content = ref.get("content", "")[:80]
                source = ref.get("source", "未知来源")
                score = ref.get("relevance_score", 0.0)
                output.append(f"  {i}. [{score:.1%}] {source}: {content}...")
            if len(references) > 5:
                output.append(f"  ... 还有 {len(references) - 5} 条参考")

        return "\n".join(output)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Athena法律世界模型命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "question",
        nargs="?",
        help="要询问的法律问题",
    )

    parser.add_argument(
        "-q",
        "--query-type",
        default="semantic_qa",
        choices=[
            "concept",
            "statute_query",
            "case_query",
            "comparison",
            "liability",
            "procedure",
            "creativity",
            "novelty",
            "semantic_qa",
        ],
        help="查询类型",
    )

    parser.add_argument(
        "-u",
        "--api-url",
        default="http://localhost:8000",
        help="API服务地址",
    )

    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=30,
        help="请求超时时间(秒)",
    )

    parser.add_argument(
        "--max-evidence",
        type=int,
        default=10,
        help="最大证据数量",
    )

    parser.add_argument(
        "--target-layers",
        nargs="+",
        choices=["layer1", "layer2", "layer3"],
        help="目标数据层",
    )

    parser.add_argument(
        "--enable-reasoning",
        action="store_true",
        help="启用推理链",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="以JSON格式输出",
    )

    parser.add_argument(
        "--health",
        action="store_true",
        help="执行健康检查",
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="获取统计信息",
    )

    args = parser.parse_args()

    # 初始化客户端
    client = LegalWorldModelClient(api_url=args.api_url, timeout=args.timeout)

    # 健康检查
    if args.health:
        health = client.health_check()
        print(json.dumps(health, ensure_ascii=False, indent=2))
        return 0 if health.get("status") == "healthy" else 1

    # 统计信息
    if args.stats:
        stats = client.get_stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0

    # 问答请求
    if not args.question:
        parser.print_help()
        return 1

    # 构建查询选项
    options = {}
    if args.max_evidence:
        options["max_evidence"] = args.max_evidence
    if args.target_layers:
        options["target_layers"] = args.target_layers
    if args.enable_reasoning:
        options["enable_reasoning"] = True

    # 发起请求
    result = client.ask(
        question=args.question,
        query_type=args.query_type,
        options=options if options else None,
    )

    # 输出结果
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(client.format_answer(result))

    return 0 if result.get("success", True) else 1


if __name__ == "__main__":
    sys.exit(main())
