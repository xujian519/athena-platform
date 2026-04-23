#!/usr/bin/env python3
from __future__ import annotations
"""
学习增强对话管理器
Learning-Enhanced Dialog Manager

为Athena平台对话系统集成P0-P2学习引擎:
- P0: 自主学习 - 对话性能监控
- P1: 在线学习 - 从用户反馈中学习
- P2: 强化学习 - 优化对话策略

作者: Athena AI Team
版本: 1.0.0
创建: 2026-01-29
"""

import asyncio

# 添加项目路径
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import setup_logging
from production.core.learning import (
    ModuleType,
    OptimizationReport,
    # 公共工具函数（v2.1新增）
    epsilon_greedy_select,
    get_learning_interface,
    get_q_values_from_orchestrator,
)

logger = setup_logging()


# =============================================================================
# 枚举和数据结构
# =============================================================================

class DialogState(Enum):
    """对话状态"""
    GREETING = "greeting"                # 问候
    UNDERSTANDING = "understanding"      # 理解需求
    CLARIFYING = "clarifying"            # 澄清
    RESPONDING = "responding"            # 回应
    FOLLOW_UP = "follow_up"              # 追问
    CLOSING = "closing"                  # 结束


class ResponseStrategy(Enum):
    """回应策略"""
    DIRECT = "direct"                    # 直接回答
    CLARIFY = "clarify"                  # 澄清询问
    SUGGEST = "suggest"                  # 建议引导
    BREAK_DOWN = "break_down"            # 分解问题
    EXAMPLE = "example"                  # 举例说明
    CONFIRM = "confirm"                  # 确认理解
    PROACTIVE = "proactive"              # 主动提供建议


@dataclass
class DialogTurn:
    """对话轮次"""
    turn_id: str
    timestamp: datetime
    user_message: str
    dialog_state: DialogState
    response_strategy: ResponseStrategy
    assistant_response: str
    confidence: float
    user_satisfaction: Optional[float] = None
    user_feedback: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "timestamp": self.timestamp.isoformat(),
            "user_message": self.user_message,
            "dialog_state": self.dialog_state.value,
            "response_strategy": self.response_strategy.value,
            "assistant_response": self.assistant_response,
            "confidence": self.confidence,
            "user_satisfaction": self.user_satisfaction,
            "user_feedback": self.user_feedback,
        }


@dataclass
class DialogContext:
    """对话上下文"""
    session_id: str
    user_id: Optional[str]
    start_time: datetime
    topic: Optional[str] = None
    history: list[DialogTurn] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_turn(self, turn: DialogTurn):
        """添加对话轮次"""
        self.history.append(turn)


@dataclass
class DialogResponse:
    """对话响应"""
    response_text: str
    strategy_used: ResponseStrategy
    confidence: float
    dialog_state: DialogState
    reasoning: str
    should_clarify: bool = False
    suggested_actions: list[str] = field(default_factory=list)


# =============================================================================
# 学习增强对话管理器
# =============================================================================

class LearningDialogManager:
    """
    学习增强对话管理器

    从对话历史中学习，优化对话策略和回应质量
    """

    def __init__(
        self,
        enable_learning: bool = True,
        auto_optimize: bool = True,
    ):
        """
        初始化学习增强对话管理器

        Args:
            enable_learning: 是否启用学习引擎
            auto_optimize: 是否自动优化
        """
        self.enable_learning = enable_learning
        self.auto_optimize = auto_optimize

        # 学习接口
        self.learning_interface: Any | None = None

        # 对话历史
        self.dialog_sessions: dict[str, DialogContext] = {}

        # 策略性能统计
        self.strategy_stats: dict[str, dict[str, Any]] = {
            strategy.value: {
                "total_uses": 0,
                "successes": 0,
                "avg_satisfaction": 0.0,
                "avg_reward": 0.0,
            }
            for strategy in ResponseStrategy
        }

        # 初始化
        if enable_learning:
            self._initialize_learning()

        logger.info(
            f"💬 学习增强对话管理器初始化完成 "
            f"(学习: {'✅' if enable_learning else '❌'})"
        )

    def _initialize_learning(self):
        """初始化学习引擎"""
        try:
            self.learning_interface = get_learning_interface(
                module_type=ModuleType.DIALOG,
                module_id="learning_dialog_manager",
                enable_p0=True,  # 性能监控
                enable_p1=True,  # 在线学习
                enable_p2=True,  # 强化学习
            )
            logger.info("✅ 学习引擎已启动")
        except Exception as e:
            logger.warning(f"⚠️ 学习引擎初始化失败: {e}")
            self.enable_learning = False

    # ==============================================================================
    # 核心功能: 智能对话管理
    # ==============================================================================

    async def process_message(
        self,
        user_message: str,
        session_id: str,
        user_id: Optional[str] = None,
        use_learning: bool = True,
    ) -> DialogResponse:
        """
        处理用户消息（带学习）

        Args:
            user_message: 用户消息
            session_id: 会话ID
            user_id: 用户ID
            use_learning: 是否使用学习引擎

        Returns:
            DialogResponse: 对话响应
        """
        # 获取或创建对话上下文
        context = self._get_or_create_context(session_id, user_id)

        # 1. 分析对话状态
        dialog_state = await self._analyze_dialog_state(user_message, context)

        # 2. 选择回应策略
        if use_learning and self.enable_learning:
            strategy, confidence, reasoning = await self._learned_strategy_selection(
                user_message, dialog_state, context
            )
        else:
            strategy, confidence, reasoning = self._default_strategy_selection(
                user_message, dialog_state
            )

        # 3. 生成回应（模拟）
        response_text = await self._generate_response(
            user_message, strategy, dialog_state
        )

        # 4. 构建响应
        response = DialogResponse(
            response_text=response_text,
            strategy_used=strategy,
            confidence=confidence,
            dialog_state=dialog_state,
            reasoning=reasoning,
            should_clarify=strategy == ResponseStrategy.CLARIFY,
            suggested_actions=self._generate_suggested_actions(strategy),
        )

        # 5. 记录对话轮次
        turn = DialogTurn(
            turn_id=f"{session_id}_{len(context.history)}",
            timestamp=datetime.now(),
            user_message=user_message,
            dialog_state=dialog_state,
            response_strategy=strategy,
            assistant_response=response_text,
            confidence=confidence,
        )
        context.add_turn(turn)

        return response

    async def _analyze_dialog_state(
        self,
        user_message: str,
        context: DialogContext,
    ) -> DialogState:
        """分析对话状态"""
        # 简单的状态分析逻辑
        if len(context.history) == 0:
            return DialogState.GREETING

        context.history[-1]

        # 如果用户在询问细节
        if any(keyword in user_message for keyword in ["什么", "如何", "怎么", "为什么"]):
            return DialogState.UNDERSTANDING

        # 如果用户表示困惑
        if any(keyword in user_message for keyword in ["不懂", "不明白", "什么意思"]):
            return DialogState.CLARIFYING

        # 如果用户在确认或感谢
        if any(keyword in user_message for keyword in ["好的", "谢谢", "明白了"]):
            return DialogState.FOLLOW_UP

        return DialogState.RESPONDING

    async def _learned_strategy_selection(
        self,
        user_message: str,
        dialog_state: DialogState,
        context: DialogContext,
    ) -> tuple[ResponseStrategy, float, str]:
        """使用学习引擎选择策略（使用公共工具函数v2.1）"""

        # 构建状态
        state = f"dialog_{dialog_state.value}"
        strategy_options = [s.value for s in ResponseStrategy]

        # 使用公共工具函数获取Q值（v2.1改进：使用get_q_values_from_orchestrator）
        q_values = get_q_values_from_orchestrator(
            self.learning_interface,
            state,
            strategy_options
        )

        # 使用公共工具函数进行ε-贪婪选择（v2.1改进：使用epsilon_greedy_select）
        selected_value, confidence = epsilon_greedy_select(
            options=strategy_options,
            q_values=q_values,
            epsilon=0.1
        )

        selected = ResponseStrategy(selected_value)

        # 生成选择原因
        max_q = q_values.get(selected_value, 0.0)
        if max_q > 0:
            reasoning = f"基于Q值选择（Q={max_q:.3f}）"
        else:
            reasoning = "探索性选择（ε-贪婪策略）"

        # 记录选择经验
        if self.enable_learning:
            await self.learning_interface.record_experience(
                context={
                    "user_message": user_message,
                    "dialog_state": dialog_state.value,
                    "turn_in_session": len(context.history),
                },
                action=selected.value,
                result={"strategy": selected.value},
                state=state,
                confidence=confidence,
            )

        return selected, confidence, reasoning

    async def _default_strategy_selection(
        self,
        user_message: str,
        dialog_state: DialogState,
    ) -> tuple[ResponseStrategy, float, str]:
        """默认策略选择"""
        # 基于对话状态选择策略
        strategy_map = {
            DialogState.GREETING: ResponseStrategy.DIRECT,
            DialogState.UNDERSTANDING: ResponseStrategy.CLARIFY,
            DialogState.CLARIFYING: ResponseStrategy.EXAMPLE,
            DialogState.RESPONDING: ResponseStrategy.DIRECT,
            DialogState.FOLLOW_UP: ResponseStrategy.PROACTIVE,
            DialogState.CLOSING: ResponseStrategy.CONFIRM,
        }

        strategy = strategy_map.get(dialog_state, ResponseStrategy.DIRECT)
        confidence = 0.7
        reasoning = f"基于对话状态选择（{dialog_state.value}）"

        return strategy, confidence, reasoning

    async def _generate_response(
        self,
        user_message: str,
        strategy: ResponseStrategy,
        dialog_state: DialogState,
    ) -> str:
        """生成回应（模拟）"""
        # 这里应该调用实际的LLM生成回应
        # 为了演示，我们返回模拟回应

        responses = {
            ResponseStrategy.DIRECT: f"根据您的问题'{user_message}'，我来直接回答...",
            ResponseStrategy.CLARIFY: f"关于'{user_message}'，我想先确认一下您的具体需求是...",
            ResponseStrategy.SUGGEST: f"对于'{user_message}'，我建议您可以...",
            ResponseStrategy.BREAK_DOWN: f"让我把'{user_message}'这个问题分解一下...",
            ResponseStrategy.EXAMPLE: f"举个例子来说明'{user_message}'...",
            ResponseStrategy.CONFIRM: f"所以我理解您的问题是'{user_message}'，对吗？",
            ResponseStrategy.PROACTIVE: f"关于'{user_message}'，我还想提醒您...",
        }

        return responses.get(strategy, f"我理解了'{user_message}'")

    def _generate_suggested_actions(
        self,
        strategy: ResponseStrategy,
    ) -> list[str]:
        """生成建议操作"""
        actions_map = {
            ResponseStrategy.CLARIFY: ["提供更多细节", "举例说明"],
            ResponseStrategy.SUGGEST: ["执行建议", "了解更多"],
            ResponseStrategy.BREAK_DOWN: ["逐步执行", "查看整体方案"],
        }

        return actions_map.get(strategy, [])

    def _get_or_create_context(
        self,
        session_id: str,
        user_id: Optional[str],
    ) -> DialogContext:
        """获取或创建对话上下文"""
        if session_id not in self.dialog_sessions:
            self.dialog_sessions[session_id] = DialogContext(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(),
            )
        return self.dialog_sessions[session_id]

    # ==============================================================================
    # 学习接口: 从对话反馈中学习
    # ==============================================================================

    async def learn_from_dialog_feedback(
        self,
        session_id: str,
        turn_id: str,
        user_satisfaction: float,
        user_feedback: Optional[str] = None,
    ):
        """
        从对话反馈中学习

        Args:
            session_id: 会话ID
            turn_id: 对话轮次ID
            user_satisfaction: 用户满意度 (0-1)
            user_feedback: 用户反馈文本
        """
        if not self.enable_learning:
            return

        # 获取对话轮次
        context = self.dialog_sessions.get(session_id)
        if not context:
            return

        turn = next((t for t in context.history if t.turn_id == turn_id), None)
        if not turn:
            return

        # 更新轮次反馈
        turn.user_satisfaction = user_satisfaction
        turn.user_feedback = user_feedback

        # 计算奖励
        reward = self._calculate_dialog_reward(turn, user_satisfaction)

        # 更新策略统计
        strategy_name = turn.response_strategy.value
        stats = self.strategy_stats[strategy_name]
        stats["total_uses"] += 1

        if user_satisfaction > 0.7:
            stats["successes"] += 1

        # 更新平均满意度
        n = stats["total_uses"]
        stats["avg_satisfaction"] = (
            (stats["avg_satisfaction"] * (n - 1) + user_satisfaction) / n
        )
        stats["avg_reward"] = (
            (stats["avg_reward"] * (n - 1) + reward) / n
        )

        # 记录学习经验
        await self.learning_interface.record_experience(
            context={
                "user_message": turn.user_message,
                "dialog_state": turn.dialog_state.value,
            },
            action=strategy_name,
            result={
                "response": turn.assistant_response,
                "strategy": strategy_name,
            },
            success=user_satisfaction > 0.5,
            confidence=turn.confidence,
            user_satisfaction=user_satisfaction,
            user_feedback=user_feedback,
            reward=reward,
        )

        logger.info(
            f"📚 对话学习: {strategy_name} | "
            f"满意度: {user_satisfaction:.1f} | 奖励: {reward:.2f}"
        )

    def _calculate_dialog_reward(
        self,
        turn: DialogTurn,
        user_satisfaction: float,
    ) -> float:
        """计算对话奖励"""
        reward = 0.0

        # 满意度奖励
        reward += (user_satisfaction - 0.5) * 2.0

        # 置信度一致性
        if user_satisfaction > 0.7:
            # 高满意度，高置信度应该获得奖励
            reward += turn.confidence * 0.3
        else:
            # 低满意度，高置信度应该受到惩罚
            reward -= turn.confidence * 0.3

        # 策略特定奖励
        if turn.response_strategy == ResponseStrategy.CLARIFY:
            # 澄清策略如果获得高满意度，额外奖励
            if user_satisfaction > 0.8:
                reward += 0.3

        return max(-1.0, min(1.0, reward))

    # ==============================================================================
    # 批量学习：从完整对话中学习
    # ==============================================================================

    async def learn_from_conversation(
        self,
        session_id: str,
        overall_satisfaction: float,
    ):
        """
        从完整对话中学习

        Args:
            session_id: 会话ID
            overall_satisfaction: 整体满意度
        """
        if not self.enable_learning:
            return

        context = self.dialog_sessions.get(session_id)
        if not context or not context.history:
            return

        # 为每个对话轮次计算奖励
        for turn in context.history:
            # 如果没有单独的满意度，使用整体满意度
            if turn.user_satisfaction is None:
                turn.user_satisfaction = overall_satisfaction

            # 计算该轮的奖励
            base_reward = self._calculate_dialog_reward(turn, overall_satisfaction)

            # 考虑在对话中的位置（中间轮次更重要）
            position_factor = 1.0
            if 0 < len(context.history) <= 3:
                position_factor = 1.2

            reward = base_reward * position_factor

            # 记录学习经验
            await self.learning_interface.record_experience(
                context={
                    "user_message": turn.user_message,
                    "dialog_state": turn.dialog_state.value,
                    "position_in_conversation": len(context.history),
                },
                action=turn.response_strategy.value,
                result={
                    "response": turn.assistant_response,
                },
                success=overall_satisfaction > 0.5,
                confidence=turn.confidence,
                user_satisfaction=overall_satisfaction,
                reward=reward,
            )

        logger.info(
            f"📚 对话学习完成: 会话 {session_id} | "
            f"轮次: {len(context.history)} | "
            f"整体满意度: {overall_satisfaction:.1f}"
        )

    # ==============================================================================
    # 统计和优化
    # ==============================================================================

    def get_dialog_statistics(self) -> dict[str, Any]:
        """获取对话统计"""
        return {
            "total_sessions": len(self.dialog_sessions),
            "total_turns": sum(len(ctx.history) for ctx in self.dialog_sessions.values()),
            "strategy_stats": self.strategy_stats.copy(),
        }

    def get_strategy_performance(self) -> list[dict[str, Any]]:
        """获取策略性能对比"""
        performance = []

        for strategy_name, stats in self.strategy_stats.items():
            if stats["total_uses"] > 0:
                performance.append({
                    "strategy": strategy_name,
                    "total_uses": stats["total_uses"],
                    "success_rate": stats["successes"] / stats["total_uses"],
                    "avg_satisfaction": stats["avg_satisfaction"],
                    "avg_reward": stats["avg_reward"],
                })

        performance.sort(key=lambda x: x["avg_reward"], reverse=True)

        return performance

    async def optimize_dialog_strategy(self) -> OptimizationReport:
        """触发对话策略优化"""
        if not self.enable_learning or not self.learning_interface:
            return OptimizationReport(
                module_type=ModuleType.DIALOG,
                module_id="learning_dialog_manager",
                status="skipped",
                message="学习引擎未启用",
            )

        logger.info("🔧 触发对话策略优化...")

        report = await self.learning_interface.trigger_optimization()

        logger.info(
            f"✅ 对话策略优化完成: {report.status} | {report.message}"
        )

        return report

    async def export_learning_data(self, filepath: Optional[str] = None) -> Optional[str]:
        """导出学习数据"""
        if not self.enable_learning or not self.learning_interface:
            return None

        return self.learning_interface.export_experiences(filepath)


# =============================================================================
# 工厂函数
# =============================================================================

def get_learning_dialog_manager(
    enable_learning: bool = True,
) -> LearningDialogManager:
    """
    获取学习增强对话管理器实例

    Args:
        enable_learning: 是否启用学习引擎

    Returns:
        LearningDialogManager: 学习增强对话管理器实例
    """
    return LearningDialogManager(enable_learning=enable_learning)


# =============================================================================
# 测试代码
# =============================================================================
if __name__ == "__main__":
    async def test_learning_dialog_manager():
        """测试学习增强对话管理器"""
        print("=" * 80)
        print("💬 测试学习增强对话管理器")
        print("=" * 80)

        # 创建对话管理器
        manager = get_learning_dialog_manager(enable_learning=True)

        # 模拟对话
        session_id = "test_session_001"

        # 轮次1
        print("\n🎯 对话轮次 1")
        print("-" * 80)

        response1 = await manager.process_message(
            user_message="我想了解专利申请的流程",
            session_id=session_id,
            use_learning=True,
        )

        print("用户: 我想了解专利申请的流程")
        print(f"策略: {response1.strategy_used.value}")
        print(f"回应: {response1.response_text}")
        print(f"置信度: {response1.confidence:.2f}")

        # 用户反馈
        await manager.learn_from_dialog_feedback(
            session_id=session_id,
            turn_id=f"{session_id}_0",
            user_satisfaction=0.8,
        )

        # 轮次2
        print("\n🎯 对话轮次 2")
        print("-" * 80)

        response2 = await manager.process_message(
            user_message="具体需要哪些材料？",
            session_id=session_id,
            use_learning=True,
        )

        print("用户: 具体需要哪些材料？")
        print(f"策略: {response2.strategy_used.value}")
        print(f"回应: {response2.response_text}")

        # 用户反馈
        await manager.learn_from_dialog_feedback(
            session_id=session_id,
            turn_id=f"{session_id}_1",
            user_satisfaction=0.9,
            user_feedback="回答很详细",
        )

        # 获取统计
        print("\n📊 对话统计:")
        print("-" * 80)
        stats = manager.get_dialog_statistics()
        print(f"总会话数: {stats['total_sessions']}")
        print(f"总对话轮次: {stats['total_turns']}")

        print("\n策略性能:")
        performance = manager.get_strategy_performance()
        for p in performance:
            print(f"\n  {p['strategy']}:")
            print(f"    使用次数: {p['total_uses']}")
            print(f"    成功率: {p['success_rate']:.1%}")
            print(f"    平均满意度: {p['avg_satisfaction']:.2f}")
            print(f"    平均奖励: {p['avg_reward']:.3f}")

        # 从完整对话学习
        print("\n📚 从完整对话学习...")
        await manager.learn_from_conversation(
            session_id=session_id,
            overall_satisfaction=0.85,
        )

        # 触发优化
        print("\n🔧 触发优化...")
        report = await manager.optimize_dialog_strategy()
        print(f"优化状态: {report.status}")

        print("\n" + "=" * 80)
        print("✅ 测试完成!")
        print("=" * 80)

    asyncio.run(test_learning_dialog_manager())


# =============================================================================
# === 别名和便捷函数 ===
# =============================================================================

# 为保持兼容性，提供 DialogManager 作为 LearningDialogManager 的别名
DialogManager = LearningDialogManager


def get_dialog_manager(
    enable_learning: bool = True,
    auto_optimize: bool = True,
) -> LearningDialogManager:
    """
    获取或创建对话管理器实例

    Args:
        enable_learning: 是否启用学习引擎
        auto_optimize: 是否自动优化

    Returns:
        LearningDialogManager 实例
    """
    return LearningDialogManager(
        enable_learning=enable_learning,
        auto_optimize=auto_optimize,
    )


__all__ = [
    # 原始类
    "LearningDialogManager",
    "DialogState",
    "ResponseStrategy",
    "DialogTurn",
    "DialogContext",
    "DialogResponse",
    # 别名
    "DialogManager",
    # 便捷函数
    "get_dialog_manager",
]
