"""
ToolFilter单元测试
"""


from core.agents.subagent_registry import SubagentConfig, SubagentRegistry
from core.agents.task_tool.models import ModelChoice


def test_tool_filter_initialization():
    """测试ToolFilter初始化"""
    from core.agents.task_tool.tool_filter import ToolFilter

    registry = SubagentRegistry()
    filter = ToolFilter(registry)

    assert filter is not None
    assert filter._registry == registry


def test_filter_tools_basic():
    """测试基本工具过滤"""
    from core.agents.task_tool.tool_filter import ToolFilter

    registry = SubagentRegistry()
    filter = ToolFilter(registry)

    # 获取专利分析师配置
    agent_config = registry.get_agent("patent-analyst")
    assert agent_config is not None

    # 过滤工具
    available_tools = [
        "code_analyzer",
        "knowledge_graph",
        "patent_search",
        "web_search",
        "document_processor",
    ]
    filtered_tools = filter.filter_tools(available_tools, agent_config)

    # 验证结果
    assert "code_analyzer" in filtered_tools
    assert "knowledge_graph" in filtered_tools
    assert "patent_search" in filtered_tools
    assert "web_search" in filtered_tools
    assert "document_processor" not in filtered_tools  # 不在允许列表中


def test_filter_tools_with_wildcard():
    """测试通配符过滤"""
    from core.agents.task_tool.tool_filter import ToolFilter

    registry = SubagentRegistry()

    # 创建一个使用通配符的配置
    custom_config = SubagentConfig(
        agent_type="custom-agent",
        display_name="自定义代理",
        description="测试通配符",
        default_model=ModelChoice.SONNET,
        allowed_tools=["patent_*", "*_search"],
    )
    registry.register_agent(custom_config)

    filter = ToolFilter(registry)

    # 测试通配符过滤
    available_tools = [
        "patent_search",
        "patent_analyzer",
        "web_search",
        "code_search",
        "document_processor",
    ]
    filtered_tools = filter.filter_tools(available_tools, custom_config)

    # 验证结果
    assert "patent_search" in filtered_tools
    assert "patent_analyzer" in filtered_tools
    assert "web_search" in filtered_tools
    assert "code_search" in filtered_tools
    assert "document_processor" not in filtered_tools


def test_filter_tools_empty_allowed_list():
    """测试空允许列表（允许所有工具）"""
    from core.agents.task_tool.tool_filter import ToolFilter

    registry = SubagentRegistry()

    # 创建一个没有限制的配置
    unrestricted_config = SubagentConfig(
        agent_type="unrestricted-agent",
        display_name="无限制代理",
        description="测试无限制",
        default_model=ModelChoice.SONNET,
        allowed_tools=[],  # 空列表表示允许所有工具
    )
    registry.register_agent(unrestricted_config)

    filter = ToolFilter(registry)

    available_tools = ["tool1", "tool2", "tool3"]
    filtered_tools = filter.filter_tools(available_tools, unrestricted_config)

    # 验证所有工具都被允许
    assert len(filtered_tools) == 3
    assert "tool1" in filtered_tools
    assert "tool2" in filtered_tools
    assert "tool3" in filtered_tools


def test_filter_tools_no_available_tools():
    """测试没有可用工具的情况"""
    from core.agents.task_tool.tool_filter import ToolFilter

    registry = SubagentRegistry()
    filter = ToolFilter(registry)

    agent_config = registry.get_agent("patent-analyst")
    filtered_tools = filter.filter_tools([], agent_config)

    # 验证返回空列表
    assert len(filtered_tools) == 0


def test_is_tool_allowed_basic():
    """测试工具权限检查"""
    from core.agents.task_tool.tool_filter import ToolFilter

    registry = SubagentRegistry()
    filter = ToolFilter(registry)

    agent_config = registry.get_agent("patent-analyst")

    # 测试允许的工具
    assert filter.is_tool_allowed("code_analyzer", agent_config) is True
    assert filter.is_tool_allowed("patent_search", agent_config) is True

    # 测试不允许的工具
    assert filter.is_tool_allowed("document_processor", agent_config) is False


def test_is_tool_allowed_with_wildcard():
    """测试通配符工具权限检查"""
    from core.agents.task_tool.tool_filter import ToolFilter

    registry = SubagentRegistry()

    # 创建使用通配符的配置
    wildcard_config = SubagentConfig(
        agent_type="wildcard-agent",
        display_name="通配符代理",
        description="测试通配符",
        default_model=ModelChoice.SONNET,
        allowed_tools=["test_*", "*_analyzer"],
    )
    registry.register_agent(wildcard_config)

    filter = ToolFilter(registry)

    # 测试通配符匹配
    assert filter.is_tool_allowed("test_tool", wildcard_config) is True
    assert filter.is_tool_allowed("test_analyzer", wildcard_config) is True
    assert filter.is_tool_allowed("code_analyzer", wildcard_config) is True
    assert filter.is_tool_allowed("test_tool_2", wildcard_config) is True

    # 测试不匹配的情况
    assert filter.is_tool_allowed("other_tool", wildcard_config) is False


def test_is_tool_allowed_empty_list():
    """测试空允许列表（允许所有工具）"""
    from core.agents.task_tool.tool_filter import ToolFilter

    registry = SubagentRegistry()

    unrestricted_config = SubagentConfig(
        agent_type="unrestricted-agent",
        display_name="无限制代理",
        description="测试无限制",
        default_model=ModelChoice.SONNET,
        allowed_tools=[],
    )
    registry.register_agent(unrestricted_config)

    filter = ToolFilter(registry)

    # 所有工具都应该被允许
    assert filter.is_tool_allowed("any_tool", unrestricted_config) is True
    assert filter.is_tool_allowed("another_tool", unrestricted_config) is True


def test_match_pattern_basic():
    """测试基本模式匹配"""
    from core.agents.task_tool.tool_filter import ToolFilter

    registry = SubagentRegistry()
    filter = ToolFilter(registry)

    # 测试精确匹配
    assert filter._match_pattern("exact", "exact") is True
    assert filter._match_pattern("exact", "different") is False

    # 测试通配符匹配
    assert filter._match_pattern("test_*", "test_tool") is True
    assert filter._match_pattern("test_*", "test_analyzer") is True
    assert filter._match_pattern("test_*", "other_tool") is False

    # 测试后缀通配符
    assert filter._match_pattern("*_analyzer", "code_analyzer") is True
    assert filter._match_pattern("*_analyzer", "test_tool") is False

    # 测试中间通配符
    assert filter._match_pattern("test_*_tool", "test_custom_tool") is True
    assert filter._match_pattern("test_*_tool", "test_other") is False


def test_get_allowed_tools_for_agent():
    """测试获取代理的允许工具列表"""
    from core.agents.task_tool.tool_filter import ToolFilter

    registry = SubagentRegistry()
    filter = ToolFilter(registry)

    agent_config = registry.get_agent("patent-analyst")
    allowed_tools = filter.get_allowed_tools_for_agent(agent_config)

    # 验证结果
    assert len(allowed_tools) > 0
    assert "code_analyzer" in allowed_tools
    assert "knowledge_graph" in allowed_tools
    assert "patent_search" in allowed_tools


def test_filter_tools_with_multiple_patterns():
    """测试多个模式过滤"""
    from core.agents.task_tool.tool_filter import ToolFilter

    registry = SubagentRegistry()

    multi_pattern_config = SubagentConfig(
        agent_type="multi-pattern-agent",
        display_name="多模式代理",
        description="测试多模式",
        default_model=ModelChoice.SONNET,
        allowed_tools=["patent_*", "web_search", "*_analyzer"],
    )
    registry.register_agent(multi_pattern_config)

    filter = ToolFilter(registry)

    available_tools = [
        "patent_search",
        "patent_analyzer",
        "web_search",
        "code_analyzer",
        "document_processor",
        "test_tool",
    ]
    filtered_tools = filter.filter_tools(available_tools, multi_pattern_config)

    # 验证结果
    assert "patent_search" in filtered_tools  # 匹配patent_*
    assert "patent_analyzer" in filtered_tools  # 匹配patent_*和*_analyzer
    assert "web_search" in filtered_tools  # 精确匹配
    assert "code_analyzer" in filtered_tools  # 匹配*_analyzer
    assert "document_processor" not in filtered_tools  # 不匹配任何模式
    assert "test_tool" not in filtered_tools  # 不匹配任何模式
