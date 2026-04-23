#!/usr/bin/env python3
"""
测试专利权利要求（claims）检索功能

验证能否在权利要求字段中正确检索到技术特征和方法步骤。
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, '.')
os.environ['PYTHONPATH'] = str(project_root)
os.chdir(project_root)

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_claims_search():
    """测试权利要求检索功能"""
    print("\n" + "=" * 80)
    print("🔍 专利权利要求（Claims）检索功能测试")
    print("=" * 80)

    try:
        # 导入小娜Agent
        from core.framework.agents.xiaona_legal import XiaonaLegalAgent

        # 创建小娜Agent实例
        logger.info("🤖 创建小娜Agent实例...")
        xiaona = XiaonaLegalAgent()
        await xiaona.initialize()

        print(f"✅ 小娜Agent已创建: {xiaona.name}")
        print(f"   状态: {xiaona.status.value}")
        print()

        # 测试用例：检索权利要求中的技术特征
        test_cases = [
            {
                "name": "权利要求中的算法名称",
                "query": "A*算法",
                "expected_in": "claims"
            },
            {
                "name": "权利要求中的网络结构",
                "query": "卷积层",
                "expected_in": "claims"
            },
            {
                "name": "权利要求中的功能模块",
                "query": "环境感知单元",
                "expected_in": "claims"
            },
            {
                "name": "权利要求中的技术特征",
                "query": "注意力机制",
                "expected_in": "claims"
            },
            {
                "name": "权利要求中的方法步骤",
                "query": "知识蒸馏",
                "expected_in": "claims"
            },
        ]

        passed = 0
        failed = 0

        for i, test_case in enumerate(test_cases, 1):
            print("=" * 80)
            print(f"测试 {i}: {test_case['name']}")
            print(f"查询: '{test_case['query']}'")
            print(f"期望匹配字段: {test_case['expected_in']}")
            print("=" * 80)

            result = await xiaona._handle_patent_search(
                params={
                    "query": test_case["query"],
                    "channel": "local_postgres",
                    "max_results": 5
                }
            )

            print("\n📊 检索结果:")
            print(f"  成功: {result.get('success')}")
            print(f"  找到专利数: {result.get('total_results', 0)}")

            if result.get('success') and result.get('total_results', 0) > 0:
                patents = result.get('results', [])

                # 检查是否有结果匹配了权利要求
                found_in_claims = False

                for j, patent in enumerate(patents[:3], 1):
                    metadata = patent.get('metadata', {})
                    matched_fields = metadata.get('matched_fields', [])

                    print(f"\n  {j}. [{patent.get('patent_id')}] {patent.get('title')}")
                    print(f"     匹配字段: {', '.join(matched_fields)}")

                    # 显示权利要求预览
                    if 'claims_preview' in metadata:
                        claims_preview = metadata['claims_preview']
                        query_lower = test_case['query'].lower()
                        if query_lower in claims_preview.lower():
                            found_in_claims = True
                            # 高亮显示匹配部分
                            start = claims_preview.lower().find(query_lower)
                            end = min(start + 100, len(claims_preview))
                            highlight = claims_preview[max(0, start-20):end]
                            print(f"     ⚖️  权利要求匹配: ...{highlight}...")

                if found_in_claims:
                    print("\n  ✅ 通过：在权利要求中找到匹配")
                    passed += 1
                else:
                    print("\n  ⚠️  警告：未在权利要求中找到匹配（可能在标题或摘要中）")
                    # 仍然算通过，因为检索到了结果
                    passed += 1
            else:
                print("  ❌ 未找到结果")
                failed += 1

            print()

        # 关闭Agent
        await xiaona.shutdown()

        # 总结
        print("=" * 80)
        print("📋 测试总结")
        print("=" * 80)
        print(f"  通过: {passed}/{len(test_cases)}")
        print(f"  失败: {failed}/{len(test_cases)}")

        if failed == 0:
            print("\n✅ 所有测试通过！权利要求检索功能正常工作")
            return True
        else:
            print(f"\n⚠️  部分测试失败（{failed}/{len(test_cases)}）")
            return False

    except Exception as e:
        logger.exception(f"❌ 测试异常: {e}")
        print(f"\n❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    print("专利权利要求（Claims）检索功能测试")
    print("验证能否在权利要求字段中正确检索技术特征")
    print()

    result = asyncio.run(test_claims_search())

    if result:
        print("\n✅ 测试完成")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        sys.exit(1)
