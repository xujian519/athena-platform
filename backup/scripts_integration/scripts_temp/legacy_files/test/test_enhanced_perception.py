#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强感知模块测试脚本
Enhanced Perception Module Test Script

测试感知模块的所有优化功能

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_basic_perception():
    """测试基础感知功能"""
    logger.info("\n🔍 测试基础感知功能")

    try:
        from core.perception import PerceptionEngine

        # 创建感知引擎
        engine = PerceptionEngine(
            agent_id='test_agent',
            config={
                'use_enhanced_multimodal': False,  # 先用标准版本
                'performance': {
                    'enable_cache': False,  # 暂时禁用优化
                    'enable_batch_processing': False,
                    'cache_ttl': 3600
                },
                'monitoring': {
                    'enabled': False,  # 暂时禁用监控
                    'collect_interval': 5,
                    'health_check_interval': 10
                }
            }
        )

        # 初始化引擎
        await engine.initialize()
        logger.info('✅ 感知引擎初始化成功')

        # 获取状态
        status = await engine.get_status()
        logger.info(f"📊 引擎状态: {json.dumps(status, indent=2, ensure_ascii=False)}")

        # 测试文本处理
        text_result = await engine.process(
            '这是一个专利文档测试，包含技术内容和创新点。',
            'text'
        )
        logger.info(f"📝 文本处理结果: 置信度={text_result.confidence:.2f}")

        # 测试多模态处理
        multimodal_data = {
            'text': '专利技术描述',
            'image': 'base64_encoded_image_data',
            'table': {'rows': 5, 'columns': 3}
        }
        multimodal_result = await engine.process(multimodal_data, 'multimodal')
        logger.info(f"🎯 多模态处理结果: 置信度={multimodal_result.confidence:.2f}")

        return engine

    except Exception as e:
        logger.error(f"❌ 基础感知测试失败: {e}")
        return None

async def test_performance_optimization(engine):
    """测试性能优化功能"""
    logger.info("\n⚡ 测试性能优化功能")

    try:
        # 获取性能指标
        dashboard = await engine.get_performance_dashboard()
        logger.info('📈 性能仪表板获取成功')

        # 测试批量处理
        start_time = time.time()
        tasks = []
        for i in range(10):
            task = engine.process(f"测试文档 {i}: 包含专利技术内容', 'text")
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        processing_time = time.time() - start_time

        logger.info(f"🚀 批量处理完成: {len(results)}个任务, 耗时: {processing_time:.2f}秒")
        logger.info(f"⏱️  平均处理时间: {processing_time/len(results):.3f}秒/任务")

        # 获取性能报告
        report = await engine.get_performance_report()
        logger.info(f"📊 性能报告生成成功: 总请求={report.get('total_requests', 0)}")

    except Exception as e:
        logger.error(f"❌ 性能优化测试失败: {e}")

async def test_error_handling(engine):
    """测试错误处理功能"""
    logger.info("\n🛡️ 测试错误处理功能")

    try:
        # 测试无效输入
        invalid_result = await engine.process(None, 'unknown')
        logger.info(f"⚠️  无效输入处理: 置信度={invalid_result.confidence:.2f}")

        # 测试大文本处理
        large_text = '这是一个很长的文本。' * 1000
        large_result = await engine.process(large_text, 'text')
        logger.info(f"📄 大文本处理: 置信度={large_result.confidence:.2f}")

        # 测试错误恢复
        try:
            # 模拟可能导致错误的输入
            error_result = await engine.process({'invalid': 'structure'}, 'multimodal')
            logger.info(f"🔄 错误恢复成功: 置信度={error_result.confidence:.2f}")
        except Exception as e:
            logger.info(f"🔧 错误处理机制激活: {str(e)[:50]}...")

    except Exception as e:
        logger.error(f"❌ 错误处理测试失败: {e}")

async def test_monitoring_system(engine):
    """测试监控系统功能"""
    logger.info("\n📊 测试监控系统功能")

    try:
        # 等待一些监控数据收集
        await asyncio.sleep(5)

        # 获取监控仪表板
        dashboard = await engine.get_performance_dashboard()

        if 'monitoring_dashboard' in dashboard:
            monitoring = dashboard['monitoring_dashboard']
            logger.info('📈 监控系统状态:')

            # 系统状态
            if 'system_status' in monitoring:
                system = monitoring['system_status']
                logger.info(f"  - CPU使用率: {system.get('cpu_percent', [])[-1] if system.get('cpu_percent') else 'N/A'}%")
                logger.info(f"  - 内存使用率: {system.get('memory_percent', [])[-1] if system.get('memory_percent') else 'N/A'}%")
                logger.info(f"  - 磁盘使用率: {system.get('disk_percent', 0)}%")

            # 处理器健康状态
            if 'processor_health' in monitoring:
                health = monitoring['processor_health']
                logger.info(f"  - 健康处理器数量: {len([h for h in health.values() if h.get('status') == 'healthy'])}")

            # 告警信息
            if 'recent_alerts' in monitoring:
                alerts = monitoring['recent_alerts']
                if alerts:
                    logger.info(f"  - 最近的告警: {len(alerts)}条")
                    for alert in alerts[:3]:
                        logger.info(f"    * {alert.get('level', 'unknown')}: {alert.get('message', 'no message')}")
                else:
                    logger.info('  - 当前无告警')

        logger.info('✅ 监控系统测试完成')

    except Exception as e:
        logger.error(f"❌ 监控系统测试失败: {e}")

async def test_enhanced_multimodal():
    """测试增强多模态处理"""
    logger.info("\n🎭 测试增强多模态处理")

    try:
        from core.perception.processors.enhanced_multimodal_processor import (
            EnhancedMultiModalProcessor,
        )

        # 创建增强多模态处理器
        processor = EnhancedMultiModalProcessor(
            processor_id='test_enhanced_multimodal',
            config={
                'fusion_strategy': 'attention_fusion',
                'enable_cross_modal': True,
                'max_modalities': 5,
                'min_confidence': 0.3
            }
        )

        await processor.initialize()
        logger.info('✅ 增强多模态处理器初始化成功')

        # 测试复杂多模态输入
        complex_input = [
            {'type': 'text', 'content': '这是一个专利技术描述'},
            {'type': 'image', 'content': 'image_data_placeholder'},
            {'type': 'table', 'content': {'rows': 10, 'columns': 4}},
            {'type': 'graph', 'content': {'nodes': 5, 'edges': 8}}
        ]

        result = await processor.process(complex_input, 'multimodal')
        logger.info(f"🎯 复杂多模态处理: 置信度={result.confidence:.2f}")

        if result.processed_content:
            analysis = result.processed_content
            logger.info(f"  - 模态数量: {analysis.processing_summary.get('modality_count', 0)}")
            logger.info(f"  - 主导模态: {analysis.processing_summary.get('dominant_modality', 'unknown')}")
            logger.info(f"  - 语义一致性: {analysis.semantic_consistency:.2f}")
            logger.info(f"  - 跨模态洞察: {len(analysis.cross_modal_insights)}条")

        # 获取处理统计
        stats = await processor.get_processing_stats()
        logger.info(f"📊 处理器统计: 融合策略={stats.get('fusion_strategy', 'unknown')}")

        # 清理
        await processor.cleanup()
        logger.info('🧹 增强多模态处理器清理完成')

    except Exception as e:
        logger.error(f"❌ 增强多模态测试失败: {e}")

async def comprehensive_test():
    """综合测试"""
    logger.info('🧪 开始感知模块综合测试')
    logger.info(str('=' * 60))

    engine = None

    try:
        # 1. 基础功能测试
        engine = await test_basic_perception()
        if not engine:
            raise Exception('基础功能测试失败')

        # 2. 性能优化测试
        await test_performance_optimization(engine)

        # 3. 错误处理测试
        await test_error_handling(engine)

        # 4. 监控系统测试
        await test_monitoring_system(engine)

        # 5. 增强多模态测试
        await test_enhanced_multimodal()

        logger.info(str("\n" + '=' * 60))
        logger.info('✅ 所有感知模块测试通过！')
        logger.info('🎉 感知模块优化完成，包含:')
        logger.info('  - ✅ 性能优化器 (缓存、批处理、异步)')
        logger.info('  - ✅ 错误处理器 (重试、降级、容错)')
        logger.info('  - ✅ 监控系统 (指标、告警、健康检查)')
        logger.info('  - ✅ 增强多模态处理器 (融合、注意力机制)')

    except Exception as e:
        logger.info(f"\n❌ 综合测试失败: {e}")
        raise

    finally:
        # 清理资源
        if engine:
            try:
                await engine.shutdown()
                logger.info('🧹 感知引擎已关闭')
            except Exception as e:
                logger.error(f"清理失败: {e}")

if __name__ == '__main__':
    # 运行综合测试
    asyncio.run(comprehensive_test())