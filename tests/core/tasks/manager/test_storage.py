#!/usr/bin/env python3

"""
任务存储测试
Task Storage Tests

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from core.tasks.manager.models import Task, TaskPriority, TaskStatus
from core.tasks.manager.storage import FileTaskStorage


@pytest.fixture
def temp_storage_dir():
    """临时存储目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def storage(temp_storage_dir):
    """任务存储实例"""
    return FileTaskStorage(storage_dir=temp_storage_dir)


@pytest.fixture
def sample_task():
    """示例任务"""
    return Task(
        id="task_1",
        title="测试任务",
        description="任务描述",
        priority=TaskPriority.HIGH,
        assigned_to="agent_1",
        created_by="user_1",
        session_id="session_1",
    )


class TestFileTaskStorage:
    """测试FileTaskStorage类"""

    def test_init_creates_directory(self, temp_storage_dir):
        """测试初始化创建目录"""
        storage_path = Path(temp_storage_dir) / "new_storage"
        storage = FileTaskStorage(storage_dir=storage_path)

        assert storage_path.exists()
        assert storage.storage_dir == storage_path

    def test_save_task(self, storage, sample_task):
        """测试保存任务"""
        result = storage.save(sample_task)

        assert result is True
        assert storage.exists(sample_task.id)

    def test_load_task(self, storage, sample_task):
        """测试加载任务"""
        storage.save(sample_task)
        loaded_task = storage.load(sample_task.id)

        assert loaded_task is not None
        assert loaded_task.id == sample_task.id
        assert loaded_task.title == sample_task.title
        assert loaded_task.status == sample_task.status

    def test_load_nonexistent_task(self, storage):
        """测试加载不存在的任务"""
        loaded_task = storage.load("nonexistent")

        assert loaded_task is None

    def test_delete_task(self, storage, sample_task):
        """测试删除任务"""
        storage.save(sample_task)
        result = storage.delete(sample_task.id)

        assert result is True
        assert not storage.exists(sample_task.id)

    def test_delete_nonexistent_task(self, storage):
        """测试删除不存在的任务"""
        result = storage.delete("nonexistent")

        assert result is False

    def test_exists_task(self, storage, sample_task):
        """测试检查任务存在"""
        assert not storage.exists(sample_task.id)

        storage.save(sample_task)
        assert storage.exists(sample_task.id)

    def test_load_all_empty(self, storage):
        """测试加载所有任务（空）"""
        all_tasks = storage.load_all()

        assert all_tasks == {}

    def test_load_all_multiple_tasks(self, storage):
        """测试加载所有任务"""
        task1 = Task(id="task_1", title="任务1")
        task2 = Task(id="task_2", title="任务2")
        task3 = Task(id="task_3", title="任务3")

        storage.save(task1)
        storage.save(task2)
        storage.save(task3)

        all_tasks = storage.load_all()

        assert len(all_tasks) == 3
        assert "task_1" in all_tasks
        assert "task_2" in all_tasks
        assert "task_3" in all_tasks

    def test_load_by_status(self, storage):
        """测试按状态加载任务"""
        task1 = Task(id="task_1", title="任务1", status=TaskStatus.PENDING)
        task2 = Task(id="task_2", title="任务2", status=TaskStatus.RUNNING)
        task3 = Task(id="task_3", title="任务3", status=TaskStatus.PENDING)

        storage.save(task1)
        storage.save(task2)
        storage.save(task3)

        pending_tasks = storage.load_by_status(TaskStatus.PENDING)
        running_tasks = storage.load_by_status(TaskStatus.RUNNING)
        completed_tasks = storage.load_by_status(TaskStatus.COMPLETED)

        assert len(pending_tasks) == 2
        assert len(running_tasks) == 1
        assert len(completed_tasks) == 0

    def test_load_by_agent(self, storage):
        """测试按Agent加载任务"""
        task1 = Task(id="task_1", title="任务1", assigned_to="agent_1")
        task2 = Task(id="task_2", title="任务2", assigned_to="agent_2")
        task3 = Task(id="task_3", title="任务3", assigned_to="agent_1")

        storage.save(task1)
        storage.save(task2)
        storage.save(task3)

        agent1_tasks = storage.load_by_agent("agent_1")
        agent2_tasks = storage.load_by_agent("agent_2")
        agent3_tasks = storage.load_by_agent("agent_3")

        assert len(agent1_tasks) == 2
        assert len(agent2_tasks) == 1
        assert len(agent3_tasks) == 0

    def test_load_by_session(self, storage):
        """测试按会话加载任务"""
        task1 = Task(id="task_1", title="任务1", session_id="session_1")
        task2 = Task(id="task_2", title="任务2", session_id="session_2")
        task3 = Task(id="task_3", title="任务3", session_id="session_1")

        storage.save(task1)
        storage.save(task2)
        storage.save(task3)

        session1_tasks = storage.load_by_session("session_1")
        session2_tasks = storage.load_by_session("session_2")
        session3_tasks = storage.load_by_session("session_3")

        assert len(session1_tasks) == 2
        assert len(session2_tasks) == 1
        assert len(session3_tasks) == 0

    def test_clear_all_tasks(self, storage):
        """测试清空所有任务"""
        task1 = Task(id="task_1", title="任务1")
        task2 = Task(id="task_2", title="任务2")

        storage.save(task1)
        storage.save(task2)

        result = storage.clear()

        assert result is True
        assert len(storage.load_all()) == 0

    def test_get_stats(self, storage):
        """测试获取统计信息"""
        task1 = Task(id="task_1", title="任务1", status=TaskStatus.PENDING, assigned_to="agent_1", session_id="session_1")
        task2 = Task(id="task_2", title="任务2", status=TaskStatus.RUNNING, assigned_to="agent_1")
        task3 = Task(id="task_3", title="任务3", status=TaskStatus.PENDING, session_id="session_1")

        storage.save(task1)
        storage.save(task2)
        storage.save(task3)

        stats = storage.get_stats()

        assert stats["total_tasks"] == 3
        assert stats["status_counts"]["pending"] == 2
        assert stats["status_counts"]["running"] == 1
        assert stats["agent_counts"]["agent_1"] == 2
        assert stats["session_counts"]["session_1"] == 2

    def test_persistence_across_instances(self, temp_storage_dir, sample_task):
        """测试跨实例持久化"""
        # 第一个实例保存任务
        storage1 = FileTaskStorage(storage_dir=temp_storage_dir)
        storage1.save(sample_task)

        # 第二个实例加载任务
        storage2 = FileTaskStorage(storage_dir=temp_storage_dir)
        loaded_task = storage2.load(sample_task.id)

        assert loaded_task is not None
        assert loaded_task.id == sample_task.id
        assert loaded_task.title == sample_task.title

    def test_save_updates_existing_task(self, storage, sample_task):
        """测试保存更新现有任务"""
        storage.save(sample_task)

        # 更新任务
        sample_task.status = TaskStatus.COMPLETED
        storage.save(sample_task)

        loaded_task = storage.load(sample_task.id)
        assert loaded_task.status == TaskStatus.COMPLETED

    def test_concurrent_access_safety(self, storage, sample_task):
        """测试并发访问安全性"""
        import threading

        results = []

        def save_task(task):
            try:
                storage.save(task)
                results.append(True)
            except Exception:
                results.append(False)

        # 创建多个线程同时保存任务
        threads = []
        for i in range(10):
            task = Task(id=f"task_{i}", title=f"任务{i}")
            thread = threading.Thread(target=save_task, args=(task,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 所有操作都应该成功
        assert all(results)
        assert len(storage.load_all()) == 10

    def test_load_invalid_json(self, temp_storage_dir):
        """测试加载无效JSON"""
        storage_path = Path(temp_storage_dir)
        tasks_file = storage_path / "tasks.json"

        # 写入无效JSON
        with open(tasks_file, "w") as f:
            f.write("{invalid json}")

        # 应该创建空索引而不是崩溃
        storage = FileTaskStorage(storage_dir=storage_path)
        assert len(storage.load_all()) == 0

    def test_save_with_dependencies(self, storage):
        """测试保存带依赖的任务"""
        task = Task(id="task_1", title="测试任务")
        task.add_dependency("task_2")
        task.add_dependency("task_3")

        storage.save(task)
        loaded_task = storage.load(task.id)

        assert len(loaded_task.dependencies) == 2
        assert loaded_task.dependencies[0].task_id == "task_2"
        assert loaded_task.dependencies[1].task_id == "task_3"

    def test_save_with_result(self, storage):
        """测试保存带结果的任务"""
        from core.tasks.manager.models import TaskResult

        task = Task(id="task_1", title="测试任务")
        result = TaskResult(
            success=True,
            data={"output": "done"},
            execution_time=1.5,
        )
        task.complete(result)

        storage.save(task)
        loaded_task = storage.load(task.id)

        assert loaded_task.result is not None
        assert loaded_task.result.success is True
        assert loaded_task.result.data == {"output": "done"}
        assert loaded_task.result.execution_time == 1.5

    def test_file_format(self, temp_storage_dir, sample_task):
        """测试文件格式"""
        storage = FileTaskStorage(storage_dir=temp_storage_dir)
        storage.save(sample_task)

        # 读取JSON文件验证格式
        with open(storage.tasks_file, encoding="utf-8") as f:
            data = json.load(f)

        assert sample_task.id in data
        task_data = data[sample_task.id]
        assert task_data["id"] == sample_task.id
        assert task_data["title"] == sample_task.title
        assert "created_at" in task_data
        assert "updated_at" in task_data

