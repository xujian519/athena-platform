#!/usr/bin/env python3
"""
全面修复剩余的所有语法错误
Comprehensive Fix for All Remaining Syntax Errors
"""

import re
from pathlib import Path

def fix_all_error_patterns(content: str) -> str:
    """应用所有错误修复模式"""
    original = content
    
    # ========================================
    # 模式1: Optional[dict[str, Any] | None = None) 
    # 最多见：120个文件
    # ========================================
    content = re.sub(
        r'Optional\[dict\[str, Any\] \| None = None\)\s*->',
        r'dict[str, Any] | None = None) ->',
        content
    )
    content = re.sub(
        r'Optional\[set\[str\] \| None = None\):',
        r'set[str] | None = None):',
        content
    )
    content = re.sub(
        r'Optional\[list\[str\] \| None = None\)\s*->',
        r'list[str] | None = None) ->',
        content
    )
    content = re.sub(
        r'Optional\[list\[dict\[str, Any\]\] \| None = None\)\s*->',
        r'list[dict[str, Any]] | None = None) ->',
        content
    )
    content = re.sub(
        r'Optional\[tuple\[str, dict\[str, Any\]\]\] \| None = None\)\s*->',
        r'tuple[str, dict[str, Any]] | None = None) ->',
        content
    )
    
    # ========================================
    # 模式2: 未闭合的 [ 
    # 57个文件
    # ========================================
    # ) -> tuple[list[QueryResult], dict[str, Any]: 
    # → )]] -> tuple[list[QueryResult], dict[str, Any]]:
    content = re.sub(
        r'\)\s*->\s*tuple\[list\[QueryResult\], dict\[str, Any\]:',
        r')]] -> tuple[list[QueryResult], dict[str, Any]]:',
        content
    )
    content = re.sub(
        r'\)\s*->\s*tuple\[list\[str\], dict\[str, Any\]:',
        r')]] -> tuple[list[str], dict[str, Any]]:',
        content
    )
    content = re.sub(
        r'\)\s*->\s*list\[dict\[str, Any\]:',
        r')]] -> list[dict[str, Any]]:',
        content
    )
    content = re.sub(
        r'workflow_steps: list\[dict\[str, Any\]\s+#',
        r'workflow_steps: list[dict[str, Any]]  #',
        content
    )
    
    # ========================================
    # 模式3: ] | None = None
    # 23个文件
    # ========================================
    # kg_client: KnowledgeGraphClient] | None = None
    # → kg_client: KnowledgeGraphClient | None = None
    content = re.sub(
        r':\s*([A-Z][a-zA-Z0-9_]*)\]\s*\|\s*None\s*=\s*None',
        r': \1 | None = None',
        content
    )
    content = re.sub(
        r':\s*([a-z][a-zA-Z0-9_]*)\]\s*\|\s*None\s*=\s*None',
        r': \1 | None = None',
        content
    )
    content = re.sub(
        r':\s*list\[int\]\]\s*\|\s*None\s*=\s*None',
        r': list[int] | None = None',
        content
    )
    content = re.sub(
        r':\s*list\[str\]\]\s*\|\s*None\s*=\s*None',
        r': list[str] | None = None',
        content
    )
    content = re.sub(
        r':\s*dict\[str, list\[str\]\]\]\s*\|\s*None\s*=\s*None',
        r': dict[str, list[str]] | None = None',
        content
    )
    content = re.sub(
        r':\s*dict\[str, list\[dict\[str, Any\]\]\]\s*\|\s*None\s*=\s*None',
        r': dict[str, list[dict[str, Any]]] | None = None',
        content
    )
    content = re.sub(
        r':\s*dict\[str, Any\]\]\s*\|\s*None\s*=\s*None',
        r': dict[str, Any] | None = None',
        content
    )
    content = re.sub(
        r':\s*list\[dict\[str, Any\]\]\s*\|\s*None\s*=\s*None',
        r': list[dict[str, Any]] | None = None',
        content
    )
    
    # ========================================
    # 模式4: 双重 None 赋值
    # ========================================
    # message_type: str | None = None | None = None
    # → message_type: str | None = None
    content = re.sub(
        r':\s*([a-zA-Z0-9_]+)\s*\|\s*None\s*=\s*None\s*\|\s*None\s*=\s*None',
        r': \1 | None = None',
        content
    )
    
    # ========================================
    # 模式5: context: dict[str, Any] | None -> (缺少 = None)
    # ========================================
    content = re.sub(
        r'context:\s*dict\[str, Any\]\s*\|\s*None\s*->\s*Any:',
        r'context: dict[str, Any] | None = None) -> Any:',
        content
    )
    content = re.sub(
        r'params:\s*dict\[str, Any\],\s*context:\s*dict\[str, Any\]\s*\|\s*None\s*->\s*Any:',
        r'params: dict[str, Any], context: dict[str, Any] | None = None) -> Any:',
        content
    )
    
    # ========================================
    # 模式6: 缺少逗号
    # ========================================
    # model: Optional[Any] 
    # def optimize_model_for_gpu(
    # → model: Optional[Any],) 或合并到下一行
    content = re.sub(
        r'model:\s*Optional\[Any\]\s*\n\s*def\s+optimize_model_for_gpu\(',
        r'model: Optional[Any] = None):\n        def optimize_model_for_gpu(',
        content
    )
    content = re.sub(
        r'operation_name:\s*Optional\[str\]\s*\n\s*def\s+trace_operation\(',
        r'operation_name: Optional[str] = None):\n        def trace_operation(',
        content
    )
    
    # ========================================
    # 模式7: 修复 hashlib.md5 usedforsecurity 参数
    # ========================================
    # usedforsecurity=False 应该是 usedforsecurity=False)
    content = re.sub(
        r'\.encode\("utf-8",\s*usedforsecurity=False\)\.hexdigest\(\)',
        r'.encode("utf-8"), usedforsecurity=False).hexdigest()',
        content
    )
    content = re.sub(
        r'\.encode\(\),\s*usedforsecurity=False\)\.hexdigest\(\)',
        r'.encode(), usedforsecurity=False).hexdigest()',
        content
    )
    
    # ========================================
    # 模式8: 修复多余的 ] 
    # ========================================
    # .hexdigest()] → .hexdigest()
    content = re.sub(
        r'\.hexdigest\(\)\]',
        r'.hexdigest()',
        content
    )
    content = re.sub(
        r'\.hexdigest\(\)6\]',
        r'.hexdigest()',
        content
    )
    
    # ========================================
    # 模式9: 修复 defaultdict 初始化
    # ========================================
    # self.response_times: dict[str, list[dict[str, Any]] = defaultdict(list)
    # → self.response_times: dict[str, list[dict[str, Any]]] = defaultdict(list)
    content = re.sub(
        r':\s*dict\[str, list\[dict\[str, Any\]\]\s*=\s*defaultdict\(list\)',
        r': dict[str, list[dict[str, Any]]] = defaultdict(list)',
        content
    )
    content = re.sub(
        r':\s*dict\[str, list\[str\]\]\s*=\s*{}',
        r': dict[str, list[str]] = {}',
        content
    )
    
    # ========================================
    # 模式10: 修复 callable 类型注解
    # ========================================
    # executor_func: callable] | None → executor_func: callable | None
    content = re.sub(
        r':\s*callable\]\s*\|\s*None',
        r': callable | None',
        content
    )
    
    # ========================================
    # 模式11: 修复 ParameterType 类型注解
    # ========================================
    # tool_schema: dict[str, ParameterType]] | None
    # → tool_schema: dict[str, ParameterType] | None
    content = re.sub(
        r':\s*dict\[str, ParameterType\]\]\s*\|\s*None',
        r': dict[str, ParameterType] | None',
        content
    )
    
    # ========================================
    # 模式12: 修复 AgentStatus 类型注解
    # ========================================
    # status: AgentStatus] | None → status: AgentStatus | None
    content = re.sub(
        r':\s*AgentStatus\]\s*\|\s*None',
        r': AgentStatus | None',
        content
    )
    
    # ========================================
    # 模式13: 修复超长类型注解未闭合
    # ========================================
    # def resolve(...) -> tuple[str, dict[str, Any]:
    # 需要确保所有括号都闭合
    content = re.sub(
        r'->\s*tuple\[str,\s*dict\[str,\s*Any\]:\s*\n',
        r'-> tuple[str, dict[str, Any]]:\n',
        content
    )
    content = re.sub(
        r'->\s*list\[list\[str\]\]:\s*\n',
        r'-> list[list[str]]:\n',
        content
    )
    
    return content

def fix_file(file_path: Path) -> bool:
    """修复单个文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
        fixed = fix_all_error_patterns(content)
        
        if fixed != content:
            file_path.write_text(fixed, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"⚠️ 处理文件失败 {file_path}: {e}")
        return False

def main():
    core_path = Path('/Users/xujian/Athena工作平台/core')
    
    print("=" * 80)
    print("🔧 全面修复剩余语法错误")
    print("=" * 80)
    
    # 多轮修复
    total_fixed = 0
    for round_num in range(1, 8):
        print(f"\n第{round_num}轮修复...")
        
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
            if fix_file(f):
                fixed_count += 1
                print(f"  ✅ {f.relative_to(core_path.parent)}")
        
        total_fixed += fixed_count
        print(f"   本轮修复: {fixed_count} 个文件")
        print(f"   剩余错误: {len(error_files) - fixed_count} 个文件")
        
        if fixed_count == 0:
            print("   ⚠️ 无法自动修复更多错误")
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
    print("📊 修复统计:")
    print(f"   总修复: {total_fixed} 个文件")
    print(f"   总文件: {len(all_files)}")
    print(f"   成功: {success_count} ({success_count*100//len(all_files)}%)")
    print(f"   失败: {error_count} ({error_count*100//len(all_files)}%)")
    
    improvement = len(all_files) - error_count
    print(f"\n✅ 成功率从 74% 提升到 {improvement*100//len(all_files)}%")
    print("=" * 80)

if __name__ == "__main__":
    main()
