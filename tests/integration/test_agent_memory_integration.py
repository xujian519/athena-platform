"""
智能体记忆系统集成测试

测试统一记忆系统与智能体的集成功能：
1. BaseAgent记忆系统方法测试
2. 小娜智能体记忆集成测试
3. 小诺编排者记忆集成测试
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from core.agents.base_agent import BaseAgent
from core.agents.xiaona_agent_with_unified_memory import XiaonaAgentWithMemory
from core.agents.xiaonuo_orchestrator_with_memory import XiaonuoOrchestratorWithMemory
from core.memory.unified_memory_system import (
    MemoryType,
    MemoryCategory
)


class TestBaseAgentMemoryIntegration:
    """BaseAgent记忆系统集成测试"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def agent_with_memory(self, temp_project):
        """创建带记忆系统的智能体"""
        agent = BaseAgent(
            name="test_agent",
            role="测试智能体",
            project_path=temp_project
        )
        return agent

    def test_memory_system_initialization(self, agent_with_memory):
        """测试记忆系统初始化"""
        assert agent_with_memory._memory_enabled is True
        assert agent_with_memory.memory_system is not None
        assert agent_with_memory.project_path is not None

    def test_save_and_load_memory(self, agent_with_memory):
        """测试记忆保存和加载"""
        # 保存记忆
        success = agent_with_memory.save_memory(
            MemoryType.PROJECT,
            MemoryCategory.PROJECT_CONTEXT,
            "test_key",
            "# 测试内容\n\n这是一条测试记忆。"
        )
        assert success is True

        # 加载记忆
        content = agent_with_memory.load_memory(
            MemoryType.PROJECT,
            MemoryCategory.PROJECT_CONTEXT,
            "test_key"
        )
        assert content is not None
        assert "测试内容" in content

    def test_save_work_history(self, agent_with_memory):
        """测试工作历史保存"""
        success = agent_with_memory.save_work_history(
            task="测试任务",
            result="任务完成",
            status="success"
        )
        assert success is True

        # 验证历史记录
        history = agent_with_memory.load_memory(
            MemoryType.PROJECT,
            MemoryCategory.WORK_HISTORY,
            "work_history"
        )
        assert history is not None
        assert "测试任务" in history

    def test_search_memory(self, agent_with_memory):
        """测试记忆搜索"""
        # 保存多条记忆
        for i in range(3):
            agent_with_memory.save_memory(
                MemoryType.PROJECT,
                MemoryCategory.LEGAL_ANALYSIS,
                f"analysis_{i}",
                f"# 分析{i}\n\n关于专利{i}的分析。"
            )

        # 搜索记忆
        results = agent_with_memory.search_memory("专利", limit=10)
        assert len(results) > 0

    def test_get_project_context(self, agent_with_memory):
        """测试获取项目上下文"""
        # 先保存项目上下文
        agent_with_memory.save_memory(
            MemoryType.PROJECT,
            MemoryCategory.PROJECT_CONTEXT,
            "project_context",
            "# 项目上下文\n\n测试项目。"
        )

        # 获取项目上下文
        context = agent_with_memory.get_project_context()
        assert context is not None
        assert "项目上下文" in context

    def test_update_learning(self, agent_with_memory):
        """测试更新学习成果"""
        success = agent_with_memory.update_learning(
            insights="这是一条重要的学习洞察。",
            metadata={"category": "test"}
        )
        assert success is True

        # 验证学习成果
        learning = agent_with_memory.load_memory(
            MemoryType.GLOBAL,
            MemoryCategory.AGENT_LEARNING,
            f"{agent_with_memory.name}_learning"
        )
        assert learning is not None
        assert "学习洞察" in learning


class TestXiaonaAgentMemoryIntegration:
    """小娜智能体记忆集成测试"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def xiaona(self, temp_project):
        """创建带记忆的小娜智能体"""
        agent = XiaonaAgentWithMemory(
            name="xiaona",
            role="专利法律专家",
            project_path=temp_project
        )
        return agent

    def test_xiaona_initialization(self, xiaona):
        """测试小娜初始化"""
        assert xiaona.name == "xiaona"
        assert xiaona._memory_enabled is True
        assert isinstance(xiaona.learning_history, list)

    def test_xiaona_process_with_memory(self, xiaona):
        """测试小娜处理任务（集成记忆）"""
        result = xiaona.process("分析专利CN123456789A的创造性")
        assert result is not None
        assert "分析结果" in result

    def test_xiaona_update_insights(self, xiaona):
        """测试更新学习洞察"""
        success = xiaona.update_insights(
            insight="创造性分析需要考虑现有技术的差异",
            category="patent_analysis"
        )
        assert success is True
        assert len(xiaona.learning_history) > 0

    def test_xiaona_get_learning_summary(self, xiaona):
        """测试获取学习摘要"""
        # 先添加一些学习记录
        xiaona.update_insights("洞察1", "test")
        xiaona.update_insights("洞察2", "test")

        summary = xiaona.get_learning_summary()
        assert summary is not None
        assert "学习历史" in summary

    def test_xiaona_save_analysis_result(self, xiaona):
        """测试保存分析结果"""
        # 执行分析
        xiaona.process("分析专利CN123456789A")

        # 验证分析结果已保存
        results = xiaona.search_memory("分析", limit=5)
        assert len(results) > 0


class TestXiaonuoOrchestratorMemoryIntegration:
    """小诺编排者记忆集成测试"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def xiaonuo(self, temp_project):
        """创建带记忆的小诺编排者"""
        orchestrator = XiaonuoOrchestratorWithMemory(
            name="xiaonuo",
            role="智能体编排者",
            project_path=temp_project
        )
        return orchestrator

    def test_xiaonuo_initialization(self, xiaonuo):
        """测试小诺初始化"""
        assert xiaonuo.name == "xiaonuo"
        assert xiaonuo._memory_enabled is True
        assert isinstance(xiaonuo.orchestration_history, list)

    def test_xiaonuo_process_with_memory(self, xiaonuo):
        """测试小诺处理任务（集成记忆）"""
        result = xiaonuo.process("帮我分析专利CN123456789A的创造性")
        assert result is not None
        assert "编排完成" in result

    def test_xiaonuo_save_collaboration_record(self, xiaonuo):
        """测试保存协作记录"""
        # 执行编排
        xiaonuo.process("分析专利CN123456789A")

        # 验证协作记录已保存
        records = xiaonuo.search_memory("协作", limit=5)
        assert len(records) > 0

    def test_xiaonuo_get_statistics(self, xiaonuo):
        """测试获取编排统计"""
        # 执行几次编排
        xiaonuo.process("任务1")
        xiaonuo.process("任务2")

        stats = xiaonuo.get_orchestration_statistics()
        assert stats is not None
        assert stats["total"] > 0


class TestMemoryIntegrationEndToEnd:
    """端到端集成测试"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_multi_agent_collaboration(self, temp_project):
        """测试多智能体协作"""
        # 创建小娜和小诺
        xiaona = XiaonaAgentWithMemory(
            name="xiaona",
            project_path=temp_project
        )
        xiaonuo = XiaonuoOrchestratorWithMemory(
            name="xiaonuo",
            project_path=temp_project
        )

        # 小娜执行任务
        analysis_result = xiaona.process("分析专利CN123456789A")
        assert analysis_result is not None

        # 小诺执行编排
        orchestration_result = xiaonuo.process("编排分析任务")
        assert orchestration_result is not None

        # 验证两个智能体的工作历史都保存了
        xiaona_history = xiaona.load_memory(
            MemoryType.PROJECT,
            MemoryCategory.WORK_HISTORY,
            "work_history"
        )
        assert xiaona_history is not None

        xiaonuo_history = xiaonuo.load_memory(
            MemoryType.PROJECT,
            MemoryCategory.WORK_HISTORY,
            "work_history"
        )
        assert xiaonuo_history is not None

    def test_memory_persistence(self, temp_project):
        """测试记忆持久化"""
        # 创建智能体并保存记忆
        agent1 = BaseAgent(
            name="test_agent",
            project_path=temp_project
        )
        agent1.save_memory(
            MemoryType.PROJECT,
            MemoryCategory.PROJECT_CONTEXT,
            "test_key",
            "持久化测试内容"
        )

        # 创建新智能体实例，验证记忆持久化
        agent2 = BaseAgent(
            name="test_agent2",
            project_path=temp_project
        )
        content = agent2.load_memory(
            MemoryType.PROJECT,
            MemoryCategory.PROJECT_CONTEXT,
            "test_key"
        )
        assert content is not None
        assert "持久化测试内容" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
