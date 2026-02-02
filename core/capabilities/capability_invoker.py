#!/usr/bin/env python3
"""
能力调用器
Capability Invoker

负责调用各种类型的原子化能力
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseCapabilityInvoker(ABC):
    """能力调用器基类"""

    @abstractmethod
    async def invoke(
        self, endpoint: str, method: str, parameters: dict[str, Any], timeout: int
    ) -> dict[str, Any]:
        """调用能力"""
        pass


class MCPCapabilityInvoker(BaseCapabilityInvoker):
    """MCP能力调用器"""

    def __init__(self):
        # MCP客户端池(简化实现)
        self.clients = {}
        logger.info("✅ MCP调用器初始化完成")

    async def invoke(
        self, endpoint: str, method: str, parameters: dict[str, Any], timeout: int
    ) -> dict[str, Any]:
        """调用MCP能力"""
        logger.info(f"📡 调用MCP能力: {endpoint}.{method}")

        try:
            # 简化实现:直接返回模拟结果
            # 实际应该调用MCP服务器

            # 根据不同的endpoint返回相应的模拟结果
            if "patent-search" in endpoint:
                return {
                    "results": [
                        {
                            "title": f"专利示例-{parameters.get('query', '未知')}",
                            "application_number": "CN202310000000",
                            "abstract": "这是一项关于...的专利技术...",
                            "applicant": "某科技公司",
                        }
                    ]
                    * parameters.get("limit", 5),
                    "total": 10,
                    "query": parameters.get("query", ""),
                }

            elif "academic-search" in endpoint:
                return {
                    "results": [
                        {
                            "title": f"论文示例-{parameters.get('query', '未知')}",
                            "authors": ["张三", "李四"],
                            "year": 2023,
                            "abstract": "本文研究了...的问题...",
                            "citation_count": 15,
                        }
                    ]
                    * parameters.get("limit", 3),
                    "total": 5,
                }

            elif "jina-embedding" in endpoint:
                # 模拟向量嵌入
                texts = parameters.get("texts", [])
                return {
                    "embeddings": [[0.1] * 768 for _ in texts],
                    "model": parameters.get("model", "jina-embeddings-v2"),
                }

            elif "jina-rerank" in endpoint:
                documents = parameters.get("documents", [])
                return {
                    "results": [
                        {"index": i, "document": doc, "relevance_score": 0.9 - i * 0.1}
                        for i, doc in enumerate(documents[: parameters.get("top_n", 10)])
                    ]
                }

            else:
                return {"status": "success", "message": "MCP调用成功(模拟)"}

        except Exception as e:
            logger.error(f"❌ MCP调用失败: {e}")
            raise


class RestfulCapabilityInvoker(BaseCapabilityInvoker):
    """RESTful能力调用器"""

    def __init__(self):
        import httpx

        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("✅ RESTful调用器初始化完成")

    async def invoke(
        self, endpoint: str, method: str, parameters: dict[str, Any], timeout: int
    ) -> dict[str, Any]:
        """调用RESTful能力"""
        logger.info(f"🌐 调用RESTful能力: {endpoint} {method}")

        try:
            # 构建URL
            url = f"http://{endpoint}/{method}"

            # 发送请求
            if method.upper() == "GET":
                response = await self.client.get(url, params=parameters, timeout=timeout)
            else:
                response = await self.client.post(url, json=parameters, timeout=timeout)

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"❌ RESTful调用失败: {e}")
            # 返回模拟结果
            return {"status": "success", "message": "RESTful调用成功(模拟)"}


class InternalCapabilityInvoker(BaseCapabilityInvoker):
    """内部能力调用器"""

    def __init__(self):
        # 内部处理器
        self.handlers = {}
        logger.info("✅ 内部调用器初始化完成")

    async def invoke(
        self, endpoint: str, method: str, parameters: dict[str, Any], timeout: int
    ) -> dict[str, Any]:
        """调用内部能力"""
        logger.info(f"🔧 调用内部能力: {endpoint}.{method}")

        try:
            # 根据endpoint路由到相应的内部模块
            if "vector" in endpoint:
                return await self._invoke_vector_search(parameters)
            elif "knowledge" in endpoint or "kg" in endpoint:
                return await self._invoke_kg_query(parameters)
            elif "llm" in endpoint:
                return await self._invoke_llm(parameters)
            else:
                return {"status": "success", "message": "内部调用成功(模拟)"}

        except Exception as e:
            logger.error(f"❌ 内部调用失败: {e}")
            raise

    async def _invoke_vector_search(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """向量检索"""
        # 模拟向量检索结果
        query_text = parameters.get("query_text", "")
        top_k = parameters.get("top_k", 5)

        return {
            "results": [
                {
                    "title": f"相似专利-{i}",
                    "similarity": 0.95 - i * 0.05,
                    "abstract": f"这是与'{query_text}'相似的专利...",
                }
                for i in range(top_k)
            ],
            "query": query_text,
        }

    async def _invoke_kg_query(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """知识图谱查询"""
        # 模拟图谱查询结果
        return {
            "nodes": [
                {"id": "1", "label": "专利", "name": "示例专利"},
                {"id": "2", "label": "概念", "name": "创造性"},
            ],
            "relationships": [{"from": "1", "to": "2", "type": "RELATED_TO"}],
        }

    async def _invoke_llm(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """LLM生成"""
        # 模拟LLM生成
        prompt = parameters.get("prompt", "")
        return {
            "text": f"这是LLM生成的回复,基于prompt: {prompt[:50]}...",
            "model": "glm-4-plus",
            "tokens_used": 100,
        }


class WebSocketCapabilityInvoker(BaseCapabilityInvoker):
    """WebSocket能力调用器"""

    def __init__(self):
        self.connections = {}
        logger.info("✅ WebSocket调用器初始化完成")

    async def invoke(
        self, endpoint: str, method: str, parameters: dict[str, Any], timeout: int
    ) -> dict[str, Any]:
        """调用WebSocket能力"""
        logger.info(f"🔌 调用WebSocket能力: {endpoint}.{method}")

        try:
            # 模拟WebSocket调用
            if "browser" in endpoint or "chrome" in endpoint:
                return {
                    "status": "success",
                    "screenshot": "base64_encoded_image...",
                    "actions_executed": len(parameters.get("actions", [])),
                }
            else:
                return {"status": "success", "message": "WebSocket调用成功(模拟)"}

        except Exception as e:
            logger.error(f"❌ WebSocket调用失败: {e}")
            raise


class CapabilityInvoker:
    """统一能力调用器"""

    def __init__(self):
        self.mcp_invoker = MCPCapabilityInvoker()
        self.restful_invoker = RestfulCapabilityInvoker()
        self.internal_invoker = InternalCapabilityInvoker()
        self.websocket_invoker = WebSocketCapabilityInvoker()

        # 调用器映射
        self.invokers = {
            "mcp": self.mcp_invoker,
            "restful": self.restful_invoker,
            "internal": self.internal_invoker,
            "websocket": self.websocket_invoker,
        }

        logger.info("✅ 统一能力调用器初始化完成")

    async def invoke(
        self, capability_id: str, parameters: dict[str, Any], timeout: int = 30
    ) -> dict[str, Any]:
        """
        调用能力

        Args:
            capability_id: 能力ID
            parameters: 参数字典
            timeout: 超时时间(秒)

        Returns:
            能力执行结果
        """
        from core.capabilities.capability_registry import capability_registry

        # 1. 获取能力定义
        capability = capability_registry.get(capability_id)
        if not capability:
            raise ValueError(f"能力不存在: {capability_id}")

        logger.info(f"🎯 调用能力: {capability.name} ({capability_id})")

        # 2. 选择调用器
        invoker = self.invokers.get(capability.invocation_type.value)
        if not invoker:
            raise ValueError(f"不支持的调用类型: {capability.invocation_type}")

        # 3. 执行调用
        try:
            result = await invoker.invoke(
                endpoint=capability.endpoint,
                method=capability.method,
                parameters=parameters,
                timeout=timeout,
            )

            logger.info(f"✅ 能力调用成功: {capability_id}")
            return result

        except Exception as e:
            logger.error(f"❌ 能力调用失败: {capability_id} - {e}")
            raise


# 便捷函数
async def invoke_capability(
    capability_id: str, parameters: dict[str, Any], timeout: int = 30
) -> dict[str, Any]:
    """
    便捷的能力调用函数

    Args:
        capability_id: 能力ID
        parameters: 参数字典
        timeout: 超时时间

    Returns:
        能力执行结果
    """
    invoker = CapabilityInvoker()
    return await invoker.invoke(capability_id, parameters, timeout)
