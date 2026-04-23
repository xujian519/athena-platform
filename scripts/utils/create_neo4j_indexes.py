#!/usr/bin/env python3
"""
创建Neo4j优化索引
Create Neo4j Optimization Indexes

自动创建复合索引以提升知识图谱查询性能

作者: Athena平台团队
创建时间: 2026-03-17
版本: v1.0.0
"""

import logging
import sys

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from config.feature_flags import is_feature_enabled
from core.neo4j.neo4j_graph_client import Neo4jClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_neo4j_indexes(client: Neo4jClient):
    """
    创建Neo4j优化索引

    Args:
        client: Neo4j客户端
    """
    logger.info("=" * 60)
    logger.info("🔨 开始创建Neo4j优化索引")
    logger.info("=" * 60)

    # 索引定义
    indexes = {
        # 专利节点索引
        "专利复合索引": [
            "CREATE INDEX patent_number_date_idx IF NOT EXISTS FOR (p:Patent) ON (p.publication_number, p.application_date)",
            "CREATE INDEX patent_title_idx IF NOT EXISTS FOR (p:Patent) ON (p.title)",
            "CREATE INDEX patent_applicant_idx IF NOT EXISTS FOR (p:Patent) ON (p.applicant)",
            "CREATE INDEX patent_inventor_idx IF NOT EXISTS FOR (p:Patent) ON (p.inventor)",
            "CREATE INDEX patent_classification_idx IF NOT EXISTS FOR (p:Patent) ON (p.classification)",
        ],

        # 技术节点索引
        "技术节点索引": [
            "CREATE INDEX technology_field_idx IF NOT EXISTS FOR (t:Technology) ON (t.field, t.subfield)",
            "CREATE INDEX technology_keywords_idx IF NOT EXISTS FOR (t:Technology) ON (t.keywords)",
        ],

        # 法律概念索引
        "法律概念索引": [
            "CREATE INDEX legal_concept_idx IF NOT EXISTS FOR (lc:LegalConcept) ON (lc.name, lc.type)",
            "CREATE INDEX legal_article_idx IF NOT EXISTS FOR (la:LegalArticle) ON (la.article_number, la.law_name)",
            "CREATE INDEX case_number_idx IF NOT EXISTS FOR (c:Case) ON (c.case_number)",
            "CREATE INDEX case_title_idx IF NOT EXISTS FOR (c:Case) ON (c.title)",
        ],

        # 实体和组织索引
        "实体组织索引": [
            "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX organization_type_idx IF NOT EXISTS FOR (o:Organization) ON (o.type, o.region)",
        ],

        # 时间相关索引
        "时间索引": [
            "CREATE INDEX patent_application_date_idx IF NOT EXISTS FOR (p:Patent) ON (p.application_date)",
            "CREATE INDEX case_judgment_date_idx IF NOT EXISTS FOR (c:Case) ON (c.judgment_date)",
        ],
    }

    # 创建索引
    success_count = 0
    total_count = sum(len(v) for v in indexes.values())

    for category, queries in indexes.items():
        logger.info(f"\n📌 {category}")
        logger.info("-" * 60)

        for query in queries:
            try:
                with client.session() as session:
                    session.run(query)

                logger.info("  ✅ 索引创建成功")
                success_count += 1

            except Exception as e:
                # 索引可能已存在，不算作错误
                if "already exists" in str(e).lower() or "EquivalentSchemaRuleAlreadyExists" in str(e):
                    logger.info("  ⏭️  索引已存在，跳过")
                    success_count += 1
                else:
                    logger.warning(f"  ⚠️  索引创建失败: {e}")

    # 创建全文索引（需要特殊处理）
    logger.info("\n📌 全文索引")
    logger.info("-" * 60)

    fulltext_indexes = [
        {
            "name": "patent_fulltext_idx",
            "query": "CALL db.index.fulltext.createNodeIndex('patent_fulltext_idx', ['Patent'], ['title', 'abstract', 'description', 'claims'])"
        },
        {
            "name": "legal_concept_fulltext_idx",
            "query": "CALL db.index.fulltext.createNodeIndex('legal_concept_fulltext_idx', ['LegalConcept', 'LegalArticle'], ['name', 'content', 'description'])"
        },
        {
            "name": "technology_fulltext_idx",
            "query": "CALL db.index.fulltext.createNodeIndex('technology_fulltext_idx', ['Technology'], ['name', 'description', 'keywords'])"
        },
    ]

    for idx in fulltext_indexes:
        try:
            # 先尝试删除旧索引
            try:
                with client.session() as session:
                    session.run(f"CALL db.index.fulltext.drop('{idx['name']}')")
                logger.info(f"  🗑️  删除旧全文索引: {idx['name']}")
            except Exception:
                pass

            # 创建新索引
            with client.session() as session:
                session.run(idx['query'])

            logger.info(f"  ✅ 全文索引创建成功: {idx['name']}")
            success_count += 1
            total_count += 1

        except Exception as e:
            logger.warning(f"  ⚠️  全文索引创建失败: {e}")
            total_count += 1

    # 验证索引
    logger.info("\n📊 索引验证")
    logger.info("-" * 60)

    try:
        with client.session() as session:
            result = session.run("SHOW INDEXES")
            indexes = list(result)

            online_count = sum(1 for idx in indexes if idx.get('state') == 'ONLINE')
            logger.info(f"  总索引数: {len(indexes)}")
            logger.info(f"  在线索引数: {online_count}")
            logger.info(f"  创建成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    except Exception as e:
        logger.warning(f"  ⚠️  索引验证失败: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("✅ Neo4j索引创建完成")
    logger.info("=" * 60)


def verify_indexes():
    """验证索引状态和性能"""
    logger.info("=" * 60)
    logger.info("🔍 验证Neo4j索引状态")
    logger.info("=" * 60)

    try:
        client = Neo4jClient()
        if not client.connect():
            logger.error("❌ 连接Neo4j失败")
            return

        # 检查索引状态
        with client.session() as session:
            result = session.run("""
                SHOW INDEXES YIELD name, state, type, labelsOrTypes, properties
                RETURN name, state, type, labelsOrTypes, properties
                ORDER BY name
            """)

            indexes = list(result)

            logger.info(f"\n索引总数: {len(indexes)}")
            logger.info("-" * 60)

            # 按类型分组
            by_type = {}
            for idx in indexes:
                idx_type = idx.get('type', 'UNKNOWN')
                if idx_type not in by_type:
                    by_type[idx_type] = []
                by_type[idx_type].append(idx)

            for idx_type, idx_list in by_type.items():
                logger.info(f"\n{idx_type}索引 ({len(idx_list)}个):")
                for idx in idx_list:
                    status = "✅" if idx.get('state') == 'ONLINE' else "⚠️"
                    logger.info(f"  {status} {idx.get('name')} - {idx.get('state')}")

        # 性能测试
        logger.info("\n📊 性能测试:")
        logger.info("-" * 60)

        import time

        # 测试专利查询
        test_queries = [
            {
                "name": "专利公开号查询",
                "query": "MATCH (p:Patent {publication_number: 'CN123456'}) RETURN p LIMIT 1"
            },
            {
                "name": "专利标题模糊查询",
                "query": "MATCH (p:Patent) WHERE p.title CONTAINS '人工智能' RETURN p LIMIT 10"
            },
            {
                "name": "全文搜索测试",
                "query": "CALL db.index.fulltext.queryNodes('patent_fulltext_idx', '人工智能') YIELD node, score RETURN node.publication_number, score LIMIT 5"
            }
        ]

        for test in test_queries:
            try:
                start = time.time()
                with client.session() as session:
                    result = session.run(test['query'])
                    list(result)  # 强制执行
                elapsed = (time.time() - start) * 1000

                status = "✅" if elapsed < 40 else "⚠️"
                logger.info(f"  {status} {test['name']}: {elapsed:.2f}ms")

            except Exception as e:
                logger.warning(f"  ❌ {test['name']}: {e}")

        client.close()

    except Exception as e:
        logger.error(f"❌ 验证失败: {e}")


def main():
    """主函数"""
    # 检查特性开关
    if not is_feature_enabled("enable_neo4j_indexes"):
        logger.warning("⚠️  Neo4j索引优化未启用")
        return

    logger.info("🚀 Neo4j索引优化工具")
    logger.info("=" * 60)

    try:
        # 创建客户端
        client = Neo4jClient()

        if not client.connect():
            logger.error("❌ 连接Neo4j失败")
            return

        # 创建索引
        create_neo4j_indexes(client)

        # 验证索引
        verify_indexes()

        client.close()

    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
