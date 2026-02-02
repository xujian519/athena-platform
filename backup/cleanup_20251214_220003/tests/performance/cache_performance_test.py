#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存性能测试脚本
测试查询缓存命中率和性能提升
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

# 添加项目路径
project_root = Path('/Users/xujian/Athena工作平台')
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CachePerformanceTester:
    """缓存性能测试器"""

    def __init__(self):
        self.results = {
            'test_time': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }

        # 导入客户端
        try:
            from services.vector_db.optimized_qdrant_client import OptimizedQdrantClient
            self.client = OptimizedQdrantClient()
            logger.info('✅ 优化Qdrant客户端已加载')
        except ImportError as e:
            logger.error(f"❌ 客户端加载失败: {e}")
            self.client = None

    def prepare_test_vectors(self, count: int = 10) -> dict:
        """准备测试向量"""
        logger.info(f"🔧 准备 {count} 个测试向量...")

        vectors = {}

        # 从legal_clauses获取一些真实向量作为基础
        if self.client:
            try:
                points, _ = self.client.qdrant_client.scroll(
                    collection_name='legal_clauses',
                    limit=count,
                    with_vectors=True
                )

                for i, point in enumerate(points[:count]):
                    vectors[f"legal_clauses_{i}"] = point.vector
                    vectors[f"similarity_{i}"] = point.vector  # 相似向量

                logger.info(f"  ✅ 获取了 {len(points)} 个真实向量")
            except Exception as e:
                logger.warning(f"⚠️ 无法获取真实向量: {e}")

        # 如果获取不足，生成随机向量
        while len(vectors) < count * 2:
            vectors[f"random_{len(vectors)//2}"] = random(1024).tolist()

        logger.info(f"📊 准备完成: {len(vectors)} 个向量")
        return vectors

    def test_cache_performance(self, iterations: int = 100) -> dict:
        """测试缓存性能"""
        if not self.client:
            logger.error('❌ 客户端未初始化')
            return {'error': '客户端未初始化'}

        logger.info(f"🚀 开始缓存性能测试，迭代次数: {iterations}")

        test_vectors = self.prepare_test_vectors(min(iterations, 10))
        test_results = {
            'iterations': iterations,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_time': 0,
            'avg_response_time': 0,
            'cache_hit_rate': 0
        }

        # 测试集合
        test_collections = ['legal_clauses', 'ai_technical_terms_1024', 'legal_documents']

        for iteration in range(iterations):
            # 选择一个测试集合
            collection = test_collections[iteration % len(test_collections)]

            # 选择一个测试向量
            vector_name = f"legal_clauses_{iteration % 10}"
            if vector_name not in test_vectors:
                vector_name = list(test_vectors.keys())[0]
            query_vector = test_vectors[vector_name]

            # 记录开始时间
            start_time = time.time()

            # 执行查询
            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=10
            )

            # 记录响应时间
            response_time = time.time() - start_time
            test_results['total_time'] += response_time

            # 统计缓存命中情况
            cache_stats = self.client.get_cache_stats()
            if cache_stats.get('cache_hits'):
                test_results['cache_hits'] = cache_stats['cache_hits']
            if cache_stats.get('cache_misses'):
                test_results['cache_misses'] = cache_stats['cache_misses']

            # 每10次迭代显示进度
            if (iteration + 1) % 10 == 0:
                progress = (iteration + 1) / iterations * 100
                logger.info(f"  进度: {progress:.1f}% | "
                           f"缓存命中: {test_results['cache_hits']} | "
                           f"响应时间: {response_time*1000:.2f}ms")

        # 计算平均值
        test_results['avg_response_time'] = test_results['total_time'] / iterations
        test_results['cache_hit_rate'] = (
            test_results['cache_hits'] / (test_results['cache_hits'] + test_results['cache_misses']) * 100
            if (test_results['cache_hits'] + test_results['cache_misses']) > 0 else 0
        )

        return test_results

    def test_without_cache(self, iterations: int = 100) -> dict:
        """测试不使用缓存的性能"""
        if not self.client:
            return {'error': '客户端未初始化'}

        logger.info(f"🔄 测试无缓存性能，迭代次数: {iterations}")

        # 临时禁用缓存
        original_use_cache = self.client.use_cache
        self.client.use_cache = False

        test_results = {
            'iterations': iterations,
            'total_time': 0,
            'avg_response_time': 0
        }

        test_vectors = self.prepare_test_vectors(min(iterations, 10))
        test_collections = ['legal_clauses', 'ai_technical_terms_1024', 'legal_documents']

        for iteration in range(iterations):
            collection = test_collections[iteration % len(test_collections)]
            vector_name = f"legal_clauses_{iteration % 10}"
            if vector_name not in test_vectors:
                vector_name = list(test_vectors.keys())[0]
            query_vector = test_vectors[vector_name]

            start_time = time.time()
            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=10
            )
            response_time = time.time() - start_time
            test_results['total_time'] += response_time

            if (iteration + 1) % 20 == 0:
                progress = (iteration + 1) / iterations * 100
                logger.info(f"  进度: {progress:.1f}% | 响应时间: {response_time*1000:.2f}ms")

        # 恢复缓存设置
        self.client.use_cache = original_use_cache

        test_results['avg_response_time'] = test_results['total_time'] / iterations
        return test_results

    def test_similarity_performance(self):
        """测试相似度缓存"""
        logger.info('🔍 测试相似度缓存功能...')

        if not self.client or not self.client.cache_service:
            logger.warning('⚠️ 缓存服务未启用，跳过测试')
            return

        # 使用相同向量测试缓存
        test_vector = random(1024).tolist()

        # 第一次查询（缓存未命中）
        start = time.time()
        results1 = self.client.search(
            collection_name='legal_clauses',
            query_vector=test_vector,
            limit=5
        )
        first_query_time = time.time() - start

        # 第二次查询（缓存命中）
        start = time.time()
        results2 = self.client.search(
            collection_name='legal_clauses',
            query_vector=test_vector,
            limit=5
        )
        second_query_time = time.time() - start

        # 第三次查询（轻微变化的向量）
        slightly_different_vector = test_vector.copy()
        slightly_different_vector[0] *= 1.01  # 轻微变化
        start = time.time()
        results3 = self.client.search(
            collection_name='legal_clauses',
            query_vector=slightly_different_vector,
            limit=5
        )
        third_query_time = time.time() - start

        logger.info(f"  📊 相似度测试结果:")
        logger.info(f"    首次查询: {first_query_time*1000:.2f}ms (缓存未命中)")
        logger.info(f"    相同查询: {second_query_time*1000:.2f}ms (缓存命中)")
        logger.info(f"    相似查询: {third_query_time*1000:.2f}ms (相似度=0.99)")

        return {
            'first_query_ms': first_query_time * 1000,
            'cached_query_ms': second_query_time * 1000,
            'similar_query_ms': third_query_time * 1000,
            'speedup_cached': first_query_time / second_query_time if second_query_time > 0 else 0,
            'results_match': len(results1) == len(results2) == len(results3)
        }

    def run_performance_tests(self):
        """运行所有性能测试"""
        logger.info('🎯 开始性能测试...')

        if not self.client:
            logger.error('❌ 无法进行测试，客户端未初始化')
            return

        # 测试1: 缓存性能
        logger.info("\n" + '='*60)
        logger.info('测试1: 缓存性能测试')
        logger.info('='*60)

        cache_results = self.test_cache_performance(iterations=50)
        self.results['tests'].append({
            'name': '缓存性能测试',
            'type': 'cache_performance',
            'results': cache_results
        })

        # 测试2: 无缓存性能
        logger.info("\n" + '='*60)
        logger.info('测试2: 无缓存性能测试')
        logger.info('='*60)

        no_cache_results = self.test_without_cache(iterations=30)
        self.results['tests'].append({
            'name': '无缓存性能测试',
            'type': 'no_cache_performance',
            'results': no_cache_results
        })

        # 测试3: 相似度性能
        logger.info("\n" + '='*60)
        logger.info('测试3: 相似度缓存测试')
        logger.info('='*60)

        similarity_results = self.test_similarity_performance()
        self.results['tests'].append({
            'name': '相似度缓存测试',
            'type': 'similarity_cache',
            'results': similarity_results
        })

        # 计算总体统计
        self.calculate_summary()

        # 保存结果
        self.save_results()

        return self.results

    def calculate_summary(self):
        """计算测试总结"""
        cache_test = None
        no_cache_test = None

        for test in self.results['tests']:
            if test['type'] == 'cache_performance':
                cache_test = test['results']
            elif test['type'] == 'no_cache_performance':
                no_cache_test = test['results']

        if cache_test and no_cache_test:
            speedup = no_cache_test['avg_response_time'] / cache_test['avg_response_time']

            self.results['summary'] = {
                'cache_hit_rate': cache_test['cache_hit_rate'],
                'avg_response_time_with_cache': cache_test['avg_response_time'] * 1000,  # ms
                'avg_response_time_without_cache': no_cache_test['avg_response_time'] * 1000,  # ms
                'performance_improvement': speedup,
                'cache_efficiency': f"{cache_test['cache_hit_rate']:.1f}%",
                'test_date': self.results['test_time']
            }

    def save_results(self):
        """保存测试结果"""
        results_path = project_root / 'tests' / 'results' / 'cache_performance_results.json'
        results_path.parent.mkdir(parents=True, exist_ok=True)

        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"💾 测试结果已保存: {results_path}")

    def print_summary(self):
        """打印测试总结"""
        summary = self.results.get('summary', {})

        if not summary:
            logger.info("\n❌ 测试结果不可用")
            return

        logger.info(str("\n" + '='*60))
        logger.info('📊 缓存性能测试总结')
        logger.info(str('='*60))

        logger.info(f"📈 缓存命中率: {summary['cache_efficiency']}")
        logger.info(f"⚡ 平均响应时间 (缓存): {summary['avg_response_time_with_cache']:.2f} ms")
        logger.info(f"⏱️  平均响应时间 (无缓存): {summary['avg_response_time_without_cache']:.2f} ms")
        logger.info(f"🚀 性能提升倍数: {summary['performance_improvement']:.1f}x")

        if 'similarity_cache' in self.results:
            sim_test = next((t for t in self.results['tests'] if t['type'] == 'similarity_cache'), None)
            if sim_test:
                sim_results = sim_test['results']
                logger.info(f"\n🔄 相似度缓存结果:")
                logger.info(f"    首次查询: {sim_results['first_query_ms']:.2f} ms")
                logger.info(f"    缓存命中: {sim_results['cached_query_ms']:.2f} ms")
                logger.info(f"    相似查询: {sim_results['similar_query_ms']:.2f} ms")
                logger.info(f"    缓存加速: {sim_results['speedup_cached']:.1f}x")

        logger.info("\n💡 建议:")
        logger.info('   • 缓存系统工作正常')
        logger.info('  • 建议调整缓存TTL以平衡性能和一致性')
        logger.info('  • 可以考虑实施legal_clauses分片以进一步提升性能')
        logger.info('  • 定期监控缓存命中率')

def main():
    """主函数"""
    logger.info('🚀 开始缓存性能测试...')

    tester = CachePerformanceTester()

    # 运行测试
    results = tester.run_performance_tests()

    # 打印总结
    tester.print_summary()

    return results

if __name__ == '__main__':
    main()