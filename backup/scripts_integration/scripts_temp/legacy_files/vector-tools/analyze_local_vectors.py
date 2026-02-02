#!/usr/bin/env python3
"""
分析本地存储的向量数据
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

def analyze_vector_data():
    """分析向量数据"""
    logger.info('📊 Athena向量数据分析')
    logger.info(str('=' * 60))
    logger.info(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 数据目录
    data_path = Path('/Users/xujian/Athena工作平台/data')

    # 分析各个目录的向量文件
    vector_sources = {}

    # 1. Qdrant存储目录
    qdrant_path = data_path / 'vectors_qdrant'
    if qdrant_path.exists():
        collections_path = qdrant_path / 'collections'
        if collections_path.exists():
            collections = [d for d in collections_path.iterdir() if d.is_dir() and d.name != 'qdrant']
            for col in collections:
                vector_sources[f"Qdrant_{col.name}"] = {
                    'type': 'Qdrant集合',
                    'path': str(col),
                    'vectors': count_qdrant_vectors(str(col))
                }

    # 2. 原始向量文件
    embeddings_path = data_path / 'vectors_qdrant' / 'embeddings'
    if embeddings_path.exists():
        for json_file in embeddings_path.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 统计向量数量
                    if isinstance(data, dict):
                        vectors = 0
                        if 'vectors' in data:
                            vectors = len(data['vectors'])
                        elif isinstance(data, list):
                            vectors = len(data)

                        vector_sources[f"Raw_{json_file.stem}"] = {
                            'type': '原始向量文件',
                            'path': str(json_file),
                            'vectors': vectors,
                            'size': os.path.getsize(json_file)
                        }
            except Exception as e:
                logger.info(f"  ⚠️ 读取文件失败 {json_file}: {e}")

    # 3. 技术术语向量文件
    technical_path = data_path / 'technical_vectors' / 'raw_vectors'
    if technical_path.exists():
        if os.path.exists(os.path.join(technical_path, 'technical_term_vectors.json')):
            try:
                with open(os.path.join(technical_path, 'technical_term_vectors.json'), 'r') as f:
                    data = json.load(f)
                    vector_sources['technical_terms'] = {
                        'type': '技术术语向量',
                        'path': str(technical_path),
                        'vectors': len(data.get('vectors', {})),
                        'dimension': data.get('dimension', 'unknown')
                    }
            except Exception as e:
                logger.info(f"  ⚠️ 读取技术术语向量失败: {e}")

    # 显示统计结果
    logger.info(f"📚 发现 {len(vector_sources)} 个向量数据源:\n")

    total_vectors = 0
    categorized = {
        'Qdrant集合': {'count': 0, 'vectors': 0},
        '原始文件': {'count': 0, 'vectors': 0},
        '技术术语': {'count': 0, 'vectors': 0}
    }

    for name, info in vector_sources.items():
        logger.info(f"\n{name}:")
        logger.info(f"  类型: {info['type']}")
        logger.info(f"  路径: {info.get('path', 'N/A')}")
        logger.info(f"  向量数: {info['vectors']:,}")
        if 'dimension' in info:
            logger.info(f"  维度: {info['dimension']}")
        if 'size' in info:
            logger.info(f"  文件大小: {info['size']/1024/1024:.2f} MB")

        total_vectors += info['vectors']

        # 分类统计
        if 'Qdrant' in name:
            categorized['Qdrant集合']['count'] += 1
            categorized['Qdrant集合']['vectors'] += info['vectors']
        elif 'Raw' in name:
            categorized['原始文件']['count'] += 1
            categorized['原始文件']['vectors'] += info['vectors']
        elif 'technical' in name:
            categorized['技术术语']['count'] += 1
            categorized['技术术语']['vectors'] += info['vectors']

    # 统计汇总
    logger.info(f"\n📈 统计汇总:")
    logger.info(f"  • 总向量数量: {total_vectors:,}")

    logger.info(f"\n📂 分类统计:")
    for category, stats in categorized.items():
        if stats['count'] > 0:
            logger.info(f"  • {category}:")
            logger.info(f"    - 数据源数: {stats['count']}")
            logger.info(f"    - 向量数: {stats['vectors']:,}")

    # 分析原始JSON文件
    logger.info(f"\n🔍 原始向量文件分析:")
    analyze_raw_json_files()

    # 存储建议
    logger.info(f"\n💡 存储建议:")
    if total_vectors < 1000:
        logger.info('  • 向量数量较少，系统运行效率高')
    elif total_vectors < 10000:
        logger.info('  • 向量数量适中，建议定期清理过期数据')
    else:
        logger.info('  • 向量数量较大，建议:')
        logger.info('    - 实施分片存储')
        logger.info('    - 使用增量更新策略')
        logger.info('    - 定期备份重要数据')

    logger.info(f"\n🎯 使用建议:")
    logger.info('  1. Qdrant集合用于实时向量检索')
    logger.info('  2. 原始JSON文件作为数据备份')
    logger.info('  3. 技术术语向量用于语义理解')

def count_qdrant_vectors(collection_path):
    """统计Qdrant集合中的向量数量"""
    vector_count = 0

    # 遍历segment目录
    segments_path = Path(collection_path) / '0' / 'segments'
    if segments_path.exists():
        for segment in segments_path.iterdir():
            if segment.is_dir():
                # 检查vector_storage目录
                vector_storage = segment / 'vector_storage' / 'vectors'
                if vector_storage.exists():
                    config_file = vector_storage / 'config.json'
                    if config_file.exists():
                        try:
                            with open(config_file, 'r') as f:
                                config = json.load(f)
                                vector_count += config.get('vector_count', 0)
                        except:
                            pass

    return vector_count

def analyze_raw_json_files():
    """分析原始JSON向量文件"""
    raw_files = [
        'ai_terminology_vectors_20251205_104422.json',
        'technical_terms_comprehensive.json',
        'ai_terminology_all_parsed.json'
    ]

    for filename in raw_files:
        file_path = Path(f"/Users/xujian/Athena工作平台/data/vectors_qdrant/embeddings/{filename}")
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    if isinstance(data, dict):
                        if 'vectors' in data:
                            vectors = data['vectors']
                            logger.info(f"  • {filename}: {len(vectors)} 个向量")
                            if vectors:
                                # 检查第一个向量的维度
                                first_vector = list(vectors.values())[0] if vectors else []
                                if isinstance(first_vector, list):
                                    logger.info(f"    - 向量维度: {len(first_vector)}")
                        elif isinstance(data, list):
                            logger.info(f"  • {filename}: {len(data)} 个向量对象")
                            if data:
                                first_item = data[0]
                                if isinstance(first_item, dict) and 'embedding' in first_item:
                                    embedding = first_item.get('embedding', [])
                                    if embedding:
                                        logger.info(f"    - 嵌入维度: {len(embedding)}")
            except Exception as e:
                logger.info(f"  ⚠️ 分析 {filename} 失败: {e}")

if __name__ == '__main__':
    analyze_vector_data()