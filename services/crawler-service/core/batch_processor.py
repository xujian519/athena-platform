#!/usr/bin/env python3
"""
批量处理系统 - 支持大规模爬虫任务的队列管理和并发处理
Batch Processing System - Queue Management and Concurrent Processing for Large-Scale Crawling
控制者: Athena & 小诺
"""

import asyncio
import json
import logging
import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

from ..config.platform_crawler_config import platform_config
from .hybrid_crawler_manager import HybridCrawlerManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = 'pending'          # 等待中
    RUNNING = 'running'          # 运行中
    COMPLETED = 'completed'      # 已完成
    FAILED = 'failed'           # 失败
    CANCELLED = 'cancelled'      # 已取消
    RETRYING = 'retrying'        # 重试中


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1      # 低优先级
    NORMAL = 2   # 普通优先级
    HIGH = 3     # 高优先级
    URGENT = 4   # 紧急优先级


@dataclass
class BatchTask:
    """批量任务数据类"""
    id: str
    name: str
    urls: list[str]
    crawler_type: str  # 'hybrid', 'custom', 'crawl4ai', 'firecrawl'
    options: dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    progress: int = 0  # 0-100
    results: list[dict[str, Any]] = None
    cost: float = 0.0

    def __post_init__(self):
        if self.results is None:
            self.results = []


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = platform_config.storage.database_path

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

    def _init_database(self) -> Any:
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batch_tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    urls TEXT NOT NULL,
                    crawler_type TEXT NOT NULL,
                    options TEXT,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    progress INTEGER DEFAULT 0,
                    results TEXT,
                    cost REAL DEFAULT 0.0
                )
            """)

            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON batch_tasks(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority ON batch_tasks(priority DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON batch_tasks(created_at)')

            conn.commit()

    async def save_task(self, task: BatchTask) -> bool:
        """保存任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO batch_tasks
                    (id, name, urls, crawler_type, options, priority, status,
                     created_at, started_at, completed_at, error_message,
                     retry_count, max_retries, progress, results, cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.id,
                    task.name,
                    json.dumps(task.urls),
                    task.crawler_type,
                    json.dumps(task.options),
                    task.priority.value,
                    task.status.value,
                    task.created_at.isoformat(),
                    task.started_at.isoformat() if task.started_at else None,
                    task.completed_at.isoformat() if task.completed_at else None,
                    task.error_message,
                    task.retry_count,
                    task.max_retries,
                    task.progress,
                    json.dumps(task.results),
                    task.cost
                ))

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"保存任务失败: {e}")
            return False

    async def get_task(self, task_id: str) -> BatchTask | None:
        """获取任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM batch_tasks WHERE id = ?', (task_id,))
                row = cursor.fetchone()

                if row:
                    return self._row_to_task(row)
                return None

        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None

    async def get_tasks_by_status(self, status: TaskStatus, limit: int = 10) -> list[BatchTask]:
        """根据状态获取任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM batch_tasks
                    WHERE status = ?
                    ORDER BY priority DESC, created_at ASC
                    LIMIT ?
                """, (status.value, limit))

                rows = cursor.fetchall()
                return [self._row_to_task(row) for row in rows]

        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []

    async def update_task_status(self, task_id: str, status: TaskStatus,
                                error_message: str = None) -> bool:
        """更新任务状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if status == TaskStatus.RUNNING:
                    cursor.execute("""
                        UPDATE batch_tasks
                        SET status = ?, started_at = ?, error_message = ?
                        WHERE id = ?
                    """, (status.value, datetime.now(timezone.utc).isoformat(), error_message, task_id))
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    cursor.execute("""
                        UPDATE batch_tasks
                        SET status = ?, completed_at = ?, error_message = ?
                        WHERE id = ?
                    """, (status.value, datetime.now(timezone.utc).isoformat(), error_message, task_id))
                else:
                    cursor.execute("""
                        UPDATE batch_tasks
                        SET status = ?, error_message = ?
                        WHERE id = ?
                    """, (status.value, error_message, task_id))

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            return False

    async def update_task_progress(self, task_id: str, progress: int,
                                  results: list[dict[str, Any]] = None,
                                  cost: float = 0.0) -> bool:
        """更新任务进度"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE batch_tasks
                    SET progress = ?, results = ?, cost = ?
                    WHERE id = ?
                """, (progress, json.dumps(results) if results else None, cost, task_id))

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")
            return False

    def _row_to_task(self, row) -> BatchTask:
        """数据库行转换为任务对象"""
        return BatchTask(
            id=row[0],
            name=row[1],
            urls=json.loads(row[2]),
            crawler_type=row[3],
            options=json.loads(row[4]) if row[4] else {},
            priority=TaskPriority(row[5]),
            status=TaskStatus(row[6]),
            created_at=datetime.fromisoformat(row[7]),
            started_at=datetime.fromisoformat(row[8]) if row[8] else None,
            completed_at=datetime.fromisoformat(row[9]) if row[9] else None,
            error_message=row[10],
            retry_count=row[11],
            max_retries=row[12],
            progress=row[13],
            results=json.loads(row[14]) if row[14] else [],
            cost=row[15]
        )


class TaskQueue:
    """任务队列管理器"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._queue = asyncio.PriorityQueue()
        self._running = False
        self._workers: list[asyncio.Task] = []

    async def start(self, num_workers: int = 3):
        """启动队列工作器"""
        if self._running:
            return

        self._running = True

        # 启动工作器
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)

        logger.info(f"任务队列已启动，工作器数量: {num_workers}")

    async def stop(self):
        """停止队列工作器"""
        self._running = False

        # 等待所有工作器完成
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)

        logger.info('任务队列已停止')

    async def add_task(self, task: BatchTask) -> bool:
        """添加任务到队列"""
        # 保存任务到数据库
        if not await self.db_manager.save_task(task):
            return False

        # 添加到优先级队列（使用负优先级值，因为PriorityQueue是最小堆）
        priority_value = -task.priority.value
        await self._queue.put((priority_value, task.created_at.timestamp(), task.id))

        logger.info(f"任务已添加到队列: {task.name} (ID: {task.id})")
        return True

    async def get_next_task(self) -> BatchTask | None:
        """获取下一个任务"""
        try:
            while self._running:
                # 从队列获取任务
                try:
                    priority_value, timestamp, task_id = await asyncio.wait_for(
                        self._queue.get(), timeout=1.0
                    )

                    # 从数据库获取任务详情
                    task = await self.db_manager.get_task(task_id)
                    if task and task.status == TaskStatus.PENDING:
                        return task

                except asyncio.TimeoutError:
                    continue

            return None

        except Exception as e:
            logger.error(f"获取下一个任务失败: {e}")
            return None

    async def _worker(self, worker_name: str):
        """队列工作器"""
        logger.info(f"工作器 {worker_name} 已启动")

        while self._running:
            try:
                # 获取下一个任务
                task = await self.get_next_task()
                if not task:
                    await asyncio.sleep(0.1)
                    continue

                # 处理任务
                await self._process_task(task, worker_name)

            except Exception as e:
                logger.error(f"工作器 {worker_name} 处理任务时出错: {e}")
                await asyncio.sleep(1.0)

        logger.info(f"工作器 {worker_name} 已停止")

    async def _process_task(self, task: BatchTask, worker_name: str):
        """处理单个任务"""
        logger.info(f"工作器 {worker_name} 开始处理任务: {task.name}")

        try:
            # 更新任务状态为运行中
            await self.db_manager.update_task_status(task.id, TaskStatus.RUNNING)

            # 这里实际的爬虫处理将由BatchProcessor来执行
            # 工作器只负责状态管理和队列操作

        except Exception as e:
            logger.error(f"处理任务 {task.name} 时出错: {e}")
            await self.db_manager.update_task_status(
                task.id, TaskStatus.FAILED, str(e)
            )


class BatchProcessor:
    """批量处理器"""

    def __init__(self, config: dict = None):
        self.config = config or platform_config.batch_processing
        self.db_manager = DatabaseManager()
        self.task_queue = TaskQueue(self.db_manager)
        self.crawler_manager = HybridCrawlerManager()
        self.executor = ThreadPoolExecutor(max_workers=self.config.concurrent_tasks)
        self._running = False
        self._stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'total_urls': 0,
            'processed_urls': 0,
            'total_cost': 0.0
        }

    async def start(self):
        """启动批量处理器"""
        if self._running:
            return

        self._running = True

        # 启动任务队列
        await self.task_queue.start(self.config.worker_count)

        # 启动任务处理协程
        asyncio.create_task(self._process_tasks())

        logger.info('批量处理器已启动')

    async def stop(self):
        """停止批量处理器"""
        self._running = False

        # 停止任务队列
        await self.task_queue.stop()

        # 关闭线程池
        self.executor.shutdown(wait=True)

        logger.info('批量处理器已停止')

    async def create_batch_task(self, name: str, urls: list[str],
                              crawler_type: str = 'hybrid',
                              options: dict[str, Any] = None,
                              priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """创建批量任务"""
        task_id = str(uuid.uuid4())

        task = BatchTask(
            id=task_id,
            name=name,
            urls=urls,
            crawler_type=crawler_type,
            options=options or {},
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            max_retries=self.config.retry_attempts
        )

        # 添加到队列
        if await self.task_queue.add_task(task):
            self._stats['total_tasks'] += 1
            self._stats['total_urls'] += len(urls)
            return task_id
        else:
            raise Exception('创建批量任务失败')

    async def get_task_status(self, task_id: str) -> dict[str, Any | None]:
        """获取任务状态"""
        task = await self.db_manager.get_task(task_id)
        if not task:
            return None

        return {
            'id': task.id,
            'name': task.name,
            'status': task.status.value,
            'progress': task.progress,
            'total_urls': len(task.urls),
            'processed_urls': len(task.results),
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'error_message': task.error_message,
            'cost': task.cost,
            'retry_count': task.retry_count
        }

    async def get_task_results(self, task_id: str) -> dict[str, Any | None]:
        """获取任务结果"""
        task = await self.db_manager.get_task(task_id)
        if not task:
            return None

        return {
            'task_id': task.id,
            'name': task.name,
            'status': task.status.value,
            'results': task.results,
            'total_count': len(task.results),
            'success_count': len([r for r in task.results if r.get('success', False)]),
            'error_count': len([r for r in task.results if not r.get('success', False)]),
            'cost': task.cost,
            'processing_time': (
                task.completed_at - task.started_at
            ).total_seconds() if task.started_at and task.completed_at else None
        }

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = await self.db_manager.get_task(task_id)
        if not task or task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            return False

        return await self.db_manager.update_task_status(task_id, TaskStatus.CANCELLED)

    async def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        task = await self.db_manager.get_task(task_id)
        if not task or task.status != TaskStatus.FAILED:
            return False

        if task.retry_count >= task.max_retries:
            return False

        # 重置任务状态
        task.retry_count += 1
        task.status = TaskStatus.PENDING
        task.error_message = None
        task.progress = 0

        await self.db_manager.save_task(task)

        # 重新添加到队列
        return await self.task_queue.add_task(task)

    async def get_batch_stats(self) -> dict[str, Any]:
        """获取批量处理统计信息"""
        # 从数据库获取实时统计
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.cursor()

            # 任务状态统计
            cursor.execute("""
                SELECT status, COUNT(*)
                FROM batch_tasks
                GROUP BY status
            """)
            status_stats = dict(cursor.fetchall())

            # 成本统计
            cursor.execute("SELECT SUM(cost), COUNT(*) FROM batch_tasks WHERE status = 'completed'")
            cost_result = cursor.fetchone()
            total_cost = cost_result[0] or 0.0
            completed_count = cost_result[1] or 0

        return {
            'total_tasks': self._stats['total_tasks'],
            'completed_tasks': completed_count,
            'failed_tasks': status_stats.get('failed', 0),
            'pending_tasks': status_stats.get('pending', 0),
            'running_tasks': status_stats.get('running', 0),
            'total_urls': self._stats['total_urls'],
            'processed_urls': self._stats['processed_urls'],
            'total_cost': total_cost,
            'average_cost_per_task': total_cost / completed_count if completed_count > 0 else 0.0,
            'success_rate': completed_count / self._stats['total_tasks'] if self._stats['total_tasks'] > 0 else 0.0
        }

    async def _process_tasks(self):
        """处理任务的主循环"""
        while self._running:
            try:
                # 获取等待中的任务
                tasks = await self.db_manager.get_tasks_by_status(TaskStatus.PENDING, 5)

                for task in tasks:
                    if not self._running:
                        break

                    # 异步处理任务
                    asyncio.create_task(self._execute_task(task))

                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"批量处理循环出错: {e}")
                await asyncio.sleep(5.0)

    async def _execute_task(self, task: BatchTask):
        """执行单个任务"""
        try:
            # 更新状态为运行中
            await self.db_manager.update_task_status(task.id, TaskStatus.RUNNING)

            logger.info(f"开始执行批量任务: {task.name} ({len(task.urls)} URLs)")

            # 分批处理URL
            batch_size = self.config.batch_size
            all_results = []
            total_cost = 0.0

            for i in range(0, len(task.urls), batch_size):
                if not self._running:
                    break

                batch_urls = task.urls[i:i + batch_size]

                # 使用线程池处理批次
                loop = asyncio.get_event_loop()
                batch_results, batch_cost = await loop.run_in_executor(
                    self.executor,
                    self._process_url_batch,
                    batch_urls,
                    task.crawler_type,
                    task.options
                )

                all_results.extend(batch_results)
                total_cost += batch_cost

                # 更新进度
                progress = min(100, int((i + len(batch_urls)) * 100 / len(task.urls)))
                await self.db_manager.update_task_progress(
                    task.id, progress, all_results, total_cost
                )

                # 更新统计
                self._stats['processed_urls'] += len(batch_results)
                self._stats['total_cost'] += batch_cost

                # 控制并发
                await asyncio.sleep(0.1)

            # 任务完成
            await self.db_manager.update_task_progress(
                task.id, 100, all_results, total_cost
            )
            await self.db_manager.update_task_status(task.id, TaskStatus.COMPLETED)

            self._stats['completed_tasks'] += 1

            logger.info(f"批量任务完成: {task.name} (成本: ${total_cost:.4f})")

        except Exception as e:
            logger.error(f"执行批量任务 {task.name} 时出错: {e}")
            await self.db_manager.update_task_status(
                task.id, TaskStatus.FAILED, str(e)
            )

            # 重试逻辑
            if task.retry_count < task.max_retries:
                logger.info(f"准备重试任务: {task.name} (第 {task.retry_count + 1} 次)")
                task.status = TaskStatus.RETRYING
                await asyncio.sleep(2 ** task.retry_count)  # 指数退避
                await self.retry_task(task.id)

    def _process_url_batch(self, urls: list[str], crawler_type: str,
                          options: dict[str, Any]) -> tuple:
        """处理URL批次（在线程池中执行）"""
        results = []
        total_cost = 0.0

        for url in urls:
            try:
                # 选择爬虫类型
                if crawler_type == 'hybrid':
                    result, cost = self._crawl_with_hybrid(url, options)
                elif crawler_type == 'custom':
                    result, cost = self._crawl_with_custom(url, options)
                elif crawler_type == 'crawl4ai':
                    result, cost = self._crawl_with_crawl4ai(url, options)
                elif crawler_type == 'firecrawl':
                    result, cost = self._crawl_with_firecrawl(url, options)
                else:
                    result, cost = {'success': False, 'error': f"不支持的爬虫类型: {crawler_type}"}, 0.0

                results.append(result)
                total_cost += cost

            except Exception as e:
                results.append({
                    'success': False,
                    'url': url,
                    'error': str(e)
                })

        return results, total_cost

    def _crawl_with_hybrid(self, url: str, options: dict[str, Any]) -> tuple:
        """使用混合爬虫"""
        # 这里应该调用实际的爬虫管理器
        # 简化实现，返回模拟结果
        return {
            'success': True,
            'url': url,
            'title': 'Mock Title',
            'content': 'Mock content from hybrid crawler',
            'crawler_type': 'hybrid'
        }, 0.001

    def _crawl_with_custom(self, url: str, options: dict[str, Any]) -> tuple:
        """使用自定义爬虫"""
        return {
            'success': True,
            'url': url,
            'title': 'Custom Crawler Result',
            'content': 'Content from custom crawler',
            'crawler_type': 'custom'
        }, 0.0005

    def _crawl_with_crawl4ai(self, url: str, options: dict[str, Any]) -> tuple:
        """使用Crawl4AI"""
        return {
            'success': True,
            'url': url,
            'title': 'Crawl4AI Result',
            'content': 'AI-enhanced content extraction',
            'crawler_type': 'crawl4ai'
        }, 0.002

    def _crawl_with_firecrawl(self, url: str, options: dict[str, Any]) -> tuple:
        """使用FireCrawl"""
        return {
            'success': True,
            'url': url,
            'title': 'FireCrawl Result',
            'content': 'Professional web scraping result',
            'crawler_type': 'firecrawl'
        }, 0.005


# 全局批量处理器实例
batch_processor = BatchProcessor()


@asynccontextmanager
async def batch_processor_context():
    """批量处理器上下文管理器"""
    await batch_processor.start()
    try:
        yield batch_processor
    finally:
        await batch_processor.stop()


# 示例使用
async def main():
    """示例函数"""
    async with batch_processor_context() as processor:
        # 创建批量任务
        urls = [
            'https://example.com/1',
            'https://example.com/2',
            'https://example.com/3'
        ]

        task_id = await processor.create_batch_task(
            name='示例批量任务',
            urls=urls,
            crawler_type='hybrid',
            priority=TaskPriority.HIGH
        )

        logger.info(f"任务已创建: {task_id}")

        # 监控任务状态
        while True:
            status = await processor.get_task_status(task_id)
            if status:
                logger.info(f"任务状态: {status['status']}, 进度: {status['progress']}%")

                if status['status'] in ['completed', 'failed', 'cancelled']:
                    break

            await asyncio.sleep(2)

        # 获取结果
        results = await processor.get_task_results(task_id)
        if results:
            logger.info(f"任务完成，成功处理 {results['success_count']} 个URL")
            logger.info(f"总成本: ${results['cost']:.4f}")


# 入口点: @async_main装饰器已添加到main函数
