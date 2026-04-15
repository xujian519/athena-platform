#!/usr/bin/env python3
"""
自愈编排器 (Self-healing Orchestrator)
协调自愈流程,整合故障预测和自动修复

作者: 小诺·双鱼公主
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HealingStatus(str, Enum):
    """自愈状态"""

    DETECTING = "detecting"  # 检测中
    PREDICTING = "predicting"  # 预测中
    HEALING = "healing"  # 修复中
    VERIFIED = "verified"  # 已验证
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class SeverityLevel(str, Enum):
    """严重程度"""

    CRITICAL = "critical"  # 严重,需要立即处理
    HIGH = "high"  # 高,需要尽快处理
    MEDIUM = "medium"  # 中等,需要关注
    LOW = "low"  # 低,可以延后处理


@dataclass
class HealingScenario:
    """自愈场景定义"""

    name: str
    description: str
    detection_rules: dict[str, Any]
    healing_strategy: str
    priority: int = 1  # 1-5, 1最高
    enabled: bool = True


@dataclass
class HealingAction:
    """自愈动作"""

    action_id: str
    scenario_name: str
    action_type: str  # predict, repair, verify
    params: dict[str, Any] = field(default_factory=dict)
    status: HealingStatus = HealingStatus.DETECTING
    result: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class SelfHealingOrchestrator:
    """
    自愈编排器

    负责协调整个自愈流程:
    1. 接收系统监控数据
    2. 触发故障预测
    3. 执行自动修复
    4. 验证修复结果
    """

    # 内置自愈场景
    BUILT_IN_SCENARIOS = [
        HealingScenario(
            name="high_memory_usage",
            description="内存使用率过高",
            detection_rules={
                "memory_usage_percent": {"gt": 85},
                "trend": "increasing",
                "duration_seconds": 60,
            },
            healing_strategy="memory_cleanup",
            priority=2,
        ),
        HealingScenario(
            name="high_cpu_usage",
            description="CPU使用率过高",
            detection_rules={"cpu_usage_percent": {"gt": 90}, "duration_seconds": 30},
            healing_strategy="process_optimization",
            priority=2,
        ),
        HealingScenario(
            name="api_error_rate",
            description="API错误率过高",
            detection_rules={"error_rate_percent": {"gt": 5}, "duration_seconds": 60},
            healing_strategy="circuit_breaker_reset",
            priority=1,
        ),
        HealingScenario(
            name="disk_space_low",
            description="磁盘空间不足",
            detection_rules={"disk_usage_percent": {"gt": 90}, "available_space_gb": {"lt": 10}},
            healing_strategy="disk_cleanup",
            priority=3,
        ),
        HealingScenario(
            name="connection_pool_exhausted",
            description="连接池耗尽",
            detection_rules={"active_connections": {"gte": 90}, "pool_size": 100},
            healing_strategy="connection_reset",
            priority=1,
        ),
    ]

    def __init__(self):
        self.name = "自愈编排器"
        self.version = "1.0.0"
        self.scenarios: dict[str, HealingScenario] = {}
        self.active_actions: dict[str, HealingAction] = {}
        self.healing_history: list[HealingAction] = []
        self.metrics = {
            "total_detections": 0,
            "successful_healings": 0,
            "failed_healings": 0,
            "avg_healing_time_seconds": 0,
        }

        # 注册内置场景
        self._register_builtin_scenarios()

        logger.info(f"✅ {self.name} v{self.version} 初始化完成")

    def _register_builtin_scenarios(self) -> Any:
        """注册内置自愈场景"""
        for scenario in self.BUILT_IN_SCENARIOS:
            self.scenarios[scenario.name] = scenario
        logger.info(f"📋 已注册 {len(self.scenarios)} 个自愈场景")

    async def detect_anomalies(self, metrics_data: dict[str, Any]) -> list[HealingAction]:
        """
        检测异常

        Args:
            metrics_data: 系统监控指标数据

        Returns:
            检测到的异常动作列表
        """
        detected_actions = []

        for scenario_name, scenario in self.scenarios.items():
            if not scenario.enabled:
                continue

            # 检查是否匹配检测规则
            if self._match_detection_rules(metrics_data, scenario.detection_rules):
                action = HealingAction(
                    action_id=f"heal_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{scenario_name}",
                    scenario_name=scenario_name,
                    action_type="detect",
                    params={
                        "scenario": scenario_name,
                        "metrics": metrics_data,
                        "strategy": scenario.healing_strategy,
                    },
                    started_at=datetime.now(),
                )
                detected_actions.append(action)
                self.active_actions[action.action_id] = action
                self.metrics["total_detections"] += 1

                logger.warning(f"⚠️ 检测到异常: {scenario.name} (动作ID: {action.action_id})")

        return detected_actions

    def _match_detection_rules(self, metrics_data: dict[str, Any], rules: dict[str, Any]) -> bool:
        """
        匹配检测规则

        Args:
            metrics_data: 监控指标数据
            rules: 检测规则

        Returns:
            是否匹配规则
        """
        for key, rule in rules.items():
            if key not in metrics_data:
                continue

            value = metrics_data[key]

            # 处理不同类型的规则
            if isinstance(rule, dict):
                if "gt" in rule and value <= rule["gt"]:
                    return False
                if "gte" in rule and value < rule["gte"]:
                    return False
                if "lt" in rule and value >= rule["lt"]:
                    return False
                if "lte" in rule and value > rule["lte"]:
                    return False

        return True

    async def predict_failure(
        self, action_id: str, historical_metrics: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        预测故障

        Args:
            action_id: 动作ID
            historical_metrics: 历史指标数据

        Returns:
            预测结果
        """
        if action_id not in self.active_actions:
            raise ValueError(f"动作不存在: {action_id}")

        action = self.active_actions[action_id]
        action.status = HealingStatus.PREDICTING

        # 简化版预测逻辑
        # 生产环境应该使用实际的ML模型
        failure_probability = 0.0
        predicted_time_to_failure = None

        # 基于趋势分析
        if len(historical_metrics) >= 3:
            recent = historical_metrics[-3:]
            trends = self._analyze_trends(recent)

            if trends.get("degrading", False):
                failure_probability = 0.75
                predicted_time_to_failure = "5-10分钟"
            elif trends.get("stable", False):
                failure_probability = 0.15
            else:
                failure_probability = 0.40

        result = {
            "failure_probability": failure_probability,
            "predicted_time_to_failure": predicted_time_to_failure,
            "confidence": "medium",
            "recommendation": "trigger_healing" if failure_probability > 0.5 else "monitor",
        }

        action.result = {"prediction": result}
        logger.info(f"🔮 预测完成: {action_id} -> {result}")

        return result

    def _analyze_trends(self, metrics: list[dict[str, Any]]) -> dict[str, bool]:
        """分析指标趋势"""
        trends = {"degrading": False, "stable": False, "improving": False}

        if len(metrics) < 2:
            return trends

        # 简化的趋势分析
        # 实际应该使用更复杂的统计方法
        first = metrics[0]
        last = metrics[-1]

        for key in first:
            if key in last:
                if isinstance(first[key], (int, float)) and isinstance(last[key], (int, float)):
                    if last[key] > first[key] * 1.2:  # 增长超过20%
                        trends["degrading"] = True
                    elif abs(last[key] - first[key]) / first[key] < 0.05:  # 变化小于5%
                        trends["stable"] = True

        return trends

    async def execute_healing(
        self, action_id: str, strategy: str | None = None
    ) -> dict[str, Any]:
        """
        执行自愈修复

        Args:
            action_id: 动作ID
            strategy: 修复策略(可选,默认使用场景定义的策略)

        Returns:
            修复结果
        """
        if action_id not in self.active_actions:
            raise ValueError(f"动作不存在: {action_id}")

        action = self.active_actions[action_id]
        action.status = HealingStatus.HEALING

        # 获取修复策略
        if strategy is None:
            scenario = self.scenarios.get(action.scenario_name)
            if scenario:
                strategy = scenario.healing_strategy

        # 执行修复(简化版)
        healing_result = await self._execute_healing_strategy(action, strategy)

        action.result = healing_result
        action.completed_at = datetime.now()

        if healing_result.get("success", False):
            action.status = HealingStatus.VERIFIED
            self.metrics["successful_healings"] += 1
            logger.info(f"✅ 自愈成功: {action_id}")
        else:
            action.status = HealingStatus.FAILED
            self.metrics["failed_healings"] += 1
            logger.error(f"❌ 自愈失败: {action_id} -> {healing_result.get('error')}")

        # 添加到历史记录
        self.healing_history.append(action)

        # 计算平均修复时间
        if action.started_at and action.completed_at:
            duration = (action.completed_at - action.started_at).total_seconds()
            total = self.metrics["successful_healings"] + self.metrics["failed_healings"]
            self.metrics["avg_healing_time_seconds"] = (
                self.metrics["avg_healing_time_seconds"] * (total - 1) + duration
            ) / total

        return healing_result

    async def _execute_healing_strategy(
        self, action: HealingAction, strategy: str
    ) -> dict[str, Any]:
        """
        执行具体的修复策略

        Args:
            action: 自愈动作
            strategy: 修复策略名称

        Returns:
            修复结果
        """
        # 简化版修复策略实现
        # 生产环境应该实现实际的修复逻辑
        strategies = {
            "memory_cleanup": self._heal_memory_cleanup,
            "process_optimization": self._heal_process_optimization,
            "circuit_breaker_reset": self._heal_circuit_breaker_reset,
            "disk_cleanup": self._heal_disk_cleanup,
            "connection_reset": self._heal_connection_reset,
        }

        heal_func = strategies.get(strategy)
        if heal_func:
            return await heal_func(action)

        return {"success": False, "error": f"未知修复策略: {strategy}"}

    async def _heal_memory_cleanup(self, action: HealingAction) -> dict[str, Any]:
        """内存清理修复策略"""
        # 模拟内存清理
        await asyncio.sleep(0.5)
        return {"success": True, "message": "内存清理完成", "freed_memory_mb": 256}

    async def _heal_process_optimization(self, action: HealingAction) -> dict[str, Any]:
        """进程优化修复策略"""
        await asyncio.sleep(0.3)
        return {"success": True, "message": "进程优化完成", "cpu_reduction_percent": 15}

    async def _heal_circuit_breaker_reset(self, action: HealingAction) -> dict[str, Any]:
        """断路器重置修复策略"""
        await asyncio.sleep(0.2)
        return {
            "success": True,
            "message": "断路器已重置",
            "services_reset": ["api-service", "database-service"],
        }

    async def _heal_disk_cleanup(self, action: HealingAction) -> dict[str, Any]:
        """磁盘清理修复策略"""
        await asyncio.sleep(1.0)
        return {"success": True, "message": "磁盘清理完成", "freed_space_gb": 5.2}

    async def _heal_connection_reset(self, action: HealingAction) -> dict[str, Any]:
        """连接重置修复策略"""
        await asyncio.sleep(0.4)
        return {"success": True, "message": "连接池已重置", "connections_reset": 15}

    def get_status(self) -> dict[str, Any]:
        """获取自愈系统状态"""
        return {
            "name": self.name,
            "version": self.version,
            "scenarios": {
                "total": len(self.scenarios),
                "enabled": sum(1 for s in self.scenarios.values() if s.enabled),
                "disabled": sum(1 for s in self.scenarios.values() if not s.enabled),
            },
            "active_actions": len(self.active_actions),
            "metrics": self.metrics,
            "recent_history": [
                {
                    "action_id": a.action_id,
                    "scenario": a.scenario_name,
                    "status": a.status.value,
                    "started_at": a.started_at.isoformat() if a.started_at else None,
                }
                for a in self.healing_history[-10:]  # 最近10条记录
            ],
        }

    def register_scenario(self, scenario: HealingScenario) -> Any:
        """注册自定义自愈场景"""
        self.scenarios[scenario.name] = scenario
        logger.info(f"📋 注册自定义场景: {scenario.name}")


# 全局单例
_orchestrator_instance: SelfHealingOrchestrator | None = None


async def get_self_healing_orchestrator() -> SelfHealingOrchestrator:
    """获取自愈编排器实例"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = SelfHealingOrchestrator()
    return _orchestrator_instance
