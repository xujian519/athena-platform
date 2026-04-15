#!/usr/bin/env python3
from __future__ import annotations
"""
增强决策模型
Enhanced Decision Model

集成多种决策策略：
- 规则引擎 (Rule-Based Engine)
- 机器学习引擎 (ML Engine)
- 强化学习引擎 (RL Engine)
- 集成投票器 (Ensemble Voter)

实现智能化的多维度决策
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """决策类型"""
    TOOL_SELECTION = "tool_selection"
    TASK_ROUTING = "task_routing"
    AGENT_ALLOCATION = "agent_allocation"
    RESOURCE_ALLOCATION = "resource_allocation"
    PRIORITY_SCORING = "priority_scoring"


class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class DecisionContext:
    """决策上下文"""
    task_type: str
    task_description: str
    complexity: TaskComplexity
    available_tools: list[str]
    available_agents: list[str]
    historical_success_rate: float
    resource_constraints: dict[str, Any]
    time_constraints: dict[str, Any]
    user_preferences: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    """决策结果"""
    decision_id: str
    decision_type: DecisionType
    action: str
    target: str
    confidence: float
    reasoning: str
    alternative_actions: list[str]
    risk_level: str
    expected_outcome: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionTrace:
    """决策轨迹"""
    trace_id: str
    context: DecisionContext
    decisions: list[Decision]
    final_decision: Decision
    outcome: str | None = None
    feedback: float | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class RuleBasedEngine:
    """基于规则的决策引擎"""

    def __init__(self):
        self.rules = self._load_rules()
        logger.info("✅ 规则引擎初始化完成")

    def _load_rules(self) -> dict:
        """加载决策规则"""
        return {
            "patent_search": {
                "priority": 1,
                "action": "use_patent_database",
                "confidence": 0.95,
                "reasoning": "专利检索任务优先使用专利数据库",
                "alternatives": ["use_web_search", "use_google_patents"]
            },
            "patent_analysis": {
                "priority": 1,
                "action": "use_xiaona_agent",
                "confidence": 0.9,
                "reasoning": "专利分析任务由小娜专家处理",
                "alternatives": ["use_general_agent"]
            },
            "legal_consultation": {
                "priority": 1,
                "action": "use_legal_expert",
                "confidence": 0.85,
                "reasoning": "法律咨询需要专业法律知识",
                "alternatives": ["use_general_agent"]
            },
            "task_coordination": {
                "priority": 1,
                "action": "use_xiaonuo_coordinator",
                "confidence": 0.9,
                "reasoning": "任务协调由小诺调度官处理",
                "alternatives": ["use_manual_coordination"]
            }
        }

    async def decide(self, context: DecisionContext) -> Decision:
        """基于规则的决策"""
        task_type = context.task_type

        if task_type in self.rules:
            rule = self.rules[task_type]
            return Decision(
                decision_id=f"rule_{task_type}_{datetime.now().timestamp()}",
                decision_type=DecisionType.TOOL_SELECTION,
                action=rule["action"],
                target=rule["action"],
                confidence=rule["confidence"],
                reasoning=rule["reasoning"],
                alternative_actions=rule["alternatives"],
                risk_level="low",
                expected_outcome="high_accuracy"
            )

        # 默认决策
        return Decision(
            decision_id=f"rule_default_{datetime.now().timestamp()}",
            decision_type=DecisionType.TOOL_SELECTION,
            action="use_general_tool",
            target="general_tool",
            confidence=0.5,
            reasoning="未匹配到特定规则，使用通用工具",
            alternative_actions=[],
            risk_level="medium",
            expected_outcome="moderate_accuracy"
        )


class MLEngine:
    """基于机器学习的决策引擎"""

    def __init__(self):
        self.model = None  # TODO: 加载预训练模型
        self.training_data = []
        logger.info("✅ ML引擎初始化完成")

    async def decide(self, context: DecisionContext) -> Decision:
        """基于ML的决策"""
        # TODO: 实现实际的ML推理
        # 目前返回基于启发式规则的决策
        return Decision(
            decision_id=f"ml_{context.task_type}_{datetime.now().timestamp()}",
            decision_type=DecisionType.TOOL_SELECTION,
            action="use_ml_recommended_tool",
            target="ml_recommended",
            confidence=0.7,
            reasoning="ML模型基于历史数据推荐",
            alternative_actions=["use_rule_based_tool"],
            risk_level="medium",
            expected_outcome="data_driven_accuracy"
        )

    async def train(self, traces: list[DecisionTrace]):
        """训练ML模型"""
        # TODO: 实现模型训练
        logger.info(f"训练ML模型，使用{len(traces)}条决策轨迹")
        self.training_data.extend(traces)


class RLEngine:
    """基于强化学习的决策引擎"""

    def __init__(self):
        self.q_table = {}  # Q值表
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.exploration_rate = 0.2
        logger.info("✅ RL引擎初始化完成")

    async def decide(self, context: DecisionContext) -> Decision:
        """基于RL的决策"""
        state = self._get_state(context)

        # ε-greedy策略
        import random
        if random.random() < self.exploration_rate:
            # 探索：随机选择
            action = random.choice(context.available_tools)
            confidence = 0.6
            reasoning = "RL探索：随机尝试新策略"
        else:
            # 利用：选择Q值最高的动作
            if state in self.q_table:
                action = max(self.q_table[state].items(), key=lambda x: x[1])[0]
                confidence = 0.8
                reasoning = f"RL利用：基于Q值选择{action}"
            else:
                action = context.available_tools[0] if context.available_tools else "general"
                confidence = 0.5
                reasoning = "RL初始化：首次遇到该状态"

        return Decision(
            decision_id=f"rl_{state}_{datetime.now().timestamp()}",
            decision_type=DecisionType.TOOL_SELECTION,
            action=action,
            target=action,
            confidence=confidence,
            reasoning=reasoning,
            alternative_actions=context.available_tools[:3],
            risk_level="medium",
            expected_outcome="reinforcement_optimized"
        )

    def update_q_value(self, state: str, action: str, reward: float, next_state: str):
        """更新Q值"""
        if state not in self.q_table:
            self.q_table[state] = {}

        current_q = self.q_table[state].get(action, 0.0)

        # Q-learning更新
        max_next_q = max(self.q_table.get(next_state, {}).values(), default=0.0)
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )

        self.q_table[state][action] = new_q
        logger.debug(f"更新Q值: state={state}, action={action}, Q={new_q:.2f}")

    def _get_state(self, context: DecisionContext) -> str:
        """获取状态表示"""
        return f"{context.task_type}_{context.complexity.value}"


class EnsembleVoter:
    """集成投票器"""

    def __init__(self):
        self.voting_weights = {
            "rule": 0.4,
            "ml": 0.3,
            "rl": 0.3
        }
        logger.info("✅ 集成投票器初始化完成")

    def vote(self, decisions: list[Decision]) -> Decision:
        """集成投票决策"""
        if not decisions:
            raise ValueError("至少需要一个决策")

        if len(decisions) == 1:
            return decisions[0]

        # 加权投票
        # 简化：选择置信度最高的决策
        best_decision = max(decisions, key=lambda d: d.confidence)

        logger.info(
            f"集成投票结果: {best_decision.action} "
            f"(置信度: {best_decision.confidence:.2f})"
        )

        return best_decision

    def weighted_vote(self, decisions: list[tuple[str, Decision]]) -> Decision:
        """加权投票"""
        scores = {}
        for engine_type, decision in decisions:
            weight = self.voting_weights.get(engine_type, 0.33)
            action = decision.action

            if action not in scores:
                scores[action] = 0.0
            scores[action] += decision.confidence * weight

        # 选择得分最高的动作
        best_action = max(scores.items(), key=lambda x: x[1])[0]

        # 返回对应的决策
        for engine_type, decision in decisions:
            if decision.action == best_action:
                return decision

        # 默认返回第一个决策
        return decisions[0][1]


class EnhancedDecisionModel:
    """增强决策模型 - 集成多种决策策略"""

    def __init__(self):
        self.rule_engine = RuleBasedEngine()
        self.ml_engine = MLEngine()
        self.rl_engine = RLEngine()
        self.ensemble_voter = EnsembleVoter()
        self.decision_traces: list[DecisionTrace] = []
        logger.info("✅ 增强决策模型初始化完成")

    async def decide(self, context: DecisionContext) -> Decision:
        """做出决策 - 集成多种策略"""
        logger.info(f"开始决策: task_type={context.task_type}")

        # 并行获取多种决策
        decisions = []

        # 1. 规则引擎决策
        rule_decision = await self.rule_engine.decide(context)
        decisions.append(("rule", rule_decision))

        # 2. ML引擎决策
        ml_decision = await self.ml_engine.decide(context)
        decisions.append(("ml", ml_decision))

        # 3. RL引擎决策
        rl_decision = await self.rl_engine.decide(context)
        decisions.append(("rl", rl_decision))

        # 4. 集成投票
        final_decision = self.ensemble_voter.weighted_vote(decisions)

        # 记录决策轨迹
        trace = DecisionTrace(
            trace_id=f"trace_{datetime.now().timestamp()}",
            context=context,
            decisions=[d[1] for d in decisions],
            final_decision=final_decision
        )
        self.decision_traces.append(trace)

        logger.info(
            f"决策完成: action={final_decision.action}, "
            f"confidence={final_decision.confidence:.2f}"
        )

        return final_decision

    async def learn_from_feedback(self, trace_id: str, outcome: str, feedback: float):
        """从反馈中学习"""
        # 找到对应的轨迹
        trace = next(
            (t for t in self.decision_traces if t.trace_id == trace_id),
            None
        )

        if not trace:
            logger.warning(f"未找到决策轨迹: {trace_id}")
            return

        # 更新RL引擎的Q值
        state = self.rl_engine._get_state(trace.context)
        action = trace.final_decision.action
        next_state = f"{state}_{outcome}"

        self.rl_engine.update_q_value(state, action, feedback, next_state)

        # 训练ML引擎
        trace.outcome = outcome
        trace.feedback = feedback
        await self.ml_engine.train([trace])

        logger.info(f"从反馈学习完成: trace_id={trace_id}, feedback={feedback}")

    def get_decision_stats(self) -> dict[str, Any]:
        """获取决策统计信息"""
        total_decisions = len(self.decision_traces)
        if total_decisions == 0:
            return {"total_decisions": 0}

        # 统计各引擎的使用情况
        action_distribution = {}

        for trace in self.decision_traces:
            for decision in trace.decisions:
                action = decision.action
                action_distribution[action] = action_distribution.get(action, 0) + 1

        # 计算平均置信度
        avg_confidence = sum(
            t.final_decision.confidence for t in self.decision_traces
        ) / total_decisions

        return {
            "total_decisions": total_decisions,
            "average_confidence": round(avg_confidence, 3),
            "action_distribution": action_distribution,
            "q_table_size": len(self.rl_engine.q_table),
            "training_data_size": len(self.ml_engine.training_data)
        }


# 全局决策模型实例
_decision_model: EnhancedDecisionModel | None = None


async def get_decision_model() -> EnhancedDecisionModel:
    """获取全局决策模型实例"""
    global _decision_model

    if _decision_model is None:
        _decision_model = EnhancedDecisionModel()

    return _decision_model


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def demo():
        """演示增强决策模型"""
        model = EnhancedDecisionModel()

        # 创建决策上下文
        context = DecisionContext(
            task_type="patent_search",
            task_description="搜索AI相关专利",
            complexity=TaskComplexity.MODERATE,
            available_tools=["patent_database", "web_search", "google_patents"],
            available_agents=["xiaona", "general_agent"],
            historical_success_rate=0.85,
            resource_constraints={"max_time": 30},
            time_constraints={"deadline": "1hour"},
            user_preferences={"accuracy": "high"}
        )

        # 做出决策
        decision = await model.decide(context)

        print("\n🎯 决策结果:")
        print(f"  动作: {decision.action}")
        print(f"  置信度: {decision.confidence:.2f}")
        print(f"  推理: {decision.reasoning}")
        print(f"  风险级别: {decision.risk_level}")

        # 获取统计信息
        stats = model.get_decision_stats()
        print("\n📊 决策统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    asyncio.run(demo())
