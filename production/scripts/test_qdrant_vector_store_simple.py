#!/usr/bin/env python3
"""
测试Qdrant向量库系统（简化版）
Test Qdrant Vector Store System (Simplified)

作者: Athena平台团队
创建时间: 2025-12-20
"""

from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_collection_creation():
    """测试集合创建"""
    logger.info("="*60)
    logger.info("测试1: 集合创建")
    logger.info("="*60)

    from patent_rules_system.qdrant_vector_store_simple import QdrantVectorStoreSimple

    store = QdrantVectorStoreSimple(collection_name="test_patent_rules")

    # 创建集合
    result = await store.create_collection()

    logger.info(f"集合创建结果: {'✅ 成功' if result else '❌ 失败'}")

    # 检查文件输出
    config_file = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/qdrant_store/test_patent_rules_config.json")

    if config_file.exists():
        logger.info(f"  ✅ 集合配置文件: {config_file}")
        with open(config_file, encoding='utf-8') as f:
            config = json.load(f)
            logger.info(f"     集合名: {config.get('collection_name')}")
            logger.info(f"     向量维度: {config.get('vector_size')}")
            logger.info(f"     距离度量: {config.get('distance')}")
    else:
        logger.warning("  ❌ 集合配置文件不存在")

    return result or config_file.exists()

async def test_embedding_generation():
    """测试向量生成"""
    logger.info("\n" + "="*60)
    logger.info("测试2: 向量生成")
    logger.info("="*60)

    from patent_rules_system.qdrant_vector_store_simple import QdrantVectorStoreSimple

    store = QdrantVectorStoreSimple()

    # 测试不同文本的向量生成
    test_texts = [
        ("专利法第一条为了保护专利权人的合法权益", "专利法"),
        ("发明专利的申请应当提交请求书、说明书及其摘要", "审查指南"),
        ("2025年修改新增了AI相关发明的审查标准", "2025年修改"),
        ("实用新型专利的保护期限为十年", "实施细则")
    ]

    embeddings = []
    for text, doc_type in test_texts:
        embedding = await store.generate_embedding(text, doc_type)
        embeddings.append(embedding)

        logger.info(f"  文本: {text[:30]}...")
        logger.info(f"    类型: {doc_type}")
        logger.info(f"    向量维度: {len(embedding)}")
        logger.info(f"    向量范数: {sum(x*x for x in embedding)**0.5:.4f}")

    # 检查向量唯一性
    unique_vectors = len({tuple(round(x, 6) for x in emb) for emb in embeddings})
    logger.info(f"\n向量唯一性: {unique_vectors}/{len(embeddings)}")

    # 检查缓存
    stats = store.get_statistics()
    logger.info(f"缓存大小: {stats.get('cache_size', 0)}")

    success = len(embeddings) == len(test_texts) and unique_vectors >= 3
    logger.info(f"\n验证结果: {'✅ 成功' if success else '❌ 失败'}")
    return success

async def test_document_indexing():
    """测试文档索引"""
    logger.info("\n" + "="*60)
    logger.info("测试3: 文档索引")
    logger.info("="*60)

    from patent_rules_system.qdrant_vector_store_simple import (
        DocumentType,
        QdrantVectorStoreSimple,
        VectorDocument,
    )

    store = QdrantVectorStoreSimple(collection_name="test_indexing")
    await store.create_collection()

    # 创建测试文档
    test_docs = [
        VectorDocument(
            doc_id="test_patent_law_001",
            content="第一条 为了保护专利权人的合法权益，鼓励发明创造，推动发明创造的应用，提高创新能力，促进科学技术进步和经济社会发展，制定本法。",
            doc_type=DocumentType.PATENT_LAW,
            metadata={
                "title": "中华人民共和国专利法",
                "version": "2023",
                "article_number": "第一条"
            }
        ),
        VectorDocument(
            doc_id="test_guideline_001",
            content="第二部分第二章发明专利的审查。2.1发明专利申请的初步审查。初步审查应当审查申请文件是否齐备，格式是否符合规定。",
            doc_type=DocumentType.GUIDELINE,
            metadata={
                "title": "专利审查指南",
                "part": "第二部分",
                "chapter": "第二章",
                "section": "2.1"
            }
        ),
        VectorDocument(
            doc_id="test_modification_2025_001",
            content="2025年修改：新增了人工智能、大数据相关发明的审查标准。算法模型的可专利性审查需要体现技术创新性。",
            doc_type=DocumentType.MODIFICATION_2025,
            metadata={
                "modification_type": "新增",
                "application_date": "2026-01-01",
                "affected_sections": ["第二部分", "第四章"]
            },
            modified_2025={
                "change_type": "new_section",
                "key_additions": ["AI相关发明", "算法模型", "技术创新性"]
            }
        )
    ]

    # 索引文档
    success_count = 0
    for doc in test_docs:
        if await store.index_document(doc):
            success_count += 1
            logger.info(f"  ✅ 索引成功: {doc.doc_id}")
        else:
            logger.error(f"  ❌ 索引失败: {doc.doc_id}")

    # 验证索引结果
    logger.info(f"\n索引统计: {success_count}/{len(test_docs)} 成功")

    # 检查数据文件
    data_file = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/qdrant_store/test_indexing.json")
    if data_file.exists():
        with open(data_file, encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"  数据文件中的点数: {len(data)}")

    success = success_count == len(test_docs)
    logger.info(f"\n验证结果: {'✅ 成功' if success else '❌ 失败'}")
    return success

async def test_search_modes():
    """测试搜索模式"""
    logger.info("\n" + "="*60)
    logger.info("测试4: 搜索模式")
    logger.info("="*60)

    from patent_rules_system.qdrant_vector_store_simple import (
        DocumentType,
        QdrantVectorStoreSimple,
        SearchMode,
        VectorDocument,
    )

    store = QdrantVectorStoreSimple(collection_name="test_search")
    await store.create_collection()

    # 先索引一些文档
    docs = [
        VectorDocument(
            doc_id="doc1",
            content="专利权是一种独占权，未经专利权人许可，不得实施其专利",
            doc_type=DocumentType.PATENT_LAW,
            metadata={"article": "第十一条"}
        ),
        VectorDocument(
            doc_id="doc2",
            content="发明专利的保护期限为二十年，实用新型专利权和外观设计专利权的期限为十年",
            doc_type=DocumentType.PATENT_LAW,
            metadata={"article": "第四十二条"}
        ),
        VectorDocument(
            doc_id="doc3",
            content="2025年修改明确了AI算法的可专利性审查标准，要求体现技术创新",
            doc_type=DocumentType.MODIFICATION_2025,
            metadata={"section": "AI相关发明"}
        ),
        VectorDocument(
            doc_id="doc4",
            content="审查指南规定，发明专利申请必须进行实质审查",
            doc_type=DocumentType.GUIDELINE,
            metadata={"part": "第二部分"}
        )
    ]

    for doc in docs:
        await store.index_document(doc)

    # 测试不同搜索模式
    query = "专利的保护期限和AI发明的审查"
    search_modes = [
        (SearchMode.SEMANTIC, "纯语义搜索"),
        (SearchMode.HYBRID, "混合搜索"),
        (SearchMode.RERANK, "重排序搜索")
    ]

    results_summary = []
    for mode, mode_name in search_modes:
        try:
            results = await store.search(
                query=query,
                top_k=3,
                search_mode=mode
            )

            logger.info(f"\n{mode_name}:")
            logger.info(f"  结果数量: {len(results)}")
            for i, result in enumerate(results):
                logger.info(f"    {i+1}. {result.doc_id} (分数: {result.score:.3f})")
                if result.explanation:
                    logger.info(f"       说明: {result.explanation}")

            results_summary.append((mode_name, len(results), results[0].score if results else 0))

        except Exception as e:
            logger.error(f"  ❌ {mode_name} 失败: {e}")
            results_summary.append((mode_name, 0, 0))

    # 验证结果
    success = any(count > 0 for _, count, _ in results_summary)
    logger.info(f"\n搜索验证: {'✅ 成功' if success else '❌ 失败'}")
    return success

async def test_rerank_optimization():
    """测试重排序优化"""
    logger.info("\n" + "="*60)
    logger.info("测试5: 重排序优化")
    logger.info("="*60)

    from patent_rules_system.qdrant_vector_store_simple import (
        DocumentType,
        QdrantVectorStoreSimple,
        SearchMode,
        VectorDocument,
    )

    store = QdrantVectorStoreSimple(collection_name="test_rerank")
    await store.create_collection()

    # 创建不同类型和重要性的文档
    docs = [
        VectorDocument(
            doc_id="legal1",
            content="专利权的取得和行使，应当遵循诚实信用原则",
            doc_type=DocumentType.PATENT_LAW,
            metadata={"importance": "high"}
        ),
        VectorDocument(
            doc_id="guideline1",
            content="审查指南规定了专利申请的具体流程",
            doc_type=DocumentType.GUIDELINE,
            metadata={"importance": "medium"}
        ),
        VectorDocument(
            doc_id="mod2025_1",
            content="2025年修改新增了AI和大数据相关发明的特殊审查规则",
            doc_type=DocumentType.MODIFICATION_2025,
            metadata={"importance": "high", "has_2025_modification": True}
        ),
        VectorDocument(
            doc_id="interpretation1",
            content="最高人民法院司法解释明确了专利侵权判定的标准",
            doc_type=DocumentType.JUDICIAL_INTERPRETATION,
            metadata={"importance": "high"}
        ),
        VectorDocument(
            doc_id="rules1",
            content="专利法实施细则详细规定了申请文件的格式要求",
            doc_type=DocumentType.IMPLEMENTATION_RULES,
            metadata={"importance": "medium"}
        )
    ]

    # 索引文档
    for doc in docs:
        await store.index_document(doc)

    # 测试重排序
    query = "专利的法律保护和2025年修改"

    # 1. 不使用重排序
    results_no_rerank = await store.search(
        query=query,
        top_k=5,
        search_mode=SearchMode.SEMANTIC
    )

    # 2. 使用重排序
    results_with_rerank = await store.search(
        query=query,
        top_k=5,
        search_mode=SearchMode.RERANK
    )

    logger.info("\n不使用重排序:")
    for i, result in enumerate(results_no_rerank):
        logger.info(f"  {i+1}. {result.doc_id} ({result.doc_type.value}): {result.score:.3f}")

    logger.info("\n使用重排序:")
    for i, result in enumerate(results_with_rerank):
        logger.info(f"  {i+1}. {result.doc_id} ({result.doc_type.value}): {result.score:.3f} (重排序: {result.rerank_score:.3f})")
        if result.explanation:
            logger.info(f"      {result.explanation}")

    # 验证重排序效果
    rerank_stats = store.get_statistics()
    rerank_queries = rerank_stats.get("rerank_queries", 0)

    success = (
        len(results_with_rerank) > 0 and
        any(r.rerank_score is not None for r in results_with_rerank) and
        rerank_queries > 0
    )

    logger.info(f"\n重排序验证: {'✅ 成功' if success else '❌ 失败'}")
    logger.info(f"重排序查询数: {rerank_queries}")
    return success

async def test_batch_operations():
    """测试批量操作"""
    logger.info("\n" + "="*60)
    logger.info("测试6: 批量操作")
    logger.info("="*60)

    from patent_rules_system.qdrant_vector_store_simple import (
        DocumentType,
        QdrantVectorStoreSimple,
        VectorDocument,
    )

    store = QdrantVectorStoreSimple(collection_name="test_batch")
    await store.create_collection()

    # 创建批量文档
    batch_docs = []
    for i in range(20):
        doc = VectorDocument(
            doc_id=f"batch_doc_{i:03d}",
            content=f"这是第{i+1}个测试文档，内容涉及专利法的第{i+1}条规定",
            doc_type=DocumentType.PATENT_LAW,
            metadata={
                "batch_id": 1,
                "doc_index": i,
                "creation_time": datetime.now().isoformat()
            }
        )
        batch_docs.append(doc)

    # 批量索引
    logger.info(f"开始批量索引 {len(batch_docs)} 个文档...")
    start_time = datetime.now()
    batch_result = await store.batch_index(batch_docs)
    batch_time = (datetime.now() - start_time).total_seconds()

    logger.info("批量索引完成:")
    logger.info(f"  成功: {batch_result['success']}")
    logger.info(f"  失败: {batch_result['error']}")
    logger.info(f"  总计: {batch_result['total']}")
    logger.info(f"  耗时: {batch_time:.3f}s")
    logger.info(f"  平均: {batch_time/len(batch_docs)*1000:.1f}ms/文档")

    # 验证索引结果
    success_rate = batch_result['success'] / batch_result['total']
    logger.info(f"  成功率: {success_rate*100:.1f}%")

    # 测试批量搜索
    search_results = await store.search(
        query="专利法规定",
        top_k=10
    )

    logger.info(f"\n搜索结果: {len(search_results)} 个文档")
    if search_results:
        logger.info(f"  最高分数: {max(r.score for r in search_results):.3f}")
        logger.info(f"  最低分数: {min(r.score for r in search_results):.3f}")

    success = success_rate >= 0.9 and len(search_results) > 0
    logger.info(f"\n批量操作验证: {'✅ 成功' if success else '❌ 失败'}")
    return success

async def test_statistics():
    """测试统计功能"""
    logger.info("\n" + "="*60)
    logger.info("测试7: 统计功能")
    logger.info("="*60)

    from patent_rules_system.qdrant_vector_store_simple import QdrantVectorStoreSimple

    store = QdrantVectorStoreSimple(collection_name="test_stats")

    # 获取初始统计
    initial_stats = store.get_statistics()
    logger.info("初始统计:")
    logger.info(f"  索引文档数: {initial_stats.get('documents_indexed', 0)}")
    logger.info(f"  搜索查询数: {initial_stats.get('search_queries', 0)}")
    logger.info(f"  总搜索时间: {initial_stats.get('total_search_time', 0):.3f}s")
    logger.info(f"  缓存大小: {initial_stats.get('cache_size', 0)}")

    # 执行一些操作
    await store.create_collection()

    # 模拟索引和搜索
    await store.search("测试查询", top_k=5)
    await store.search("另一个查询", top_k=3)

    # 获取更新后的统计
    updated_stats = store.get_statistics()
    logger.info("\n更新后统计:")
    logger.info(f"  索引文档数: {updated_stats.get('documents_indexed', 0)}")
    logger.info(f"  搜索查询数: {updated_stats.get('search_queries', 0)}")
    logger.info(f"  总搜索时间: {updated_stats.get('total_search_time', 0):.3f}s")
    logger.info(f"  平均搜索时间: {updated_stats.get('average_search_time', 0):.3f}s")
    logger.info(f"  缓存命中数: {updated_stats.get('cache_hits', 0)}")
    logger.info(f"  重排序查询数: {updated_stats.get('rerank_queries', 0)}")

    # 检查集合信息
    collection_info = updated_stats.get('collection_info', {})
    if collection_info:
        logger.info("\n集合信息:")
        logger.info(f"  集合名: {collection_info.get('collection_name')}")
        logger.info(f"  向量维度: {collection_info.get('vector_size')}")
        logger.info(f"  距离度量: {collection_info.get('distance')}")
        logger.info(f"  文档数量: {collection_info.get('points_count', 0)}")

    # 验证统计完整性
    expected_keys = [
        "documents_indexed", "search_queries", "total_search_time",
        "cache_hits", "rerank_queries", "cache_size"
    ]

    has_all_keys = all(key in updated_stats for key in expected_keys)
    queries_increased = updated_stats.get('search_queries', 0) > initial_stats.get('search_queries', 0)

    success = has_all_keys and queries_increased
    logger.info(f"\n统计验证: {'✅ 成功' if success else '❌ 失败'}")
    return success

async def test_cache_performance():
    """测试缓存性能"""
    logger.info("\n" + "="*60)
    logger.info("测试8: 缓存性能")
    logger.info("="*60)

    from patent_rules_system.qdrant_vector_store_simple import QdrantVectorStoreSimple

    store = QdrantVectorStoreSimple()

    # 测试向量生成缓存
    test_text = "专利权的保护范围以权利要求的内容为准"
    doc_type = "专利法"

    # 第一次生成（无缓存）
    logger.info("第一次生成向量...")
    start_time = datetime.now()
    embedding1 = await store.generate_embedding(test_text, doc_type)
    first_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"  耗时: {first_time*1000:.1f}ms")

    # 第二次生成（使用缓存）
    logger.info("\n第二次生成向量（使用缓存）...")
    start_time = datetime.now()
    embedding2 = await store.generate_embedding(test_text, doc_type)
    cached_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"  耗时: {cached_time*1000:.1f}ms")

    # 验证缓存效果
    cache_stats = store.get_statistics()
    cache_hits = cache_stats.get('cache_hits', 0)
    cache_size = cache_stats.get('cache_size', 0)

    logger.info("\n缓存统计:")
    logger.info(f"  缓存命中数: {cache_hits}")
    logger.info(f"  缓存大小: {cache_size}")

    # 检查向量一致性
    vectors_equal = embedding1 == embedding2
    logger.info(f"  向量一致性: {'✅' if vectors_equal else '❌'}")

    # 测试缓存清理
    logger.info("\n清理缓存...")
    store.clear_cache()
    cleared_stats = store.get_statistics()
    cache_cleared = cleared_stats.get('cache_size', 0) == 0
    logger.info(f"  缓存清理: {'✅ 成功' if cache_cleared else '❌ 失败'}")

    # 性能提升计算
    if cached_time > 0:
        speedup = first_time / cached_time if cached_time > 0 else 1
        logger.info(f"\n性能提升: {speedup:.1f}x")

    success = (
        vectors_equal and
        cache_hits > 0 and
        cache_cleared
    )

    logger.info(f"\n缓存性能验证: {'✅ 成功' if success else '❌ 失败'}")
    return success

async def main():
    """主测试函数"""
    logger.info("\n" + "="*80)
    logger.info("Qdrant向量库系统测试（简化版）")
    logger.info("="*80)

    # 执行测试
    tests = [
        ("集合创建", test_collection_creation),
        ("向量生成", test_embedding_generation),
        ("文档索引", test_document_indexing),
        ("搜索模式", test_search_modes),
        ("重排序优化", test_rerank_optimization),
        ("批量操作", test_batch_operations),
        ("统计功能", test_statistics),
        ("缓存性能", test_cache_performance)
    ]

    test_results = []
    for test_name, test_func in tests:
        try:
            logger.info(f"\n开始测试: {test_name}")
            result = await test_func()
            test_results.append((test_name, result, None))
            status = "✅" if result else "❌"
            logger.info(f"{status} {test_name} 测试完成")
        except Exception as e:
            test_results.append((test_name, False, str(e)))
            logger.error(f"❌ {test_name} 测试失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())

    # 生成测试报告
    logger.info("\n" + "="*80)
    logger.info("测试报告")
    logger.info("="*80)

    passed_count = 0
    for test_name, result, error in test_results:
        if result:
            logger.info(f"✅ {test_name}: 通过")
            passed_count += 1
        else:
            logger.error(f"❌ {test_name}: 失败")
            if error:
                logger.error(f"   错误: {error}")

    logger.info(f"\n总计: {passed_count}/{len(test_results)} 个测试通过")

    # 保存测试报告
    report_file = Path("/Users/xujian/Athena工作平台/production/logs/qdrant_vector_store_simple_test_report.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "test_time": datetime.now().isoformat(),
        "total_tests": len(test_results),
        "passed_tests": passed_count,
        "test_results": [
            {
                "name": name,
                "passed": result,
                "error": error
            }
            for name, result, error in test_results
        ]
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    logger.info(f"\n📋 测试报告已保存: {report_file}")

    return passed_count == len(test_results)

if __name__ == "__main__":
    # 添加脚本路径到sys.path
    import sys
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))

    # 运行测试
    success = asyncio.run(main())

    if success:
        logger.info("\n🎉 所有测试通过！Qdrant向量库系统功能正常。")
    else:
        logger.warning("\n⚠️ 部分测试失败，请检查日志。")

    exit(0 if success else 1)
