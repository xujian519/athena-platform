#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合Qdrant数据
将现有的分散Qdrant集合整合为优化的结构
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        FieldCondition,
        Filter,
        MatchValue,
        PointStruct,
        VectorParams,
    )
    QDRANT_AVAILABLE = True
except ImportError:
    logger.info('❌ 请安装qdrant-client')
    QDRANT_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QdrantConsolidator:
    """Qdrant数据整合器"""

    def __init__(self):
        self.project_root = Path(project_root)
        self.qdrant_client = QdrantClient('http://localhost:6333') if QDRANT_AVAILABLE else None

        # 目标集合配置
        self.target_collections = {
            'patents_unified': {
                'vector_size': 1024,
                'description': '统一的专利向量集合'
            },
            'legal_unified': {
                'vector_size': 1024,
                'description': '统一的法律文档向量集合'
            },
            'technical_unified': {
                'vector_size': 768,
                'description': '统一的技术术语向量集合'
            },
            'memory_unified': {
                'vector_size': 1024,
                'description': '统一的记忆向量集合'
            }
        }

    def analyze_existing_collections(self) -> Dict[str, Any]:
        """分析现有的Qdrant集合"""
        logger.info('🔍 分析现有Qdrant集合...')

        if not self.qdrant_client:
            logger.error('❌ Qdrant客户端未初始化')
            return {}

        collections = self.qdrant_client.get_collections().collections
        analysis = {
            'total_collections': len(collections),
            'collections': {},
            'total_vectors': 0
        }

        for collection in collections:
            name = collection.name
            try:
                info = self.qdrant_client.get_collection(name)
                analysis['collections'][name] = {
                    'points_count': info.points_count,
                    'vector_size': info.config.params.vectors.size,
                    'distance': info.config.params.vectors.distance.value,
                    'status': info.status
                }
                analysis['total_vectors'] += info.points_count
                logger.info(f"  ✅ {name}: {info.points_count} 向量")
            except Exception as e:
                logger.warning(f"  ⚠️ 无法获取集合 {name} 信息: {e}")
                analysis['collections'][name] = {'error': str(e)}

        return analysis

    def create_target_collections(self) -> Dict[str, bool]:
        """创建目标集合"""
        logger.info('🏗️ 创建目标集合...')

        results = {}

        for collection_name, config in self.target_collections.items():
            try:
                # 检查是否已存在
                existing = self.qdrant_client.get_collections().collections
                exists = any(c.name == collection_name for c in existing)

                if not exists:
                    self.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=config['vector_size'],
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"  ✅ 创建集合: {collection_name}")
                    results[collection_name] = True
                else:
                    logger.info(f"  ⚠️ 集合已存在: {collection_name}")
                    results[collection_name] = True

            except Exception as e:
                logger.error(f"  ❌ 创建集合失败 {collection_name}: {e}")
                results[collection_name] = False

        return results

    def consolidate_patent_collections(self) -> Dict[str, Any]:
        """整合专利相关集合"""
        logger.info('📦 整合专利集合...')

        patent_collections = [
            'patent_judgment_db',
            'patent_invalid_db',
            'patent_rules_unified_1024',
            'patent_review_db'
        ]

        stats = {
            'total_migrated': 0,
            'collections_processed': 0,
            'errors': []
        }

        for collection_name in patent_collections:
            try:
                # 检查集合是否存在
                info = self.qdrant_client.get_collection(collection_name)
                if info.points_count == 0:
                    logger.info(f"  ⚠️ 跳过空集合: {collection_name}")
                    continue

                logger.info(f"  🔄 处理集合: {collection_name} ({info.points_count} 向量)")

                # 获取所有向量（分批）
                all_points = []
                offset = None
                batch_size = 1000

                while True:
                    points, next_offset = self.qdrant_client.scroll(
                        collection_name=collection_name,
                        limit=batch_size,
                        offset=offset,
                        with_payload=True,
                        with_vectors=True
                    )

                    if not points:
                        break

                    # 转换为目标格式
                    for point in points:
                        # 确保向量维度正确
                        if hasattr(point.vector, '__len__') and len(point.vector) != 1024:
                            logger.warning(f"  ⚠️ 跳过维度不正确的向量: {len(point.vector)}")
                            continue

                        # 添加来源信息
                        point.payload['_source_collection'] = collection_name
                        point.payload['_migrated_at'] = datetime.now().isoformat()

                        all_points.append(point)

                    offset = next_offset
                    if offset is None:
                        break

                # 批量插入到目标集合
                if all_points:
                    self.qdrant_client.upsert(
                        collection_name='patents_unified',
                        points=all_points
                    )
                    stats['total_migrated'] += len(all_points)
                    logger.info(f"  ✅ 迁移 {len(all_points)} 个向量到 patents_unified")

                stats['collections_processed'] += 1

            except Exception as e:
                error_msg = f"处理集合 {collection_name} 失败: {e}"
                logger.error(f"  ❌ {error_msg}")
                stats['errors'].append(error_msg)

        return stats

    def consolidate_legal_collections(self) -> Dict[str, Any]:
        """整合法律相关集合"""
        logger.info('⚖️ 整合法律集合...')

        legal_collections = [
            'legal_vector_db',
            'legal_clauses',
            'legal_clauses_shard_0',
            'legal_clauses_shard_1',
            'legal_laws_comprehensive',
            'legal_documents',
            'legal_patent_vectors'
        ]

        stats = {
            'total_migrated': 0,
            'collections_processed': 0,
            'errors': []
        }

        for collection_name in legal_collections:
            try:
                info = self.qdrant_client.get_collection(collection_name)
                if info.points_count == 0:
                    logger.info(f"  ⚠️ 跳过空集合: {collection_name}")
                    continue

                logger.info(f"  🔄 处理集合: {collection_name} ({info.points_count} 向量)")

                # 获取所有向量
                all_points = []
                offset = None
                batch_size = 1000

                while True:
                    points, next_offset = self.qdrant_client.scroll(
                        collection_name=collection_name,
                        limit=batch_size,
                        offset=offset,
                        with_payload=True,
                        with_vectors=True
                    )

                    if not points:
                        break

                    for point in points:
                        # 调整向量维度到1024
                        if hasattr(point.vector, '__len__') and len(point.vector) != 1024:
                            if len(point.vector) < 1024:
                                # 填充到1024维
                                vector = list(point.vector) + [0.0] * (1024 - len(point.vector))
                            else:
                                # 截断到1024维
                                vector = list(point.vector)[:1024]
                            point.vector = vector

                        # 添加元数据
                        point.payload['_source_collection'] = collection_name
                        point.payload['_migrated_at'] = datetime.now().isoformat()

                        all_points.append(point)

                    offset = next_offset
                    if offset is None:
                        break

                # 批量插入
                if all_points:
                    self.qdrant_client.upsert(
                        collection_name='legal_unified',
                        points=all_points
                    )
                    stats['total_migrated'] += len(all_points)
                    logger.info(f"  ✅ 迁移 {len(all_points)} 个向量到 legal_unified")

                stats['collections_processed'] += 1

            except Exception as e:
                error_msg = f"处理集合 {collection_name} 失败: {e}"
                logger.error(f"  ❌ {error_msg}")
                stats['errors'].append(error_msg)

        return stats

    def consolidate_other_collections(self) -> Dict[str, Any]:
        """整合其他集合"""
        logger.info('📚 整合其他集合...')

        # 处理技术术语
        tech_stats = self._consolidate_collection(
            'ai_technical_terms_vector_db',
            'technical_unified',
            768
        )

        # 处理记忆数据
        memory_stats = self._consolidate_collection(
            'general_memory_db',
            'memory_unified',
            1024
        )

        return {
            'technical': tech_stats,
            'memory': memory_stats
        }

    def _consolidate_collection(self, source: str, target: str, target_size: int) -> Dict[str, Any]:
        """整合单个集合"""
        stats = {
            'source': source,
            'target': target,
            'total_migrated': 0,
            'errors': []
        }

        try:
            info = self.qdrant_client.get_collection(source)
            if info.points_count == 0:
                logger.info(f"  ⚠️ 跳过空集合: {source}")
                return stats

            logger.info(f"  🔄 {source} -> {target}")

            all_points = []
            offset = None
            batch_size = 1000

            while True:
                points, next_offset = self.qdrant_client.scroll(
                    collection_name=source,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True
                )

                if not points:
                    break

                for point in points:
                    # 调整向量维度
                    if hasattr(point.vector, '__len__') and len(point.vector) != target_size:
                        if len(point.vector) < target_size:
                            vector = list(point.vector) + [0.0] * (target_size - len(point.vector))
                        else:
                            vector = list(point.vector)[:target_size]
                        point.vector = vector

                    point.payload['_source_collection'] = source
                    point.payload['_migrated_at'] = datetime.now().isoformat()

                    all_points.append(point)

                offset = next_offset
                if offset is None:
                    break

            if all_points:
                self.qdrant_client.upsert(
                    collection_name=target,
                    points=all_points
                )
                stats['total_migrated'] = len(all_points)
                logger.info(f"  ✅ 迁移 {len(all_points)} 个向量")

        except Exception as e:
            stats['errors'].append(str(e))

        return stats

    def verify_migration(self) -> Dict[str, Any]:
        """验证迁移结果"""
        logger.info('✅ 验证迁移结果...')

        verification = {
            'target_collections': {},
            'total_vectors': 0
        }

        for collection_name in self.target_collections.keys():
            try:
                info = self.qdrant_client.get_collection(collection_name)
                verification['target_collections'][collection_name] = {
                    'points_count': info.points_count,
                    'vector_size': info.config.params.vectors.size,
                    'status': info.status
                }
                verification['total_vectors'] += info.points_count

                logger.info(f"  ✅ {collection_name}: {info.points_count} 向量")

            except Exception as e:
                logger.error(f"  ❌ 验证集合失败 {collection_name}: {e}")
                verification['target_collections'][collection_name] = {'error': str(e)}

        return verification

    def generate_optimized_config(self) -> Dict[str, Any]:
        """生成优化后的配置"""
        config = {
            'qdrant_optimized': {
                'collections': {
                    'patents': {
                        'collection_name': 'patents_unified',
                        'vector_size': 1024,
                        'description': '统一存储所有专利相关向量',
                        'access_pattern': 'high_frequency',
                        'cache_policy': 'aggressive'
                    },
                    'legal': {
                        'collection_name': 'legal_unified',
                        'vector_size': 1024,
                        'description': '统一存储所有法律文档向量',
                        'access_pattern': 'medium_frequency',
                        'cache_policy': 'moderate'
                    },
                    'technical': {
                        'collection_name': 'technical_unified',
                        'vector_size': 768,
                        'description': '统一存储技术术语向量',
                        'access_pattern': 'medium_frequency',
                        'cache_policy': 'moderate'
                    },
                    'memory': {
                        'collection_name': 'memory_unified',
                        'vector_size': 1024,
                        'description': '统一存储记忆向量',
                        'access_pattern': 'low_frequency',
                        'cache_policy': 'minimal'
                    }
                },
                'search_strategy': {
                    'patent_queries': ['patents_unified'],
                    'legal_queries': ['legal_unified', 'patents_unified'],
                    'technical_queries': ['technical_unified'],
                    'memory_queries': ['memory_unified']
                },
                'optimization_settings': {
                    'hnsw': {
                        'm': 16,
                        'ef_construct': 100
                    },
                    'quantization': {
                        'enabled': True,
                        'scalar': {
                            'type': 'int8'
                        }
                    },
                    'wal': {
                        'disabled': False,
                        'wal_capacity_mb': 32
                    }
                }
            }
        }

        return config

    def run_consolidation(self) -> Dict[str, Any]:
        """执行完整的整合流程"""
        logger.info('🚀 开始Qdrant数据整合...')

        start_time = datetime.now()

        results = {
            'consolidation_id': f"qdrant_consolidation_{start_time.strftime('%Y%m%d_%H%M%S')}",
            'start_time': start_time.isoformat(),
            'steps': {}
        }

        # 1. 分析现有集合
        logger.info("\n📍 步骤1: 分析现有集合")
        analysis = self.analyze_existing_collections()
        results['steps']['analysis'] = analysis

        # 2. 创建目标集合
        logger.info("\n📍 步骤2: 创建目标集合")
        created = self.create_target_collections()
        results['steps']['create_collections'] = created

        # 3. 整合专利集合
        logger.info("\n📍 步骤3: 整合专利数据")
        patent_stats = self.consolidate_patent_collections()
        results['steps']['patent_consolidation'] = patent_stats

        # 4. 整合法律集合
        logger.info("\n📍 步骤4: 整合法律数据")
        legal_stats = self.consolidate_legal_collections()
        results['steps']['legal_consolidation'] = legal_stats

        # 5. 整合其他集合
        logger.info("\n📍 步骤5: 整合其他数据")
        other_stats = self.consolidate_other_collections()
        results['steps']['other_consolidation'] = other_stats

        # 6. 验证结果
        logger.info("\n📍 步骤6: 验证迁移")
        verification = self.verify_migration()
        results['steps']['verification'] = verification

        # 7. 生成优化配置
        logger.info("\n📍 步骤7: 生成配置")
        config = self.generate_optimized_config()
        results['steps']['config'] = config

        # 保存配置
        config_path = self.project_root / 'config' / 'qdrant_optimized.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 配置已保存: {config_path}")

        # 完成信息
        end_time = datetime.now()
        results['end_time'] = end_time.isoformat()
        results['duration_seconds'] = (end_time - start_time).total_seconds()

        # 统计摘要
        total_migrated = (
            patent_stats.get('total_migrated', 0) +
            legal_stats.get('total_migrated', 0) +
            other_stats.get('technical', {}).get('total_migrated', 0) +
            other_stats.get('memory', {}).get('total_migrated', 0)
        )

        results['summary'] = {
            'total_collections_analyzed': analysis.get('total_collections', 0),
            'total_vectors_before': analysis.get('total_vectors', 0),
            'total_vectors_migrated': total_migrated,
            'total_vectors_after': verification.get('total_vectors', 0),
            'target_collections_created': sum(created.values())
        }

        # 保存整合报告
        report_path = self.project_root / 'qdrant_consolidation_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        return results

def main():
    """主函数"""
    logger.info('🔄 Athena工作平台 - Qdrant数据整合工具')
    logger.info(str('='*60))

    if not QDRANT_AVAILABLE:
        logger.info('❌ 请安装qdrant-client: pip install qdrant-client')
        return

    # 创建整合器
    consolidator = QdrantConsolidator()

    # 执行整合
    try:
        results = consolidator.run_consolidation()

        # 打印摘要
        logger.info(str("\n" + '='*60))
        logger.info('📊 整合摘要')
        logger.info(str('='*60))

        summary = results['summary']
        logger.info(f"集合数量: {summary['total_collections_analyzed']} -> {len(consolidator.target_collections)}")
        logger.info(f"向量总数: {summary['total_vectors_before']} -> {summary['total_vectors_after']}")
        logger.info(f"迁移向量: {summary['total_vectors_migrated']}")
        logger.info(f"耗时: {results['duration_seconds']:.2f} 秒")

        logger.info("\n集合详情:")
        for collection, info in results['steps']['verification']['target_collections'].items():
            if 'points_count' in info:
                logger.info(f"  ✅ {collection}: {info['points_count']:,} 向量")

        logger.info("\n✅ 整合完成！")
        logger.info('📋 配置文件: config/qdrant_optimized.json')
        logger.info('📋 详细报告: qdrant_consolidation_report.json')

    except Exception as e:
        logger.error(f"❌ 整合失败: {e}")
        logger.info(f"\n❌ 整合过程中出现错误: {e}")

if __name__ == '__main__':
    main()