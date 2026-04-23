"""
声明式 Agent 系统单元测试

覆盖:
- AgentDefinition 数据模型
- ToolPermissionFilter 权限过滤
- parse_frontmatter 工具函数
- AgentLoader 加载器
- DeclarativeAgent 代理
- OutputStyleManager 输出风格
- 条件化提示词组装

运行: pytest tests/test_declarative_agent.py -v -m unit
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from core.framework.agents.declarative.loader import AgentLoader
from core.framework.agents.declarative.models import (
    AgentDefinition,
    AgentPermissionMode,
    AgentSource,
)
from core.framework.agents.declarative.permissions import ToolPermissionFilter
from core.framework.agents.declarative.utils import parse_frontmatter

# ============================================================================
# AgentDefinition 测试
# ============================================================================


class TestAgentDefinition:
    """AgentDefinition 数据模型测试"""

    def test_basic_creation(self):
        d = AgentDefinition(name="test-agent", description="测试用")
        assert d.name == "test-agent"
        assert d.description == "测试用"
        assert d.tools == []
        assert d.disallowed_tools == []
        assert d.model == "default"
        assert d.permission_mode == AgentPermissionMode.DEFAULT
        assert d.is_readonly is False

    def test_readonly_mode(self):
        d = AgentDefinition(name="ro", permission_mode=AgentPermissionMode.READONLY)
        assert d.is_readonly is True

    def test_full_permission_mode(self):
        d = AgentDefinition(name="full", permission_mode=AgentPermissionMode.FULL)
        assert d.is_readonly is False

    def test_to_dict(self):
        d = AgentDefinition(name="dict-test", model="haiku")
        result = d.to_dict()
        assert result["name"] == "dict-test"
        assert result["model"] == "haiku"
        assert result["is_readonly"] is False
        assert result["permission_mode"] == "default"
        assert "system_prompt" not in result

    def test_from_frontmatter_basic(self):
        metadata = {
            "name": "frontmatter-test",
            "description": "从 frontmatter 创建",
            "tools": ["file_read", "search"],
            "model": "sonnet",
            "permission_mode": "readonly",
        }
        d = AgentDefinition.from_frontmatter(
            metadata, "正文内容", AgentSource.BUILTIN, "test.md"
        )
        assert d.name == "frontmatter-test"
        assert d.tools == ["file_read", "search"]
        assert d.model == "sonnet"
        assert d.is_readonly is True
        assert d.system_prompt == "正文内容"
        assert d.filename == "test.md"

    def test_from_frontmatter_unknown_fields_to_extra(self):
        metadata = {
            "name": "extra-test",
            "custom_field": "custom_value",
            "another_field": 42,
        }
        d = AgentDefinition.from_frontmatter(metadata, "")
        assert d.extra["custom_field"] == "custom_value"
        assert d.extra["another_field"] == 42

    def test_from_frontmatter_invalid_permission_defaults(self):
        metadata = {"name": "test", "permission_mode": "invalid_mode"}
        d = AgentDefinition.from_frontmatter(metadata, "")
        assert d.permission_mode == AgentPermissionMode.DEFAULT

    def test_from_frontmatter_fallback_name(self):
        metadata = {}
        d = AgentDefinition.from_frontmatter(metadata, "", filename="my-agent.md")
        assert d.name == "my-agent"


# ============================================================================
# parse_frontmatter 测试
# ============================================================================


class TestParseFrontmatter:
    """Frontmatter 解析测试"""

    def test_basic_frontmatter(self):
        content = "---\nname: test\nvalue: 42\n---\nBody text"
        meta, body = parse_frontmatter(content)
        assert meta["name"] == "test"
        assert meta["value"] == 42
        assert body == "Body text"

    def test_no_frontmatter(self):
        content = "Just plain text without frontmatter"
        meta, body = parse_frontmatter(content)
        assert meta == {}
        assert body == content

    def test_empty_frontmatter(self):
        content = "---\n---\nBody text"
        meta, body = parse_frontmatter(content)
        assert meta == {}
        assert body == "Body text"

    def test_invalid_yaml(self):
        content = "---\n: invalid: yaml: [}\n---\nBody"
        meta, body = parse_frontmatter(content)
        assert meta == {}
        assert body == "Body"

    def test_incomplete_frontmatter_no_closing(self):
        content = "---\nname: test\nNo closing"
        meta, body = parse_frontmatter(content)
        assert meta == {}
        assert body == content

    def test_multiline_body(self):
        content = "---\nname: test\n---\nLine 1\nLine 2\nLine 3"
        meta, body = parse_frontmatter(content)
        assert meta["name"] == "test"
        assert "Line 1" in body
        assert "Line 3" in body


# ============================================================================
# ToolPermissionFilter 测试
# ============================================================================


class TestToolPermissionFilter:
    """工具权限过滤测试"""

    def test_no_restrictions(self):
        f = ToolPermissionFilter()
        assert f.is_tool_permitted("any_tool") is True

    def test_blacklist_exact_match(self):
        f = ToolPermissionFilter(disallowed_tools=["bash"])
        assert f.is_tool_permitted("bash") is False
        assert f.is_tool_permitted("bash.run") is False  # 前缀匹配
        assert f.is_tool_permitted("file_read") is True

    def test_whitelist(self):
        f = ToolPermissionFilter(allowed_tools=["file_read", "search"])
        assert f.is_tool_permitted("file_read") is True
        assert f.is_tool_permitted("file_read.content") is True
        assert f.is_tool_permitted("bash") is False

    def test_readonly_mode(self):
        f = ToolPermissionFilter(is_readonly=True)
        assert f.is_tool_permitted("file_read") is True
        assert f.is_tool_permitted("file_write") is False
        assert f.is_tool_permitted("bash") is False
        assert f.is_tool_permitted("execute") is False

    def test_blacklist_overrides_whitelist(self):
        f = ToolPermissionFilter(
            allowed_tools=["file_read", "file_write"],
            disallowed_tools=["file_write"],
        )
        assert f.is_tool_permitted("file_read") is True
        assert f.is_tool_permitted("file_write") is False

    def test_filter_tools_list(self):
        f = ToolPermissionFilter(disallowed_tools=["bash", "execute"])
        tools = [
            {"id": "file_read", "name": "Read"},
            {"id": "bash", "name": "Shell"},
            {"id": "search", "name": "Search"},
        ]
        filtered = f.filter_tools(tools)
        assert len(filtered) == 2
        assert all(t["id"] != "bash" for t in filtered)

    def test_filter_tools_with_tool_id_key(self):
        f = ToolPermissionFilter(disallowed_tools=["bash"])
        tools = [{"tool_id": "bash", "name": "Shell"}]
        filtered = f.filter_tools(tools)
        assert len(filtered) == 0

    def test_from_definition(self):
        d = AgentDefinition(
            name="test",
            tools=["search"],
            disallowed_tools=["bash"],
            permission_mode=AgentPermissionMode.READONLY,
        )
        f = ToolPermissionFilter.from_definition(d)
        assert f.is_readonly is True
        assert f.allowed_tools == ["search"]
        assert f.disallowed_tools == ["bash"]

    def test_get_readonly_filter(self):
        f = ToolPermissionFilter.get_readonly_filter()
        assert f.is_readonly is True
        assert f.is_tool_permitted("file_read") is True
        assert f.is_tool_permitted("file_write") is False


# ============================================================================
# AgentLoader 测试
# ============================================================================


class TestAgentLoader:
    """Agent 加载器测试"""

    def test_load_builtin_agents(self):
        loader = AgentLoader()
        agents = loader.load_all()
        assert len(agents) >= 3
        assert "explorer" in agents
        assert "planner" in agents
        assert "researcher" in agents

    def test_get_agent_by_name(self):
        loader = AgentLoader()
        agent = loader.get("explorer")
        assert agent is not None
        assert agent.name == "explorer"
        assert agent.model == "haiku"

    def test_get_nonexistent_agent(self):
        loader = AgentLoader()
        assert loader.get("nonexistent") is None

    def test_list_names(self):
        loader = AgentLoader()
        names = loader.list_names()
        assert "explorer" in names

    def test_project_overrides_builtin(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            athena_dir = Path(tmpdir) / ".athena" / "agents"
            athena_dir.mkdir(parents=True)
            (athena_dir / "explorer.md").write_text(
                "---\nname: explorer\ndescription: 覆盖版\nmodel: opus\n---\n覆盖提示词",
                encoding="utf-8",
            )
            loader = AgentLoader(project_root=tmpdir)
            agents = loader.load_all()
            assert agents["explorer"].model == "opus"
            assert agents["explorer"].source == AgentSource.PROJECT

    def test_force_reload(self):
        loader = AgentLoader()
        agents1 = loader.load_all()
        agents2 = loader.load_all(force_reload=True)
        assert set(agents1.keys()) == set(agents2.keys())

    def test_custom_agent_from_project_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            athena_dir = Path(tmpdir) / ".athena" / "agents"
            athena_dir.mkdir(parents=True)
            (athena_dir / "my-custom.md").write_text(
                "---\nname: my-custom\ndescription: 自定义\nmodel: sonnet\n---\n自定义提示词",
                encoding="utf-8",
            )
            loader = AgentLoader(project_root=tmpdir)
            agents = loader.load_all()
            assert "my-custom" in agents
            assert agents["my-custom"].system_prompt == "自定义提示词"

    def test_malformed_file_skipped(self):
        """格式错误的 .md 文件应被跳过而非报错"""
        with tempfile.TemporaryDirectory() as tmpdir:
            athena_dir = Path(tmpdir) / ".athena" / "agents"
            athena_dir.mkdir(parents=True)
            (athena_dir / "bad.md").write_bytes(b"\x00\x01\x02\xff\xfe")
            loader = AgentLoader(project_root=tmpdir)
            agents = loader.load_all()
            assert "bad" not in agents
            # 不应崩溃，内置 Agent 应仍正常
            assert "explorer" in agents


# ============================================================================
# DeclarativeAgent 测试
# ============================================================================


class TestDeclarativeAgent:
    """声明式 Agent 代理测试"""

    def _create_test_agent(self, **kwargs):
        """创建测试用 Agent 定义和实例"""
        defaults = {
            "name": "test-agent",
            "description": "测试 Agent",
            "model": "default",
            "system_prompt": "你是一个测试助手",
            "permission_mode": AgentPermissionMode.DEFAULT,
        }
        defaults.update(kwargs)
        definition = AgentDefinition(**defaults)

        from core.framework.agents.declarative.proxy import DeclarativeAgent

        agent_cls = DeclarativeAgent.from_definition(definition)
        return agent_cls(), definition

    def test_name_property(self):
        agent, _ = self._create_test_agent()
        assert agent.name == "test-agent"

    def test_permission_filter_default(self):
        agent, _ = self._create_test_agent()
        filt = agent._get_permission_filter()
        assert filt is not None
        assert filt.is_readonly is False

    def test_permission_filter_readonly(self):
        agent, _ = self._create_test_agent(
            permission_mode=AgentPermissionMode.READONLY,
            disallowed_tools=["bash"],
        )
        filt = agent._get_permission_filter()
        assert filt.is_readonly is True
        assert filt.is_tool_permitted("bash") is False

    def test_initialize_and_shutdown(self):
        agent, _ = self._create_test_agent()
        asyncio.run(agent.initialize())
        assert agent.status.value == "ready"
        asyncio.run(agent.shutdown())
        assert agent.status.value == "shutdown"

    def test_health_check(self):
        agent, _ = self._create_test_agent()
        asyncio.run(agent.initialize())
        health = asyncio.run(agent.health_check())
        assert health.is_healthy()

    def test_process_no_message_returns_error(self):
        from core.framework.agents.base import AgentRequest

        agent, _ = self._create_test_agent()
        asyncio.run(agent.initialize())
        req = AgentRequest(request_id="t1", action="test", parameters={})
        resp = asyncio.run(agent.process(req))
        # 无消息时，LLM 不可用返回 fallback（success=True）
        # 或有 LLM 时返回 error（success=False）
        if resp.success:
            assert resp.data.get("status") == "fallback"
        else:
            assert "未包含" in (resp.error or "")

    def test_process_with_message_returns_response(self):
        from core.framework.agents.base import AgentRequest

        agent, _ = self._create_test_agent()
        asyncio.run(agent.initialize())
        req = AgentRequest(
            request_id="t2",
            action="test",
            parameters={"message": "hello"},
        )
        resp = asyncio.run(agent.process(req))
        # LLM 可能不可用（fallback），但不应抛异常
        assert resp.success is True
        assert resp.data.get("status") in ("completed", "fallback")

    def test_readonly_agent_blocks_write_tools(self):
        agent, _ = self._create_test_agent(
            permission_mode=AgentPermissionMode.READONLY,
        )
        asyncio.run(agent.initialize())
        result = asyncio.run(agent.call_tool("file_write", {"path": "/tmp/test"}))
        assert result["success"] is False


# ============================================================================
# 条件化提示词测试
# ============================================================================


class TestConditionalPrompts:
    """条件化提示词组装测试"""

    def test_default_sections_count(self):
        from core.framework.agents.prompts.xiaona_prompts import get_system_prompt

        sections = get_system_prompt()
        assert len(sections) >= 4  # L1 + security + verbosity + 至少一个 L 层

    def test_concise_style_injected(self):
        from core.framework.agents.prompts.xiaona_prompts import (
            OutputStyleType,
            PromptOptions,
            get_system_prompt,
        )

        opts = PromptOptions(output_style=OutputStyleType.CONCISE)
        sections = get_system_prompt(opts)
        full = "\n".join(sections)
        assert "极简" in full

    def test_exclude_layers(self):
        from core.framework.agents.prompts.xiaona_prompts import PromptOptions, get_system_prompt

        opts = PromptOptions(
            include_data_layer=False,
            include_capability_layer=False,
            include_business_layer=False,
        )
        sections = get_system_prompt(opts)
        full = "\n".join(sections)
        assert "Qdrant" not in full
        assert "10大核心" not in full
        assert "强制HITL" not in full

    def test_readonly_section_injected(self):
        from core.framework.agents.prompts.xiaona_prompts import PromptOptions, get_system_prompt

        opts = PromptOptions(is_readonly=True)
        sections = get_system_prompt(opts)
        full = "\n".join(sections)
        assert "只读模式" in full

    def test_task_section_oa_response(self):
        from core.framework.agents.prompts.xiaona_prompts import (
            PromptOptions,
            TaskType,
            get_system_prompt,
        )

        opts = PromptOptions(task_type=TaskType.OA_RESPONSE)
        sections = get_system_prompt(opts)
        full = "\n".join(sections)
        assert "审查意见" in full

    def test_model_adaptation(self):
        from core.framework.agents.prompts.xiaona_prompts import (
            PromptOptions,
            get_system_prompt,
        )

        opts = PromptOptions(model_name="haiku")
        sections = get_system_prompt(opts)
        full = "\n".join(sections)
        assert "Haiku" in full

    def test_backward_compatible_constants(self):
        """确保旧版常量仍可导入"""
        from core.framework.agents.prompts.xiaona_prompts import (
            XIAONA_L1_FOUNDATION,
            XiaonaPrompts,
        )

        assert len(XIAONA_L1_FOUNDATION) > 100
        p = XiaonaPrompts()
        full = p.get_full_prompt()
        assert "小娜" in full


# ============================================================================
# OutputStyleManager 测试
# ============================================================================


class TestOutputStyleManager:
    """输出风格管理器测试"""

    def test_load_builtin_styles(self):
        from core.ai.prompts.output_styles import OutputStyleManager

        mgr = OutputStyleManager()
        styles = mgr.load_all_styles()
        assert len(styles) >= 4
        assert "default" in styles
        assert "professional" in styles
        assert "educational" in styles
        assert "concise" in styles

    def test_set_and_get_style(self):
        from core.ai.prompts.output_styles import OutputStyleManager

        mgr = OutputStyleManager()
        mgr.load_all_styles()
        mgr.set_current_style("concise")
        current = mgr.get_current_style()
        assert current is not None
        assert current.name == "concise"

    def test_default_style_returns_none(self):
        from core.ai.prompts.output_styles import OutputStyleManager

        mgr = OutputStyleManager()
        mgr.load_all_styles()
        mgr.set_current_style("default")
        assert mgr.get_current_style() is None

    def test_reset_style(self):
        from core.ai.prompts.output_styles import OutputStyleManager

        mgr = OutputStyleManager()
        mgr.load_all_styles()
        mgr.set_current_style("professional")
        mgr.reset_style()
        assert mgr.get_current_style() is None

    def test_style_prompt_additions(self):
        from core.ai.prompts.output_styles import OutputStyleManager

        mgr = OutputStyleManager()
        mgr.load_all_styles()
        mgr.set_current_style("professional")
        additions = mgr.get_style_prompt_additions()
        assert len(additions) == 1
        assert "法律专业模式" in additions[0]

    def test_invalid_style_raises(self):
        from core.ai.prompts.output_styles import OutputStyleManager

        mgr = OutputStyleManager()
        mgr.load_all_styles()
        with pytest.raises(ValueError, match="未知风格"):
            mgr.set_current_style("nonexistent")

    def test_list_styles(self):
        from core.ai.prompts.output_styles import OutputStyleManager

        mgr = OutputStyleManager()
        styles = mgr.list_styles()
        names = [s["name"] for s in styles]
        assert "default" in names
        assert "concise" in names

    def test_custom_style_loading(self):
        from core.ai.prompts.output_styles import OutputStyleManager

        with tempfile.TemporaryDirectory() as tmpdir:
            style_dir = Path(tmpdir) / ".athena" / "output-styles"
            style_dir.mkdir(parents=True)
            (style_dir / "my-style.md").write_text(
                "---\nname: my-style\ndescription: 我的风格\n---\n自定义提示词",
                encoding="utf-8",
            )
            mgr = OutputStyleManager(project_root=tmpdir)
            styles = mgr.load_all_styles()
            assert "my-style" in styles
            assert styles["my-style"].prompt == "自定义提示词"


# ============================================================================
# Schema 验证测试
# ============================================================================


class TestSchemaValidation:
    """Frontmatter schema 验证测试"""

    def test_tools_non_list_auto_corrected(self):
        """tools 字段不是列表时应自动修正为空列表"""
        metadata = {"name": "bad-tools", "tools": "not_a_list"}
        d = AgentDefinition.from_frontmatter(metadata, "")
        assert d.tools == []

    def test_disallowed_tools_non_list_auto_corrected(self):
        """disallowed_tools 字段不是列表时应自动修正"""
        metadata = {"name": "bad-dt", "disallowed_tools": 123}
        d = AgentDefinition.from_frontmatter(metadata, "")
        assert d.disallowed_tools == []

    def test_unknown_model_falls_back_to_default(self):
        """未知模型名称应回退到 default"""
        metadata = {"name": "bad-model", "model": "nonexistent-gpt-99"}
        d = AgentDefinition.from_frontmatter(metadata, "")
        assert d.model == "default"

    def test_valid_model_accepted(self):
        """有效模型名称应被接受"""
        for model in ("default", "haiku", "sonnet", "opus"):
            d = AgentDefinition(name=f"test-{model}", model=model)
            assert d.model == model

    def test_empty_name_uses_filename(self):
        """空名称应使用文件名"""
        metadata = {"name": ""}
        d = AgentDefinition.from_frontmatter(metadata, "", filename="fallback.md")
        assert d.name == "fallback"

    def test_invalid_permission_mode_logs_warning(self):
        """无效权限模式应回退到 default"""
        metadata = {"name": "test", "permission_mode": "superadmin"}
        d = AgentDefinition.from_frontmatter(metadata, "")
        assert d.permission_mode == AgentPermissionMode.DEFAULT


# ============================================================================
# 线程安全测试
# ============================================================================


class TestThreadSafety:
    """单例线程安全测试"""

    def test_get_loader_thread_safe(self):
        """多个线程同时获取 loader 应返回同一实例"""
        from concurrent.futures import ThreadPoolExecutor

        # 重置单例
        import core.agents.declarative.loader as loader_mod

        from core.framework.agents.declarative.loader import get_loader
        loader_mod._loader_instance = None

        loaders = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_loader) for _ in range(10)]
            for f in futures:
                loaders.append(f.result())

        # 所有线程应获得同一个实例
        assert all(l is loaders[0] for l in loaders)

    def test_get_style_manager_thread_safe(self):
        """多个线程同时获取 style manager 应返回同一实例"""
        from concurrent.futures import ThreadPoolExecutor

        # 重置单例
        import core.prompts.output_styles as styles_mod

        from core.ai.prompts.output_styles import get_style_manager
        styles_mod._manager_instance = None

        managers = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_style_manager) for _ in range(10)]
            for f in futures:
                managers.append(f.result())

        # 所有线程应获得同一个实例
        assert all(m is managers[0] for m in managers)


# ============================================================================
# Bug 修复回归测试
# ============================================================================


class TestBugFixes:
    """修复回归测试 + 新增边界条件测试"""

    def test_readonly_no_false_positive_substring(self):
        """只读模式不应误杀包含写入关键字的合法工具"""
        f = ToolPermissionFilter(is_readonly=True)
        # "description_writer" 包含 "file_write" 的子串... 不再误杀
        assert f.is_tool_permitted("description_writer") is True
        assert f.is_tool_permitted("get_write_status") is True
        # 但真正的写入工具应被禁止
        assert f.is_tool_permitted("file_write") is False
        assert f.is_tool_permitted("file_write.content") is False
        assert f.is_tool_permitted("file_write_something") is False

    def test_tools_list_elements_coerced_to_str(self):
        """tools 列表元素应被强制转换为字符串"""
        metadata = {"name": "test", "tools": [123, "search", None]}
        d = AgentDefinition.from_frontmatter(metadata, "")
        assert all(isinstance(t, str) for t in d.tools)
        assert "123" in d.tools
        assert "None" in d.tools
        assert "search" in d.tools

    def test_load_all_agents_exception_returns_empty(self):
        """load_all_agents 异常时应返回空列表而非崩溃"""
        loader = AgentLoader(project_root="/nonexistent/path/that/does/not/exist")
        # 不应崩溃
        agents = loader.load_all()
        assert isinstance(agents, dict)

    def test_get_style_manager_does_not_override_singleton(self):
        """get_style_manager 带 project_root 不应覆盖已有单例"""
        # 重置单例
        import core.prompts.output_styles as styles_mod

        from core.ai.prompts.output_styles import get_style_manager
        styles_mod._manager_instance = None

        mgr1 = get_style_manager()
        mgr2 = get_style_manager(project_root="/tmp")
        # mgr2 应是新实例
        assert mgr2 is not mgr1
        # 全局单例未被覆盖
        mgr3 = get_style_manager()
        assert mgr3 is mgr1

    def test_get_loader_does_not_override_singleton(self):
        """get_loader 带 project_root 不应覆盖已有单例"""
        # 重置单例
        import core.agents.declarative.loader as loader_mod

        from core.framework.agents.declarative.loader import get_loader
        loader_mod._loader_instance = None

        loader1 = get_loader()
        loader2 = get_loader(project_root="/tmp")
        assert loader2 is not loader1
        loader3 = get_loader()
        assert loader3 is loader1

    def test_filter_tools_non_string_id(self):
        """filter_tools 中工具 ID 为非字符串时应优雅处理"""
        f = ToolPermissionFilter()
        tools = [{"id": 12345, "name": "WeirdTool"}]
        filtered = f.filter_tools(tools)
        assert len(filtered) == 1  # 不应崩溃
