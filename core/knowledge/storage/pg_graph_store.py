#!/usr/bin/env python3
"""
PostgreSQL Graph Store Adapter
Provides persistence for Knowledge Graph Nodes and Relations in PostgreSQL
"""

import json
import logging
from typing import Any

from core.database.connection_pool import get_database_pool

logger = logging.getLogger(__name__)


class PGGraphStore:
    """PostgreSQL Graph Store Adapter"""

    def __init__(self, database: str = "patent_db"):
        self.db_pool = get_database_pool()
        self.database = database
        self.schema = "knowledge_graph"
        self._initialized = False

    async def initialize(self):
        """初始化图存储"""
        try:
            # 检查数据库连接
            with self._get_connection() as conn, conn.cursor() as cursor:
                cursor.execute("SELECT 1")

            # 创建schema和表(如果不存在)
            await self._ensure_schema()
            self._initialized = True
            logger.info("✅ PGGraphStore 初始化完成")
            return True
        except Exception as e:
            logger.error(f"❌ PGGraphStore 初始化失败: {e}")
            return False

    async def _ensure_schema(self):
        """确保schema和表存在"""
        try:
            # 创建schema
            self._execute(f"""
                CREATE SCHEMA IF NOT EXISTS {self.schema}
            """)

            # 创建kg_nodes表
            self._execute(f"""
                CREATE TABLE IF NOT EXISTS {self.schema}.kg_nodes (
                    id VARCHAR(255) PRIMARY KEY,
                    type VARCHAR(100) NOT NULL,
                    name VARCHAR(500) NOT NULL,
                    content TEXT,
                    properties JSONB DEFAULT '{{}}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建kg_edges表
            self._execute(f"""
                CREATE TABLE IF NOT EXISTS {self.schema}.kg_edges (
                    id VARCHAR(255) PRIMARY KEY,
                    source_id VARCHAR(255) NOT NULL,
                    target_id VARCHAR(255) NOT NULL,
                    type VARCHAR(100) NOT NULL,
                    weight FLOAT DEFAULT 1.0,
                    properties JSONB DEFAULT '{{}}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES {self.schema}.kg_nodes(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES {self.schema}.kg_nodes(id) ON DELETE CASCADE
                )
            """)

            # 创建索引
            indexes = [
                f"CREATE INDEX IF NOT EXISTS idx_kg_nodes_type ON {self.schema}.kg_nodes(type)",
                f"CREATE INDEX IF NOT EXISTS idx_kg_nodes_name ON {self.schema}.kg_nodes(name)",
                f"CREATE INDEX IF NOT EXISTS idx_kg_edges_source ON {self.schema}.kg_edges(source_id)",
                f"CREATE INDEX IF NOT EXISTS idx_kg_edges_target ON {self.schema}.kg_edges(target_id)",
                f"CREATE INDEX IF NOT EXISTS idx_kg_edges_type ON {self.schema}.kg_edges(type)",
            ]

            for index_sql in indexes:
                self._execute(index_sql)

            logger.info("✅ 知识图谱表结构创建完成")
        except Exception as e:
            logger.error(f"❌ 创建表结构失败: {e}")
            raise

    async def close(self):
        """关闭连接"""
        if self._initialized:
            # PG连接池会自动管理连接
            self._initialized = False
            logger.info("✅ PGGraphStore 连接已关闭")

    def _get_connection(self) -> Any:
        """Get database connection"""
        return self.db_pool.get_connection_context(database=self.database)

    def _execute(self, query: str, params: tuple | None = None, fetch: bool = False) -> Any:
        """Execute query helper"""
        # 验证schema名称(只允许字母、数字和下划线)
        import re

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", self.schema):
            raise ValueError(f"Invalid schema name: {self.schema}")

        with self._get_connection() as conn, conn.cursor() as cursor:
            # 安全设置search_path - schema已通过正则验证,可以安全使用
            # 使用标识符引用防止SQL注入
            cursor.execute(f'SET search_path TO "{self.schema}", public')

            cursor.execute(query, params or ())
            conn.commit()

            if fetch:
                if cursor.description:
                    return cursor.fetchall()
                return []
            return cursor.rowcount

    async def add_node(
        self,
        node_id: str,
        node_type: str,
        name: str,
        content: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Add or update a node"""
        query = """
        INSERT INTO kg_nodes (id, type, name, content, properties, updated_at)
        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO UPDATE SET
            type = EXCLUDED.type,
            name = EXCLUDED.name,
            content = EXCLUDED.content,
            properties = EXCLUDED.properties,
            updated_at = CURRENT_TIMESTAMP;
        """
        try:
            self._execute(query, (node_id, node_type, name, content, json.dumps(properties or {})))
            return True
        except Exception as e:
            logger.error(f"Failed to add node {node_id}: {e}")
            return False

    async def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        weight: float = 1.0,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Add a relation"""
        # First ensure nodes exist (optional check, but FK constraints will handle it)
        # We assume nodes are added before relations

        query = """
        INSERT INTO kg_edges (source_id, target_id, type, weight, properties)
        VALUES (%s, %s, %s, %s, %s)
        """
        try:
            self._execute(
                query, (source_id, target_id, relation_type, weight, json.dumps(properties or {}))
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add relation {source_id}->{target_id}: {e}")
            return False

    async def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get a node by ID"""
        query = "SELECT id, type, name, content, properties FROM kg_nodes WHERE id = %s"
        rows = self._execute(query, (node_id,), fetch=True)
        if rows:
            return {
                "id": rows[0][0],
                "type": rows[0][1],
                "name": rows[0][2],
                "content": rows[0][3],
                "properties": rows[0][4],
            }
        return None

    async def get_nodes_by_ids(self, node_ids: list[str]) -> list[dict[str, Any]]:
        """Batch get nodes by IDs"""
        if not node_ids:
            return []

        query = "SELECT id, type, name, content, properties FROM kg_nodes WHERE id = ANY(%s)"
        rows = self._execute(query, (node_ids,), fetch=True)

        nodes = []
        for row in rows:
            nodes.append(
                {
                    "id": row[0],
                    "type": row[1],
                    "name": row[2],
                    "content": row[3],
                    "properties": row[4],
                }
            )
        return nodes

    async def get_related_nodes(
        self, node_id: str, relation_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Get nodes directly related to the given node"""
        query = """
        SELECT n.id, n.type, n.name, n.content, n.properties, e.type as relation, e.weight
        FROM kg_edges e
        JOIN kg_nodes n ON e.target_id = n.id
        WHERE e.source_id = %s
        """
        params = [node_id]

        if relation_types:
            query += " AND e.type = ANY(%s)"
            params.append(relation_types)

        rows = self._execute(query, tuple(params), fetch=True)

        results = []
        for row in rows:
            results.append(
                {
                    "node": {
                        "id": row[0],
                        "type": row[1],
                        "name": row[2],
                        "content": row[3],
                        "properties": row[4],
                    },
                    "relation": row[5],
                    "weight": row[6],
                }
            )
        return results

    async def search_nodes_by_text(self, keyword: str, limit: int = 10) -> list[dict[str, Any]]:
        """Simple text search (backup for vector search)"""
        query = """
        SELECT id, type, name, content, properties
        FROM kg_nodes
        WHERE name ILIKE %s OR content ILIKE %s
        LIMIT %s
        """
        pattern = f"%{keyword}%"
        rows = self._execute(query, (pattern, pattern, limit), fetch=True)

        nodes = []
        for row in rows:
            nodes.append(
                {
                    "id": row[0],
                    "type": row[1],
                    "name": row[2],
                    "content": row[3],
                    "properties": row[4],
                }
            )
        return nodes

    async def clear_graph(self):
        """Clear all data (Use with caution)"""
        self._execute("TRUNCATE TABLE kg_edges CASCADE")
        self._execute("TRUNCATE TABLE kg_nodes CASCADE")
        logger.warning("Knowledge Graph data cleared from PostgreSQL")

    async def get_node(self, node_id: str) -> dict[str, Any] | None:
        """获取单个节点"""
        query = """
        SELECT id, type, name, content, properties, created_at, updated_at
        FROM kg_nodes WHERE id = %s
        """
        result = self._execute(query, (node_id,), fetch=True)

        if result:
            row = result[0]
            return {
                "node_id": row[0],
                "node_type": row[1],
                "name": row[2],
                "content": row[3],
                "properties": row[4],
                "created_at": row[5],
                "updated_at": row[6],
            }
        return None

    async def get_connected_nodes(self, node_id: str, max_depth: int = 1) -> list[dict[str, Any]]:
        """获取连接的节点"""
        if max_depth < 1:
            return []

        # 使用递归CTE查询连接节点
        query = """
        WITH RECURSIVE connected_nodes AS (
            -- 基础层:直接连接的节点
            SELECT
                e.target_id as connected_id,
                e.type as relation_type,
                e.weight,
                n.type as node_type,
                n.name as node_name,
                n.content,
                n.properties,
                1 as depth
            FROM kg_edges e
            JOIN kg_nodes n ON e.target_id = n.id
            WHERE e.source_id = %s

            UNION ALL

            -- 递归层:连接的节点的连接
            SELECT
                e.target_id as connected_id,
                e.type as relation_type,
                e.weight,
                n.type as node_type,
                n.name as node_name,
                n.content,
                n.properties,
                cn.depth + 1
            FROM kg_edges e
            JOIN kg_nodes n ON e.target_id = n.id
            JOIN connected_nodes cn ON e.source_id = cn.connected_id
            WHERE cn.depth < %s
        )
        SELECT * FROM connected_nodes
        WHERE depth <= %s
        ORDER BY depth, weight DESC
        """

        result = self._execute(query, (node_id, max_depth, max_depth), fetch=True)

        connected_nodes = []
        for row in result:
            connected_nodes.append(
                {
                    "node_id": row[0],
                    "relation_type": row[1],
                    "weight": row[2],
                    "node_type": row[3],
                    "name": row[4],
                    "content": row[5],
                    "properties": row[6],
                    "depth": row[7],
                }
            )

        return connected_nodes

    async def search_nodes(
        self, keyword: str, node_types: list[str] | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """搜索节点"""
        # 构建WHERE条件
        conditions = ["(name ILIKE %s OR content ILIKE %s)"]
        params = [f"%{keyword}%", f"%{keyword}%"]

        if node_types:
            type_placeholders = ",".join(["%s"] * len(node_types))
            conditions.append(f"type IN ({type_placeholders})")
            params.extend(node_types)

        where_clause = " AND ".join(conditions)

        query = f"""
        SELECT id, type, name, content, properties
        FROM kg_nodes
        WHERE {where_clause}
        ORDER BY
            CASE
                WHEN name ILIKE %s THEN 1
                WHEN content ILIKE %s THEN 2
                ELSE 3
            END
        LIMIT %s
        """

        params.extend([f"%{keyword}%", f"%{keyword}%", limit])
        result = self._execute(query, tuple(params), fetch=True)

        nodes = []
        for row in result:
            nodes.append(
                {
                    "node_id": row[0],
                    "node_type": row[1],
                    "name": row[2],
                    "content": row[3],
                    "properties": row[4],
                }
            )

        return nodes

    async def full_text_search(
        self, query: str, node_types: list[str] | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """全文搜索(使用PostgreSQL的全文检索)"""
        # 构建WHERE条件
        conditions = [
            "to_tsvector('chinese', name || ' ' || COALESCE(content, '')) @@ plainto_tsquery('chinese', %s)"
        ]
        params = [query]

        if node_types:
            type_placeholders = ",".join(["%s"] * len(node_types))
            conditions.append(f"type IN ({type_placeholders})")
            params.extend(node_types)

        where_clause = " AND ".join(conditions)

        query_sql = f"""
        SELECT
            id, type, name, content, properties,
            ts_rank(to_tsvector('chinese', name || ' ' || COALESCE(content, '')), plainto_tsquery('chinese', %s)) as rank
        FROM kg_nodes
        WHERE {where_clause}
        ORDER BY rank DESC
        LIMIT %s
        """

        params.extend([query, limit])
        result = self._execute(query_sql, tuple(params), fetch=True)

        nodes = []
        for row in result:
            nodes.append(
                {
                    "node_id": row[0],
                    "node_type": row[1],
                    "name": row[2],
                    "content": row[3],
                    "properties": row[4],
                    "rank": float(row[5]),
                }
            )

        return nodes
