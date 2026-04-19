#!/usr/bin/env python3
from __future__ import annotations
"""
失败模式防护系统 - 系统性防护多智能体常见失败模式
Failure Prevention System - Systematic Prevention of Multi-Agent Failure Modes

基于行业最佳实践,防护四大失败模式:
- Token Sprawl: 上下文随交互轮次指数增长
- Coordination Drift: 智能体间目标不一致,行动冲突
- Context Overflow: 上下文超过模型处理能力
- Hallucination: 智能体生成虚假或错误信息

作者: 小诺·双鱼公主
创建时间: 2026-01-07
版本: v1.0.0
"""

import asyncio
import contextlib
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class FailureMode(Enum):
    """失败模式"""

    TOKEN_SPRAWL = "token_sprawl"  # Token扩张
    COORDINATION_DRIFT = "coordination_drift"  # 协调漂移
    CONTEXT_OVERFLOW = "context_overflow"  # 上下文溢出
    HALLUCINATION = "hallucination"  # 幻觉


class PreventionAction(Enum):
    """预防行动"""

    COMPRESS_CONTEXT = "compress_context"
    SYNC_GOALS = "sync_goals"
    RESOLVE_CONFLICT = "resolve_conflict"
    FACT_CHECK = "fact_check"
    REDUCE_COMPLEXITY = "reduce_complexity"
    REQUEST_CONFIRMATION = "request_confirmation"


@dataclass
class AgentGoal:
    """智能体目标"""

    agent_id: str
    goal: str
    priority: int
    timestamp: float
    status: str = "active"  # active, completed, failed


@dataclass
class ConflictInfo:
    """冲突信息"""

    conflict_id: str
    conflict_type: str
    agents_involved: list[str]
    description: str
    severity: str  # low, medium, high, critical
    detected_at: float
    resolution_status: str = "unresolved"


@dataclass
class PreventionAlert:
    """预防警报"""

    failure_mode: FailureMode
    severity: str  # low, medium, high, critical
    description: str
    suggested_actions: list[PreventionAction]
    detected_at: float
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreventionMetrics:
    """预防指标"""

    total_alerts: int = 0
    alerts_by_mode: dict[FailureMode, int] = field(default_factory=dict)
    alerts_resolved: int = 0
    avg_resolution_time: float = 0.0
    last_check_time: float = 0.0


class FailurePreventionSystem:
    """
    失败模式防护系统

    核心功能:
    1. Token Sprawl防护
    2. Coordination Drift检测和解决
    3. Context Overflow监控
    4. Hallucination检测和预防
    5. 系统健康监控和告警
    """

    def __init__(self, check_interval: float = 30.0):
        """
        初始化失败模式防护系统

        Args:
            check_interval: 检查间隔(秒)
        """
        self.check_interval = check_interval

        # 智能体目标追踪
        self.agent_goals: dict[str, AgentGoal] = {}

        # 冲突追踪
        self.active_conflicts: list[ConflictInfo] = []
        self.resolved_conflicts: list[ConflictInfo] = []

        # 警报历史
        self.alert_history: deque = deque(maxlen=1000)

        # 预防指标
        self.metrics = PreventionMetrics()

        # 监控任务
        self._monitoring_task: asyncio.Task | None = None

        logger.info("失败模式防护系统初始化完成")

    async def start_monitoring(self):
        """启动监控任务"""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("监控任务已在运行")
            return

        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("失败模式防护监控已启动")

    async def stop_monitoring(self):
        """停止监控任务"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitoring_task
            logger.info("失败模式防护监控已停止")

    async def _monitoring_loop(self):
        """监控循环"""
        while True:
            try:
                # 执行所有检查
                await self._run_all_checks()

                # 等待下一次检查
                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环异常: {e}", exc_info=True)

    async def _run_all_checks(self):
        """运行所有检查"""
        # 1. Token Sprawl检查
        token_sprawl_alerts = await self.check_token_sprawl()

        # 2. Coordination Drift检查
        coordination_alerts = await self.check_coordination_drift()

        # 3. Context Overflow检查
        overflow_alerts = await self.check_context_overflow()

        # 4. Hallucination检查 (基于历史)
        hallucination_alerts = await self.check_hallucination_risk()

        # 汇总警报
        all_alerts = (
            token_sprawl_alerts + coordination_alerts + overflow_alerts + hallucination_alerts
        )

        # 处理警报
        for alert in all_alerts:
            await self._handle_alert(alert)

        # 更新指标
        self.metrics.total_alerts += len(all_alerts)
        self.metrics.last_check_time = datetime.now().timestamp()

    async def check_token_sprawl(self, context: dict | None = None) -> list[PreventionAlert]:
        """
        检查Token Sprawl

        检查指标:
        1. 对话历史长度
        2. Token增长速率
        3. 重复内容比例
        """
        alerts = []

        # 示例检查逻辑 (实际应传入真实上下文)
        if context:
            message_count = context.get("message_count", 0)
            total_tokens = context.get("total_tokens", 0)

            # 检查1: 消息数量过多
            if message_count > 50:
                alerts.append(
                    PreventionAlert(
                        failure_mode=FailureMode.TOKEN_SPRAWL,
                        severity="high",
                        description=f"对话历史过长: {message_count}条消息",
                        suggested_actions=[
                            PreventionAction.COMPRESS_CONTEXT,
                            PreventionAction.REDUCE_COMPLEXITY,
                        ],
                        detected_at=datetime.now().timestamp(),
                        context={"message_count": message_count},
                    )
                )

            # 检查2: Token数量过多
            if total_tokens > 10000:
                alerts.append(
                    PreventionAlert(
                        failure_mode=FailureMode.TOKEN_SPRAWL,
                        severity="critical",
                        description=f"上下文Token数过多: {total_tokens}",
                        suggested_actions=[PreventionAction.COMPRESS_CONTEXT],
                        detected_at=datetime.now().timestamp(),
                        context={"total_tokens": total_tokens},
                    )
                )

        return alerts

    async def check_coordination_drift(self) -> list[PreventionAlert]:
        """
        检查Coordination Drift

        检查指标:
        1. 智能体目标一致性
        2. 冲突检测
        3. 通信频率异常
        """
        alerts = []

        # 1. 检查目标一致性
        if len(self.agent_goals) > 1:
            # 提取所有目标
            goals = list(self.agent_goals.values())

            # 检查目标冲突
            conflicts = self._detect_goal_conflicts(goals)

            for conflict in conflicts:
                alerts.append(
                    PreventionAlert(
                        failure_mode=FailureMode.COORDINATION_DRIFT,
                        severity=conflict.get("severity", "medium"),
                        description=conflict["description"],
                        suggested_actions=[
                            PreventionAction.SYNC_GOALS,
                            PreventionAction.RESOLVE_CONFLICT,
                        ],
                        detected_at=datetime.now().timestamp(),
                        context=conflict,
                    )
                )

        # 2. 检查活跃冲突
        for conflict in self.active_conflicts:
            if conflict.severity in ["high", "critical"]:
                alerts.append(
                    PreventionAlert(
                        failure_mode=FailureMode.COORDINATION_DRIFT,
                        severity=conflict.severity,
                        description=f"未解决冲突: {conflict.description}",
                        suggested_actions=[PreventionAction.RESOLVE_CONFLICT],
                        detected_at=datetime.now().timestamp(),
                        context={"conflict_id": conflict.conflict_id},
                    )
                )

        return alerts

    def _detect_goal_conflicts(self, goals: list[AgentGoal]) -> list[dict[str, Any]]:
        """检测目标冲突"""
        conflicts = []

        # 简单实现: 检查目标关键词冲突
        goal_keywords = {"快": "慢", "增加": "减少", "创建": "删除", "启用": "禁用"}

        for i, goal1 in enumerate(goals):
            for goal2 in goals[i + 1 :]:
                # 检查冲突关键词
                for positive, negative in goal_keywords.items():
                    if positive in goal1.goal and negative in goal2.goal:
                        conflicts.append(
                            {
                                "severity": "medium",
                                "description": f"目标冲突: {goal1.agent_id}想要'{positive}',但{goal2.agent_id}想要'{negative}'",
                                "agents_involved": [goal1.agent_id, goal2.agent_id],
                                "goal1": goal1.goal,
                                "goal2": goal2.goal,
                            }
                        )

        return conflicts

    async def check_context_overflow(self, context: dict | None = None) -> list[PreventionAlert]:
        """
        检查Context Overflow

        检查指标:
        1. 上下文大小接近限制
        2. 单条消息过长
        3. 嵌套层级过深
        """
        alerts = []

        if context:
            # 检查上下文大小
            context_size = context.get("context_size", 0)
            max_size = context.get("max_size", 8000)

            if context_size > max_size * 0.9:
                alerts.append(
                    PreventionAlert(
                        failure_mode=FailureMode.CONTEXT_OVERFLOW,
                        severity="critical",
                        description=f"上下文大小接近限制: {context_size}/{max_size}",
                        suggested_actions=[
                            PreventionAction.COMPRESS_CONTEXT,
                            PreventionAction.REDUCE_COMPLEXITY,
                        ],
                        detected_at=datetime.now().timestamp(),
                        context={"context_size": context_size, "max_size": max_size},
                    )
                )

        return alerts

    async def check_hallucination_risk(self) -> list[PreventionAlert]:
        """
        检查Hallucination风险

        检查指标:
        1. 置信度异常低
        2. 多智能体结果不一致
        3. 缺少数据源引用
        """
        alerts = []

        # 这个检查需要智能体执行后的结果
        # 这里提供框架,实际检查需要传入结果数据

        return alerts

    async def _handle_alert(self, alert: PreventionAlert):
        """处理警报"""
        logger.warning(f"失败模式警报: {alert.failure_mode.value} - {alert.description}")

        # 记录到历史
        self.alert_history.append(alert)

        # 更新指标
        self.metrics.alerts_by_mode[alert.failure_mode] = (
            self.metrics.alerts_by_mode.get(alert.failure_mode, 0) + 1
        )

        # 根据严重程度采取行动
        if alert.severity == "critical":
            # 关键警报: 立即采取预防行动
            await self._execute_prevention_actions(alert)

    async def _execute_prevention_actions(self, alert: PreventionAlert):
        """执行预防行动"""
        logger.info(f"执行预防行动: {alert.suggested_actions}")

        for action in alert.suggested_actions:
            try:
                if action == PreventionAction.COMPRESS_CONTEXT:
                    await self._compress_context()

                elif action == PreventionAction.SYNC_GOALS:
                    await self._sync_agent_goals()

                elif action == PreventionAction.RESOLVE_CONFLICT:
                    await self._resolve_active_conflicts()

                elif action == PreventionAction.FACT_CHECK:
                    await self._trigger_fact_check()

                elif action == PreventionAction.REQUEST_CONFIRMATION:
                    await self._request_human_confirmation(alert)

            except Exception as e:
                logger.error(f"执行预防行动失败 {action.value}: {e}")

    async def _compress_context(self):
        """压缩上下文"""
        logger.info("执行上下文压缩")
        # 实际实现应调用ContextCompressor

    async def _sync_agent_goals(self):
        """同步智能体目标"""
        logger.info("同步智能体目标")

        if len(self.agent_goals) < 2:
            return

        # 提取所有目标
        goals = list(self.agent_goals.values())

        # 创建共同目标 (简化实现)
        # 实际应该使用更复杂的协商机制
        shared_goal = "协同完成用户任务"

        # 更新所有智能体的目标
        for goal in goals:
            goal.goal = shared_goal
            goal.timestamp = datetime.now().timestamp()

        logger.info(f"已同步 {len(goals)} 个智能体的目标")

    async def _resolve_active_conflicts(self):
        """解决活跃冲突"""
        logger.info(f"解决 {len(self.active_conflicts)} 个活跃冲突")

        # 简单实现: 标记为已解决
        for conflict in self.active_conflicts:
            conflict.resolution_status = "resolved"
            self.resolved_conflicts.append(conflict)

        self.active_conflicts.clear()

    async def _trigger_fact_check(self):
        """触发事实核查"""
        logger.info("触发事实核查")
        # 实际实现应该:
        # 1. 识别需要核查的陈述
        # 2. 查询可信数据源
        # 3. 对比和验证
        # 4. 标记不可信的内容

    async def _request_human_confirmation(self, alert: PreventionAlert):
        """请求人类确认"""
        logger.info(f"请求人类确认: {alert.description}")
        # 实际实现应该触发HITL协议

    def register_agent_goal(self, agent_id: str, goal: str, priority: int = 5) -> Any:
        """
        注册智能体目标

        Args:
            agent_id: 智能体ID
            goal: 目标描述
            priority: 优先级 (1-10)
        """
        agent_goal = AgentGoal(
            agent_id=agent_id, goal=goal, priority=priority, timestamp=datetime.now().timestamp()
        )

        self.agent_goals[agent_id] = agent_goal

        logger.info(f"注册智能体目标: {agent_id} -> {goal}")

    def update_agent_goal(self, agent_id: str, new_goal: str) -> None:
        """更新智能体目标"""
        if agent_id in self.agent_goals:
            self.agent_goals[agent_id].goal = new_goal
            self.agent_goals[agent_id].timestamp = datetime.now().timestamp()
            logger.info(f"更新智能体目标: {agent_id} -> {new_goal}")

    def complete_agent_goal(self, agent_id: str) -> Any:
        """标记智能体目标为完成"""
        if agent_id in self.agent_goals:
            self.agent_goals[agent_id].status = "completed"
            logger.info(f"完成智能体目标: {agent_id}")

    def get_agent_goals(self) -> dict[str, AgentGoal]:
        """获取所有智能体目标"""
        return self.agent_goals.copy()

    def report_conflict(
        self, agents_involved: list[str], description: str, severity: str = "medium"
    ):
        """
        报告冲突

        Args:
            agents_involved: 涉及的智能体列表
            description: 冲突描述
            severity: 严重程度
        """
        conflict = ConflictInfo(
            conflict_id=f"conflict_{datetime.now().timestamp()}",
            conflict_type="goal_conflict",
            agents_involved=agents_involved,
            description=description,
            severity=severity,
            detected_at=datetime.now().timestamp(),
        )

        self.active_conflicts.append(conflict)

        logger.warning(f"报告冲突: {description}")

    def get_metrics(self) -> PreventionMetrics:
        """获取预防指标"""
        return self.metrics

    def get_recent_alerts(self, limit: int = 10) -> list[PreventionAlert]:
        """获取最近的警报"""
        return list(self.alert_history)[-limit:]


# ============================================================================
# 便捷函数
# ============================================================================

_prevention_system_instance: FailurePreventionSystem | None = None


def get_failure_prevention_system() -> FailurePreventionSystem:
    """获取失败模式防护系统单例"""
    global _prevention_system_instance
    if _prevention_system_instance is None:
        _prevention_system_instance = FailurePreventionSystem()
    return _prevention_system_instance


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "AgentGoal",
    "ConflictInfo",
    "FailureMode",
    "FailurePreventionSystem",
    "PreventionAction",
    "PreventionAlert",
    "PreventionMetrics",
    "get_failure_prevention_system",
]
