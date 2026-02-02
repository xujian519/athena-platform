#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建向量索引脚本
Create Vector Indexes Script

为Qdrant中的向量集合创建索引以提升搜索性能
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import asyncio
import logging
import os
import sys
from typing import Any, Dict, List

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.http import models

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VectorIndexManager:
    """向量索引管理器"""
    
    def __init__(self, host: str = 'localhost', port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        self.collections_info = {}
        
    async def check_collections_status(self) -> Dict[str, Any]:
        """检查集合状态"""
        try:
            collections = self.client.get_collections().collections
            logger.info(f"📊 发现 {len(collections)} 个集合")
            
            for collection in collections:
                try:
                    collection_info = self.client.get_collection(collection.name)
                    self.collections_info[collection.name] = {
                        'points_count': collection_info.points_count,
                        'vectors_config': collection_info.config.params.vectors,
                        'has_index': hasattr(collection_info.config.params.vectors, 'hnsw_config'),
                        'status': 'active'
                    }
                    
                    logger.info(f"✅ {collection.name}: {collection_info.points_count} 点")
                    
                except Exception as e:
                    logger.error(f"❌ 获取集合 {collection.name} 信息失败: {e}")
                    self.collections_info[collection.name] = {'status': 'error', 'error': str(e)}
            
            return self.collections_info
            
        except Exception as e:
            logger.error(f"❌ 检查集合状态失败: {e}")
            raise
    
    async def create_indexes_for_all_collections(self) -> Dict[str, Any]:
        """为所有集合创建索引"""
        results = {}
        
        for collection_name, info in self.collections_info.items():
            if info.get('status') != 'active':
                logger.warning(f"⚠️ 跳过非活跃集合: {collection_name}")
                continue
                
            try:
                result = await self.create_index_for_collection(collection_name)
                results[collection_name] = result
                logger.info(f"✅ {collection_name} 索引创建完成")
                
            except Exception as e:
                logger.error(f"❌ {collection_name} 索引创建失败: {e}")
                results[collection_name] = {'status': 'failed', 'error': str(e)}
        
        return results
    
    async def create_index_for_collection(self, collection_name: str) -> Dict[str, Any]:
        """为指定集合创建索引"""
        try:
            collection_info = self.client.get_collection(collection_name)
            
            # 检查是否已有索引
            if hasattr(collection_info.config.params.vectors, 'hnsw_config'):
                logger.info(f"🔍 {collection_name} 已有HNSW索引")
                return {'status': 'already_exists', 'type': 'hnsw'}
            
            # 创建HNSW索引
            logger.info(f"🔧 正在为 {collection_name} 创建HNSW索引...")
            
            # 获取向量配置
            vectors_config = collection_info.config.params.vectors
            
            # 更新集合配置以添加索引
            self.client.update_collection(
                collection_name=collection_name,
                optimizer_config=models.OptimizersConfigDiff(
                    indexing_threshold=20000,  # 索引阈值
                    default_segment_number=2,   # 默认段数
                    max_segment_size=200000,    # 最大段大小
                    memmap_threshold=50000,     # 内存映射阈值
                ),
                hnsw_config=models.HnswConfigDiff(
                    m=16,                       # 连接数
                    ef_construct=100,           # 构建时的搜索深度
                    full_scan_threshold=10000,  # 全扫描阈值
                    max_indexing_threads=4,     # 最大索引线程数
                    on_disk=True,               # 磁盘索引
                )
            )
            
            logger.info(f"✅ {collection_name} HNSW索引创建成功")
            
            return {
                'status': 'created',
                'type': 'hnsw',
                'config': {
                    'm': 16,
                    'ef_construct': 100,
                    'full_scan_threshold': 10000,
                    'max_indexing_threads': 4,
                    'on_disk': True
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 创建索引失败: {e}")
            raise
    
    async def test_search_performance(self, collection_name: str, num_tests: int = 10) -> Dict[str, Any]:
        """测试搜索性能"""
        try:
            import time

            import numpy as np

            # 生成测试向量
            collection_info = self.client.get_collection(collection_name)
            vector_size = collection_info.config.params.vectors.size
            
            test_vector = random((vector_size)).tolist()
            
            # 执行多次搜索测试
            search_times = []
            
            for i in range(num_tests):
                start_time = time.time()
                
                results = self.client.search(
                    collection_name=collection_name,
                    query_vector=test_vector,
                    limit=10,
                    with_payload=True
                )
                
                search_time = time.time() - start_time
                search_times.append(search_time)
                
                logger.debug(f"🔍 测试 {i+1}: {search_time:.4f}s, 结果: {len(results)}")
            
            # 计算性能指标
            avg_time = sum(search_times) / len(search_times)
            min_time = min(search_times)
            max_time = max(search_times)
            
            performance_stats = {
                'collection': collection_name,
                'num_tests': num_tests,
                'avg_search_time': avg_time,
                'min_search_time': min_time,
                'max_search_time': max_time,
                'total_points': collection_info.points_count,
                'performance_rating': self._evaluate_performance(avg_time)
            }
            
            logger.info(f"📊 {collection_name} 性能测试完成:")
            logger.info(f"   平均搜索时间: {avg_time:.4f}s")
            logger.info(f"   性能评级: {performance_stats['performance_rating']}")
            
            return performance_stats
            
        except Exception as e:
            logger.error(f"❌ 性能测试失败: {e}")
            raise
    
    def _evaluate_performance(self, avg_time: float) -> str:
        """评估性能等级"""
        if avg_time < 0.01:
            return '优秀'
        elif avg_time < 0.05:
            return '良好'
        elif avg_time < 0.1:
            return '一般'
        else:
            return '需要优化'
    
    async def generate_report(self) -> str:
        """生成索引状态报告"""
        report_lines = [
            '# Qdrant向量索引状态报告',
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            '',
            '## 集合状态概览',
            ''
        ]
        
        for collection_name, info in self.collections_info.items():
            report_lines.append(f"### {collection_name}")
            
            if info.get('status') != 'active':
                report_lines.extend([
                    '- 状态: ❌ 异常',
                    f"- 错误: {info.get('error', '未知错误')}",
                    ''
                ])
                continue
            
            points_count = info.get('points_count', 0)
            has_index = info.get('has_index', False)
            
            report_lines.extend([
                f"- 状态: ✅ 正常",
                f"- 向量数量: {points_count:,}",
                f"- 索引状态: {'✅ 已有索引' if has_index else '❌ 无索引'}",
                ''
            ])
        
        return "\n".join(report_lines)

async def main():
    """主函数"""
    logger.info('🚀 开始创建向量索引...')
    
    try:
        # 创建索引管理器
        index_manager = VectorIndexManager()
        
        # 检查集合状态
        logger.info('📊 检查集合状态...')
        collections_status = await index_manager.check_collections_status()
        
        # 显示状态概览
        logger.info('📋 集合状态概览:')
        active_collections = [name for name, info in collections_status.items() if info.get('status') == 'active']
        logger.info(f"   活跃集合: {len(active_collections)}")
        
        for collection_name in active_collections:
            info = collections_status[collection_name]
            logger.info(f"   - {collection_name}: {info.get('points_count', 0):,} 向量")
        
        # 创建索引
        logger.info('🔧 开始创建索引...')
        index_results = await index_manager.create_indexes_for_all_collections()
        
        # 显示创建结果
        logger.info('📊 索引创建结果:')
        for collection_name, result in index_results.items():
            status = result.get('status', 'unknown')
            if status == 'created':
                logger.info(f"   ✅ {collection_name}: 索引创建成功")
            elif status == 'already_exists':
                logger.info(f"   ⚠️ {collection_name}: 索引已存在")
            else:
                logger.error(f"   ❌ {collection_name}: {result.get('error', '未知错误')}")
        
        # 性能测试
        logger.info('⚡ 开始性能测试...')
        for collection_name in active_collections:
            try:
                performance = await index_manager.test_search_performance(collection_name, num_tests=5)
                rating = performance['performance_rating']
                logger.info(f"   {collection_name}: {rating} ({performance['avg_search_time']:.4f}s)")
            except Exception as e:
                logger.warning(f"   {collection_name}: 性能测试失败 - {e}")
        
        # 生成报告
        logger.info('📄 生成状态报告...')
        report = await index_manager.generate_report()
        
        # 保存报告
        report_file = '/Users/xujian/Athena工作平台/vector_index_report.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"✅ 报告已保存到: {report_file}")
        logger.info('🎉 向量索引创建完成！')
        
    except Exception as e:
        logger.error(f"❌ 索引创建失败: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())