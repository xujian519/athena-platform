#!/usr/bin/env python3
"""
测试工具选择缓存功能
Test Tool Selection Cache

验证工具选择多级缓存的正确性和性能提升

作者: Athena平台团队
创建时间: 2026-03-17
"""

import sys
import time

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from config.feature_flags import is_feature_enabled
from production.core.nlp.xiaonuo_intelligent_tool_selector import (
    ToolSelectionConfig,
    XiaonuoIntelligentToolSelector,
)


def test_tool_selector_cache():
    """测试工具选择缓存"""
    print("=" * 60)
    print("🧪 工具选择缓存功能测试")
    print("=" * 60)

    # 检查特性开关
    if not is_feature_enabled("enable_tool_cache"):
        print("⚠️  工具选择缓存未启用，跳过测试")
        return

    # 创建选择器
    print("\n1️⃣ 初始化工具选择器...")
    config = ToolSelectionConfig()
    selector = XiaonuoIntelligentToolSelector(config)

    # 尝试加载已训练的模型
    try:
        print("   加载预训练模型...")
        selector.load_models()
        print("   ✅ 模型加载成功")
    except Exception as e:
        print(f"   ⚠️  未找到预训练模型，需要先训练: {e}")
        print("   开始训练模型（这可能需要几分钟）...")
        selector.train_tool_selection_model()
        print("   ✅ 模型训练完成")

    # 测试用例
    test_cases = [
        # 技术类意图
        ("优化代码性能", "TECHNICAL", {"language": "python"}),
        ("数据库查询优化", "TECHNICAL", {"domain": "database"}),
        ("API接口测试", "TECHNICAL", {"type": "api"}),

        # 查询类意图
        ("查询专利信息", "QUERY", {"domain": "patent"}),
        ("知识图谱查询", "QUERY", {"domain": "knowledge"}),
        ("搜索技术文档", "QUERY", {"domain": "documentation"}),

        # 协调类意图
        ("项目任务管理", "COORDINATION", {"type": "project"}),
        ("团队协作安排", "COORDINATION", {"type": "team"}),

        # 指令类意图
        ("启动监控服务", "COMMAND", {"service": "monitoring"}),
        ("清理系统日志", "COMMAND", {"action": "cleanup"}),
    ]

    print(f"\n2️⃣ 执行 {len(test_cases)} 个测试用例...")
    print("-" * 60)

    # 第一轮执行（冷启动，无缓存）
    print("\n📊 第一轮执行（冷启动，无缓存）:")
    start_time = time.time()
    for i, (text, intent, context) in enumerate(test_cases[:5], 1):
        tools = selector.select_tools(text, intent, context)
        elapsed = (time.time() - start_time) * 1000
        tool_names = [t[0] for t in tools[:3]]
        print(f"  [{i}] {text:20s} -> {tool_names} (耗时: {elapsed:.2f}ms)")
        start_time = time.time()

    # 第二轮执行（应该命中缓存）
    print("\n📊 第二轮执行（应该命中缓存）:")
    start_time = time.time()
    for i, (text, intent, context) in enumerate(test_cases[:5], 1):
        tools = selector.select_tools(text, intent, context)
        elapsed = (time.time() - start_time) * 1000
        tool_names = [t[0] for t in tools[:3]]
        cache_status = "缓存命中" if elapsed < 5 else "未命中"
        print(f"  [{i}] {text:20s} -> {tool_names} (耗时: {elapsed:.2f}ms) [{cache_status}]")
        start_time = time.time()

    # 获取缓存统计
    print("\n3️⃣ 缓存统计信息:")
    print("-" * 60)
    stats = selector.get_cache_stats()
    print(f"  总请求数: {stats['total_requests']}")
    print(f"  缓存命中数: {stats['cache_hits']}")
    print(f"  缓存未命中数: {stats['cache_misses']}")
    print(f"  缓存命中率: {stats['cache_hit_rate']:.2%}")

    if 'multi_level_cache_stats' in stats:
        print("\n  多级缓存详情:")
        mlcs = stats['multi_level_cache_stats']
        print(f"    - 命中率: {mlcs.get('hit_rate', 0):.2%}")
        print(f"    - 总查询次数: {mlcs.get('total_gets', 0)}")
        print(f"    - 总设置次数: {mlcs.get('total_sets', 0)}")
        if 'hits_by_level' in mlcs:
            print("    - 分级命中:")
            for level, count in mlcs['hits_by_level'].items():
                print(f"      * {level}: {count}")

    # 测试缓存预热
    print("\n4️⃣ 测试缓存预热:")
    print("-" * 60)
    print("  执行缓存预热...")
    selector.warmup_cache()
    print("  ✅ 缓存预热完成")

    # 再次执行查询，验证预热效果
    print("\n  验证预热效果:")
    start_time = time.time()
    for text, intent, context in test_cases[:3]:
        tools = selector.select_tools(text, intent, context)
    elapsed = (time.time() - start_time) * 1000
    print(f"    查询3个预热模式耗时: {elapsed:.2f}ms")

    # 性能对比
    print("\n5️⃣ 性能对比测试:")
    print("-" * 60)

    # 清空缓存
    if selector.cache:
        print("  清空缓存...")
        try:
            selector.cache.clear()
        except Exception as e:
            print(f"  ⚠️  清空缓存失败: {e}")

    # 无缓存性能测试
    print("  测试无缓存性能...")
    times_no_cache = []
    for text, intent, context in test_cases:
        start = time.time()
        selector.select_tools(text, intent, context)
        times_no_cache.append((time.time() - start) * 1000)

    avg_no_cache = sum(times_no_cache) / len(times_no_cache)
    print(f"    平均延迟（无缓存）: {avg_no_cache:.2f}ms")

    # 有缓存性能测试
    print("  测试有缓存性能...")
    times_with_cache = []
    for text, intent, context in test_cases:
        start = time.time()
        selector.select_tools(text, intent, context)
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
    test_tool_selector_cache()
