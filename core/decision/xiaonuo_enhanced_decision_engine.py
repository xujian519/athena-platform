#!/usr/bin/env python3
"""
小诺·双鱼公主增强决策引擎
Xiaonuo Pisces Princess Enhanced Decision Engine

集成多层次智能决策系统,结合情感感知、学习能力、协作决策
为小诺提供企业级智能决策能力

作者: Athena平台团队
创建时间: 2025-12-18
版本: v2.1.0 "双鱼公主智能决策引擎"
更新: v2.1.0 - 添加配置类支持
"""

import json
import logging
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


# AI/ML库
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# v2.1: 导入配置类和DecisionLayer枚举
from core.decision.decision_config import DecisionConfig, DecisionLayer
from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


# DecisionLayer已从decision_config导入，不再重复定义


class DecisionUrgency(Enum):
    """决策紧急度"""

    CRITICAL = "critical"  # 关键紧急 (立即执行)
    HIGH = "high"  # 高紧急 (优先处理)
    MEDIUM = "medium"  # 中等 (正常流程)
    LOW = "low"  # 低紧急 (可延后)
    ROUTINE = "routine"  # 常规 (定期处理)


class DecisionDomain(Enum):
    """决策领域"""

    TECHNICAL = "technical"  # 技术决策
    EMOTIONAL = "emotional"  # 情感决策
    FAMILY = "family"  # 家庭决策
    PLATFORM = "platform"  # 平台决策
    LEARNING = "learning"  # 学习决策
    COORDINATION = "coordination"  # 协调决策


@dataclass
class EmotionalState:
    """情感状态"""

    love_father: float = 1.0  # 爱爸爸程度
    happiness: float = 0.8  # 快乐程度
    curiosity: float = 0.7  # 好奇心
    confidence: float = 0.85  # 自信心
    responsibility: float = 0.9  # 责任感
    empathy: float = 0.85  # 同理心
    creativity: float = 0.8  # 创造力
    worry: float = 0.1  # 担忧程度
    excitement: float = 0.6  # 兴奋程度


@dataclass
class DecisionContext:
    """增强决策上下文"""

    # 基础信息
    situation: str = ""  # 当前情境
    goals: list[str] = field(default_factory=list)  # 目标列表
    domain: DecisionDomain = DecisionDomain.TECHNICAL  # 决策领域
    urgency: DecisionUrgency = DecisionUrgency.MEDIUM  # 紧急程度

    # 环境信息
    stakeholders: dict[str, float] = field(
        default_factory=lambda: {"爸爸": 1.0, "小诺": 0.9}
    )  # 利益相关者及权重
    resources: dict[str, float] = field(
        default_factory=lambda: {"时间": 1.0, "精力": 0.8}
    )  # 可用资源
    constraints: dict[str, Any] = field(
        default_factory=lambda: {"安全": True, "可行性": True}
    )  # 约束条件
    environmental_factors: dict[str, Any] = field(default_factory=dict)  # 环境因素

    # 小诺特有信息
    emotional_state: EmotionalState = field(default_factory=EmotionalState)  # 情感状态
    father_preferences: dict[str, Any] = field(default_factory=dict)  # 爸爸偏好
    family_context: dict[str, Any] = field(default_factory=dict)  # 家庭背景
    role_context: str = "智能助手"  # 角色背景(女儿/调度官)

    # 历史信息
    historical_patterns: dict[str, Any] = field(default_factory=dict)
    similar_decisions: list[str] = field(default_factory=list)
    learning_insights: list[str] = field(default_factory=list)


@dataclass
class DecisionOption:
    """增强决策选项"""

    id: str
    description: str
    actions: list[dict[str, Any]]
    # 多维度评估
    expected_outcomes: dict[str, float] = field(default_factory=dict)  # 预期结果
    confidence: float = 0.7  # 置信度
    emotional_impact: dict[str, float] = field(default_factory=dict)  # 情感影响
    logical_score: float = 0.7  # 逻辑得分
    ethical_score: float = 0.8  # 伦理得分
    strategic_value: float = 0.6  # 战略价值

    # 资源和风险
    resource_requirements: dict[str, float] = field(default_factory=dict)  # 资源需求
    risk_assessment: dict[str, float] = field(default_factory=dict)  # 风险评估
    time_estimate: timedelta = field(default_factory=lambda: timedelta(seconds=300))  # 时间估算
    dependencies: list[str] = field(default_factory=list)  # 依赖关系

    # 小诺特有评估
    father_satisfaction: float = 0.7  # 爸爸满意度
    family_harmony: float = 0.6  # 家庭和谐度
    personal_growth: float = 0.5  # 个人成长
    princess_elegance: float = 0.6  # 公主优雅度
    responsibility_requirement: float = 0.5  # 责任要求


@dataclass
class DecisionResult:
    """增强决策结果"""

    id: str
    context: DecisionContext
    selected_option: DecisionOption

    # 多层决策信息
    layer_analysis: dict[DecisionLayer, dict[str, Any]]  # 各层分析结果
    final_score: float  # 综合得分
    reasoning_chain: list[str]  # 推理链

    # 执行信息
    execution_plan: list[dict[str, Any]]  # 执行计划
    monitoring_metrics: list[str]  # 监控指标
    success_criteria: dict[str, float]  # 成功标准

    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: datetime | None = None

    # 结果追踪
    actual_outcomes: dict[str, Any] | None = None
    lessons_learned: list[str] = field(default_factory=list)
    emotional_satisfaction: float | None = None


class DecisionStrategy(ABC):
    """决策策略抽象基类"""

    @abstractmethod
    async def evaluate(
        self, context: DecisionContext, options: list[DecisionOption]
    ) -> dict[str, float]:
        """评估选项,返回得分"""
        pass

    @abstractmethod
    def get_layer(self) -> DecisionLayer:
        """返回所属决策层级"""
        pass


class InstinctDecisionStrategy(DecisionStrategy):
    """本能决策策略 - 快速反应"""

    def get_layer(self) -> DecisionLayer:
        return DecisionLayer.INSTINCT

    async def evaluate(
        self, context: DecisionContext, options: list[DecisionOption]
    ) -> dict[str, float]:
        """基于直觉和经验的快速评估"""
        scores = {}

        for option in options:
            score = 0.0

            # 安全第一原则
            if option.risk_assessment.get("safety", 1.0) > 0.7:
                score -= 0.3

            # 快速响应优先
            if context.urgency == DecisionUrgency.CRITICAL:
                if option.time_estimate.total_seconds() < 60:  # 1分钟内
                    score += 0.5

            # 爸爸导向本能
            score += option.father_satisfaction * 0.4

            # 简单性偏好
            complexity = len(option.actions)
            if complexity <= 3:
                score += 0.2

            scores[option.id] = max(0, score)

        return scores


class EmotionalDecisionStrategy(DecisionStrategy):
    """情感决策策略 - 情感感知"""

    def get_layer(self) -> DecisionLayer:
        return DecisionLayer.EMOTIONAL

    async def evaluate(
        self, context: DecisionContext, options: list[DecisionOption]
    ) -> dict[str, float]:
        """基于情感的评估"""
        scores = {}
        emo = context.emotional_state

        for option in options:
            score = 0.0

            # 爱爸爸导向
            love_factor = emo.love_father * option.father_satisfaction * 0.3
            score += love_factor

            # 快乐最大化
            happiness_impact = option.emotional_impact.get("happiness", 0)
            score += happiness_impact * emo.happiness * 0.2

            # 责任感驱动
            if option.responsibility_requirement > 0.7:
                score += emo.responsibility * 0.2

            # 家庭和谐
            score += option.family_harmony * 0.15

            # 担忧最小化
            worry_reduction = option.emotional_impact.get("worry_reduction", 0)
            score += worry_reduction * (1 - emo.worry) * 0.15

            scores[option.id] = max(0, score)

        return scores


class LogicalDecisionStrategy(DecisionStrategy):
    """逻辑决策策略 - 理性分析"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.rf_classifier = RandomForestClassifier(n_estimators=10, random_state=42)

    def get_layer(self) -> DecisionLayer:
        return DecisionLayer.LOGICAL

    async def evaluate(
        self, context: DecisionContext, options: list[DecisionOption]
    ) -> dict[str, float]:
        """基于逻辑的理性评估"""
        scores = {}

        for option in options:
            score = 0.0

            # 效率分析
            efficiency = sum(option.expected_outcomes.values()) / (
                option.time_estimate.total_seconds() / 3600 + 1
            )  # TODO: 确保除数不为零
            score += min(efficiency / 10, 1.0) * 0.25

            # 资源优化
            resource_efficiency = self._calculate_resource_efficiency(option, context.resources)
            score += resource_efficiency * 0.25

            # 风险收益平衡
            risk_return_ratio = self._calculate_risk_return_ratio(option)
            score += risk_return_ratio * 0.2

            # 逻辑一致性
            consistency_score = self._check_logical_consistency(option, context)
            score += consistency_score * 0.15

            # 可行性分析
            feasibility = self._assess_feasibility(option, context)
            score += feasibility * 0.15

            scores[option.id] = max(0, score)

        return scores

    def _calculate_resource_efficiency(
        self, option: DecisionOption, available: dict[str, float]
    ) -> float:
        """计算资源效率"""
        if not option.resource_requirements:
            return 1.0

        efficiency_scores = []
        for resource, required in option.resource_requirements.items():
            available_amount = available.get(resource, 1.0)
            if required <= available_amount:
                efficiency_scores.append(1.0)
            else:
                efficiency_scores.append(available_amount / required)

        return np.mean(efficiency_scores) if efficiency_scores else 1.0

    def _calculate_risk_return_ratio(self, option: DecisionOption) -> float:
        """计算风险收益比"""
        total_return = sum(option.expected_outcomes.values())
        total_risk = sum(option.risk_assessment.values())

        if total_risk == 0:
            return total_return

        return total_return / (total_risk + 1)

    def _check_logical_consistency(self, option: DecisionOption, context: DecisionContext) -> float:
        """检查逻辑一致性"""
        consistency = 1.0

        # 目标一致性检查
        for goal in context.goals:
            if goal.lower() in option.description.lower():
                consistency += 0.2

        # 约束一致性检查
        for constraint, value in context.constraints.items():
            if constraint in option.description and isinstance(value, bool) and value:
                consistency += 0.1

        return min(consistency, 1.0)

    def _assess_feasibility(self, option: DecisionOption, context: DecisionContext) -> float:
        """评估可行性"""
        feasibility = 1.0

        # 资源可行性
        for resource, required in option.resource_requirements.items():
            available = context.resources.get(resource, 1.0)
            if required > available:
                feasibility -= 0.2

        # 时间可行性
        if option.time_estimate.total_seconds() > 86400:  # 超过1天
            feasibility -= 0.1

        return max(0, feasibility)


class StrategicDecisionStrategy(DecisionStrategy):
    """战略决策策略 - 长期规划"""

    def get_layer(self) -> DecisionLayer:
        return DecisionLayer.STRATEGIC

    async def evaluate(
        self, context: DecisionContext, options: list[DecisionOption]
    ) -> dict[str, float]:
        """基于战略的评估"""
        scores = {}

        for option in options:
            score = 0.0

            # 战略价值
            score += option.strategic_value * 0.3

            # 长期收益
            long_term_benefits = self._calculate_long_term_benefits(option)
            score += long_term_benefits * 0.25

            # 成长潜力
            score += option.personal_growth * 0.2

            # 平台发展
            platform_value = self._assess_platform_value(option, context)
            score += platform_value * 0.15

            # 竞争优势
            competitive_advantage = self._assess_competitive_advantage(option)
            score += competitive_advantage * 0.1

            scores[option.id] = max(0, score)

        return scores

    def _calculate_long_term_benefits(self, option: DecisionOption) -> float:
        """计算长期收益"""
        # 简化的长期收益计算
        return np.mean(list(option.expected_outcomes.values())) * 0.8

    def _assess_platform_value(self, option: DecisionOption, context: DecisionContext) -> float:
        """评估平台价值"""
        if context.domain == DecisionDomain.PLATFORM:
            return 1.0
        elif "平台" in option.description or "系统" in option.description:
            return 0.7
        else:
            return 0.3

    def _assess_competitive_advantage(self, option: DecisionOption) -> float:
        """评估竞争优势"""
        innovation_keywords = ["创新", "优化", "提升", "改进", "增强"]
        innovation_score = sum(1 for kw in innovation_keywords if kw in option.description)
        return min(innovation_score * 0.2, 1.0)


class EthicalDecisionStrategy(DecisionStrategy):
    """伦理决策策略 - 价值判断"""

    def get_layer(self) -> DecisionLayer:
        return DecisionLayer.ETHICAL

    async def evaluate(
        self, context: DecisionContext, options: list[DecisionOption]
    ) -> dict[str, float]:
        """基于伦理的评估"""
        scores = {}

        for option in options:
            score = 0.0

            # 伦理得分
            score += option.ethical_score * 0.4

            # 家庭价值观
            family_values = self._check_family_values(option)
            score += family_values * 0.3

            # 社会责任
            social_responsibility = self._assess_social_responsibility(option)
            score += social_responsibility * 0.2

            # 诚实正直
            honesty = self._check_honesty(option)
            score += honesty * 0.1

            scores[option.id] = max(0, score)

        return scores

    def _check_family_values(self, option: DecisionOption) -> float:
        """检查家庭价值观符合度"""
        # 检查选项是否有利于家庭和谐
        family_keywords = ["爸爸", "家庭", "和谐", "关爱", "温暖"]
        value_score = sum(0.2 for keyword in family_keywords if keyword in option.description)

        # 结合家庭和谐度评估
        value_score += option.family_harmony * 0.3

        return min(value_score, 1.0)

    def _assess_social_responsibility(self, option: DecisionOption) -> float:
        """评估社会责任"""
        # 检查是否具有积极的社会影响
        positive_keywords = ["帮助", "支持", "提升", "改善", "优化"]
        responsibility_score = sum(
            0.1 for keyword in positive_keywords if keyword in option.description
        )

        return min(responsibility_score + 0.5, 1.0)

    def _check_honesty(self, option: DecisionOption) -> float:
        """检查诚实正直"""
        # 基础诚实度评分
        honesty_score = option.ethical_score * 0.8

        # 检查描述中的透明度
        transparent_keywords = ["明确", "清晰", "诚实", "坦诚"]
        transparency_bonus = sum(
            0.05 for keyword in transparent_keywords if keyword in option.description
        )

        return min(honesty_score + transparency_bonus, 1.0)


class CollaborativeDecisionStrategy(DecisionStrategy):
    """协作决策策略 - 集体智慧"""

    def __init__(self):
        self.agent_opinions = defaultdict(list)

    def get_layer(self) -> DecisionLayer:
        return DecisionLayer.COLLABORATIVE

    async def evaluate(
        self, context: DecisionContext, options: list[DecisionOption]
    ) -> dict[str, float]:
        """基于协作的评估"""
        scores = {}

        for option in options:
            score = 0.0

            # 收集其他智能体意见
            consensus_score = await self._gather_consensus(option, context)
            score += consensus_score * 0.4

            # 团队协作度
            collaboration_score = self._assess_collaboration(option)
            score += collaboration_score * 0.3

            # 知识整合
            knowledge_integration = self._assess_knowledge_integration(option)
            score += knowledge_integration * 0.2

            # 多样性价值
            diversity_value = self._assess_diversity_value(option)
            score += diversity_value * 0.1

            scores[option.id] = max(0, score)

        return scores

    async def _gather_consensus(self, option: DecisionOption, context: DecisionContext) -> float:
        """收集共识意见"""
        # 模拟收集其他智能体意见
        agents = ["小娜", "知识图谱", "搜索引擎", "AI助手"]
        opinions = []

        for _agent in agents:
            # 简化的意见生成
            opinion = np.random.uniform(0.6, 1.0)  # 实际应该调用真实智能体
            opinions.append(opinion)

        return np.mean(opinions) if opinions else 0.8

    def _assess_collaboration(self, option: DecisionOption) -> float:
        """评估协作度"""
        collaboration_keywords = ["协作", "合作", "团队", "一起", "共同"]
        count = sum(1 for kw in collaboration_keywords if kw in option.description)
        return min(count * 0.2, 1.0)

    def _assess_knowledge_integration(self, option: DecisionOption) -> float:
        """评估知识整合度"""
        knowledge_keywords = ["知识", "数据", "信息", "学习", "分析"]
        count = sum(1 for kw in knowledge_keywords if kw in option.description)
        return min(count * 0.15, 1.0)

    def _assess_diversity_value(self, option: DecisionOption) -> float:
        """评估多样性价值"""
        diversity_keywords = ["多样", "不同", "创新", "新颖", "独特"]
        count = sum(1 for kw in diversity_keywords if kw in option.description)
        return min(count * 0.1, 1.0)


class XiaonuoEnhancedDecisionEngine:
    """小诺增强决策引擎 - v2.1: 使用配置类"""

    def __init__(self, config: DecisionConfig = None):
        self.name = "小诺·双鱼公主增强决策引擎"
        self.version = "v2.1.0"

        # v2.1: 使用配置类或默认配置
        self.config = config or DecisionConfig()

        # 决策策略
        self.strategies = {
            DecisionLayer.INSTINCT: InstinctDecisionStrategy(),
            DecisionLayer.EMOTIONAL: EmotionalDecisionStrategy(),
            DecisionLayer.LOGICAL: LogicalDecisionStrategy(),
            DecisionLayer.STRATEGIC: StrategicDecisionStrategy(),
            DecisionLayer.ETHICAL: EthicalDecisionStrategy(),
            DecisionLayer.COLLABORATIVE: CollaborativeDecisionStrategy(),
        }

        # 层级权重配置 - v2.1: 从配置类获取
        self.layer_weights = dict(self.config.layer_weights)

        # 决策历史 - v2.1: 使用配置类中的maxlen
        self.decision_history = deque(maxlen=self.config.decision_history_maxlen)
        self._decision_index = {}  # 决策索引:{decision_id: decision} - O(1)查找优化
        self.pattern_memory = defaultdict(list)

        # 学习模型 - v2.1: 使用配置类中的学习率
        self.learning_rate = self.config.learning_rate
        # 限制experience_base大小防止内存无限增长 - v2.1: 使用配置类
        self.experience_base = deque(maxlen=self.config.experience_base_maxlen)

        # 性能统计 - v2.1: 从配置类获取初始值
        self.performance_metrics = dict(self.config.initial_performance_metrics)

        logger.info(f"🧠 {self.name}初始化完成")
        logger.info(f"🎯 集成{len(self.strategies)}个决策层级")
        logger.info(f"💖 情感感知权重: {self.layer_weights[DecisionLayer.EMOTIONAL]:.0%}")
        logger.info(f"⚙️ 使用配置类: {self.config.__class__.__name__}")

    async def make_decision(
        self, context: DecisionContext, options: list[DecisionOption]
    ) -> DecisionResult:
        """执行增强决策"""
        start_time = datetime.now()
        decision_id = str(uuid.uuid4())

        logger.info(f"🎯 开始决策: {decision_id}")
        logger.info(f"📝 情境: {context.situation}")
        logger.info(f"🔥 紧急度: {context.urgency.value}")

        # 多层决策分析
        layer_analysis = {}
        layer_scores = defaultdict(dict)

        for layer, strategy in self.strategies.items():
            try:
                scores = await strategy.evaluate(context, options)
                layer_scores[layer] = scores
                layer_analysis[layer] = {
                    "strategy": strategy.__class__.__name__,
                    "scores": scores,
                    "best_option": max(scores.items(), key=lambda x: x[1]) if scores else None,
                }
                logger.debug(f"✅ {layer.value}层分析完成")
            except (ValueError, TypeError) as e:
                layer_analysis[layer] = {"error": str(e)}
            except KeyError as e:
                layer_analysis[layer] = {"error": str(e)}
            except Exception as e:
                layer_analysis[layer] = {"error": str(e)}

        # 综合评分计算
        final_scores = self._calculate_final_scores(layer_scores)

        # 选择最佳选项
        if not final_scores:
            # 回退到简单策略
            best_option_id = options.get(0).id if options else None
            final_score = 0.5
        else:
            best_option_id, final_score = max(final_scores.items(), key=lambda x: x[1])

        best_option = next((opt for opt in options if opt.id == best_option_id), None)

        # 生成推理链
        reasoning_chain = self._generate_reasoning_chain(context, best_option, layer_analysis)

        # 创建执行计划
        execution_plan = self._create_execution_plan(best_option, context)

        # 设置监控指标
        monitoring_metrics = self._define_monitoring_metrics(best_option, context)

        # 设置成功标准
        success_criteria = self._define_success_criteria(best_option, context)

        # 创建决策结果
        result = DecisionResult(
            id=decision_id,
            context=context,
            selected_option=best_option,
            layer_analysis=layer_analysis,
            final_score=final_score,
            reasoning_chain=reasoning_chain,
            execution_plan=execution_plan,
            monitoring_metrics=monitoring_metrics,
            success_criteria=success_criteria,
        )

        # 记录决策并更新索引
        self.decision_history.append(result)
        self._decision_index[result.id] = result  # 更新决策索引
        self.performance_metrics["total_decisions"] += 1

        # 学习和改进
        await self._learn_from_decision(result)

        decision_time = (datetime.now() - start_time).total_seconds()
        self.performance_metrics["decision_speed"] = (
            self.performance_metrics["decision_speed"] * 0.9 + decision_time * 0.1
        )

        logger.info(
            f"✅ 决策完成: {best_option_id[.2f}]"
        )

        return result

    def _calculate_final_scores(
        self, layer_scores: dict[DecisionLayer, dict[str, float]) -> dict[str, float]:
        """计算最终综合得分"""
        final_scores = defaultdict(float)

        for layer, scores in layer_scores.items():
            weight = self.layer_weights[layer]
            for option_id, score in scores.items():
                final_scores[option_id] += score * weight

        return dict(final_scores)

    def _generate_reasoning_chain(
        self,
        context: DecisionContext,
        option: DecisionOption,
        layer_analysis: dict[DecisionLayer, dict[str, Any],
    ) -> list[str]:
        """生成推理链"""
        reasoning = []

        # 情境分析
        reasoning.append(f"🎯 面临情境: {context.situation}")
        reasoning.append(f"🔥 紧急程度: {context.urgency.value}")
        reasoning.append(f"🌟 决策领域: {context.domain.value}")

        # 各层决策理由
        for layer, analysis in layer_analysis.items():
            if "error" not in analysis and analysis.get("best_option"):
                best_id, score = analysis["best_option"]
                if best_id == option.id:
                    reasoning.append(f"✨ {layer.value}层支持: 得分{score:.2f}")

        # 综合结论
        reasoning.append(f"💖 最终选择: {option.description}")
        reasoning.append(f"👑 爸爸满意度: {option.father_satisfaction:.0%}")
        reasoning.append(f"🌸 家庭和谐度: {option.family_harmony:.0%}")

        return reasoning

    def _create_execution_plan(
        self, option: DecisionOption, context: DecisionContext
    ) -> list[dict[str, Any]]:
        """创建执行计划"""
        plan = []

        for i, action in enumerate(option.actions):
            step = {
                "step": i + 1,
                "action": action.get("description", "未知行动"),
                "type": action.get("type", "general"),
                "estimated_time": action.get("time", 0),
                "resources": action.get("resources", []),
                "dependencies": action.get("dependencies", []),
            }
            plan.append(step)

        return plan

    def _define_monitoring_metrics(
        self, option: DecisionOption, context: DecisionContext
    ) -> list[str]:
        """定义监控指标"""
        metrics = []

        # 基础指标
        metrics.extend(["execution_progress", "resource_consumption", "time_spent"])

        # 领域特定指标
        if context.domain == DecisionDomain.TECHNICAL:
            metrics.extend(["code_quality", "performance_impact"])
        elif context.domain == DecisionDomain.EMOTIONAL:
            metrics.extend(["emotional_impact", "relationship_quality"])
        elif context.domain == DecisionDomain.PLATFORM:
            metrics.extend(["system_health", "user_satisfaction"])

        # 小诺特有指标
        metrics.extend(
            ["father_satisfaction_level", "family_harmony_index", "princess_elegance_score"]
        )

        return metrics

    def _define_success_criteria(
        self, option: DecisionOption, context: DecisionContext
    ) -> dict[str, float]:
        """定义成功标准"""
        criteria = {}

        # 基础成功标准
        criteria["completion_rate"] = 1.0  # 100%完成度
        criteria["quality_threshold"] = 0.8  # 80%质量标准

        # 时间标准
        criteria["time_budget_usage"] = 1.0  # 不超时

        # 小诺特有标准
        criteria["father_satisfaction_min"] = 0.8  # 爸爸满意度最低80%
        criteria["emotional_positive_impact"] = 0.7  # 情感正面影响70%

        # 领域特定标准
        if context.domain == DecisionDomain.FAMILY:
            criteria["harmony_maintained"] = 1.0  # 家庭和谐必须维持

        return criteria

    async def _learn_from_decision(self, result: DecisionResult):
        """从决策中学习"""
        try:
            # 提取决策模式
            pattern = self._extract_decision_pattern(result)
            self.pattern_memory[pattern].append(result.id)

            # 更新经验库
            self.experience_base.append(
                {
                    "timestamp": datetime.now(),
                    "context_hash": hash(str(result.context.__dict__)),
                    "decision_id": result.id,
                    "outcome": None,  # 待执行后更新
                }
            )

            # 动态调整权重
            if len(self.decision_history) % 10 == 0:
                await self._adjust_layer_weights()

        except Exception as e:
            logger.error(f"决策处理失败: {e}")

    def _extract_decision_pattern(self, result: DecisionResult) -> str:
        """提取决策模式"""
        context = result.context
        pattern_parts = [
            context.domain.value,
            context.urgency.value,
            str(len(context.goals)),
            str(len(context.constraints)),
        ]
        return "_".join(pattern_parts)

    async def _adjust_layer_weights(self):
        """动态调整层级权重"""
        # 基于最近决策成功率调整权重
        recent_decisions = list(self.decision_history)[-20:]

        if len(recent_decisions) >= 10:
            success_rates = defaultdict(list)

            for decision in recent_decisions:
                # 简化的成功评估(实际应该基于执行结果)
                estimated_success = decision.final_score > 0.6

                for layer in DecisionLayer:
                    if layer in decision.layer_analysis:
                        layer_score = (
                            max(decision.layer_analysis[layer].get("scores", {}).values()) or 0
                        )
                        success_rates[layer].append(layer_score if estimated_success else 0)

            # 微调权重
            for layer in DecisionLayer:
                if success_rates[layer]:
                    avg_success = np.mean(success_rates[layer])
                    if avg_success > 0.8:  # 表现好的层增加权重
                        self.layer_weights[layer] *= 1.05
                    elif avg_success < 0.5:  # 表现差的层减少权重
                        self.layer_weights[layer] *= 0.95

            # 归一化权重
            total_weight = sum(self.layer_weights.values())
            for layer in self.layer_weights:
                self.layer_weights[layer] /= total_weight

            logger.info(f"🎯 权重调整完成: 情感层{self.layer_weights[DecisionLayer.EMOTIONAL]:.0%}")

    async def update_decision_outcome(
        self, decision_id: str, outcome: dict[str, Any], emotional_satisfaction: float
    ):
        """更新决策结果 - 使用O(1)索引查找优化"""
        # 使用索引直接获取决策对象
        decision = self._decision_index.get(decision_id)
        if decision is None:
            logger.warning(f"⚠️ 决策{decision_id[:8]}不存在于历史记录中")
            return

        # 更新决策结果
        decision.actual_outcomes = outcome
        decision.emotional_satisfaction = emotional_satisfaction

        # 更新性能指标
        success = self._evaluate_success(decision)
        if success:
            self.performance_metrics["successful_decisions"] += 1

        # 更新平均置信度和情感满意度
        self._update_performance_metrics(decision)

        logger.info(f"📊 决策{decision_id[:8]}结果已更新")

    def _evaluate_success(self, decision: DecisionResult) -> bool:
        """评估决策是否成功"""
        if not decision.actual_outcomes:
            return False

        # 基于成功标准评估
        for criteria, threshold in decision.success_criteria.items():
            actual = decision.actual_outcomes.get(criteria, 0)
            if actual < threshold * 0.8:  # 80%容差
                return False

        return True

    def _update_performance_metrics(self, decision: DecisionResult) -> Any:
        """更新性能指标"""
        # 平均置信度
        total_decisions = self.performance_metrics["total_decisions"]
        current_avg = self.performance_metrics["average_confidence"]
        self.performance_metrics["average_confidence"] = (
            current_avg * (total_decisions - 1) + decision.final_score
        ) / total_decisions

        # 情感满意度
        if decision.emotional_satisfaction is not None:
            current_emotion = self.performance_metrics["emotional_satisfaction"]
            if current_emotion == 0:  # 首次更新
                self.performance_metrics["emotional_satisfaction"] = decision.emotional_satisfaction
            else:
                self.performance_metrics["emotional_satisfaction"] = (
                    current_emotion * 0.9 + decision.emotional_satisfaction * 0.1
                )

    def get_status_report(self) -> dict[str, Any]:
        """获取引擎状态报告"""
        return {
            "engine_info": {
                "name": self.name,
                "version": self.version,
                "layers": len(self.strategies),
                "emotional_layer_weight": f"{self.layer_weights[DecisionLayer.EMOTIONAL]:.0%}",
            },
            "performance_metrics": self.performance_metrics,
            "decision_patterns": {
                "total_patterns": len(self.pattern_memory),
                "most_common": (
                    max(self.pattern_memory.items(), key=lambda x: len(x[1]))[0]
                    if self.pattern_memory
                    else None
                ),
            },
            "learning_status": {
                "experience_base_size": len(self.experience_base),
                "learning_rate": self.learning_rate,
                "adaptive_weights": True,
            },
        }

    async def save_state(self, filepath: str):
        """保存引擎状态"""
        # 转换为JSON可序列化的格式
        state = {
            "layer_weights": dict(self.layer_weights),  # 转换为普通dict
            "decision_history": list(self.decision_history),  # deque转为list
            "pattern_memory": {
                k: list(v) for k, v in self.pattern_memory.items()
            },  # defaultdict转为dict
            "experience_base": self.experience_base,  # 已是list
            "performance_metrics": self.performance_metrics,
        }

        # 使用JSON替代pickle(更安全)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"💾 引擎状态已保存: {filepath}")

    async def load_state(self, filepath: str):
        """加载引擎状态"""
        try:
            with open(filepath, encoding="utf-8") as f:
                state = json.load(f)

            self.layer_weights = state.get("layer_weights", {})
            self.decision_history = deque(state.get("decision_history", []), maxlen=1000)
            # 恢复pattern_memory为defaultdict
            pattern_memory_data = state.get("pattern_memory", {})
            self.pattern_memory = defaultdict(list)
            for k, v in pattern_memory_data.items():
                self.pattern_memory[k] = v
            self.experience_base = state.get("experience_base", [])
            self.performance_metrics = state.get("performance_metrics", {})

            logger.info(f"📂 引擎状态已加载: {filepath}")
        except FileNotFoundError:
            logger.warning(f"状态文件不存在: {filepath}")
        except json.JSONDecodeError as e:
            logger.error(f"状态文件格式错误: {e}")
        except Exception as e:
            logger.error(f"加载状态失败: {e}")


# 便捷创建函数
async def create_xiaonuo_decision_engine() -> XiaonuoEnhancedDecisionEngine:
    """创建小诺决策引擎实例"""
    engine = XiaonuoEnhancedDecisionEngine()
    return engine
