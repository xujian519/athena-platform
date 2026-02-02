#!/usr/bin/env python3
"""
系统管理器 - 依赖图管理
System Manager - Dependency Graph

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import logging
from collections import defaultdict, deque
from typing import Any

from .types import DependencyType

logger = logging.getLogger(__name__)


class DependencyGraph:
    """依赖图管理器

    负责管理模块之间的依赖关系，支持循环依赖检测和拓扑排序。
    """

    def __init__(self):
        """初始化依赖图"""
        self.dependencies: dict[str, dict[str, DependencyType]] = defaultdict(dict)
        self.dependents: dict[str, set[str]] = defaultdict(set)
        self.logger = logging.getLogger(__name__)

    def add_module(
        self, module_id: str, dependencies: dict[str, DependencyType] | None = None
    ):
        """添加模块到依赖图

        Args:
            module_id: 模块ID
            dependencies: 依赖字典 {module_id: DependencyType}
        """
        if dependencies:
            self.dependencies[module_id] = dependencies
            for dep_id in dependencies:
                self.dependents[dep_id].add(module_id)
        else:
            self.dependencies[module_id] = {}

        self.logger.debug(f"模块已添加到依赖图: {module_id}")

    def remove_module(self, module_id: str):
        """从依赖图中移除模块

        Args:
            module_id: 模块ID
        """
        # 移除依赖关系
        if module_id in self.dependencies:
            for dep_id in self.dependencies[module_id]:
                if dep_id in self.dependents and module_id in self.dependents[dep_id]:
                    self.dependents[dep_id].remove(module_id)
            del self.dependencies[module_id]

        # 移除被依赖关系
        if module_id in self.dependents:
            del self.dependents[module_id]

        self.logger.debug(f"模块已从依赖图移除: {module_id}")

    def get_dependencies(self, module_id: str) -> set[str]:
        """获取模块的依赖

        Args:
            module_id: 模块ID

        Returns:
            依赖模块ID集合
        """
        return set(self.dependencies.get(module_id, {}).keys())

    def get_dependents(self, module_id: str) -> set[str]:
        """获取依赖该模块的其他模块

        Args:
            module_id: 模块ID

        Returns:
            依赖者ID集合
        """
        return self.dependents.get(module_id, set()).copy()

    def check_circular_dependency(self, module_id: str) -> bool:
        """检查循环依赖

        Args:
            module_id: 模块ID

        Returns:
            是否存在循环依赖
        """
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def _dfs(node: str) -> bool:
            """深度优先搜索"""
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.get_dependencies(node):
                if neighbor not in visited:
                    if _dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        return _dfs(module_id)

    def get_load_order(self, module_ids: list[str]) -> list[str]:
        """获取模块加载顺序(拓扑排序)

        Args:
            module_ids: 模块ID列表

        Returns:
            排序后的模块ID列表
        """
        # 计算入度
        in_degree: dict[str, int] = {module_id: 0 for module_id in module_ids}
        adjacency_list: dict[str, list[str]] = {module_id: [] for module_id in module_ids}

        for module_id in module_ids:
            for dep_id in self.get_dependencies(module_id):
                if dep_id in in_degree:
                    in_degree[module_id] += 1
                    adjacency_list[dep_id].append(module_id)

        # Kahn算法
        queue: deque[str] = deque([m for m in module_ids if in_degree[m] == 0])
        load_order: list[str] = []

        while queue:
            node = queue.popleft()
            load_order.append(node)

            for neighbor in adjacency_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(load_order) != len(module_ids):
            self.logger.warning("存在循环依赖，无法完全拓扑排序")

        return load_order

    def visualize(self) -> dict[str, Any]:
        """可视化依赖图

        Returns:
            依赖图数据
        """
        return {
            "modules": list(self.dependencies.keys()),
            "dependencies": {
                module_id: list(deps.keys())
                for module_id, deps in self.dependencies.items()
            },
            "dependents": {
                module_id: list(deps) for module_id, deps in self.dependents.items()
            },
        }


__all__ = ["DependencyGraph"]
