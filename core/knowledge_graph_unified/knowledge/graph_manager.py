#!/usr/bin/env python3

"""
知识图谱管理器
Knowledge Graph Manager

提供统一的知识图谱管理接口，支持Neo4j作为后端存储
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class KnowledgeGraphManager:
    """
    知识图谱管理器

    提供知识图谱的创建、查询、更新等功能
    作为Neo4jManager的适配器，提供更高级的抽象接口
    """

    def __init__(self, uri: str = 'bolt://localhost:7687',
                 username: str = 'neo4j', password: str = 'password',
                 database: str = 'patent_kg'):
        """
        初始化知识图谱管理器

        Args:
            uri: Neo4j服务器URI
            username: 用户名
            password: 密码
            database: 数据库名称
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self._neo4j_manager = None
        self._connected = False

    def connect(self) -> bool:
        """连接到知识图谱"""
        try:
            from patents.platform.workspace.src.knowledge_graph.neo4j_manager import Neo4jManager

            self._neo4j_manager = Neo4jManager(
                uri=self.uri,
                username=self.username,
                password=self.password,
                database=self.database
            )

            self._connected = self._neo4j_manager.connect()
            if self._connected:
                logger.info("知识图谱管理器连接成功")
            else:
                logger.warning("知识图谱管理器连接失败")

            return self._connected

        except ImportError as e:
            logger.warning(f"无法导入Neo4j管理器: {e}")
            logger.info("知识图谱功能将使用模拟模式")
            return False
        except Exception as e:
            logger.error(f"连接知识图谱失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        if self._neo4j_manager:
            self._neo4j_manager.close()
            self._connected = False

    def search_nodes(self, query: str, node_types: Optional[list[str]] = None,
                    max_depth: int = 2, limit: int = 20) -> list[dict[str, Any]]:
        """
        搜索知识图谱节点

        Args:
            query: 查询字符串
            node_types: 节点类型列表
            max_depth: 最大深度
            limit: 返回结果数量限制

        Returns:
            节点列表
        """
        if not self._connected or not self._neo4j_manager:
            # 返回模拟数据
            return self._get_mock_nodes(query, limit)

        try:
            # 使用Neo4j管理器进行搜索
            results = self._neo4j_manager.search_entities(
                entity_type=node_types[0] if node_types else None,
                name_pattern=query,
                limit=limit
            )

            # 格式化结果
            nodes = []
            for entity in results:
                nodes.append({
                    'id': entity.get('id'),
                    'name': entity.get('name'),
                    'type': entity.get('type'),
                    'description': entity.get('description'),
                    'properties': entity
                })

            return nodes

        except Exception as e:
            logger.error(f"搜索节点失败: {e}")
            return self._get_mock_nodes(query, limit)

    def search_relations(self, source_id: Optional[str] = None,
                        target_id: Optional[str] = None,
                        relation_type: Optional[str] = None,
                        limit: int = 20) -> list[dict[str, Any]]:
        """
        搜索关系

        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            relation_type: 关系类型
            limit: 返回结果数量限制

        Returns:
            关系列表
        """
        if not self._connected or not self._neo4j_manager:
            return []

        try:
            if source_id:
                results = self._neo4j_manager.query_relations(
                    entity_id=source_id,
                    relation_type=relation_type
                )

                relations = []
                for rel in results[:limit]:
                    relations.append({
                        'source': rel.get('source', {}),
                        'target': rel.get('target', {}),
                        'relation': rel.get('relation', {}),
                        'type': rel.get('relation', {}).get('type')
                    })

                return relations

            return []

        except Exception as e:
            logger.error(f"搜索关系失败: {e}")
            return []

    def get_statistics(self) -> dict[str, Any]:
        """获取知识图谱统计信息"""
        if not self._connected or not self._neo4j_manager:
            return {
                'total_nodes': 0,
                'total_relations': 0,
                'node_types': {},
                'relation_types': {}
            }

        try:
            stats = self._neo4j_manager.get_knowledge_graph_statistics()
            return {
                'total_nodes': stats.get('total_entities', 0),
                'total_relations': stats.get('total_relations', 0),
                'node_types': stats.get('entity_types', {}),
                'relation_types': stats.get('relation_types', {})
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_nodes': 0,
                'total_relations': 0,
                'node_types': {},
                'relation_types': {}
            }

    def execute_query(self, cypher: str, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        """
        执行Cypher查询

        Args:
            cypher: Cypher查询语句
            params: 查询参数

        Returns:
            查询结果列表
        """
        if not self._connected or not self._neo4j_manager:
            return []

        try:
            return self._neo4j_manager.execute_cypher_query(cypher, params)
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            return []

    def _get_mock_nodes(self, query: str, limit: int) -> list[dict[str, Any]]:
        """获取模拟节点数据"""
        # 基于查询返回一些模拟数据
        mock_nodes = []

        # 专利相关节点
        if '专利' in query or 'patent' in query.lower():
            mock_nodes.extend([
                {
                    'id': 'concept_1',
                    'name': '专利',
                    'type': '概念',
                    'description': '专利是保护发明创造的一种法律制度',
                    'properties': {'legal_protection': True}
                },
                {
                    'id': 'concept_2',
                    'name': '发明专利',
                    'type': '专利类型',
                    'description': '针对产品、方法或其改进所提出的新的技术方案',
                    'properties': {'protection_term': '20年'}
                },
                {
                    'id': 'concept_3',
                    'name': '实用新型',
                    'type': '专利类型',
                    'description': '针对产品的形状、构造或其结合所提出的适于实用的新的技术方案',
                    'properties': {'protection_term': '10年'}
                }
            ])

        # 法律相关节点
        if '法' in query or 'law' in query.lower():
            mock_nodes.extend([
                {
                    'id': 'law_1',
                    'name': '专利法',
                    'type': '法律',
                    'description': '中华人民共和国专利法',
                    'properties': {'issuing_authority': '全国人大常委会'}
                }
            ])

        # 程序相关节点
        mock_nodes.extend([
            {
                'id': 'procedure_1',
                'name': '专利申请流程',
                'type': '程序',
                'description': '提交申请 → 初步审查 → 实质审查 → 授权/驳回',
                'properties': {
                    'steps': ['提交申请', '初步审查', '实质审查', '授权'],
                    'estimated_time': '2-3年'
                }
            }
        ])

        return mock_nodes[:limit]

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 便捷函数
def create_graph_manager(**kwargs) -> KnowledgeGraphManager:
    """
    创建知识图谱管理器实例

    Args:
        **kwargs: 传递给KnowledgeGraphManager的参数

    Returns:
        KnowledgeGraphManager实例
    """
    return KnowledgeGraphManager(**kwargs)

