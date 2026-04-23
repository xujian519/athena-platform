#!/usr/bin/env python3
from __future__ import annotations
"""
Agent工具注册表

自动发现声明式Agent和代理Agent，注册到FunctionCallingSystem。

Author: Athena平台团队
创建时间: 2026-04-21
"""

import logging
from typing import Any

from .agent_adapter import AgentAdapter
from .proxy_adapter import ProxyAgentAdapter
from core.agents.declarative.loader import get_loader
from core.xiaonuo_agent.tools.function_calling import get_function_calling_system

logger = logging.getLogger(__name__)


class AgentToolRegistry:
    """
    Agent工具注册表

    功能:
    1. 自动发现声明式Agent（.md文件）
    2. 自动发现代理Agent（新版小娜代理）
    3. 统一注册到FunctionCallingSystem
    4. 提供查询和管理接口
    """

    def __init__(self):
        """初始化注册表"""
        self._registered_agents: dict[str, Any] = {}
        self._fc_system = None

        logger.info("🔧 Agent工具注册表初始化")

    async def register_all_agents(self, include_proxies: bool = True) -> dict[str, Any]:
        """
        注册所有Agent到FunctionCallingSystem

        Args:
            include_proxies: 是否包含新版小娜代理

        Returns:
            注册统计信息
        """
        logger.info("🚀 开始注册所有Agent...")

        # 获取FunctionCallingSystem
        self._fc_system = await get_function_calling_system()

        stats = {
            "declarative_agents": 0,
            "proxy_agents": 0,
            "total": 0,
            "failed": 0,
        }

        # 1. 注册声明式Agent
        try:
            declarative_count = await self._register_declarative_agents()
            stats["declarative_agents"] = declarative_count
        except Exception as e:
            logger.error(f"❌ 注册声明式Agent失败: {e}")

        # 2. 注册代理Agent
        if include_proxies:
            try:
                proxy_count = await self._register_proxy_agents()
                stats["proxy_agents"] = proxy_count
            except Exception as e:
                logger.error(f"❌ 注册代理Agent失败: {e}")

        # 3. 计算总数
        stats["total"] = stats["declarative_agents"] + stats["proxy_agents"]

        logger.info(f"✅ Agent注册完成: {stats}")

        return stats

    async def _register_declarative_agents(self) -> int:
        """
        注册声明式Agent

        Returns:
            注册数量
        """
        count = 0

        # 加载所有声明式Agent定义
        loader = get_loader()
        agent_definitions = loader.load_all()

        logger.info(f"📄 发现 {len(agent_definitions)} 个声明式Agent")

        # 为每个Agent创建适配器并注册
        for agent_def in agent_definitions.values():
            try:
                # 创建适配器
                adapter = AgentAdapter(agent_def)

                # 注册到FunctionCallingSystem
                await self._register_adapter(adapter, agent_def.name)

                # 记录
                self._registered_agents[agent_def.name] = {
                    "type": "declarative",
                    "adapter": adapter,
                    "definition": agent_def,
                }

                count += 1
                logger.debug(f"✅ 注册声明式Agent: {agent_def.name}")

            except Exception as e:
                logger.error(f"❌ 注册Agent失败: {agent_def.name} - {e}")

        return count

    async def _register_proxy_agents(self) -> int:
        """
        注册代理Agent

        Returns:
            注册数量
        """
        count = 0

        # 获取所有代理
        proxy_names = ProxyAgentAdapter.list_all_proxies()

        logger.info(f"🔧 发现 {len(proxy_names)} 个代理Agent")

        # 为每个代理创建适配器并注册
        for proxy_name in proxy_names:
            try:
                # 获取代理的所有方法
                methods = ProxyAgentAdapter.get_proxy_methods(proxy_name)

                # 为每个方法创建适配器
                for method_name in methods:
                    try:
                        # 创建适配器
                        adapter = ProxyAgentAdapter(proxy_name, method_name)

                        # 工具名称
                        tool_name = f"{proxy_name}.{method_name}"

                        # 注册到FunctionCallingSystem
                        await self._register_adapter(adapter, tool_name)

                        # 记录
                        self._registered_agents[tool_name] = {
                            "type": "proxy",
                            "adapter": adapter,
                            "proxy_name": proxy_name,
                            "method_name": method_name,
                        }

                        count += 1
                        logger.debug(f"✅ 注册代理Agent: {tool_name}")

                    except Exception as e:
                        logger.error(f"❌ 注册代理方法失败: {proxy_name}.{method_name} - {e}")

            except Exception as e:
                logger.error(f"❌ 注册代理失败: {proxy_name} - {e}")

        return count

    async def _register_adapter(self, adapter: Any, name: str):
        """
        注册适配器到FunctionCallingSystem

        Args:
            adapter: 适配器对象
            name: 工具名称
        """
        if self._fc_system is None:
            raise RuntimeError("FunctionCallingSystem未初始化")

        # 获取工具定义
        tool_def = adapter.to_tool_definition()

        # 注册工具
        self._fc_system.register_tool(
            name=name,
            description=tool_def["description"],
            function=adapter,
            category=tool_def["category"],
            metadata=tool_def["metadata"]
        )

    def list_agents(self, agent_type: Optional[str] = None) -> list[str]:
        """
        列出已注册的Agent

        Args:
            agent_type: Agent类型过滤 ("declarative" | "proxy" | None)

        Returns:
            Agent名称列表
        """
        if agent_type is None:
            return list(self._registered_agents.keys())

        return [
            name
            for name, info in self._registered_agents.items()
            if info["type"] == agent_type
        ]

    def get_agent_info(self, agent_name: str) -> Optional[dict[str, Any]]:
        """
        获取Agent信息

        Args:
            agent_name: Agent名称

        Returns:
            Agent信息字典
        """
        return self._registered_agents.get(agent_name)

    def get_stats(self) -> dict[str, Any]:
        """
        获取注册统计信息

        Returns:
            统计信息字典
        """
        declarative_count = sum(
            1 for info in self._registered_agents.values()
            if info["type"] == "declarative"
        )
        proxy_count = sum(
            1 for info in self._registered_agents.values()
            if info["type"] == "proxy"
        )

        return {
            "total": len(self._registered_agents),
            "declarative_agents": declarative_count,
            "proxy_agents": proxy_count,
            "agents": list(self._registered_agents.keys()),
        }


# 全局注册表实例
_registry: AgentToolRegistry | None = None


async def get_agent_registry() -> AgentToolRegistry:
    """
    获取全局Agent工具注册表实例

    Returns:
        Agent工具注册表
    """
    global _registry

    if _registry is None:
        _registry = AgentToolRegistry()

    return _registry


async def register_all_agents(include_proxies: bool = True) -> dict[str, Any]:
    """
    注册所有Agent到FunctionCallingSystem

    Args:
        include_proxies: 是否包含新版小娜代理

    Returns:
        注册统计信息
    """
    registry = await get_agent_registry()
    return await registry.register_all_agents(include_proxies=include_proxies)
