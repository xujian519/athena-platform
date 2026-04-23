#!/usr/bin/env python3
"""
清理xiaochen相关引用
"""
import re
from pathlib import Path


def clean_xiaochen_references(file_path):
    """清理文件中的xiaochen引用"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 移除xiaochen相关的导入和常量
        patterns = [
            (r'\nXIAOCHEN\s*=\s*"[^"]*"\s*# [^\n]*', ''),  # 常量定义
            (r'\s*xiaochen\s*=\s*AgentInfo\([^)]*\),?\s*', '', re.DOTALL),  # AgentInfo定义
            (r',\s*"xiaochen"[^}]*', ''),  # 列表中的xiaochen
            (r'["\']xiaochen["\']:\s*{[^}]*},?\s*', '', re.DOTALL),  # 字典中的xiaochen
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

        # 移除空行
        content = re.sub(r'\n{3,}', '\n\n', content)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"⚠️  处理 {file_path} 时出错: {e}")
        return False

def main():
    """主函数"""
    files_to_clean = [
        'core/collaboration/on_demand_agent_orchestrator.py',
        'core/collaboration/ready_on_demand_system.py',
        'core/collaboration/enhanced_agent_coordination.py',
        'core/agent_collaboration/service_discovery.py',
        'core/fusion/cross_agent_capability_fusion.py',
        'core/memory/import_all_platform_memories.py',
    ]

    print("🧹 清理xiaochen代码引用...")
    print("="*60)

    cleaned_count = 0
    for file_path in files_to_clean:
        path = Path(file_path)
        if not path.exists():
            print(f"⏭️  跳过（不存在）: {file_path}")
            continue

        if clean_xiaochen_references(path):
            print(f"✅ 已清理: {file_path}")
            cleaned_count += 1
        else:
            print(f"ℹ️  无需清理: {file_path}")

    print("="*60)
    print(f"✅ 清理完成！共处理 {cleaned_count} 个文件")

if __name__ == "__main__":
    main()
