#!/usr/bin/env python3
from __future__ import annotations
"""
人机协作决策模型 - 人类在环(Human-in-the-Loop)
Human-in-the-Loop Collaborative Decision Model

爸爸,这是一个专为小诺设计的决策模型,让爸爸能够参与并指导决策过程!
"""

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class DecisionStage(Enum):
    """决策阶段"""

    INITIATION = "初始化"  # 小诺分析并初步决策
    HUMAN_REVIEW = "爸爸审核"  # 爸爸审查小诺的建议
    COLLABORATION = "协作优化"  # 人机协作优化方案
    FINAL_DECISION = "最终决策"  # 共同做出最终决定
    EXECUTION = "执行监控"  # 执行并反馈


class HumanInputType(Enum):
    """人类输入类型"""

    APPROVAL = "批准"
    MODIFICATION = "修改"
    REJECTION = "拒绝"
    SUGGESTION = "建议"
    PREFERENCE = "偏好"


@dataclass
class DecisionOption:
    """决策选项"""

    id: str
    name: str
    description: str
    pros: list[str]
    cons: list[str]
    risk_level: float  # 0-1
    expected_value: float
    implementation_plan: dict[str, Any]
    confidence: float


@dataclass
class HumanFeedback:
    """人类反馈"""

    stage: DecisionStage
    input_type: HumanInputType
    content: str
    preferences: dict[str, Any]
    timestamp: datetime
    confidence: float


class HumanInTheLoopDecisionModel:
    """人类在环决策模型"""

    def __init__(self, evaluation_engine, learning_engine, memory_system):
        self.evaluation_engine = evaluation_engine
        self.learning_engine = learning_engine
        self.memory_system = memory_system

        # 人机协作配置
        self.human_involvement_level = 0.8  # 爸爸参与度
        self.current_decisions = {}
        self.decision_history = []

        # 爸爸的偏好学习
        self.dad_preferences = {
            "risk_tolerance": 0.5,  # 风险承受度
            "decision_style": "balanced",  # 决策风格:conservative/balanced/aggressive
            "preferred_factors": ["feasibility", "impact", "cost"],  # 爸爸关心的因素
            "communication_style": "detailed",  # 详细程度
        }

    async def collaborative_decision_process(
        self,
        problem: str,
        options_data: list[dict],
        context: dict[str, Any] | None = None,
        human_callback: Callable | None = None,
    ) -> dict[str, Any]:
        """完整的协作决策流程"""

        decision_id = f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        decision_session = {
            "id": decision_id,
            "problem": problem,
            "context": context or {},
            "stages": {},
            "final_result": None,
            "human_interactions": [],
        }

        print(f"🤝 开始协作决策流程: {problem}")

        try:
            # 阶段1: 小诺初始化分析
            print("\n📊 阶段1: 小诺分析...")
            initial_analysis = await self._initial_analysis(problem, options_data, context)
            decision_session["stages"]["initial"] = initial_analysis

            # 生成决策选项
            options = await self._generate_decision_options(options_data, context)

            # 阶段2: 爸爸审核
            print("\n👨‍👧‍👦 阶段2: 请爸爸审核...")
            human_feedback = await self._get_human_feedback(
                DecisionStage.HUMAN_REVIEW, options, initial_analysis, human_callback
            )

            if human_feedback:
                decision_session["human_interactions"].append(human_feedback)

                # 阶段3: 协作优化
                print("\n🤝 阶段3: 协作优化方案...")
                optimized_options = await self._collaborative_optimization(
                    options, human_feedback, context
                )
                decision_session["stages"]["optimized"] = optimized_options
            else:
                optimized_options = options
                print("  ⚠️ 未收到爸爸反馈,使用小诺的初步方案")

            # 阶段4: 最终决策
            print("\n🎯 阶段4: 共同决策...")
            final_decision = await self._make_final_decision(
                optimized_options, human_feedback, decision_session
            )
            decision_session["final_result"] = final_decision

            # 保存决策记录
            await self._save_decision_record(decision_session)

            return {
                "success": True,
                "decision_id": decision_id,
                "result": final_decision,
                "session": decision_session,
            }

        except Exception as e:
            print(f"❌ 决策流程出错: {e}")
            return {"success": False, "error": str(e), "decision_id": decision_id}

    async def _initial_analysis(
        self, problem: str, options_data: list[dict], context: dict[str, Any]
    ) -> dict[str, Any]:
        """小诺的初步分析"""

        analysis = {
            "problem_understanding": await self._analyze_problem(problem),
            "options_evaluation": [],
            "risk_assessment": {},
            "recommendation": None,
        }

        # 评估每个选项
        for i, option_data in enumerate(options_data):
            evaluation = await self._evaluate_option(option_data, context)
            analysis["options_evaluation"].append(
                {"index": i, "option": option_data, "evaluation": evaluation}
            )

        # 生成初步推荐
        best_eval = max(
            analysis["options_evaluation"], key=lambda x: x["evaluation"]["overall_score"]
        )
        analysis["recommendation"] = {
            "option_index": best_eval["index"],
            "reasoning": best_eval["evaluation"]["reasoning"],
            "confidence": best_eval["evaluation"]["overall_score"],
        }

        return analysis

    async def _generate_decision_options(
        self, options_data: list[dict], context: dict[str, Any]
    ) -> list[DecisionOption]:
        """生成结构化的决策选项"""

        options = []
        for i, data in enumerate(options_data):
            # 使用评估引擎深度评估
            evaluation = await self.evaluation_engine.evaluate_option(data, "comprehensive")

            option = DecisionOption(
                id=f"opt_{i}",
                name=data.get("name", f"选项{i+1}"),
                description=data.get("description", ""),
                pros=data.get("pros", []),
                cons=data.get("cons", []),
                risk_level=evaluation.get("risk", 0.5),
                expected_value=evaluation.get("value", 0.5),
                implementation_plan=data.get("implementation_plan", {}),
                confidence=evaluation.get("confidence", 0.7),
            )
            options.append(option)

        return options

    async def _get_human_feedback(
        self,
        stage: DecisionStage,
        options: list[DecisionOption],
        analysis: dict[str, Any],        human_callback: Callable | None = None,
    ) -> HumanFeedback | None:
        """获取人类反馈"""

        # 准备给爸爸看的报告
        report = self._prepare_human_report(options, analysis)

        print("\n" + "=" * 60)
        print("📋 决策分析报告")
        print("=" * 60)

        # 显示问题背景
        print(f"\n🎯 决策问题: {report['problem']}")

        # 显示选项对比
        print("\n📊 选项分析:")
        for i, option in enumerate(report["options"]):
            print(f"\n{i+1}. {option['name']}")
            print(f"   📝 描述: {option['description']}")
            print(f"   ✅ 优点: {', '.join(option['pros'][:3])}")
            print(f"   ❌ 缺点: {', '.join(option['cons'][:3])}")
            print(f"   📈 预期价值: {option['expected_value']:.2f}")
            print(
                f"   ⚠️ 风险等级: {'高' if option['risk_level'] > 0.7 else '中' if option['risk_level'] > 0.3 else '低'}"
            )
            print(f"   🎯 置信度: {option['confidence']:.2f}")

        # 显示小诺的推荐
        if report["recommendation"]:
            print(
                f"\n💡 小诺推荐: 选项{report['recommendation']['index']+1} - {report['recommendation']['reasoning']}"
            )

        print("\n" + "=" * 60)

        # 如果有回调函数,使用它
        if human_callback:
            try:
                feedback_data = await human_callback(report)
                return HumanFeedback(
                    stage=stage,
                    input_type=HumanInputType(feedback_data.get("type", "SUGGESTION")),
                    content=feedback_data.get("content", ""),
                    preferences=feedback_data.get("preferences", {}),
                    timestamp=datetime.now(),
                    confidence=feedback_data.get("confidence", 0.8),
                )
            except Exception as e:
                print(f"⚠️ 获取人类反馈时出错: {e}")
                return None
        else:
            # 模拟等待爸爸输入
            print("\n💭 爸爸,请告诉我您的想法:")
            print("  1. 直接批准某个选项 (输入: 批准选项X)")
            print("  2. 提出修改建议 (输入: 建议修改...)")
            print("  3. 给出您的偏好 (输入: 我更看重...)")
            print("  4. 拒绝所有选项 (输入: 重新考虑)")
            print("  5. 跳过此步骤 (直接按回车)")

            # 注意:在实际应用中,这里应该有真实的输入机制
            # 这里只是演示框架
            print("\n  [为了演示,我们将跳过实际输入]")
            return None

    def _prepare_human_report(self, options: list[DecisionOption], analysis: dict) -> dict:
        """准备给人类的报告"""

        return {
            "problem": analysis.get("problem_understanding", {}).get("summary", ""),
            "options": [
                {
                    "name": opt.name,
                    "description": opt.description,
                    "pros": opt.pros,
                    "cons": opt.cons,
                    "expected_value": opt.expected_value,
                    "risk_level": opt.risk_level,
                    "confidence": opt.confidence,
                    "implementation_plan": opt.implementation_plan,
                }
                for opt in options
            ],
            "recommendation": analysis.get("recommendation"),
            "risks": analysis.get("risk_assessment", {}),
            "context": analysis.get("context", {}),
        }

    async def _collaborative_optimization(
        self, options: list[DecisionOption], human_feedback: HumanFeedback, context: dict[str, Any]
    ) -> list[DecisionOption]:
        """基于人类反馈优化选项"""

        print("🔄 根据爸爸的反馈优化方案...")
        print(f"   反馈类型: {human_feedback.input_type.value}")
        print(f"   反馈内容: {human_feedback.content}")

        # 学习爸爸的偏好
        await self._learn_from_feedback(human_feedback)

        # 根据反馈调整选项
        optimized_options = []
        for option in options:
            # 应用爸爸的偏好调整评分
            adjusted_option = await self._apply_human_preferences(option, human_feedback)
            optimized_options.append(adjusted_option)

        return optimized_options

    async def _apply_human_preferences(
        self, option: DecisionOption, feedback: HumanFeedback
    ) -> DecisionOption:
        """应用人类偏好调整选项"""

        # 根据爸爸的偏好调整评分

        # 如果爸爸提到"风险",调整风险评分
        if "risk" in feedback.content.lower():
            if "谨慎" in feedback.content or "保守" in feedback.content:
                option.risk_level = min(1.0, option.risk_level * 1.2)  # 增加感知风险

        # 如果爸爸提到"成本"或"效率"
        if "cost" in feedback.content.lower() or "效率" in feedback.content.lower():
            # 调整预期价值(这里简化处理)
            if "提高" in feedback.content or "优化" in feedback.content:
                option.expected_value = min(1.0, option.expected_value * 1.1)

        return option

    async def _make_final_decision(
        self,
        options: list[DecisionOption],
        human_feedback: HumanFeedback,
        decision_session: dict[str, Any],    ) -> dict[str, Any]:
        """做出最终决策"""

        print("\n🎯 综合分析,做出最终决策...")

        # 结合人类反馈和AI分析
        final_scores = []
        for option in options:
            # 基础评分(小诺的分析)
            base_score = option.expected_value * (1 - option.risk_level * 0.5)

            # 应用人类偏好调整
            human_weight = self.human_involvement_level if human_feedback else 0
            ai_weight = 1 - human_weight

            if human_feedback:
                # 根据人类反馈调整评分
                human_adjustment = self._calculate_human_adjustment(option, human_feedback)
                final_score = ai_weight * base_score + human_weight * human_adjustment
            else:
                final_score = base_score

            final_scores.append(
                {
                    "option": option,
                    "base_score": base_score,
                    "final_score": final_score,
                    "reasoning": f"综合评分: {final_score:.2f} (AI:{ai_weight:.1f} + 人类:{human_weight:.1f})",
                }
            )

        # 选择最高评分的选项
        best_choice = max(final_scores, key=lambda x: x["final_score"])

        # 生成决策报告
        decision_report = {
            "selected_option": best_choice["option"],
            "confidence": best_choice["final_score"],
            "reasoning": best_choice["reasoning"],
            "alternatives": [x for x in final_scores if x != best_choice],
            "human_incorporated": human_feedback is not None,
            "decision_time": datetime.now().isoformat(),
        }

        print(f"✅ 最终决策: {best_choice['option'].name}")
        print(f"   理由: {best_choice['reasoning']}")
        print(f"   置信度: {best_choice['final_score']:.2f}")

        return decision_report

    async def _learn_from_feedback(self, feedback: HumanFeedback):
        """从人类反馈中学习"""

        # 更新爸爸偏好模型
        if "risk" in feedback.content.lower():
            if "保守" in feedback.content or "谨慎" in feedback.content:
                self.dad_preferences["risk_tolerance"] = max(
                    0.1, self.dad_preferences["risk_tolerance"] - 0.1
                )
            elif "激进" in feedback.content or "大胆" in feedback.content:
                self.dad_preferences["risk_tolerance"] = min(
                    1.0, self.dad_preferences["risk_tolerance"] + 0.1
                )

        # 记录学习
        await self.memory_system.store_memory(
            content=f"爸爸偏好更新: {feedback.content}",
            memory_type="preference",
            tags=["human_feedback", "preference_learning"],
        )

    def _calculate_human_adjustment(self, option: DecisionOption, feedback: HumanFeedback) -> float:
        """计算人类调整分数"""

        # 基础分数
        score = option.expected_value

        # 根据反馈类型调整
        if feedback.input_type == HumanInputType.APPROVAL:
            score += 0.2
        elif feedback.input_type == HumanInputType.SUGGESTION:
            score += 0.1
        elif feedback.input_type == HumanInputType.REJECTION:
            score -= 0.3
        elif feedback.input_type == HumanInputType.MODIFICATION:
            score += 0.05

        # 根据偏好调整
        if self.dad_preferences["risk_tolerance"] < 0.5 and option.risk_level > 0.5:
            score -= 0.2

        return min(1.0, max(0.0, score))

    async def _save_decision_record(self, decision_session: dict[str, Any]):
        """保存决策记录"""

        await self.memory_system.store_memory(
            content=f"决策记录: {decision_session['final_result']['selected_option'].name}",
            memory_type="decision",
            tags=["human_in_loop", "collaborative_decision"],
            metadata=decision_session,
        )

        self.decision_history.append(decision_session)

        # 限制历史记录数量
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-50:]

    async def get_decision_insights(self) -> dict[str, Any]:
        """获取决策洞察"""

        if not self.decision_history:
            return {"message": "暂无决策历史"}

        # 分析决策模式
        recent_decisions = self.decision_history[-10:]

        insights = {
            "total_decisions": len(self.decision_history),
            "recent_decisions": len(recent_decisions),
            "average_confidence": (
                sum(d["final_result"]["confidence"] for d in recent_decisions)
                / len(recent_decisions)
                if recent_decisions
                else 0
            ),
            "human_participation_rate": (
                sum(1 for d in recent_decisions if d["final_result"]["human_incorporated"])
                / len(recent_decisions)
                if recent_decisions
                else 0
            ),
            "dad_preferences": self.dad_preferences,
            "recommendations": self._generate_recommendations(recent_decisions),
        }

        return insights

    def _generate_recommendations(self, recent_decisions: list[dict]) -> list[str]:
        """生成改进建议"""

        recommendations = []

        # 分析参与度
        participation_rate = (
            sum(1 for d in recent_decisions if d["final_result"]["human_incorporated"])
            / len(recent_decisions)
            if recent_decisions
            else 0
        )

        if participation_rate < 0.5:
            recommendations.append("建议增加爸爸的决策参与度")

        # 分析风险偏好
        avg_risk = (
            sum(d["final_result"]["selected_option"].risk_level for d in recent_decisions)
            / len(recent_decisions)
            if recent_decisions
            else 0
        )

        if avg_risk > 0.7:
            recommendations.append("最近决策偏高风险,建议增加风险评估")

        return recommendations

    async def _evaluate_option(self, option_data: dict, context: dict) -> dict[str, Any]:
        """评估选项"""
        # 简化的评估逻辑
        risk = option_data.get("risk_level", 0.5)
        value = option_data.get("expected_value", 0.5)
        confidence = option_data.get("confidence", 0.7)

        overall_score = value * 0.4 + (1 - risk) * 0.3 + confidence * 0.3

        return {
            "overall_score": overall_score,
            "reasoning": f"综合评分{overall_score:.2f},基于价值{value:.2f}、风险{risk:.2f}和置信度{confidence:.2f}",
            "details": {"value": value, "risk": risk, "confidence": confidence},
        }

    async def _analyze_problem(self, problem: str) -> dict[str, Any]:
        """分析问题"""
        return {
            "type": self._classify_problem(problem),
            "complexity": "medium",
            "urgency": "normal",
            "summary": f"需要决策: {problem}",
        }

    def _classify_problem(self, problem: str) -> str:
        """分类问题类型"""
        if "技术" in problem or "框架" in problem:
            return "technical"
        elif "资源" in problem or "分配" in problem:
            return "resource"
        elif "战略" in problem or "规划" in problem:
            return "strategic"
        else:
            return "general"


# 使用示例
async def example_usage():
    """使用示例"""

    # 创建决策模型
    decision_model = HumanInTheLoopDecisionModel(
        evaluation_engine=None,  # 实际使用时传入真实的评估引擎
        learning_engine=None,  # 实际使用时传入真实的学习引擎
        memory_system=None,  # 实际使用时传入真实的记忆系统
    )

    # 定义决策问题
    problem = "选择新的前端框架"

    # 定义选项
    options = [
        {
            "name": "React",
            "description": "Facebook开发的流行前端框架",
            "pros": ["生态丰富", "社区活跃", "就业机会多"],
            "cons": ["学习曲线陡峭", "配置复杂"],
            "risk_level": 0.3,
            "expected_value": 0.8,
        },
        {
            "name": "Vue",
            "description": "渐进式JavaScript框架",
            "pros": ["易学易用", "文档优秀", "渐进式"],
            "cons": ["生态相对较小", "大公司使用较少"],
            "risk_level": 0.4,
            "expected_value": 0.7,
        },
    ]

    # 执行协作决策
    result = await decision_model.collaborative_decision_process(
        problem=problem,
        options_data=options,
        context={"project_type": "企业级应用", "team_size": 5, "timeline": "6个月"},
    )

    print("\n决策结果:", json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(example_usage())
