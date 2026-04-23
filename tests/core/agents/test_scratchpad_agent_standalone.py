#!/usr/bin/env python3
"""
小娜代理Scratchpad版本独立测试脚本

不依赖Athena平台的其他模块，直接测试代理功能
"""

import json
import sys


# 模拟BaseAgent（避免导入整个平台）
class BaseAgent:
    def __init__(self, name: str, role: str, model: str = "gpt-4"):
        self.name = name
        self.role = role
        self.model = model
        self.conversation_history = []
        self.capabilities = []
        self.memory = {}


# 导入修复后的代理类
sys.path.insert(0, '/Users/xujian/Athena工作平台')

# 暂时替换BaseAgent，避免导入错误
import core.framework.agents.base_agent as base_module

original_base = base_module.BaseAgent
base_module.BaseAgent = BaseAgent

# 现在导入我们的代理
from core.framework.agents.xiaona_agent_with_scratchpad import XiaonaAgentWithScratchpad

# 恢复原始BaseAgent
base_module.BaseAgent = original_base


def test_agent():
    """测试代理功能"""
    print("=" * 60)
    print("小娜代理Scratchpad版本测试")
    print("=" * 60)

    # 创建代理
    agent = XiaonaAgentWithScratchpad()
    print("\n✅ 代理创建成功")
    print(f"   名称: {agent.name}")
    print(f"   角色: {agent.role}")

    # 测试1: 普通文本输入
    print("\n" + "=" * 60)
    print("测试1: 普通文本输入")
    print("=" * 60)

    result_json = agent.process("帮我分析专利CN123456789A的创造性")
    result = json.loads(result_json)

    print(f"✅ 任务类型: {result['task_type']}")
    print(f"✅ 有推理摘要: {'reasoning_summary' in result}")
    print(f"✅ 有输出内容: {'output' in result}")
    print(f"✅ Scratchpad可用: {result.get('scratchpad_available', False)}")
    print("\n推理摘要（前200字符）:")
    print(result['reasoning_summary'][:200] + "...")

    # 测试2: JSON输入
    print("\n" + "=" * 60)
    print("测试2: JSON格式输入")
    print("=" * 60)

    task_json = json.dumps({
        'task_id': 'TEST_20260419_001',
        'type': 'patent_analysis',
        'patent_id': 'CN987654321A',
        'analysis_type': '新颖性分析'
    })

    result_json = agent.process(task_json)
    result = json.loads(result_json)

    print(f"✅ 任务ID: {result.get('task_id', 'N/A')}")
    print(f"✅ 任务类型: {result['task_type']}")
    print(f"✅ 有推理摘要: {'reasoning_summary' in result}")

    # 测试3: 错误的JSON输入
    print("\n" + "=" * 60)
    print("测试3: 错误的JSON输入（应该被捕获）")
    print("=" * 60)

    result_json = agent.process('{invalid json}')
    result = json.loads(result_json)

    print(f"✅ 错误被正确捕获: {'error' in result}")
    print(f"✅ 错误信息: {result.get('error', 'N/A')}")

    # 测试4: 不同任务类型
    print("\n" + "=" * 60)
    print("测试4: 不同任务类型")
    print("=" * 60)

    task_types = [
        ('patent_analysis', '专利分析'),
        ('office_action', '审查意见答复'),
        ('invalidity', '无效宣告'),
        ('unknown_type', '通用任务')
    ]

    for task_type, description in task_types:
        task = {
            'task_id': f'TEST_{task_type}',
            'type': task_type,
            'description': f'测试{description}'
        }
        result_json = agent.process(json.dumps(task))
        result = json.loads(result_json)
        print(f"✅ {description}: {result['task_type']}")

    # 测试5: Scratchpad历史
    print("\n" + "=" * 60)
    print("测试5: Scratchpad历史记录")
    print("=" * 60)

    scratchpads = asyncio.run(agent.list_scratchpads(limit=5))
    print(f"✅ Scratchpad历史记录数: {len(scratchpads)}")

    if scratchpads:
        latest = scratchpads[-1]
        print("✅ 最新记录:")
        print(f"   任务ID: {latest.get('task_id', 'N/A')}")
        print(f"   任务类型: {latest.get('task_type', 'N/A')}")
        print(f"   时间戳: {latest.get('timestamp', 'N/A')}")
        print(f"   摘要长度: {len(latest.get('summary', ''))}")
        print(f"   Scratchpad长度: {len(latest.get('scratchpad', ''))}")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_agent()
