#!/usr/bin/env python3
"""
Athena知识图谱系统 - Phase 3 数据库初始化脚本
生产环境数据库和存储系统配置
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 设置环境变量
os.environ['ATHENA_ENV'] = 'production'

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseSetupManager:
    """数据库设置管理器"""

    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.setup_config = self._load_setup_config()

    def _load_setup_config(self) -> dict[str, Any]:
        """加载设置配置"""
        config_file = self.base_path / "production" / "config" / "database_setup.json"

        default_config = {
            "postgres": {
                "host": "localhost",
                "port": 5432,
                "admin_user": "postgres",
                "admin_password": "",
                "infrastructure/infrastructure/database": "athena_patent_production",
                "user": "athena_admin",
                "password": "secure_password_2024",
                "pool_size": 50,
                "schemas": ["public", "reasoning", "patent_analysis", "knowledge_graph"]
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": "",
                "max_connections": 30
            },
            "elasticsearch": {
                "host": "localhost",
                "port": 9200,
                "indices": [
                    "patents_production",
                    "prior_art_production",
                    "compliance_records_production",
                    "reasoning_cache_production"
                ]
            },
            "qdrant": {
                "host": "localhost",
                "port": 6333,
                "collections": [
                    "patent_vectors_production",
                    "reasoning_embeddings_production",
                    "knowledge_graph_embeddings_production"
                ]
            }
        }

        if config_file.exists():
            with open(config_file, encoding='utf-8') as f:
                user_config = json.load(f)
                # 合并配置
                for key, value in user_config.items():
                    if key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value

        return default_config

    async def setup_postgresql(self):
        """设置PostgreSQL数据库"""
        logger.info("🔧 设置PostgreSQL数据库...")

        try:
            import asyncpg
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

            postgres_config = self.setup_config["postgres"]

            # 连接到PostgreSQL（不指定数据库）
            admin_conn = psycopg2.connect(
                host=postgres_config["host"],
                port=postgres_config["port"],
                user=postgres_config["admin_user"],
                password=postgres_config["admin_password"],
                database="postgres"
            )
            admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            admin_cursor = admin_conn.cursor()

            # 创建数据库
            try:
                admin_cursor.execute(f"CREATE DATABASE {postgres_config['infrastructure/infrastructure/database']}")
                logger.info(f"✅ 数据库 {postgres_config['infrastructure/infrastructure/database']} 创建成功")
            except psycopg2.errors.DuplicateDatabase:
                logger.info(f"⚠️  数据库 {postgres_config['infrastructure/infrastructure/database']} 已存在")
            except Exception as e:
                logger.error(f"❌ 创建数据库失败: {e}")
                return False

            # 创建用户
            try:
                admin_cursor.execute(
                    f"CREATE USER {postgres_config['user']} WITH PASSWORD '{postgres_config['password']}'"
                )
                logger.info(f"✅ 用户 {postgres_config['user']} 创建成功")
            except psycopg2.errors.DuplicateObject:
                logger.info(f"⚠️  用户 {postgres_config['user']} 已存在")
            except Exception as e:
                logger.error(f"❌ 创建用户失败: {e}")

            # 授权
            try:
                admin_cursor.execute(
                    f"GRANT ALL PRIVILEGES ON DATABASE {postgres_config['infrastructure/infrastructure/database']} TO {postgres_config['user']}"
                )
                logger.info("✅ 数据库授权成功")
            except Exception as e:
                logger.error(f"❌ 数据库授权失败: {e}")

            admin_cursor.close()
            admin_conn.close()

            # 连接到目标数据库并创建模式
            target_conn = psycopg2.connect(
                host=postgres_config["host"],
                port=postgres_config["port"],
                user=postgres_config["user"],
                password=postgres_config["password"],
                database=postgres_config["infrastructure/infrastructure/database"]
            )
            target_cursor = target_conn.cursor()

            # 创建模式
            for schema in postgres_config["schemas"]:
                try:
                    target_cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                    logger.info(f"✅ 模式 {schema} 创建成功")
                except Exception as e:
                    logger.error(f"❌ 创建模式 {schema} 失败: {e}")

            # 创建基础表结构
            await self._create_postgresql_tables(target_cursor)

            target_conn.commit()
            target_cursor.close()
            target_conn.close()

            logger.info("✅ PostgreSQL数据库设置完成")
            return True

        except ImportError:
            logger.warning("⚠️  PostgreSQL驱动未安装，跳过数据库设置")
            return False
        except Exception as e:
            logger.error(f"❌ PostgreSQL设置失败: {e}")
            return False

    async def _create_postgresql_tables(self, cursor):
        """创建PostgreSQL表结构"""

        # 推理记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reasoning.reasoning_records (
                id SERIAL PRIMARY KEY,
                reasoning_type VARCHAR(50) NOT NULL,
                input_facts TEXT[],
                reasoning_chain JSONB,
                confidence DECIMAL(3,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 专利合规性检查记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patent_analysis.compliance_checks (
                id SERIAL PRIMARY KEY,
                patent_id VARCHAR(100),
                rule_types TEXT[],
                compliance_results JSONB,
                overall_score DECIMAL(3,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 技术演进分析记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_graph.evolution_analysis (
                id SERIAL PRIMARY KEY,
                technology_field VARCHAR(200),
                time_range_start DATE,
                time_range_end DATE,
                evolution_data JSONB,
                key_innovations TEXT[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 系统性能统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reasoning.performance_stats (
                id SERIAL PRIMARY KEY,
                service_name VARCHAR(100),
                metric_name VARCHAR(100),
                metric_value DECIMAL(10,2),
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_reasoning_records_type ON reasoning.reasoning_records(reasoning_type)",
            "CREATE INDEX IF NOT EXISTS idx_reasoning_records_created ON reasoning.reasoning_records(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_checks_patent ON patent_analysis.compliance_checks(patent_id)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_checks_created ON patent_analysis.compliance_checks(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_evolution_analysis_field ON knowledge_graph.evolution_analysis(technology_field)",
            "CREATE INDEX IF NOT EXISTS idx_performance_stats_service ON reasoning.performance_stats(service_name, recorded_at)"
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                logger.info("✅ 索引创建成功")
            except Exception as e:
                logger.warning(f"⚠️  索引创建失败: {e}")

    async def setup_redis(self):
        """设置Redis缓存"""
        logger.info("🔧 设置Redis缓存...")

        try:
            import aioredis
            import redis

            redis_config = self.setup_config["redis"]

            # 测试连接
            client = redis.Redis(
                host=redis_config["host"],
                port=redis_config["port"],
                db=redis_config["db"],
                password=redis_config["password"] if redis_config["password"] else None,
                decode_responses=True
            )

            # 测试连接
            client.ping()
            logger.info("✅ Redis连接成功")

            # 设置基础配置
            client.config_set("maxmemory", "2gb")
            client.config_set("maxmemory-policy", "allkeys-lru")

            # 创建缓存键结构示例
            cache_structure = {
                "reasoning:cache:*": "推理结果缓存",
                "patent:compliance:*": "专利合规性检查结果",
                "analysis:evolution:*": "技术演进分析结果",
                "judgment:results:*": "智能判断结果",
                "roadmap:generated:*": "技术路线图结果"
            }

            logger.info("✅ Redis缓存设置完成")
            return True

        except ImportError:
            logger.warning("⚠️  Redis驱动未安装，跳过Redis设置")
            return False
        except Exception as e:
            logger.error(f"❌ Redis设置失败: {e}")
            return False

    async def setup_elasticsearch(self):
        """设置Elasticsearch"""
        logger.info("🔧 设置Elasticsearch...")

        try:
            from elasticsearch import Elasticsearch

            es_config = self.setup_config["elasticsearch"]

            # 连接Elasticsearch
            es = Elasticsearch([{
                "host": es_config["host"],
                "port": es_config["port"]
            }])

            # 测试连接
            if es.ping():
                logger.info("✅ Elasticsearch连接成功")

                # 创建索引
                for index in es_config["indices"]:
                    try:
                        if not es.indices.exists(index=index):
                            # 创建索引映射
                            if "apps/apps/patents" in index:
                                mapping = {
                                    "mappings": {
                                        "properties": {
                                            "title": {"type": "text"},
                                            "abstract": {"type": "text"},
                                            "claims": {"type": "text"},
                                            "ipc": {"type": "keyword"},
                                            "publication_date": {"type": "date"},
                                            "inventors": {"type": "text"},
                                            "assignee": {"type": "text"},
                                            "patent_id": {"type": "keyword"}
                                        }
                                    }
                                }
                            elif "prior_art" in index:
                                mapping = {
                                    "mappings": {
                                        "properties": {
                                            "patent_id": {"type": "keyword"},
                                            "technology_field": {"type": "keyword"},
                                            "similarity_score": {"type": "float"},
                                            "relation_type": {"type": "keyword"},
                                            "analysis_date": {"type": "date"}
                                        }
                                    }
                                }
                            else:
                                mapping = {"mappings": {"properties": {}}}

                            es.indices.create(index=index, body=mapping)
                            logger.info(f"✅ 索引 {index} 创建成功")
                        else:
                            logger.info(f"⚠️  索引 {index} 已存在")
                    except Exception as e:
                        logger.error(f"❌ 创建索引 {index} 失败: {e}")

                logger.info("✅ Elasticsearch设置完成")
                return True
            else:
                logger.error("❌ Elasticsearch连接失败")
                return False

        except ImportError:
            logger.warning("⚠️  Elasticsearch驱动未安装，跳过Elasticsearch设置")
            return False
        except Exception as e:
            logger.error(f"❌ Elasticsearch设置失败: {e}")
            return False

    async def setup_qdrant(self):
        """设置Qdrant向量数据库"""
        logger.info("🔧 设置Qdrant向量数据库...")

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import CreateCollection, Distance, VectorParams

            qdrant_config = self.setup_config["qdrant"]

            # 连接Qdrant
            client = QdrantClient(
                host=qdrant_config["host"],
                port=qdrant_config["port"]
            )

            # 测试连接
            try:
                client.get_collections()
                logger.info("✅ Qdrant连接成功")
            except Exception as e:
                logger.error(f"❌ Qdrant连接失败: {e}")
                return False

            # 创建集合
            for collection in qdrant_config["collections"]:
                try:
                    if not client.collection_exists(collection_name=collection):
                        client.create_collection(
                            collection_name=collection,
                            vectors_config=VectorParams(
                                size=768,  # BERT向量维度
                                distance=Distance.COSINE
                            )
                        )
                        logger.info(f"✅ 集合 {collection} 创建成功")
                    else:
                        logger.info(f"⚠️  集合 {collection} 已存在")
                except Exception as e:
                    logger.error(f"❌ 创建集合 {collection} 失败: {e}")

            logger.info("✅ Qdrant向量数据库设置完成")
            return True

        except ImportError:
            logger.warning("⚠️  Qdrant驱动未安装，跳过Qdrant设置")
            return False
        except Exception as e:
            logger.error(f"❌ Qdrant设置失败: {e}")
            return False

    def save_setup_config(self) -> None:
        """保存设置配置"""
        config_file = self.base_path / "production" / "config" / "database_setup.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.setup_config, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 数据库配置已保存到: {config_file}")

    async def run_setup(self):
        """运行完整的数据库设置"""
        logger.info("🚀 开始Phase 3数据库和存储系统设置...")

        setup_results = {
            "postgresql": False,
            "redis": False,
            "elasticsearch": False,
            "qdrant": False
        }

        # 保存配置
        self.save_setup_config()

        # 设置各个存储系统
        setup_results["postgresql"] = await self.setup_postgresql()
        setup_results["redis"] = await self.setup_redis()
        setup_results["elasticsearch"] = await self.setup_elasticsearch()
        setup_results["qdrant"] = await self.setup_qdrant()

        # 生成设置报告
        success_count = sum(setup_results.values())
        total_count = len(setup_results)
        success_rate = (success_count / total_count) * 100

        logger.info("=" * 60)
        logger.info("📊 数据库设置摘要:")
        logger.info(f"   • PostgreSQL: {'✅ 成功' if setup_results['postgresql'] else '❌ 失败'}")
        logger.info(f"   • Redis: {'✅ 成功' if setup_results['redis'] else '❌ 失败'}")
        logger.info(f"   • Elasticsearch: {'✅ 成功' if setup_results['elasticsearch'] else '❌ 失败'}")
        logger.info(f"   • Qdrant: {'✅ 成功' if setup_results['qdrant'] else '❌ 失败'}")
        logger.info(f"   • 总体成功率: {success_rate:.1f}% ({success_count}/{total_count})")
        logger.info("=" * 60)

        # 保存设置报告
        report = {
            "setup_time": datetime.now().isoformat(),
            "reports/reports/results": setup_results,
            "success_rate": success_rate,
            "config": self.setup_config
        }

        report_file = self.base_path / "production" / "logs" / "database_setup_report.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        return success_rate >= 75  # 75%以上成功率认为设置成功

async def main():
    """主函数"""
    print("🧠 Athena知识图谱系统 - Phase 3 数据库初始化")
    print("=" * 60)

    setup_manager = DatabaseSetupManager()
    success = await setup_manager.run_setup()

    if success:
        print("✅ 数据库和存储系统设置成功！")
        print("🚀 系统已准备好启动Phase 3推理引擎")
        return 0
    else:
        print("❌ 数据库设置失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
