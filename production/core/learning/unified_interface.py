#!/usr/bin/env python3
"""
统一学习引擎接口
Unified Learning Engine Interface

为Athena平台所有模块提供统一的学习引擎接口:
- 标准化的经验记录
- 统一的数据格式
- 通用的优化触发
- 跨模块学习协调

作者: Athena AI Team
版本: 1.0.0
创建: 2026-01-29
"""

from __future__ import annotations
import asyncio
import json

# 添加项目路径
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent  # 修复：移除多余的.parent
sys.path.insert(0, str(project_root))

# 使用统一的日志配置
try:
    from production.core.logging_config import setup_logging
    logger = setup_logging()
except ImportError:
    # 如果导入失败，使用标准logging
    import logging
    logger = logging.getLogger(__name__)


# =============================================================================
# 枚举定义
# =============================================================================

class ModuleType(Enum):
    """平台模块类型"""
    AGENT = "agent"                    # 智能体
    INTENT = "intent"                  # 意图识别
    RAG = "rag"                        # RAG检索
    TOOL = "tool"                      # 工具调用
    DIALOG = "dialog"                  # 对话管理
    KNOWLEDGE = "knowledge"            # 知识图谱
    PLANNING = "planning"              # 任务规划
    EXECUTION = "execution"            # 任务执行


class LearningPriority(Enum):
    """学习优先级"""
    CRITICAL = "critical"              # 关键（用户纠正）
    HIGH = "high"                      # 高（失败案例）
    MEDIUM = "medium"                  # 中（低置信度）
    LOW = "low"                        # 低（正常执行）


class FeedbackType(Enum):
    """反馈类型"""
    EXPLICIT = "explicit"              # 显式反馈（用户评价）
    IMPLICIT = "implicit"              # 隐式反馈（行为数据）
    CORRECTION = "correction"          # 纠正反馈（用户纠正）


# =============================================================================
# 统一数据结构
# =============================================================================

@dataclass
class LearningExperience:
    """
    统一学习经验数据结构

    所有模块的学习经验都使用这个统一格式
    """
    # 基本信息
    experience_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    module_type: ModuleType = ModuleType.AGENT
    module_id: str = ""                # 具体模块标识

    # 上下文信息
    context: dict[str, Any] = field(default_factory=dict)
    state: str = ""                    # 状态标识

    # 决策信息
    action: str = ""                   # 采取的动作
    action_parameters: dict[str, Any] = field(default_factory=dict)

    # 结果信息
    result: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    confidence: float = 0.0
    execution_time_ms: float = 0.0

    # 反馈信息
    true_action: str | None = None          # 真实正确的动作（用户反馈）
    user_feedback: str | None = None        # 用户反馈内容
    user_satisfaction: float | None = None  # 用户满意度 (0-1)
    feedback_type: FeedbackType = FeedbackType.IMPLICIT

    # 学习信息
    reward: float = 0.0
    priority: LearningPriority = LearningPriority.MEDIUM
    importance: float = 0.5            # 重要性权重 (0-1)

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['module_type'] = self.module_type.value
        data['priority'] = self.priority.value
        data['feedback_type'] = self.feedback_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'LearningExperience':
        """从字典创建"""
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if isinstance(data.get('module_type'), str):
            data['module_type'] = ModuleType(data['module_type'])
        if isinstance(data.get('priority'), str):
            data['priority'] = LearningPriority(data['priority'])
        if isinstance(data.get('feedback_type'), str):
            data['feedback_type'] = FeedbackType(data['feedback_type'])
        return cls(**data)


@dataclass
class OptimizationReport:
    """优化报告"""
    timestamp: datetime = field(default_factory=datetime.now)
    module_type: ModuleType = ModuleType.AGENT
    module_id: str = ""

    # 优化前后的指标
    baseline_metrics: dict[str, float] = field(default_factory=dict)
    optimized_metrics: dict[str, float] = field(default_factory=dict)
    improvement: dict[str, float] = field(default_factory=dict)

    # 优化详情
    optimization_type: str = ""        # 优化类型
    optimization_details: dict[str, Any] = field(default_factory=dict)

    # 状态
    status: str = "completed"          # completed, failed, skipped
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['module_type'] = self.module_type.value
        return data


# =============================================================================
# 统一学习引擎接口
# =============================================================================

class UnifiedLearningInterface:
    """
    统一学习引擎接口

    为所有平台模块提供标准化的学习接口
    """

    def __init__(
        self,
        module_type: ModuleType,
        module_id: str,
        enable_p0: bool = True,
        enable_p1: bool = True,
        enable_p2: bool = True,
    ):
        """
        初始化统一学习接口

        Args:
            module_type: 模块类型
            module_id: 模块标识
            enable_p0: 是否启用P0自主学习
            enable_p1: 是否启用P1在线学习
            enable_p2: 是否启用P2强化学习
        """
        self.module_type = module_type
        self.module_id = module_id
        self.enable_p0 = enable_p0
        self.enable_p1 = enable_p1
        self.enable_p2 = enable_p2

        # 学习引擎编排器（延迟加载）
        self._orchestrator = None

        # 本地经验缓存
        self._experience_cache: list[LearningExperience] = []
        self._cache_size = 100

        logger.info(
            f"🧠 统一学习接口初始化: {module_type.value}/{module_id} "
            f"(P0:{enable_p0}, P1:{enable_p1}, P2:{enable_p2})"
        )

    @property
    def orchestrator(self):
        """延迟加载学习引擎编排器"""
        if self._orchestrator is None:
            from production.core.intent.learning_integration import get_intent_learning_orchestrator
            self._orchestrator = get_intent_learning_orchestrator(
                agent_id=f"{self.module_type.value}_{self.module_id}",
                enable_all=True,
            )
        return self._orchestrator

    # ==============================================================================
    # 核心接口: 记录经验
    # ==============================================================================

    async def record_experience(
        self,
        context: dict[str, Any],
        action: str,
        result: dict[str, Any],
        success: bool = True,
        confidence: float = 0.0,
        execution_time_ms: float = 0.0,
        true_action: str | None = None,
        user_satisfaction: float | None = None,
        user_feedback: str | None = None,
        state: str | None = None,
        reward: float | None = None,
        importance: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LearningExperience:
        """
        记录学习经验（统一接口）

        Args:
            context: 执行上下文
            action: 执行的动作
            result: 执行结果
            success: 是否成功
            confidence: 置信度
            execution_time_ms: 执行时间（毫秒）
            true_action: 真实正确的动作（用户反馈）
            user_satisfaction: 用户满意度 (0-1)
            user_feedback: 用户反馈内容
            state: 状态标识
            reward: 奖励值（如果不提供，将自动计算）
            importance: 重要性权重 (0-1)
            metadata: 额外元数据

        Returns:
            LearningExperience: 记录的经验对象
        """
        # 自动计算奖励
        if reward is None:
            reward = self._calculate_reward(
                success=success,
                confidence=confidence,
                execution_time_ms=execution_time_ms,
                user_satisfaction=user_satisfaction,
                true_action=true_action,
                action=action,
            )

        # 自动确定优先级
        priority = self._determine_priority(
            success=success,
            true_action=true_action,
            user_satisfaction=user_satisfaction,
            reward=reward,
        )

        # 确定反馈类型
        feedback_type = FeedbackType.IMPLICIT
        if true_action is not None:
            feedback_type = FeedbackType.CORRECTION
        elif user_feedback is not None or user_satisfaction is not None:
            feedback_type = FeedbackType.EXPLICIT

        # 创建经验对象
        experience = LearningExperience(
            module_type=self.module_type,
            module_id=self.module_id,
            context=context,
            state=state or self._generate_state(context),
            action=action,
            result=result,
            success=success,
            confidence=confidence,
            execution_time_ms=execution_time_ms,
            true_action=true_action,
            user_feedback=user_feedback,
            user_satisfaction=user_satisfaction,
            feedback_type=feedback_type,
            reward=reward,
            priority=priority,
            importance=importance or abs(reward),
            metadata=metadata or {},
        )

        # 添加到缓存
        self._experience_cache.append(experience)
        if len(self._experience_cache) > self._cache_size:
            self._experience_cache.pop(0)

        # 转发到学习引擎编排器
        try:
            await self.orchestrator.record_experience(
                query=context.get("query", ""),
                predicted_intent=action,
                confidence=confidence,
                response_time_ms=execution_time_ms,
                true_intent=true_action,
                user_satisfaction=user_satisfaction,
            )
        except Exception as e:
            logger.warning(f"⚠️ 转发经验到编排器失败: {e}")

        logger.debug(
            f"📚 经验已记录: {self.module_type.value}/{action} "
            f"(奖励: {reward:.2f}, 优先级: {priority.value})"
        )

        return experience

    # ==============================================================================
    # 核心接口: 触发优化
    # ==============================================================================

    async def trigger_optimization(self) -> OptimizationReport:
        """
        触发系统优化

        Returns:
            OptimizationReport: 优化报告
        """
        logger.info(f"🔧 触发优化: {self.module_type.value}/{self.module_id}")

        # 获取优化前指标
        baseline_metrics = await self._get_current_metrics()

        # 调用学习引擎编排器优化
        try:
            optimization_result = await self.orchestrator.optimize_system()

            # 获取优化后指标
            optimized_metrics = await self._get_current_metrics()

            # 计算改进
            improvement = {}
            for key in baseline_metrics:
                if key in optimized_metrics:
                    improvement[key] = optimized_metrics[key] - baseline_metrics[key]

            report = OptimizationReport(
                module_type=self.module_type,
                module_id=self.module_id,
                baseline_metrics=baseline_metrics,
                optimized_metrics=optimized_metrics,
                improvement=improvement,
                optimization_type=optimization_result.get("status", "unknown"),
                optimization_details=optimization_result,
                status="completed" if optimization_result.get("status") in ["optimized", "good"] else "skipped",
                message=optimization_result.get("message", ""),
            )

        except Exception as e:
            logger.error(f"❌ 优化失败: {e}")
            report = OptimizationReport(
                module_type=self.module_type,
                module_id=self.module_id,
                baseline_metrics=baseline_metrics,
                optimized_metrics=baseline_metrics,
                status="failed",
                message=str(e),
            )

        return report

    # ==============================================================================
    # 核心接口: 强化学习更新
    # ==============================================================================

    async def update_q_value(
        self,
        state: str,
        action: str,
        reward: float,
    ):
        """
        更新Q值（强化学习）

        Args:
            state: 状态
            action: 动作
            reward: 奖励值
        """
        if not self.enable_p2:
            return

        try:
            rl_agent = self.orchestrator.learning_engines.get("p2_reinforcement")
            if rl_agent:
                # 获取当前Q值
                current_q = rl_agent.q_table.get((state, action), 0.0)

                # Q值更新: Q(s,a) = Q(s,a) + α * [r - Q(s,a)]
                new_q = current_q + rl_agent.learning_rate * (reward - current_q)

                # 更新Q表
                rl_agent.q_table[(state, action)] = new_q

                logger.debug(
                    f"🎮 Q值更新: {state}/{action} "
                    f"{current_q:.3f} → {new_q:.3f}"
                )

        except Exception as e:
            logger.warning(f"⚠️ Q值更新失败: {e}")

    # ==============================================================================
    # 辅助方法
    # ==============================================================================

    def _calculate_reward(
        self,
        success: bool,
        confidence: float,
        execution_time_ms: float,
        user_satisfaction: float | None,
        true_action: str | None,
        action: str,
    ) -> float:
        """计算奖励值"""
        reward = 0.0

        # 基础奖励
        if success:
            reward += 1.0
        else:
            reward -= 1.0

        # 置信度奖励
        if success:
            reward += confidence * 0.5  # 成功且高置信度，额外奖励
        else:
            reward -= confidence * 0.3  # 失败但高置信度，额外惩罚

        # 时间惩罚
        if execution_time_ms > 1000:  # 超过1秒
            reward -= min(execution_time_ms / 5000.0, 0.5)

        # 用户满意度奖励
        if user_satisfaction is not None:
            reward += (user_satisfaction - 0.5) * 2.0  # 放大满意度影响

        # 纠正惩罚
        if true_action is not None and true_action != action:
            reward -= 1.5  # 用户纠正，严重惩罚

        return max(-2.0, min(2.0, reward))

    def _determine_priority(
        self,
        success: bool,
        true_action: str | None,
        user_satisfaction: float | None,
        reward: float,
    ) -> LearningPriority:
        """确定学习优先级"""
        # 用户纠正，最高优先级
        if true_action is not None:
            return LearningPriority.CRITICAL

        # 失败案例，高优先级
        if not success:
            return LearningPriority.HIGH

        # 低满意度，中高优先级
        if user_satisfaction is not None and user_satisfaction < 0.5:
            return LearningPriority.HIGH

        # 负奖励，中优先级
        if reward < 0:
            return LearningPriority.MEDIUM

        # 默认低优先级
        return LearningPriority.LOW

    def _generate_state(self, context: dict[str, Any]) -> str:
        """从上下文生成状态标识"""
        # 根据模块类型生成不同的状态
        if self.module_type == ModuleType.INTENT:
            query = context.get("query", "")[:50]
            return f"intent_{hash(query) % 10000}"

        elif self.module_type == ModuleType.RAG:
            query_type = context.get("query_type", "general")
            return f"rag_{query_type}"

        elif self.module_type == ModuleType.TOOL:
            task = context.get("task", "unknown")
            return f"tool_{task}"

        else:
            return f"{self.module_type.value}_default"

    async def _get_current_metrics(self) -> dict[str, float]:
        """获取当前性能指标"""
        try:
            status = self.orchestrator.get_learning_status()
            return status.get("metrics", {})
        except Exception:
            return {}

    # ==============================================================================
    # 数据导出
    # ==============================================================================

    def export_experiences(self, filepath: str | None = None) -> str:
        """
        导出学习经验

        Args:
            filepath: 导出文件路径（可选）

        Returns:
            导出文件的路径
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"data/learning_experiences_{self.module_id}_{timestamp}.json"

        # 确保目录存在
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # 导出数据
        data = {
            "export_time": datetime.now().isoformat(),
            "module_type": self.module_type.value,
            "module_id": self.module_id,
            "total_experiences": len(self._experience_cache),
            "experiences": [exp.to_dict() for exp in self._experience_cache],
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"📤 学习经验已导出: {filepath}")
        return filepath

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self._experience_cache:
            return {
                "total_experiences": 0,
                "success_rate": 0.0,
                "avg_reward": 0.0,
                "avg_confidence": 0.0,
            }

        total = len(self._experience_cache)
        successes = sum(1 for e in self._experience_cache if e.success)
        total_reward = sum(e.reward for e in self._experience_cache)
        total_confidence = sum(e.confidence for e in self._experience_cache)

        return {
            "total_experiences": total,
            "success_rate": successes / total,
            "avg_reward": total_reward / total,
            "avg_confidence": total_confidence / total,
            "priority_distribution": {
                priority.value: sum(1 for e in self._experience_cache if e.priority == priority)
                for priority in LearningPriority
            },
        }


# =============================================================================
# 工厂函数
# =============================================================================

def get_learning_interface(
    module_type: ModuleType | str,
    module_id: str,
    enable_p0: bool = True,
    enable_p1: bool = True,
    enable_p2: bool = True,
) -> UnifiedLearningInterface:
    """
    获取统一学习接口实例

    Args:
        module_type: 模块类型
        module_id: 模块标识
        enable_p0: 是否启用P0
        enable_p1: 是否启用P1
        enable_p2: 是否启用P2

    Returns:
        UnifiedLearningInterface: 学习接口实例
    """
    if isinstance(module_type, str):
        module_type = ModuleType(module_type)

    return UnifiedLearningInterface(
        module_type=module_type,
        module_id=module_id,
        enable_p0=enable_p0,
        enable_p1=enable_p1,
        enable_p2=enable_p2,
    )


# =============================================================================
# 公共工具函数
# =============================================================================

def epsilon_greedy_select(
    options: list[Any],
    q_values: dict[Any, float],
    epsilon: float = 0.1,
) -> tuple[Any, float]:
    """
    ε-贪婪选择策略

    在探索和利用之间平衡：
    - 以epsilon概率随机选择（探索）
    - 以1-epsilon概率选择Q值最高的选项（利用）

    Args:
        options: 可选选项列表
        q_values: 每个选项的Q值字典
        epsilon: 探索率（默认0.1）

    Returns:
        (selected_option, confidence): 选中的选项和置信度

    Examples:
        >>> options = ["tool_a", "tool_b", "tool_c"]
        >>> q_values = {"tool_a": 0.8, "tool_b": 0.5, "tool_c": 0.3}
        >>> option, confidence = epsilon_greedy_select(options, q_values, epsilon=0.1)
        >>> # 90%概率选择tool_a，10%概率随机选择

        >>> # 如果所有Q值都是0，会随机选择
        >>> q_values = {"tool_a": 0.0, "tool_b": 0.0, "tool_c": 0.0}
        >>> option, confidence = epsilon_greedy_select(options, q_values)
        >>> # 会随机选择一个选项
    """
    import random

    # 如果没有Q值或所有Q值都是0，强制探索
    if not q_values or not any(q_values.values()):
        selected = random.choice(options)
        confidence = 0.5
        return selected, confidence

    # ε-贪婪策略
    if random.random() < epsilon:
        # 探索：随机选择
        selected = random.choice(options)
        confidence = 0.5
    else:
        # 利用：选择Q值最高的选项
        selected = max(q_values, key=q_values.get)
        max_q = q_values[selected]
        # 将Q值转换为置信度（假设Q值范围是[-2, 2]，映射到[0, 1]）
        confidence = min(max_q / 2.0 + 0.5, 1.0)
        confidence = max(confidence, 0.0)

    return selected, confidence


def calculate_q_table_reward(
    success: bool,
    confidence: float,
    execution_time_ms: float,
    user_satisfaction: float | None = None,
    baseline_time_ms: float = 1000.0,
) -> float:
    """
    计算Q学习奖励值

    综合考虑多个因素计算奖励：
    - 成功/失败
    - 置信度
    - 执行时间
    - 用户满意度

    Args:
        success: 是否成功
        confidence: 置信度 (0-1)
        execution_time_ms: 执行时间（毫秒）
        user_satisfaction: 用户满意度 (0-1)，可选
        baseline_time_ms: 基准执行时间（毫秒），默认1000ms

    Returns:
        float: 奖励值，通常在[-2, 2]范围内

    Examples:
        >>> # 成功、快速、高满意度
        >>> reward = calculate_q_table_reward(
        ...     success=True,
        ...     confidence=0.9,
        ...     execution_time_ms=500.0,
        ...     user_satisfaction=0.95
        ... )
        >>> # reward ≈ 1.5 - 2.0

        >>> # 失败、慢、低满意度
        >>> reward = calculate_q_table_reward(
        ...     success=False,
        ...     confidence=0.5,
        ...     execution_time_ms=2000.0,
        ...     user_satisfaction=0.3
        ... )
        >>> # reward ≈ -1.5 - -2.0
    """
    reward = 0.0

    # 1. 成功奖励
    if success:
        reward += 1.0
    else:
        reward -= 1.0

    # 2. 置信度奖励（鼓励高置信度的正确决策）
    reward += (confidence - 0.5) * 0.5

    # 3. 时间奖励（鼓励快速响应）
    time_ratio = execution_time_ms / baseline_time_ms
    if time_ratio < 1.0:
        # 比基准快，给予奖励
        reward += (1.0 - time_ratio) * 0.3
    else:
        # 比基准慢，给予惩罚
        reward -= min((time_ratio - 1.0) * 0.3, 0.5)

    # 4. 用户满意度奖励
    if user_satisfaction is not None:
        reward += (user_satisfaction - 0.5) * 1.0

    # 限制奖励范围
    return max(-2.0, min(2.0, reward))


def get_q_values_from_orchestrator(
    learning_interface: Any,
    state: str,
    options: list[Any],
) -> dict[Any, float]:
    """
    从学习编排器获取Q值（带None检查）

    安全地从learning_interface.orchestrator获取Q值，
    如果任何中间对象为None，返回空字典。

    Args:
        learning_interface: 学习接口实例
        state: 状态标识
        options: 选项列表

    Returns:
        Dict[Any, float]: 选项到Q值的映射

    Examples:
        >>> q_values = get_q_values_from_orchestrator(
        ...     learning_interface,
        ...     state="tool_for_search",
        ...     options=["tool_a", "tool_b"]
        ... )
        >>> # q_values = {"tool_a": 0.8, "tool_b": 0.5}
        >>> # 或者如果orchestrator为None：q_values = {}
    """
    q_values = {}

    # None检查链
    if not learning_interface:
        return q_values

    if not hasattr(learning_interface, 'orchestrator'):
        return q_values

    orchestrator = learning_interface.orchestrator
    if not orchestrator:
        return q_values

    if not hasattr(orchestrator, 'learning_engines'):
        return q_values

    learning_engines = orchestrator.learning_engines
    if not learning_engines:
        return q_values

    rl_agent = learning_engines.get("p2_reinforcement")
    if not rl_agent:
        return q_values

    if not hasattr(rl_agent, 'q_table'):
        return q_values

    # 获取Q值
    for option in options:
        q_values[option] = rl_agent.q_table.get((state, option), 0.0)

    return q_values


# =============================================================================
# 测试代码
# =============================================================================
if __name__ == "__main__":
    import asyncio

    async def test_unified_interface():
        """测试统一接口"""
        print("=" * 80)
        print("🧪 测试统一学习引擎接口")
        print("=" * 80)

        # 创建接口
        interface = get_learning_interface(
            module_type=ModuleType.AGENT,
            module_id="test_agent",
        )

        # 测试记录经验
        print("\n📚 测试记录经验...")
        await interface.record_experience(
            context={"query": "搜索专利", "task": "patent_search"},
            action="use_patent_search_tool",
            result={"found": 15},
            success=True,
            confidence=0.9,
            execution_time_ms=150.0,
            user_satisfaction=0.95,
        )

        await interface.record_experience(
            context={"query": "分析专利", "task": "patent_analysis"},
            action="use_patent_analysis_tool",
            result={"error": "tool not available"},
            success=False,
            confidence=0.7,
            execution_time_ms=50.0,
            true_action="use_alternative_tool",  # 用户纠正
            user_satisfaction=0.3,
        )

        # 获取统计
        print("\n📊 统计信息:")
        stats = interface.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # 导出数据
        print("\n📤 导出学习经验...")
        export_path = interface.export_experiences()
        print(f"  文件: {export_path}")

        print("\n" + "=" * 80)
        print("✅ 测试完成!")
        print("=" * 80)

    asyncio.run(test_unified_interface())
