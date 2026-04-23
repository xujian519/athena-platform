#!/usr/bin/env python3
"""
法律文献分析工具验证测试

验证legal_analysis工具的完整性和可用性。

Author: Athena平台团队
Created: 2026-04-19
Version: v1.0.0
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def test_legal_analysis_handler():
    """测试法律分析处理器"""
    print("=" * 80)
    print("法律文献分析工具验证测试")
    print("=" * 80)

    # 导入处理器
    try:
        from core.tools.legal_analysis_handler import legal_analysis_handler
        print("✅ 步骤1: Handler导入成功")
    except Exception as e:
        print(f"❌ 步骤1: Handler导入失败: {e}")
        return False

    # 测试用例
    test_cases = [
        {
            "name": "专利咨询",
            "query": "如何申请发明专利？需要什么材料？",
            "expected_need": "patent_inquiry",
        },
        {
            "name": "商标咨询",
            "query": "商标注册流程是怎样的？",
            "expected_need": "trademark_inquiry",
        },
        {
            "name": "版权咨询",
            "query": "版权保护有哪些特点？",
            "expected_need": "copyright_inquiry",
        },
        {
            "name": "法律策略",
            "query": "如何制定知识产权保护策略？",
            "expected_need": "legal_strategy",
        },
        {
            "name": "案件分析",
            "query": "帮我分析这个专利侵权案件",
            "expected_need": "case_analysis",
        },
    ]

    print("\n" + "=" * 80)
    print("步骤2: 功能测试")
    print("=" * 80)

    all_passed = True

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}/{len(test_cases)}: {test_case['name']}")
        print(f"查询: {test_case['query']}")

        try:
            # 执行分析
            result = await legal_analysis_handler(test_case['query'])

            # 验证结果
            if result['status'] != 'success':
                print(f"❌ 执行失败: {result.get('error', 'Unknown error')}")
                all_passed = False
                continue

            # 验证法律需求识别
            legal_need = result.get('legal_need')
            if legal_need != test_case['expected_need']:
                print(f"⚠️  需求识别不匹配: 期望 {test_case['expected_need']}, 得到 {legal_need}")
            else:
                print(f"✅ 需求识别正确: {legal_need}")

            # 验证结果内容
            result_text = result.get('result', '')
            if not result_text:
                print("❌ 结果为空")
                all_passed = False
            else:
                print(f"✅ 结果长度: {len(result_text)} 字符")
                print(f"⏱️  执行时间: {result.get('execution_time', 0):.3f}秒")

                # 显示结果预览
                preview = result_text[:200].replace('\n', ' ')
                print(f"📄 结果预览: {preview}...")

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            all_passed = False

    # 测试错误处理
    print("\n" + "=" * 80)
    print("步骤3: 错误处理测试")
    print("=" * 80)

    # 空查询测试
    print("\n测试: 空查询")
    try:
        result = await legal_analysis_handler("")
        if result['status'] == 'error':
            print("✅ 空查询正确拒绝")
        else:
            print("❌ 空查询未正确拒绝")
            all_passed = False
    except Exception as e:
        print(f"⚠️  空查询测试异常: {e}")

    # 无效类型测试
    print("\n测试: 无效类型")
    try:
        result = await legal_analysis_handler(12345)  # type: ignore
        if result['status'] == 'error':
            print("✅ 无效类型正确拒绝")
        else:
            print("❌ 无效类型未正确拒绝")
            all_passed = False
    except Exception as e:
        print(f"⚠️  无效类型测试异常: {e}")

    # 测试工具注册
    print("\n" + "=" * 80)
    print("步骤4: 工具注册验证")
    print("=" * 80)

    try:
        from core.tools.base import get_unified_registry

        registry = get_unified_registry()
        tool = registry.get("legal_analysis")

        if tool:
            print("✅ 工具已注册到统一注册表")
            print(f"   工具名称: {tool.name}")
            print(f"   工具描述: {tool.description}")
            print(f"   工具分类: {tool.category.value}")
            print(f"   工具优先级: {tool.priority.value}")

            # 验证能力
            if tool.capability:
                print(f"   输入类型: {tool.capability.input_types}")
                print(f"   输出类型: {tool.capability.output_types}")
                print(f"   适用领域: {tool.capability.domains}")
                print(f"   任务类型: {tool.capability.task_types}")
                print(f"   特性: {list(tool.capability.features.keys())}")
        else:
            print("❌ 工具未注册到统一注册表")
            all_passed = False

    except Exception as e:
        print(f"❌ 工具注册验证失败: {e}")
        all_passed = False

    # 最终结果
    print("\n" + "=" * 80)
    print("验证结果")
    print("=" * 80)

    if all_passed:
        print("✅ 所有测试通过！legal_analysis工具验证成功")
        return True
    else:
        print("❌ 部分测试失败，请检查上述错误")
        return False


async def test_legal_analysis_performance():
    """性能测试"""
    print("\n" + "=" * 80)
    print("性能测试")
    print("=" * 80)

    import time

    from core.tools.legal_analysis_handler import legal_analysis_handler

    # 并发测试
    queries = [
        "专利申请流程",
        "商标注册要求",
        "版权保护期限",
        "知识产权策略",
        "专利侵权分析",
    ]

    print(f"\n并发执行 {len(queries)} 个查询...")

    start_time = time.time()

    tasks = [legal_analysis_handler(q) for q in queries]
    results = await asyncio.gather(*tasks)

    total_time = time.time() - start_time

    print("✅ 并发执行完成")
    print(f"   总耗时: {total_time:.3f}秒")
    print(f"   平均耗时: {total_time/len(queries):.3f}秒/查询")
    print(f"   吞吐量: {len(queries)/total_time:.2f} 查询/秒")

    # 验证所有结果
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"   成功率: {success_count}/{len(queries)} ({success_count/len(queries)*100:.1f}%)")


async def main():
    """主函数"""
    print("开始验证legal_analysis工具...\n")

    # 基础验证
    success = await test_legal_analysis_handler()

    # 性能测试（仅在基础验证通过后执行）
    if success:
        await test_legal_analysis_performance()

    print("\n" + "=" * 80)
    print("验证完成")
    print("=" * 80)

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
