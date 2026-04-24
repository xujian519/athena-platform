"""
统一注册中心测试

测试UnifiedRegistryCenter的核心功能。
"""

import pytest
import threading
import time

from core.registry_center.base import BaseRegistry, RegistryEvent, RegistryEventType
from core.registry_center.unified import UnifiedRegistryCenter


class TestUnifiedRegistryCenter:
    """测试统一注册中心"""

    def setup_method(self):
        """测试前准备"""
        self.registry = UnifiedRegistryCenter.get_instance()
        self.registry.clear()

    def teardown_method(self):
        """测试后清理"""
        self.registry.clear()

    def test_singleton_pattern(self):
        """测试单例模式"""
        registry1 = UnifiedRegistryCenter.get_instance()
        registry2 = UnifiedRegistryCenter.get_instance()

        assert registry1 is registry2

    def test_register_and_unregister(self):
        """测试注册和注销"""
        # 注册实体
        entity = {"name": "test_entity"}
        success = self.registry.register("entity1", entity, entity_type="test")
        assert success is True

        # 验证注册成功
        assert self.registry.exists("entity1") is True
        assert self.registry.count() == 1

        # 注销实体
        success = self.registry.unregister("entity1")
        assert success is True

        # 验证注销成功
        assert self.registry.exists("entity1") is False
        assert self.registry.count() == 0

    def test_get_entity(self):
        """测试获取实体"""
        entity = {"name": "test_entity", "value": 42}
        self.registry.register("entity1", entity)

        # 获取实体
        retrieved = self.registry.get("entity1")
        assert retrieved is not None
        assert retrieved["name"] == "test_entity"
        assert retrieved["value"] == 42

        # 获取不存在的实体
        assert self.registry.get("nonexistent") is None

    def test_list_all(self):
        """测试列出所有实体"""
        entities = [
            ("entity1", {"name": "entity1"}),
            ("entity2", {"name": "entity2"}),
            ("entity3", {"name": "entity3"}),
        ]

        for entity_id, entity in entities:
            self.registry.register(entity_id, entity)

        # 列出所有实体
        all_entities = self.registry.list_all()
        assert len(all_entities) == 3

    def test_list_by_type(self):
        """测试按类型列出实体"""
        # 注册不同类型的实体
        self.registry.register("agent1", {"name": "agent1"}, entity_type="agent")
        self.registry.register("agent2", {"name": "agent2"}, entity_type="agent")
        self.registry.register("tool1", {"name": "tool1"}, entity_type="tool")

        # 按类型列出
        agents = self.registry.list_by_type("agent")
        tools = self.registry.list_by_type("tool")

        assert len(agents) == 2
        assert len(tools) == 1

    def test_count_by_type(self):
        """测试按类型计数"""
        self.registry.register("agent1", {"name": "agent1"}, entity_type="agent")
        self.registry.register("agent2", {"name": "agent2"}, entity_type="agent")
        self.registry.register("tool1", {"name": "tool1"}, entity_type="tool")

        assert self.registry.count_by_type("agent") == 2
        assert self.registry.count_by_type("tool") == 1
        assert self.registry.count_by_type("nonexistent") == 0

    def test_update_entity(self):
        """测试更新实体"""
        entity = {"name": "test_entity", "value": 1}
        self.registry.register("entity1", entity)

        # 更新实体
        updated_entity = {"name": "test_entity", "value": 2}
        success = self.registry.update("entity1", updated_entity)
        assert success is True

        # 验证更新
        retrieved = self.registry.get("entity1")
        assert retrieved["value"] == 2

    def test_clear(self):
        """测试清空注册表"""
        # 注册多个实体
        for i in range(5):
            self.registry.register(f"entity{i}", {"name": f"entity{i}"})

        assert self.registry.count() == 5

        # 清空
        self.registry.clear()

        assert self.registry.count() == 0
        assert len(self.registry.list_all()) == 0

    def test_event_notification(self):
        """测试事件通知"""
        events_received = []

        def event_listener(event: RegistryEvent):
            events_received.append(event)

        # 添加事件监听器
        self.registry.add_event_listener(
            RegistryEventType.ENTITY_REGISTERED, event_listener
        )

        # 注册实体（触发事件）
        self.registry.register("entity1", {"name": "test"})

        # 验证事件
        assert len(events_received) == 1
        assert events_received[0].event_type == RegistryEventType.ENTITY_REGISTERED
        assert events_received[0].entity_id == "entity1"

        # 移除事件监听器
        self.registry.remove_event_listener(
            RegistryEventType.ENTITY_REGISTERED, event_listener
        )

        # 再次注册（不应触发事件）
        self.registry.register("entity2", {"name": "test2"})
        assert len(events_received) == 1  # 仍然是1

    def test_update_heartbeat(self):
        """测试心跳更新"""
        self.registry.register("entity1", {"name": "test"})

        # 更新心跳
        self.registry.update_heartbeat("entity1")

        # 验证健康状态
        health = self.registry.check_health()
        assert health["healthy"] is True
        assert health["total_entities"] == 1

    def test_get_statistics(self):
        """测试获取统计信息"""
        # 注册不同类型的实体
        self.registry.register("agent1", {"name": "agent1"}, entity_type="agent")
        self.registry.register("agent2", {"name": "agent2"}, entity_type="agent")
        self.registry.register("tool1", {"name": "tool1"}, entity_type="tool")

        # 获取统计信息
        stats = self.registry.get_statistics()

        assert stats["total_entities"] == 3
        assert stats["entity_types"] == 2
        assert stats["type_distribution"]["agent"] == 2
        assert stats["type_distribution"]["tool"] == 1
        assert "metrics" in stats

    def test_thread_safety(self):
        """测试线程安全"""
        num_threads = 10
        num_registrations = 100

        def register_entities(thread_id: int):
            for i in range(num_registrations):
                entity_id = f"thread{thread_id}_entity{i}"
                self.registry.register(entity_id, {"thread": thread_id})

        # 启动多个线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=register_entities, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有实体都已注册
        expected_count = num_threads * num_registrations
        assert self.registry.count() == expected_count

    def test_concurrent_read_write(self):
        """测试并发读写"""
        # 先注册一些实体
        for i in range(100):
            self.registry.register(f"entity{i}", {"value": i})

        def read_entities():
            for _ in range(1000):
                self.registry.list_all()
                self.registry.count()

        def write_entities():
            for i in range(100, 200):
                self.registry.register(f"entity{i}", {"value": i})

        # 启动读写线程
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=read_entities))
            threads.append(threading.Thread(target=write_entities))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # 验证没有数据丢失
        assert self.registry.count() == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
