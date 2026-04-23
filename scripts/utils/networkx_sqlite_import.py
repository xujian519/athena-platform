#!/usr/bin/env python3
"""
NetworkX + SQLite 知识图谱导入脚本
轻量级本地解决方案
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)

class NetworkXSQLiteImporter:
    def __init__(self, db_path: str = '/tmp/knowledge_graph.db'):
        self.db_path = db_path
        self.graph = nx.MultiDiGraph()
        self.init_database()

    def init_database(self) -> Any:
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                entity_type TEXT,
                confidence REAL,
                source TEXT,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                target_id INTEGER,
                relation_type TEXT,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES entities (id),
                FOREIGN KEY (target_id) REFERENCES entities (id)
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type)')

        conn.commit()
        conn.close()

    def import_json_graph(self, json_file: Path, graph_name: str) -> Any:
        """从JSON导入知识图谱"""
        with open(json_file, encoding='utf-8') as f:
            data = json.load(f)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建图的命名空间
        cursor.execute('INSERT INTO entities (name, entity_type) VALUES (?, ?)',
                       (f"graph:{graph_name}', 'graph_namespace"))

        # 导入实体
        entity_id_map = {}
        for entity in data.get('entities', []):
            cursor.execute('''
                INSERT INTO entities (name, entity_type, confidence, source, properties)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                entity.get('name'),
                entity.get('entity_type'),
                entity.get('confidence'),
                entity.get('source'),
                json.dumps(entity)
            ))

            entity_id = cursor.lastrowid
            entity_id_map[entity.get('name')] = entity_id

            # 添加到NetworkX图
            self.graph.add_node(entity_id, **entity)

        # 导入关系
        for relation in data.get('relations', []):
            source_name = relation.get('source')
            target_name = relation.get('target')

            if source_name in entity_id_map and target_name in entity_id_map:
                source_id = entity_id_map[source_name]
                target_id = entity_id_map[target_name]

                cursor.execute('''
                    INSERT INTO relations (source_id, target_id, relation_type, properties)
                    VALUES (?, ?, ?, ?)
                ''', (
                    source_id,
                    target_id,
                    relation.get('relation_type'),
                    json.dumps(relation)
                ))

                # 添加到NetworkX图
                self.graph.add_edge(source_id, target_id, relation_type=relation.get('relation_type'))

        conn.commit()
        conn.close()
        logger.info(f"✅ 成功导入到SQLite: {graph_name}")

    def query_entity(self, entity_name: str) -> list[dict]:
        """查询实体"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM entities WHERE name LIKE ?
        ''', (f"%{entity_name}%",))

        results = cursor.fetchall()
        conn.close()

        columns = ['id', 'name', 'entity_type', 'confidence', 'source', 'properties', 'created_at']
        return [dict(zip(columns, row, strict=False)) for row in results]

    def get_graph_statistics(self) -> dict:
        """获取图统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM entities')
        entity_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM relations')
        relation_count = cursor.fetchone()[0]

        conn.close()

        return {
            'entities': entity_count,
            'relations': relation_count,
            'networkx_nodes': len(self.graph.nodes()),
            'networkx_edges': len(self.graph.edges())
        }

# 使用示例
if __name__ == '__main__':
    importer = NetworkXSQLiteImporter()

    # 导入法律知识图谱
    importer.import_json_graph(
        Path('/Users/xujian/Athena工作平台/data/knowledge_graph_neo4j/processed_data/unified_legal_knowledge_graph.json'),
        'legal'
    )

    # 查询统计信息
    stats = importer.get_graph_statistics()
    logger.info(f"图统计信息: {stats}")

    # 查询示例
    results = importer.query_entity('民法典')
    logger.info(f"查询结果: {results}")
