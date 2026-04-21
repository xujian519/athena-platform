#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台LLM层集成演示脚本
演示如何使用Athena平台的统一LLM层进行专利分析

Created by Athena AI系统
Date: 2025-12-14
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_usage():
    """演示基础用法"""
    logger.info("\n" + "="*60)
    logger.info("演示1: 基础用法")
    logger.info("="*60)

    from patent_executors_platform_llm import (
        PatentExecutorFactory,
        PatentTask,
        TaskPriority,
        AnalysisType
    )

    # 创建工厂
    factory = PatentExecutorFactory()

    # 创建专利分析任务
    task = PatentTask(
        id='demo_001',
        task_type='patent_analysis',
        parameters={
            'patent_data': {
                'patent_id': 'CN202410001234.5',
                'title': '基于深度学习的智能图像识别系统及方法',
                'abstract': '本发明公开了一种基于深度学习的智能图像识别系统，包括图像预处理模块、特征提取模块、分类模块和输出模块。该系统采用改进的卷积神经网络结构，具有高精度、实时性强的特点，可广泛应用于安防监控、医疗诊断等领域。',
                'claims': '1. 一种基于深度学习的智能图像识别系统，其特征在于，包括：图像预处理模块，用于对输入图像进行标准化和增强处理；特征提取模块，使用改进的卷积神经网络提取图像深层特征；分类模块，通过全连接层实现高精度图像分类；输出模块，生成分类结果和置信度信息。2. 根据权利要求1所述的系统，其特征在于，所述卷积神经网络采用残差连接结构。',
                'description': '本发明涉及人工智能和计算机视觉技术领域。针对现有图像识别技术精度低、实时性差的问题，本发明提出了一种基于深度学习的智能图像识别系统。该系统首先通过图像预处理模块对输入图像进行标准化处理，然后使用改进的卷积神经网络提取特征，最后通过分类模块输出识别结果。实验表明，该系统在多个数据集上都取得了优异的性能。'
            },
            'analysis_type': 'novelty'
        },
        priority=TaskPriority.HIGH
    )

    # 执行任务
    logger.info("🚀 执行专利分析任务...")
    result = await factory.execute_with_executor('patent_analysis', task)

    # 显示结果
    logger.info(f"\n📊 执行结果:")
    logger.info(f"  状态: {'✅ 成功' if result.is_success() else '❌ 失败'}")
    logger.info(f"  执行时间: {result.execution_time:.2f}秒")
    logger.info(f"  置信度: {result.confidence:.2f}")

    if result.is_success() and result.data:
        logger.info(f"\n🤖 AI分析信息:")
        logger.info(f"  提供商: {result.data.get('llm_provider', 'N/A')}")
        logger.info(f"  模型: {result.data.get('model_used', 'N/A')}")
        logger.info(f"  Token使用: {result.data.get('tokens_used', 0)}")

        logger.info(f"\n📋 分析摘要:")
        report = result.data.get('report', {})
        logger.info(f"  {report.get('executive_summary', 'N/A')}")

        logger.info(f"\n💡 建议:")
        for i, rec in enumerate(result.data.get('recommendations', []), 1):
            logger.info(f"  {i}. {rec}")


async def demo_different_analysis_types():
    """演示不同分析类型"""
    logger.info("\n" + "="*60)
    logger.info("演示2: 不同分析类型")
    logger.info("="*60)

    from patent_executors_platform_llm import (
        PatentExecutorFactory,
        PatentTask
    )

    factory = PatentExecutorFactory()

    # 准备测试数据
    patent_data = {
        'title': '基于区块链的分布式数据存储系统',
        'abstract': '本发明提供一种基于区块链技术的分布式数据存储方案，通过智能合约实现数据的去中心化存储和访问控制，确保数据的安全性和不可篡改性。',
        'description': '本发明涉及区块链和分布式存储技术领域...'
    }

    analysis_types = ['novelty', 'inventiveness', 'comprehensive']

    for analysis_type in analysis_types:
        logger.info(f"\n{'='*40}")
        logger.info(f"分析类型: {analysis_type}")
        logger.info(f"{'='*40}")

        task = PatentTask(
            id=f'demo_{analysis_type}_001',
            task_type='patent_analysis',
            parameters={
                'patent_data': patent_data,
                'analysis_type': analysis_type
            }
        )

        result = await factory.execute_with_executor('patent_analysis', task)

        if result.is_success():
            report = result.data.get('report', {})
            logger.info(f"摘要: {report.get('executive_summary', 'N/A')}")


async def show_available_models():
    """显示可用模型"""
    logger.info("\n" + "="*60)
    logger.info("演示3: 可用LLM模型")
    logger.info("="*60)

    try:
        from core.llm.model_registry import get_model_registry
        from core.llm.unified_llm_manager import get_unified_llm_manager

        registry = get_model_registry()

        logger.info(f"\n📦 已注册的模型:")
        for model_id, capability in registry.capabilities.items():
            logger.info(f"\n  模型: {model_id}")
            logger.info(f"    - 类型: {capability.model_type.value}")
            logger.info(f"    - 部署: {capability.deployment.value}")
            logger.info(f"    - 上下文: {capability.max_context:,} tokens")
            logger.info(f"    - 质量评分: {capability.quality_score:.2f}")
            logger.info(f"    - 成本: ¥{capability.cost_per_1k_tokens}/1K tokens")

        # 显示加载的适配器
        llm_manager = get_unified_llm_manager()
        if llm_manager.adapters:
            logger.info(f"\n✅ 已加载的适配器 ({len(llm_manager.adapters)}个):")
            for model_id in llm_manager.adapters.keys():
                logger.info(f"  - {model_id}")
        else:
            logger.info(f"\n⚠️ 尚未加载适配器，执行任务时会自动初始化")

    except ImportError as e:
        logger.error(f"无法导入LLM层: {e}")


async def demo_error_handling():
    """演示错误处理"""
    logger.info("\n" + "="*60)
    logger.info("演示4: 错误处理和降级")
    logger.info("="*60)

    from patent_executors_platform_llm import (
        PatentExecutorFactory,
        PatentTask
    )

    factory = PatentExecutorFactory()

    # 测试参数验证
    logger.info("\n🔍 测试1: 缺少必需参数")
    task = PatentTask(
        id='demo_error_001',
        task_type='patent_analysis',
        parameters={}  # 空参数
    )

    result = await factory.execute_with_executor('patent_analysis', task)
    logger.info(f"结果: {result.status}")
    logger.info(f"错误: {result.error}")

    # 测试不完整的专利数据
    logger.info("\n🔍 测试2: 不完整的专利数据（使用规则引擎）")
    task = PatentTask(
        id='demo_error_002',
        task_type='patent_analysis',
        parameters={
            'patent_data': {
                'title': '测试专利'  # 只有标题
            },
            'analysis_type': 'novelty'
        }
    )

    result = await factory.execute_with_executor('patent_analysis', task)
    logger.info(f"结果: {result.status}")
    if result.is_success():
        logger.info(f"提供商: {result.data.get('llm_provider')}")
        logger.info(f"方法: {result.data.get('analysis_result', {}).get('method')}")


async def main():
    """主函数"""
    logger.info("\n" + "="*60)
    logger.info("🚀 平台LLM层集成演示")
    logger.info("="*60)
    logger.info("\n本演示将展示:")
    logger.info("1. 基础用法 - 创建和执行分析任务")
    logger.info("2. 不同分析类型 - novelty, inventiveness, comprehensive")
    logger.info("3. 可用模型 - 查看平台LLM层的所有模型")
    logger.info("4. 错误处理 - 参数验证和降级机制")

    try:
        # 演示1: 基础用法
        await demo_basic_usage()

        # 演示2: 不同分析类型
        # await demo_different_analysis_types()

        # 演示3: 可用模型
        # await show_available_models()

        # 演示4: 错误处理
        # await demo_error_handling()

        logger.info("\n" + "="*60)
        logger.info("✅ 演示完成！")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"演示执行失败: {e}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())
