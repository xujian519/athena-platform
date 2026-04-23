#!/usr/bin/env python3
"""
法律世界模型启动与验证脚本
Legal World Model Startup and Verification Script

功能:
1. 启动/检查三层数据库 (PostgreSQL本地, Qdrant/Neo4j持久化)
2. 验证数据库连接和数据量
3. 显示法律世界模型状态

Author: Athena Team
Version: 1.0.0
Date: 2026-03-06
"""

import asyncio
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 第三方库导入
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("⚠️ psycopg2未安装，PostgreSQL功能不可用")

try:
    from neo4j import AsyncGraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️ neo4j未安装，Neo4j功能不可用")

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("⚠️ qdrant-client未安装，Qdrant功能不可用")


@dataclass
class DatabaseStatus:
    """数据库状态"""
    name: str
    type: str
    host: str
    port: int
    connected: bool = False
    data_volume: int = 0
    collections_count: int = 0
    error: str = ""
    details: dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class LegalWorldVerifier:
    """法律世界模型验证器"""

    def __init__(self):
        """初始化验证器"""
        self.databases: list[DatabaseStatus] = []
        self.startup_time = datetime.now()

    async def verify_all(self) -> dict[str, Any]:
        """验证所有数据库"""
        print("=" * 70)
        print("⚖️ 法律世界模型启动与验证")
        print("=" * 70)
        print()

        # 1. 检查Docker服务
        await self._check_docker_services()

        # 2. 验证PostgreSQL (本地)
        await self._verify_postgresql()

        # 3. 验证Qdrant (持久化)
        await self._verify_qdrant()

        # 4. 验证Neo4j (持久化)
        await self._verify_neo4j()

        # 5. 生成总结报告
        return self._generate_report()

    async def _check_docker_services(self):
        """检查Docker服务状态"""
        print("🔍 检查Docker服务...")
        print("-" * 70)

        try:
            # 检查Docker是否运行
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                containers = json.loads(result.stdout)

                # 检查关键服务
                services = {
                    "athena-qdrant": "Qdrant向量数据库",
                    "athena-neo4j": "Neo4j图数据库",
                }

                for container_name, service_name in services.items():
                    matching = [c for c in containers if c.get("Names", [""])[0].replace("/", "") == container_name]
                    if matching:
                        state = matching[0].get("State", "unknown")
                        print(f"  ✅ {service_name}: 运行中 ({state})")
                    else:
                        print(f"  ⚠️ {service_name}: 未运行")
                        print(f"     💡 启动命令: docker-compose up -d {container_name}")

                print()
            else:
                print("  ❌ Docker未运行")
                print()

        except Exception as e:
            print(f"  ❌ 检查失败: {e}")
            print()

    async def _verify_postgresql(self):
        """验证PostgreSQL"""
        print("📊 验证PostgreSQL (本地)")
        print("-" * 70)

        if not POSTGRES_AVAILABLE:
            print("  ❌ psycopg2未安装，无法验证PostgreSQL")
            self.databases.append(DatabaseStatus(
                name="PostgreSQL",
                type="关系型数据库",
                host="localhost",
                port=5432,
                connected=False,
                error="psycopg2未安装"
            ))
            print()
            return

        try:
            # 连接PostgreSQL
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres",
                password="postgres",
                connect_timeout=10
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # 检查数据库列表
            cursor.execute("""
                SELECT datname, pg_database_size(datname) as size
                FROM pg_database
                WHERE datistemplate = false
                ORDER BY pg_database_size(datname) DESC
            """)
            databases = cursor.fetchall()

            # 检查专利相关表
            cursor.execute("""
                SELECT schemaname, tablename
                FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schemaname, tablename
            """)
            tables = cursor.fetchall()

            # 计算总数据量
            total_size = sum([db[1] for db in databases if db[1]])

            status = DatabaseStatus(
                name="PostgreSQL",
                type="关系型数据库",
                host="localhost",
                port=5432,
                connected=True,
                data_volume=total_size,
                collections_count=len(databases),
                details={
                    "databases": [{"name": db[0], "size": db[1]} for db in databases[:10]],
                    "tables": [{"schema": t[0], "table": t[1]} for t in tables[:20]],
                }
            )

            print("  ✅ 连接成功: localhost:5432")
            print(f"  📦 数据库数量: {len(databases)}")
            print(f"  📋 表数量: {len(tables)}")
            print(f"  💾 总数据量: {self._format_bytes(total_size)}")

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            status = DatabaseStatus(
                name="PostgreSQL",
                type="关系型数据库",
                host="localhost",
                port=5432,
                connected=False,
                error=str(e)
            )

        self.databases.append(status)
        print()

    async def _verify_qdrant(self):
        """验证Qdrant"""
        print("🔍 验证Qdrant (持久化)")
        print("-" * 70)

        if not QDRANT_AVAILABLE:
            print("  ❌ qdrant-client未安装，无法验证Qdrant")
            self.databases.append(DatabaseStatus(
                name="Qdrant",
                type="向量数据库",
                host="localhost",
                port=6333,
                connected=False,
                error="qdrant-client未安装"
            ))
            print()
            return

        try:
            # 连接Qdrant
            client = QdrantClient(url="http://localhost:6333", timeout=10)

            # 检查集合 (使用正确的方法)
            collections_response = client.get_collections()
            collections = collections_response.collections
            total_vectors = 0
            collection_details = []

            for collection in collections:
                info_response = client.get_collection(collection.name)
                total_vectors += info_response.points_count
                collection_details.append({
                    "name": collection.name,
                    "vectors": info_response.points_count,
                    "vectors_count": info_response.points_count,
                    "config": info_response.config,
                })

            # 检查磁盘使用
            # 注意: Qdrant不直接提供磁盘使用API，这里使用向量数量估算

            status = DatabaseStatus(
                name="Qdrant",
                type="向量数据库",
                host="localhost",
                port=6333,
                connected=True,
                data_volume=total_vectors * 768,  # 估算: 每个向量768维float32
                collections_count=len(collections),
                details={
                    "collections": collection_details,
                    "total_vectors": total_vectors,
                }
            )

            print("  ✅ 连接成功: localhost:6333")
            print(f"  📦 集合数量: {len(collections)}")
            print(f"  🔢 向量总数: {total_vectors:,}")
            print(f"  💾 估算数据量: {self._format_bytes(status.data_volume)}")

            if collections:
                print("  📋 集合列表:")
                for coll in collection_details[:5]:
                    print(f"     - {coll['name']}: {coll['vectors']:,} 个向量")

        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            status = DatabaseStatus(
                name="Qdrant",
                type="向量数据库",
                host="localhost",
                port=6333,
                connected=False,
                error=str(e)
            )

        self.databases.append(status)
        print()

    async def _verify_neo4j(self):
        """验证Neo4j"""
        print("🕸️ 验证Neo4j (持久化)")
        print("-" * 70)

        if not NEO4J_AVAILABLE:
            print("  ❌ neo4j未安装，无法验证Neo4j")
            self.databases.append(DatabaseStatus(
                name="Neo4j",
                type="图数据库",
                host="localhost",
                port=7687,
                connected=False,
                error="neo4j未安装"
            ))
            print()
            return

        try:
            # 连接Neo4j
            driver = AsyncGraphDatabase.driver(
                "bolt://localhost:7687",
                auth=("neo4j", "athena_neo4j_2024"),
            )

            async with driver.session() as session:
                # 检查节点数量
                result = await session.run("MATCH (n) RETURN count(n) as node_count")
                record = await result.single()
                node_count = record["node_count"] if record else 0

                # 检查关系数量
                result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                record = await result.single()
                rel_count = record["rel_count"] if record else 0

                # 检查标签
                result = await session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
                records = await result.data()
                labels = records[0]["labels"] if records else []

                # 检查数据库信息
                result = await session.run("CALL dbms.queryJmx('org.neo4j:*') RETURN jmx")
                # 解析数据库信息...

            await driver.close()

            status = DatabaseStatus(
                name="Neo4j",
                type="图数据库",
                host="localhost",
                port=7687,
                connected=True,
                data_volume=node_count + rel_count,  # 简单计数
                collections_count=len(labels),
                details={
                    "nodes": node_count,
                    "relationships": rel_count,
                    "labels": labels,
                }
            )

            print("  ✅ 连接成功: localhost:7687")
            print(f"  📊 节点数量: {node_count:,}")
            print(f"  🔗 关系数量: {rel_count:,}")
            print(f"  🏷️ 标签数量: {len(labels)}")

            if labels:
                print("  📋 标签列表:")
                for label in labels[:10]:
                    print(f"     - {label}")

        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
            status = DatabaseStatus(
                name="Neo4j",
                type="图数据库",
                host="localhost",
                port=7687,
                connected=False,
                error=str(e)
            )

        self.databases.append(status)
        print()

    def _format_bytes(self, bytes_count: int) -> str:
        """格式化字节数"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.2f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.2f} PB"

    def _generate_report(self) -> dict[str, Any]:
        """生成验证报告"""
        connected_count = sum([1 for db in self.databases if db.connected])
        total_data_volume = sum([db.data_volume for db in self.databases if db.connected])

        report = {
            "timestamp": datetime.now().isoformat(),
            "databases": [
                {
                    "name": db.name,
                    "type": db.type,
                    "host": f"{db.host}:{db.port}",
                    "connected": db.connected,
                    "data_volume": db.data_volume,
                    "collections": db.collections_count,
                    "error": db.error,
                    "details": db.details,
                }
                for db in self.databases
            ],
            "summary": {
                "total_databases": len(self.databases),
                "connected_databases": connected_count,
                "total_data_volume": total_data_volume,
                "ready_for_legal_world": connected_count == 3,
            }
        }

        return report


async def main():
    """主函数"""
    print()
    verifier = LegalWorldVerifier()
    report = await verifier.verify_all()

    # 显示总结
    print("=" * 70)
    print("📊 法律世界模型状态报告")
    print("=" * 70)
    print()

    summary = report["summary"]
    print(f"数据库总数: {summary['total_databases']}")
    print(f"已连接: {summary['connected_databases']}")
    print(f"总数据量: {verifier._format_bytes(summary['total_data_volume'])}")
    print()

    if summary["ready_for_legal_world"]:
        print("✅ 法律世界模型已就绪，可以开始使用!")
    else:
        print("⚠️ 法律世界模型未完全就绪，请检查未连接的数据库")

    # 保存报告
    report_path = Path("/Users/xujian/Athena工作平台/data/reports")
    report_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_path / f"法律世界模型验证报告_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"📄 报告已保存: {report_file}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 验证已取消")
        sys.exit(0)
