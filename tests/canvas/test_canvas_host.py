"""
Canvas/Host UI系统测试

测试Canvas渲染和UI组件功能。
"""


import pytest
from core.canvas.canvas_host import (
    CanvasHost,
    UIComponent,
    UIComponentFactory,
    UIComponentType,
)


class TestCanvasHost:
    """CanvasHost功能测试"""

    @pytest.fixture
    async def canvas_host(self):
        """创建CanvasHost实例"""
        host = CanvasHost("test_host")
        await host.start()
        yield host
        await host.stop()

    @pytest.mark.asyncio
    async def test_canvas_host_initialization(self):
        """测试CanvasHost初始化"""
        host = CanvasHost("test_host")
        assert host.host_id == "test_host"
        assert not host._running
        assert len(host._canvases) == 0

    @pytest.mark.asyncio
    async def test_start_stop(self, canvas_host):
        """测试启动和停止"""
        assert canvas_host._running is True

        await canvas_host.stop()
        assert canvas_host._running is False

    @pytest.mark.asyncio
    async def test_create_canvas(self, canvas_host):
        """测试创建Canvas"""
        result = await canvas_host.create_canvas("canvas_1", "Test Canvas")
        assert result is True
        assert "canvas_1" in canvas_host._canvases

    @pytest.mark.asyncio
    async def test_create_duplicate_canvas(self, canvas_host):
        """测试创建重复Canvas"""
        await canvas_host.create_canvas("canvas_1")
        result = await canvas_host.create_canvas("canvas_1")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_canvas(self, canvas_host):
        """测试删除Canvas"""
        await canvas_host.create_canvas("canvas_1")
        result = await canvas_host.delete_canvas("canvas_1")
        assert result is True
        assert "canvas_1" not in canvas_host._canvases

    @pytest.mark.asyncio
    async def test_add_component(self, canvas_host):
        """测试添加组件"""
        await canvas_host.create_canvas("canvas_1")

        component = UIComponent(
            component_id="comp_1",
            component_type=UIComponentType.TEXT,
            title="Test Component",
            data={"text": "Hello"},
        )

        result = await canvas_host.add_component("canvas_1", component)
        assert result is True

        components = await canvas_host.get_canvas_components("canvas_1")
        assert len(components) == 1
        assert components[0].component_id == "comp_1"

    @pytest.mark.asyncio
    async def test_update_component(self, canvas_host):
        """测试更新组件"""
        await canvas_host.create_canvas("canvas_1")

        component = UIComponent(
            component_id="comp_1",
            component_type=UIComponentType.TEXT,
            title="Test Component",
            data={"text": "Hello"},
        )

        await canvas_host.add_component("canvas_1", component)

        # 更新组件
        result = await canvas_host.update_component(
            "canvas_1",
            "comp_1",
            {"text": "Updated"}
        )
        assert result is True

        components = await canvas_host.get_canvas_components("canvas_1")
        assert components[0].data["text"] == "Updated"

    @pytest.mark.asyncio
    async def test_remove_component(self, canvas_host):
        """测试移除组件"""
        await canvas_host.create_canvas("canvas_1")

        component = UIComponent(
            component_id="comp_1",
            component_type=UIComponentType.TEXT,
            title="Test Component",
            data={"text": "Hello"},
        )

        await canvas_host.add_component("canvas_1", component)

        result = await canvas_host.remove_component("canvas_1", "comp_1")
        assert result is True

        components = await canvas_host.get_canvas_components("canvas_1")
        assert len(components) == 0

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self, canvas_host):
        """测试订阅和取消订阅"""
        # Mock WebSocket connection
        class MockWebSocket:
            def __init__(self):
                self.messages = []

            async def send(self, message: str):
                self.messages.append(message)

        mock_ws = MockWebSocket()

        # 测试订阅
        result = await canvas_host.subscribe("sub_1", mock_ws)
        assert result is True
        assert "sub_1" in canvas_host._subscribers

        # 测试取消订阅
        result = await canvas_host.unsubscribe("sub_1")
        assert result is True
        assert "sub_1" not in canvas_host._subscribers

    @pytest.mark.asyncio
    async def test_get_statistics(self, canvas_host):
        """测试获取统计信息"""
        await canvas_host.create_canvas("canvas_1")
        await canvas_host.create_canvas("canvas_2")

        stats = canvas_host.get_statistics()
        assert stats["total_canvases"] == 2
        assert stats["running"] is True


class TestUIComponentFactory:
    """UIComponentFactory功能测试"""

    def test_create_text_component(self):
        """测试创建文本组件"""
        component = UIComponentFactory.create_text_component(
            "text_1",
            "Hello",
            "Hello World"
        )

        assert component.component_id == "text_1"
        assert component.component_type == UIComponentType.TEXT
        assert component.data["text"] == "Hello World"

    def test_create_metric_component(self):
        """测试创建指标组件"""
        component = UIComponentFactory.create_metric_component(
            "metric_1",
            "CPU指标",
            "CPU Usage",
            75.5,
            "%"
        )

        assert component.component_type == UIComponentType.METRIC
        assert component.data["metric_name"] == "CPU Usage"
        assert component.data["value"] == 75.5
        assert component.data["unit"] == "%"

    def test_create_progress_component(self):
        """测试创建进度条组件"""
        component = UIComponentFactory.create_progress_component(
            "progress_1",
            "Loading",
            75,
            100
        )

        assert component.component_type == UIComponentType.PROGRESS
        assert component.data["current"] == 75
        assert component.data["total"] == 100
        assert component.data["percentage"] == 75.0

    def test_create_chart_component(self):
        """测试创建图表组件"""
        data = [
            {"x": 1, "y": 10},
            {"x": 2, "y": 20},
            {"x": 3, "y": 15},
        ]

        component = UIComponentFactory.create_chart_component(
            "chart_1",
            "Line Chart",
            "line",
            data
        )

        assert component.component_type == UIComponentType.CHART
        assert component.data["chart_type"] == "line"
        assert len(component.data["data"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
