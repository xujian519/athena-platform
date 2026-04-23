#!/usr/bin/env python3
"""
SQLite统一数据服务
SQLite Unified Data Service

统一管理SQLite形式的向量库和知识图谱数据
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from core.logging_config import setup_logging

# 导入统一认证模块

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title='SQLite统一数据服务',
    description='统一管理SQLite向量库和知识图谱数据',
    version='1.0.0'
)

# 配置CORS

# 数据库路径配置
BASE_PATH = Path('/Users/xujian/Athena工作平台/data')
SQLITE_DATABASES = {
    'knowledge_graph': str(BASE_PATH / 'knowledge_graph_sqlite/databases/patent_knowledge_graph.db'),
    'patent_cache': str(BASE_PATH / 'cache/patent_cache.db'),
    'patent_index': str(BASE_PATH / 'patents/processed/indexed_patents.db'),
    'patent_legal': str(BASE_PATH / 'support_data/databases/patent_legal_database.db'),
    'legal_laws': str(BASE_PATH / 'support_data/databases/legal_laws_database.db'),
    'athena_memory': str(BASE_PATH / 'support_data/databases/databases/memory_system/athena_memory.db'),
    'memory_cold': str(BASE_PATH / 'memory/cold_tier.db'),
    'performance': str(BASE_PATH / 'performance_metrics.db'),
    'legal_knowledge': '/Users/xujian/Athena工作平台/domains/legal-knowledge/db.sqlite3'
}

# 全局连接池
connections = {}

class DatabaseInfo(BaseModel):
    name: str
    path: str
    size: str
    tables: list[str]
    exists: bool
    last_modified: str | None = None

class QueryRequest(BaseModel):
    database: str
    query: str
    params: list[Any] | None = None
    limit: int | None = Field(100, ge=1, le=1000)

class VectorSearchRequest(BaseModel):
    query: str = Field(..., description='搜索文本')
    database: str = Field('patent_index', description='数据库')
    limit: int = Field(10, ge=1, le=100)
    threshold: float = Field(0.5, ge=0.0, le=1.0)

class GraphSearchRequest(BaseModel):
    query: str = Field(..., description='搜索节点或关系')
    database: str = Field('knowledge_graph', description='知识图谱数据库')
    node_type: str | None = None
    relation_type: str | None = None
    limit: int = Field(20, ge=1, le=200)

@app.on_event('startup')
async def startup_event():
    """服务启动事件"""
    logger.info('🚀 SQLite统一数据服务启动')

    # 检查所有数据库
    for db_name, db_path in SQLITE_DATABASES.items():
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                connections[db_name] = conn
                logger.info(f"✅ {db_name}: {db_path}")
            except Exception as e:
                logger.error(f"❌ {db_name} 连接失败: {str(e)}")
        else:
            logger.warning(f"⚠️ {db_name}: {db_path} - 文件不存在")

    logger.info(f"📊 成功连接 {len(connections)} 个SQLite数据库")

@app.on_event('shutdown')
async def shutdown_event():
    """服务关闭事件"""
    for db_name, conn in connections.items():
        try:
            conn.close()
            logger.info(f"📌 {db_name} 连接已关闭")
        except (FileNotFoundError, PermissionError, OSError):
            pass

@app.get('/')
async def root():
    """根路径"""
    return {
        'service': 'SQLite统一数据服务',
        'status': 'running',
        'databases': len(connections),
        'timestamp': datetime.now().isoformat()
    }

@app.get('/api/databases')
async def list_databases():
    """列出所有数据库及其信息"""
    db_infos = []

    for db_name, db_path in SQLITE_DATABASES.items():
        exists = os.path.exists(db_path)
        size = 'N/A'
        last_modified = None
        tables = []

        if exists:
            try:
                stat = os.stat(db_path)
                size = f"{stat.st_size / 1024:.2f} KB"
                last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

                # 获取表列表
                if db_name in connections:
                    cursor = connections[db_name].cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
            except Exception as e:
                logger.error(f"获取 {db_name} 信息失败: {str(e)}")

        db_infos.append(DatabaseInfo(
            name=db_name,
            path=db_path,
            size=size,
            tables=tables,
            exists=exists,
            last_modified=last_modified
        ))

    return {'databases': db_infos}

@app.get('/api/database/{db_name}/tables')
async def get_database_tables(db_name: str):
    """获取数据库的表结构"""
    if db_name not in connections:
        raise HTTPException(status_code=404, detail=f"Database {db_name} not found")

    conn = connections[db_name]
    cursor = conn.cursor()

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    table_info = {}
    for table in tables:
        table_name = table[0]

        # 获取表结构
        # TODO: 检查SQL注入风险
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        # 获取行数
        try:
            # TODO: 检查SQL注入风险
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
        except (ConnectionError, OSError, TimeoutError):
            row_count = 0

        table_info[table_name] = {
            'columns': [
                {
                    'name': col[1],
                    'type': col[2],
                    'nullable': not col[3],
                    'primary_key': bool(col[5])
                }
                for col in columns
            ],
            'row_count': row_count
        }

    return {'database': db_name, 'tables': table_info}

@app.post('/api/query')
async def execute_query(request: QueryRequest):
    """执行SQL查询"""
    if request.database not in connections:
        raise HTTPException(status_code=404, detail=f"Database {request.database} not found")

    conn = connections[request.database]
    cursor = conn.cursor()

    try:
        # 安全检查：只允许SELECT查询
        if not request.query.strip().upper().startswith('SELECT'):
            raise HTTPException(status_code=400, detail='Only SELECT queries are allowed')

        # 执行查询
        if request.params:
            cursor.execute(request.query, request.params)
        else:
            cursor.execute(request.query)

        # 获取结果
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = cursor.fetchall()

        # 转换为字典列表
        results = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            results.append(row_dict)

        # 应用限制
        if request.limit and len(results) > request.limit:
            results = results[:request.limit]

        return {
            'database': request.database,
            'query': request.query,
            'columns': columns,
            'results': results,
            'count': len(results)
        }

    except Exception as e:
        logger.error(f"查询执行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}") from e

@app.post('/api/vector/search')
async def vector_search(request: VectorSearchRequest):
    """向量搜索"""
    if request.database not in connections:
        raise HTTPException(status_code=404, detail=f"Database {request.database} not found")

    # 简单的文本搜索（实际应该使用向量相似度）
    conn = connections[request.database]
    cursor = conn.cursor()

    # 尝试查找包含文本的表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    results = []
    for table in tables:
        table_name = table[0]

        try:
            # 获取列信息
            # TODO: 检查SQL注入风险
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            # 查找文本列
            text_columns = [col[1] for col in columns if 'TEXT' in col[2].upper()]

            if text_columns:
                # 构建搜索查询
                search_conditions = [f"{col} LIKE ?" for col in text_columns]
                search_query = f"SELECT * FROM {table_name} WHERE {' OR '.join(search_conditions)} LIMIT {request.limit}"

                search_params = [f"%{request.query}%"] * len(text_columns)
                cursor.execute(search_query, search_params)

                rows = cursor.fetchall()

                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col[1] = row[i]
                    results.append({
                        'table': table_name,
                        'data': row_dict,
                        'relevance': 0.8  # 模拟相关性分数
                    })

        except Exception as e:
            logger.warning(f"表 {table_name} 搜索失败: {str(e)}")
            continue

    # 按相关性排序并限制结果
    results.sort(key=lambda x: x['relevance'], reverse=True)
    results = results[:request.limit]

    return {
        'query': request.query,
        'database': request.database,
        'results': results,
        'count': len(results)
    }

@app.post('/api/graph/search')
async def graph_search(request: GraphSearchRequest):
    """知识图谱搜索"""
    if request.database not in connections:
        raise HTTPException(status_code=404, detail=f"Database {request.database} not found")

    conn = connections[request.database]
    cursor = conn.cursor()

    try:
        # 获取表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        results = []

        # 查找节点
        if 'nodes' in tables or 'entities' in tables:
            table_name = 'nodes' if 'nodes' in tables else 'entities'

            # 构建查询
            query = f"SELECT * FROM {table_name} WHERE name LIKE ? OR type LIKE ?"
            params = [f"%{request.query}%', f'%{request.query}%"]

            if request.node_type:
                query += ' AND type = ?'
                params.append(request.node_type)

            query += f" LIMIT {request.limit}"

            cursor.execute(query, params)
            nodes = cursor.fetchall()

            columns = [description[0] for description in cursor.description] if cursor.description else []

            for node in nodes:
                node_dict = {}
                for i, col in enumerate(columns):
                    node_dict[col] = node[i]
                results.append({
                    'type': 'node',
                    'table': table_name,
                    'data': node_dict
                })

        # 查找关系
        if 'relationships' in tables or 'edges' in tables:
            table_name = 'relationships' if 'relationships' in tables else 'edges'

            # 构建查询
            query = f"SELECT * FROM {table_name} WHERE relation_type LIKE ?"
            params = [f"%{request.query}%"]

            if request.relation_type:
                query += ' AND relation_type = ?'
                params.append(request.relation_type)

            query += f" LIMIT {request.limit}"

            cursor.execute(query, params)
            edges = cursor.fetchall()

            columns = [description[0] for description in cursor.description] if cursor.description else []

            for edge in edges:
                edge_dict = {}
                for i, col in enumerate(columns):
                    edge_dict[col] = edge[i]
                results.append({
                    'type': 'edge',
                    'table': table_name,
                    'data': edge_dict
                })

        return {
            'query': request.query,
            'database': request.database,
            'results': results,
            'count': len(results)
        }

    except Exception as e:
        logger.error(f"图搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Graph search failed: {str(e)}") from e

@app.get('/api/database/{db_name}/stats')
async def get_database_stats(db_name: str):
    """获取数据库统计信息"""
    if db_name not in connections:
        raise HTTPException(status_code=404, detail=f"Database {db_name} not found")

    conn = connections[db_name]
    cursor = conn.cursor()

    try:
        # 获取表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        stats = {
            'database': db_name,
            'tables': {},
            'total_records': 0
        }

        for table in tables:
            table_name = table[0]

            # 获取记录数
            try:
                # TODO: 检查SQL注入风险
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]

                # 获取表大小（估算）
                # TODO: 检查SQL注入风险
                cursor.execute(f"SELECT COUNT(*) * AVG(LENGTH(CAST(* AS TEXT))) FROM {table_name}")
                size_info = cursor.fetchone()
                estimated_size = size_info[0] if size_info and size_info[0] else 0

                stats['tables'][table_name] = {
                    'records': count,
                    'estimated_size_bytes': estimated_size
                }

                stats['total_records'] += count

            except Exception as e:
                logger.warning(f"获取表 {table_name} 统计失败: {str(e)}")
                stats['tables'][table_name] = {'error': str(e)}

        return stats

    except Exception as e:
        logger.error(f"获取数据库统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}") from e

@app.get('/api/knowledge-graph/paths')
async def find_paths(
    start_node: str = Query(..., description='起始节点'),
    end_node: str = Query(..., description='目标节点'),
    max_depth: int = Query(3, ge=1, le=5, description='最大路径深度'),
    database: str = Query('knowledge_graph', description='数据库名称')
):
    """查找知识图谱中的路径"""
    if database not in connections:
        raise HTTPException(status_code=404, detail=f"Database {database} not found")

    # 这是一个简化的实现，实际应该使用图算法
    # 这里返回模拟数据
    return {
        'start_node': start_node,
        'end_node': end_node,
        'max_depth': max_depth,
        'paths': [
            {
                'path': [start_node, '中间节点1', '中间节点2', end_node],
                'length': 3,
                'weight': 0.8
            }
        ]
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'sqlite_unified_service:app',
        host='0.0.0.0',
        port=8011,
        reload=True,
        log_level='info'
    )
