#!/usr/bin/env python3.11
"""
最终语法错误修复脚本

修复所有剩余的类型注解和语法错误
"""

import re
from pathlib import Path


def fix_file(file_path: Path) -> bool:
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 修复模式
        patterns = [
            # Optional[Dict[str, Any]]] -> Optional[Dict[str, Any]] = None
            (r': Optional\[Dict\[str, Any\]\]](?=\s*\))', r': Optional[Dict[str, Any]] = None'),
            # Optional[List[Dict[str, Any]]]] -> Optional[List[Dict[str, Any]]] = None
            (r': Optional\[List\[Dict\[str, Any\]\]\]](?=\s*\))', r': Optional[List[Dict[str, Any]]] = None'),
            # result["key"]] -> result["key"]
            (r'result\[("[^"]+)"\]\]', r'result["\1"]'),
            # Optional[[]] -> []
            (r'Optional\[\[\]\]', r'[]'),
            # 修复多余方括号在行尾
            (r'\]\s*\)', r')'),
            # 修复Dict和List大小写
            (r'\bdict\[', r'Dict['),
            (r'\blist\[', r'List['),
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        if content != original_content:
            # 创建备份
            backup_path = file_path.with_suffix('.py.final_backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)

            # 写入修复后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        return False

    except Exception as e:
        print(f"❌ {file_path}: {e}")
        return False


def main():
    """主函数"""
    # 目标文件
    target_files = [
        'core/framework/agents/xiaona/application_reviewer_proxy.py',
        'core/framework/agents/xiaona/creativity_analyzer_proxy.py',
        'core/framework/agents/xiaona/infringement_analyzer_proxy.py',
        'core/framework/agents/xiaona/invalidation_analyzer_proxy.py',
        'core/framework/agents/xiaona/novelty_analyzer_proxy.py',
        'core/framework/agents/xiaona/writing_reviewer_proxy.py',
        'core/framework/agents/xiaona/writer_agent.py',
    ]

    print("🔧 开始最终语法修复...")

    fixed_count = 0
    for file_path_str in target_files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            continue

        print(f"🔍 {file_path.name}")
        if fix_file(file_path):
            print(f"  ✅ 已修复")
            fixed_count += 1
        else:
            print(f"  ➡️  无需修复")

    print(f"\n✅ 修复完成: {fixed_count} 个文件")

    # 验证修复
    print("\n🔍 验证修复...")
    import subprocess
    for file_path_str in target_files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            continue

        result = subprocess.run(
            ['python3.11', '-m', 'py_compile', str(file_path)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✅ {file_path.name} 编译成功")
        else:
            print(f"❌ {file_path.name} 编译失败")
            print(f"   {result.stderr[:100]}")


if __name__ == '__main__':
    main()
