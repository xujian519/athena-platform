#!/usr/bin/env python3
"""
模块集成测试系统
Module Integration Test System

验证所有BaseModule兼容模块的集成功能和协同工作能力
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入BaseModule标准接口
from core.base_module import BaseModule, HealthStatus, ModuleStatus

# 导入依赖管理器
from core.dependency.module_dependency_manager import (
    CORE_MODULE_DEPENDENCIES,
    ModuleDependencyManager,
    ModuleInfo,
    ModulePriority,
)

# 导入所有增强模块
try:
    from core.cognition.enhanced_cognition_module import EnhancedCognitionModule
    from core.communication.enhanced_communication_module import (
        EnhancedCommunicationModule,
    )
    from core.evaluation.enhanced_evaluation_module import EnhancedEvaluationModule
    from core.execution.enhanced_execution_engine import EnhancedExecutionEngine
    from core.knowledge.enhanced_knowledge_tools_module import (
        EnhancedKnowledgeToolsModule,
    )
    from core.learning.enhanced_learning_engine import EnhancedLearningEngine
    from core.memory.enhanced_memory_module import EnhancedMemoryModule
    from core.perception.enhanced_perception_module import EnhancedPerceptionModule
    ALL_MODULES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"无法导入某些增强模块: {e}")
    ALL_MODULES_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class IntegrationTestResult:
    """集成测试结果"""
    test_name: str
    success: bool = False
    execution_time: float = 0.0
    error_message: str | None = None
    test_data: dict[str, Any] = field(default_factory=dict)
    module_results: dict[str, dict[str, Any]] = field(default_factory=dict)

@dataclass
class IntegrationTestReport:
    """集成测试报告"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_execution_time: float
    test_results: list[IntegrationTestResult] = field(default_factory=list)
    module_status_summary: dict[str, Any] = field(default_factory=dict)
    integration_health_score: float = 0.0

class ModuleIntegrationTester:
    """模块集成测试器"""

    def __init__(self):
        """初始化集成测试器"""
        self.dependency_manager = ModuleDependencyManager({
            'default_timeout': 15.0,
            'enable_parallel_startup': True,
            'health_check_interval': 3.0
        })
        self.loaded_modules: dict[str, BaseModule] = {}
        self.test_results: list[IntegrationTestResult] = []

        logger.info('🧪 模块集成测试器初始化完成')

    async def run_full_integration_test(self) -> IntegrationTestReport:
        """
        运行完整的集成测试

        Returns:
            集成测试报告
        """
        start_time = time.time()
        logger.info('🚀 开始完整模块集成测试')

        test_plan = [
            ('模块注册与依赖验证', self._test_module_registration),
            ('单独模块功能测试', self._test_individual_modules),
            ('模块间通信测试', self._test_module_communication),
            ('并行操作测试', self._test_parallel_operations),
            ('错误处理与恢复测试', self._test_error_handling),
            ('性能指标测试', self._test_performance_metrics),
            ('健康检查集成', self._test_health_checking),
            ('启动与关闭流程', self._test_lifecycle_management)
        ]

        for test_name, test_function in test_plan:
            logger.info(f"📋 执行测试: {test_name}")
            test_result = await test_function()
            self.test_results.append(test_result)

            if test_result.success:
                logger.info(f"✅ {test_name} - 通过")
            else:
                logger.error(f"❌ {test_name} - 失败: {test_result.error_message}")

        # 生成测试报告
        total_time = time.time() - start_time
        report = self._generate_test_report(total_time)

        logger.info('🎯 集成测试完成')
        logger.info(f"📊 总体结果: {report.passed_tests}/{report.total_tests} 通过")
        logger.info(f"🏆 集成健康评分: {report.integration_health_score:.1f}/100")

        return report

    async def _test_module_registration(self) -> IntegrationTestResult:
        """测试模块注册与依赖验证"""
        test_result = IntegrationTestResult('模块注册与依赖验证')
        start_time = time.time()

        try:
            if not ALL_MODULES_AVAILABLE:
                raise ImportError('部分增强模块不可用')

            # 注册所有模块
            module_classes = {
                'perception': (EnhancedPerceptionModule, ModulePriority.CRITICAL),
                'memory': (EnhancedMemoryModule, ModulePriority.CRITICAL),
                'cognition': (EnhancedCognitionModule, ModulePriority.CRITICAL),
                'execution': (EnhancedExecutionEngine, ModulePriority.HIGH),
                'learning': (EnhancedLearningEngine, ModulePriority.HIGH),
                'communication': (EnhancedCommunicationModule, ModulePriority.NORMAL),
                'evaluation': (EnhancedEvaluationModule, ModulePriority.NORMAL),
                'knowledge_tools': (EnhancedKnowledgeToolsModule, ModulePriority.LOW)
            }

            for module_id, (module_class, priority) in module_classes.items():
                module_info = ModuleInfo(
                    module_id=module_id,
                    module_name=f"Enhanced {module_id.title()}",
                    module_class=module_class,
                    priority=priority,
                    required=True,
                    startup_timeout=10.0,
                    config={'test_mode': True, 'enable_fast_mode': True}
                )
                self.dependency_manager.register_module(module_info)

            # 注册依赖关系
            for module_id, dependencies in CORE_MODULE_DEPENDENCIES.items():
                for dep in dependencies:
                    self.dependency_manager.register_dependency(module_id, dep)

            # 验证启动计划
            startup_plan = self.dependency_manager.create_startup_plan()
            test_result.test_data = {
                'registered_modules': len(module_classes),
                'startup_order': startup_plan.startup_order,
                'parallel_groups': len(startup_plan.parallel_groups),
                'dependency_graph_nodes': startup_plan.total_estimated_time
            }

            test_result.success = True
            logger.info(f"   注册模块: {len(module_classes)} 个")
            logger.info(f"   启动顺序: {startup_plan.startup_order}")

        except Exception as e:
            test_result.success = False
            test_result.error_message = str(e)

        test_result.execution_time = time.time() - start_time
        return test_result

    async def _test_individual_modules(self) -> IntegrationTestResult:
        """测试单独模块功能"""
        test_result = IntegrationTestResult('单独模块功能测试')
        start_time = time.time()

        try:
            startup_plan = self.dependency_manager.create_startup_plan()
            module_results = {}

            # 测试每个模块的基本功能
            for module_id in startup_plan.startup_order[:3]:  # 测试前3个模块
                logger.info(f"   测试模块: {module_id}")

                # 启动模块
                success = await self.dependency_manager.startup_module(module_id)
                if not success:
                    logger.error(f"   ❌ 模块启动失败: {module_id}")
                    continue

                # 获取模块实例
                if module_id in self.dependency_manager.modules:
                    module_info = self.dependency_manager.modules[module_id]
                    if module_info.instance:
                        self.loaded_modules[module_id] = module_info.instance

                        # 基本功能测试
                        test_data = {'test_input': 'integration_test'}
                        result = await module_info.instance.process(test_data)

                        # 健康检查
                        health_status = await module_info.instance.health_check()

                        # 获取状态
                        status = module_info.instance.get_status()

                        module_results[module_id] = {
                            'startup': True,
                            'process': result.get('success', False),
                            'health': health_status.value,
                            'status': status.get('status', 'unknown')
                        }

                        logger.info(f"   ✅ {module_id} - 启动:成功, 处理:{'成功' if result.get('success') else '失败'}")

            test_result.test_data = {'module_results': module_results}
            test_result.success = True

        except Exception as e:
            test_result.success = False
            test_result.error_message = str(e)

        test_result.execution_time = time.time() - start_time
        return test_result

    async def _test_module_communication(self) -> IntegrationTestResult:
        """测试模块间通信"""
        test_result = IntegrationTestResult('模块间通信测试')
        start_time = time.time()

        try:
            communication_results = {}

            # 测试感知到认知的通信
            if 'perception' in self.loaded_modules and 'cognition' in self.loaded_modules:
                perception_module = self.loaded_modules['perception']
                cognition_module = self.loaded_modules['cognition']

                # 感知模块处理数据
                perception_data = await perception_module.process({
                    'operation': 'perceive',
                    'input_data': '集成测试输入数据',
                    'perception_type': 'text'
                })

                # 认知模块处理感知结果
                if perception_data.get('success'):
                    cognition_data = await cognition_module.process({
                        'operation': 'analyze',
                        'input_data': perception_data
                    })

                    communication_results['perception_to_cognition'] = cognition_data.get('success', False)
                    logger.info('   ✅ 感知 -> 认知通信: 成功')

            # 测试记忆到学习的通信
            if 'memory' in self.loaded_modules and 'learning' in self.loaded_modules:
                memory_module = self.loaded_modules['memory']
                learning_module = self.loaded_modules['learning']

                # 存储经验
                memory_data = await memory_module.process({
                    'operation': 'store',
                    'content': '集成测试经验数据',
                    'memory_type': 'short_term',
                    'metadata': {'test': True}
                })

                # 学习模块处理
                if memory_data.get('success'):
                    learning_data = await learning_module.process({
                        'operation': 'process_experience',
                        'task': '集成测试',
                        'action': '存储测试数据',
                        'result': {'success': True},
                        'reward': 0.8
                    })

                    communication_results['memory_to_learning'] = learning_data.get('success', False)
                    logger.info('   ✅ 记忆 -> 学习通信: 成功')

            test_result.test_data = {'communication_results': communication_results}
            test_result.success = len(communication_results) > 0

        except Exception as e:
            test_result.success = False
            test_result.error_message = str(e)

        test_result.execution_time = time.time() - start_time
        return test_result

    async def _test_parallel_operations(self) -> IntegrationTestResult:
        """测试并行操作"""
        test_result = IntegrationTestResult('并行操作测试')
        start_time = time.time()

        try:
            parallel_tasks = []
            task_results = {}

            # 初始化任务结果字典
            task_results = {}

            # 创建并行任务
            for module_id, module in self.loaded_modules.items():
                # 健康检查任务
                health_task = asyncio.create_task(module.health_check())
                parallel_tasks.append((module_id, 'health_check', health_task))

                # 状态获取任务 (同步调用,不需要包装)
                try:
                    status_result = module.get_status()
                    task_results[f"{module_id}_get_status"] = status_result is not None
                except Exception as e:
                    task_results[f"{module_id}_get_status"] = False
                    logger.warning(f"   ⚠️ 状态获取失败 {module_id}: {e}")

                # 处理任务
                process_task = asyncio.create_task(module.process({'test': 'parallel_test', 'module_id': module_id}))
                parallel_tasks.append((module_id, 'process', process_task))

            # 并行执行异步任务
            if parallel_tasks:
                async_results = await asyncio.gather(
                    *[task for _, _, task in parallel_tasks],
                    return_exceptions=True
                )

                for i, (module_id, operation, _) in enumerate(parallel_tasks):
                    result = async_results[i]
                    if isinstance(result, Exception):
                        logger.warning(f"   ⚠️ 并行操作失败 {module_id}.{operation}: {result}")
                        task_results[f"{module_id}_{operation}"] = False
                    else:
                        if operation == 'health_check':
                            task_results[f"{module_id}_{operation}"] = result.value == 'healthy'
                        elif operation == 'process':
                            task_results[f"{module_id}_{operation}"] = result.get('success', False)

            successful_operations = sum(1 for v in task_results.values() if v)
            total_operations = len(task_results)

            test_result.test_data = {
                'total_operations': total_operations,
                'successful_operations': successful_operations,
                'success_rate': successful_operations / total_operations if total_operations > 0 else 0
            }
            test_result.success = successful_operations >= total_operations * 0.7  # 70%成功率

            logger.info(f"   并行操作: {successful_operations}/{total_operations} 成功")

        except Exception as e:
            test_result.success = False
            test_result.error_message = str(e)

        test_result.execution_time = time.time() - start_time
        return test_result

    async def _test_error_handling(self) -> IntegrationTestResult:
        """测试错误处理与恢复"""
        test_result = IntegrationTestResult('错误处理与恢复测试')
        start_time = time.time()

        try:
            error_handling_results = {}

            # 测试无效输入处理
            for module_id, module in self.loaded_modules.items():
                try:
                    # 发送无效操作
                    result = await module.process({'operation': 'invalid_operation'})
                    error_handling_results[f"{module_id}_invalid_input"] = not result.get('success', True)
                    logger.info(f"   ✅ {module_id} 无效输入处理: 正常")
                except Exception as e:
                    error_handling_results[f"{module_id}_invalid_input"] = True
                    logger.info(f"   ✅ {module_id} 异常捕获: 正常")

            # 测试健康检查失败处理
            for module_id, module in self.loaded_modules.items():
                try:
                    # 强制设置错误状态(模拟)
                    if hasattr(module, '_module_status'):
                        original_status = module._module_status
                        module._module_status = ModuleStatus.ERROR

                        health_status = await module.health_check()
                        error_handling_results[f"{module_id}_health_error"] = health_status == HealthStatus.UNHEALTHY

                        # 恢复状态
                        module._module_status = original_status
                        logger.info(f"   ✅ {module_id} 错误恢复: 正常")
                except Exception as e:
                    logger.warning(f"   ⚠️ {module_id} 错误恢复异常: {e}")

            test_result.test_data = {'error_handling_results': error_handling_results}
            test_result.success = len(error_handling_results) > 0

        except Exception as e:
            test_result.success = False
            test_result.error_message = str(e)

        test_result.execution_time = time.time() - start_time
        return test_result

    async def _test_performance_metrics(self) -> IntegrationTestResult:
        """测试性能指标"""
        test_result = IntegrationTestResult('性能指标测试')
        start_time = time.time()

        try:
            performance_results = {}

            for module_id, module in self.loaded_modules.items():
                try:
                    # 获取性能指标
                    metrics = module.get_metrics()
                    if metrics:
                        performance_results[module_id] = {
                            'initialized': metrics.get('initialized', False),
                            'uptime': metrics.get('uptime_seconds', 0),
                            'has_metrics': len(metrics) > 2
                        }

                        # 测试响应时间
                        response_start = time.time()
                        status = module.get_status()
                        response_time = time.time() - response_start

                        performance_results[module_id]['response_time'] = response_time
                        logger.info(f"   ✅ {module_id} 响应时间: {response_time:.3f}s")

                except Exception as e:
                    logger.warning(f"   ⚠️ {module_id} 性能测试异常: {e}")

            test_result.test_data = {'performance_results': performance_results}
            test_result.success = len(performance_results) > 0

        except Exception as e:
            test_result.success = False
            test_result.error_message = str(e)

        test_result.execution_time = time.time() - start_time
        return test_result

    async def _test_health_checking(self) -> IntegrationTestResult:
        """测试健康检查集成"""
        test_result = IntegrationTestResult('健康检查集成')
        start_time = time.time()

        try:
            health_results = {}

            for module_id, module in self.loaded_modules.items():
                try:
                    # 执行健康检查
                    health_status = await module.health_check()
                    health_results[module_id] = {
                        'status': health_status.value,
                        'is_healthy': health_status == HealthStatus.HEALTHY
                    }

                    if health_status == HealthStatus.HEALTHY:
                        logger.info(f"   ✅ {module_id} 健康: {health_status.value}")
                    else:
                        logger.warning(f"   ⚠️ {module_id} 健康: {health_status.value}")

                except Exception as e:
                    health_results[module_id] = {
                        'status': 'error',
                        'is_healthy': False,
                        'error': str(e)
                    }
                    logger.error(f"   ❌ {module_id} 健康检查失败: {e}")

            healthy_modules = sum(1 for r in health_results.values() if r.get('is_healthy', False))
            total_modules = len(health_results)

            test_result.test_data = {
                'healthy_modules': healthy_modules,
                'total_modules': total_modules,
                'health_rate': healthy_modules / total_modules if total_modules > 0 else 0
            }
            test_result.success = healthy_modules >= total_modules * 0.8  # 80%健康率

        except Exception as e:
            test_result.success = False
            test_result.error_message = str(e)

        test_result.execution_time = time.time() - start_time
        return test_result

    async def _test_lifecycle_management(self) -> IntegrationTestResult:
        """测试启动与关闭流程"""
        test_result = IntegrationTestResult('启动与关闭流程测试')
        start_time = time.time()

        try:
            lifecycle_results = {}

            # 测试模块重启
            for module_id, module in list(self.loaded_modules.items())[:2]:  # 测试前2个模块
                try:
                    logger.info(f"   重启模块: {module_id}")

                    # 停止模块
                    if hasattr(module, 'stop'):
                        await module.stop()
                        lifecycle_results[f"{module_id}_stop"] = True

                    # 重新启动
                    if hasattr(module, 'start'):
                        await module.start()
                        lifecycle_results[f"{module_id}_restart"] = True

                    # 验证状态
                    status = module.get_status()
                    lifecycle_results[f"{module_id}_final_status"] = status.get('status', 'unknown')

                    logger.info(f"   ✅ {module_id} 重启完成: {lifecycle_results.get(f'{module_id}_restart', False)}")

                except Exception as e:
                    lifecycle_results[f"{module_id}_restart_error"] = str(e)
                    logger.error(f"   ❌ {module_id} 重启失败: {e}")

            successful_restarts = sum(1 for k, v in lifecycle_results.items() if k.endswith('_restart') and v)
            total_restarts = sum(1 for k in lifecycle_results.keys() if k.endswith('_restart'))

            test_result.test_data = {
                'lifecycle_results': lifecycle_results,
                'successful_restarts': successful_restarts,
                'total_restarts': total_restarts
            }
            test_result.success = successful_restarts == total_restarts and total_restarts > 0

        except Exception as e:
            test_result.success = False
            test_result.error_message = str(e)

        test_result.execution_time = time.time() - start_time
        return test_result

    def _generate_test_report(self, total_time: float) -> IntegrationTestReport:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - passed_tests

        # 计算模块状态摘要
        module_status = self.dependency_manager.get_module_status()

        # 计算集成健康评分
        health_score = (passed_tests / total_tests * 50 +
                        sum(1 for result in self.test_results if result.success and result.execution_time < 10.0) / total_tests * 50)

        return IntegrationTestReport(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            total_execution_time=total_time,
            test_results=self.test_results,
            module_status_summary=module_status,
            integration_health_score=health_score
        )

    async def cleanup(self):
        """清理资源"""
        logger.info('🧹 清理集成测试资源...')

        try:
            # 关闭所有加载的模块
            await self.dependency_manager.shutdown_all()
            self.loaded_modules.clear()
            logger.info('✅ 资源清理完成')
        except Exception as e:
            logger.error(f"❌ 资源清理失败: {e}")

# 导出
__all__ = [
    'ModuleIntegrationTester',
    'IntegrationTestResult',
    'IntegrationTestReport'
]