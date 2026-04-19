#!/usr/bin/env python3
"""
混沌工程实践
Chaos Engineering

通过主动注入故障提高系统鲁棒性:
1. 故障注入器
2. 压力测试
3. 恢复测试
4. 韧性评估
5. 容灾演练
6. 混沌实验

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "混沌工程"
"""

from __future__ import annotations
import asyncio
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FaultType(Enum):
    """故障类型"""

    LATENCY = "latency"  # 延迟注入
    DROP = "drop"  # 请求丢弃
    ERROR = "error"  # 错误响应
    OVERLOAD = "overload"  # 过载
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # 资源耗尽
    NETWORK_FAILURE = "network_failure"  # 网络故障
    CRASH = "crash"  # 崩溃


class TestMetric(Enum):
    """测试指标"""

    RECOVERY_TIME = "recovery_time"  # 恢复时间
    ERROR_RATE = "error_rate"  # 错误率
    AVAILABILITY = "availability"  # 可用性
    THROUGHPUT = "throughput"  # 吞吐量
    LATENCY = "latency"  # 延迟


@dataclass
class FaultInjection:
    """故障注入配置"""

    name: str
    fault_type: FaultType
    target: str  # 目标组件
    probability: float = 0.1  # 注入概率
    duration: float = 5.0  # 持续时间(秒)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChaosExperiment:
    """混沌实验"""

    experiment_id: str
    name: str
    description: str
    fault_injections: list[FaultInjection]
    duration: float
    success_criteria: dict[TestMetric, float]
    results: dict[str, Any] | None = None
    timestamp: datetime = None


@dataclass
class ResilienceScore:
    """韧性评分"""

    availability: float  # 可用性
    recoverability: float  # 可恢复性
    fault_tolerance: float  # 容错性
    overall: float  # 综合评分


class ChaosEngineering:
    """
    混沌工程实践

    核心功能:
    1. 故障注入
    2. 压力测试
    3. 韧性评估
    4. 恢复测试
    5. 容灾演练
    6. 持续改进
    """

    def __init__(self):
        # 故障注入器
        self.fault_injectors: dict[FaultType, Callable] = {}
        self._initialize_fault_injectors()

        # 实验历史
        self.experiment_history: list[ChaosExperiment] = []

        # 系统基准
        self.baseline_metrics: dict[str, float] = {}

        # 当前活跃的故障
        self.active_faults: dict[str, FaultInjection] = {}

        # 统计信息
        self.metrics = {
            "total_experiments": 0,
            "successful_experiments": 0,
            "failed_experiments": 0,
            "avg_recovery_time": 0.0,
        }

        logger.info("🌀 混沌工程实践初始化完成")

    def _initialize_fault_injectors(self) -> Any:
        """初始化故障注入器"""
        self.fault_injectors[FaultType.LATENCY] = self._inject_latency
        self.fault_injectors[FaultType.DROP] = self._inject_drop
        self.fault_injectors[FaultType.ERROR] = self._inject_error
        self.fault_injectors[FaultType.OVERLOAD] = self._inject_overload
        self.fault_injectors[FaultType.RESOURCE_EXHAUSTION] = self._inject_resource_exhaustion
        self.fault_injectors[FaultType.NETWORK_FAILURE] = self._inject_network_failure
        self.fault_injectors[FaultType.CRASH] = self._inject_crash

    async def inject_fault(self, injection: FaultInjection):
        """
        注入故障

        Args:
            injection: 故障注入配置
        """
        # 检查概率
        if random.random() > injection.probability:
            return

        logger.warning(
            f"🔥 注入故障: {injection.name} "
            f"({injection.fault_type.value}) -> {injection.target}"
        )

        # 执行注入
        injector = self.fault_injectors.get(injection.fault_type)
        if injector:
            await injector(injection)
            self.active_faults[injection.name] = injection

    async def _inject_latency(self, injection: FaultInjection):
        """注入延迟"""
        delay = injection.parameters.get("delay_ms", random.randint(100, 5000))
        logger.info(f"⏱️ 延迟注入: {delay}ms")
        await asyncio.sleep(delay / 1000.0)

    async def _inject_drop(self, injection: FaultInjection):
        """注入请求丢弃"""
        logger.warning("🚫 请求丢弃")
        raise Exception("请求被混沌工程丢弃")

    async def _inject_error(self, injection: FaultInjection):
        """注入错误响应"""
        error_type = injection.parameters.get("error_type", "InternalError")
        logger.warning(f"❌ 错误注入: {error_type}")
        raise Exception(f"混沌工程错误: {error_type}")

    async def _inject_overload(self, injection: FaultInjection):
        """注入过载"""
        load_factor = injection.parameters.get("load_factor", 10)
        logger.warning(f"📊 过载注入: {load_factor}x")

        # 模拟CPU密集型任务
        start = time.time()
        while time.time() - start < 0.5:
            _ = sum(range(1000))

    async def _inject_resource_exhaustion(self, injection: FaultInjection):
        """注入资源耗尽"""
        logger.warning("💾 资源耗尽注入")
        raise MemoryError("混沌工程: 内存不足")

    async def _inject_network_failure(self, injection: FaultInjection):
        """注入网络故障"""
        logger.warning("🌐 网络故障注入")
        raise ConnectionError("混沌工程: 网络不可达")

    async def _inject_crash(self, injection: FaultInjection):
        """注入崩溃"""
        logger.critical("💥 崩溃注入")
        raise SystemError("混沌工程: 系统崩溃")

    async def run_chaos_experiment(self, experiment: ChaosExperiment) -> dict[str, Any]:
        """
        运行混沌实验

        Args:
            experiment: 混沌实验配置

        Returns:
            Dict: 实验结果
        """
        logger.info(f"🧪 开始混沌实验: {experiment.name}")

        experiment.timestamp = datetime.now()
        self.metrics["total_experiments"] += 1

        # 1. 采集基准指标
        baseline = await self._collect_metrics()

        # 2. 注入故障
        time.time()
        injection_tasks = []

        for injection in experiment.fault_injections:
            task = asyncio.create_task(self.inject_fault(injection))
            injection_tasks.append(task)

        # 3. 运行实验
        try:
            await asyncio.wait_for(
                asyncio.gather(*injection_tasks, return_exceptions=True),
                timeout=experiment.duration,
            )

        except asyncio.TimeoutError:
            logger.warning("⏰ 实验超时")

        # 4. 采集故障后指标
        faulted_metrics = await self._collect_metrics()

        # 5. 等待恢复
        recovery_start = time.time()
        await self._wait_for_recovery(baseline, timeout=60)
        recovery_time = time.time() - recovery_start

        # 6. 采集恢复后指标
        recovered_metrics = await self._collect_metrics()

        # 7. 评估结果
        results = await self._evaluate_experiment(
            experiment, baseline, faulted_metrics, recovered_metrics, recovery_time
        )

        experiment.results = results
        self.experiment_history.append(experiment)

        # 8. 更新统计
        if results.get("passed", False):
            self.metrics["successful_experiments"] += 1
        else:
            self.metrics["failed_experiments"] += 1

        self.metrics["avg_recovery_time"] = (
            self.metrics["avg_recovery_time"] * 0.9 + recovery_time * 0.1
        )

        logger.info(
            f"✅ 实验完成: {experiment.name} - " f"{'通过' if results.get('passed') else '失败'}"
        )

        return results

    async def _collect_metrics(self) -> dict[str, float]:
        """采集系统指标"""
        # 简化实现:返回模拟指标
        return {"availability": 0.99, "throughput": 100.0, "latency": 50.0, "error_rate": 0.01}

    async def _wait_for_recovery(self, baseline: dict[str, float], timeout: float = 60):
        """等待系统恢复"""
        start = time.time()

        while time.time() - start < timeout:
            current = await self._collect_metrics()

            # 检查是否恢复到基准水平的80%
            if (
                current["availability"] >= baseline["availability"] * 0.8
                and current["error_rate"] <= baseline["error_rate"] * 1.2
            ):
                logger.info("✅ 系统已恢复")
                return

            await asyncio.sleep(1)

        logger.warning("⚠️ 系统未在预期时间内恢复")

    async def _evaluate_experiment(
        self,
        experiment: ChaosExperiment,
        baseline: dict[str, float],
        faulted: dict[str, float],
        recovered: dict[str, float],
        recovery_time: float,
    ) -> dict[str, Any]:
        """评估实验结果"""
        results = {"passed": True, "metrics": {}, "criteria_met": {}}

        # 检查成功标准
        for metric, threshold in experiment.success_criteria.items():
            if metric == TestMetric.RECOVERY_TIME:
                passed = recovery_time <= threshold
                results["metrics"]["recovery_time"] = recovery_time
                results["criteria_met"][metric.value] = passed

            elif metric == TestMetric.ERROR_RATE:
                error_rate_increase = (faulted["error_rate"] - baseline["error_rate"]) / max(
                    baseline["error_rate"], 0.001
                )
                passed = error_rate_increase <= threshold
                results["metrics"]["error_rate_increase"] = error_rate_increase
                results["criteria_met"][metric.value] = passed

            elif metric == TestMetric.AVAILABILITY:
                availability_drop = baseline["availability"] - faulted["availability"]
                passed = availability_drop <= threshold
                results["metrics"]["availability_drop"] = availability_drop
                results["criteria_met"][metric.value] = passed

            elif metric == TestMetric.THROUGHPUT:
                throughput_retention = recovered["throughput"] / max(baseline["throughput"], 1)
                passed = throughput_retention >= threshold
                results["metrics"]["throughput_retention"] = throughput_retention
                results["criteria_met"][metric.value] = passed

            elif metric == TestMetric.LATENCY:
                latency_increase = (faulted["latency"] - baseline["latency"]) / max(
                    baseline["latency"], 1
                )
                passed = latency_increase <= threshold
                results["metrics"]["latency_increase"] = latency_increase
                results["criteria_met"][metric.value] = passed

            if not passed:
                results["passed"] = False

        return results

    async def calculate_resilience_score(self) -> ResilienceScore:
        """计算系统韧性评分"""
        # 基于历史实验计算
        if not self.experiment_history:
            return ResilienceScore(0.8, 0.8, 0.8, 0.8)

        # 可用性:实验通过率
        passed = sum(1 for e in self.experiment_history if e.results and e.results.get("passed"))
        total = len(self.experiment_history)
        availability = passed / max(total, 1)

        # 可恢复性:基于平均恢复时间
        avg_recovery = self.metrics["avg_recovery_time"]
        recoverability = max(0, 1 - avg_recovery / 60)  # 60秒为满分线

        # 容错性:成功实验占比
        fault_tolerance = self.metrics["successful_experiments"] / max(
            self.metrics["total_experiments"], 1
        )

        # 综合评分
        overall = (availability + recoverability + fault_tolerance) / 3

        return ResilienceScore(
            availability=availability,
            recoverability=recoverability,
            fault_tolerance=fault_tolerance,
            overall=overall,
        )

    def create_common_experiments(self) -> list[ChaosExperiment]:
        """创建常用混沌实验"""
        experiments = []

        # 实验1: 延迟注入
        experiments.append(
            ChaosExperiment(
                experiment_id="chaos_latency_001",
                name="延迟注入测试",
                description="测试系统在高延迟下的表现",
                fault_injections=[
                    FaultInjection(
                        name="network_latency",
                        fault_type=FaultType.LATENCY,
                        target="network",
                        probability=0.3,
                        duration=10,
                        parameters={"delay_ms": 2000},
                    )
                ],
                duration=30,
                success_criteria={TestMetric.RECOVERY_TIME: 10, TestMetric.AVAILABILITY: 0.1},
            )
        )

        # 实验2: 服务故障
        experiments.append(
            ChaosExperiment(
                experiment_id="chaos_crash_001",
                name="服务故障测试",
                description="测试系统在服务崩溃下的恢复能力",
                fault_injections=[
                    FaultInjection(
                        name="service_crash",
                        fault_type=FaultType.CRASH,
                        target="service",
                        probability=0.2,
                        duration=5,
                    )
                ],
                duration=30,
                success_criteria={TestMetric.RECOVERY_TIME: 20, TestMetric.AVAILABILITY: 0.2},
            )
        )

        # 实验3: 资源耗尽
        experiments.append(
            ChaosExperiment(
                experiment_id="chaos_resource_001",
                name="资源耗尽测试",
                description="测试系统在资源不足时的表现",
                fault_injections=[
                    FaultInjection(
                        name="memory_exhaustion",
                        fault_type=FaultType.RESOURCE_EXHAUSTION,
                        target="memory",
                        probability=0.15,
                        duration=10,
                    )
                ],
                duration=30,
                success_criteria={TestMetric.RECOVERY_TIME: 15, TestMetric.ERROR_RATE: 0.5},
            )
        )

        return experiments

    async def get_chaos_metrics(self) -> dict[str, Any]:
        """获取混沌工程统计"""
        resilience = await self.calculate_resilience_score()

        return {
            "experiments": {
                "total": self.metrics["total_experiments"],
                "successful": self.metrics["successful_experiments"],
                "failed": self.metrics["failed_experiments"],
                "success_rate": (
                    self.metrics["successful_experiments"]
                    / max(self.metrics["total_experiments"], 1)
                ),
            },
            "recovery": {"avg_recovery_time": self.metrics["avg_recovery_time"]},
            "resilience": {
                "availability": resilience.availability,
                "recoverability": resilience.recoverability,
                "fault_tolerance": resilience.fault_tolerance,
                "overall": resilience.overall,
            },
            "active_faults": len(self.active_faults),
        }


# 导出便捷函数
_chaos: ChaosEngineering | None = None


def get_chaos_engineering() -> ChaosEngineering:
    """获取混沌工程单例"""
    global _chaos
    if _chaos is None:
        _chaos = ChaosEngineering()
    return _chaos
