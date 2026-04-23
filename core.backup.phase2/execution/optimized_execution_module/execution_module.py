#!/usr/bin/env python3
from __future__ import annotations
"""
优化版执行模块 - 主执行模块
Optimized Execution Module - Main Execution Module

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import inspect
import json
import logging
import multiprocessing
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

import psutil

from core.base_module import BaseModule
from core.logging_config import setup_logging

# 尝试导入现有的执行系统
try:
    from core.execution.execution_engine import ExecutionEngine

    EXECUTION_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"无法导入现有执行系统: {e}")
    EXECUTION_SYSTEM_AVAILABLE = False

from .load_balancer import LoadBalancer
from .resource_monitor import ResourceMonitor
from .scheduler import IntelligentScheduler
from .types import Task, TaskPriority, TaskStatus

logger = setup_logging()


class OptimizedExecutionModule(BaseModule):
    """优化版执行模块 - 集成智能调度、资源监控和负载均衡"""

    def __init__(self, agent_id: str, config: dict[str, Any] | None = None):
        """初始化优化版执行模块

        Args:
            agent_id: 智能体ID
            config: 配置字典
        """
        super().__init__(agent_id, config)

        # 优化配置
        self.optimization_config = {
            "intelligent_scheduling": True,
            "dynamic_resource_allocation": True,
            "load_balancing": True,
            "parallel_processing": True,
            "resource_monitoring": True,
            "auto_scaling": True,
            **self.config,
        }

        # 初始化优化组件
        if self.optimization_config["intelligent_scheduling"]:
            self.scheduler = IntelligentScheduler(self.optimization_config)

        if self.optimization_config["load_balancing"]:
            self.load_balancer = LoadBalancer(self.optimization_config)

        if self.optimization_config["resource_monitoring"]:
            self.resource_monitor = ResourceMonitor()

        # 现有执行系统集成
        self.execution_engine = None
        self.fallback_enabled = True

        if EXECUTION_SYSTEM_AVAILABLE:
            try:
                self.execution_engine = ExecutionEngine(self.agent_id)
                logger.info("✅ 现有执行引擎集成成功")
            except Exception as e:
                logger.warning(f"现有执行引擎集成失败: {e}")

        # 统计信息
        self.optimization_stats = {
            "total_submitted_tasks": 0,
            "total_completed_tasks": 0,
            "total_failed_tasks": 0,
            "average_waiting_time": 0.0,
            "average_execution_time": 0.0,
            "resource_utilization": 0.0,
            "scheduling_efficiency": 0.0,
            "load_balance_score": 0.0,
        }

        logger.info("⚡ 优化版执行模块初始化完成")

    async def _on_initialize(self) -> bool:
        """初始化优化执行模块

        Returns:
            是否初始化成功
        """
        try:
            logger.info("⚡ 初始化优化执行模块...")

            # 添加本地工作节点到负载均衡器
            if hasattr(self, "load_balancer"):
                self.load_balancer.add_worker_node(
                    {
                        "node_id": f"{self.agent_id}_local",
                        "cpu_cores": multiprocessing.cpu_count(),
                        "memory_mb": psutil.virtual_memory().total // (1024 * 1024),
                    }
                )

            logger.info("✅ 优化执行模块初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化执行模块初始化失败: {e!s}")
            return False

    async def _on_start(self) -> bool:
        """启动优化执行模块

        Returns:
            是否启动成功
        """
        try:
            logger.info("🚀 启动优化执行模块")

            # 启动后台任务
            if self.optimization_config.get("auto_scaling", True):
                asyncio.create_task(self._auto_scaling_loop())

            if hasattr(self, "load_balancer"):
                asyncio.create_task(self._health_check_loop())

            logger.info("✅ 优化执行模块启动成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化执行模块启动失败: {e!s}")
            return False

    async def _on_stop(self) -> bool:
        """停止优化执行模块

        Returns:
            是否停止成功
        """
        try:
            logger.info("⏹️ 停止优化执行模块")
            logger.info("✅ 优化执行模块停止成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化执行模块停止失败: {e!s}")
            return False

    async def _on_shutdown(self) -> bool:
        """关闭优化执行模块

        Returns:
            是否关闭成功
        """
        try:
            logger.info("🔚 关闭优化执行模块")

            # 停止资源监控
            if hasattr(self, "resource_monitor"):
                self.resource_monitor.stop()

            # 关闭线程池和进程池
            if hasattr(self, "scheduler"):
                self.scheduler.thread_pool.shutdown(wait=True)
                self.scheduler.process_pool.shutdown(wait=True)

            # 生成优化报告
            self._generate_optimization_report()

            logger.info("✅ 优化执行模块关闭成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化执行模块关闭失败: {e!s}")
            return False

    async def _on_health_check(self) -> bool:
        """健康检查

        Returns:
            是否健康
        """
        try:
            checks = {
                "scheduler_available": hasattr(self, "scheduler")
                or not self.optimization_config["intelligent_scheduling"],
                "load_balancer_available": hasattr(self, "load_balancer")
                or not self.optimization_config["load_balancing"],
                "resource_monitor_available": hasattr(self, "resource_monitor")
                or not self.optimization_config["resource_monitoring"],
                "execution_engine_available": self.execution_engine is not None
                or self.fallback_enabled,
                "parallel_processing_enabled": self.optimization_config["parallel_processing"],
                "auto_scaling_enabled": self.optimization_config["auto_scaling"],
            }

            overall_healthy = (
                checks["scheduler_available"]
                and checks["load_balancer_available"]
                and checks["resource_monitor_available"]
                and checks["execution_engine_available"]
            )

            # 存储健康检查详情
            self._health_check_details = {
                "scheduler_status": "available" if checks["scheduler_available"] else "unavailable",
                "load_balancer_status": (
                    "available" if checks["load_balancer_available"] else "unavailable"
                ),
                "resource_monitor_status": (
                    "available" if checks["resource_monitor_available"] else "unavailable"
                ),
                "execution_engine_status": (
                    "available" if checks["execution_engine_available"] else "unavailable"
                ),
                "optimization_stats": self.optimization_stats,
                "overall_healthy": overall_healthy,
            }

            return overall_healthy

        except Exception as e:
            logger.error(f"健康检查失败: {e!s}")
            return False

    async def submit_task_optimized(
        self,
        name: str,
        function: Callable,
        priority: TaskPriority = TaskPriority.NORMAL,
        args: tuple = (),
        kwargs: dict | None = None,
        dependencies: list[str] | None = None,
        timeout: float | None = None,
        max_retries: int = 3,
        estimated_cpu: float = 0.1,
        estimated_memory: float = 0.1,
        tags: list[str] | None = None,
    ) -> str:
        """优化任务提交

        Args:
            name: 任务名称
            function: 要执行的函数
            priority: 任务优先级
            args: 位置参数
            kwargs: 关键字参数
            dependencies: 依赖任务ID列表
            timeout: 超时时间(秒)
            max_retries: 最大重试次数
            estimated_cpu: 预估CPU使用率
            estimated_memory: 预估内存使用率
            tags: 任务标签

        Returns:
            任务ID,如果提交失败则返回空字符串
        """
        start_time = time.time()

        try:
            task_id = str(uuid.uuid4())

            task = Task(
                task_id=task_id,
                name=name,
                priority=priority,
                function=function,
                args=args,
                kwargs=kwargs or {},
                dependencies=dependencies or [],
                timeout=timeout,
                max_retries=max_retries,
                estimated_cpu_usage=estimated_cpu,
                estimated_memory_usage=estimated_memory,
                tags=tags or [],
            )

            # 提交到调度器
            if hasattr(self, "scheduler"):
                success = await self.scheduler.submit_task(task)
            else:
                # 回退到直接执行
                success = await self._fallback_execute(task)

            # 更新统计
            if success:
                self.optimization_stats["total_submitted_tasks"] += 1

                waiting_time = time.time() - start_time
                current_avg = self.optimization_stats["average_waiting_time"]
                total_tasks = self.optimization_stats["total_submitted_tasks"]
                new_avg = (current_avg * (total_tasks - 1) + waiting_time) / total_tasks
                self.optimization_stats["average_waiting_time"] = new_avg

            logger.debug(f"✅ 任务提交成功: {task_id}")
            return task_id if success else ""

        except Exception as e:
            logger.error(f"❌ 任务提交失败: {e}")
            return ""

    async def _fallback_execute(self, task: Task) -> bool:
        """回退执行机制

        Args:
            task: 要执行的任务

        Returns:
            是否执行成功
        """
        try:
            # 简化的直接执行
            if inspect.iscoroutinefunction(task.function):
                result = await task.function(*task.args, **task.kwargs)
            else:
                result = task.function(*task.args, **task.kwargs)

            task.result = result
            task.status = TaskStatus.COMPLETED
            self.optimization_stats["total_completed_tasks"] += 1
            return True

        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            self.optimization_stats["total_failed_tasks"] += 1
            return False

    async def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息,如果未找到则返回None
        """
        if hasattr(self, "scheduler"):
            return self.scheduler.get_task_status(task_id)
        return None

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 要取消的任务ID

        Returns:
            是否成功取消
        """
        if hasattr(self, "scheduler"):
            return await self.scheduler.cancel_task(task_id)
        return False

    async def _auto_scaling_loop(self):
        """自动扩缩容循环"""
        logger.info("🔄 启动自动扩缩容循环")

        while True:
            try:
                # 每30秒检查一次
                await asyncio.sleep(30)

                # 获取当前负载
                if hasattr(self, "scheduler") and hasattr(self, "resource_monitor"):
                    scheduler_stats = self.scheduler.get_scheduler_stats()
                    current_load = scheduler_stats["resource_utilization"]["cpu"]

                    # 自动扩缩容逻辑
                    if current_load > 0.8:  # 80%负载,考虑扩容
                        await self._scale_up()
                    elif current_load < 0.3:  # 30%负载,考虑缩容
                        await self._scale_down()

            except Exception as e:
                logger.error(f"自动扩缩容循环异常: {e}")
                await asyncio.sleep(60)  # 出错后等待

    async def _scale_up(self):
        """扩容"""
        logger.info("📈 执行扩容操作")
        # 这里实现具体的扩容逻辑
        pass

    async def _scale_down(self):
        """缩容"""
        logger.info("📉 执行缩容操作")
        # 这里实现具体的缩容逻辑
        pass

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                # 执行负载均衡器健康检查
                if hasattr(self, "load_balancer"):
                    await self.load_balancer.health_check()

                await asyncio.sleep(self.load_balancer.health_check_interval)

            except Exception as e:
                logger.error(f"健康检查循环异常: {e}")
                await asyncio.sleep(60)

    def _generate_optimization_report(self) -> Any:
        """生成优化报告

        Returns:
            优化报告字典
        """
        try:
            report = {
                "execution_summary": {
                    "total_submitted_tasks": self.optimization_stats["total_submitted_tasks"],
                    "total_completed_tasks": self.optimization_stats["total_completed_tasks"],
                    "total_failed_tasks": self.optimization_stats["total_failed_tasks"],
                    "average_waiting_time": self.optimization_stats["average_waiting_time"],
                    "average_execution_time": self.optimization_stats["average_execution_time"],
                    "resource_utilization": self.optimization_stats["resource_utilization"],
                },
                "scheduler_statistics": {},
                "load_balancer_statistics": {},
                "configuration": self.optimization_config,
            }

            if hasattr(self, "scheduler"):
                report["scheduler_statistics"] = self.scheduler.get_scheduler_stats()

            if hasattr(self, "load_balancer"):
                report["load_balancer_statistics"] = {
                    "total_nodes": len(self.load_balancer.worker_nodes),
                    "healthy_nodes": len(
                        [n for n in self.load_balancer.worker_nodes if n["healthy"]]
                    ),
                    "load_balance_strategy": self.load_balancer.strategy,
                }

            # 保存报告
            report_path = f"execution_optimization_report_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"📊 执行模块优化报告已生成: {report_path}")
            return report

        except Exception as e:
            logger.error(f"生成优化报告失败: {e}")
            return {}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """标准处理接口

        Args:
            data: 包含operation和参数的字典

        Returns:
            处理结果字典
        """
        operation = data.get("operation", "submit_task")

        if operation == "submit_task":
            name = data.get("name", "unnamed_task")
            function = data.get("function")
            priority = TaskPriority(data.get("priority", TaskPriority.NORMAL.value))
            args = data.get("args", ())
            kwargs = data.get("kwargs", {})
            dependencies = data.get("dependencies", [])
            timeout = data.get("timeout")
            max_retries = data.get("max_retries", 3)
            estimated_cpu = data.get("estimated_cpu", 0.1)
            estimated_memory = data.get("estimated_memory", 0.1)
            tags = data.get("tags", [])

            if function:
                task_id = await self.submit_task_optimized(
                    name=name,
                    function=function,
                    priority=priority,
                    args=args,
                    kwargs=kwargs,
                    dependencies=dependencies,
                    timeout=timeout,
                    max_retries=max_retries,
                    estimated_cpu=estimated_cpu,
                    estimated_memory=estimated_memory,
                    tags=tags,
                )
                return {"success": bool(task_id), "task_id": task_id}

        elif operation == "get_task_status":
            task_id = data.get("task_id")
            if task_id:
                status = await self.get_task_status(task_id)
                return {"success": status is not None, "task_id": task_id, "status": status}

        elif operation == "cancel_task":
            task_id = data.get("task_id")
            if task_id:
                success = await self.cancel_task(task_id)
                return {"success": success, "task_id": task_id}

        # 其他操作的默认处理
        return await super().process(data)

    def get_optimization_stats(self) -> dict[str, Any]:
        """获取优化统计信息

        Returns:
            包含优化统计信息的字典
        """
        stats = {"module_stats": self.optimization_stats, "configuration": self.optimization_config}

        if hasattr(self, "scheduler"):
            stats["scheduler_statistics"] = self.scheduler.get_scheduler_stats()

        if hasattr(self, "load_balancer"):
            stats["load_balancer_statistics"] = {
                "total_nodes": len(self.load_balancer.worker_nodes),
                "healthy_nodes": len([n for n in self.load_balancer.worker_nodes if n["healthy"]]),
                "load_balance_strategy": self.load_balancer.strategy,
            }

        if hasattr(self, "resource_monitor"):
            current_usage = self.resource_monitor.get_current_usage()
            stats["resource_usage"] = {
                "cpu_cores": current_usage.cpu_cores,
                "memory_mb": current_usage.memory_mb,
                "disk_io_mb_s": current_usage.disk_io_mb_s,
                "network_mbps": current_usage.network_mbps,
            }

        return stats
