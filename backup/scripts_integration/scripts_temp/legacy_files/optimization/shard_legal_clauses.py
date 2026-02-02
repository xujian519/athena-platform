#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为legal_clauses实施分片策略
将131,885个法律条款向量分片到多个集合
"""

import json
import logging
import time
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sharded_collections():
    """创建分片集合"""
    client = QdrantClient('http://localhost:6333')

    # 定义分片策略
    shards = {
        'legal_clauses_contract': '合同条款',
        'legal_clauses_ip': '知识产权条款',
        'legal_clauses_tort': '侵权条款',
        'legal_clauses_labor': '劳动条款',
        'legal_clauses_corporate': '公司条款',
        'legal_clauses_property': '财产条款'
    }

    logger.info('🏗️ 创建分片集合...')

    for shard_name, description in shards.items():
        try:
            # 检查是否已存在
            collections = client.get_collections().collections
            if not any(c.name == shard_name for c in collections):
                client.create_collection(
                    collection_name=shard_name,
                    vectors_config=VectorParams(
                        size=1024,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"  ✅ 创建集合: {shard_name} - {description}")
            else:
                logger.info(f"  ⚠️ 集合已存在: {shard_name}")
        except Exception as e:
            logger.error(f"  ❌ 创建集合失败 {shard_name}: {e}")

    return shards

def analyze_legal_clauses_content():
    """分析法律条款内容分布"""
    client = QdrantClient('http://localhost:6333')

    logger.info('📊 分析legal_clauses内容分布...')

    # 获取样本数据
    sample_size = 1000
    points, _ = client.scroll(
        collection_name='legal_clauses',
        limit=sample_size,
        with_payload=True
    )

    # 分析类别分布
    category_count = {}
    content_keywords = {
        'contract': ['合同', '协议', '约定', '条款'],
        'ip': ['专利', '商标', '著作权', '知识产权'],
        'tort': ['侵权', '赔偿', '责任', '损害'],
        'labor': ['劳动', '工资', '雇佣', '解雇'],
        'corporate': ['公司', '股权', '董事会', '股东'],
        'property': ['房产', '土地', '不动产', '所有权']
    }

    for point in points:
        content = point.payload.get('content', '').lower()
        category = point.payload.get('category', '')

        # 基于内容关键词分类
        matched = False
        for cat_name, keywords in content_keywords.items():
            if any(keyword in content for keyword in keywords):
                category_count[cat_name] = category_count.get(cat_name, 0) + 1
                matched = True
                break

        if not matched:
            category_count['other'] = category_count.get('other', 0) + 1

    logger.info('  📈 类别分布:')
    for cat, count in sorted(category_count.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"    {cat}: {count}")

    return category_count

def migrate_to_shards():
    """迁移数据到分片"""
    client = QdrantClient('http://localhost:6333')

    logger.info('🔄 开始迁移legal_clauses到分片...')

    # 获取总数据量
    total_count = client.count('legal_clauses').count
    batch_size = 1000
    migrated_count = 0

    logger.info(f"  📦 总数据量: {total_count:,}")

    # 分批处理
    with tqdm(total=total_count, desc='迁移进度') as pbar:
        offset = None

        while True:
            # 获取批次数据
            points, next_offset = client.scroll(
                collection_name='legal_clauses',
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )

            if not points:
                break

            # 分类并迁移
            for point in points:
                content = point.payload.get('content', '').lower()
                target_shard = 'legal_clauses_contract'  # 默认分片

                # 基于内容确定目标分片
                if '专利' in content or '商标' in content or '著作权' in content:
                    target_shard = 'legal_clauses_ip'
                elif '侵权' in content or '赔偿' in content or '损害' in content:
                    target_shard = 'legal_clauses_tort'
                elif '劳动' in content or '工资' in content or '雇佣' in content:
                    target_shard = 'legal_clauses_labor'
                elif '公司' in content or '股权' in content or '股东' in content:
                    target_shard = 'legal_clauses_corporate'
                elif '房产' in content or '土地' in content or '财产' in content:
                    target_shard = 'legal_clauses_property'

                # 添加分片信息到payload
                point.payload['_shard_source'] = 'legal_clauses'
                point.payload['_migrated_at'] = datetime.now().isoformat()

                # 插入到目标分片
                client.upsert(
                    collection_name=target_shard,
                    points=[PointStruct(
                        id=point.id,
                        vector=point.vector,
                        payload=point.payload
                    )]
                )

                migrated_count += 1
                pbar.update(1)

            offset = next_offset
            if offset is None:
                break

            # 短暂休息
            time.sleep(0.1)

    logger.info(f"  ✅ 迁移完成: {migrated_count:,} 条数据")

    return migrated_count

def verify_migration():
    """验证迁移结果"""
    client = QdrantClient('http://localhost:6333')

    logger.info('✅ 验证迁移结果...')

    shard_collections = [
        'legal_clauses_contract',
        'legal_clauses_ip',
        'legal_clauses_tort',
        'legal_clauses_labor',
        'legal_clauses_corporate',
        'legal_clauses_property'
    ]

    total_in_shards = 0

    for shard in shard_collections:
        try:
            count = client.count(shard).count
            total_in_shards += count
            logger.info(f"  • {shard:30} : {count:>10,} vectors")
        except:
            logger.info(f"  • {shard:30} : {'不存在':>10}")

    original_count = client.count('legal_clauses').count

    logger.info(f"\n📊 迁移统计:")
    logger.info(f"  原始legal_clauses: {original_count:,}")
    logger.info(f"  分片总计: {total_in_shards:,}")
    logger.info(f"  迁移率: {(total_in_shards/original_count*100):.2f}%")

    return total_in_shards

def main():
    logger.info('🚀 开始legal_clauses分片优化...')

    # 1. 创建分片集合
    shards = create_sharded_collections()

    # 2. 分析内容分布
    category_count = analyze_legal_clauses_content()

    # 3. 迁移数据
    migrated = migrate_to_shards()

    # 4. 验证结果
    verify_migration()

    logger.info("\n✅ 分片优化完成！")
    logger.info('下一步：')
    logger.info('  1. 验证新分片的查询功能')
    logger.info('  2. 更新应用查询逻辑以使用分片')
    logger.info('  3. 考虑是否删除原legal_clauses集合')

if __name__ == '__main__':
    main()