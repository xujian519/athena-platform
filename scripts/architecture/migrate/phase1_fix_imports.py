#!/usr/bin/env python3
# ============================================================================
# Athena平台架构优化 - 阶段1：批量修复imports
# ============================================================================
# 功能：
#   1. 扫描core/中所有反向依赖
#   2. 替换为接口依赖
#   3. 更新构造函数为依赖注入
#   4. 生成迁移报告
# ============================================================================

import ast
import re
import shutil
from datetime import datetime
from pathlib import Path

# 配置
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
CORE_DIR = PROJECT_ROOT / "core"
BACKUP_DIR = PROJECT_ROOT / "backups" / "phase1-migration"
REPORTS_DIR = PROJECT_ROOT / "reports/architecture/phase1"

# 创建必要目录
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Import迁移规则
IMPORT_MIGRATION_RULES = {
    # 旧导入 → 新导入（通过接口）
    "from services.agent_services.vector_db.optimized_qdrant_client import OptimizedQdrantClient": (
        "from core.interfaces.vector_store import VectorStoreProvider\n"
        "from config.dependency_injection import DIContainer"
    ),
    "from services.sqlite_patent_knowledge_service import get_sqlite_patent_knowledge_service": (
        "from core.interfaces.knowledge_base import KnowledgeBaseService\n"
        "from config.dependency_injection import DIContainer"
    ),
    "from services.patents.google_patents_retriever import GooglePatentsRetriever": (
        "from core.interfaces.patent_service import PatentRetrievalService\n"
        "from config.dependency_injection import DIContainer"
    ),
    "from domains.patent.crawlers.enhanced_google_patents_crawler": (
        "from core.interfaces.patent_service import PatentRetrievalService\n"
        "from config.dependency_injection import DIContainer"
    ),
    "from domains.legal_ai.knowledge.legal_ontology import LegalOntology": (
        "from core.interfaces.knowledge_base import KnowledgeBaseService\n"
        "from config.dependency_injection import DIContainer"
    ),
}

# 需要重构的实例化模式
INSTANTIATION_PATTERNS = {
    r"OptimizedQdrantClient\(\)": "DIContainer.resolve(VectorStoreProvider)",
    r"get_sqlite_patent_knowledge_service\(\)": "DIContainer.resolve(KnowledgeBaseService)",
    r"GooglePatentsRetriever\(\)": "DIContainer.resolve(PatentRetrievalService)",
}


class ImportFixer:
    """Import修复器"""

    def __init__(self):
        self.fixed_files: list[Path] = []
        self.errors: list[tuple[Path, str] = []
        self.violations_found: dict[str, int] = {
            "from services.": 0,
            "from domains.": 0,
        }

    def backup_file(self, file_path: Path) -> Path:
        """备份文件"""
        rel_path = file_path.relative_to(PROJECT_ROOT)
        backup_path = BACKUP_DIR / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        return backup_path

    def find_violations(self) -> set[Path]:
        """查找所有违反架构的文件"""
        violating_files = set()

        for py_file in CORE_DIR.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")

                # 检查违规导入
                if "from services." in content:
                    self.violations_found["from services."] += 1
                    violating_files.add(py_file)

                if "from domains." in content:
                    self.violations_found["from domains."] += 1
                    violating_files.add(py_file)

            except Exception as e:
                self.errors.append((py_file, str(e)))

        return violating_files

    def fix_file(self, file_path: Path) -> bool:
        """修复单个文件"""
        try:
            # 备份
            self.backup_file(file_path)

            # 读取内容
            content = file_path.read_text(encoding="utf-8")
            original_content = content
            modifications = []

            # 1. 替换imports
            for old_import, new_import in IMPORT_MIGRATION_RULES.items():
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    modifications.append(f"Import: {old_import[:50]}...")

            # 2. 替换实例化
            for pattern, replacement in INSTANTIATION_PATTERNS.items():
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    modifications.append(f"Instantiation: {pattern} → {replacement}")

            # 3. 添加依赖注入到构造函数（如果需要）
            if "DIContainer.resolve" in content and "__init__" in content:
                # 检查是否需要添加构造函数参数
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # 查找__init__方法
                        init_methods = [
                            n for n in node.body
                            if isinstance(n, ast.FunctionDef) and n.name == "__init__"
                        ]

                        if init_methods:
                            init_method = init_methods[0]
                            # 检查是否已有DIContainer.resolve调用
                            has_di = False
                            for stmt in ast.walk(init_method):
                                if isinstance(stmt, ast.Call):
                                    if isinstance(stmt.func, ast.Attribute):
                                        if stmt.func.attr == "resolve":
                                            has_di = True
                                            break

                            if not has_di:
                                # 在__init__开头添加依赖注入
                                modifications.append("建议：手动检查是否需要在__init__中添加依赖注入")

            # 写回文件（仅当有修改时）
            if content != original_content:
                file_path.write_text(content, encoding="utf-8")
                self.fixed_files.append(file_path)
                return True

            return False

        except Exception as e:
            self.errors.append((file_path, str(e)))
            return False

    def fix_all(self) -> dict:
        """修复所有文件"""
        print("🔍 查找架构违规...")
        violating_files = self.find_violations()

        print(f"✅ 发现 {len(violating_files)} 个文件需要修复")
        print()

        print("📊 违规统计:")
        for violation_type, count in self.violations_found.items():
            if count > 0:
                print(f"  - {violation_type}: {count} 处")
        print()

        print("🔧 开始修复...")
        for i, file_path in enumerate(violating_files, 1):
            fixed = self.fix_file(file_path)
            status = "✅" if fixed else "⏭️ "
            print(f"  {status} [{i}/{len(violating_files)}] {file_path.relative_to(PROJECT_ROOT)}")

        print()

        return {
            "total_files": len(violating_files),
            "fixed_files": len(self.fixed_files),
            "errors": len(self.errors),
            "violations": self.violations_found,
        }

    def generate_report(self, stats: dict):
        """生成迁移报告"""
        report_path = REPORTS_DIR / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        report_content = f"""# 架构优化阶段1 - Import迁移报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计摘要

- **扫描文件**: {stats['total_files']} 个
- **修复文件**: {stats['fixed_files']} 个
- **错误**: {stats['errors']} 个

## 违规统计

"""

        for violation_type, count in stats['violations'].items():
            if count > 0:
                report_content += f"- **{violation_type}**: {count} 处\n"

        report_content += """

## 修复文件列表

"""
        for file_path in self.fixed_files:
            report_content += f"- `{file_path.relative_to(PROJECT_ROOT)}`\n"

        if self.errors:
            report_content += """

## 错误列表

"""
            for file_path, error in self.errors:
                report_content += f"- **{file_path.relative_to(PROJECT_ROOT)}**: {error}\n"

        report_content += f"""

## 备份位置

所有原始文件已备份至: `{BACKUP_DIR.relative_to(PROJECT_ROOT)}`

## 后续步骤

1. ✅ Import迁移完成
2. ⏳ 手动检查构造函数依赖注入
3. ⏳ 运行测试套件验证
4. ⏳ 提交更改

---

*由 `phase1_fix_imports.py` 自动生成*
"""

        report_path.write_text(report_content, encoding="utf-8")
        print(f"📝 迁移报告: {report_path}")

        return report_path


def main():
    """主函数"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔧 Athena平台架构优化 - 阶段1：Import迁移")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    fixer = ImportFixer()

    # 执行修复
    stats = fixer.fix_all()
    print()

    # 生成报告
    report_path = fixer.generate_report(stats)
    print()

    # 输出摘要
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 迁移摘要")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  扫描文件: {stats['total_files']}")
    print(f"  修复文件: {stats['fixed_files']}")
    print(f"  错误: {stats['errors']}")
    print()
    print("📁 报告位置:")
    print(f"  迁移报告: {report_path}")
    print(f"  文件备份: {BACKUP_DIR}")
    print()

    if stats['errors'] > 0:
        print("⚠️  部分文件修复失败，请检查错误列表")
        return 1

    if stats['fixed_files'] == 0:
        print("✅ 未发现需要修复的文件")
        return 0

    print("✅ Import迁移完成")
    print()
    print("💡 后续步骤:")
    print("  1. 检查修复的文件")
    print("  2. 运行测试: pytest tests/")
    print("  3. 如有问题，使用回滚脚本恢复")

    return 0


if __name__ == "__main__":
    exit(main())
