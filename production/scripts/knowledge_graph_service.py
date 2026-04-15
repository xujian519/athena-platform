#!/usr/bin/env python3
"""
Athena知识图谱API服务
Knowledge Graph API Service

为记忆系统提供知识图谱查询接口
支持向量搜索和关系推理
"""

from __future__ import annotations
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_file = project_root / "production" / "config" / ".env.memory"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

# 配置日志
log_dir = project_root / "production" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "knowledge_graph_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# FastAPI应用
app = FastAPI(
    title="Athena知识图谱API",
    description="为记忆系统提供知识图谱查询接口",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求/响应模型
class EntityNode(BaseModel):
    """实体节点"""
    id: str
    name: str
    type: str
    properties: dict[str, Any] = {}
    created_at: str | None = None


class EntityRelation(BaseModel):
    """实体关系"""
    id: str
    source: str
    target: str
    relation_type: str
    properties: dict[str, Any] = {}
    weight: float = 1.0


class GraphSearchResult(BaseModel):
    """图搜索结果"""
    nodes: list[EntityNode]
    relations: list[EntityRelation]
    total: int


class EntityCreateRequest(BaseModel):
    """创建实体请求"""
    name: str
    type: str
    properties: dict[str, Any] = {}


class RelationCreateRequest(BaseModel):
    """创建关系请求"""
    source_id: str
    target_id: str
    relation_type: str
    properties: dict[str, Any] = {}
    weight: float = 1.0


# 内存存储（生产环境应使用数据库）
class InMemoryGraphStore:
    """内存图存储"""

    def __init__(self):
        self.nodes: dict[str, EntityNode] = {}
        self.relations: list[EntityRelation] = []
        self.node_index: dict[str, list[str]] = {}  # type -> [node_ids]
        self._initialize_default_data()

    def _initialize_default_data(self):
        """初始化默认数据"""
        # 添加默认实体类型
        default_entities = [
            {"id": "athena", "name": "Athena", "type": "agent"},
            {"id": "xiaonuo", "name": "小诺", "type": "agent"},
            {"id": "xiaona", "name": "小娜", "type": "agent"},
            {"id": "yunxi", "name": "云熙", "type": "agent"},
            {"id": "xiaochen", "name": "小宸", "type": "agent"},
            {"id": "patent", "name": "专利", "type": "concept"},
            {"id": "knowledge", "name": "知识", "type": "concept"},
            {"id": "memory", "name": "记忆", "type": "concept"},
        ]

        for entity in default_entities:
            self.add_node(EntityNode(
                id=entity["id"],
                name=entity["name"],
                type=entity["type"],
                properties={},
                created_at=datetime.now().isoformat()
            ))

        # 添加默认关系
        default_relations = [
            {"source": "athena", "target": "knowledge", "type": "manages"},
            {"source": "xiaonuo", "target": "athena", "type": "coordinates"},
            {"source": "xiaona", "target": "athena", "type": "assists"},
            {"source": "yunxi", "target": "patent", "type": "manages"},
            {"source": "xiaochen", "target": "patent", "type": "analyzes"},
        ]

        for rel in default_relations:
            self.add_relation(EntityRelation(
                id=f"{rel['source']}_{rel['target']}_{rel['type']}",
                source=rel["source"],
                target=rel["target"],
                relation_type=rel["type"],
                properties={},
                weight=1.0
            ))

        logger.info(f"已初始化默认图数据: {len(self.nodes)}个节点, {len(self.relations)}条关系")

    def add_node(self, node: EntityNode) -> EntityNode:
        """添加节点"""
        self.nodes[node.id] = node
        if node.type not in self.node_index:
            self.node_index[node.type] = []
        self.node_index[node.type].append(node.id)
        return node

    def get_node(self, node_id: str) -> EntityNode | None:
        """获取节点"""
        return self.nodes.get(node_id)

    def get_nodes_by_type(self, node_type: str) -> list[EntityNode]:
        """按类型获取节点"""
        node_ids = self.node_index.get(node_type, [])
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]

    def add_relation(self, relation: EntityRelation) -> EntityRelation:
        """添加关系"""
        self.relations.append(relation)
        return relation

    def get_relations(self, source_id: str | None = None,
                     target_id: str | None = None) -> list[EntityRelation]:
        """获取关系"""
        relations = self.relations
        if source_id:
            relations = [r for r in relations if r.source == source_id]
        if target_id:
            relations = [r for r in relations if r.target == target_id]
        return relations

    def search(self, query: str, limit: int = 20) -> GraphSearchResult:
        """搜索图"""
        query_lower = query.lower()

        # 搜索节点
        matching_nodes = [
            node for node in self.nodes.values()
            if query_lower in node.name.lower() or
               query_lower in node.type.lower() or
               any(query_lower in str(v).lower() for v in node.properties.values())
        ][:limit]

        # 获取相关关系
        node_ids = {n.id for n in matching_nodes}
        matching_relations = [
            rel for rel in self.relations
            if rel.source in node_ids or rel.target in node_ids
        ]

        return GraphSearchResult(
            nodes=matching_nodes,
            relations=matching_relations,
            total=len(matching_nodes)
        )

    def get_neighbors(self, node_id: str, max_depth: int = 1) -> dict[str, Any]:
        """获取邻居节点"""
        if node_id not in self.nodes:
            return {"nodes": [], "relations": []}

        visited = {node_id}
        current_level = {node_id}
        result_nodes = [self.nodes[node_id]]
        result_relations = []

        for _depth in range(max_depth):
            next_level = set()
            for nid in current_level:
                relations = self.get_relations(source_id=nid)
                for rel in relations:
                    if rel.target not in visited:
                        visited.add(rel.target)
                        next_level.add(rel.target)
                        result_nodes.append(self.nodes[rel.target])
                        result_relations.append(rel)

                # 反向关系
                relations = self.get_relations(target_id=nid)
                for rel in relations:
                    if rel.source not in visited:
                        visited.add(rel.source)
                        next_level.add(rel.source)
                        result_nodes.append(self.nodes[rel.source])
                        result_relations.append(rel)

            current_level = next_level
            if not current_level:
                break

        return {
            "nodes": result_nodes,
            "relations": result_relations,
            "depth": max_depth
        }

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        type_counts = {}
        for node in self.nodes.values():
            type_counts[node.type] = type_counts.get(node.type, 0) + 1

        relation_types = {}
        for rel in self.relations:
            relation_types[rel.relation_type] = relation_types.get(rel.relation_type, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_relations": len(self.relations),
            "node_types": type_counts,
            "relation_types": relation_types
        }


# 全局图存储
graph_store = InMemoryGraphStore()


# API端点
@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "Athena知识图谱API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    stats = graph_store.get_statistics()
    return {
        "service": "Athena知识图谱API",
        "status": "healthy",
        "storage": "in_memory",
        "statistics": stats,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/stats")
async def get_stats():
    """获取统计信息"""
    stats = graph_store.get_statistics()
    return {
        "success": True,
        "data": stats,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/entities", response_model=EntityNode)
async def create_entity(request: EntityCreateRequest):
    """创建实体"""
    entity_id = f"{request.type}_{request.name.lower().replace(' ', '_')}_{datetime.now().timestamp()}"

    node = EntityNode(
        id=entity_id,
        name=request.name,
        type=request.type,
        properties=request.properties,
        created_at=datetime.now().isoformat()
    )

    graph_store.add_node(node)
    logger.info(f"创建实体: {node.name} ({node.type})")

    return node


@app.get("/api/v1/entities/{entity_id}", response_model=EntityNode)
async def get_entity(entity_id: str):
    """获取实体"""
    node = graph_store.get_node(entity_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"实体未找到: {entity_id}")
    return node


@app.get("/api/v1/entities/type/{entity_type}", response_model=list[EntityNode])
async def get_entities_by_type(entity_type: str):
    """按类型获取实体"""
    nodes = graph_store.get_nodes_by_type(entity_type)
    return nodes


@app.post("/api/v1/relations", response_model=EntityRelation)
async def create_relation(request: RelationCreateRequest):
    """创建关系"""
    # 验证节点存在
    if request.source_id not in graph_store.nodes:
        raise HTTPException(status_code=404, detail=f"源节点未找到: {request.source_id}")
    if request.target_id not in graph_store.nodes:
        raise HTTPException(status_code=404, detail=f"目标节点未找到: {request.target_id}")

    relation_id = f"{request.source_id}_{request.target_id}_{request.relation_type}"

    relation = EntityRelation(
        id=relation_id,
        source=request.source_id,
        target=request.target_id,
        relation_type=request.relation_type,
        properties=request.properties,
        weight=request.weight
    )

    graph_store.add_relation(relation)
    logger.info(f"创建关系: {request.source_id} -> {request.target_id} ({request.relation_type})")

    return relation


@app.get("/api/v1/relations/{entity_id}")
async def get_entity_relations(entity_id: str):
    """获取实体的关系"""
    if entity_id not in graph_store.nodes:
        raise HTTPException(status_code=404, detail=f"实体未找到: {entity_id}")

    outgoing = graph_store.get_relations(source_id=entity_id)
    incoming = graph_store.get_relations(target_id=entity_id)

    return {
        "entity_id": entity_id,
        "outgoing_relations": outgoing,
        "incoming_relations": incoming,
        "total": len(outgoing) + len(incoming)
    }


@app.post("/api/v1/search", response_model=GraphSearchResult)
async def search_graph(query: str = "", limit: int = 20):
    """搜索图"""
    if not query:
        raise HTTPException(status_code=400, detail="查询不能为空")

    result = graph_store.search(query, limit)
    return result


@app.get("/api/v1/neighbors/{entity_id}")
async def get_neighbors(entity_id: str, max_depth: int = 1):
    """获取邻居节点"""
    result = graph_store.get_neighbors(entity_id, max_depth)

    if not result["nodes"]:
        raise HTTPException(status_code=404, detail=f"实体未找到: {entity_id}")

    return result


@app.post("/api/v1/query")
async def query_graph(query: str = "", params: dict | None = None):
    """高级图查询"""
    # 简化实现：调用搜索
    if not query:
        raise HTTPException(status_code=400, detail="查询不能为空")

    result = graph_store.search(query, params.get("limit", 20) if params else 20)

    return {
        "success": True,
        "data": result,
        "timestamp": datetime.now().isoformat()
    }


def main():
    """主函数"""
    host = os.getenv('KG_HOST', '0.0.0.0')
    port = int(os.getenv('KG_PORT', '8002'))

    logger.info("=" * 60)
    logger.info("🧠 Athena知识图谱API服务")
    logger.info("=" * 60)
    logger.info(f"📡 服务地址: http://{host}:{port}")
    logger.info(f"📖 API文档: http://{host}:{port}/docs")
    logger.info(f"📊 健康检查: http://{host}:{port}/health")
    logger.info(f"📖 日志文件: {log_dir / 'knowledge_graph_service.log'}")
    logger.info("=" * 60)

    uvicorn.run(
        "knowledge_graph_service:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
