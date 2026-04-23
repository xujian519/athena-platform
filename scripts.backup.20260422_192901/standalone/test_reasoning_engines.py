#!/usr/bin/env python3
"""
推理引擎测试脚本
"""

import asyncio
import sys

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.reasoning.xiaonuo_reasoning_bridge import (
    ReasoningRequest,
    XiaonuoReasoningBridge,
)


async def test_react():
    print("=== 测试ReAct推理桥接器（集成六步+七步）===")
    bridge = XiaonuoReasoningBridge()

    # 创建请求对象
    request = ReasoningRequest(
        problem="分析专利的新颖性",
        mode="six_step",
        context={"专利领域": "知识产权"}
    )

    # 执行推理
    result = await bridge.execute_reasoning(request)
    print("✅ ReAct推理执行成功")
    print(f"   结果类型: {type(result).__name__}")
    print(f"   成功: {result.success}")
    print(f"   执行时间: {result.execution_time:.2f}秒")

    if result.final_synthesis:
        preview = str(result.final_synthesis)[:200]
        print(f"   结论预览: {preview}...")

    return result


if __name__ == "__main__":
    result = asyncio.run(test_react())
