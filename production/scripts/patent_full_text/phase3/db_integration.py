#!/usr/bin/env python3
"""
数据库集成层
Database Integration Layer

负责Qdrant和NebulaGraph的连接、初始化和操作

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from core.config.secure_config import get_config

config = get_config()


# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入安全配置
try:
    from production.config import get_nebula_config
except ImportError:
    def get_nebula_config() -> Any | None:
        return {
            'host': 'localhost',
            'port': 9669,
            'user': 'root',
            "password": config.get("NEBULA_PASSWORD", required=True),
            'space': 'patent_full_text_v2'
        }

logger = logging.getLogger(__name__)


class DBType(Enum):
    """数据库类型"""
    QDRANT = "qdrant"
    NEBULA = "nebula"


class ConnectionStatus(Enum):
    """连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class ConnectionInfo:
    """连接信息"""
    db_type: DBType
    status: ConnectionStatus
    host: str
    port: int
    connected_at: float | None = None
    error_message: str | None = None


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    db_type: DBType
    is_healthy: bool
    response_time: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


class QdrantManager:
    """
    Qdrant向量数据库管理器

    负责连接、初始化、向量操作
    """

    def __init__(self):
        self.client = None
        self.connected = False
        self.collection_name = "patent_full_text_v2"

    def connect(
        self,
        host: str = "localhost",
        port: int = 6333,
        timeout: int = 60
    ):
        """
        连接到Qdrant

        Args:
            host: 主机地址
            port: 端口
            timeout: 超时时间
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, PointStruct, VectorParams

            self.client = QdrantClient(
                url=f"http://{host}:{port}",
                timeout=timeout,
                check_compatibility=False  # 禁用版本检查
            )

            # 测试连接
            collections = self.client.get_collections()
            self.connected = True

            logger.info(f"✅ 已连接到Qdrant: {host}:{port}")

        except ImportError:
            logger.warning("⚠️  qdrant-client未安装")
            self.client = None
        except Exception as e:
            logger.error(f"❌ Qdrant连接失败: {e}")
            self.client = None
            raise

    def disconnect(self) -> Any:
        """断开连接"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("✅ 已断开Qdrant连接")

    def initialize_collection(self) -> Any:
        """初始化集合"""
        if not self.client or not self.connected:
            logger.warning("⚠️  未连接到Qdrant，跳过初始化")
            return

        try:
            from qdrant_client.models import Distance, VectorParams

            # 检查集合是否存在
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name in collection_names:
                logger.info(f"📦 集合 {self.collection_name} 已存在")
                return

            # 创建集合
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=768,  # BGE-base-zh-v1.5维度
                    distance=Distance.COSINE
                )
            )

            logger.info(f"✅ 集合 {self.collection_name} 创建成功")

        except Exception as e:
            logger.error(f"❌ 集合创建失败: {e}")
            raise

    def insert_vectors(
        self,
        vectors: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        批量插入向量

        Args:
            vectors: 向量列表
                [{
                    "id": "vector_id",
                    "vector": [0.1, 0.2, ...],
                    "payload": {...}
                }]

        Returns:
            操作结果
        """
        if not self.client or not self.connected:
            return {"success": False, "error": "未连接到Qdrant"}

        try:
            from qdrant_client.models import PointStruct

            points = [
                PointStruct(
                    id=v["id"],
                    vector=v["vector"],
                    payload=v.get("payload", {})
                )
                for v in vectors
            ]

            operation_info = self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            return {
                "success": True,
                "operation_info": operation_info,
                "count": len(points)
            }

        except Exception as e:
            logger.error(f"❌ 向量插入失败: {e}")
            return {"success": False, "error": str(e)}

    def search_vectors(
        self,
        query_vector: list[float],
        limit: int = 10,
        filter_params: dict | None = None
    ) -> list[dict[str, Any]]:
        """
        向量搜索

        Args:
            query_vector: 查询向量
            limit: 返回数量
            filter_params: 过滤条件

        Returns:
            搜索结果
        """
        if not self.client or not self.connected:
            return []

        try:

            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filter_params
            )

            results = []
            for hit in search_result:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                })

            return results

        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e}")
            return []

    def health_check(self) -> HealthCheckResult:
        """健康检查"""
        start_time = time.time()

        try:
            if not self.client or not self.connected:
                return HealthCheckResult(
                    db_type=DBType.QDRANT,
                    is_healthy=False,
                    error_message="未连接"
                )

            # 尝试获取集合列表
            collections = self.client.get_collections()

            return HealthCheckResult(
                db_type=DBType.QDRANT,
                is_healthy=True,
                response_time=time.time() - start_time,
                details={
                    "collection_count": len(collections.collections),
                    "collection_names": [c.name for c in collections.collections]
                }
            )

        except Exception as e:
            return HealthCheckResult(
                db_type=DBType.QDRANT,
                is_healthy=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )


class NebulaManager:
    """
    NebulaGraph图数据库管理器

    负责连接、初始化、图操作
    """

    def __init__(self):
        self.pool = None
        self.session = None
        self.connected = False
        self.space_name = "patent_full_text_v2"

    def connect(
        self,
        host: str = None,
        port: int = None,
        space_name: str = None,
        username: str = None,
        password: str = None
    ):
        """
        连接到NebulaGraph

        Args:
            host: 主机地址 (如果为None,从配置读取)
            port: 端口 (如果为None,从配置读取)
            space_name: 空间名称 (如果为None,从配置读取)
            username: 用户名 (如果为None,从配置读取)
            password: 密码 (如果为None,从配置读取)
        """
        # 从配置获取默认值
        nebula_config = get_nebula_config()
        host = host or nebula_config.get('host', '127.0.0.1')
        port = port or nebula_config.get('port', 9669)
        space_name = space_name or nebula_config.get('space', 'patent_full_text_v2')
        username = username or nebula_config.get('user', 'root')
        password = password or nebula_config.get("password", config.get("NEBULA_PASSWORD", required=True))

        try:
            from nebula3.Config import ConfigPool
            from nebula3.gclient.net import ConnectionPool

            # 创建连接池配置
            config = ConfigPool()
            config.max_size = 10

            # 创建连接池
            self.pool = ConnectionPool()
            self.pool.init(
                [(host, port)],
                username,
                password,
                space_name,
                config
            )

            # 测试连接
            session = self.pool.session_pool.get_session()
            try:
                result = session.execute(f"USE {space_name};")
                if not result.is_succeeded():
                    logger.warning(f"⚠️  空间 {space_name} 不存在，需要初始化")
                else:
                    self.connected = True
            finally:
                session.release()

            logger.info(f"✅ 已连接到NebulaGraph: {host}:{port}/{space_name}")

        except ImportError:
            logger.warning("⚠️  nebula3未安装")
            self.pool = None
        except Exception as e:
            logger.error(f"❌ NebulaGraph连接失败: {e}")
            self.pool = None
            raise

    def disconnect(self) -> Any:
        """断开连接"""
        if self.pool:
            self.pool.close()
            self.connected = False
            logger.info("✅ 已断开NebulaGraph连接")

    def initialize_space(self, ngql_file: str | None = None) -> Any:
        """
        初始化空间

        Args:
            ngql_file: NGQL脚本文件路径（可选）
        """
        if not self.pool:
            logger.warning("⚠️  未连接到NebulaGraph，跳过初始化")
            return

        try:
            session = self.pool.session_pool.get_session()
            try:
                # 创建空间
                create_space_sql = f"""
                CREATE SPACE IF NOT EXISTS {self.space_name} (
                    partition_num = 10,
                    replica_factor = 1,
                    vid_type = FIXED_STRING(32)
                );
                """
                result = session.execute(create_space_sql)
                if result.is_succeeded():
                    logger.info(f"✅ 空间 {self.space_name} 已存在或创建成功")
                else:
                    logger.error(f"❌ 空间创建失败: {result.error_msg()}")

            finally:
                session.release()

        except Exception as e:
            logger.error(f"❌ 空间初始化失败: {e}")

    def execute_ngql(self, ngql: str) -> dict[str, Any]:
        """
        执行NGQL语句

        Args:
            ngql: NGQL语句

        Returns:
            执行结果
        """
        if not self.pool:
            return {"success": False, "error": "未连接到NebulaGraph"}

        try:
            session = self.pool.session_pool.get_session()
            try:
                result = session.execute(ngql)

                if result.is_succeeded():
                    return {
                        "success": True,
                        "data": result.data(),
                        "latency": result.latency()
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error_msg()
                    }

            finally:
                session.release()

        except Exception as e:
            logger.error(f"❌ NGQL执行失败: {e}")
            return {"success": False, "error": str(e)}

    def health_check(self) -> HealthCheckResult:
        """健康检查"""
        start_time = time.time()

        try:
            if not self.pool:
                return HealthCheckResult(
                    db_type=DBType.NEBULA,
                    is_healthy=False,
                    error_message="连接池未初始化"
                )

            # 测试查询
            session = self.pool.session_pool.get_session()
            try:
                result = session.execute("SHOW SPACES;")
                if result.is_succeeded():
                    spaces = [row[0] for row in result.data()]

                    return HealthCheckResult(
                        db_type=DBType.NEBULA,
                        is_healthy=True,
                        response_time=time.time() - start_time,
                        details={"spaces": spaces}
                    )
                else:
                    return HealthCheckResult(
                        db_type=DBType.NEBULA,
                        is_healthy=False,
                        error_message=result.error_msg()
                    )
            finally:
                session.release()

        except Exception as e:
            return HealthCheckResult(
                db_type=DBType.NEBULA,
                is_healthy=False,
                response_time=time.time() - start_time,
                error_message=str(e)
            )


@dataclass
class DBIntegrationConfig:
    """数据库集成配置"""
    # Qdrant配置
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_timeout: int = 60
    qdrant_collection: str = "patent_full_text_v2"

    # NebulaGraph配置 - 从环境变量读取
    @property
    def nebula_host(self) -> str:
        nebula_config = get_nebula_config()
        return nebula_config.get('host', '127.0.0.1')

    @property
    def nebula_port(self) -> int:
        nebula_config = get_nebula_config()
        return nebula_config.get('port', 9669)

    @property
    def nebula_space(self) -> str:
        nebula_config = get_nebula_config()
        return nebula_config.get('space', 'patent_full_text_v2')

    @property
    def nebula_username(self) -> str:
        nebula_config = get_nebula_config()
        return nebula_config.get('user', 'root')

    @property
    def nebula_password(self) -> str:
        nebula_config = get_nebula_config()
        return nebula_config.get("password", config.get("NEBULA_PASSWORD", required=True))


class DatabaseIntegration:
    """
    数据库集成层

    统一管理Qdrant和NebulaGraph的连接和操作
    """

    def __init__(self, config: DBIntegrationConfig | None = None):
        """
        初始化数据库集成层

        Args:
            config: 配置对象
        """
        self.config = config or DBIntegrationConfig()

        # 管理器
        self.qdrant = QdrantManager()
        self.nebula = NebulaManager()

        # 连接信息
        self.connections: list[ConnectionInfo] = []

    def connect_all(self) -> dict[str, bool]:
        """
        连接所有数据库

        Returns:
            {db_name: success}
        """
        results = {}

        # 连接Qdrant
        try:
            self.qdrant.connect(
                host=self.config.qdrant_host,
                port=self.config.qdrant_port,
                timeout=self.config.qdrant_timeout
            )
            results["qdrant"] = True
            self.connections.append(ConnectionInfo(
                db_type=DBType.QDRANT,
                status=ConnectionStatus.CONNECTED,
                host=self.config.qdrant_host,
                port=self.config.qdrant_port,
                connected_at=time.time()
            ))
        except Exception as e:
            logger.error(f"❌ Qdrant连接失败: {e}")
            results["qdrant"] = False
            self.connections.append(ConnectionInfo(
                db_type=DBType.QDRANT,
                status=ConnectionStatus.ERROR,
                host=self.config.qdrant_host,
                port=self.config.qdrant_port,
                error_message=str(e)
            ))

        # 连接NebulaGraph
        try:
            self.nebula.connect(
                host=self.config.nebula_host,
                port=self.config.nebula_port,
                space_name=self.config.nebula_space,
                username=self.config.nebula_username,
                password=self.config.nebula_password
            )
            results["nebula"] = True
            self.connections.append(ConnectionInfo(
                db_type=DBType.NEBULA,
                status=ConnectionStatus.CONNECTED,
                host=self.config.nebula_host,
                port=self.config.nebula_port,
                connected_at=time.time()
            ))
        except Exception as e:
            logger.error(f"❌ NebulaGraph连接失败: {e}")
            results["nebula"] = False
            self.connections.append(ConnectionInfo(
                db_type=DBType.NEBULA,
                status=ConnectionStatus.ERROR,
                host=self.config.nebula_host,
                port=self.config.nebula_port,
                error_message=str(e)
            ))

        return results

    def disconnect_all(self) -> Any:
        """断开所有连接"""
        self.qdrant.disconnect()
        self.nebula.disconnect()
        self.connections.clear()

    def initialize_databases(self) -> Any:
        """初始化数据库（创建集合/空间）"""
        # 初始化Qdrant集合
        self.qdrant.initialize_collection()

        # 初始化NebulaGraph空间
        self.nebula.initialize_space()

    def health_check_all(self) -> list[HealthCheckResult]:
        """健康检查所有数据库"""
        results = []
        results.append(self.qdrant.health_check())
        results.append(self.nebula.health_check())
        return results

    def get_connection_status(self) -> dict[str, ConnectionInfo]:
        """获取连接状态"""
        return {
            "qdrant": next((c for c in self.connections if c.db_type == DBType.QDRANT), None),
            "nebula": next((c for c in self.connections if c.db_type == DBType.NEBULA), None)
        }


# ========== 便捷函数 ==========

def create_db_integration(**kwargs) -> DatabaseIntegration:
    """创建数据库集成层"""
    config = DBIntegrationConfig(**kwargs)
    return DatabaseIntegration(config)


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("数据库集成层示例")
    print("=" * 70)

    # 创建集成层
    db_integration = create_db_integration()

    # 连接所有数据库
    print("\n📡 连接数据库...")
    connection_results = db_integration.connect_all()

    for db_name, success in connection_results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {db_name}")

    # 健康检查
    print("\n🏥 健康检查...")
    health_results = db_integration.health_check_all()

    for result in health_results:
        status = "✅" if result.is_healthy else "❌"
        print(f"  {status} {result.db_type.value}: {result.response_time*1000:.2f}ms")

    # 断开连接
    print("\n🔌 断开连接...")
    db_integration.disconnect_all()
    print("✅ 所有连接已关闭")


if __name__ == "__main__":
    main()
