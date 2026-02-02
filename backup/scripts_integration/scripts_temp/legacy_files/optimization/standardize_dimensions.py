#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准化向量维度
将非1024维的向量标准化为1024维
"""

import json
import logging
from datetime import datetime

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    PointStruct,
    VectorParams,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_vector_dimensions():
    """检查向量维度分布"""
    client = QdrantClient('http://localhost:6333')

    logger.info('📊 检查向量维度分布...')

    collections = client.get_collections().collections
    dimensions = {}

    for collection in collections:
        try:
            info = client.get_collection(collection.name)
            vector_size = info.config.params.vectors.size
            count = client.count(collection.name).count

            if vector_size not in dimensions:
                dimensions[vector_size] = []
            dimensions[vector_size].append({
                'name': collection.name,
                'count': count
            })

            logger.info(f"  {collection.name:35} : {vector_size:>4}维, {count:>8,} vectors")
        except Exception as e:
            logger.warning(f"  ⚠️ {collection.name}: {e}")

    logger.info("\n📈 维度分布:")
    for dim, collections in sorted(dimensions.items()):
        total_count = sum(c['count'] for c in collections)
        logger.info(f"  {dim:>4}维: {len(collections)}个集合, {total_count:,} vectors")

    return dimensions

def create_standardized_collections():
    """创建标准维度集合"""
    client = QdrantClient('http://localhost:6333')

    # 需要标准化的集合
    target_collections = {
        'ai_technical_terms_1024': {
            'source': 'ai_technical_terms_vector_db',
            'source_dim': 384,
            'target_dim': 1024
        },
        'legal_laws_1024': {
            'source': 'legal_laws_comprehensive',
            'source_dim': 768,
            'target_dim': 1024
        }
    }

    logger.info('🏗️ 创建标准维度集合...')

    for target_name, config in target_collections.items():
        try:
            # 检查是否已存在
            collections = client.get_collections().collections
            if not any(c.name == target_name for c in collections):
                client.create_collection(
                    collection_name=target_name,
                    vectors_config=VectorParams(
                        size=1024,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"  ✅ 创建: {target_name}")
            else:
                logger.info(f"  ⚠️ 已存在: {target_name}")
        except Exception as e:
            logger.error(f"  ❌ 创建失败 {target_name}: {e}")

    return target_collections

def normalize_vector(vector, target_dim=1024):
    """将向量标准化到目标维度"""
    current_dim = len(vector)

    if current_dim == target_dim:
        return vector

    # 如果维度不足，填充零
    if current_dim < target_dim:
        padding = target_dim - current_dim
        return np.pad(vector, (0, padding), 'constant').tolist()

    # 如果维度过多，截断
    if current_dim > target_dim:
        return vector[:target_dim]

    return vector

def migrate_with_standardization():
    """执行维度标准化迁移"""
    client = QdrantClient('http://localhost:6333')

    # 需要标准化的配置
    migrations = [
        {
            'source': 'ai_technical_terms_vector_db',
            'target': 'ai_technical_terms_1024',
            'batch_size': 1000
        },
        {
            'source': 'legal_laws_comprehensive',
            'target': 'legal_laws_1024',
            'batch_size': 500
        }
    ]

    total_migrated = 0

    for migration in migrations:
        source = migration['source']
        target = migration['target']
        batch_size = migration['batch_size']

        logger.info(f"\n🔄 标准化迁移: {source} -> {target}")

        # 获取总数量
        total_count = client.count(source).count
        if total_count == 0:
            logger.info(f"  ⚠️ 源集合为空，跳过")
            continue

        logger.info(f"  📦 总数据量: {total_count:,}")

        offset = None
        migrated = 0

        while True:
            # 获取批次数据
            points, next_offset = client.scroll(
                collection_name=source,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )

            if not points:
                break

            # 标准化向量并迁移
            standardized_points = []
            for point in points:
                # 标准化向量维度
                if hasattr(point.vector, '__len__'):
                    std_vector = normalize_vector(point.vector, 1024)
                else:
                    continue

                # 更新payload
                payload = point.payload.copy()
                payload['_standardized_from'] = source
                payload['_original_dim'] = len(point.vector)
                payload['_standardized_at'] = datetime.now().isoformat()

                standardized_points.append(PointStruct(
                    id=point.id,
                    vector=std_vector,
                    payload=payload
                ))

            # 批量插入
            if standardized_points:
                client.upsert(
                    collection_name=target,
                    points=standardized_points
                )
                migrated += len(standardized_points)

            logger.info(f"    已迁移: {migrated:,}/{total_count:,}")

            offset = next_offset
            if offset is None:
                break

        logger.info(f"  ✅ {source} 迁移完成: {migrated:,} 条")
        total_migrated += migrated

    return total_migrated

def verify_standardization():
    """验证标准化结果"""
    client = QdrantClient('http://localhost:6333')

    logger.info('✅ 验证标准化结果...')

    # 检查标准化后的集合
    standardized_collections = ['ai_technical_terms_1024', 'legal_laws_1024']

    total_standardized = 0
    for col in standardized_collections:
        try:
            count = client.count(col).count
            if count > 0:
                info = client.get_collection(col)
                dim = info.config.params.vectors.size
                total_standardized += count
                logger.info(f"  ✅ {col:30} : {count:>8,} vectors, {dim}维")
        except:
            logger.warning(f"  ⚠️ 集合不存在: {col}")

    logger.info(f"\n📊 标准化统计:")
    logger.info(f"  总标准化向量: {total_standardized:,}")

    return total_standardized

def generate_dimension_standardization_config():
    """生成维度标准化配置"""
    config = {
        'dimension_standardization': {
            'enabled': True,
            'target_dimension': 1024,
            'standardized_collections': {
                'ai_technical_terms': 'ai_technical_terms_1024',
                'legal_laws': 'legal_laws_1024'
            },
            'migration_strategy': {
                '384_to_1024': 'zero_padding',
                '768_to_1024': 'zero_padding',
                '1024+': 'truncation'
            },
            'performance_impact': {
                'storage_increase': '~66%',
                'query_consistency': 'improved',
                'compatibility': 'full'
            }
        },
        'next_steps': [
            '1. 更新应用代码使用新的集合名称',
            '2. 验证查询功能正常',
            '3. 考虑删除原始非标准维度集合',
            '4. 监控性能变化'
        ]
    }

    # 保存配置
    import json
    with open('/Users/xujian/Athena工作平台/config/dimension_standardization.json', 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    logger.info('💾 配置已保存: config/dimension_standardization.json')

def main():
    logger.info('🚀 开始向量维度标准化...')

    # 1. 检查维度分布
    dimensions = check_vector_dimensions()

    # 2. 创建标准化集合
    create_standardized_collections()

    # 3. 执行迁移
    migrated = migrate_with_standardization()

    # 4. 验证结果
    verify_standardization()

    # 5. 生成配置
    generate_dimension_standardization_config()

    logger.info("\n✅ 向量维度标准化完成！")
    logger.info(f"总标准化向量: {migrated:,}")

if __name__ == '__main__':
    main()