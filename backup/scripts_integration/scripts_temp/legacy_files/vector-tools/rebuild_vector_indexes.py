#!/usr/bin/env python3
"""
🔧 向量索引重建工具
小诺的智能索引修复脚本

功能:
1. 重建指定集合的向量索引
2. 优化索引配置
3. 监控重建进度
4. 性能测试验证

作者: 小诺 (AI助手)
创建时间: 2025-12-11
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx
from loguru import logger

logger = logging.getLogger(__name__)

# 配置日志
logger.add('vector_index_rebuild.log', rotation='10 MB', level='INFO')

class VectorIndexRebuilder:
    """向量索引重建器"""

    def __init__(self, qdrant_url: str = 'http://localhost:6333'):
        self.qdrant_url = qdrant_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def get_collections(self) -> List[Dict]:
        """获取所有集合信息"""
        try:
            response = await self.client.get(f"{self.qdrant_url}/collections")
            response.raise_for_status()
            data = response.json()
            return data['result']['collections']
        except Exception as e:
            logger.error(f"获取集合失败: {e}")
            return []

    async def get_collection_info(self, collection_name: str) -> Dict:
        """获取集合详细信息"""
        try:
            response = await self.client.get(f"{self.qdrant_url}/collections/{collection_name}")
            response.raise_for_status()
            return response.json()['result']
        except Exception as e:
            logger.error(f"获取集合 {collection_name} 信息失败: {e}")
            return {}

    async def update_collection_config(self, collection_name: str, config: Dict) -> bool:
        """更新集合配置"""
        try:
            response = await self.client.patch(
                f"{self.qdrant_url}/collections/{collection_name}",
                json=config
            )
            response.raise_for_status()
            logger.info(f"集合 {collection_name} 配置更新成功")
            return True
        except Exception as e:
            logger.error(f"更新集合 {collection_name} 配置失败: {e}")
            return False

    async def trigger_indexing(self, collection_name: str) -> bool:
        """触发索引重建"""
        try:
            # 更新索引配置来触发重建
            config = {
                'optimizer_config': {
                    'deleted_threshold': 0.1,
                    'vacuum_min_vector_number': 500,
                    'default_segment_number': 2,
                    'indexing_threshold': 1000,  # 降低阈值以触发索引
                    'flush_interval_sec': 3
                },
                'hnsw_config': {
                    'm': 32,  # 增加连接数
                    'ef_construct': 200,  # 增加构建时的搜索候选
                    'full_scan_threshold': 5000,  # 降低全扫描阈值
                    'max_indexing_threads': 4  # 增加索引线程数
                }
            }

            return await self.update_collection_config(collection_name, config)
        except Exception as e:
            logger.error(f"触发集合 {collection_name} 索引重建失败: {e}")
            return False

    async def wait_for_indexing(self, collection_name: str, timeout: int = 300) -> bool:
        """等待索引重建完成"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                info = await self.get_collection_info(collection_name)
                if info:
                    indexed_count = info.get('indexed_vectors_count', 0)
                    total_count = info.get('points_count', 0)

                    logger.info(f"集合 {collection_name}: {indexed_count}/{total_count} 向量已索引")

                    if indexed_count >= total_count:
                        logger.info(f"集合 {collection_name} 索引重建完成!")
                        return True

                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"检查索引进度失败: {e}")
                await asyncio.sleep(5)

        logger.warning(f"集合 {collection_name} 索引重建超时")
        return False

    async def test_collection_performance(self, collection_name: str) -> Dict:
        """测试集合搜索性能"""
        try:
            # 获取集合信息
            info = await self.get_collection_info(collection_name)
            if not info:
                return {'error': '无法获取集合信息'}

            vector_size = info['config']['params']['vectors']['size']

            # 创建测试向量
            test_vector = [0.1] * vector_size

            # 测试搜索性能
            search_data = {
                'vector': test_vector,
                'limit': 10,
                'with_payload': True
            }

            start_time = time.time()
            response = await self.client.post(
                f"{self.qdrant_url}/collections/{collection_name}/points/search",
                json=search_data
            )
            search_time = (time.time() - start_time) * 1000  # 转换为毫秒

            response.raise_for_status()
            results = response.json()['result']

            return {
                'search_time_ms': round(search_time, 2),
                'results_count': len(results),
                'indexed_vectors': info.get('indexed_vectors_count', 0),
                'total_vectors': info.get('points_count', 0),
                'collection_status': info.get('status', 'unknown'),
                'performance_score': '优秀' if search_time < 5 else '良好' if search_time < 15 else '需优化'
            }

        except Exception as e:
            logger.error(f"测试集合 {collection_name} 性能失败: {e}")
            return {'error': str(e)}

    async def rebuild_collection_index(self, collection_name: str) -> Dict:
        """重建单个集合的索引"""
        logger.info(f"开始重建集合 {collection_name} 的索引")

        result = {
            'collection': collection_name,
            'start_time': datetime.now().isoformat(),
            'success': False,
            'before_performance': {},
            'after_performance': {}
        }

        try:
            # 测试重建前性能
            logger.info(f"测试 {collection_name} 重建前性能...")
            result['before_performance'] = await self.test_collection_performance(collection_name)

            # 触发索引重建
            logger.info(f"触发 {collection_name} 索引重建...")
            if not await self.trigger_indexing(collection_name):
                result['error'] = '触发索引重建失败'
                return result

            # 等待重建完成
            logger.info(f"等待 {collection_name} 索引重建完成...")
            rebuild_success = await self.wait_for_indexing(collection_name)

            if rebuild_success:
                # 测试重建后性能
                logger.info(f"测试 {collection_name} 重建后性能...")
                result['after_performance'] = await self.test_collection_performance(collection_name)
                result['success'] = True
                logger.info(f"集合 {collection_name} 索引重建成功!")
            else:
                result['error'] = '索引重建超时'

        except Exception as e:
            logger.error(f"重建集合 {collection_name} 索引失败: {e}")
            result['error'] = str(e)

        result['end_time'] = datetime.now().isoformat()
        return result

    async def rebuild_all_collections(self, priority_collections: List[str] = None) -> Dict:
        """重建所有集合的索引"""
        logger.info('🚀 开始向量索引重建任务')

        if priority_collections is None:
            priority_collections = [
                'ai_technical_terms_vector_db',
                'patent_rules_unified_1024',
                'legal_clauses',
                'legal_documents',
                'general_memory_db'
            ]

        # 获取所有集合
        all_collections = await self.get_collections()
        collection_names = [col['name'] for col in all_collections]

        # 过滤出需要重建的集合
        target_collections = []
        for name in priority_collections:
            if name in collection_names:
                target_collections.append(name)

        logger.info(f"目标集合: {target_collections}")

        results = {
            'task_start_time': datetime.now().isoformat(),
            'target_collections': target_collections,
            'results': {},
            'summary': {
                'total': len(target_collections),
                'success': 0,
                'failed': 0
            }
        }

        # 并发重建索引
        tasks = []
        for collection_name in target_collections:
            task = asyncio.create_task(self.rebuild_collection_index(collection_name))
            tasks.append(task)

        # 等待所有任务完成
        rebuild_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for i, result in enumerate(rebuild_results):
            collection_name = target_collections[i]

            if isinstance(result, Exception):
                results['results'][collection_name] = {
                    'collection': collection_name,
                    'success': False,
                    'error': str(result)
                }
                results['summary']['failed'] += 1
            else:
                results['results'][collection_name] = result
                if result.get('success', False):
                    results['summary']['success'] += 1
                else:
                    results['summary']['failed'] += 1

        results['task_end_time'] = datetime.now().isoformat()

        # 保存结果
        output_file = '.runtime/index_rebuild_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"索引重建任务完成! 结果保存到: {output_file}")
        return results

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

async def main():
    """主函数"""
    rebuilder = VectorIndexRebuilder()

    try:
        # 执行索引重建
        results = await rebuilder.rebuild_all_collections()

        # 显示结果摘要
        summary = results['summary']
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 向量索引重建结果摘要")
        logger.info(f"{'='*60}")
        logger.info(f"总计集合: {summary['total']}")
        logger.info(f"成功重建: {summary['success']} ✅")
        logger.info(f"重建失败: {summary['failed']} ❌")
        logger.info(f"成功率: {summary['success']/summary['total']*100:.1f}%")

        logger.info(f"\n📈 性能改善情况:")
        for collection_name, result in results['results'].items():
            if result.get('success') and 'before_performance' in result:
                before = result['before_performance']
                after = result['after_performance']

                if 'search_time_ms' in before and 'search_time_ms' in after:
                    improvement = before['search_time_ms'] - after['search_time_ms']
                    improvement_pct = (improvement / before['search_time_ms']) * 100
                    logger.info(f"  {collection_name}: {improvement_pct:+.1f}% ({before['search_time_ms']:.1f}ms → {after['search_time_ms']:.1f}ms)")

    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断了索引重建过程")
    except Exception as e:
        logger.error(f"索引重建过程出错: {e}")
    finally:
        await rebuilder.close()

if __name__ == '__main__':
    asyncio.run(main())