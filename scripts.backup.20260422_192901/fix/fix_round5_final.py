#!/usr/bin/env python3
"""第五轮最终修复 - 处理剩余的所有错误模式"""

import re
from pathlib import Path

def fix_all_remaining_patterns(content: str) -> str:
    """应用所有剩余的修复模式"""
    
    # ========================================
    # 模式组1: 类型注解中的 | None = None 后面缺少 ]
    # ========================================
    patterns = [
        # dict[str, ... | None = None
        (r'dict\[str,\s*([a-zA-Z0-9_\[\],:\s]+?)\s*\|\s*None\s*=\s*None', r'dict[str, \1] | None = None'),
        (r'dict\[str,\s*str\s*\|\s*None\s*=\s*None', r'dict[str, str] | None = None'),
        (r'dict\[str,\s*Any\s*\|\s*None\s*=\s*None', r'dict[str, Any] | None = None'),
        (r'dict\[str,\s*float\s*\|\s*None\s*=\s*None', r'dict[str, float] | None = None'),
        (r'dict\[str,\s*int\s*\|\s*None\s*=\s*None', r'dict[str, int] | None = None'),
        
        # list[str, ... | None = None
        (r'list\[str,\s*([a-zA-Z0-9_\[\],:\s]+?)\s*\|\s*None\s*=\s*None', r'list[str, \1] | None = None'),
        (r'list\[str,\s*str\s*\|\s*None\s*=\s*None', r'list[str, str] | None = None'),
        (r'list\[str,\s*Any\s*\|\s*None\s*=\s*None', r'list[str, Any] | None = None'),
        (r'list\[int,\s*([a-zA-Z0-9_\[\],:\s]+?)\s*\|\s*None\s*=\s*None', r'list[int, \1] | None = None'),
        
        # set[str | None = None
        (r'set\[str\s*\|\s*None\s*=\s*None', r'set[str] | None = None'),
        (r'set\[str\s*\|\s*None\s*=\s*None,', r'set[str] | None = None,'),
        
        # tuple[..., ... | None = None
        (r'tuple\[([^\]]+)\)\s*\|\s*None\s*=\s*None', r'tuple[\1)] | None = None'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # ========================================
    # 模式组2: 修复函数参数列表中的错误
    # ========================================
    # name: str, value: float = 1.0, labels: dict[str, str | None = None
    content = re.sub(
        r'(\w+:\s*float\s*=\s*[\d.]+,\s*)\w+:\s*dict\[str,\s*str\s*\|\s*None\s*=\s*None',
        r'\1labels: dict[str, str] | None = None',
        content
    )
    
    # ========================================
    # 模式组3: 修复 hashlib.md5 参数
    # ========================================
    content = re.sub(
        r'\.md5\(\s*[^)]*\.encode\([^\)]*\)\s*,\s*usedforsecurity=False\s*\)\s*\)',
        r'.md5(\1).hexdigest()',
        content
    )
    
    content = re.sub(
        r'hashlib\.md5\([^)]*\.encode\([^\)]*\)\s*,\s*usedforsecurity=False\)',
        r'hashlib.md5(\1.encode("utf-8"), usedforsecurity=False)',
        content
    )
    
    # ========================================
    # 模式组4: 修复 )]] -> 和类似的模式
    # ========================================
    content = re.sub(
        r'\)\]\]\s*->\s*',
        r']) -> ',
        content
    )
    
    # ========================================
    # 模式组5: 修复缺少闭合括号的参数列表
    # ========================================
    # self, nodes: list[dict[str, Any]] -> None
    # → self, nodes: list[dict[str, Any]] | None = None
    content = re.sub(
        r'nodes:\s*list\[dict\[str,\s*Any\]\]\]\s*->\s*None',
        r'nodes: list[dict[str, Any]] | None = None',
        content
    )
    
    # ========================================
    # 模式组6: 修复 output_file: str, patent_list: list[PatentInfo]] | None
    # ========================================
    content = re.sub(
        r'output_file:\s*str,\s*patent_list:\s*list\[PatentInfo\]\]\s*\|\s*Non',
        r'output_file: str, patent_list: list[PatentInfo]] | None',
        content
    )
    content = re.sub(
        r'output_file:\s*str,\s*patent_list:\s*list\[PatentInfo\]\]\s*\|\s*None',
        r'output_file: str, patent_list: list[PatentInfo]] | None',
        content
    )
    
    # ========================================
    # 模式组7: 修复多层嵌套的类型注解
    # ========================================
    # dict[str, list[dict[str, Any]]] 已经是正确的
    # 但有时候会变成 dict[str, list[dict[str, Any]] | None = None
    content = re.sub(
        r'dict\[str,\s*list\[dict\[str,\s*Any\]\]\]\s*\|\s*None\s*=\s*None',
        r'dict[str, list[dict[str, Any]]] | None = None',
        content
    )
    
    # ========================================
    # 模式组8: 修复 )]: 模式
    # ========================================
    content = re.sub(
        r'\)\]:\s*',
        r'): ',
        content
    )
    
    # ========================================
    # 模式组9: 修复缺少闭合的泛型
    # ========================================
    # conversation_log: list[dict[str, Any]  # 专家对话记录
    content = re.sub(
        r'conversation_log:\s*list\[dict\[str,\s*Any\]\s*#',
        r'conversation_log: list[dict[str, Any]]  #',
        content
    )
    
    content = re.sub(
        r'workflow_steps:\s*list\[dict\[str,\s*Any\]\s*#',
        r'workflow_steps: list[dict[str, Any]]  #',
        content
    )
    
    # ========================================
    # 模式组10: 修复 except 块
    # ========================================
    # 如果 except 行后面没有代码，添加 pass
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        fixed_lines.append(line)
        
        # 如果是 except 行且以冒号结尾
        if re.match(r'^\s*except\s+', line) and line.rstrip().endswith(':'):
            # 检查下一行
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # 如果下一行是空行或更小的缩进，添加 pass
                if not next_line.strip() or len(next_line) - len(next_line.lstrip()) < len(line) - len(line.lstrip()):
                    # 在 except 后添加 pass
                    fixed_lines[-1] = line + '\n            pass  # TODO: 实现异常处理'
    
    content = '\n'.join(fixed_lines)
    
    return content

def fix_file_safe(file_path: Path) -> bool:
    """安全地修复文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # 只处理有语法错误的文件
        try:
            compile(content, str(file_path), 'exec')
            return False
        except SyntaxError:
            pass
        
        # 应用修复
        fixed = fix_all_remaining_patterns(content)
        
        if fixed != content:
            # 验证修复
            try:
                compile(fixed, str(file_path), 'exec')
                file_path.write_text(fixed, encoding='utf-8')
                return True
            except SyntaxError:
                pass
        return False
    except Exception:
        return False

def main():
    core_path = Path('/Users/xujian/Athena工作平台/core')
    
    print("=" * 80)
    print("🔧 第五轮最终修复 - 处理所有剩余错误")
    print("=" * 80)
    
    # 多轮修复
    for round_num in range(1, 6):
        print(f"\n第{round_num}轮...")
        
        # 获取有错误的文件
        error_files = []
        for f in core_path.rglob('*.py'):
            try:
                compile(f.read_text(encoding='utf-8'), str(f), 'exec')
            except SyntaxError:
                error_files.append(f)
        
        if not error_files:
            print("✅ 所有文件语法正确!")
            break
        
        # 修复文件
        fixed_count = 0
        for f in error_files:
            if fix_file_safe(f):
                fixed_count += 1
        
        print(f"   修复: {fixed_count} 个文件, 剩余: {len(error_files)} 个")
        
        if fixed_count == 0:
            break
    
    # 最终统计
    all_files = list(core_path.rglob('*.py'))
    error_count = 0
    success_count = 0
    
    for f in all_files:
        try:
            compile(f.read_text(encoding='utf-8'), str(f), 'exec')
            success_count += 1
        except SyntaxError:
            error_count += 1
    
    print("\n" + "=" * 80)
    print(f"📊 最终统计:")
    print(f"   总文件: {len(all_files)}")
    print(f"   成功: {success_count} ({success_count*100//len(all_files)}%)")
    print(f"   失败: {error_count} ({error_count*100//len(all_files)}%)")
    
    improvement = success_count * 100 // len(all_files)
    print(f"\n📈 总体成功率: {improvement}%")
    
    if improvement >= 90:
        print("🎉 优秀!成功率已达到90%以上!")
    elif improvement >= 85:
        print("✨ 很好!成功率已达到85%以上!")
    elif improvement >= 82:
        print("👍 良好!成功率已达到82%以上!")
    else:
        print(f"⚠️ 当前成功率: {improvement}%")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
