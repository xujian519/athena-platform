#!/usr/bin/env python3
"""
状态模块系统测试
Tests for State Module System

测试用例：
1. StateModule自动注册
2. 状态保存和恢复
3. 嵌套状态模块
4. StatePersistenceManager
5. CheckpointManager
6. 持久化策略

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.state.checkpoint import CheckpointManager
from core.state.persistence_manager import (
    PersistenceConfig,
    PersistenceStrategy,
    StatePersistenceManager,
)
from core.state.state_module import StateModule

# ============================================================================
# 测试 fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """临时目录"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def simple_state_module():
    """简单状态模块"""
    class SimpleModule(StateModule):
        def __init__(self):
            super().__init__()
            self.count = 0
            self.name = "test"
            self.register_state("count")
            self.register_state("name")

    return SimpleModule()


@pytest.fixture
def nested_state_module():
    """嵌套状态模块"""
    class InnerModule(StateModule):
        def __init__(self):
            super().__init__()
            self.inner_value = 100
            self.register_state("inner_value")

    class OuterModule(StateModule):
        def __init__(self):
            super().__init__()
            self.inner = InnerModule()  # 自动注册
            self.outer_value = 200
            self.register_state("outer_value")

    return OuterModule()


# ============================================================================
# StateModule 测试
# ============================================================================

class TestStateModule:
    """StateModule测试"""

    def test_module_initialization(self, simple_state_module):
        """测试模块初始化"""
        assert simple_state_module.count == 0
        assert simple_state_module.name == "test"

    def test_auto_register_child_module(self, nested_state_module):
        """测试自动注册子模块"""
        summary = nested_state_module.get_state_summary()
        assert summary["auto_registered_attrs"] == 1
        assert "inner" in summary["auto_attrs"]

    def test_manual_register_state(self, simple_state_module):
        """测试手动注册状态"""
        summary = simple_state_module.get_state_summary()
        assert summary["manually_registered_attrs"] == 2
        assert "count" in summary["manual_attrs"]
        assert "name" in summary["manual_attrs"]

    def test_state_dict(self, simple_state_module):
        """测试生成状态字典"""
        state = simple_state_module.state_dict()
        assert state["count"] == 0
        assert state["name"] == "test"

    def test_nested_state_dict(self, nested_state_module):
        """测试嵌套状态字典"""
        state = nested_state_module.state_dict()
        assert "inner" in state
        assert state["inner"]["inner_value"] == 100
        assert state["outer_value"] == 200

    def test_load_state_dict(self, simple_state_module):
        """测试加载状态字典"""
        new_state = {"count": 42, "name": "updated"}
        simple_state_module.load_state_dict(new_state)
        assert simple_state_module.count == 42
        assert simple_state_module.name == "updated"

    def test_register_states_batch(self, simple_state_module):
        """测试批量注册状态"""
        simple_state_module.value1 = "a"
        simple_state_module.value2 = "b"
        simple_state_module.register_states({"value1", "value2"})

        summary = simple_state_module.get_state_summary()
        assert "value1" in summary["manual_attrs"]
        assert "value2" in summary["manual_attrs"]

    def test_unregister_state(self, simple_state_module):
        """测试取消注册状态"""
        simple_state_module.unregister_state("count")
        state = simple_state_module.state_dict()
        assert "count" not in state

    @pytest.mark.asyncio
    async def test_save_and_load_state(self, simple_state_module, temp_dir):
        """测试保存和加载状态"""
        file_path = temp_dir / "test_state.json"

        # 修改状态
        simple_state_module.count = 999
        simple_state_module.name = "saved"

        # 保存
        await simple_state_module.save_state(str(file_path))
        assert file_path.exists()

        # 修改状态
        simple_state_module.count = 0
        simple_state_module.name = "modified"

        # 加载
        await simple_state_module.load_state(str(file_path))
        assert simple_state_module.count == 999
        assert simple_state_module.name == "saved"


# ============================================================================
# StatePersistenceManager 测试
# ============================================================================

class TestStatePersistenceManager:
    """StatePersistenceManager测试"""

    @pytest.mark.asyncio
    async def test_manager_initialization(self, temp_dir):
        """测试管理器初始化"""
        config = PersistenceConfig(persistence_dir=str(temp_dir))
        manager = StatePersistenceManager(config)
        assert manager.config.strategy == PersistenceStrategy.DELAYED

    @pytest.mark.asyncio
    async def test_register_module(self, temp_dir):
        """测试注册模块"""
        config = PersistenceConfig(persistence_dir=str(temp_dir))
        manager = StatePersistenceManager(config)

        module = StateModule.__new__(StateModule)
        module.__init__()

        manager.register_module("test", module)

        assert "test" in manager._modules

    @pytest.mark.asyncio
    async def test_save_and_load_module(self, temp_dir):
        """测试保存和加载模块"""
        config = PersistenceConfig(
            persistence_dir=str(temp_dir),
            strategy=PersistenceStrategy.IMMEDIATE
        )
        manager = StatePersistenceManager(config)

        # 创建并注册模块
        class TestModule(StateModule):
            def __init__(self):
                super().__init__()
                self.value = 123
                self.register_state("value")

        module = TestModule()
        manager.register_module("test", module)

        # 保存
        file_path = await manager.save_module("test")
        assert file_path is not None
        assert Path(file_path).exists()

        # 修改状态
        module.value = 456

        # 加载
        success = await manager.load_module("test")
        assert success is True
        assert module.value == 123

    @pytest.mark.asyncio
    async def test_save_all(self, temp_dir):
        """测试保存所有模块"""
        config = PersistenceConfig(
            persistence_dir=str(temp_dir),
            strategy=PersistenceStrategy.IMMEDIATE
        )
        manager = StatePersistenceManager(config)

        # 创建多个模块
        for i in range(3):
            module = StateModule.__new__(StateModule)
            module.__init__()
            manager.register_module(f"module_{i}", module)

        # 保存所有
        results = await manager.save_all()
        assert len(results) == 3
        assert all(v is not None for v in results.values())

    @pytest.mark.asyncio
    async def test_get_metrics(self, temp_dir):
        """测试获取指标"""
        config = PersistenceConfig(
            persistence_dir=str(temp_dir),
            strategy=PersistenceStrategy.IMMEDIATE
        )
        manager = StatePersistenceManager(config)

        class TestModule(StateModule):
            def __init__(self):
                super().__init__()
                self.value = 1
                self.register_state("value")

        module = TestModule()
        manager.register_module("test", module)

        # 保存
        await manager.save_module("test")

        # 获取指标
        metrics = manager.get_metrics("test")
        assert metrics is not None
        assert metrics.total_saves == 1
        assert metrics.get_save_success_rate() == 1.0


# ============================================================================
# CheckpointManager 测试
# ============================================================================

class TestCheckpointManager:
    """CheckpointManager测试"""

    @pytest.mark.asyncio
    async def test_manager_initialization(self, temp_dir):
        """测试管理器初始化"""
        manager = CheckpointManager(
            checkpoint_dir=str(temp_dir / "checkpoints"),
            max_checkpoints=5
        )
        assert manager.max_checkpoints == 5

    @pytest.mark.asyncio
    async def test_save_and_load_checkpoint(self, temp_dir):
        """测试保存和加载检查点"""
        manager = CheckpointManager(
            checkpoint_dir=str(temp_dir / "checkpoints")
        )

        class TestModule(StateModule):
            def __init__(self):
                super().__init__()
                self.checkpoint_value = 42
                self.register_state("checkpoint_value")

        module = TestModule()

        # 保存检查点
        info = await manager.save_checkpoint(module, checkpoint_id="test_checkpoint")
        assert info.checkpoint_id == "test_checkpoint"
        assert Path(info.file_path).exists()

        # 修改状态
        module.checkpoint_value = 999

        # 加载检查点
        loaded_info = await manager.load_checkpoint(module, checkpoint_id="test_checkpoint")
        assert loaded_info is not None
        assert module.checkpoint_value == 42

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, temp_dir):
        """测试列出检查点"""
        manager = CheckpointManager(
            checkpoint_dir=str(temp_dir / "checkpoints"),
            max_checkpoints=10
        )

        class TestModule(StateModule):
            def __init__(self):
                super().__init__()
                self.value = 1
                self.register_state("value")

        module = TestModule()

        # 创建多个检查点
        for i in range(3):
            module.value = i
            await manager.save_checkpoint(module, checkpoint_id=f"checkpoint_{i}")

        # 列出检查点
        checkpoints = await manager.list_checkpoints()
        assert len(checkpoints) == 3

    @pytest.mark.asyncio
    async def test_auto_cleanup(self, temp_dir):
        """测试自动清理"""
        manager = CheckpointManager(
            checkpoint_dir=str(temp_dir / "checkpoints"),
            max_checkpoints=3,
            auto_cleanup=True
        )

        class TestModule(StateModule):
            def __init__(self):
                super().__init__()
                self.value = 1
                self.register_state("value")

        module = TestModule()

        # 创建超过限制的检查点
        for i in range(5):
            module.value = i
            await manager.save_checkpoint(module, checkpoint_id=f"checkpoint_{i}")

        # 只保留最新的3个
        checkpoints = await manager.list_checkpoints()
        assert len(checkpoints) == 3

    @pytest.mark.asyncio
    async def test_delete_checkpoint(self, temp_dir):
        """测试删除检查点"""
        manager = CheckpointManager(
            checkpoint_dir=str(temp_dir / "checkpoints")
        )

        class TestModule(StateModule):
            def __init__(self):
                super().__init__()
                self.value = 1
                self.register_state("value")

        module = TestModule()

        # 保存检查点
        await manager.save_checkpoint(module, checkpoint_id="to_delete")

        # 删除检查点
        success = await manager.delete_checkpoint("to_delete")
        assert success is True

        # 验证已删除
        checkpoints = await manager.list_checkpoints()
        assert len(checkpoints) == 0

    @pytest.mark.asyncio
    async def test_save_with_metadata(self, temp_dir):
        """测试保存带元数据的检查点"""
        manager = CheckpointManager(
            checkpoint_dir=str(temp_dir / "checkpoints")
        )

        class TestModule(StateModule):
            def __init__(self):
                super().__init__()
                self.value = 1
                self.register_state("value")

        module = TestModule()

        # 保存检查点并附加元数据
        info = await manager.save_with_metadata(
            module,
            checkpoint_id="meta_checkpoint",
            task_id="task_123",
            quality_score=0.95
        )

        assert info.checkpoint_id == "meta_checkpoint"


# ============================================================================
# 集成测试
# ============================================================================

class TestStateIntegration:
    """状态系统集成测试"""

    @pytest.mark.asyncio
    async def test_full_state_lifecycle(self, temp_dir):
        """测试完整的状态生命周期"""
        # 创建嵌套模块
        class InnerModule(StateModule):
            def __init__(self):
                super().__init__()
                self.data = "inner_data"
                self.register_state("data")

        class OuterModule(StateModule):
            def __init__(self):
                super().__init__()
                self.inner = InnerModule()
                self.info = "outer_info"
                self.register_state("info")

        # 创建持久化管理器
        config = PersistenceConfig(
            persistence_dir=str(temp_dir / "state"),
            strategy=PersistenceStrategy.IMMEDIATE
        )
        persistence_manager = StatePersistenceManager(config)
        persistence_manager.register_module("outer", OuterModule())

        # 创建检查点管理器
        checkpoint_manager = CheckpointManager(
            checkpoint_dir=str(temp_dir / "checkpoints")
        )

        # 1. 保存状态
        await persistence_manager.save_module("outer")

        # 2. 创建检查点（带元数据）
        outer = persistence_manager._modules["outer"]
        await checkpoint_manager.save_with_metadata(
            outer,
            checkpoint_id="checkpoint_1",
            phase="initial"
        )

        # 3. 修改状态
        outer.info = "modified_info"
        outer.inner.data = "modified_data"

        # 4. 从检查点恢复
        await checkpoint_manager.load_checkpoint(outer, checkpoint_id="checkpoint_1")

        # 5. 验证状态已恢复
        assert outer.info == "outer_info"
        assert outer.inner.data == "inner_data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
