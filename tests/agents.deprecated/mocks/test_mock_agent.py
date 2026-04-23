"""
Mock Agent使用示例和测试

演示如何使用Mock Agent进行各种测试场景。
"""

import asyncio

import pytest
from tests.agents.mocks.mock_agent import (
    ConfigurableMockAgent,
    MockAgent,
    create_delayed_mock,
    create_failure_mock,
    create_success_mock,
)

from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentStatus,
)

# ==================== 示例1: 基本使用 ====================

def test_basic_mock_usage():
    """测试Mock Agent的基本使用"""
    # 创建Mock Agent
    mock = MockAgent(agent_id="test_mock")

    # 验证基本信息
    assert mock.agent_id == "test_mock"
    assert len(mock.get_capabilities()) >= 1
    assert mock.has_capability("mock_capability")

    # 验证get_info
    info = mock.get_info()
    assert info["agent_id"] == "test_mock"
    assert "capabilities" in info


@pytest.mark.asyncio
async def test_mock_execute_success():
    """测试Mock Agent执行成功"""
    mock = create_success_mock(
        agent_id="success_mock",
        result={"test": "result"}
    )

    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"input": "data"},
        config={},
        metadata={},
    )

    result = await mock.execute(context)

    assert result.status == AgentStatus.COMPLETED
    assert result.output_data["test"] == "result"
    assert result.execution_time >= 0


@pytest.mark.asyncio
async def test_mock_execute_failure():
    """测试Mock Agent执行失败"""
    mock = create_failure_mock(
        agent_id="failure_mock",
        error_message="测试错误"
    )

    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"input": "data"},
        config={},
        metadata={},
    )

    result = await mock.execute(context)

    assert result.status == AgentStatus.ERROR
    assert result.error_message == "测试错误"
    assert result.execution_time >= 0


@pytest.mark.asyncio
async def test_mock_execute_delay():
    """测试Mock Agent执行延迟"""
    import time

    mock = create_delayed_mock(
        agent_id="delayed_mock",
        delay=0.5
    )

    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"input": "data"},
        config={},
        metadata={},
    )

    start = time.time()
    result = await mock.execute(context)
    elapsed = time.time() - start

    assert result.status == AgentStatus.COMPLETED
    assert elapsed >= 0.5  # 应该有至少0.5秒的延迟


# ==================== 示例2: 可配置Mock ====================

@pytest.mark.asyncio
async def test_configurable_mock_chain():
    """测试可配置Mock Agent的链式配置"""
    # 使用链式配置创建Mock Agent
    mock = (ConfigurableMockAgent(agent_id="configurable_mock")
            .with_capability("capability1", "能力1", 1.0)
            .with_capability("capability2", "能力2", 2.0)
            .with_delay(0.1)
            .with_result({"custom": "result"}))

    # 验证能力注册（不需要调用_initialize，因为with_capability已经注册）
    capabilities = mock.get_capabilities()
    capability_names = [cap.name for cap in capabilities]
    assert "capability1" in capability_names
    assert "capability2" in capability_names

    # 执行并验证结果
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={},
        config={},
        metadata={},
    )

    result = await mock.execute(context)

    assert result.status == AgentStatus.COMPLETED
    assert result.output_data["custom"] == "result"


# ==================== 示例3: 测试不同场景 ====================

@pytest.mark.asyncio
async def test_mock_with_previous_results():
    """测试Mock Agent处理前序Agent的结果"""
    # 使用默认Mock（不设置预设结果，会返回input_received）
    mock = MockAgent(agent_id="test_mock")

    # 模拟前序Agent的结果
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={
            "user_input": "测试输入",
            "previous_results": {
                "agent1": {
                    "output_data": {"intermediate": "result"}
                }
            }
        },
        config={},
        metadata={},
    )

    result = await mock.execute(context)

    assert result.status == AgentStatus.COMPLETED
    # Mock Agent应该能够返回input_received（默认行为）
    assert "input_received" in result.output_data
    assert "previous_results" in result.output_data["input_received"]


@pytest.mark.asyncio
async def test_mock_with_config():
    """测试Mock Agent使用配置参数"""
    mock = MockAgent(agent_id="test_mock")

    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={
            "test": "data",
            "timeout": 300.0,  # 将config参数放在input_data中以便Mock Agent可以访问
            "model": "kimi-k2.5",
        },
        config={},
        metadata={},
    )

    result = await mock.execute(context)

    assert result.status == AgentStatus.COMPLETED
    # 验证配置被传递到input_received
    assert "input_received" in result.output_data
    assert result.output_data["input_received"]["timeout"] == 300.0


@pytest.mark.asyncio
async def test_mock_with_metadata():
    """测试Mock Agent使用元数据"""
    mock = MockAgent(agent_id="test_mock")

    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={
            "test": "data",
            "priority": "high",  # 将metadata参数放在input_data中
            "user_id": "test_user",
        },
        config={},
        metadata={},
    )

    result = await mock.execute(context)

    assert result.status == AgentStatus.COMPLETED
    # 验证元数据被传递到input_received
    assert "input_received" in result.output_data
    assert result.output_data["input_received"]["priority"] == "high"


# ==================== 示例4: 测试边界情况 ====================

@pytest.mark.asyncio
async def test_mock_with_empty_input():
    """测试Mock Agent处理空输入"""
    mock = create_success_mock()

    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={},
        config={},
        metadata={},
    )

    result = await mock.execute(context)

    assert result.status == AgentStatus.COMPLETED


@pytest.mark.asyncio
async def test_mock_with_large_input():
    """测试Mock Agent处理大量输入"""
    mock = MockAgent(agent_id="test_mock")

    large_data = {"data": "x" * 10000}

    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data=large_data,
        config={},
        metadata={},
    )

    result = await mock.execute(context)

    assert result.status == AgentStatus.COMPLETED
    # 验证大数据被正确传递
    assert "input_received" in result.output_data
    assert len(result.output_data["input_received"]["data"]) == 10000


@pytest.mark.asyncio
async def test_mock_concurrent_execution():
    """测试Mock Agent并发执行"""
    mock = create_delayed_mock(delay=0.5)

    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={},
        config={},
        metadata={},
    )

    # 并发执行10个任务
    tasks = [mock.execute(context) for _ in range(10)]
    results = await asyncio.gather(*tasks)

    # 验证所有任务都成功
    assert all(r.status == AgentStatus.COMPLETED for r in results)


# ==================== 示例5: 集成测试 ====================

@pytest.mark.asyncio
async def test_multi_agent_workflow():
    """测试多Agent工作流"""
    # 创建3个Mock Agent
    retriever = create_success_mock(
        agent_id="retriever",
        result={"patents": ["patent1", "patent2", "patent3"]}
    )

    analyzer = create_success_mock(
        agent_id="analyzer",
        result={"analysis": "positive"}
    )

    writer = create_success_mock(
        agent_id="writer",
        result={"document": "generated"}
    )

    # 模拟工作流
    # 步骤1: 检索
    context1 = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"query": "test query"},
        config={},
        metadata={},
    )
    result1 = await retriever.execute(context1)

    # 步骤2: 分析（使用检索结果）
    context2 = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_002",
        input_data={
            "previous_results": {
                "retriever": result1.output_data
            }
        },
        config={},
        metadata={},
    )
    result2 = await analyzer.execute(context2)

    # 步骤3: 撰写（使用分析结果）
    context3 = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_003",
        input_data={
            "previous_results": {
                "retriever": result1.output_data,
                "analyzer": result2.output_data
            }
        },
        config={},
        metadata={},
    )
    result3 = await writer.execute(context3)

    # 验证工作流
    assert result1.status == AgentStatus.COMPLETED
    assert result2.status == AgentStatus.COMPLETED
    assert result3.status == AgentStatus.COMPLETED

    assert len(result1.output_data["patents"]) == 3
    assert result2.output_data["analysis"] == "positive"
    assert result3.output_data["document"] == "generated"


# ==================== 示例6: 性能测试 ====================

@pytest.mark.asyncio
async def test_mock_performance():
    """测试Mock Agent性能"""
    mock = create_success_mock()

    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={},
        config={},
        metadata={},
    )

    # 执行100次
    import time
    start = time.time()
    for _ in range(100):
        await mock.execute(context)
    elapsed = time.time() - start

    # 验证性能（应该在1秒内完成100次执行）
    assert elapsed < 1.0, f"性能测试失败: {elapsed}秒 > 1.0秒"

    print(f"\n性能测试: 100次执行耗时 {elapsed:.3f}秒")
    print(f"平均每次执行: {elapsed/100*1000:.2f}毫秒")


# ==================== 示例7: 错误恢复测试 ====================

@pytest.mark.asyncio
async def test_mock_error_recovery():
    """测试错误恢复"""
    # 创建一个会失败的Mock Agent
    mock = create_failure_mock(error_message="临时错误")

    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={},
        config={},
        metadata={},
    )

    # 第一次执行失败
    result1 = await mock.execute(context)
    assert result1.status == AgentStatus.ERROR

    # 修改Mock Agent为成功
    mock.mock_behavior["should_fail"] = False
    mock.mock_behavior["execute_result"] = {"recovered": True}

    # 第二次执行成功
    result2 = await mock.execute(context)
    assert result2.status == AgentStatus.COMPLETED
    assert result2.output_data["recovered"] is True


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v"])
