#!/usr/bin/env python3
"""
测试专利审查指南解析
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parsers.pdf_parser import PatentGuidelineParser


def main():
    """主函数"""
    pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '专利审查指南（最新版）.pdf')

    logger.info('开始解析专利审查指南...')

    # 创建解析器
    parser = PatentGuidelineParser(pdf_path)

    # 解析文档
    try:
        data = parser.parse()

        logger.info("\n✅ 解析成功!")
        logger.info(f"文档标题: {data['document_info']['title']}")
        logger.info(f"总页数: {data['document_info']['total_pages']}")
        logger.info(f"识别章节数: {data['document_info']['total_sections']}")
        logger.info(f"引用数量: {len(data['references'])}")

        # 保存结果
        import json
        output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'processed', 'test_parse_result.json')

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 结果已保存到: {output_path}")

        # 显示一些示例章节
        if data['structure']:
            logger.info("\n📚 章节 示例:")
            for i, section in enumerate(data['structure'][:5], 1):
                logger.info(f"\n{i}. [{section.get('type', 'UNKNOWN').upper()}]")
                logger.info(f"   ID: {section.get('id', 'N/A')}")
                logger.info(f"   编号: {section.get('number', 'N/A')}")
                logger.info(f"   级别: {section.get('level', 'N/A')}")
                logger.info(f"   标题: {section.get('title', '无标题')}")

                content = section.get('content', '')
                if content and len(content) > 100:
                    logger.info(f"   内容预览: {content[:100]}...")
                elif content:
                    logger.info(f"   完整内容: {content}")

        # 显示引用示例
        if data['references']:
            logger.info("\n🔗 引用 示例:")
            for i, ref in enumerate(data['references'][:5], 1):
                logger.info(f"\n{i}. 类型: {ref.get('type', 'UNKNOWN')}")
                logger.info(f"   上下文: {ref.get('context', 'N/A')}")

    except Exception as e:
        logger.info(f"\n❌ 解析失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
