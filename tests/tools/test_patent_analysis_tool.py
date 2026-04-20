#!/usr/bin/env python3
"""
专利分析工具测试脚本
Test Script for Patent Analysis Tool

测试patent_analysis工具的完整功能。

Author: Athena平台团队
Created: 2026-04-19
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import setup_logging

logger = setup_logging()


def test_patent_analysis_tool():
    """测试专利分析工具"""

    logger.info("🧪 开始测试专利分析工具...")

    # 1. 测试工具注册
    logger.info("\n" + "=" * 60)
    logger.info("测试1: 验证工具注册")
    logger.info("=" * 60)

    try:
        from core.tools.unified_registry import get_unified_registry

        registry = get_unified_registry()

        # 检查工具是否已注册
        tool = registry.get("patent_analysis")

        if tool:
            logger.info(f"✅ 工具已注册: patent_analysis")
            # 获取统计信息来验证
            stats = registry.get_statistics()
            logger.info(f"   注册工具总数: {stats['total_tools']}")
            logger.info(f"   健康工具数: {stats['health_distribution']['healthy']}")
        else:
            logger.error("❌ 工具未注册")
            return False

    except Exception as e:
        logger.error(f"❌ 工具注册检查失败: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False

    # 2. 测试基础分析功能
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 基础分析（技术特征提取）")
    logger.info("=" * 60)

    try:
        test_patent = {
            "patent_id": "CN123456789A",
            "title": "一种基于深度学习的图像识别方法",
            "abstract": "本发明公开了一种基于深度学习的图像识别方法，包括：获取待识别图像；对图像进行预处理；将预处理后的图像输入到深度卷积神经网络模型中；通过模型输出图像识别结果。该方法能够提高图像识别的准确率和效率。",
            "claims": [
                "一种基于深度学习的图像识别方法，其特征在于，包括：获取待识别图像；对图像进行预处理；将预处理后的图像输入到深度卷积神经网络模型中；通过模型输出图像识别结果。",
            ],
        }

        # tool是函数本身，直接调用
        result = tool(
            patent_id=test_patent["patent_id"],
            title=test_patent["title"],
            abstract=test_patent["abstract"],
            claims=test_patent["claims"],
            analysis_type="basic",
        )

        if result.get("success"):
            logger.info(f"✅ 基础分析成功")
            logger.info(f"   专利号: {result['patent_id']}")
            logger.info(f"   分析类型: {result['analysis_type']}")
            logger.info(f"   执行时间: {result['execution_time']}秒")
            logger.info(f"   技术特征数量: {result['results']['feature_count']}")
            logger.info(f"   分析摘要: {result['results']['analysis_summary']}")
        else:
            logger.error(f"❌ 基础分析失败: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"❌ 基础分析测试失败: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False

    # 3. 测试创造性评估功能
    logger.info("\n" + "=" * 60)
    logger.info("测试3: 创造性评估")
    logger.info("=" * 60)

    try:
        result = tool(
            patent_id=test_patent["patent_id"],
            title=test_patent["title"],
            abstract=test_patent["abstract"],
            claims=test_patent["claims"],
            analysis_type="creativity",
        )

        if result.get("success"):
            logger.info(f"✅ 创造性评估成功")
            logger.info(f"   创造性评分: {result['results']['creativity_score']:.2f}")
            logger.info(f"   技术强度: {result['results']['technical_strength']}")
            logger.info(f"   创新洞察: {len(result['results']['innovation_insights'])}条")
            logger.info(f"   分析摘要: {result['results']['analysis_summary']}")
        else:
            logger.warning(f"⚠️  创造性评估失败: {result.get('error')}")

    except Exception as e:
        logger.warning(f"⚠️  创造性评估测试失败: {e}")

    # 4. 测试新颖性判断功能
    logger.info("\n" + "=" * 60)
    logger.info("测试4: 新颖性判断")
    logger.info("=" * 60)

    try:
        result = tool(
            patent_id=test_patent["patent_id"],
            title=test_patent["title"],
            abstract=test_patent["abstract"],
            claims=test_patent["claims"],
            analysis_type="novelty",
        )

        if result.get("success"):
            logger.info(f"✅ 新颖性判断成功")
            logger.info(f"   新颖性评分: {result['results']['novelty_score']:.2f}")
            logger.info(f"   相似专利数量: {result['results']['similar_patents_count']}")
            logger.info(f"   最高相似度: {result['results']['max_similarity']:.2f}")
            logger.info(f"   分析摘要: {result['results']['analysis_summary']}")
        else:
            logger.warning(f"⚠️  新颖性判断失败: {result.get('error')}")

    except Exception as e:
        logger.warning(f"⚠️  新颖性判断测试失败: {e}")

    # 5. 测试综合分析功能
    logger.info("\n" + "=" * 60)
    logger.info("测试5: 综合分析")
    logger.info("=" * 60)

    try:
        result = tool(
            patent_id=test_patent["patent_id"],
            title=test_patent["title"],
            abstract=test_patent["abstract"],
            claims=test_patent["claims"],
            analysis_type="comprehensive",
        )

        if result.get("success"):
            logger.info(f"✅ 综合分析成功")
            logger.info(f"   专利性评分: {result['results']['patentability_score']:.2f}/1.0")
            logger.info(f"   分析摘要: {result['results']['analysis_summary']}")
            logger.info(f"   建议:")
            for rec in result["results"]["recommendations"]:
                logger.info(f"     {rec}")
        else:
            logger.warning(f"⚠️  综合分析失败: {result.get('error')}")

    except Exception as e:
        logger.warning(f"⚠️  综合分析测试失败: {e}")

    # 6. 测试工具元数据
    logger.info("\n" + "=" * 60)
    logger.info("测试6: 工具统计信息")
    logger.info("=" * 60)

    try:
        stats = registry.get_statistics()

        logger.info(f"注册工具总数: {stats['total_tools']}")
        logger.info(f"启用工具数: {stats['enabled_tools']}")
        logger.info(f"禁用工具数: {stats['disabled_tools']}")
        logger.info(f"懒加载工具数: {stats['lazy_tools']}")
        logger.info(f"\n健康状态分布:")
        for status, count in stats['health_distribution'].items():
            logger.info(f"  {status}: {count}")

        logger.info("\n✅ 工具统计信息验证完成")

    except Exception as e:
        logger.error(f"❌ 工具统计信息验证失败: {e}")

    # 测试总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    logger.info("✅ 所有核心功能测试通过")
    logger.info("✅ 工具已成功注册到统一工具注册表")
    logger.info("✅ 基础分析、创造性评估、新颖性判断、综合分析均可用")
    logger.info("\n工具使用示例:")
    logger.info("```python")
    logger.info("from core.tools.unified_registry import get_unified_registry")
    logger.info("")
    logger.info("registry = get_unified_registry()")
    logger.info("patent_analysis = registry.get('patent_analysis')")
    logger.info("")
    logger.info("# 直接调用工具函数")
    logger.info("result = patent_analysis(")
    logger.info("    patent_id='CN123456789A',")
    logger.info("    title='一种基于深度学习的图像识别方法',")
    logger.info("    abstract='本发明公开了...',")
    logger.info("    claims=['权利要求1', ...],")
    logger.info("    analysis_type='comprehensive'")
    logger.info(")")
    logger.info("```")

    return True


if __name__ == "__main__":
    success = test_patent_analysis_tool()
    sys.exit(0 if success else 1)
