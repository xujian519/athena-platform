#!/usr/bin/env python3
"""验证已注册的生产工具"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tools.base import get_global_registry


def main():
    registry = get_global_registry()

    # 获取所有已注册的工具
    tools = registry._tools

    print('📋 已注册的工具列表:')
    print('=' * 60)

    if not tools:
        print('  ⚠️  没有找到已注册的工具')
        print('\n提示: 运行 python3 scripts/register_production_tools.py 来注册工具')
        return 1

    for tool_id, tool in tools.items():
        status = '✅ 启用' if tool.enabled else '❌ 禁用'
        print(f'\n  • {tool_id}')
        print(f'    名称: {tool.name}')
        print(f'    分类: {tool.category.value}')
        print(f'    优先级: {tool.priority.value}')
        print(f'    状态: {status}')
        print(f'    描述: {tool.description[:80]}...')

        if tool.capability:
            print(f'    输入类型: {", ".join(tool.capability.input_types)}')
            print(f'    输出类型: {", ".join(tool.capability.output_types)}')
            print(f'    支持领域: {", ".join(tool.capability.domains)}')
            print(f'    任务类型: {", ".join(tool.capability.task_types)}')

    stats = registry.get_statistics()
    print('\n' + '=' * 60)
    print(f'📊 总计: {stats["total_tools"]} 个工具')
    print(f'   - 启用: {stats["enabled_tools"]} 个')
    print(f'   - 禁用: {stats["disabled_tools"]} 个')

    # 检查生产工具
    print('\n' + '=' * 60)
    print('🔍 生产工具检查:')

    production_tools = {
        'local_web_search': '本地网络搜索',
        'enhanced_document_parser': '增强文档解析器'
    }

    for tool_id, tool_name in production_tools.items():
        if tool_id in tools:
            tool = tools[tool_id]
            if tool.enabled:
                print(f'  ✅ {tool_name} 已注册并启用')
            else:
                print(f'  ⚠️  {tool_name} 已注册但未启用')
        else:
            print(f'  ❌ {tool_name} 未注册')

    return 0


if __name__ == '__main__':
    sys.exit(main())
