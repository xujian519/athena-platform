#!/usr/bin/env python3
"""
工具路由强化学习环境 - 第二阶段
Tool Routing Reinforcement Learning Environment - Phase 2

基于强化学习的智能工具路由优化

核心功能:
1. 状态空间定义
2. 动作空间定义
3. 奖励函数设计
4. 环境交互接口
5. 训练和评估框架

作者: 小诺·双鱼公主
版本: v1.0.0 "RL路由优化"
创建: 2026-01-12
"""

from __future__ import annotations
import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ToolRoutingAction(Enum):
    """路由动作类型"""

    SELECT_SINGLE = "select_single"  # 选择单个工具
    SELECT_COMBINATION = "select_combination"  # 选择工具组合
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行


@dataclass
class RoutingState:
    """路由状态"""

    # 意图信息
    intent: str
    intent_confidence: float

    # 上下文特征
    user_preferences: dict[str, float]
    conversation_history: list[str]

    # 可用工具
    available_tools: list[str]
    tool_capabilities: dict[str, list[str]]  # 工具性能特征
    tool_reliability: dict[str, float]
    tool_cost: dict[str, float]
    tool_speed: dict[str, float]

    # 状态向量(用于神经网络输入)
    state_vector: np.ndarray = field(init=False)

    def __post_init__(self):
        """构建状态向量"""
        self.state_vector = self._encode_to_vector()

    def _encode_to_vector(self) -> np.ndarray:
        """将状态编码为向量"""
        # 意图编码 (one-hot)
        intent_features = self._encode_intent()

        # 工具特征编码
        tool_features = self._encode_tools()

        # 上下文特征编码
        context_features = self._encode_context()

        # 拼接所有特征
        return np.concatenate([intent_features, tool_features, context_features])

    def _encode_intent(self) -> np.ndarray:
        """编码意图特征"""
        # 简化: 使用意图置信度
        return np.array([self.intent_confidence])

    def _encode_tools(self) -> np.ndarray:
        """编码工具特征"""
        if not self.available_tools:
            return np.zeros(10)  # 特征维度

        # 工具数量
        num_tools = len(self.available_tools)

        # 平均可靠性
        avg_reliability = np.mean([self.tool_reliability.get(t, 0.8) for t in self.available_tools])

        # 平均成本
        avg_cost = np.mean([self.tool_cost.get(t, 0.3) for t in self.available_tools])

        return np.array([num_tools / 20, avg_reliability, avg_cost] + [0] * 7)

    def _encode_context(self) -> np.ndarray:
        """编码上下文特征"""
        # 对话轮次
        history_len = len(self.conversation_history)

        # 用户偏好数量
        pref_count = len(self.user_preferences)

        return np.array([history_len / 50, pref_count / 10] + [0] * 8)


@dataclass
class RoutingAction:
    """路由动作"""

    action_type: ToolRoutingAction
    selected_tools: list[str]
    execution_order: list[str]
    confidence: float
    reasoning: str


@dataclass
class RoutingReward:
    """路由奖励"""

    success: float  # 成功奖励
    efficiency: float  # 效率奖励
    cost_saving: float  # 成本奖励
    user_satisfaction: float  # 用户满意度
    total: float  # 总奖励


class ToolRoutingEnv:
    """工具路由强化学习环境"""

    metadata = {"render_modes": [], "render_fps": 30}

    def __init__(self, config: dict[str, Any] | None = None):
        self.name = "工具路由RL环境"
        self.version = "1.0.0"

        # 配置
        self.config = config or self._default_config()

        # 状态空间
        self.state: RoutingState | None = None

        # 动作空间
        self.action_space_size = self.config.get("action_space_size", 50)

        # 奖励权重
        self.reward_weights = self.config.get(
            "reward_weights",
            {"success": 0.5, "efficiency": 0.2, "cost": 0.15, "satisfaction": 0.15},
        )

        # 统计信息
        self.stats = {
            "total_episodes": 0,
            "total_steps": 0,
            "successful_routes": 0,
            "avg_reward": 0.0,
            "avg_reward_history": [],
        }

        # 当前回合信息
        self.current_step = 0
        self.current_reward = 0.0
        self.done = False

        logger.info(f"🎮 {self.name} 初始化完成")

    def _default_config(self) -> dict[str, Any]:
        """默认配置"""
        return {
            "action_space_size": 50,
            "max_steps_per_episode": 10,
            "reward_weights": {
                "success": 0.5,
                "efficiency": 0.2,
                "cost": 0.15,
                "satisfaction": 0.15,
            },
        }

    def reset(self, seed: int | None = None) -> RoutingState:
        """重置环境"""
        # 随机生成初始状态
        self.state = self._generate_random_state()
        self.current_step = 0
        self.current_reward = 0.0
        self.done = False

        self.stats["total_episodes"] += 1

        return self.state

    def _generate_random_state(self) -> RoutingState:
        """生成随机状态"""
        # 随机选择意图
        intents = [
            "patent_search",
            "patent_analysis",
            "coding",
            "data_analysis",
            "daily_chat",
            "legal_query",
        ]
        intent = random.choice(intents)

        # 随机可用工具
        all_tools = [
            "patent",
            "xiaona",
            "coding_assistant",
            "nlp",
            "knowledge_graph",
            "daily_chat",
            "optimization",
        ]
        available_tools = random.sample(all_tools, k=random.randint(3, 5))

        # 工具能力
        tool_capabilities = {
            "patent": ["专利分析", "专利检索"],
            "xiaona": ["专利法律", "案例分析"],
            "coding_assistant": ["代码生成", "调试"],
            "nlp": ["文本分析", "实体识别"],
            "knowledge_graph": ["知识推理", "关系分析"],
            "daily_chat": ["闲聊", "问候"],
            "optimization": ["性能优化", "资源调度"],
        }

        return RoutingState(
            intent=intent,
            intent_confidence=random.uniform(0.7, 0.99),
            user_preferences={},
            conversation_history=[],
            available_tools=available_tools,
            tool_capabilities={t: tool_capabilities.get(t, []) for t in available_tools},
            tool_reliability={t: random.uniform(0.8, 0.99) for t in available_tools},
            tool_cost={t: random.uniform(0.1, 0.5) for t in available_tools},
            tool_speed={t: random.uniform(0.5, 1.0) for t in available_tools},
        )

    def step(self, action: RoutingAction) -> tuple[RoutingState, float, bool, dict[str, Any]]:
        """
        执行一步

        Returns:
            tuple: (next_state, reward, done, info)
        """
        self.current_step += 1

        # 1. 验证动作有效性
        if not self._is_valid_action(action):
            return self.state, -1.0, True, {"reason": "invalid_action"}

        # 2. 计算奖励
        reward = self._calculate_reward(action)

        # 3. 更新状态
        self.current_reward += reward
        self.done = self.current_step >= self.config["max_steps_per_episode"]

        # 4. 更新统计
        self.stats["total_steps"] += 1

        # 5. 返回信息
        info = {"step": self.current_step, "action": action, "episode_reward": self.current_reward}

        return self.state, reward, self.done, info

    def _is_valid_action(self, action: RoutingAction) -> bool:
        """验证动作有效性"""
        # 检查选择的工具是否可用
        for tool in action.selected_tools:
            if tool not in self.state.available_tools:
                return False

        # 检查执行顺序是否合理
        return set(action.execution_order) == set(action.selected_tools)

    def _calculate_reward(self, action: RoutingAction) -> float:
        """计算奖励"""
        # 1. 成功奖励
        success_reward = self._calculate_success_reward(action)

        # 2. 效率奖励
        efficiency_reward = self._calculate_efficiency_reward(action)

        # 3. 成本奖励
        cost_reward = self._calculate_cost_reward(action)

        # 4. 用户满意度奖励(模拟)
        satisfaction_reward = self._calculate_satisfaction_reward(action)

        # 加权求和
        total_reward = (
            self.reward_weights["success"] * success_reward
            + self.reward_weights["efficiency"] * efficiency_reward
            + self.reward_weights["cost"] * cost_reward
            + self.reward_weights["satisfaction"] * satisfaction_reward
        )

        return total_reward

    def _calculate_success_reward(self, action: RoutingAction) -> float:
        """计算成功奖励"""
        # 基于意图和工具匹配度
        intent_tool_map = {
            "patent_search": ["patent", "xiaona", "knowledge_graph"],
            "patent_analysis": ["patent", "xiaona", "nlp"],
            "coding": ["coding_assistant", "optimization"],
            "data_analysis": ["nlp", "knowledge_graph"],
            "daily_chat": ["daily_chat"],
            "legal_query": ["xiaona", "legal"],
        }

        expected_tools = set(intent_tool_map.get(self.state.intent, []))
        selected_tools = set(action.selected_tools)

        # 计算匹配度
        if not expected_tools:
            return 0.5  # 未知意图,中等奖励

        intersection = expected_tools & selected_tools
        match_score = len(intersection) / len(expected_tools)

        return match_score

    def _calculate_efficiency_reward(self, action: RoutingAction) -> float:
        """计算效率奖励"""
        # 工具数量越少,效率越高
        num_tools = len(action.selected_tools)

        if num_tools == 1:
            return 1.0
        elif num_tools == 2:
            return 0.8
        else:
            return 0.5

    def _calculate_cost_reward(self, action: RoutingAction) -> float:
        """计算成本奖励"""
        # 总成本
        total_cost = sum(self.state.tool_cost.get(t, 0.3) for t in action.selected_tools)

        # 成本越低,奖励越高
        if total_cost < 0.2:
            return 1.0
        elif total_cost < 0.4:
            return 0.7
        else:
            return 0.4

    def _calculate_satisfaction_reward(self, action: RoutingAction) -> float:
        """计算用户满意度奖励(模拟)"""
        # 基于置信度
        confidence_bonus = action.confidence * 0.5

        # 基于执行顺序合理性
        order_bonus = 0.3 if len(action.execution_order) <= 2 else 0.1

        return confidence_bonus + order_bonus

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def close(self):
        """关闭环境"""
        logger.info(f"🎮 {self.name} 已关闭")


# 全局实例
_env_instance: ToolRoutingEnv | None = None


def get_tool_routing_env(config: dict | None = None) -> ToolRoutingEnv:
    """获取工具路由RL环境单例"""
    global _env_instance
    if _env_instance is None:
        _env_instance = ToolRoutingEnv(config)
    return _env_instance


# 辅助函数
def create_random_action(state: RoutingState) -> RoutingAction:
    """创建随机动作"""
    # 随机选择工具
    num_tools = random.choice([1, 2, 3])
    selected_tools = random.sample(
        state.available_tools, k=min(num_tools, len(state.available_tools))
    )

    # 执行顺序(按优先级)
    execution_order = sorted(
        selected_tools, key=lambda t: state.tool_reliability.get(t, 0.8), reverse=True
    )

    return RoutingAction(
        action_type=(
            ToolRoutingAction.SELECT_COMBINATION
            if num_tools > 1
            else ToolRoutingAction.SELECT_SINGLE
        ),
        selected_tools=selected_tools,
        execution_order=execution_order,
        confidence=random.uniform(0.7, 0.95),
        reasoning="random_action",
    )


def validate_rl_installation():
    """验证RL环境依赖"""
    try:

        logger.info("✅ Gymnasium已安装")
        return True
    except ImportError:
        logger.warning("⚠️ Gymnasium未安装,使用简化RL环境")
        return False
