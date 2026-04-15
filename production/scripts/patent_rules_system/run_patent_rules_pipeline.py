#!/usr/bin/env python3
"""
专利规则数据库处理管道 - 主执行脚本
Patent Rules Database Processing Pipeline - Main Execution Script

执行完整的专利规则处理流程：
1. 扫描源文档
2. 解析和分块
3. 向量化（BGE-M3）
4. 存储到三数据库
5. 抽取复杂语义关系
6. 构建知识图谱
7. 质量验证

用法:
    python run_patent_rules_pipeline.py --priority P0 --with-relations --incremental

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool
from qdrant_client import QdrantClient

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from production.scripts.patent_rules_system.patent_relation_extractor import (
    PatentRuleRelationExtractor,
    SemanticRelation,
)
from production.scripts.patent_rules_system.patent_rules_processor import (
    PatentRulesProcessor,
    PatentRulesStorage,
    Priority,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler('patent_rules_pipeline.log', encoding='utf-8'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class PatentRulesPipeline:
    """专利规则处理管道"""

    def __init__(self, config: dict):
        """
        初始化管道

        Args:
            config: 配置字典，包含数据库连接等信息
        """
        self.config = config
        self.processor: PatentRulesProcessor | None = None
        self.storage: PatentRulesStorage | None = None
        self.relation_extractor: PatentRuleRelationExtractor | None = None

        # 数据库连接
        self.pg_conn = None
        self.qdrant_client = None
        self.nebula_pool = None
        self.nebula_session = None

    async def initialize(self):
        """初始化管道"""
        logger.info("\n" + "=" * 60)
        logger.info("🚀 初始化专利规则处理管道")
        logger.info("=" * 60)

        # 1. 连接PostgreSQL
        logger.info("连接 PostgreSQL...")
        self.pg_conn = psycopg2.connect(
            host=self.config.get('pg_host', 'localhost'),
            port=self.config.get('pg_port', 5432),
            database=self.config.get('pg_database', 'athena_platform'),
            user=self.config.get('pg_user', 'athena_user'),
            password=self.config.get('pg_password', '')
        )
        logger.info("✅ PostgreSQL已连接")

        # 2. 连接Qdrant
        logger.info("连接 Qdrant...")
        self.qdrant_client = QdrantClient(
            url=self.config.get('qdrant_url', 'http://localhost:6333'),
            api_key=self.config.get('qdrant_api_key')
        )
        logger.info("✅ Qdrant已连接")

        # 3. 连接NebulaGraph
        logger.info("连接 NebulaGraph...")
        self.nebula_pool = ConnectionPool()
        nebula_config = Config()
        nebula_config.max_connection_pool_size = 10
        self.nebula_pool.init(
            [(self.config.get('nebula_host', '127.0.0.1'),
              self.config.get('nebula_port', 9669))],
            nebula_config
        )
        self.nebula_session = self.nebula_pool.get_session(
            self.config.get('nebula_user', 'root'),
            self.config.get('nebula_password', 'nebula')
        )
        logger.info("✅ NebulaGraph已连接")

        # 4. 初始化存储层
        logger.info("初始化存储层...")
        self.storage = PatentRulesStorage(
            self.pg_conn,
            self.qdrant_client,
            self.nebula_session
        )
        self.storage.initialize_schemas()
        logger.info("✅ 存储层已初始化")

        # 5. 初始化处理器
        logger.info("初始化处理器...")
        self.processor = PatentRulesProcessor(self.config.get('processor_config', {}))
        await self.processor.initialize()
        self.processor.set_storage(self.storage)
        logger.info("✅ 处理器已初始化")

        # 6. 初始化关系抽取器
        logger.info("初始化关系抽取器...")
        self.relation_extractor = PatentRuleRelationExtractor(
            embedding_service=self.processor.embedding_service
        )
        logger.info("✅ 关系抽取器已初始化")

        logger.info("✅ 管道初始化完成\n")

    async def run(
        self,
        priorities: list[Priority] = None,
        extract_relations: bool = True,
        incremental: bool = False
    ):
        """
        运行管道

        Args:
            priorities: 要处理的优先级列表
            extract_relations: 是否抽取关系
            incremental: 是否使用增量更新模式
        """
        if priorities is None:
            priorities = [Priority.P0, Priority.P1, Priority.P2]

        logger.info("\n" + "=" * 60)
        logger.info("🔄 运行专利规则处理管道")
        logger.info("=" * 60)
        logger.info(f"优先级: {[p.name for p in priorities]}")
        logger.info(f"抽取关系: {extract_relations}")
        logger.info(f"增量模式: {incremental}")
        logger.info("=" * 60 + "\n")

        total_start = datetime.now()

        # 扫描文档
        logger.info("📂 扫描源文档...")
        documents = self.processor.scan_documents()

        # 增量更新模式
        if incremental:
            from production.scripts.patent_rules_system.patent_incremental_updater import (
                IncrementalUpdateProcessor,
            )

            updater = IncrementalUpdateProcessor(
                manifest_file=self.config.get('manifest_file', 'patent_rules_manifest.json'),
                dry_run=False
            )

            await updater.process_updates(documents, self.processor, self.storage)

        else:
            # 全量处理模式
            await self.processor.process_documents(documents, priorities)

        # 抽取关系
        if extract_relations and self.processor.stats['total_rules'] > 0:
            logger.info("\n" + "=" * 60)
            logger.info("🔗 抽取语义关系")
            logger.info("=" * 60)

            # 获取所有已存储的规则
            all_rules = self._get_all_rules()

            if all_rules:
                relations = self.relation_extractor.extract_relations(
                    all_rules,
                    use_semantic=True
                )

                # 存储关系到NebulaGraph
                if relations:
                    await self._store_relations(relations)

        # 质量验证
        await self._validate_results()

        total_time = (datetime.now() - total_start).total_seconds()

        # 打印最终统计
        logger.info("\n" + "=" * 60)
        logger.info("📊 管道执行完成统计")
        logger.info("=" * 60)
        logger.info(f"总文档数: {self.processor.stats['total_documents']}")
        logger.info(f"总规则数: {self.processor.stats['total_rules']}")
        logger.info(f"总关系数: {self.relation_extractor.stats['total_relations'] if self.relation_extractor else 0}")
        logger.info(f"总处理时间: {total_time:.2f}秒")
        logger.info(f"平均速度: {self.processor.stats['total_rules'] / max(total_time, 1):.1f} 规则/秒")
        logger.info("=" * 60 + "\n")

    def _get_all_rules(self) -> list[dict]:
        """从数据库获取所有规则"""
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT id, rule_type, source_name, priority,
                   hierarchy_path, article_number, chapter, section,
                   content, keywords, metadata
            FROM patent_rules
            ORDER BY priority, source_name, hierarchy_path;
        """)

        rules = []
        for row in cursor.fetchall():
            rules.append({
                'id': row[0],
                'rule_type': row[1],
                'source_name': row[2],
                'priority': row[3],
                'hierarchy_path': row[4],
                'article_number': row[5],
                'chapter': row[6],
                'section': row[7],
                'content': row[8],
                'keywords': row[9],
                'metadata': row[10]
            })

        logger.info(f"✅ 从数据库读取 {len(rules)} 条规则")
        return rules

    async def _store_relations(self, relations: list[SemanticRelation]):
        """存储关系到NebulaGraph"""
        logger.info(f"存储 {len(relations)} 条关系到 NebulaGraph...")

        stored_count = 0

        for rel in relations:
            try:
                # 生成边ID
                src_vid = f"{rel.source_id}"
                dst_vid = f"{rel.target_id}"

                # 插入边
                stmt = f'''
                    INSERT EDGE `{rel.relation_type.value}`(
                        confidence, evidence, created_at
                    ) VALUES "{src_vid}"->"{dst_vid}": (
                        {rel.confidence},
                        "{rel.evidence[:100].replace(chr(34), '')}",
                        "{datetime.now().isoformat()}"
                    );
                '''

                self.nebula_session.execute(stmt)
                stored_count += 1

            except Exception as e:
                logger.debug(f"边插入失败 {rel.source_id}->{rel.target_id}: {e}")

        logger.info(f"✅ 存储 {stored_count}/{len(relations)} 条关系")

    async def _validate_results(self):
        """验证处理结果"""
        logger.info("\n" + "=" * 60)
        logger.info("🔍 质量验证")
        logger.info("=" * 60)

        # 1. PostgreSQL验证
        cursor = self.pg_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patent_rules;")
        pg_count = cursor.fetchone()[0]
        logger.info(f"✅ PostgreSQL规则数: {pg_count}")

        cursor.execute("SELECT rule_type, COUNT(*) FROM patent_rules GROUP BY rule_type;")
        logger.info("   按类型分布:")
        for row in cursor.fetchall():
            logger.info(f"     {row[0]}: {row[1]}")

        # 2. Qdrant验证
        collection_info = self.qdrant_client.get_collection(self.storage.collection_name)
        qdrant_count = collection_info.points_count
        logger.info(f"\n✅ Qdrant向量数: {qdrant_count}")

        # 3. NebulaGraph验证
        self.nebula_session.execute('USE legaldb;')
        result = self.nebula_session.execute('MATCH (v) RETURN count(v);')
        if result.is_succeeded():
            for row in result:
                logger.info(f"\n✅ NebulaGraph顶点数: {row[0]}")

        result = self.nebula_session.execute('MATCH ()-[e]->() RETURN count(e);')
        if result.is_succeeded():
            for row in result:
                logger.info(f"✅ NebulaGraph边数: {row[0]}")

        # 4. 查询测试
        logger.info("\n🔍 查询功能测试...")

        # 测试向量搜索
        test_query = "专利权的期限"
        from core.embedding.bge_embedding_service import BGEEmbeddingService
        embedding_service = BGEEmbeddingService(model_name='bge-m3', device='mps')
        query_vector = embedding_service.encode([test_query])[0]

        search_results = self.qdrant_client.search(
            collection_name=self.storage.collection_name,
            query_vector=query_vector.tolist(),
            limit=5
        )

        logger.info(f"\n查询: '{test_query}'")
        logger.info("Top 5 结果:")
        for i, result in enumerate(search_results, 1):
            logger.info(f"  {i}. [{result.payload.get('rule_type', 'N/A')}] "
                       f"{result.payload.get('content_preview', 'N/A')[:60]}... "
                       f"(相似度: {result.score:.3f})")

        logger.info("=" * 60 + "\n")

    async def close(self):
        """关闭管道"""
        logger.info("关闭管道...")

        if self.processor:
            await self.processor.close()

        if self.nebula_session:
            self.nebula_session.release()

        if self.nebula_pool:
            self.nebula_pool.close()

        if self.pg_conn:
            self.pg_conn.close()

        logger.info("✅ 管道已关闭")


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='专利规则数据库处理管道')
    parser.add_argument(
        '--priority',
        choices=['P0', 'P1', 'P2', 'ALL'],
        default='P0',
        help='处理优先级（P0=核心法律，P1=司法解释，P2=决定书，ALL=全部）'
    )
    parser.add_argument(
        '--with-relations',
        action='store_true',
        help='是否抽取复杂语义关系'
    )
    parser.add_argument(
        '--incremental',
        action='store_true',
        help='使用增量更新模式'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='试运行模式（不实际修改数据库）'
    )
    parser.add_argument(
        '--pg-host',
        default='localhost',
        help='PostgreSQL主机'
    )
    parser.add_argument(
        '--pg-port',
        type=int,
        default=5432,
        help='PostgreSQL端口'
    )
    parser.add_argument(
        '--pg-database',
        default='athena_platform',
        help='PostgreSQL数据库名'
    )
    parser.add_argument(
        '--pg-user',
        default='athena_user',
        help='PostgreSQL用户'
    )
    parser.add_argument(
        '--pg-password',
        default='',
        help='PostgreSQL密码'
    )
    parser.add_argument(
        '--qdrant-url',
        default='http://localhost:6333',
        help='Qdrant URL'
    )
    parser.add_argument(
        '--nebula-host',
        default='127.0.0.1',
        help='NebulaGraph主机'
    )
    parser.add_argument(
        '--nebula-port',
        type=int,
        default=9669,
        help='NebulaGraph端口'
    )

    args = parser.parse_args()

    # 确定优先级
    if args.priority == 'ALL':
        priorities = [Priority.P0, Priority.P1, Priority.P2]
    else:
        priorities = [Priority[args.priority]]

    # 配置
    config = {
        'source_dir': '/Users/xujian/Athena工作平台/data/专利',
        'pg_host': args.pg_host,
        'pg_port': args.pg_port,
        'pg_database': args.pg_database,
        'pg_user': args.pg_user,
        'pg_password': args.pg_password,
        'qdrant_url': args.qdrant_url,
        'nebula_host': args.nebula_host,
        'nebula_port': args.nebula_port,
        'manifest_file': 'patent_rules_manifest.json',
        'processor_config': {
            'batch_size': 32,
            'use_mps': True
        }
    }

    if args.dry_run:
        logger.info("⚠️  试运行模式，不实际修改数据库")

    try:
        # 创建管道
        pipeline = PatentRulesPipeline(config)

        # 初始化
        await pipeline.initialize()

        # 运行
        if not args.dry_run:
            await pipeline.run(
                priorities=priorities,
                extract_relations=args.with_relations,
                incremental=args.incremental
            )
        else:
            logger.info("试运行模式：仅扫描文档")
            pipeline.processor = PatentRulesProcessor(config)
            await pipeline.processor.initialize()
            documents = pipeline.processor.scan_documents()
            logger.info(f"发现 {sum(len(docs) for docs in documents.values())} 个文档")

    except Exception as e:
        logger.error(f"❌ 管道执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # 关闭管道
        if not args.dry_run:
            await pipeline.close()

    logger.info("✅ 执行完成！")


if __name__ == "__main__":
    asyncio.run(main())
