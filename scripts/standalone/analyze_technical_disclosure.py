#!/usr/bin/env python3
"""
技术交底书发明专利申请可行性分析工具

使用Athena平台的深度技术分析能力，对技术交底书进行全面分析，
评估其发明专利申请的可行性。

作者: Athena AI研究员
创建时间: 2026-03-13
"""

import asyncio
import logging
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, "/Users/xujian/Athena工作平台")

from core.patents.xiaona_deep_technical_analyzer import XiaonaDeepTechnicalAnalyzer


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("analysis.log", encoding="utf-8")
        ]
    )
    return logging.getLogger(__name__)


def extract_word_document_content(file_path: str) -> str:
    """从Word文档中提取文本内容"""
    logger = logging.getLogger(__name__)

    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text.strip())
        content = "\n".join(paragraphs)
        logger.info(f"成功提取文档内容，共 {len(content)} 字符")
        return content
    except Exception as e:
        logger.error(f"提取Word文档内容失败: {e}")
        raise


async def analyze_technical_disclosure(file_path: str):
    """分析技术交底书的发明专利申请可行性"""
    logger = setup_logging()

    logger.info("=" * 80)
    logger.info("技术交底书发明专利申请可行性分析")
    logger.info("=" * 80)

    # 1. 提取文档内容
    logger.info("步骤1: 提取技术交底书内容")
    try:
        content = extract_word_document_content(file_path)
    except Exception as e:
        logger.error(f"文档提取失败: {e}")
        return

    # 2. 使用小娜深度技术分析器
    logger.info("步骤2: 使用小娜深度技术分析器")

    # 创建分析器实例
    analyzer = XiaonaDeepTechnicalAnalyzer(
        output_dir="data/analysis_reports",
        use_dolphin=True,
        enable_visualization=True
    )

    try:
        # 执行深度分析
        logger.info("开始深度技术分析...")

        # 分析技术交底书（将其视为单个专利进行分析）
        analysis_result = await analyzer._analyze_single_patent(
            patent_number="TEMP001",
            patent_title="一种自修复模拟骨髓腔输液技术训练模型",
            patent_type="技术交底书",
            patent_text=content
        )

        logger.info("=" * 80)
        logger.info("分析完成 - 详细结果")
        logger.info("=" * 80)

        # 输出关键分析结果
        logger.info(f"技术领域: {analysis_result.technical_field}")
        logger.info(f"技术问题: {analysis_result.technical_problem}")
        logger.info(f"技术方案: {analysis_result.technical_solution}")

        logger.info("\n--- 技术特征分析 ---")
        if analysis_result.technical_features:
            for i, feature in enumerate(analysis_result.technical_features, 1):
                logger.info(f"{i}. {feature.feature_name}")
                logger.info(f"   创新性: {feature.novelty_level}")
                logger.info(f"   重要性: {feature.importance:.1%}")

        logger.info("\n--- 权利要求分析 ---")
        logger.info(f"独立权利要求数量: {analysis_result.independent_claims}")
        logger.info(f"从属权利要求数量: {analysis_result.dependent_claims}")
        logger.info(f"总权利要求数量: {analysis_result.total_claims}")

        logger.info("\n--- 关键技术点 ---")
        for i, point in enumerate(analysis_result.key_technical_points, 1):
            logger.info(f"{i}. {point}")

        logger.info("\n--- 创新亮点 ---")
        for i, innovation in enumerate(analysis_result.innovation_highlights, 1):
            logger.info(f"{i}. {innovation}")

        logger.info(f"\n技术复杂度: {analysis_result.complexity_score:.1%}")
        logger.info(f"分析置信度: {analysis_result.analysis_confidence:.1%}")

        # 保存分析报告
        report_path = analyzer.output_dir / f"analysis_report_{analysis_result.patent_number}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(analysis_result.to_markdown())
        logger.info(f"分析报告已保存到: {report_path}")

        return analysis_result

    except Exception as e:
        logger.error(f"分析过程失败: {e}")
        import traceback
        logger.error(f"错误详情:\n{traceback.format_exc()}")
        raise


def main():
    """主函数"""
    # 使用转换后的.docx文件
    file_path = "/Users/xujian/Athena工作平台/temp_converted.docx"

    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        return

    print(f"正在分析技术交底书: {file_path}")
    print("=" * 80)

    try:
        # 运行异步分析
        result = asyncio.run(analyze_technical_disclosure(file_path))

        if result:
            print("\n✅ 分析完成!")
            print(f"📄 技术领域: {result.technical_field}")
            print(f"🎯 技术问题: {result.technical_problem}")

            print("\n📋 权利要求分析:")
            print(f"   独立权利要求: {result.independent_claims}")
            print(f"   从属权利要求: {result.dependent_claims}")
            print(f"   总权利要求数: {result.total_claims}")

            if result.innovation_highlights:
                print(f"\n💡 创新亮点 ({len(result.innovation_highlights)}条):")
                for i, innovation in enumerate(result.innovation_highlights, 1):
                    print(f"   {i}. {innovation}")

            if result.key_technical_points:
                print(f"\n🔧 关键技术点 ({len(result.key_technical_points)}条):")
                for i, point in enumerate(result.key_technical_points, 1):
                    print(f"   {i}. {point}")

            print(f"\n📊 技术复杂度: {result.complexity_score:.1%}")
            print(f"🎯 分析置信度: {result.analysis_confidence:.1%}")

            report_path = f"data/analysis_reports/analysis_report_{result.patent_number}.md"
            print(f"\n📄 详细分析报告已保存到: {report_path}")

    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        print(f"错误详情:\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
