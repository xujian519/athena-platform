#!/usr/bin/env python3
"""
增强版专利执行器单元测试
Unit Tests for Enhanced Patent Executors

测试覆盖:
- PatentTask数据类
- ExecutionResult数据类
- 各个执行器的功能测试
- 边界条件和异常处理

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Any

import pytest

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from patent_executors_enhanced import (
    AnalysisType,
    ExecutionResult,
    ExecutorConfig,
    FilingType,
    MonitoringType,
    PatentAnalysisExecutor,
    PatentExecutorFactory,
    PatentFilingExecutor,
    PatentMonitoringExecutor,
    PatentTask,
    PatentValidationExecutor,
    TaskPriority,
    TaskStatus,
)

# =============================================================================
# 测试数据生成器
# =============================================================================

class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def get_sample_patent_data() -> dict[str, Any]:
        """获取示例专利数据"""
        return {
            'patent_id': 'CN202410001234.5',
            'title': '基于深度学习的智能图像识别系统及方法',
            'abstract': '本发明公开了一种基于深度学习的智能图像识别系统，包括图像预处理模块、特征提取模块、分类模块和输出模块。该系统具有高精度、实时性强的特点。',
            'claims': '1. 一种基于深度学习的智能图像识别系统，其特征在于，包括：图像预处理模块，用于对输入图像进行标准化处理；特征提取模块，使用卷积神经网络提取图像特征；分类模块，通过全连接层实现图像分类；输出模块，生成分类结果和置信度。',
            'description': '本发明涉及人工智能技术领域，具体涉及一种基于深度学习的图像识别方法...',
            'technical_problem': '现有图像识别技术精度低、实时性差',
            'technical_solution': '采用改进的卷积神经网络结构',
            'beneficial_effects': '提高了识别精度和处理速度'
        }

    @staticmethod
    def get_sample_analysis_task() -> PatentTask:
        """获取示例分析任务"""
        return PatentTask(
            id='test_analysis_001',
            task_type='patent_analysis',
            parameters={
                'patent_data': TestDataGenerator.get_sample_patent_data(),
                'analysis_type': 'novelty',
                'depth': 'standard'
            },
            priority=TaskPriority.NORMAL
        )

    @staticmethod
    def get_sample_filing_task() -> PatentTask:
        """获取示例申请任务"""
        return PatentTask(
            id='test_filing_001',
            task_type='patent_filing',
            parameters={
                'patent_data': TestDataGenerator.get_sample_patent_data(),
                'filing_type': 'utility_model',
                'jurisdiction': 'CN'
            }
        )

    @staticmethod
    def get_sample_monitoring_task() -> PatentTask:
        """获取示例监控任务"""
        return PatentTask(
            id='test_monitoring_001',
            task_type='patent_monitoring',
            parameters={
                'patent_ids': ['CN202410001234.5', 'CN202410001235.2'],
                'monitoring_type': 'legal_status',
                'frequency': 'weekly'
            }
        )

    @staticmethod
    def get_sample_validation_task() -> PatentTask:
        """获取示例验证任务"""
        return PatentTask(
            id='test_validation_001',
            task_type='patent_validation',
            parameters={
                'patent_data': TestDataGenerator.get_sample_patent_data(),
                'validation_scope': 'comprehensive'
            }
        )


# =============================================================================
# PatentTask数据类测试
# =============================================================================

class TestPatentTask:
    """PatentTask数据类测试"""

    def test_initialization(self):
        """测试初始化"""
        task = PatentTask(
            id='test_001',
            task_type='patent_analysis',
            parameters={'test': 'data'}
        )

        assert task.id == 'test_001'
        assert task.task_type == 'patent_analysis'
        assert task.parameters == {'test': 'data'}
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL
        assert task.retry_count == 0
        assert isinstance(task.created_at, datetime)
        assert task.started_at is None
        assert task.completed_at is None

    def test_to_dict(self):
        """测试转换为字典"""
        task = PatentTask(
            id='test_002',
            task_type='patent_filing',
            parameters={'key': 'value'},
            priority=TaskPriority.HIGH
        )

        task_dict = task.to_dict()

        assert task_dict['id'] == 'test_002'
        assert task_dict['task_type'] == 'patent_filing'
        assert task_dict['priority'] == TaskPriority.HIGH.value
        assert task_dict['status'] == TaskStatus.PENDING.value
        assert isinstance(task_dict['created_at'], str)

    def test_from_dict(self):
        """测试从字典创建"""
        task_dict = {
            'id': 'test_003',
            'task_type': 'patent_analysis',
            'parameters': {'test': 'data'},
            'priority': 8,
            'status': 'running',
            'created_at': '2025-12-14T10:00:00',
            'retry_count': 1
        }

        task = PatentTask.from_dict(task_dict)

        assert task.id == 'test_003'
        assert task.task_type == 'patent_analysis'
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.RUNNING
        assert task.retry_count == 1


# =============================================================================
# ExecutionResult数据类测试
# =============================================================================

class TestExecutionResult:
    """ExecutionResult数据类测试"""

    def test_initialization(self):
        """测试初始化"""
        result = ExecutionResult(
            status='success',
            data={'key': 'value'},
            execution_time=1.5
        )

        assert result.status == 'success'
        assert result.data == {'key': 'value'}
        assert result.execution_time == 1.5
        assert result.error is None
        assert result.confidence == 0.0

    def test_is_success(self):
        """测试is_success方法"""
        success_result = ExecutionResult(status='success')
        failed_result = ExecutionResult(status='failed')

        assert success_result.is_success() is True
        assert failed_result.is_success() is False

    def test_is_failed(self):
        """测试is_failed方法"""
        failed_result = ExecutionResult(status='failed')
        success_result = ExecutionResult(status='success')

        assert failed_result.is_failed() is True
        assert success_result.is_failed() is False

    def test_to_dict(self):
        """测试转换为字典"""
        result = ExecutionResult(
            status='success',
            data={'test': 'data'},
            task_id='task_001',
            confidence=0.85,
            warnings=['warning1', 'warning2']
        )

        result_dict = result.to_dict()

        assert result_dict['status'] == 'success'
        assert result_dict['data'] == {'test': 'data'}
        assert result_dict['task_id'] == 'task_001'
        assert result_dict['confidence'] == 0.85
        assert len(result_dict['warnings']) == 2


# =============================================================================
# ExecutorConfig测试
# =============================================================================

class TestExecutorConfig:
    """ExecutorConfig测试"""

    def test_default_values(self):
        """测试默认值"""
        config = ExecutorConfig()

        assert config.ai_provider == 'openai'
        assert config.ai_model == 'gpt-4'
        assert config.pg_host == 'localhost'
        assert config.pg_port == 5432
        assert config.redis_host == 'localhost'
        assert config.redis_port == 6379
        assert config.enable_cache is True
        assert config.cache_ttl == 300

    def test_custom_values(self):
        """测试自定义值"""
        os.environ['AI_PROVIDER'] = 'anthropic'
        os.environ['PG_HOST'] = '192.168.1.100'

        config = ExecutorConfig()

        assert config.ai_provider == 'anthropic'
        assert config.pg_host == '192.168.1.100'

        # 清理环境变量
        del os.environ['AI_PROVIDER']
        del os.environ['PG_HOST']


# =============================================================================
# PatentAnalysisExecutor测试
# =============================================================================

class TestPatentAnalysisExecutor:
    """PatentAnalysisExecutor测试"""

    @pytest.fixture
    def executor(self):
        """创建执行器实例"""
        return PatentAnalysisExecutor()

    @pytest.fixture
    def valid_task(self):
        """创建有效的分析任务"""
        return TestDataGenerator.get_sample_analysis_task()

    def test_initialization(self, executor):
        """测试初始化"""
        assert executor.name == 'PatentAnalysisExecutor'
        assert executor.description == '专利分析执行器（增强版）'
        assert len(executor.analysis_configs) == 6

    def test_validate_parameters_valid(self, executor, valid_task):
        """测试参数验证 - 有效参数"""
        is_valid, error_msg = executor.validate_parameters(valid_task.parameters)

        assert is_valid is True
        assert error_msg is None

    def test_validate_parameters_missing_patent_data(self, executor):
        """测试参数验证 - 缺少patent_data"""
        is_valid, error_msg = executor.validate_parameters({})

        assert is_valid is False
        assert 'patent_data' in error_msg

    def test_validate_parameters_invalid_analysis_type(self, executor):
        """测试参数验证 - 无效分析类型"""
        parameters = {
            'patent_data': TestDataGenerator.get_sample_patent_data(),
            'analysis_type': 'invalid_type'
        }

        is_valid, error_msg = executor.validate_parameters(parameters)

        assert is_valid is False
        assert 'analysis_type' in error_msg

    @pytest.mark.asyncio
    async def test_execute_success(self, executor, valid_task):
        """测试执行 - 成功"""
        result = await executor.execute(valid_task)

        assert result.is_success()
        assert result.status == 'success'
        assert result.execution_time > 0
        assert result.data is not None
        assert 'analysis_result' in result.data
        assert 'report' in result.data
        assert 'recommendations' in result.data
        assert valid_task.status == TaskStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_execute_failure_invalid_parameters(self, executor):
        """测试执行 - 参数验证失败"""
        invalid_task = PatentTask(
            id='test_invalid',
            task_type='patent_analysis',
            parameters={}
        )

        result = await executor.execute(invalid_task)

        assert result.is_failed()
        assert '参数验证失败' in result.error
        assert invalid_task.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_cache_functionality(self, executor, valid_task):
        """测试缓存功能"""
        # 第一次执行
        result1 = await executor.execute(valid_task)
        assert result1.metadata.get('cached') is False

        # 第二次执行（应该使用缓存）
        result2 = await executor.execute(valid_task)
        assert result2.metadata.get('cached') is True
        assert result2.execution_time < result1.execution_time

    @pytest.mark.asyncio
    async def test_different_analysis_types(self, executor):
        """测试不同分析类型"""
        analysis_types = [
            AnalysisType.NOVELTY,
            AnalysisType.INVENTIVENESS,
            AnalysisType.COMPREHENSIVE,
            AnalysisType.TECHNICAL_ANALYSIS
        ]

        for analysis_type in analysis_types:
            task = PatentTask(
                id=f'test_{analysis_type.value}',
                task_type='patent_analysis',
                parameters={
                    'patent_data': TestDataGenerator.get_sample_patent_data(),
                    'analysis_type': analysis_type.value
                }
            )

            result = await executor.execute(task)
            assert result.is_success()
            assert result.data['analysis_type'] == analysis_type.value


# =============================================================================
# PatentFilingExecutor测试
# =============================================================================

class TestPatentFilingExecutor:
    """PatentFilingExecutor测试"""

    @pytest.fixture
    def executor(self):
        """创建执行器实例"""
        return PatentFilingExecutor()

    @pytest.fixture
    def valid_task(self):
        """创建有效的申请任务"""
        return TestDataGenerator.get_sample_filing_task()

    def test_initialization(self, executor):
        """测试初始化"""
        assert executor.name == 'PatentFilingExecutor'
        assert len(executor.filing_configs) == 3

    def test_validate_parameters_valid(self, executor, valid_task):
        """测试参数验证 - 有效参数"""
        is_valid, error_msg = executor.validate_parameters(valid_task.parameters)

        assert is_valid is True
        assert error_msg is None

    def test_validate_parameters_missing_required_fields(self, executor):
        """测试参数验证 - 缺少必需字段"""
        is_valid, error_msg = executor.validate_parameters({})

        assert is_valid is False
        assert error_msg is not None

    def test_validate_parameters_invalid_filing_type(self, executor):
        """测试参数验证 - 无效申请类型"""
        parameters = {
            'patent_data': TestDataGenerator.get_sample_patent_data(),
            'filing_type': 'invalid_type',
            'jurisdiction': 'CN'
        }

        is_valid, error_msg = executor.validate_parameters(parameters)

        assert is_valid is False
        assert 'filing_type' in error_msg

    @pytest.mark.asyncio
    async def test_execute_success(self, executor, valid_task):
        """测试执行 - 成功"""
        result = await executor.execute(valid_task)

        assert result.is_success()
        assert result.data is not None
        assert 'application_number' in result.data
        assert 'documents' in result.data
        assert 'fees' in result.data
        assert result.data['application_number'].startswith('2025')

    @pytest.mark.asyncio
    async def test_different_filing_types(self, executor):
        """测试不同申请类型"""
        filing_types = [
            FilingType.INVENTION_PATENT,
            FilingType.UTILITY_MODEL,
            FilingType.DESIGN_PATENT
        ]

        for filing_type in filing_types:
            task = PatentTask(
                id=f'test_{filing_type.value}',
                task_type='patent_filing',
                parameters={
                    'patent_data': TestDataGenerator.get_sample_patent_data(),
                    'filing_type': filing_type.value,
                    'jurisdiction': 'CN'
                }
            )

            result = await executor.execute(task)
            assert result.is_success()
            assert result.data['filing_type'] == filing_type.value


# =============================================================================
# PatentMonitoringExecutor测试
# =============================================================================

class TestPatentMonitoringExecutor:
    """PatentMonitoringExecutor测试"""

    @pytest.fixture
    def executor(self):
        """创建执行器实例"""
        return PatentMonitoringExecutor()

    @pytest.fixture
    def valid_task(self):
        """创建有效的监控任务"""
        return TestDataGenerator.get_sample_monitoring_task()

    def test_initialization(self, executor):
        """测试初始化"""
        assert executor.name == 'PatentMonitoringExecutor'
        assert len(executor.monitoring_tasks) == 0

    def test_validate_parameters_valid(self, executor, valid_task):
        """测试参数验证 - 有效参数"""
        is_valid, error_msg = executor.validate_parameters(valid_task.parameters)

        assert is_valid is True
        assert error_msg is None

    def test_validate_parameters_empty_patent_ids(self, executor):
        """测试参数验证 - 空专利列表"""
        parameters = {
            'patent_ids': [],
            'monitoring_type': 'legal_status'
        }

        is_valid, error_msg = executor.validate_parameters(parameters)

        assert is_valid is False
        assert '不能为空' in error_msg

    @pytest.mark.asyncio
    async def test_execute_success(self, executor, valid_task):
        """测试执行 - 成功"""
        result = await executor.execute(valid_task)

        assert result.is_success()
        assert result.data is not None
        assert 'monitoring_id' in result.data
        assert 'initial_check' in result.data
        assert 'next_check' in result.data
        assert len(executor.monitoring_tasks) == 1

    @pytest.mark.asyncio
    async def test_different_monitoring_types(self, executor):
        """测试不同监控类型"""
        monitoring_types = [
            MonitoringType.LEGAL_STATUS,
            MonitoringType.INFRINGEMENT,
            MonitoringType.COMPETITOR
        ]

        for monitoring_type in monitoring_types:
            task = PatentTask(
                id=f'test_{monitoring_type.value}',
                task_type='patent_monitoring',
                parameters={
                    'patent_ids': ['CN202410001234.5'],
                    'monitoring_type': monitoring_type.value,
                    'frequency': 'weekly'
                }
            )

            result = await executor.execute(task)
            assert result.is_success()
            assert result.data['monitoring_type'] == monitoring_type.value


# =============================================================================
# PatentValidationExecutor测试
# =============================================================================

class TestPatentValidationExecutor:
    """PatentValidationExecutor测试"""

    @pytest.fixture
    def executor(self):
        """创建执行器实例"""
        return PatentValidationExecutor()

    @pytest.fixture
    def valid_task(self):
        """创建有效的验证任务"""
        return TestDataGenerator.get_sample_validation_task()

    def test_initialization(self, executor):
        """测试初始化"""
        assert executor.name == 'PatentValidationExecutor'

    def test_validate_parameters_valid(self, executor, valid_task):
        """测试参数验证 - 有效参数"""
        is_valid, error_msg = executor.validate_parameters(valid_task.parameters)

        assert is_valid is True

    def test_validate_parameters_missing_patent_data(self, executor):
        """测试参数验证 - 缺少patent_data"""
        is_valid, error_msg = executor.validate_parameters({})

        assert is_valid is False
        assert 'patent_data' in error_msg

    @pytest.mark.asyncio
    async def test_execute_success(self, executor, valid_task):
        """测试执行 - 成功"""
        result = await executor.execute(valid_task)

        assert result.is_success()
        assert result.data is not None
        assert 'validation_results' in result.data
        assert 'overall_validity' in result.data
        assert result.confidence >= 0.0

    @pytest.mark.asyncio
    async def test_validation_checks(self, executor):
        """测试各种验证检查"""
        task = TestDataGenerator.get_sample_validation_task()
        result = await executor.execute(task)

        validation_results = result.data['validation_results']

        # 检查各个验证项
        assert 'formality_check' in validation_results
        assert 'technical_validation' in validation_results
        assert 'legal_compliance' in validation_results

        # 检查状态
        for _check_name, check_result in validation_results.items():
            assert 'status' in check_result
            assert check_result['status'] in ['passed', 'warning', 'failed']


# =============================================================================
# PatentExecutorFactory测试
# =============================================================================

class TestPatentExecutorFactory:
    """PatentExecutorFactory测试"""

    @pytest.fixture
    def factory(self):
        """创建工厂实例"""
        return PatentExecutorFactory()

    def test_initialization(self, factory):
        """测试初始化"""
        assert len(factory.executors) == 4
        assert len(factory.aliases) > 0

    def test_list_executors(self, factory):
        """测试列出执行器"""
        executors = factory.list_executors()

        assert 'patent_analysis' in executors
        assert 'patent_filing' in executors
        assert 'patent_monitoring' in executors
        assert 'patent_validation' in executors

        for _name, info in executors.items():
            assert 'name' in info
            assert 'description' in info
            assert 'class' in info

    def test_get_executor(self, factory):
        """测试获取执行器"""
        # 直接获取
        executor1 = factory.get_executor('patent_analysis')
        assert executor1 is not None
        assert isinstance(executor1, PatentAnalysisExecutor)

        # 通过别名获取
        executor2 = factory.get_executor('analysis')
        assert executor2 is not None
        assert isinstance(executor2, PatentAnalysisExecutor)

        # 获取不存在的执行器
        executor3 = factory.get_executor('non_existent')
        assert executor3 is None

    def test_register_executor(self, factory):
        """测试注册新执行器"""
        initial_count = len(factory.executors)

        # 创建自定义执行器
        from patent_executors_enhanced import BasePatentExecutor

        class CustomExecutor(BasePatentExecutor):
            async def execute(self, task):
                return ExecutionResult(status='success')

            def validate_parameters(self, parameters):
                return True, None

        custom_executor = CustomExecutor('custom', '自定义执行器')
        factory.register_executor('custom', custom_executor)

        assert len(factory.executors) == initial_count + 1
        assert factory.get_executor('custom') is not None

    @pytest.mark.asyncio
    async def test_execute_with_executor(self, factory):
        """测试通过工厂执行任务"""
        task = TestDataGenerator.get_sample_analysis_task()

        result = await factory.execute_with_executor('patent_analysis', task)

        assert result.is_success()
        assert result.task_id == task.id

    @pytest.mark.asyncio
    async def test_execute_with_invalid_executor(self, factory):
        """测试使用无效执行器执行"""
        task = TestDataGenerator.get_sample_analysis_task()

        result = await factory.execute_with_executor('invalid_executor', task)

        assert result.is_failed()
        assert '未找到执行器' in result.error

    def test_get_statistics(self, factory):
        """测试获取统计信息"""
        stats = factory.get_statistics()

        assert 'total_executors' in stats
        assert 'executor_names' in stats
        assert 'aliases_count' in stats
        assert 'config_valid' in stats

        assert stats['total_executors'] == 4
        assert len(stats['executor_names']) == 4


# =============================================================================
# 集成测试
# =============================================================================

class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """测试完整工作流"""
        factory = PatentExecutorFactory()

        # 1. 专利分析
        analysis_task = TestDataGenerator.get_sample_analysis_task()
        analysis_result = await factory.execute_with_executor(
            'patent_analysis', analysis_task
        )
        assert analysis_result.is_success()

        # 2. 专利验证
        validation_task = TestDataGenerator.get_sample_validation_task()
        validation_result = await factory.execute_with_executor(
            'patent_validation', validation_task
        )
        assert validation_result.is_success()

        # 3. 专利申请
        filing_task = TestDataGenerator.get_sample_filing_task()
        filing_result = await factory.execute_with_executor(
            'patent_filing', filing_task
        )
        assert filing_result.is_success()

        # 4. 专利监控
        monitoring_task = TestDataGenerator.get_sample_monitoring_task()
        monitoring_result = await factory.execute_with_executor(
            'patent_monitoring', monitoring_task
        )
        assert monitoring_result.is_success()

    @pytest.mark.asyncio
    async def test_concurrent_execution(self):
        """测试并发执行"""
        factory = PatentExecutorFactory()

        # 创建多个任务
        tasks = [
            TestDataGenerator.get_sample_analysis_task(),
            TestDataGenerator.get_sample_validation_task(),
            TestDataGenerator.get_sample_filing_task()
        ]

        # 并发执行
        results = await asyncio.gather(*[
            factory.execute_with_executor('patent_analysis', tasks[0]),
            factory.execute_with_executor('patent_validation', tasks[1]),
            factory.execute_with_executor('patent_filing', tasks[2])
        ])

        # 验证所有结果
        for result in results:
            assert result.is_success()

    @pytest.mark.asyncio
    async def test_task_retry_mechanism(self):
        """测试任务重试机制"""
        executor = PatentAnalysisExecutor()

        # 创建一个会失败的任务（通过空参数）
        failing_task = PatentTask(
            id='test_retry',
            task_type='patent_analysis',
            parameters={}
        )
        failing_task.max_retries = 2

        result = await executor.execute(failing_task)

        assert result.is_failed()
        assert failing_task.retry_count > 0

    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """测试缓存性能"""
        executor = PatentAnalysisExecutor()
        task = TestDataGenerator.get_sample_analysis_task()

        # 第一次执行
        import time
        start1 = time.time()
        result1 = await executor.execute(task)
        time1 = time.time() - start1

        # 第二次执行（使用缓存）
        start2 = time.time()
        result2 = await executor.execute(task)
        time2 = time.time() - start2

        # 第二次应该更快
        assert time2 < time1
        assert result1.data == result2.data


# =============================================================================
# 运行测试的主函数
# =============================================================================

if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])
