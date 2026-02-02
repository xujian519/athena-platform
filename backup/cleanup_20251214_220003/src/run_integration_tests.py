#!/usr/bin/env python3
"""
Athena AI系统模块集成测试运行器
Athena AI System Module Integration Test Runner

执行所有BaseModule兼容模块的集成测试
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('integration_test_results.log')
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """主函数"""
    logger.info('🚀 Athena AI系统 - 模块集成测试')
    logger.info(str('=' * 80))
    logger.info(f"开始时间: {datetime.now()}")
    logger.info(str('=' * 80))

    try:
        # 导入集成测试器
        from core.integration.module_integration_test import ModuleIntegrationTester

        # 创建集成测试器
        logger.info('🔧 创建模块集成测试器...')
        tester = ModuleIntegrationTester()

        # 运行完整集成测试
        logger.info('🧪 开始执行完整模块集成测试...')
        report = await tester.run_full_integration_test()

        # 显示测试结果
        logger.info(str("\n" + '=' * 80))
        logger.info('📊 集成测试报告')
        logger.info(str('=' * 80))

        logger.info(f"测试时间: {report.total_execution_time:.2f} 秒")
        logger.info(f"总测试数: {report.total_tests}")
        logger.info(f"通过测试: {report.passed_tests}")
        logger.info(f"失败测试: {report.failed_tests}")
        logger.info(f"成功率: {(report.passed_tests/report.total_tests)*100:.1f}%")
        logger.info(f"集成健康评分: {report.integration_health_score:.1f}/100")

        # 显示详细测试结果
        logger.info("\n📋 详细测试结果:")
        logger.info(str('-' * 80))
        for result in report.test_results:
            status = '✅ 通过' if result.success else '❌ 失败'
            logger.info(f"{status} {result.test_name}")
            logger.info(f"   执行时间: {result.execution_time:.2f}s")
            if result.error_message:
                logger.info(f"   错误信息: {result.error_message}")

        # 显示模块状态摘要
        logger.info(f"\n🏠 模块状态摘要:")
        logger.info(str('-' * 80))
        summary = report.module_status_summary.get('summary', {})
        for status, count in summary.items():
            logger.info(f"   {status}: {count} 个模块")

        # 保存测试报告
        try:
            report_data = {
                'test_time': datetime.now().isoformat(),
                'total_execution_time': report.total_execution_time,
                'total_tests': report.total_tests,
                'passed_tests': report.passed_tests,
                'failed_tests': report.failed_tests,
                'success_rate': (report.passed_tests / report.total_tests) * 100,
                'integration_health_score': report.integration_health_score,
                'module_status_summary': report.module_status_summary
            }

            import json
            with open('integration_test_report.json', 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"\n📁 测试报告已保存到: integration_test_report.json")

        except Exception as e:
            logger.warning(f"⚠️ 保存测试报告失败: {e}")

        # 清理资源
        logger.info('🧹 清理测试资源...')
        await tester.cleanup()

        logger.info(str("\n" + '=' * 80))
        if report.integration_health_score >= 80:
            logger.info('🎉 集成测试成功！系统架构健康稳定')
        elif report.integration_health_score >= 60:
            logger.info('⚠️ 集成测试部分通过，系统架构需要优化')
        else:
            logger.info('❌ 集成测试失败，系统架构存在严重问题')

        logger.info(f"健康评分: {report.integration_health_score:.1f}/100")
        logger.info(str('=' * 80))

        return report.integration_health_score >= 60

    except Exception as e:
        logger.error(f"❌ 集成测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)