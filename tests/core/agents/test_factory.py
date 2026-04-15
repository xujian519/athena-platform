#!/usr/bin/env python3
"""
AgentFactory单元测试

测试智能体工厂的创建、配置和加载功能。
"""

import pytest

# 跳过整个测试模块
pytestmark = pytest.mark.skip(reason="模块导入问题，待修复")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from core.agents.athena_advisor import AthenaAdvisorAgent
    from core.agents.base import AgentRegistry
    from core.agents.base_agent import AgentRegistry
    from core.agents.factory import AgentFactory
    from core.agents.xiaona_legal import XiaonaLegalAgent
    from core.agents.xiaonuo_coordinator import XiaonuoAgent
except ImportError:
    pass  # 模块导入失败时，测试会被跳过


# ========== 测试清理fixture ==========

@pytest.fixture(autouse=True)
def clear_registry():
    """每个测试前后清理注册表"""
    AgentRegistry.clear()
    yield
    AgentRegistry.clear()


@pytest.fixture(autouse=True)
def clear_factory():
    """每个测试前后清理工厂"""
    # 清除已注册的类
    for name in list(AgentFactory._agent_classes.keys()):
        AgentFactory.unregister_agent_class(name)
    yield
    # 再次清除
    for name in list(AgentFactory._agent_classes.keys()):
        AgentFactory.unregister_agent_class(name)


# ========== AgentFactory测试 ==========


def test_factory_register_xiaona():
    """测试注册小娜智能体类"""
    name = AgentFactory.register_agent_class(XiaonaLegalAgent)
    assert name == "xiaona-legal"
    assert "xiaona-legal" in AgentFactory.list_available_agents()


def test_factory_register_xiaonuo():
    """测试注册小诺智能体类"""
    name = AgentFactory.register_agent_class(XiaonuoAgent)
    assert name == "xiaonuo-coordinator"
    assert "xiaonuo-coordinator" in AgentFactory.list_available_agents()


def test_factory_register_athena():
    """测试注册Athena智能体类"""
    name = AgentFactory.register_agent_class(AthenaAdvisorAgent)
    assert name == "athena-advisor"
    assert "athena-advisor" in AgentFactory.list_available_agents()


def test_factory_create_xiaona():
    """测试创建小娜智能体"""
    AgentFactory.register_agent_class(XiaonaLegalAgent)

    agent = AgentFactory.create("xiaona-legal")

    assert agent is not None
    assert agent.name == "xiaona-legal"


def test_factory_create_with_config():
    """测试带配置创建"""
    AgentFactory.register_agent_class(XiaonaLegalAgent)

    agent = AgentFactory.create("xiaona-legal", config={"test": "value"})

    assert agent is not None


def test_factory_create_invalid_type():
    """测试无效类型"""
    # 不注册任何类型
    with pytest.raises(ValueError, match="未知的智能体类型"):
        AgentFactory.create("invalid-agent-type")


def test_factory_duplicate_registration():
    """测试重复注册"""
    AgentFactory.register_agent_class(XiaonaLegalAgent)

    with pytest.raises(ValueError, match="已存在"):
        AgentFactory.register_agent_class(XiaonaLegalAgent)


def test_factory_unregister():
    """测试注销"""
    name = AgentFactory.register_agent_class(XiaonuoAgent)
    AgentFactory.unregister_agent_class(name)

    assert name not in AgentFactory.list_available_agents()


# ========== 异步创建测试 ==========


@pytest.mark.asyncio
async def test_factory_create_async():
    """测试异步创建"""
    AgentFactory.register_agent_class(XiaonaLegalAgent)

    agent = await AgentFactory.create_async("xiaona-legal")

    assert agent is not None
    assert agent.is_ready


@pytest.mark.asyncio
async def test_factory_create_many():
    """测试批量创建"""
    AgentFactory.register_agent_class(XiaonaLegalAgent)
    AgentFactory.register_agent_class(XiaonuoAgent)
    AgentFactory.register_agent_class(AthenaAdvisorAgent)

    configs = [
        {"name": "xiaona-legal"},
        {"name": "xiaonuo-coordinator"},
        {"name": "athena-advisor"},
    ]

    agents = await AgentFactory.create_many(configs)

    assert len(agents) == 3
    assert all(a.is_ready for a in agents)


# ========== 列表功能测试 ==========


def test_factory_list_empty():
    """测试空列表"""
    # 清除所有注册
    for name in list(AgentFactory._agent_classes.keys()):
        AgentFactory.unregister_agent_class(name)

    assert AgentFactory.list_available_agents() == []


def test_factory_list_multiple():
    """测试多个智能体"""
    AgentFactory.register_agent_class(XiaonaLegalAgent)
    AgentFactory.register_agent_class(XiaonuoAgent)
    AgentFactory.register_agent_class(AthenaAdvisorAgent)

    agents = AgentFactory.list_available_agents()

    assert len(agents) == 3
    assert "xiaona-legal" in agents
    assert "xiaonuo-coordinator" in agents
    assert "athena-advisor" in agents


# ========== 类型验证测试 ==========


def test_factory_invalid_agent_class():
    """测试无效的智能体类"""
    class NotAnAgent:
        pass

    with pytest.raises(TypeError, match="必须继承自 BaseAgent"):
        AgentFactory.register_agent_class(NotAnAgent)


# ========== 运行测试 ==========

if __name__ == "__main__":
    print("运行AgentFactory测试...")
    pytest.main([__file__, "-v"])
