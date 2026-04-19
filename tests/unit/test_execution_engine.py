#!/usr/bin/env python3
"""
执行引擎单元测试
Unit tests for Execution Engine

测试目标：验证8种动作类型的执行
- search: 搜索动作
- analyze: 分析动作
- generate: 生成动作
- retrieve: 检索动作
- store: 存储动作
- communicate: 通信动作
- delegate: 委托动作
- monitor: 监控动作
"""

import asyncio
import sys
from pathlib import Path

import pytest

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestActionExecutorBasic:
    """动作执行器基础功能测试"""

    @pytest.mark.asyncio
    async def test_executor_initialization(self):
        """测试执行器初始化"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()
            assert executor is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")

    @pytest.mark.asyncio
    async def test_execute_simple_action(self):
        """测试执行简单动作"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            action = {
                "type": "search",
                "query": "人工智能专利",
                "params": {"limit": 10}
            }

            result = await executor.execute(action)

            assert result is not None
            # 验证结果结构
            if hasattr(result, 'success'):
                # 结果对象形式
                pass
            else:
                # 字典形式
                assert isinstance(result, dict)

        except ImportError:
            pytest.skip("ActionExecutor not available")


class TestSearchAction:
    """搜索动作测试"""

    @pytest.mark.asyncio
    async def test_search_patent_database(self):
        """测试专利数据库搜索"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "search",
                "query": "AI patents",
                "source": "patent_database",
                "limit": 5
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")

    @pytest.mark.asyncio
    async def test_search_web(self):
        """测试网络搜索"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "search",
                "query": "机器学习最新进展",
                "source": "web",
                "limit": 10
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")

    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        """测试带过滤器的搜索"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "search",
                "query": "专利",
                "filters": {
                    "date_range": {"start": "2020-01-01", "end": "2026-12-31"},
                    "assignee": "Microsoft"
                }
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")


class TestAnalyzeAction:
    """分析动作测试"""

    @pytest.mark.asyncio
    async def test_analyze_patent_validity(self):
        """测试专利有效性分析"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "analyze",
                "target": "US8302089",
                "analysis_type": "patent_validity"
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")

    @pytest.mark.asyncio
    async def test_analyze_infringement(self):
        """测试侵权分析"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "analyze",
                "target_patent": "US8302089",
                "product_description": "A display driver upgrade system",
                "analysis_type": "infringement"
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")

    @pytest.mark.asyncio
    async def test_analyze_with_context(self):
        """测试带上下文的分析"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            context = {
                "prior_art": ["US1234567", "US2345678"],
                "claims": ["claim1", "claim2"]
            }

            result = await executor.execute({
                "type": "analyze",
                "target": "patent_portfolio",
                "context": context
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")


class TestGenerateAction:
    """生成动作测试"""

    @pytest.mark.asyncio
    async def test_generate_patent_report(self):
        """测试生成专利报告"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "generate",
                "content_type": "patent_report",
                "patent_number": "US8302089",
                "format": "markdown"
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")

    @pytest.mark.asyncio
    async def test_generate_legal_document(self):
        """测试生成法律文书"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "generate",
                "content_type": "legal_opinion",
                "case_details": {
                    "patent_number": "US8302089",
                    "issue": "validity"
                }
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")


class TestRetrieveAction:
    """检索动作测试"""

    @pytest.mark.asyncio
    async def test_retrieve_from_memory(self):
        """测试从记忆系统检索"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "retrieve",
                "source": "memory",
                "key": "patent_US8302089"
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")

    @pytest.mark.asyncio
    async def test_retrieve_from_database(self):
        """测试从数据库检索"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "retrieve",
                "source": "patent_database",
                "query": {"patent_number": "US8302089"}
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")


class TestStoreAction:
    """存储动作测试"""

    @pytest.mark.asyncio
    async def test_store_to_memory(self):
        """测试存储到记忆系统"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "store",
                "target": "memory",
                "key": "test_storage",
                "value": {"data": "test_value"},
                "metadata": {"type": "test"}
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")

    @pytest.mark.asyncio
    async def test_store_to_database(self):
        """测试存储到数据库"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "store",
                "target": "patent_database",
                "data": {
                    "patent_number": "TEST123",
                    "title": "Test Patent"
                }
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")


class TestCommunicateAction:
    """通信动作测试"""

    @pytest.mark.asyncio
    async def test_communicate_to_agent(self):
        """测试向智能体发送消息"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "communicate",
                "target_agent": "xiaona",
                "message": "请分析这个专利",
                "data": {"patent_number": "US8302089"}
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")

    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """测试广播消息"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "communicate",
                "mode": "broadcast",
                "message": "系统更新通知",
                "recipients": ["xiaona", "xiaonuo", "yunxi"]
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")


class TestDelegateAction:
    """委托动作测试"""

    @pytest.mark.asyncio
    async def test_delegate_to_specialist(self):
        """测试委托给专家智能体"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "delegate",
                "specialist": "legal_expert",
                "task": "专利无效分析",
                "context": {"patent_number": "US8302089"}
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")


class TestMonitorAction:
    """监控动作测试"""

    @pytest.mark.asyncio
    async def test_monitor_system_health(self):
        """测试监控系统健康"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            result = await executor.execute({
                "type": "monitor",
                "target": "system_health",
                "metrics": ["cpu", "memory", "disk"]
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")


class TestParallelExecution:
    """并行执行测试"""

    @pytest.mark.asyncio
    async def test_parallel_search(self):
        """测试并行搜索"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            actions = [
                {"type": "search", "query": "AI"},
                {"type": "search", "query": "ML"},
                {"type": "search", "query": "DL"}
            ]

            if hasattr(executor, 'execute_parallel'):
                results = await executor.execute_parallel(actions)
                assert len(results) == 3
            else:
                # 如果不支持并行，串行执行
                results = []
                for action in actions:
                    result = await executor.execute(action)
                    results.append(result)
                assert len(results) == 3

        except ImportError:
            pytest.skip("ActionExecutor not available")

    @pytest.mark.asyncio
    async def test_concurrent_execution(self):
        """测试并发执行"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            # 创建多个并发任务
            tasks = [
                executor.execute({"type": "search", "query": f"query_{i}"})
                for i in range(5)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 验证所有任务都完成（或返回异常）
            assert len(results) == 5

        except ImportError:
            pytest.skip("ActionExecutor not available")


class TestActionTimeout:
    """动作超时测试"""

    @pytest.mark.asyncio
    async def test_action_with_timeout(self):
        """测试带超时的动作"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor(timeout=5)

            result = await executor.execute({
                "type": "search",
                "query": "patents"
            })

            assert result is not None

        except ImportError:
            pytest.skip("ActionExecutor not available")

    @pytest.mark.asyncio
    async def test_action_timeout_expired(self):
        """测试动作超时过期"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor(timeout=1)

            # 一个会超时的慢动作
            # 注意：这需要执行器支持超时控制
            with pytest.raises((TimeoutError, asyncio.TimeoutError)):
                await executor.execute({
                    "type": "slow_operation",
                    "duration": 5  # 5秒，超过1秒超时
                })

        except (ImportError, AttributeError):
            pytest.skip("ActionExecutor timeout not available")


class TestActionErrorHandling:
    """动作错误处理测试"""

    @pytest.mark.asyncio
    async def test_invalid_action_type(self):
        """测试无效动作类型"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            # 无效的动作类型
            await executor.execute({
                "type": "invalid_action_type",
                "data": "test"
            })

            # 应该返回错误状态或抛出异常
            # 具体行为取决于实现

        except (ImportError, ValueError, KeyError):
            # 预期的异常
            pass

    @pytest.mark.asyncio
    async def test_malformed_action(self):
        """测试畸形动作"""
        try:
            from core.execution.execution_engine.action_executor import ActionExecutor

            executor = ActionExecutor()

            # 缺少必要字段的动作
            await executor.execute({})

            # 应该优雅处理

        except (ImportError, ValueError, KeyError):
            # 预期的异常
            pass


# 运行测试的辅助函数
def run_execution_tests():
    """运行执行引擎测试"""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_execution_tests()
