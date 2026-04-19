#!/usr/bin/env python3
from __future__ import annotations
"""
增强感知模块测试脚本
Test Enhanced Perception Module

验证BaseModule兼容性和基础功能
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.enhanced_perception_module import EnhancedPerceptionModule

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_enhanced_perception_module():
    """测试增强感知模块"""
    logger.info("\n🔍 增强感知模块测试")
    logger.info(str("=" * 60))

    try:
        # 1. 创建模块实例
        logger.info("\n1. 创建增强感知模块...")
        perception_module = EnhancedPerceptionModule(
            agent_id="test_perception_agent_001",
            config={
                "enable_multimodal": True,
                "max_file_size": 10 * 1024 * 1024,  # 10MB
                "test_mode": True,
            },
        )
        logger.info("✅ 感知模块创建成功")

        # 2. 初始化模块
        logger.info("\n2. 初始化感知模块...")
        init_success = await perception_module.initialize()
        if init_success:
            logger.info("✅ 感知模块初始化成功")
        else:
            logger.info("❌ 感知模块初始化失败")
            return False

        # 3. 健康检查
        logger.info("\n3. 执行健康检查...")
        health_status = await perception_module.health_check()
        logger.info("✅ 健康检查结果:")
        logger.info(f"   - 健康状态: {'健康' if health_status.value == 'healthy' else '不健康'}")
        logger.info(f"   - 状态值: {health_status.value}")

        # 获取健康检查详情
        if hasattr(perception_module, "_health_check_details"):
            details = perception_module._health_check_details
            logger.info(f"   - 感知引擎状态: {details.get('perception_status', 'unknown')}")
            logger.info(f"   - 依赖状态: {details.get('dependencies_status', 'unknown')}")
            logger.info(f"   - 处理状态: {details.get('processing_status', 'unknown')}")
            logger.info(f"   - 整体健康: {details.get('overall_healthy', False)}")

            stats = details.get("stats", {})
            if stats:
                logger.info(
                    f"   - 处理统计: 总计{stats.get('total_documents', 0)}, 成功{stats.get('successful_documents', 0)}, 失败{stats.get('failed_documents', 0)}"
                )

        # 4. 测试数据感知
        logger.info("\n4. 测试数据感知...")
        test_data = {
            "content": "这是一个测试文档内容,包含技术特征:传感器装置、微处理器组件。",
            "type": "test_document",
            "metadata": {"source": "test", "timestamp": "2025-12-11"},
        }

        perception_result = await perception_module.perceive(test_data, "document")
        logger.info("✅ 数据感知完成")
        logger.info(f"   - 处理成功: {perception_result.get('success', False)}")
        logger.info(f"   - 数据类型: {perception_result.get('data_type', 'unknown')}")
        logger.info(f"   - 处理方法: {perception_result.get('processing_method', 'unknown')}")

        # 5. 测试分析方法
        logger.info("\n5. 测试分析方法...")
        analysis_result = await perception_module.analyze(test_data)
        logger.info("✅ 分析完成")
        logger.info(f"   - 包含感知结果: {'perception' in analysis_result}")
        logger.info(f"   - 包含分析结果: {'analysis' in analysis_result}")
        logger.info(f"   - 处理智能体: {analysis_result.get('processing_agent', 'unknown')}")

        # 6. 获取模块状态
        logger.info("\n6. 获取模块状态...")
        status = perception_module.get_status()
        logger.info("✅ 状态获取完成")
        logger.info(f"   - 智能体ID: {status.get('agent_id', 'unknown')}")
        logger.info(f"   - 模块类型: {status.get('module_type', 'unknown')}")
        logger.info(f"   - 运行状态: {status.get('status', 'unknown')}")
        logger.info(f"   - 统计信息: {status.get('statistics', {})}")

        # 7. 获取性能指标
        logger.info("\n7. 获取性能指标...")
        metrics = perception_module.get_metrics()
        logger.info("✅ 指标获取完成")
        logger.info(f"   - 模块状态: {metrics.get('module_status', 'unknown')}")
        logger.info(f"   - 代理ID: {metrics.get('agent_id', 'unknown')}")
        logger.info(f"   - 初始化状态: {metrics.get('initialized', False)}")
        logger.info(f"   - 运行时长: {metrics.get('uptime_seconds', 0):.2f}s")

        # 8. 测试关闭
        logger.info("\n8. 测试模块关闭...")
        await perception_module.shutdown()
        logger.info("✅ 模块关闭成功")

        logger.info(str("\n" + "=" * 60))
        logger.info("🎉 增强感知模块测试完成 - 所有测试通过!")
        return True

    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e!s}")
        import traceback

        traceback.print_exc()
        return False


async def test_file_processing():
    """测试文件处理功能(如果存在测试文件)"""
    logger.info("\n📁 文件处理测试")
    logger.info(str("=" * 60))

    try:
        perception_module = EnhancedPerceptionModule(
            agent_id="file_test_agent", config={"test_mode": True}
        )

        await perception_module.initialize()

        # 查找测试文件
        test_files = [
            Path(__file__).parent.parent.parent / "test_data" / "sample.txt",
            Path(__file__).parent / "test_sample.txt",
        ]

        test_file = None
        for file_path in test_files:
            if file_path.exists():
                test_file = file_path
                break

        if test_file:
            logger.info(f"\n使用测试文件: {test_file}")
            result = await perception_module.perceive(str(test_file), "document")
            logger.info(f"✅ 文件处理成功: {result.get('success', False)}")
        else:
            logger.info("⚠️ 未找到测试文件,跳过文件处理测试")

        await perception_module.shutdown()
        return True

    except Exception as e:
        logger.error(f"❌ 文件处理测试失败: {e!s}")
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 增强感知模块完整测试套件")
    logger.info(str("=" * 80))

    # 基础功能测试
    basic_test_passed = await test_enhanced_perception_module()

    # 文件处理测试
    file_test_passed = await test_file_processing()

    # 测试总结
    logger.info(str("\n" + "=" * 80))
    logger.info("📊 测试总结")
    logger.info(str("=" * 80))
    logger.info(f"基础功能测试: {'✅ 通过' if basic_test_passed else '❌ 失败'}")
    logger.info(f"文件处理测试: {'✅ 通过' if file_test_passed else '❌ 失败'}")

    overall_success = basic_test_passed and file_test_passed
    logger.info(f"\n🎯 总体结果: {'✅ 全部测试通过' if overall_success else '❌ 存在失败测试'}")

    return overall_success


if __name__ == "__main__":
    asyncio.run(main())
