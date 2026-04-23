#!/usr/bin/env python3
from __future__ import annotations
"""
Athena增强工具调用管理器 - 集成全链路监控
Enhanced Tool Call Manager with Full-Link Monitoring

在原有工具调用管理器基础上集成:
1. 全链路追踪 - 完整的调用链路追踪
2. 实时监控 - 性能指标实时收集
3. 自动验证 - 调用结果自动验证
4. 智能告警 - 异常自动告警
5. 监控仪表板 - 可视化监控数据

作者: Athena平台团队
创建时间: 2025-12-29
版本: v2.0.0
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.logging_config import setup_logging
from core.monitoring.full_link_monitoring_system import (
    FullLinkMonitoringSystem,
    ValidationResult,
    get_monitoring_system,
)
from core.tools.tool_call_manager import (
    CallStatus,
    ToolCallManager,
    ToolCallResult,
)

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class MonitoredToolCallResult(ToolCallResult):
    """带监控的工具调用结果"""

    trace_id: Optional[str] = None
    validation_result: ValidationResult | None = None
    validation_error: Optional[str] = None
    monitoring_data: dict[str, Any] = field(default_factory=dict)


class MonitoredToolCallManager(ToolCallManager):
    """
    增强的工具调用管理器 - 集成全链路监控

    在原有功能基础上增加:
    1. 自动追踪每次工具调用
    2. 实时收集性能指标
    3. 自动验证调用结果
    4. 智能异常检测和告警
    5. 监控仪表板数据生成
    """

    def __init__(self, log_dir: str = "logs/tool_calls"):
        # 初始化父类
        super().__init__(log_dir)

        # 集成监控系统
        self.monitoring: FullLinkMonitoringSystem = get_monitoring_system()

        # 启用监控标志
        self.monitoring_enabled = True

        # 验证启用标志
        self.validation_enabled = True

        logger.info("🔧 增强工具调用管理器初始化完成(已集成全链路监控)")

    async def call_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],        context: Optional[dict[str, Any]] = None,
        priority: int = 2,
        timeout: Optional[float] = None,
        enable_monitoring: bool = True,
        enable_validation: bool = True,
    ) -> MonitoredToolCallResult:
        """
        调用工具(增强版 - 带监控和验证)

        Args:
            tool_name: 工具名称
            parameters: 参数字典
            context: 上下文信息
            priority: 优先级 (1=high, 2=medium, 3=low)
            timeout: 超时时间(秒)
            enable_monitoring: 是否启用监控
            enable_validation: 是否启用结果验证

        Returns:
            MonitoredToolCallResult: 带监控的调用结果
        """
        # 开始追踪
        trace_id = None
        if enable_monitoring and self.monitoring_enabled:
            trace_id = self.monitoring.start_trace(
                operation=f"tool.{tool_name}",
                input_data={"parameters": parameters, "context": context},
                tags={"tool_name": tool_name, "priority": str(priority)},
            )

        # 调用父类方法
        base_result = await super().call_tool(
            tool_name=tool_name,
            parameters=parameters,
            context=context,
            priority=priority,
            timeout=timeout,
        )

        # 创建增强结果对象
        result = MonitoredToolCallResult(
            request_id=base_result.request_id,
            tool_name=base_result.tool_name,
            status=base_result.status,
            result=base_result.result,
            error=base_result.error,
            execution_time=base_result.execution_time,
            timestamp=base_result.timestamp,
            metadata=base_result.metadata,
            trace_id=trace_id,
        )

        # 结果验证
        if (
            enable_validation
            and self.validation_enabled
            and base_result.status == CallStatus.SUCCESS
        ):
            validation_result, validation_error = self.monitoring.validate_result(
                tool_name=tool_name, result=base_result.result, trace_id=trace_id
            )
            result.validation_result = validation_result
            result.validation_error = validation_error

            # 如果验证失败,记录警告但不影响调用状态
            if validation_result != ValidationResult.VALID:
                logger.warning(
                    f"⚠️ 工具 {tool_name} 结果验证失败: {validation_result.value} - {validation_error}"
                )
                result.metadata["validation_warning"] = True

        # 完成追踪
        if trace_id:
            self.monitoring.finish_trace(
                trace_id=trace_id,
                output_data=(
                    {"result": str(base_result.result)[:200]} if base_result.result else None
                ),
                status=base_result.status.value,
                error=base_result.error,
            )

            # 添加监控数据到结果
            trace = self.monitoring.get_trace(trace_id)
            if trace:
                result.monitoring_data = trace

        return result

    async def call_tool_batch(
        self,
        calls: list[dict[str, Any]],        enable_monitoring: bool = True,
        enable_validation: bool = True,
    ) -> list[MonitoredToolCallResult]:
        """
        批量调用工具

        Args:
            calls: 调用列表,每个元素是包含 tool_name, parameters, context 等的字典
            enable_monitoring: 是否启用监控
            enable_validation: 是否启用结果验证

        Returns:
            调用结果列表
        """
        # 创建父追踪
        parent_trace_id = None
        if enable_monitoring and self.monitoring_enabled:
            parent_trace_id = self.monitoring.start_trace(
                operation="batch_tool_call",
                input_data={"call_count": len(calls)},
                tags={"batch": "true"},
            )

        # 并发执行所有调用
        tasks = []
        for call in calls:
            task = self.call_tool(
                tool_name=call["tool_name"],
                parameters=call.get("parameters", {}),
                context=call.get("context"),
                priority=call.get("priority", 2),
                timeout=call.get("timeout"),
                enable_monitoring=enable_monitoring,
                enable_validation=enable_validation,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                # 创建失败结果
                final_results.append(
                    MonitoredToolCallResult(
                        request_id=str(i),
                        tool_name=calls[i].get("tool_name", "unknown"),
                        status=CallStatus.FAILED,
                        error=str(r),
                    )
                )
            else:
                final_results.append(r)

        # 完成父追踪
        if parent_trace_id:
            self.monitoring.finish_trace(
                trace_id=parent_trace_id,
                output_data={
                    "success_count": sum(1 for r in final_results if r.status == CallStatus.SUCCESS)
                },
                status=(
                    "success"
                    if all(r.status == CallStatus.SUCCESS for r in final_results)
                    else "partial_success"
                ),
            )

        return final_results

    def get_monitoring_dashboard(self) -> dict[str, Any]:
        """获取监控仪表板数据"""
        return self.monitoring.get_dashboard_data()

    def get_tool_performance_metrics(self, tool_name: str) -> dict[str, Any]:
        """获取工具性能指标"""
        traces = self.monitoring.get_traces_by_operation(f"tool.{tool_name}", limit=100)

        if not traces:
            return {"error": f"没有找到工具 {tool_name} 的追踪数据"}

        # 计算性能指标
        durations = [t["metrics"].get("duration_ms", 0) for t in traces if "metrics" in t]
        durations = [d for d in durations if d > 0]

        if not durations:
            return {"error": f"工具 {tool_name} 没有有效的性能数据"}

        durations.sort()
        n = len(durations)

        total_calls = len(traces)
        success_calls = sum(1 for t in traces if t.get("status") == "success")
        error_calls = sum(1 for t in traces if t.get("status") in ["failed", "error", "timeout"])

        return {
            "tool_name": tool_name,
            "total_calls": total_calls,
            "success_calls": success_calls,
            "error_calls": error_calls,
            "success_rate": (success_calls / total_calls * 100) if total_calls > 0 else 0,
            "error_rate": (error_calls / total_calls * 100) if total_calls > 0 else 0,
            "performance": {
                "avg_duration_ms": sum(durations) / n,
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "p50_duration_ms": durations[int(n * 0.5)],
                "p95_duration_ms": durations[int(n * 0.95)],
                "p99_duration_ms": durations[int(n * 0.99)],
            },
            "recent_traces": traces[-10:],
        }

    def get_all_tools_performance(self) -> dict[str, Any]:
        """获取所有工具的性能概览"""
        all_tools = self.list_tools()
        performance = {}

        for tool_name in all_tools:
            tool_performance = self.get_tool_performance_metrics(tool_name)
            if "error" not in tool_performance:
                performance[tool_name] = {
                    "total_calls": tool_performance["total_calls"],
                    "success_rate": tool_performance["success_rate"],
                    "avg_duration_ms": tool_performance["performance"]["avg_duration_ms"],
                    "p95_duration_ms": tool_performance["performance"]["p95_duration_ms"],
                }

        return performance

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """获取活跃告警"""
        dashboard = self.monitoring.get_dashboard_data()
        return dashboard.get("active_alerts", [])

    def get_validation_stats(self) -> dict[str, Any]:
        """获取验证统计"""
        dashboard = self.monitoring.get_dashboard_data()

        # 从指标中计算验证统计
        validation_metrics = {}
        for metric_data in dashboard.get("current_metrics", {}).items():
            if "validation" in str(metric_data):
                validation_metrics[metric_data[0]] = metric_data[1]

        return {
            "validation_enabled": self.validation_enabled,
            "metrics": validation_metrics,
            "dashboard": dashboard,
        }

    def export_monitoring_report(self, filepath: str) -> Any:
        """导出监控报告"""
        import json

        report = {
            "timestamp": datetime.now().isoformat(),
            "tool_stats": self.get_all_tools_performance(),
            "monitoring_dashboard": self.get_monitoring_dashboard(),
            "validation_stats": self.get_validation_stats(),
            "manager_stats": self.get_stats(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📊 监控报告已导出: {filepath}")

    def enable_monitoring(self, enabled: bool = True) -> Any:
        """启用/禁用监控"""
        self.monitoring_enabled = enabled
        logger.info(f"🔍 监控已{'启用' if enabled else '禁用'}")

    def enable_validation(self, enabled: bool = True) -> Any:
        """启用/禁用验证"""
        self.validation_enabled = enabled
        logger.info(f"✅ 验证已{'启用' if enabled else '禁用'}")

    def cleanup(self) -> Any:
        """清理资源"""
        logger.info("🧹 正在清理增强工具调用管理器...")
        self.monitoring.cleanup()
        logger.info("✅ 增强工具调用管理器清理完成")


# 全局单例
_monitored_tool_manager: MonitoredToolCallManager | None = None


def get_monitored_tool_manager() -> MonitoredToolCallManager:
    """获取增强工具调用管理器单例"""
    global _monitored_tool_manager
    if _monitored_tool_manager is None:
        _monitored_tool_manager = MonitoredToolCallManager()

        # 注册所有工具
        from core.tools.production_tool_implementations import register_production_tools
        from core.tools.tool_implementations import register_real_tools

        register_real_tools(_monitored_tool_manager)
        register_production_tools(_monitored_tool_manager)

        logger.info(f"✅ 已注册 {_monitored_tool_manager.tools.__len__()} 个工具")

    return _monitored_tool_manager


# 便捷函数
async def call_tool(
    tool_name: str, parameters: dict[str, Any], context: Optional[dict[str, Any]] = None
) -> MonitoredToolCallResult:
    """便捷的工具调用函数(带监控)"""
    manager = get_monitored_tool_manager()
    return await manager.call_tool(tool_name, parameters, context)


# 测试
async def test_monitored_tool_call_manager():
    """测试增强工具调用管理器"""
    print("🧪 测试增强工具调用管理器")
    print("=" * 60)

    # 获取管理器
    manager = get_monitored_tool_manager()

    print(f"\n🔧 已注册工具: {len(manager.tools)}个")

    # 测试单个工具调用
    print("\n📞 测试单个工具调用(带监控和验证)")
    result = await manager.call_tool(
        tool_name="emotional_support",
        parameters={"emotion": "焦虑", "intensity": 7},
        enable_monitoring=True,
        enable_validation=True,
    )

    print(f"工具: {result.tool_name}")
    print(f"状态: {result.status.value}")
    print(f"执行时间: {result.execution_time:.3f}秒")
    print(f"验证结果: {result.validation_result.value if result.validation_result else 'N/A'}")
    print(f"追踪ID: {result.trace_id[:8] if result.trace_id else 'NLA'}...")

    # 测试批量调用
    print("\n📞 测试批量工具调用")
    batch_calls = [
        {
            "tool_name": "code_analyzer",
            "parameters": {"code": "print('hello')", "language": "python"},
        },
        {"tool_name": "decision_engine", "parameters": {"context": "测试", "options": ["A", "B"]}},
        {"tool_name": "system_monitor_real", "parameters": {"target": "system"}},
    ]

    batch_results = await manager.call_tool_batch(batch_calls)
    print(f"批量调用完成: {len(batch_results)}个")
    for i, r in enumerate(batch_results):
        print(f"  {i+1}. {r.tool_name}: {r.status.value}")

    # 获取监控仪表板
    print("\n📊 监控仪表板")
    dashboard = manager.get_monitoring_dashboard()
    print(f"活跃追踪: {dashboard['summary']['active_traces']}")
    print(f"已完成追踪: {dashboard['summary']['completed_traces']}")
    print(f"活跃告警: {dashboard['summary']['unresolved_alerts']}")

    # 获取工具性能
    print("\n📈 工具性能概览")
    performance = manager.get_all_tools_performance()
    for tool_name, perf in performance.items():
        print(f"  {tool_name}:")
        print(f"    调用次数: {perf['total_calls']}")
        print(f"    成功率: {perf['success_rate']:.1f}%")
        print(f"    平均延迟: {perf['avg_duration_ms']:.2f}ms")

    # 导出监控报告
    print("\n💾 导出监控报告")
    report_path = "logs/monitoring/test_report.json"
    manager.export_monitoring_report(report_path)

    print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(test_monitored_tool_call_manager())
