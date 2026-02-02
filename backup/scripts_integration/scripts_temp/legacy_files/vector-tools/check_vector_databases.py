#!/usr/bin/env python3
"""
检查向量数据库状态和统计信息
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

def get_qdrant_collections():
    """获取Qdrant中的所有集合"""
    try:
        # 使用curl调用Qdrant API获取集合列表
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:6334/collections'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('result', {}).get('collections', [])
        else:
            logger.info('⚠️ 无法连接到Qdrant服务')
            return []
    except Exception as e:
        logger.info(f"❌ 获取Qdrant集合失败: {e}")
        return []

def get_collection_info(collection_name):
    """获取特定集合的信息"""
    try:
        result = subprocess.run(
            ['curl', '-s', f'http://localhost:6334/collections/{collection_name}'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('result', {})
        else:
            return None
    except Exception as e:
        logger.info(f"❌ 获取集合{collection_name}信息失败: {e}")
        return None

def check_qdrant_status():
    """检查Qdrant服务状态"""
    try:
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:6334/health'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('result', {}).get('status') == 'ok'
        else:
            return False
    except:
        return False

def count_local_vectors(collection_path):
    """统计本地存储的向量文件"""
    vector_count = 0
    config_files = []

    # 递归查找vector配置文件
    for root, dirs, files in os.walk(collection_path):
        for file in files:
            if file == 'config.json' and 'vector_storage' in root:
                config_files.append(os.path.join(root, file))

    # 读取配置文件获取向量数量
    for config_file in config_files:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                vector_count += config.get('vector_count', 0)
        except Exception as e:
            logger.info(f"  ⚠️ 读取配置文件失败 {config_file}: {e}")

    return vector_count

def main():
    """主函数"""
    logger.info('📊 Athena向量数据库状态检查')
    logger.info(str('=' * 60))
    logger.info(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 检查Qdrant服务状态
    logger.info('🔍 Qdrant服务状态:')
    qdrant_status = check_qdrant_status()
    if qdrant_status:
        logger.info('  ✅ Qdrant服务运行中')
    else:
        logger.info('  ❌ Qdrant服务未运行')
        logger.info('  💡 请先启动Qdrant服务: ./scripts/start_qdrant.sh')
        return

    # 获取所有集合
    collections = get_qdrant_collections()
    logger.info(f"\n📚 发现 {len(collections)} 个向量数据库集合:\n")

    total_vectors = 0
    active_collections = []

    # 统计每个集合的信息
    for collection in collections:
        name = collection['name']
        info = get_collection_info(name)

        if info:
            vectors_count = info.get('vectors_count', 0)
            points_count = info.get('points_count', 0)
            status = info.get('status', 'unknown')
            config = info.get('config', {})

            dimension = config.get('params', {}).get('vector', {}).get('size', 0)
            distance = config.get('params', {}).get('vector', {}).get('distance', 'unknown')

            active_collections.append({
                'name': name,
                'vectors': vectors_count,
                'points': points_count,
                'dimension': dimension,
                'distance': distance,
                'status': status
            })

            total_vectors += vectors_count

    # 显示统计结果
    if active_collections:
        logger.info(f"{'集合名称':<30} {'向量数量':<10} {'维度':<8} {'距离度量':<12} {'状态':<10}")
        logger.info(str('-' * 80))

        for col in active_collections:
            logger.info(f"{col['name']:<30} {col['vectors']:<10} {col['dimension']:<8} {col['distance']:<12} {col['status']:<10}")
    else:
        logger.info('  ❌ 未找到活跃的集合')

    logger.info(f"\n📈 统计汇总:")
    logger.info(f"  • 总向量数量: {total_vectors:,}")
    logger.info(f"  • 活跃集合数: {len(active_collections)}")

    # 检查本地存储文件
    data_path = Path('/Users/xujian/Athena工作平台/data/vectors_qdrant/collections')
    if data_path.exists():
        logger.info(f"\n💾 本地存储检查:")
        local_dirs = [d for d in data_path.iterdir() if d.is_dir() and d.name != 'qdrant']

        for dir_path in local_dirs:
            local_count = count_local_vectors(str(dir_path))
            logger.info(f"  • {dir_path.name}: {local_count} 个向量存储文件")

    # 显示数据库详情
    logger.info("\n🗃️ 数据库详情:")

    database_details = {
        'patent_rules_unified_1024': {
            '描述': '专利规则数据库',
            '用途': '存储专利规则、审查指南和案例分析',
            '状态': '✅ 活跃'
        },
        'ai_technical_terms_vector_db': {
            '描述': 'AI技术术语库',
            '用途': 'AI相关术语、标准和规范的向量表示',
            '状态': '✅ 活跃'
        },
        'general_memory_db': {
            '描述': '通用记忆库',
            '用途': '存储通用对话和系统记忆',
            '状态': '✅ 活跃'
        },
        'legal_*': {
            '描述': '法律相关数据库',
            '用途': '法律条款、法规文档、专利法律案例',
            '状态': '✅ 活跃'
        },
        'patent_*': {
            '描述': '专利相关数据库',
            '用途': '专利无效、复审、判决等案例数据',
            '状态': '✅ 活跃'
        }
    }

    logger.info("\n按类别统计:")
    categories = {}
    for col in active_collections:
        name = col['name']
        categorized = False

        # 分类统计
        for pattern, details in database_details.items():
            if pattern == name or (pattern.endswith('*') and name.startswith(pattern[:-1])):
                category = pattern.replace('*', '')
                if category not in categories:
                    categories[category] = {'count': 0, 'vectors': 0, 'collections': []}
                categories[category]['count'] += 1
                categories[category]['vectors'] += col['vectors']
                categories[category]['collections'].append(name)
                categorized = True
                break

        if not categorized:
            if '其他' not in categories:
                categories['其他'] = {'count': 0, 'vectors': 0, 'collections': []}
            categories['其他']['count'] += 1
            categories['其他']['vectors'] += col['vectors']
            categories['其他']['collections'].append(name)

    for category, stats in categories.items():
        logger.info(f"  {category}:")
        logger.info(f"    • 集合数: {stats['count']}")
        logger.info(f"    • 向量数: {stats['vectors']:,}")
        logger.info(f"    • 集合: {', '.join(stats['collections'])}")

    # 性能建议
    logger.info("\n💡 性能建议:")
    if total_vectors < 1000:
        logger.info('  • 向量数量较少，系统响应很快')
        logger.info('  • 可以考虑导入更多数据以提升检索效果')
    elif total_vectors < 10000:
        logger.info('  • 向量数量适中，建议保持当前配置')
    else:
        logger.info('  • 向量数量较大，建议:')
        logger.info('    - 考虑分片存储')
        logger.info('    - 优化查询索引')
        logger.info('    - 定期清理过期数据')

    logger.info("\n🎯 使用建议:")
    logger.info('  1. 专利检索 → 使用 patent_rules_unified_1024')
    logger.info('  2. 技术术语查询 → 使用 ai_technical_terms_vector_db')
    logger.info('  3. 通用搜索 → 使用 general_memory_db')
    logger.info('  4. 法律咨询 → 使用 legal_* 系列数据库')

    logger.info(str("\n" + '=' * 60))
    logger.info('✅ 向量数据库检查完成！')


if __name__ == '__main__':
    main()