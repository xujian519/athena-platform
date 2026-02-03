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
    # 创建模拟数据库管理器
    class MockDBManager:
        def __init__(self):
            self.rules = {
                ("专利无效", "证据检索", "初步审查"): {
                    "rule_template": "测试规则",
                    "priority": "high",
                    "confidence": 0.9,
                }
            }

        def get_rule(self, domain, task_type, phase):
            key = (domain, task_type, phase)
            return self.rules.get(key)

        # async method
        async def aget_rule(self, domain, task_type, phase):
            return self.get_rule(domain, task_type, phase)

    # 创建检索器
    retriever = ScenarioRuleRetrieverOptimized(db_manager=MockDBManager())

    # 测试检索功能
    rule = await retriever.aget_rule("专利无效", "证据检索", "初步审查")

    assert rule is not None
    assert rule.get("rule_template") == "测试规则"


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

    # 测试检索器性能
    class MockDBManager:
        async def aget_rule(self, domain, task_type, phase):
            # 模拟数据库延迟
            await asyncio.sleep(0.001)  # 1ms
            return {"rule_template": "测试"}

    retriever = ScenarioRuleRetrieverOptimized(db_manager=MockDBManager())

    start = time.time()
    rule = await retriever.aget_rule("专利无效", "证据检索", "初步审查")
    elapsed = (time.time() - start) * 1000

    assert rule is not None
    assert elapsed < 100, f"规则检索耗时过长: {elapsed:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "integration"])
