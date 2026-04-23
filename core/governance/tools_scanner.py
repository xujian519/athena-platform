#!/usr/bin/env python3
from __future__ import annotations
"""
工具目录扫描器和注册器
Tool Directory Scanner and Registrar

自动扫描tools目录中的Python文件,提取工具元数据并注册到统一工具注册中心。

核心功能:
1. 扫描tools目录中的所有.py文件
2. 解析函数签名和docstring提取元数据
3. 自动注册到UnifiedToolRegistry
4. 支持手动注册和自动发现两种模式

Author: Athena Team
Date: 2026-02-24
Version: 1.0.0
"""

import ast
import asyncio
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 添加项目根目录到sys.path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.governance.unified_tool_registry import ToolCategory, UnifiedToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class ToolFunctionMetadata:
    """工具函数元数据"""

    file_path: str
    function_name: str
    module_name: str
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    return_type: str = "Any"
    category: ToolCategory = ToolCategory.UTILITY
    tags: list[str] = field(default_factory=list)
    is_async: bool = False
    line_number: int = 0


class ToolScanner:
    """
    工具目录扫描器

    扫描tools目录,提取函数元数据,注册到统一工具注册中心
    """

    def __init__(
        self,
        tools_dir: Path | str = None,
        registry: UnifiedToolRegistry = None,
        config: Optional[dict[str, Any]] = None
    ):
        """
        初始化工具扫描器

        Args:
            tools_dir: 工具目录路径,默认为项目根目录/tools
            registry: 统一工具注册中心
            config: 配置字典
        """
        self.tools_dir = Path(tools_dir) if tools_dir else PROJECT_ROOT / "tools"
        self.registry = registry
        self.config = config or {}

        # 扫描统计
        self.scan_stats = {
            "total_files": 0,
            "scanned_files": 0,
            "found_functions": 0,
            "registered_tools": 0,
            "failed_files": [],
            "scan_time": 0.0
        }

        # 过滤配置
        self.exclude_patterns = self.config.get(
            "exclude_patterns",
            ["__pycache__", "*.pyc", ".git", "node_modules", "test_"]
        )
        self.include_patterns = self.config.get("include_patterns", ["*.py"])

        # 函数命名模式(识别工具函数)
        self.function_patterns = self.config.get(
            "function_patterns",
            ["^_", "^test_", "^__"]  # 排除以这些开头的函数
        )

    def should_exclude_file(self, file_path: Path) -> bool:
        """判断是否应排除文件"""
        for pattern in self.exclude_patterns:
            if pattern in str(file_path):
                return True
        return False

    def should_include_file(self, file_path: Path) -> bool:
        """判断是否应包含文件"""
        if not file_path.suffix == ".py":
            return False
        return not self.should_exclude_file(file_path)

    def is_tool_function(self, func_name: str) -> bool:
        """判断是否为工具函数"""
        import re
        for pattern in self.function_patterns:
            if re.match(pattern, func_name):
                return False
        return True

    def extract_function_metadata(
        self,
        file_path: Path,
        func_name: str,
        node: ast.FunctionDef
    ) -> ToolFunctionMetadata | None:
        """
        提取函数元数据

        Args:
            file_path: 文件路径
            func_name: 函数名
            node: AST函数节点

        Returns:
            ToolFunctionMetadata或None
        """
        try:
            # 提取docstring
            docstring = ast.get_docstring(node) or ""
            description = docstring.split("\n")[0] if docstring else f"{func_name}工具"

            # 提取参数信息
            parameters = {}
            returns = "Any"

            for arg in node.args.args:
                arg_name = arg.arg
                # 尝试获取类型注解
                if arg.annotation:
                    arg_type = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
                else:
                    arg_type = "Any"

                parameters[arg_name] = {
                    "type": arg_type,
                    "required": True
                }

            # 处理默认参数
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            for i, default in enumerate(node.args.defaults):
                arg_idx = defaults_offset + i
                if arg_idx < len(node.args.args):
                    arg_name = node.args.args[arg_idx].arg
                    if arg_name in parameters:
                        parameters[arg_name]["required"] = False
                        parameters[arg_name]["default"] = ast.literal_eval(default)

            # 返回类型
            if node.returns:
                returns = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)

            # 判断是否为async函数
            is_async = isinstance(node, (ast.AsyncFunctionDef, ))

            # 推断类别
            category = self._infer_category(func_name, description, file_path)

            # 生成标签
            tags = self._generate_tags(func_name, description, file_path)

            return ToolFunctionMetadata(
                file_path=str(file_path),
                function_name=func_name,
                module_name=file_path.stem,
                name=func_name,
                description=description,
                parameters=parameters,
                return_type=returns,
                category=category,
                tags=tags,
                is_async=is_async,
                line_number=node.lineno
            )

        except Exception as e:
            logger.debug(f"提取函数元数据失败 {func_name}@{file_path}: {e}")
            return None

    def _infer_category(
        self,
        func_name: str,
        description: str,
        file_path: Path
    ) -> ToolCategory:
        """推断工具类别"""
        name_lower = func_name.lower()
        desc_lower = description.lower()
        file_lower = file_path.name.lower()

        # 搜索类工具
        if any(kw in name_lower or kw in desc_lower for kw in ["search", "find", "query", "检索", "搜索"]):
            return ToolCategory.SEARCH

        # 专利相关
        if any(kw in name_lower or kw in desc_lower or kw in file_lower for kw in ["patent", "专利", "invention"]):
            return ToolCategory.DOMAIN

        # 文件处理
        if any(kw in name_lower or kw in desc_lower for kw in ["file", "read", "write", "文件", "读写"]):
            return ToolCategory.UTILITY

        # 数据处理
        if any(kw in name_lower or kw in desc_lower for kw in ["data", "parse", "extract", "数据", "解析"]):
            return ToolCategory.UTILITY

        # 文档处理
        if any(kw in name_lower or kw in desc_lower for kw in ["document", "format", "convert", "文档", "转换"]):
            return ToolCategory.UTILITY

        # 默认为工具函数
        return ToolCategory.UTILITY

    def _generate_tags(
        self,
        func_name: str,
        description: str,
        file_path: Path
    ) -> list[str]:
        """生成工具标签"""
        tags = []

        # 从文件名推断
        tags.append(file_path.stem)

        # 从函数名推断
        for part in func_name.split("_"):
            if len(part) > 2:
                tags.append(part)

        # 去重并限制数量
        return list(set(tags))[:5]

    def scan_file(self, file_path: Path) -> list[ToolFunctionMetadata]:
        """
        扫描单个文件

        Args:
            file_path: 文件路径

        Returns:
            工具函数元数据列表
        """
        functions = []

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name

                    # 过滤非工具函数
                    if not self.is_tool_function(func_name):
                        continue

                    # 提取元数据
                    metadata = self.extract_function_metadata(file_path, func_name, node)
                    if metadata:
                        functions.append(metadata)

        except SyntaxError as e:
            logger.warning(f"语法错误 {file_path}: {e}")
            self.scan_stats["failed_files"].append(str(file_path))
        except Exception as e:
            logger.debug(f"扫描文件失败 {file_path}: {e}")
            self.scan_stats["failed_files"].append(str(file_path))

        return functions

    async def scan_directory(self, recursive: bool = True) -> list[ToolFunctionMetadata]:
        """
        扫描工具目录

        Args:
            recursive: 是否递归扫描子目录

        Returns:
            所有工具函数元数据列表
        """
        import time
        start_time = time.time()

        logger.info(f"🔍 开始扫描工具目录: {self.tools_dir}")

        all_functions = []

        if recursive:
            pattern = "**/*.py"
        else:
            pattern = "*.py"

        for file_path in self.tools_dir.glob(pattern):
            self.scan_stats["total_files"] += 1

            if not self.should_include_file(file_path):
                continue

            self.scan_stats["scanned_files"] += 1

            functions = self.scan_file(file_path)
            all_functions.extend(functions)
            self.scan_stats["found_functions"] += len(functions)

        self.scan_stats["scan_time"] = time.time() - start_time

        logger.info("✅ 扫描完成:")
        logger.info(f"   总文件数: {self.scan_stats['total_files']}")
        logger.info(f"   已扫描: {self.scan_stats['scanned_files']}")
        logger.info(f"   发现函数: {self.scan_stats['found_functions']}")
        logger.info(f"   耗时: {self.scan_stats['scan_time']:.2f}秒")

        if self.scan_stats["failed_files"]:
            logger.warning(f"   失败文件: {len(self.scan_stats['failed_files'])}")

        return all_functions

    async def register_all(
        self,
        functions: list[ToolFunctionMetadata] | None = None,
        dry_run: bool = False
    ) -> int:
        """
        注册所有工具到统一注册中心

        Args:
            functions: 工具函数元数据列表,如果为None则自动扫描
            dry_run: 是否为试运行(不实际注册)

        Returns:
            成功注册的工具数量
        """
        if not self.registry:
            logger.warning("工具注册中心未初始化,跳过注册")
            return 0

        if functions is None:
            functions = await self.scan_directory()

        logger.info(f"📝 开始注册 {len(functions)} 个工具...")

        registered = 0

        for metadata in functions:
            tool_id = f"utility.{metadata.module_name}.{metadata.function_name}"

            # 构建能力列表
            capabilities = [metadata.function_name]
            capabilities.extend(metadata.tags)

            try:
                if dry_run:
                    logger.info(f"[DRY RUN] {tool_id}: {metadata.description}")
                    registered += 1
                else:
                    success = await self.registry.register_tool(
                        tool_id=tool_id,
                        name=metadata.function_name,
                        category=metadata.category,
                        version="1.0.0",
                        description=metadata.description,
                        capabilities=capabilities,
                        input_schema=metadata.parameters,
                        output_schema={"type": metadata.return_type},
                        registration_source="tools_scanner"
                    )

                    if success:
                        registered += 1
                        self.scan_stats["registered_tools"] += 1

            except Exception as e:
                logger.warning(f"注册工具失败 {tool_id}: {e}")

        logger.info(f"✅ 注册完成,共注册 {registered} 个工具")

        return registered

    def get_statistics(self) -> dict[str, Any]:
        """获取扫描统计信息"""
        return self.scan_stats.copy()


# ================================
# 便捷函数
# ================================


async def scan_and_register_tools(
    tools_dir: str | Path = None,
    registry: UnifiedToolRegistry = None,
    recursive: bool = True,
    dry_run: bool = False
) -> int:
    """
    扫描并注册工具

    Args:
        tools_dir: 工具目录路径
        registry: 统一工具注册中心
        recursive: 是否递归扫描
        dry_run: 是否为试运行

    Returns:
        注册的工具数量
    """
    scanner = ToolScanner(tools_dir=tools_dir, registry=registry)

    # 扫描目录
    functions = await scanner.scan_directory(recursive=recursive)

    # 注册工具
    registered = await scanner.register_all(functions=functions, dry_run=dry_run)

    return registered


# ================================
# 测试代码
# ================================


async def main():
    """主函数(用于测试)"""
    import logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("🔍 工具目录扫描器测试")
    print("=" * 80)
    print()

    # 获取统一注册中心
    from core.governance.unified_tool_registry import get_unified_registry

    registry = get_unified_registry()
    await registry.initialize()

    print()

    # 创建扫描器
    scanner = ToolScanner(registry=registry)

    # 扫描目录
    functions = await scanner.scan_directory(recursive=False)  # 只扫描顶层

    print()

    # 显示部分结果
    print("📋 前10个发现的工具函数:")
    for func in functions[:10]:
        print(f"   - {func.function_name} ({func.category.value}): {func.description[:60]}...")

    print()

    # 注册工具(试运行)
    print("📝 试运行注册...")
    await scanner.register_all(functions=functions, dry_run=True)

    print()
    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
