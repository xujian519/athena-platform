"""
统一记忆系统单元测试

测试覆盖：
- 全局记忆写入和读取
- 项目记忆写入和读取
- 记忆索引更新
- 工作历史追加
- 搜索功能
- 错误处理
"""

from __future__ import annotations

import tempfile  # noqa: ARG001 (used in fixtures)
from datetime import datetime
from pathlib import Path
from unittest.mock import patch  # noqa: ARG001 (used in tests)

import pytest

from core.memory.unified_memory_system import (
    MemoryCategory,
    MemoryEntry,
    MemoryType,
    UnifiedMemorySystem,
    get_global_memory,
    get_project_memory,
)


class TestMemoryTypeAndCategory:
    """测试记忆类型和分类枚举"""

    def test_memory_type_enum(self) -> None:
        """测试MemoryType枚举"""
        assert MemoryType.GLOBAL.value == "global"
        assert MemoryType.PROJECT.value == "project"

    def test_memory_category_enum(self) -> None:
        """测试MemoryCategory枚举"""
        assert MemoryCategory.USER_PREFERENCE.value == "user_preference"
        assert MemoryCategory.AGENT_LEARNING.value == "agent_learning"
        assert MemoryCategory.PROJECT_CONTEXT.value == "project_context"
        assert MemoryCategory.WORK_HISTORY.value == "work_history"
        assert MemoryCategory.AGENT_COLLABORATION.value == "agent_collaboration"
        assert MemoryCategory.TECHNICAL_FINDINGS.value == "technical_findings"
        assert MemoryCategory.LEGAL_ANALYSIS.value == "legal_analysis"


class TestMemoryEntry:
    """测试记忆条目数据类"""

    def test_memory_entry_creation(self) -> None:
        """测试MemoryEntry创建"""
        entry = MemoryEntry(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="test_key",
            content="测试内容",
            metadata={"author": "test"}
        )

        assert entry.type == MemoryType.GLOBAL
        assert entry.category == MemoryCategory.USER_PREFERENCE
        assert entry.key == "test_key"
        assert entry.content == "测试内容"
        assert entry.metadata == {"author": "test"}
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.updated_at, datetime)
        assert entry.embedding is None

    def test_memory_entry_with_embedding(self) -> None:
        """测试带向量嵌入的MemoryEntry"""
        embedding = [0.1, 0.2, 0.3]
        entry = MemoryEntry(
            type=MemoryType.PROJECT,
            category=MemoryCategory.WORK_HISTORY,
            key="test",
            content="内容",
            embedding=embedding
        )

        assert entry.embedding == embedding


class TestUnifiedMemorySystem:
    """测试统一记忆系统"""

    @pytest.fixture
    def temp_global_path(self) -> Path:
        """创建临时全局记忆路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def temp_project_path(self) -> Path:
        """创建临时项目路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def memory_system(
        self,
        temp_global_path: Path,
        temp_project_path: Path
    ) -> UnifiedMemorySystem:
        """创建记忆系统实例"""
        return UnifiedMemorySystem(
            global_memory_path=str(temp_global_path),
            current_project_path=str(temp_project_path)
        )

    @pytest.fixture
    def global_only_system(
        self,
        temp_global_path: Path
    ) -> UnifiedMemorySystem:
        """创建只有全局记忆的系统"""
        return UnifiedMemorySystem(
            global_memory_path=str(temp_global_path),
            current_project_path=None
        )

    def test_initialization_with_project(
        self,
        temp_global_path: Path,
        temp_project_path: Path
    ) -> None:
        """测试初始化（带项目路径）"""
        system = UnifiedMemorySystem(
            global_memory_path=str(temp_global_path),
            current_project_path=str(temp_project_path)
        )

        # 验证目录创建
        assert temp_global_path.exists()
        assert (temp_project_path / ".athena").exists()
        assert (temp_global_path / "agent_learning").exists()
        assert (temp_project_path / ".athena" / "project_knowledge").exists()

        # 验证索引初始化
        assert isinstance(system.memory_index, dict)

    def test_initialization_without_project(
        self,
        temp_global_path: Path
    ) -> None:
        """测试初始化（无项目路径）"""
        system = UnifiedMemorySystem(
            global_memory_path=str(temp_global_path),
            current_project_path=None
        )

        # 验证全局目录创建
        assert temp_global_path.exists()
        assert (temp_global_path / "agent_learning").exists()

        # 验证索引初始化
        assert isinstance(system.memory_index, dict)

    def test_write_global_memory(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试写入全局记忆"""
        content = "# 用户偏好\n\n代码风格：简体中文注释"
        entry = memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="user_preferences",
            content=content,
            metadata={"version": "1.0"}
        )

        # 验证返回值
        assert isinstance(entry, MemoryEntry)
        assert entry.type == MemoryType.GLOBAL
        assert entry.key == "user_preferences"

        # 验证文件创建
        file_path = (
            memory_system.global_memory_path /
            "user_preferences.md"
        )
        assert file_path.exists()

        # 验证文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            assert f.read() == content

    def test_write_project_memory(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试写入项目记忆"""
        content = "# 项目上下文\n\n项目名称：测试项目"
        entry = memory_system.write(
            type=MemoryType.PROJECT,
            category=MemoryCategory.PROJECT_CONTEXT,
            key="project_context",
            content=content,
            metadata={"project": "test"}
        )

        # 验证返回值
        assert entry.type == MemoryType.PROJECT
        assert entry.key == "project_context"

        # 验证文件创建
        project_path = memory_system.current_project_path
        assert project_path is not None
        file_path = project_path / ".athena" / "project_context.md"
        assert file_path.exists()

    def test_write_agent_learning_memory(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试写入智能体学习记忆"""
        content = "# 小娜学习成果\n\n学习了新的法律原则"
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.AGENT_LEARNING,
            key="xiaona_learning",
            content=content
        )

        # 验证文件创建在子目录
        file_path = (
            memory_system.global_memory_path /
            "agent_learning" /
            "xiaona_learning.md"
        )
        assert file_path.exists()

    def test_write_project_knowledge_memory(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试写入项目知识记忆"""
        content = "# 技术发现\n\n发现了新的技术方案"
        memory_system.write(
            type=MemoryType.PROJECT,
            category=MemoryCategory.TECHNICAL_FINDINGS,
            key="technical_findings",
            content=content
        )

        # 验证文件创建在子目录
        project_path = memory_system.current_project_path
        assert project_path is not None
        file_path = (
            project_path /
            ".athena" /
            "project_knowledge" /
            "technical_findings.md"
        )
        assert file_path.exists()

    def test_write_project_memory_without_project_path(
        self,
        global_only_system: UnifiedMemorySystem
    ) -> None:
        """测试写入项目记忆但没有项目路径"""
        with pytest.raises(IOError, match="无法写入记忆"):
            global_only_system.write(
                type=MemoryType.PROJECT,
                category=MemoryCategory.PROJECT_CONTEXT,
                key="test",
                content="测试内容"
            )

    def test_read_existing_memory(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试读取存在的记忆"""
        # 先写入
        content = "# 测试内容\n\n这是测试"
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="test_read",
            content=content
        )

        # 再读取
        read_content = memory_system.read(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="test_read"
        )

        assert read_content == content

    def test_read_non_existing_memory(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试读取不存在的记忆"""
        content = memory_system.read(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="non_existing"
        )

        assert content is None

    def test_memory_index_update(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试记忆索引更新"""
        # 写入记忆
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="index_test",
            content="索引测试内容",
            metadata={"test": "data"}
        )

        # 验证索引更新
        unique_key = "global/user_preference/index_test"
        assert unique_key in memory_system.memory_index

        entry_data = memory_system.memory_index[unique_key]
        assert entry_data['type'] == "global"
        assert entry_data['category'] == "user_preference"
        assert entry_data['key'] == "index_test"
        assert entry_data['metadata'] == {"test": "data"}
        assert len(entry_data['content']) <= 500  # 索引只保存前500字符

    def test_memory_index_persistence(
        self,
        temp_global_path: Path,
        temp_project_path: Path
    ) -> None:
        """测试记忆索引持久化"""
        # 创建第一个实例并写入
        system1 = UnifiedMemorySystem(
            global_memory_path=str(temp_global_path),
            current_project_path=str(temp_project_path)
        )
        system1.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="persistence_test",
            content="持久化测试"
        )

        # 创建第二个实例（应该加载之前的索引）
        system2 = UnifiedMemorySystem(
            global_memory_path=str(temp_global_path),
            current_project_path=str(temp_project_path)
        )

        # 验证索引被正确加载
        unique_key = "global/user_preference/persistence_test"
        assert unique_key in system2.memory_index

    def test_search_basic(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试基本搜索功能"""
        # 写入多条记忆
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="pref1",
            content="代码风格：简体中文注释"
        )
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="pref2",
            content="交互风格：先规划再执行"
        )
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.AGENT_LEARNING,
            key="learning1",
            content="学习了新的检索策略"
        )

        # 搜索"代码"
        results = memory_system.search(query="代码")
        assert len(results) == 1
        assert results[0].key == "pref1"

        # 搜索"风格"
        results = memory_system.search(query="风格")
        assert len(results) == 2

    def test_search_with_type_filter(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试带类型过滤的搜索"""
        # 写入不同类型的记忆
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="global_pref",
            content="全局偏好"
        )
        memory_system.write(
            type=MemoryType.PROJECT,
            category=MemoryCategory.PROJECT_CONTEXT,
            key="project_ctx",
            content="项目上下文"
        )

        # 只搜索全局记忆
        results = memory_system.search(
            query="偏好",
            type=MemoryType.GLOBAL
        )
        assert len(results) == 1
        assert results[0].type == MemoryType.GLOBAL

    def test_search_with_category_filter(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试带分类过滤的搜索"""
        # 写入不同分类的记忆
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="pref",
            content="用户偏好"
        )
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.AGENT_LEARNING,
            key="learning",
            content="学习成果"
        )

        # 只搜索用户偏好
        results = memory_system.search(
            query="用户",
            category=MemoryCategory.USER_PREFERENCE
        )
        assert len(results) == 1
        assert results[0].category == MemoryCategory.USER_PREFERENCE

    def test_search_with_limit(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试搜索结果数量限制"""
        # 写入多条记忆
        for i in range(5):
            memory_system.write(
                type=MemoryType.GLOBAL,
                category=MemoryCategory.USER_PREFERENCE,
                key=f"pref_{i}",
                content=f"偏好设置 {i}"
            )

        # 限制返回3条
        results = memory_system.search(query="偏好", limit=3)
        assert len(results) == 3

    def test_search_case_insensitive(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试搜索不区分大小写"""
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="test",
            content="Python代码风格"
        )

        # 小写搜索
        results = memory_system.search(query="python")
        assert len(results) == 1

        # 大写搜索
        results = memory_system.search(query="PYTHON")
        assert len(results) == 1

    def test_append_work_history(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试追加工作历史"""
        # 追加第一条工作历史
        memory_system.append_work_history(
            agent_name="xiaonuo",
            task="分析专利",
            result="完成分析",
            status="success"
        )

        # 读取工作历史
        content = memory_system.read(
            type=MemoryType.PROJECT,
            category=MemoryCategory.WORK_HISTORY,
            key="work_history"
        )

        assert content is not None
        assert "xiaonuo" in content
        assert "分析专利" in content
        assert "完成分析" in content
        assert "success" in content

    def test_append_work_history_multiple_times(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试多次追加工作历史"""
        # 追加多条工作历史
        for i in range(3):
            memory_system.append_work_history(
                agent_name=f"agent_{i}",
                task=f"任务_{i}",
                result=f"结果_{i}",
                status="success"
            )

        # 读取工作历史
        content = memory_system.read(
            type=MemoryType.PROJECT,
            category=MemoryCategory.WORK_HISTORY,
            key="work_history"
        )

        assert content is not None
        assert "agent_0" in content
        assert "agent_1" in content
        assert "agent_2" in content

    def test_append_work_history_without_project_path(
        self,
        global_only_system: UnifiedMemorySystem
    ) -> None:
        """测试没有项目路径时追加工作历史"""
        with pytest.raises(ValueError, match="工作历史需要指定项目路径"):
            global_only_system.append_work_history(
                agent_name="test",
                task="test",
                result="test"
            )

    def test_get_subdirectory(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试子目录获取"""
        # 测试全局记忆分类
        assert (
            memory_system._get_subdirectory(
                MemoryCategory.AGENT_LEARNING
            ) == "agent_learning"
        )

        # 测试项目记忆分类
        assert (
            memory_system._get_subdirectory(
                MemoryCategory.TECHNICAL_FINDINGS
            ) == "project_knowledge"
        )

        # 测试未定义的分类（返回value）
        assert (
            memory_system._get_subdirectory(
                MemoryCategory.USER_PREFERENCE
            ) == ""
        )


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_global_memory(self) -> None:
        """测试获取全局记忆系统"""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = get_global_memory(global_memory_path=tmpdir)

            assert isinstance(memory, UnifiedMemorySystem)
            assert memory.global_memory_path == Path(tmpdir).expanduser()
            assert memory.current_project_path is None

    def test_get_project_memory(self) -> None:
        """测试获取项目记忆系统"""
        with tempfile.TemporaryDirectory() as tmpdir:
            global_path = Path(tmpdir) / "global"
            project_path = Path(tmpdir) / "project"

            memory = get_project_memory(
                project_path=str(project_path),
                global_memory_path=str(global_path)
            )

            assert isinstance(memory, UnifiedMemorySystem)
            assert memory.global_memory_path == global_path.expanduser()
            assert memory.current_project_path == project_path.expanduser()


class TestErrorHandling:
    """测试错误处理"""

    @pytest.fixture
    def temp_global_path(self) -> Path:
        """创建临时全局记忆路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def temp_project_path(self) -> Path:
        """创建临时项目路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def memory_system(
        self,
        temp_global_path: Path,
        temp_project_path: Path
    ) -> UnifiedMemorySystem:
        """创建记忆系统实例"""
        return UnifiedMemorySystem(
            global_memory_path=str(temp_global_path),
            current_project_path=str(temp_project_path)
        )

    def test_write_with_invalid_path(self, memory_system: UnifiedMemorySystem) -> None:
        """测试写入到无效路径"""
        # 模拟权限错误（通过patch）
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(IOError):
                memory_system.write(
                    type=MemoryType.GLOBAL,
                    category=MemoryCategory.USER_PREFERENCE,
                    key="test",
                    content="测试"
                )

    def test_read_with_corrupted_index(
        self,
        temp_global_path: Path,
        temp_project_path: Path
    ) -> None:
        """测试读取损坏的索引文件"""
        # 创建损坏的索引文件
        index_file = Path(temp_global_path) / "memory_index.json"
        index_file.write_text("invalid json{{")

        # 初始化系统（应该处理损坏的索引）
        system = UnifiedMemorySystem(
            global_memory_path=str(temp_global_path),
            current_project_path=str(temp_project_path)
        )

        # 索引应该为空字典
        assert system.memory_index == {}

    def test_search_empty_index(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试空索引搜索"""
        results = memory_system.search(query="test")
        assert results == []

    def test_write_updates_existing_entry(
        self,
        memory_system: UnifiedMemorySystem
    ) -> None:
        """测试写入更新现有条目"""
        # 第一次写入
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="update_test",
            content="原始内容"
        )

        # 第二次写入（更新）
        memory_system.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="update_test",
            content="更新后的内容"
        )

        # 验证文件被更新
        content = memory_system.read(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="update_test"
        )

        assert content == "更新后的内容"

        # 验证索引被更新
        unique_key = "global/user_preference/update_test"
        assert unique_key in memory_system.memory_index
        assert "更新后的内容" in memory_system.memory_index[unique_key]['content']


@pytest.mark.integration
class TestIntegrationScenarios:
    """集成测试场景"""

    @pytest.fixture
    def temp_global_path(self) -> Path:
        """创建临时全局记忆路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def temp_project_path(self) -> Path:
        """创建临时项目路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_complete_workflow(
        self,
        temp_global_path: Path,
        temp_project_path: Path
    ) -> None:
        """测试完整工作流程"""
        # 1. 创建记忆系统
        memory = UnifiedMemorySystem(
            global_memory_path=str(temp_global_path),
            current_project_path=str(temp_project_path)
        )

        # 2. 写入用户偏好
        memory.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.USER_PREFERENCE,
            key="user_preferences",
            content="# 用户偏好\n\n代码风格：简体中文"
        )

        # 3. 写入项目上下文
        memory.write(
            type=MemoryType.PROJECT,
            category=MemoryCategory.PROJECT_CONTEXT,
            key="project_context",
            content="# 项目上下文\n\n项目：测试项目"
        )

        # 4. 记录工作历史
        memory.append_work_history(
            agent_name="xiaonuo",
            task="初始化项目",
            result="成功",
            status="success"
        )

        # 5. 搜索记忆
        results = memory.search(query="项目")
        assert len(results) >= 1

        # 6. 读取记忆
        context = memory.read(
            type=MemoryType.PROJECT,
            category=MemoryCategory.PROJECT_CONTEXT,
            key="project_context"
        )
        assert context is not None
        assert "测试项目" in context

    def test_multi_agent_collaboration(
        self,
        temp_global_path: Path,
        temp_project_path: Path
    ) -> None:
        """测试多智能体协作场景"""
        memory = UnifiedMemorySystem(
            global_memory_path=str(temp_global_path),
            current_project_path=str(temp_project_path)
        )

        # 智能体1工作
        memory.append_work_history(
            agent_name="xiaonuo",
            task="任务分解",
            result="分解为3个子任务",
            status="success"
        )

        # 智能体2工作
        memory.append_work_history(
            agent_name="xiaona",
            task="法律分析",
            result="完成专利分析",
            status="success"
        )

        # 智能体3工作
        memory.append_work_history(
            agent_name="analyzer",
            task="技术分析",
            result="完成技术特征提取",
            status="success"
        )

        # 验证所有工作历史被记录
        history = memory.read(
            type=MemoryType.PROJECT,
            category=MemoryCategory.WORK_HISTORY,
            key="work_history"
        )

        assert history is not None
        assert "xiaonuo" in history
        assert "xiaona" in history
        assert "analyzer" in history

    def test_cross_project_knowledge_sharing(
        self,
        temp_global_path: Path
    ) -> None:
        """测试跨项目知识共享"""
        # 项目A
        project_a_path = Path(temp_global_path) / "project_a"
        project_a_path.mkdir()

        # 项目B
        project_b_path = Path(temp_global_path) / "project_b"
        project_b_path.mkdir()

        # 项目A写入学习成果到全局记忆
        memory_a = UnifiedMemorySystem(
            global_memory_path=str(temp_global_path),
            current_project_path=str(project_a_path)
        )
        memory_a.write(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.AGENT_LEARNING,
            key="retrieval_strategy",
            content="# 检索策略\n\n使用本地PG+Google Patents"
        )

        # 项目B可以读取该学习成果
        memory_b = UnifiedMemorySystem(
            global_memory_path=str(temp_global_path),
            current_project_path=str(project_b_path)
        )
        content = memory_b.read(
            type=MemoryType.GLOBAL,
            category=MemoryCategory.AGENT_LEARNING,
            key="retrieval_strategy"
        )

        assert content is not None
        assert "本地PG" in content
