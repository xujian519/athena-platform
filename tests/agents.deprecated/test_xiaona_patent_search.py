#!/usr/bin/env python3
"""
测试小娜Agent专利检索功能

验证小娜Agent能否正确调用专利检索工具并返回结构化结果。

作者: Athena平台团队
创建时间: 2026-04-20
"""

import asyncio
import sys
from pathlib import Path
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, '.')  # 添加当前目录到路径

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


async def test_patent_search():
    """测试专利检索功能"""
    print("\n" + "=" * 80)
    print("🔍 小娜Agent - 专利检索功能测试")
    print("=" * 80)

    try:
        # 确保路径正确
        import sys
        import os
        from pathlib import Path

        # 获取项目根目录（从tests/agents/向上两级）
        if __file__:
            project_root = Path(__file__).parent.parent.parent
        else:
            project_root = Path.cwd()

        # 确保项目根目录在sys.path中
        project_root_str = str(project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)

        # 确保当前目录在sys.path中
        if '.' not in sys.path:
            sys.path.insert(0, '.')

        # 切换到项目根目录
        os.chdir(project_root)

        print(f"📁 工作目录: {os.getcwd()}")
        print(f"📂 项目根目录: {project_root_str}")
        print(f"✅ core/agents/xiaona_legal.py存在: {Path('core/agents/xiaona_legal.py').exists()}")
        print()

        # 导入小娜Agent
        from core.agents.xiaona_legal import XiaonaLegalAgent

        # 创建小娜Agent实例
        logger.info("🤖 创建小娜Agent实例...")
        xiaona = XiaonaLegalAgent()

        # 初始化Agent
        await xiaona.initialize()

        print(f"✅ 小娜Agent已创建: {xiaona.name}")
        # metadata是内部属性，通过_load_metadata方法加载
        # print(f"   版本: {xiaona._metadata.version}")
        # print(f"   描述: {xiaona._metadata.description}")
        print(f"   状态: {xiaona.status.value}")
        print()

        # 测试1: 简单专利检索
        print("=" * 80)
        print("测试1: 简单专利检索 - '人工智能'")
        print("=" * 80)

        result1 = await xiaona._handle_patent_search(
            params={
                "query": "人工智能",
                "channel": "local_postgres",  # 使用本地PostgreSQL
                "max_results": 5
            }
        )

        print(f"\n📊 检索结果:")
        print(f"  成功: {result1.get('success')}")
        print(f"  消息: {result1.get('message')}")

        if result1.get('success'):
            total_found = result1.get('total_results', 0)
            patents = result1.get('results', [])

            print(f"  找到专利数: {total_found}")
            print(f"  检索策略: {result1.get('search_strategy')}")

            if patents:
                print(f"\n  前3个相关专利:")
                for i, patent in enumerate(patents[:3], 1):
                    print(f"    {i}. {patent.get('patent_id')} - {patent.get('title')}")
                    if patent.get('abstract'):
                        abstract = patent.get('abstract', '')[:100]
                        print(f"       摘要: {abstract}...")
        else:
            error = result1.get('error', 'UNKNOWN_ERROR')
            print(f"  ❌ 检索失败: {error}")

        print()

        # 测试2: 更具体的检索
        print("=" * 80)
        print("测试2: 具体专利检索 - '自动驾驶 路径规划'")
        print("=" * 80)

        result2 = await xiaona._handle_patent_search(
            params={
                "query": "自动驾驶车辆路径规划",
                "channel": "local_postgres",
                "max_results": 3
            }
        )

        print(f"\n📊 检索结果:")
        print(f"  成功: {result2.get('success')}")
        print(f"  消息: {result2.get('message')}")

        if result2.get('success'):
            total_found = result2.get('total_results', 0)
            print(f"  找到专利数: {total_found}")

            if 'execution_time_ms' in result2:
                print(f"  执行时间: {result2['execution_time_ms']}ms")

        print()

        # 测试3: Google Patents在线检索
        print("=" * 80)
        print("测试3: Google Patents在线检索 - 'artificial intelligence'")
        print("=" * 80)

        result3 = await xiaona._handle_patent_search(
            params={
                "query": "artificial intelligence machine learning",
                "channel": "google_patents",
                "max_results": 5
            }
        )

        print(f"\n📊 检索结果:")
        print(f"  成功: {result3.get('success')}")
        print(f"  消息: {result3.get('message')}")

        if result3.get('success'):
            total_found = result3.get('total_results', 0)
            patents = result3.get('results', [])

            print(f"  找到专利数: {total_found}")
            print(f"  检索策略: {result3.get('search_strategy', 'N/A')}")

            if patents:
                print(f"\n  前3个相关专利:")
                for i, patent in enumerate(patents[:3], 1):
                    print(f"    {i}. {patent.get('patent_id')} - {patent.get('title')}")
                    if patent.get('abstract'):
                        abstract = patent.get('abstract', '')[:100]
                        print(f"       摘要: {abstract}...")

            if 'execution_time_ms' in result3:
                print(f"  执行时间: {result3['execution_time_ms']}ms")
        else:
            error = result3.get('error', 'UNKNOWN_ERROR')
            print(f"  ❌ 检索失败: {error}")

        print()

        # 测试4: 双渠道对比
        print("=" * 80)
        print("测试4: 双渠道对比 - 'deep learning'")
        print("=" * 80)

        result4 = await xiaona._handle_patent_search(
            params={
                "query": "deep learning neural network",
                "channel": "both",
                "max_results": 3
            }
        )

        print(f"\n📊 检索结果:")
        print(f"  成功: {result4.get('success')}")
        print(f"  消息: {result4.get('message')}")

        if result4.get('success'):
            total_found = result4.get('total_results', 0)
            print(f"  找到专利数: {total_found}")
            print(f"  检索策略: {result4.get('search_strategy', 'N/A')}")

            # 显示渠道分布
            results = result4.get('results', [])
            if results:
                channel_count = {}
                for patent in results:
                    source = patent.get('source', 'unknown')
                    channel_count[source] = channel_count.get(source, 0) + 1

                print(f"  渠道分布: {channel_count}")
        else:
            error = result4.get('error', 'UNKNOWN_ERROR')
            print(f"  ❌ 检索失败: {error}")

        print()

        # 关闭Agent
        await xiaona.shutdown()

        # 总结
        print("=" * 80)
        print("📋 测试总结")
        print("=" * 80)

        success_count = sum([
            1 if result1.get('success') else 0,
            1 if result2.get('success') else 0,
            1 if result3.get('success') else 0,
            1 if result4.get('success') else 0,
        ])

        print(f"  成功: {success_count}/4")
        print(f"  失败: {4 - success_count}/4")

        if success_count == 4:
            print("\n✅ 所有测试通过！小娜Agent专利检索功能正常工作（包括Google Patents在线检索）")
            return True
        else:
            print(f"\n⚠️  部分测试失败（{4 - success_count}/4），请检查日志")
            return False

    except Exception as e:
        logger.exception(f"❌ 测试异常: {e}")
        print(f"\n❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    print("小娜Agent专利检索功能测试")
    print("测试小娜Agent能否正确调用专利检索工具")
    print()

    result = asyncio.run(test_patent_search())

    if result:
        print("\n✅ 测试完成")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        sys.exit(1)
