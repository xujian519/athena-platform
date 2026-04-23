"""
T1-5: 测试TaskStore

此测试验证任务存储的功能。
"""

import sys
import tempfile
from pathlib import Path

import pytest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.task.task_store import TaskStore

    from core.framework.agents.task_tool.models import TaskInput, TaskRecord, TaskStatus
except ImportError:
    pytest.skip("task_store.py尚未创建", allow_module_level=True)


class TestTaskStore:
    """测试TaskStore类"""

    def test_init_creates_store(self):
        """测试初始化创建存储"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "hot_limit_mb": 10,
                "warm_ttl": 300,
                "cold_db_path": f"{temp_dir}/test_tasks.db",
            }
            store = TaskStore(config=config)
            assert store is not None
            assert isinstance(store, TaskStore)

    def test_save_task(self):
        """测试保存任务"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "hot_limit_mb": 10,
                "warm_ttl": 300,
                "cold_db_path": f"{temp_dir}/test_tasks.db",
            }
            store = TaskStore(config=config)

            task_input = TaskInput(prompt="test prompt", tools=["tool1"])
            task_record = TaskRecord(
                task_id="test-id-1",
                agent_id="agent-1",
                model="haiku",
                status=TaskStatus.PENDING,
                input=task_input,
            )

            saved = store.save_task(task_record)
            assert saved is True

    def test_get_task(self):
        """测试获取任务"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "hot_limit_mb": 10,
                "warm_ttl": 300,
                "cold_db_path": f"{temp_dir}/test_tasks.db",
            }
            store = TaskStore(config=config)

            task_input = TaskInput(prompt="test prompt", tools=["tool1"])
            task_record = TaskRecord(
                task_id="test-id-2",
                agent_id="agent-2",
                model="sonnet",
                status=TaskStatus.RUNNING,
                input=task_input,
            )

            store.save_task(task_record)
            retrieved = store.get_task("test-id-2")

            assert retrieved is not None
            assert retrieved.task_id == "test-id-2"
            assert retrieved.agent_id == "agent-2"
            assert retrieved.model == "sonnet"
            assert retrieved.status == TaskStatus.RUNNING

    def test_get_nonexistent_task(self):
        """测试获取不存在的任务"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "hot_limit_mb": 10,
                "warm_ttl": 300,
                "cold_db_path": f"{temp_dir}/test_tasks.db",
            }
            store = TaskStore(config=config)

            retrieved = store.get_task("nonexistent-id")
            assert retrieved is None

    def test_get_active_tasks(self):
        """测试获取活动任务"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "hot_limit_mb": 10,
                "warm_ttl": 300,
                "cold_db_path": f"{temp_dir}/test_tasks.db",
            }
            store = TaskStore(config=config)

            # 创建多个任务
            for i in range(5):
                task_input = TaskInput(prompt=f"test prompt {i}", tools=["tool1"])
                task_record = TaskRecord(
                    task_id=f"test-id-{i}",
                    agent_id="agent-1",
                    model="haiku",
                    status=TaskStatus.RUNNING if i < 3 else TaskStatus.COMPLETED,
                    input=task_input,
                )
                store.save_task(task_record)

            active_tasks = store.get_active_tasks()
            assert len(active_tasks) >= 3

    def test_get_task_history(self):
        """测试获取任务历史"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "hot_limit_mb": 10,
                "warm_ttl": 300,
                "cold_db_path": f"{temp_dir}/test_tasks.db",
            }
            store = TaskStore(config=config)

            # 创建任务历史
            for i in range(10):
                task_input = TaskInput(prompt=f"test prompt {i}", tools=["tool1"])
                task_record = TaskRecord(
                    task_id=f"test-id-{i}",
                    agent_id="agent-1",
                    model="haiku",
                    status=TaskStatus.COMPLETED,
                    input=task_input,
                )
                store.save_task(task_record)

            history = store.get_task_history(limit=5)
            assert len(history) <= 5

    def test_update_task_status(self):
        """测试更新任务状态"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "hot_limit_mb": 10,
                "warm_ttl": 300,
                "cold_db_path": f"{temp_dir}/test_tasks.db",
            }
            store = TaskStore(config=config)

            task_input = TaskInput(prompt="test prompt", tools=["tool1"])
            task_record = TaskRecord(
                task_id="test-id-3",
                agent_id="agent-3",
                model="haiku",
                status=TaskStatus.PENDING,
                input=task_input,
            )

            store.save_task(task_record)

            # 更新状态
            task_record.status = TaskStatus.COMPLETED
            updated = store.save_task(task_record)
            assert updated is True

            # 验证更新
            retrieved = store.get_task("test-id-3")
            assert retrieved.status == TaskStatus.COMPLETED

    def test_hot_tier_storage(self):
        """测试热层存储"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "hot_limit_mb": 1,  # 小限制以测试LRU
                "warm_ttl": 300,
                "cold_db_path": f"{temp_dir}/test_tasks.db",
            }
            store = TaskStore(config=config)

            task_input = TaskInput(prompt="test prompt", tools=["tool1"])
            task_record = TaskRecord(
                task_id="test-id-hot",
                agent_id="agent-1",
                model="haiku",
                status=TaskStatus.RUNNING,
                input=task_input,
            )

            saved = store.save_task(task_record)
            assert saved is True

            # 应该可以从热层获取
            retrieved = store.get_task("test-id-hot")
            assert retrieved is not None

    def test_warm_tier_integration(self):
        """测试温层集成（Redis可选）"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "hot_limit_mb": 10,
                "warm_ttl": 300,
                "cold_db_path": f"{temp_dir}/test_tasks.db",
                "redis_host": "localhost",
                "redis_port": 6379,
            }
            # 即使Redis不可用，也应该能够工作
            store = TaskStore(config=config)

            task_input = TaskInput(prompt="test prompt", tools=["tool1"])
            task_record = TaskRecord(
                task_id="test-id-warm",
                agent_id="agent-1",
                model="sonnet",
                status=TaskStatus.RUNNING,
                input=task_input,
            )

            saved = store.save_task(task_record)
            assert saved is True

    def test_cold_tier_persistence(self):
        """测试冷层持久化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/test_tasks.db"
            config = {
                "hot_limit_mb": 10,
                "warm_ttl": 300,
                "cold_db_path": db_path,
            }

            # 创建第一个store并保存任务
            store1 = TaskStore(config=config)
            task_input = TaskInput(prompt="test prompt", tools=["tool1"])
            task_record = TaskRecord(
                task_id="test-id-cold",
                agent_id="agent-1",
                model="opus",
                status=TaskStatus.COMPLETED,
                input=task_input,
            )
            store1.save_task(task_record)

            # 关闭第一个store
            del store1

            # 创建第二个store并验证任务仍然存在
            store2 = TaskStore(config=config)
            retrieved = store2.get_task("test-id-cold")
            assert retrieved is not None
            assert retrieved.task_id == "test-id-cold"
            assert retrieved.model == "opus"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

