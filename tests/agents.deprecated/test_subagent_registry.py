"""
SubagentRegistry单元测试

测试子代理注册表的所有功能。
"""

import pytest

from core.framework.agents.subagent_registry import (
    SubagentConfig,
    SubagentRegistry,
    get_subagent_registry,
)
from core.framework.agents.task_tool.models import ModelChoice


class TestSubagentConfig:
    """测试SubagentConfig数据类"""

    def test_create_config(self) -> None:
        """测试创建配置"""
        config = SubagentConfig(
            agent_type="test-agent",
            display_name="测试代理",
            description="这是一个测试代理",
            default_model=ModelChoice.SONNET,
        )

        assert config.agent_type == "test-agent"
        assert config.display_name == "测试代理"
        assert config.description == "这是一个测试代理"
        assert config.default_model == ModelChoice.SONNET
        assert config.capabilities == []
        assert config.allowed_tools == []
        assert config.max_concurrent_tasks == 3
        assert config.priority == 5

    def test_to_dict(self) -> None:
        """测试转换为字典"""
        config = SubagentConfig(
            agent_type="test-agent",
            display_name="测试代理",
            description="测试描述",
            default_model=ModelChoice.OPUS,
            capabilities=["capability1", "capability2"],
            system_prompt="测试提示词",
            allowed_tools=["tool1", "tool2"],
            max_concurrent_tasks=5,
            priority=3,
        )

        result = config.to_dict()

        assert result["agent_type"] == "test-agent"
        assert result["display_name"] == "测试代理"
        assert result["description"] == "测试描述"
        assert result["default_model"] == "opus"
        assert result["capabilities"] == ["capability1", "capability2"]
        assert result["system_prompt"] == "测试提示词"
        assert result["allowed_tools"] == ["tool1", "tool2"]
        assert result["max_concurrent_tasks"] == 5
        assert result["priority"] == 3


class TestSubagentRegistry:
    """测试SubagentRegistry类"""

    def test_init(self) -> None:
        """测试初始化"""
        registry = SubagentRegistry()

        assert registry.get_agent_count() == 4  # 预定义的4种代理类型
        assert "patent-analyst" in registry.list_agent_types()
        assert "patent-searcher" in registry.list_agent_types()
        assert "legal-researcher" in registry.list_agent_types()
        assert "patent-drafter" in registry.list_agent_types()

    def test_register_agent(self) -> None:
        """测试注册代理"""
        registry = SubagentRegistry()

        config = SubagentConfig(
            agent_type="custom-agent",
            display_name="自定义代理",
            description="自定义描述",
            default_model=ModelChoice.SONNET,
        )

        registry.register_agent(config)

        assert registry.agent_exists("custom-agent")
        assert registry.get_agent_count() == 5

    def test_register_duplicate_agent(self) -> None:
        """测试注册重复代理（应该覆盖）"""
        registry = SubagentRegistry()

        config1 = SubagentConfig(
            agent_type="test-agent",
            display_name="测试代理1",
            description="描述1",
            default_model=ModelChoice.SONNET,
        )

        config2 = SubagentConfig(
            agent_type="test-agent",
            display_name="测试代理2",
            description="描述2",
            default_model=ModelChoice.OPUS,
        )

        registry.register_agent(config1)
        registry.register_agent(config2)  # 应该覆盖

        config = registry.get_agent("test-agent")
        assert config.display_name == "测试代理2"
        assert config.description == "描述2"
        assert config.default_model == ModelChoice.OPUS

    def test_get_agent(self) -> None:
        """测试获取代理配置"""
        registry = SubagentRegistry()

        config = registry.get_agent("patent-analyst")

        assert config is not None
        assert config.agent_type == "patent-analyst"
        assert config.display_name == "专利分析师"
        assert config.description == "负责专利技术分析、创新点识别、技术对比分析"
        assert config.default_model == ModelChoice.SONNET
        assert len(config.capabilities) > 0
        assert len(config.system_prompt) > 0
        assert len(config.allowed_tools) > 0
        assert config.max_concurrent_tasks == 5
        assert config.priority == 1

    def test_get_nonexistent_agent(self) -> None:
        """测试获取不存在的代理"""
        registry = SubagentRegistry()

        config = registry.get_agent("nonexistent-agent")
        assert config is None

    def test_get_available_agents(self) -> None:
        """测试获取可用代理列表"""
        registry = SubagentRegistry()

        agents = registry.get_available_agents()

        assert len(agents) == 4
        # 检查按优先级排序
        priorities = [agent.priority for agent in agents]
        assert priorities == sorted(priorities)

    def test_get_available_agents_with_priority(self) -> None:
        """测试按优先级过滤代理"""
        registry = SubagentRegistry()

        agents = registry.get_available_agents(priority=1)

        assert len(agents) == 2  # patent-analyst和legal-researcher优先级为1
        assert all(agent.priority == 1 for agent in agents)

    def test_get_agent_config(self) -> None:
        """测试获取完整代理配置（包括模型配置）"""
        registry = SubagentRegistry()

        config = registry.get_agent_config("patent-searcher")

        assert config["agent_type"] == "patent-searcher"
        assert config["display_name"] == "专利检索员"
        assert config["default_model"] == "haiku"
        assert "model_config" in config
        assert config["model_config"]["name"] == "quick"
        assert config["model_config"]["temperature"] == 0.7
        assert config["model_config"]["max_tokens"] == 4096

    def test_get_agent_config_nonexistent(self) -> None:
        """测试获取不存在代理的配置"""
        registry = SubagentRegistry()

        with pytest.raises(ValueError, match="代理类型不存在"):
            registry.get_agent_config("nonexistent-agent")

    def test_agent_exists(self) -> None:
        """测试检查代理是否存在"""
        registry = SubagentRegistry()

        assert registry.agent_exists("patent-analyst")
        assert registry.agent_exists("patent-searcher")
        assert registry.agent_exists("legal-researcher")
        assert registry.agent_exists("patent-drafter")
        assert not registry.agent_exists("nonexistent-agent")

    def test_get_agent_count(self) -> None:
        """测试获取代理数量"""
        registry = SubagentRegistry()

        assert registry.get_agent_count() == 4

        # 添加新代理
        config = SubagentConfig(
            agent_type="new-agent",
            display_name="新代理",
            description="描述",
            default_model=ModelChoice.SONNET,
        )
        registry.register_agent(config)

        assert registry.get_agent_count() == 5

    def test_list_agent_types(self) -> None:
        """测试列出代理类型"""
        registry = SubagentRegistry()

        types = registry.list_agent_types()

        assert len(types) == 4
        assert "patent-analyst" in types
        assert "patent-searcher" in types
        assert "legal-researcher" in types
        assert "patent-drafter" in types

    def test_get_agents_by_capability(self) -> None:
        """测试根据能力查询代理"""
        registry = SubagentRegistry()

        # 查询具有"专利检索策略制定"能力的代理
        agents = registry.get_agents_by_capability("专利检索策略制定")

        # patent-searcher应该有这个能力
        assert len(agents) > 0
        assert any(agent.agent_type == "patent-searcher" for agent in agents)

    def test_update_agent_config(self) -> None:
        """测试更新代理配置"""
        registry = SubagentRegistry()

        # 更新max_concurrent_tasks
        registry.update_agent_config("patent-analyst", max_concurrent_tasks=10)

        config = registry.get_agent("patent-analyst")
        assert config.max_concurrent_tasks == 10

        # 更新多个配置项
        registry.update_agent_config(
            "patent-analyst",
            max_concurrent_tasks=15,
            priority=2,
        )

        config = registry.get_agent("patent-analyst")
        assert config.max_concurrent_tasks == 15
        assert config.priority == 2

    def test_update_agent_config_nonexistent(self) -> None:
        """测试更新不存在的代理配置"""
        registry = SubagentRegistry()

        with pytest.raises(ValueError, match="代理类型不存在"):
            registry.update_agent_config("nonexistent-agent", max_concurrent_tasks=10)

    def test_update_agent_config_invalid_field(self) -> None:
        """测试更新无效的配置项"""
        registry = SubagentRegistry()

        # 更新无效字段应该不报错，但记录警告
        registry.update_agent_config("patent-analyst", invalid_field=123)

        # 配置应该保持不变
        config = registry.get_agent("patent-analyst")
        assert not hasattr(config, "invalid_field")

    def test_predefined_agents_integrity(self) -> None:
        """测试预定义代理的完整性"""
        registry = SubagentRegistry()

        # 测试patent-analyst
        analyst = registry.get_agent("patent-analyst")
        assert analyst.agent_type == "patent-analyst"
        assert analyst.default_model == ModelChoice.SONNET
        assert analyst.priority == 1
        assert "专利技术分析" in analyst.capabilities
        assert len(analyst.system_prompt) > 100

        # 测试patent-searcher
        searcher = registry.get_agent("patent-searcher")
        assert searcher.agent_type == "patent-searcher"
        assert searcher.default_model == ModelChoice.HAIKU
        assert searcher.priority == 2
        assert "专利检索策略制定" in searcher.capabilities
        assert searcher.max_concurrent_tasks == 10

        # 测试legal-researcher
        researcher = registry.get_agent("legal-researcher")
        assert researcher.agent_type == "legal-researcher"
        assert researcher.default_model == ModelChoice.OPUS
        assert researcher.priority == 1
        assert "法律法规检索" in researcher.capabilities

        # 测试patent-drafter
        drafter = registry.get_agent("patent-drafter")
        assert drafter.agent_type == "patent-drafter"
        assert drafter.default_model == ModelChoice.SONNET
        assert drafter.priority == 2
        assert "专利申请文件撰写" in drafter.capabilities


class TestSubagentRegistrySingleton:
    """测试全局单例"""

    def test_get_singleton(self) -> None:
        """测试获取全局单例"""
        registry1 = get_subagent_registry()
        registry2 = get_subagent_registry()

        assert registry1 is registry2
        assert isinstance(registry1, SubagentRegistry)

    def test_singleton_shared_state(self) -> None:
        """测试单例共享状态"""
        registry1 = get_subagent_registry()

        # 在registry1中注册新代理
        config = SubagentConfig(
            agent_type="singleton-test",
            display_name="单例测试",
            description="描述",
            default_model=ModelChoice.SONNET,
        )
        registry1.register_agent(config)

        # 通过registry2应该也能访问到
        registry2 = get_subagent_registry()
        assert registry2.agent_exists("singleton-test")


class TestSubagentRegistryIntegration:
    """测试SubagentRegistry的集成功能"""

    def test_integration_with_model_mapper(self) -> None:
        """测试与ModelMapper的集成"""
        registry = SubagentRegistry()

        # 测试4种预定义代理的模型映射
        for agent_type in [
            "patent-analyst",
            "patent-searcher",
            "legal-researcher",
            "patent-drafter",
        ]:
            config = registry.get_agent_config(agent_type)

            assert "model_config" in config
            assert "name" in config["model_config"]
            assert "temperature" in config["model_config"]
            assert "max_tokens" in config["model_config"]

    def test_allowed_tools_format(self) -> None:
        """测试allowed_tools的格式"""
        registry = SubagentRegistry()

        for agent_type in registry.list_agent_types():
            config = registry.get_agent(agent_type)
            assert isinstance(config.allowed_tools, list)
            assert all(isinstance(tool, str) for tool in config.allowed_tools)
            assert len(config.allowed_tools) > 0

    def test_capabilities_format(self) -> None:
        """测试capabilities的格式"""
        registry = SubagentRegistry()

        for agent_type in registry.list_agent_types():
            config = registry.get_agent(agent_type)
            assert isinstance(config.capabilities, list)
            assert all(isinstance(cap, str) for cap in config.capabilities)
            assert len(config.capabilities) > 0
