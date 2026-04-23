#!/usr/bin/env python3
from __future__ import annotations

"""
赫布定律优化系统
Hebbian Learning Optimizer

基于神经科学中赫布定律的思想:
"一起活动的神经细胞会连接在一起" (Cells that fire together, wire together)

应用到AI系统:
- 经常一起调用的功能应该强化连接
- 优化调用路径,提升系统效率
- 类比NMDA受体作为"裁判蛋白"调节学习敏感度

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import heapq
import json
import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class SynapseState(Enum):
    """突触状态"""

    WEAK = "weak"  # 弱连接
    MODERATE = "moderate"  # 中等连接
    STRONG = "strong"  # 强连接
    PERMANENT = "permanent"  # 永久连接(长期记忆)


@dataclass
class NeuralConnection:
    """神经连接"""

    source: str  # 源节点
    target: str  # 目标节点
    strength: float = 0.1  # 连接强度 (0-1)
    state: SynapseState = SynapseState.WEAK
    activation_count: int = 0  # 激活次数
    last_activation: str = field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def age(self) -> float:
        """连接年龄(天数)"""
        created = datetime.fromisoformat(self.created_at)
        return (datetime.now() - created).total_seconds() / 86400

    @property
    def activation_frequency(self) -> float:
        """激活频率(次/天)"""
        if self.age <= 0:
            return 0
        return self.activation_count / self.age


@dataclass
class CoActivationRecord:
    """协同激活记录"""

    timestamp: str
    nodes: set[str]
    context: dict[str, Any] = field(default_factory=dict)


class HebbianOptimizer:
    """
    赫布定律优化器

    核心思想:
    1. 一起激活的节点加强连接
    2. 连接强度随使用增强
    3. 不使用的连接逐渐弱化
    4. 形成高效的神经网络
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        decay_rate: float = 0.01,
        strong_threshold: float = 0.7,
        weak_threshold: float = 0.3,
    ):
        """
        初始化赫布定律优化器

        Args:
            learning_rate: 学习率(NMDA受体敏感度)
            decay_rate: 衰减率(不使用时的弱化速度)
            strong_threshold: 强连接阈值
            weak_threshold: 弱连接阈值
        """
        self.name = "赫布定律优化系统"
        self.version = "v0.1.2"

        # 神经网络
        self.connections: dict[str, NeuralConnection] = {}  # {connection_id: connection}

        # 节点集合
        self.nodes: set[str] = set()

        # 协同激活历史
        self.coactivation_history: list[CoActivationRecord] = []

        # 学习参数
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate
        self.strong_threshold = strong_threshold
        self.weak_threshold = weak_threshold

        logger.info(f"🧠 {self.name} ({self.version}) 初始化完成")
        logger.info(f"   学习率: {learning_rate}, 衰减率: {decay_rate}")

    def record_activation(self, nodes: list[str], context: dict[str, Any] | None = None) -> None:
        """
        记录节点激活(协同激活)

        Args:
            nodes: 激活的节点列表
            context: 上下文信息
        """
        if not nodes or len(nodes) < 2:
            return

        timestamp = datetime.now().isoformat()
        node_set = set(nodes)

        # 记录协同激活
        record = CoActivationRecord(timestamp=timestamp, nodes=node_set, context=context or {})
        self.coactivation_history.append(record)

        # 更新所有节点对之间的连接
        for i, source in enumerate(nodes):
            for target in nodes[i + 1 :]:
                self._strengthen_connection(source, target)

        # 清理过期历史(保留最近1000条)
        if len(self.coactivation_history) > 1000:
            self.coactivation_history = self.coactivation_history[-1000:]

        logger.debug(f"🧠 记录激活: {nodes}")

    def _strengthen_connection(self, source: str, target: str) -> None:
        """
        加强两个节点之间的连接

        Args:
            source: 源节点
            target: 目标节点
        """
        # 确保节点存在
        self.nodes.add(source)
        self.nodes.add(target)

        # 生成连接ID(按字典序保证唯一)
        connection_id = self._get_connection_id(source, target)

        # 获取或创建连接
        if connection_id not in self.connections:
            self.connections[connection_id] = NeuralConnection(
                source=source, target=target, strength=0.1, state=SynapseState.WEAK
            )

        connection = self.connections[connection_id]

        # 赫布定律:加强连接
        connection.strength = min(1.0, connection.strength + self.learning_rate)
        connection.activation_count += 1
        connection.last_activation = datetime.now().isoformat()

        # 更新状态
        connection.state = self._get_state(connection.strength)

    def _get_connection_id(self, node1: str, node2: str) -> str:
        """生成连接ID"""
        nodes = sorted([node1, node2])
        return f"{nodes[0]}<->{nodes[1]}"

    def _get_state(self, strength: float) -> SynapseState:
        """根据强度获取状态"""
        if strength >= self.strong_threshold:
            return SynapseState.STRONG
        elif strength >= self.weak_threshold:
            return SynapseState.MODERATE
        else:
            return SynapseState.WEAK

    def decay_connections(self) -> None:
        """
        衰减连接(不使用的连接逐渐弱化)

        类似于突触的长时程压抑(LTD)
        """
        now = datetime.now()
        to_remove = []

        for conn_id, connection in self.connections.items():
            # 计算距离上次激活的时间
            last_active = datetime.fromisoformat(connection.last_activation)
            days_since_activation = (now - last_active).total_seconds() / 86400

            # 衰减强度
            decay = self.decay_rate * days_since_activation
            connection.strength = max(0.0, connection.strength - decay)

            # 更新状态
            connection.state = self._get_state(connection.strength)

            # 标记完全衰减的连接
            if connection.strength <= 0:
                to_remove.append(conn_id)

        # 移除完全衰减的连接
        for conn_id in to_remove:
            del self.connections[conn_id]

        if to_remove:
            logger.info(f"🧠 衰减连接: 移除 {len(to_remove)} 个弱连接")

    def get_strongest_connections(self, top_n: int = 10) -> list[NeuralConnection]:
        """
        获取最强的连接

        Args:
            top_n: 返回前N个

        Returns:
            最强连接列表
        """
        return heapq.nlargest(top_n, self.connections.values(), key=lambda c: c.strength)

    def get_node_connections(self, node: str, min_strength: float = 0.0) -> list[NeuralConnection]:
        """
        获取节点的所有连接

        Args:
            node: 节点名称
            min_strength: 最小强度阈值

        Returns:
            连接列表
        """
        connections = []

        for connection in self.connections.values():
            if connection.source == node or connection.target == node:
                if connection.strength >= min_strength:
                    connections.append(connection)

        # 按强度排序
        return sorted(connections, key=lambda c: c.strength, reverse=True)

    def optimize_call_path(self, start_node: str, end_node: str) -> list[str]:
        """
        优化调用路径(基于连接强度)

        Args:
            start_node: 起始节点
            end_node: 目标节点

        Returns:
            优化后的路径
        """
        # 使用Dijkstra算法,但用连接强度作为权重(强度越高,权重越小)
        # 这里简化实现:返回最强的直接连接路径

        connection_id = self._get_connection_id(start_node, end_node)

        if connection_id in self.connections:
            connection = self.connections[connection_id]
            if connection.strength > 0.5:
                return [start_node, end_node]

        # 如果没有强直接连接,寻找中间节点
        path = [start_node]
        current = start_node

        # 简单的贪婪策略
        visited = {start_node}
        max_iterations = 10

        for _ in range(max_iterations):
            # 找到当前节点的最强连接
            connections = self.get_node_connections(current, min_strength=0.3)

            next_node = None
            best_strength = 0

            for conn in connections:
                candidate = conn.target if conn.source == current else conn.source

                if candidate not in visited and conn.strength > best_strength:
                    best_strength = conn.strength
                    next_node = candidate

            if next_node is None:
                break

            path.append(next_node)
            visited.add(next_node)

            if next_node == end_node:
                break

            current = next_node

        return path

    def get_network_stats(self) -> dict[str, Any]:
        """获取神经网络统计"""
        if not self.connections:
            return {"message": "暂无连接"}

        total_strength = sum(c.strength for c in self.connections.values())
        avg_strength = total_strength / len(self.connections)

        # 状态分布
        state_counts = Counter(c.state.value for c in self.connections.values())

        # 激活频率统计
        activation_counts = [c.activation_count for c in self.connections.values()]
        avg_activations = sum(activation_counts) / len(activation_counts)

        # 最强连接
        strongest = max(self.connections.values(), key=lambda c: c.strength)

        return {
            "total_nodes": len(self.nodes),
            "total_connections": len(self.connections),
            "average_strength": avg_strength,
            "total_strength": total_strength,
            "state_distribution": dict(state_counts),
            "average_activations": avg_activations,
            "strongest_connection": {
                "nodes": f"{strongest.source} <-> {strongest.target}",
                "strength": strongest.strength,
                "activations": strongest.activation_count,
            },
            "learning_rate": self.learning_rate,
            "decay_rate": self.decay_rate,
        }


# 全局单例
_hebbian_optimizer_instance = None


def get_hebbian_optimizer() -> HebbianOptimizer:
    """获取赫布定律优化器单例"""
    global _hebbian_optimizer_instance
    if _hebbian_optimizer_instance is None:
        _hebbian_optimizer_instance = HebbianOptimizer()
    return _hebbian_optimizer_instance


# 测试代码
async def main():
    """测试赫布定律优化系统"""

    print("\n" + "=" * 60)
    print("🧠 赫布定律优化系统测试")
    print("=" * 60 + "\n")

    optimizer = get_hebbian_optimizer()

    # 测试1:记录激活
    print("📝 测试1: 记录协同激活")
    optimizer.record_activation(["小诺", "小娜", "记忆系统"])
    optimizer.record_activation(["小诺", "小娜"])
    optimizer.record_activation(["小诺", "小娜", "知识图谱"])
    optimizer.record_activation(["云熙", "IP管理"])
    print("✅ 激活记录完成\n")

    # 测试2:查看最强连接
    print("📝 测试2: 最强连接")
    strongest = optimizer.get_strongest_connections(top_n=5)
    for i, conn in enumerate(strongest, 1):
        print(f"{i}. {conn.source} <-> {conn.target}")
        print(f"   强度: {conn.strength:.2f}, 激活: {conn.activation_count}次")
    print()

    # 测试3:路径优化
    print("📝 测试3: 路径优化")
    path = optimizer.optimize_call_path("小诺", "知识图谱")
    print(f"优化路径: {' -> '.join(path)}")
    print()

    # 测试4:网络统计
    print("📝 测试4: 网络统计")
    stats = optimizer.get_network_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print()

    # 测试5:衰减连接
    print("📝 测试5: 连接衰减")
    # 模拟时间流逝(这里只是演示,实际衰减需要真实时间间隔)
    optimizer.decay_connections()
    print("✅ 衰减完成")

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
