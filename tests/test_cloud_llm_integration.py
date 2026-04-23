#!/usr/bin/env python3
"""
云端LLM集成测试脚本
测试DeepSeek、通义千问、智谱GLM等云端API是否正常工作
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path("/Users/xujian/Athena工作平台")
sys.path.insert(0, str(project_root))

from core.ai.llm.adapters.cloud_adapter import CloudLLMAdapter


async def test_provider(provider: str, model: str) -> bool:
    """测试单个服务商"""
    print(f"\n{'='*60}")
    print(f"🧪 测试 {provider.upper()} - {model} 模型")
    print(f"{'='*60}")

    try:
        # 创建适配器
        adapter = CloudLLMAdapter(provider=provider, model=model)

        # 初始化
        print("⏳ 正在初始化...")
        if not await adapter.initialize():
            print(f"❌ {provider} 初始化失败")
            return False

        # 测试简单生成
        print("⏳ 测试简单生成...")
        test_prompt = "请用一句话介绍专利法"
        result = await adapter.generate(
            prompt=test_prompt,
            temperature=0.7,
            max_tokens=100
        )

        # 显示结果预览
        preview = result[:150] + "..." if len(result) > 150 else result
        print("✅ 生成成功")
        print(f"📝 结果: {preview}")

        # 关闭连接
        await adapter.close()

        print(f"✅ {provider.upper()} 测试通过")
        return True

    except Exception as e:
        print(f"❌ {provider.upper()} 测试失败: {e}")
        return False


async def test_cost_optimization():
    """测试成本优化策略"""
    print(f"\n{'='*60}")
    print("💰 成本优化策略测试")
    print(f"{'='*60}")

    providers = [
        ("zhipu", "flash", "¥0.5/百万tokens - 最便宜"),
        ("deepseek", "chat", "¥1/百万tokens - 推荐"),
        ("qwen", "turbo", "¥0.8/百万tokens - 中文优化"),
    ]

    results = {}

    for provider, model, description in providers:
        print(f"\n⏳ 测试 {provider} ({description})...")
        try:
            adapter = CloudLLMAdapter(provider=provider, model=model)
            await adapter.initialize()
            # 生成测试（结果不需要使用，只是验证功能）
            await adapter.generate("简单测试", max_tokens=50)
            await adapter.close()
            results[provider] = True
            print(f"✅ {provider} 可用")
        except Exception as e:
            results[provider] = False
            print(f"❌ {provider} 不可用: {e}")

    # 推荐
    print(f"\n{'='*60}")
    print("📊 测试结果汇总")
    print(f"{'='*60}")

    for provider, available in results.items():
        status = "✅ 可用" if available else "❌ 不可用"
        print(f"{provider:15} {status}")

    # 推荐
    available_providers = [p for p, available in results.items() if available]
    if available_providers:
        print(f"\n💡 推荐使用: {available_providers[0]}（成本最低且可用）")
    else:
        print("\n⚠️ 没有可用的云端服务商，请检查API密钥配置")


async def main():
    """主测试流程"""
    print("🌸 Athena平台 - 云端LLM集成测试")
    print(f"{'='*60}")

    # 检查环境变量
    print("\n📋 检查环境变量配置:")
    env_vars = {
        "DEEPSEEK_API_KEY": "DeepSeek",
        "DASHSCOPE_API_KEY": "通义千问",
        "ZHIPU_API_KEY": "智谱GLM",
        "ANTHROPIC_API_KEY": "Claude"
    }

    configured = []
    for var, name in env_vars.items():
        if os.getenv(var):
            print(f"  ✅ {name:15} 已配置")
            configured.append(name)
        else:
            print(f"  ❌ {name:15} 未配置")

    if not configured:
        print("\n⚠️ 没有检测到任何API密钥配置")
        print("\n💡 配置方法:")
        print("  export DEEPSEEK_API_KEY='sk-xxx'")
        print("  export DASHSCOPE_API_KEY='sk-xxx'")
        print("  export ZHIPU_API_KEY='xxx'")
        print("\n或添加到 ~/.zshrc:")
        print("  echo 'export DEEPSEEK_API_KEY=\"sk-xxx\"' >> ~/.zshrc")
        return

    print(f"\n已配置服务: {', '.join(configured)}")

    # 测试成本优化策略
    await test_cost_optimization()

    # 逐个测试服务商
    print(f"\n{'='*60}")
    print("🔍 详细测试")
    print(f"{'='*60}")

    test_cases = [
        ("deepseek", "chat", "DeepSeek"),
        ("qwen", "turbo", "通义千问"),
        ("zhipu", "flash", "智谱GLM"),
    ]

    results = []
    for provider, model, name in test_cases:
        if os.getenv(provider.upper() + "_API_KEY") or \
           (provider == "qwen" and os.getenv("DASHSCOPE_API_KEY")):
            success = await test_provider(provider, model)
            results.append((name, success))
        else:
            print(f"\n⏭️ 跳过 {name}（未配置API密钥）")

    # 最终报告
    print(f"\n{'='*60}")
    print("📊 最终测试报告")
    print(f"{'='*60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name:15} {status}")

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！云端LLM已准备就绪。")
    elif passed > 0:
        print("\n⚠️ 部分测试通过，可使用已成功的服务商。")
    else:
        print("\n❌ 所有测试失败，请检查:")
        print("  1. API密钥是否正确")
        print("  2. 网络连接是否正常")
        print("  3. API服务是否可用")

    print(f"\n{'='*60}")
    print("🌸 测试完成")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
