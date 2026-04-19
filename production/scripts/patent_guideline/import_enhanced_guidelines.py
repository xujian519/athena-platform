#!/usr/bin/env python3
"""
专利审查指南增强数据统一导入脚本
Enhanced Patent Guidelines Unified Import Script

功能：
1. 导入增强JSON数据到PostgreSQL关系数据库
2. 导入BGE-M3向量到pgvector/Qdrant向量数据库
3. 导入BERT-NER实体和关系到NebulaGraph知识图谱

作者: Athena平台团队
创建时间: 2026-01-21
版本: 4.0 (支持三模型增强数据)
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(log_dir / f'enhanced_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class EnhancedGuidelineImporter:
    """增强版专利审查指南统一导入器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/语料/专利-json-enhanced-v4/guideline")
        self.project_root = Path("/Users/xujian/Athena工作平台")

        # 数据库配置
        self.pg_config = {
            "host": "localhost",
            "port": 5432,
            "database": "patent_guidelines",
            "user": "xujian",
            "password": ""
        }

        self.qdrant_url = "http://localhost:6333"
        self.nebula_config = {
            "address": ("127.0.0.1", 9669),
            "space": "patent_guidelines"
        }

        # 客户端初始化标志
        self.pg_conn = None
        self.qdrant_client = None
        self.nebula_client = None

        # 统计信息
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "postgresql_imported": 0,
            "qdrant_imported": 0,
            "nebula_nodes": 0,
            "nebula_edges": 0,
            "start_time": None,
            "end_time": None
        }

        logger.info("=" * 80)
        logger.info("🚀 增强版专利审查指南统一导入器初始化")
        logger.info("=" * 80)

    # ==================== PostgreSQL关系数据库导入 ====================

    async def initialize_postgresql(self):
        """初始化PostgreSQL连接并创建表"""
        logger.info("=" * 80)
        logger.info("📊 初始化PostgreSQL关系数据库")
        logger.info("=" * 80)

        try:
            import psycopg2

            # 连接数据库
            self.pg_conn = psycopg2.connect(**self.pg_config)
            cursor = self.pg_conn.cursor()

            # 创建数据库（如果不存在）
            cursor.execute("SELECT 1 FROM pg_database WHERE datname='patent_guidelines'")
            if not cursor.fetchone():
                conn2 = psycopg2.connect(
                    host=self.pg_config["host"],
                    port=self.pg_config["port"],
                    database="postgres",
                    user=self.pg_config["user"],
                    password=self.pg_config["password"]
                )
                conn2.autocommit = True
                cursor2 = conn2.cursor()
                cursor2.execute("CREATE DATABASE patent_guidelines")
                cursor2.close()
                conn2.close()
                logger.info("✅ 创建数据库: patent_guidelines")

            self.pg_conn.close()
            self.pg_conn = psycopg2.connect(**self.pg_config)
            cursor = self.pg_conn.cursor()

            # 启用pgvector扩展
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                logger.info("✅ pgvector扩展已启用")
            except Exception as e:
                logger.warning(f"⚠️ pgvector扩展警告: {e}")

            # 创建表结构
            tables_sql = [
                # 1. 主文档表
                """
                CREATE TABLE IF NOT EXISTS guideline_documents (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR(100) UNIQUE NOT NULL,
                    file_name VARCHAR(255) NOT NULL,
                    file_path TEXT,
                    hierarchy JSONB,
                    total_chunks INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """,

                # 2. 内容块表（包含增强数据）
                """
                CREATE TABLE IF NOT EXISTS guideline_chunks (
                    id SERIAL PRIMARY KEY,
                    chunk_id VARCHAR(100) UNIQUE NOT NULL,
                    document_id VARCHAR(100) REFERENCES guideline_documents(document_id),
                    level INTEGER,
                    title TEXT,
                    content TEXT,
                    bge_m3_embedding vector(1024),

                    # BERT-NER实体
                    bert_ner_entities JSONB,

                    # DeepSeek-R1增强
                    deepseek_summary TEXT,
                    deepseek_key_concepts TEXT[],
                    deepseek_practical_guidance TEXT,
                    deepseek_related_rules TEXT[],
                    deepseek_risk_points TEXT[],
                    deepseek_thinking_process TEXT,

                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """,

                # 3. 实体表（用于知识图谱关联）
                """
                CREATE TABLE IF NOT EXISTS guideline_entities (
                    id SERIAL PRIMARY KEY,
                    entity_id VARCHAR(100) UNIQUE NOT NULL,
                    chunk_id VARCHAR(100) REFERENCES guideline_chunks(chunk_id),
                    entity_type VARCHAR(50) NOT NULL,
                    entity_text TEXT NOT NULL,
                    confidence FLOAT,
                    properties JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """,

                # 4. 关系表
                """
                CREATE TABLE IF NOT EXISTS guideline_relations (
                    id SERIAL PRIMARY KEY,
                    relation_id VARCHAR(100) UNIQUE NOT NULL,
                    source_entity_id VARCHAR(100) REFERENCES guideline_entities(entity_id),
                    target_entity_id VARCHAR(100) REFERENCES guideline_entities(entity_id),
                    relation_type VARCHAR(50) NOT NULL,
                    properties JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """,

                # 创建索引
                "CREATE INDEX IF NOT EXISTS idx_chunks_document ON guideline_chunks(document_id);",
                "CREATE INDEX IF NOT EXISTS idx_chunks_level ON guideline_chunks(level);",
                "CREATE INDEX IF NOT EXISTS idx_entities_chunk ON guideline_entities(chunk_id);",
                "CREATE INDEX IF NOT EXISTS idx_entities_type ON guideline_entities(entity_type);",
                "CREATE INDEX IF NOT EXISTS idx_relations_source ON guideline_relations(source_entity_id);",
                "CREATE INDEX IF NOT EXISTS idx_relations_target ON guideline_relations(target_entity_id);",
            ]

            for sql in tables_sql:
                cursor.execute(sql)

            self.pg_conn.commit()
            cursor.close()

            logger.info("✅ PostgreSQL表结构创建完成")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ PostgreSQL初始化失败: {e}")
            logger.error(traceback.format_exc())
            raise

    async def import_to_postgresql(self, enhanced_data: dict[str, Any]) -> bool:
        """导入增强数据到PostgreSQL"""
        try:
            from psycopg2.extras import execute_values

            cursor = self.pg_conn.cursor()

            # 提取基础信息
            original_data = enhanced_data.get("original_data", {})
            hierarchy_info = enhanced_data.get("hierarchy_info", {})
            enhanced_chunks = enhanced_data.get("enhanced_chunks", [])

            document_id = original_data.get("section_id", "unknown")
            file_name = hierarchy_info.get("file_name", "unknown")

            # 1. 插入或更新文档记录
            cursor.execute(
                """
                INSERT INTO guideline_documents (document_id, file_name, file_path, hierarchy, total_chunks)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (document_id)
                DO UPDATE SET
                    total_chunks = EXCLUDED.total_chunks + %s,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (
                    document_id,
                    file_name,
                    str(hierarchy_info.get("file_path", "")),
                    json.dumps(original_data.get("hierarchy", {}), ensure_ascii=False),
                    len(enhanced_chunks),
                    len(enhanced_chunks)
                )
            )

            # 2. 批量插入内容块
            chunk_values = []
            entity_values = []

            for chunk in enhanced_chunks:
                chunk_id = chunk.get("chunk_id", "")
                bge_embedding = chunk.get("bge_m3_embedding", {})
                bert_entities = chunk.get("bert_ner_entities", [])
                deepseek_enhancement = chunk.get("qwen_enhancement", {}).get("enhanced_content", {})

                # 构建向量字符串
                embedding_str = None
                if bge_embedding.get("embedding"):
                    embedding_str = f"[{','.join(map(str, bge_embedding['embedding']))}]"

                chunk_values.append((
                    chunk_id,
                    document_id,
                    chunk.get("level", 0),
                    chunk.get("title", "")[:500],
                    chunk.get("content", "")[:5000],
                    embedding_str,
                    json.dumps(bert_entities, ensure_ascii=False),
                    deepseek_enhancement.get("summary", "")[:1000],
                    deepseek_enhancement.get("key_concepts", []),
                    deepseek_enhancement.get("practical_guidance", "")[:2000],
                    deepseek_enhancement.get("related_rules", []),
                    deepseek_enhancement.get("risk_points", []),
                    deepseek_enhancement.get("thinking_process", "")[:2000],
                    json.dumps(chunk.get("metadata", {}), ensure_ascii=False)
                ))

                # 准备实体数据
                for entity in bert_entities:
                    entity_id = f"{chunk_id}_{entity.get('type', '')}_{hash(entity.get('text', ''))}"
                    entity_values.append((
                        entity_id,
                        chunk_id,
                        entity.get("type", ""),
                        entity.get("text", ""),
                        entity.get("confidence", 0.0),
                        json.dumps(entity, ensure_ascii=False)
                    ))

            # 批量插入内容块
            if chunk_values:
                execute_values(
                    cursor,
                    """
                    INSERT INTO guideline_chunks (
                        chunk_id, document_id, level, title, content, bge_m3_embedding,
                        bert_ner_entities, deepseek_summary, deepseek_key_concepts,
                        deepseek_practical_guidance, deepseek_related_rules,
                        deepseek_risk_points, deepseek_thinking_process, metadata
                    ) VALUES %s
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        bge_m3_embedding = EXCLUDED.bge_m3_embedding,
                        bert_ner_entities = EXCLUDED.bert_ner_entities,
                        deepseek_summary = EXCLUDED.deepseek_summary,
                        deepseek_key_concepts = EXCLUDED.deepseek_key_concepts,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    chunk_values
                )
                self.stats["postgresql_imported"] += len(chunk_values)

            # 批量插入实体
            if entity_values:
                execute_values(
                    cursor,
                    """
                    INSERT INTO guideline_entities (
                        entity_id, chunk_id, entity_type, entity_text, confidence, properties
                    ) VALUES %s
                    ON CONFLICT (entity_id) DO UPDATE SET
                        entity_type = EXCLUDED.entity_type,
                        confidence = EXCLUDED.confidence,
                        properties = EXCLUDED.properties
                    """,
                    entity_values
                )

            self.pg_conn.commit()
            cursor.close()

            return True

        except Exception as e:
            logger.error(f"❌ PostgreSQL导入失败: {e}")
            logger.error(traceback.format_exc())
            if self.pg_conn:
                self.pg_conn.rollback()
            return False

    # ==================== Qdrant向量数据库导入 ====================

    async def initialize_qdrant(self):
        """初始化Qdrant客户端"""
        logger.info("=" * 80)
        logger.info("🔍 初始化Qdrant向量数据库")
        logger.info("=" * 80)

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, PayloadSchema, VectorParams

            self.qdrant_client = QdrantClient(url=self.qdrant_url)

            collection_name = "patent_guidelines_enhanced"

            # 检查并创建集合
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]

            if collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
                )
                logger.info(f"✅ Qdrant集合已创建: {collection_name}")
            else:
                logger.info(f"✅ Qdrant集合已存在: {collection_name}")

            # 创建payload索引（加速过滤查询）
            try:
                self.qdrant_client.create_payload_index(
                    collection_name=collection_name,
                    field_name="document_id",
                    field_schema=PayloadSchema.KEYWORD
                )
                self.qdrant_client.create_payload_index(
                    collection_name=collection_name,
                    field_name="level",
                    field_schema=PayloadSchema.INTEGER
                )
                logger.info("✅ Payload索引已创建")
            except Exception as e:
                logger.debug(f"Payload索引创建跳过: {e}")

            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ Qdrant初始化失败: {e}")
            logger.error(traceback.format_exc())
            raise

    async def import_to_qdrant(self, enhanced_data: dict[str, Any]) -> bool:
        """导入向量到Qdrant"""
        try:
            from qdrant_client.models import PointStruct

            enhanced_chunks = enhanced_data.get("enhanced_chunks", [])
            document_id = enhanced_data.get("original_data", {}).get("section_id", "unknown")

            points = []
            for chunk in enhanced_chunks:
                chunk_id = chunk.get("chunk_id", "")
                bge_embedding = chunk.get("bge_m3_embedding", {})
                embedding = bge_embedding.get("embedding", [])

                if not embedding:
                    continue

                # 生成数值ID
                hash_id = abs(hash(chunk_id)) % (10 ** 10)

                # 准备payload（包含所有增强信息）
                payload = {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "level": chunk.get("level", 0),
                    "title": chunk.get("title", "")[:500],
                    "content": chunk.get("content", "")[:1000],
                    "metadata": json.dumps(chunk.get("metadata", {}), ensure_ascii=False),

                    # BERT-NER实体摘要
                    "entity_types": [e.get("type", "") for e in chunk.get("bert_ner_entities", [])],
                    "entity_count": len(chunk.get("bert_ner_entities", [])),

                    # DeepSeek-R1增强摘要
                    "has_summary": bool(chunk.get("qwen_enhancement", {}).get("enhanced_content", {}).get("summary")),
                    "key_concepts": chunk.get("qwen_enhancement", {}).get("enhanced_content", {}).get("key_concepts", [])[:10],
                    "risk_points_count": len(chunk.get("qwen_enhancement", {}).get("enhanced_content", {}).get("risk_points", [])),
                }

                points.append(PointStruct(
                    id=hash_id,
                    vector=embedding,
                    payload=payload
                ))

            # 批量上传
            if points:
                self.qdrant_client.upsert(
                    collection_name="patent_guidelines_enhanced",
                    points=points
                )
                self.stats["qdrant_imported"] += len(points)

            return True

        except Exception as e:
            logger.error(f"❌ Qdrant导入失败: {e}")
            logger.error(traceback.format_exc())
            return False

    # ==================== NebulaGraph知识图谱导入 ====================

    async def initialize_nebula(self):
        """初始化NebulaGraph连接"""
        logger.info("=" * 80)
        logger.info("🕸️ 初始化NebulaGraph知识图谱")
        logger.info("=" * 80)

        try:
            from nebula3.Config import ConfigPool
            from nebula3.gclient.net import ConnectionPool

            self.nebula_pool = ConnectionPool()

            # 配置连接
            config = ConfigPool()
            config.max_connection_pool_size = 10

            # 连接到NebulaGraph (同步API)
            self.nebula_pool.init(
                [(self.nebula_config["address"][0], self.nebula_config["address"][1])],
                config
            )

            # 获取session
            self.nebula_client = self.nebula_pool.get_session("root", "nebula")

            # 创建图空间（如果不存在）
            try:
                result = self.nebula_client.execute(
                    f"CREATE SPACE IF NOT EXISTS {self.nebula_config['space']}"
                    f"(partition_num=10, replica_factor=1, vid_type=FIXED_STRING(100))"
                )
                logger.info(f"✅ NebulaGraph空间已创建: {self.nebula_config['space']}")
            except Exception as e:
                logger.debug(f"图空间创建跳过: {e}")

            # 等待空间创建完成
            import asyncio
            await asyncio.sleep(2)

            # 使用图空间
            try:
                self.nebula_client.execute(f"USE {self.nebula_config['space']}")
            except Exception as e:
                logger.warning(f"使用图空间警告: {e}")

            # 创建图结构
            schema_commands = [
                # 实体点类型
                "CREATE TAG IF NOT EXISTS entity(entity_type string, entity_text string, confidence double, properties string)",

                # 内容块点类型
                "CREATE TAG IF NOT EXISTS chunk(level int, title string, content_summary string, embedding_dimension int)",

                # 文档点类型
                "CREATE TAG IF NOT EXISTS document(file_name string, total_chunks int)",

                # 关系边类型
                "CREATE EDGE IF NOT EXISTS mentions(relation_type string, confidence double, properties string)",
                "CREATE EDGE IF NOT EXISTS belongs_to(level int)",
                "CREATE EDGE IF NOT EXISTS relates_to(relation_type string, properties string)",
            ]

            for cmd in schema_commands:
                try:
                    self.nebula_client.execute(cmd)
                except Exception as e:
                    logger.debug(f"Schema创建跳过: {e}")

            logger.info("✅ NebulaGraph图结构创建完成")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ NebulaGraph初始化失败: {e}")
            logger.error(traceback.format_exc())
            # NebulaGraph是可选的，不中断流程
            self.nebula_client = None
            self.nebula_pool = None

    async def import_to_nebula(self, enhanced_data: dict[str, Any]) -> bool:
        """导入实体和关系到NebulaGraph"""
        if not self.nebula_client:
            return False

        try:
            import hashlib

            document_id = enhanced_data.get("original_data", {}).get("section_id", "unknown")
            enhanced_chunks = enhanced_data.get("enhanced_chunks", [])

            for chunk in enhanced_chunks:
                chunk_id = chunk.get("chunk_id", "")
                bert_entities = chunk.get("bert_ner_entities", [])
                original_relations = enhanced_data.get("original_data", {}).get("relations", [])

                # 1. 创建内容块节点
                chunk_vid = f"chunk_{chunk_id}"
                bge_embedding = chunk.get("bge_m3_embedding", {})

                try:
                    self.nebula_client.execute(
                        f'INSERT VERTEX chunk("{chunk_id}", {chunk.get("level", 0)}, '
                        f'"{chunk.get("title", "")[:50]}", '
                        f'"{chunk.get("content", "")[:100]}", '
                        f'{bge_embedding.get("embedding_dimension", 1024)}) '
                        f'IF NOT EXISTS'
                    )
                    self.stats["nebula_nodes"] += 1
                except Exception as e:
                    logger.debug(f"Chunk节点创建跳过: {e}")

                # 2. 创建实体节点和关系
                for entity in bert_entities:
                    entity_text = entity.get("text", "")
                    entity_type = entity.get("type", "")
                    if not entity_text:
                        continue

                    # 生成实体VID
                    entity_vid = f"entity_{entity_type}_{hashlib.md5(entity_text.encode('utf-8'), usedforsecurity=False).hexdigest()}"

                    # 创建实体节点
                    try:
                        self.nebula_client.execute(
                            f'INSERT VERTEX entity("{entity_type}", "{entity_text[:100]}", '
                            f'{entity.get("confidence", 0.0)}, '
                            f'\'{json.dumps(entity, ensure_ascii=False)}\') '
                            f'IF NOT EXISTS'
                        )
                        self.stats["nebula_nodes"] += 1
                    except Exception as e:
                        logger.debug(f"实体节点创建跳过: {e}")

                    # 创建内容块->实体关系（mentions）
                    try:
                        self.nebula_client.execute(
                            f'INSERT EDGE mentions("{entity_type}", {entity.get("confidence", 0.0)}, '
                            f'\'{json.dumps(entity, ensure_ascii=False)}\') '
                            f'IF NOT EXISTS'
                        )
                        self.stats["nebula_edges"] += 1
                    except Exception as e:
                        logger.debug(f"mentions边创建跳过: {e}")

                # 3. 创建实体间关系（来自原始数据）
                for relation in original_relations:
                    source = relation.get("source", "")
                    target = relation.get("target", "")
                    rel_type = relation.get("relation", "")

                    if not source or not target:
                        continue

                    try:
                        source_vid = f"entity_{hashlib.md5(source.encode('utf-8'), usedforsecurity=False).hexdigest()}"
                        target_vid = f"entity_{hashlib.md5(target.encode('utf-8'), usedforsecurity=False).hexdigest()}"

                        self.nebula_client.execute(
                            f'INSERT EDGE relates_to("{rel_type}", '
                            f'\'{json.dumps(relation, ensure_ascii=False)}\') '
                            f'IF NOT EXISTS'
                        )
                        self.stats["nebula_edges"] += 1
                    except Exception as e:
                        logger.debug(f"relates_to边创建跳过: {e}")

            return True

        except Exception as e:
            logger.error(f"❌ NebulaGraph导入失败: {e}")
            logger.error(traceback.format_exc())
            return False

    # ==================== 主导入流程 ====================

    async def process_file(self, json_path: Path) -> bool:
        """处理单个增强JSON文件"""
        try:
            with open(json_path, encoding='utf-8') as f:
                enhanced_data = json.load(f)

            # 并行导入到三个数据库
            results = await asyncio.gather(
                self.import_to_postgresql(enhanced_data),
                self.import_to_qdrant(enhanced_data),
                self.import_to_nebula(enhanced_data),
                return_exceptions=True
            )

            # 检查结果
            success_count = sum(1 for r in results if r is True)
            if success_count >= 1:  # 至少一个成功
                self.stats["processed_files"] += 1
                self.stats["total_chunks"] += len(enhanced_data.get("enhanced_chunks", []))
                return True
            else:
                self.stats["failed_files"] += 1
                for i, r in enumerate(results):
                    if isinstance(r, Exception):
                        logger.error(f"  导入错误 [{i}]: {r}")
                return False

        except Exception as e:
            logger.error(f"❌ 处理文件失败 {json_path.name}: {e}")
            self.stats["failed_files"] += 1
            return False

    async def run(self):
        """运行完整导入流程"""
        self.stats["start_time"] = datetime.now()

        logger.info("=" * 80)
        logger.info("🚀 开始增强数据导入流程")
        logger.info("=" * 80)

        # 1. 初始化所有数据库连接
        await self.initialize_postgresql()
        await self.initialize_qdrant()
        await self.initialize_nebula()

        # 2. 扫描增强JSON文件
        json_files = list(self.base_dir.glob("*.json"))
        self.stats["total_files"] = len(json_files)

        logger.info(f"📁 发现 {len(json_files)} 个增强JSON文件")
        logger.info("=" * 80)

        # 3. 批量处理文件
        batch_size = 10
        for i in range(0, len(json_files), batch_size):
            batch = json_files[i:i + batch_size]
            logger.info(f"📦 处理批次 {i // batch_size + 1}/{(len(json_files) + batch_size - 1) // batch_size}")

            for json_path in batch:
                logger.info(f"  处理: {json_path.name}")
                await self.process_file(json_path)

            # 显示进度
            progress = (i + len(batch)) / len(json_files) * 100
            logger.info(f"📊 进度: {min(progress, 100):.1f}% ({self.stats['processed_files']}/{len(json_files)})")

        self.stats["end_time"] = datetime.now()

        # 4. 显示最终统计
        self.print_statistics()

    def print_statistics(self) -> Any:
        """打印统计信息"""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        logger.info("")
        logger.info("=" * 80)
        logger.info("🎉 导入流程完成！")
        logger.info("=" * 80)
        logger.info("📊 统计信息:")
        logger.info(f"  总文件数: {self.stats['total_files']}")
        logger.info(f"  成功处理: {self.stats['processed_files']}")
        logger.info(f"  失败文件: {self.stats['failed_files']}")
        logger.info(f"  总内容块: {self.stats['total_chunks']}")
        logger.info(f"  PostgreSQL导入: {self.stats['postgresql_imported']}")
        logger.info(f"  Qdrant导入: {self.stats['qdrant_imported']}")
        logger.info(f"  Nebula节点: {self.stats['nebula_nodes']}")
        logger.info(f"  Nebula边: {self.stats['nebula_edges']}")
        logger.info(f"  处理时间: {duration:.2f}秒")
        logger.info(f"  平均速度: {self.stats['total_chunks'] / duration if duration > 0 else 0:.2f} 块/秒")
        logger.info("=" * 80)

        # 保存统计到JSON
        stats_file = self.project_root / "logs" / f"import_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                **self.stats,
                "start_time": self.stats["start_time"].isoformat(),
                "end_time": self.stats["end_time"].isoformat()
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"📄 统计信息已保存: {stats_file}")

    async def close(self):
        """关闭所有连接"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.nebula_client:
            self.nebula_client.release()
        if hasattr(self, 'nebula_pool') and self.nebula_pool:
            # NebulaGraph的close是同步方法
            self.nebula_pool.close()


async def main():
    """主函数"""
    importer = EnhancedGuidelineImporter()

    try:
        await importer.run()
    except KeyboardInterrupt:
        logger.info("⚠️ 用户中断导入流程")
    except Exception as e:
        logger.error(f"❌ 导入流程异常: {e}")
        logger.error(traceback.format_exc())
    finally:
        await importer.close()


if __name__ == "__main__":
    asyncio.run(main())
