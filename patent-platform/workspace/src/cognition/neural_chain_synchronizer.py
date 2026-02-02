#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
神经元链同步器
Neural Chain Synchronizer

实现神经元链之间的同步机制，确保数据一致性和处理协调性

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SyncMode(Enum):
    """同步模式"""
    SYNCHRONOUS = 'synchronous'          # 同步模式
    ASYNCHRONOUS = 'asynchronous'        # 异步模式
    SEMI_SYNCHRONOUS = 'semi_synchronous' # 半同步模式
    PIPELINE = 'pipeline'                # 流水线模式

class ConsistencyLevel(Enum):
    """一致性级别"""
    WEAK = 'weak'                        # 弱一致性
    EVENTUAL = 'eventual'                # 最终一致性
    STRONG = 'strong'                    # 强一致性
    SEQUENTIAL = 'sequential'            # 顺序一致性

class NeuronState(Enum):
    """神经元状态"""
    IDLE = 'idle'                        # 空闲
    PROCESSING = 'processing'            # 处理中
    WAITING = 'waiting'                  # 等待同步
    SYNCHRONIZING = 'synchronizing'      # 同步中
    ERROR = 'error'                      # 错误

@dataclass
class NeuralMessage:
    """神经元消息"""
    message_id: str
    source_id: str
    target_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0

@dataclass
class SyncCheckpoint:
    """同步检查点"""
    checkpoint_id: str
    neuron_ids: List[str]
    state_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    completed: bool = False

@dataclass
class NeuronInfo:
    """神经元信息"""
    neuron_id: str
    neuron_type: str
    state: NeuronState
    input_buffer: List[NeuralMessage]
    output_buffer: List[NeuralMessage]
    sync_dependencies: List[str]
    last_activity: datetime = field(default_factory=datetime.now)
    processing_count: int = 0
    error_count: int = 0

class NeuralNode:
    """神经网络节点"""

    def __init__(self, node_id: str, node_type: str, processing_function: Callable | None = None):
        self.node_id = node_id
        self.node_type = node_type
        self.processing_function = processing_function or self._default_processing

        # 状态管理
        self.state = NeuronState.IDLE
        self.input_buffer = asyncio.Queue(maxsize=1000)
        self.output_buffer = asyncio.Queue(maxsize=1000)

        # 同步依赖
        self.sync_dependencies = []
        self.sync_waiters = []

        # 性能指标
        self.metrics = {
            'processed_messages': 0,
            'processing_time_total': 0.0,
            'average_processing_time': 0.0,
            'last_processed_time': None
        }

        # 控制标志
        self.running = False
        self.paused = False

    async def start(self):
        """启动神经元"""
        self.running = True
        logger.info(f"🚀 神经元 {self.node_id} 已启动")
        asyncio.create_task(self._processing_loop())

    async def stop(self):
        """停止神经元"""
        self.running = False
        logger.info(f"🛑 神经元 {self.node_id} 已停止")

    async def pause(self):
        """暂停神经元"""
        self.paused = True
        self.state = NeuronState.WAITING
        logger.info(f"⏸️ 神经元 {self.node_id} 已暂停")

    async def resume(self):
        """恢复神经元"""
        self.paused = False
        self.state = NeuronState.IDLE
        logger.info(f"▶️ 神经元 {self.node_id} 已恢复")

    async def receive_message(self, message: NeuralMessage):
        """接收消息"""
        try:
            await self.input_buffer.put(message)
            logger.debug(f"📨 神经元 {self.node_id} 接收消息: {message.message_id}")
        except asyncio.QueueFull:
            logger.warning(f"⚠️ 神经元 {self.node_id} 输入缓冲区已满")
            raise

    def add_sync_dependency(self, neuron_id: str):
        """添加同步依赖"""
        if neuron_id not in self.sync_dependencies:
            self.sync_dependencies.append(neuron_id)
            logger.debug(f"🔗 神经元 {self.node_id} 添加同步依赖: {neuron_id}")

    async def wait_for_sync(self, checkpoint_id: str, timeout: float = 10.0):
        """等待同步"""
        self.state = NeuronState.WAITING

        try:
            # 创建同步事件
            sync_event = asyncio.Event()
            self.sync_waiters.append((checkpoint_id, sync_event))

            # 等待同步信号
            await asyncio.wait_for(sync_event.wait(), timeout=timeout)

            logger.debug(f"✅ 神经元 {self.node_id} 同步完成: {checkpoint_id}")

        except asyncio.TimeoutError:
            logger.error(f"⏰ 神经元 {self.node_id} 同步超时: {checkpoint_id}")
            raise

        finally:
            # 清理同步等待器
            self.sync_waiters = [(cid, event) for cid, event in self.sync_waiters
                               if cid != checkpoint_id]

    async def trigger_sync(self, checkpoint_id: str):
        """触发同步"""
        self.state = NeuronState.SYNCHRONIZING

        # 通知所有等待的神经元
        for cid, event in self.sync_waiters:
            if cid == checkpoint_id:
                event.set()
                logger.debug(f"🔄 神经元 {self.node_id} 触发同步: {checkpoint_id}")

    async def _processing_loop(self):
        """处理循环"""
        while self.running:
            try:
                if not self.paused:
                    # 从输入缓冲区获取消息
                    message = await asyncio.wait_for(
                        self.input_buffer.get(),
                        timeout=0.1
                    )

                    # 处理消息
                    await self._process_message(message)

                else:
                    # 暂停状态，等待恢复
                    await asyncio.sleep(0.1)

            except asyncio.TimeoutError:
                continue  # 没有消息，继续循环

            except Exception as e:
                logger.error(f"❌ 神经元 {self.node_id} 处理错误: {e}")
                self.state = NeuronState.ERROR
                await asyncio.sleep(1)  # 错误恢复延迟

    async def _process_message(self, message: NeuralMessage):
        """处理消息"""
        start_time = time.time()

        try:
            self.state = NeuronState.PROCESSING

            # 执行处理函数
            result = await self.processing_function(message, self)

            # 创建输出消息
            output_message = NeuralMessage(
                message_id=str(uuid.uuid4()),
                source_id=self.node_id,
                target_id=message.source_id,
                message_type='response',
                payload=result
            )

            # 发送到输出缓冲区
            await self.output_buffer.put(output_message)

            # 更新指标
            processing_time = time.time() - start_time
            self._update_metrics(processing_time)

            self.state = NeuronState.IDLE
            logger.debug(f"✅ 神经元 {self.node_id} 处理完成: {message.message_id}")

        except Exception as e:
            logger.error(f"❌ 神经元 {self.node_id} 处理失败: {e}")
            self.metrics['error_count'] += 1
            self.state = NeuronState.ERROR

    async def _default_processing(self, message: NeuralMessage, node: 'NeuralNode') -> Dict[str, Any]:
        """默认处理函数"""
        return {
            'processed_by': node.node_id,
            'input_message': message.message_id,
            'processing_time': time.time(),
            'status': 'processed'
        }

    def _update_metrics(self, processing_time: float):
        """更新性能指标"""
        self.metrics['processed_messages'] += 1
        self.metrics['processing_time_total'] += processing_time

        total_processed = self.metrics['processed_messages']
        if total_processed > 0:
            self.metrics['average_processing_time'] = (
                self.metrics['processing_time_total'] / total_processed
            )

        self.metrics['last_processed_time'] = datetime.now()

class NeuralChainSynchronizer:
    """神经元链同步器"""

    def __init__(self, sync_mode: SyncMode = SyncMode.SYNCHRONOUS,
                 consistency_level: ConsistencyLevel = ConsistencyLevel.EVENTUAL):
        self.sync_mode = sync_mode
        self.consistency_level = consistency_level

        # 神经元管理
        self.neurons: Dict[str, NeuralNode] = {}
        self.neuron_dependencies: Dict[str, List[str]] = defaultdict(list)

        # 同步管理
        self.checkpoints: Dict[str, SyncCheckpoint] = {}
        self.active_sync_groups: Dict[str, List[str]] = defaultdict(list)

        # 消息路由
        self.message_router = MessageRouter()

        # 性能监控
        self.metrics = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'average_sync_time': 0.0,
            'total_messages': 0,
            'message_delivery_time': 0.0
        }

        # 同步配置
        self.sync_timeout = 30.0
        self.max_retry_attempts = 3
        self.batch_size = 10

        logger.info(f"🧠 神经元链同步器初始化完成，模式: {sync_mode.value}, 一致性: {consistency_level.value}")

    def add_neuron(self, neuron: NeuralNode, dependencies: Optional[List[str] = None):
        """添加神经元"""
        self.neurons[neuron.node_id] = neuron
        if dependencies:
            self.neuron_dependencies[neuron.node_id] = dependencies
            # 添加同步依赖
            for dep_id in dependencies:
                neuron.add_sync_dependency(dep_id)

        logger.info(f"➕ 添加神经元: {neuron.node_id}")

    async def start_all(self):
        """启动所有神经元"""
        logger.info(f"🚀 启动 {len(self.neurons)} 个神经元...")

        for neuron in self.neurons.values():
            await neuron.start()

        # 启动消息路由器
        await self.message_router.start()

        logger.info('✅ 所有神经元已启动')

    async def stop_all(self):
        """停止所有神经元"""
        logger.info('🛑 停止所有神经元...')

        for neuron in self.neurons.values():
            await neuron.stop()

        # 停止消息路由器
        await self.message_router.stop()

        logger.info('✅ 所有神经元已停止')

    async def send_message(self, message: NeuralMessage):
        """发送消息"""
        self.metrics['total_messages'] += 1

        try:
            if message.target_id in self.neurons:
                # 直接发送到目标神经元
                await self.neurons[message.target_id].receive_message(message)
            else:
                # 通过路由器发送
                await self.message_router.route_message(message)

            logger.debug(f"📤 消息已发送: {message.message_id}")

        except Exception as e:
            logger.error(f"❌ 消息发送失败: {e}")
            raise

    async def create_sync_group(self, group_id: str, neuron_ids: List[str]):
        """创建同步组"""
        # 验证神经元存在
        for neuron_id in neuron_ids:
            if neuron_id not in self.neurons:
                raise ValueError(f"神经元不存在: {neuron_id}")

        self.active_sync_groups[group_id] = neuron_ids

        # 设置神经元间的同步依赖
        for i, neuron_id in enumerate(neuron_ids):
            for other_id in neuron_ids[i+1:]:
                self.neurons[neuron_id].add_sync_dependency(other_id)
                self.neurons[other_id].add_sync_dependency(neuron_id)

        logger.info(f"🔗 创建同步组: {group_id}, 包含 {len(neuron_ids)} 个神经元")

    async def synchronize_group(self, group_id: str, timeout: float | None = None) -> bool:
        """同步组内所有神经元"""
        start_time = time.time()
        timeout = timeout or self.sync_timeout

        try:
            if group_id not in self.active_sync_groups:
                raise ValueError(f"同步组不存在: {group_id}")

            neuron_ids = self.active_sync_groups[group_id]
            checkpoint_id = str(uuid.uuid4())

            logger.info(f"🔄 开始同步组: {group_id}, 检查点: {checkpoint_id}")

            # 创建检查点
            checkpoint = SyncCheckpoint(
                checkpoint_id=checkpoint_id,
                neuron_ids=neuron_ids.copy(),
                state_data={}
            )
            self.checkpoints[checkpoint_id] = checkpoint

            # 根据一致性级别执行同步
            if self.consistency_level == ConsistencyLevel.STRONG:
                success = await self._strong_sync(neuron_ids, checkpoint_id, timeout)
            elif self.consistency_level == ConsistencyLevel.SEQUENTIAL:
                success = await self._sequential_sync(neuron_ids, checkpoint_id, timeout)
            elif self.consistency_level == ConsistencyLevel.EVENTUAL:
                success = await self._eventual_sync(neuron_ids, checkpoint_id, timeout)
            else:  # WEAK
                success = await self._weak_sync(neuron_ids, checkpoint_id, timeout)

            # 更新指标
            sync_time = time.time() - start_time
            self._update_sync_metrics(success, sync_time)

            if success:
                checkpoint.completed = True
                logger.info(f"✅ 同步组 {group_id} 同步成功, 耗时: {sync_time:.2f}秒")
            else:
                logger.error(f"❌ 同步组 {group_id} 同步失败")

            return success

        except Exception as e:
            logger.error(f"❌ 同步组 {group_id} 同步异常: {e}")
            self.metrics['failed_syncs'] += 1
            return False

    async def _strong_sync(self, neuron_ids: List[str], checkpoint_id: str, timeout: float) -> bool:
        """强一致性同步"""
        tasks = []

        # 所有神经元等待同步
        for neuron_id in neuron_ids:
            task = asyncio.create_task(
                self.neurons[neuron_id].wait_for_sync(checkpoint_id, timeout)
            )
            tasks.append(task)

        # 等待所有神经元准备就绪
        try:
            await asyncio.gather(*tasks)

            # 同时触发所有神经元
            trigger_tasks = []
            for neuron_id in neuron_ids:
                task = asyncio.create_task(
                    self.neurons[neuron_id].trigger_sync(checkpoint_id)
                )
                trigger_tasks.append(task)

            await asyncio.gather(*trigger_tasks)
            return True

        except Exception as e:
            logger.error(f"❌ 强同步失败: {e}")
            return False

    async def _sequential_sync(self, neuron_ids: List[str], checkpoint_id: str, timeout: float) -> bool:
        """顺序一致性同步"""
        for neuron_id in neuron_ids:
            try:
                # 等待当前神经元
                await self.neurons[neuron_id].wait_for_sync(checkpoint_id, timeout)

                # 触发当前神经元
                await self.neurons[neuron_id].trigger_sync(checkpoint_id)

                logger.debug(f"✅ 神经元 {neuron_id} 顺序同步完成")

            except Exception as e:
                logger.error(f"❌ 神经元 {neuron_id} 顺序同步失败: {e}")
                return False

        return True

    async def _eventual_sync(self, neuron_ids: List[str], checkpoint_id: str, timeout: float) -> bool:
        """最终一致性同步"""
        # 创建同步任务
        sync_tasks = []
        for neuron_id in neuron_ids:
            task = asyncio.create_task(
                self._eventual_sync_neuron(neuron_id, checkpoint_id, timeout)
            )
            sync_tasks.append(task)

        # 等待大部分神经元完成
        try:
            results = await asyncio.gather(*sync_tasks, return_exceptions=True)

            # 检查成功率
            success_count = sum(1 for result in results if result is True)
            success_rate = success_count / len(results)

            if success_rate >= 0.8:  # 80%成功率即可
                logger.info(f"✅ 最终同步完成，成功率: {success_rate:.2%}")
                return True
            else:
                logger.warning(f"⚠️ 最终同步成功率较低: {success_rate:.2%}")
                return False

        except Exception as e:
            logger.error(f"❌ 最终同步异常: {e}")
            return False

    async def _eventual_sync_neuron(self, neuron_id: str, checkpoint_id: str, timeout: float) -> bool:
        """单个神经元的最终同步"""
        try:
            # 尝试同步，但允许失败
            await asyncio.wait_for(
                self.neurons[neuron_id].wait_for_sync(checkpoint_id, timeout/2),
                timeout=timeout/2
            )
            await self.neurons[neuron_id].trigger_sync(checkpoint_id)
            return True

        except Exception:
            # 最终一致性允许部分失败
            logger.warning(f"⚠️ 神经元 {neuron_id} 最终同步失败，但允许继续")
            return False

    async def _weak_sync(self, neuron_ids: List[str], checkpoint_id: str, timeout: float) -> bool:
        """弱一致性同步"""
        # 简单通知，不等待完成
        for neuron_id in neuron_ids:
            try:
                # 异步触发，不等待
                asyncio.create_task(
                    self.neurons[neuron_id].trigger_sync(checkpoint_id)
                )
            except Exception as e:
                logger.debug(f"⚠️ 神经元 {neuron_id} 弱同步通知失败: {e}")

        # 弱一致性总是返回成功
        logger.info('✅ 弱一致性同步通知已发送')
        return True

    def _update_sync_metrics(self, success: bool, sync_time: float):
        """更新同步指标"""
        self.metrics['total_syncs'] += 1

        if success:
            self.metrics['successful_syncs'] += 1
        else:
            self.metrics['failed_syncs'] += 1

        # 更新平均同步时间
        total_syncs = self.metrics['total_syncs']
        if total_syncs > 0:
            current_avg = self.metrics['average_sync_time']
            self.metrics['average_sync_time'] = (
                (current_avg * (total_syncs - 1) + sync_time) / total_syncs
            )

    async def batch_sync(self, sync_requests: List[Tuple[str, List[str]]]) -> Dict[str, bool]:
        """批量同步"""
        logger.info(f"🔄 开始批量同步 {len(sync_requests)} 个组...")

        # 根据同步模式执行
        if self.sync_mode == SyncMode.SYNCHRONOUS:
            # 顺序同步
            results = {}
            for group_id, neuron_ids in sync_requests:
                result = await self.synchronize_group(group_id)
                results[group_id] = result

        elif self.sync_mode == SyncMode.ASYNCHRONOUS:
            # 并发同步
            tasks = []
            for group_id, neuron_ids in sync_requests:
                task = asyncio.create_task(self.synchronize_group(group_id))
                tasks.append((group_id, task))

            results = {}
            for group_id, task in tasks:
                try:
                    result = await task
                    results[group_id] = result
                except Exception as e:
                    logger.error(f"❌ 组 {group_id} 批量同步失败: {e}")
                    results[group_id] = False

        else:  # SEMI_SYNCHRONOUS or PIPELINE
            # 分批并发同步
            results = {}
            batch_size = self.batch_size

            for i in range(0, len(sync_requests), batch_size):
                batch = sync_requests[i:i+batch_size]
                batch_tasks = []

                for group_id, neuron_ids in batch:
                    task = asyncio.create_task(self.synchronize_group(group_id))
                    batch_tasks.append((group_id, task))

                for group_id, task in batch_tasks:
                    try:
                        result = await task
                        results[group_id] = result
                    except Exception as e:
                        logger.error(f"❌ 组 {group_id} 分批同步失败: {e}")
                        results[group_id] = False

        logger.info(f"✅ 批量同步完成: {sum(results.values())}/{len(results)} 成功")
        return results

    def get_sync_status(self, group_id: str | None = None) -> Dict[str, Any]:
        """获取同步状态"""
        status = {
            'sync_mode': self.sync_mode.value,
            'consistency_level': self.consistency_level.value,
            'total_neurons': len(self.neurons),
            'active_groups': len(self.active_sync_groups),
            'metrics': self.metrics.copy()
        }

        if group_id and group_id in self.active_sync_groups:
            neuron_ids = self.active_sync_groups[group_id]
            status['group_info'] = {
                'neuron_count': len(neuron_ids),
                'neuron_states': {
                    neuron_id: self.neurons[neuron_id].state.value
                    for neuron_id in neuron_ids
                }
            }

        return status

    def export_sync_history(self, file_path: str):
        """导出同步历史"""
        export_data = {
            'sync_configuration': {
                'sync_mode': self.sync_mode.value,
                'consistency_level': self.consistency_level.value,
                'sync_timeout': self.sync_timeout,
                'max_retry_attempts': self.max_retry_attempts
            },
            'neurons': {
                neuron_id: {
                    'node_type': neuron.node_type,
                    'state': neuron.state.value,
                    'sync_dependencies': neuron.sync_dependencies,
                    'metrics': neuron.metrics
                }
                for neuron_id, neuron in self.neurons.items()
            },
            'sync_groups': self.active_sync_groups,
            'checkpoints': {
                checkpoint_id: {
                    'neuron_ids': checkpoint.neuron_ids,
                    'timestamp': checkpoint.timestamp.isoformat(),
                    'completed': checkpoint.completed
                }
                for checkpoint_id, checkpoint in self.checkpoints.items()
            },
            'performance_metrics': self.metrics
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 同步历史已导出到: {file_path}")

class MessageRouter:
    """消息路由器"""

    def __init__(self):
        self.routes: Dict[str, List[str]] = defaultdict(list)
        self.running = False
        self.message_queue = asyncio.Queue()
        self.routing_tasks: List[asyncio.Task] = []

    async def start(self):
        """启动路由器"""
        self.running = True
        # 启动路由工作线程
        for i in range(3):  # 3个工作线程
            task = asyncio.create_task(self._routing_worker())
            self.routing_tasks.append(task)
        logger.info('🚀 消息路由器已启动')

    async def stop(self):
        """停止路由器"""
        self.running = False
        for task in self.routing_tasks:
            task.cancel()
        logger.info('🛑 消息路由器已停止')

    def add_route(self, pattern: str, target_ids: List[str]):
        """添加路由规则"""
        self.routes[pattern] = target_ids
        logger.debug(f"📝 添加路由规则: {pattern} -> {target_ids}")

    async def route_message(self, message: NeuralMessage):
        """路由消息"""
        await self.message_queue.put(message)

    async def _routing_worker(self):
        """路由工作线程"""
        while self.running:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=0.1
                )

                await self._process_routing(message)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ 路由处理错误: {e}")

    async def _process_routing(self, message: NeuralMessage):
        """处理路由"""
        # 查找匹配的路由规则
        matched_routes = []
        for pattern, targets in self.routes.items():
            if self._pattern_match(message.target_id, pattern):
                matched_routes.extend(targets)

        # 发送到匹配的目标
        for target_id in matched_routes:
            # 这里应该有实际的发送机制
            logger.debug(f"📨 路由消息 {message.message_id} 到 {target_id}")

    def _pattern_match(self, target: str, pattern: str) -> bool:
        """模式匹配"""
        if pattern == '*':
            return True
        elif pattern.startswith('*') and target.endswith(pattern[1:]):
            return True
        elif pattern.endswith('*') and target.startswith(pattern[:-1]):
            return True
        elif pattern == target:
            return True
        return False

# 测试用例
async def main():
    """主函数"""
    logger.info('🧠 神经元链同步器测试')
    logger.info(str('='*50))

    # 创建同步器
    synchronizer = NeuralChainSynchronizer(
        sync_mode=SyncMode.SYNCHRONOUS,
        consistency_level=ConsistencyLevel.EVENTUAL
    )

    # 创建神经元
    neuron1 = NeuralNode('neuron1', 'input')
    neuron2 = NeuralNode('neuron2', 'processor')
    neuron3 = NeuralNode('neuron3', 'output')

    # 添加神经元到同步器
    synchronizer.add_neuron(neuron1)
    synchronizer.add_neuron(neuron2)
    synchronizer.add_neuron(neuron3)

    # 启动所有神经元
    await synchronizer.start_all()

    # 创建同步组
    await synchronizer.create_sync_group('group1', ['neuron1', 'neuron2', 'neuron3'])

    # 发送测试消息
    test_message = NeuralMessage(
        message_id='msg1',
        source_id='external',
        target_id='neuron1',
        message_type='test',
        payload={'data': 'test'}
    )

    await synchronizer.send_message(test_message)

    # 等待处理
    await asyncio.sleep(2)

    # 执行同步
    logger.info("\n🔄 执行同步...")
    sync_result = await synchronizer.synchronize_group('group1')
    logger.info(f"同步结果: {sync_result}")

    # 获取状态
    status = synchronizer.get_sync_status('group1')
    logger.info(f"\n📊 同步状态: {json.dumps(status, indent=2, ensure_ascii=False)}")

    # 停止所有神经元
    await synchronizer.stop_all()

    # 导出历史
    synchronizer.export_sync_history('sync_history.json')

    logger.info("\n✅ 测试完成！")

if __name__ == '__main__':
    asyncio.run(main())