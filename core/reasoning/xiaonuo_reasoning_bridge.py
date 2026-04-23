#!/usr/bin/env python3
from __future__ import annotations
"""
小诺推理引擎桥接器(新版)
Xiaonuo Reasoning Bridge v2.0

统一入口,支持六步和七步推理框架

作者: 小诺·双鱼座 💖
创建: 2025-12-31
版本: v2.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# 导入推理引擎(直接从具体模块导入避免循环导入)
from core.reasoning.athena_super_reasoning import AthenaSuperReasoningEngine

try:
    from core.reasoning.xiaonuo_six_step_reasoning import (
        ReasoningMode,
        XiaonuoSixStepReasoningEngine,
    )
except ImportError:
    # 如果没有六步引擎,使用超推理引擎作为替代
    try:
        from core.reasoning.athena_multimodal_reasoning_system import ReasoningMode
    except ImportError:
        # 定义一个基本的推理模式枚举
        from enum import Enum

        class ReasoningMode(Enum):
            SEVEN_STEP = "seven_step"
            SIX_STEP = "six_step"

    XiaonuoSixStepReasoningEngine = AthenaSuperReasoningEngine

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class ReasoningRequest:
    """推理请求"""

    problem: str  # 待解决的问题
    mode: str = "seven_step"  # 推理模式: 'six_step' 或 'seven_step'
    context: Optional[dict[str, Any]] = None  # 上下文信息
    session_id: Optional[str] = None  # 会话ID
    user_id: Optional[str] = None  # 用户ID
    timeout: float = 60.0  # 超时时间(秒)


@dataclass
class ReasoningResponse:
    """推理响应"""

    success: bool
    problem: str
    mode: str
    final_synthesis: dict[str, Any]
    reasoning_steps: list[dict[str, Any]]
    execution_time: float
    insights: list[str]
    confidence: float
    error_message: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class XiaonuoReasoningBridge:
    """小诺推理引擎桥接器(统一入口)

    支持两种推理框架:
    - 六步推理 (six_step): 深度分析模式
    - 七步推理 (seven_step): 系统化策略模式
    """

    def __init__(self):
        """初始化桥接器"""
        self.six_step_engine = XiaonuoSixStepReasoningEngine()
        self.seven_step_engine = AthenaSuperReasoningEngine()

        self.request_history: dict[str, list[ReasoningResponse]] = {}

        logger.info("🧠 小诺推理引擎桥接器已初始化(支持六步+七步)")

    async def execute_reasoning(self, request: ReasoningRequest) -> ReasoningResponse:
        """执行推理

        Args:
            request: 推理请求

        Returns:
            推理响应
        """
        start_time = datetime.now()

        try:
            logger.info(f"🚀 执行{request.mode}推理: {request.problem[:50]}...")

            # 根据模式选择引擎
            if request.mode == "six_step":
                engine = self.six_step_engine
            elif request.mode == "seven_step":
                engine = self.seven_step_engine
            else:
                raise ValueError(f"未知的推理模式: {request.mode}")

            # 执行推理
            result = await asyncio.wait_for(
                engine.execute_super_reasoning(problem=request.problem, context=request.context),
                timeout=request.timeout,
            )

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # 构建响应
            response = ReasoningResponse(
                success=True,
                problem=request.problem,
                mode=request.mode,
                final_synthesis=result.get("final_synthesis", {}),
                reasoning_steps=result.get("phase_summary", []),
                execution_time=execution_time,
                insights=result.get("thought_insights", []),
                confidence=result.get("final_synthesis", {}).get("confidence_level", 0.0),
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "session_id": request.session_id,
                    "user_id": request.user_id,
                    "context": request.context,
                },
            )

            # 记录历史
            if request.session_id:
                if request.session_id not in self.request_history:
                    self.request_history[request.session_id] = []
                self.request_history[request.session_id].append(response)

            logger.info(f"✅ {request.mode}推理完成,耗时 {execution_time:.2f}秒")
            return response

        except asyncio.TimeoutError:
            return ReasoningResponse(
                success=False,
                problem=request.problem,
                mode=request.mode,
                final_synthesis={},
                reasoning_steps=[],
                execution_time=request.timeout,
                insights=[],
                confidence=0.0,
                error_message=f"推理超时({request.timeout}秒)",
            )

        except Exception as e:
            return ReasoningResponse(
                success=False,
                problem=request.problem,
                mode=request.mode,
                final_synthesis={},
                reasoning_steps=[],
                execution_time=0.0,
                insights=[],
                confidence=0.0,
                error_message=str(e),
            )

    def get_status(self) -> dict[str, Any]:
        """获取桥接器状态"""
        return {
            "six_step_engine": "initialized",
            "seven_step_engine": "initialized",
            "supported_modes": ["six_step", "seven_step"],
            "total_sessions": len(self.request_history),
            "total_requests": sum(len(h) for h in self.request_history.values()),
        }


# 全局桥接器实例
_bridge_instance: XiaonuoReasoningBridge | None = None


def get_reasoning_bridge() -> XiaonuoReasoningBridge:
    """获取推理桥接器单例"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = XiaonuoReasoningBridge()
    return _bridge_instance


# 便捷函数
async def reason(
    problem: str, mode: str = "seven_step", context: dict | None = None
) -> ReasoningResponse:
    """推理的便捷函数

    Args:
        problem: 待解决的问题
        mode: 推理模式 ('six_step' 或 'seven_step')
        context: 上下文信息

    Returns:
        推理响应
    """
    bridge = get_reasoning_bridge()
    request = ReasoningRequest(problem=problem, mode=mode, context=context)
    return await bridge.execute_reasoning(request)


if __name__ == "__main__":
    # 测试代码
    async def test():
        """测试双推理框架"""
        bridge = get_reasoning_bridge()

        print("=" * 70)
        print("🧠 小诺双推理框架测试")
        print("=" * 70)

        test_problem = "如何提高专利检索的准确率?"

        # 测试六步推理
        print("\n📊 测试六步推理框架\n")
        result_six = await bridge.execute_reasoning(
            ReasoningRequest(
                problem=test_problem, mode="six_step", context={"domain": "patent_law"}
            )
        )

        print(f"✅ 成功: {result_six.success}")
        print(f"📝 结论: {result_six.final_synthesis.get('summary', 'N/A')[:100]}...")
        print(f"💪 置信度: {result_six.confidence:.2f}")
        print(f"⏱️ 耗时: {result_six.execution_time:.2f}秒")

        print("\n" + "=" * 70)

        # 测试七步推理
        print("\n🧪 测试七步推理框架\n")
        result_seven = await bridge.execute_reasoning(
            ReasoningRequest(
                problem=test_problem, mode="seven_step", context={"domain": "patent_law"}
            )
        )

        print(f"✅ 成功: {result_seven.success}")
        print(f"📝 结论: {result_seven.final_synthesis.get('summary', 'N/A')[:100]}...")
        print(f"💪 置信度: {result_seven.confidence:.2f}")
        print(f"⏱️ 耗时: {result_seven.execution_time:.2f}秒")

        print("\n" + "=" * 70)
        print("✅ 双推理框架测试完成")
        print("=" * 70)

    asyncio.run(test())
