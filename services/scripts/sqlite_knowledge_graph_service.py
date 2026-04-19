#!/usr/bin/env python3
"""
SQLite知识图谱服务
SQLite Knowledge Graph Service

基于SQLite的知识图谱查询和管理服务
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# FastAPI应用
app = FastAPI(
    title='Athena SQLite知识图谱服务',
    description='基于SQLite的智能知识图谱查询服务',
    version='1.0.0'
)

# 知识图谱数据库路径
KNOWLEDGE_DIR = Path('/Users/xujian/Athena工作平台/data/knowledge')
GRAPHS = {
    'main': KNOWLEDGE_DIR / 'kg_main.db',
    'patent': KNOWLEDGE_DIR / 'patent_kg.db',
    'athena_ipc': KNOWLEDGE_DIR / 'athena_ipc.db'
}

class SQLiteKnowledgeGraph:
    """SQLite知识图谱管理类"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection = None
        self.connect()

    def connect(self):
        """连接数据库"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            logger.info(f"成功连接知识图谱: {self.db_path.name}")
        except Exception as e:
            logger.error(f"连接知识图谱失败 {self.db_path}: {e}")
            raise

    def close(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()

    def get_statistics(self) -> dict[str, Any]:
        """获取图谱统计信息"""
        stats = {'name': self.db_path.name}

        try:
            cursor = self.connection.cursor()

            # 获取表列表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            stats['tables'] = tables

            # 实体统计
            if 'entities' in tables:
                cursor.execute('SELECT COUNT(*) FROM entities')
                stats['entity_count'] = cursor.fetchone()[0]

                # 实体类型分布
                try:
                    cursor.execute("""
                        SELECT entity_type, COUNT(*) as count
                        FROM entities
                        GROUP BY entity_type
                        ORDER BY count DESC
                        LIMIT 10
                    """)
                    stats['entity_types'] = dict(cursor.fetchall())
                except Exception as e:
                    logger.error(f"Error: {e}", exc_info=True)

            # 关系统计
            if 'relations' in tables:
                cursor.execute('SELECT COUNT(*) FROM relations')
                stats['relation_count'] = cursor.fetchone()[0]

                # 关系类型分布
                try:
                    cursor.execute("""
                        SELECT relation_type, COUNT(*) as count
                        FROM relations
                        GROUP BY relation_type
                        ORDER BY count DESC
                        LIMIT 10
                    """)
                    stats['relation_types'] = dict(cursor.fetchall())
                except Exception as e:
                    logger.error(f"Error: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            stats['error'] = str(e)

        return stats

    def search_entities(self, keyword: str, limit: int = 10) -> list[dict]:
        """搜索实体"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM entities
                WHERE name LIKE ? OR aliases LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (f"%{keyword}%", f"%{keyword}%", limit))

            results = []
            for row in cursor.fetchall():
                entity = dict(row)
                # 解析JSON字段
                if entity.get('properties'):
                    try:
                        entity['properties'] = json.loads(entity['properties'])
                    except Exception as e:
                        logger.error(f"Error: {e}", exc_info=True)
                results.append(entity)

            return results

        except Exception as e:
            logger.error(f"搜索实体失败: {e}")
            return []

    def get_entity_relations(self, entity_id: str, limit: int = 20) -> list[dict]:
        """获取实体的关系"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT r.*,
                       e1.name as from_name,
                       e2.name as to_name
                FROM relations r
                LEFT JOIN entities e1 ON r.from_entity = e1.entity_id
                LEFT JOIN entities e2 ON r.to_entity = e2.entity_id
                WHERE r.from_entity = ? OR r.to_entity = ?
                LIMIT ?
            """, (entity_id, entity_id, limit))

            results = []
            for row in cursor.fetchall():
                relation = dict(row)
                # 解析JSON字段
                if relation.get('properties'):
                    try:
                        relation['properties'] = json.loads(relation['properties'])
                    except Exception as e:
                        logger.error(f"Error: {e}", exc_info=True)
                results.append(relation)

            return results

        except Exception as e:
            logger.error(f"获取实体关系失败: {e}")
            return []

    def find_path(self, from_entity: str, to_entity: str, max_depth: int = 3) -> list[dict]:
        """查找实体间路径（简化版）"""
        try:
            cursor = self.connection.cursor()

            # 简单的路径查找（基于关系表）
            cursor.execute("""
                WITH RECURSIVE path(from_entity, to_entity, relation_type, depth, path_str) AS (
                    SELECT from_entity, to_entity, relation_type, 1,
                           from_entity || '->' || relation_type || '->' || to_entity
                    FROM relations
                    WHERE from_entity = ?

                    UNION

                    SELECT r.from_entity, r.to_entity, r.relation_type, p.depth + 1,
                           p.path_str || '->' || r.relation_type || '->' || r.to_entity
                    FROM relations r
                    JOIN path p ON r.from_entity = p.to_entity
                    WHERE p.depth < ?
                )
                SELECT * FROM path
                WHERE to_entity = ?
                ORDER BY depth
                LIMIT 10
            """, (from_entity, max_depth, to_entity))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'from': row['from_entity'],
                    'to': row['to_entity'],
                    'relation': row['relation_type'],
                    'depth': row['depth'],
                    'path': row['path_str']
                })

            return results

        except Exception as e:
            logger.error(f"查找路径失败: {e}")
            return []

# 全局图谱实例
graph_instances = {}
for name, path in GRAPHS.items():
    if path.exists():
        try:
            graph_instances[name] = SQLiteKnowledgeGraph(path)
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)

# API模型定义
class QueryRequest(BaseModel):
    """查询请求模型"""
    graph: str = 'main'
    query: str
    parameters: dict[str, Any] | None = {}

class EntityResponse(BaseModel):
    """实体响应模型"""
    entity_id: str
    entity_type: str
    name: str
    properties: dict[str, Any]
    aliases: str | None

# API路由
@app.on_event('shutdown')
async def shutdown_event():
    """关闭服务时的清理"""
    for graph in graph_instances.values():
        graph.close()

@app.get('/')
async def root():
    """根路径"""
    return {
        'service': 'Athena SQLite知识图谱服务',
        'status': 'running',
        'graphs': list(graph_instances.keys()),
        'timestamp': datetime.now().isoformat()
    }

@app.get('/health')
async def health_check():
    """健康检查"""
    try:
        # 检查主图谱是否可访问
        if 'main' in graph_instances:
            stats = graph_instances['main'].get_statistics()
            return {
                'status': 'healthy',
                'graphs_loaded': len(graph_instances),
                'main_graph_entities': stats.get('entity_count', 0),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    'status': 'unhealthy',
                    'error': '主知识图谱未加载',
                    'timestamp': datetime.now().isoformat()
                }
            )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )

@app.get('/graphs')
async def list_graphs():
    """列出所有知识图谱"""
    graphs_info = {}
    for name, graph in graph_instances.items():
        graphs_info[name] = graph.get_statistics()
    return {
        'graphs': graphs_info,
        'count': len(graphs_info),
        'timestamp': datetime.now().isoformat()
    }

@app.get('/graphs/{graph_name}/stats')
async def get_graph_stats(graph_name: str):
    """获取特定图谱统计信息"""
    if graph_name not in graph_instances:
        raise HTTPException(status_code=404, detail=f"知识图谱 {graph_name} 不存在")

    return graph_instances[graph_name].get_statistics()

@app.get('/search/entities')
async def search_entities_endpoint(
    keyword: str = Query(..., description='搜索关键词'),
    graph: str = Query('main', description='知识图谱名称'),
    limit: int = Query(10, le=100, description='返回数量限制')
):
    """搜索实体"""
    if graph not in graph_instances:
        raise HTTPException(status_code=404, detail=f"知识图谱 {graph} 不存在")

    results = graph_instances[graph].search_entities(keyword, limit)
    return {
        'keyword': keyword,
        'graph': graph,
        'entities': results,
        'count': len(results),
        'timestamp': datetime.now().isoformat()
    }

@app.get('/entities/{entity_id}/relations')
async def get_entity_relations_endpoint(
    entity_id: str,
    graph: str = Query('main', description='知识图谱名称'),
    limit: int = Query(20, le=100, description='返回数量限制')
):
    """获取实体关系"""
    if graph not in graph_instances:
        raise HTTPException(status_code=404, detail=f"知识图谱 {graph} 不存在")

    results = graph_instances[graph].get_entity_relations(entity_id, limit)
    return {
        'entity_id': entity_id,
        'graph': graph,
        'relations': results,
        'count': len(results),
        'timestamp': datetime.now().isoformat()
    }

@app.get('/path')
async def find_path_endpoint(
    from_entity: str = Query(..., description='起始实体ID'),
    to_entity: str = Query(..., description='目标实体ID'),
    graph: str = Query('main', description='知识图谱名称'),
    max_depth: int = Query(3, le=5, description='最大深度')
):
    """查找实体间路径"""
    if graph not in graph_instances:
        raise HTTPException(status_code=404, detail=f"知识图谱 {graph} 不存在")

    results = graph_instances[graph].find_path(from_entity, to_entity, max_depth)
    return {
        'from_entity': from_entity,
        'to_entity': to_entity,
        'graph': graph,
        'paths': results,
        'count': len(results),
        'timestamp': datetime.now().isoformat()
    }

@app.post('/query')
async def execute_query(request: QueryRequest):
    """执行自定义SQL查询（仅限SELECT）"""
    if request.graph not in graph_instances:
        raise HTTPException(status_code=404, detail=f"知识图谱 {request.graph} 不存在")

    # 安全检查
    if any(keyword in request.query.upper() for keyword in ['DELETE', 'DROP', 'UPDATE', 'INSERT', 'ALTER']):
        raise HTTPException(status_code=400, detail='只允许执行查询操作')

    try:
        cursor = graph_instances[request.graph].connection.cursor()
        cursor.execute(request.query, request.parameters or {})

        # 获取列名
        columns = [description[0] for description in cursor.description]

        # 获取结果
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row, strict=False)))

        return {
            'query': request.query,
            'graph': request.graph,
            'results': results,
            'count': len(results),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"查询执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# 记忆系统集成接口
@app.get('/memory/graph_entities')
async def get_memory_graph_entities():
    """获取记忆相关的图谱实体"""
    # 从主知识图谱中查找可能与记忆相关的实体
    memory_related = []

    if 'main' in graph_instances:
        # 查找可能相关的实体类型
        cursor = graph_instances['main'].connection.cursor()

        # 尝试查找不同类型的实体
        for entity_type in ['person', 'organization', 'concept', 'event']:
            try:
                cursor.execute("""
                    SELECT entity_id, name, entity_type, properties
                    FROM entities
                    WHERE entity_type LIKE ?
                    LIMIT 5
                """, (f"%{entity_type}%",))

                for row in cursor.fetchall():
                    entity = dict(row)
                    if entity.get('properties'):
                        try:
                            entity['properties'] = json.loads(entity['properties'])
                        except Exception as e:
                            logger.error(f"Error: {e}", exc_info=True)
                    memory_related.append(entity)
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)

    return {
        'entities': memory_related,
        'count': len(memory_related),
        'timestamp': datetime.now().isoformat()
    }

if __name__ == '__main__':
    uvicorn.run(
        'sqlite_knowledge_graph_service:app',
        host='0.0.0.0',
        port=8089,
        reload=True,
        log_level='info'
    )
