#!/usr/bin/env python3
"""
增强决策模型单元测试
Unit tests for Enhanced Decision Model

测试内容:
- 规则引擎决策
- ML引擎决策
- RL引擎决策
- 集成投票决策
- 反馈学习
- 决策统计
"""

import sys
from pathlib import Path

import pytest

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.decision.enhanced_decision_model import (
    Decision,
    DecisionContext,
    EnhancedDecisionModel,
    EnsembleVoter,
    MLEngine,
    RLEngine,
    RuleBasedEngine,
    TaskComplexity,
)


class TestRuleBasedEngine:
    """规则引擎测试"""

    @pytest.mark.asyncio
    async def test_patent_search_rule(self):
        """测试专利检索规则"""
        engine = RuleBasedEngine()

        context = DecisionContext(
            task_type="patent_search",
            task_description="搜索AI相关专利",
            complexity=TaskComplexity.MODERATE,
            available_tools=["patent_database", "web_search"],
            available_agents=["xiaona"],
            historical_success_rate=0.85,
            resource_constraints={},
            time_constraints={},
            user_preferences={}
        )

        decision = await engine.decide(context)

        assert decision.action == "use_patent_database"
        assert decision.confidence == 0.95
        assert "专利数据库" in decision.reasoning

    @pytest.mark.asyncio
    async def test_patent_analysis_rule(self):
        """测试专利分析规则"""
        engine = RuleBasedEngine()

        context = DecisionContext(
            task_type="patent_analysis",
            task_description="分析专利有效性",
            complexity=TaskComplexity.COMPLEX,
            available_tools=["xiaona_agent", "general_agent"],
            available_agents=["xiaona", "general"],
            historical_success_rate=0.90,
            resource_constraints={},
            time_constraints={},
            user_preferences={}
        )

        decision = await engine.decide(context)

        assert decision.action == "use_xiaona_agent"
        assert decision.confidence == 0.9

    @pytest.mark.asyncio
    async def test_default_rule(self):
        """测试默认规则"""
        engine = RuleBasedEngine()

        context = DecisionContext(
            task_type="unknown_task",
            task_description="未知任务类型",
            complexity=TaskComplexity.SIMPLE,
            available_tools=["general_tool"],
            available_agents=["general"],
            historical_success_rate=0.5,
            resource_constraints={},
            time_constraints={},
            user_preferences={}
        )

        decision = await engine.decide(context)

        assert decision.action == "use_general_tool"
        assert decision.confidence == 0.5


class TestMLEngine:
    """ML引擎测试"""

    @pytest.mark.asyncio
    async def test_ml_decision(self):
        """测试ML决策"""
        engine = MLEngine()

        context = DecisionContext(
            task_type="ml_task",
            task_description="ML任务",
            complexity=TaskComplexity.MODERATE,
            available_tools=["ml_tool"],
            available_agents=["ml_agent"],
            historical_success_rate=0.7,
            resource_constraints={},
            time_constraints={},
            user_preferences={}
        )

        decision = await engine.decide(context)

        assert decision.action == "use_ml_recommended_tool"
        assert decision.confidence == 0.7

    @pytest.mark.asyncio
    async def test_ml_training(self):
        """测试ML训练"""
        engine = MLEngine()

        # 模拟训练数据
        from core.decision.enhanced_decision_model import DecisionTrace
        trace = DecisionTrace(
            trace_id="test_trace_001",
            context=DecisionContext(
                task_type="test",
                task_description="test",
                complexity=TaskComplexity.SIMPLE,
                available_tools=["test_tool"],
                available_agents=["test_agent"],
                historical_success_rate=0.8,
                resource_constraints={},
                time_constraints={},
                user_preferences={}
            ),
            decisions=[],
            final_decision=Decision(
                decision_id="test",
                decision_type="tool_selection",
                action="test_action",
                target="test_target",
                confidence=0.8,
                reasoning="test",
                alternative_actions=[],
                risk_level="low",
                expected_outcome="test"
            )
        )

        await engine.train([trace])

        assert len(engine.training_data) == 1


class TestRLEngine:
    """RL引擎测试"""

    @pytest.mark.asyncio
    async def test_rl_decision_exploration(self):
        """测试RL探索策略"""
        engine = RLEngine()

        context = DecisionContext(
            task_type="rl_task",
            task_description="RL任务",
            complexity=TaskComplexity.MODERATE,
            available_tools=["tool1", "tool2"],
            available_agents=["agent1"],
            historical_success_rate=0.7,
            resource_constraints={},
            time_constraints={},
            user_preferences={}
        )

        # 设置低探索率以确保利用
        engine.exploration_rate = 0.0

        decision = await engine.decide(context)

        assert decision is not None
        assert decision.action in ["tool1", "tool2"]

    @pytest.mark.asyncio
    async def test_rl_q_value_update(self):
        """测试Q值更新"""
        engine = RLEngine()

        # 初始Q值
        state = "test_state"
        action = "test_action"
        reward = 1.0
        next_state = "test_next_state"

        # 更新Q值
        engine.update_q_value(state, action, reward, next_state)

        # 验证Q值已更新
        assert state in engine.q_table
        assert action in engine.q_table[state]
        assert engine.q_table[state][action] > 0

    @pytest.mark.asyncio
    async def test_rl_state_representation(self):
        """测试状态表示"""
        engine = RLEngine()

        context = DecisionContext(
            task_type="patent_search",
            task_description="专利搜索",
            complexity=TaskComplexity.SIMPLE,
            available_tools=["test_tool"],
            available_agents=["test_agent"],
            historical_success_rate=0.8,
            resource_constraints={},
            time_constraints={},
            user_preferences={}
        )

        state = engine._get_state(context)

        assert "patent_search" in state
        assert "simple" in state


class TestEnsembleVoter:
    """集成投票器测试"""

    def test_single_decision(self):
        """测试单一决策"""
        voter = EnsembleVoter()

        decision = Decision(
            decision_id="test",
            decision_type="tool_selection",
            action="test_action",
            target="test_target",
            confidence=0.8,
            reasoning="test",
            alternative_actions=[],
            risk_level="low",
            expected_outcome="test"
        )

        result = voter.vote([decision])

        assert result.action == "test_action"
        assert result.confidence == 0.8

    def test_multiple_decisions(self):
        """测试多决策投票"""
        voter = EnsembleVoter()

        decision1 = Decision(
            decision_id="test1",
            decision_type="tool_selection",
            action="action1",
            target="target1",
            confidence=0.7,
            reasoning="test1",
            alternative_actions=[],
            risk_level="low",
            expected_outcome="test1"
        )

        decision2 = Decision(
            decision_id="test2",
            decision_type="tool_selection",
            action="action2",
            target="target2",
            confidence=0.9,
            reasoning="test2",
            alternative_actions=[],
            risk_level="low",
            expected_outcome="test2"
        )

        result = voter.vote([decision1, decision2])

        # 应该选择置信度更高的决策
        assert result.action == "action2"
        assert result.confidence == 0.9

    def test_weighted_vote(self):
        """测试加权投票"""
        voter = EnsembleVoter()

        decisions = [
            ("rule", Decision(
                decision_id="rule",
                decision_type="tool_selection",
                action="rule_action",
                target="rule_target",
                confidence=0.8,
                reasoning="rule",
                alternative_actions=[],
                risk_level="low",
                expected_outcome="rule"
            )),
            ("ml", Decision(
                decision_id="ml",
                decision_type="tool_selection",
                action="ml_action",
                target="ml_target",
                confidence=0.7,
                reasoning="ml",
                alternative_actions=[],
                risk_level="low",
                expected_outcome="ml"
            )),
        ]

        result = voter.weighted_vote(decisions)

        assert result is not None


class TestEnhancedDecisionModel:
    """增强决策模型测试"""

    @pytest.mark.asyncio
    async def test_enhanced_decision(self):
        """测试增强决策"""
        model = EnhancedDecisionModel()

        context = DecisionContext(
            task_type="patent_search",
            task_description="搜索专利",
            complexity=TaskComplexity.MODERATE,
            available_tools=["patent_database", "web_search"],
            available_agents=["xiaona"],
            historical_success_rate=0.85,
            resource_constraints={"max_time": 30},
            time_constraints={"deadline": "1hour"},
            user_preferences={"accuracy": "high"}
        )

        decision = await model.decide(context)

        assert decision is not None
        assert decision.action in ["patent_database", "web_search"]
        assert decision.confidence > 0
        assert len(decision.reasoning) > 0

    @pytest.mark.asyncio
    async def test_feedback_learning(self):
        """测试反馈学习"""
        model = EnhancedDecisionModel()

        # 先做一个决策
        context = DecisionContext(
            task_type="test_task",
            task_description="测试任务",
            complexity=TaskComplexity.SIMPLE,
            available_tools=["test_tool"],
            available_agents=["test_agent"],
            historical_success_rate=0.8,
            resource_constraints={},
            time_constraints={},
            user_preferences={}
        )

        await model.decide(context)

        # 获取决策轨迹
        trace = model.decision_traces[-1]

        # 从反馈中学习
        await model.learn_from_feedback(
            trace_id=trace.trace_id,
            outcome="success",
            feedback=0.9
        )

        # 验证学习结果
        assert len(model.decision_traces) == 1
        assert len(model.ml_engine.training_data) == 1

    def test_decision_stats(self):
        """测试决策统计"""
        model = EnhancedDecisionModel()

        stats = model.get_decision_stats()

        assert "total_decisions" in stats
        assert "average_confidence" in stats
        assert "action_distribution" in stats
        assert stats["total_decisions"] == 0  # 初始状态


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
