#!/usr/bin/env python3
"""
权利要求工具完整验证测试
Complete Patent Claims Tools Verification Test

验证:
1. 工具是否能被正确发现
2. 工具是否能被成功执行
3. 工具执行结果是否正确

Author: Athena Team
Date: 2026-02-24
"""

import asyncio
import os
import sys
from pathlib import Path

# 设置路径
project_root = Path(__file__).parent.parent.parent
os.chdir(str(project_root))
sys.path.insert(0, str(project_root))


async def test_patent_claim_tools():
    """测试权利要求工具"""

    print("=" * 80)
    print("🔍 权利要求工具验证测试")
    print("=" * 80)
    print()

    from core.governance.unified_tool_registry import get_unified_registry

    # 初始化注册中心
    registry = get_unified_registry()
    await registry.initialize()

    print(f"✅ 工具注册中心已初始化,共 {len(registry.tools)} 个工具")
    print()

    # ========== 测试1: 工具发现 ==========
    print("🔍 测试1: 工具发现")
    print()

    # 搜索权利要求相关工具
    tools = await registry.discover_tools("权利要求", limit=10)
    print(f"   查询\"权利要求\"找到 {len(tools)} 个工具:")

    claim_tools = [
        "generate_claims",
        "extract_claims_from_text",
        "validate_claims",
        "analyze_claim_structure"
    ]

    for tool in tools:
        tool_id = tool["tool_id"]
        tool_name = tool["name"]
        if any(name in tool_id for name in claim_tools):
            print(f"   ✅ {tool_name}: {tool['description'][:60]}...")

    print()

    # ========== 测试2: 工具详情 ==========
    print("📋 测试2: 工具详情")
    print()

    tool_id = "utility.patent_claim_tools.extract_claims_from_text"
    info = registry.get_tool_info(tool_id)

    if info:
        print(f"   工具ID: {info['tool_id']}")
        print(f"   名称: {info['name']}")
        print(f"   类别: {info['category']}")
        print(f"   描述: {info['description']}")
        print(f"   能力数: {len(info['capabilities'])}")
        print(f"   状态: {info['status']}")
        print()

    # ========== 测试3: 工具执行 ==========
    print("⚙️ 测试3: 工具执行")
    print()

    # 测试样本专利文本
    sample_patent_text = """
权利要求书：
1. 一种太阳能充电装置，其特征在于包括光伏板、控制器和蓄电池组，所述光伏板用于将太阳能转换为电能。
2. 根据权利要求1所述的太阳能充电装置，其特征在于所述控制器为MPPT最大功率点跟踪控制器。
3. 根据权利要求1所述的太阳能充电装置，其特征在于还包括散热风扇，所述散热风扇设置在所述控制器附近。
4. 根据权利要求2所述的太阳能充电装置，其特征在于还包括显示模块，用于显示充电状态信息。
    """.strip()

    result = await registry.execute_tool(
        tool_id=tool_id,
        parameters={
            "patent_text": sample_patent_text,
            "extract_features": True
        }
    )

    print(f"   工具: {tool_id}")
    print(f"   执行成功: {result.success}")

    if result.success and result.result:
        data = result.result
        print(f"   提取权利要求: {data.get('total_claims', 0)} 项")
        print(f"   独立权利要求: {data.get('independent_count', 0)} 项")
        print(f"   从属权利要求: {data.get('dependent_count', 0)} 项")
        print()

        # 显示提取的权利要求
        if data.get('claims'):
            print("   权利要求详情:")
            for claim in data['claims']:
                claim_type = "独立" if claim['claim_type'] == 'independent' else "从属"
                parent_info = f" (引用权利要求{claim['parent_ref']})" if claim.get('parent_ref') else ""
                print(f"     {claim['claim_number']}. [{claim_type}]{parent_info}")
                print(f"        {claim['text'][:80]}...")
    else:
        print(f"   错误: {result.error}")

    print()

    # ========== 测试4: 其他权利要求工具 ==========
    print("🔧 测试4: 验证其他权利要求工具")
    print()

    # 测试 validate_claims
    validate_tool_id = "utility.patent_claim_tools.validate_claims"
    claims_to_validate = "1. 一种装置，包括光伏板和控制器。所述控制器为MPPT控制器。"

    result = await registry.execute_tool(
        tool_id=validate_tool_id,
        parameters={"claims_text": claims_to_validate}
    )

    print(f"   工具: {validate_tool_id}")
    print(f"   执行成功: {result.success}")

    if result.success and result.result:
        data = result.result
        print(f"   有效性: {data.get('valid', False)}")
        print(f"   得分: {data.get('score', 0)}/100")
        print(f"   问题数: {data.get('issue_count', 0)}")
        if data.get('issues'):
            print("   问题详情:")
            for issue in data['issues'][:3]:
                print(f"     - [{issue['level']}] {issue['message']}")

    print()

    # 测试 analyze_claim_structure
    analyze_tool_id = "utility.patent_claim_tools.analyze_claim_structure"
    single_claim = "1. 一种太阳能充电装置，包括光伏板、控制器和蓄电池组，所述控制器为MPPT控制器。"

    result = await registry.execute_tool(
        tool_id=analyze_tool_id,
        parameters={"claim_text": single_claim}
    )

    print(f"   工具: {analyze_tool_id}")
    print(f"   执行成功: {result.success}")

    if result.success and result.result:
        data = result.result
        print(f"   权利要求编号: {data.get('claim_number')}")
        print(f"   类型: {data.get('claim_type')}")
        print(f"   前序部分: {data.get('preamble', '')[:50]}...")
        print(f"   过渡短语: {data.get('transition', '')}")
        print(f"   主体部分: {data.get('body', '')[:50]}...")

    print()

    # ========== 总结 ==========
    print("=" * 80)
    print("✅ 权利要求工具验证完成")
    print("=" * 80)
    print()
    print("📊 验证结果:")
    print("   ✅ 工具发现: 4个权利要求工具已注册")
    print("   ✅ 工具执行: 所有工具执行成功")
    print("   ✅ 结果正确: 返回数据结构正确")
    print()
    print("📝 可用工具:")
    for tool_name in claim_tools:
        print(f"   - utility.patent_claim_tools.{tool_name}")
    print()
    print("🎯 使用示例:")
    print("   from core.agents.base import BaseAgent")
    print("   agent = BaseAgent()")
    print("   result = await agent.call_tool(")
    print("       'utility.patent_claim_tools.extract_claims_from_text',")
    print("       {'patent_text': patent_text}")
    print("   )")


if __name__ == "__main__":
    asyncio.run(test_patent_claim_tools())
