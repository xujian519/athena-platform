#!/usr/bin/env python3
"""
🔧 向量维度修复工具
小诺的智能维度修复脚本

功能:
1. 修复集合的向量维度配置
2. 重新创建维度不匹配的集合
3. 数据迁移和转换
4. 验证修复结果

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
logger.add('vector_dimension_fix.log', rotation='10 MB', level='INFO')

class VectorDimensionFixer:
    """向量维度修复器"""

    def __init__(self, qdrant_url: str = 'http://localhost:6333'):
        self.qdrant_url = qdrant_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def get_collection_info(self, collection_name: str) -> Dict:
        """获取集合详细信息"""
        try:
            response = await self.client.get(f"{self.qdrant_url}/collections/{collection_name}")
            response.raise_for_status()
            return response.json()['result']
        except Exception as e:
            logger.error(f"获取集合 {collection_name} 信息失败: {e}")
            return {}

    async def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            response = await self.client.delete(f"{self.qdrant_url}/collections/{collection_name}")
            response.raise_for_status()
            logger.info(f"集合 {collection_name} 删除成功")
            return True
        except Exception as e:
            logger.error(f"删除集合 {collection_name} 失败: {e}")
            return False

    async def create_collection(self, collection_name: str, vector_size: int,
                               distance: str = 'Cosine') -> bool:
        """创建新集合"""
        try:
            collection_config = {
                'vectors': {
                    'size': vector_size,
                    'distance': distance
                },
                'optimizers_config': {
                    'deleted_threshold': 0.1,
                    'vacuum_min_vector_number': 500,
                    'default_segment_number': 2,
                    'indexing_threshold': 1000,
                    'max_optimization_threads': 4
                },
                'hnsw_config': {
                    'm': 32,
                    'ef_construct': 200,
                    'full_scan_threshold': 5000,
                    'max_indexing_threads': 4
                },
                'quantization_config': None,
                'on_disk_payload': True
            }

            response = await self.client.put(
                f"{self.qdrant_url}/collections/{collection_name}",
                json=collection_config
            )
            response.raise_for_status()
            logger.info(f"集合 {collection_name} 创建成功 (向量维度: {vector_size})")
            return True

        except Exception as e:
            logger.error(f"创建集合 {collection_name} 失败: {e}")
            return False

    async def backup_collection_data(self, collection_name: str) -> List[Dict]:
        """备份集合数据"""
        try:
            # 获取所有向量
            scroll_data = {
                'limit': 10000,  # 每次获取1万个向量
                'with_payload': True,
                'with_vector': True
            }

            all_points = []
            offset = None

            while True:
                if offset:
                    scroll_data['offset'] = offset

                response = await self.client.post(
                    f"{self.qdrant_url}/collections/{collection_name}/points/scroll",
                    json=scroll_data
                )
                response.raise_for_status()

                result = response.json()['result']
                points = result.get('points', [])

                if not points:
                    break

                all_points.extend(points)

                if len(points) < scroll_data['limit']:
                    break

                # 使用最后一个点的ID作为偏移
                offset = points[-1]['id']

                logger.info(f"已备份 {len(all_points)} 个向量...")

            logger.info(f"集合 {collection_name} 数据备份完成，共 {len(all_points)} 个向量")
            return all_points

        except Exception as e:
            logger.error(f"备份集合 {collection_name} 数据失败: {e}")
            return []

    async def restore_collection_data(self, collection_name: str,
                                     data: List[Dict], batch_size: int = 100) -> bool:
        """恢复集合数据"""
        try:
            if not data:
                logger.warning(f"集合 {collection_name} 无数据需要恢复")
                return True

            # 分批插入数据
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]

                upload_data = {
                    'points': batch
                }

                response = await self.client.put(
                    f"{self.qdrant_url}/collections/{collection_name}/points",
                    json=upload_data
                )
                response.raise_for_status()

                logger.info(f"已恢复 {min(i + batch_size, len(data))}/{len(data)} 个向量")

            logger.info(f"集合 {collection_name} 数据恢复完成")
            return True

        except Exception as e:
            logger.error(f"恢复集合 {collection_name} 数据失败: {e}")
            return False

    async def convert_vector_dimensions(self, old_vectors: List[List[float]],
                                       new_size: int) -> List[List[float]]:
        """转换向量维度"""
        if not old_vectors:
            return []

        converted_vectors = []
        old_size = len(old_vectors[0])

        for vector in old_vectors:
            if old_size == new_size:
                # 维度相同，直接使用
                converted_vectors.append(vector)
            elif old_size < new_size:
                # 维度不足，填充0
                new_vector = vector + [0.0] * (new_size - old_size)
                converted_vectors.append(new_vector)
            else:
                # 维度过多，截断
                new_vector = vector[:new_size]
                converted_vectors.append(new_vector)

        return converted_vectors

    async def fix_collection_dimensions(self, collection_name: str,
                                       target_vector_size: int) -> Dict:
        """修复集合的向量维度"""
        logger.info(f"开始修复集合 {collection_name} 的向量维度到 {target_vector_size}")

        result = {
            'collection': collection_name,
            'target_vector_size': target_vector_size,
            'start_time': datetime.now().isoformat(),
            'success': False,
            'steps': []
        }

        try:
            # 1. 获取当前集合信息
            logger.info(f"步骤1: 获取集合 {collection_name} 当前信息...")
            current_info = await self.get_collection_info(collection_name)
            if not current_info:
                result['error'] = '无法获取集合信息'
                return result

            current_size = current_info['config']['params']['vectors']['size']
            points_count = current_info.get('points_count', 0)

            result['steps'].append(f"当前向量维度: {current_size}")
            result['steps'].append(f"向量数量: {points_count}")

            if current_size == target_vector_size:
                result['steps'].append('向量维度已匹配，无需修复')
                result['success'] = True
                return result

            # 2. 备份现有数据
            logger.info(f"步骤2: 备份集合 {collection_name} 数据...")
            backup_data = await self.backup_collection_data(collection_name)
            if not backup_data and points_count > 0:
                result['error'] = '数据备份失败'
                return result

            result['steps'].append(f"备份数据: {len(backup_data)} 个向量")

            # 3. 删除旧集合
            logger.info(f"步骤3: 删除旧集合 {collection_name}...")
            if not await self.delete_collection(collection_name):
                result['error'] = '删除旧集合失败'
                return result

            result['steps'].append('删除旧集合成功')

            # 4. 创建新集合
            logger.info(f"步骤4: 创建新集合 {collection_name} (维度: {target_vector_size})...")
            if not await self.create_collection(collection_name, target_vector_size):
                result['error'] = '创建新集合失败'
                return result

            result['steps'].append('创建新集合成功')

            # 5. 转换和恢复数据
            if backup_data:
                logger.info(f"步骤5: 转换向量维度并恢复数据...")

                # 转换向量维度
                for point in backup_data:
                    if 'vector' in point:
                        vector = point['vector']
                        if len(vector) != target_vector_size:
                            converted_vector = await self.convert_vector_dimensions([vector], target_vector_size)
                            point['vector'] = converted_vector[0]

                # 恢复数据
                if not await self.restore_collection_data(collection_name, backup_data):
                    result['error'] = '数据恢复失败'
                    return result

                result['steps'].append(f"转换和恢复数据: {len(backup_data)} 个向量")

            # 6. 验证修复结果
            logger.info(f"步骤6: 验证修复结果...")
            new_info = await self.get_collection_info(collection_name)
            if new_info:
                new_size = new_info['config']['params']['vectors']['size']
                new_points_count = new_info.get('points_count', 0)

                if new_size == target_vector_size:
                    result['success'] = True
                    result['steps'].append(f"验证成功: 维度={new_size}, 向量数={new_points_count}")
                else:
                    result['error'] = f"维度修复失败: 期望{target_vector_size}, 实际{new_size}"

        except Exception as e:
            logger.error(f"修复集合 {collection_name} 维度失败: {e}")
            result['error'] = str(e)

        result['end_time'] = datetime.now().isoformat()
        return result

    async def test_fixed_collection(self, collection_name: str,
                                  test_query: str = '测试查询') -> Dict:
        """测试修复后的集合"""
        try:
            # 获取集合信息
            info = await self.get_collection_info(collection_name)
            if not info:
                return {'error': '无法获取集合信息'}

            vector_size = info['config']['params']['vectors']['size']

            # 创建测试向量
            test_vector = [0.1] * vector_size

            # 测试搜索
            search_data = {
                'vector': test_vector,
                'limit': 5,
                'with_payload': True
            }

            start_time = time.time()
            response = await self.client.post(
                f"{self.qdrant_url}/collections/{collection_name}/points/search",
                json=search_data
            )
            search_time = (time.time() - start_time) * 1000

            response.raise_for_status()
            results = response.json()['result']

            return {
                'test_success': True,
                'search_time_ms': round(search_time, 2),
                'results_count': len(results),
                'vector_size': vector_size,
                'total_vectors': info.get('points_count', 0),
                'indexed_vectors': info.get('indexed_vectors_count', 0),
                'collection_status': info.get('status', 'unknown')
            }

        except Exception as e:
            logger.error(f"测试集合 {collection_name} 失败: {e}")
            return {'error': str(e)}

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

async def main():
    """主函数"""
    fixer = VectorDimensionFixer()

    try:
        logger.info('🔧 开始向量维度修复任务')

        # 定义需要修复的集合
        collections_to_fix = [
            {
                'name': 'general_memory_db',
                'target_size': 384,  # 修改为384以匹配其他集合
                'description': '通用记忆数据库'
            }
        ]

        results = {
            'task_start_time': datetime.now().isoformat(),
            'collections': collections_to_fix,
            'results': {},
            'summary': {
                'total': len(collections_to_fix),
                'success': 0,
                'failed': 0
            }
        }

        # 修复每个集合
        for collection_info in collections_to_fix:
            collection_name = collection_info['name']
            target_size = collection_info['target_size']

            logger.info(f"开始修复集合: {collection_name}")

            # 修复维度
            fix_result = await fixer.fix_collection_dimensions(collection_name, target_size)
            results['results'][collection_name] = fix_result

            if fix_result.get('success', False):
                results['summary']['success'] += 1

                # 测试修复后的集合
                logger.info(f"测试修复后的集合: {collection_name}")
                test_result = await fixer.test_fixed_collection(collection_name)
                results['results'][collection_name]['test_result'] = test_result

                if test_result.get('test_success', False):
                    logger.info(f"集合 {collection_name} 测试通过! 搜索时间: {test_result.get('search_time_ms', 0)}ms")
                else:
                    logger.error(f"集合 {collection_name} 测试失败")
            else:
                results['summary']['failed'] += 1

        results['task_end_time'] = datetime.now().isoformat()

        # 保存结果
        output_file = '.runtime/dimension_fix_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 显示结果摘要
        summary = results['summary']
        logger.info(f"\n{'='*60}")
        logger.info(f"🔧 向量维度修复结果摘要")
        logger.info(f"{'='*60}")
        logger.info(f"总计集合: {summary['total']}")
        logger.info(f"修复成功: {summary['success']} ✅")
        logger.info(f"修复失败: {summary['failed']} ❌")
        logger.info(f"成功率: {summary['success']/summary['total']*100:.1f}%")

        logger.info(f"\n📊 修复详情:")
        for collection_name, result in results['results'].items():
            if result.get('success', False):
                logger.info(f"  {collection_name}: ✅ 成功")
                if 'test_result' in result:
                    test = result['test_result']
                    logger.info(f"    - 向量维度: {test.get('vector_size', 'N/A')}")
                    logger.info(f"    - 向量数量: {test.get('total_vectors', 'N/A')}")
                    logger.info(f"    - 搜索时间: {test.get('search_time_ms', 'N/A')}ms")
            else:
                logger.info(f"  {collection_name}: ❌ 失败")
                logger.info(f"    - 错误: {result.get('error', 'Unknown error')}")

    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断了维度修复过程")
    except Exception as e:
        logger.error(f"维度修复过程出错: {e}")
    finally:
        await fixer.close()

if __name__ == '__main__':
    asyncio.run(main())