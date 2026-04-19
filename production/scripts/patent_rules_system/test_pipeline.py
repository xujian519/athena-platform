#!/usr/bin/env python3
"""
测试专利规则处理管道
Test Patent Rules Processing Pipeline

在不修改数据库的情况下测试整个处理流程

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from production.scripts.patent_rules_system.patent_rules_processor import (
    DocumentType,
    PatentRulesProcessor,
    Priority,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_parser():
    """测试文档解析器"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 测试文档解析器")
    logger.info("=" * 60)

    # 创建处理器
    processor = PatentRulesProcessor()
    await processor.initialize()

    # 扫描P0文档
    documents = processor.scan_documents()
    p0_docs = documents[Priority.P0]

    logger.info(f"\n发现 {len(p0_docs)} 个P0文档")

    # 测试解析第一个文档
    if p0_docs:
        file_path, doc_type = p0_docs[0]
        logger.info(f"\n测试解析: {file_path.name}")

        processed_doc = processor.parser.parse_document(file_path, doc_type, Priority.P0)

        logger.info(f"✅ 提取 {len(processed_doc.rules)} 条规则")
        logger.info(f"   处理时间: {processed_doc.processing_time:.2f}秒")

        # 显示前3条规则
        logger.info("\n前3条规则:")
        for i, rule in enumerate(processed_doc.rules[:3], 1):
            logger.info(f"\n{i}. {rule.hierarchy_path}")
            logger.info(f"   类型: {rule.rule_type}")
            logger.info(f"   内容: {rule.content[:100]}...")

        # 测试向量化
        logger.info("\n测试向量化...")
        texts = [rule.content for rule in processed_doc.rules[:10]]  # 只测试前10条
        embeddings = processor.embedding_service.encode(texts)

        logger.info("✅ 向量化完成")
        logger.info(f"   向量维度: {len(embeddings[0])}")
        logger.info(f"   向量示例（前5维）: {embeddings[0][:5].tolist()}")

    await processor.close()


async def test_examination_guide():
    """测试审查指南解析（大文件）"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 测试审查指南解析")
    logger.info("=" * 60)

    processor = PatentRulesProcessor()
    await processor.initialize()

    # 查找审查指南
    guide_path = Path("/Users/xujian/Athena工作平台/data/专利/专利审查指南（最新版）.md")

    if not guide_path.exists():
        logger.error(f"文件不存在: {guide_path}")
        return

    logger.info(f"文件大小: {guide_path.stat().st_size / 1024 / 1024:.2f} MB")

    # 解析
    processed_doc = processor.parser.parse_document(
        guide_path,
        DocumentType.EXAMINATION_GUIDE,
        Priority.P0
    )

    logger.info(f"✅ 提取 {len(processed_doc.rules)} 个分块")
    logger.info(f"   处理时间: {processed_doc.processing_time:.2f}秒")

    # 显示分块统计
    chunk_sizes = [len(rule.content) for rule in processed_doc.rules]
    logger.info("\n分块大小统计:")
    logger.info(f"   平均: {sum(chunk_sizes) / len(chunk_sizes):.0f} 字符")
    logger.info(f"   最小: {min(chunk_sizes)} 字符")
    logger.info(f"   最大: {max(chunk_sizes)} 字符")

    # 显示前2个分块
    logger.info("\n前2个分块:")
    for i, rule in enumerate(processed_doc.rules[:2], 1):
        logger.info(f"\n{i}. {rule.hierarchy_path}")
        logger.info(f"   内容: {rule.content[:150]}...")

    await processor.close()


async def test_decision_parsing():
    """测试决定书解析"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 测试决定书解析")
    logger.info("=" * 60)

    processor = PatentRulesProcessor()

    # 查找决定书
    decision_dir = Path("/Users/xujian/Athena工作平台/data/专利/无效复审决定_cleaned")

    if not decision_dir.exists():
        logger.warning(f"目录不存在: {decision_dir}")
        return

    # 获取第一个文件
    decision_files = list(decision_dir.glob("*.md"))[:3]  # 测试3个文件

    logger.info(f"测试 {len(decision_files)} 个决定书文件")

    for file_path in decision_files:
        logger.info(f"\n解析: {file_path.name}")
        processed_doc = processor.parser.parse_document(
            file_path,
            DocumentType.INVALIDATION_DECISION,
            Priority.P2
        )

        logger.info(f"✅ 提取 {len(processed_doc.rules)} 条规则")
        if processed_doc.rules:
            rule = processed_doc.rules[0]
            logger.info(f"   决定号: {rule.article_number}")
            logger.info(f"   内容: {rule.content[:200]}...")

    logger.info("\n✅ 决定书解析测试完成")


async def test_relation_extraction():
    """测试关系抽取"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 测试关系抽取")
    logger.info("=" * 60)

    from production.scripts.patent_rules_system.patent_relation_extractor import (
        PatentRuleRelationExtractor,
    )

    # 创建测试规则
    test_rules = [
        {
            'id': 'rule_001',
            'content': '专利权的期限为二十年，自申请日起计算。',
            'article_number': '第四十二条',
            'chapter': '第一章',
            'section': None
        },
        {
            'id': 'rule_002',
            'content': '发明专利权的期限为二十年，实用新型专利权的期限为十年，外观设计专利权的期限为十五年，均自申请日起计算。',
            'article_number': '第四十二条',
            'chapter': '第一章',
            'section': None
        },
        {
            'id': 'rule_003',
            'content': '专利权人应当自被授予专利权的当年开始缴纳年费。',
            'article_number': '第四十三条',
            'chapter': '第一章',
            'section': None
        },
        {
            'id': 'rule_004',
            'content': '有下列情形之一的，专利权在期限届满前终止：（一）没有按照规定缴纳年费的；（二）专利权人以书面声明放弃其专利权的。',
            'article_number': '第四十四条',
            'chapter': '第一章',
            'section': None
        }
    ]

    # 初始化抽取器（不使用嵌入服务）
    extractor = PatentRuleRelationExtractor(embedding_service=None)

    # 抽取关系
    relations = extractor.extract_relations(test_rules, use_semantic=False)

    logger.info(f"\n✅ 抽取 {len(relations)} 条关系")

    for i, rel in enumerate(relations, 1):
        logger.info(f"\n{i}. {rel.relation_type.value}")
        logger.info(f"   源: {rel.source_id}")
        logger.info(f"   目标: {rel.target_id}")
        logger.info(f"   置信度: {rel.confidence:.3f}")
        logger.info(f"   证据: {rel.evidence[:80]}...")


async def main():
    """主测试函数"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 专利规则处理管道测试")
    logger.info("=" * 60)

    # 测试1: 基本文档解析
    await test_parser()

    # 测试2: 审查指南解析
    # await test_examination_guide()

    # 测试3: 决定书解析
    # await test_decision_parsing()

    # 测试4: 关系抽取
    # await test_relation_extraction()

    logger.info("\n" + "=" * 60)
    logger.info("✅ 所有测试完成")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
