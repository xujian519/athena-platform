#!/usr/bin/env python3
"""
ArangoDB知识图谱导入脚本
"""

import json
import logging
from pathlib import Path

from arango import ArangoClient

logger = logging.getLogger(__name__)

class ArangoDBImporter:
    def __init__(self, host='http://localhost:8529', username='root', password=''):
        self.client = ArangoClient(hosts=host)
        self.username = username
        self.password = password

    def connect(self):
        """连接到ArangoDB"""
        self.db = self.client.db('_system', username=self.username, password=self.password)

    def import_knowledge_graph(self, json_file: Path, graph_name: str):
        """导入知识图谱到ArangoDB"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 创建数据库
        if not self.db.has_database(graph_name):
            self.db.create_database(graph_name)

        graph_db = self.client.db(graph_name, username=self.username, password=self.password)

        # 创建集合
        if not graph_db.has_collection('entities'):
            entities = graph_db.create_collection('entities')
        else:
            entities = graph_db.collection('entities')

        if not graph_db.has_collection('relations'):
            relations = graph_db.create_collection('relations')
        else:
            relations = graph_db.collection('relations')

        # 导入实体
        for entity in data.get('entities', []):
            entities.insert(entity)

        # 导入关系
        for relation in data.get('relations', []):
            relations.insert(relation)

        logger.info(f"✅ 成功导入到ArangoDB: {graph_name}")

# 使用示例
if __name__ == '__main__':
    importer = ArangoDBImporter(password='your_password')
    importer.connect()

    # 导入法律知识图谱
    importer.import_knowledge_graph(
        Path('/Users/xujian/Athena工作平台/data/knowledge_graph_neo4j/processed_data/unified_legal_knowledge_graph.json'),
        'legal_knowledge_graph'
    )