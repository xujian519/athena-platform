#!/usr/bin/env python3
"""
快速验证脚本 - 检查需要更新的import路径
"""

import os
import re
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")

# 需要检查的模块迁移映射
MIGRATION_MAP = {
    "core.legal_kg": "domains.legal.knowledge_graph",
    "core.compliance": "domains.legal.compliance",
    "core.biology": "domains.biology",
    "core.emotion": "domains.emotion",
    "core.patents": "domains.patents",
    "core.database": "core.infrastructure.database",
    "core.cache": "core.infrastructure.cache",
    "core.llm": "core.ai.llm",
    "core.embedding": "core.ai.embedding",
    "core.prompts": "core.ai.prompts",
    "core.cognition": "core.ai.cognition",
    "core.nlp": "core.ai.nlp",
    "core.perception": "core.ai.perception",
    "core.agents": "core.framework.agents",
    "core.memory": "core.framework.memory",
    "core.collaboration": "core.framework.collaboration",
}

def find_python_files():
    """查找所有Python文件"""
    python_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # 跳过虚拟环境和缓存目录
        dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', 'node_modules', '.git']

        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)

    return python_files

def check_imports(file_path):
    """检查文件中的import语句"""
    issues = []

    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # 检查from imports
            from_match = re.match(r'^from\s+(\S+)\s+import', line)
            if from_match:
                old_module = from_match.group(1)
                if old_module in MIGRATION_MAP:
                    new_module = MIGRATION_MAP[old_module]
                    issues.append({
                        'line': i,
                        'type': 'from',
                        'old': old_module,
                        'new': new_module,
                        'content': line.strip()
                    })

            # 检查直接imports
            import_match = re.match(r'^import\s+(\S+)', line)
            if import_match:
                old_module = import_match.group(1).split('.')[0]
                full_module = import_match.group(1)

                # 检查是否是顶级模块迁移
                for old_base, new_base in MIGRATION_MAP.items():
                    if full_module.startswith(old_base + '.'):
                        new_module = full_module.replace(old_base, new_base, 1)
                        issues.append({
                            'line': i,
                            'type': 'import',
                            'old': full_module,
                            'new': new_module,
                            'content': line.strip()
                        })
                        break

    except Exception as e:
        print(f"⚠️  无法读取文件 {file_path}: {e}")

    return issues

def main():
    print("🔍 检查需要更新的import路径...\n")

    python_files = find_python_files()
    print(f"📁 找到 {len(python_files)} 个Python文件\n")

    all_issues = defaultdict(list)

    for file_path in python_files:
        issues = check_imports(file_path)
        if issues:
            rel_path = file_path.relative_to(PROJECT_ROOT)
            all_issues[rel_path] = issues

    # 统计
    total_files = len(all_issues)
    total_issues = sum(len(issues) for issues in all_issues.values())

    print(f"📊 发现需要更新的文件: {total_files}")
    print(f"📊 发现需要更新的import: {total_issues}\n")

    if total_files > 0:
        print("=" * 80)
        print("详细列表:")
        print("=" * 80)

        for file_path, issues in sorted(all_issues.items()):
            print(f"\n📄 {file_path} ({len(issues)}个问题)")
            for issue in issues:
                print(f"  行{issue['line']}: {issue['content']}")
                print(f"    → 旧: {issue['old']}")
                print(f"    → 新: {issue['new']}")

        print("\n" + "=" * 80)
        print("💡 建议:")
        print("=" * 80)
        print("""
1. 手动更新这些import路径
2. 或使用自动化脚本批量替换:
   sed -i '' 's/from core.legal_kg/from domains.legal.knowledge_graph/g' **/*.py
3. 更新后运行测试验证
        """)

        # 生成sed脚本
        sed_script = []
        for old_module, new_module in MIGRATION_MAP.items():
            old_module.replace('.', r'\.')
            sed_script.append(f"sed -i '' 's/from {old_module}/from {new_module}/g' **/*.py")

        print("\n# 自动化替换脚本")
        print("#" + "=" * 78)
        for cmd in sed_script:
            print(cmd)

    else:
        print("✅ 所有import路径都是正确的！")

    print("\n" + "=" * 80)
    print("验证完成")
    print("=" * 80)

if __name__ == '__main__':
    main()
