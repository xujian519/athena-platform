#!/usr/bin/env python3
"""
端到端优化器 (End-to-End Optimizer)
全链路性能优化,最大化端到端成功率

作者: 小诺·双鱼公主
版本: v2.0.0
优化目标: 端到端成功率 82% → 90%
"""

from __future__ import annotations
import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class StageType(str, Enum):
    """阶段类型"""

    INTENT_RECOGNITION = "intent_recognition"  # 意图识别
    PARAMETER_EXTRACTION = "parameter_extraction"  # 参数提取
    TOOL_SELECTION = "tool_selection"  # 工具选择
    TOOL_EXECUTION = "tool_execution"  # 工具执行
    RESULT_PROCESSING = "result_processing"  # 结果处理
    RESPONSE_GENERATION = "response_generation"  # 响应生成


class ExecutionStatus(str, Enum):
    """执行状态"""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    RETRY = "retry"
    FALLBACK = "fallback"


@dataclass
class StageResult:
    """阶段结果"""

    stage: StageType
    status: ExecutionStatus
    latency_ms: float
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionTrace:
    """执行追踪"""

    trace_id: str
    request_id: str
    stages: list[StageResult]
    overall_status: ExecutionStatus
    total_latency_ms: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationPoint:
    """优化点"""

    stage: StageType
    issue: str
    suggestion: str
    potential_improvement: float
    priority: int  # 1-10, 10最高


class EndToEndOptimizer:
    """
    端到端优化器

    功能:
    1. 全链路追踪
    2. 瓶颈识别
    3. 自动优化建议
    4. A/B测试支持
    5. 性能监控
    """

    def __init__(self, target_success_rate: float = 0.90):
        self.name = "端到端优化器"
        self.version = "2.0.0"
        self.target_success_rate = target_success_rate

        # 执行追踪历史
        self.execution_traces: deque = deque(maxlen=1000)

        # 阶段性能统计
        self.stage_stats: dict[StageType, dict[str, float]] = {
            stage: {"total": 0, "success": 0, "failure": 0, "avg_latency_ms": 0}
            for stage in StageType
        }

        # 优化点队列
        self.optimization_points: list[OptimizationPoint] = []

        # A/B测试配置
        self.ab_tests: dict[str, dict[str, Any]] = {}

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "current_success_rate": 0.0,
            "avg_latency_ms": 0,
            "optimization_implemented": 0,
        }

        logger.info(f"✅ {self.name} 初始化完成 (目标成功率: {target_success_rate:.1%})")

    async def execute_pipeline(
        self, request_id: str, stages: list[Callable], context: dict[str, Any] | None = None
    ) -> ExecutionTrace:
        """
        执行端到端流程

        Args:
            request_id: 请求ID
            stages: 阶段函数列表
            context: 上下文

        Returns:
            执行追踪
        """
        self.stats["total_requests"] += 1

        trace_id = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        stage_results = []
        start_time = time.time()

        current_context = context or {}

        for _i, stage_func in enumerate(stages):
            stage_start = time.time()

            try:
                # 执行阶段
                stage_output = await self._execute_stage(stage_func, current_context)

                stage_latency = (time.time() - stage_start) * 1000

                # 记录结果
                stage_result = StageResult(
                    stage=StageType(stage_func.__name__),
                    status=ExecutionStatus.SUCCESS,
                    latency_ms=stage_latency,
                    output=stage_output,
                )

                stage_results.append(stage_result)

                # 更新上下文
                if isinstance(stage_output, dict):
                    current_context.update(stage_output)
                else:
                    current_context["output"] = stage_output

                # 更新统计
                self._update_stage_stats(stage_result.stage, stage_result)

            except Exception as e:
                stage_latency = (time.time() - stage_start) * 1000

                stage_result = StageResult(
                    stage=StageType(stage_func.__name__),
                    status=ExecutionStatus.FAILURE,
                    latency_ms=stage_latency,
                    error=str(e),
                )

                stage_results.append(stage_result)
                self._update_stage_stats(stage_result.stage, stage_result)

                # 尝试恢复
                recovery_result = await self._attempt_recovery(stage_result, current_context)
                if recovery_result:
                    stage_results.append(recovery_result)
                    if recovery_result.status == ExecutionStatus.SUCCESS:
                        current_context.update(recovery_result.output or {})
                else:
                    # 无法恢复,终止流程
                    break

        total_latency = (time.time() - start_time) * 1000

        # 判断整体成功
        overall_success = all(
            s.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FALLBACK] for s in stage_results
        )

        overall_status = ExecutionStatus.SUCCESS if overall_success else ExecutionStatus.FAILURE

        trace = ExecutionTrace(
            trace_id=trace_id,
            request_id=request_id,
            stages=stage_results,
            overall_status=overall_status,
            total_latency_ms=total_latency,
            success=overall_success,
        )

        # 记录追踪
        self.execution_traces.append(trace)

        # 更新统计
        if overall_success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1

        self.stats["current_success_rate"] = (
            self.stats["successful_requests"] / self.stats["total_requests"]
            if self.stats["total_requests"] > 0
            else 0
        )

        self.stats["avg_latency_ms"] = (
            self.stats["avg_latency_ms"] * (self.stats["total_requests"] - 1) + total_latency
        ) / self.stats["total_requests"]

        # 分析并生成优化建议
        if not overall_success:
            await self._analyze_failure(trace)

        return trace

    async def _execute_stage(self, stage_func: Callable, context: dict[str, Any]) -> Any:
        """执行单个阶段"""
        if asyncio.iscoroutinefunction(stage_func):
            return await stage_func(context)
        else:
            return stage_func(context)

    async def _attempt_recovery(
        self, failed_stage: StageResult, context: dict[str, Any]
    ) -> StageResult | None:
        """尝试恢复"""
        logger.warning(f"⚠️ 阶段 {failed_stage.stage} 失败,尝试恢复...")

        # 简化版:尝试降级处理
        try:
            # 使用默认值或缓存
            fallback_output = self._get_fallback_output(failed_stage.stage)

            return StageResult(
                stage=failed_stage.stage,
                status=ExecutionStatus.FALLBACK,
                latency_ms=0,
                output=fallback_output,
                metadata={"recovery": "fallback"},
            )

        except Exception as e:
            logger.error(f"❌ 恢复失败: {e}")
            return None

    def _get_fallback_output(self, stage: StageType) -> Any:
        """获取降级输出"""
        fallbacks = {
            StageType.INTENT_RECOGNITION: {"intent": "unknown", "confidence": 0.5},
            StageType.PARAMETER_EXTRACTION: {},
            StageType.TOOL_SELECTION: {"tool": "default"},
            StageType.TOOL_EXECUTION: {"result": "unavailable"},
            StageType.RESULT_PROCESSING: {"processed": False},
            StageType.RESPONSE_GENERATION: {"response": "抱歉,处理出现问题。"},
        }
        return fallbacks.get(stage, {})

    def _update_stage_stats(self, stage: StageType, result: StageResult) -> Any:
        """更新阶段统计"""
        stats = self.stage_stats[stage]
        stats["total"] += 1

        if result.status == ExecutionStatus.SUCCESS:
            stats["success"] += 1
        else:
            stats["failure"] += 1

        # 更新平均延迟
        stats["avg_latency_ms"] = (
            stats["avg_latency_ms"] * (stats["total"] - 1) + result.latency_ms
        ) / stats["total"]

    async def _analyze_failure(self, trace: ExecutionTrace):
        """分析失败原因"""
        # 找出失败的阶段
        failed_stages = [s for s in trace.stages if s.status == ExecutionStatus.FAILURE]

        for stage in failed_stages:
            # 生成优化建议
            optimization_point = OptimizationPoint(
                stage=stage.stage,
                issue=f"阶段失败: {stage.error}",
                suggestion=f"建议: {self._generate_suggestion(stage)}",
                potential_improvement=0.05,
                priority=self._compute_priority(stage),
            )

            self.optimization_points.append(optimization_point)

        logger.warning(f"🔍 失败分析: {len(failed_stages)} 个阶段失败")

    def _generate_suggestion(self, stage: StageResult) -> str:
        """生成优化建议"""
        suggestions = {
            StageType.INTENT_RECOGNITION: "增加训练数据,优化模型",
            StageType.PARAMETER_EXTRACTION: "改进提取规则,增加上下文推理",
            StageType.TOOL_SELECTION: "使用强化学习路由,优化选择策略",
            StageType.TOOL_EXECUTION: "添加重试机制,优化错误处理",
            StageType.RESULT_PROCESSING: "增强容错性,添加验证",
            StageType.RESPONSE_GENERATION: "优化模板,增加个性化",
        }
        return suggestions.get(stage.stage, "请检查错误日志")

    def _compute_priority(self, stage: StageResult) -> int:
        """计算优化优先级"""
        # 基于失败频率和影响计算优先级
        stats = self.stage_stats.get(stage.stage, {})
        failure_rate = stats.get("failure", 0) / max(1, stats.get("total", 1))

        priority = int(failure_rate * 10)
        return min(10, max(1, priority))

    async def identify_bottlenecks(self) -> list[OptimizationPoint]:
        """识别瓶颈"""
        bottlenecks = []

        for stage, stats in self.stage_stats.items():
            if stats["total"] == 0:
                continue

            # 检查失败率
            failure_rate = stats["failure"] / stats["total"]
            if failure_rate > 0.15:  # 失败率超过15%
                bottlenecks.append(
                    OptimizationPoint(
                        stage=stage,
                        issue=f"高失败率 ({failure_rate:.1%})",
                        suggestion="优化错误处理,增加重试机制",
                        potential_improvement=failure_rate * 0.5,
                        priority=8,
                    )
                )

            # 检查延迟
            if stats["avg_latency_ms"] > 500:  # 延迟超过500ms
                bottlenecks.append(
                    OptimizationPoint(
                        stage=stage,
                        issue=f"高延迟 ({stats['avg_latency_ms']:.0f}ms)",
                        suggestion="优化算法,使用缓存,并行处理",
                        potential_improvement=0.1,
                        priority=6,
                    )
                )

        # 按优先级排序
        bottlenecks.sort(key=lambda x: x.priority, reverse=True)

        return bottlenecks

    async def implement_optimization(self, optimization_point: OptimizationPoint) -> bool:
        """
        实施优化

        Args:
            optimization_point: 优化点

        Returns:
            是否成功
        """
        logger.info(f"🔧 实施优化: {optimization_point.stage} - {optimization_point.suggestion}")

        # 简化版:记录优化实施
        self.stats["optimization_implemented"] += 1

        # 从优化点队列中移除
        if optimization_point in self.optimization_points:
            self.optimization_points.remove(optimization_point)

        return True

    async def run_ab_test(
        self, test_name: str, control_func: Callable, variant_func: Callable, sample_size: int = 100
    ) -> dict[str, Any]:
        """
        运行A/B测试

        Args:
            test_name: 测试名称
            control_func: 对照组函数
            variant_func: 实验组函数
            sample_size: 样本量

        Returns:
            测试结果
        """
        logger.info(f"🧪 开始A/B测试: {test_name}")

        # 运行测试
        control_results = []
        variant_results = []

        for _i in range(sample_size):
            # 对照组
            control_start = time.time()
            try:
                await control_func()
                control_latency = (time.time() - control_start) * 1000
                control_results.append({"success": True, "latency_ms": control_latency})
            except Exception:
                control_results.append({"success": False, "latency_ms": 0})

            # 实验组
            variant_start = time.time()
            try:
                await variant_func()
                variant_latency = (time.time() - variant_start) * 1000
                variant_results.append({"success": True, "latency_ms": variant_latency})
            except Exception:
                variant_results.append({"success": False, "latency_ms": 0})

        # 计算结果
        control_success_rate = sum(1 for r in control_results if r["success"]) / sample_size
        variant_success_rate = sum(1 for r in variant_results if r["success"]) / sample_size

        control_avg_latency = sum(r["latency_ms"] for r in control_results) / sample_size
        variant_avg_latency = sum(r["latency_ms"] for r in variant_results) / sample_size

        improvement = (variant_success_rate - control_success_rate) / max(
            control_success_rate, 0.01
        )

        result = {
            "test_name": test_name,
            "control": {
                "success_rate": control_success_rate,
                "avg_latency_ms": control_avg_latency,
            },
            "variant": {
                "success_rate": variant_success_rate,
                "avg_latency_ms": variant_avg_latency,
            },
            "improvement": improvement,
            "recommendation": "variant" if improvement > 0 else "control",
        }

        self.ab_tests[test_name] = result

        logger.info(f"✅ A/B测试完成: 改进 {improvement:.1%}, 推荐 {result['recommendation']}")

        return result

    def get_status(self) -> dict[str, Any]:
        """获取优化器状态"""
        asyncio.create_task(self.identify_bottlenecks())

        return {
            "name": self.name,
            "version": self.version,
            "target_success_rate": self.target_success_rate,
            "current_success_rate": self.stats["current_success_rate"],
            "gap_to_target": self.target_success_rate - self.stats["current_success_rate"],
            "statistics": self.stats,
            "stage_performance": {
                stage.value: {
                    "success_rate": stats["success"] / max(1, stats["total"]),
                    "avg_latency_ms": stats["avg_latency_ms"],
                    "total": stats["total"],
                }
                for stage, stats in self.stage_stats.items()
            },
            "optimization_points": len(self.optimization_points),
            "top_bottlenecks": [
                {"stage": p.stage.value, "issue": p.issue, "priority": p.priority}
                for p in self.optimization_points[:5]
            ],
            "ab_tests": list(self.ab_tests.keys()),
        }


# 全局单例
_e2e_optimizer_instance: EndToEndOptimizer | None = None


def get_end_to_end_optimizer() -> EndToEndOptimizer:
    """获取端到端优化器实例"""
    global _e2e_optimizer_instance
    if _e2e_optimizer_instance is None:
        _e2e_optimizer_instance = EndToEndOptimizer()
    return _e2e_optimizer_instance
