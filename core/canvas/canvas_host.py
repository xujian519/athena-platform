"""
Canvas/Host UI系统 - 渲染引擎和UI组件

提供Canvas渲染、实时UI更新、Agent状态可视化等功能。
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)


class UIComponentType(str, Enum):
    """UI组件类型"""
    TEXT = "text"
    PROGRESS = "progress"
    CHART = "chart"
    TABLE = "table"
    METRIC = "metric"
    LOG = "log"


@dataclass
class UIComponent:
    """UI组件数据类"""
    component_id: str
    component_type: UIComponentType
    title: str
    data: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, Any] = field(default_factory=dict)
    style: Dict[str, str] = field(default_factory=dict)
    update_interval: int = 0  # 更新间隔（秒），0表示手动更新


@dataclass
class CanvasUpdate:
    """Canvas更新数据"""
    canvas_id: str
    component_id: str
    action: str  # create, update, delete
    data: Optional[UIComponent] = None


class CanvasHost:
    """
    Canvas Host服务

    负责管理Canvas渲染和UI组件更新。
    """

    def __init__(self, host_id: str = "canvas_host_main"):
        """初始化Canvas Host"""
        self.host_id = host_id
        self._canvases: Dict[str, List[UIComponent]] = {}
        self._subscribers: Dict[str, Any] = {}  # WebSocket连接
        self._running = False

        logger.info(f"CanvasHost {host_id} initialized")

    async def start(self) -> None:
        """启动Canvas Host"""
        if self._running:
            logger.warning(f"CanvasHost {self.host_id} is already running")
            return

        self._running = True
        logger.info(f"CanvasHost {self.host_id} started")

    async def stop(self) -> None:
        """停止Canvas Host"""
        if not self._running:
            logger.warning(f"CanvasHost {self.host_id} is not running")
            return

        self._running = False
        logger.info(f"CanvasHost {self.host_id} stopped")

    async def create_canvas(self, canvas_id: str, title: str = "") -> bool:
        """
        创建Canvas

        Args:
            canvas_id: Canvas ID
            title: Canvas标题

        Returns:
            是否成功创建
        """
        if canvas_id in self._canvases:
            logger.warning(f"Canvas {canvas_id} already exists")
            return False

        self._canvases[canvas_id] = []
        logger.info(f"Canvas {canvas_id} created with title: {title}")

        # 通知订阅者
        await self._broadcast_create_canvas(canvas_id, title)
        return True

    async def delete_canvas(self, canvas_id: str) -> bool:
        """
        删除Canvas

        Args:
            canvas_id: Canvas ID

        Returns:
            是否成功删除
        """
        if canvas_id not in self._canvases:
            logger.warning(f"Canvas {canvas_id} not found")
            return False

        del self._canvases[canvas_id]
        logger.info(f"Canvas {canvas_id} deleted")

        # 通知订阅者
        await self._broadcast_delete_canvas(canvas_id)
        return True

    async def add_component(
        self,
        canvas_id: str,
        component: UIComponent
    ) -> bool:
        """
        添加UI组件到Canvas

        Args:
            canvas_id: Canvas ID
            component: UI组件

        Returns:
            是否成功添加
        """
        if canvas_id not in self._canvases:
            logger.warning(f"Canvas {canvas_id} not found")
            return False

        self._canvases[canvas_id].append(component)
        logger.info(
            f"Component {component.component_id} added to canvas {canvas_id}"
        )

        # 通知订阅者
        await self._broadcast_component_update(
            canvas_id, component, "create"
        )
        return True

    async def update_component(
        self,
        canvas_id: str,
        component_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        更新UI组件

        Args:
            canvas_id: Canvas ID
            component_id: 组件ID
            data: 更新数据

        Returns:
            是否成功更新
        """
        if canvas_id not in self._canvases:
            logger.warning(f"Canvas {canvas_id} not found")
            return False

        # 查找组件
        for component in self._canvases[canvas_id]:
            if component.component_id == component_id:
                component.data.update(data)
                logger.info(f"Component {component_id} updated")

                # 通知订阅者
                await self._broadcast_component_update(
                    canvas_id, component, "update"
                )
                return True

        logger.warning(f"Component {component_id} not found in canvas {canvas_id}")
        return False

    async def remove_component(
        self,
        canvas_id: str,
        component_id: str
    ) -> bool:
        """
        从Canvas移除UI组件

        Args:
            canvas_id: Canvas ID
            component_id: 组件ID

        Returns:
            是否成功移除
        """
        if canvas_id not in self._canvases:
            logger.warning(f"Canvas {canvas_id} not found")
            return False

        # 查找并移除组件
        for i, component in enumerate(self._canvases[canvas_id]):
            if component.component_id == component_id:
                removed = self._canvases[canvas_id].pop(i)
                logger.info(f"Component {component_id} removed from canvas {canvas_id}")

                # 通知订阅者
                await self._broadcast_component_update(
                    canvas_id, removed, "delete"
                )
                return True

        logger.warning(f"Component {component_id} not found in canvas {canvas_id}")
        return False

    async def get_canvas_components(self, canvas_id: str) -> List[UIComponent]:
        """
        获取Canvas的所有组件

        Args:
            canvas_id: Canvas ID

        Returns:
            UI组件列表
        """
        return self._canvases.get(canvas_id, [])

    async def subscribe(self, subscriber_id: str, websocket_connection: Any) -> bool:
        """
        订阅Canvas更新

        Args:
            subscriber_id: 订阅者ID
            websocket_connection: WebSocket连接

        Returns:
            是否成功订阅
        """
        self._subscribers[subscriber_id] = websocket_connection
        logger.info(f"Subscriber {subscriber_id} subscribed to canvas updates")
        return True

    async def unsubscribe(self, subscriber_id: str) -> bool:
        """
        取消订阅

        Args:
            subscriber_id: 订阅者ID

        Returns:
            是否成功取消订阅
        """
        if subscriber_id in self._subscribers:
            del self._subscribers[subscriber_id]
            logger.info(f"Subscriber {subscriber_id} unsubscribed")
            return True

        return False

    async def _broadcast_create_canvas(self, canvas_id: str, title: str) -> None:
        """广播Canvas创建事件"""
        message = {
            "type": "canvas_created",
            "canvas_id": canvas_id,
            "title": title,
            "timestamp": datetime.now().isoformat(),
        }
        await self._broadcast_to_subscribers(message)

    async def _broadcast_delete_canvas(self, canvas_id: str) -> None:
        """广播Canvas删除事件"""
        message = {
            "type": "canvas_deleted",
            "canvas_id": canvas_id,
            "timestamp": datetime.now().isoformat(),
        }
        await self._broadcast_to_subscribers(message)

    async def _broadcast_component_update(
        self,
        canvas_id: str,
        component: UIComponent,
        action: str
    ) -> None:
        """广播组件更新事件"""
        message = {
            "type": "component_updated",
            "canvas_id": canvas_id,
            "action": action,
            "component": {
                "component_id": component.component_id,
                "component_type": component.component_type.value,
                "title": component.title,
                "data": component.data,
                "position": component.position,
                "style": component.style,
            },
            "timestamp": datetime.now().isoformat(),
        }
        await self._broadcast_to_subscribers(message)

    async def _broadcast_to_subscribers(self, message: Dict[str, Any]) -> None:
        """向所有订阅者广播消息"""
        for subscriber_id, connection in self._subscribers.items():
            try:
                # 这里假设connection有send方法
                if hasattr(connection, 'send'):
                    await connection.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send to subscriber {subscriber_id}: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "host_id": self.host_id,
            "total_canvases": len(self._canvases),
            "total_subscribers": len(self._subscribers),
            "running": self._running,
        }


# 预定义的UI组件工厂
class UIComponentFactory:
    """UI组件工厂"""

    @staticmethod
    def create_text_component(
        component_id: str,
        title: str,
        text: str,
        position: Dict[str, Any] = None,
        style: Dict[str, str] = None,
    ) -> UIComponent:
        """创建文本组件"""
        return UIComponent(
            component_id=component_id,
            component_type=UIComponentType.TEXT,
            title=title,
            data={"text": text},
            position=position or {"x": 0, "y": 0},
            style=style or {},
        )

    @staticmethod
    def create_metric_component(
        component_id: str,
        title: str,
        metric_name: str,
        value: float,
        unit: str = "",
        position: Dict[str, Any] = None,
        style: Dict[str, str] = None,
    ) -> UIComponent:
        """创建指标组件"""
        return UIComponent(
            component_id=component_id,
            component_type=UIComponentType.METRIC,
            title=title,
            data={
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
            },
            position=position or {"x": 0, "y": 0},
            style=style or {},
        )

    @staticmethod
    def create_progress_component(
        component_id: str,
        title: str,
        current: int,
        total: int,
        position: Dict[str, Any] = None,
        style: Dict[str, str] = None,
    ) -> UIComponent:
        """创建进度条组件"""
        return UIComponent(
            component_id=component_id,
            component_type=UIComponentType.PROGRESS,
            title=title,
            data={
                "current": current,
                "total": total,
                "percentage": (current / total * 100) if total > 0 else 0,
            },
            position=position or {"x": 0, "y": 0},
            style=style or {},
        )

    @staticmethod
    def create_chart_component(
        component_id: str,
        title: str,
        chart_type: str,
        data: List[Dict[str, Any]],
        position: Dict[str, Any] = None,
        style: Dict[str, str] = None,
    ) -> UIComponent:
        """创建图表组件"""
        return UIComponent(
            component_id=component_id,
            component_type=UIComponentType.CHART,
            title=title,
            data={
                "chart_type": chart_type,
                "data": data,
            },
            position=position or {"x": 0, "y": 0},
            style=style or {},
        )
