#!/usr/bin/env python3
"""
分布式爬虫架构 - 多节点协同爬取系统
Distributed Crawler Architecture - Multi-node Collaborative Crawling System

实现任务分发、负载均衡、结果聚合和故障转移

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import asyncio
import logging
import random
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# 导入相关模块

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [DistributedCrawler] %(message)s',
    handlers=[
        logging.FileHandler(f"distributed_crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class NodeStatus(Enum):
    """节点状态"""
    ACTIVE = 'active'
    BUSY = 'busy'
    IDLE = 'idle'
    FAILED = 'failed'
    OFFLINE = 'offline'

@dataclass
class CrawlTask:
    """爬取任务"""
    task_id: str
    url: str
    method: str = 'GET'
    data: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    retries: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    assigned_node: str | None = None
    result: dict | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

@dataclass
class WorkerNode:
    """工作节点"""
    node_id: str
    host: str
    port: int
    status: NodeStatus = NodeStatus.IDLE
    last_heartbeat: datetime = field(default_factory=datetime.now)
    current_tasks: list[str] = field(default_factory=list)
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_response_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    capabilities: list[str] = field(default_factory=list)

    @property
    def is_available(self) -> bool:
        """节点是否可用"""
        return (self.status in [NodeStatus.IDLE, NodeStatus.ACTIVE] and
                len(self.current_tasks) < 10 and
                time.time() - self.last_heartbeat.timestamp() < 60)

    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.completed_tasks + self.failed_tasks
        return (self.completed_tasks / total * 100) if total > 0 else 0.0

class TaskQueue:
    """任务队列"""

    def __init__(self):
        self.priority_queues = defaultdict(deque)  # 按优先级分组的队列
        self.task_dict = {}  # 任务ID到任务的映射
        self.lock = threading.Lock()

    def add_task(self, task: CrawlTask):
        """添加任务"""
        with self.lock:
            self.priority_queues[task.priority].append(task.task_id)
            self.task_dict[task.task_id] = task

    def get_next_task(self) -> CrawlTask | None:
        """获取下一个任务（按优先级）"""
        with self.lock:
            # 按优先级从高到低查找
            for priority in sorted(self.priority_queues.keys(), reverse=True):
                queue = self.priority_queues[priority]
                if queue:
                    task_id = queue.popleft()
                    if task_id in self.task_dict:
                        task = self.task_dict[task_id]
                        task.status = TaskStatus.RUNNING
                        task.started_at = datetime.now()
                        return task
                    else:
                        # 任务已被删除
                        continue
            return None

    def get_task(self, task_id: str) -> CrawlTask | None:
        """获取指定任务"""
        with self.lock:
            return self.task_dict.get(task_id)

    def update_task(self, task_id: str, **kwargs):
        """更新任务"""
        with self.lock:
            if task_id in self.task_dict:
                task = self.task_dict[task_id]
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)

    def complete_task(self, task_id: str, result: dict = None, error: str = None):
        """完成任务"""
        with self.lock:
            if task_id in self.task_dict:
                task = self.task_dict[task_id]
                task.status = TaskStatus.COMPLETED if result else TaskStatus.FAILED
                task.completed_at = datetime.now()
                task.result = result
                task.error = error
                return task
            return None

    def get_pending_tasks(self) -> list[CrawlTask]:
        """获取所有待处理任务"""
        with self.lock:
            return [task for task in self.task_dict.values()
                   if task.status == TaskStatus.PENDING]

    def get_running_tasks(self) -> list[CrawlTask]:
        """获取所有运行中任务"""
        with self.lock:
            return [task for task in self.task_dict.values()
                   if task.status == TaskStatus.RUNNING]

    def get_stats(self) -> dict[str, Any]:
        """获取队列统计"""
        with self.lock:
            status_counts = defaultdict(int)
            for task in self.task_dict.values():
                status_counts[task.status.value] += 1

            return {
                'total_tasks': len(self.task_dict),
                'pending_tasks': status_counts[TaskStatus.PENDING.value],
                'running_tasks': status_counts[TaskStatus.RUNNING.value],
                'completed_tasks': status_counts[TaskStatus.COMPLETED.value],
                'failed_tasks': status_counts[TaskStatus.FAILED.value],
                'priority_distribution': {
                    str(priority): len(queue)
                    for priority, queue in self.priority_queues.items()
                }
            }

class LoadBalancer:
    """负载均衡器"""

    def __init__(self):
        self.nodes: dict[str, WorkerNode] = {}
        self.lock = threading.Lock()

    def add_node(self, node: WorkerNode):
        """添加节点"""
        with self.lock:
            self.nodes[node.node_id] = node
            logger.info(f"➕ 添加工作节点: {node.node_id} ({node.host}:{node.port})")

    def remove_node(self, node_id: str):
        """移除节点"""
        with self.lock:
            if node_id in self.nodes:
                self.nodes.pop(node_id)
                logger.info(f"➖ 移除工作节点: {node_id}")

    def update_node_status(self, node_id: str, **kwargs):
        """更新节点状态"""
        with self.lock:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                for key, value in kwargs.items():
                    if hasattr(node, key):
                        setattr(node, key, value)
                node.last_heartbeat = datetime.now()

    def select_node(self) -> WorkerNode | None:
        """选择最佳节点（负载均衡）"""
        with self.lock:
            available_nodes = [
                node for node in self.nodes.values()
                if node.is_available
            ]

            if not available_nodes:
                return None

            # 综合评分选择节点
            def node_score(node: WorkerNode) -> float:
                # 基础分数
                score = 100

                # 任务负载惩罚
                load_penalty = len(node.current_tasks) * 10
                score -= load_penalty

                # 成功率奖励
                success_bonus = node.success_rate * 0.3
                score += success_bonus

                # 响应时间惩罚
                response_penalty = node.avg_response_time * 2
                score -= response_penalty

                # CPU使用率惩罚
                cpu_penalty = node.cpu_usage * 0.5
                score -= cpu_penalty

                return max(0, score)

            # 选择分数最高的节点
            best_node = max(available_nodes, key=node_score)
            best_node.status = NodeStatus.BUSY
            return best_node

    def get_stats(self) -> dict[str, Any]:
        """获取负载均衡统计"""
        with self.lock:
            status_counts = defaultdict(int)
            total_capacity = 0
            used_capacity = 0

            for node in self.nodes.values():
                status_counts[node.status.value] += 1
                total_capacity += 10  # 假设每个节点容量为10
                used_capacity += len(node.current_tasks)

            return {
                'total_nodes': len(self.nodes),
                'active_nodes': status_counts[NodeStatus.ACTIVE.value],
                'busy_nodes': status_counts[NodeStatus.BUSY.value],
                'idle_nodes': status_counts[NodeStatus.IDLE.value],
                'failed_nodes': status_counts[NodeStatus.FAILED.value],
                'offline_nodes': status_counts[NodeStatus.OFFLINE.value],
                'total_capacity': total_capacity,
                'used_capacity': used_capacity,
                'capacity_utilization': (used_capacity / total_capacity * 100) if total_capacity > 0 else 0,
                'nodes': [
                    {
                        'node_id': node.node_id,
                        'host': f"{node.host}:{node.port}",
                        'status': node.status.value,
                        'current_tasks': len(node.current_tasks),
                        'success_rate': round(node.success_rate, 1),
                        'avg_response_time': round(node.avg_response_time, 2)
                    }
                    for node in self.nodes.values()
                ]
            }

class DistributedCrawlerMaster:
    """分布式爬虫主控节点"""

    def __init__(self, host: str = 'localhost', port: int = 8080):
        self.host = host
        self.port = port
        self.task_queue = TaskQueue()
        self.load_balancer = LoadBalancer()
        self.result_store = {}  # 简单的结果存储
        self.is_running = False
        self.stats = {
            'total_tasks_created': 0,
            'total_tasks_completed': 0,
            'total_tasks_failed': 0,
            'start_time': datetime.now()
        }

    async def start(self):
        """启动主控节点"""
        self.is_running = True
        logger.info(f"🚀 分布式爬虫主控节点启动 ({self.host}:{self.port})")

        # 启动监控线程
        monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitoring_thread.start()

        logger.info('✅ 主控节点已启动，等待工作节点连接...')

    def stop(self):
        """停止主控节点"""
        self.is_running = False
        logger.info('⏹️ 主控节点已停止')

    def add_urls(self, urls: list[str], priority: int = 0) -> list[str]:
        """添加URL到任务队列"""
        task_ids = []
        for url in urls:
            task = CrawlTask(
                task_id=str(uuid.uuid4()),
                url=url,
                priority=priority
            )
            self.task_queue.add_task(task)
            task_ids.append(task.task_id)

        self.stats['total_tasks_created'] += len(urls)
        logger.info(f"📋 添加了 {len(urls)} 个任务到队列 (优先级: {priority})")
        return task_ids

    def get_task_results(self, task_ids: list[str] | None = None) -> dict[str, Any]:
        """获取任务结果"""
        if not task_ids:
            # 返回所有任务结果
            return {
                task_id: {
                    'status': task.status.value,
                    'result': task.result,
                    'error': task.error,
                    'created_at': task.created_at.isoformat(),
                    'started_at': task.started_at.isoformat() if task.started_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None
                }
                for task_id, task in self.task_queue.task_dict.items()
            }
        else:
            return {
                task_id: {
                    'status': task.status.value,
                    'result': task.result,
                    'error': task.error,
                    'created_at': task.created_at.isoformat(),
                    'started_at': task.started_at.isoformat() if task.started_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None
                }
                for task_id in task_ids
                for task in [self.task_queue.task_dict.get(task_id)]
                if task is not None
            }

    def add_worker_node(self, host: str, port: int, capabilities: list[str] | None = None) -> str:
        """添加工作节点"""
        node_id = str(uuid.uuid4())
        node = WorkerNode(
            node_id=node_id,
            host=host,
            port=port,
            capabilities=capabilities or []
        )
        self.load_balancer.add_node(node)
        return node_id

    def _monitoring_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                # 任务调度
                self._schedule_tasks()

                # 节点健康检查
                self._check_node_health()

                # 清理过期任务
                self._cleanup_expired_tasks()

                time.sleep(1)  # 每秒检查一次

            except Exception as e:
                logger.error(f"监控循环出错: {e}")

    def _schedule_tasks(self):
        """任务调度"""
        pending_tasks = self.task_queue.get_pending_tasks()
        if not pending_tasks:
            return

        # 尝试为待处理任务分配节点
        for _ in range(min(len(pending_tasks), 5)):  # 每次最多调度5个任务
            node = self.load_balancer.select_node()
            if not node:
                break  # 没有可用节点

            task = self.task_queue.get_next_task()
            if not task:
                break  # 没有待处理任务

            # 分配任务给节点
            task.assigned_node = node.node_id
            node.current_tasks.append(task.task_id)
            node.total_tasks += 1

            # 这里应该实际发送任务到节点，简化处理直接在本地执行
            threading.Thread(
                target=self._execute_task_locally,
                args=(task, node),
                daemon=True
            ).start()

            logger.info(f"📤 任务 {task.task_id} 分配给节点 {node.node_id}")

    def _execute_task_locally(self, task: CrawlTask, node: WorkerNode):
        """本地执行任务（简化实现）"""
        try:
            # 模拟执行爬取任务
            time.time()

            # 这里应该调用实际的爬虫逻辑
            # 为了演示，我们模拟成功/失败
            success = random.choice([True, True, False])  # 2/3 成功率
            response_time = random.uniform(0.5, 3.0)

            if success:
                result = {
                    'success': True,
                    'url': task.url,
                    'content': f"Mock content for {task.url}",
                    'response_time': response_time,
                    'node_id': node.node_id
                }
                self.task_queue.complete_task(task.task_id, result=result)
                node.completed_tasks += 1
                self.stats['total_tasks_completed'] += 1
            else:
                error = 'Simulated failure'
                self.task_queue.complete_task(task.task_id, error=error)
                node.failed_tasks += 1
                self.stats['total_tasks_failed'] += 1

            # 更新节点统计
            node.avg_response_time = (node.avg_response_time + response_time) / 2
            if task.task_id in node.current_tasks:
                node.current_tasks.remove(task.task_id)

            if len(node.current_tasks) == 0:
                node.status = NodeStatus.IDLE
            else:
                node.status = NodeStatus.ACTIVE

        except Exception as e:
            logger.error(f"执行任务 {task.task_id} 时出错: {e}")
            self.task_queue.complete_task(task.task_id, error=str(e))
            node.failed_tasks += 1
            self.stats['total_tasks_failed'] += 1

    def _check_node_health(self):
        """检查节点健康状态"""
        datetime.now()
        for node_id, node in list(self.load_balancer.nodes.items()):
            # 检查心跳超时
            if time.time() - node.last_heartbeat.timestamp() > 120:  # 2分钟超时
                logger.warning(f"⚠️ 节点 {node_id} 心跳超时，标记为离线")
                node.status = NodeStatus.OFFLINE

    def _cleanup_expired_tasks(self):
        """清理过期任务"""
        current_time = datetime.now()
        expired_tasks = []

        for task in self.task_queue.task_dict.values():
            # 检查运行时间过长的任务
            if (task.status == TaskStatus.RUNNING and
                task.started_at and
                (current_time - task.started_at).total_seconds() > 300):  # 5分钟超时
                expired_tasks.append(task.task_id)

        # 标记过期任务为失败
        for task_id in expired_tasks:
            self.task_queue.complete_task(task_id, error='Task timeout')
            logger.warning(f"⏰ 任务 {task_id} 运行超时，标记为失败")

    def get_master_stats(self) -> dict[str, Any]:
        """获取主控节点统计"""
        uptime = datetime.now() - self.stats['start_time']

        return {
            'master_info': {
                'host': self.host,
                'port': self.port,
                'uptime': str(uptime),
                'is_running': self.is_running
            },
            'task_stats': {
                'total_tasks_created': self.stats['total_tasks_created'],
                'total_tasks_completed': self.stats['total_tasks_completed'],
                'total_tasks_failed': self.stats['total_tasks_failed'],
                'completion_rate': (
                    self.stats['total_tasks_completed'] / self.stats['total_tasks_created'] * 100
                    if self.stats['total_tasks_created'] > 0 else 0
                )
            },
            'queue_stats': self.task_queue.get_stats(),
            'node_stats': self.load_balancer.get_stats()
        }

async def demo_distributed_crawler():
    """演示分布式爬虫"""
    logger.info('🌐 分布式爬虫演示')
    logger.info(str('=' * 50))

    # 创建主控节点
    master = DistributedCrawlerMaster()
    await master.start()

    # 添加工作节点（模拟）
    worker_nodes = [
        ('192.168.1.10', 8001),
        ('192.168.1.11', 8002),
        ('192.168.1.12', 8003)
    ]

    logger.info("\n🔧 添加工作节点...")
    for host, port in worker_nodes:
        node_id = master.add_worker_node(host, port, ['http', 'https'])
        logger.info(f"   节点 {node_id}: {host}:{port}")

    # 添加测试URLs
    test_urls = [
        f"https://example.com/page{i}" for i in range(1, 21)
    ]

    logger.info(f"\n📋 添加 {len(test_urls)} 个测试URL...")
    task_ids = master.add_urls(test_urls, priority=0)

    # 添加高优先级URLs
    priority_urls = [
        f"https://example.com/priority_page{i}" for i in range(1, 6)
    ]

    logger.info(f"📋 添加 {len(priority_urls)} 个高优先级URL...")
    master.add_urls(priority_urls, priority=10)

    # 监控执行进度
    logger.info("\n📊 监控任务执行进度...")
    for i in range(30):  # 监控30秒
        await asyncio.sleep(1)

        stats = master.get_master_stats()
        task_stats = stats['task_stats']
        queue_stats = stats['queue_stats']
        node_stats = stats['node_stats']

        print(f"\r⏱️ {i+1:2d}s | "
              f"完成: {task_stats['total_tasks_completed']:3d} | "
              f"失败: {task_stats['total_tasks_failed']:3d} | "
              f"运行中: {queue_stats['running_tasks']:3d} | "
              f"待处理: {queue_stats['pending_tasks']:3d} | "
              f"活跃节点: {node_stats['active_nodes'] + node_stats['busy_nodes']}', end='")

        # 检查是否所有任务完成
        if (queue_stats['pending_tasks'] == 0 and
            queue_stats['running_tasks'] == 0):
            break

    logger.info("\n\n📈 最终统计:")
    final_stats = master.get_master_stats()

    logger.info(f"   总任务数: {final_stats['task_stats']['total_tasks_created']}")
    logger.info(f"   完成任务: {final_stats['task_stats']['total_tasks_completed']}")
    logger.info(f"   失败任务: {final_stats['task_stats']['total_tasks_failed']}")
    logger.info(f"   完成率: {final_stats['task_stats']['completion_rate']:.1f}%")
    logger.info(f"   总节点数: {final_stats['node_stats']['total_nodes']}")
    logger.info(f"   活跃节点: {final_stats['node_stats']['active_nodes'] + final_stats['node_stats']['busy_nodes']}")

    # 获取部分任务结果
    logger.info("\n📋 示例任务结果:")
    sample_results = master.get_task_results(task_ids[:3])
    for task_id, result in sample_results.items():
        status = result['status']
        logger.info(f"   任务 {task_id[:8]}: {status}")
        if status == 'completed':
            logger.info(f"      响应时间: {result['result']['response_time']:.2f}s")
            logger.info(f"      执行节点: {result['result']['node_id']}")

    master.stop()

if __name__ == '__main__':
    asyncio.run(demo_distributed_crawler())
