#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一Numpy技术栈工具
Unify Numpy Stack Tool
"""

import os
import sys
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NumpyStackUnifier:
    """Numpy技术栈统一器"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.numpy_files: List[Path] = []
        self.requirement_files: List[Path] = []
        self.venv_paths: List[Path] = []
        self.analysis_results = {}

    def analyze_project(self) -> Dict:
        """分析项目中的numpy使用情况"""
        logger.info("🔍 开始分析项目...")

        # 1. 查找所有使用numpy的Python文件
        self._find_numpy_files()

        # 2. 查找所有requirements文件
        self._find_requirement_files()

        # 3. 查找虚拟环境
        self._find_virtual_environments()

        # 4. 分析numpy使用模式
        self._analyze_numpy_usage()

        # 5. 生成报告
        return self._generate_analysis_report()

    def _find_numpy_files(self):
        """查找使用numpy的文件"""
        pattern = re.compile(r'(import numpy|from numpy|import np|np\.)')

        for py_file in self.project_root.rglob("*.py"):
            # 跳过备份和缓存目录
            if any(skip in str(py_file) for skip in [
                "__pycache__", ".git", "node_modules", ".venv", "venv"
            ]):
                continue

            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                if pattern.search(content):
                    self.numpy_files.append(py_file)
            except Exception as e:
                logger.warning(f"读取文件失败 {py_file}: {e}")

        logger.info(f"✅ 找到 {len(self.numpy_files)} 个使用numpy的文件")

    def _find_requirement_files(self):
        """查找requirements文件"""
        req_patterns = [
            "requirements*.txt",
            "pyproject.toml",
            "setup.py",
            "Pipfile",
            "environment.yml"
        ]

        for pattern in req_patterns:
            for req_file in self.project_root.rglob(pattern):
                # 跳过备份和缓存目录
                if any(skip in str(req_file) for skip in [
                    "__pycache__", ".git", "node_modules"
                ]):
                    continue
                self.requirement_files.append(req_file)

        logger.info(f"✅ 找到 {len(self.requirement_files)} 个依赖文件")

    def _find_virtual_environments(self):
        """查找虚拟环境"""
        venv_indicators = [
            "bin/python",
            "Scripts/python.exe",
            "pyvenv.cfg",
            ".venv",
            "venv",
            "athena_env"
        ]

        for indicator in venv_indicators:
            for venv_path in self.project_root.rglob(indicator):
                venv_root = venv_path.parent
                if venv_root not in self.venv_paths:
                    self.venv_paths.append(venv_root)

        logger.info(f"✅ 找到 {len(self.venv_paths)} 个虚拟环境")

    def _analyze_numpy_usage(self):
        """分析numpy使用模式"""
        usage_patterns = {
            "basic_imports": 0,
            "np_aliases": 0,
            "array_creation": 0,
            "math_operations": 0,
            "linear_algebra": 0,
            "random": 0,
            "advanced_features": 0
        }

        patterns = {
            "basic_imports": [r"import numpy", r"from numpy"],
            "np_aliases": [r"import np", r"as np"],
            "array_creation": [r"np\.array", r"np\.zeros", r"np\.ones", r"np\.empty"],
            "math_operations": [r"np\.(sum|mean|max|min|std|var)", r"np\.(sqrt|log|exp)"],
            "linear_algebra": [r"np\.(dot|matmul|linalg|einsum)"],
            "random": [r"np\.random"],
            "advanced_features": [r"np\.(vectorize|apply_along_axis|einsum_path)"]
        }

        for py_file in self.numpy_files:
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')

                for category, regex_list in patterns.items():
                    for regex in regex_list:
                        if re.search(regex, content):
                            usage_patterns[category] += 1
                            break
            except Exception as e:
                logger.warning(f"分析文件失败 {py_file}: {e}")

        self.analysis_results["usage_patterns"] = usage_patterns

    def _generate_analysis_report(self) -> Dict:
        """生成分析报告"""
        report = {
            "project_root": str(self.project_root),
            "summary": {
                "numpy_files_count": len(self.numpy_files),
                "requirement_files_count": len(self.requirement_files),
                "virtual_envs_count": len(self.venv_paths)
            },
            "files": {
                "numpy_files": [str(f.relative_to(self.project_root)) for f in self.numpy_files[:20]],  # 限制显示数量
                "requirement_files": [str(f.relative_to(self.project_root)) for f in self.requirement_files]
            },
            "usage_patterns": self.analysis_results.get("usage_patterns", {}),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 基于Python版本的建议
        if sys.version_info >= (3, 14):
            recommendations.extend([
                "✅ 使用Python 3.14，建议升级到numpy 2.x",
                "⚠️ 检查所有numpy导入语句，确保兼容性",
                "🔧 使用numpy_compatibility.py模块统一管理"
            ])
        elif sys.version_info >= (3, 11):
            recommendations.extend([
                "✅ Python 3.11兼容性好，可以使用numpy 1.24+",
                "💡 建议升级到numpy 2.0以获得更好的性能",
                "🔧 启用numpy的性能优化选项"
            ])
        else:
            recommendations.extend([
                "⚠️ Python版本较旧，建议升级到3.11+",
                "📦 锁定numpy版本为1.23.x以确保稳定性",
                "🔧 考虑使用兼容性层"
            ])

        # 基于文件数量的建议
        if len(self.numpy_files) > 100:
            recommendations.append("📊 项目大量使用numpy，建议创建统一的numpy配置模块")

        # 基于使用模式的建议
        patterns = self.analysis_results.get("usage_patterns", {})
        if patterns.get("advanced_features", 0) > 10:
            recommendations.append("🧮 项目使用了numpy高级功能，需要仔细测试兼容性")

        return recommendations

    def create_unified_requirements(self) -> str:
        """创建统一的requirements.txt"""
        requirements = []

        # 基础依赖
        base_requirements = [
            "# 统一的numpy技术栈依赖",
            "# Generated by unify_numpy_stack.py",
            "",
            "# Core numerical computing",
        ]

        # 根据Python版本选择numpy版本
        if sys.version_info >= (3, 14):
            numpy_version = "numpy>=2.0.0"
        elif sys.version_info >= (3, 11):
            numpy_version = "numpy>=1.24.0,<3.0.0"
        else:
            numpy_version = "numpy>=1.21.0,<2.0.0"

        requirements.extend(base_requirements)
        requirements.append(numpy_version)

        # 添加相关依赖
        related_deps = [
            "",
            "# Scientific computing stack",
            "scipy>=1.9.0",
            "pandas>=1.5.0",
            "scikit-learn>=1.1.0",
            "",
            "# Machine learning frameworks (compatible)",
            "torch>=2.0.0",
            "tensorflow-cpu>=2.10.0",  # 使用CPU版本避免MPS问题
            "",
            "# Vector databases",
            "qdrant-client>=1.6.0",
            "",
            "# Performance optimization",
            "numba>=0.56.0" if sys.version_info >= (3, 11) else "numba>=0.56.0,<0.60.0",
        ]

        requirements.extend(related_deps)

        return "\n".join(requirements)

    def update_imports(self, dry_run: bool = True) -> Dict[str, List[str]]:
        """更新numpy导入语句"""
        updates = {
            "updated": [],
            "skipped": [],
            "errors": []
        }

        import_pattern = re.compile(r'^(import numpy|from numpy|import np)', re.MULTILINE)

        for py_file in self.numpy_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content

                # 标准化numpy导入
                lines = content.split('\n')
                new_lines = []
                numpy_imported = False

                for line in lines:
                    # 处理numpy导入
                    if import_pattern.match(line.strip()):
                        if not numpy_imported:
                            new_lines.append("# 导入统一配置的numpy")
                            new_lines.append("from config.numpy_compatibility import np, array, random, mean, sum, dot")
                            numpy_imported = True
                        else:
                            # 跳过重复的numpy导入
                            continue
                    else:
                        new_lines.append(line)

                # 如果文件使用了numpy但没有导入，添加导入
                if not numpy_imported and re.search(r'np\.', content):
                    new_lines.insert(0, "# 导入统一配置的numpy")
                    new_lines.insert(1, "from config.numpy_compatibility import np, array, random, mean, sum, dot")
                    numpy_imported = True

                updated_content = '\n'.join(new_lines)

                if updated_content != original_content:
                    if not dry_run:
                        py_file.write_text(updated_content, encoding='utf-8')
                    updates["updated"].append(str(py_file.relative_to(self.project_root)))
                else:
                    updates["skipped"].append(str(py_file.relative_to(self.project_root)))

            except Exception as e:
                updates["errors"].append(f"{py_file}: {str(e)}")
                logger.error(f"处理文件失败 {py_file}: {e}")

        return updates

    def fix_numpy_compatibility(self) -> Dict[str, Any]:
        """修复numpy兼容性问题"""
        fixes = {
            "array_creation": 0,
            "deprecated_functions": 0,
            "type_issues": 0
        }

        # 需要修复的模式
        deprecated_patterns = {
            r'np\.int': 'np.int64',
            r'np\.float': 'np.float64',
            r'np\.bool': 'np.bool_',
        }

        array_patterns = {
            r'np\.array\(\[\]\)': 'array([])',  # 使用安全的array创建
        }

        for py_file in self.numpy_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content

                # 修复废弃的函数
                for old, new in deprecated_patterns.items():
                    content = re.sub(old, new, content)
                    if old != new and content != original_content:
                        fixes["deprecated_functions"] += 1

                # 修复数组创建
                for old, new in array_patterns.items():
                    content = re.sub(old, new, content)
                    if old != new and content != original_content:
                        fixes["array_creation"] += 1

                # 如果有修改，写回文件
                if content != original_content:
                    py_file.write_text(content, encoding='utf-8')

            except Exception as e:
                logger.error(f"修复文件失败 {py_file}: {e}")

        return fixes

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="统一Numpy技术栈工具")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--dry-run", action="store_true", help="仅分析不修改")
    parser.add_argument("--update-imports", action="store_true", help="更新导入语句")
    parser.add_argument("--fix-compatibility", action="store_true", help="修复兼容性问题")
    parser.add_argument("--output", help="输出报告文件")

    args = parser.parse_args()

    unifier = NumpyStackUnifier(args.project_root)

    print("🚀 开始统一Numpy技术栈...")
    print("=" * 60)

    # 1. 分析项目
    report = unifier.analyze_project()

    # 2. 显示分析结果
    print(f"\n📊 分析结果:")
    print(f"   项目路径: {report['project_root']}")
    print(f"   Python版本: {report['python_version']}")
    print(f"   Numpy文件数: {report['summary']['numpy_files_count']}")
    print(f"   依赖文件数: {report['summary']['requirement_files_count']}")
    print(f"   虚拟环境数: {report['summary']['virtual_envs_count']}")

    print(f"\n🔍 Numpy使用模式:")
    patterns = report['usage_patterns']
    for pattern, count in patterns.items():
        print(f"   {pattern}: {count}")

    print(f"\n💡 优化建议:")
    for rec in report['recommendations']:
        print(f"   {rec}")

    # 3. 创建统一的requirements
    if not args.dry_run:
        unified_req = unifier.create_unified_requirements()
        req_path = Path(args.project_root) / "requirements_unified.txt"
        req_path.write_text(unified_req)
        print(f"\n✅ 统一依赖文件已保存: {req_path}")

    # 4. 更新导入语句
    if args.update_imports:
        print(f"\n🔄 更新导入语句...")
        updates = unifier.update_imports(dry_run=args.dry_run)
        print(f"   更新文件: {len(updates['updated'])}")
        print(f"   跳过文件: {len(updates['skipped'])}")
        if updates['errors']:
            print(f"   错误文件: {len(updates['errors'])}")

    # 5. 修复兼容性问题
    if args.fix_compatibility:
        print(f"\n🔧 修复兼容性问题...")
        fixes = unifier.fix_numpy_compatibility()
        print(f"   数组创建修复: {fixes['array_creation']}")
        print(f"   废弃函数修复: {fixes['deprecated_functions']}")
        print(f"   类型问题修复: {fixes['type_issues']}")

    # 6. 保存报告
    if args.output:
        report_path = Path(args.output)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📄 分析报告已保存: {report_path}")

    print("\n✅ Numpy技术栈统一完成！")

if __name__ == "__main__":
    main()