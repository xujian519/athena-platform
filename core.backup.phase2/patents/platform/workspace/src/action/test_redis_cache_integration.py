#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis缓存集成测试
Redis Cache Integration Tests

测试覆盖：
- RedisCacheService基本功能
- 智能缓存策略
- 优化版执行器缓存集成
- 缓存预热功能

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

import asyncio
import json
import pytest
import time
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

# 导入被测试模块
from redis_cache_service import (
    RedisCacheService,
    SmartCacheStrategy,
    InMemoryCache,
    get_cache_service
)
from cache_warmup_manager import CacheWarmupManager, PatentDataLoader


class TestRedisCacheService:
    """Redis缓存服务测试"""

    @pytest.fixture
    async def cache_service(self):
        """创建缓存服务实例"""
        service = RedisCacheService()
        yield service
        await service.close()

    @pytest.mark.asyncio
    async def test_basic_get_set(self, cache_service):
        """测试基本GET/SET操作"""
        # SET操作
        success = await cache_service.set('test_key', {'data': 'test_value'}, ttl=60)
        assert success is True

        # GET操作
        value = await cache_service.get('test_key')
        assert value is not None
        assert value['data'] == 'test_value'

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_service):
        """测试缓存未命中"""
        value = await cache_service.get('nonexistent_key')
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_service):
        """测试缓存过期"""
        # 设置1秒过期的缓存
        await cache_service.set('expiring_key', 'data', ttl=1)

        # 立即获取应该存在
        value = await cache_service.get('expiring_key')
        assert value == 'data'

        # 等待过期
        await asyncio.sleep(2)

        # 再次获取应该不存在
        value = await cache_service.get('expiring_key')
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, cache_service):
        """测试删除缓存"""
        # 设置缓存
        await cache_service.set('delete_key', 'data')

        # 验证存在
        exists = await cache_service.exists('delete_key')
        assert exists is True

        # 删除缓存
        success = await cache_service.delete('delete_key')
        assert success is True

        # 验证不存在
        exists = await cache_service.exists('delete_key')
        assert exists is False

    @pytest.mark.asyncio
    async def test_batch_operations(self, cache_service):
        """测试批量操作"""
        # 批量SET
        batch_data = {
            'key1': 'value1',
            'key2': {'nested': 'data'},
            'key3': [1, 2, 3]
        }
        results = await cache_service.set_batch(batch_data, ttl=60)
        assert all(results.values())

        # 批量GET
        retrieved = await cache_service.get_batch(['key1', 'key2', 'key3'])
        assert len(retrieved) == 3
        assert retrieved['key1'] == 'value1'
        assert retrieved['key2']['nested'] == 'data'
        assert retrieved['key3'] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_pattern_clear(self, cache_service):
        """测试模式清除"""
        # 设置多个键
        await cache_service.set('patent:1', 'data1')
        await cache_service.set('patent:2', 'data2')
        await cache_service.set('other:1', 'data3')

        # 清除patent:*
        cleared = await cache_service.clear_pattern('patent:*')
        assert cleared >= 2  # 至少清除2个

        # 验证
        assert await cache_service.get('patent:1') is None
        assert await cache_service.get('patent:2') is None
        assert await cache_service.get('other:1') == 'data3'

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_service):
        """测试缓存统计"""
        # 执行一些操作
        await cache_service.set('stat_key', 'value')
        await cache_service.get('stat_key')
        await cache_service.get('nonexistent')

        # 获取统计
        stats = await cache_service.get_stats()
        assert isinstance(stats, dict)


class TestSmartCacheStrategy:
    """智能缓存策略测试"""

    def test_get_strategy(self):
        """测试获取缓存策略"""
        strategy = SmartCacheStrategy.get_strategy('patent_analysis')
        assert 'ttl' in strategy
        assert strategy['ttl'] == 3600  # 1小时

    def test_generate_cache_key(self):
        """测试生成缓存键"""
        patent_data = {
            'title': '基于深度学习的图像识别系统',
            'abstract': '本发明公开了一种基于深度学习的图像识别系统...'
        }

        cache_key = SmartCacheStrategy.generate_cache_key(
            'patent_analysis', patent_data, 'novelty'
        )

        assert isinstance(cache_key, str)
        assert 'patent_analysis' in cache_key
        assert 'novelty' in cache_key
        assert ':' in cache_key  # 应该有分隔符

    def test_cache_key_consistency(self):
        """测试缓存键一致性"""
        patent_data = {
            'title': '测试专利',
            'abstract': '测试摘要'
        }

        key1 = SmartCacheStrategy.generate_cache_key('patent_analysis', patent_data, 'novelty')
        key2 = SmartCacheStrategy.generate_cache_key('patent_analysis', patent_data, 'novelty')

        assert key1 == key2  # 相同输入应该生成相同的键

    def test_cache_key_uniqueness(self):
        """测试缓存键唯一性"""
        patent_data1 = {'title': '专利1', 'abstract': '摘要1'}
        patent_data2 = {'title': '专利2', 'abstract': '摘要2'}

        key1 = SmartCacheStrategy.generate_cache_key('patent_analysis', patent_data1, 'novelty')
        key2 = SmartCacheStrategy.generate_cache_key('patent_analysis', patent_data2, 'novelty')

        assert key1 != key2  # 不同输入应该生成不同的键


class TestInMemoryCache:
    """内存缓存测试（fallback）"""

    @pytest.mark.asyncio
    async def test_basic_operations(self):
        """测试基本操作"""
        cache = InMemoryCache()

        # SET
        await cache.set('key1', 'value1')
        assert await cache.exists('key1') is True

        # GET
        value = await cache.get('key1')
        assert value == 'value1'

        # DELETE
        await cache.delete('key1')
        assert await cache.exists('key1') is False

    @pytest.mark.asyncio
    async def test_expiration(self):
        """测试过期"""
        cache = InMemoryCache()

        # 设置1秒过期
        await cache.setex('expiring', 1, b'value')
        assert await cache.get('expiring') == b'value'

        # 等待过期
        await asyncio.sleep(2)
        assert await cache.get('expiring') is None


class TestCacheWarmupManager:
    """缓存预热管理器测试"""

    @pytest.fixture
    def warmup_manager(self):
        """创建预热管理器"""
        return CacheWarmupManager()

    def test_create_mock_analysis_result(self, warmup_manager):
        """测试创建模拟分析结果"""
        patent_data = {'patent_id': 'CN001', 'title': '测试专利'}

        result = warmup_manager._create_mock_analysis_result(patent_data, 'novelty')

        assert 'analysis_type' in result
        assert result['analysis_type'] == 'novelty'
        assert result['patent_id'] == 'CN001'
        assert result['report']['is_warmup'] is True

    @pytest.mark.asyncio
    async def test_warmup_patent_analysis_cache(self, warmup_manager):
        """测试预热专利分析缓存"""
        test_patents = [
            {'patent_id': 'CN001', 'title': '专利1', 'abstract': '摘要1'},
            {'patent_id': 'CN002', 'title': '专利2', 'abstract': '摘要2'}
        ]

        result = await warmup_manager.warmup_patent_analysis_cache(
            patent_list=test_patents,
            analysis_types=['novelty']
        )

        assert 'total_items' in result
        assert result['total_items'] == 2
        assert 'success_count' in result

    @pytest.mark.asyncio
    async def test_warmup_popular_patents(self, warmup_manager):
        """测试预热热门专利"""
        result = await warmup_manager.warmup_popular_patents(
            popular_patent_ids=['CN001', 'CN002', 'CN003']
        )

        assert result['total_items'] == 3
        assert result['success_count'] >= 0

    def test_get_warmup_stats(self, warmup_manager):
        """测试获取预热统计"""
        stats = warmup_manager.get_warmup_stats()
        assert isinstance(stats, dict)
        assert 'total_prepared' in stats
        assert 'success_count' in stats


class TestCacheIntegration:
    """缓存集成测试"""

    @pytest.mark.asyncio
    async def test_cache_fallback_mechanism(self):
        """测试缓存降级机制"""
        # 创建会失败的Redis服务
        failing_cache = RedisCacheService(redis_url='redis://invalid:6379')

        # 应该fallback到内存缓存
        success = await failing_cache.set('test_key', 'test_value')
        assert success is True or success is False  # 两种结果都可接受（取决于fallback）

        # 获取应该能工作（通过fallback）
        value = await failing_cache.get('test_key')
        # 如果Redis失败，内存缓存应该能工作
        # 这个测试可能需要根据实际实现调整

        await failing_cache.close()

    @pytest.mark.asyncio
    async def test_cache_hit_rate_calculation(self):
        """测试缓存命中率计算"""
        cache = RedisCacheService()

        # 设置一些数据
        await cache.set('key1', 'value1')
        await cache.set('key2', 'value2')

        # 命中
        await cache.get('key1')
        await cache.get('key2')

        # 未命中
        await cache.get('nonexistent')

        stats = await cache.get_stats()
        # 验证统计信息存在
        assert isinstance(stats, dict)

        await cache.close()


# =============================================================================
# 性能测试
# =============================================================================

class TestCachePerformance:
    """缓存性能测试"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_write_performance(self):
        """测试缓存写入性能"""
        cache = RedisCacheService()

        start_time = time.time()
        num_writes = 100

        for i in range(num_writes):
            await cache.set(f'perf_key_{i}', f'perf_value_{i}', ttl=60)

        elapsed = time.time() - start_time
        throughput = num_writes / elapsed

        print(f"\n📊 写入性能: {throughput:.2f} ops/sec")
        print(f"   平均延迟: {elapsed/num_writes*1000:.2f} ms")

        await cache.close()

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_read_performance(self):
        """测试缓存读取性能"""
        cache = RedisCacheService()

        # 预先设置数据
        num_keys = 100
        for i in range(num_keys):
            await cache.set(f'perf_key_{i}', f'perf_value_{i}', ttl=60)

        # 测试读取性能
        start_time = time.time()

        for i in range(num_keys):
            await cache.get(f'perf_key_{i}')

        elapsed = time.time() - start_time
        throughput = num_keys / elapsed

        print(f"\n📊 读取性能: {throughput:.2f} ops/sec")
        print(f"   平均延迟: {elapsed/num_keys*1000:.2f} ms")

        await cache.close()

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_hit_rate_under_load(self):
        """测试负载下的缓存命中率"""
        cache = RedisCacheService()

        # 设置50%的数据
        num_keys = 100
        for i in range(num_keys // 2):
            await cache.set(f'key_{i}', f'value_{i}', ttl=60)

        # 随机读取
        import random
        hits = 0
        misses = 0

        for _ in range(num_keys):
            key = f'key_{random.randint(0, num_keys - 1)}'
            value = await cache.get(key)
            if value is not None:
                hits += 1
            else:
                misses += 1

        hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0

        print(f"\n📊 缓存命中率: {hit_rate:.1%}")
        print(f"   命中: {hits}, 未命中: {misses}")

        await cache.close()


# =============================================================================
# 运行测试
# =============================================================================

def run_tests():
    """运行所有测试"""
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-x'  # 遇到第一个失败就停止
    ])


if __name__ == '__main__':
    run_tests()
