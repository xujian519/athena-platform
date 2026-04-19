#!/usr/bin/env python3
"""
Athena工具注册中心
负责管理、注册和调度所有可用工具
"""

from __future__ import annotations
import importlib
import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class ToolStatus(Enum):
    """工具状态"""

    AVAILABLE = "available"  # 可用
    ERROR = "error"  # 错误
    DEPRECATED = "deprecated"  # 已弃用
    TESTING = "testing"  # 测试中


class ToolPriority(Enum):
    """工具优先级"""

    CRITICAL = "critical"  # 关键工具
    HIGH = "high"  # 高优先级
    MEDIUM = "medium"  # 中等优先级
    LOW = "low"  # 低优先级


class ToolCategory(Enum):
    """工具分类"""

    # 核心工具
    CORE_GOVERNANCE = "core.governance"  # 核心治理
    CORE_AGENT = "core.agent"  # 核心智能体
    CORE_SEARCH = "core.search"  # 核心搜索
    CORE_STORAGE = "core.storage"  # 核心存储
    CORE_MONITORING = "core.monitoring"  # 核心监控
    CORE_OPTIMIZATION = "core.optimization"  # 核心优化

    # 服务工具
    SERVICE_BROWSER = "service.browser"  # 浏览器自动化
    SERVICE_PATENT = "service.patent"  # 专利服务
    SERVICE_LEGAL = "service.legal"  # 法律服务
    SERVICE_KNOWLEDGE = "service.knowledge"  # 知识库服务

    # MCP工具
    MCP_ACADEMIC = "mcp.academic"  # 学术搜索
    MCP_PATENT = "mcp.patent"  # 专利下载
    MCP_GEO = "mcp.geo"  # 地图服务

    # 应用工具
    APP_XIAONUO = "app.xiaonuo"  # 小诺应用


@dataclass
class ToolInfo:
    """工具信息"""

    name: str  # 工具名称
    module_path: str  # 模块路径
    file_path: str  # 文件路径
    category: ToolCategory  # 分类
    status: ToolStatus  # 状态
    priority: ToolPriority  # 优先级
    description: str = ""  # 描述
    version: str = "1.0.0"  # 版本
    dependencies: list[str] | None = None  # 依赖
    metadata: dict[str, Any] | None = None  # 元数据

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class ToolRegistryCenter:
    """工具注册中心"""

    # 已知的核心工具列表(基于测试通过的93个工具)
    PRODUCTION_TOOLS = {
        # 核心工具组
        "core.governance": [
            "ReActExecutor",
            "ToolManager",
            "ToolCallManager",
            "MonitoredToolCallManager",
        ],
        "core.search": [
            "GoogleScholarSearchTool",
            "RealWebSearchAdapter",
            "RealPatentSearchAdapter",
            "AdaptedWebSearchManager",
        ],
        "core.storage": [
            "CacheManager",
            "EmbeddingManager",
            "PostgreSQLManager",
            "NebulaGraphManager",
            "DatabaseManager",
            "execute_query",
        ],
        "core.monitoring": [
            "AlertManager",
            "ProgressLogHandler",
        ],
        "core.optimization": [
            "XiaonuoOptimizationManager",
            "StudyManager",
            "FaultToleranceManager",
            "execute_with_fallback",
            "execute_with_retry",
        ],
        # 浏览器自动化(只保留存在的工具)
        "service.browser": [
            "BrowserAutomationTool",
            "AthenaPlaywrightAgent",
            "AthenaBrowserAgent",  # 已修复logger问题
        ],
        # 专利工具
        "service.patent": [
            "EnhancedPatentCrawler",
            "EnhancedPatentSearchTool",
            "ProductionPatentSearchTool",
            "LangChainPatentSearchTool",
            "PDFPatentParser",
            "execute_novelty_analysis",
            "PatentServiceManager",
        ],
        # 智能体
        "core.agent": [
            "BaseAgent",
            "AthenaCoreAgent",
            "XiaonaFamilyAgent",
            "XuNuoSearchAgent",
            "XiaonaAgent",
        ],
        # NLP工具(更新正确路径)
        "module.nlp": [
            "XiaonuoNLPService",  # 实际路径: modules.nlp.xiaonuo_nlp_deployment.xiaonuo_nlp_service
        ],
        # 存储工具(更新正确路径)
        "module.storage": [
            "SimplifiedStorageManager",  # 实际路径: modules.storage.storage-system.api.simplified_storage
        ],
        # MCP工具
        "mcp.academic": [
            "search_papers",
            "get_paper_metadata",
            "search_by_author",
        ],
        "mcp.patent": [
            "search_cn_patents",
            "search_us_patents",
            "get_cn_patent_by_id",
        ],
        "mcp.geo": [
            "POISearchTool",
            "GeocodingTool",
            "TrafficServiceTool",
        ],
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tools: dict[str, ToolInfo] = {}
        self.category_index: dict[ToolCategory, list[str]] = {}
        self.status_index: dict[ToolStatus, list[str]] = {}
        self._load_tools()

    def _load_tools(self):
        """加载工具配置"""
        logger.info("📦 加载工具注册配置...")

        # 从PRODUCTION_TOOLS构建工具信息
        for category_name, tool_names in self.PRODUCTION_TOOLS.items():
            try:
                category = ToolCategory(category_name)
                is_core = category_name.startswith("core")
            except ValueError:
                # 如果不在枚举中,使用字符串
                category = category_name  # type: ignore
                is_core = category_name.startswith("core")

            for tool_name in tool_names:
                tool_info = ToolInfo(
                    name=tool_name,
                    module_path=self._get_module_path(category_name, tool_name),
                    file_path=self._guess_file_path(category_name, tool_name),
                    category=category,  # type: ignore
                    status=ToolStatus.AVAILABLE,
                    priority=ToolPriority.HIGH if is_core else ToolPriority.MEDIUM,
                    description=f"{tool_name} - {category_name}工具",
                )

                self.register_tool(tool_info)

        logger.info(f"✅ 已加载 {len(self.tools)} 个工具")

    def _get_module_path(self, category: str, tool_name: str) -> str:
        """根据类别和工具名生成模块路径"""
        # 特殊处理需要自定义路径的工具
        special_cases = {
            "XiaonuoNLPService": "modules.nlp.xiaonuo_nlp_deployment.xiaonuo_nlp_service",
            "SimplifiedStorageManager": "modules.storage.storage_system.api.simplified_storage",
        }

        if tool_name in special_cases:
            return special_cases[tool_name]

        # 默认:category.tool_name格式
        return f"{category}.{tool_name.lower()}"

    def _guess_file_path(self, category: str, tool_name: str) -> str:
        """根据类别和工具名猜测文件路径"""
        category_parts = category.split(".")

        if category_parts[0] == "core":
            return f"core/{category_parts[1]}/{tool_name.lower()}.py"

        elif category_parts[0] == "service":
            service_map = {
                "browser": "browser_automation_service",
                "patent": "yunpat_agent",
                "legal": "legal-support",  # 更新: laws_knowledge_base已废弃
            }
            service_dir = service_map.get(category_parts[1], category_parts[1])
            return f"services/{service_dir}/{tool_name.lower()}.py"

        elif category_parts[0] == "mcp":
            mcp_map = {
                "academic": "academic-search-mcp-server",
                "patent": "patent-search-mcp-server",
                "geo": "gaode-mcp-server",
            }
            mcp_dir = mcp_map.get(category_parts[1], category_parts[1])
            return f"mcp-servers/{mcp_dir}/{tool_name.lower()}.py"

        elif category_parts[0] == "module":
            # 处理特殊路径
            if category_parts[1] == "nlp" and tool_name == "XiaonuoNLPService":
                return "modules/nlp/xiaonuo_nlp_deployment/xiaonuo_nlp_service.py"
            elif category_parts[1] == "storage" and tool_name == "SimplifiedStorageManager":
                return "modules/storage/storage-system/api/simplified_storage.py"
            else:
                return f"modules/{category_parts[1]}/{tool_name.lower()}.py"

        else:
            return f"{category.replace('.', '/')}/{tool_name.lower()}.py"

    def register_tool(self, tool_info: ToolInfo):
        """注册工具"""
        self.tools[tool_info.name] = tool_info

        # 更新分类索引
        if tool_info.category not in self.category_index:
            self.category_index[tool_info.category] = []
        self.category_index[tool_info.category].append(tool_info.name)

        # 更新状态索引
        if tool_info.status not in self.status_index:
            self.status_index[tool_info.status] = []
        self.status_index[tool_info.status].append(tool_info.name)

    def get_tool(self, tool_name: str) -> ToolInfo | None:
        """获取工具信息"""
        return self.tools.get(tool_name)

    def get_tools_by_category(self, category: ToolCategory) -> list[ToolInfo]:
        """按类别获取工具"""
        tool_names = self.category_index.get(category, [])
        return [self.tools[name] for name in tool_names]

    def get_tools_by_status(self, status: ToolStatus) -> list[ToolInfo]:
        """按状态获取工具"""
        tool_names = self.status_index.get(status, [])
        return [self.tools[name] for name in tool_names]

    def import_tool(self, tool_name: str):
        """动态导入工具"""
        tool_info = self.get_tool(tool_name)
        if not tool_info:
            raise ValueError(f"工具未注册: {tool_name}")

        if tool_info.status != ToolStatus.AVAILABLE:
            raise RuntimeError(f"工具不可用: {tool_name} (状态: {tool_info.status.value})")

        try:
            module = importlib.import_module(tool_info.module_path)
            tool_class = getattr(module, tool_info.name)
            return tool_class
        except ImportError as e:
            logger.error(f"导入工具失败: {tool_name} - {e}")
            raise
        except AttributeError as e:
            logger.error(f"工具类不存在: {tool_name} - {e}")
            raise

    def export_registry(self, output_path: Path):
        """导出工具注册配置"""
        registry_data = {
            "version": "1.0.0",
            "created_at": "2026-01-22",
            "total_tools": len(self.tools),
            "categories": {},
            "tools": [],
        }

        # 按类别组织
        for category, tool_names in self.category_index.items():
            registry_data["categories"][
                category if isinstance(category, str) else category.value
            ] = len(tool_names)

        # 添加工具详情
        for tool_info in self.tools.values():
            tool_dict = asdict(tool_info)
            # 转换枚举为字符串
            cat_value = (
                tool_info.category.value
                if isinstance(tool_info.category, Enum)
                else str(tool_info.category)
            )
            tool_dict["category"] = cat_value
            tool_dict["status"] = tool_info.status.value
            tool_dict["priority"] = tool_info.priority.value
            registry_data["tools"].append(tool_dict)

        # 保存到JSON
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(registry_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 工具注册配置已导出到: {output_path}")

    def print_summary(self):
        """打印工具摘要"""
        print("\n" + "=" * 80)
        print("📊 Athena工具注册中心 - 工具摘要")
        print("=" * 80)

        print("\n📈 总体统计:")
        print(f"  总工具数: {len(self.tools)}")
        print(f"  分类数: {len(self.category_index)}")

        print("\n📂 按分类统计:")
        # 使用 key 参数进行排序,将枚举转换为字符串
        for category, tool_names in sorted(self.category_index.items(), key=lambda x: str(x[0])):
            cat_name = category.value if isinstance(category, Enum) else category
            print(f"  {cat_name}: {len(tool_names)} 个工具")

        print("\n✅ 按状态统计:")
        for status, tool_names in sorted(self.status_index.items(), key=lambda x: str(x[0])):
            print(f"  {status.value}: {len(tool_names)} 个工具")

        print("\n" + "=" * 80)


def main():
    """主函数"""
    project_root = Path("/Users/xujian/Athena工作平台")

    # 创建工具注册中心
    registry = ToolRegistryCenter(project_root)

    # 打印摘要
    registry.print_summary()

    # 导出配置
    registry.export_registry(project_root / "config" / "production_tools.json")

    print("\n✅ 工具注册中心初始化完成!")


if __name__ == "__main__":
    main()
