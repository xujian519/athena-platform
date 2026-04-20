#!/usr/bin/env python3
"""
P0系统端到端集成测试

测试Skills、Plugins和会话记忆系统的协同工作。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import logging
import pytest
import tempfile

logger = logging.getLogger(__name__)

from core.skills.loader import SkillLoader
from core.skills.registry import SkillRegistry
from core.skills.tool_mapper import SkillToolMapper
from core.plugins.loader import PluginLoader as PluginLoader
from core.plugins.registry import PluginRegistry
from core.memory.sessions.manager import SessionManager
from core.memory.sessions.storage import FileSessionStorage
from core.memory.sessions.types import MessageRole, SessionStatus


class TestP0Integration:
    """P0系统集成测试"""

    @pytest.fixture(scope="class")
    def skill_registry(self):
        """创建技能注册表"""
        registry = SkillRegistry()
        loader = SkillLoader(registry)
        loader.load_from_directory("core/skills/bundled")
        return registry

    @pytest.fixture(scope="class")
    def plugin_registry(self):
        """创建插件注册表"""
        registry = PluginRegistry()
        loader = PluginLoader(registry)
        loader.load_from_directory("core/plugins/bundled")
        return registry

    @pytest.fixture(scope="function")
    def session_manager(self):
        """创建会话管理器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileSessionStorage(temp_dir)
            manager = SessionManager(storage=storage)
            yield manager

    def test_skills_plugins_integration(
        self,
        skill_registry,
        plugin_registry,
    ):
        """测试Skills与Plugins系统集成"""
        # 1. 验证技能已加载
        patent_skill = skill_registry.get_skill("patent_analysis")
        assert patent_skill is not None
        assert patent_skill.id == "patent_analysis"

        # 2. 验证插件已加载
        patent_plugin = plugin_registry.get_plugin("patent_analyzer_plugin")
        assert patent_plugin is not None
        assert patent_plugin.id == "patent_analyzer_plugin"

        # 3. 验证技能与插件的关联
        # patent_analysis技能使用patent_analyzer插件提供的工具
        assert "patent_analyzer" in patent_skill.tools

        # 4. 验证插件提供的技能
        assert "patent_analysis" in patent_plugin.skills

        logger.info("✅ Skills与Plugins系统集成测试通过")

    def test_session_with_skills(
        self,
        skill_registry,
        session_manager,
    ):
        """测试会话与Skills系统集成"""
        # 1. 创建会话
        session = session_manager.create_session(
            session_id="test_session_001",
            user_id="user123",
            agent_id="xiaona",
        )

        # 2. 添加用户消息
        session_manager.add_message(
            session_id="test_session_001",
            role=MessageRole.USER,
            content="帮我分析专利CN123456789A",
            token_count=15,
        )

        # 3. 获取技能
        patent_skill = skill_registry.get_skill("patent_analysis")
        assert patent_skill is not None

        # 4. 模拟使用技能（添加助手消息）
        session_manager.add_message(
            session_id="test_session_001",
            role=MessageRole.ASSISTANT,
            content=f"使用 {patent_skill.name} 分析专利...",
            token_count=20,
        )

        # 5. 验证会话状态
        messages = session_manager.get_session_messages("test_session_001")
        assert len(messages) == 2
        assert messages[0].role == MessageRole.USER
        assert messages[1].role == MessageRole.ASSISTANT

        logger.info("✅ 会话与Skills系统集成测试通过")

    def test_tool_mapping_consistency(
        self,
        skill_registry,
    ):
        """测试工具映射一致性"""
        # 1. 创建工具映射器
        mapper = SkillToolMapper(skill_registry)

        # 2. 获取工具到技能的映射
        tool_to_skills = mapper.map_tools_to_skills()

        # 3. 验证映射完整性
        assert len(tool_to_skills) > 0

        # 4. 验证每个工具都有对应的技能
        for tool_id, skill_ids in tool_to_skills.items():
            assert len(skill_ids) > 0
            # 验证技能确实使用该工具
            for skill_id in skill_ids:
                skill = skill_registry.get_skill(skill_id)
                assert tool_id in skill.tools

        # 5. 验证没有工具冲突
        conflicts = mapper.detect_tool_conflicts()
        # 目前bundled skills没有冲突
        assert len(conflicts) == 0

        logger.info("✅ 工具映射一致性测试通过")

    def test_multi_skill_workflow(
        self,
        skill_registry,
        session_manager,
    ):
        """测试多技能工作流"""
        # 1. 创建会话
        session = session_manager.create_session(
            session_id="test_session_002",
            user_id="user456",
            agent_id="xiaona",
        )

        # 2. 用户：检索专利
        session_manager.add_message(
            session_id="test_session_002",
            role=MessageRole.USER,
            content="检索专利CN123456789A的相关文献",
            token_count=12,
        )

        # 3. Agent：使用检索技能
        case_skill = skill_registry.get_skill("case_retrieval")
        session_manager.add_message(
            session_id="test_session_002",
            role=MessageRole.ASSISTANT,
            content=f"使用 {case_skill.name} 检索到5篇相关文献",
            token_count=18,
        )

        # 4. 用户：分析专利
        session_manager.add_message(
            session_id="test_session_002",
            role=MessageRole.USER,
            content="现在分析专利的创造性",
            token_count=10,
        )

        # 5. Agent：使用分析技能
        patent_skill = skill_registry.get_skill("patent_analysis")
        session_manager.add_message(
            session_id="test_session_002",
            role=MessageRole.ASSISTANT,
            content=f"使用 {patent_skill.name} 完成创造性分析",
            token_count=22,
        )

        # 6. 验证工作流
        messages = session_manager.get_session_messages("test_session_002")
        assert len(messages) == 4

        # 验证使用了多个技能
        used_skills = set()
        for msg in messages:
            if msg.role == MessageRole.ASSISTANT:
                if case_skill.id in msg.content or case_skill.name in msg.content:
                    used_skills.add(case_skill.id)
                if patent_skill.id in msg.content or patent_skill.name in msg.content:
                    used_skills.add(patent_skill.id)

        assert case_skill.id in used_skills
        assert patent_skill.id in used_skills

        logger.info("✅ 多技能工作流测试通过")

    def test_session_lifecycle(
        self,
        skill_registry,
        session_manager,
    ):
        """测试会话完整生命周期"""
        session_id = "test_session_003"

        # 1. 创建会话
        session = session_manager.create_session(
            session_id=session_id,
            user_id="user789",
            agent_id="xiaona",
        )
        assert session.context.status == SessionStatus.ACTIVE

        # 2. 添加交互
        session_manager.add_message(
            session_id,
            MessageRole.USER,
            "Hello",
            token_count=5,
        )
        session_manager.add_message(
            session_id,
            MessageRole.ASSISTANT,
            "Hi there!",
            token_count=3,
        )

        # 3. 关闭会话
        success = session_manager.close_session(session_id)
        assert success is True

        # 4. 验证会话状态
        session = session_manager.get_session(session_id)
        assert session.context.status == SessionStatus.CLOSED

        # 5. 验证持久化
        assert session_manager.storage.exists(session_id)

        # 6. 重新加载会话
        loaded = session_manager.storage.load(session_id)
        assert loaded is not None
        assert loaded.context.session_id == session_id
        assert len(loaded.messages) == 2

        logger.info("✅ 会话生命周期测试通过")

    def test_concurrent_sessions(
        self,
        skill_registry,
        session_manager,
    ):
        """测试并发会话处理"""
        # 1. 创建多个会话
        session_ids = []
        for i in range(5):
            session_id = f"concurrent_session_{i}"
            session_ids.append(session_id)

            session_manager.create_session(
                session_id=session_id,
                user_id=f"user{i}",
                agent_id="xiaona",
            )

            # 添加消息
            session_manager.add_message(
                session_id=session_id,
                role=MessageRole.USER,
                content=f"Message {i}",
                token_count=5,
            )

        # 2. 验证所有会话都创建成功
        active_sessions = session_manager.get_active_sessions()
        assert len(active_sessions) == 5

        # 3. 验证会话统计
        stats = session_manager.get_session_stats()
        assert stats["total_sessions"] == 5
        assert stats["active_sessions"] == 5
        assert stats["total_messages"] == 5

        # 4. 关闭所有会话
        for session_id in session_ids:
            session_manager.close_session(session_id)

        # 5. 验证会话都已关闭
        active_sessions = session_manager.get_active_sessions()
        assert len(active_sessions) == 0

        logger.info("✅ 并发会话测试通过")

    def test_skill_tool_execution_flow(
        self,
        skill_registry,
        plugin_registry,
        session_manager,
    ):
        """测试技能-工具执行流程"""
        # 1. 创建会话
        session_manager.create_session(
            session_id="test_session_004",
            user_id="user000",
            agent_id="xiaona",
        )

        # 2. 用户请求
        session_manager.add_message(
            session_id="test_session_004",
            role=MessageRole.USER,
            content="分析专利CN123456789A",
            token_count=10,
        )

        # 3. 选择技能
        skill = skill_registry.get_skill("patent_analysis")
        assert skill is not None

        # 4. 获取技能的工具
        tools = skill.tools
        assert len(tools) > 0

        # 5. 模拟执行工具（添加响应）
        response = f"使用技能 {skill.name}，执行工具: {', '.join(tools)}"
        session_manager.add_message(
            session_id="test_session_004",
            role=MessageRole.ASSISTANT,
            content=response,
            token_count=len(response.split()),
        )

        # 6. 验证消息
        messages = session_manager.get_session_messages("test_session_004")
        assert len(messages) == 2

        # 7. 生成会话摘要
        summary = session_manager.generate_session_summary(
            session_id="test_session_004",
            title="专利分析会话",
            summary="用户咨询专利CN123456789A的创造性",
            key_points=["专利检索", "创造性分析"],
            tags=["专利", "分析"],
        )

        assert summary is not None
        assert summary.title == "专利分析会话"

        logger.info("✅ 技能-工具执行流程测试通过")


class TestP0Performance:
    """P0系统性能测试"""

    def test_skill_loading_performance(self):
        """测试技能加载性能"""
        import time

        registry = SkillRegistry()
        loader = SkillLoader(registry)

        # 测试加载性能
        start = time.time()
        skills = loader.load_from_directory("core/skills/bundled")
        elapsed = time.time() - start

        # 验证性能
        assert elapsed < 1.0  # 应在1秒内完成
        assert len(skills) == 4

        logger.info(f"✅ 技能加载性能: {elapsed:.3f}s (< 1.0s)")

    def test_plugin_loading_performance(self):
        """测试插件加载性能"""
        import time

        registry = PluginRegistry()
        loader = PluginLoader(registry)

        # 测试加载性能
        start = time.time()
        plugins = loader.load_from_directory("core/plugins/bundled")
        elapsed = time.time() - start

        # 验证性能
        assert elapsed < 1.0  # 应在1秒内完成
        assert len(plugins) == 3

        logger.info(f"✅ 插件加载性能: {elapsed:.3f}s (< 1.0s)")

    def test_session_operations_performance(self):
        """测试会话操作性能"""
        import time

        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileSessionStorage(temp_dir)
            manager = SessionManager(storage=storage)

            # 测试创建会话性能
            start = time.time()
            session = manager.create_session("perf_test", "user", "agent")
            create_time = time.time() - start

            assert create_time < 0.01  # 应在10ms内完成

            # 测试添加消息性能
            start = time.time()
            for i in range(100):
                manager.add_message(
                    "perf_test",
                    MessageRole.USER,
                    f"Message {i}",
                    token_count=5,
                )
            add_time = time.time() - start

            assert add_time < 0.5  # 100条消息应在500ms内完成

            # 测试查询性能
            start = time.time()
            messages = manager.get_session_messages("perf_test")
            query_time = time.time() - start

            assert query_time < 0.01  # 查询应在10ms内完成
            assert len(messages) == 100

            logger.info(f"✅ 会话操作性能:")
            logger.info(f"  创建: {create_time*1000:.2f}ms")
            logger.info(f"  添加100条消息: {add_time*1000:.2f}ms")
            logger.info(f"  查询: {query_time*1000:.2f}ms")


class TestP0ErrorHandling:
    """P0系统错误处理测试"""

    @pytest.fixture(scope="class")
    def skill_registry(self):
        """创建技能注册表"""
        registry = SkillRegistry()
        loader = SkillLoader(registry)
        loader.load_from_directory("core/skills/bundled")
        return registry

    @pytest.fixture(scope="class")
    def plugin_registry(self):
        """创建插件注册表"""
        registry = PluginRegistry()
        loader = PluginLoader(registry)
        loader.load_from_directory("core/plugins/bundled")
        return registry

    @pytest.fixture(scope="function")
    def session_manager(self):
        """创建会话管理器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileSessionStorage(temp_dir)
            manager = SessionManager(storage=storage)
            yield manager

    def test_skill_not_found(self, skill_registry):
        """测试技能不存在"""
        skill = skill_registry.get_skill("nonexistent_skill")
        assert skill is None

    def test_plugin_not_found(self, plugin_registry):
        """测试插件不存在"""
        plugin = plugin_registry.get_plugin("nonexistent_plugin")
        assert plugin is None

    def test_session_not_found(self, session_manager):
        """测试会话不存在"""
        session = session_manager.get_session("nonexistent_session")
        assert session is None

    def test_duplicate_skill_registration(self, skill_registry):
        """测试重复技能注册"""
        from core.skills.types import SkillDefinition, SkillCategory

        skill = SkillDefinition(
            id="dup_test",
            name="Duplicate Test",
            category=SkillCategory.ANALYSIS,
            description="Test",
        )

        skill_registry.register(skill)

        # 尝试重复注册应抛出错误
        with pytest.raises(ValueError, match="already registered"):
            skill_registry.register(skill)

    def test_duplicate_plugin_registration(self, plugin_registry):
        """测试重复插件注册"""
        from core.plugins.types import PluginDefinition, PluginType

        plugin = PluginDefinition(
            id="dup_test",
            name="Duplicate Test",
            type=PluginType.TOOL,
        )

        plugin_registry.register(plugin)

        # 尝试重复注册应抛出错误
        with pytest.raises(ValueError, match="already registered"):
            plugin_registry.register(plugin)


def setup_logger():
    """设置日志"""
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


if __name__ == "__main__":
    import sys

    setup_logger()

    # 运行测试
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
