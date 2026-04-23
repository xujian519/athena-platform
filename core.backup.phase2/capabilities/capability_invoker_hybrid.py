#!/usr/bin/env python3
from __future__ import annotations
"""
混合模式能力调用器
Hybrid Capability Invoker

支持真实MCP连接和模拟数据的混合模式
"""

import logging
from datetime import datetime
from typing import Any

from core.capabilities.capability_invoker_optimized import (
    MCPCapabilityInvokerOptimized,
    RestfulCapabilityInvokerOptimized,
)
from core.capabilities.real_mcp_connector import RealMCPConnector

logger = logging.getLogger(__name__)


class HybridCapabilityInvoker:
    """混合模式能力调用器"""

    def __init__(self, use_real_mcp: bool = True):
        """
        初始化混合调用器

        Args:
            use_real_mcp: 是否使用真实MCP连接
        """
        self.use_real_mcp = use_real_mcp

        # 创建真实MCP连接器
        if use_real_mcp:
            self.real_mcp = RealMCPConnector()
            logger.info("✅ 真实MCP连接器已启用")
        else:
            self.real_mcp = None
            logger.info("⚠️  使用模拟MCP模式")

        # 保留优化的模拟调用器作为后备
        self.mcp_invoker = MCPCapabilityInvokerOptimized()
        self.restful_invoker = RestfulCapabilityInvokerOptimized()

        logger.info("✅ 混合模式能力调用器初始化完成")

    async def invoke(
        self, capability_id: str, parameters: dict[str, Any], timeout: int = 30
    ) -> dict[str, Any]:
        """
        调用能力(优先使用真实MCP)

        Args:
            capability_id: 能力ID
            parameters: 调用参数
            timeout: 超时时间

        Returns:
            调用结果
        """
        start_time = datetime.now()

        try:
            # 尝试使用真实MCP连接
            if self.use_real_mcp and self.real_mcp:
                logger.info(f"🔌 尝试真实MCP调用: {capability_id}")

                # 检查能力是否在映射中
                available_capabilities = self.real_mcp.list_available_capabilities()
                if capability_id in available_capabilities:
                    result = await self.real_mcp.invoke_capability(
                        capability_id, parameters, timeout
                    )

                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    logger.info(
                        f"✅ 真实MCP调用成功: {capability_id} (耗时: {response_time:.2f}ms)"
                    )

                    return result
                else:
                    logger.info(f"⚠️  能力未在真实MCP中配置: {capability_id}")

            # 回退到模拟模式
            logger.info(f"🔄 使用模拟模式: {capability_id}")
            return await self._invoke_mock(capability_id, parameters, timeout)

        except Exception as e:
            logger.error(f"❌ 能力调用失败: {e}")
            # 出错时回退到模拟模式
            return await self._invoke_mock(capability_id, parameters, timeout)

    async def _invoke_mock(
        self, capability_id: str, parameters: dict[str, Any], timeout: int
    ) -> dict[str, Any]:
        """使用模拟模式调用"""
        # 根据能力类型选择调用器
        if any(keyword in capability_id for keyword in ["patent", "academic", "jina"]):
            # MCP能力
            endpoint = capability_id.replace("_", "-")
            result = await self.mcp_invoker.invoke(
                endpoint=endpoint, method="call", parameters=parameters, timeout=timeout
            )
            return result
        else:
            # RESTful能力
            result = await self.restful_invoker.invoke(
                endpoint="localhost", method=capability_id, parameters=parameters, timeout=timeout
            )
            return result

    async def start_mcp_servers(self) -> dict[str, bool]:
        """启动所有启用的MCP服务器"""
        if not self.use_real_mcp or not self.real_mcp:
            logger.info("⚠️  真实MCP未启用,跳过服务器启动")
            return {}

        enabled_servers = self.real_mcp.list_enabled_servers()
        results = {}

        logger.info(f"🚀 启动{len(enabled_servers)}个MCP服务器...")

        for server_name in enabled_servers:
            success = await self.real_mcp.start_server(server_name)
            results[server_name] = success

        successful = sum(1 for v in results.values() if v)
        logger.info(f"✅ MCP服务器启动完成: {successful}/{len(enabled_servers)}成功")

        return results

    async def stop_mcp_servers(self):
        """停止所有MCP服务器"""
        if self.real_mcp:
            await self.real_mcp.stop_all_servers()
            logger.info("🛑 所有MCP服务器已停止")

    async def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        status = {
            "mode": "real_mcp" if self.use_real_mcp else "mock",
            "timestamp": datetime.now().isoformat(),
        }

        if self.real_mcp:
            status["mcp_servers"] = await self.real_mcp.get_server_status()
            status["available_capabilities"] = self.real_mcp.list_available_capabilities()
            status["enabled_servers"] = self.real_mcp.list_enabled_servers()

        return status

    async def close(self):
        """关闭连接器"""
        await self.stop_mcp_servers()
        await self.mcp_invoker.close()

        logger.info("🔌 混合模式调用器已关闭")


# 单例模式
_hybrid_invoker: HybridCapabilityInvoker = None


def get_hybrid_invoker(use_real_mcp: bool = True) -> HybridCapabilityInvoker:
    """获取混合调用器单例"""
    global _hybrid_invoker
    if _hybrid_invoker is None:
        _hybrid_invoker = HybridCapabilityInvoker(use_real_mcp=use_real_mcp)
    return _hybrid_invoker
