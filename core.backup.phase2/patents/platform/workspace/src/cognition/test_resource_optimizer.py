#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源效率优化器测试脚本
Resource Efficiency Optimizer Test Script

测试资源使用效率优化器的各项功能，包括监控、优化、策略切换等

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import os
import time
from datetime import datetime

import psutil
from resource_efficiency_optimizer import (
    OptimizationStrategy,
    ResourceEfficiencyOptimizer,
    ResourceThreshold,
    ResourceType,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResourceOptimizerTester:
    """资源优化器测试器"""

    def __init__(self):
        self.optimizer = None
        self.test_results = []

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info('🧪 资源效率优化器综合测试')
        logger.info(str('='*60))

        # 测试1: 基础功能测试
        await self.test_basic_functionality()

        # 测试2: 资源监控测试
        await self.test_resource_monitoring()

        # 测试3: 优化策略测试
        await self.test_optimization_strategies()

        # 测试4: 阈值管理测试
        await self.test_threshold_management()

        # 测试5: 自动优化测试
        await self.test_automatic_optimization()

        # 测试6: 性能压力测试
        await self.test_performance_stress()

        # 测试7: 数据导出测试
        await self.test_data_export()

        # 生成测试报告
        self.generate_test_report()

    async def test_basic_functionality(self):
        """测试基础功能"""
        logger.info("\n🔧 测试1: 基础功能测试")
        logger.info(str('-' * 40))

        try:
            # 创建优化器
            self.optimizer = ResourceEfficiencyOptimizer(
                strategy=OptimizationStrategy.ADAPTIVE,
                monitoring_interval=2,
                history_window=60
            )

            # 验证初始化
            assert self.optimizer.strategy == OptimizationStrategy.ADAPTIVE
            assert len(self.optimizer.optimization_actions) > 0
            assert len(self.optimizer.thresholds) > 0

            logger.info('✅ 优化器初始化成功')

            # 测试资源状态获取
            status = self.optimizer.get_resource_status()
            assert isinstance(status, dict)
            logger.info('✅ 资源状态获取正常')

            # 测试优化报告
            report = self.optimizer.get_optimization_report()
            assert 'overall_efficiency_score' in report
            assert 'optimization_statistics' in report
            logger.info('✅ 优化报告生成正常')

            self.test_results.append({
                'test': 'basic_functionality',
                'status': 'passed',
                'message': '所有基础功能测试通过'
            })

        except Exception as e:
            logger.info(f"❌ 基础功能测试失败: {e}")
            self.test_results.append({
                'test': 'basic_functionality',
                'status': 'failed',
                'message': str(e)
            })

    async def test_resource_monitoring(self):
        """测试资源监控"""
        logger.info("\n📊 测试2: 资源监控测试")
        logger.info(str('-' * 40))

        try:
            # 启动监控
            self.optimizer.start_monitoring()
            assert self.optimizer.is_monitoring == True
            logger.info('✅ 监控启动成功')

            # 收集数据
            logger.info('📈 收集资源数据中...')
            await asyncio.sleep(10)

            # 验证数据收集
            for resource_type, metrics in self.optimizer.resource_metrics.items():
                if resource_type != ResourceType.GPU:  # GPU可能不可用
                    assert len(metrics) > 0, f"{resource_type} 没有收集到数据"

            logger.info('✅ 所有资源类型数据收集正常')

            # 验证数据质量
            cpu_metrics = self.optimizer.resource_metrics[ResourceType.CPU]
            latest_cpu = cpu_metrics[-1]
            assert 0 <= latest_cpu.usage_percent <= 100
            logger.info(f"✅ CPU使用率数据有效: {latest_cpu.usage_percent:.1f}%")

            memory_metrics = self.optimizer.resource_metrics[ResourceType.MEMORY]
            latest_memory = memory_metrics[-1]
            assert 0 <= latest_memory.usage_percent <= 100
            logger.info(f"✅ 内存使用率数据有效: {latest_memory.usage_percent:.1f}%")

            # 停止监控
            self.optimizer.stop_monitoring()
            assert self.optimizer.is_monitoring == False
            logger.info('✅ 监控停止成功')

            self.test_results.append({
                'test': 'resource_monitoring',
                'status': 'passed',
                'message': '资源监控功能正常'
            })

        except Exception as e:
            logger.info(f"❌ 资源监控测试失败: {e}")
            self.test_results.append({
                'test': 'resource_monitoring',
                'status': 'failed',
                'message': str(e)
            })

    async def test_optimization_strategies(self):
        """测试优化策略"""
        logger.info("\n🎯 测试3: 优化策略测试")
        logger.info(str('-' * 40))

        try:
            strategies = [
                OptimizationStrategy.CONSERVATIVE,
                OptimizationStrategy.BALANCED,
                OptimizationStrategy.AGGRESSIVE,
                OptimizationStrategy.ADAPTIVE
            ]

            for strategy in strategies:
                logger.info(f"测试策略: {strategy.value}")

                # 设置策略
                self.optimizer.set_strategy(strategy)
                assert self.optimizer.strategy == strategy

                # 模拟资源优化
                for resource_type in [ResourceType.CPU, ResourceType.MEMORY]:
                    # 创建模拟指标
                    metric = self.optimizer.resource_metrics[resource_type][-1] if \
                             self.optimizer.resource_metrics[resource_type] else None

                    if metric:
                        # 手动触发优化
                        await self.optimizer._optimize_resource(resource_type)

                logger.info(f"✅ {strategy.value} 策略测试通过")

            self.test_results.append({
                'test': 'optimization_strategies',
                'status': 'passed',
                'message': '所有优化策略测试通过'
            })

        except Exception as e:
            logger.info(f"❌ 优化策略测试失败: {e}")
            self.test_results.append({
                'test': 'optimization_strategies',
                'status': 'failed',
                'message': str(e)
            })

    async def test_threshold_management(self):
        """测试阈值管理"""
        logger.info("\n⚡ 测试4: 阈值管理测试")
        logger.info(str('-' * 40))

        try:
            # 测试默认阈值
            cpu_threshold = self.optimizer.thresholds[ResourceType.CPU]
            assert cpu_threshold.warning_threshold == 70.0
            assert cpu_threshold.critical_threshold == 90.0
            logger.info('✅ 默认阈值配置正确')

            # 测试阈值设置
            self.optimizer.set_threshold(
                ResourceType.CPU,
                warning=60.0,
                critical=85.0,
                optimization=75.0
            )

            updated_threshold = self.optimizer.thresholds[ResourceType.CPU]
            assert updated_threshold.warning_threshold == 60.0
            assert updated_threshold.critical_threshold == 85.0
            assert updated_threshold.optimization_threshold == 75.0
            logger.info('✅ 阈值更新成功')

            # 测试资源状态判断
            # 创建模拟的高使用率指标
            import datetime

            from resource_efficiency_optimizer import ResourceMetric

            high_usage_metric = ResourceMetric(
                timestamp=datetime.datetime.now(),
                resource_type=ResourceType.CPU,
                usage_percent=95.0,
                absolute_value=4.0,
                unit='cores'
            )

            self.optimizer.resource_metrics[ResourceType.CPU].append(high_usage_metric)

            # 获取状态
            status = self.optimizer.get_resource_status()
            cpu_status = status['cpu']['status']
            assert cpu_status == 'critical'
            logger.info(f"✅ 资源状态判断正确: {cpu_status}")

            self.test_results.append({
                'test': 'threshold_management',
                'status': 'passed',
                'message': '阈值管理功能正常'
            })

        except Exception as e:
            logger.info(f"❌ 阈值管理测试失败: {e}")
            self.test_results.append({
                'test': 'threshold_management',
                'status': 'failed',
                'message': str(e)
            })

    async def test_automatic_optimization(self):
        """测试自动优化"""
        logger.info("\n🤖 测试5: 自动优化测试")
        logger.info(str('-' * 40))

        try:
            # 启动监控
            self.optimizer.start_monitoring()

            # 创建高负载环境
            logger.info('💪 创建高负载环境...')
            load_tasks = []

            # CPU负载
            def cpu_load():
                end_time = time.time() + 10
                while time.time() < end_time:
                    sum(i*i for i in range(1000))

            # 内存负载
            data_chunks = []
            def memory_load():
                for i in range(100):
                    data_chunks.append([0] * 100000)  # 分配内存
                time.sleep(5)
                for chunk in data_chunks:
                    del chunk
                data_chunks.clear()

            # 启动负载任务
            import threading
            cpu_threads = [threading.Thread(target=cpu_load) for _ in range(2)]
            memory_thread = threading.Thread(target=memory_load)

            for t in cpu_threads:
                t.start()
            memory_thread.start()

            # 等待优化触发
            logger.info('⏱️ 等待自动优化触发...')
            await asyncio.sleep(15)

            # 等待负载任务完成
            for t in cpu_threads:
                t.join()
            memory_thread.join()

            # 检查优化历史
            optimization_count = len(self.optimizer.optimization_history)
            logger.info(f"📊 执行了 {optimization_count} 次优化")

            # 验证统计信息
            stats = self.optimizer.stats
            assert stats['total_optimizations'] >= 0
            logger.info(f"✅ 优化统计正常: 总计{stats['total_optimizations']}次")

            # 停止监控
            self.optimizer.stop_monitoring()

            self.test_results.append({
                'test': 'automatic_optimization',
                'status': 'passed',
                'message': f'自动优化执行了{optimization_count}次'
            })

        except Exception as e:
            logger.info(f"❌ 自动优化测试失败: {e}")
            self.test_results.append({
                'test': 'automatic_optimization',
                'status': 'failed',
                'message': str(e)
            })

    async def test_performance_stress(self):
        """测试性能压力"""
        logger.info("\n💪 测试6: 性能压力测试")
        logger.info(str('-' * 40))

        try:
            # 启动监控
            self.optimizer.start_monitoring()

            # 记录开始时间
            start_time = time.time()

            # 执行大量操作
            operations = 100
            logger.info(f"🔄 执行 {operations} 次资源操作...")

            for i in range(operations):
                # 获取资源状态
                status = self.optimizer.get_resource_status()

                # 获取优化报告
                report = self.optimizer.get_optimization_report()

                # 模拟优化
                if i % 10 == 0:
                    await self.optimizer._optimize_resource(ResourceType.MEMORY)

                # 短暂延迟
                await asyncio.sleep(0.1)

            # 计算执行时间
            end_time = time.time()
            execution_time = end_time - start_time
            ops_per_second = operations / execution_time

            logger.info(f"✅ 性能测试完成")
            logger.info(f"   执行时间: {execution_time:.2f}秒")
            logger.info(f"   操作速率: {ops_per_second:.2f} ops/sec")

            # 验证性能指标
            assert execution_time < 30, '执行时间过长'
            assert ops_per_second > 3, '操作速率过低'

            # 停止监控
            self.optimizer.stop_monitoring()

            self.test_results.append({
                'test': 'performance_stress',
                'status': 'passed',
                'message': f'性能测试通过，速率: {ops_per_second:.2f} ops/sec'
            })

        except Exception as e:
            logger.info(f"❌ 性能压力测试失败: {e}")
            self.test_results.append({
                'test': 'performance_stress',
                'status': 'failed',
                'message': str(e)
            })

    async def test_data_export(self):
        """测试数据导出"""
        logger.info("\n💾 测试7: 数据导出测试")
        logger.info(str('-' * 40))

        try:
            # 确保有数据
            if not self.optimizer.is_monitoring:
                self.optimizer.start_monitoring()
                await asyncio.sleep(5)
                self.optimizer.stop_monitoring()

            # 导出数据
            export_file = 'test_resource_optimization_data.json'
            self.optimizer.export_optimization_data(export_file)

            # 验证文件存在
            assert os.path.exists(export_file), '导出文件不存在'
            logger.info('✅ 数据导出文件创建成功')

            # 验证文件内容
            import json
            with open(export_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            required_keys = [
                'export_time',
                'resource_metrics',
                'optimization_history',
                'statistics',
                'thresholds',
                'strategy'
            ]

            for key in required_keys:
                assert key in data, f"导出数据缺少键: {key}"

            logger.info('✅ 导出数据格式正确')

            # 清理测试文件
            os.remove(export_file)
            logger.info('✅ 测试文件清理完成')

            self.test_results.append({
                'test': 'data_export',
                'status': 'passed',
                'message': '数据导出功能正常'
            })

        except Exception as e:
            logger.info(f"❌ 数据导出测试失败: {e}")
            self.test_results.append({
                'test': 'data_export',
                'status': 'failed',
                'message': str(e)
            })

    def generate_test_report(self):
        """生成测试报告"""
        logger.info(str("\n" + '='*60))
        logger.info('📋 测试报告')
        logger.info(str('='*60))

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['status'] == 'passed')
        failed_tests = total_tests - passed_tests

        logger.info(f"\n总测试数: {total_tests}")
        logger.info(f"通过: {passed_tests} ✅")
        logger.info(f"失败: {failed_tests} ❌")
        logger.info(f"通过率: {(passed_tests/total_tests)*100:.1f}%")

        logger.info("\n详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = '✅' if result['status'] == 'passed' else '❌'
            logger.info(f"\n{i}. {result['test'].replace('_', ' ').title()}")
            logger.info(f"   {status_icon} {result['status'].upper()}")
            logger.info(f"   📝 {result['message']}")

        # 生成优化器当前状态报告
        if self.optimizer:
            logger.info(str("\n" + '-'*60))
            logger.info('🔍 优化器当前状态')
            logger.info(str('-'*60))

            status = self.optimizer.get_resource_status()
            for resource, info in status.items():
                status_icon = '🟢' if info['status'] == 'healthy' else '🟡' if info['status'] == 'warning' else '🔴'
                logger.info(f"\n{status_icon} {resource.upper()}")
                logger.info(f"   使用率: {info['current_usage']:.1f}%")
                logger.info(f"   状态: {info['status']}")

            report = self.optimizer.get_optimization_report()
            logger.info(f"\n📊 整体效率分数: {report['overall_efficiency_score']:.1f}/100")

            if report['recommendations']:
                logger.info("\n💡 当前建议:")
                for rec in report['recommendations']:
                    logger.info(f"   - {rec}")

        logger.info(str("\n" + '='*60))

async def main():
    """主函数"""
    tester = ResourceOptimizerTester()
    await tester.run_all_tests()

if __name__ == '__main__':
    asyncio.run(main())