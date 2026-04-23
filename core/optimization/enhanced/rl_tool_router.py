#!/usr/bin/env python3
from __future__ import annotations
"""
强化学习工具路由器 (RL Tool Router)
基于强化学习的智能工具选择和路由决策

作者: 小诺·双鱼公主
版本: v2.0.0
优化目标: 工具选择准确率 94% → 97%
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class Action(str, Enum):
    """动作类型(工具选择)"""

    TOOL_PATENT_SEARCH = "patent_search"
    TOOL_PATENT_ANALYSIS = "patent_analysis"
    TOOL_LEGAL_QA = "legal_qa"
    TOOL_WEB_SEARCH = "web_search"
    TOOL_CODE_GENERATION = "code_generation"
    TOOL_DATA_ANALYSIS = "data_analysis"
    TOOL_KNOWLEDGE_GRAPH = "knowledge_graph"
    TOOL_MEMORY_RETRIEVAL = "memory_retrieval"


class RewardType(str, Enum):
    """奖励类型"""

    SUCCESS = "success"  # 成功完成
    FAILURE = "failure"  # 执行失败
    TIMEOUT = "timeout"  # 超时
    USER_FEEDBACK = "user_feedback"  # 用户反馈
    LATENCY = "latency"  # 延迟奖励


@dataclass
class RLState:
    """强化学习状态"""

    query_features: dict[str, float]  # 查询特征
    context_features: dict[str, float]  # 上下文特征
    tool_features: dict[str, dict[str, float]]  # 工具特征
    timestamp: datetime = field(default_factory=datetime.now)

    def to_vector(self) -> np.ndarray:
        """转换为向量表示"""
        # 简化版:拼接所有特征
        features = []

        # 查询特征
        features.extend(list(self.query_features.values()))

        # 上下文特征
        features.extend(list(self.context_features.values()))

        # 工具特征(取平均值)
        if self.tool_features:
            tool_values = []
            for tool_feats in self.tool_features.values():
                tool_values.extend(list(tool_feats.values()))
            features.extend(tool_values)

        return np.array(features, dtype=np.float32)


@dataclass
class RLAction:
    """强化学习动作"""

    tool_id: Action
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RLReward:
    """强化学习奖励"""

    reward_type: RewardType
    value: float  # 奖励值(正奖励或负奖励)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RLTransition:
    """强化学习转换(经验)"""

    state: RLState
    action: RLAction
    reward: float  # 可能为None(尚未收到奖励)
    next_state: RLState
    done: bool
    timestamp: datetime = field(default_factory=datetime.now)


class QLearningAgent:
    """
    Q-Learning智能体

    使用Q-Learning算法学习工具选择策略
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        exploration_rate: float = 0.1,
        exploration_decay: float = 0.995,
    ):
        self.learning_rate = learning_rate  # 学习率
        self.discount_factor = discount_factor  # 折扣因子
        self.exploration_rate = exploration_rate  # 探索率
        self.exploration_decay = exploration_decay  # 探索衰减

        # Q表(状态-动作价值函数)
        self.q_table: dict[str, dict[Action, float]] = defaultdict(lambda: defaultdict(float))

        # 经验回放缓冲区
        self.experience_buffer: list[RLTransition] = []

        # 统计信息
        self.stats = {
            "total_steps": 0,
            "exploration_steps": 0,
            "exploitation_steps": 0,
            "total_reward": 0.0,
            "average_reward": 0.0,
        }

    def _get_state_key(self, state: RLState) -> str:
        """获取状态键(用于Q表索引)"""
        # 简化版:基于查询意图和上下文生成键
        query_intent = state.query_features.get("intent", "unknown")
        context_type = state.context_features.get("type", "general")
        return f"{query_intent}:{context_type}"

    def select_action(self, state: RLState) -> Action:
        """
        选择动作(工具)

        使用ε-贪婪策略
        """
        self.stats["total_steps"] += 1

        # ε-贪婪策略
        if np.random.random() < self.exploration_rate:
            # 探索:随机选择(确保返回Action枚举)
            self.stats["exploration_steps"] += 1
            action_list = list(Action)
            idx = np.random.randint(0, len(action_list))
            action = action_list[idx]
            logger.debug(f"🔍 探索: 选择 {action}")
        else:
            # 利用:选择Q值最大的动作
            self.stats["exploitation_steps"] += 1
            state_key = self._get_state_key(state)
            q_values = self.q_table[state_key]

            if q_values:
                action = max(q_values.items(), key=lambda x: x[1])[0]
                logger.debug(f"🎯 利用: 选择 {action} (Q={q_values[action]:.2f})")
            else:
                # 状态未见过,随机选择(确保返回Action枚举)
                action_list = list(Action)
                idx = np.random.randint(0, len(action_list))
                action = action_list[idx]

        return action

    def update_q_value(
        self, state: RLState, action: Action, reward: float, next_state: RLState, done: bool
    ):
        """
        更新Q值

        Q(s,a) ← Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
        """
        state_key = self._get_state_key(state)
        next_state_key = self._get_state_key(next_state)

        # 当前Q值
        current_q = self.q_table[state_key][action]

        # 计算最大Q值(下一状态)
        if done:
            max_next_q = 0.0
        else:
            if self.q_table[next_state_key]:
                max_next_q = max(self.q_table[next_state_key].values())
            else:
                max_next_q = 0.0

        # Q-Learning更新
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )

        self.q_table[state_key][action] = new_q

        # 更新统计
        self.stats["total_reward"] += reward
        self.stats["average_reward"] = self.stats["total_reward"] / self.stats["total_steps"]

        # 衰减探索率
        self.exploration_rate *= self.exploration_decay
        self.exploration_rate = max(0.01, self.exploration_rate)

        logger.debug(
            f"📊 Q值更新: {state_key} -> {action} "
            f"({current_q:.2f} → {new_q:.2f}), 奖励={reward:.2f}"
        )

    def store_experience(self, transition: RLTransition):
        """存储经验"""
        self.experience_buffer.append(transition)

        # 保持缓冲区大小
        if len(self.experience_buffer) > 10000:
            self.experience_buffer.pop(0)

    def train(self, batch_size: int = 32):
        """从经验回放中训练"""
        if len(self.experience_buffer) < batch_size:
            return

        # 随机采样
        batch = np.random.choice(self.experience_buffer, batch_size, replace=False)

        for transition in batch:
            if transition.reward is not None and transition.next_state is not None:
                self.update_q_value(
                    transition.state,
                    transition.action.tool_id,
                    transition.reward,
                    transition.next_state,
                    transition.done,
                )


class RLToolRouter:
    """
    强化学习工具路由器

    功能:
    1. 基于RL的工具选择
    2. 在线学习和策略更新
    3. 经验回放
    4. 奖励函数设计
    5. 探索-利用平衡
    """

    def __init__(self):
        self.name = "强化学习工具路由器"
        self.version = "2.0.0"

        # Q-Learning智能体
        self.agent = QLearningAgent()

        # 工具注册表
        self.tool_registry: dict[Action, dict[str, Any]] = {}

        # 历史决策
        self.decision_history: list[dict[str, Any]] = []

        # 统计信息
        self.stats = {
            "total_decisions": 0,
            "correct_decisions": 0,
            "accuracy": 0.0,
            "average_reward": 0.0,
        }

        # 注册工具
        self._register_tools()

        logger.info(f"✅ {self.name} 初始化完成")

    def _register_tools(self):
        """注册工具"""
        tools = {
            Action.TOOL_PATENT_SEARCH: {
                "name": "专利搜索",
                "capabilities": ["patent", "search", "retrieval"],
                "avg_latency_ms": 150,
                "success_rate": 0.92,
            },
            Action.TOOL_PATENT_ANALYSIS: {
                "name": "专利分析",
                "capabilities": ["patent", "analysis", "nlp"],
                "avg_latency_ms": 300,
                "success_rate": 0.89,
            },
            Action.TOOL_LEGAL_QA: {
                "name": "法律问答",
                "capabilities": ["legal", "qa", "knowledge"],
                "avg_latency_ms": 200,
                "success_rate": 0.90,
            },
            Action.TOOL_WEB_SEARCH: {
                "name": "网络搜索",
                "capabilities": ["web", "search", "browser"],
                "avg_latency_ms": 250,
                "success_rate": 0.88,
            },
            Action.TOOL_CODE_GENERATION: {
                "name": "代码生成",
                "capabilities": ["code", "generation", "programming"],
                "avg_latency_ms": 400,
                "success_rate": 0.85,
            },
            Action.TOOL_DATA_ANALYSIS: {
                "name": "数据分析",
                "capabilities": ["data", "analysis", "statistics"],
                "avg_latency_ms": 350,
                "success_rate": 0.87,
            },
            Action.TOOL_KNOWLEDGE_GRAPH: {
                "name": "知识图谱",
                "capabilities": ["knowledge", "graph", "reasoning"],
                "avg_latency_ms": 180,
                "success_rate": 0.91,
            },
            Action.TOOL_MEMORY_RETRIEVAL: {
                "name": "记忆检索",
                "capabilities": ["memory", "retrieval", "context"],
                "avg_latency_ms": 50,
                "success_rate": 0.95,
            },
        }

        for action, info in tools.items():
            self.tool_registry[action] = info

        logger.info(f"📝 已注册 {len(self.tool_registry)} 个工具")

    async def select_tool(
        self, query: str, intent: str, context: Optional[dict[str, Any]] = None
    ) -> RLAction:
        """
        选择工具(基于RL)

        Args:
            query: 用户查询
            intent: 意图类型
            context: 上下文信息

        Returns:
            工具选择动作
        """
        self.stats["total_decisions"] += 1

        # 1. 构建状态
        state = self._build_state(query, intent, context)

        # 2. 智能体选择动作
        action_id = self.agent.select_action(state)

        # 3. 获取工具信息
        tool_info = self.tool_registry[action_id]
        confidence = self._compute_action_confidence(state, action_id)

        action = RLAction(
            tool_id=action_id,
            confidence=confidence,
            metadata={"tool_name": tool_info["name"], "capabilities": tool_info["capabilities"]},
        )

        # 4. 记录决策(等待奖励)
        self.decision_history.append(
            {
                "state": state,
                "action": action,
                "timestamp": datetime.now(),
                "reward": None,  # 待更新
            }
        )

        logger.info(f"🎯 RL选择: {action.tool_id} (置信度: {confidence:.2f})")

        return action

    def _build_state(self, query: str, intent: str, context: dict[str, Any]) -> RLState:
        """构建RL状态"""
        # 查询特征
        query_features = {
            "intent": self._encode_intent(intent),
            "length": len(query) / 1000,  # 归一化
            "complexity": self._compute_complexity(query),
            "has_numbers": 1.0 if any(c.isdigit() for c in query) else 0.0,
        }

        # 上下文特征
        context_features = {
            "type": self._encode_context_type(context),
            "has_history": 1.0 if context and "history" in context else 0.0,
            "has_user_info": 1.0 if context and "user" in context else 0.0,
        }

        # 工具特征(每个工具的适用性)
        tool_features = {}
        for tool_id, tool_info in self.tool_registry.items():
            tool_features[tool_id.value] = {
                "success_rate": tool_info["success_rate"],
                "latency": tool_info["avg_latency_ms"] / 1000,  # 归一化
                "capability_match": self._compute_capability_match(
                    intent, tool_info["capabilities"]
                ),
            }

        return RLState(
            query_features=query_features,
            context_features=context_features,
            tool_features=tool_features,
        )

    def _encode_intent(self, intent: str) -> float:
        """编码意图为数值"""
        intent_map = {
            "patent_search": 0.1,
            "patent_analysis": 0.2,
            "legal_qa": 0.3,
            "web_search": 0.4,
            "code_generation": 0.5,
            "data_analysis": 0.6,
        }
        return intent_map.get(intent, 0.0)

    def _encode_context_type(self, context: dict[str, Any]) -> float:
        """编码上下文类型"""
        if not context:
            return 0.0

        ctx_type = context.get("type", "general")
        type_map = {"general": 0.1, "conversation": 0.2, "task": 0.3, "batch": 0.4}
        return type_map.get(ctx_type, 0.1)

    def _compute_complexity(self, query: str) -> float:
        """计算查询复杂度"""
        # 简化版:基于长度和特殊字符
        return min(1.0, len(query) / 500 + 0.1)

    def _compute_capability_match(self, intent: str, capabilities: list[str]) -> float:
        """计算能力匹配度"""
        intent_lower = intent.lower()
        matches = sum(1 for cap in capabilities if cap in intent_lower)
        return min(1.0, matches * 0.3 + 0.4)

    def _compute_action_confidence(self, state: RLState, action: Action) -> float:
        """计算动作置信度"""
        state_key = self.agent._get_state_key(state)
        q_values = self.agent.q_table[state_key]

        if not q_values:
            return 0.5  # 默认置信度

        max_q = max(q_values.values())
        current_q = q_values[action]

        # 归一化到0-1
        return min(1.0, current_q / (max_q + 1e-6))

    async def provide_feedback(
        self,
        decision_id: int,
        reward_type: RewardType,
        success: bool = True,
        latency_ms: float = 0,
        user_score: Optional[float] = None,
    ):
        """
        提供反馈(奖励信号)

        Args:
            decision_id: 决策ID
            reward_type: 奖励类型
            success: 是否成功
            latency_ms: 延迟(毫秒)
            user_score: 用户评分(0-1)
        """
        if decision_id >= len(self.decision_history):
            logger.warning(f"⚠️ 无效的决策ID: {decision_id}")
            return

        decision = self.decision_history[decision_id]

        # 计算奖励
        reward = self._compute_reward(reward_type, success, latency_ms, user_score)

        # 更新决策记录
        decision["reward"] = reward

        # 更新Q值
        state = decision["state"]
        action = decision["action"].tool_id

        # 简化版:假设没有下一个状态
        dummy_next_state = state
        self.agent.update_q_value(state, action, reward, dummy_next_state, True)

        # 更新统计
        if success:
            self.stats["correct_decisions"] += 1

        self.stats["accuracy"] = self.stats["correct_decisions"] / self.stats["total_decisions"]
        self.stats["average_reward"] = self.agent.stats["average_reward"]

        logger.info(f"📊 反馈已处理: 决策#{decision_id}, 奖励={reward:.2f}")

    def _compute_reward(
        self, reward_type: RewardType, success: bool, latency_ms: float, user_score: float,
    ) -> float:
        """计算奖励值"""
        if reward_type == RewardType.SUCCESS:
            # 成功奖励:+1.0
            base_reward = 1.0 if success else -1.0

            # 延迟惩罚:延迟越高,奖励越低
            latency_penalty = max(0, (latency_ms - 200) / 1000)  # 200ms为基准

            return base_reward - latency_penalty

        elif reward_type == RewardType.FAILURE:
            # 失败惩罚
            return -1.0

        elif reward_type == RewardType.TIMEOUT:
            # 超时惩罚(更严重)
            return -2.0

        elif reward_type == RewardType.USER_FEEDBACK:
            # 用户反馈:直接使用用户评分
            return (user_score or 0.5) * 2 - 1  # 映射到[-1, 1]

        elif reward_type == RewardType.LATENCY:
            # 延迟奖励:延迟越低,奖励越高
            return max(-1, 1 - latency_ms / 500)

        return 0.0

    async def train_model(self, episodes: int = 100):
        """训练模型"""
        logger.info(f"🏋️ 开始训练 ({episodes} 轮)...")

        for episode in range(episodes):
            # 从经验回放中训练
            self.agent.train(batch_size=32)

            if (episode + 1) % 10 == 0:
                logger.info(
                    f"  进度: {episode + 1}/{episodes}, "
                    f"平均奖励: {self.agent.stats['average_reward']:.3f}, "
                    f"探索率: {self.agent.exploration_rate:.3f}"
                )

        logger.info("✅ 训练完成")

    def get_status(self) -> dict[str, Any]:
        """获取路由器状态"""
        return {
            "name": self.name,
            "version": self.version,
            "registered_tools": len(self.tool_registry),
            "decision_stats": self.stats,
            "agent_stats": self.agent.stats,
            "exploration_rate": self.agent.exploration_rate,
            "q_table_size": len(self.agent.q_table),
            "accuracy": self.stats["accuracy"],
        }


# 全局单例
_rl_router_instance: RLToolRouter | None = None


def get_rl_tool_router() -> RLToolRouter:
    """获取强化学习工具路由器实例"""
    global _rl_router_instance
    if _rl_router_instance is None:
        _rl_router_instance = RLToolRouter()
    return _rl_router_instance
