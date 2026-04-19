#!/usr/bin/env python3
"""
本地搜索引擎快速测试脚本

验证web_search工具是否能正常使用本地搜索引擎
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from core.tools.real_tool_implementations import real_web_search_handler


async def test_search():
    """测试搜索功能"""
    print("=" * 60)
    print("🔍 本地搜索引擎集成测试")
    print("=" * 60)

    # 测试1: 基本搜索
    print("\n📋 测试1: 基本搜索")
    print("-" * 60)

    params = {
        "query": "Python异步编程",
        "limit": 5
    }

    try:
        result = await real_web_search_handler(params)

        print(f"✅ 搜索成功")
        print(f"   引擎: {result['engine']}")
        print(f"   类型: {result['engine_type']}")
        print(f"   结果数: {result['total']}")
        print(f"   时间戳: {result['timestamp']}")

        if result['total'] > 0:
            print(f"\n   前3个结果:")
            for i, item in enumerate(result['results'][:3], 1):
                print(f"   {i}. {item.get('title', 'N/A')}")
                print(f"      URL: {item.get('url', 'N/A')}")
                print(f"      摘要: {item.get('snippet', 'N/A')[:80]}...")
        else:
            print("   ⚠️ 未找到结果")

    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return False

    # 测试2: 空查询
    print("\n\n📋 测试2: 空查询（应该抛出异常）")
    print("-" * 60)

    try:
        result = await real_web_search_handler({"query": ""})
        print("❌ 应该抛出异常但没有")
        return False
    except ValueError as e:
        print(f"✅ 正确抛出异常: {e}")

    # 测试3: 缺少参数
    print("\n\n📋 测试3: 缺少参数（应该抛出异常）")
    print("-" * 60)

    try:
        result = await real_web_search_handler({"limit": 5})
        print("❌ 应该抛出异常但没有")
        return False
    except ValueError as e:
        print(f"✅ 正确抛出异常: {e}")

    print("\n" + "=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_search())
    sys.exit(0 if success else 1)
