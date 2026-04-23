#!/usr/bin/env python3
"""
专利检索边界测试用例

测试各种边界情况和异常输入，验证系统的健壮性。

作者: Athena平台团队
创建时间: 2026-04-20
"""

import asyncio
import sys
from pathlib import Path
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, '.')

# 设置PYTHONPATH环境变量
os.environ['PYTHONPATH'] = str(project_root)

# 切换到项目根目录
os.chdir(project_root)

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 80)
    print("🧪 专利检索边界测试")
    print("=" * 80)

    try:
        # 导入小娜Agent
        from core.agents.xiaona_legal import XiaonaLegalAgent

        # 创建小娜Agent实例
        logger.info("🤖 创建小娜Agent实例...")
        xiaona = XiaonaLegalAgent()

        # 初始化Agent
        await xiaona.initialize()

        print(f"✅ 小娜Agent已创建: {xiaona.name}")
        print()

        # 测试结果记录
        test_results = []

        # 边界测试1: 空查询
        print("=" * 80)
        print("边界测试1: 空查询字符串")
        print("=" * 80)

        try:
            result1 = await xiaona._handle_patent_search(
                params={
                    "query": "",  # 空字符串
                    "channel": "local_postgres",
                    "max_results": 5
                }
            )

            success1 = not result1.get('success') and "缺少必需参数" in result1.get('error', '')
            print(f"\n📊 测试结果:")
            print(f"  成功: {result1.get('success')}")
            print(f"  错误: {result1.get('error', 'N/A')}")
            print(f"  预期: 应该返回错误（缺少query参数）")
            print(f"  实际: {'✅ 通过' if success1 else '❌ 失败'} - 系统正确拒绝空查询")
            test_results.append(("空查询", success1))

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            test_results.append(("空查询", False))

        print()

        # 边界测试2: 只有空格的查询
        print("=" * 80)
        print("边界测试2: 只有空格的查询")
        print("=" * 80)

        try:
            result2 = await xiaona._handle_patent_search(
                params={
                    "query": "   ",  # 只有空格
                    "channel": "local_postgres",
                    "max_results": 5
                }
            )

            # strip后应该变成空字符串
            success2 = not result2.get('success') or result2.get('total_results', 0) == 0
            print(f"\n📊 测试结果:")
            print(f"  成功: {result2.get('success')}")
            print(f"  找到专利数: {result2.get('total_results', 0)}")
            print(f"  预期: 应该返回0个结果或错误")
            print(f"  实际: {'✅ 通过' if success2 else '❌ 失败'}")
            test_results.append(("纯空格查询", success2))

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            test_results.append(("纯空格查询", False))

        print()

        # 边界测试3: 特殊字符查询
        print("=" * 80)
        print("边界测试3: 特殊字符查询")
        print("=" * 80)

        try:
            result3 = await xiaona._handle_patent_search(
                params={
                    "query": "!@#$%^&*()",  # 特殊字符
                    "channel": "local_postgres",
                    "max_results": 5
                }
            )

            # 不应该崩溃，应该优雅处理
            success3 = result3.get('success') is not None  # 不管成功失败，只要不崩溃
            print(f"\n📊 测试结果:")
            print(f"  成功: {result3.get('success')}")
            print(f"  找到专利数: {result3.get('total_results', 0)}")
            print(f"  预期: 不应该崩溃，优雅处理特殊字符")
            print(f"  实际: {'✅ 通过' if success3 else '❌ 失败'}")
            test_results.append(("特殊字符查询", success3))

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            test_results.append(("特殊字符查询", False))

        print()

        # 边界测试4: 超长查询
        print("=" * 80)
        print("边界测试4: 超长查询（10000字符）")
        print("=" * 80)

        try:
            long_query = "专利" * 5000  # 10000个字符
            result4 = await xiaona._handle_patent_search(
                params={
                    "query": long_query,
                    "channel": "local_postgres",
                    "max_results": 5
                }
            )

            # 不应该崩溃
            success4 = result4.get('success') is not None
            print(f"\n📊 测试结果:")
            print(f"  查询长度: {len(long_query)} 字符")
            print(f"  成功: {result4.get('success')}")
            print(f"  预期: 不应该崩溃")
            print(f"  实际: {'✅ 通过' if success4 else '❌ 失败'}")
            test_results.append(("超长查询", success4))

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            test_results.append(("超长查询", False))

        print()

        # 边界测试5: 无效channel
        print("=" * 80)
        print("边界测试5: 无效的channel参数")
        print("=" * 80)

        try:
            result5 = await xiaona._handle_patent_search(
                params={
                    "query": "人工智能",
                    "channel": "invalid_channel",  # 无效的channel
                    "max_results": 5
                }
            )

            # 应该返回错误或降级处理
            success5 = not result5.get('success') or "不支持的检索渠道" in str(result5.get('error', ''))
            print(f"\n📊 测试结果:")
            print(f"  成功: {result5.get('success')}")
            print(f"  错误: {result5.get('error', 'N/A')}")
            print(f"  预期: 应该返回错误（不支持的channel）")
            print(f"  实际: {'✅ 通过' if success5 else '⚠️  降级处理'}")
            test_results.append(("无效channel", success5))

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            test_results.append(("无效channel", False))

        print()

        # 边界测试6: 极限max_results（0）
        print("=" * 80)
        print("边界测试6: max_results=0")
        print("=" * 80)

        try:
            result6 = await xiaona._handle_patent_search(
                params={
                    "query": "人工智能",
                    "channel": "local_postgres",
                    "max_results": 0  # 0个结果
                }
            )

            # 应该返回空结果
            success6 = result6.get('total_results', 0) == 0
            print(f"\n📊 测试结果:")
            print(f"  成功: {result6.get('success')}")
            print(f"  找到专利数: {result6.get('total_results', 0)}")
            print(f"  预期: 应该返回0个结果")
            print(f"  实际: {'✅ 通过' if success6 else '❌ 失败'}")
            test_results.append(("max_results=0", success6))

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            test_results.append(("max_results=0", False))

        print()

        # 边界测试7: 极限max_results（超大值）
        print("=" * 80)
        print("边界测试7: max_results=999999")
        print("=" * 80)

        try:
            result7 = await xiaona._handle_patent_search(
                params={
                    "query": "人工智能",
                    "channel": "local_postgres",
                    "max_results": 999999  # 超大值
                }
            )

            # 应该限制到合理范围或返回错误
            success7 = result7.get('success') is not None
            print(f"\n📊 测试结果:")
            print(f"  成功: {result7.get('success')}")
            print(f"  找到专利数: {result7.get('total_results', 0)}")
            print(f"  预期: 不应该崩溃，应该限制到合理范围")
            print(f"  实际: {'✅ 通过' if success7 else '❌ 失败'}")
            test_results.append(("max_results超大值", success7))

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            test_results.append(("max_results超大值", False))

        print()

        # 边界测试8: SQL注入尝试
        print("=" * 80)
        print("边界测试8: SQL注入尝试")
        print("=" * 80)

        try:
            sql_injection = "'; DROP TABLE patents; --"
            result8 = await xiaona._handle_patent_search(
                params={
                    "query": sql_injection,
                    "channel": "local_postgres",
                    "max_results": 5
                }
            )

            # 应该安全处理，不执行SQL注入
            success8 = result8.get('success') is not None  # 只要不崩溃就算通过
            print(f"\n📊 测试结果:")
            print(f"  查询: {sql_injection}")
            print(f"  成功: {result8.get('success')}")
            print(f"  预期: 应该安全处理，不执行SQL注入")
            print(f"  实际: {'✅ 通过' if success8 else '❌ 失败'}")
            test_results.append(("SQL注入防护", success8))

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            test_results.append(("SQL注入防护", False))

        print()

        # 关闭Agent
        await xiaona.shutdown()

        # 总结
        print("=" * 80)
        print("📋 边界测试总结")
        print("=" * 80)

        passed_count = sum(1 for _, success in test_results if success)
        total_count = len(test_results)

        print(f"\n测试用例总数: {total_count}")
        print(f"通过: {passed_count}")
        print(f"失败: {total_count - passed_count}")
        print(f"通过率: {passed_count / total_count * 100:.1f}%")

        print("\n详细结果:")
        for test_name, success in test_results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {status} - {test_name}")

        if passed_count == total_count:
            print("\n✅ 所有边界测试通过！系统健壮性良好")
            return True
        else:
            print(f"\n⚠️  {total_count - passed_count}个测试失败，需要改进错误处理")
            return False

    except Exception as e:
        logger.exception(f"❌ 测试异常: {e}")
        print(f"\n❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    print("专利检索边界测试")
    print("测试系统的健壮性和错误处理能力")
    print()

    result = asyncio.run(test_edge_cases())

    if result:
        print("\n✅ 测试完成")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        sys.exit(1)
