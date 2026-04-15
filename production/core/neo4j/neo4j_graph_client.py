#!/usr/bin/env python3
"""
Neo4j图数据库客户端
Neo4j Graph Database Client

统一的Neo4j客户端,提供简洁的API用于连接和操作Neo4j图数据库
替代NebulaGraph客户端(v2.0.0迁移)

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.1 - 修复循环导入问题
"""

from __future__ import annotations
import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

# 使用 TYPE_CHECKING 避免运行时循环导入
if TYPE_CHECKING:
    from neo4j import Driver, GraphDatabase
    from neo4j.exceptions import AuthError, ServiceUnavailable
else:
    # 延迟导入占位符
    Driver = None
    GraphDatabase = None
    ServiceUnavailable = Exception
    AuthError = Exception

from core.config.settings import get_database_config

logger = logging.getLogger(__name__)


def _import_neo4j():
    """
    延迟导入第三方 neo4j 包,避免与项目 core.neo4j 模块循环导入

    Returns:
        neo4j 模块对象
    """
    import importlib
    import sys

    # 临时移除 sys.modules 中的 core.neo4j,避免干扰
    core_neo4j_key = "core.neo4j"
    core_neo4j_init_key = "core.neo4j.__init__"

    saved_core_neo4j = sys.modules.get(core_neo4j_key)
    saved_core_neo4j_init = sys.modules.get(core_neo4j_init_key)

    # 临时移除
    if core_neo4j_key in sys.modules:
        del sys.modules[core_neo4j_key]
    if core_neo4j_init_key in sys.modules:
        del sys.modules[core_neo4j_init_key]

    try:
        # 导入第三方 neo4j 包
        neo4j_module = importlib.import_module("neo4j")
        return neo4j_module
    finally:
        # 恢复 core.neo4j 模块
        if saved_core_neo4j is not None:
            sys.modules[core_neo4j_key] = saved_core_neo4j
        if saved_core_neo4j_init is not None:
            sys.modules[core_neo4j_init_key] = saved_core_neo4j_init


@dataclass
class Neo4jConfig:
    """Neo4j连接配置"""

    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = os.getenv("NEO4J_PASSWORD", "neo4j_password")
    database: str = "neo4j"
    max_pool_size: int = 50


class Neo4jClient:
    """
    Neo4j图数据库客户端

    使用Driver进行连接管理,支持执行Cypher查询
    提供与NebulaGraph客户端类似的API接口,便于迁移
    """

    def __init__(self, config: Neo4jConfig | None = None, **kwargs):
        """
        初始化Neo4j客户端

        Args:
            config: Neo4j配置对象
            **kwargs: 直接配置参数(优先级高于config)
        """
        if config:
            self.config = config
        else:
            # 使用全局配置
            db_config = get_database_config()
            self.config = Neo4jConfig(
                uri=db_config.neo4j_uri,
                username=db_config.neo4j_username,
                password=db_config.neo4j_password,
                database=db_config.neo4j_database,
            )

        # 更新配置(如果有kwargs传入)
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        self._driver: Driver | None = None
        self._connected = False
        self._neo4j = None  # 延迟导入的 neo4j 模块

        logger.info(f"🔗 Neo4j客户端初始化: {self.config.uri}")

    def _get_neo4j(self):
        """获取第三方 neo4j 包(延迟导入)"""
        if self._neo4j is None:
            self._neo4j = _import_neo4j()
        return self._neo4j

    def connect(self) -> bool:
        """
        连接到Neo4j

        Returns:
            连接是否成功
        """
        try:
            neo4j = self._get_neo4j()

            # 创建Driver
            self._driver = neo4j.GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password),
                max_connection_pool_size=self.config.max_pool_size,
            )

            # 测试连接
            with self._driver.session(database=self.config.database) as session:
                session.run("RETURN 1")

            self._connected = True
            logger.info(f"✅ Neo4j连接成功: {self.config.database}")
            return True

        except Exception as e:
            # 动态获取异常类型
            error_msg = str(e)
            error_class = type(e).__name__

            if "authentication" in error_msg.lower() or error_class == "AuthError":
                logger.error(f"❌ Neo4j认证失败: {e}")
            elif "unavailable" in error_msg.lower() or error_class == "ServiceUnavailable":
                logger.error(f"❌ Neo4j服务不可用: {e}")
            else:
                logger.error(f"❌ Neo4j连接异常: {e}")
            return False

    def execute(self, query: str, parameters: dict[str, Any] | None = None) -> Any | None:
        """
        执行Cypher查询

        Args:
            query: Cypher查询语句
            parameters: 查询参数

        Returns:
            查询结果对象,失败返回None
        """
        if not self._connected:
            logger.error("⚠️  未连接到Neo4j,请先调用connect()")
            return None

        try:
            with self._driver.session(database=self.config.database) as session:
                result = session.run(query, parameters or {})
                logger.debug(f"✅ 查询执行成功: {query[:50]}...")
                return result

        except Exception as e:
            logger.error(f"❌ 查询执行异常: {e}")
            logger.error(f"查询语句: {query[:100]}")
            return None

    def execute_and_fetch(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        执行Cypher查询并获取所有结果

        Args:
            query: Cypher查询语句
            parameters: 查询参数

        Returns:
            结果列表
        """
        result = self.execute(query, parameters)
        if result:
            try:
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"❌ 获取结果失败: {e}")
                return []
        return []

    def get_database_info(self) -> dict[str, Any]:
        """
        获取当前数据库的信息

        Returns:
            数据库信息字典
        """
        info = {
            "database_name": self.config.database,
            "labels": [],
            "relationship_types": [],
            "nodes": 0,
            "relationships": 0,
        }

        # 获取所有Labels(节点类型)
        result = self.execute_and_fetch("CALL db.labels() YIELD label RETURN label;")
        if result:
            info["labels"] = [record["label"] for record in result]

        # 获取所有Relationship Types(关系类型)
        result = self.execute_and_fetch(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType;"
        )
        if result:
            info["relationship_types"] = [record["relationshipType"] for record in result]

        # 获取节点数量
        result = self.execute_and_fetch("MATCH (n) RETURN count(n) AS count;")
        if result:
            info["nodes"] = result[0]["count"] if result else 0

        # 获取关系数量
        result = self.execute_and_fetch("MATCH ()-[r]->() RETURN count(r) AS count;")
        if result:
            info["relationships"] = result[0]["count"] if result else 0

        return info

    def list_constraints(self) -> list[dict[str, Any]]:
        """
        列出所有约束

        Returns:
            约束列表
        """
        result = self.execute("CALL db.constraints() YIELD description RETURN description;")
        if result:
            return [{"description": record["description"]} for record in result]
        return []

    def list_indexes(self) -> list[dict[str, Any]]:
        """
        列出所有索引

        Returns:
            索引列表
        """
        result = self.execute("CALL db.indexes() YIELD * RETURN *;")
        if result:
            return [record.data() for record in result]
        return []

    def create_constraint(self, label: str, property: str) -> bool:
        """
        创建唯一性约束

        Args:
            label: 节点标签
            property: 属性名

        Returns:
            是否成功
        """
        query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{property} IS UNIQUE"
        result = self.execute(query)
        return result is not None

    def create_index(self, label: str, property: str) -> bool:
        """
        创建索引

        Args:
            label: 节点标签
            property: 属性名

        Returns:
            是否成功
        """
        query = f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.{property})"
        result = self.execute(query)
        return result is not None

    def clear_database(self) -> bool:
        """
        清空数据库(危险操作!)

        Returns:
            是否成功
        """
        # 先删除所有关系
        result1 = self.execute("MATCH ()-[r]->() DELETE r")
        # 再删除所有节点
        result2 = self.execute("MATCH (n) DELETE n")
        return result1 is not None and result2 is not None

    def close(self) -> None:
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._connected = False
            logger.info("🔌 Neo4j连接已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    @contextmanager
    def session(self, **kwargs):
        """
        创建会话上下文

        Args:
            **kwargs: 会话参数

        Yields:
            Neo4j会话对象
        """
        if not self._connected:
            self.connect()

        with self._driver.session(database=self.config.database, **kwargs) as session:
            yield session


# 兼容性接口 - 用于替换NebulaGraph客户端
class GraphClient(Neo4jClient):
    """
    图数据库客户端兼容层

    提供与NebulaGraph客户端兼容的接口,
    便于快速迁移代码
    """

    def __init__(self, **kwargs):
        """初始化客户端"""
        super().__init__(**kwargs)

    def is_succeeded(self) -> bool:
        """兼容方法:查询是否成功(由子类覆盖)"""
        return True


# 便捷函数
def get_neo4j_client(**kwargs) -> Neo4jClient:
    """
    获取Neo4j客户端实例

    Args:
        **kwargs: 连接配置参数

    Returns:
        Neo4j客户端实例
    """
    return Neo4jClient(**kwargs)


def get_graph_client(**kwargs) -> GraphClient:
    """
    获取图数据库客户端实例(兼容层)

    Args:
        **kwargs: 连接配置参数

    Returns:
        图数据库客户端实例
    """
    return GraphClient(**kwargs)


# 测试代码
if __name__ == "__main__":
    import asyncio

    def test():
        print("🧪 测试Neo4j客户端")
        print("=" * 80)

        # 创建客户端
        client = Neo4jClient()

        # 连接
        print("\n1️⃣  连接Neo4j...")
        if client.connect():
            print("✅ 连接成功")

            # 获取数据库信息
            print("\n2️⃣  获取数据库信息...")
            info = client.get_database_info()
            print(f"数据库名称: {info['database_name']}")
            print(f"节点类型: {info['labels']}")
            print(f"关系类型: {info['relationship_types']}")
            print(f"节点数: {info['nodes']}")
            print(f"关系数: {info['relationships']}")

            # 列出约束
            print("\n3️⃣  列出约束...")
            constraints = client.list_constraints()
            print(f"约束数量: {len(constraints)}")

            # 列出索引
            print("\n4️⃣  列出索引...")
            indexes = client.list_indexes()
            print(f"索引数量: {len(indexes)}")

            # 关闭连接
            client.close()
            print("\n✅ 测试完成")
        else:
            print("❌ 连接失败")

    asyncio.run(test())
