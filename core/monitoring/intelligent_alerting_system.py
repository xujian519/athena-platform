#!/usr/bin/env python3
"""
智能告警系统
Intelligent Alerting System

提供多级告警、根因分析、自动恢复等高级告警功能
作者: Athena AI系统
创建时间: 2025-12-11
版本: 2.0.0
"""
import networkx as nx
import numpy as np

import asyncio
import logging

# 添加项目路径
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional



sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.monitoring.optimized_monitoring_module import (
    Alert,
    AlertLevel,
    AlertStatus,
)

logger = logging.getLogger(__name__)


class RecoveryActionStatus(Enum):
    """恢复动作状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RecoveryAction:
    """恢复动作"""

    id: str
    name: str
    description: str
    action_type: str  # script, api_call, service_restart, config_change
    parameters: dict[str, Any]
    priority: int = 1  # 1-10, 10最高
    timeout: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    max_retries: int = 3
    status: RecoveryActionStatus = RecoveryActionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0
    result: dict[str, Any] | None = None


@dataclass
class RootCause:
    """根因分析结果"""

    id: str
    alert_id: str
    primary_cause: str
    confidence: float  # 0-1
    contributing_factors: list[str]
    affected_services: list[str]
    evidence: dict[str, Any]
    analysis_method: str
    timestamp: datetime = field(default_factory=datetime.now)


class RootCauseAnalyzer:
    """根因分析器"""

    def __init__(self, metrics_collector, config: dict[str, Any] | None = None):
        self.metrics_collector = metrics_collector
        self.config = config or {}
        self.dependency_graph = nx.DiGraph()
        self.service_metrics = defaultdict(list)

        # 分析窗口
        self.analysis_window = self.config.get("analysis_window", timedelta(minutes=30))
        self.correlation_threshold = self.config.get("correlation_threshold", 0.7)

        # 预定义的因果关系
        self.causal_patterns = {
            "high_cpu": ["memory_leak", "process_spike", "inefficient_code"],
            "high_memory": ["memory_leak", "cache_bloat", "connection_leak"],
            "disk_full": ["log_bloat", "cache_bloat", "temp_files"],
            "network_error": ["dns_failure", "firewall_block", "service_down"],
            "database_error": ["connection_pool_exhausted", "deadlock", "slow_query"],
        }

    def build_dependency_graph(
        self, services: list[str], dependencies: list[tuple[str, str]) -> Any:
        """构建服务依赖图"""
        self.dependency_graph.clear()

        # 添加服务节点
        for service in services:
            self.dependency_graph.add_node(service)

        # 添加依赖边
        for dependency in dependencies:
            if len(dependency) == 2:
                upstream, downstream = dependency
                self.dependency_graph.add_edge(upstream, downstream)

    def analyze_root_cause(self, alert: Alert, related_alerts: list[Alert | None = None) -> RootCause:
        """分析告警根因"""
        try:
            # 收集相关指标数据
            metric_data = self._collect_metric_data(alert, self.analysis_window)

            # 分析时间相关性
            time_correlations = self._analyze_time_correlations(metric_data)

            # 分析服务依赖影响
            dependency_impact = self._analyze_dependency_impact(alert)

            # 应用因果模式
            causal_factors = self._apply_causal_patterns(alert, metric_data)

            # 确定主要根因
            primary_cause, confidence = self._determine_primary_cause(
                time_correlations, dependency_impact, causal_factors
            )

            # 生成分析结果
            root_cause = RootCause(
                id=f"root_cause_{alert.id}_{int(time.time())}",
                alert_id=alert.id,
                primary_cause=primary_cause,
                confidence=confidence,
                contributing_factors=list(
                    set(time_correlations.keys())
                    | set(dependency_impact.keys())
                    | set(causal_factors)
                ),
                affected_services=self._get_affected_services(alert),
                evidence={
                    "metric_data": metric_data,
                    "time_correlations": time_correlations,
                    "dependency_impact": dependency_impact,
                    "causal_patterns": causal_factors,
                },
                analysis_method="multi_factor_correlation",
            )

            logger.info(f"根因分析完成: {primary_cause} (置信度: {confidence:.2f})")
            return root_cause

        except Exception as e:
            logger.error(f"根因分析失败: {e}")
            return RootCause(
                id=f"root_cause_{alert.id}_{int(time.time())}",
                alert_id=alert.id,
                primary_cause="analysis_failed",
                confidence=0.0,
                contributing_factors=[],
                affected_services=[],
                evidence={"error": str(e)},
                analysis_method="fallback",
            )

    def _collect_metric_data(self, alert: Alert, window: timedelta) -> dict[str, list]:
        """收集指标数据"""
        metric_data = {}

        # 收集告警相关的指标历史
        end_time = datetime.now()
        start_time = end_time - window

        for metric in alert.metric_values:
            history = self.metrics_collector.get_metrics_history(
                metric.name, metric.labels, start_time, end_time
            )
            metric_data[metric.name] = history

        # 收集系统级指标
        system_metrics = [
            "system_cpu_usage",
            "system_memory_usage",
            "system_disk_usage",
            "system_network_bytes_sent",
            "system_network_bytes_recv",
        ]

        for metric_name in system_metrics:
            history = self.metrics_collector.get_metrics_history(
                metric_name, None, start_time, end_time
            )
            if history:
                metric_data[metric_name] = history

        return metric_data

    def _analyze_time_correlations(self, metric_data: dict[str, list]) -> dict[str, float]:
        """分析时间相关性"""
        correlations = {}

        # 找出所有指标的值序列
        metric_series = {}
        for name, history in metric_data.items():
            if len(history) > 1:
                # 获取时间序列值
                timestamps = [m.timestamp.timestamp() for m in history]
                values = [m.value for m in history]

                # 标准化时间
                if timestamps:
                    min_time = min(timestamps)
                    normalized_times = [(t - min_time) for t in timestamps]
                    metric_series[name] = list(zip(normalized_times, values, strict=False))

        # 计算相关性
        metric_names = list(metric_series.keys())
        for i, name1 in enumerate(metric_names):
            for name2 in metric_names[i + 1 :]:
                correlation = self._calculate_correlation(
                    metric_series[name1], metric_series[name2]
                )
                if abs(correlation) > self.correlation_threshold:
                    correlations[f"{name1}_vs_{name2}"] = correlation

        return correlations

    def _calculate_correlation(self, series1: list[tuple], series2: list[tuple]) -> float:
        """计算两个时间序列的相关性"""
        try:
            # 对齐时间点
            times1 = [s[0] for s in series1]
            times2 = [s[0] for s in series2]

            # 找到共同的时间范围
            start_time = max(min(times1), min(times2))
            end_time = min(max(times1), max(times2))

            # 提取共同时间范围内的值
            values1 = [s[1] for s in series1 if start_time <= s[0] <= end_time]
            values2 = [s[1] for s in series2 if start_time <= s[0] <= end_time]

            if len(values1) < 3 or len(values2) < 3:
                return 0.0

            # 计算相关系数
            correlation = np.corrcoef(values1, values2)[0, 1]
            return correlation if not np.isnan(correlation) else 0.0

        except Exception:
            return 0.0

    def _analyze_dependency_impact(self, alert: Alert) -> dict[str, float]:
        """分析服务依赖影响"""
        impact_scores = {}

        if not alert.labels or "service" not in alert.labels:
            return impact_scores

        service = alert.labels["service"]

        # 找出上游服务
        upstream_services = list(self.dependency_graph.predecessors(service))

        # 检查上游服务的指标异常
        for upstream in upstream_services:
            # 这里简化处理,实际应该查询上游服务的具体指标
            # 假设上游服务有异常则可能影响当前服务
            impact_scores[f"upstream_{upstream}"] = 0.8

        # 找出下游服务
        downstream_services = list(self.dependency_graph.successors(service))

        # 检查当前服务对下游的影响
        for downstream in downstream_services:
            impact_scores[f"downstream_{downstream}"] = 0.6

        return impact_scores

    def _apply_causal_patterns(self, alert: Alert, metric_data: dict[str, list]) -> list[str]:
        """应用因果模式识别"""
        factors = []

        # 根据告警名称和指标应用模式
        alert_name = alert.name.lower()
        alert_metric = alert.rule_id.lower() if alert.rule_id else ""

        for pattern, possible_causes in self.causal_patterns.items():
            if pattern in alert_name or pattern in alert_metric:
                factors.extend(possible_causes)

        # 根据指标数据识别异常模式
        for metric_name, history in metric_data.items():
            if not history:
                continue

            values = [h.value for h in history]

            # 检测突然飙升
            if len(values) >= 2:
                recent_change = (values[-1] - values[-2]) / values[-2] if values[-2] != 0 else 0
                if recent_change > 0.5:  # 50%以上增长
                    factors.append(f"sudden_spike_{metric_name}")

                # 检测持续增长
                if len(values) >= 5:
                    trend = np.polyfit(range(len(values)), values, 1)[0]
                    if trend > 0.1:
                        factors.append(f"continuous_growth_{metric_name}")

        return list(set(factors))

    def _determine_primary_cause(
        self, correlations: dict, dependency_impact: dict, causal_factors: list
    ) -> tuple[str, float]:
        """确定主要根因"""
        cause_scores = defaultdict(float)

        # 时间相关性权重
        for _correlation_key, correlation_value in correlations.items():
            if correlation_value > 0:
                cause_scores["time_correlation"] += abs(correlation_value) * 0.3

        # 依赖影响权重
        for _impact_key, impact_value in dependency_impact.items():
            cause_scores["dependency_impact"] += impact_value * 0.4

        # 因果模式权重
        for factor in causal_factors:
            cause_scores[factor] += 0.3

        if not cause_scores:
            return "unknown", 0.0

        # 找出最高分的根因
        primary_cause = max(cause_scores.items(), key=lambda x: x[1])

        # 计算置信度
        confidence = min(primary_cause[1] / 1.0, 1.0)  # 归一化到0-1

        return primary_cause[0], confidence

    def _get_affected_services(self, alert: Alert) -> list[str]:
        """获取受影响的服务"""
        services = []

        # 从告警标签中提取服务
        if alert.labels:
            for key, value in alert.labels.items():
                if key in ["service", "module", "component"]:
                    services.append(value)

        # 基于依赖关系推断受影响的服务
        for service in services.copy():
            downstream = list(self.dependency_graph.successors(service))
            services.extend(downstream)

        return list(set(services))


class AutoRecoveryEngine:
    """自动恢复引擎"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.recovery_actions: dict[str, RecoveryAction] = {}
        self.action_queue = asyncio.Queue()
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 预定义恢复动作
        self.predefined_actions = self._load_predefined_actions()

        # 配置参数
        self.max_concurrent_actions = self.config.get("max_concurrent_actions", 3)
        self.default_timeout = self.config.get("default_timeout", timedelta(minutes=5))

    def _load_predefined_actions(self) -> dict[str, dict]:
        """加载预定义恢复动作"""
        return {
            "restart_service": {
                "action_type": "service_restart",
                "description": "重启服务",
                "script_template": "systemctl restart {service_name}",
                "timeout": timedelta(minutes=2),
            },
            "clear_cache": {
                "action_type": "script",
                "description": "清理缓存",
                "script_template": "rm -rf {cache_path}/*",
                "timeout": timedelta(minutes=1),
            },
            "scale_up": {
                "action_type": "api_call",
                "description": "扩容服务",
                "endpoint_template": "http://orchestrator/api/v1/services/{service_name}/scale",
                "parameters": {"replicas": "+1"},
                "timeout": timedelta(minutes=5),
            },
            "restart_container": {
                "action_type": "api_call",
                "description": "重启容器",
                "endpoint_template": "http://docker/api/v1/containers/{container_id}/restart",
                "timeout": timedelta(minutes=3),
            },
            "update_config": {
                "action_type": "config_change",
                "description": "更新配置",
                "config_path_template": "/etc/{service_name}/config.json",
                "timeout": timedelta(minutes=2),
            },
        }

    async def start(self):
        """启动自动恢复引擎"""
        self.running = True

        # 启动恢复动作执行器
        for _i in range(self.max_concurrent_actions):
            asyncio.create_task(self._action_executor())

        logger.info("自动恢复引擎启动成功")

    async def stop(self):
        """停止自动恢复引擎"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("自动恢复引擎停止成功")

    def create_recovery_action(
        self, alert: Alert, root_cause: RootCause = None
    ) -> list[RecoveryAction]:
        """创建恢复动作"""
        actions = []

        # 根据告警级别和根因创建恢复动作
        if alert.level == AlertLevel.CRITICAL:
            actions.extend(self._create_critical_actions(alert, root_cause))
        elif alert.level == AlertLevel.ERROR:
            actions.extend(self._create_error_actions(alert, root_cause))
        elif alert.level == AlertLevel.WARNING:
            actions.extend(self._create_warning_actions(alert, root_cause))

        # 添加到队列
        for action in actions:
            self.recovery_actions[action.id] = action
            asyncio.create_task(self.action_queue.put(action))
            logger.info(f"创建恢复动作: {action.name}")

        return actions

    def _create_critical_actions(
        self, alert: Alert, root_cause: RootCause = None
    ) -> list[RecoveryAction]:
        """创建严重告警的恢复动作"""
        actions = []

        # 服务重启
        if "service" in alert.labels:
            actions.append(
                RecoveryAction(
                    id=f"restart_{alert.id}_{int(time.time())}",
                    name="重启服务",
                    description=f"重启服务 {alert.labels['service']}",
                    action_type="service_restart",
                    parameters={"service_name": alert.labels["service"]},
                    priority=10,
                    timeout=timedelta(minutes=3),
                )
            )

        # 扩容
        if "cpu" in alert.name.lower() or "memory" in alert.name.lower():
            if "service" in alert.labels:
                actions.append(
                    RecoveryAction(
                        id=f"scale_up_{alert.id}_{int(time.time())}",
                        name="扩容服务",
                        description=f"扩容服务 {alert.labels['service']}",
                        action_type="api_call",
                        parameters={"service_name": alert.labels["service"], "replicas": 2},
                        priority=8,
                        timeout=timedelta(minutes=5),
                    )
                )

        return actions

    def _create_error_actions(
        self, alert: Alert, root_cause: RootCause = None
    ) -> list[RecoveryAction]:
        """创建错误告警的恢复动作"""
        actions = []

        # 基于根因的动作
        if root_cause:
            if "memory_leak" in root_cause.contributing_factors:
                actions.append(
                    RecoveryAction(
                        id=f"restart_memory_{alert.id}_{int(time.time())}",
                        name="重启服务解决内存泄漏",
                        description="重启服务以释放内存",
                        action_type="service_restart",
                        parameters={"service_name": alert.labels.get("service", "unknown")},
                        priority=7,
                        timeout=timedelta(minutes=3),
                    )
                )

            if "cache_bloat" in root_cause.contributing_factors:
                actions.append(
                    RecoveryAction(
                        id=f"clear_cache_{alert.id}_{int(time.time())}",
                        name="清理缓存",
                        description="清理膨胀的缓存",
                        action_type="script",
                        parameters={"cache_path": "/tmp/cache"},
                        priority=6,
                        timeout=timedelta(minutes=1),
                    )
                )

        # 通用动作
        if "service" in alert.labels:
            actions.append(
                RecoveryAction(
                    id=f"graceful_restart_{alert.id}_{int(time.time())}",
                    name="优雅重启",
                    description="优雅重启服务",
                    action_type="service_restart",
                    parameters={"service_name": alert.labels["service"], "graceful": True},
                    priority=5,
                    timeout=timedelta(minutes=5),
                )
            )

        return actions

    def _create_warning_actions(
        self, alert: Alert, root_cause: RootCause = None
    ) -> list[RecoveryAction]:
        """创建警告告警的恢复动作"""
        actions = []

        # 预防性动作
        if "disk" in alert.name.lower():
            actions.append(
                RecoveryAction(
                    id=f"cleanup_disk_{alert.id}_{int(time.time())}",
                    name="磁盘清理",
                    description="清理临时文件和日志",
                    action_type="script",
                    parameters={"cleanup_paths": ["/tmp", "/var/log"], "keep_days": 7},
                    priority=4,
                    timeout=timedelta(minutes=2),
                )
            )

        return actions

    async def _action_executor(self):
        """恢复动作执行器"""
        while self.running:
            try:
                # 获取恢复动作
                action = await asyncio.wait_for(self.action_queue.get(), timeout=1.0)

                # 执行动作
                await self._execute_action(action)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"恢复动作执行器异常: {e}")

    async def _execute_action(self, action: RecoveryAction):
        """执行恢复动作"""
        try:
            # 更新状态
            action.status = RecoveryActionStatus.IN_PROGRESS
            action.started_at = datetime.now()

            logger.info(f"执行恢复动作: {action.name}")

            # 根据动作类型执行
            if action.action_type == "service_restart":
                result = await self._execute_service_restart(action)
            elif action.action_type == "script":
                result = await self._execute_script(action)
            elif action.action_type == "api_call":
                result = await self._execute_api_call(action)
            elif action.action_type == "config_change":
                result = await self._execute_config_change(action)
            else:
                result = {"success": False, "error": f"未知动作类型: {action.action_type}"}

            # 更新结果
            action.result = result
            action.completed_at = datetime.now()

            if result.get("success", False):
                action.status = RecoveryActionStatus.COMPLETED
                logger.info(f"恢复动作成功: {action.name}")
            else:
                action.status = RecoveryActionStatus.FAILED
                logger.error(f"恢复动作失败: {action.name} - {result.get('error', '未知错误')}")

                # 重试逻辑
                if action.retry_count < action.max_retries:
                    action.retry_count += 1
                    action.status = RecoveryActionStatus.PENDING
                    await asyncio.sleep(5)  # 等待后重试
                    await self.action_queue.put(action)
                    logger.info(
                        f"恢复动作重试 ({action.retry_count}/{action.max_retries}): {action.name}"
                    )

        except Exception as e:
            action.status = RecoveryActionStatus.FAILED
            action.result = {"success": False, "error": str(e)}
            logger.error(f"恢复动作执行异常: {action.name} - {e}")

    async def _execute_service_restart(self, action: RecoveryAction) -> dict[str, Any]:
        """执行服务重启"""
        try:
            service_name = action.parameters.get("service_name")
            graceful = action.parameters.get("graceful", False)

            if graceful:
                # 优雅重启
                pass
            else:
                # 强制重启
                pass

            # 在实际环境中,这里应该执行真实的系统命令
            # 模拟执行
            await asyncio.sleep(1)

            return {"success": True, "message": f"服务 {service_name} 重启成功"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_script(self, action: RecoveryAction) -> dict[str, Any]:
        """执行脚本"""
        try:
            # 构建脚本命令
            action.parameters.get("script", "")

            # 在实际环境中,这里应该执行真实的脚本
            # 模拟执行
            await asyncio.sleep(0.5)

            return {"success": True, "message": "脚本执行成功"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_api_call(self, action: RecoveryAction) -> dict[str, Any]:
        """执行API调用"""
        try:
            action.parameters.get("endpoint", "")
            action.parameters.get("method", "POST")

            # 在实际环境中,这里应该发送真实的HTTP请求
            # 模拟API调用
            await asyncio.sleep(2)

            return {"success": True, "message": "API调用成功"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_config_change(self, action: RecoveryAction) -> dict[str, Any]:
        """执行配置变更"""
        try:
            action.parameters.get("config_path", "")
            action.parameters.get("config_data", {})

            # 在实际环境中,这里应该修改配置文件
            # 模拟配置变更
            await asyncio.sleep(1)

            return {"success": True, "message": "配置变更成功"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_action_status(self, action_id: str) -> RecoveryAction | None:
        """获取恢复动作状态"""
        return self.recovery_actions.get(action_id)

    def list_actions(self, status: RecoveryActionStatus | None = None) -> list[RecoveryAction]:
        """列出恢复动作"""
        actions = list(self.recovery_actions.values())

        if status:
            actions = [a for a in actions if a.status == status]

        return sorted(actions, key=lambda a: a.created_at, reverse=True)

    def cancel_action(self, action_id: str) -> bool:
        """取消恢复动作"""
        action = self.recovery_actions.get(action_id)
        if action and action.status in [
            RecoveryActionStatus.PENDING,
            RecoveryActionStatus.IN_PROGRESS,
        ]:
            action.status = RecoveryActionStatus.CANCELLED
            logger.info(f"取消恢复动作: {action.name}")
            return True
        return False


# 便捷函数
def create_root_cause_analyzer(
    Optional[metrics_collector, config: dict[str, Any] | None = None
) -> RootCauseAnalyzer:
    """创建根因分析器"""
    return RootCauseAnalyzer(metrics_collector, config)


def create_auto_recovery_engine(config: dict[str, Any] | None = None) -> AutoRecoveryEngine:
    """创建自动恢复引擎"""
    return AutoRecoveryEngine(config)


if __name__ == "__main__":
    # 测试代码
    async def test_intelligent_alerting():
        from core.monitoring.optimized_monitoring_module import (
            Alert,
            create_monitoring_module,
        )

        # 创建监控模块
        monitoring = create_monitoring_module("test_intelligent")
        await monitoring.initialize()
        await monitoring.start()

        # 创建根因分析器
        root_cause_analyzer = create_root_cause_analyzer(monitoring.metrics_collector)

        # 创建自动恢复引擎
        recovery_engine = create_auto_recovery_engine()
        await recovery_engine.start()

        # 模拟告警
        alert = Alert(
            id="test_alert_1",
            rule_id="cpu_high",
            name="CPU使用率过高",
            description="CPU使用率超过90%",
            level=AlertLevel.CRITICAL,
            status=AlertStatus.ACTIVE,
            message="CPU使用率95%",
            timestamp=datetime.now(),
            labels={"service": "api_server"},
        )

        # 根因分析
        root_cause = root_cause_analyzer.analyze_root_cause(alert)
        logger.info(
            f"根因分析结果: {root_cause.primary_cause} (置信度: {root_cause.confidence:.2f})"
        )

        # 创建恢复动作
        actions = recovery_engine.create_recovery_action(alert, root_cause)
        logger.info(f"创建 {len(actions)} 个恢复动作")

        # 等待恢复动作执行
        await asyncio.sleep(5)

        # 检查动作状态
        for action in actions:
            status = recovery_engine.get_action_status(action.id)
            logger.info(f"动作 {action.name}: {status.status.value}")

        # 清理
        await recovery_engine.stop()
        await monitoring.stop()
        await monitoring.shutdown()

    asyncio.run(test_intelligent_alerting())
