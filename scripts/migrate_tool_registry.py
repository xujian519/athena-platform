#!/usr/bin/env python3
"""
工具注册表迁移脚本
Tool Registry Migration Script

扫描旧的工具注册表系统，迁移工具定义到统一注册表。

核心功能:
1. 扫描旧注册表
2. 迁移工具定义
3. 生成迁移报告

Author: Athena平台团队
Created: 2026-04-19
Version: v2.0.0
"""

import ast
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """迁移结果"""

    total_tools: int = 0
    migrated_tools: int = 0
    failed_tools: int = 0
    skipped_tools: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ToolRegistryMigrator:
    """工具注册表迁移器"""

    def __init__(self, project_root: Path):
        """
        初始化迁移器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self.result = MigrationResult()

        # 旧注册表路径
        self.old_registries = [
            "core/tools/base.py",  # ToolRegistry
            "core/tools/tool_manager.py",  # ToolManager
            "core/search/registry/tool_registry.py",  # SearchRegistry
            "core/governance/unified_tool_registry.py",  # UnifiedToolRegistry
        ]

    def scan_old_registries(self) -> dict[str, Any]:
        """
        扫描旧注册表

        Returns:
            扫描结果字典
        """
        logger.info("🔍 扫描旧注册表...")

        scan_result = {
            "registries": [],
            "total_tools": 0,
        }

        for registry_path in self.old_registries:
            registry_file = self.project_root / registry_path

            if not registry_file.exists():
                logger.warning(f"⚠️ 注册表文件不存在: {registry_path}")
                continue

            # 扫描注册表
            tools = self._scan_registry_file(registry_file)

            scan_result["registries"].append(
                {
                    "path": registry_path,
                    "tool_count": len(tools),
                    "tools": tools,
                }
            )

            scan_result["total_tools"] += len(tools)

            logger.info(f"   {registry_path}: {len(tools)} 个工具")

        logger.info(f"✅ 扫描完成，共发现 {scan_result['total_tools']} 个工具")

        return scan_result

    def _scan_registry_file(self, file_path: Path) -> list[dict[str, Any]]:
        """
        扫描注册表文件

        Args:
            file_path: 文件路径

        Returns:
            工具列表
        """
        tools = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # 解析AST
            tree = ast.parse(content)

            # 查找类定义
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # 查找方法
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            # 检查是否是register方法
                            if item.name.startswith("register"):
                                # 分析方法体，查找工具注册
                                registered_tools = self._analyze_register_method(item)
                                tools.extend(registered_tools)

        except Exception as e:
            logger.error(f"❌ 扫描文件失败 {file_path}: {e}")

        return tools

    def _analyze_register_method(self, func_node: ast.FunctionDef) -> list[dict[str, Any]]:
        """
        分析register方法

        Args:
            func_node: 函数节点

        Returns:
            工具列表
        """
        tools = []

        # 遍历方法体
        for node in func_node.body:
            # 查找工具注册调用
            if isinstance(node, ast.Expr):
                if isinstance(node.value, ast.Call):
                    call = node.value

                    # 检查是否是ToolDefinition调用
                    if isinstance(call.func, ast.Name):
                        if call.func.id == "ToolDefinition":
                            tool = self._extract_tool_definition(call)
                            if tool:
                                tools.append(tool)

        return tools

    def _extract_tool_definition(self, call_node: ast.Call) -> dict[str, Any] | None:
        """
        提取ToolDefinition参数

        Args:
            call_node: 调用节点

        Returns:
            工具定义字典
        """
        tool_def = {}

        # 提取关键字参数
        for keyword in call_node.keywords:
            if keyword.arg == "tool_id":
                if isinstance(keyword.value, ast.Constant):
                    tool_def["tool_id"] = keyword.value.value
            elif keyword.arg == "name":
                if isinstance(keyword.value, ast.Constant):
                    tool_def["name"] = keyword.value.value
            elif keyword.arg == "description":
                if isinstance(keyword.value, ast.Constant):
                    tool_def["description"] = keyword.value.value
            elif keyword.arg == "category":
                if isinstance(keyword.value, ast.Attribute):
                    tool_def["category"] = keyword.value.attr

        return tool_def if tool_def else None

    def migrate_tools(
        self, scan_result: dict[str, Any], dry_run: bool = True
    ) -> MigrationResult:
        """
        迁移工具

        Args:
            scan_result: 扫描结果
            dry_run: 是否只演练不实际迁移

        Returns:
            迁移结果
        """
        logger.info("🚀 开始迁移工具...")

        if dry_run:
            logger.info("📋 演练模式（不会实际修改文件）")

        for registry_info in scan_result["registries"]:
            logger.info(f"   处理: {registry_info['path']}")

            for tool in registry_info["tools"]:
                try:
                    self._migrate_single_tool(tool, dry_run)
                    self.result.migrated_tools += 1

                except Exception as e:
                    self.result.failed_tools += 1
                    self.result.errors.append(f"{tool.get('tool_id', 'unknown')}: {e}")
                    logger.error(f"❌ 迁移失败 {tool.get('tool_id')}: {e}")

        self.result.total_tools = scan_result["total_tools"]

        logger.info(f"✅ 迁移完成")
        logger.info(f"   总计: {self.result.total_tools}")
        logger.info(f"   成功: {self.result.migrated_tools}")
        logger.info(f"   失败: {self.result.failed_tools}")
        logger.info(f"   跳过: {self.result.skipped_tools}")

        return self.result

    def _migrate_single_tool(self, tool: dict[str, Any], dry_run: bool):
        """
        迁移单个工具

        Args:
            tool: 工具定义
            dry_run: 是否只演练
        """
        tool_id = tool.get("tool_id")
        if not tool_id:
            self.result.skipped_tools += 1
            return

        logger.debug(f"   迁移工具: {tool_id}")

        if not dry_run:
            # 实际迁移逻辑
            # TODO: 实现实际的迁移代码
            pass

    def generate_report(self, output_path: Path):
        """
        生成迁移报告

        Args:
            output_path: 输出路径
        """
        logger.info(f"📄 生成迁移报告: {output_path}")

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tools": self.result.total_tools,
                "migrated_tools": self.result.migrated_tools,
                "failed_tools": self.result.failed_tools,
                "skipped_tools": self.result.skipped_tools,
            },
            "errors": self.result.errors,
            "warnings": self.result.warnings,
        }

        # 写入JSON报告
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info("✅ 报告已生成")


async def main():
    """主函数"""
    print("=" * 80)
    print("🔧 工具注册表迁移脚本")
    print("=" * 80)
    print()

    # 项目根目录
    project_root = Path("/Users/xujian/Athena工作平台")

    # 创建迁移器
    migrator = ToolRegistryMigrator(project_root)

    # 1. 扫描旧注册表
    scan_result = migrator.scan_old_registries()

    print()
    print("📊 扫描结果:")
    print(f"   注册表数量: {len(scan_result['registries'])}")
    print(f"   工具总数: {scan_result['total_tools']}")

    # 2. 迁移工具（演练模式）
    print()
    result = migrator.migrate_tools(scan_result, dry_run=True)

    # 3. 生成报告
    report_path = project_root / "reports" / "tool_migration_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    migrator.generate_report(report_path)

    print()
    print("✅ 迁移完成")
    print(f"   报告路径: {report_path}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
