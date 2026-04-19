from __future__ import annotations
"""
高级自主决策引擎
基于论文中的先进方法实现增强的决策能力
"""
import logging
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class DecisionStrategy(Enum):
    """决策策略"""

    REACTIVE = "reactive"  # 反应式决策
    PROACTIVE = "proactive"  # 主动式决策
    COLLABORATIVE = "collaborative"  # 协作式决策
    LEARNING_BASED = "learning_based"  # 学习型决策
    EMOTION_AWARE = "emotion_aware"  # 情感感知决策


class ComplexityLevel(Enum):
    """决策复杂度"""

    SIMPLE = "simple"  # 简单决策
    MODERATE = "moderate"  # 中等复杂度
    COMPLEX = "complex"  # 复杂决策
    CRITICAL = "critical"  # 关键决策


@dataclass
class DecisionContext:
    """决策上下文"""

    situation: str  # 当前情境
    goals: list[str]  # 目标列表
    constraints: dict[str, Any]  # 约束条件
    resources: dict[str, float]  # 可用资源
    emotional_state: dict[str, float]  # 情感状态
    historical_performance: dict[str, float] = field(default_factory=dict)
    environmental_factors: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionOption:
    """决策选项"""

    id: str
    description: str
    actions: list[dict[str, Any]]
    expected_outcomes: dict[str, float]
    confidence: float
    resource_requirements: dict[str, float]
    risk_level: float
    time_estimate: timedelta
    prerequisites: list[str] = field(default_factory=list)
    side_effects: list[str] = field(default_factory=list)


@dataclass
class DecisionResult:
    """决策结果"""

    id: str
    context: DecisionContext
    selected_option: DecisionOption
    reasoning: str
    confidence: float
    strategy: DecisionStrategy
    execution_plan: list[dict[str, Any]]
    expected_benefits: dict[str, float]
    risk_assessment: dict[str, float]
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: datetime | None = None
    outcome: dict[str, Any] | None = None


class AdvancedDecisionEngine:
    """高级自主决策引擎"""

    def __init__(self):
        # 决策历史
        self.decision_history = deque(maxlen=1000)

        # 知识图谱
        self.knowledge_graph = nx.DiGraph()

        # 学习模型
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.decision_embeddings = []
        self.outcome_embeddings = []

        # 性能指标
        self.performance_metrics = {
            "total_decisions": 0,
            "successful_decisions": 0,
            "average_confidence": 0.0,
            "decision_speed": 0.0,
            "learning_rate": 0.1,
        }

        # 决策权重配置
        self.strategy_weights = {
            DecisionStrategy.REACTIVE: 0.2,
            DecisionStrategy.PROACTIVE: 0.25,
            DecisionStrategy.COLLABORATIVE: 0.25,
            DecisionStrategy.LEARNING_BASED: 0.2,
            DecisionStrategy.EMOTION_AWARE: 0.1,
        }

    async def analyze_situation(self, context: DecisionContext) -> dict[str, Any]:
        """分析当前情境"""
        try:
            analysis = {
                "complexity": self._assess_complexity(context),
                "urgency": self._assess_urgency(context),
                "resource_availability": self._assess_resources(context),
                "emotional_impact": self._assess_emotional_impact(context),
                "historical_patterns": self._find_historical_patterns(context),
                "risk_factors": self._identify_risk_factors(context),
            }
            return analysis
        except Exception as e:
            logger.error(f"情境分析失败: {e}")
            return {}

    def _assess_complexity(self, context: DecisionContext) -> ComplexityLevel:
        """评估决策复杂度"""
        complexity_score = 0

        # 目标数量
        complexity_score += len(context.goals) * 0.2

        # 约束条件
        complexity_score += len(context.constraints) * 0.15

        # 资源限制
        limited_resources = sum(1 for v in context.resources.values() if v < 0.5)
        complexity_score += limited_resources * 0.3

        # 环境因素
        complexity_score += len(context.environmental_factors) * 0.1

        if complexity_score < 1:
            return ComplexityLevel.SIMPLE
        elif complexity_score < 2:
            return ComplexityLevel.MODERATE
        elif complexity_score < 3:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.CRITICAL

    def _assess_urgency(self, context: DecisionContext) -> float:
        """评估紧急程度"""
        urgency = 0.0

        # 时间约束
        if "deadline" in context.constraints:
            deadline = context.constraints["deadline"]
            if isinstance(deadline, datetime):
                time_remaining = (deadline - datetime.now()).total_seconds()
                urgency = max(0, 1 - time_remaining / 3600)  # 小时为单位

        # 资源紧张度
        resource_pressure = sum(1 for v in context.resources.values() if v < 0.3)
        urgency += resource_pressure * 0.2

        return min(1.0, urgency)

    def _assess_resources(self, context: dict[str, float]) -> dict[str, str]:
        """评估资源可用性"""
        assessment = {}
        for resource, amount in context.items():
            if amount >= 0.8:
                assessment[resource] = "充足"
            elif amount >= 0.5:
                assessment[resource] = "适中"
            elif amount >= 0.3:
                assessment[resource] = "紧张"
            else:
                assessment[resource] = "严重不足"
        return assessment

    def _assess_emotional_impact(self, context: DecisionContext) -> float:
        """评估情感影响"""
        # 计算情感强度
        emotion_intensity = sum(abs(v) for v in context.emotional_state.values())
        return min(1.0, emotion_intensity / len(context.emotional_state))

    def _find_historical_patterns(self, context: DecisionContext) -> list[dict[str, Any]]:
        """查找历史模式"""
        patterns = []

        # 简单的相似性匹配
        for decision in list(self.decision_history)[-10:]:  # 最近10个决策
            similarity = self._calculate_context_similarity(context, decision.context)
            if similarity > 0.7:
                patterns.append(
                    {"similarity": similarity, "decision": decision, "outcome": decision.outcome}
                )

        return sorted(patterns, key=lambda x: x["similarity"], reverse=True)

    def _calculate_context_similarity(
        self, context1: DecisionContext, context2: DecisionContext
    ) -> float:
        """计算情境相似度"""
        # 简单的相似度计算
        goal_similarity = len(set(context1.goals) & set(context2.goals)) / max(
            len(set(context1.goals) | set(context2.goals)), 1
        )

        # 情感相似度
        emotion_similarity = 0
        for emotion in context1.emotional_state:
            if emotion in context2.emotional_state:
                diff = abs(context1.emotional_state[emotion] - context2.emotional_state[emotion])
                emotion_similarity += 1 - diff
        emotion_similarity /= max(len(context1.emotional_state), 1)

        return (goal_similarity + emotion_similarity) / 2

    def _identify_risk_factors(self, context: DecisionContext) -> list[str]:
        """识别风险因素"""
        risks = []

        # 资源风险
        for resource, amount in context.resources.items():
            if amount < 0.3:
                risks.append(f"{resource}资源严重不足")

        # 时间风险
        if "deadline" in context.constraints:
            deadline = context.constraints["deadline"]
            if isinstance(deadline, datetime):
                if (deadline - datetime.now()).total_seconds() < 1800:  # 30分钟内
                    risks.append("时间紧迫,决策风险高")

        # 情感风险
        negative_emotions = ["worry", "frustration", "fear"]
        for emotion in negative_emotions:
            if emotion in context.emotional_state and context.emotional_state[emotion] > 0.7:
                risks.append(f"高{emotion}情绪可能影响决策质量")

        return risks

    async def generate_options(
        self, context: DecisionContext, analysis: dict[str, Any]
    ) -> list[DecisionOption]:
        """生成决策选项"""
        try:
            options = []

            # 基于不同策略生成选项
            strategies = self._select_strategies(context, analysis)

            for strategy in strategies:
                strategy_options = await self._generate_strategy_options(context, strategy)
                options.extend(strategy_options)

            # 评估和排序选项
            evaluated_options = await self._evaluate_options(options, context)

            return sorted(evaluated_options, key=lambda x: x.confidence, reverse=True)[
                :5
            ]  # 返回前5个最佳选项

        except Exception as e:
            logger.error(f"生成决策选项失败: {e}")
            return []

    def _select_strategies(
        self, context: DecisionContext, analysis: dict[str, Any]
    ) -> list[DecisionStrategy]:
        """选择决策策略"""
        strategies = []

        # 基于复杂度选择策略
        complexity = analysis.get("complexity", ComplexityLevel.MODERATE)
        if complexity == ComplexityLevel.SIMPLE:
            strategies.append(DecisionStrategy.REACTIVE)
        elif complexity == ComplexityLevel.COMPLEX:
            strategies.append(DecisionStrategy.COLLABORATIVE)
        elif complexity == ComplexityLevel.CRITICAL:
            strategies.append(DecisionStrategy.LEARNING_BASED)

        # 基于紧急程度选择策略
        urgency = analysis.get("urgency", 0.5)
        if urgency > 0.7:
            strategies.append(DecisionStrategy.REACTIVE)
        else:
            strategies.append(DecisionStrategy.PROACTIVE)

        # 基于情感影响选择策略
        emotional_impact = analysis.get("emotional_impact", 0.5)
        if emotional_impact > 0.6:
            strategies.append(DecisionStrategy.EMOTION_AWARE)

        # 确保至少有一个策略
        if not strategies:
            strategies.append(DecisionStrategy.PROACTIVE)

        return strategies

    async def _generate_strategy_options(
        self, context: DecisionContext, strategy: DecisionStrategy
    ) -> list[DecisionOption]:
        """基于特定策略生成选项"""
        options = []

        if strategy == DecisionStrategy.REACTIVE:
            options.extend(self._generate_reactive_options(context))
        elif strategy == DecisionStrategy.PROACTIVE:
            options.extend(self._generate_proactive_options(context))
        elif strategy == DecisionStrategy.COLLABORATIVE:
            options.extend(self._generate_collaborative_options(context))
        elif strategy == DecisionStrategy.LEARNING_BASED:
            options.extend(self._generate_learning_options(context))
        elif strategy == DecisionStrategy.EMOTION_AWARE:
            options.extend(self._generate_emotion_aware_options(context))

        return options

    def _generate_reactive_options(self, context: DecisionContext) -> list[DecisionOption]:
        """生成反应式选项"""
        options = []

        # 简单直接的选项
        for goal in context.goals:
            option = DecisionOption(
                id=str(uuid.uuid4()),
                description=f"直接执行{goal}",
                actions=[{"type": "execute", "target": goal, "method": "direct"}],
                expected_outcomes={"goal_achievement": 0.6, "efficiency": 0.8},
                confidence=0.7,
                resource_requirements={"time": 0.3, "cpu": 0.4},
                risk_level=0.3,
                time_estimate=timedelta(minutes=10),
            )
            options.append(option)

        return options

    def _generate_proactive_options(self, context: DecisionContext) -> list[DecisionOption]:
        """生成主动式选项"""
        options = []

        # 预防性措施
        option = DecisionOption(
            id=str(uuid.uuid4()),
            description="制定预防性计划以应对潜在风险",
            actions=[
                {"type": "analyze", "target": "risks"},
                {"type": "plan", "target": "prevention"},
                {"type": "implement", "target": "safeguards"},
            ],
            expected_outcomes={"risk_reduction": 0.8, "stability": 0.9},
            confidence=0.8,
            resource_requirements={"time": 0.6, "cpu": 0.3},
            risk_level=0.2,
            time_estimate=timedelta(minutes=30),
        )
        options.append(option)

        return options

    def _generate_collaborative_options(self, context: DecisionContext) -> list[DecisionOption]:
        """生成协作式选项"""
        options = []

        # 协作决策
        option = DecisionOption(
            id=str(uuid.uuid4()),
            description="与小诺协作制定最优方案",
            actions=[
                {"type": "consult", "target": "xiaonuo"},
                {"type": "collaborate", "target": "decision_making"},
                {"type": "synthesize", "target": "solution"},
            ],
            expected_outcomes={"decision_quality": 0.9, "team_satisfaction": 0.95},
            confidence=0.85,
            resource_requirements={"time": 0.5, "communication": 0.7},
            risk_level=0.1,
            time_estimate=timedelta(minutes=20),
        )
        options.append(option)

        return options

    def _generate_learning_options(self, context: DecisionContext) -> list[DecisionOption]:
        """生成学习型选项"""
        options = []

        # 基于历史学习的选项
        patterns = self._find_historical_patterns(context)
        if patterns:
            best_pattern = patterns[0]
            option = DecisionOption(
                id=str(uuid.uuid4()),
                description=f"基于历史成功经验调整方案(相似度: {best_pattern['similarity']:.2f})",
                actions=[
                    {"type": "analyze", "target": "historical_pattern"},
                    {"type": "adapt", "target": "strategy"},
                    {"type": "apply", "target": "learned_solution"},
                ],
                expected_outcomes={
                    "success_probability": best_pattern["similarity"],
                    "learning_gain": 0.7,
                },
                confidence=best_pattern["similarity"] * 0.9,
                resource_requirements={"time": 0.4, "analysis": 0.6},
                risk_level=0.2,
                time_estimate=timedelta(minutes=25),
            )
            options.append(option)

        return options

    def _generate_emotion_aware_options(self, context: DecisionContext) -> list[DecisionOption]:
        """生成情感感知选项"""
        options = []

        # 考虑情感因素的选项
        dominant_emotion = max(context.emotional_state.items(), key=lambda x: x[1])

        if dominant_emotion[0] in ["confidence", "joy"]:
            # 积极情绪:采取更积极的策略
            option = DecisionOption(
                id=str(uuid.uuid4()),
                description=f"利用当前的{dominant_emotion[0]}状态推进目标",
                actions=[
                    {"type": "leverage", "target": "positive_emotion"},
                    {"type": "accelerate", "target": "goal_achievement"},
                ],
                expected_outcomes={"momentum": 0.8, "motivation": 0.9},
                confidence=0.8,
                resource_requirements={"energy": 0.6, "focus": 0.7},
                risk_level=0.2,
                time_estimate=timedelta(minutes=15),
            )
        else:
            # 消极情绪:采取缓解策略
            option = DecisionOption(
                id=str(uuid.uuid4()),
                description=f"先处理{dominant_emotion[0]}情绪,再推进任务",
                actions=[
                    {"type": "address", "target": "negative_emotion"},
                    {"type": "stabilize", "target": "emotional_state"},
                    {"type": "proceed", "target": "goal_achievement"},
                ],
                expected_outcomes={"emotional_balance": 0.9, "sustainable_progress": 0.8},
                confidence=0.75,
                resource_requirements={"emotional_support": 0.8, "time": 0.5},
                risk_level=0.1,
                time_estimate=timedelta(minutes=20),
            )

        options.append(option)
        return options

    async def _evaluate_options(
        self, options: list[DecisionOption], context: DecisionContext
    ) -> list[DecisionOption]:
        """评估决策选项"""
        evaluated_options = []

        for option in options:
            # 多维度评估
            scores = {
                "feasibility": self._evaluate_feasibility(option, context),
                "efficiency": self._evaluate_efficiency(option, context),
                "risk_acceptability": self._evaluate_risk(option, context),
                "resource_optimization": self._evaluate_resource_usage(option, context),
                "alignment": self._evaluate_goal_alignment(option, context),
            }

            # 综合评分
            weights = {
                "feasibility": 0.25,
                "efficiency": 0.2,
                "risk_acceptability": 0.2,
                "resource_optimization": 0.15,
                "alignment": 0.2,
            }
            total_score = sum(scores[k] * weights[k] for k in scores)

            # 更新选项置信度
            option.confidence = total_score
            evaluated_options.append(option)

        return evaluated_options

    def _evaluate_feasibility(self, option: DecisionOption, context: DecisionContext) -> float:
        """评估可行性"""
        # 检查资源是否足够
        for resource, required in option.resource_requirements.items():
            if resource in context.resources and context.resources[resource] < required:
                return 0.3  # 资源不足,可行性低
        return 0.9

    def _evaluate_efficiency(self, option: DecisionOption, context: DecisionContext) -> float:
        """评估效率"""
        # 基于时间估计和预期结果计算效率
        time_hours = option.time_estimate.total_seconds() / 3600
        outcome_sum = sum(option.expected_outcomes.values())

        if time_hours > 0:
            return min(1.0, outcome_sum / time_hours)
        return 0.5

    def _evaluate_risk(self, option: DecisionOption, context: DecisionContext) -> float:
        """评估风险可接受性"""
        # 风险越低,可接受性越高
        return 1.0 - option.risk_level

    def _evaluate_resource_usage(self, option: DecisionOption, context: DecisionContext) -> float:
        """评估资源使用优化"""
        # 计算资源使用效率
        total_required = sum(option.resource_requirements.values())
        outcome_sum = sum(option.expected_outcomes.values())

        if total_required > 0:
            return min(1.0, outcome_sum / total_required)
        return 0.5

    def _evaluate_goal_alignment(self, option: DecisionOption, context: DecisionContext) -> float:
        """评估目标对齐度"""
        # 简单的关键词匹配
        alignment = 0
        for goal in context.goals:
            if goal.lower() in option.description.lower():
                alignment += 0.5
        return min(1.0, alignment)

    async def make_advanced_decision(self, context: DecisionContext) -> DecisionResult:
        """做出高级决策"""
        try:
            # 记录决策开始
            decision_start = datetime.now()

            # 1. 分析情境
            logger.info("开始分析决策情境...")
            analysis = await self.analyze_situation(context)

            # 2. 生成选项
            logger.info("生成决策选项...")
            options = await self.generate_options(context, analysis)

            if not options:
                raise ValueError("无法生成有效的决策选项")

            # 3. 选择最佳选项
            best_option = options[0]  # 已经按置信度排序

            # 4. 生成执行计划
            execution_plan = await self._generate_execution_plan(best_option, context)

            # 5. 评估收益和风险
            expected_benefits = best_option.expected_outcomes
            risk_assessment = await self._assess_decision_risks(best_option, context)

            # 6. 生成推理过程
            reasoning = await self._generate_reasoning(context, analysis, best_option)

            # 7. 创建决策结果
            decision_result = DecisionResult(
                id=str(uuid.uuid4()),
                context=context,
                selected_option=best_option,
                reasoning=reasoning,
                confidence=best_option.confidence,
                strategy=analysis.get("selected_strategy", DecisionStrategy.PROACTIVE),
                execution_plan=execution_plan,
                expected_benefits=expected_benefits,
                risk_assessment=risk_assessment,
                created_at=decision_start,
            )

            # 8. 更新性能指标
            self._update_performance_metrics(decision_result)

            # 9. 存储决策历史
            self.decision_history.append(decision_result)

            # 10. 更新学习模型
            await self._update_learning_model(decision_result)

            logger.info(f"决策完成,置信度: {decision_result.confidence:.2f}")
            return decision_result

        except Exception as e:
            logger.error(f"高级决策失败: {e}")
            raise

    async def _generate_execution_plan(
        self, option: DecisionOption, context: DecisionContext
    ) -> list[dict[str, Any]]:
        """生成执行计划"""
        plan = []

        # 将选项动作转换为具体步骤
        for i, action in enumerate(option.actions):
            step = {
                "step": i + 1,
                "action": action["type"],
                "target": action["target"],
                "method": action.get("method", "standard"),
                "estimated_time": option.time_estimate.total_seconds() / len(option.actions),
                "dependencies": action.get("dependencies", []),
                "success_criteria": action.get("success_criteria", ["completion"]),
            }
            plan.append(step)

        # 添加验证步骤
        plan.append(
            {
                "step": len(plan) + 1,
                "action": "verify",
                "target": "outcomes",
                "method": "comprehensive_check",
                "estimated_time": 300,  # 5分钟验证
                "dependencies": [s["step"] for s in plan[:-1]],
                "success_criteria": ["all_objectives_met", "quality_standard"],
            }
        )

        return plan

    async def _assess_decision_risks(
        self, option: DecisionOption, context: DecisionContext
    ) -> dict[str, float]:
        """评估决策风险"""
        risks = {
            "execution_risk": option.risk_level,
            "resource_risk": 0.0,
            "time_risk": 0.0,
            "dependency_risk": 0.0,
            "external_risk": 0.0,
        }

        # 资源风险
        for resource, required in option.resource_requirements.items():
            if resource in context.resources:
                shortage = max(0, required - context.resources[resource])
                risks["resource_risk"] = max(risks["resource_risk"], shortage)

        # 时间风险
        if "deadline" in context.constraints:
            deadline = context.constraints["deadline"]
            if isinstance(deadline, datetime):
                time_available = (deadline - datetime.now()).total_seconds()
                if option.time_estimate.total_seconds() > time_available:
                    risks["time_risk"] = 1.0

        # 依赖风险
        risks["dependency_risk"] = len(option.prerequisites) * 0.1

        # 外部风险(环境因素)
        risks["external_risk"] = len(context.environmental_factors) * 0.05

        return risks

    async def _generate_reasoning(
        self, context: DecisionContext, analysis: dict[str, Any], option: DecisionOption
    ) -> str:
        """生成决策推理"""
        reasoning_parts = [
            f"基于当前情境分析(复杂度: {analysis.get('complexity', 'unknown')})",
            f"识别到 {len(analysis.get('risk_factors', []))} 个风险因素",
            f"考虑了 {len(context.goals)} 个目标",
            f"选择了置信度最高的选项({option.confidence:.2f})",
            f"预计需要 {option.time_estimate.total_seconds()/60:.0f} 分钟执行",
        ]

        return "; ".join(reasoning_parts)

    def _update_performance_metrics(self, decision: DecisionResult) -> Any:
        """更新性能指标"""
        self.performance_metrics["total_decisions"] += 1

        # 更新平均置信度
        total = self.performance_metrics["total_decisions"]
        current_avg = self.performance_metrics["average_confidence"]
        self.performance_metrics["average_confidence"] = (
            current_avg * (total - 1) + decision.confidence
        ) / total

    async def _update_learning_model(self, decision: DecisionResult):
        """更新学习模型"""
        # 将决策向量化

        # 这里可以实现更复杂的机器学习模型更新
        # 简化实现:更新决策嵌入
        try:
            # 维护决策历史向量
            if len(self.decision_embeddings) > 1000:
                self.decision_embeddings = self.decision_embeddings[-500:]

            logger.debug("学习模型已更新")
        except Exception as e:
            logger.warning(f"学习模型更新失败: {e}")

    async def learn_from_outcome(self, decision_id: str, outcome: dict[str, Any]):
        """从决策结果中学习"""
        try:
            # 查找决策
            decision = None
            for d in self.decision_history:
                if d.id == decision_id:
                    decision = d
                    break

            if not decision:
                logger.warning(f"未找到决策: {decision_id}")
                return

            # 更新决策结果
            decision.outcome = outcome
            decision.executed_at = datetime.now()

            # 计算实际收益与预期收益的差异
            outcome.get("benefits", {})

            # 更新学习率
            success_rate = outcome.get("success_rate", 0.0)
            if success_rate > 0.8:
                self.performance_metrics["successful_decisions"] += 1

                # 成功决策,增强相似策略的权重
                self.performance_metrics["learning_rate"] = min(
                    0.5, self.performance_metrics["learning_rate"] * 1.1
                )
            else:
                # 失败决策,降低相似策略的权重
                self.performance_metrics["learning_rate"] = max(
                    0.05, self.performance_metrics["learning_rate"] * 0.9
                )

            logger.info(f"从决策结果中学习,成功率: {success_rate:.2f}")

        except Exception as e:
            logger.error(f"学习失败: {e}")

    def get_performance_summary(self) -> dict[str, Any]:
        """获取性能摘要"""
        total = self.performance_metrics["total_decisions"]
        if total == 0:
            return {"message": "暂无决策数据"}

        success_rate = self.performance_metrics["successful_decisions"] / total

        return {
            "total_decisions": total,
            "successful_decisions": self.performance_metrics["successful_decisions"],
            "success_rate": success_rate,
            "average_confidence": self.performance_metrics["average_confidence"],
            "learning_rate": self.performance_metrics["learning_rate"],
            "recent_decisions": len(
                [d for d in self.decision_history if (datetime.now() - d.created_at).days <= 7]
            ),
        }


# 全局高级决策引擎实例
advanced_decision_engine = AdvancedDecisionEngine()
