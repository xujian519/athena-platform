#!/usr/bin/env python3
"""
人机协作决策系统 - Human-in-the-Loop Decision System
在终端和Claude Code环境下实现的人机协作决策框架

作者: 小诺·双鱼座
版本: v1.0.0 "人机协作"
创建时间: 2025-12-17
"""

from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

try:
    from claude_code import ask_user_question
except ImportError:
    ask_user_question = None


class DecisionType(Enum):
    """决策类型"""

    SIMPLE = "simple"  # 简单决策(可以自动处理)
    COMPLEX = "complex"  # 复杂决策(需要人类审核)
    CRITICAL = "critical"  # 关键决策(必须人类批准)
    EMERGENCY = "emergency"  # 紧急决策(立即响应)


class InteractionMode(Enum):
    """交互模式"""

    TERMINAL = "terminal"  # 终端模式
    CLAUDE_CODE = "claude_code"  # Claude Code模式
    AUTO = "auto"  # 自动模式


@dataclass
class DecisionOption:
    """决策选项"""

    id: str
    title: str
    description: str
    confidence: float = 0.0
    risk_level: str = "low"  # low, medium, high
    estimated_cost: float | None = None
    expected_outcome: str | None = None


@dataclass
class DecisionContext:
    """决策上下文"""

    problem: str
    options: list[DecisionOption]
    ai_recommendation: DecisionOption | None = None
    requires_human: bool = False
    deadline: datetime | None = None
    stakeholders: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)


@dataclass
class HumanFeedback:
    """人类反馈"""

    decision_id: str
    selected_option: str
    feedback: str
    confidence: int  # 1-5
    timestamp: datetime = field(default_factory=datetime.now)
    additional_comments: str | None = None


class HumanInLoopDecisionEngine:
    """人机协作决策引擎"""

    def __init__(self, mode: InteractionMode = InteractionMode.TERMINAL):
        self.mode = mode
        self.decision_history = []
        self.feedback_database = []
        self.auto_approve_threshold = 0.9  # 高置信度自动批准

        # Claude Code环境检查
        self._is_claude_code = self._detect_claude_code()

    def _detect_claude_code(self) -> bool:
        """检测是否在Claude Code环境"""
        try:
            # 检查是否有AskUserQuestion工具

            return any("AskUserQuestion" in str(type(obj)) for name, obj in globals().items())
        except (ValueError, KeyError, AttributeError):  # TODO: 根据上下文指定具体异常类型
            return False

    async def make_decision(self, context: DecisionContext) -> DecisionOption:
        """执行人机协作决策"""
        print(f"\n🤔 开始决策: {context.problem}")

        # 1. AI初步分析
        ai_recommendation = await self._ai_analyze(context)
        context.ai_recommendation = ai_recommendation

        # 2. 判断是否需要人类参与
        needs_human = await self._assess_human_requirement(context)
        context.requires_human = needs_human

        if not needs_human:
            print("✅ AI决策:置信度足够,自动执行")
            return ai_recommendation

        # 3. 人机协作决策
        return await self._human_collaborative_decision(context)

    async def _ai_analyze(self, context: DecisionContext) -> DecisionOption:
        """AI分析并推荐"""
        print("🧠 AI正在分析...")

        # 模拟AI分析过程
        best_option = max(context.options, key=lambda x: x.confidence)

        # 分析额外因素
        risk_score = self._calculate_risk(context.options)
        cost_benefit = self._calculate_cost_benefit(context.options)

        print("   📊 AI分析结果:")
        print(f"   推荐选项: {best_option.title}")
        print(f"   置信度: {best_option.confidence:.2f}")
        print(f"   风险评估: {risk_score:.2f}")
        print(f"   成本效益: {cost_benefit:.2f}")

        return best_option

    async def _assess_human_requirement(self, context: DecisionContext) -> bool:
        """评估是否需要人类参与"""
        decision_type = self._classify_decision(context)

        # 关键决策总是需要人类
        if decision_type == DecisionType.CRITICAL:
            return True

        # 高风险决策需要人类
        high_risk_options = [opt for opt in context.options if opt.risk_level == "high"]
        if high_risk_options and context.ai_recommendation in high_risk_options:
            return True

        # 低置信度需要人类
        if context.ai_recommendation and context.ai_recommendation.confidence < 0.7:
            return True

        # 紧急决策可以自动处理
        if decision_type == DecisionType.EMERGENCY:
            return False

        return False

    def _classify_decision(self, context: DecisionContext) -> DecisionType:
        """分类决策类型"""
        # 关键词判断
        problem_lower = context.problem.lower()

        if any(word in problem_lower for word in ["紧急", "emergency", "立刻", "马上"]):
            return DecisionType.EMERGENCY
        elif any(word in problem_lower for word in ["关键", "critical", "重要", "重要决策"]):
            return DecisionType.CRITICAL
        elif len(context.options) > 5 or "复杂" in problem_lower:
            return DecisionType.COMPLEX
        else:
            return DecisionType.SIMPLE

    async def _human_collaborative_decision(self, context: DecisionContext) -> DecisionOption:
        """人机协作决策"""
        if self._is_claude_code:
            return await self._claude_code_interaction(context)
        else:
            return await self._terminal_interaction(context)

    async def _terminal_interaction(self, context: DecisionContext) -> DecisionOption:
        """终端模式交互"""
        print("\n💬 需要您的决策参与")
        print("=" * 50)

        # 显示问题背景
        print(f"\n📋 决策问题: {context.problem}")
        if context.constraints:
            print(f"⚠️ 约束条件: {', '.join(context.constraints)}")

        # 显示AI推荐
        if context.ai_recommendation:
            print("\n🤖 AI推荐:")
            print(f"   选项: {context.ai_recommendation.title}")
            print(f"   置信度: {context.ai_recommendation.confidence:.2f}")
            print(f"   描述: {context.ai_recommendation.description}")

        # 显示所有选项
        print("\n📝 所有选项:")
        for i, option in enumerate(context.options, 1):
            risk_icon = (
                "🔴"
                if option.risk_level == "high"
                else "🟡" if option.risk_level == "medium" else "🟢"
            )
            print(f"   {i}. {option.title} {risk_icon}")
            print(f"      {option.description}")
            print(f"      置信度: {option.confidence:.2f} | 风险: {option.risk_level}")

        # 获取用户选择
        while True:
            try:
                choice = input(
                    f"\n👤 请选择 (1-{len(context.options)}) 或 'auto' 接受AI推荐: "
                ).strip()

                if choice.lower() == "auto" and context.ai_recommendation:
                    # 验证自动选择
                    confirm = (
                        input(f"确认选择AI推荐: {context.ai_recommendation.title}? (y/n): ")
                        .strip()
                        .lower()
                    )
                    if confirm == "y":
                        return context.ai_recommendation

                elif choice.isdigit():
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(context.options):
                        selected = context.options.get(choice_idx)

                        # 收集反馈
                        await self._collect_feedback(selected, context)

                        # 询问是否确认
                        final_confirm = (
                            input(f"\n✅ 确认选择: {selected.title}? (y/n): ").strip().lower()
                        )
                        if final_confirm == "y":
                            return selected

                else:
                    print("❌ 无效输入,请重试")

            except (EOFError, KeyboardInterrupt):
                return context.ai_recommendation or context.options.get(0)

    async def _claude_code_interaction(self, context: DecisionContext) -> DecisionOption:
        """Claude Code模式交互"""
        # 使用AskUserQuestion工具(如果可用)
        try:

            # 准备问题
            question = f"需要您做出决策: {context.problem}\n\n"
            question += f"🤖 AI推荐: {context.ai_recommendation.title if context.ai_recommendation else '无'}\n\n"
            question += "请选择您的决策选项:"

            # 准备选项
            options = []
            for option in context.options:
                option_text = (
                    f"{option.title} (置信度: {option.confidence:.2f}, 风险: {option.risk_level})"
                )
                options.append({"label": option_text, "description": option.description})

            # 添加自动选项
            if context.ai_recommendation:
                options.insert(
                    0, {"label": "🤖 接受AI推荐", "description": "接受AI系统推荐的最优选项"}
                )

            # 调用交互
            response = await ask_user_question(
                question=question, options=options, multi_select=False, required=True
            )

            # 处理响应
            if response == "🤖 接受AI推荐" and context.ai_recommendation:
                return context.ai_recommendation
            else:
                # 查找对应的选项
                for option in context.options:
                    if option.title in response:
                        return option

                # 默认返回第一个选项
                return context.options.get(0)

        except ImportError:
            print("⚠️ Claude Code工具不可用,使用终端模式")
            return await self._terminal_interaction(context)

    async def _collect_feedback(
        self, selected: DecisionOption, context: DecisionContext
    ) -> HumanFeedback:
        """收集人类反馈"""
        print("\n💭 请提供决策反馈:")

        try:
            confidence = input("您的决策信心 (1-5): ").strip()
            feedback = input("选择理由: ").strip()
            comments = input("其他建议 (可选): ").strip()

            feedback_obj = HumanFeedback(
                decision_id=f"decision_{int(time.time())}",
                selected_option=selected.id,
                feedback=feedback,
                confidence=int(confidence) if confidence.isdigit() else 3,
                additional_comments=comments if comments else None,
            )

            self.feedback_database.append(feedback_obj)
            return feedback_obj

        except (EOFError, KeyboardInterrupt):
            return HumanFeedback(
                decision_id=f"decision_{int(time.time())}",
                selected_option=selected.id,
                feedback="默认反馈",
                confidence=3,
            )

    def _calculate_risk(self, options: list[DecisionOption]) -> float:
        """计算风险分数"""
        risk_scores = {"low": 0.1, "medium": 0.5, "high": 0.9}
        return sum(risk_scores.get(opt.risk_level, 0.5) for opt in options) / len(options)

    def _calculate_cost_benefit(self, options: list[DecisionOption]) -> float:
        """计算成本效益比"""
        total_score = 0
        for opt in options:
            benefit = opt.confidence * 100
            cost = opt.estimated_cost or 0
            ratio = benefit / max(cost, 1)
            total_score += ratio
        return total_score / len(options)

    def get_decision_stats(self) -> dict[str, Any]:
        """获取决策统计"""
        if not self.decision_history:
            return {"message": "暂无决策记录"}

        total_decisions = len(self.decision_history)
        human_decisions = sum(1 for d in self.decision_history if d.get("required_human", False))

        return {
            "total_decisions": total_decisions,
            "human_involved": human_decisions,
            "auto_decisions": total_decisions - human_decisions,
            "human_involvement_rate": human_decisions
            / total_decisions
            * 100,  # TODO: 确保除数不为零
            "feedback_count": len(self.feedback_database),
        }


# 使用示例
async def demo_human_in_loop():
    """演示人机协作决策"""
    print("🚀 人机协作决策系统演示")
    print("=" * 50)

    # 创建决策引擎
    engine = HumanInLoopDecisionEngine()

    # 示例1: 简单决策
    print("\n📝 示例1: 选择开发方案")
    context1 = DecisionContext(
        problem="为新功能选择开发方案",
        options=[
            DecisionOption("opt1", "快速实现", "使用现有框架快速开发", confidence=0.8),
            DecisionOption(
                "opt2", "重构架构", "重构系统架构再开发", confidence=0.6, risk_level="medium"
            ),
            DecisionOption(
                "opt3", "引入新技术", "使用最新的技术栈", confidence=0.4, risk_level="high"
            ),
        ],
    )

    decision1 = await engine.make_decision(context1)
    print(f"最终决策: {decision1.title}")

    # 示例2: 关键决策
    print("\n📝 示例2: 发布关键版本")
    context2 = DecisionContext(
        problem="是否发布包含重大功能的新版本",
        options=[
            DecisionOption("release", "立即发布", "按计划发布新版本", confidence=0.7),
            DecisionOption("delay", "延期发布", "延期一个月充分测试", confidence=0.8),
            DecisionOption(
                "rollback", "回滚版本", "撤销所有更改", confidence=0.5, risk_level="high"
            ),
        ],
        stakeholders=["开发团队", "产品经理", "用户"],
        constraints=["必须在Q4完成", "不能影响现有功能"],
    )

    decision2 = await engine.make_decision(context2)
    print(f"最终决策: {decision2.title}")

    # 显示统计
    stats = engine.get_decision_stats()
    print("\n📊 决策统计:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(demo_human_in_loop())
