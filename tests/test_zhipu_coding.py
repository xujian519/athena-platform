#!/usr/bin/env python3
"""
智谱GLM编程端点测试脚本
测试 https://open.bigmodel.cn/api/coding/paas/v4
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path("/Users/xujian/Athena工作平台")
sys.path.insert(0, str(project_root))

from core.llm.adapters.cloud_adapter import CloudLLMAdapter


async def test_zhipu_coding():
    """测试智谱GLM编程端点"""

    print("🧪 测试智谱GLM编程端点")
    print("="*60)
    print("端点: https://open.bigmodel.cn/api/coding/paas/v4")
    print("="*60)

    # 检查API密钥
    import os
    if not os.getenv("ZHIPU_API_KEY"):
        print("\n⚠️ 请先设置环境变量:")
        print("   export ZHIPU_API_KEY='your-api-key'")
        return

    try:
        # 创建编程端点适配器
        print("\n1️⃣ 创建编程端点适配器...")
        adapter = CloudLLMAdapter(
            provider="zhipu",
            model="coding",
            endpoint_type="coding"  # 使用编程端点
        )

        # 初始化
        print("2️⃣ 初始化连接...")
        success = await adapter.initialize()

        if not success:
            print("❌ 初始化失败")
            return

        print("✅ 连接成功")

        # 测试代码生成
        print("\n3️⃣ 测试代码生成...")
        print("提示词: 编写一个Python函数计算斐波那契数列\n")

        code_prompt = """
        请编写一个Python函数来计算斐波那契数列的第n项。
        要求：
        1. 使用递归实现
        2. 添加类型注解
        3. 包含文档字符串
        4. 添加示例代码
        """

        result = await adapter.generate(
            prompt=code_prompt,
            temperature=0.3,  # 代码生成使用较低温度
            max_tokens=2000
        )

        print("✅ 代码生成成功")
        print("\n📝 生成的代码:")
        print("-"*60)
        print(result)
        print("-"*60)

        # 测试代码分析
        print("\n4️⃣ 测试代码分析...")
        print("提示词: 分析以下Python代码的时间复杂度\n")

        analysis_prompt = """
        请分析以下Python代码的时间复杂度和空间复杂度：

        def find_duplicates(arr):
            seen = set()
            duplicates = []
            for item in arr:
                if item in seen:
                    duplicates.append(item)
                else:
                    seen.add(item)
            return duplicates
        """

        analysis = await adapter.generate(
            prompt=analysis_prompt,
            temperature=0.5,
            max_tokens=1000
        )

        print("✅ 分析完成")
        print("\n📝 分析结果:")
        print("-"*60)
        print(analysis)
        print("-"*60)

        # 关闭连接
        await adapter.close()

        print("\n" + "="*60)
        print("🎉 所有测试通过！智谱GLM编程端点工作正常")
        print("="*60)

        # 成本估算
        print("\n💰 成本估算:")
        print("  模型: GLM-4-Flash (编程端点)")
        print("  价格: ¥0.5/百万tokens")
        print("  预估本次成本: ¥0.003-0.005")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def compare_chat_vs_coding():
    """对比聊天端点和编程端点"""

    print("\n" + "="*60)
    print("📊 对比: 聊天端点 vs 编程端点")
    print("="*60)

    import os
    if not os.getenv("ZHIPU_API_KEY"):
        print("\n⚠️ 请先设置环境变量:")
        print("   export ZHIPU_API_KEY='your-api-key'")
        return

    code_task = "编写一个快速排序算法"

    # 测试聊天端点
    print(f"\n1️⃣ 聊天端点 (https://open.bigmodel.cn/api/paas/v4)")
    print(f"任务: {code_task}\n")

    try:
        chat_adapter = CloudLLMAdapter(
            provider="zhipu",
            model="flash",
            endpoint_type="chat"
        )
        await chat_adapter.initialize()
        chat_result = await chat_adapter.generate(
            prompt=code_task,
            max_tokens=1000
        )
        await chat_adapter.close()

        print("聊天端点结果:")
        print("-"*40)
        print(chat_result[:300] + "...")
        print("-"*40)

    except Exception as e:
        print(f"❌ 聊天端点失败: {e}")
        chat_result = ""

    # 测试编程端点
    print(f"\n2️⃣ 编程端点 (https://open.bigmodel.cn/api/coding/paas/v4)")
    print(f"任务: {code_task}\n")

    try:
        coding_adapter = CloudLLMAdapter(
            provider="zhipu",
            model="coding",
            endpoint_type="coding"
        )
        await coding_adapter.initialize()
        coding_result = await coding_adapter.generate(
            prompt=code_task,
            max_tokens=1000
        )
        await coding_adapter.close()

        print("编程端点结果:")
        print("-"*40)
        print(coding_result[:300] + "...")
        print("-"*40)

    except Exception as e:
        print(f"❌ 编程端点失败: {e}")
        coding_result = ""

    print("\n" + "="*60)
    print("💡 建议:")
    print("  - 通用对话 → 使用聊天端点 (endpoint_type='chat')")
    print("  - 代码生成 → 使用编程端点 (endpoint_type='coding')")
    print("  - 代码分析 → 使用编程端点 (endpoint_type='coding')")
    print("="*60)


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="智谱GLM编程端点测试")
    parser.add_argument(
        "--compare",
        action="store_true",
        help="对比聊天端点和编程端点"
    )

    args = parser.parse_args()

    if args.compare:
        # 对比测试
        await test_zhipu_coding()
        await compare_chat_vs_coding()
    else:
        # 仅测试编程端点
        await test_zhipu_coding()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
