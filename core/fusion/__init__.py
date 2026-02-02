#!/usr/bin/env python3
"""
向量-图融合架构
Vector-Graph Fusion Architecture

深度融合 pgvector 向量搜索与 NebulaGraph 图数据库

作者: 小诺·双鱼公主
创建时间: 2025-12-28
"""

# 导入核心融合服务
# 导入API扩展
from .fusion_api_extension import (
    FusionAPIExtension,
    FusionSearchRequest,
    FusionSearchResponse,
    FusionStatsResponse,
    FusionStoreRequest,
    get_fusion_api,
)
from .vector_graph_fusion_service import (
    FusionConfig,
    FusionQueryResult,
    QueryStrategy,
    VectorGraphFusionService,
    get_fusion_service,
)

__all__ = [
    # API Extension
    "FusionAPIExtension",
    "FusionConfig",
    "FusionQueryResult",
    "FusionSearchRequest",
    "FusionSearchResponse",
    "FusionStatsResponse",
    "FusionStoreRequest",
    "QueryStrategy",
    # Service
    "VectorGraphFusionService",
    "get_fusion_api",
    "get_fusion_service",
]


# 保留原有测试脚本功能
import os
import sys


# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入安全配置
from core.config.secure_config import get_config


async def init_sample_data():
    """初始化示例数据"""
    print("🔧 初始化示例数据...")


    from core.database.unified_connection import get_postgres_pool

    # 使用安全配置获取数据库连接
    config = get_config()
    conn = await asyncpg.connect(
        host=config.get("POSTGRES_HOST", "localhost"),
        port=config.get_int("POSTGRES_PORT", 5438),
        user=config.get("POSTGRES_USER", "postgres"),
        password=config.get("POSTGRES_PASSWORD", required=True),
        database=config.get("POSTGRES_DBNAME", "agent_memory_db"),
    )

    try:
        # 检查向量表是否存在
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'agent_memory_vectors'
            )
        """)

        if not table_exists:
            print("  创建向量表...")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_memory_vectors (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    content TEXT NOT NULL,
                    title VARCHAR(500),
                    embedding vector(768),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # 插入示例向量数据
        print("  插入示例数据...")

        sample_data = [
            {"title": "专利审查指南", "content": "专利审查指南是专利申请和审查的重要参考文档..."},
            {"title": "新颖性判断", "content": "专利新颖性是指该发明在申请日之前未被公开..."},
            {"title": "创造性标准", "content": "创造性是指同申请日以前已有的技术相比..."},
        ]

        for data in sample_data:
            # 生成简单的向量(实际应使用 embedding 模型)
            import json


            vector = np.random.rand(768).tolist()
            vector_str = "[" + ",".join(map(str, vector)) + "]"

            await conn.execute(
                """
                INSERT INTO agent_memory_vectors (content, title, embedding, metadata)
                VALUES ($1, $2, $3::vector, $4::jsonb)
                ON CONFLICT DO NOTHING
            """,
                data["content"],
                data["title"],
                vector_str,
                json.dumps({}),
            )

        print("✅ 示例数据初始化完成")

    finally:
        await conn.close()


async def test_fusion_query():
    """测试融合查询"""
    print("🔍 测试融合查询...")

    # 导入核心模块
    import os
    import sys

    # 添加项目根目录到路径
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    import asyncpg

    from core.fusion.vgraph_fusion_query_engine import FusionQueryEngine
    from core.fusion.vgraph_joint_index import VectorGraphJointIndex

    # 创建连接
    config = get_config()
    await get_postgres_pool(
        host=config.get("POSTGRES_HOST", "localhost"),
        port=config.get_int("POSTGRES_PORT", 5438),
        user=config.get("POSTGRES_USER", "postgres"),
        password=config.get("POSTGRES_PASSWORD", required=True),
        database=config.get("POSTGRES_DBNAME", "agent_memory_db"),
        min_size=2,
        max_size=5,
    )

    try:
        # 创建联合索引
        joint_index = VectorGraphJointIndex(pg_pool)

        # 创建 NebulaGraph 连接池(可选)
        nebula_pool = None
        try:

            nebula_config = config.get_nebula_config()
            nebula_pool = NebulaPool()
            await nebula_pool.init(
                username=nebula_config.get("user", "root"),
                password=nebula_config.get("password", required=True),
                space_name=nebula_config.get("space", "vgraph_unified_space"),
                addresses=[
                    (nebula_config.get("host", "localhost"), nebula_config.get_int("port", 9669))
                ],
            )
        except Exception as e:
            print(f"  ⚠️  NebulaGraph 连接跳过: {e}")

        # 创建融合查询引擎
        engine = FusionQueryEngine(pg_pool, nebula_pool, joint_index)

        # 执行测试查询
        print("  执行融合查询测试...")
        query_vector = np.random.rand(768).tolist()

        results, report = await engine.execute_fusion_query(
            query_text="专利审查指南",
            query_vector=query_vector,
            entity_types=["agent_memory_vectors"],
            limit=5,
            strategy="balanced",
        )

        print("\n  📊 查询报告:")
        print(f"    结果数量: {report['result_count']}")
        print(f"    延迟: {report['latency_ms']:.2f}ms")
        print(f"    缓存命中: {report['from_cache']}")

        print("\n  🎯 前3个结果:")
        for i, result in enumerate(results[:3], 1):
            print(f"    {i}. [{result.entity_type}]分数: {result.fusion_score:.4f}")
            print(f"       内容: {result.content[:80]}...")

        # 获取统计
        stats = await engine.get_query_statistics()
        print("\n  📈 查询统计:")
        print(f"    总查询数: {stats['total_queries']}")
        print(f"    缓存命中率: {stats['cache_hit_rate']:.2%}")
        print(f"    平均延迟: {stats['avg_latency_ms']:.2f}ms")

        print("✅ 融合查询测试通过")

    except Exception as e:
        print(f"❌ 融合查询测试失败: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await pg_pool.close()
        # 关闭NebulaGraph连接池
        if nebula_pool:
            nebula_pool.close()


async def test_sync_service():
    """测试同步服务"""
    print("🔄 测试同步服务...")

    from core.fusion.vgraph_sync_service import RealtimeSyncService

    # 使用安全配置
    config = get_config()
    pg_config = config.get_postgres_config()
    nebula_config = config.get_nebula_config()

    sync_service = RealtimeSyncService(pg_config=pg_config, nebula_config=nebula_config)

    try:
        await sync_service.initialize()

        # 获取统计
        stats = await sync_service.get_sync_statistics()
        print(f"  同步统计: {stats}")

        print("✅ 同步服务测试通过")

    except Exception as e:
        print(f"❌ 同步服务测试失败: {e}")
    finally:
        await sync_service.close()


async def main():
    """主函数"""
    print("=" * 60)
    print("  NebulaGraph + pgvector 深度融合 - 验证测试")
    print("=" * 60)
    print()

    # 检查 PostgreSQL 是否运行
    try:
        import asyncpg

        config = get_config()
        conn = await asyncpg.connect(
            host=config.get("POSTGRES_HOST", "localhost"),
            port=config.get_int("POSTGRES_PORT", 5438),
            user=config.get("POSTGRES_USER", "postgres"),
            password=config.get("POSTGRES_PASSWORD", required=True),
            database=config.get("POSTGRES_DBNAME", "agent_memory_db"),
        )
        await conn.close()
        print("✅ PostgreSQL 连接正常")
    except Exception as e:
        print(f"❌ PostgreSQL 连接失败: {e}")
        print("  请先运行: bash core/fusion/deploy_vgraph_fusion.sh")
        return

    # 执行测试
    try:
        await init_sample_data()
        print()

        await test_fusion_query()
        print()

        # 同步服务测试(可选)
        # await test_sync_service()

        print()
        print("=" * 60)
        print("  ✅ 所有测试通过!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


# 入口点: @async_main装饰器已添加到main函数
