#!/usr/bin/env python3
"""
Athena Agent记忆增强测试
Athena Agent Memory Enhancement Tests

测试AthenaAgent的记忆增强功能
"""
import pytest

from core.agent.athena_agent import AthenaAgent, MEMORY_SYSTEM_AVAILABLE


@pytest.mark.asyncio
async def test_athena_agent_memory_enabled():
    """测试AthenaAgent记忆系统状态"""
    agent = AthenaAgent()

    # 验证记忆系统状态
    assert agent.memory_enhanced == MEMORY_SYSTEM_AVAILABLE

    if MEMORY_SYSTEM_AVAILABLE:
        assert agent.memory_enhanced is True


@pytest.mark.asyncio
async def test_athena_agent_wisdom_memory_loading():
    """测试智慧记忆加载"""
    agent = AthenaAgent()

    if not MEMORY_SYSTEM_AVAILABLE:
        pytest.skip("记忆系统不可用")

    # 初始化Agent
    await agent.initialize()

    # 验证智慧记忆已加载（通过检查是否有记忆系统调用）
    # 注意：这里只是验证没有报错
    assert agent.initialized is True


@pytest.mark.asyncio
async def test_athena_agent_remember_wisdom():
    """测试记录智慧记忆"""
    agent = AthenaAgent()

    if not MEMORY_SYSTEM_AVAILABLE:
        pytest.skip("记忆系统不可用")

    await agent.initialize()

    # 记录智慧记忆
    success = await agent.remember_wisdom(
        content="测试智慧记忆",
        importance=0.9,
        emotional_weight=0.8,
        tags=["测试", "智慧"],
    )

    # 验证记录成功
    assert success is True


@pytest.mark.asyncio
async def test_athena_agent_recall_wisdom():
    """测试回忆智慧"""
    agent = AthenaAgent()

    if not MEMORY_SYSTEM_AVAILABLE:
        pytest.skip("记忆系统不可用")

    await agent.initialize()

    # 先记录一些记忆
    await agent.remember_wisdom(
        content="专利分析需要全面考虑技术方案",
        importance=0.9,
        tags=["专利", "分析"],
    )

    await agent.remember_wisdom(
        content="系统架构设计要考虑可扩展性",
        importance=0.8,
        tags=["架构", "设计"],
    )

    # 回忆相关知识
    memories = await agent.recall_wisdom(query="专利分析", limit=5)

    # 验证回忆结果
    assert isinstance(memories, list)
    # 注意：可能返回空列表，取决于记忆系统的实现


@pytest.mark.asyncio
async def test_athena_agent_remember_learning():
    """测试记录学习内容"""
    agent = AthenaAgent()

    if not MEMORY_SYSTEM_AVAILABLE:
        pytest.skip("记忆系统不可用")

    await agent.initialize()

    # 记录学习内容
    success = await agent.remember_learning(
        topic="专利法",
        knowledge="专利保护期为20年",
        importance=0.9,
    )

    # 验证记录成功
    assert success is True


@pytest.mark.asyncio
async def test_athena_agent_remember_work():
    """测试记录工作内容"""
    agent = AthenaAgent()

    if not MEMORY_SYSTEM_AVAILABLE:
        pytest.skip("记忆系统不可用")

    await agent.initialize()

    # 记录工作内容
    success = await agent.remember_work(
        task="分析专利CN123456",
        result="具有创造性",
        importance=0.8,
    )

    # 验证记录成功
    assert success is True


@pytest.mark.asyncio
async def test_athena_agent_memory_statistics():
    """测试获取记忆统计"""
    agent = AthenaAgent()

    if not MEMORY_SYSTEM_AVAILABLE:
        pytest.skip("记忆系统不可用")

    await agent.initialize()

    # 获取记忆统计
    stats = await agent.get_memory_statistics()

    # 验证统计信息
    assert isinstance(stats, dict)
    assert "enabled" in stats
    assert stats["enabled"] is True


@pytest.mark.asyncio
async def test_athena_agent_memory_without_system():
    """测试没有记忆系统时的行为"""
    agent = AthenaAgent()

    if MEMORY_SYSTEM_AVAILABLE:
        pytest.skip("记忆系统可用，跳过此测试")

    # 记忆功能应该返回False或空列表
    success = await agent.remember_wisdom("测试")
    assert success is False

    memories = await agent.recall_wisdom("测试")
    assert memories == []

    stats = await agent.get_memory_statistics()
    assert stats["enabled"] is False


@pytest.mark.asyncio
async def test_athena_agent_memory_with_importance_filter():
    """测试重要性过滤"""
    agent = AthenaAgent()

    if not MEMORY_SYSTEM_AVAILABLE:
        pytest.skip("记忆系统不可用")

    await agent.initialize()

    # 记录不同重要性的记忆
    await agent.remember_wisdom("高重要性内容", importance=0.9)
    await agent.remember_wisdom("中重要性内容", importance=0.6)
    await agent.remember_wisdom("低重要性内容", importance=0.3)

    # 回忆高重要性记忆
    memories = await agent.recall_wisdom(query="内容", min_importance=0.7)

    # 验证过滤结果
    assert isinstance(memories, list)
    # 高重要性的记忆应该被包含


@pytest.mark.asyncio
async def test_athena_agent_all_memory_methods():
    """测试所有记忆方法"""
    agent = AthenaAgent()

    if not MEMORY_SYSTEM_AVAILABLE:
        pytest.skip("记忆系统不可用")

    await agent.initialize()

    # 测试所有记忆方法
    # 1. remember_wisdom
    assert await agent.remember_wisdom("智慧记忆") is True

    # 2. remember_learning
    assert await agent.remember_learning(topic="主题", knowledge="知识") is True

    # 3. remember_work
    assert await agent.remember_work(task="任务", result="结果") is True

    # 4. recall_wisdom
    memories = await agent.recall_wisdom("查询")
    assert isinstance(memories, list)

    # 5. get_memory_statistics
    stats = await agent.get_memory_statistics()
    assert stats["enabled"] is True


@pytest.mark.asyncio
async def test_athena_agent_memory_integration_with_process():
    """测试记忆与process_input的集成"""
    agent = AthenaAgent()

    if not MEMORY_SYSTEM_AVAILABLE:
        pytest.skip("记忆系统不可用")

    await agent.initialize()

    # 记录一些专业知识
    await agent.remember_learning(
        topic="专利创造性",
        knowledge="需要突出的技术特点和显著进步",
        importance=0.9,
    )

    # 处理输入
    result = await agent.process_input("分析专利创造性")

    # 验证处理成功
    assert "athena_analysis" in result
    assert "technical_assessment" in result
    assert "performance" in result


@pytest.mark.asyncio
async def test_athena_agent_memory_error_handling():
    """测试记忆功能的错误处理"""
    agent = AthenaAgent()

    if not MEMORY_SYSTEM_AVAILABLE:
        pytest.skip("记忆系统不可用")

    await agent.initialize()

    # 测试None内容
    success = await agent.remember_wisdom(None)
    # 应该优雅地处理错误
    assert isinstance(success, bool)

    # 测试空查询
    memories = await agent.recall_wisdom("")
    assert isinstance(memories, list)
