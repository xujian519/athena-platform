#!/usr/bin/env python3
"""
测试NebulaGraph知识图谱构建器
Test NebulaGraph Knowledge Graph Builder

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

async def test_space_initialization():
    """测试空间初始化"""
    logger.info("="*60)
    logger.info("测试1: 空间初始化")
    logger.info("="*60)

    from patent_rules_system.nebula_graph_builder import NebulaGraphBuilder

    # 初始化构建器
    builder = NebulaGraphBuilder()

    # 初始化空间
    result = await builder.initialize_space()

    logger.info(f"空间初始化结果: {'✅ 成功' if result else '❌ 失败'}")

    # 检查文件输出
    graph_dir = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/knowledge_graph")
    schema_file = graph_dir / "nebula_schema.json"

    if schema_file.exists():
        logger.info(f"  ✅ 空间模式文件: {schema_file}")
        with open(schema_file, encoding='utf-8') as f:
            schema = json.load(f)
            logger.info(f"     空间名: {schema.get('space_name')}")
            logger.info(f"     标签数量: {len(schema.get('tags', {}))}")
            logger.info(f"     边类型数量: {len(schema.get('edges', {}))}")
    else:
        logger.warning("  ❌ 空间模式文件不存在")

    return result or schema_file.exists()

async def test_vertex_creation():
    """测试顶点创建"""
    logger.info("\n" + "="*60)
    logger.info("测试2: 顶点创建")
    logger.info("="*60)

    from patent_rules_system.nebula_graph_builder import (
        GraphEntity,
        GraphEntityType,
        NebulaGraphBuilder,
    )

    builder = NebulaGraphBuilder()

    # 创建测试文档顶点
    doc_vertex = GraphEntity(
        vertex_id="test_doc_001",
        entity_type=GraphEntityType.DOCUMENT,
        properties={
            "title": "专利法测试文档",
            "version": "2023",
            "source_type": "PDF",
            "created_at": datetime.now().isoformat()
        }
    )

    # 保存顶点
    await builder._save_vertex_to_file(doc_vertex)

    # 创建测试法条顶点
    article_vertex = GraphEntity(
        vertex_id="test_article_001",
        entity_type=GraphEntityType.LAW_ARTICLE,
        properties={
            "article_number": "第一条",
            "content": "为了保护专利权人的合法权益...",
            "full_text": "第一条 为了保护专利权人的合法权益，鼓励发明创造..."
        }
    )

    await builder._save_vertex_to_file(article_vertex)

    # 创建2025年修改顶点
    mod_vertex = GraphEntity(
        vertex_id="test_mod_2025",
        entity_type=GraphEntityType.MODIFICATION_2025,
        properties={
            "change_type": "amended",
            "old_content": "原内容",
            "new_content": "新内容",
            "application_date": "2026-01-01"
        }
    )

    await builder._save_vertex_to_file(mod_vertex)

    # 验证文件
    vertices_file = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/knowledge_graph/vertices.json")
    if vertices_file.exists():
        with open(vertices_file, encoding='utf-8') as f:
            vertices = json.load(f)
            logger.info(f"  ✅ 保存了 {len(vertices)} 个顶点")

            # 验证顶点类型
            doc_count = sum(1 for v in vertices if v['type'] == 'Document')
            article_count = sum(1 for v in vertices if v['type'] == 'LawArticle')
            mod_count = sum(1 for v in vertices if v['type'] == 'Modification2025')

            logger.info(f"     文档顶点: {doc_count}")
            logger.info(f"     法条顶点: {article_count}")
            logger.info(f"     修改顶点: {mod_count}")

            success = doc_count >= 1 and article_count >= 1 and mod_count >= 1
            logger.info(f"验证结果: {'✅ 成功' if success else '❌ 失败'}")
            return success
    else:
        logger.error("  ❌ 顶点文件未创建")
        return False

async def test_edge_creation():
    """测试边创建"""
    logger.info("\n" + "="*60)
    logger.info("测试3: 边创建")
    logger.info("="*60)

    from patent_rules_system.nebula_graph_builder import (
        GraphRelation,
        GraphRelationType,
        NebulaGraphBuilder,
    )

    builder = NebulaGraphBuilder()

    # 创建包含关系
    contains_relation = GraphRelation(
        edge_id="rel_contains_001",
        relation_type=GraphRelationType.CONTAINS,
        src_vertex_id="test_doc_001",
        dst_vertex_id="test_article_001",
        properties={
            "relationship": "contains",
            "created_at": datetime.now().isoformat()
        }
    )

    await builder._save_edge_to_file(contains_relation)

    # 创建引用关系
    references_relation = GraphRelation(
        edge_id="rel_references_001",
        relation_type=GraphRelationType.REFERENCES,
        src_vertex_id="test_article_002",
        dst_vertex_id="test_article_001",
        properties={
            "context": "根据该条款...",
            "confidence": 0.9
        }
    )

    await builder._save_edge_to_file(references_relation)

    # 创建2025年引入关系
    intro_2025_relation = GraphRelation(
        edge_id="rel_intro_2025_001",
        relation_type=GraphRelationType.INTRODUCED_IN,
        src_vertex_id="test_mod_2025",
        dst_vertex_id="test_concept_001",
        properties={
            "date": "2025-06-01",
            "confidence": 0.95
        }
    )

    await builder._save_edge_to_file(intro_2025_relation)

    # 验证文件
    edges_file = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/knowledge_graph/edges.json")
    if edges_file.exists():
        with open(edges_file, encoding='utf-8') as f:
            edges = json.load(f)
            logger.info(f"  ✅ 保存了 {len(edges)} 条边")

            # 验证边类型
            contains_count = sum(1 for e in edges if e['type'] == 'CONTAINS')
            references_count = sum(1 for e in edges if e['type'] == 'REFERENCES')
            intro_2025_count = sum(1 for e in edges if e['type'] == 'INTRODUCED_IN')

            logger.info(f"     包含关系: {contains_count}")
            logger.info(f"     引用关系: {references_count}")
            logger.info(f"     2025引入关系: {intro_2025_count}")

            success = contains_count >= 1 and references_count >= 1
            logger.info(f"验证结果: {'✅ 成功' if success else '❌ 失败'}")
            return success
    else:
        logger.error("  ❌ 边文件未创建")
        return False

async def test_graph_building_from_data():
    """测试从数据构建图谱"""
    logger.info("\n" + "="*60)
    logger.info("测试4: 从数据构建图谱")

    from patent_rules_system.nebula_graph_builder import NebulaGraphBuilder

    builder = NebulaGraphBuilder()

    # 创建测试数据文件
    test_data = {
        "doc_id": "test_patent_law_2025",
        "metadata": {
            "title": "中华人民共和国专利法（2025年修订版）",
            "version": "2025",
            "source_type": "PDF",
            "file_path": "/test/patent_law_2025.pdf"
        },
        "sections": [
            {
                "section_id": "P1",
                "level": 1,
                "title": "第一部分 总则",
                "content": "为了保护专利权人的合法权益，鼓励发明创造...",
                "modification_2025": {
                    "change_type": "amended",
                    "added_content": "特别关注人工智能和大数据领域"
                }
            },
            {
                "section_id": "C1",
                "level": 2,
                "title": "第一章 发明和实用新型",
                "content": "第一章规定了发明和实用新型的定义...",
                "modification_2025": {
                    "change_type": "new_section",
                    "title": "AI相关发明"
                }
            },
            {
                "section_id": "A1",
                "level": 3,
                "title": "第一条",
                "content": "为了保护专利权人的合法权益，鼓励发明创造...",
                "modification_2025": {
                    "change_type": "modified",
                    "old_content": "原有的审查标准",
                    "new_content": "新的审查标准，特别考虑AI和大数据"
                }
            }
        ],
        "entities": [
            {
                "entity_id": "entity_patent_right",
                "entity_type": "专利权",
                "entity_text": "专利权",
                "confidence": 0.95,
                "extraction_method": "nlp"
            },
            {
                "entity_id": "entity_invention",
                "entity_type": "发明",
                "entity_text": "发明",
                "confidence": 0.92,
                "extraction_method": "rule"
            },
            {
                "entity_id": "entity_ai",
                "entity_type": "AI相关章节",
                "entity_text": "AI相关发明",
                "confidence": 0.88,
                "extraction_method": "keyword"
            }
        ],
        "relations": [
            {
                "relation_id": "rel_001",
                "relation_type": "2025年引入",
                "source_entity_id": "C1",
                "target_entity_id": "entity_ai",
                "confidence": 0.90,
                "evidence": "第一章新增了AI相关发明",
                "extraction_method": "rule"
            },
            {
                "relation_id": "rel_002",
                "relation_type": "修改为",
                "source_entity_id": "A1",
                "target_entity_id": "entity_invention",
                "confidence": 0.85,
                "evidence": "审查标准已修改",
                "extraction_method": "nlp"
            }
        ]
    }

    # 保存测试数据
    processed_dir = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    test_file = processed_dir / "test_patent_data.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    logger.info(f"  创建测试数据文件: {test_file}")

    # 构建图谱
    await builder.build_graph_from_data(test_file)

    # 获取统计
    stats = builder.get_statistics()
    logger.info("\n  构建统计:")
    logger.info(f"    创建顶点: {stats['vertices_created']}")
    logger.info(f"    创建边: {stats['edges_created']}")
    logger.info(f"    处理文档: {stats['documents_processed']}")
    logger.info(f"    处理实体: {stats['entities_processed']}")
    logger.info(f"    处理关系: {stats['relations_processed']}")
    logger.info(f"    错误数: {len(stats['errors'])}")

    # 验证结果
    success = (
        stats['vertices_created'] >= 5 and  # 至少5个顶点
        stats['edges_created'] >= 2 and      # 至少2条边
        stats['documents_processed'] >= 1     # 至少1个文档
    )

    logger.info(f"\n验证结果: {'✅ 成功' if success else '❌ 失败'}")
    return success

async def test_2025_modification_subgraph():
    """测试2025年修改子图"""
    logger.info("\n" + "="*60)
    logger.info("测试5: 2025年修改子图")
    logger.info("="*60)

    from patent_rules_system.nebula_graph_builder import NebulaGraphBuilder

    builder = NebulaGraphBuilder()

    # 创建包含2025修改的顶点和边
    await builder._save_vertex_to_file({
        "vertex_id": "mod_2025_1",
        "type": "Modification2025",
        "properties": {
            "change_type": "amended",
            "application_date": "2026-01-01"
        }
    })

    await builder._save_edge_to_file({
        "edge_id": "mod_rel_1",
        "type": "INTRODUCED_IN",
        "src": "mod_2025_1",
        "dst": "ai_section_1",
        "properties": {
            "date": "2025-06-01"
        }
    })

    # 构建子图
    await builder.build_2025_modification_subgraph()

    # 验证子图文件
    subgraph_file = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/knowledge_graph/modification_2025_subgraph.json")
    if subgraph_file.exists():
        with open(subgraph_file, encoding='utf-8') as f:
            subgraph = json.load(f)
            logger.info(f"  ✅ 子图文件: {subgraph_file}")
            logger.info(f"     子图名称: {subgraph.get('name')}")
            logger.info(f"     顶点数: {subgraph.get('statistics', {}).get('vertices_count', 0)}")
            logger.info(f"     边数: {subgraph.get('statistics', {}).get('edges_count', 0)}")
            logger.info(f"     创建时间: {subgraph.get('created_at')}")

            success = subgraph.get('vertices_count', 0) > 0
            logger.info(f"验证结果: {'✅ 成功' if success else '❌ 失败'}")
            return success
    else:
        logger.error("  ❌ 子图文件未创建")
        return False

async def test_id_generation():
    """测试ID生成"""
    logger.info("\n" + "="*60)
    logger.info("测试6: ID生成")
    logger.info("="*60)

    from patent_rules_system.nebula_graph_builder import NebulaGraphBuilder

    builder = NebulaGraphBuilder()

    # 测试不同对象的ID生成
    test_objects = [
        {"title": "专利法"},
        {"content": "第一条内容"},
        {"relation": "引用关系"},
        {"metadata": {"version": "2023", "type": "PDF"}}
    ]

    ids = []
    for obj in test_objects:
        id1 = builder._generate_id(obj)
        id2 = builder._generate_id(obj)

        # 相同对象应该生成相同ID
        is_consistent = id1 == id2
        ids.append(id1)

        logger.info(f"  对象: {str(obj)[:30]}...")
        logger.info(f"    ID1: {id1}")
        logger.info(f"    ID2: {id2}")
        logger.info(f"    一致性: {'✅' if is_consistent else '❌'}")

    # 检查ID唯一性
    unique_ids = set(ids)
    all_unique = len(unique_ids) == len(ids)

    logger.info(f"\nID唯一性: {'✅ 唯一' if all_unique else '❌ 重复'}")

    return all_unique

async def test_classification():
    """测试分类功能"""
    logger.info("\n" + "="*60)
    logger.info("测试7: 分类功能")
    logger.info("="*60)

    from patent_rules_system.nebula_graph_builder import (
        GraphEntityType,
        NebulaGraphBuilder,
    )

    builder = NebulaGraphBuilder()

    # 测试章节分类
    test_sections = [
        {"section_id": "A1", "title": "第一条"},
        {"section_id": "P1-C1", "title": "第一章 第一节"},
        {"section_id": "interpret_1", "title": "最高人民法院司法解释"},
        {"section_id": "mod_2025", "title": "2025年修订"}
    ]

    logger.info("章节分类测试:")
    section_results = []
    for section in test_sections:
        entity_type = builder._classify_section(section)
        logger.info(f"  {section['section_id']} -> {entity_type.value}")
        section_results.append(entity_type)

    # 验证分类结果
    has_article = GraphEntityType.LAW_ARTICLE in section_results
    has_modification = GraphEntityType.MODIFICATION_2025 in section_results

    # 测试实体分类
    test_entities = [
        {"entity_type": "专利权"},
        {"entity_type": "概念"},
        {"entity_type": "2025年修改"},
        {"entity_type": "未定义"}
    ]

    logger.info("\n实体分类测试:")
    entity_results = []
    for entity in test_entities:
        entity_type = builder._classify_entity(entity)
        logger.info(f"  {entity['entity_type']} -> {entity_type.value}")
        entity_results.append(entity_type)

    # 测试关系分类
    test_relations = [
        {"relation_type": "包含"},
        {"relation_type": "引用"},
        {"relation_type": "2025年引入"},
        {"relation_type": "相关于"}
    ]

    logger.info("\n关系分类测试:")
    relation_results = []
    for relation in test_relations:
        relation_type = builder._classify_relation(relation)
        logger.info(f"  {relation['relation_type']} -> {relation_type.value}")
        relation_results.append(relation_type)

    # 验证结果
    success = (
        has_article and
        has_modification and
        len(set(section_results)) >= 3 and
        len(set(entity_results)) >= 3 and
        len(set(relation_results)) >= 3
    )

    logger.info(f"\n分类验证结果: {'✅ 成功' if success else '❌ 失败'}")
    return success

async def test_statistics():
    """测试统计功能"""
    logger.info("\n" + "="*60)
    logger.info("测试8: 统计功能")
    logger.info("="*60)

    from patent_rules_system.nebula_graph_builder import NebulaGraphBuilder

    builder = NebulaGraphBuilder()

    # 模拟一些构建操作
    builder.stats = {
        "vertices_created": 150,
        "edges_created": 75,
        "documents_processed": 10,
        "entities_processed": 300,
        "relations_processed": 50,
        "errors": []
    }

    stats = builder.get_statistics()
    logger.info("统计信息:")
    logger.info(f"  创建顶点: {stats['vertices_created']}")
    logger.info(f"  创建边: {stats['edges_created']}")
    logger.info(f"  处理文档: {stats['documents_processed']}")
    logger.info(f"  处理实体: {stats['entities_processed']}")
    logger.info(f"  处理关系: {stats['relations_processed']}")
    logger.info(f"  错误数: {len(stats['errors'])}")

    # 验证统计完整性
    expected_keys = [
        "vertices_created", "edges_created", "documents_processed",
        "entities_processed", "relations_processed", "errors"
    ]

    has_all_keys = all(key in stats for key in expected_keys)
    all_positive = all(stats[key] >= 0 for key in expected_keys)

    success = has_all_keys and all_positive
    logger.info(f"\n统计验证: {'✅ 成功' if success else '❌ 失败'}")
    return success

async def main():
    """主测试函数"""
    logger.info("\n" + "="*80)
    logger.info("NebulaGraph知识图谱构建器测试")
    logger.info("="*80)

    # 执行测试
    tests = [
        ("空间初始化", test_space_initialization),
        ("顶点创建", test_vertex_creation),
        ("边创建", test_edge_creation),
        ("从数据构建图谱", test_graph_building_from_data),
        ("2025修改子图", test_2025_modification_subgraph),
        ("ID生成", test_id_generation),
        ("分类功能", test_classification),
        ("统计功能", test_statistics)
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
    report_file = Path("/Users/xujian/Athena工作平台/production/logs/nebula_graph_builder_test_report.json")
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
        logger.info("\n🎉 所有测试通过！NebulaGraph知识图谱构建器功能正常。")
    else:
        logger.warning("\n⚠️ 部分测试失败，请检查日志。")

    exit(0 if success else 1)
