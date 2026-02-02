#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量操作管理器
Batch Operations Manager

支持批量文件上传、下载、处理和分析等操作
"""

import asyncio
from core.async_main import async_main
import uuid
import time
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

class BatchOperationStatus(Enum):
    """批量操作状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BatchOperation:
    """批量操作数据结构"""
    operation_id: str
    operation_type: str  # upload, download, process, analyze, delete
    user_id: str
    files: List[Dict[str, Any]]
    status: BatchOperationStatus
    progress: float = 0.0
    total_files: int = 0
    processed_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    error_message: str | None = None
    results: List[Dict[str, Any]] = None
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.results is None:
            self.results = []
        if self.config is None:
            self.config = {}

class BatchOperationManager:
    """批量操作管理器"""

    def __init__(self, max_concurrent_operations: int = 10, max_workers: int = 4):
        self.max_concurrent_operations = max_concurrent_operations
        self.max_workers = max_workers
        self.operations: Dict[str, BatchOperation] = {}
        self.active_operations: Dict[str, asyncio.Task] = {}
        self.operation_queue: asyncio.Queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent_operations)
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        self.worker_task = None
        self.progress_callbacks: Dict[str, List[Callable]] = {}

    async def start(self):
        """启动批量操作管理器"""
        if self.running:
            return

        self.running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        logger.info("批量操作管理器已启动")

    async def stop(self):
        """停止批量操作管理器"""
        self.running = False

        # 取消所有活动任务
        for task in self.active_operations.values():
            task.cancel()

        # 等待工作线程结束
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                logger.error(f"Error: {e}", exc_info=True)

        # 关闭线程池
        self.thread_pool.shutdown(wait=True)

        logger.info("批量操作管理器已停止")

    async def _worker_loop(self):
        """工作循环"""
        while self.running:
            try:
                # 获取待处理的操作
                operation_id = await self.operation_queue.get()
                if operation_id not in self.operations:
                    continue

                operation = self.operations[operation_id]

                # 检查是否已取消
                if operation.status == BatchOperationStatus.CANCELLED:
                    continue

                # 执行操作
                async with self.semaphore:
                    task = asyncio.create_task(
                        self._execute_operation(operation_id),
                        name=f"batch_operation_{operation_id}"
                    )
                    self.active_operations[operation_id] = task

                    try:
                        await task
                    except Exception as e:
                        logger.error(f"批量操作 {operation_id} 执行失败: {e}")
                        operation.status = BatchOperationStatus.FAILED
                        operation.error_message = str(e)
                        operation.completed_at = datetime.now()
                    finally:
                        self.active_operations.pop(operation_id, None)

                self.operation_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作循环异常: {e}")
                await asyncio.sleep(1)

    async def create_batch_operation(self, operation_type: str, user_id: str,
                                   files: List[Dict[str, Any]],
                                   config: Dict[str, Any] = None) -> str:
        """创建批量操作"""
        operation_id = str(uuid.uuid4())

        operation = BatchOperation(
            operation_id=operation_id,
            operation_type=operation_type,
            user_id=user_id,
            files=files,
            status=BatchOperationStatus.PENDING,
            total_files=len(files),
            config=config or {}
        )

        self.operations[operation_id] = operation

        # 添加到队列
        await self.operation_queue.put(operation_id)

        logger.info(f"创建批量操作: {operation_id} - {operation_type} ({len(files)} 个文件)")

        return operation_id

    async def _execute_operation(self, operation_id: str):
        """执行批量操作"""
        operation = self.operations[operation_id]
        operation.status = BatchOperationStatus.RUNNING
        operation.started_at = datetime.now()

        try:
            # 根据操作类型执行相应的方法
            if operation.operation_type == "upload":
                await self._execute_batch_upload(operation)
            elif operation.operation_type == "download":
                await self._execute_batch_download(operation)
            elif operation.operation_type == "process":
                await self._execute_batch_process(operation)
            elif operation.operation_type == "analyze":
                await self._execute_batch_analyze(operation)
            elif operation.operation_type == "delete":
                await self._execute_batch_delete(operation)
            else:
                raise ValueError(f"不支持的操作类型: {operation.operation_type}")

            # 更新状态
            if operation.failed_files > 0 and operation.successful_files == 0:
                operation.status = BatchOperationStatus.FAILED
                operation.error_message = "所有文件操作失败"
            elif operation.failed_files > 0:
                operation.status = BatchOperationStatus.COMPLETED  # 部分成功
            else:
                operation.status = BatchOperationStatus.COMPLETED

            operation.completed_at = datetime.now()
            logger.info(f"批量操作 {operation_id} 完成: 成功 {operation.successful_files}, 失败 {operation.failed_files}")

        except Exception as e:
            operation.status = BatchOperationStatus.FAILED
            operation.error_message = str(e)
            operation.completed_at = datetime.now()
            logger.error(f"批量操作 {operation_id} 失败: {e}")

        finally:
            # 通知进度回调
            await self._notify_progress_callbacks(operation_id, operation)

    async def _execute_batch_upload(self, operation: BatchOperation):
        """执行批量上传"""
        from ..secure_multimodal_api import secure_storage
        from ..security.auth_manager import UserInfo

        for i, file_info in enumerate(operation.files):
            # 检查是否已取消
            if operation.status == BatchOperationStatus.CANCELLED:
                break

            try:
                # 创建用户信息
                user_info = UserInfo(
                    user_id=operation.user_id,
                    role="user",
                    name="批量上传用户"
                )

                # 执行上传
                result = await secure_storage.save_file_secure(
                    file_content=file_info.get("content", b""),
                    filename=file_info.get("filename", ""),
                    user_info=user_info,
                    metadata=file_info.get("metadata", {})
                )

                operation.results.append({
                    "file_index": i,
                    "filename": file_info.get("filename", ""),
                    "success": True,
                    "result": result
                })
                operation.successful_files += 1

            except Exception as e:
                logger.error(f"文件上传失败 {file_info.get('filename', '')}: {e}")
                operation.results.append({
                    "file_index": i,
                    "filename": file_info.get("filename", ""),
                    "success": False,
                    "error": str(e)
                })
                operation.failed_files += 1

            # 更新进度
            operation.processed_files += 1
            operation.progress = operation.processed_files / operation.total_files * 100

            # 通知进度
            await self._notify_progress_callbacks(operation.operation_id, operation)

            # 短暂休息，避免过度占用资源
            await asyncio.sleep(0.1)

    async def _execute_batch_download(self, operation: BatchOperation):
        """执行批量下载"""
        # 这里需要根据实际的存储实现来编写
        for i, file_info in enumerate(operation.files):
            if operation.status == BatchOperationStatus.CANCELLED:
                break

            try:
                file_id = file_info.get("file_id")
                if not file_id:
                    raise ValueError("缺少文件ID")

                # 模拟下载过程
                await asyncio.sleep(0.5)  # 模拟下载时间

                operation.results.append({
                    "file_index": i,
                    "file_id": file_id,
                    "success": True,
                    "download_path": f"/downloads/{file_id}"
                })
                operation.successful_files += 1

            except Exception as e:
                operation.results.append({
                    "file_index": i,
                    "file_id": file_info.get("file_id", ""),
                    "success": False,
                    "error": str(e)
                })
                operation.failed_files += 1

            operation.processed_files += 1
            operation.progress = operation.processed_files / operation.total_files * 100
            await self._notify_progress_callbacks(operation.operation_id, operation)

    async def _execute_batch_process(self, operation: BatchOperation):
        """执行批量处理"""
        # 实现批量处理逻辑（如缩略图生成、格式转换等）
        for i, file_info in enumerate(operation.files):
            if operation.status == BatchOperationStatus.CANCELLED:
                break

            try:
                # 模拟处理过程
                await asyncio.sleep(1.0)  # 模拟处理时间

                operation.results.append({
                    "file_index": i,
                    "file_id": file_info.get("file_id", ""),
                    "success": True,
                    "processed_path": f"/processed/{file_info.get('file_id', '')}"
                })
                operation.successful_files += 1

            except Exception as e:
                operation.results.append({
                    "file_index": i,
                    "file_id": file_info.get("file_id", ""),
                    "success": False,
                    "error": str(e)
                })
                operation.failed_files += 1

            operation.processed_files += 1
            operation.progress = operation.processed_files / operation.total_files * 100
            await self._notify_progress_callbacks(operation.operation_id, operation)

    async def _execute_batch_analyze(self, operation: BatchOperation):
        """执行批量分析"""
        # 实现批量分析逻辑（如AI分析、内容识别等）
        for i, file_info in enumerate(operation.files):
            if operation.status == BatchOperationStatus.CANCELLED:
                break

            try:
                # 模拟分析过程
                await asyncio.sleep(2.0)  # 模拟分析时间

                operation.results.append({
                    "file_index": i,
                    "file_id": file_info.get("file_id", ""),
                    "success": True,
                    "analysis_result": {
                        "content_type": "image",
                        "tags": ["tag1", "tag2"],
                        "confidence": 0.95
                    }
                })
                operation.successful_files += 1

            except Exception as e:
                operation.results.append({
                    "file_index": i,
                    "file_id": file_info.get("file_id", ""),
                    "success": False,
                    "error": str(e)
                })
                operation.failed_files += 1

            operation.processed_files += 1
            operation.progress = operation.processed_files / operation.total_files * 100
            await self._notify_progress_callbacks(operation.operation_id, operation)

    async def _execute_batch_delete(self, operation: BatchOperation):
        """执行批量删除"""
        # 实现批量删除逻辑
        for i, file_info in enumerate(operation.files):
            if operation.status == BatchOperationStatus.CANCELLED:
                break

            try:
                file_id = file_info.get("file_id")
                if not file_id:
                    raise ValueError("缺少文件ID")

                # 模拟删除过程
                await asyncio.sleep(0.3)

                operation.results.append({
                    "file_index": i,
                    "file_id": file_id,
                    "success": True,
                    "deleted": True
                })
                operation.successful_files += 1

            except Exception as e:
                operation.results.append({
                    "file_index": i,
                    "file_id": file_info.get("file_id", ""),
                    "success": False,
                    "error": str(e)
                })
                operation.failed_files += 1

            operation.processed_files += 1
            operation.progress = operation.processed_files / operation.total_files * 100
            await self._notify_progress_callbacks(operation.operation_id, operation)

    async def cancel_operation(self, operation_id: str) -> bool:
        """取消批量操作"""
        if operation_id not in self.operations:
            return False

        operation = self.operations[operation_id]

        # 如果还未开始，直接标记为取消
        if operation.status == BatchOperationStatus.PENDING:
            operation.status = BatchOperationStatus.CANCELLED
            operation.completed_at = datetime.now()
            return True

        # 如果正在运行，取消任务
        if operation.status == BatchOperationStatus.RUNNING:
            operation.status = BatchOperationStatus.CANCELLED
            task = self.active_operations.get(operation_id)
            if task:
                task.cancel()
            return True

        return False

    def get_operation_status(self, operation_id: str) -> BatchOperation | None:
        """获取操作状态"""
        return self.operations.get(operation_id)

    def get_user_operations(self, user_id: str, status: BatchOperationStatus | None = None) -> List[BatchOperation]:
        """获取用户的操作列表"""
        operations = [
            op for op in self.operations.values()
            if op.user_id == user_id
        ]

        if status:
            operations = [op for op in operations if op.status == status]

        # 按创建时间倒序排列
        operations.sort(key=lambda x: x.created_at, reverse=True)
        return operations

    async def add_progress_callback(self, operation_id: str, callback: Callable):
        """添加进度回调"""
        if operation_id not in self.progress_callbacks:
            self.progress_callbacks[operation_id] = []
        self.progress_callbacks[operation_id].append(callback)

    async def _notify_progress_callbacks(self, operation_id: str, operation: BatchOperation):
        """通知进度回调"""
        callbacks = self.progress_callbacks.get(operation_id, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(operation)
                else:
                    callback(operation)
            except Exception as e:
                logger.error(f"进度回调执行失败: {e}")

    def cleanup_old_operations(self, days: int = 7) -> Any:
        """清理旧操作记录"""
        cutoff_time = datetime.now() - timedelta(days=days)
        old_operations = [
            op_id for op_id, op in self.operations.items()
            if op.created_at < cutoff_time and op.status in [
                BatchOperationStatus.COMPLETED,
                BatchOperationStatus.FAILED,
                BatchOperationStatus.CANCELLED
            ]
        ]

        for op_id in old_operations:
            del self.operations[op_id]
            self.progress_callbacks.pop(op_id, None)

        logger.info(f"清理了 {len(old_operations)} 个旧操作记录")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_operations = len(self.operations)
        active_operations = len(self.active_operations)
        pending_operations = len([
            op for op in self.operations.values()
            if op.status == BatchOperationStatus.PENDING
        ])

        # 按状态统计
        status_counts = {}
        for status in BatchOperationStatus:
            status_counts[status.value] = len([
                op for op in self.operations.values()
                if op.status == status
            ])

        # 按类型统计
        type_counts = {}
        for op in self.operations.values():
            type_counts[op.operation_type] = type_counts.get(op.operation_type, 0) + 1

        return {
            "total_operations": total_operations,
            "active_operations": active_operations,
            "pending_operations": pending_operations,
            "queue_length": self.operation_queue.qsize(),
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "max_concurrent_operations": self.max_concurrent_operations,
            "max_workers": self.max_workers
        }

# 全局批量操作管理器实例
batch_operation_manager = BatchOperationManager()

# 使用示例
async def example_usage():
    """使用示例"""
    # 启动管理器
    await batch_operation_manager.start()

    # 创建批量上传操作
    files = [
        {"filename": "test1.jpg", "content": b"fake image content 1"},
        {"filename": "test2.jpg", "content": b"fake image content 2"},
        {"filename": "test3.pdf", "content": b"fake pdf content"}
    ]

    operation_id = await batch_operation_manager.create_batch_operation(
        operation_type="upload",
        user_id="user123",
        files=files
    )

    # 添加进度回调
    async def progress_callback(operation: BatchOperation):
        print(f"操作 {operation.operation_id} 进度: {operation.progress:.1f}%")

    await batch_operation_manager.add_progress_callback(operation_id, progress_callback)

    # 等待完成
    while True:
        operation = batch_operation_manager.get_operation_status(operation_id)
        if operation and operation.status in [
            BatchOperationStatus.COMPLETED,
            BatchOperationStatus.FAILED,
            BatchOperationStatus.CANCELLED
        ]:
            break
        await asyncio.sleep(1)

    print("操作完成:", asdict(operation))

    # 停止管理器
    await batch_operation_manager.stop()

if __name__ == "__main__":
    asyncio.run(example_usage())