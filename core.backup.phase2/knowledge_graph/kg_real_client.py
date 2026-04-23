#!/usr/bin/env python3
from __future__ import annotations
"""
知识图谱真实客户端

连接到现有的知识图谱服务 (http://localhost:PORT)
"""

import asyncio
import logging
from typing import Any

import aiohttp

from .kg_integration import (
    Entity,
    EntityType,
    GraphPath,
    KnowledgeGraphClient,
    Relation,
    RelationType,
)

logger = logging.getLogger(__name__)


class RealKnowledgeGraphClient(KnowledgeGraphClient):
    """
    真实知识图谱客户端

    连接到本地的知识图谱服务API
    默认地址: http://localhost:8100 (知识图谱服务端口)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8100",
        timeout: float = 30.0,
        retry_attempts: int = 3,
    ):
        """
        初始化真实知识图谱客户端

        Args:
            base_url: 知识图谱服务的基础URL
            timeout: 请求超时时间(秒)
            retry_attempts: 失败重试次数
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建aiohttp会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """关闭客户端连接"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """
        发送HTTP请求到知识图谱服务

        Args:
            method: HTTP方法
            endpoint: API端点
            **kwargs: 额外参数

        Returns:
            响应数据字典
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.retry_attempts):
            try:
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientError as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt == self.retry_attempts - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))  # 指数退避

        return {}

    async def search_entities(
        self, query: str, entity_type: EntityType | None = None, limit: int = 10
    ) -> list[Entity]:
        """
        搜索实体

        Args:
            query: 搜索关键词
            entity_type: 实体类型过滤
            limit: 返回数量限制

        Returns:
            实体列表
        """
        try:
            # 构建请求参数
            params = {"query": query, "limit": limit}
            if entity_type:
                params["entity_type"] = entity_type.value

            # 发送请求 - 使用知识图谱服务的搜索API
            data = await self._request("GET", "/api/v1/search/entities", params=params)

            # 转换响应为Entity对象
            entities = []
            for item in data.get("entities", []):
                entities.append(
                    Entity(
                        id=item.get("id", ""),
                        name=item.get("name", ""),
                        type=EntityType(item.get("type", "concept")),
                        properties=item.get("properties", {}),
                    )
                )

            logger.info(f"搜索到 {len(entities)} 个实体")
            return entities

        except Exception as e:
            logger.error(f"搜索实体失败: {e}")
            return []

    async def get_relations(
        self, entity_id: str, relation_type: RelationType | None = None, direction: str = "out"
    ) -> list[Relation]:
        """
        获取实体的关系

        Args:
            entity_id: 实体ID
            relation_type: 关系类型过滤
            direction: 关系方向 (in/out/both)

        Returns:
            关系列表
        """
        try:
            # 构建请求参数
            params = {"entity_id": entity_id, "direction": direction}
            if relation_type:
                params["relation_type"] = relation_type.value

            # 发送请求
            data = await self._request("GET", "/api/v1/graph/relations", params=params)

            # 转换响应为Relation对象
            relations = []
            for item in data.get("relations", []):
                relations.append(
                    Relation(
                        id=item.get("id", ""),
                        from_entity=item.get(
                            "from_entity", item.get("source", "")
                        ),  # 兼容source字段
                        to_entity=item.get("to_entity", item.get("target", "")),  # 兼容target字段
                        type=RelationType(item.get("type", "related_to")),
                        properties=item.get("properties", {}),
                    )
                )

            return relations

        except Exception as e:
            logger.error(f"获取关系失败: {e}")
            return []

    async def find_paths(
        self, from_entity: str, to_entity: str, max_depth: int = 3, max_paths: int = 10
    ) -> list[GraphPath]:
        """
        查找两个实体之间的路径

        Args:
            from_entity: 起始实体ID
            to_entity: 目标实体ID
            max_depth: 最大搜索深度
            max_paths: 最大返回路径数

        Returns:
            路径列表
        """
        try:
            # 构建请求参数
            params = {
                "from": from_entity,
                "to": to_entity,
                "max_depth": max_depth,
                "limit": max_paths,
            }

            # 发送请求
            data = await self._request("GET", "/api/v1/graph/paths", params=params)

            # 转换响应为GraphPath对象
            paths = []
            for item in data.get("paths", []):
                path_entities = [
                    Entity(
                        id=e.get("id", ""),
                        name=e.get("name", ""),
                        type=EntityType(e.get("type", "concept")),
                        properties=e.get("properties", {}),
                    )
                    for e in item.get("entities", [])
                ]
                path_relations = [
                    Relation(
                        id=r.get("id", ""),
                        from_entity=r.get("from_entity", r.get("source", "")),
                        to_entity=r.get("to_entity", r.get("target", "")),
                        type=RelationType(r.get("type", "related_to")),
                        properties=r.get("properties", {}),
                    )
                    for r in item.get("relations", [])
                ]
                paths.append(
                    GraphPath(
                        entities=path_entities,
                        relations=path_relations,
                        score=item.get("score", 0.0),
                    )
                )

            return paths

        except Exception as e:
            logger.error(f"查找路径失败: {e}")
            return []

    async def get_entity(self, entity_id: str) -> Entity | None:
        """
        获取实体详情

        Args:
            entity_id: 实体ID

        Returns:
            实体对象,如果不存在返回None
        """
        try:
            # 发送请求获取实体详情
            data = await self._request("GET", f"/api/v1/entities/{entity_id}")

            # 转换响应为Entity对象
            return Entity(
                id=data.get("id", entity_id),
                name=data.get("name", ""),
                type=EntityType(data.get("type", "concept")),
                properties=data.get("properties", {}),
                embedding=data.get("embedding"),  # 可选的向量嵌入
            )

        except Exception as e:
            logger.warning(f"获取实体失败 (ID: {entity_id}): {e}")
            return None

    async def get_neighbors(
        self, entity_id: str, depth: int = 1, relation_types: list[RelationType] | None = None
    ) -> dict[str, list[Entity]]:
        """
        获取邻居实体

        Args:
            entity_id: 实体ID
            depth: 邻居深度
            relation_types: 关系类型过滤

        Returns:
            邻居实体字典 {"neighbors": [Entity, ...]}
        """
        try:
            # 获取关系(支持类型过滤)
            relations = await self.get_relations(
                entity_id,
                relation_type=relation_types[0] if relation_types else None,
                direction="both",
            )

            # 如果有多个关系类型,获取所有类型的关系
            if relation_types and len(relation_types) > 1:
                for rel_type in relation_types[1:]:
                    more_relations = await self.get_relations(
                        entity_id, relation_type=rel_type, direction="both"
                    )
                    relations.extend(more_relations)

            # 提取邻居实体ID
            neighbor_ids = set()
            for rel in relations:
                neighbor_ids.add(rel.from_entity)
                neighbor_ids.add(rel.to_entity)

            neighbor_ids.discard(entity_id)  # 排除自己

            # 获取邻居实体详情
            neighbors = []
            for nid in list(neighbor_ids)[:50]:  # 限制数量
                try:
                    entity = await self.get_entity(nid)
                    if entity:
                        neighbors.append(entity)
                except Exception as e:
                    # 单个实体获取失败不应该影响其他实体
                    logger.debug(f"获取邻居实体失败 (ID: {nid}): {e}")
                    continue

            return {"neighbors": neighbors}

        except Exception as e:
            logger.error(f"获取邻居失败: {e}")
            return {"neighbors": []}

    async def add_entity(
        self, name: str, entity_type: EntityType, properties: dict[str, Any]
    ) -> Entity:
        """
        添加新实体

        Args:
            name: 实体名称
            entity_type: 实体类型
            properties: 实体属性

        Returns:
            创建的实体
        """
        try:
            payload = {"name": name, "type": entity_type.value, "properties": properties}

            data = await self._request("POST", "/api/v1/entities", json=payload)

            return Entity(id=data.get("id", ""), name=name, type=entity_type, properties=properties)

        except Exception as e:
            logger.error(f"添加实体失败: {e}")
            raise

    async def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        properties: dict[str, Any],    ) -> Relation:
        """
        添加新关系

        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            properties: 关系属性

        Returns:
            创建的关系
        """
        try:
            payload = {
                "source": source_id,
                "target": target_id,
                "type": relation_type.value,
                "properties": properties,
            }

            data = await self._request("POST", "/api/v1/relations", json=payload)

            return Relation(
                id=data.get("id", ""),
                from_entity=source_id,
                to_entity=target_id,
                type=relation_type,
                properties=properties,
            )

        except Exception as e:
            logger.error(f"添加关系失败: {e}")
            raise

    async def expand_concept(self, concept: str, expand_type: str = "hierarchy") -> list[Entity]:
        """
        扩展概念(获取父概念、子概念、相关概念)

        Args:
            concept: 概念名称
            expand_type: 扩展类型 ("hierarchy", "related", "both")

        Returns:
            扩展的概念列表
        """
        try:
            # 构建请求参数
            params = {"concept": concept, "expand_type": expand_type}

            # 发送请求
            data = await self._request("GET", "/api/v1/concepts/expand", params=params)

            # 转换响应为Entity对象列表
            entities = []
            for item in data.get("concepts", []):
                entities.append(
                    Entity(
                        id=item.get("id", ""),
                        name=item.get("name", ""),
                        type=EntityType(item.get("type", "concept")),
                        properties=item.get("properties", {}),
                    )
                )

            logger.info(f"扩展概念 '{concept}' 得到 {len(entities)} 个相关概念")
            return entities

        except Exception as e:
            logger.error(f"扩展概念失败: {e}")
            return []

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            服务是否可用
        """
        try:
            data = await self._request("GET", "/health")
            return data.get("status") == "healthy"
        except Exception as e:
            # 健康检查失败不是错误,记录并返回False
            logger.debug(f"健康检查失败: {e}")
            return False


# 工厂函数
def create_knowledge_graph_client(client_type: str = "real", **kwargs) -> KnowledgeGraphClient:
    """
    创建知识图谱客户端

    Args:
        client_type: 客户端类型 ("real" 或 "mock")
        **kwargs: 客户端配置参数

    Returns:
        知识图谱客户端实例
    """
    if client_type == "real":
        return RealKnowledgeGraphClient(**kwargs)
    else:
        from .kg_integration import MockKnowledgeGraphClient

        return MockKnowledgeGraphClient(**kwargs)


# 导出
__all__ = [
    "RealKnowledgeGraphClient",
    "create_knowledge_graph_client",
]
