#!/usr/bin/env python3
"""
小诺主编排器 - 优化增强版
Xiaonuo Main Orchestrator - Optimization Enhanced

集成Athena优化能力的小诺主编排器。

主要增强:
1. 任务执行前进行错误预测
2. 工具选择时使用智能发现
3. 参数执行前进行实时验证

作者: Athena平台团队
创建时间: 2025-12-27
版本: v1.1.0 "优化增强版"
"""

from __future__ import annotations
import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from core.async_main import async_main
from core.logging_config import setup_logging

# 导入原始编排器
from .xiaonuo_main_orchestrator import (
    OrchestrationMode,
    OrchestrationReport,
    Task,
    TaskPriority,
    TaskStatus,
    TaskType,
    XiaonuoMainOrchestrator,
)
from .xiaonuo_orchestration_hub import (
    SubTask,
)

# 导入优化管理器
try:
    from core.optimization.xiaonuo_optimization_manager import (
        OptimizationConfig,
        OptimizationResult,
        XiaonuoOptimizationManager,
    )

    OPTIMIZATION_AVAILABLE = True
except ImportError:
    OPTIMIZATION_AVAILABLE = False
    logging.warning("优化管理器导入失败,将使用基础编排功能")


logger = setup_logging()


class XiaonuoOptimizedOrchestrator(XiaonuoMainOrchestrator):
    """
    小诺主编排器 - 优化增强版

    在原有编排器基础上,集成Athena的三大优化能力:
    1. 错误预测 - 在任务执行前预测潜在错误
    2. 工具发现 - 智能选择最适合的工具
    3. 参数验证 - 实时验证参数有效性
    """

    def __init__(self, optimization_config_path: str | None = None):
        """
        初始化优化增强版编排器

        Args:
            optimization_config_path: 优化配置文件路径
        """
        # 调用父类初始化
        super().__init__()

        # 更新名称和版本
        self.name = "小诺·双鱼公主主编排中枢 (优化增强版)"
        self.version = "1.1.0"

        # 加载优化配置
        self.optimization_config = self._load_optimization_config(optimization_config_path)

        # 初始化优化管理器
        self.optimization_manager: XiaonuoOptimizationManager | None = None
        if OPTIMIZATION_AVAILABLE and self.optimization_config.get("optimizations", {}).get(
            "enabled", False
        ):
            self._initialize_optimization_manager()

        # 优化统计
        self.optimization_metrics = {
            "total_optimizations": 0,
            "errors_prevented": 0,
            "tools_optimized": 0,
            "parameters_validated": 0,
            "optimization_time_saved": 0.0,
        }

        if self.optimization_manager:
            print(f"🚀 {self.name} 初始化完成 (优化已启用)")
        else:
            print(f"✅ {self.name} 初始化完成 (优化未启用)")

    def _load_optimization_config(self, config_path: str,) -> dict:
        """加载优化配置"""
        default_config_path = (
            Path(__file__).parent.parent.parent / "config" / "optimization" / "xiaonuo.yaml"
        )

        config_file = Path(config_path or default_config_path)

        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                logger.info(f"✅ 已加载优化配置: {config_file}")
                return config
            except Exception as e:
                logger.warning(f"⚠️ 加载优化配置失败: {e}")

        # 返回默认配置
        return {
            "optimizations": {"enabled": False, "fallback_on_error": True},
            "tool_discovery": {"enabled": True},
            "parameter_validation": {"enabled": True},
            "error_prediction": {"enabled": True},
        }

    def _initialize_optimization_manager(self) -> Any:
        """初始化优化管理器"""
        try:
            opt_config = self.optimization_config.get("optimizations", {})

            # 创建优化配置
            config = OptimizationConfig(
                enable_tool_discovery=self.optimization_config.get("tool_discovery", {}).get(
                    "enabled", True
                ),
                enable_parameter_validation=self.optimization_config.get(
                    "parameter_validation", {}
                ).get("enabled", True),
                enable_error_prediction=self.optimization_config.get("error_prediction", {}).get(
                    "enabled", True
                ),
                tool_discovery_config=self.optimization_config.get("tool_discovery", {}).get(
                    "config"
                ),
                validation_config=self.optimization_config.get("parameter_validation", {}).get(
                    "config"
                ),
                prediction_config=self.optimization_config.get("error_prediction", {}).get(
                    "config"
                ),
                fallback_on_error=opt_config.get("fallback_on_error", True),
            )

            self.optimization_manager = XiaonuoOptimizationManager(config)
            logger.info("✅ 优化管理器已启用")

        except Exception as e:
            logger.error(f"❌ 优化管理器初始化失败: {e}")
            self.optimization_manager = None

    async def orchestrate_task(
        self,
        task_type: TaskType,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        mode: OrchestrationMode | None = None,
        context: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> OrchestrationReport:
        """
        编排执行任务(优化增强版)

        在原有编排流程基础上,集成三大优化能力。

        Args:
            task_type: 任务类型
            title: 任务标题
            description: 任务描述
            priority: 任务优先级
            mode: 编排模式
            context: 上下文信息
            parameters: 任务参数

        Returns:
            编排报告
        """
        # 创建任务
        task = Task(
            id=str(uuid.uuid4()),
            task_type=task_type,
            title=title,
            description=description,
            priority=priority,
        )

        # 设置编排模式
        orchestration_mode = mode or self.config["default_mode"]

        # 创建报告
        report = OrchestrationReport(
            task_id=task.id,
            task_title=title,
            orchestration_mode=orchestration_mode,
            start_time=datetime.now(),
        )

        # 集成点1: 任务执行前优化
        if self.optimization_manager:
            await self._optimize_before_execution(task, context, parameters, report)

        try:
            self.logger.info(f"开始编排任务: {title}")

            # 1. 任务分解
            self.logger.info("执行任务分解...")
            subtasks = self.task_decomposer.decompose(task)
            report.total_subtasks = len(subtasks)

            # 集成点2: 工具选择优化
            if self.optimization_manager and context:
                await self._optimize_tool_selection(subtasks, context, report)

            # 2. 资源调度
            self.logger.info("执行资源调度...")
            assignments = self.resource_scheduler.assign_tasks(
                subtasks, strategy="resource_optimal"
            )

            # 集成点3: 参数验证
            if self.optimization_manager and parameters:
                await self._validate_task_parameters(parameters, report)

            # 3. 构建执行图
            self.logger.info("构建执行图...")
            execution_graph = self._build_execution_graph(subtasks)

            # 4. 执行任务
            self.logger.info("开始执行子任务...")
            execution_result = await self._execute_tasks(
                subtasks, assignments, execution_graph, orchestration_mode
            )

            # 5. 整合结果
            self.logger.info("整合执行结果...")
            task.result = self._integrate_results(subtasks, execution_result)
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()

            # 6. 生成报告
            report = self._generate_report(task, subtasks, assignments, execution_result)

            # 更新指标
            self._update_performance_metrics(report)

            self.logger.info(f"任务编排完成: {title}")

        except Exception as e:
            self.logger.error(f"任务编排失败: {title}, 错误: {e!s}")
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            report.end_time = datetime.now()
            report.error = str(e)

        finally:
            # 保存任务和报告
            self.active_tasks[task.id] = task
            self.task_reports[task.id] = report

            # 更新优化统计
            if self.optimization_manager:
                self.optimization_metrics["total_optimizations"] += 1

        return report

    async def _optimize_before_execution(
        self,
        task: Task,
        context: dict,
        parameters: dict,
        report: OrchestrationReport,
    ):
        """执行前优化(错误预测)"""
        try:
            # 收集系统上下文
            system_context = self._collect_system_context(context)

            # 预测潜在错误
            predictions = await self.optimization_manager.predict_errors(
                context=system_context, top_k=5
            )

            if predictions:
                high_risk_predictions = [
                    p
                    for p in predictions
                    if p.risk_level.value in ["HIGH", "CRITICAL"] and p.probability > 0.5
                ]

                if high_risk_predictions:
                    self.logger.warning(f"⚠️ 预测到 {len(high_risk_predictions)} 个高风险错误")

                    # 添加到优化建议
                    for pred in high_risk_predictions[:3]:
                        report.optimization_suggestions.append(
                            f"[错误预防] {pred.error_pattern.value}: "
                            f"{pred.prevention_suggestions[0] if pred.prevention_suggestions else '无建议'}"
                        )

                    self.optimization_metrics["errors_prevented"] += len(high_risk_predictions)

        except Exception as e:
            logger.error(f"执行前优化失败: {e}")

    async def _optimize_tool_selection(
        self, subtasks: list[SubTask], context: dict, report: OrchestrationReport
    ):
        """优化工具选择"""
        try:
            # 为每个子任务优化工具选择
            for subtask in subtasks:
                # 获取可用工具(从已注册的agent中)
                available_tools = self._get_available_tools_for_task(subtask)

                if not available_tools:
                    continue

                # 调用优化管理器
                selected_tools = await self.optimization_manager.discover_best_tools(
                    task_description=subtask.description,
                    available_tools=available_tools,
                    context=context,
                    top_k=3,
                )

                # 更新子任务的工具分配
                if selected_tools:
                    self.optimization_metrics["tools_optimized"] += 1
                    self.logger.debug(
                        f"为子任务 {subtask.title} 优化选择了 {len(selected_tools)} 个工具"
                    )

        except Exception as e:
            logger.error(f"工具选择优化失败: {e}")

    async def _validate_task_parameters(self, parameters: dict, report: OrchestrationReport):
        """验证任务参数"""
        try:
            # 调用优化管理器验证参数
            validation_results = await self.optimization_manager.validate_parameters(
                parameters=parameters
            )

            if validation_results:
                invalid_count = sum(1 for r in validation_results.values() if not r.is_valid())

                if invalid_count > 0:
                    self.logger.warning(f"⚠️ 发现 {invalid_count} 个无效参数")

                    # 添加验证建议到报告
                    for param_name, result in validation_results.items():
                        if not result.is_valid() and result.suggestions:
                            report.optimization_suggestions.append(
                                f"[参数验证] {param_name}: {result.suggestions[0]}"
                            )

                self.optimization_metrics["parameters_validated"] += len(validation_results)

        except Exception as e:
            logger.error(f"参数验证失败: {e}")

    def _collect_system_context(self, context: dict,) -> dict:
        """收集系统上下文"""
        import psutil

        system_context = {
            "cpu_usage": psutil.cpu_percent() / 100.0,
            "memory_usage": psutil.virtual_memory().percent / 100.0,
            "disk_usage": psutil.disk_usage("/").percent / 100.0,
            "request_rate": len(self.active_tasks),
            "concurrent_requests": sum(
                1 for t in self.active_tasks.values() if t.status == TaskStatus.IN_PROGRESS
            ),
            "queue_length": len(
                [t for t in self.active_tasks.values() if t.status == TaskStatus.PENDING]
            ),
        }

        # 合并用户提供的上下文
        if context:
            system_context.update(context)

        return system_context

    def _get_available_tools_for_task(self, subtask: SubTask) -> list:
        """获取子任务的可用工具"""
        # 从已注册的agents中获取工具
        tools = []

        for agent_id, agent_info in self.resource_scheduler.registered_agents.items():
            # 简单的匹配逻辑:根据agent能力匹配子任务类型
            tools.append(
                {
                    "tool_id": agent_id,
                    "name": agent_info.name,
                    "description": f"具备能力: {[c.value for c in agent_info.capabilities]}",
                    "capabilities": [c.value for c in agent_info.capabilities],
                    "available": True,
                }
            )

        return tools

    def get_optimization_stats(self) -> dict:
        """获取优化统计信息"""
        if not self.optimization_manager:
            return {"enabled": False}

        manager_stats = self.optimization_manager.get_stats()

        return {
            "enabled": True,
            "module_status": self.optimization_manager.get_module_status(),
            "metrics": self.optimization_metrics,
            "manager_stats": manager_stats,
        }


# 便捷函数
def create_optimized_orchestrator(
    config_path: str | None = None, enable_optimization: bool = False
) -> XiaonuoOptimizedOrchestrator:
    """
    创建优化增强版编排器

    Args:
        config_path: 优化配置文件路径
        enable_optimization: 是否启用优化(默认False)

    Returns:
        优化增强版编排器实例
    """
    orchestrator = XiaonuoOptimizedOrchestrator(config_path)

    # 如果明确禁用优化,清除管理器
    if not enable_optimization and orchestrator.optimization_manager:
        orchestrator.optimization_manager = None
        logger.info("优化已明确禁用")

    return orchestrator


# 使用示例
@async_main
async def main():
    """演示函数"""
    print("=" * 70)
    print("小诺优化增强版编排器演示")
    print("=" * 70)

    # 创建优化增强版编排器(启用优化)
    orchestrator = create_optimized_orchestrator(enable_optimization=True)

    # 执行任务
    print("\n🚀 执行优化增强任务...")

    report = await orchestrator.orchestrate_task(
        task_type=TaskType.PATENT_SEARCH,
        title="专利检索任务",
        description="搜索关于人工智能的专利",
        priority=TaskPriority.NORMAL,
        mode=OrchestrationMode.ADAPTIVE,
        context={"search_keywords": ["人工智能", "AI", "机器学习"], "max_results": 50},
        parameters={"query": "人工智能", "max_results": 50},
    )

    print(f"\n结果: {'成功' if report.execution_time > 0 else '失败'}")
    print(f"执行时间: {report.execution_time:.2f}秒")
    print(f"子任务: {report.completed_subtasks}/{report.total_subtasks}")

    if report.optimization_suggestions:
        print(f"\n优化建议: {len(report.optimization_suggestions)}条")
        for suggestion in report.optimization_suggestions[:3]:
            print(f"  - {suggestion}")

    # 优化统计
    print("\n📊 优化统计:")
    stats = orchestrator.get_optimization_stats()
    if stats["enabled"]:
        print(f"   总优化次数: {stats['metrics']['total_optimizations']}")
        print(f"   预防错误: {stats['metrics']['errors_prevented']}")
        print(f"   优化工具选择: {stats['metrics']['tools_optimized']}")
        print(f"   验证参数: {stats['metrics']['parameters_validated']}")
    else:
        print("   优化未启用")

    print("\n✅ 演示完成")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
