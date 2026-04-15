#!/usr/bin/env python3
"""
NebulaGraph图数据库客户端 (兼容层)
NebulaGraph Graph Database Client (Compatibility Layer)

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

此模块提供与旧版NebulaGraph客户端兼容的接口，实际使用Neo4j作为后端。
所有实现都委托给 core.neo4j.neo4j_graph_client 模块。

迁移说明:
- 使用 Neo4j 替代 NebulaGraph
- nGQL 查询转换为 Cypher 查询
- SessionPool 替换为 GraphDatabase.driver

作者: 小诺·双鱼公主
创建时间: 2025-12-24
更新时间: 2026-01-25 (TD-001: 迁移到Neo4j)
"""

from __future__ import annotations
import logging
import os
import warnings
from dataclasses import dataclass
from typing import Any

warnings.warn(
    "NebulaGraph客户端已废弃(TD-001)，请使用 core.neo4j.neo4j_graph_client",
    DeprecationWarning,
    stacklevel=2,
)

# 从Neo4j模块导入实际实现
from core.neo4j.neo4j_graph_client import (
    Neo4jClient,
    Neo4jConfig,
)

logger = logging.getLogger(__name__)


# 兼容层配置类
@dataclass
class NebulaGraphConfig:
    """
    NebulaGraph连接配置 (兼容层)

    实际映射到Neo4jConfig，参数映射：
    - host + port -> uri (bolt://host:port)
    - space_name -> database
    - pool_size -> max_pool_size
    """

    host: str = "127.0.0.1"
    port: int = 9669
    username: str = "root"
    password: str = os.getenv("NEBULA_PASSWORD", "nebula")
    space_name: str = "patent_kg"
    pool_size: int = 10

    def __post_init__(self):
        """验证配置参数"""
        import re

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", self.space_name):
            raise ValueError(
                f"Invalid space_name: {self.space_name}. Only letters, numbers and underscores are allowed."
            )

    def to_neo4j_config(self) -> Neo4jConfig:
        """转换为Neo4j配置"""
        uri = f"bolt://{self.host}:{self.port}"
        return Neo4jConfig(
            uri=uri,
            username=self.username,
            password=self.password,
            database=self.space_name,
            max_pool_size=self.pool_size,
        )


# 兼容层客户端类
class Neo4jClient(Neo4jClient):
    """
    NebulaGraph图数据库客户端 (兼容层)

    继承自Neo4j客户端，提供与旧版NebulaGraph客户端兼容的API接口。
    方法映射：
    - connect() -> connect()
    - execute() -> execute()
    - get_space_info() -> get_database_info()
    - list_spaces() -> (不适用，返回当前database)
    """

    def __init__(self, config: NebulaGraphConfig | None = None, **kwargs):
        """
        初始化NebulaGraph客户端 (兼容层)

        Args:
            config: NebulaGraph配置对象
            **kwargs: 直接配置参数(优先级高于config)
        """
        # 转换配置
        if config:
            neo4j_config = config.to_neo4j_config()
        else:
            # 从kwargs创建NebulaGraphConfig
            nebula_config = NebulaGraphConfig(**kwargs)
            neo4j_config = nebula_config.to_neo4j_config()

        # 调用父类初始化
        super().__init__(config=neo4j_config, **kwargs)

        # 保存原始配置
        self._nebula_config = config or NebulaGraphConfig(**kwargs)

        # 兼容属性
        self._connected = False  # 将由父类管理
        self._pool = None  # 替换为driver的别名

    @property
    def config(self):
        """兼容属性: 返回nebula配置"""
        return self._nebula_config

    @property
    def _pool(self):
        """兼容属性: 返回driver (替代pool)"""
        return self._driver

    @_pool.setter
    def _pool(self, value):
        """兼容属性: 设置driver"""
        self._driver = value

    def connect(self) -> bool:
        """
        连接到Neo4j (兼容方法)

        Returns:
            连接是否成功
        """
        result = super().connect()
        if result:
            self._connected = True
        return result

    def execute(self, query: str) -> Any | None:
        """
        执行查询 (兼容方法，自动转换nGQL到Cypher)

        Args:
            query: nGQL/Cypher查询语句

        Returns:
            查询结果对象,失败返回None
        """
        # 自动转换常见的nGQL到Cypher
        cypher_query = self._convert_ngql_to_cypher(query)
        return super().execute(cypher_query)

    def _convert_ngql_to_cypher(self, query: str) -> str:
        """
        转换nGQL到Cypher (简化版本)

        Args:
            query: nGQL查询语句

        Returns:
            Cypher查询语句
        """
        # 常见转换
        conversions = [
            # SHOW TAGS -> CALL db.labels()
            (r"SHOW TAGS", "CALL db.labels() YIELD label RETURN label"),
            # SHOW EDGES -> CALL db.relationshipTypes()
            (r"SHOW EDGES", "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"),
            # SHOW SPACES -> (Neo4j不直接支持，返回当前database)
            (r"SHOW SPACES", "RETURN 'neo4j' AS name"),
        ]

        for ngql, cypher in conversions:
            if ngql in query.upper():
                return cypher

        # 如果没有匹配，返回原查询（假设已经是Cypher）
        return query

    def get_space_info(self) -> dict[str, Any]:
        """
        获取当前Space的信息 (兼容方法)

        Returns:
            Space信息字典
        """
        info = self.get_database_info()

        # 转换键名以保持兼容性
        return {
            "space_name": info.get("database_name", self._nebula_config.space_name),
            "tags": info.get("labels", []),
            "edge_types": info.get("relationship_types", []),
            "nodes": info.get("nodes", 0),
            "edges": info.get("relationships", 0),
        }

    def list_spaces(self) -> list[str]:
        """
        列出所有Space (兼容方法)

        Neo4j只支持单个database，返回当前database

        Returns:
            Database名称列表
        """
        return [self._nebula_config.space_name]


# 便捷函数
def get_neo4j_client(**kwargs) -> Neo4jClient:
    """
    获取NebulaGraph客户端实例 (兼容层)

    实际返回使用Neo4j后端的客户端

    Args:
        **kwargs: 连接配置参数

    Returns:
        NebulaGraph客户端实例 (Neo4j后端)
    """
    return Neo4jClient(**kwargs)


# 兼容层: SessionPool (用于保持与旧代码的兼容)
class SessionPool:
    """
    SessionPool兼容类 (占位符)

    此类仅用于类型兼容，实际使用Neo4j的Driver
    """

    def __init__(self, *args, **kwargs):
        """占位符初始化"""
        logger.warning(
            "SessionPool是NebulaGraph的概念，当前使用Neo4j Driver。"
            "请使用Neo4jClient代替。"
        )

    def init(self, *args, **kwargs):
        """占位符方法"""
        return True

    def execute(self, *args, **kwargs):
        """占位符方法"""
        return None

    def close(self):
        """占位符方法"""
        pass


# 兼容层: SessionPoolConfig (用于保持与旧代码的兼容)
class SessionPoolConfig:
    """
    SessionPoolConfig兼容类 (占位符)

    此类仅用于类型兼容
    """

    def __init__(self, **kwargs):
        """占位符初始化"""
        self.max_connection_pool_size = kwargs.get("max_connection_pool_size", 50)


# 测试代码
if __name__ == "__main__":
    import asyncio

    async def test():
        print("🧪 测试NebulaGraph客户端 (Neo4j后端)")
        print("=" * 80)

        # 创建客户端
        client = Neo4jClient(
            host="127.0.0.1",
            port=7687,  # Neo4j默认端口
            username="neo4j",
            password="password",
            space_name="neo4j",  # Neo4j使用database概念
        )

        # 连接
        print("\n1️⃣  连接Neo4j...")
        if client.connect():
            print("✅ 连接成功")

            # 获取Space信息
            print("\n2️⃣  获取Space信息...")
            info = client.get_space_info()
            print(f"Space名称: {info['space_name']}")
            print(f"Tags: {info['tags']}")
            print(f"Edge Types: {info['edge_types']}")
            print(f"节点数: {info['nodes']}")
            print(f"边数: {info['edges']}")

            # 列出所有Space
            print("\n3️⃣  列出所有Space...")
            spaces = client.list_spaces()
            print(f"Spaces: {spaces}")

            # 关闭连接
            client.close()
            print("\n✅ 测试完成")
        else:
            print("❌ 连接失败")

    asyncio.run(test())
