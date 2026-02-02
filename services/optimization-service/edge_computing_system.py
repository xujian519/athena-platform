#!/usr/bin/env python3
"""
Athena平台边缘计算系统
提供边缘节点管理、分布式计算、负载均衡、数据同步等功能
"""

import asyncio
from core.async_main import async_main
import hashlib
import json
import logging
from core.logging_config import setup_logging
import os
import pickle
import queue
import socket
import subprocess
import threading
import time
import uuid
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import aiohttp
import psutil
import requests
from docker.errors import APIError

import docker

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class NodeType(Enum):
    """节点类型"""
    CLOUD = 'cloud'               # 云端中心节点
    EDGE = 'edge'                 # 边缘计算节点
    GATEWAY = 'gateway'           # 网关节点
    STORAGE = 'storage'           # 存储节点
    COMPUTE = 'compute'           # 计算节点
    HYBRID = 'hybrid'             # 混合节点

class NodeStatus(Enum):
    """节点状态"""
    ONLINE = 'online'
    OFFLINE = 'offline'
    MAINTENANCE = 'maintenance'
    ERROR = 'error'
    DEGRADED = 'degraded'
    SCALING = 'scaling'

class TaskStatus(Enum):
    """任务状态"""
    PENDING = 'pending'
    SCHEDULED = 'scheduled'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    TIMEOUT = 'timeout'

class LoadBalancingStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = 'round_robin'
    LEAST_CONNECTIONS = 'least_connections'
    WEIGHTED_ROUND_ROBIN = 'weighted_round_robin'
    RESPONSE_TIME = 'response_time'
    RESOURCE_BASED = 'resource_based'
    GEOGRAPHIC = 'geographic'

class DataSyncStrategy(Enum):
    """数据同步策略"""
    IMMEDIATE = 'immediate'         # 立即同步
    BATCH = 'batch'                 # 批量同步
    PERIODIC = 'periodic'           # 定期同步
    EVENT_DRIVEN = 'event_driven'   # 事件驱动
    LAZY = 'lazy'                   # 延迟同步

@dataclass
class EdgeNode:
    """边缘节点"""
    node_id: str
    name: str
    node_type: NodeType
    host: str
    port: int
    location: str  # 地理位置
    capabilities: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    status: NodeStatus = NodeStatus.OFFLINE
    last_heartbeat: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComputeTask:
    """计算任务"""
    task_id: str
    name: str
    task_type: str
    priority: int = 1
    requirements: Dict[str, Any] = field(default_factory=dict)
    data_size: int = 0
    estimated_duration: float = 0.0  # 秒
    max_retries: int = 3
    retry_count: int = 0
    status: TaskStatus = TaskStatus.PENDING
    assigned_node: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any | None = None
    error_message: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataSync:
    """数据同步记录"""
    sync_id: str
    source_node: str
    target_node: str
    data_type: str
    data_size: int
    sync_strategy: DataSyncStrategy
    status: str = 'pending'
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    error_message: str | None = None

class NodeManager:
    """节点管理器"""

    def __init__(self):
        """初始化节点管理器"""
        self.nodes = {}  # node_id -> EdgeNode
        self.node_groups = {}  # group_name -> Set[node_id]
        self.heartbeat_interval = 30  # 秒
        self.heartbeat_timeout = 90  # 秒

    def register_node(self, node: EdgeNode) -> bool:
        """注册节点"""
        try:
            node.status = NodeStatus.ONLINE
            node.last_heartbeat = datetime.now()
            self.nodes[node.node_id] = node

            # 根据地理位置分组
            location = node.location or 'default'
            if location not in self.node_groups:
                self.node_groups[location] = set()
            self.node_groups[location].add(node.node_id)

            logger.info(f"注册边缘节点: {node.name} ({node.node_id}) at {location}")
            return True

        except Exception as e:
            logger.error(f"注册节点失败: {e}")
            return False

    def unregister_node(self, node_id: str) -> bool:
        """注销节点"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.status = NodeStatus.OFFLINE

            # 从分组中移除
            for group_nodes in self.node_groups.values():
                group_nodes.discard(node_id)

            logger.info(f"注销边缘节点: {node.name} ({node_id})")
            return True

        return False

    def update_heartbeat(self, node_id: str) -> bool:
        """更新节点心跳"""
        if node_id in self.nodes:
            self.nodes[node_id].last_heartbeat = datetime.now()
            if self.nodes[node_id].status == NodeStatus.OFFLINE:
                self.nodes[node_id].status = NodeStatus.ONLINE
            return True

        return False

    def check_node_health(self) -> List[str]:
        """检查节点健康状态"""
        now = datetime.now()
        unhealthy_nodes = []

        for node_id, node in self.nodes.items():
            if node.last_heartbeat:
                time_diff = (now - node.last_heartbeat).total_seconds()

                if time_diff > self.heartbeat_timeout:
                    if node.status != NodeStatus.OFFLINE:
                        node.status = NodeStatus.OFFLINE
                        unhealthy_nodes.append(node_id)
                        logger.warning(f"节点 {node.name} ({node_id}) 心跳超时，标记为离线")

        return unhealthy_nodes

    def get_available_nodes(self, location: str = None, node_type: NodeType = None) -> List[EdgeNode]:
        """获取可用节点"""
        available_nodes = []

        for node in self.nodes.values():
            if node.status != NodeStatus.ONLINE:
                continue

            if location and node.location != location:
                continue

            if node_type and node.node_type != node_type:
                continue

            # 检查资源可用性
            if self._check_node_resources(node):
                available_nodes.append(node)

        return available_nodes

    def _check_node_resources(self, node: EdgeNode) -> bool:
        """检查节点资源可用性"""
        resources = node.resources

        # 检查CPU使用率
        cpu_usage = resources.get('cpu_usage', 0)
        if cpu_usage > 90:  # 超过90%
            return False

        # 检查内存使用率
        memory_usage = resources.get('memory_usage', 0)
        if memory_usage > 90:  # 超过90%
            return False

        # 检查存储使用率
        storage_usage = resources.get('storage_usage', 0)
        if storage_usage > 90:  # 超过90%
            return False

        return True

    def get_node_stats(self) -> Dict[str, Any]:
        """获取节点统计信息"""
        stats = {
            'total_nodes': len(self.nodes),
            'online_nodes': 0,
            'offline_nodes': 0,
            'nodes_by_type': {},
            'nodes_by_location': {},
            'total_resources': {
                'cpu_cores': 0,
                'memory_gb': 0,
                'storage_gb': 0
            }
        }

        for node in self.nodes.values():
            # 统计状态
            if node.status == NodeStatus.ONLINE:
                stats['online_nodes'] += 1
            else:
                stats['offline_nodes'] += 1

            # 统计类型
            node_type = node.node_type.value
            stats['nodes_by_type'][node_type] = stats['nodes_by_type'].get(node_type, 0) + 1

            # 统计地理位置
            location = node.location or 'unknown'
            stats['nodes_by_location'][location] = stats['nodes_by_location'].get(location, 0) + 1

            # 统计资源
            resources = node.resources
            stats['total_resources']['cpu_cores'] += resources.get('cpu_cores', 0)
            stats['total_resources']['memory_gb'] += resources.get('memory_gb', 0)
            stats['total_resources']['storage_gb'] += resources.get('storage_gb', 0)

        return stats

class LoadBalancer:
    """负载均衡器"""

    def __init__(self, node_manager: NodeManager):
        """初始化负载均衡器"""
        self.node_manager = node_manager
        self.strategy = LoadBalancingStrategy.RESOURCE_BASED
        self.round_robin_index = 0
        self.node_loads = {}  # node_id -> load_info
        self.response_times = {}  # node_id -> List[response_time]

    def set_strategy(self, strategy: LoadBalancingStrategy) -> None:
        """设置负载均衡策略"""
        self.strategy = strategy
        logger.info(f"负载均衡策略已设置为: {strategy.value}")

    def select_node(self, task: ComputeTask, location: str = None) -> EdgeNode | None:
        """选择节点执行任务"""
        available_nodes = self.node_manager.get_available_nodes(location)

        if not available_nodes:
            logger.warning(f"没有可用的边缘节点 (location: {location})")
            return None

        # 根据任务要求过滤节点
        suitable_nodes = self._filter_nodes_by_requirements(available_nodes, task)

        if not suitable_nodes:
            logger.warning(f"没有满足任务要求的节点")
            return None

        # 根据策略选择节点
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(suitable_nodes)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_selection(suitable_nodes)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection(suitable_nodes)
        elif self.strategy == LoadBalancingStrategy.RESPONSE_TIME:
            return self._response_time_selection(suitable_nodes)
        elif self.strategy == LoadBalancingStrategy.RESOURCE_BASED:
            return self._resource_based_selection(suitable_nodes)
        elif self.strategy == LoadBalancingStrategy.GEOGRAPHIC:
            return self._geographic_selection(suitable_nodes, task)
        else:
            return suitable_nodes[0]

    def _filter_nodes_by_requirements(self, nodes: List[EdgeNode], task: ComputeTask) -> List[EdgeNode]:
        """根据任务要求过滤节点"""
        suitable_nodes = []
        requirements = task.requirements

        for node in nodes:
            suitable = True

            # 检查CPU要求
            min_cpu = requirements.get('min_cpu', 0)
            if node.resources.get('cpu_cores', 0) < min_cpu:
                suitable = False

            # 检查内存要求
            min_memory = requirements.get('min_memory', 0)
            if node.resources.get('memory_gb', 0) < min_memory:
                suitable = False

            # 检查存储要求
            min_storage = requirements.get('min_storage', 0)
            if node.resources.get('storage_gb', 0) < min_storage:
                suitable = False

            # 检查特殊能力要求
            required_capabilities = requirements.get('capabilities', [])
            for capability in required_capabilities:
                if capability not in node.capabilities:
                    suitable = False
                    break

            if suitable:
                suitable_nodes.append(node)

        return suitable_nodes

    def _round_robin_selection(self, nodes: List[EdgeNode]) -> EdgeNode:
        """轮询选择"""
        if not nodes:
            return None

        node = nodes[self.round_robin_index % len(nodes)]
        self.round_robin_index += 1
        return node

    def _least_connections_selection(self, nodes: List[EdgeNode]) -> EdgeNode:
        """最少连接选择"""
        min_connections = float('inf')
        selected_node = None

        for node in nodes:
            connections = self.node_loads.get(node.node_id, {}).get('connections', 0)
            if connections < min_connections:
                min_connections = connections
                selected_node = node

        return selected_node

    def _weighted_round_robin_selection(self, nodes: List[EdgeNode]) -> EdgeNode:
        """加权轮询选择"""
        total_weight = 0
        weighted_nodes = []

        for node in nodes:
            # 计算权重（基于资源）
            weight = (
                node.resources.get('cpu_cores', 1) * 2 +
                node.resources.get('memory_gb', 1) +
                node.resources.get('storage_gb', 0.5)
            )

            total_weight += weight
            weighted_nodes.extend([node] * int(weight))

        if not weighted_nodes:
            return nodes[0]

        return weighted_nodes[self.round_robin_index % len(weighted_nodes)]

    def _response_time_selection(self, nodes: List[EdgeNode]) -> EdgeNode:
        """响应时间选择"""
        best_node = None
        best_response_time = float('inf')

        for node in nodes:
            response_times = self.response_times.get(node.node_id, [])

            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
            else:
                avg_response_time = 1000  # 默认1秒

            if avg_response_time < best_response_time:
                best_response_time = avg_response_time
                best_node = node

        return best_node or nodes[0]

    def _resource_based_selection(self, nodes: List[EdgeNode]) -> EdgeNode:
        """基于资源选择"""
        best_node = None
        best_score = -1

        for node in nodes:
            # 计算资源评分
            cpu_available = node.resources.get('cpu_cores', 0) * (1 - node.resources.get('cpu_usage', 0) / 100)
            memory_available = node.resources.get('memory_gb', 0) * (1 - node.resources.get('memory_usage', 0) / 100)
            storage_available = node.resources.get('storage_gb', 0) * (1 - node.resources.get('storage_usage', 0) / 100)

            score = cpu_available + memory_available + storage_available

            if score > best_score:
                best_score = score
                best_node = node

        return best_node or nodes[0]

    def _geographic_selection(self, nodes: List[EdgeNode], task: ComputeTask) -> EdgeNode:
        """地理位置选择"""
        task_location = task.metadata.get('preferred_location')

        if task_location:
            # 优先选择同一地理位置的节点
            local_nodes = [node for node in nodes if node.location == task_location]
            if local_nodes:
                return self._resource_based_selection(local_nodes)

        # 否则选择距离最近的节点
        return self._resource_based_selection(nodes)

    def update_node_load(self, node_id: str, connections: int, response_time: float = None) -> None:
        """更新节点负载信息"""
        if node_id not in self.node_loads:
            self.node_loads[node_id] = {'connections': 0, 'last_update': datetime.now()}

        self.node_loads[node_id]['connections'] = connections
        self.node_loads[node_id]['last_update'] = datetime.now()

        if response_time is not None:
            if node_id not in self.response_times:
                self.response_times[node_id] = []

            self.response_times[node_id].append(response_time)

            # 只保留最近的100个响应时间记录
            if len(self.response_times[node_id]) > 100:
                self.response_times[node_id] = self.response_times[node_id][-100:]

class TaskScheduler:
    """任务调度器"""

    def __init__(self, node_manager: NodeManager, load_balancer: LoadBalancer):
        """初始化任务调度器"""
        self.node_manager = node_manager
        self.load_balancer = load_balancer
        self.pending_tasks = queue.PriorityQueue()
        self.running_tasks = {}  # task_id -> task_info
        self.completed_tasks = {}  # task_id -> task_info
        self.max_concurrent_tasks = 100

    def submit_task(self, task: ComputeTask) -> bool:
        """提交任务"""
        try:
            # 优先级队列：数字越小优先级越高
            priority = task.priority
            self.pending_tasks.put((priority, task))

            logger.info(f"提交任务: {task.name} ({task.task_id})")
            return True

        except Exception as e:
            logger.error(f"提交任务失败: {e}")
            return False

    async def schedule_tasks(self):
        """调度任务"""
        while True:
            try:
                # 检查是否可以执行新任务
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(1)
                    continue

                # 获取待执行任务
                try:
                    priority, task = self.pending_tasks.get(timeout=1.0)
                except queue.Empty:
                    await asyncio.sleep(1)
                    continue

                # 选择执行节点
                node = self.load_balancer.select_node(task)
                if not node:
                    # 没有可用节点，重新放回队列
                    self.pending_tasks.put((priority, task))
                    await asyncio.sleep(5)
                    continue

                # 执行任务
                task.assigned_node = node.node_id
                task.status = TaskStatus.SCHEDULED
                task.started_at = datetime.now()

                self.running_tasks[task.task_id] = {
                    'task': task,
                    'node': node,
                    'start_time': time.time()
                }

                # 异步执行任务
                asyncio.create_task(self._execute_task(task, node))

            except Exception as e:
                logger.error(f"任务调度异常: {e}")
                await asyncio.sleep(1)

    async def _execute_task(self, task: ComputeTask, node: EdgeNode):
        """执行任务"""
        task_id = task.task_id
        node_id = node.node_id

        try:
            # 更新节点负载
            current_connections = self.load_balancer.node_loads.get(node_id, {}).get('connections', 0)
            self.load_balancer.update_node_load(node_id, current_connections + 1)

            task.status = TaskStatus.RUNNING

            # 记录开始时间
            start_time = time.time()

            # 根据任务类型执行
            if task.task_type == 'data_processing':
                result = await self._execute_data_processing_task(task, node)
            elif task.task_type == 'model_inference':
                result = await self._execute_model_inference_task(task, node)
            elif task.task_type == 'multimodal_processing':
                result = await self._execute_multimodal_task(task, node)
            else:
                result = await self._execute_generic_task(task, node)

            # 记录响应时间
            response_time = (time.time() - start_time) * 1000  # 毫秒
            self.load_balancer.update_node_load(node_id, current_connections, response_time)

            # 任务完成
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.execution_time = response_time / 1000

            # 移动到完成任务列表
            if task_id in self.running_tasks:
                completed_task = self.running_tasks.pop(task_id)
                self.completed_tasks[task_id] = completed_task

            logger.info(f"任务执行完成: {task.name} ({task_id}) on {node.name}, 耗时: {response_time:.2f}ms")

        except Exception as e:
            # 任务失败
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()

            # 更新负载
            current_connections = self.load_balancer.node_loads.get(node_id, {}).get('connections', 0)
            self.load_balancer.update_node_load(node_id, max(0, current_connections - 1))

            # 重试逻辑
            task.retry_count += 1
            if task.retry_count < task.max_retries:
                logger.warning(f"任务失败，准备重试: {task.name} ({task_id}), 重试次数: {task.retry_count}")

                # 重新提交任务
                task.status = TaskStatus.PENDING
                task.assigned_node = None
                self.pending_tasks.put((task.priority, task))
            else:
                logger.error(f"任务最终失败: {task.name} ({task_id}), 错误: {e}")

                # 移动到完成列表
                if task_id in self.running_tasks:
                    failed_task = self.running_tasks.pop(task_id)
                    self.completed_tasks[task_id] = failed_task

            # 记录负载
            current_connections = self.load_balancer.node_loads.get(node_id, {}).get('connections', 0)
            self.load_balancer.update_node_load(node_id, max(0, current_connections - 1))

    async def _execute_data_processing_task(self, task: ComputeTask, node: EdgeNode) -> Any:
        """执行数据处理任务"""
        # 模拟数据处理
        await asyncio.sleep(task.estimated_duration or 1.0)

        return {
            'processed_items': task.metadata.get('item_count', 100),
            'processing_rate': task.metadata.get('item_count', 100) / (task.estimated_duration or 1.0),
            'node_id': node.node_id
        }

    async def _execute_model_inference_task(self, task: ComputeTask, node: EdgeNode) -> Any:
        """执行模型推理任务"""
        # 模拟模型推理
        model_name = task.metadata.get('model_name', 'default_model')
        input_size = task.metadata.get('input_size', 1024)

        await asyncio.sleep(task.estimated_duration or 2.0)

        return {
            'model': model_name,
            'input_size': input_size,
            'output_size': input_size,  # 假设输出大小
            'inference_time': task.estimated_duration or 2.0,
            'node_id': node.node_id
        }

    async def _execute_multimodal_task(self, task: ComputeTask, node: EdgeNode) -> Any:
        """执行多模态处理任务"""
        # 模拟多模态处理
        media_type = task.metadata.get('media_type', 'image')
        processing_complexity = task.metadata.get('complexity', 'medium')

        duration = task.estimated_duration or 3.0
        if processing_complexity == 'high':
            duration *= 2

        await asyncio.sleep(duration)

        return {
            'media_type': media_type,
            'processing_complexity': processing_complexity,
            'processing_time': duration,
            'output_format': task.metadata.get('output_format', 'json'),
            'node_id': node.node_id
        }

    async def _execute_generic_task(self, task: ComputeTask, node: EdgeNode) -> Any:
        """执行通用任务"""
        # 通用任务执行逻辑
        await asyncio.sleep(task.estimated_duration or 1.0)

        return {
            'task_type': task.task_type,
            'execution_time': task.estimated_duration or 1.0,
            'node_id': node.node_id,
            'result': 'Task completed successfully'
        }

    def get_task_stats(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        return {
            'pending_tasks': self.pending_tasks.qsize(),
            'running_tasks': len(self.running_tasks),
            'completed_tasks': len(self.completed_tasks),
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'total_processed': len(self.completed_tasks)
        }

class DataSyncManager:
    """数据同步管理器"""

    def __init__(self, node_manager: NodeManager):
        """初始化数据同步管理器"""
        self.node_manager = node_manager
        self.sync_queue = asyncio.Queue()
        self.active_syncs = {}  # sync_id -> sync_info
        self.sync_history = {}  # sync_id -> sync_record

    def schedule_sync(self, source_node: str, target_node: str, data_type: str,
                     data_size: int, strategy: DataSyncStrategy) -> str:
        """调度数据同步"""
        sync_id = str(uuid.uuid4())

        sync = DataSync(
            sync_id=sync_id,
            source_node=source_node,
            target_node=target_node,
            data_type=data_type,
            data_size=data_size,
            sync_strategy=strategy
        )

        self.sync_queue.put(sync)
        logger.info(f"调度数据同步: {source_node} -> {target_node}, 数据类型: {data_type}")

        return sync_id

    async def process_syncs(self):
        """处理数据同步"""
        while True:
            try:
                sync = await self.sync_queue.get()

                self.active_syncs[sync.sync_id] = {
                    'sync': sync,
                    'start_time': time.time()
                }

                # 执行同步
                await self._execute_sync(sync)

                # 记录完成
                self.active_syncs.pop(sync.sync_id, None)

            except Exception as e:
                logger.error(f"数据同步处理异常: {e}")
                await asyncio.sleep(1)

    async def _execute_sync(self, sync: DataSync):
        """执行数据同步"""
        try:
            # 验证节点状态
            if sync.source_node not in self.node_manager.nodes:
                raise ValueError(f"源节点不存在: {sync.source_node}")

            if sync.target_node not in self.node_manager.nodes:
                raise ValueError(f"目标节点不存在: {sync.target_node}")

            source_node = self.node_manager.nodes[sync.source_node]
            target_node = self.node_manager.nodes[sync.target_node]

            if source_node.status != NodeStatus.ONLINE:
                raise ValueError(f"源节点离线: {sync.source_node}")

            if target_node.status != NodeStatus.ONLINE:
                raise ValueError(f"目标节点离线: {sync.target_node}")

            # 根据同步策略执行同步
            if sync.sync_strategy == DataSyncStrategy.IMMEDIATE:
                await self._immediate_sync(sync)
            elif sync.sync_strategy == DataSyncStrategy.BATCH:
                await self._batch_sync(sync)
            elif sync.sync_strategy == DataSyncStrategy.PERIODIC:
                await self._periodic_sync(sync)
            else:
                await self._immediate_sync(sync)

            # 更新同步状态
            sync.status = 'completed'
            sync.completed_at = datetime.now()
            self.sync_history[sync.sync_id] = sync

            logger.info(f"数据同步完成: {sync.sync_id}")

        except Exception as e:
            sync.status = 'failed'
            sync.error_message = str(e)
            sync.completed_at = datetime.now()
            self.sync_history[sync.sync_id] = sync

            logger.error(f"数据同步失败: {sync.sync_id}, 错误: {e}")

    async def _immediate_sync(self, sync: DataSync):
        """立即同步"""
        # 模拟立即数据传输
        logger.info(f"执行立即同步: {sync.sync_id}")

        # 这里应该实现实际的数据传输逻辑
        # 例如：复制文件、数据库同步等

        await asyncio.sleep(0.1)  # 模拟网络延迟

    async def _batch_sync(self, sync: DataSync):
        """批量同步"""
        logger.info(f"执行批量同步: {sync.sync_id}")

        # 批量处理逻辑
        await asyncio.sleep(0.5)  # 模拟批量处理时间

    async def _periodic_sync(self, sync: DataSync):
        """定期同步"""
        logger.info(f"执行定期同步: {sync.sync_id}")

        # 定期同步逻辑
        await asyncio.sleep(0.3)  # 模拟定期处理时间

    def get_sync_stats(self) -> Dict[str, Any]:
        """获取同步统计信息"""
        return {
            'pending_syncs': self.sync_queue.qsize(),
            'active_syncs': len(self.active_syncs),
            'completed_syncs': len(self.sync_history),
            'sync_strategies': [s.value for s in DataSyncStrategy]
        }

class EdgeComputingSystem:
    """边缘计算系统主类"""

    def __init__(self):
        """初始化边缘计算系统"""
        self.node_manager = NodeManager()
        self.load_balancer = LoadBalancer(self.node_manager)
        self.task_scheduler = TaskScheduler(self.node_manager, self.load_balancer)
        self.data_sync_manager = DataSyncManager(self.node_manager)
        self.running = False
        self.background_tasks = []

    async def start(self):
        """启动边缘计算系统"""
        logger.info('启动边缘计算系统...')

        self.running = True

        # 启动后台任务
        self.background_tasks = [
            asyncio.create_task(self.task_scheduler.schedule_tasks()),
            asyncio.create_task(self.data_sync_manager.process_syncs()),
            asyncio.create_task(self._monitor_nodes()),
            asyncio.create_task(self._collect_metrics())
        ]

        logger.info('边缘计算系统已启动')

    async def stop(self):
        """停止边缘计算系统"""
        logger.info('停止边缘计算系统...')

        self.running = False

        # 取消后台任务
        for task in self.background_tasks:
            task.cancel()

        # 等待任务完成
        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        logger.info('边缘计算系统已停止')

    async def add_edge_node(self, name: str, host: str, port: int, location: str,
                           node_type: NodeType = NodeType.EDGE,
                           capabilities: Dict[str, Any] = None) -> str:
        """添加边缘节点"""
        node = EdgeNode(
            node_id=str(uuid.uuid4()),
            name=name,
            node_type=node_type,
            host=host,
            port=port,
            location=location,
            capabilities=capabilities or {},
            resources=self._collect_node_resources(host, port)
        )

        if self.node_manager.register_node(node):
            # 启动节点监控
            asyncio.create_task(self._monitor_node(node))
            return node.node_id

        return ''

    async def _monitor_node(self, node: EdgeNode):
        """监控单个节点"""
        while self.running:
            try:
                # 更新节点资源信息
                resources = self._collect_node_resources(node.host, node.port)
                node.resources.update(resources)

                # 等待下一次心跳
                await asyncio.sleep(self.node_manager.heartbeat_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控节点 {node.name} 失败: {e}")
                await asyncio.sleep(10)

    async def _monitor_nodes(self):
        """监控所有节点"""
        while self.running:
            try:
                # 检查节点健康状态
                unhealthy_nodes = self.node_manager.check_node_health()

                for node_id in unhealthy_nodes:
                    node = self.node_manager.nodes.get(node_id)
                    if node:
                        logger.warning(f"节点 {node.name} ({node_id}) 不健康")

                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"节点监控异常: {e}")
                await asyncio.sleep(10)

    async def _collect_metrics(self):
        """收集系统指标"""
        while self.running:
            try:
                # 收集各项指标
                metrics = self._get_system_metrics()

                # 这里可以发送到监控系统
                # logger.info(f"系统指标: {metrics}")

                await asyncio.sleep(60)  # 每分钟收集一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"指标收集异常: {e}")
                await asyncio.sleep(10)

    def _collect_node_resources(self, host: str, port: int) -> Dict[str, Any]:
        """收集节点资源信息"""
        try:
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # 内存信息
            memory = psutil.virtual_memory()

            # 磁盘信息
            disk = psutil.disk_usage('/')

            # 网络信息
            network = psutil.net_io_counters()

            return {
                'cpu_usage': cpu_percent,
                'cpu_cores': cpu_count,
                'memory_usage': memory.percent,
                'memory_gb': memory.total / (1024**3),
                'storage_usage': disk.percent,
                'storage_gb': disk.total / (1024**3),
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"收集节点资源失败: {e}")
            return {}

    def _get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        node_stats = self.node_manager.get_node_stats()
        task_stats = self.task_scheduler.get_task_stats()
        sync_stats = self.data_sync_manager.get_sync_stats()

        return {
            'timestamp': datetime.now().isoformat(),
            'nodes': node_stats,
            'tasks': task_stats,
            'data_sync': sync_stats,
            'load_balancing_strategy': self.load_balancer.strategy.value
        }

    async def submit_task(self, task_name: str, task_type: str, requirements: Dict[str, Any] = None,
                         priority: int = 1, location: str = None, **kwargs) -> str:
        """提交计算任务"""
        task = ComputeTask(
            task_id=str(uuid.uuid4()),
            name=task_name,
            task_type=task_type,
            priority=priority,
            requirements=requirements or {},
            metadata={'location': location, **kwargs}
        )

        if self.task_scheduler.submit_task(task):
            return task.task_id

        return ''

    async def schedule_data_sync(self, source_node: str, target_node: str, data_type: str,
                                data_size: int, strategy: DataSyncStrategy = DataSyncStrategy.IMMEDIATE) -> str:
        """调度数据同步"""
        return self.data_sync_manager.schedule_sync(
            source_node, target_node, data_type, data_size, strategy
        )

# 全局边缘计算系统实例
_edge_computing_system = None

def get_edge_computing_system() -> EdgeComputingSystem:
    """获取边缘计算系统实例"""
    global _edge_computing_system
    if _edge_computing_system is None:
        _edge_computing_system = EdgeComputingSystem()
    return _edge_computing_system

# 工具函数
async def create_sample_edge_nodes() -> List[str]:
    """创建示例边缘节点"""
    edge_system = get_edge_computing_system()

    # 等待系统启动
    if not edge_system.running:
        await edge_system.start()
        await asyncio.sleep(2)  # 等待2秒确保系统完全启动

    # 创建示例节点
    sample_nodes = [
        {
            'name': '北京边缘节点1',
            'host': '192.168.1.101',
            'port': 8081,
            'location': '北京',
            'capabilities': {'gpu': True, 'camera': True}
        },
        {
            'name': '上海边缘节点1',
            'host': '192.168.1.102',
            'port': 8081,
            'location': '上海',
            'capabilities': {'storage': True, 'cache': True}
        },
        {
            'name': '深圳边缘节点1',
            'host': '192.168.1.103',
            'port': 8081,
            'location': '深圳',
            'capabilities': {'ai_model': True, 'inference': True}
        }
    ]

    node_ids = []

    for node_config in sample_nodes:
        node_id = await edge_system.add_edge_node(**node_config)
        if node_id:
            node_ids.append(node_id)
            logger.info(f"创建边缘节点: {node_config['name']} ({node_id})")

    return node_ids

async def test_edge_computing_workflow():
    """测试边缘计算工作流"""
    edge_system = get_edge_computing_system()

    # 启动系统
    await edge_system.start()

    try:
        # 创建示例节点
        node_ids = await create_sample_edge_nodes()

        if not node_ids:
            logger.error('没有可用的边缘节点')
            return

        logger.info(f"创建了 {len(node_ids)} 个边缘节点")

        # 提交测试任务
        test_tasks = [
            {
                'name': '图像处理任务',
                'task_type': 'multimodal_processing',
                'requirements': {'min_cpu': 2, 'min_memory': 4},
                'priority': 2,
                'metadata': {
                    'media_type': 'image',
                    'complexity': 'medium',
                    'item_count': 50
                }
            },
            {
                'name': '数据推理任务',
                'task_type': 'model_inference',
                'requirements': {'min_cpu': 1, 'min_memory': 2},
                'priority': 3,
                'metadata': {
                    'model_name': 'yolo',
                    'input_size': 1024
                }
            },
            {
                'name': '批量数据处理',
                'task_type': 'data_processing',
                'requirements': {'min_cpu': 1, 'min_memory': 1},
                'priority': 1,
                'metadata': {
                    'item_count': 1000
                }
            }
        ]

        task_ids = []
        for task_config in test_tasks:
            task_id = await edge_system.submit_task(**task_config)
            if task_id:
                task_ids.append(task_id)

        logger.info(f"提交了 {len(task_ids)} 个计算任务")

        # 等待一段时间让任务执行
        await asyncio.sleep(10)

        # 获取系统指标
        metrics = edge_system._get_system_metrics()
        logger.info(f"系统指标: {json.dumps(metrics, ensure_ascii=False, indent=2)}")

        # 测试数据同步
        if len(node_ids) >= 2:
            sync_id = await edge_system.schedule_data_sync(
                node_ids[0], node_ids[1], 'test_data', 1024, DataSyncStrategy.IMMEDIATE
            )
            logger.info(f"调度数据同步: {sync_id}")

        # 等待同步完成
        await asyncio.sleep(5)

        # 获取同步统计
        sync_stats = edge_system.data_sync_manager.get_sync_stats()
        logger.info(f"数据同步统计: {sync_stats}")

    finally:
        # 停止系统
        await edge_system.stop()

if __name__ == '__main__':
    asyncio.run(test_edge_computing_workflow())