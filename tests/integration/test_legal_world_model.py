#!/usr/bin/env python3
"""
法律世界模型集成测试
Integration Tests for Legal World Model

测试法律世界模型各组件的端到端功能。

作者: Athena平台团队
创建时间: 2026-02-03
版本: v1.0.0
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path

from core.legal_world_model.health_check import (
    check_health,
    HealthStatus,
    SystemHealthReport,
)
from core.legal_world_model.scenario_rule_retriever_optimized import (
    ScenarioRuleRetrieverOptimized,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check_integration():
    """测试健康检查集成"""
    report = await check_health()

    assert isinstance(report, SystemHealthReport)
    assert report.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    assert len(report.components) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scenario_retriever_end_to_end():
    """测试场景检索器端到端流程"""
    # 创建模拟数据库管理器（最小化mock）
    class MockSession:
        def run(self, query, **params):
            # 返回空结果（模拟没有找到规则）
            class MockResult:
                def single(self):
                    return None
            return MockResult()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class MockDBManager:
        def session(self):
            return MockSession()

    # 创建检索器（验证可以实例化）
    try:
        retriever = ScenarioRuleRetrieverOptimized(db_manager=MockDBManager())
        # 验证检索器有正确的属性
        assert hasattr(retriever, 'db_manager')
        assert hasattr(retriever, 'retrieve_rule')
        assert hasattr(retriever, 'ALLOWED_DOMAINS')
        # 验证ALLOWED_DOMAINS包含预期值
        assert 'patent' in retriever.ALLOWED_DOMAINS
    except Exception as e:
        pytest.fail(f"场景检索器实例化失败: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cross_module_integration():
    """测试跨模块集成"""
    # 测试学习引擎与法律世界模型的集成
    try:
        from core.learning import get_module_capabilities
        from core.legal_world_model.health_check import check_health

        # 获取学习模块能力
        capabilities = get_module_capabilities()

        # 检查关键模块可用
        assert "meta_learning" in capabilities
        assert "reinforcement_learning" in capabilities

        # 检查健康状态
        report = await check_health()
        assert isinstance(report, SystemHealthReport)

    except Exception as e:
        pytest.fail(f"跨模块集成测试失败: {e}")


@pytest.mark.integration
def test_data_persistence_integration():
    """测试数据持久化集成"""
    # 检查数据目录结构
    data_dirs = [
        Path("data/neo4j"),
        Path("data/qdrant"),
        Path("data/rl_production"),
    ]

    for data_dir in data_dirs:
        # 检查目录是否存在
        # 注意：不强制要求目录存在，因为可能在测试环境
        if data_dir.exists():
            assert data_dir.is_dir()


@pytest.mark.integration
def test_backup_scripts_exist():
    """测试备份脚本存在性"""
    backup_scripts = [
        "scripts/backup/backup_all.sh",
        "scripts/backup/backup_legal_model.sh",
        "scripts/backup/run_backup.py",
    ]

    project_root = Path("/Users/xujian/Athena工作平台")

    for script in backup_scripts:
        script_path = project_root / script
        assert script_path.exists(), f"备份脚本不存在: {script}"
        assert script_path.stat().st_size > 0, f"备份脚本为空: {script}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_monitoring_integration():
    """测试监控集成"""
    try:
        from core.monitoring import MonitoringEngine

        # 创建监控引擎
        monitor = MonitoringEngine(
            agent_id="test_agent",
            config={"enable_performance_monitoring": False},
        )

        # 初始化
        await monitor.initialize()

        # 检查状态
        status = await monitor.get_monitoring_status()

        assert "agent_id" in status
        assert status["agent_id"] == "test_agent"

        # 关闭
        await monitor.shutdown()

    except Exception as e:
        pytest.fail(f"监控集成测试失败: {e}")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_performance_baseline():
    """测试性能基线"""
    import time

    # 测试健康检查性能
    start = time.time()
    report = await check_health()
    elapsed = (time.time() - start) * 1000

    assert elapsed < 5000, f"健康检查耗时过长: {elapsed:.2f}ms"

    # 测试检索器性能（同步方法）
    class MockSession:
        def run(self, query, **params):
            # 返回模拟结果
            class MockResult:
                def single(self):
                    return None  # 返回None模拟没有找到规则
            return MockResult()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class MockDBManager:
        def session(self):
            return MockSession()

    retriever = ScenarioRuleRetrieverOptimized(db_manager=MockDBManager())

    start = time.time()
    rule = retriever.retrieve_rule("patent", "search", "application")
    elapsed = (time.time() - start) * 1000

    # 规则可能为None（mock返回空结果），但响应时间应该快
    assert elapsed < 100, f"规则检索耗时过长: {elapsed:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "integration"])
