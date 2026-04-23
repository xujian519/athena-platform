#!/usr/bin/env python3
from __future__ import annotations
"""
提示词优化系统测试脚本
Test Script for Prompt Optimization System

验证：
1. 渐进式加载器功能
2. Token消耗对比
3. 缓存效率
4. 质量评估

作者: 小诺·双鱼公主
"""

import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.prompts.progressive_loader import (
    ComplexityLevel,
    ProgressivePromptLoader,
    PromptContext,
    TaskType,
)
from core.prompts.quality_evaluator import (
    PromptQualityEvaluator,
)


def test_progressive_loading():
    """测试渐进式加载"""
    print("=" * 70)
    print("测试1: 渐进式加载")
    print("=" * 70)

    loader = ProgressivePromptLoader(
        prompts_dir="/Users/xujian/Athena工作平台/prompts",
        compression_ratio=0.4,
    )

    # 测试最小上下文
    print("\n📊 最小上下文:")
    minimal = loader.get_minimal_context()
    print(f"   长度: {len(minimal):,} chars")
    print(f"   估算tokens: ~{len(minimal)//4:,}")

    # 测试不同任务类型
    test_cases = [
        ("general", "simple", "通用简单任务"),
        ("patent_writing", "medium", "专利撰写"),
        ("office_action", "complex", "OA答复"),
        ("prior_art_search", "simple", "现有技术检索"),
    ]

    print("\n📊 各任务类型提示词大小:")
    results = []

    for task_type, complexity, desc in test_cases:
        context = PromptContext(
            task_type=TaskType(task_type),
            complexity=ComplexityLevel(complexity),
        )

        start = time.time()
        loaded = loader.build_prompt(context)
        elapsed = (time.time() - start) * 1000

        results.append({
            "task": desc,
            "tokens": loaded.total_tokens,
            "time_ms": elapsed,
            "segments": len(loaded.segments),
            "cache_hit": loaded.cache_hit,
        })

        print(f"   {desc}:")
        print(f"      Tokens: {loaded.total_tokens:,}")
        print(f"      片段数: {len(loaded.segments)}")
        print(f"      加载时间: {elapsed:.1f}ms")
        print(f"      缓存命中: {loaded.cache_hit}")

    return results


def test_token_savings():
    """测试Token节省"""
    print("\n" + "=" * 70)
    print("测试2: Token节省对比")
    print("=" * 70)

    # 原始提示词大小
    prompts_dir = Path("/Users/xujian/Athena工作平台/prompts")
    original_size = 0
    for md_file in prompts_dir.rglob("*.md"):
        original_size += len(md_file.read_text())

    print(f"\n📊 原始提示词总大小: {original_size:,} chars (~{original_size//4:,} tokens)")

    # 使用渐进式加载器
    loader = ProgressivePromptLoader(
        prompts_dir=str(prompts_dir),
        compression_ratio=0.4,
    )

    # 测试典型场景
    context = PromptContext(
        task_type=TaskType.PATENT_WRITING,
        complexity=ComplexityLevel.MEDIUM,
    )

    loaded = loader.build_prompt(context)
    optimized_size = sum(len(s.content) for s in loaded.segments)

    print(f"📊 优化后提示词大小: {optimized_size:,} chars (~{optimized_size//4:,} tokens)")

    savings = (1 - optimized_size / original_size) * 100
    print(f"📊 节省比例: {savings:.1f}%")

    # 分层统计
    print("\n📊 分层Token消耗:")
    for segment in loaded.segments:
        print(f"   {segment.layer}: ~{segment.token_count:,} tokens")

    return {
        "original_tokens": original_size // 4,
        "optimized_tokens": optimized_size // 4,
        "savings_percent": savings,
    }


def test_cache_efficiency():
    """测试缓存效率"""
    print("\n" + "=" * 70)
    print("测试3: 缓存效率")
    print("=" * 70)

    loader = ProgressivePromptLoader(
        prompts_dir="/Users/xujian/Athena工作平台/prompts",
        compression_ratio=0.4,
    )

    context = PromptContext(
        task_type=TaskType.OFFICE_ACTION,
        complexity=ComplexityLevel.COMPLEX,
    )

    # 第一次加载（缓存未命中）
    print("\n📊 第一次加载:")
    start = time.time()
    loaded1 = loader.build_prompt(context)
    time1 = (time.time() - start) * 1000
    print(f"   时间: {time1:.1f}ms")
    print(f"   缓存命中: {loaded1.cache_hit}")

    # 第二次加载（缓存命中）
    print("\n📊 第二次加载（相同请求）:")
    start = time.time()
    loaded2 = loader.build_prompt(context)
    time2 = (time.time() - start) * 1000
    print(f"   时间: {time2:.1f}ms")
    print(f"   缓存命中: {loaded2.cache_hit}")

    speedup = time1 / time2 if time2 > 0 else 0
    print(f"\n📊 加载速度提升: {speedup:.1f}x")

    # 缓存统计
    stats = loader.get_stats()
    print(f"📊 缓存统计: {stats['cache_stats']}")

    return {
        "first_load_ms": time1,
        "second_load_ms": time2,
        "speedup": speedup,
        "cache_stats": stats["cache_stats"],
    }


def test_quality_evaluation():
    """测试质量评估"""
    print("\n" + "=" * 70)
    print("测试4: 质量评估")
    print("=" * 70)

    evaluator = PromptQualityEvaluator()

    # 评估几个关键文件
    test_files = [
        "prompts/foundation/xiaona_core_v3_compressed.md",
        "prompts/foundation/hitl_protocol_v3_mandatory.md",
        "prompts/capability/cap01_retrieval.md",
    ]

    results = []

    for file_path in test_files:
        full_path = Path("/Users/xujian/Athena工作平台") / file_path
        if full_path.exists():
            content = full_path.read_text()
            report = evaluator.evaluate(content)

            results.append({
                "file": file_path,
                "score": report.overall_score,
                "recommendations": len(report.recommendations),
            })

            print(f"\n📊 {file_path}:")
            print(f"   总分: {report.overall_score:.1%}")
            print(f"   清晰度: {report.clarity.score:.1%}")
            print(f"   完整性: {report.completeness.score:.1%}")
            print(f"   Token效率: {report.token_efficiency.score:.1%}")

            if report.recommendations:
                print("   优化建议:")
                for rec in report.recommendations[:2]:
                    print(f"      - {rec}")

    return results


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("提示词优化系统综合测试")
    print("=" * 70)
    print("\n测试开始时间:", time.strftime("%Y-%m-%d %H:%M:%S"))

    results = {}

    try:
        # 测试1: 渐进式加载
        results["progressive_loading"] = test_progressive_loading()

        # 测试2: Token节省
        results["token_savings"] = test_token_savings()

        # 测试3: 缓存效率
        results["cache_efficiency"] = test_cache_efficiency()

        # 测试4: 质量评估
        results["quality_evaluation"] = test_quality_evaluation()

        # 总结
        print("\n" + "=" * 70)
        print("测试总结")
        print("=" * 70)

        print("\n✅ 所有测试通过!")

        print("\n📊 关键指标:")
        print(f"   Token节省: {results['token_savings']['savings_percent']:.1f}%")
        print(f"   缓存加速: {results['cache_efficiency']['speedup']:.1f}x")
        print(f"   缓存命中率: {results['cache_efficiency']['cache_stats']['hit_rate']}")

        print("\n💡 优化效果:")
        print(f"   原始: ~{results['token_savings']['original_tokens']:,} tokens")
        print(f"   优化后: ~{results['token_savings']['optimized_tokens']:,} tokens")
        print(f"   节省: ~{results['token_savings']['original_tokens'] - results['token_savings']['optimized_tokens']:,} tokens")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
