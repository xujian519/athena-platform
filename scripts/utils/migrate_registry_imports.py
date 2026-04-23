#!/usr/bin/env python3
"""
工具注册表导入路径迁移工具

功能：
1. 扫描所有Python文件的导入语句
2. 替换旧的导入路径为新的统一注册表
3. 生成迁移报告
4. 支持dry-run模式

使用方法：
    python3 scripts/migrate_registry_imports.py --dry-run  # 预览变更
    python3 scripts/migrate_registry_imports.py            # 执行迁移
    python3 scripts/migrate_registry_imports.py --verify   # 验证迁移

Author: Agent 4 (迁移专家)
Created: 2026-04-19
"""

import argparse
import ast
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 导入路径映射规则
IMPORT_MAPPINGS: dict[str, str] = {
    # 旧路径 → 新路径
    "from core.tools.tool_manager import ToolManager": "from core.tools.centralized_registry import get_centralized_registry",
    "from core.tools.registry import ToolRegistry": "from core.tools.centralized_registry import CentralizedRegistry",
    "from core.tools.registry import get_global_registry": "from core.tools.centralized_registry import get_centralized_registry",
    "from core.tools.base import ToolRegistry": "from core.tools.centralized_registry import CentralizedRegistry",
    "from core.tools.base import get_global_registry": "from core.tools.centralized_registry import get_centralized_registry",
    "from core.tools.tool_manager import get_tool_manager": "from core.tools.centralized_registry import get_centralized_registry",
    "import core.tools.registry": "import core.tools.centralized_registry",
    "import core.tools.tool_manager": "import core.tools.centralized_registry",
}


class ImportMigrationScanner:
    """导入迁移扫描器"""

    def __init__(self, root_path: str):
        """
        初始化扫描器

        Args:
            root_path: 项目根目录
        """
        self.root_path = Path(root_path)
        self.files_to_migrate: list[Path] = []
        self.migration_report: dict[str, list[dict] = {}

    def scan_python_files(self) -> list[Path]:
        """
        扫描所有Python文件

        Returns:
            Python文件路径列表
        """
        logger.info(f"🔍 开始扫描Python文件: {self.root_path}")

        python_files = []
        for py_file in self.root_path.rglob("*.py"):
            # 排除虚拟环境和缓存目录
            if any(
                excluded in str(py_file)
                for excluded in ["venv", "__pycache__", ".venv", "node_modules"]
            ):
                continue

            python_files.append(py_file)

        logger.info(f"✅ 找到 {len(python_files)} 个Python文件")
        return python_files

    def analyze_imports(self, file_path: Path) -> list[dict]:
        """
        分析文件的导入语句

        Args:
            file_path: 文件路径

        Returns:
            需要迁移的导入语句列表
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # 使用AST解析导入语句
            tree = ast.parse(content, filename=str(file_path))

            imports_to_migrate = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_stmt = self._get_import_statement(node)

                    # 检查是否需要迁移
                    for old_pattern, new_pattern in IMPORT_MAPPINGS.items():
                        if old_pattern in import_stmt:
                            imports_to_migrate.append({
                                "line": node.lineno,
                                "old": import_stmt,
                                "new": new_pattern,
                                "type": "import" if isinstance(node, ast.Import) else "from_import"
                            })
                            break

            return imports_to_migrate

        except SyntaxError as e:
            logger.warning(f"⚠️ 语法错误 {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ 解析错误 {file_path}: {e}")
            return []

    def _get_import_statement(self, node: ast.AST) -> str:
        """
        从AST节点获取导入语句

        Args:
            node: AST节点

        Returns:
            导入语句字符串
        """
        if isinstance(node, ast.Import):
            module_names = [alias.name for alias in node.names]
            return f"import {', '.join(module_names)}"

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [alias.name for alias in node.names]
            return f"from {module} import {', '.join(names)}"

        return ""

    def generate_report(self) -> dict:
        """
        生成迁移报告

        Returns:
            迁移报告字典
        """
        total_files = 0
        total_imports = 0

        for _file_path, imports in self.migration_report.items():
            if imports:
                total_files += 1
                total_imports += len(imports)

        return {
            "total_files_scanned": len(self.files_to_migrate),
            "total_files_to_migrate": total_files,
            "total_imports_to_migrate": total_imports,
            "files": self.migration_report
        }


class ImportMigrator:
    """导入迁移执行器"""

    def __init__(self, root_path: str, dry_run: bool = True):
        """
        初始化迁移执行器

        Args:
            root_path: 项目根目录
            dry_run: 是否为干运行模式
        """
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        self.scanner = ImportMigrationScanner(root_path)
        self.migration_stats = {
            "files_processed": 0,
            "imports_migrated": 0,
            "errors": []
        }

    def scan(self) -> dict:
        """
        扫描需要迁移的文件

        Returns:
            扫描报告
        """
        logger.info("🔍 开始扫描导入语句...")

        python_files = self.scanner.scan_python_files()
        self.scanner.files_to_migrate = python_files

        for py_file in python_files:
            imports = self.scanner.analyze_imports(py_file)
            if imports:
                self.scanner.migration_report[str(py_file)] = imports

        report = self.scanner.generate_report()
        self._print_scan_report(report)

        return report

    def migrate(self) -> dict:
        """
        执行迁移

        Returns:
            迁移统计信息
        """
        if not self.scanner.migration_report:
            logger.warning("⚠️ 没有需要迁移的导入语句")
            return self.migration_stats

        logger.info("🚀 开始迁移导入语句...")

        for file_path_str, imports in self.scanner.migration_report.items():
            file_path = Path(file_path_str)
            self._migrate_file(file_path, imports)

        self._print_migration_summary()
        return self.migration_stats

    def _migrate_file(self, file_path: Path, imports: list[dict]):
        """
        迁移单个文件

        Args:
            file_path: 文件路径
            imports: 需要迁移的导入列表
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            # 按行号倒序处理（避免行号偏移）
            for imp in sorted(imports, key=lambda x: x["line"], reverse=True):
                line_num = imp["line"] - 1  # 转换为0索引

                if line_num < len(lines):
                    old_line = lines[line_num]
                    new_line = old_line.replace(imp["old"], imp["new"])

                    if old_line != new_line:
                        lines[line_num] = new_line
                        self.migration_stats["imports_migrated"] += 1

                        logger.info(f"✅ {file_path}:{imp['line']}")
                        logger.info(f"   旧: {old_line.strip()}")
                        logger.info(f"   新: {new_line.strip()}")

            if not self.dry_run:
                # 写入文件
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                self.migration_stats["files_processed"] += 1

        except Exception as e:
            error_msg = f"❌ 迁移失败 {file_path}: {e}"
            logger.error(error_msg)
            self.migration_stats["errors"].append(error_msg)

    def verify(self) -> dict:
        """
        验证迁移结果

        Returns:
            验证报告
        """
        logger.info("🔍 验证迁移结果...")

        # 重新扫描
        python_files = self.scanner.scan_python_files()
        remaining_imports = []

        for py_file in python_files:
            imports = self.scanner.analyze_imports(py_file)
            if imports:
                remaining_imports.append({
                    "file": str(py_file),
                    "imports": imports
                })

        verification_report = {
            "total_files_scanned": len(python_files),
            "files_with_remaining_imports": len(remaining_imports),
            "remaining_imports": remaining_imports,
            "migration_success": len(remaining_imports) == 0
        }

        self._print_verification_report(verification_report)
        return verification_report

    def _print_scan_report(self, report: dict):
        """打印扫描报告"""
        logger.info("=" * 80)
        logger.info("📊 导入扫描报告")
        logger.info("=" * 80)
        logger.info(f"扫描文件数: {report['total_files_scanned']}")
        logger.info(f"需要迁移的文件: {report['total_files_to_migrate']}")
        logger.info(f"需要迁移的导入: {report['total_imports_to_migrate']}")

        if report['total_files_to_migrate'] > 0:
            logger.info("\n📁 需要迁移的文件:")
            for file_path, imports in report['files'].items():
                logger.info(f"\n  {file_path}:")
                for imp in imports:
                    logger.info(f"    Line {imp['line']}: {imp['old']}")

        logger.info("=" * 80)

    def _print_migration_summary(self):
        """打印迁移摘要"""
        logger.info("=" * 80)
        logger.info("✅ 迁移完成摘要")
        logger.info("=" * 80)
        logger.info(f"处理文件数: {self.migration_stats['files_processed']}")
        logger.info(f"迁移导入数: {self.migration_stats['imports_migrated']}")

        if self.migration_stats['errors']:
            logger.info(f"错误数: {len(self.migration_stats['errors'])}")
            for error in self.migration_stats['errors']:
                logger.error(error)

        if self.dry_run:
            logger.info("\n⚠️ 这是干运行模式，没有实际修改文件")
            logger.info("   要执行实际迁移，请运行: python3 scripts/migrate_registry_imports.py")

        logger.info("=" * 80)

    def _print_verification_report(self, report: dict):
        """打印验证报告"""
        logger.info("=" * 80)
        logger.info("🔍 迁移验证报告")
        logger.info("=" * 80)
        logger.info(f"扫描文件数: {report['total_files_scanned']}")
        logger.info(f"仍有旧导入的文件: {report['files_with_remaining_imports']}")

        if report['remaining_imports']:
            logger.info("\n⚠️ 以下文件仍有旧导入:")
            for item in report['remaining_imports']:
                logger.info(f"\n  {item['file']}:")
                for imp in item['imports']:
                    logger.info(f"    Line {imp['line']}: {imp['old']}")

        if report['migration_success']:
            logger.info("\n✅ 所有导入已成功迁移！")
        else:
            logger.info("\n⚠️ 仍有部分导入需要手动处理")

        logger.info("=" * 80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="工具注册表导入路径迁移工具"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干运行模式，不实际修改文件"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="验证迁移结果"
    )
    parser.add_argument(
        "--root-path",
        type=str,
        default=".",
        help="项目根目录路径"
    )

    args = parser.parse_args()

    # 创建迁移执行器
    migrator = ImportMigrator(
        root_path=args.root_path,
        dry_run=args.dry_run
    )

    if args.verify:
        # 验证模式
        migrator.verify()
    else:
        # 扫描和迁移
        report = migrator.scan()

        if report['total_imports_to_migrate'] > 0:
            if not args.dry_run:
                # 执行迁移
                migrator.migrate()

                # 验证结果
                migrator.verify()
        else:
            logger.info("✅ 没有需要迁移的导入语句")


if __name__ == "__main__":
    main()
