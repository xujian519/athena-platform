#!/usr/bin/env python3
"""
测试法律法规数据处理器
Test Legal Data Processor

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

async def test_document_type_identification():
    """测试文档类型识别"""
    logger.info("="*60)
    logger.info("测试1: 文档类型识别")
    logger.info("="*60)

    from patent_rules_system.legal_data_processor import LegalDataProcessor, LegalDocType

    processor = LegalDataProcessor()

    # 测试用例
    test_cases = [
        ("专利法2023年版.docx", LegalDocType.PATENT_LAW),
        ("专利法实施细则.doc", LegalDocType.IMPLEMENTATION_RULES),
        ("最高人民法院司法解释.pdf", LegalDocType.JUDICIAL_INTERPRETATION),
        ("专利审查指南.docx", LegalDocType.GUIDELINE),
        ("专利案例笔记.txt", LegalDocType.CASE_NOTE),
        ("unknown_document.docx", LegalDocType.OTHER)
    ]

    passed = 0
    for filename, expected_type in test_cases:
        result = processor.identify_document_type(filename)
        status = "✅" if result == expected_type else "❌"
        logger.info(f"  {status} {filename} -> {result.value}")
        if result == expected_type:
            passed += 1

    logger.info(f"\n结果: {passed}/{len(test_cases)} 个测试通过")
    return passed == len(test_cases)

async def test_article_extraction():
    """测试法条提取"""
    logger.info("\n" + "="*60)
    logger.info("测试2: 法条提取")
    logger.info("="*60)

    from patent_rules_system.legal_data_processor import LegalDataProcessor

    processor = LegalDataProcessor()

    # 测试文本
    test_content = """
    中华人民共和国专利法

    第一条 为了保护专利权人的合法权益，鼓励发明创造，推动发明创造的应用，
    提高创新能力，促进科学技术进步和经济社会发展，制定本法。

    第二条 本法所称的发明创造是指发明、实用新型和外观设计。

    第三条 国务院专利行政部门负责管理全国的专利工作；
    统一受理和审查专利申请，依法授予专利权。

    Article 4 本法修改涉及AI相关发明创造的特殊规定。
    """

    articles = processor.extract_articles(test_content)

    logger.info(f"  提取到 {len(articles)} 条法条:")

    passed = 0
    expected_articles = ["第一条", "第二条", "第三条", "Article 4"]

    for article in articles:
        logger.info(f"    - {article['article_id']}: {article['content'][:50]}...")
        if article['article_id'] in expected_articles:
            passed += 1

    # 检查2025年修改标记
    has_modification = any(article.get('has_2025_modification') for article in articles)
    logger.info(f"  检测到2025年修改: {'是' if has_modification else '否'}")

    return len(articles) >= 3  # 至少应该提取到3条中文法条

async def test_chapter_extraction():
    """测试章节提取"""
    logger.info("\n" + "="*60)
    logger.info("测试3: 章节提取")
    logger.info("="*60)

    from patent_rules_system.legal_data_processor import LegalDataProcessor

    processor = LegalDataProcessor()

    # 测试文本
    test_content = """
    专利审查指南

    第一章 总则
    本部分规定了专利审查的基本原则和程序要求。

    第二章 申请文件的审查
    包括发明专利申请的初步审查和实质审查。

    第三章 授权与公告
    专利权的授予和公告程序。

    Chapter Four Special Provisions
    AI相关发明的特殊审查程序。

    第五章 附则
    本指南的实施日期。
    """

    chapters = processor.extract_chapters(test_content)

    logger.info(f"  提取到 {len(chapters)} 个章节:")

    for chapter in chapters:
        logger.info(f"    - {chapter['chapter_id']}: {chapter['title']}")

    return len(chapters) >= 3  # 至少应该提取到3个章节

async def test_modification_detection():
    """测试2025年修改检测"""
    logger.info("\n" + "="*60)
    logger.info("测试4: 2025年修改检测")
    logger.info("="*60)

    from patent_rules_system.legal_data_processor import LegalDataProcessor

    processor = LegalDataProcessor()

    # 测试文本
    test_content = """
    本条款于2025年进行了修改，新增了AI相关发明的审查标准。
    特别是在人工智能和大数据领域，创造性判断标准有所调整。
    基因编辑技术和比特流保护也在此次修改中有所涉及。
    """

    # 测试关键词检查
    has_modification = processor.check_2025_modification(test_content)
    logger.info(f"  关键词检测: {'✅ 检测到' if has_modification else '❌ 未检测到'}")

    # 测试详细修改检测
    modifications = processor.find_2025_modifications(test_content)

    logger.info("  详细检测结果:")
    logger.info(f"    有修改: {modifications['has_modifications']}")
    logger.info(f"    找到关键词: {modifications['keywords_found']}")
    logger.info(f"    相关段落数: {len(modifications['relevant_sections'])}")

    if modifications['relevant_sections']:
        logger.info("  相关段落预览:")
        for i, section in enumerate(modifications['relevant_sections'][:2]):
            logger.info(f"    {i+1}. {section[:50]}...")

    return modifications['has_modifications'] and len(modifications['keywords_found']) > 0

async def test_document_processing():
    """测试文档处理（模拟）"""
    logger.info("\n" + "="*60)
    logger.info("测试5: 文档处理流程（模拟）")
    logger.info("="*60)

    from patent_rules_system.legal_data_processor import (
        LegalDataProcessor,
        LegalDocType,
        LegalDocument,
    )

    processor = LegalDataProcessor()

    # 创建模拟文档
    mock_content = """
    中华人民共和国专利法（示例）

    为了保护专利权人的合法权益，鼓励发明创造，特制定本法。

    第一章 总则
    第一条 本法所称发明创造是指发明、实用新型和外观设计。
    第二条 国务院专利行政部门负责管理全国的专利工作。

    第二章 专利申请
    第三条 申请专利的发明创造，应当符合新颖性、创造性和实用性的要求。
    第四条 2025年修改：AI相关发明创造的特殊审查标准另行规定。
    """

    # 模拟处理
    logger.info("  1. 创建文档对象...")
    legal_doc = LegalDocument()
    legal_doc.doc_id = processor.generate_doc_id(Path("专利法示例.docx"))
    legal_doc.doc_type = LegalDocType.PATENT_LAW
    legal_doc.title = "中华人民共和国专利法（示例）"
    legal_doc.content = mock_content

    # 提取信息
    logger.info("  2. 提取文档信息...")
    doc_info = processor.extract_document_info(mock_content, LegalDocType.PATENT_LAW)
    legal_doc.version = doc_info.get("version", "示例版")

    # 提取法条和章节
    logger.info("  3. 提取法条和章节...")
    legal_doc.articles = processor.extract_articles(mock_content)
    legal_doc.chapters = processor.extract_chapters(mock_content)

    # 检查修改
    logger.info("  4. 检查2025年修改...")
    legal_doc.modifications_2025 = processor.find_2025_modifications(mock_content)

    # 提取关键词
    logger.info("  5. 提取关键词...")
    legal_doc.keywords = processor.extract_keywords(mock_content, LegalDocType.PATENT_LAW)

    # 设置元数据
    legal_doc.metadata = {
        "processed_at": datetime.now().isoformat(),
        "word_count": len(mock_content),
        "articles_count": len(legal_doc.articles),
        "chapters_count": len(legal_doc.chapters)
    }

    # 验证结果
    logger.info("  处理结果:")
    logger.info(f"    文档ID: {legal_doc.doc_id}")
    logger.info(f"    文档类型: {legal_doc.doc_type.value}")
    logger.info(f"    法条数: {len(legal_doc.articles)}")
    logger.info(f"    章节数: {len(legal_doc.chapters)}")
    logger.info(f"    2025修改: {legal_doc.modifications_2025['has_modifications']}")
    logger.info(f"    关键词数: {len(legal_doc.keywords)}")

    # 保存测试结果
    output_dir = Path("/Users/xujian/Athena工作平台/production/data/patent_rules/legal_documents")
    output_dir.mkdir(parents=True, exist_ok=True)

    test_file = output_dir / "test_legal_document.json"
    doc_dict = {
        "doc_id": legal_doc.doc_id,
        "doc_type": legal_doc.doc_type.value,
        "title": legal_doc.title,
        "version": legal_doc.version,
        "articles": legal_doc.articles,
        "chapters": legal_doc.chapters,
        "modifications_2025": legal_doc.modifications_2025,
        "keywords": legal_doc.keywords,
        "metadata": legal_doc.metadata
    }

    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(doc_dict, f, ensure_ascii=False, indent=2)

    logger.info(f"  ✅ 测试文档已保存: {test_file}")

    # 验证结果
    success = (
        len(legal_doc.articles) >= 2 and
        len(legal_doc.chapters) >= 1 and
        len(legal_doc.keywords) >= 5 and
        legal_doc.modifications_2025['has_modifications']
    )

    return success

async def test_integration():
    """测试集成功能"""
    logger.info("\n" + "="*60)
    logger.info("测试6: 集成功能")
    logger.info("="*60)

    from patent_rules_system.legal_data_processor import LegalDataProcessor

    # 初始化处理器
    processor = LegalDataProcessor()

    # 检查目录结构
    logger.info("  检查目录结构:")
    directories = [
        processor.legal_dir,
        processor.laws_dir,
        processor.rules_dir,
        processor.interpretations_dir,
        processor.notes_dir
    ]

    all_dirs_exist = True
    for dir_path in directories:
        exists = dir_path.exists()
        status = "✅" if exists else "❌"
        logger.info(f"    {status} {dir_path.name}")
        if not exists:
            all_dirs_exist = False

    # 测试数据源目录
    source_exists = processor.source_dir.exists()
    logger.info(f"  数据源目录: {'✅' if source_exists else '❌'} {processor.source_dir}")

    if source_exists:
        # 查找文档
        doc_files = []
        for ext in ["*.docx", "*.doc", "*.txt", "*.rtf"]:
            doc_files.extend(processor.source_dir.glob(ext))

        logger.info(f"  找到文档: {len(doc_files)} 个")

        if doc_files:
            # 显示文件列表
            logger.info("  文档列表:")
            for file_path in doc_files[:5]:  # 只显示前5个
                logger.info(f"    - {file_path.name}")
            if len(doc_files) > 5:
                logger.info(f"    ... 还有 {len(doc_files) - 5} 个文件")

    # 测试统计功能
    logger.info("\n  测试统计功能:")
    processor.stats = {
        "documents_processed": 10,
        "articles_extracted": 50,
        "chapters_extracted": 15,
        "modifications_found": 3,
        "doc_types_count": {
            "专利法": 2,
            "实施细则": 3,
            "司法解释": 4,
            "其他": 1
        }
    }

    processor.print_summary()

    return all_dirs_exist and source_exists

async def main():
    """主测试函数"""
    logger.info("\n" + "="*80)
    logger.info("法律法规数据处理器测试")
    logger.info("="*80)

    # 执行测试
    tests = [
        ("文档类型识别", test_document_type_identification),
        ("法条提取", test_article_extraction),
        ("章节提取", test_chapter_extraction),
        ("2025修改检测", test_modification_detection),
        ("文档处理流程", test_document_processing),
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
    report_file = Path("/Users/xujian/Athena工作平台/production/logs/legal_data_processor_test_report.json")
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
        logger.info("\n🎉 所有测试通过！法律法规数据处理器功能正常。")
    else:
        logger.warning("\n⚠️ 部分测试失败，请检查日志。")

    exit(0 if success else 1)
