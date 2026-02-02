#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一知识图谱管理系统
Unified Knowledge Graph Management System

实现专业知识图谱统一管理 + 记忆模块分布式管理
"""

import asyncio
import json
import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import JSONResponse

# 导入统一认证模块
from shared.auth.auth_middleware import create_auth_middleware, setup_cors

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据模型
@dataclass
class KnowledgeGraphInfo:
    """知识图谱信息"""
    kg_type: str
    name: str
    description: str
    path: str
    category: str  # 'professional' 或 'memory'
    size: int
    entity_count: int
    relation_count: int
    last_updated: str

class GraphNode(BaseModel):
    """图谱节点"""
    id: str
    type: str
    name: str
    properties: Optional[Dict[str, Any]] = None
    description: str | None = None

class GraphRelation(BaseModel):
    """图谱关系"""
    id: str
    source_id: str
    target_id: str
    type: str
    properties: Optional[Dict[str, Any]] = None
    weight: float = 1.0

class UnifiedQuery(BaseModel):
    """统一查询"""
    query: str
    kg_types: Optional[List[str] = None
    categories: Optional[List[str] = None
    limit: int = 100
    offset: int = 0

# 创建FastAPI应用
app = FastAPI(
    title='Athena统一知识图谱管理系统',
    description='专业知识图谱统一管理 + 记忆模块分布式管理',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

# CORS配置

class UnifiedKnowledgeManager:
    """统一知识图谱管理器"""

    def __init__(self):
        self.project_root = str(Path(__file__).resolve().parents[1])
        self.professional_kg_dir = str(Path(self.project_root) / 'data/professional_knowledge_graphs')
        self.memory_kg_dir = str(Path(self.project_root) / 'data/memory_knowledge_graphs')
        self.merged_kg_dir = str(Path(self.project_root) / 'data/merged_knowledge_graphs')

        # 专业知识图谱配置
        self.professional_types = {
            'legal': '法律知识图谱',
            'patent_core': '专利核心知识图谱',
            'trademark': '商标知识图谱',
            'patent_invalid': '专利无效知识图谱',
            'patent_reconsideration': '专利复审知识图谱',
            'patent_judgment': '专利判决知识图谱',
            'technical_terms': '技术术语知识图谱'
        }

        self.kg_registry = {}
        self.connection_cache = {}
        self.initialize_registry()

    def initialize_registry(self) -> Any:
        """初始化知识图谱注册中心"""
        logger.info('初始化知识图谱注册中心...')

        # 注册专业知识图谱
        self.register_professional_kgs()

        # 注册记忆模块图谱
        self.register_memory_kgs()

        logger.info(f"知识图谱注册完成: {len(self.kg_registry)} 个图谱")

    def register_professional_kgs(self) -> Any:
        """注册专业知识图谱"""
        professional_dir = Path(self.professional_kg_dir)
        if not professional_dir.exists():
            logger.warning(f"专业知识图谱目录不存在: {professional_dir}")
            return

        for file_path in professional_dir.glob('*_rebuilt.db'):
            kg_type = file_path.stem.replace('_rebuilt', '')
            if kg_type in self.professional_types:
                info = self.get_kg_info(file_path, 'professional', kg_type)
                self.kg_registry[kg_type] = info
                logger.info(f"注册专业图谱: {kg_type}")

    def register_memory_kgs(self) -> Any:
        """注册记忆模块图谱"""
        # 注册合并后的主图谱
        merged_dir = Path(self.merged_kg_dir)
        if merged_dir.exists():
            for file_path in merged_dir.glob('*.db'):
                kg_type = file_path.stem
                info = self.get_kg_info(file_path, 'memory', kg_type)
                self.kg_registry[f"memory_{kg_type}"] = info
                logger.info(f"注册记忆图谱: {kg_type}")

    def get_kg_info(self, file_path: Path, category: str, kg_type: str) -> KnowledgeGraphInfo:
        """获取知识图谱信息"""
        try:
            conn = sqlite3.connect(str(file_path))
            cursor = conn.cursor()

            # 获取实体和关系数量
            entity_count = 0
            relation_count = 0

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]

            if 'entities' in tables:
                cursor.execute('SELECT COUNT(*) FROM entities')
                entity_count = cursor.fetchone()[0]

            if 'relations' in tables:
                cursor.execute('SELECT COUNT(*) FROM relations')
                relation_count = cursor.fetchone()[0]

            # 获取元数据
            description = kg_type
            if 'kg_metadata' in tables:
                try:
                    cursor.execute("SELECT value FROM kg_metadata WHERE key = 'kg_description'")
                    result = cursor.fetchone()
                    if result:
                        description = result[0]
                except:
                    pass

            conn.close()

            return KnowledgeGraphInfo(
                kg_type=kg_type,
                name=kg_type.replace('_', ' ').title(),
                description=description,
                category=category,
                path=str(file_path),
                size=file_path.stat().st_size,
                entity_count=entity_count,
                relation_count=relation_count,
                last_updated=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"获取图谱信息失败 {file_path}: {e}")
            return KnowledgeGraphInfo(
                kg_type=kg_type,
                name=kg_type,
                description=f"Error: {str(e)}",
                category=category,
                path=str(file_path),
                size=0,
                entity_count=0,
                relation_count=0,
                last_updated=datetime.now().isoformat()
            )

    def get_connection(self, kg_type: str) -> sqlite3.Connection | None:
        """获取数据库连接"""
        if kg_type not in self.kg_registry:
            return None

        # 连接缓存
        if kg_type in self.connection_cache:
            return self.connection_cache[kg_type]

        try:
            kg_info = self.kg_registry[kg_type]
            conn = sqlite3.connect(kg_info.path, check_same_thread=False)
            self.connection_cache[kg_type] = conn
            return conn
        except Exception as e:
            logger.error(f"连接数据库失败 {kg_type}: {e}")
            return None

    def search_across_kgs(self, query: str, kg_types: Optional[List[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """跨知识图谱搜索"""
        results = []

        # 确定搜索范围
        target_kgs = []
        if kg_types:
            target_kgs = [kg for kg in kg_types if kg in self.kg_registry]
        else:
            target_kgs = list(self.kg_registry.keys())

        for kg_type in target_kgs:
            try:
                conn = self.get_connection(kg_type)
                if not conn:
                    continue

                cursor = conn.cursor()
                kg_info = self.kg_registry[kg_type]

                # 搜索实体
                cursor.execute("""
                    SELECT id, type, name, properties, description, ? as kg_type, ? as kg_name
                    FROM entities
                    WHERE name LIKE ? OR description LIKE ?
                    LIMIT ?
                """, (kg_type, kg_info.name, f"%{query}%", f"%{query}%", limit // len(target_kgs)))

                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    result = dict(zip(columns, row))
                    if result['properties']:
                        result['properties'] = json.loads(result['properties'])
                    results.append(result)

            except Exception as e:
                logger.error(f"搜索 {kg_type} 失败: {e}")

        return results

    def get_kg_statistics(self, kg_type: str = None) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        if kg_type:
            # 单个图谱统计
            if kg_type not in self.kg_registry:
                return {'error': f"知识图谱 {kg_type} 不存在"}

            kg_info = self.kg_registry[kg_type]
            return {
                'kg_type': kg_type,
                'name': kg_info.name,
                'category': kg_info.category,
                'entity_count': kg_info.entity_count,
                'relation_count': kg_info.relation_count,
                'size_kb': kg_info.size // 1024,
                'last_updated': kg_info.last_updated
            }
        else:
            # 全局统计
            stats = {
                'total_graphs': len(self.kg_registry),
                'professional_graphs': 0,
                'memory_graphs': 0,
                'total_entities': 0,
                'total_relations': 0,
                'total_size_mb': 0,
                'graphs_by_type': {}
            }

            for kg_type, kg_info in self.kg_registry.items():
                if kg_info.category == 'professional':
                    stats['professional_graphs'] += 1
                else:
                    stats['memory_graphs'] += 1

                stats['total_entities'] += kg_info.entity_count
                stats['total_relations'] += kg_info.relation_count
                stats['total_size_mb'] += kg_info.size / (1024 * 1024)

                stats['graphs_by_type'][kg_type] = {
                    'name': kg_info.name,
                    'category': kg_info.category,
                    'entity_count': kg_info.entity_count,
                    'relation_count': kg_info.relation_count
                }

            return stats

# 创建管理器实例
manager = UnifiedKnowledgeManager()

@app.get('/')
async def root():
    """根路径"""
    return {
        'service': 'Athena统一知识图谱管理系统',
        'status': 'running',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'registry_size': len(manager.kg_registry)
    }

@app.get('/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'registered_graphs': len(manager.kg_registry),
        'professional_graphs': len([g for g in manager.kg_registry.values() if g.category == 'professional']),
        'memory_graphs': len([g for g in manager.kg_registry.values() if g.category == 'memory'])
    }

@app.get('/graphs')
async def list_graphs(category: str | None = None):
    """列出所有知识图谱"""
    graphs = []

    for kg_type, kg_info in manager.kg_registry.items():
        if category and kg_info.category != category:
            continue

        graphs.append({
            'kg_type': kg_type,
            'name': kg_info.name,
            'description': kg_info.description,
            'category': kg_info.category,
            'size_kb': kg_info.size // 1024,
            'entity_count': kg_info.entity_count,
            'relation_count': kg_info.relation_count,
            'last_updated': kg_info.last_updated
        })

    return {
        'total_graphs': len(graphs),
        'graphs': graphs
    }

@app.get('/graphs/{kg_type}/statistics')
async def get_graph_statistics(kg_type: str):
    """获取特定知识图谱统计信息"""
    stats = manager.get_kg_statistics(kg_type)
    if 'error' in stats:
        raise HTTPException(status_code=404, detail=stats['error'])
    return stats

@app.get('/statistics')
async def get_global_statistics():
    """获取全局统计信息"""
    return manager.get_kg_statistics()

@app.post('/search')
async def search_knowledge(query: UnifiedQuery):
    """跨知识图谱搜索"""
    results = manager.search_across_kgs(
        query=query.query,
        kg_types=query.kg_types,
        limit=query.limit
    )

    return {
        'query': query.query,
        'total_results': len(results),
        'results': results,
        'search_time': datetime.now().isoformat()
    }

@app.get('/graphs/{kg_type}/nodes')
async def get_graph_nodes(
    kg_type: str,
    node_type: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """获取知识图谱节点"""
    conn = manager.get_connection(kg_type)
    if not conn:
        raise HTTPException(status_code=404, detail=f"知识图谱 {kg_type} 不存在")

    cursor = conn.cursor()

    try:
        if node_type:
            cursor.execute("""
                SELECT id, type, name, properties, description
                FROM entities
                WHERE type = ?
                LIMIT ? OFFSET ?
            """, (node_type, limit, offset))
        else:
            cursor.execute("""
                SELECT id, type, name, properties, description
                FROM entities
                LIMIT ? OFFSET ?
            """, (limit, offset))

        columns = [desc[0] for desc in cursor.description]
        nodes = []

        for row in cursor.fetchall():
            node_dict = dict(zip(columns, row))
            if node_dict['properties']:
                node_dict['properties'] = json.loads(node_dict['properties'])
            nodes.append(node_dict)

        return {
            'kg_type': kg_type,
            'nodes': nodes,
            'total': len(nodes)
        }

    except Exception as e:
        logger.error(f"获取节点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/graphs/{kg_type}/relations')
async def get_graph_relations(
    kg_type: str,
    relation_type: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """获取知识图谱关系"""
    conn = manager.get_connection(kg_type)
    if not conn:
        raise HTTPException(status_code=404, detail=f"知识图谱 {kg_type} 不存在")

    cursor = conn.cursor()

    try:
        if relation_type:
            cursor.execute("""
                SELECT id, source_id, target_id, type, properties, weight
                FROM relations
                WHERE type = ?
                LIMIT ? OFFSET ?
            """, (relation_type, limit, offset))
        else:
            cursor.execute("""
                SELECT id, source_id, target_id, type, properties, weight
                FROM relations
                LIMIT ? OFFSET ?
            """, (limit, offset))

        columns = [desc[0] for desc in cursor.description]
        relations = []

        for row in cursor.fetchall():
            relation_dict = dict(zip(columns, row))
            if relation_dict['properties']:
                relation_dict['properties'] = json.loads(relation_dict['properties'])
            relations.append(relation_dict)

        return {
            'kg_type': kg_type,
            'relations': relations,
            'total': len(relations)
        }

    except Exception as e:
        logger.error(f"获取关系失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/graphs/{kg_type}/metadata')
async def get_graph_metadata(kg_type: str):
    """获取知识图谱元数据"""
    conn = manager.get_connection(kg_type)
    if not conn:
        raise HTTPException(status_code=404, detail=f"知识图谱 {kg_type} 不存在")

    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = 'kg_metadata'")
        if not cursor.fetchone():
            return {'error': '元数据表不存在'}

        cursor.execute('SELECT key, value FROM kg_metadata')
        metadata = {}
        for row in cursor.fetchall():
            metadata[row[0]] = row[1]

        return {
            'kg_type': kg_type,
            'metadata': metadata
        }

    except Exception as e:
        logger.error(f"获取元数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/graphs/{kg_type}/node')
async def create_node(kg_type: str, node: GraphNode):
    """创建节点"""
    conn = manager.get_connection(kg_type)
    if not conn:
        raise HTTPException(status_code=404, detail=f"知识图谱 {kg_type} 不存在")

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO entities (id, type, name, properties, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                node.id,
                node.type,
                node.name,
                json.dumps(node.properties or {}, ensure_ascii=False),
                node.description,
            ),
        )

        conn.commit()

        return {
            'success': True,
            'node_id': node.id,
            'kg_type': kg_type,
            'message': '节点创建成功'
        }

    except Exception as e:
        logger.error(f"创建节点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/graphs/{kg_type}/relation')
async def create_relation(kg_type: str, relation: GraphRelation):
    """创建关系"""
    conn = manager.get_connection(kg_type)
    if not conn:
        raise HTTPException(status_code=404, detail=f"知识图谱 {kg_type} 不存在")

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO relations (id, source_id, target_id, type, properties, weight)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                relation.id,
                relation.source_id,
                relation.target_id,
                relation.type,
                json.dumps(relation.properties or {}, ensure_ascii=False),
                relation.weight,
            ),
        )

        conn.commit()

        return {
            'success': True,
            'relation_id': relation.id,
            'kg_type': kg_type,
            'message': '关系创建成功'
        }

    except Exception as e:
        logger.error(f"创建关系失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/categories')
async def get_categories():
    """获取知识图谱分类"""
    categories = {
        'professional': {
            'name': '专业知识图谱',
            'description': '统一管理的专业领域知识图谱',
            'types': list(manager.professional_types.keys())
        },
        'memory': {
            'name': '记忆模块知识图谱',
            'description': '分布式管理的通用知识图谱',
            'types': [kg for kg in manager.kg_registry.keys() if kg.startswith('memory_')]
        }
    }

    return categories

@app.get('/registry/reload')
async def reload_registry():
    """重新加载知识图谱注册中心"""
    try:
        manager.kg_registry.clear()
        manager.connection_cache.clear()
        manager.initialize_registry()

        return {
            'success': True,
            'message': '知识图谱注册中心重新加载完成',
            'registered_graphs': len(manager.kg_registry)
        }
    except Exception as e:
        logger.error(f"重新加载失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    logger.info('🚀 启动Athena统一知识图谱管理系统')
    logger.info('📍 服务地址: http://localhost:9050')
    logger.info('📊 健康检查: http://localhost:9050/health')
    logger.info('📖 API文档: http://localhost:9050/docs')
    logger.info('')
    logger.info('🎯 核心功能:')
    logger.info('   ✅ 专业知识图谱统一管理')
    logger.info('   ✅ 记忆模块分布式管理')
    logger.info('   ✅ 跨图谱统一搜索')
    logger.info('   ✅ 实时统计和监控')
    logger.info('')

    uvicorn.run(
        'unified_knowledge_manager:app',
        host='0.0.0.0',
        port=9050,
        reload=False,
        log_level='info'
    )
