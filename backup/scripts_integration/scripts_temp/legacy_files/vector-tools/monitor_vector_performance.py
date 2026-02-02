#!/usr/bin/env python3
"""
向量数据库性能监控脚本
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import psutil

logger = logging.getLogger(__name__)

sys.path.insert(0, os.getcwd())

from qdrant_client import QdrantClient
from qdrant_client.models import Filter


class VectorPerformanceMonitor:
    """向量数据库性能监控器"""

    def __init__(self, host='localhost', port=6333):
        self.client = QdrantClient(host=host, port=port)
        self.performance_log = []
        self.log_file = Path('vector_performance_log.json')

    def monitor_search_performance(self, collection_name: str,
                                 test_queries: List[str],
                                 dimensions: int = 384,
                                 top_k: int = 10) -> Dict[str, Any]:
        """监控搜索性能"""
        logger.info(f"\n🔍 监控集合: {collection_name}")
        logger.info(str('-' * 50))

        # 生成测试向量
        test_vectors = []
        for query in test_queries:
            # 使用随机向量作为测试（实际应用中应使用真实embedding）
            np.random.seed(hash(query) & 0xFFFFFFFF)
            test_vectors.append(random((dimensions)).tolist())

        # 性能指标
        latencies = []
        throughputs = []
        memory_usage = []

        for i, (query, vector) in enumerate(zip(test_queries, test_vectors)):
            logger.info(f"\n测试查询 {i+1}: {query[:30]}...")

            # 记录内存使用
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            # 记录开始时间
            start_time = time.time()

            # 执行搜索
            try:
                results = self.client.search(
                    collection_name=collection_name,
                    query_vector=vector,
                    limit=top_k,
                    with_payload=True,
                    with_vectors=False  # 不返回向量以减少网络传输
                )

                # 记录结束时间
                end_time = time.time()
                latency = (end_time - start_time) * 1000  # ms
                latencies.append(latency)

                # 计算吞吐量（QPS）
                throughput = 1000 / latency if latency > 0 else 0
                throughputs.append(throughput)

                # 记录内存使用
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_usage.append(memory_after - memory_before)

                logger.info(f"  延迟: {latency:.2f} ms")
                logger.info(f"  QPS: {throughput:.2f}")
                logger.info(f"  内存变化: {memory_after - memory_before:.2f} MB")
                logger.info(f"  返回结果数: {len(results)}")

                # 记录最高相似度分数
                if results:
                    logger.info(f"  最高相似度: {results[0].score:.4f}")

            except Exception as e:
                logger.info(f"  ❌ 搜索失败: {e}")
                latencies.append(0)
                throughputs.append(0)
                memory_usage.append(0)

        # 计算统计信息
        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        p99_latency = np.percentile(latencies, 99)
        max_latency = np.max(latencies)

        avg_throughput = np.mean(throughputs)
        avg_memory = np.mean(memory_usage)

        performance_metrics = {
            'collection': collection_name,
            'timestamp': datetime.now().isoformat(),
            'queries': test_queries,
            'latency': {
                'avg_ms': float(avg_latency),
                'p95_ms': float(p95_latency),
                'p99_ms': float(p99_latency),
                'max_ms': float(max_latency)
            },
            'throughput': {
                'avg_qps': float(avg_throughput)
            },
            'memory': {
                'avg_delta_mb': float(avg_memory)
            },
            'dimensions': dimensions,
            'top_k': top_k
        }

        # 打印总结
        logger.info(f"\n📊 性能总结:")
        logger.info(f"  平均延迟: {avg_latency:.2f} ms")
        logger.info(f"  P95延迟: {p95_latency:.2f} ms")
        logger.info(f"  P99延迟: {p99_latency:.2f} ms")
        logger.info(f"  平均QPS: {avg_throughput:.2f}")
        logger.info(f"  平均内存变化: {avg_memory:.2f} MB")

        return performance_metrics

    def check_collection_health(self, collection_name: str) -> Dict[str, Any]:
        """检查集合健康状态"""
        logger.info(f"\n💾 检查集合健康状态: {collection_name}")
        logger.info(str('-' * 50))

        try:
            # 获取集合信息
            info = self.client.get_collection(collection_name)

            # 统计向量数量
            count = self.client.count(collection_name)

            health_info = {
                'collection': collection_name,
                'timestamp': datetime.now().isoformat(),
                'status': info.status,
                'optimizer_status': info.optimizer_status,
                'vectors_count': count.count,
                'config': {
                    'distance': str(info.config.params.vectors.distance),
                    'vector_size': info.config.params.vectors.size,
                    'on_disk': info.config.params.vectors.on_disk
                }
            }

            logger.info(f"  状态: {info.status}")
            logger.info(f"  优化器状态: {info.optimizer_status}")
            logger.info(f"  向量数量: {count.count:,}")
            logger.info(f"  向量维度: {info.config.params.vectors.size}")
            logger.info(f"  距离度量: {info.config.params.vectors.distance}")
            logger.info(f"  磁盘存储: {info.config.params.vectors.on_disk}")

            return health_info

        except Exception as e:
            logger.info(f"  ❌ 检查失败: {e}")
            return {
                'collection': collection_name,
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }

    def save_metrics(self, metrics: Dict[str, Any]):
        """保存性能指标"""
        self.performance_log.append(metrics)

        # 保存到文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n')

        logger.info(f"\n✅ 性能指标已保存到: {self.log_file}")

    def generate_performance_report(self):
        """生成性能报告"""
        logger.info(str("\n" + '=' * 60))
        logger.info('📈 Athena向量数据库性能报告')
        logger.info(str('=' * 60))
        logger.info(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 检查所有集合
        collections = self.client.get_collections()

        logger.info(f"\n📚 集合概览:")
        logger.info(f"  总集合数: {len(collections.collections)}")

        total_vectors = 0
        active_collections = []

        for col in collections.collections:
            try:
                count = self.client.count(col.name)
                vectors_count = count.count
                total_vectors += vectors_count

                if vectors_count > 0:
                    active_collections.append(col.name)

                logger.info(f"  • {col.name}: {vectors_count:,} 个向量")
            except:
                logger.info(f"  • {col.name}: 无法获取数量")

        logger.info(f"\n  总向量数: {total_vectors:,}")
        logger.info(f"  活跃集合数: {len(active_collections)}")

        # 性能测试
        test_queries = [
            '深度学习算法优化',
            '专利审查标准',
            '法律条款解释',
            '技术创新点',
            '系统性能优化'
        ]

        for collection in ['ai_technical_terms_vector_db', 'patent_rules_unified_1024',
                          'general_memory_db', 'legal_vector_db']:
            if collection in active_collections:
                # 确定维度
                dimensions = 384
                if '1024' in collection:
                    dimensions = 1024
                elif '768' in collection or 'legal' in collection:
                    dimensions = 768

                # 监控性能
                metrics = self.monitor_search_performance(
                    collection, test_queries[:3], dimensions
                )
                self.save_metrics(metrics)

                # 检查健康状态
                health = self.check_collection_health(collection)

        # 系统资源使用
        logger.info("\n💻 系统资源使用:")
        logger.info(f"  CPU使用率: {psutil.cpu_percent(interval=1):.1f}%")
        memory = psutil.virtual_memory()
        logger.info(f"  内存使用: {memory.percent:.1f}% ({memory.used/1024/1024/1024:.1f} GB / {memory.total/1024/1024/1024:.1f} GB)")

        disk = psutil.disk_usage('/')
        logger.info(f"  磁盘使用: {disk.percent:.1f}% ({disk.used/1024/1024/1024:.1f} GB / {disk.total/1024/1024/1024:.1f} GB)")

        logger.info(str("\n" + '=' * 60))
        logger.info('✅ 性能监控完成！')

        # 优化建议
        logger.info("\n💡 优化建议:")
        if total_vectors < 10000:
            logger.info('  • 向量数量较少，当前性能表现良好')
            logger.info('  • 建议定期备份数据')
        elif total_vectors < 100000:
            logger.info('  • 向量数量适中，建议监控查询延迟')
            logger.info('  • 考虑实施向量索引优化')
        else:
            logger.info('  • 向量数量较大，建议:')
            logger.info('    - 实施分片存储')
            logger.info('    - 优化索引配置')
            logger.info('    - 考虑增加内存资源')

def main():
    """主函数"""
    logger.info('🚀 Athena向量数据库性能监控')
    logger.info(str('=' * 60))

    # 创建监控器
    monitor = VectorPerformanceMonitor()

    # 生成性能报告
    monitor.generate_performance_report()

    # 持续监控选项
    logger.info("\n🔄 是否启动持续监控？")
    logger.info('  输入间隔时间(秒)启动监控，或按Enter退出')

    user_input = input("\n监控间隔(秒): ").strip()

    if user_input.isdigit():
        interval = int(user_input)
        logger.info(f"\n启动持续监控，间隔: {interval}秒")
        logger.info('按Ctrl+C停止监控')

        try:
            while True:
                time.sleep(interval)
                logger.info(f"\n--- {datetime.now().strftime('%H:%M:%S')} ---")

                # 简单的性能检查
                collections = monitor.client.get_collections()
                total_vectors = 0

                for col in collections.collections:
                    try:
                        count = monitor.client.count(col.name)
                        total_vectors += count.count
                    except:
                        pass

                logger.info(f"集合数: {len(collections.collections)}, 总向量: {total_vectors:,}")

        except KeyboardInterrupt:
            logger.info("\n\n监控已停止")
    else:
        logger.info("\n监控完成")

if __name__ == '__main__':
    main()