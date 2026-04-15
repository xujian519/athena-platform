#!/usr/bin/env python3
"""
专利检索系统测试脚本
Patent Retrieval System Test Script
用于验证修复后的系统功能
"""

import asyncio
import logging
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_hybrid_retrieval_system():
    """测试混合检索系统"""
    logger.info("🔧 测试混合检索系统修复结果")

    try:
        # 测试numpy兼容性
        logger.info("📚 测试numpy兼容性...")
        from config.numpy_compatibility import array, mean, ones, random, sum, zeros

        test_array = array([1, 2, 3, 4, 5])
        zeros(5)
        ones(5)
        random(5)
        test_mean = mean(test_array)
        sum(test_array)

        logger.info(f"✅ numpy兼容性测试通过: array={test_array}, mean={test_mean}")

        # 测试数据库配置
        logger.info("🗄️ 测试数据库配置...")
        from config.database import get_patent_db_config

        db_config = get_patent_db_config()
        config_dict = db_config.get_config()

        logger.info(
            f"✅ 数据库配置加载成功: {config_dict.host}:{config_dict.port}/{config_dict.database}"
        )

        # 测试混合检索系统导入
        logger.info("🔍 测试混合检索系统导入...")
        from patent_hybrid_retrieval.hybrid_retrieval_system import HybridRetrievalSystem

        logger.info("✅ 混合检索系统导入成功")

        # 创建系统实例（不连接数据库）
        logger.info("🚀 创建混合检索系统实例...")
        retrieval_system = HybridRetrievalSystem()

        # 测试系统统计
        logger.info("📊 获取系统统计...")
        stats = retrieval_system.get_statistics()

        logger.info(f"✅ 系统统计信息: {stats}")

        # 测试示例数据检索
        logger.info("🔍 测试示例数据检索...")

        # 加载示例数据
        count = retrieval_system.load_patent_data("")
        logger.info(f"✅ 加载了 {count} 条示例专利数据")

        # 执行测试查询
        test_queries = ["深度学习图像识别", "智能语音交互系统", "区块链数据存储"]

        for query in test_queries:
            logger.info(f"🔎 执行查询: {query}")
            results = retrieval_system.search(query, top_k=3)

            if results:
                logger.info(f"✅ 查询成功，返回 {len(results)} 条结果")
                for i, result in enumerate(results, 1):
                    logger.info(
                        f"   {i}. {result.patent_id} - 评分: {result.score:.4f} - 来源: {result.source}"
                    )
            else:
                logger.warning(f"⚠️ 查询无结果: {query}")

        logger.info("✅ 混合检索系统测试完成")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        logger.error(traceback.format_exc())


async def test_real_patent_system():
    """测试真实专利系统（不连接数据库）"""
    logger.info("🔧 测试真实专利检索系统修复结果")

    try:
        # 测试真实专利系统导入
        logger.info("🔍 测试真实专利检索系统导入...")
        from patent_hybrid_retrieval.real_patent_hybrid_retrieval import RealPatentHybridRetrieval

        logger.info("✅ 真实专利检索系统导入成功")

        # 创建系统实例（不连接数据库）
        logger.info("🚀 创建真实专利检索系统实例...")
        retrieval_system = RealPatentHybridRetrieval()

        # 测试关键词提取
        logger.info("📝 测试关键词提取...")
        test_text = "基于深度学习的图像识别方法和系统"
        keywords = retrieval_system._extract_keywords(test_text)
        logger.info(f"✅ 关键词提取成功: {keywords}")

        # 测试查询向量生成
        logger.info("🔢 测试查询向量生成...")
        query_vector = await retrieval_system._generate_query_vector(test_text)
        if query_vector:
            logger.info(f"✅ 查询向量生成成功: 维度={len(query_vector)}")
        else:
            logger.warning("⚠️ 查询向量生成失败")

        # 测试系统配置
        logger.info("⚙️ 测试系统配置...")
        stats = retrieval_system.get_system_stats()
        logger.info(f"✅ 系统配置: 组件={stats['components']}")

        logger.info("✅ 真实专利检索系统测试完成")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        logger.error(traceback.format_exc())


async def main():
    """主测试函数"""
    logger.info("🚀 开始专利检索系统修复验证测试")
    logger.info("=" * 80)

    # 测试混合检索系统
    await test_hybrid_retrieval_system()

    logger.info("\n" + "-" * 80)

    # 测试真实专利系统
    await test_real_patent_system()

    logger.info("\n" + "=" * 80)
    logger.info("✅ 所有测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
