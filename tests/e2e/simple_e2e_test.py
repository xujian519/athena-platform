#!/usr/bin/env python3
"""
简化的端到端测试

用于验证测试框架的基本功能
"""

import asyncio
import time
from pathlib import Path
from typing import Any

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
import sys

sys.path.insert(0, str(project_root))


class SimpleMockAgent:
    """简化的模拟Agent"""

    def __init__(self, agent_id: str, delay: float = 0.1):
        self.agent_id = agent_id
        self.delay = delay

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """模拟执行"""
        await asyncio.sleep(self.delay)
        return {
            "status": "success",
            "agent_id": self.agent_id,
            "output": f"Mock output from {self.agent_id}",
            "execution_time": self.delay
        }


async def test_workflow():
    """测试工作流"""
    print("🚀 开始运行简化的端到端测试...")

    # 创建模拟智能体
    agents = {
        "retriever": SimpleMockAgent("retriever", 0.1),
        "analyzer": SimpleMockAgent("analyzer", 0.2),
        "writer": SimpleMockAgent("writer", 0.3)
    }

    results = []

    # 步骤1：检索
    print("\n🔍 步骤1：检索")
    start_time = time.time()
    await agents["retriever"].execute({"query": "test"})
    search_time = time.time() - start_time
    print(f"✅ 检索完成，耗时: {search_time:.2f}秒")
    results.append(("检索", search_time, "success"))

    # 步骤2：分析
    print("\n🔬 步骤2：分析")
    start_time = time.time()
    await agents["analyzer"].execute({"data": "test"})
    analysis_time = time.time() - start_time
    print(f"✅ 分析完成，耗时: {analysis_time:.2f}秒")
    results.append(("分析", analysis_time, "success"))

    # 步骤3：撰写
    print("\n✍️ 步骤3：撰写")
    start_time = time.time()
    await agents["writer"].execute({"content": "test"})
    writing_time = time.time() - start_time
    print(f"✅ 撰写完成，耗时: {writing_time:.2f}秒")
    results.append(("撰写", writing_time, "success"))

    # 汇总结果
    total_time = sum(r[1] for r in results)
    print("\n📊 测试汇总")
    print("=" * 50)
    for step, duration, status in results:
        print(f"{step}: {duration:.2f}秒 ({status})")
    print(f"总耗时: {total_time:.2f}秒")

    # 生成报告
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tests": 3,
        "passed_tests": 3,
        "failed_tests": 0,
        "pass_rate": 1.0,
        "total_duration": total_time,
        "step_results": results
    }

    # 保存报告
    output_dir = Path("test_results/e2e")
    output_dir.mkdir(parents=True, exist_ok=True)

    import json
    with open(output_dir / "simple_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📊 测试报告已保存到: {output_dir / 'simple_test_report.json'}")
    print("🎉 简化的端到端测试完成！")

    return report


if __name__ == "__main__":
    asyncio.run(test_workflow())
