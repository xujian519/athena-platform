#!/usr/bin/env python3
"""
能力注册中心
Capability Registry

管理平台所有原子化能力的注册、发现和调用
"""

from __future__ import annotations
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class InvocationType(Enum):
    """调用类型"""

    MCP = "mcp"
    RESTFUL = "restful"
    INTERNAL = "internal"
    WEBSOCKET = "websocket"


@dataclass
class CapabilityDefinition:
    """能力定义"""

    capability_id: str
    name: str
    description: str

    # 调用配置
    invocation_type: InvocationType
    endpoint: str
    method: str = "GET"

    # 参数定义
    parameters: dict[str, dict[str, Any]] = field(default_factory=dict)

    # 输出格式
    output_format: dict[str, str] = field(default_factory=dict)

    # 元数据
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    is_active: bool = True

    # 性能指标
    avg_response_time: float = 0.0
    success_rate: float = 1.0

    # 处理器(用于internal类型)
    handler: Callable | None = None


class CapabilityRegistry:
    """能力注册中心"""

    _instance = None
    _capabilities: dict[str, CapabilityDefinition] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._capabilities = {}
        self._initialized = True
        self._register_builtin_capabilities()
        logger.info("✅ 能力注册中心初始化完成")

    def _register_builtin_capabilities(self):
        """注册内置能力"""
        # 专利相关能力
        self.register(
            CapabilityDefinition(
                capability_id="patent_search_cn",
                name="中国专利搜索",
                description="搜索2800万+中国专利数据",
                invocation_type=InvocationType.MCP,
                endpoint="patent-search-mcp-server",
                method="search_cn_patents",
                parameters={
                    "query": {"type": "string", "required": True, "description": "搜索关键词"},
                    "limit": {"type": "integer", "required": False, "default": 10},
                },
                category="patent",
                tags=["search", "patent", "cn"],
                avg_response_time=0.5,
            )
        )

        self.register(
            CapabilityDefinition(
                capability_id="patent_download",
                name="专利文档下载",
                description="下载专利全文文档",
                invocation_type=InvocationType.MCP,
                endpoint="patent-downloader-mcp-server",
                method="download_patent",
                parameters={
                    "patent_id": {"type": "string", "required": True, "description": "专利号"}
                },
                category="patent",
                tags=["download", "patent", "document"],
            )
        )

        self.register(
            CapabilityDefinition(
                capability_id="academic_search",
                name="学术论文搜索",
                description="检索学术论文和引用关系",
                invocation_type=InvocationType.MCP,
                endpoint="academic-search-mcp-server",
                method="search_papers",
                parameters={
                    "query": {"type": "string", "required": True, "description": "搜索关键词"},
                    "limit": {"type": "integer", "required": False, "default": 5},
                },
                category="academic",
                tags=["search", "academic", "paper"],
            )
        )

        self.register(
            CapabilityDefinition(
                capability_id="jina_embedding",
                name="Jina向量嵌入",
                description="生成文本向量嵌入",
                invocation_type=InvocationType.MCP,
                endpoint="jina-ai-mcp-server",
                method="embedding",
                parameters={
                    "texts": {"type": "array", "required": True, "description": "文本列表"},
                    "model": {"type": "string", "required": False, "default": "jina-embeddings-v2"},
                },
                category="ai",
                tags=["embedding", "vector", "ai"],
            )
        )

        self.register(
            CapabilityDefinition(
                capability_id="jina_rerank",
                name="Jina结果重排",
                description="重新排序搜索结果",
                invocation_type=InvocationType.MCP,
                endpoint="jina-ai-mcp-server",
                method="rerank",
                parameters={
                    "query": {"type": "string", "required": True, "description": "查询文本"},
                    "documents": {"type": "array", "required": True, "description": "文档列表"},
                    "top_n": {"type": "integer", "required": False, "default": 10},
                },
                category="ai",
                tags=["rerank", "ai", "search"],
            )
        )

        self.register(
            CapabilityDefinition(
                capability_id="patent_vector_search",
                name="专利向量检索",
                description="基于向量的语义搜索",
                invocation_type=InvocationType.INTERNAL,
                endpoint="core/vector",
                method="vector_search",
                parameters={
                    "query_text": {"type": "string", "required": True, "description": "查询文本"},
                    "top_k": {"type": "integer", "required": False, "default": 5},
                },
                category="patent",
                tags=["search", "vector", "semantic"],
            )
        )

        # 专业法律写作能力
        self.register(
            CapabilityDefinition(
                capability_id="legal_writing",
                name="专业法律写作",
                description="生成高质量的法律研究报告、法律文书等专业文档",
                invocation_type=InvocationType.INTERNAL,
                endpoint="core.capabilities.legal_writing_capability",
                method="generate",
                parameters={
                    "topic": {"type": "string", "required": True, "description": "文档主题"},
                    "task_type": {
                        "type": "string",
                        "required": False,
                        "default": "research_report",
                        "description": "文档类型: research_report/legal_brief/opinion_letter/oa_response/judgment",
                    },
                    "role": {
                        "type": "string",
                        "required": False,
                        "default": "scholar",
                        "description": "写作角色: patent_attorney/lawyer/judge/scholar",
                    },
                    "word_count": {
                        "type": "integer",
                        "required": False,
                        "default": 5000,
                        "description": "目标字数",
                    },
                    "structure": {"type": "array", "required": False, "description": "自定义结构"},
                    "context": {"type": "object", "required": False, "description": "额外上下文"},
                },
                category="legal",
                tags=["writing", "legal", "document", "research"],
                avg_response_time=30.0,
                version="1.0.0",
            )
        )

        self.register(
            CapabilityDefinition(
                capability_id="patent_kg_query",
                name="专利图谱查询",
                description="知识图谱查询和推理",
                invocation_type=InvocationType.INTERNAL,
                endpoint="core/knowledge_graph",
                method="query",
                parameters={
                    "cypher": {"type": "string", "required": True, "description": "Cypher查询"},
                    "params": {"type": "object", "required": False},
                },
                category="patent",
                tags=["graph", "kg", "reasoning"],
            )
        )

        self.register(
            CapabilityDefinition(
                capability_id="browser_automate",
                name="浏览器自动化",
                description="网页自动化操作",
                invocation_type=InvocationType.WEBSOCKET,
                endpoint="ws://localhost:8030",
                method="automate",
                parameters={
                    "actions": {"type": "array", "required": True, "description": "操作列表"}
                },
                category="automation",
                tags=["browser", "automation", "web"],
            )
        )

        self.register(
            CapabilityDefinition(
                capability_id="chrome_control",
                name="Chrome控制",
                description="Chrome浏览器控制",
                invocation_type=InvocationType.MCP,
                endpoint="chrome-mcp-server",
                method="navigate",
                parameters={
                    "url": {"type": "string", "required": True, "description": "URL"},
                    "actions": {"type": "array", "required": False},
                },
                category="automation",
                tags=["browser", "chrome", "automation"],
            )
        )

        logger.info(f"✅ 已注册 {len(self._capabilities)} 个内置能力")

    def register(self, capability: CapabilityDefinition):
        """注册能力"""
        self._capabilities[capability.capability_id] = capability
        logger.info(f"✅ 注册能力: {capability.capability_id} - {capability.name}")

    def get(self, capability_id: str) -> CapabilityDefinition | None:
        """获取能力定义"""
        return self._capabilities.get(capability_id)

    def find_by_tags(self, tags: list[str]) -> list[CapabilityDefinition]:
        """按标签查找能力"""
        results = []
        for capability in self._capabilities.values():
            if any(tag in capability.tags for tag in tags):
                results.append(capability)
        return results

    def find_by_category(self, category: str) -> list[CapabilityDefinition]:
        """按类别查找能力"""
        return [cap for cap in self._capabilities.values() if cap.category == category]

    def recommend_for_scenario(self, domain: str, task_type: str) -> list[CapabilityDefinition]:
        """为场景推荐能力"""
        # 简单的推荐逻辑
        recommendations = []

        # 专利领域
        if domain == "patent":
            patent_caps = self.find_by_category("patent")
            recommendations.extend(patent_caps)

            if task_type == "creativity_analysis":
                # 创造性分析需要学术搜索
                academic_caps = self.find_by_category("academic")
                recommendations.extend(academic_caps)

        # 商标领域
        elif domain == "trademark":
            # 可以添加商标相关能力
            pass

        return recommendations

    def list_all(self) -> list[CapabilityDefinition]:
        """列出所有能力"""
        return list(self._capabilities.values())

    def list_active(self) -> list[CapabilityDefinition]:
        """列出活跃能力"""
        return [cap for cap in self._capabilities.values() if cap.is_active]


# 全局单例
capability_registry = CapabilityRegistry()


# 便捷函数
def register_capability(
    capability_id: str, name: str, invocation_type: str, endpoint: str, **kwargs
) -> None:
    """便捷的注册函数"""
    capability = CapabilityDefinition(
        capability_id=capability_id,
        name=name,
        description=kwargs.get("description", ""),
        invocation_type=InvocationType(invocation_type),
        endpoint=endpoint,
        method=kwargs.get("method", "GET"),
        parameters=kwargs.get("parameters", {}),
        category=kwargs.get("category", "general"),
        tags=kwargs.get("tags", []),
        version=kwargs.get("version", "1.0.0"),
    )
    capability_registry.register(capability)


def get_capability(capability_id: str) -> CapabilityDefinition | None:
    """获取能力"""
    return capability_registry.get(capability_id)


def find_capabilities(tags: list[str] = None, category: str | None = None) -> list[CapabilityDefinition]:
    """查找能力"""
    if tags:
        return capability_registry.find_by_tags(tags)
    elif category:
        return capability_registry.find_by_category(category)
    else:
        return capability_registry.list_all()
