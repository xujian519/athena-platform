#!/usr/bin/env python3
"""
测试验证器框架 - Phase 2
Test Verification Framework - Phase 2

验证验证器框架是否正常工作

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_verifier_import():
    """测试验证器导入"""
    logger.info("🧪 测试1: 验证器导入")

    try:
        from core.cognition.verification import (
            ClaimDraftingVerifier,
            PatentAnalysisVerifier,
            PatentSearchVerifier,
            VerificationIssue,
            VerificationResult,
            VerificationStatus,
            VerifierFactory,
        )
        logger.info("   ✅ 验证器模块导入成功")

        # 检查支持的验证器
        supported = VerifierFactory.get_supported_actions()
        logger.info(f"   📋 支持的操作: {', '.join(supported)}")

        return True

    except ImportError as e:
        logger.error(f"   ❌ 导入失败: {e}")
        return False


async def test_patent_search_verifier():
    """测试专利检索验证器"""
    logger.info("🧪 测试2: 专利检索验证器")

    try:
        from core.cognition.verification import PatentSearchVerifier

        verifier = PatentSearchVerifier()

        # 测试数据 - 有效结果
        valid_data = {
            "results": [
                {"title": "专利1", "patent_id": "CN123456"},
                {"title": "专利2", "patent_id": "CN789012"},
            ],
            "query": "深度学习",
            "total_count": 2,
        }

        result = await verifier.verify(valid_data)
        logger.info(f"   📊 有效数据验证: {result.status.value} (分数: {result.score:.1f})")

        # 测试数据 - 无结果
        no_results_data = {
            "results": [],
            "query": "test",
            "total_count": 0,
        }

        result = await verifier.verify(no_results_data)
        logger.info(f"   📊 无结果验证: {result.status.value} (分数: {result.score:.1f})")

        logger.info("   ✅ 专利检索验证器测试成功")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def test_patent_analysis_verifier():
    """测试专利分析验证器"""
    logger.info("🧪 测试3: 专利分析验证器")

    try:
        from core.cognition.verification import PatentAnalysisVerifier

        verifier = PatentAnalysisVerifier()

        # 测试数据 - 简单分析
        analysis_data = {
            "analysis": """
            本发明涉及一种深度学习模型，包括输入层、隐藏层和输出层。
            创新点：使用新的激活函数提高模型性能。
            技术效果：准确率提高10%。
            """,
            "patent_id": "CN123456",
        }

        result = await verifier.verify(analysis_data)
        logger.info(f"   📊 分析验证: {result.status.value} (分数: {result.score:.1f})")

        if result.issues:
            for issue in result.issues:
                logger.info(f"      - {issue.severity}: {issue.message}")

        logger.info("   ✅ 专利分析验证器测试成功")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def test_claim_drafting_verifier():
    """测试权利要求撰写验证器"""
    logger.info("🧪 测试4: 权利要求撰写验证器")

    try:
        from core.cognition.verification import ClaimDraftingVerifier

        verifier = ClaimDraftingVerifier()

        # 测试数据 - 标准权利要求
        claims_data = {
            "claims": """
            1. 一种深度学习模型，其特征在于，包括：
               输入层，用于接收输入数据；
               隐藏层，所述隐藏层包括至少一个神经网络层；
               输出层，用于输出预测结果。

            2. 根据权利要求1所述的深度学习模型，其特征在于，
               所述神经网络层使用ReLU激活函数。
            """
        }

        result = await verifier.verify(claims_data)
        logger.info(f"   📊 权利要求验证: {result.status.value} (分数: {result.score:.1f})")

        if result.issues:
            for issue in result.issues:
                logger.info(f"      - {issue.severity}: {issue.message}")

        logger.info("   ✅ 权利要求撰写验证器测试成功")
        return True

    except Exception as e:
        logger.error(f"   ❌ 测试失败: {e}", exc_info=True)
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 开始测试 Phase 2: 验证机制系统")
    logger.info("=" * 60)

    success = True

    try:
        if not await test_verifier_import():
            success = False
        logger.info("")

        if not await test_patent_search_verifier():
            success = False
        logger.info("")

        if not await test_patent_analysis_verifier():
            success = False
        logger.info("")

        if not await test_claim_drafting_verifier():
            success = False
        logger.info("")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        success = False

    logger.info("=" * 60)
    if success:
        logger.info("✅ Phase 2: 验证机制系统 - 测试通过")
    else:
        logger.info("❌ Phase 2: 验证机制系统 - 测试失败")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
