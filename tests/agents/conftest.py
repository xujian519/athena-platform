"""
测试配置 - 专利撰写智能体测试套件

处理Prometheus metrics重复注册问题
"""

import logging
import os

import pytest

# 配置日志
logging.basicConfig(level=logging.INFO)


# 在导入任何模块前禁用LLM metrics
os.environ.setdefault("LLM_METRICS_ENABLED", "false")


@pytest.fixture(autouse=True)
def reset_prometheus_metrics():
    """
    自动清理Prometheus metrics，避免重复注册错误

    在每个测试前运行
    """
    from prometheus_client import REGISTRY

    # 创建一个包含所有要移除的metric名称集合
    metrics_to_remove = set()

    # 遍历所有已注册的collectors
    for collector in list(REGISTRY._collector_to_names.keys()):
        # 获取该collector的所有名称
        names = REGISTRY._collector_to_names.get(collector, set())
        for name in names:
            # 检查是否是LLM相关的metrics
            if 'llm' in name.lower():
                metrics_to_remove.add(collector)

    # 移除标记的collectors
    for collector in metrics_to_remove:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass  # 忽略未注册的collector

    yield


@pytest.fixture
def mock_llm_manager():
    """
    Mock LLM管理器fixture
    避免实际调用LLM API
    """
    from unittest.mock import AsyncMock, Mock

    mock = Mock()
    mock.generate = AsyncMock(
        return_value='{"result": "mock response"}'
    )
    return mock


# 模块级清理 - 在所有测试开始前运行一次
def pytest_configure(config):
    """
    Pytest配置钩子
    在测试会话开始时执行
    """
    from prometheus_client import REGISTRY

    # 清理所有LLM相关的metrics
    collectors_to_remove = []
    for collector in list(REGISTRY._collector_to_names.keys()):
        names = REGISTRY._collector_to_names.get(collector, set())
        for name in names:
            if 'llm' in name.lower():
                collectors_to_remove.append(collector)
                break

    for collector in collectors_to_remove:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
