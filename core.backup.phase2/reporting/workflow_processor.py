#!/usr/bin/env python3
from __future__ import annotations
"""
混合工作流处理器 (Hybrid Workflow Processor)

实现Dolphin + NetworkX + Athena的完整混合工作流。
支持批量处理、并行任务、智能调度等功能。

Author: Athena工作平台
Date: 2026-01-16
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.reporting.unified_report_service import (
    ReportResult,
    ReportType,
    UnifiedReportService,
)

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """工作流状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowTask:
    """工作流任务"""

    task_id: str
    report_type: ReportType
    input_source: str
    output_dir: str | None = None
    custom_data: dict | None = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: ReportResult | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class WorkflowStatistics:
    """工作流统计"""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0


class HybridWorkflowProcessor:
    """
    混合工作流处理器

    功能:
    - 批量报告生成
    - 并行任务处理
    - 智能任务调度
    - 进度跟踪
    - 错误处理
    """

    def __init__(
        self,
        max_concurrent_tasks: int = 3,
        report_service: UnifiedReportService | None = None,
    ):
        """
        初始化工作流处理器

        Args:
            max_concurrent_tasks: 最大并发任务数
            report_service: 统一报告服务实例
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.report_service = report_service or UnifiedReportService()

        # 任务队列
        self.tasks: dict[str, WorkflowTask] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()

        # 统计信息
        self.statistics = WorkflowStatistics()

        # 信号量(控制并发数)
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)

        logger.info("🔄 混合工作流处理器初始化完成")
        logger.info(f"   最大并发任务数: {max_concurrent_tasks}")

    async def add_task(
        self,
        task_id: str,
        report_type: ReportType,
        input_source: str,
        output_dir: str | None = None,
        custom_data: dict | None = None,
    ) -> WorkflowTask:
        """
        添加任务到工作流

        Args:
            task_id: 任务ID
            report_type: 报告类型
            input_source: 输入源(文档路径或数据)
            output_dir: 输出目录
            custom_data: 自定义数据

        Returns:
            WorkflowTask: 工作流任务
        """
        task = WorkflowTask(
            task_id=task_id,
            report_type=report_type,
            input_source=input_source,
            output_dir=output_dir,
            custom_data=custom_data,
        )

        self.tasks[task_id] = task
        await self.task_queue.put(task)

        self.statistics.total_tasks += 1

        logger.info(f"📝 任务已添加: {task_id} ({report_type.value})")

        return task

    async def process_all(
        self,
        progress_callback: Callable[[str, WorkflowStatus, float], None] | None = None,
    ) -> WorkflowStatistics:
        """
        处理所有任务

        Args:
            progress_callback: 进度回调函数
                参数: (task_id, status, progress)

        Returns:
            WorkflowStatistics: 工作流统计
        """
        logger.info(f"🚀 开始处理 {self.statistics.total_tasks} 个任务")

        # 创建工作任务
        workers = [self._worker(progress_callback) for _ in range(self.max_concurrent_tasks)]

        # 等待所有任务完成
        await asyncio.gather(*workers)

        # 计算统计信息
        self._calculate_statistics()

        logger.info("✅ 所有任务处理完成")
        logger.info(f"   完成: {self.statistics.completed_tasks}/{self.statistics.total_tasks}")
        logger.info(f"   失败: {self.statistics.failed_tasks}/{self.statistics.total_tasks}")
        logger.info(f"   平均处理时间: {self.statistics.average_processing_time:.2f}秒")

        return self.statistics

    async def _worker(
        self,
        progress_callback: Callable[[str, WorkflowStatus, float], None] | None = None,
    ):
        """工作线程"""
        while True:
            try:
                # 从队列获取任务
                task = await self.task_queue.get()

                if task is None:  # 哨兵值,表示结束
                    break

                # 处理任务
                await self._process_task(task, progress_callback)

                # 标记任务完成
                self.task_queue.task_done()

            except Exception as e:
                logger.error(f"❌ 工作线程错误: {e}")

    async def _process_task(
        self,
        task: WorkflowTask,
        progress_callback: Callable[[str, WorkflowStatus, float], None] | None = None,
    ):
        """处理单个任务"""
        async with self.semaphore:  # 控制并发数
            try:
                # 更新状态
                task.status = WorkflowStatus.RUNNING
                task.started_at = datetime.now()

                if progress_callback:
                    progress_callback(task.task_id, task.status, 0.0)

                logger.info(f"⚙️  开始处理任务: {task.task_id}")

                # 判断任务类型
                if task.input_source.endswith((".pdf", ".png", ".jpg", ".jpeg")):
                    # 文档任务
                    result = await self.report_service.generate_from_document(
                        document_path=task.input_source,
                        report_type=task.report_type,
                        output_dir=task.output_dir,
                        custom_data=task.custom_data,
                    )
                else:
                    # 数据任务
                    result = await self.report_service.generate_from_data(
                        data=task.custom_data or {},
                        report_type=task.report_type,
                        output_dir=task.output_dir,
                    )

                # 更新结果
                task.result = result
                task.status = WorkflowStatus.COMPLETED
                task.completed_at = datetime.now()

                if progress_callback:
                    progress_callback(task.task_id, task.status, 1.0)

                self.statistics.completed_tasks += 1
                self.statistics.total_processing_time += result.processing_time_seconds

                logger.info(f"✅ 任务完成: {task.task_id} ({result.processing_time_seconds:.2f}秒)")

            except Exception as e:
                logger.error(f"❌ 任务失败: {task.task_id} - {e}")
                task.status = WorkflowStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()

                if progress_callback:
                    progress_callback(task.task_id, task.status, 0.0)

                self.statistics.failed_tasks += 1

    def _calculate_statistics(self) -> Any:
        """计算统计信息"""
        if self.statistics.completed_tasks > 0:
            self.statistics.average_processing_time = (
                self.statistics.total_processing_time / self.statistics.completed_tasks
            )

    def get_task_status(self, task_id: str) -> WorkflowTask | None:
        """获取任务状态"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> list[WorkflowTask]:
        """获取所有任务"""
        return list(self.tasks.values())

    def get_pending_tasks(self) -> list[WorkflowTask]:
        """获取待处理任务"""
        return [t for t in self.tasks.values() if t.status == WorkflowStatus.PENDING]

    def get_running_tasks(self) -> list[WorkflowTask]:
        """获取运行中任务"""
        return [t for t in self.tasks.values() if t.status == WorkflowStatus.RUNNING]

    def get_completed_tasks(self) -> list[WorkflowTask]:
        """获取已完成任务"""
        return [t for t in self.tasks.values() if t.status == WorkflowStatus.COMPLETED]

    def get_failed_tasks(self) -> list[WorkflowTask]:
        """获取失败任务"""
        return [t for t in self.tasks.values() if t.status == WorkflowStatus.FAILED]

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if task and task.status == WorkflowStatus.PENDING:
            task.status = WorkflowStatus.CANCELLED
            logger.info(f"🚫 任务已取消: {task_id}")
            return True
        return False

    async def retry_failed_tasks(
        self,
        progress_callback: Callable[[str, WorkflowStatus, float], None] | None = None,
    ) -> WorkflowStatistics:
        """重试失败的任务"""
        failed_tasks = self.get_failed_tasks()

        if not failed_tasks:
            logger.info("✅ 没有需要重试的任务")
            return self.statistics

        logger.info(f"🔄 重试 {len(failed_tasks)} 个失败任务")

        # 重置失败任务状态
        for task in failed_tasks:
            task.status = WorkflowStatus.PENDING
            task.error = None
            await self.task_queue.put(task)

        # 重新处理
        return await self.process_all(progress_callback)


# 便捷函数
async def batch_generate_reports(
    documents: list[str],
    report_type: ReportType = ReportType.PATENT_TECHNICAL_ANALYSIS,
    output_dir: str | None = None,
    max_concurrent: int = 3,
) -> list[ReportResult]:
    """
    批量生成报告

    Args:
        documents: 文档路径列表
        report_type: 报告类型
        output_dir: 输出目录
        max_concurrent: 最大并发数

    Returns:
        list[ReportResult]: 报告结果列表
    """
    processor = HybridWorkflowProcessor(max_concurrent_tasks=max_concurrent)

    # 添加所有任务
    for i, doc_path in enumerate(documents):
        await processor.add_task(
            task_id=f"batch_task_{i}",
            report_type=report_type,
            input_source=doc_path,
            output_dir=output_dir,
        )

    # 处理所有任务
    await processor.process_all()

    # 返回结果
    completed_tasks = processor.get_completed_tasks()
    return [task.result for task in completed_tasks if task.result]


async def batch_compare_documents(
    document_pairs: list[tuple],
    output_dir: str | None = None,
    max_concurrent: int = 2,
) -> list[ReportResult]:
    """
    批量对比文档

    Args:
        document_pairs: 文档对列表 [(doc1, doc2), (doc3, doc4), ...]
        output_dir: 输出目录
        max_concurrent: 最大并发数

    Returns:
        list[ReportResult]: 对比报告结果列表
    """
    HybridWorkflowProcessor(max_concurrent_tasks=max_concurrent)
    service = UnifiedReportService()

    # 添加所有对比任务
    for _i, (doc1, doc2) in enumerate(document_pairs):
        # 直接执行对比(使用服务的方法)
        await service.compare_documents(
            doc1_path=doc1,
            doc2_path=doc2,
            output_dir=output_dir,
        )

        logger.info(f"✅ 对比完成: {Path(doc1).name} vs {Path(doc2).name}")

    return []  # 实际实现应该返回结果列表
