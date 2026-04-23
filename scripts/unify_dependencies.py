#!/usr/bin/env python3.11
"""
统一项目依赖管理

将分散的requirements.txt文件整合到Poetry管理
"""

import re
from pathlib import Path
from typing import Dict, List, Set


def parse_requirements(file_path: Path) -> List[str]:
    """解析requirements.txt文件"""
    if not file_path.exists():
        return []

    requirements = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue
            # 跳过-e选项（本地包）
            if line.startswith('-e '):
                continue
            # 提取包名（去掉版本号）
            pkg_name = re.split(r'[=<>~!]', line)[0].strip()
            if pkg_name:
                requirements.append(pkg_name)

    return requirements


def collect_all_requirements() -> Dict[str, List[str]]:
    """收集所有requirements.txt文件的依赖"""
    all_requirements = {}

    # 扫描所有requirements.txt文件
    for req_file in Path('.').rglob('requirements*.txt'):
        # 跳过虚拟环境和备份文件
        if any(x in str(req_file) for x in ['.venv', 'node_modules', '.backup']):
            continue

        requirements = parse_requirements(req_file)
        if requirements:
            key = str(req_file.relative_to('.'))
            all_requirements[key] = requirements

    return all_requirements


def merge_dependencies(all_requirements: Dict[str, List[str]]) -> Dict[str, Set[str]]:
    """合并所有依赖，去重"""
    merged = {
        'core': set(),      # 核心依赖
        'dev': set(),       # 开发依赖
        'test': set(),      # 测试依赖
        'docs': set(),      # 文档依赖
        'services': set(),  # 服务依赖
        'mcp': set(),       # MCP服务器依赖
    }

    for file_path, requirements in all_requirements.items():
        for req in requirements:
            # 分类依赖
            if 'test' in file_path.lower():
                merged['test'].add(req)
            elif 'doc' in file_path.lower():
                merged['docs'].add(req)
            elif 'services' in file_path.lower():
                merged['services'].add(req)
            elif 'mcp-servers' in file_path.lower():
                merged['mcp'].add(req)
            elif any(x in req for x in ['pytest', 'black', 'ruff', 'mypy', 'coverage']):
                merged['dev'].add(req)
            else:
                merged['core'].add(req)

    return merged


def generate_poetry_config(merged_deps: Dict[str, Set[str]]) -> str:
    """生成Poetry配置"""
    config = f'''[tool.poetry]
name = "athena-platform"
version = "0.1.0"
description = "Athena工作平台 - 企业级AI代理协作平台"
authors = ["徐健 <xujian519@gmail.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"

# 核心依赖
'''

    # 添加核心依赖（排除测试和开发工具）
    core_deps = merged_deps['core'] - merged_deps['dev'] - merged_deps['test']
    for dep in sorted(core_deps):
        config += f'{dep} = "*"\n'

    config += '''
[tool.poetry.group.dev.dependencies]
# 开发工具
'''

    # 开发依赖
    for dep in sorted(merged_deps['dev']):
        config += f'{dep} = "*"\n'

    config += '''
[tool.poetry.group.test.dependencies]
# 测试工具
'''

    # 测试依赖
    for dep in sorted(merged_deps['test']):
        config += f'{dep} = "*"\n'

    config += '''
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
'''

    return config


def main():
    """主函数"""
    print("🔍 扫描依赖文件...")
    all_requirements = collect_all_requirements()

    print(f"📊 发现 {len(all_requirements)} 个requirements文件:")
    for file_path, requirements in all_requirements.items():
        print(f"  - {file_path}: {len(requirements)} 个依赖")

    print("\n🔧 合并依赖...")
    merged = merge_dependencies(all_requirements)

    print("\n📦 依赖分类统计:")
    for category, deps in merged.items():
        print(f"  - {category}: {len(deps)} 个唯一依赖")

    print("\n✨ 生成Poetry配置...")
    poetry_config = generate_poetry_config(merged)

    # 输出到文件
    output_file = Path('pyproject-poetry-unified.toml')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(poetry_config)

    print(f"\n✅ 统一配置已生成: {output_file}")
    print("\n📋 下一步:")
    print("  1. 审查生成的配置文件")
    print("  2. 替换现有的pyproject.toml")
    print("  3. 运行: poetry install")
    print("  4. 删除旧的requirements.txt文件")

    # 生成报告
    with open('/tmp/dependency_unification_report.json', 'w', encoding='utf-8') as f:
        import json
        json.dump({
            'source_files': list(all_requirements.keys()),
            'categories': {k: len(v) for k, v in merged.items()},
            'total_unique_dependencies': sum(len(v) for v in merged.values())
        }, f, indent=2, ensure_ascii=False)

    print("\n📄 详细报告: /tmp/dependency_unification_report.json")


if __name__ == '__main__':
    main()
