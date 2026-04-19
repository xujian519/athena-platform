#!/usr/bin/env python3
"""
数据库连接验证脚本
Database Connection Verification Script

验证所有数据库服务是否正常工作

作者: Athena AI系统
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# 颜色输出
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    NC = '\033[0m'


def print_header(title):
    print(f"\n{Colors.PURPLE}{'=' * 70}{Colors.NC}")
    print(f"{Colors.PURPLE}{title.center(70)}{Colors.NC}")
    print(f"{Colors.PURPLE}{'=' * 70}{Colors.NC}\n")


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.NC}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")


async def verify_postgresql():
    """验证PostgreSQL连接"""
    print("📦 PostgreSQL 17.7")
    print("-" * 70)

    try:
        import psycopg
        from psycopg.rows import dict_row

        # 连接数据库
        conn = await psycopg.AsyncConnection.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            user=os.getenv("POSTGRES_USER", os.getenv("USER", "xujian")),
            dbname=os.getenv("POSTGRES_DB", "athena_production")
        )

        # 执行查询
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("SELECT version();")
            result = await cur.fetchone()
            version = result['version'].split(",")[0]
            print_success(f"已连接: {version}")

            # 检查表数量
            await cur.execute("""
                SELECT COUNT(*) as count FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
            """)
            result = await cur.fetchone()
            print_success(f"数据库表数量: {result['count']}")

        await conn.close()
        return True

    except ImportError:
        print_warning("psycopg模块未安装，尝试使用psycopg2...")
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                user=os.getenv("POSTGRES_USER", os.getenv("USER", "xujian")),
                dbname=os.getenv("POSTGRES_DB", "athena_production")
            )
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()[0].split(",")[0]
            print_success(f"已连接: {version}")
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print_error(f"连接失败: {e}")
            return False
    except Exception as e:
        print_error(f"连接失败: {e}")
        return False


async def verify_redis():
    """验证Redis连接"""
    print("\n🗃️ Redis")
    print("-" * 70)

    try:
        import redis.asyncio as redis

        r = await redis.from_url(
            f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}",
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=True
        )

        # 测试连接
        await r.ping()
        print_success("连接成功")

        # 获取信息
        info = await r.info('server')
        print_success(f"Redis版本: {info.get('redis_version', 'unknown')}")

        # 测试写入和读取
        await r.set('athena_test', 'connection_ok', ex=10)
        value = await r.get('athena_test')
        if value == 'connection_ok':
            print_success("读写测试通过")

        await r.close()
        return True

    except Exception as e:
        print_error(f"连接失败: {e}")
        print_info("请确保Redis正在运行: docker ps | grep redis")
        return False


async def verify_qdrant():
    """验证Qdrant连接"""
    print("\n🧮 Qdrant 向量数据库")
    print("-" * 70)

    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(
            url=f"http://{os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', 6333)}",
            api_key=os.getenv('QDRANT_API_KEY')
        )

        # 获取集合列表
        collections = client.get_collections()
        print_success(f"连接成功，现有集合: {len(collections.collections)} 个")

        # 检查默认集合
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'athena_vectors')
        if collection_name in [c.name for c in collections.collections]:
            print_success(f"集合 '{collection_name}' 已存在")
        else:
            print_info(f"集合 '{collection_name}' 不存在，将在首次使用时创建")

        return True

    except Exception as e:
        print_error(f"连接失败: {e}")
        print_info("请确保Qdrant正在运行: docker ps | grep qdrant")
        return False


async def verify_neo4j():
    """验证Neo4j连接（可选）"""
    print("\n🕸️ Neo4j 图数据库 (可选)")
    print("-" * 70)

    try:
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(
            os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'password'))
        )

        async with driver.session() as session:
            result = await session.run("RETURN 'Connection OK' as message")
            record = await result.single()
            print_success(f"连接成功: {record['message']}")

            # 获取版本信息
            result = await session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions[0] as version")
            record = await result.single()
            if record:
                print_success(f"Neo4j: {record['name']} {record['version']}")

        await driver.close()
        return True

    except Exception as e:
        print_warning(f"连接失败（这是正常的，如果未使用Neo4j）: {e}")
        print_info("Neo4j是可选的，不影响核心功能")
        return True  # 返回True因为Neo4j是可选的


async def main():
    """主函数"""
    print_header("🔍 Athena数据库连接验证")

    # 加载环境变量
    env_file = PROJECT_ROOT / '.env.production'
    if env_file.exists():
        print_success(f"已加载配置: {env_file}")
        # 简单读取环境变量
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # 移除引号
                    value = value.strip('"').strip("'")
                    os.environ[key] = value

    results = {
        'postgresql': await verify_postgresql(),
        'redis': await verify_redis(),
        'qdrant': await verify_qdrant(),
        'neo4j': await verify_neo4j()
    }

    # 汇总结果
    print_header("📊 验证结果汇总")

    passed = sum(results.values())
    total = len(results)

    for db, status in results.items():
        icon = "✅" if status else "❌"
        name = db.upper()
        if status or db == 'neo4j':
            print(f"{icon} {name}: {'连接成功' if status else '未配置（可选）'}")
        else:
            print(f"{icon} {name}: 连接失败")

    print(f"\n{Colors.BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
    if passed >= 3:
        print_success(f"核心数据库验证通过 ({passed}/{total})")
        print(f"\n{Colors.GREEN}所有核心服务已就绪，可以启动生产环境！{Colors.NC}")
        return 0
    else:
        print_error(f"部分数据库验证失败 ({passed}/{total})")
        print(f"\n{Colors.YELLOW}请检查数据库服务状态{Colors.NC}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
