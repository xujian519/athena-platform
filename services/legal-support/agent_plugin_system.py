#!/usr/bin/env python3
"""
智能体插件系统
为所有智能体提供法律能力插件
作者: 小诺·双鱼座
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from dynamic_prompt_generator import LegalPromptGenerator
from graph_query_enhancer import GraphQueryEnhancer
from legal_kg_support import LegalKnowledgeGraphSupport

logger = logging.getLogger(__name__)

class PluginType(Enum):
    """插件类型"""
    SEARCH = "search"
    QA = "qa"
    PROMPT = "prompt"
    REASONING = "reasoning"
    ANALYSIS = "analysis"

@dataclass
class PluginCapability:
    """插件能力描述"""
    name: str
    description: str
    input_types: list[str]
    output_types: list[str]
    parameters: dict[str, Any]
    examples: list[dict]

@dataclass
class PluginResult:
    """插件执行结果"""
    success: bool
    data: Any
    error: str | None = None
    metadata: dict | None = None

class BasePlugin(ABC):
    """插件基类"""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.enabled = True
        self.capabilities = []

    @abstractmethod
    async def execute(self, *args, **kwargs) -> PluginResult:
        """执行插件"""
        pass

    @abstractmethod
    def get_capabilities(self) -> list[PluginCapability]:
        """获取插件能力"""
        pass

    def validate_input(self, input_data: Any) -> bool:
        """验证输入数据"""
        return True

    def get_info(self) -> dict:
        """获取插件信息"""
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "capabilities": [vars(cap) for cap in self.get_capabilities()]
        }

class LegalSearchPlugin(BasePlugin):
    """法律搜索插件"""

    def __init__(self, kg_support: LegalKnowledgeGraphSupport):
        super().__init__("legal_search", "1.0.0")
        self.kg_support = kg_support

    async def execute(self, query: str, search_type: str = "hybrid", top_k: int = 10) -> PluginResult:
        """执行法律搜索"""
        try:
            if search_type == "vector":
                results = self.kg_support.search_by_vector(query, top_k)
            elif search_type == "graph":
                results = self.kg_support.search_by_graph(query)
            else:
                results = self.kg_support.hybrid_search(query, top_k)

            return PluginResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "count": len(results)
                }
            )
        except Exception as e:
            logger.error(f"搜索插件执行失败: {e}")
            return PluginResult(success=False, error=str(e))

    def get_capabilities(self) -> list[PluginCapability]:
        return [
            PluginCapability(
                name="法律搜索",
                description="在法律知识库中搜索相关信息",
                input_types=["text"],
                output_types=["search_results"],
                parameters={
                    "query": {"type": "string", "required": True},
                    "search_type": {"type": "string", "enum": ["vector", "graph", "hybrid"]},
                    "top_k": {"type": "integer", "default": 10}
                },
                examples=[
                    {
                        "input": {"query": "离婚财产分割", "search_type": "hybrid"},
                        "output": "相关法律条文和案例"
                    }
                ]
            )
        ]

class LegalQAPlugin(BasePlugin):
    """法律问答插件"""

    def __init__(self, kg_support: LegalKnowledgeGraphSupport, prompt_generator: LegalPromptGenerator):
        super().__init__("legal_qa", "1.0.0")
        self.kg_support = kg_support
        self.prompt_generator = prompt_generator

    async def execute(self, query: str, context: dict = None) -> PluginResult:
        """执行法律问答"""
        try:
            # 获取对话支持
            self.kg_support.get_conversation_support(query)

            # 生成动态提示词
            prompt_result = self.prompt_generator.generate_prompt(query, context)

            return PluginResult(
                success=True,
                data={
                    "query": query,
                    "prompt": prompt_result["prompt"],
                    "legal_basis": prompt_result["legal_basis"],
                    "confidence": prompt_result["confidence"],
                    "suggestions": self.prompt_generator.get_prompt_suggestions(query)
                }
            )
        except Exception as e:
            logger.error(f"问答插件执行失败: {e}")
            return PluginResult(success=False, error=str(e))

    def get_capabilities(self) -> list[PluginCapability]:
        return [
            PluginCapability(
                name="法律问答",
                description="提供专业的法律问答服务",
                input_types=["question"],
                output_types=["answer", "legal_basis"],
                parameters={
                    "query": {"type": "string", "required": True},
                    "context": {"type": "object", "optional": True}
                },
                examples=[
                    {
                        "input": {"query": "劳动合同解除需要什么条件？"},
                        "output": "相关法律规定和操作建议"
                    }
                ]
            )
        ]

class LegalReasoningPlugin(BasePlugin):
    """法律推理插件"""

    def __init__(self, graph_enhancer: GraphQueryEnhancer):
        super().__init__("legal_reasoning", "1.0.0")
        self.graph_enhancer = graph_enhancer

    async def execute(self, query: str, reasoning_type: str = "chain") -> PluginResult:
        """执行法律推理"""
        try:
            # 增强查询
            enhanced = self.graph_enhancer.enhance_query(query)

            # 执行推理
            if enhanced["query_type"] == "reasoning":
                reasoning_chain = enhanced.get("reasoning_chain", [])
                confidence = enhanced.get("confidence", 0.5)

                # 执行推理链
                results = []
                for step in reasoning_chain:
                    step_results = self.graph_enhancer.execute_enhanced_query({"enhanced_queries": [step]})
                    results.append(step_results)

                return PluginResult(
                    success=True,
                    data={
                        "query": query,
                        "reasoning_chain": reasoning_chain,
                        "results": results,
                        "confidence": confidence
                    }
                )
            else:
                # 使用查询增强
                results = self.graph_enhancer.execute_enhanced_query(enhanced)
                return PluginResult(
                    success=True,
                    data={
                        "query": query,
                        "results": results,
                        "query_type": enhanced["query_type"]
                    }
                )
        except Exception as e:
            logger.error(f"推理插件执行失败: {e}")
            return PluginResult(success=False, error=str(e))

    def get_capabilities(self) -> list[PluginCapability]:
        return [
            PluginCapability(
                name="法律推理",
                description="基于知识图谱进行法律推理",
                input_types=["question", "facts"],
                output_types=["reasoning", "conclusions"],
                parameters={
                    "query": {"type": "string", "required": True},
                    "reasoning_type": {"type": "string", "enum": ["chain", "tree", "graph"]},
                    "depth": {"type": "integer", "default": 3}
                },
                examples=[
                    {
                        "input": {"query": "如果合同违约会承担什么责任？"},
                        "output": "违约责任推理过程"
                    }
                ]
            )
        ]

class DocumentAnalysisPlugin(BasePlugin):
    """文档分析插件"""

    def __init__(self, kg_support: LegalKnowledgeGraphSupport):
        super().__init__("document_analysis", "1.0.0")
        self.kg_support = kg_support

    async def execute(self, document: str, analysis_type: str = "extract") -> PluginResult:
        """执行文档分析"""
        try:
            # 提取关键信息
            if analysis_type == "extract":
                # 提取法律实体和关系
                entities = self._extract_legal_entities(document)
                relations = self._extract_legal_relations(document)

                # 搜索相关法律
                legal_references = []
                for entity in entities[:5]:
                    refs = self.kg_support.hybrid_search(entity, top_k=3)
                    legal_references.extend(refs)

                return PluginResult(
                    success=True,
                    data={
                        "entities": entities,
                        "relations": relations,
                        "legal_references": legal_references[:10],
                        "analysis_type": analysis_type
                    }
                )
            else:
                return PluginResult(success=False, error=f"不支持的分析类型: {analysis_type}")

        except Exception as e:
            logger.error(f"文档分析插件执行失败: {e}")
            return PluginResult(success=False, error=str(e))

    def _extract_legal_entities(self, text: str) -> list[str]:
        """提取法律实体"""
        import re
        patterns = [
            r'《([^》]+法)》',
            r'《([^》]+条例)》',
            r'《([^》]+规定)》',
            r'第([一二三四五六七八九十百千万\d]+)条',
            r'([一二三四五六七八九十百千万\d]+年)',
        ]

        entities = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)

        return list(entities)

    def _extract_legal_relations(self, text: str) -> list[dict]:
        """提取法律关系"""
        relations = []
        # 简化实现，可以进一步优化
        if "违约" in text:
            relations.append({"type": "违约责任", "confidence": 0.8})
        if "侵权" in text:
            relations.append({"type": "侵权责任", "confidence": 0.8})
        if "解除" in text and "合同" in text:
            relations.append({"type": "合同解除", "confidence": 0.7})

        return relations

    def get_capabilities(self) -> list[PluginCapability]:
        return [
            PluginCapability(
                name="文档分析",
                description="分析法律文档并提取关键信息",
                input_types=["document"],
                output_types=["entities", "relations", "references"],
                parameters={
                    "document": {"type": "string", "required": True},
                    "analysis_type": {"type": "string", "enum": ["extract", "summarize"]}
                },
                examples=[
                    {
                        "input": {"document": "租赁合同文本", "analysis_type": "extract"},
                        "output": "合同关键条款和法律风险"
                    }
                ]
            )
        ]

class PluginManager:
    """插件管理器"""

    def __init__(self):
        self.plugins: dict[str, BasePlugin] = {}
        self.plugin_registry: dict[str, type] = {}
        self.middleware: list[Callable] = []

    def register_plugin(self, plugin: BasePlugin):
        """注册插件"""
        self.plugins[plugin.name] = plugin
        logger.info(f"插件 {plugin.name} 已注册")

    def unregister_plugin(self, plugin_name: str):
        """注销插件"""
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            logger.info(f"插件 {plugin_name} 已注销")

    def get_plugin(self, plugin_name: str) -> BasePlugin | None:
        """获取插件"""
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> list[dict]:
        """列出所有插件"""
        return [plugin.get_info() for plugin in self.plugins.values()]

    def get_plugins_by_type(self, plugin_type: PluginType) -> list[BasePlugin]:
        """根据类型获取插件"""
        # 简化实现，可以基于插件名称或能力判断
        type_mapping = {
            PluginType.SEARCH: ["legal_search"],
            PluginType.QA: ["legal_qa"],
            PluginType.REASONING: ["legal_reasoning"],
            PluginType.ANALYSIS: ["document_analysis"]
        }

        plugin_names = type_mapping.get(plugin_type, [])
        return [self.plugins[name] for name in plugin_names if name in self.plugins]

    async def execute_plugin(self, plugin_name: str, *args, **kwargs) -> PluginResult:
        """执行插件"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return PluginResult(success=False, error=f"插件 {plugin_name} 未找到")

        if not plugin.enabled:
            return PluginResult(success=False, error=f"插件 {plugin_name} 已禁用")

        # 执行中间件
        for middleware in self.middleware:
            result = await middleware(plugin_name, *args, **kwargs)
            if not result.success:
                return result

        # 执行插件
        return await plugin.execute(*args, **kwargs)

    def add_middleware(self, middleware: Callable):
        """添加中间件"""
        self.middleware.append(middleware)

    def enable_plugin(self, plugin_name: str):
        """启用插件"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True

    def disable_plugin(self, plugin_name: str):
        """禁用插件"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False

# Agent类 - 使用插件的智能体
class LegalAgent:
    """法律智能体"""

    def __init__(self, agent_id: str, plugin_manager: PluginManager):
        self.agent_id = agent_id
        self.plugin_manager = plugin_manager
        self.loaded_plugins = []
        self.capabilities = []

    def load_plugin(self, plugin_name: str):
        """加载插件"""
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if plugin:
            self.loaded_plugins.append(plugin_name)
            self.capabilities.extend([cap.name for cap in plugin.get_capabilities()])
            logger.info(f"智能体 {self.agent_id} 加载插件 {plugin_name}")

    def unload_plugin(self, plugin_name: str):
        """卸载插件"""
        if plugin_name in self.loaded_plugins:
            self.loaded_plugins.remove(plugin_name)
            # 更新能力列表
            self._update_capabilities()
            logger.info(f"智能体 {self.agent_id} 卸载插件 {plugin_name}")

    def _update_capabilities(self):
        """更新能力列表"""
        self.capabilities = []
        for plugin_name in self.loaded_plugins:
            plugin = self.plugin_manager.get_plugin(plugin_name)
            if plugin:
                self.capabilities.extend([cap.name for cap in plugin.get_capabilities()])

    async def process_request(self, request_type: str, *args, **kwargs) -> dict:
        """处理请求"""
        # 根据请求类型选择合适的插件
        plugin_mapping = {
            "search": "legal_search",
            "qa": "legal_qa",
            "reasoning": "legal_reasoning",
            "analysis": "document_analysis"
        }

        plugin_name = plugin_mapping.get(request_type)
        if not plugin_name:
            return {"error": f"不支持的请求类型: {request_type}"}

        if plugin_name not in self.loaded_plugins:
            return {"error": f"插件 {plugin_name} 未加载"}

        # 执行插件
        result = await self.plugin_manager.execute_plugin(plugin_name, *args, **kwargs)

        return {
            "agent_id": self.agent_id,
            "plugin_used": plugin_name,
            "result": result.__dict__
        }

    def get_info(self) -> dict:
        """获取智能体信息"""
        return {
            "agent_id": self.agent_id,
            "loaded_plugins": self.loaded_plugins,
            "capabilities": self.capabilities
        }


# 初始化插件系统
def initialize_plugin_system():
    """初始化插件系统"""
    # 创建核心组件
    kg_support = LegalKnowledgeGraphSupport()
    prompt_generator = LegalPromptGenerator(kg_support)
    graph_enhancer = GraphQueryEnhancer(kg_support)

    # 创建插件管理器
    plugin_manager = PluginManager()

    # 注册核心插件
    plugin_manager.register_plugin(LegalSearchPlugin(kg_support))
    plugin_manager.register_plugin(LegalQAPlugin(kg_support, prompt_generator))
    plugin_manager.register_plugin(LegalReasoningPlugin(graph_enhancer))
    plugin_manager.register_plugin(DocumentAnalysisPlugin(kg_support))

    return plugin_manager


# 使用示例
async def main():
    # 初始化插件系统
    plugin_manager = initialize_plugin_system()

    # 列出所有插件
    print("\n=== 已注册的插件 ===")
    for plugin_info in plugin_manager.list_plugins():
        print(f"- {plugin_info['name']}: {plugin_info['version']}")

    # 创建智能体
    agent = LegalAgent("legal_assistant_001", plugin_manager)
    agent.load_plugin("legal_search")
    agent.load_plugin("legal_qa")

    # 处理请求
    print("\n=== 处理搜索请求 ===")
    search_result = await agent.process_request("search", query="劳动合同解除")
    print(json.dumps(search_result, ensure_ascii=False, indent=2))

    print("\n=== 处理问答请求 ===")
    qa_result = await agent.process_request("qa", query="租赁合同需要注意什么？")
    print(json.dumps(qa_result, ensure_ascii=False, indent=2))

    # 关闭系统
    kg_support = plugin_manager.get_plugin("legal_search").kg_support
    kg_support.close()


if __name__ == "__main__":
    asyncio.run(main())
