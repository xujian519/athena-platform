#!/usr/bin/env python3
# ============================================================================
# Athena平台架构优化 - 依赖关系分析工具
# ============================================================================
# 功能：
#   1. 扫描所有Python文件的import语句
#   2. 生成模块依赖矩阵
#   3. 检测循环依赖
#   4. 输出可视化图表（Graphviz）
# ============================================================================

import ast
import json
from collections import defaultdict
from pathlib import Path

# 配置
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
OUTPUT_DIR = PROJECT_ROOT / "reports/architecture"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 要排除的目录
EXCLUDE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    "node_modules",
    "htmlcov",
    "venv",
    ".venv",
    "build",
    "dist",
    "*.egg-info",
    "backups",
    "scripts.backup",
}

# 标准库模块（不记录）
STANDARD_LIBS = {
    "os", "sys", "re", "json", "datetime", "pathlib", "typing",
    "collections", "itertools", "functools", "math", "random",
    "time", "uuid", "hashlib", "base64", "copy", "io",
}


class DependencyAnalyzer:
    """依赖关系分析器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.imports = defaultdict(set)  # module -> set of imported modules
        self.imports_by_file = defaultdict(set)  # file -> set of imports
        self.module_to_files = defaultdict(set)  # module -> set of files

    def is_excluded(self, path: Path) -> bool:
        """检查路径是否应排除"""
        parts = path.parts
        for part in parts:
            if part in EXCLUDE_DIRS:
                return True
            if part.startswith("."):
                return True
        return False

    def extract_imports_from_file(self, file_path: Path) -> set[str]:
        """从Python文件中提取imports"""
        imports = set()

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])

        except Exception as e:
            print(f"⚠️  解析失败: {file_path}: {e}")

        return imports

    def normalize_module(self, import_path: str, file_path: Path) -> str:
        """规范化模块路径"""
        # 跳过标准库
        if import_path in STANDARD_LIBS:
            return None

        # 跳过第三方库（假设不在项目根目录下）
        import_path_obj = self.project_root / import_path.replace(".", "/")
        if not import_path_obj.exists():
            # 可能是第三方库
            return None

        return import_path

    def scan_project(self):
        """扫描整个项目"""
        print("🔍 扫描项目文件...")

        py_files = list(self.project_root.rglob("*.py"))
        total = len(py_files)

        for i, py_file in enumerate(py_files, 1):
            if self.is_excluded(py_file):
                continue

            # 确定模块名
            try:
                rel_path = py_file.relative_to(self.project_root)
                module = str(rel_path.parent).replace("/", ".")

                # 提取imports
                imports = self.extract_imports_from_file(py_file)

                # 过滤和规范化
                normalized_imports = set()
                for imp in imports:
                    normalized = self.normalize_module(imp, py_file)
                    if normalized:
                        normalized_imports.add(normalized)

                # 记录
                if normalized_imports:
                    self.imports[module].update(normalized_imports)
                    self.imports_by_file[str(rel_path)].update(normalized_imports)
                    for imp in normalized_imports:
                        self.module_to_files[imp].add(str(rel_path))

                if i % 100 == 0:
                    print(f"  进度: {i}/{total} ({i*100//total}%)")

            except Exception as e:
                print(f"⚠️  处理失败: {py_file}: {e}")

        print(f"✅ 扫描完成: {len(self.imports)} 个模块")

    def detect_circular_dependencies(self) -> list[list[str]:
        """检测循环依赖"""
        print("🔍 检测循环依赖...")

        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: list[str]):
            if node in rec_stack:
                # 找到循环
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.imports.get(node, []):
                dfs(neighbor, path + [node])

            rec_stack.remove(node)

        for module in self.imports:
            dfs(module, [])

        print(f"✅ 发现 {len(cycles)} 个循环依赖")
        return cycles

    def detect_violations(self) -> dict[str, list[str]:
        """检测架构违规"""
        print("🔍 检测架构违规...")

        violations = defaultdict(list)

        # core → services/domains (反向依赖)
        for module, imports in self.imports.items():
            if module.startswith("core."):
                for imp in imports:
                    if imp.startswith("services.") or imp.startswith("domains."):
                        violations["core_reverse_deps"].append({
                            "module": module,
                            "imports": imp,
                        })

        print(f"✅ 发现 {sum(len(v) for v in violations.values())} 个违规")
        return violations

    def generate_dependency_matrix(self) -> dict[tuple[str, str], int]:
        """生成依赖矩阵"""
        print("📊 生成依赖矩阵...")

        matrix = defaultdict(int)
        all_modules = set(self.imports.keys()) | {
            imp for imports in self.imports.values() for imp in imports
        }

        for module, imports in self.imports.items():
            for imp in imports:
                matrix[(module, imp)] += 1

        print(f"✅ 矩阵维度: {len(all_modules)} x {len(all_modules)}")
        return matrix

    def export_json(self):
        """导出JSON报告"""
        print("📝 导出JSON报告...")

        # 循环依赖
        cycles = self.detect_circular_dependencies()

        # 违规
        violations = self.detect_violations()

        # 统计
        stats = {
            "total_modules": len(self.imports),
            "total_dependencies": sum(len(v) for v in self.imports.values()),
            "circular_dependencies": len(cycles),
            "violations": {k: len(v) for k, v in violations.items()},
        }

        # 导出
        report = {
            "stats": stats,
            "imports": {k: sorted(v) for k, v in self.imports.items()},
            "circular_dependencies": cycles,
            "violations": violations,
        }

        output_path = OUTPUT_DIR / "dependency_graph.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ JSON报告: {output_path}")

        # 导出CSV矩阵
        self.export_csv_matrix()

        return report

    def export_csv_matrix(self):
        """导出CSV矩阵"""
        import csv

        matrix = self.generate_dependency_matrix()
        all_modules = sorted({
            k[0] for k in matrix.keys()
        } | {k[1] for k in matrix.keys()})

        output_path = OUTPUT_DIR / "dependency_matrix.csv"
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([""] + all_modules)
            for row_module in all_modules:
                row = [row_module]
                for col_module in all_modules:
                    row.append(matrix.get((row_module, col_module), 0))
                writer.writerow(row)

        print(f"✅ CSV矩阵: {output_path}")

    def export_graphviz(self):
        """导出Graphviz图表"""
        print("📊 导出Graphviz图表...")

        output_path = OUTPUT_DIR / "dependency_graph.dot"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("digraph DependencyGraph {\n")
            f.write("  rankdir=LR;\n")
            f.write("  node [shape=box, fontsize=10];\n")
            f.write("\n")

            # 定义节点
            for module in sorted(self.imports.keys()):
                color = "lightblue" if module.startswith("core.") else "lightgreen"
                f.write(f'  "{module}" [fillcolor={color}, style=filled];\n')

            f.write("\n")

            # 定义边
            for module, imports in sorted(self.imports.items()):
                for imp in sorted(imports):
                    # 高亮违规依赖
                    if module.startswith("core.") and (
                        imp.startswith("services.") or imp.startswith("domains.")
                    ):
                        f.write(f'  "{module}" -> "{imp}" [color=red, penwidth=2.0];\n')
                    else:
                        f.write(f'  "{module}" -> "{imp}";\n')

            f.write("}\n")

        print(f"✅ Graphviz文件: {output_path}")
        print("💡 使用以下命令生成PNG:")
        print(f"   dot -Tpng {output_path} -o {OUTPUT_DIR / 'dependency_graph.png'}")


def main():
    """主函数"""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔍 Athena平台依赖关系分析")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    analyzer = DependencyAnalyzer(PROJECT_ROOT)

    # 扫描项目
    analyzer.scan_project()
    print()

    # 导出报告
    report = analyzer.export_json()
    print()

    # 输出统计
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 统计摘要")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  总模块数: {report['stats']['total_modules']}")
    print(f"  总依赖数: {report['stats']['total_dependencies']}")
    print(f"  循环依赖: {report['stats']['circular_dependencies']}")
    print()
    print("⚠️  架构违规:")
    for violation_type, count in report['stats']['violations'].items():
        if count > 0:
            print(f"    - {violation_type}: {count}")
    print()

    # 输出循环依赖
    if report['circular_dependencies']:
        print("🔄 循环依赖:")
        for cycle in report['circular_dependencies'][:5]:  # 只显示前5个
            print(f"    {' → '.join(cycle)}")
        if len(report['circular_dependencies']) > 5:
            print(f"    ... 还有 {len(report['circular_dependencies']) - 5} 个")
        print()

    # 输出违规详情
    if report['violations'].get('core_reverse_deps'):
        print("❌ Core反向依赖（违规）:")
        for v in report['violations']['core_reverse_deps'][:10]:
            print(f"    {v['module']} → {v['imports']}")
        if len(report['violations']['core_reverse_deps']) > 10:
            print(f"    ... 还有 {len(report['violations']['core_reverse_deps']) - 10} 个")
        print()

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📁 报告目录: {OUTPUT_DIR}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    main()
