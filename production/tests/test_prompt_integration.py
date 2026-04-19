#!/usr/bin/env python3
"""
提示词系统生产环境集成测试
测试渐进式加载器与现有系统的集成

作者: 小诺·双鱼公主
"""

from __future__ import annotations
import sys
import time
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入加载器
from production.services.unified_prompt_loader_v3 import (
    LoadMode,
    PromptConfig,
    UnifiedPromptLoader,
    get_minimal_prompt,
    get_prompt,
)


def test_backward_compatibility():
    """测试向后兼容性"""
    print("=" * 70)
    print("测试1: 向后兼容性")
    print("=" * 70)

    # 使用旧版API
    prompt = get_prompt(task_type="patent_writing", complexity="medium")

    print(f"\n✅ get_prompt() 返回: {len(prompt):,} chars")
    print(f"✅ 内容预览: {prompt[:200]}...")

    return True


def test_progressive_loading():
    """测试渐进式加载"""
    print("\n" + "=" * 70)
    print("测试2: 渐进式加载")
    print("=" * 70)

    # 配置渐进式加载
    config = PromptConfig(
        load_mode=LoadMode.PROGRESSIVE,
        compression_ratio=0.4,
        verbose=True,
    )

    loader = UnifiedPromptLoader(
        prompts_dir="/Users/xujian/Athena工作平台/prompts",
        config=config,
    )

    # 测试不同任务类型
    test_cases = [
        ("general", "simple"),
        ("patent_writing", "medium"),
        ("office_action", "complex"),
    ]

    for task, complexity in test_cases:
        loaded = loader.load(task, complexity)
        print(f"\n📊 {task} ({complexity}):")
        print(f"   Tokens: ~{loaded.total_tokens:,}")
        print(f"   字符: {loaded.total_chars:,}")
        print(f"   片段: {len(loaded.segments)}")
        print(f"   时间: {loaded.load_time_ms:.1f}ms")

    return True


def test_minimal_context():
    """测试最小上下文"""
    print("\n" + "=" * 70)
    print("测试3: 最小上下文")
    print("=" * 70)

    minimal = get_minimal_prompt()

    print(f"\n✅ 长度: {len(minimal):,} chars")
    print(f"✅ 估算Tokens: ~{len(minimal)//4:,}")
    print("\n预览:")
    print("-" * 40)
    print(minimal[:500])
    print("...")

    return True


def test_cache_efficiency():
    """测试缓存效率"""
    print("\n" + "=" * 70)
    print("测试4: 缓存效率")
    print("=" * 70)

    config = PromptConfig(
        load_mode=LoadMode.PROGRESSIVE,
        enable_cache=True,
        verbose=True,
    )

    loader = UnifiedPromptLoader(
        prompts_dir="/Users/xujian/Athena工作平台/prompts",
        config=config,
    )

    # 第一次加载
    print("\n第一次加载:")
    start = time.time()
    loaded1 = loader.load("office_action", "complex")
    time1 = (time.time() - start) * 1000
    print(f"   时间: {time1:.1f}ms")
    print(f"   缓存命中: {loaded1.cache_hit}")

    # 第二次加载
    print("\n第二次加载 (相同请求):")
    start = time.time()
    loaded2 = loader.load("office_action", "complex")
    time2 = (time.time() - start) * 1000
    print(f"   时间: {time2:.1f}ms")
    print(f"   缓存命中: {loaded2.cache_hit}")

    # 计算加速
    speedup = time1 / max(time2, 0.01)
    print(f"\n✅ 加速: {speedup:.1f}x")

    # 统计
    stats = loader.get_stats()
    print(f"✅ 缓存统计: {stats['cache_stats']}")

    return True


def test_token_savings():
    """测试Token节省"""
    print("\n" + "=" * 70)
    print("测试5: Token节省对比")
    print("=" * 70)

    prompts_dir = Path("/Users/xujian/Athena工作平台/prompts")

    # 原始大小
    original_size = sum(len(f.read_text()) for f in prompts_dir.rglob("*.md"))
    original_tokens = original_size // 4

    print("\n📊 原始提示词总大小:")
    print(f"   字符: {original_size:,}")
    print(f"   Tokens: ~{original_tokens:,}")

    # 使用渐进式加载
    config = PromptConfig(
        load_mode=LoadMode.PROGRESSIVE,
        compression_ratio=0.4,
    )

    loader = UnifiedPromptLoader(str(prompts_dir), config)

    # 测试典型场景
    scenarios = [
        ("最小上下文", "general", "simple", LoadMode.MINIMAL),
        ("专利撰写", "patent_writing", "medium", LoadMode.PROGRESSIVE),
        ("OA答复", "office_action", "complex", LoadMode.PROGRESSIVE),
    ]

    print("\n📊 各场景Token消耗:")
    for name, task, complexity, mode in scenarios:
        config.load_mode = mode
        loader = UnifiedPromptLoader(str(prompts_dir), config)
        loaded = loader.load(task, complexity)
        savings = (1 - loaded.total_tokens / original_tokens) * 100
        print(f"   {name}: ~{loaded.total_tokens:,} tokens (节省 {savings:.1f}%)")

    return True


def test_load_modes():
    """测试不同加载模式"""
    print("\n" + "=" * 70)
    print("测试6: 加载模式对比")
    print("=" * 70)

    modes = [
        ("MINIMAL", LoadMode.MINIMAL),
        ("PROGRESSIVE", LoadMode.PROGRESSIVE),
        ("FULL", LoadMode.FULL),
    ]

    for name, mode in modes:
        config = PromptConfig(
            load_mode=mode,
            compression_ratio=0.4,
        )

        loader = UnifiedPromptLoader(
            prompts_dir="/Users/xujian/Athena工作平台/prompts",
            config=config,
        )

        loaded = loader.load("patent_writing", "medium")

        print(f"\n📊 {name} 模式:")
        print(f"   Tokens: ~{loaded.total_tokens:,}")
        print(f"   片段数: {len(loaded.segments)}")
        print(f"   时间: {loaded.load_time_ms:.1f}ms")

    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("提示词系统生产环境集成测试")
    print("=" * 70)
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("向后兼容性", test_backward_compatibility),
        ("渐进式加载", test_progressive_loading),
        ("最小上下文", test_minimal_context),
        ("缓存效率", test_cache_efficiency),
        ("Token节省", test_token_savings),
        ("加载模式", test_load_modes),
    ]

    results = {}

    for name, test_func in tests:
        try:
            success = test_func()
            results[name] = "✅ 通过" if success else "❌ 失败"
        except Exception as e:
            results[name] = f"❌ 错误: {e}"
            import traceback
            traceback.print_exc()

    # 汇总
    print("\n" + "=" * 70)
    print("测试汇总")
    print("=" * 70)

    for name, result in results.items():
        print(f"{name}: {result}")

    passed = sum(1 for r in results.values() if r.startswith("✅"))
    total = len(results)

    print(f"\n总计: {passed}/{total} 通过")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
