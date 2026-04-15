#!/usr/bin/env python3
"""
Redis缓存集成使用示例
Redis Cache Integration Usage Examples

演示如何使用新集成的Redis缓存功能

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

import asyncio
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_1_basic_cache_operations():
    """示例1: 基本缓存操作"""
    print("\n" + "="*60)
    print("📝 示例1: 基本缓存操作")
    print("="*60)

    from redis_cache_service import RedisCacheService

    # 创建缓存服务
    cache = RedisCacheService()

    # SET操作
    print("\n1️⃣ 设置缓存...")
    await cache.set('user:1001', {'name': '张三', 'role': 'admin'}, ttl=3600)
    print("✅ 缓存已设置: user:1001")

    # GET操作
    print("\n2️⃣ 获取缓存...")
    user = await cache.get('user:1001')
    print(f"✅ 缓存命中: {user}")

    # EXISTS操作
    print("\n3️⃣ 检查缓存是否存在...")
    exists = await cache.exists('user:1001')
    print(f"✅ 缓存存在: {exists}")

    # DELETE操作
    print("\n4️⃣ 删除缓存...")
    await cache.delete('user:1001')
    print("✅ 缓存已删除")

    # 验证删除
    exists = await cache.exists('user:1001')
    print(f"✅ 删除后存在: {exists}")

    await cache.close()


async def example_2_smart_cache_strategy():
    """示例2: 智能缓存策略"""
    print("\n" + "="*60)
    print("🧠 示例2: 智能缓存策略")
    print("="*60)

    from redis_cache_service import SmartCacheStrategy

    # 专利数据
    patent_data = {
        'patent_id': 'CN202410001234.5',
        'title': '基于深度学习的智能图像识别系统',
        'abstract': '本发明公开了一种基于深度学习的智能图像识别系统...'
    }

    print("\n1️⃣ 生成不同分析类型的缓存键...")

    # 新颖性分析
    novelity_key = SmartCacheStrategy.generate_cache_key(
        'patent_analysis', patent_data, 'novelty'
    )
    print(f"   新颖性分析键: {novelity_key}")

    # 创造性分析
    inventiveness_key = SmartCacheStrategy.generate_cache_key(
        'patent_analysis', patent_data, 'inventiveness'
    )
    print(f"   创造性分析键: {inventiveness_key}")

    # 综合分析
    comprehensive_key = SmartCacheStrategy.generate_cache_key(
        'patent_analysis', patent_data, 'comprehensive'
    )
    print(f"   综合分析键: {comprehensive_key}")

    print("\n2️⃣ 查看缓存策略配置...")
    strategy = SmartCacheStrategy.get_strategy('patent_analysis')
    print(f"   TTL: {strategy['ttl']}秒")
    print(f"   预热: {strategy['warm_up']}")
    print(f"   预取: {strategy['prefetch']}")


async def example_3_cache_warmup():
    """示例3: 缓存预热"""
    print("\n" + "="*60)
    print("🔥 示例3: 缓存预热")
    print("="*60)

    from cache_warmup_manager import CacheWarmupManager

    # 创建预热管理器
    warmup_manager = CacheWarmupManager()

    # 准备测试专利
    test_patents = [
        {
            'patent_id': 'CN001',
            'title': '基于深度学习的图像识别系统',
            'abstract': '本发明公开了一种基于深度学习的图像识别系统...'
        },
        {
            'patent_id': 'CN002',
            'title': '智能机器人控制方法',
            'abstract': '本发明公开了一种智能机器人控制方法...'
        },
        {
            'patent_id': 'CN003',
            'title': '自然语言处理方法及系统',
            'abstract': '本发明公开了一种自然语言处理方法及系统...'
        }
    ]

    print("\n1️⃣ 预热专利分析缓存...")
    result = await warmup_manager.warmup_patent_analysis_cache(
        patent_list=test_patents,
        analysis_types=['novelty', 'inventiveness']
    )

    print("✅ 预热完成:")
    print(f"   总项目: {result['total_items']}")
    print(f"   成功: {result['success_count']}")
    print(f"   失败: {result['failed_count']}")
    print(f"   耗时: {result['elapsed_time']:.2f}秒")
    print(f"   成功率: {result['warmup_rate']:.1%}")

    print("\n2️⃣ 获取预热统计...")
    stats = warmup_manager.get_warmup_stats()
    print(f"   总计准备: {stats['total_prepared']}")
    print(f"   成功次数: {stats['success_count']}")
    print(f"   失败次数: {stats['failed_count']}")
    print(f"   最后预热: {stats['last_warmup_time']}")


async def example_4_executor_with_cache():
    """示例4: 使用缓存的执行器"""
    print("\n" + "="*60)
    print("🚀 示例4: 使用缓存的执行器")
    print("="*60)

    import time

    from patent_executors_optimized import OptimizedPatentExecutorFactory
    from patent_executors_platform_llm import PatentTask

    # 创建执行器
    factory = OptimizedPatentExecutorFactory()
    executor = factory.get_executor('patent_analysis')

    # 创建测试任务
    test_patent = {
        'patent_id': 'CN202410001234.5',
        'title': '基于深度学习的智能图像识别系统',
        'abstract': '本发明公开了一种基于深度学习的智能图像识别系统，包括图像预处理模块、特征提取模块、分类模块和输出模块。'
    }

    task = PatentTask(
        id='demo_task_001',
        task_type='patent_analysis',
        parameters={
            'patent_data': test_patent,
            'analysis_type': 'novelty'
        }
    )

    print("\n1️⃣ 第一次执行（缓存未命中，调用LLM）...")
    start = time.time()
    result1 = await executor.execute(task)
    time1 = time.time() - start

    print(f"   状态: {result1.status}")
    print(f"   耗时: {time1:.2f}秒")
    print(f"   来自缓存: {result1.metadata.get('cached', False)}")

    print("\n2️⃣ 第二次执行（缓存命中，直接返回）...")
    start = time.time()
    result2 = await executor.execute(task)
    time2 = time.time() - start

    print(f"   状态: {result2.status}")
    print(f"   耗时: {time2:.2f}秒")
    print(f"   来自缓存: {result2.metadata.get('cached', False)}")

    print("\n3️⃣ 缓存效果统计...")
    print(f"   性能提升: {(time1/time2):.1f}x")
    print(f"   时间节省: {((time1-time2)/time1*100):.1f}%")
    print(f"   缓存命中率: {executor._get_cache_hit_rate():.1%}")
    print(f"   命中次数: {executor.cache_stats['hits']}")
    print(f"   未命中次数: {executor.cache_stats['misses']}")


async def example_5_batch_operations():
    """示例5: 批量操作"""
    print("\n" + "="*60)
    print("📦 示例5: 批量操作")
    print("="*60)

    from redis_cache_service import RedisCacheService

    cache = RedisCacheService()

    print("\n1️⃣ 批量设置缓存...")
    batch_data = {
        'patent:001': {'title': '专利1', 'status': 'active'},
        'patent:002': {'title': '专利2', 'status': 'pending'},
        'patent:003': {'title': '专利3', 'status': 'active'},
        'patent:004': {'title': '专利4', 'status': 'granted'},
        'patent:005': {'title': '专利5', 'status': 'active'}
    }

    results = await cache.set_batch(batch_data, ttl=3600)
    success_count = sum(1 for v in results.values() if v)
    print(f"✅ 批量设置完成: {success_count}/{len(batch_data)} 成功")

    print("\n2️⃣ 批量获取缓存...")
    keys = ['patent:001', 'patent:002', 'patent:003', 'patent:999']
    retrieved = await cache.get_batch(keys)
    print(f"✅ 批量获取完成: {len(retrieved)}/{len(keys)} 命中")
    print(f"   命中键: {list(retrieved.keys())}")

    print("\n3️⃣ 模式清除...")
    cleared = await cache.clear_pattern('patent:00*')
    print(f"✅ 清除了 {cleared} 个缓存键")

    await cache.close()


async def example_6_cache_statistics():
    """示例6: 缓存统计"""
    print("\n" + "="*60)
    print("📊 示例6: 缓存统计")
    print("="*60)

    from redis_cache_service import get_cache_service

    cache = get_cache_service()

    # 执行一些操作
    print("\n1️⃣ 执行缓存操作...")
    await cache.set('stat_key_1', 'value1')
    await cache.set('stat_key_2', 'value2')
    await cache.get('stat_key_1')  # 命中
    await cache.get('stat_key_2')  # 命中
    await cache.get('nonexistent')  # 未命中

    print("✅ 操作完成")

    print("\n2️⃣ 获取缓存统计...")
    stats = await cache.get_stats()
    print(f"   总键数: {stats.get('total_keys', 'N/A')}")
    print(f"   命中次数: {stats.get('hits', 'N/A')}")
    print(f"   未命中次数: {stats.get('misses', 'N/A')}")

    if 'hits' in stats and 'misses' in stats:
        total = stats['hits'] + stats['misses']
        hit_rate = stats['hits'] / total if total > 0 else 0
        print(f"   命中率: {hit_rate:.1%}")


async def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("🎯 Redis缓存集成使用示例")
    print("="*70)

    examples = [
        ("基本缓存操作", example_1_basic_cache_operations),
        ("智能缓存策略", example_2_smart_cache_strategy),
        ("缓存预热", example_3_cache_warmup),
        ("使用缓存的执行器", example_4_executor_with_cache),
        ("批量操作", example_5_batch_operations),
        ("缓存统计", example_6_cache_statistics)
    ]

    for i, (name, func) in enumerate(examples, 1):
        try:
            await func()
            print(f"\n✅ 示例{i}完成: {name}")
        except Exception as e:
            print(f"\n❌ 示例{i}失败: {name}")
            print(f"   错误: {e}")

        # 等待一下，让输出更清晰
        await asyncio.sleep(0.5)

    print("\n" + "="*70)
    print("🎉 所有示例运行完成！")
    print("="*70)
    print("\n💡 提示:")
    print("   - 确保Redis服务正在运行: redis-server")
    print("   - 或使用Docker: docker run -d -p 6379:6379 redis:alpine")
    print("   - 安装依赖: pip install aioredis")
    print("   - 查看文档: REDIS_CACHE_INTEGRATION_GUIDE.md")
    print()


if __name__ == '__main__':
    asyncio.run(main())
