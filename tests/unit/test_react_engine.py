#!/usr/bin/env python3
"""
ReAct引擎单元测试
Unit tests for ReAct (Reasoning + Acting) Engine

测试目标：验证ReAct引擎的核心功能，包括：
- Thought-Action-Observation循环
- 工具调用
- 最大迭代限制
- 任务求解
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestReActEngineBasic:
    """ReAct引擎基础功能测试"""

    @pytest.mark.asyncio
    async def test_react_engine_initialization(self):
        """测试ReAct引擎初始化"""
        from core.xiaonuo_agent.reasoning.react_engine import ReActEngine

        engine = ReActEngine()

        assert engine is not None
        assert hasattr(engine, 'solve')
        assert hasattr(engine, 'max_iterations')
        assert engine.max_iterations > 0

    @pytest.mark.asyncio
    async def test_react_solve_simple_task(self):
        """测试ReAct解决简单任务"""
        from core.xiaonuo_agent.reasoning.react_engine import ReActEngine

        engine = ReActEngine(max_iterations=5)

        # 模拟简单任务
        result = await engine.solve(
            task="查询专利US8302089的基本信息",
            context={}
        )

        # 验证结果结构
        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'final_answer') or hasattr(result, 'answer')

    @pytest.mark.asyncio
    async def test_react_thought_action_observation_loop(self):
        """测试Thought-Action-Observation循环"""
        from core.xiaonuo_agent.reasoning.react_engine import ReActEngine

        engine = ReActEngine()

        result = await engine.solve(
            task="分析一个专利的有效性",
            context={"patent_number": "US8302089"}
        )

        # 验证推理循环产生的内容
        # ReAct引擎应该产生思考、行动和观察
        assert result is not None

        # 检查是否有推理过程（通过iterations或steps属性）
        if hasattr(result, 'iterations'):
            assert result.iterations >= 1
        if hasattr(result, 'steps'):
            assert len(result.steps) >= 1


class TestReActEngineWithTools:
    """ReAct引擎工具调用测试"""

    @pytest.mark.asyncio
    async def test_react_with_mock_tools(self):
        """测试ReAct使用模拟工具"""
        from core.xiaonuo_agent.reasoning.react_engine import ReActEngine

        # 创建模拟工具
        mock_search_tool = AsyncMock(return_value={"results": ["专利1", "专利2"]})
        mock_analyze_tool = AsyncMock(return_value={"validity": 0.85})

        tools = {
            "search": mock_search_tool,
            "analyze": mock_analyze_tool
        }

        engine = ReActEngine(tools=tools)

        result = await engine.solve(
            task="搜索并分析专利",
            context={}
        )

        assert result is not None
        # 验证工具可能被调用（取决于ReAct的实现）

    @pytest.mark.asyncio
    async def test_react_tool_selection(self):
        """测试ReAct工具选择逻辑"""
        from core.xiaonuo_agent.reasoning.react_engine import ReActEngine

        # 为不同任务类型准备不同的工具
        tools = {
            "patent_search": AsyncMock(return_value=["patent1", "patent2"]),
            "legal_analysis": AsyncMock(return_value={"analysis": "valid"}),
            "web_search": AsyncMock(return_value=["result1", "result2"])
        }

        engine = ReActEngine(tools=tools)

        # 执行专利搜索任务
        result = await engine.solve(
            task="搜索人工智能相关专利",
            context={}
        )

        assert result is not None


class TestReActEngineConstraints:
    """ReAct引擎约束条件测试"""

    @pytest.mark.asyncio
    async def test_react_max_iterations(self):
        """测试最大迭代次数限制"""
        from core.xiaonuo_agent.reasoning.react_engine import ReActEngine

        # 设置较小的最大迭代次数
        max_iter = 3
        engine = ReActEngine(max_iterations=max_iter)

        # 执行一个可能需要多轮迭代的复杂任务
        result = await engine.solve(
            task="进行复杂的专利分析",
            context={}
        )

        # 验证迭代次数不超过限制
        if hasattr(result, 'iterations'):
            assert result.iterations <= max_iter
        if hasattr(result, 'steps'):
            assert len(result.steps) <= max_iter

    @pytest.mark.asyncio
    async def test_react_timeout_handling(self):
        """测试超时处理"""
        from core.xiaonuo_agent.reasoning.react_engine import ReActEngine

        engine = ReActEngine(timeout=2)  # 2秒超时

        # 执行任务（实际实现中可能需要mock耗时操作）
        result = await engine.solve(
            task="快速查询",
            context={}
        )

        # 任务应该在超时前完成或返回超时状态
        assert result is not None


class TestReActEngineErrorHandling:
    """ReAct引擎错误处理测试"""

    @pytest.mark.asyncio
    async def test_react_empty_task(self):
        """测试空任务处理"""
        from core.xiaonuo_agent.reasoning.react_engine import ReActEngine

        engine = ReActEngine()

        # 空任务应该优雅处理
        result = await engine.solve(task="", context={})

        assert result is not None
        # 可能返回失败状态或默认响应

    @pytest.mark.asyncio
    async def test_react_invalid_context(self):
        """测试无效上下文处理"""
        from core.xiaonuo_agent.reasoning.react_engine import ReActEngine

        engine = ReActEngine()

        # 无效上下文应该优雅处理
        result = await engine.solve(
            task="查询专利",
            context=None  # 无效上下文
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_react_tool_failure(self):
        """测试工具失败处理"""
        from core.xiaonuo_agent.reasoning.react_engine import ReActEngine

        # 创建会失败的工具
        failing_tool = AsyncMock(side_effect=Exception("工具执行失败"))

        tools = {"failing_tool": failing_tool}
        engine = ReActEngine(tools=tools)

        result = await engine.solve(
            task="使用失败工具",
            context={}
        )

        # ReAct引擎应该处理工具失败并继续或优雅降级
        assert result is not None


class TestReActEngineIntegration:
    """ReAct引擎集成测试"""

    @pytest.mark.asyncio
    async def test_react_with_llm_integration(self):
        """测试ReAct与LLM的集成"""
        from core.xiaonuo_agent.reasoning.react_engine import ReActEngine

        # 这个测试需要实际的LLM集成
        # 在实际环境中可能需要mock或使用测试LLM
        engine = ReActEngine()

        result = await engine.solve(
            task="简单查询：今天天气如何？",
            context={}
        )

        assert result is not None
        assert hasattr(result, 'final_answer') or hasattr(result, 'answer')

    @pytest.mark.asyncio
    async def test_react_multi_step_reasoning(self):
        """测试多步推理能力"""
        from core.xiaonuo_agent.reasoning.react_engine import ReActEngine

        engine = ReActEngine(max_iterations=5)

        # 多步任务：搜索 → 分析 → 总结
        result = await engine.solve(
            task="搜索AI专利，分析技术趋势，并总结关键发现",
            context={}
        )

        assert result is not None
        # 验证多步推理过程
        if hasattr(result, 'steps'):
            assert len(result.steps) >= 1


# 运行测试的辅助函数
def run_react_tests():
    """运行ReAct引擎测试"""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_react_tests()
