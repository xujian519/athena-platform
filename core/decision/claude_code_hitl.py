#!/usr/bin/env python3
from __future__ import annotations
"""
Claude Code环境人机协作决策系统
专门优化用于Claude Code环境的HITL实现

作者: 小诺·双鱼座
版本: v1.0.0 "Claude Code HITL"
创建时间: 2025-12-17
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class DecisionUrgency(Enum):
    """决策紧急程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DecisionCategory(Enum):
    """决策类别"""
    TECHNICAL = "technical"      # 技术决策
    BUSINESS = "business"        # 业务决策
    STRATEGIC = "strategic"      # 战略决策
    OPERATIONAL = "operational"  # 运营决策

@dataclass
class DecisionRequest:
    """决策请求"""
    title: str
    description: str
    options: list[dict[str, Any]]
    category: DecisionCategory
    urgency: DecisionUrgency = DecisionUrgency.MEDIUM
    context: dict[str, Any] | None = None
    stakeholders: list[str] | None = None
    deadline: datetime | None = None

@dataclass
class DecisionResult:
    """决策结果"""
    chosen_option: str
    confidence: float
    human_feedback: str | None = None
    rationale: str | None = None
    timestamp: datetime = None

class ClaudeCodeHITLDecisionEngine:
    """Claude Code环境人机协作决策引擎"""

    def __init__(self):
        self.decision_history = []
        self.auto_approve_rules = self._initialize_rules()
        self.user_preferences = {}

    def _initialize_rules(self) -> dict[str, Any]:
        """初始化自动批准规则"""
        return {
            "auto_approve_confidence": 0.95,
            "low_risk_categories": [DecisionCategory.OPERATIONAL],
            "urgent_auto_approve": True,
            "require_human_categories": [DecisionCategory.STRATEGIC, DecisionCategory.BUSINESS],
            "stakeholder_threshold": 3
        }

    async def make_decision(self, request: DecisionRequest) -> DecisionResult:
        """执行人机协作决策"""
        print(f"\n🎯 决策请求: {request.title}")
        print(f"📝 描述: {request.description}")

        # 1. 预处理和分析
        processed_options = self._preprocess_options(request.options)

        # 2. AI分析和推荐
        ai_analysis = await self._analyze_with_ai(request, processed_options)

        # 3. 判断决策策略
        strategy = self._determine_decision_strategy(request, ai_analysis)

        # 4. 执行决策
        if strategy == "auto":
            return await self._auto_decision(request, ai_analysis)
        else:
            return await self._human_assisted_decision(request, ai_analysis)

    def _preprocess_options(self, options: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """预处理选项"""
        processed = []
        for opt in options:
            processed_option = {
                "id": opt.get("id", f"opt_{len(processed)}"),
                "title": opt.get("title", "未命名选项"),
                "description": opt.get("description", ""),
                "pros": opt.get("pros", []),
                "cons": opt.get("cons", []),
                "confidence": opt.get("confidence", 0.5),
                "risk_level": opt.get("risk_level", "medium"),
                "estimated_cost": opt.get("estimated_cost", 0),
                "expected_value": opt.get("expected_value", 0)
            }
            processed.append(processed_option)
        return processed

    async def _analyze_with_ai(self, request: DecisionRequest, options: list[dict[str, Any]]) -> dict[str, Any]:
        """AI分析"""
        # 模拟AI分析过程
        best_option = max(options, key=lambda x: x["confidence"] * (1 + x.get("expected_value", 0)))

        # 计算决策指标
        risk_score = sum(1 for opt in options if opt["risk_level"] == "high") / len(options)
        avg_confidence = sum(opt["confidence"] for opt in options) / len(options)

        analysis = {
            "recommended_option": best_option,
            "recommendation_confidence": best_option["confidence"],
            "risk_assessment": risk_score,
            "avg_confidence": avg_confidence,
            "analysis_summary": f"推荐选项: {best_option['title']},置信度: {best_option['confidence']:.2f}"
        }

        print("\n🧠 AI分析结果:")
        print(f"   推荐: {analysis['recommendation_confidence']:.2f} 置信度")
        print(f"   风险评估: {analysis['risk_assessment']:.2f}")
        print(f"   {analysis['analysis_summary']}")

        return analysis

    def _determine_decision_strategy(self, request: DecisionRequest, analysis: dict[str, Any]) -> str:
        """确定决策策略"""
        # 关键决策类别需要人类参与
        if request.category in self.auto_approve_rules["require_human_categories"]:
            return "human"

        # 高风险需要人类审核
        if analysis["risk_assessment"] > 0.6:
            return "human"

        # 多利益相关者需要人类协调
        if request.stakeholders and len(request.stakeholders) >= self.auto_approve_rules["stakeholder_threshold"]:
            return "human"

        # 高置信度可以自动决策
        if analysis["recommendation_confidence"] >= self.auto_approve_rules["auto_approve_confidence"]:
            return "auto"

        # 紧急决策可以快速处理
        if request.urgency == DecisionUrgency.CRITICAL:
            return "auto"

        # 默认人机协作
        return "human"

    async def _auto_decision(self, request: DecisionRequest, analysis: dict[str, Any]) -> DecisionResult:
        """自动决策"""
        chosen = analysis["recommended_option"]

        print(f"\n✨ 自动决策: 选择 '{chosen['title']}'")
        print(f"   理由: 高置信度({chosen['confidence']:.2f}),低风险")

        return DecisionResult(
            chosen_option=chosen["id"],
            confidence=chosen["confidence"],
            rationale=f"AI自动决策 - 置信度: {chosen['confidence']:.2f}",
            timestamp=datetime.now()
        )

    async def _human_assisted_decision(self, request: DecisionRequest, analysis: dict[str, Any]) -> DecisionResult:
        """人机协作决策"""
        return await self._ask_user_for_decision(request, analysis)

    async def _ask_user_for_decision(self, request: DecisionRequest, analysis: dict[str, Any]) -> DecisionResult:
        """向用户请求决策"""
        try:
            # 使用AskUserQuestion获取用户输入
            from claude_code import ask_user_question  # Claude Code专用工具

            # 构建问题
            question = f"**{request.title}**\n\n"
            question += f"{request.description}\n\n"

            # AI推荐
            if analysis["recommended_option"]:
                question += f"🤖 **AI推荐**: {analysis['recommended_option']['title']}\n"
                question += f"置信度: {analysis['recommendation_confidence']:.2f}\n\n"

            # 约束和背景
            if request.context:
                question += "**背景信息:**\n"
                for key, value in request.context.items():
                    question += f"- {key}: {value}\n"
                question += "\n"

            # 利益相关者
            if request.stakeholders:
                question += f"**利益相关者**: {', '.join(request.stakeholders)}\n\n"

            # 准备选项
            options = []

            # 添加AI推荐作为第一个选项
            if analysis["recommended_option"]:
                rec_opt = analysis["recommended_option"]
                options.append({
                    "label": f"🤖 AI推荐: {rec_opt['title']}",
                    "description": self._format_option_description(rec_opt)
                })

            # 添加其他选项
            for opt in request.options:
                if opt["title"] != analysis["recommended_option"]["title"]:
                    options.append({
                        "label": opt["title"],
                        "description": self._format_option_description(opt)
                    })

            # 添加"需要更多信息"选项
            options.append({
                "label": "📋 需要更多信息",
                "description": "需要更多信息才能做出决策"
            })

            # 调用Claude Code的交互功能
            response = await ask_user_question(
                question=question,
                options=options,
                multi_select=False,
                required=True
            )

            # 处理响应
            if "需要更多信息" in response:
                return await self._handle_need_more_info(request, analysis)
            elif "AI推荐" in response and analysis["recommended_option"]:
                chosen = analysis["recommended_option"]
                return DecisionResult(
                    chosen_option=chosen["id"],
                    confidence=chosen["confidence"],
                    human_feedback=f"用户接受了AI推荐: {response}",
                    rationale="人机协作 - 信任AI推荐",
                    timestamp=datetime.now()
                )
            else:
                # 查找用户选择的选项
                for opt in request.options:
                    if opt["title"] in response:
                        return await self._collect_human_feedback(request, opt, response)

                # 默认选择
                return DecisionResult(
                    chosen_option=request.options.get(0)["id"],
                    confidence=0.5,
                    human_feedback=f"用户选择: {response}",
                    timestamp=datetime.now()
                )

        except ImportError:
            print("⚠️ 不在Claude Code环境,使用终端模式")
            return await self._terminal_fallback(request, analysis)

    def _format_option_description(self, option: dict[str, Any]) -> str:
        """格式化选项描述"""
        desc = option.get("description", "")

        # 添加置信度
        if option.get("confidence"):
            desc += f"\n置信度: {option['confidence']:.2f}"

        # 添加风险评估
        if option.get("risk_level"):
            risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}
            desc += f"\n风险等级: {risk_icon.get(option['risk_level'], '⚪')} {option['risk_level']}"

        # 添加成本效益
        if option.get("estimated_cost") or option.get("expected_value"):
            cost = option.get("estimated_cost", 0)
            value = option.get("expected_value", 0)
            desc += f"\n成本: {cost} | 预期价值: {value}"

        # 添加优缺点
        if option.get("pros"):
            desc += f"\n优点: {', '.join(option['pros'])}"
        if option.get("cons"):
            desc += f"\n缺点: {', '.join(option['cons'])}"

        return desc

    async def _collect_human_feedback(self, request: DecisionRequest, option: dict[str, Any], response: str) -> DecisionResult:
        """收集人类反馈"""
        # 在Claude Code环境中,可以继续使用AskUserQuestion
        try:
            from claude_code import ask_user_question

            feedback_question = f"您选择了: **{option['title']}**\n\n请提供决策理由:"

            feedback = await ask_user_question(
                question=feedback_question,
                options=[
                    "快速决策,相信直觉",
                    "基于数据和逻辑分析",
                    "考虑了所有因素后的最佳选择",
                    "风险可控,值得尝试",
                    "其他原因"
                ],
                multi_select=True
            )

            # 询问置信度
            confidence_question = "您对这个决策的信心如何?"
            confidence_options = [
                {"label": "⭐⭐⭐⭐⭐ 非常确定", "value": 5},
                {"label": "⭐⭐⭐⭐ 比较确定", "value": 4},
                {"label": "⭐⭐⭐ 中等确定", "value": 3},
                {"label": "⭐⭐ 不太确定", "value": 2},
                {"label": "⭐ 很不确定", "value": 1}
            ]

            confidence_response = await ask_user_question(
                question=confidence_question,
                options=confidence_options,
                multi_select=False
            )

            # 提取信心分数
            confidence = 3  # 默认值
            for opt in confidence_options:
                if opt["label"] in confidence_response:
                    confidence = opt["value"]
                    break

            return DecisionResult(
                chosen_option=option["id"],
                confidence=confidence / 5.0,  # 转换为0-1范围
                human_feedback=f"理由: {', '.join(feedback)} | 信心: {confidence}/5",
                rationale=f"人机协作决策 - 用户选择: {response}",
                timestamp=datetime.now()
            )

        except ImportError:
            # 回退到默认选项
            return DecisionResult(
                chosen_option=option["id"],
                confidence=option.get("confidence", 0.5),
                human_feedback=f"用户选择: {response}",
                timestamp=datetime.now()
            )

    async def _handle_need_more_info(self, request: DecisionRequest, analysis: dict[str, Any]) -> DecisionResult:
        """处理需要更多信息的情况"""
        try:
            from claude_code import ask_user_question

            info_question = "您需要什么额外信息来做决策?"

            needed_info = await ask_user_question(
                question=info_question,
                options=[
                    "成本分析详情",
                    "风险评估报告",
                    "时间线安排",
                    "资源需求说明",
                    "成功案例参考",
                    "其他信息"
                ],
                multi_select=True
            )

            return DecisionResult(
                chosen_option="need_more_info",
                confidence=0.0,
                human_feedback=f"需要更多信息: {', '.join(needed_info)}",
                rationale="决策延期 - 需要补充信息",
                timestamp=datetime.now()
            )

        except ImportError:
            # 回退到默认响应
            return DecisionResult(
                chosen_option="need_more_info",
                confidence=0.0,
                human_feedback="需要更多信息",
                timestamp=datetime.now()
            )

    async def _terminal_fallback(self, request: DecisionRequest, analysis: dict[str, Any]) -> DecisionResult:
        """终端模式回退"""
        print("\n💬 终端模式交互")
        print("="*50)

        # 显示基本信息
        print(f"问题: {request.title}")
        print(f"描述: {request.description}")

        # 显示AI推荐
        if analysis["recommended_option"]:
            rec = analysis["recommended_option"]
            print(f"\n🤖 AI推荐: {rec['title']}")
            print(f"置信度: {rec['confidence']:.2f}")

        # 显示选项
        print("\n📝 选项:")
        for i, opt in enumerate(request.options, 1):
            print(f"  {i}. {opt['title']}")

        # 获取用户输入
        try:
            choice = input("\n请选择 (输入数字): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(request.options):
                    chosen = request.options.get(idx)
                    return DecisionResult(
                        chosen_option=chosen["id"],
                        confidence=chosen.get("confidence", 0.5),
                        human_feedback="终端模式选择",
                        timestamp=datetime.now()
                    )
        except (EOFError, KeyboardInterrupt):
            # 用户中断,返回AI推荐
            pass

        # 默认返回AI推荐
        return DecisionResult(
            chosen_option=analysis["recommended_option"]["id"],
            confidence=analysis["recommendation_confidence"],
            human_feedback="使用AI推荐",
            timestamp=datetime.now()
        )

    def get_decision_insights(self) -> dict[str, Any]:
        """获取决策洞察"""
        if not self.decision_history:
            return {"message": "暂无决策记录"}

        return {
            "total_decisions": len(self.decision_history),
            "auto_decisions": len([d for d in self.decision_history if not d.human_feedback]),
            "human_decisions": len([d for d in self.decision_history if d.human_feedback]),
            "avg_confidence": sum(d.confidence for d in self.decision_history) / len(self.decision_history),
            "decision_categories": self._analyze_categories()
        }

    def _analyze_categories(self) -> dict[str, int]:
        """分析决策类别分布"""
        categories = {}
        for _decision in self.decision_history:
            # 这里需要在决策中存储类别信息
            pass
        return categories


# 使用示例
async def claude_code_demo():
    """Claude Code环境演示"""
    print("🚀 Claude Code人机协作决策系统")
    print("="*50)

    engine = ClaudeCodeHITLDecisionEngine()

    # 示例1: 技术决策
    tech_request = DecisionRequest(
        title="选择前端框架",
        description="为新项目选择最合适的前端框架",
        category=DecisionCategory.TECHNICAL,
        urgency=DecisionUrgency.MEDIUM,
        stakeholders=["开发团队", "产品经理"],
        context={
            "项目规模": "中型",
            "团队经验": "React和Vue都有经验",
            "时间要求": "3个月内完成"
        },
        options=[
            {
                "title": "React 18",
                "description": "使用最新React版本",
                "confidence": 0.8,
                "pros": ["生态丰富", "团队熟悉", "性能优秀"],
                "cons": ["包体积大", "学习曲线"],
                "risk_level": "low"
            },
            {
                "title": "Vue 3",
                "description": "使用Vue 3 Composition API",
                "confidence": 0.7,
                "pros": ["易学易用", "包体积小", "中文文档好"],
                "cons": ["生态相对较小"],
                "risk_level": "low"
            },
            {
                "title": "Next.js",
                "description": "全栈React框架",
                "confidence": 0.6,
                "pros": ["SSR支持", "SEO友好", "全栈方案"],
                "cons": ["学习成本高", "过度设计"],
                "risk_level": "medium"
            }
        ]
    )

    result = await engine.make_decision(tech_request)
    print(f"\n✅ 决策完成: {result.chosen_option}")

    # 显示洞察
    insights = engine.get_decision_insights()
    print("\n📊 决策洞察:")
    for key, value in insights.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(claude_code_demo())
