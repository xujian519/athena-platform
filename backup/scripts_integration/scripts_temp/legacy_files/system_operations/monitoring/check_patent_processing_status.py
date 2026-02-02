#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查专利处理完成情况
"""

import glob
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def main():
    """主函数"""
    logger.info(str('=' * 60))
    logger.info('专利处理完成情况检查')
    logger.info(str('=' * 60))

    # 1. 原始专利文档统计
    patent_dir = Path('/Users/xujian/学习资料/专利')
    patent_files = list(patent_dir.rglob('*'))
    patent_docs = [f for f in patent_files if f.is_file()]

    logger.info(f"\n📁 原始专利文档统计:")
    logger.info(f"  总文档数: {len(patent_docs):,}")

    # 按类型分类
    by_type = {}
    for file_path in patent_docs:
        ext = file_path.suffix.lower()
        if ext not in by_type:
            by_type[ext] = 0
        by_type[ext] += 1

    logger.info(f"  按类型分布:")
    for ext, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"    {ext:<10} {count:>10,} 个")

    # 2. 处理后的批次文件
    batch_dir = Path('/Users/xujian/Athena工作平台/data/knowledge_graph_neo4j/raw_data/patent_kg_superfast')
    batch_files = sorted(batch_dir.glob('batch_*.json'))

    logger.info(f"\n📊 已处理的批次文件:")
    logger.info(f"  批次文件数: {len(batch_files):,}")

    # 统计处理结果
    total_patents = 0
    total_triples = 0
    processed_patents = set()

    logger.info(f"\n📈 处理结果统计:")
    for i, batch_file in enumerate(batch_files, 1):
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                if 'patents' in data:
                    batch_patents = len(data['patents'])
                    total_patents += batch_patents

                    # 记录已处理的专利ID
                    for patent in data['patents']:
                        if 'id' in patent:
                            processed_patents.add(patent['id'])
                        elif 'doc_id' in patent:
                            processed_patents.add(patent['doc_id'])

                if 'all_triples' in data:
                    batch_triples = len(data['all_triples'])
                    total_triples += batch_triples
                else:
                    batch_triples = 0

                # 显示前5个和最后5个批次
                if i <= 5 or i >= len(batch_files) - 5:
                    range_str = '前5个' if i <= 5 else f"最后{len(batch_files)-i+1}个"
                    logger.info(f"  {range_str}批次 {batch_file.name:<15} 专利:{batch_patents:>5,}  三元组:{batch_triples:>6,}")

        except Exception as e:
            logger.info(f"  ❌ 批次文件 {batch_file.name} 读取失败: {e}")

    # 3. 汇总统计
    logger.info(f"\n📋 处理汇总:")
    logger.info(f"  原始文档总数: {len(patent_docs):,}")
    logger.info(f"  实际处理文档数: {len(processed_patents):,}")
    logger.info(f"  生成批次文件数: {len(batch_files):,}")
    logger.info(f"  知识图谱三元组数: {total_triples:,}")

    # 计算处理率（假设文档数就是需要处理的专利数）
    if len(patent_docs) > 0:
        processing_rate = len(processed_patents) / len(patent_docs) * 100
        logger.info(f"  处理完成率: {processing_rate:.1f}%")

    # 4. 导入Neo4j的状态
    logger.info(f"\n🔗 Neo4j导入状态:")
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

        with driver.session() as session:
            # 尝试简单的查询
            result = session.run('MATCH (p:Patent) RETURN count(p) as count LIMIT 1')
            record = result.single()
            if record:
                patent_nodes = record['count']
                logger.info(f"  Neo4j中专利节点数: {patent_nodes:,}")
            else:
                logger.info(f"  Neo4j中暂无专利节点")

        driver.close()
    except Exception as e:
        logger.info(f"  ❌ Neo4j连接失败: {e}")
        logger.info(f"  建议检查Neo4j服务状态")

    # 5. 状态判断
    logger.info(f"\n✅ 处理状态:")
    if len(processed_patents) == len(patent_docs):
        logger.info('  🎉 所有专利文档都已处理完成！')
        logger.info(f"  📊 成功生成 {len(batch_files)} 个批次文件")
        logger.info(f"  🔗 包含 {total_triples:,} 个知识图谱关系")
    elif len(processed_patents) > 0:
        remaining = len(patent_docs) - len(processed_patents)
        logger.info(f"  ⏳ 处理中...")
        logger.info(f"  ✅ 已处理: {len(processed_patents):,}")
        logger.info(f"  ⏳ 待处理: {remaining:,}")
        logger.info(f"  📊 完成度: {len(processed_patents)/len(patent_docs)*100:.1f}%")
    else:
        logger.info('  ❌ 暂无处理记录')
        logger.info(f"  💡 请运行专利处理脚本")

    logger.info(str("\n" + '=' * 60))

if __name__ == '__main__':
    main()