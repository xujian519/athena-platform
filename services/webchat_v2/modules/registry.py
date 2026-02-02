#!/usr/bin/env python3
"""
平台模块注册表
管理可用的平台模块和能力

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.0
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import time


class ModuleStatus(str, Enum):
    """模块状态"""
    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ModuleDefinition:
    """模块定义"""
    name: str                                    # 模块名称
    display_name: str                            # 显示名称
    description: str                             # 描述
    category: str                                # 分类 (patent/knowledge/tool)
    version: str = "1.0.0"
    enabled: bool = True

    # 能力声明
    actions: List[str] = field(default_factory=list)
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # 运行时信息
    status: ModuleStatus = ModuleStatus.AVAILABLE
    health_check_url: Optional[str] = None

    # 处理器
    handler: Optional[Callable] = None


@dataclass
class InvokeRequest:
    """调用请求"""
    session_id: str
    module: str
    action: str
    params: Dict[str, Any]
    user_id: str
    request_id: Optional[str] = None


@dataclass
class InvokeResult:
    """调用结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    module: str = ""
    action: str = ""
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PlatformModuleRegistry:
    """平台模块注册表"""

    def __init__(self):
        self._modules: Dict[str, ModuleDefinition] = {}
        self._initialize_builtin_modules()

    def _initialize_builtin_modules(self) -> None:
        """初始化内置模块"""
        # 专利搜索模块
        self.register(ModuleDefinition(
            name="patent.search",
            display_name="专利搜索",
            description="Google Patents搜索",
            category="patent",
            actions=["search", "advanced_search", "batch_search"],
            parameters={
                "search": {
                    "query": {"type": "string", "required": True},
                    "limit": {"type": "integer", "required": False, "default": 10},
                },
            },
        ))

        # 专利分析模块
        self.register(ModuleDefinition(
            name="patent.analyze",
            display_name="专利分析",
            description="BERT模型深度分析",
            category="patent",
            actions=["analyze", "compare", "assess_value"],
            parameters={
                "analyze": {
                    "patent_id": {"type": "string", "required": True},
                },
            },
        ))

        # 知识图谱模块
        self.register(ModuleDefinition(
            name="knowledge.graph",
            display_name="知识图谱",
            description="Neo4j知识图谱查询",
            category="knowledge",
            actions=["query", "explore", "find_path"],
        ))

        # 向量搜索模块
        self.register(ModuleDefinition(
            name="knowledge.vector",
            display_name="向量搜索",
            description="Qdrant语义检索",
            category="knowledge",
            actions=["search", "similarity", "hybrid"],
            parameters={
                "search": {
                    "query": {"type": "string", "required": True},
                    "top_k": {"type": "integer", "required": False, "default": 5},
                },
            },
        ))

        # 数据查询模块
        self.register(ModuleDefinition(
            name="knowledge.sql",
            display_name="数据查询",
            description="PostgreSQL查询",
            category="knowledge",
            actions=["query", "aggregate", "join"],
        ))

        # 对话导出模块
        self.register(ModuleDefinition(
            name="tool.webchat",
            display_name="对话导出",
            description="导出对话记录",
            category="tool",
            actions=["export_session", "export_all", "export_filtered"],
        ))

        # 报告生成模块
        self.register(ModuleDefinition(
            name="tool.report",
            display_name="报告生成",
            description="生成分析报告",
            category="tool",
            actions=["generate", "preview", "schedule"],
        ))

        # 数据导出模块
        self.register(ModuleDefinition(
            name="tool.export",
            display_name="数据导出",
            description="导出各类数据",
            category="tool",
            actions=["export", "bulk_export", "schedule_export"],
        ))

    def register(self, definition: ModuleDefinition) -> bool:
        """
        注册模块

        Args:
            definition: 模块定义

        Returns:
            是否成功
        """
        self._modules[definition.name] = definition
        return True

    def register_handler(
        self,
        module: str,
        handler: Callable
    ) -> bool:
        """
        注册处理器

        Args:
            module: 模块名称
            handler: 处理器函数

        Returns:
            是否成功
        """
        if module not in self._modules:
            return False
        self._modules[module].handler = handler
        return True

    def get_module(self, name: str) -> Optional[ModuleDefinition]:
        """
        获取模块定义

        Args:
            name: 模块名称

        Returns:
            模块定义或None
        """
        return self._modules.get(name)

    def list_modules(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[ModuleDefinition]:
        """
        列出模块

        Args:
            category: 分类过滤
            enabled_only: 只显示启用的模块

        Returns:
            模块列表
        """
        modules = list(self._modules.values())

        if category:
            modules = [m for m in modules if m.category == category]

        if enabled_only:
            modules = [m for m in modules if m.enabled]

        return modules

    def get_handler(self, module: str, action: str) -> Optional[Callable]:
        """
        获取处理器

        Args:
            module: 模块名称
            action: 操作名称

        Returns:
            处理器函数或None
        """
        mod_def = self._modules.get(module)
        if not mod_def:
            return None

        # 模块级别的处理器
        if mod_def.handler:
            return mod_def.handler

        # TODO: 支持action级别的处理器
        return None

    def update_status(
        self,
        module: str,
        status: ModuleStatus
    ) -> bool:
        """
        更新模块状态

        Args:
            module: 模块名称
            status: 新状态

        Returns:
            是否成功
        """
        if module not in self._modules:
            return False
        self._modules[module].status = status
        return True

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set(m.category for m in self._modules.values())
        return sorted(categories)
