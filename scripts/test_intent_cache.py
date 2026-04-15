#!/usr/bin/env python3
"""
测试意图识别缓存功能
Test Intent Recognition Cache

验证意图识别缓存的正确性和性能提升

作者: Athena平台团队
创建时间: 2026-03-17
"""

import sys
import time

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from config.feature_flags import is_feature_enabled
from production.core.nlp.xiaonuo_enhanced_intent_classifier import (
    EnhancedIntentConfig,
    XiaonuoEnhancedIntentClassifier,
)


def test_intent_cache():
    """测试意图识别缓存"""
    print("=" * 60)
    print("🧪 意图识别缓存功能测试")
    print("=" * 60)

    # 检查特性开关
    if not is_feature_enabled("enable_intent_cache"):
        print("⚠️  意图识别缓存未启用，跳过测试")
        return

    # 创建分类器
    print("\n1️⃣ 初始化意图分类器...")
    config = EnhancedIntentConfig()
    classifier = XiaonuoEnhancedIntentClassifier(config)

    # 尝试加载已训练的模型
    try:
        print("   加载预训练模型...")
        classifier.load_model()
        print("   ✅ 模型加载成功")
    except Exception as e:
        print(f"   ⚠️  未找到预训练模型，需要先训练: {e}")
        print("   开始训练模型（这可能需要几分钟）...")
        classifier.train_model()
        print("   ✅ 模型训练完成")

    # 测试用例
    test_cases = [
        # 完全相同的查询
        "帮我优化这段代码的性能",
        "帮我优化这段代码的性能",  # 重复查询（应命中精确缓存）

        # 语义相似的查询
        "数据库查询太慢了怎么办",
        "数据库查询速度很慢如何解决",  # 语义相似（应命中语义缓存）

        # 不同意图的查询
        "爸爸，今天工作好累",
        "有时候感到很孤独",
        "谢谢你一直以来的陪伴",

        # 技术类查询
        "如何设计高并发系统",
        "系统架构如何改进",
        "代码重构建议",

        # 查询类
        "什么是区块链技术",
        "最新的AI发展趋势",

        # 指令类
        "启动系统监控服务",
        "清理服务器日志",
    ]

    print(f"\n2️⃣ 执行 {len(test_cases)} 个测试用例...")
    print("-" * 60)

    # 第一次执行（冷启动）
    print("\n📊 第一轮执行（冷启动，无缓存）:")
    start_time = time.time()
    for i, test_text in enumerate(test_cases[:4], 1):  # 只测试前4个
        intent, confidence = classifier.predict_intent(test_text)
        elapsed = (time.time() - start_time) * 1000
        print(f"  [{i}] {test_text[:30]:30s} -> {intent:15s} "
              f"(置信度: {confidence:.3f}, 耗时: {elapsed:.2f}ms)")
        start_time = time.time()

    # 第二次执行（应该命中缓存）
    print("\n📊 第二轮执行（应该命中缓存）:")
    start_time = time.time()
    for i, test_text in enumerate(test_cases[:4], 1):
        intent, confidence = classifier.predict_intent(test_text)
        elapsed = (time.time() - start_time) * 1000
        cache_status = "缓存命中" if elapsed < 10 else "未命中"
        print(f"  [{i}] {test_text[:30]:30s} -> {intent:15s} "
              f"(置信度: {confidence:.3f}, 耗时: {elapsed:.2f}ms) [{cache_status}]")
        start_time = time.time()

    # 获取缓存统计
    print("\n3️⃣ 缓存统计信息:")
    print("-" * 60)
    stats = classifier.get_cache_stats()
    print(f"  总请求数: {stats['total_requests']}")
    print(f"  缓存命中数: {stats['cache_hits']}")
    print(f"  缓存未命中数: {stats['cache_misses']}")
    print(f"  缓存命中率: {stats['cache_hit_rate']:.2%}")
    print(f"  精确命中数: {stats['exact_hits']}")
    print(f"  语义命中数: {stats['semantic_hits']}")

    if 'semantic_cache_stats' in stats:
        print("\n  语义缓存详情:")
        scs = stats['semantic_cache_stats']
        print(f"    - 缓存条目数: {scs['total_entries']}")
        print(f"    - 总命中次数: {scs['total_hits']}")
        print(f"    - 平均命中次数: {scs['avg_hit_count']:.2f}")

    # 性能对比
    print("\n4️⃣ 性能对比测试:")
    print("-" * 60)

    # 无缓存性能测试
    print("  测试无缓存性能...")
    # 清空缓存（如果需要）
    if classifier.semantic_cache:
        classifier.semantic_cache.clear()

    times_no_cache = []
    for test_text in test_cases[:10]:
        start = time.time()
        classifier.predict_intent(test_text)
        times_no_cache.append((time.time() - start) * 1000)

    avg_no_cache = sum(times_no_cache) / len(times_no_cache)
    print(f"    平均延迟（无缓存）: {avg_no_cache:.2f}ms")

    # 有缓存性能测试
    print("  测试有缓存性能...")
    times_with_cache = []
    for test_text in test_cases[:10]:
        start = time.time()
        classifier.predict_intent(test_text)
        times_with_cache.append((time.time() - start) * 1000)

    avg_with_cache = sum(times_with_cache) / len(times_with_cache)
    print(f"    平均延迟（有缓存）: {avg_with_cache:.2f}ms")

    # 计算性能提升
    if avg_no_cache > 0:
        improvement = ((avg_no_cache - avg_with_cache) / avg_no_cache) * 100
        print(f"\n  📈 性能提升: {improvement:.1f}%")
        print(f"  📉 延迟降低: {avg_no_cache - avg_with_cache:.2f}ms")

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_intent_cache()
