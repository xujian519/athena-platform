#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析Neo4j中的知识图谱类型和用途
"""

import json
import logging
import os
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

def analyze_neo4j_knowledge_graphs():
    """分析Neo4j中的知识图谱"""

    if not NEO4J_AVAILABLE:
        logger.info('❌ Neo4j库未安装')
        return {}

    try:
        driver = GraphDatabase.driver(
            'bolt://localhost:7687',
            auth=('neo4j', 'password')
        )

        with driver.session(database='neo4j') as session:
            # 获取所有节点标签
            labels_query = """
            CALL db.labels() YIELD label
            RETURN label
            """
            labels_result = session.run(labels_query)
            labels = [record['label'] for record in labels_result]

            # 获取所有关系类型
            rel_types_query = """
            CALL db.relationshipTypes() YIELD relationshipType
            RETURN relationshipType
            """
            rel_types_result = session.run(rel_types_query)
            rel_types = [record['relationshipType'] for record in rel_types_result]

            # 分析每种标签的节点数量和属性
            label_analysis = {}
            for label in labels:
                count_query = f"MATCH (n:`{label}`) RETURN count(n) as count"
                count_result = session.run(count_query).single()
                count = count_result['count']

                # 获取样例节点和属性
                sample_query = f"MATCH (n:`{label}`) RETURN n LIMIT 3"
                sample_result = list(session.run(sample_query))

                properties = set()
                samples = []
                for record in sample_result:
                    node = record['n']
                    properties.update(node.keys())
                    samples.append(dict(node))

                label_analysis[label] = {
                    'count': count,
                    'properties': list(properties),
                    'samples': samples
                }

            # 分析每种关系类型
            rel_analysis = {}
            for rel_type in rel_types:
                count_query = f"MATCH ()-[r:`{rel_type}`]->() RETURN count(r) as count"
                count_result = session.run(count_query).single()
                count = count_result['count']

                # 获取样例关系和属性
                sample_query = f"MATCH ()-[r:`{rel_type}`]->() RETURN r LIMIT 3"
                sample_result = list(session.run(sample_query))

                properties = set()
                samples = []
                for record in sample_result:
                    rel = record['r']
                    properties.update(rel.keys())
                    samples.append(dict(rel))

                rel_analysis[rel_type] = {
                    'count': count,
                    'properties': list(properties),
                    'samples': samples
                }

            driver.close()

            return {
                'labels': label_analysis,
                'relationships': rel_analysis,
                'total_labels': len(labels),
                'total_relationship_types': len(rel_types)
            }

    except Exception as e:
        logger.info(f"❌ 分析Neo4j失败: {e}")
        return {}

if __name__ == '__main__':
    logger.info('🔍 分析Neo4j知识图谱...')
    result = analyze_neo4j_knowledge_graphs()

    if result:
        logger.info("\n📊 Neo4j知识图谱分析结果:")
        logger.info(f"  节点标签数量: {result['total_labels']}")
        logger.info(f"  关系类型数量: {result['total_relationship_types']}")

        logger.info("\n🏷️ 节点标签详情:")
        for label, info in result['labels'].items():
            logger.info(f"  - {label}: {info['count']}个节点")
            if info['properties']:
                logger.info(f"    属性: {', '.join(info['properties'])}")

        logger.info("\n🔗 关系类型详情:")
        for rel_type, info in result['relationships'].items():
            logger.info(f"  - {rel_type}: {info['count']}个关系")
            if info['properties']:
                logger.info(f"    属性: {', '.join(info['properties'])}")

        # 保存分析结果 - 简化版本避免序列化问题
        simplified_result = {
            'labels': {k: {'count': v['count'], 'properties': v['properties']} for k, v in result['labels'].items()},
            'relationships': {k: {'count': v['count'], 'properties': v['properties']} for k, v in result['relationships'].items()},
            'total_labels': len(result['labels']),
            'total_relationship_types': len(result['relationships'])
        }

        with open('/Users/xujian/Athena工作平台/.runtime/neo4j_knowledge_graph_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(simplified_result, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 分析结果已保存")