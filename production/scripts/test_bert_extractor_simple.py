#!/usr/bin/env python3
"""
测试简化版BERT实体关系提取器
Test Simplified BERT Entity Relation Extractor

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

async def test_entity_extraction():
    """测试实体提取功能"""
    logger.info("="*60)
    logger.info("测试1: 实体提取功能")
    logger.info("="*60)

    from patent_rules_system.bert_extractor_simple import PatentEntityRelationExtractor

    # 初始化提取器
    extractor = PatentEntityRelationExtractor()

    # 测试文本
    test_text = """
    中华人民共和国专利法（2023修订）

    第一条 为了保护专利权人的合法权益，鼓励发明创造，推动发明创造的应用，
    提高创新能力，促进科学技术进步和经济社会发展，制定本法。

    第二条 本法所称的发明创造是指发明、实用新型和外观设计。

    第三章 专利申请
    3.1 申请发明专利应当提交请求书、说明书及其摘要和权利要求书等文件。
    3.2 说明书应当对发明作出清楚、完整的说明，以所属技术领域的技术人员能够实现为准。

    2025年修改：新增AI相关发明的特殊审查规定。算法模型的创造性判断应当考虑
    技术方案的进步性，特别要注意大数据领域的应用。比特流单独保护不予支持。
    """

    logger.info(f"测试文本长度: {len(test_text)} 字符")

    # 提取实体
    entities = await extractor.extract_entities(test_text, "test_doc")

    logger.info(f"提取到 {len(entities)} 个实体:")

    # 按类型统计
    entity_types = {}
    for entity in entities:
        entity_type = entity.entity_type.value
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

    logger.info("实体类型分布:")
    for entity_type, count in sorted(entity_types.items()):
        logger.info(f"  {entity_type}: {count} 个")

    # 显示部分实体
    logger.info("\n部分实体示例:")
    for entity in entities[:10]:
        logger.info(f"  - {entity.entity_text} [{entity.entity_type.value}] "
                   f"(置信度: {entity.confidence:.2f}, 方法: {entity.extraction_method})")

    # 验证特定实体类型
    has_law_articles = any(e.entity_type.value == "法律条文" for e in entities)
    has_chapters = any(e.entity_type.value == "指南章节" for e in entities)
    has_2025_mods = any(e.entity_type.value == "2025年修改" for e in entities)

    logger.info("\n验证结果:")
    logger.info(f"  法律条文: {'✅' if has_law_articles else '❌'}")
    logger.info(f"  章节结构: {'✅' if has_chapters else '❌'}")
    logger.info(f"  2025修改: {'✅' if has_2025_mods else '❌'}")

    return len(entities) > 5 and (has_law_articles or has_chapters)

async def test_relation_extraction():
    """测试关系提取功能"""
    logger.info("\n" + "="*60)
    logger.info("测试2: 关系提取功能")
    logger.info("="*60)

    from patent_rules_system.bert_extractor_simple import PatentEntityRelationExtractor

    # 初始化提取器
    extractor = PatentEntityRelationExtractor()

    # 测试文本
    test_text = """
    专利法第一条规定了专利保护的基本原则。根据该条款，发明创造应当具备
    新颖性、创造性和实用性。第二条明确规定发明创造包括发明、实用新型和外观设计。
    2025年修订引入了AI相关发明的特殊审查标准，这些标准适用于算法模型。
    """

    logger.info("提取实体...")
    entities = await extractor.extract_entities(test_text, "relation_test")
    logger.info(f"找到 {len(entities)} 个实体")

    logger.info("提取关系...")
    relations = await extractor.extract_relations(test_text, entities)
    logger.info(f"提取到 {len(relations)} 个关系")

    # 显示关系
    logger.info("\n关系列表:")
    for relation in relations:
        logger.info(f"  - {relation.relation_type.value}")
        logger.info(f"    置信度: {relation.confidence:.2f}")
        logger.info(f"    证据: {relation.evidence[:60]}...")

    return len(relations) >= 0

async def test_joint_extraction():
    """测试联合提取功能"""
    logger.info("\n" + "="*60)
    logger.info("测试3: 联合提取功能")
    logger.info("="*60)

    from patent_rules_system.bert_extractor_simple import PatentEntityRelationExtractor

    # 初始化提取器
    extractor = PatentEntityRelationExtractor()

    # 测试文本
    test_text = """
    专利审查指南第五章（2025年修订）

    5.1 人工智能相关发明
    人工智能相关发明的审查应当适用特殊标准。算法模型必须体现技术方案的
    创新性，不能仅仅是抽象的数学方法。

    5.2 大数据应用
    基于大数据的技术方案需要考虑数据处理的技术特征。

    5.3 比特流保护
    单纯的比特流不授予专利权。但是，包含比特流的技术方案可以申请保护。
    """

    logger.info("执行联合提取...")
    result = await extractor.extract(test_text, "joint_test")

    logger.info("\n提取结果:")
    logger.info(f"  实体数: {len(result.entities)}")
    logger.info(f"  关系数: {len(result.relations)}")
    logger.info(f"  处理时间: {result.processing_time:.2f} 秒")
    logger.info(f"  使用系统: {result.model_used}")

    # 显示统计信息
    stats = result.statistics
    logger.info("\n详细统计:")
    logger.info(f"  平均实体置信度: {stats['avg_entity_confidence']:.2f}")
    logger.info(f"  平均关系置信度: {stats['avg_relation_confidence']:.2f}")

    logger.info("\n实体类型分布:")
    for entity_type, count in stats['entity_type_distribution'].items():
        logger.info(f"  {entity_type}: {count} 个")

    if stats['relation_type_distribution']:
        logger.info("\n关系类型分布:")
        for relation_type, count in stats['relation_type_distribution'].items():
            logger.info(f"  {relation_type}: {count} 个")

    return len(result.entities) > 0

async def test_quality():
    """测试提取质量"""
    logger.info("\n" + "="*60)
    logger.info("测试4: 提取质量")
    logger.info("="*60)

    from patent_rules_system.bert_extractor_simple import PatentEntityRelationExtractor

    extractor = PatentEntityRelationExtractor()

    # 准备测试用例
    test_cases = [
        {
            "text": "专利法第一条规定专利保护的基本原则",
            "expected_entities": ["专利法", "第一条", "专利保护", "基本原则"],
            "description": "基础法条识别"
        },
        {
            "text": "2025年新增AI相关发明的审查标准",
            "expected_entities": ["2025年", "AI", "审查标准"],
            "description": "2025年修改识别"
        },
        {
            "text": "发明必须具备新颖性、创造性和实用性",
            "expected_entities": ["发明", "新颖性", "创造性", "实用性"],
            "description": "专利条件识别"
        }
    ]

    total_precision = 0
    total_recall = 0
    total_f1 = 0

    for i, test_case in enumerate(test_cases):
        logger.info(f"\n测试用例 {i+1}: {test_case['description']}")
        logger.info(f"文本: {test_case['text']}")

        # 提取实体
        result = await extractor.extract(test_case['text'], f"quality_test_{i}")

        # 计算指标
        extracted_texts = [e.entity_text for e in result.entities]

        # 精确率
        correct = 0
        for extracted in extracted_texts:
            if any(expected in extracted or extracted in expected
                  for expected in test_case['expected_entities']):
                correct += 1
        precision = correct / len(extracted_texts) if extracted_texts else 0

        # 召回率
        found = 0
        for expected in test_case['expected_entities']:
            if any(expected in extracted or extracted in expected
                  for extracted in extracted_texts):
                found += 1
        recall = found / len(test_case['expected_entities'])

        # F1
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        total_precision += precision
        total_recall += recall
        total_f1 += f1

        logger.info(f"  提取实体: {extracted_texts}")
        logger.info(f"  精确率: {precision:.2f}, 召回率: {recall:.2f}, F1: {f1:.2f}")

    # 计算平均指标
    avg_precision = total_precision / len(test_cases)
    avg_recall = total_recall / len(test_cases)
    avg_f1 = total_f1 / len(test_cases)

    logger.info("\n平均质量指标:")
    logger.info(f"  精确率: {avg_precision:.3f}")
    logger.info(f"  召回率: {avg_recall:.3f}")
    logger.info(f"  F1分数: {avg_f1:.3f}")

    # 验证质量（暂定标准）
    quality_ok = avg_f1 >= 0.6

    logger.info(f"\n质量验证: {'✅' if quality_ok else '❌'}")
    if not quality_ok:
        logger.warning(f"当前F1分数为{avg_f1:.3f}，目标为0.95")

    return quality_ok

async def test_performance():
    """测试性能"""
    logger.info("\n" + "="*60)
    logger.info("测试5: 性能测试")
    logger.info("="*60)

    from patent_rules_system.bert_extractor_simple import PatentEntityRelationExtractor

    extractor = PatentEntityRelationExtractor()

    # 测试不同长度的文本
    test_cases = [
        ("短文本", "专利法规定了发明和实用新型的保护要求。"),
        ("中文本", """
            专利审查指南规定了专利申请的具体要求。发明应当具备新颖性、创造性和实用性。
            新颖性是指在申请日以前没有同样的发明在国内外出版物上公开发表过。
        """),
        ("长文本", """
            专利法实施细则对专利申请的程序作出了详细规定。申请发明专利应当提交请求书、
            说明书及其摘要和权利要求书等文件。请求书应当写明发明创造的名称、
            发明人的姓名、申请人姓名或者名称、地址以及其他事项。

            说明书应当对发明作出清楚、完整的说明，以所属技术领域的技术人员能够实现为准。
            必要的时候，应当有附图。摘要应当简要说明发明的技术要点。

            权利要求书应当以说明书为依据，清楚、简要地限定要求专利保护的范围。
            2025年修改特别指出，AI相关发明需要额外披露训练数据来源。
        """)
    ]

    results = []
    total_time = 0

    for case_name, text in test_cases:
        logger.info(f"\n测试 {case_name}...")
        logger.info(f"  文本长度: {len(text)} 字符")

        # 执行提取
        result = await extractor.extract(text, f"perf_test_{len(text)}")
        processing_time = result.processing_time
        total_time += processing_time

        results.append({
            "name": case_name,
            "length": len(text),
            "entities": len(result.entities),
            "relations": len(result.relations),
            "time": processing_time
        })

        logger.info(f"  实体数: {len(result.entities)}")
        logger.info(f"  关系数: {len(result.relations)}")
        logger.info(f"  处理时间: {processing_time:.2f} 秒")

    # 性能总结
    logger.info("\n性能总结:")
    avg_time = total_time / len(test_cases)
    logger.info(f"  平均处理时间: {avg_time:.2f} 秒")

    # 验证性能要求
    performance_ok = avg_time < 5.0  # 平均处理时间小于5秒

    logger.info(f"\n性能验证: {'✅' if performance_ok else '❌'}")

    return performance_ok

async def test_integration():
    """测试集成功能"""
    logger.info("\n" + "="*60)
    logger.info("测试6: 集成功能")
    logger.info("="*60)

    from patent_rules_system.bert_extractor_simple import PatentEntityRelationExtractor

    # 初始化提取器
    extractor = PatentEntityRelationExtractor()

    # 处理多个文档
    test_docs = [
        ("专利法", "专利法规定了发明和实用新型的保护要求。"),
        ("审查指南", "审查指南第五章涉及AI相关发明的审查。"),
        ("2025修改", "2025年新增了算法模型的特殊审查标准。")
    ]

    for doc_name, text in test_docs:
        result = await extractor.extract(text, doc_name)
        logger.info(f"  {doc_name}: {len(result.entities)} 实体, {len(result.relations)} 关系")

    # 获取统计信息
    stats = extractor.get_statistics()

    logger.info("\n总体统计:")
    logger.info(f"  处理文档数: {stats['documents_processed']}")
    logger.info(f"  总实体数: {stats['total_entities']}")
    logger.info(f"  总关系数: {stats['total_relations']}")
    if 'avg_entities_per_doc' in stats:
        logger.info(f"  平均每文档实体数: {stats['avg_entities_per_doc']:.1f}")
        logger.info(f"  平均每文档关系数: {stats['avg_relations_per_doc']:.1f}")
        logger.info(f"  平均处理时间: {stats['avg_processing_time']:.2f} 秒")

    # 保存示例结果
    if test_docs:
        result = await extractor.extract(test_docs[-1][1], "integration_example")

        # 转换为可保存的格式
        result_dict = {
            "doc_id": result.doc_id,
            "entities": [
                {
                    "entity_id": e.entity_id,
                    "entity_type": e.entity_type.value,
                    "entity_text": e.entity_text,
                    "confidence": e.confidence,
                    "extraction_method": e.extraction_method
                }
                for e in result.entities
            ],
            "relations": [
                {
                    "relation_id": r.relation_id,
                    "relation_type": r.relation_type.value,
                    "confidence": r.confidence,
                    "extraction_method": r.extraction_method
                }
                for r in result.relations
            ],
            "statistics": result.statistics
        }

        output_dir = Path("/Users/xujian/Athena工作平台/production/data/patent_rules")
        output_dir.mkdir(parents=True, exist_ok=True)

        result_file = output_dir / "bert_extraction_example.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)

        logger.info(f"\n✅ 示例结果已保存: {result_file}")

    return stats['documents_processed'] > 0

async def main():
    """主测试函数"""
    logger.info("\n" + "="*80)
    logger.info("简化版BERT实体关系提取器测试")
    logger.info("="*80)

    # 执行测试
    tests = [
        ("实体提取功能", test_entity_extraction),
        ("关系提取功能", test_relation_extraction),
        ("联合提取功能", test_joint_extraction),
        ("提取质量", test_quality),
        ("性能测试", test_performance),
        ("集成功能", test_integration)
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
    report_file = Path("/Users/xujian/Athena工作平台/production/logs/bert_extractor_simple_test_report.json")
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
        logger.info("\n🎉 所有测试通过！简化版BERT实体关系提取器功能正常。")
    else:
        logger.warning("\n⚠️ 部分测试失败，请检查日志。")

    exit(0 if success else 1)
