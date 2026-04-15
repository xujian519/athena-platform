#!/usr/bin/env python3
"""
专利检索服务管理器
Patent Search Service Manager

统一管理Athena工作平台的所有专利检索服务，包括Google Patents、CNIPA、USPTO等

作者: Athena (智慧女神)
创建时间: 2025-12-07
版本: 1.0.0
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

# 导入Google Patents检索器
from google_patents_retriever import GooglePatentsRetriever, PatentData, PatentPriority

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatentSource(Enum):
    """专利数据源"""
    GOOGLE_PATENTS = 'google_patents'
    CNIPA = 'cnipa'
    USPTO = 'uspto'
    EPO = 'epo'
    WIPO = 'wipo'

class SearchStatus(Enum):
    """搜索状态"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

@dataclass
class SearchTask:
    """搜索任务"""
    task_id: str
    source: PatentSource
    query: str
    max_results: int
    status: SearchStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    results: list[PatentData] | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None

@dataclass
class ServiceStatus:
    """服务状态"""
    source: PatentSource
    available: bool
    last_check: datetime
    response_time: float | None = None
    error_count: int = 0
    success_count: int = 0

class PatentServiceManager:
    """专利检索服务管理器"""

    def __init__(self):
        self.google_patents_retriever: GooglePatentsRetriever | None = None
        self.search_tasks: dict[str, SearchTask] = {}
        self.service_status: dict[PatentSource, ServiceStatus] = {}
        self.concurrent_searches = 0
        self.max_concurrent = 3

    async def initialize(self):
        """初始化服务管理器"""
        logger.info('🚀 初始化专利检索服务管理器...')

        try:
            # 初始化Google Patents检索器
            config = {
                'headless': True,
                'use_browser_use': False,
                'use_playwright': True,
                'max_concurrent': self.max_concurrent,
                'request_delay': 2.0,
                'timeout': 30,
                'cache_enabled': True,
                'cache_ttl': 1800,
                'performance_mode': True
            }

            self.google_patents_retriever = GooglePatentsRetriever(config)
            await self.google_patents_retriever.initialize()

            # 初始化服务状态
            self.service_status[PatentSource.GOOGLE_PATENTS] = ServiceStatus(
                source=PatentSource.GOOGLE_PATENTS,
                available=True,
                last_check=datetime.now()
            )

            logger.info('✅ 专利检索服务管理器初始化成功')

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            raise

    async def close(self):
        """关闭服务管理器"""
        logger.info('🔒 关闭专利检索服务管理器...')

        if self.google_patents_retriever:
            await self.google_patents_retriever.close()

        logger.info('✅ 专利检索服务管理器已关闭')

    def generate_task_id(self, source: PatentSource, query: str) -> str:
        """生成任务ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        query_hash = abs(hash(query)) % 10000
        return f"{source.value}_{timestamp}_{query_hash}"

    async def search_patents(
        self,
        query: str,
        max_results: int = 20,
        source: PatentSource = PatentSource.GOOGLE_PATENTS,
        priority: PatentPriority = PatentPriority.MEDIUM,
        filters: dict[str, Any] | None = None
    ) -> str:
        """
        搜索专利

        Args:
            query: 搜索查询
            max_results: 最大结果数
            source: 数据源
            priority: 搜索优先级
            filters: 搜索筛选器

        Returns:
            task_id: 任务ID
        """
        if self.concurrent_searches >= self.max_concurrent:
            raise Exception(f"并发搜索数已达上限 ({self.max_concurrent})")

        # 检查服务可用性
        if not await self.check_service_availability(source):
            raise Exception(f"服务 {source.value} 不可用")

        # 创建搜索任务
        task_id = self.generate_task_id(source, query)
        task = SearchTask(
            task_id=task_id,
            source=source,
            query=query,
            max_results=max_results,
            status=SearchStatus.PENDING,
            created_at=datetime.now(),
            metadata={
                'priority': priority.value,
                'filters': filters or {}
            }
        )

        self.search_tasks[task_id] = task

        # 异步执行搜索
        asyncio.create_task(self._execute_search(task))

        return task_id

    async def _execute_search(self, task: SearchTask):
        """执行搜索任务"""
        try:
            self.concurrent_searches += 1
            task.status = SearchStatus.RUNNING
            task.started_at = datetime.now()

            logger.info(f"🔍 开始搜索: {task.task_id} - {task.query}")

            if task.source == PatentSource.GOOGLE_PATENTS and self.google_patents_retriever:
                result = await self.google_patents_retriever.search_patents(
                    query=task.query,
                    max_results=task.max_results,
                    filters=task.metadata.get('filters'),
                    priority=PatentPriority(task.metadata.get('priority', 'medium'))
                )

                if result['success']:
                    task.results = result['patents']
                    task.status = SearchStatus.COMPLETED

                    # 更新服务状态
                    status = self.service_status[task.source]
                    status.success_count += 1
                    status.last_check = datetime.now()

                    logger.info(f"✅ 搜索完成: {task.task_id} - 找到 {len(task.results)} 个专利")
                else:
                    task.error = result.get('error', '搜索失败')
                    task.status = SearchStatus.FAILED

                    # 更新服务状态
                    status = self.service_status[task.source]
                    status.error_count += 1

                    logger.error(f"❌ 搜索失败: {task.task_id} - {task.error}")
            else:
                raise Exception(f"不支持的数据源: {task.source}")

        except Exception as e:
            task.error = str(e)
            task.status = SearchStatus.FAILED
            logger.error(f"❌ 搜索异常: {task.task_id} - {e}")

        finally:
            task.completed_at = datetime.now()
            self.concurrent_searches -= 1

    async def batch_search_patents(
        self,
        queries: list[str],
        max_results_per_query: int = 10,
        source: PatentSource = PatentSource.GOOGLE_PATENTS,
        max_concurrent: int = 3
    ) -> list[str]:
        """
        批量搜索专利

        Args:
            queries: 查询列表
            max_results_per_query: 每个查询的最大结果数
            source: 数据源
            max_concurrent: 最大并发数

        Returns:
            task_ids: 任务ID列表
        """
        task_ids = []

        # 限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)

        async def search_with_semaphore(query: str) -> str:
            async with semaphore:
                return await self.search_patents(query, max_results_per_query, source)

        # 并发执行搜索
        tasks = [search_with_semaphore(query) for query in queries]
        task_ids = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常
        valid_task_ids = [tid for tid in task_ids if isinstance(tid, str)]

        return valid_task_ids

    async def get_search_status(self, task_id: str) -> dict[str, Any | None]:
        """获取搜索任务状态"""
        task = self.search_tasks.get(task_id)
        if not task:
            return None

        return {
            'task_id': task.task_id,
            'source': task.source.value,
            'query': task.query,
            'status': task.status.value,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'result_count': len(task.results) if task.results else 0,
            'error': task.error,
            'metadata': task.metadata
        }

    async def get_search_results(self, task_id: str) -> dict[str, Any | None]:
        """获取搜索结果"""
        task = self.search_tasks.get(task_id)
        if not task:
            return None

        if task.status != SearchStatus.COMPLETED:
            return {
                'task_id': task_id,
                'status': task.status.value,
                'message': '搜索尚未完成'
            }

        # 转换PatentData对象为字典
        results_dicts = []
        for patent in task.results:
            if hasattr(patent, '__dict__'):
                results_dicts.append(patent.__dict__)
            else:
                results_dicts.append(asdict(patent))

        return {
            'task_id': task_id,
            'status': task.status.value,
            'query': task.query,
            'source': task.source.value,
            'total_found': len(results_dicts),
            'patents': results_dicts,
            'search_time': task.completed_at.isoformat() if task.completed_at else None,
            'duration': (task.completed_at - task.started_at).total_seconds() if task.completed_at and task.started_at else None
        }

    async def cancel_search(self, task_id: str) -> bool:
        """取消搜索任务"""
        task = self.search_tasks.get(task_id)
        if not task:
            return False

        if task.status in [SearchStatus.COMPLETED, SearchStatus.FAILED, SearchStatus.CANCELLED]:
            return False

        task.status = SearchStatus.CANCELLED
        task.completed_at = datetime.now()

        logger.info(f"⏹️ 搜索已取消: {task_id}")
        return True

    async def list_search_tasks(
        self,
        status: SearchStatus | None = None,
        source: PatentSource | None = None,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """列出搜索任务"""
        tasks = list(self.search_tasks.values())

        # 过滤条件
        if status:
            tasks = [t for t in tasks if t.status == status]
        if source:
            tasks = [t for t in tasks if t.source == source]

        # 按创建时间倒序排列
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # 限制数量
        tasks = tasks[:limit]

        # 转换为字典格式
        return [await self.get_search_status(t.task_id) for t in tasks if t.task_id]

    async def cleanup_old_tasks(self, max_age_days: int = 7):
        """清理旧任务"""
        cutoff_time = datetime.now() - timedelta(days=max_age_days)

        old_task_ids = [
            task_id for task_id, task in self.search_tasks.items()
            if task.created_at < cutoff_time and task.status in [SearchStatus.COMPLETED, SearchStatus.FAILED, SearchStatus.CANCELLED]
        ]

        for task_id in old_task_ids:
            del self.search_tasks[task_id]

        logger.info(f"🧹 清理了 {len(old_task_ids)} 个旧任务")

    async def check_service_availability(self, source: PatentSource) -> bool:
        """检查服务可用性"""
        if source == PatentSource.GOOGLE_PATENTS:
            return self.google_patents_retriever is not None

        # 其他数据源的检查可以在这里添加
        return False

    async def get_service_statistics(self) -> dict[str, Any]:
        """获取服务统计信息"""
        stats = {
            'services': {},
            'tasks': {
                'total': len(self.search_tasks),
                'pending': 0,
                'running': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0
            },
            'performance': {
                'concurrent_searches': self.concurrent_searches,
                'max_concurrent': self.max_concurrent,
                'utilization': (self.concurrent_searches / self.max_concurrent) * 100
            }
        }

        # 服务状态
        for source, status in self.service_status.items():
            stats['services'][source.value] = {
                'available': status.available,
                'last_check': status.last_check.isoformat(),
                'success_count': status.success_count,
                'error_count': status.error_count,
                'success_rate': (
                    status.success_count / (status.success_count + status.error_count) * 100
                    if (status.success_count + status.error_count) > 0 else 0
                )
            }

        # 任务状态统计
        for task in self.search_tasks.values():
            stats['tasks'][task.status.value] += 1

        # 添加Google Patents检索器统计
        if self.google_patents_retriever:
            try:
                retriever_stats = await self.google_patents_retriever.get_statistics()
                stats['google_patents'] = retriever_stats
            except Exception as e:
                logger.warning(f"获取Google Patents统计失败: {e}")

        return stats

# 全局服务管理器实例
patent_service_manager: PatentServiceManager | None = None

async def get_patent_service_manager() -> PatentServiceManager:
    """获取专利服务管理器实例"""
    global patent_service_manager

    if patent_service_manager is None:
        patent_service_manager = PatentServiceManager()
        await patent_service_manager.initialize()

    return patent_service_manager

async def cleanup_patent_service_manager():
    """清理专利服务管理器"""
    global patent_service_manager

    if patent_service_manager:
        await patent_service_manager.close()
        patent_service_manager = None

if __name__ == '__main__':
    # 测试代码
    async def main():
        manager = PatentServiceManager()
        await manager.initialize()

        try:
            # 测试搜索
            task_id = await manager.search_patents('machine learning', max_results=5)
            logger.info(f"搜索任务已创建: {task_id}")

            # 等待完成
            await asyncio.sleep(15)

            # 获取结果
            status = await manager.get_search_status(task_id)
            logger.info(f"任务状态: {status}")

            if status['status'] == 'completed':
                results = await manager.get_search_results(task_id)
                logger.info(f"找到 {results['total_found']} 个专利")

            # 获取统计
            stats = await manager.get_service_statistics()
            logger.info(f"服务统计: {json.dumps(stats, indent=2)}")

        finally:
            await manager.close()

    asyncio.run(main())
