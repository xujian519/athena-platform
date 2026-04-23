#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite知识图谱管理器
SQLite Knowledge Graph Manager

完整的知识图谱SQLite数据库管理、查询和分析系统
"""

import json
import logging
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SQLiteKnowledgeGraphManager:
    """SQLite知识图谱管理器"""

    def __init__(self, db_path: str = '/tmp/knowledge_graph.db'):
        """
        初始化知识图谱管理器

        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = db_path
        self.connection = None
        self.lock = threading.Lock()

        logger.info(f"🗄️ 初始化SQLite知识图谱管理器: {db_path}")

    def connect(self):
        """连接到数据库"""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None  # 自动提交模式
            )

            # 启用WAL模式提高并发性能
            self.connection.execute('PRAGMA journal_mode=WAL')
            self.connection.execute('PRAGMA synchronous=NORMAL')
            self.connection.execute('PRAGMA cache_size=10000')
            self.connection.execute('PRAGMA temp_store=MEMORY')

            logger.info('✅ SQLite知识图谱数据库连接成功')
            return True

        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False

    def initialize_schema(self):
        """初始化数据库结构"""
        with self.lock:
            try:
                cursor = self.connection.cursor()

                # 创建实体表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS entities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        entity_type TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        source TEXT,
                        properties TEXT,  -- JSON格式存储额外属性
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 创建关系表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS relations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_id INTEGER NOT NULL,
                        target_id INTEGER NOT NULL,
                        relation_type TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        properties TEXT,  -- JSON格式存储额外属性
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (source_id) REFERENCES entities (id),
                        FOREIGN KEY (target_id) REFERENCES entities (id)
                    )
                """)

                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_type ON entities (entity_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_name ON entities (name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_relations_source ON relations (source_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_relations_target ON relations (target_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_relations_type ON relations (relation_type)')

                # 创建全文搜索索引
                cursor.execute('CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(name, properties)')

                # 创建统计信息表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS graph_stats (
                        id INTEGER PRIMARY KEY,
                        total_entities INTEGER DEFAULT 0,
                        total_relations INTEGER DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                self.connection.commit()
                logger.info('✅ 数据库结构初始化完成')
                return True

            except Exception as e:
                logger.error(f"❌ 数据库结构初始化失败: {e}")
                return False

    def add_entity(self, name: str, entity_type: str, confidence: float = 1.0,
                   source: str = None, properties: Dict = None) -> int:
        """
        添加实体

        Args:
            name: 实体名称
            entity_type: 实体类型
            confidence: 置信度
            source: 数据来源
            properties: 额外属性

        Returns:
            实体ID
        """
        with self.lock:
            try:
                cursor = self.connection.cursor()

                props_json = json.dumps(properties, ensure_ascii=False) if properties else None

                cursor.execute("""
                    INSERT INTO entities (name, entity_type, confidence, source, properties)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, entity_type, confidence, source, props_json))

                entity_id = cursor.lastrowid
                self.connection.commit()

                # 更新全文搜索索引
                cursor.execute("""
                    INSERT INTO entities_fts (rowid, name, properties)
                    VALUES (?, ?, ?)
                """, (entity_id, name, props_json))

                logger.debug(f"➕ 添加实体: {name} ({entity_type}) - ID: {entity_id}")
                return entity_id

            except Exception as e:
                logger.error(f"❌ 添加实体失败: {e}")
                return -1

    def add_relation(self, source_id: int, target_id: int, relation_type: str,
                    confidence: float = 1.0, properties: Dict = None) -> int:
        """
        添加关系

        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            confidence: 置信度
            properties: 额外属性

        Returns:
            关系ID
        """
        with self.lock:
            try:
                cursor = self.connection.cursor()

                props_json = json.dumps(properties, ensure_ascii=False) if properties else None

                cursor.execute("""
                    INSERT INTO relations (source_id, target_id, relation_type, confidence, properties)
                    VALUES (?, ?, ?, ?, ?)
                """, (source_id, target_id, relation_type, confidence, props_json))

                relation_id = cursor.lastrowid
                self.connection.commit()

                logger.debug(f"🔗 添加关系: {source_id} -> {target_id} ({relation_type}) - ID: {relation_id}")
                return relation_id

            except Exception as e:
                logger.error(f"❌ 添加关系失败: {e}")
                return -1

    def search_entities(self, query: str, entity_type: str = None,
                        limit: int = 100) -> List[Dict]:
        """
        搜索实体

        Args:
            query: 搜索查询
            entity_type: 实体类型过滤
            limit: 结果限制

        Returns:
            实体列表
        """
        try:
            cursor = self.connection.cursor()

            if entity_type:
                cursor.execute("""
                    SELECT id, name, entity_type, confidence, source, properties
                    FROM entities
                    WHERE entity_type = ? AND (name LIKE ? OR properties LIKE ?)
                    ORDER BY confidence DESC
                    LIMIT ?
                """, (entity_type, f"%{query}%", f"%{query}%", limit))
            else:
                # 使用全文搜索
                cursor.execute("""
                    SELECT e.id, e.name, e.entity_type, e.confidence, e.source, e.properties
                    FROM entities e
                    JOIN entities_fts fts ON e.id = fts.rowid
                    WHERE entities_fts MATCH ?
                    ORDER BY e.confidence DESC
                    LIMIT ?
                """, (query, limit))

            results = []
            for row in cursor.fetchall():
                entity = {
                    'id': row[0],
                    'name': row[1],
                    'entity_type': row[2],
                    'confidence': row[3],
                    'source': row[4],
                    'properties': json.loads(row[5]) if row[5] else {}
                }
                results.append(entity)

            return results

        except Exception as e:
            logger.error(f"❌ 搜索实体失败: {e}")
            return []

    def get_entity_relations(self, entity_id: int, relation_type: str = None,
                           direction: str = 'both') -> List[Dict]:
        """
        获取实体的关系

        Args:
            entity_id: 实体ID
            relation_type: 关系类型过滤
            direction: 方向 (outgoing/incoming/both)

        Returns:
            关系列表
        """
        try:
            cursor = self.connection.cursor()
            results = []

            if direction in ['outgoing', 'both']:
                # 出向关系
                if relation_type:
                    cursor.execute("""
                        SELECT r.id, r.target_id, e.name as target_name, e.entity_type as target_type,
                               r.relation_type, r.confidence, r.properties
                        FROM relations r
                        JOIN entities e ON r.target_id = e.id
                        WHERE r.source_id = ? AND r.relation_type = ?
                    """, (entity_id, relation_type))
                else:
                    cursor.execute("""
                        SELECT r.id, r.target_id, e.name as target_name, e.entity_type as target_type,
                               r.relation_type, r.confidence, r.properties
                        FROM relations r
                        JOIN entities e ON r.target_id = e.id
                        WHERE r.source_id = ?
                    """, (entity_id,))

                for row in cursor.fetchall():
                    relation = {
                        'id': row[0],
                        'target_id': row[1],
                        'target_name': row[2],
                        'target_type': row[3],
                        'relation_type': row[4],
                        'confidence': row[5],
                        'properties': json.loads(row[6]) if row[6] else {},
                        'direction': 'outgoing'
                    }
                    results.append(relation)

            if direction in ['incoming', 'both']:
                # 入向关系
                if relation_type:
                    cursor.execute("""
                        SELECT r.id, r.source_id, e.name as source_name, e.entity_type as source_type,
                               r.relation_type, r.confidence, r.properties
                        FROM relations r
                        JOIN entities e ON r.source_id = e.id
                        WHERE r.target_id = ? AND r.relation_type = ?
                    """, (entity_id, relation_type))
                else:
                    cursor.execute("""
                        SELECT r.id, r.source_id, e.name as source_name, e.entity_type as source_type,
                               r.relation_type, r.confidence, r.properties
                        FROM relations r
                        JOIN entities e ON r.source_id = e.id
                        WHERE r.target_id = ?
                    """, (entity_id,))

                for row in cursor.fetchall():
                    relation = {
                        'id': row[0],
                        'source_id': row[1],
                        'source_name': row[2],
                        'source_type': row[3],
                        'relation_type': row[4],
                        'confidence': row[5],
                        'properties': json.loads(row[6]) if row[6] else {},
                        'direction': 'incoming'
                    }
                    results.append(relation)

            return results

        except Exception as e:
            logger.error(f"❌ 获取实体关系失败: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """获取图数据库统计信息"""
        try:
            cursor = self.connection.cursor()

            # 基本统计
            cursor.execute('SELECT COUNT(*) FROM entities')
            total_entities = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM relations')
            total_relations = cursor.fetchone()[0]

            # 实体类型分布
            cursor.execute("""
                SELECT entity_type, COUNT(*) as count
                FROM entities
                GROUP BY entity_type
                ORDER BY count DESC
                LIMIT 10
            """)
            entity_types = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]

            # 关系类型分布
            cursor.execute("""
                SELECT relation_type, COUNT(*) as count
                FROM relations
                GROUP BY relation_type
                ORDER BY count DESC
                LIMIT 10
            """)
            relation_types = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]

            # 更新统计表
            cursor.execute("""
                INSERT OR REPLACE INTO graph_stats (id, total_entities, total_relations, last_updated)
                VALUES (1, ?, ?, ?)
            """, (total_entities, total_relations, datetime.now()))

            stats = {
                'total_entities': total_entities,
                'total_relations': total_relations,
                'entity_types': entity_types,
                'relation_types': relation_types,
                'last_updated': datetime.now().isoformat()
            }

            return stats

        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {}

    def find_path(self, source_id: int, target_id: int, max_depth: int = 5) -> List[List[int]:
        """
        查找两个实体之间的路径

        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            max_depth: 最大搜索深度

        Returns:
            路径列表
        """
        try:
            cursor = self.connection.cursor()

            # 使用递归CTE查找路径
            cursor.execute("""
                WITH RECURSIVE path (start_id, end_id, depth, path_str) AS (
                    SELECT ?, ?, 0, CAST(? AS TEXT)
                    UNION ALL
                    SELECT
                        p.start_id,
                        r.target_id as end_id,
                        p.depth + 1,
                        p.path_str || '->' || CAST(r.target_id AS TEXT)
                    FROM path p
                    JOIN relations r ON p.end_id = r.source_id
                    WHERE p.depth < ? AND r.target_id != p.start_id
                )
                SELECT path_str FROM path WHERE end_id = ? AND depth <= ?
            """, (source_id, source_id, source_id, max_depth, target_id, max_depth))

            paths = []
            for row in cursor.fetchall():
                path = [int(x) for x in row[0].split('->')]
                paths.append(path)

            return paths

        except Exception as e:
            logger.error(f"❌ 查找路径失败: {e}")
            return []

    def export_subgraph(self, center_id: int, radius: int = 2) -> Dict[str, Any]:
        """
        导出子图

        Args:
            center_id: 中心实体ID
            radius: 半径

        Returns:
            子图数据
        """
        try:
            cursor = self.connection.cursor()

            # 使用递归CTE查找指定半径内的所有节点和边
            cursor.execute("""
                WITH RECURSIVE neighbors (entity_id, depth) AS (
                    SELECT ?, 0
                    UNION ALL
                    SELECT
                        CASE
                            WHEN d.depth % 2 = 0 THEN r.target_id
                            ELSE r.source_id
                        END as entity_id,
                        (d.depth + 1) / 2 as depth
                    FROM neighbors d
                    JOIN relations r ON (
                        (d.depth % 2 = 0 AND d.entity_id = r.source_id) OR
                        (d.depth % 2 = 1 AND d.entity_id = r.target_id)
                    )
                    WHERE (d.depth + 1) / 2 <= ? * 2
                )
                SELECT DISTINCT entity_id FROM neighbors WHERE depth <= ?
            """, (center_id, radius, radius))

            entity_ids = [row[0] for row in cursor.fetchall()]

            # 获取实体信息
            placeholders = ','.join(['?'] * len(entity_ids))
        # TODO: 检查SQL注入风险 - cursor.execute(f"""
                    cursor.execute(f"""
                SELECT id, name, entity_type, confidence, source, properties
                FROM entities
                WHERE id IN ({placeholders})
            """, entity_ids)

            entities = {}
            for row in cursor.fetchall():
                entities[row[0] = {
                    'id': row[0],
                    'name': row[1],
                    'entity_type': row[2],
                    'confidence': row[3],
                    'source': row[4],
                    'properties': json.loads(row[5]) if row[5] else {}
                }

            # 获取关系信息
        # TODO: 检查SQL注入风险 - cursor.execute(f"""
                    cursor.execute(f"""
                SELECT r.source_id, r.target_id, r.relation_type, r.confidence, r.properties
                FROM relations r
                WHERE r.source_id IN ({placeholders}) AND r.target_id IN ({placeholders})
            """, entity_ids + entity_ids)

            relations = []
            for row in cursor.fetchall():
                relation = {
                    'source_id': row[0],
                    'target_id': row[1],
                    'relation_type': row[2],
                    'confidence': row[3],
                    'properties': json.loads(row[4]) if row[4] else {}
                }
                relations.append(relation)

            subgraph = {
                'center_id': center_id,
                'radius': radius,
                'entities': entities,
                'relations': relations,
                'statistics': {
                    'entity_count': len(entities),
                    'relation_count': len(relations)
                }
            }

            return subgraph

        except Exception as e:
            logger.error(f"❌ 导出子图失败: {e}")
            return {}

    def optimize_database(self):
        """优化数据库性能"""
        try:
            cursor = self.connection.cursor()

            # 重建索引
            cursor.execute('REINDEX')

            # 分析表统计信息
            cursor.execute('ANALYZE')

            # 清理数据库
            cursor.execute('VACUUM')

            logger.info('✅ 数据库优化完成')
            return True

        except Exception as e:
            logger.error(f"❌ 数据库优化失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info('🔒 数据库连接已关闭')

# 全局知识图谱管理器实例
kg_manager = None

def get_knowledge_graph_manager(db_path: str = '/tmp/knowledge_graph.db') -> SQLiteKnowledgeGraphManager:
    """获取知识图谱管理器单例"""
    global kg_manager
    if kg_manager is None:
        kg_manager = SQLiteKnowledgeGraphManager(db_path)
        if not kg_manager.connect():
            raise RuntimeError('无法连接到知识图谱数据库')
        if not kg_manager.initialize_schema():
            raise RuntimeError('无法初始化知识图谱数据库结构')
    return kg_manager

if __name__ == '__main__':
    # 测试代码
    manager = get_knowledge_graph_manager()

    # 获取统计信息
    stats = manager.get_statistics()
    logger.info('📊 知识图谱统计信息:')
    logger.info(f"   实体总数: {stats.get('total_entities', 0)}")
    logger.info(f"   关系总数: {stats.get('total_relations', 0)}")
    logger.info(f"   实体类型: {len(stats.get('entity_types', []))}")
    logger.info(f"   关系类型: {len(stats.get('relation_types', []))}")

    # 搜索测试
    results = manager.search_entities('法律', limit=5)
    logger.info(f"\n🔍 搜索'法律'结果: {len(results)}个")
    for entity in results[:3]:
        logger.info(f"   {entity['name']} ({entity['entity_type']})")

    manager.close()