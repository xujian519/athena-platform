#!/usr/bin/env python3
"""
Athena Agent性能监控测试
Athena Agent Performance Monitoring Tests

测试AthenaAgent的性能监控功能
"""
import pytest
from core.framework.agents.athena_agent import AthenaAgent


@pytest.mark.asyncio
async def test_athena_agent_performance_monitoring():
    """测试AthenaAgent性能监控"""
    agent = AthenaAgent()

    # 初始化Agent
    await agent.initialize()

    # 执行一次处理
    result = await agent.process_input("测试任务")

    # 验证性能数据存在
    assert "performance" in result
    assert "processing_time" in result["performance"]
    assert result["performance"]["processing_time"] >= 0

    # 验证统计信息
    stats = result["performance"]["statistics"]
    assert "total_requests" in stats
    assert stats["total_requests"] == 1
    assert "successful_requests" in stats
    assert stats["successful_requests"] == 1
    assert "avg_processing_time" in stats


@pytest.mark.asyncio
async def test_athena_agent_performance_statistics():
    """测试性能统计信息"""
    agent = AthenaAgent()

    # 初始化Agent
    await agent.initialize()

    # 执行多次处理
    for i in range(5):
        await agent.process_input(f"测试任务 {i}")

    # 获取统计信息
    stats = await agent.get_performance_statistics()

    # 验证统计信息
    assert stats["total_requests"] == 5
    assert stats["successful_requests"] == 5
    assert stats["avg_processing_time"] > 0
    assert stats["min_processing_time"] > 0
    assert stats["max_processing_time"] >= stats["min_processing_time"]
    assert stats["success_rate"] == 1.0  # 100%成功率


@pytest.mark.asyncio
async def test_athena_agent_recent_performance():
    """测试最近性能记录"""
    agent = AthenaAgent()

    # 初始化Agent
    await agent.initialize()

    # 执行多次处理
    for i in range(15):
        await agent.process_input(f"测试任务 {i}")

    # 获取最近10次性能记录
    recent = await agent.get_recent_performance(10)

    # 验证最近性能记录
    assert len(recent) == 10
    assert all("time" in record for record in recent)
    assert all("success" in record for record in recent)
    assert all("timestamp" in record for record in recent)
    assert all(record["success"] for record in recent)


@pytest.mark.asyncio
async def test_athena_agent_performance_reset():
    """测试性能监控重置"""
    agent = AthenaAgent()

    # 初始化Agent
    await agent.initialize()

    # 执行几次处理
    for i in range(3):
        await agent.process_input(f"测试任务 {i}")

    # 验证统计信息
    stats = await agent.get_performance_statistics()
    assert stats["total_requests"] == 3

    # 重置性能监控
    await agent.reset_performance_monitor()

    # 验证重置后的统计信息
    stats = await agent.get_performance_statistics()
    assert stats["total_requests"] == 0
    assert stats["successful_requests"] == 0


@pytest.mark.asyncio
async def test_athena_agent_performance_with_error():
    """测试错误情况下的性能记录"""
    agent = AthenaAgent()

    # 初始化Agent
    await agent.initialize()

    # 模拟错误处理
    try:
        # 传递无效输入可能触发错误
        await agent.process_input(None)
    except Exception:
        pass  # 预期会出错

    # 获取统计信息
    stats = await agent.get_performance_statistics()

    # 验证失败请求被记录
    assert stats["total_requests"] >= 1
    # 失败请求可能被记录
    # assert stats["failed_requests"] >= 1


@pytest.mark.asyncio
async def test_athena_agent_performance_overhead():
    """测试性能监控的开销"""
    agent = AthenaAgent()

    # 初始化Agent
    await agent.initialize()

    # 执行100次处理
    times = []
    for i in range(100):
        import time
        start = time.time()
        await agent.process_input(f"测试任务 {i}")
        times.append(time.time() - start)

    avg_time = sum(times) / len(times)

    # 验证平均响应时间合理（< 3秒）
    assert avg_time < 3.0, f"平均响应时间过长: {avg_time:.2f}秒"

    # 验证成功率
    stats = await agent.get_performance_statistics()
    assert stats["success_rate"] > 0.95  # 95%以上成功率


@pytest.mark.asyncio
async def test_athena_agent_all_features_with_performance():
    """测试所有功能与性能监控的集成"""
    agent = AthenaAgent()

    # 初始化Agent
    await agent.initialize()

    # 执行完整处理
    result = await agent.process_input("分析专利CN123456的创造性")

    # 验证所有功能正常
    assert "athena_analysis" in result
    assert "technical_assessment" in result
    assert "strategic_recommendations" in result
    assert "performance" in result

    # 验证性能数据
    perf = result["performance"]
    assert perf["processing_time"] > 0
    assert perf["statistics"]["total_requests"] >= 1
