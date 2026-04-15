#!/usr/bin/env python3
"""
测试统一缓存接口
Test Unified Cache Interface

验证统一缓存管理器的功能

作者: Athena平台团队
创建时间: 2026-03-17
"""

import sys

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from config.feature_flags import is_feature_enabled
from core.cache.unified_cache_interface import get_unified_cache_manager


def test_unified_cache():
    """测试统一缓存接口"""
    print("=" * 60)
    print("🧪 统一缓存接口功能测试")
    print("=" * 60)

    # 检查特性开关
    if not is_feature_enabled("enable_unified_cache"):
        print("⚠️  统一缓存未启用，跳过测试")
        return

    # 获取缓存管理器
    print("\n1️⃣ 初始化统一缓存管理器...")
    manager = get_unified_cache_manager()
    print("   ✅ 缓存管理器初始化完成")

    # 查看已注册的缓存
    print("\n2️⃣ 已注册的缓存系统:")
    print("-" * 60)
    for cache_name in manager.caches.keys():
        print(f"   - {cache_name}")

    # 测试语义缓存
    print("\n3️⃣ 测试语义缓存:")
    print("-" * 60)

    test_data = {
        "intent": "TECHNICAL",
        "confidence": 0.95,
        "timestamp": "2026-03-17T10:30:00"
    }

    # 设置缓存
    print("   设置缓存...")
    success = manager.set('semantic', 'test_query', test_data, ttl=3600)
    print(f"   {'✅' if success else '❌'} 设置结果: {success}")

    # 获取缓存
    print("   获取缓存...")
    result = manager.get('semantic', 'test_query')
    print(f"   {'✅' if result else '❌'} 获取结果: {result}")

    # 测试语义相似度匹配
    print("   测试语义相似度匹配...")
    similar_query = "测试查询"  # 与"test_query"不同的键
    result = manager.get('semantic', similar_query)
    print(f"   相似查询结果: {'命中' if result else '未命中'}")

    # 测试多级缓存
    print("\n4️⃣ 测试多级缓存:")
    print("-" * 60)

    tool_data = [
        ("code_analyzer", 0.92),
        ("api_tester", 0.85),
        ("performance_profiler", 0.78)
    ]

    # 设置缓存
    print("   设置缓存...")
    success = manager.set('multi_level', 'tool_selection_key', tool_data, ttl=1800)
    print(f"   {'✅' if success else '❌'} 设置结果: {success}")

    # 获取缓存
    print("   获取缓存...")
    result = manager.get('multi_level', 'tool_selection_key')
    print(f"   {'✅' if result else '❌'} 获取结果: {result}")

    # 删除缓存
    print("   删除缓存...")
    success = manager.delete('multi_level', 'tool_selection_key')
    print(f"   {'✅' if success else '❌'} 删除结果: {success}")

    # 验证删除
    result = manager.get('multi_level', 'tool_selection_key')
    print(f"   删除后获取: {'✅ 已删除' if result is None else '❌ 仍然存在'}")

    # 获取统计信息
    print("\n5️⃣ 缓存统计信息:")
    print("-" * 60)

    stats = manager.get_stats()

    print("   管理器统计:")
    print(f"     - 总查询次数: {stats['manager_stats']['total_gets']}")
    print(f"     - 总设置次数: {stats['manager_stats']['total_sets']}")
    print(f"     - 总删除次数: {stats['manager_stats']['total_deletes']}")
    print(f"     - 命中次数: {stats['manager_stats']['hits']}")
    print(f"     - 未命中次数: {stats['manager_stats']['misses']}")
    print(f"     - 命中率: {stats['manager_stats']['hit_rate']:.2%}")

    print("\n   各缓存系统统计:")
    for cache_name, cache_stats in stats['cache_stats'].items():
        print(f"     {cache_name}:")
        for key, value in cache_stats.items():
            print(f"       - {key}: {value}")

    # 测试批量操作
    print("\n6️⃣ 测试批量操作:")
    print("-" * 60)

    # 批量设置
    print("   批量设置缓存...")
    items = [
        ('item1', {'value': 1}),
        ('item2', {'value': 2}),
        ('item3', {'value': 3}),
    ]

    for key, value in items:
        manager.set('multi_level', key, value, ttl=600)

    print(f"   ✅ 已设置 {len(items)} 个缓存项")

    # 批量获取
    print("   批量获取缓存...")
    results = []
    for key, _ in items:
        result = manager.get('multi_level', key)
        results.append(result)

    print(f"   ✅ 获取到 {sum(1 for r in results if r is not None)} 个缓存项")

    # 清空特定缓存
    print("\n7️⃣ 测试清空操作:")
    print("-" * 60)

    print("   清空多级缓存...")
    success = manager.clear('multi_level')
    print(f"   {'✅' if success else '❌'} 清空结果: {success}")

    # 验证清空
    result = manager.get('multi_level', 'item1')
    print(f"   清空后获取: {'✅ 已清空' if result is None else '❌ 仍存在'}")

    # 性能测试
    print("\n8️⃣ 性能测试:")
    print("-" * 60)

    import time

    # 写入性能
    print("   测试写入性能 (100次)...")
    start = time.time()
    for i in range(100):
        manager.set('multi_level', f'perf_test_{i}', {'index': i}, ttl=300)
    write_time = (time.time() - start) * 1000
    print(f"   写入耗时: {write_time:.2f}ms ({write_time/100:.2f}ms/次)")

    # 读取性能
    print("   测试读取性能 (100次)...")
    start = time.time()
    for i in range(100):
        manager.get('multi_level', f'perf_test_{i}')
    read_time = (time.time() - start) * 1000
    print(f"   读取耗时: {read_time:.2f}ms ({read_time/100:.2f}ms/次)")

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_unified_cache()
