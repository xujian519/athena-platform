from __future__ import annotations
"""
Athena事件中间件系统

基于PAI Hook系统思想,为Athena实现Python版本的事件中间件

功能:
- 事件驱动架构
- 安全验证中间件
- 日志和监控中间件
- 性能优化中间件
- 自定义中间件支持
"""

import asyncio
import json
import logging
import shlex
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""

    # Agent生命周期事件
    AGENT_INITIALIZE = "agent_initialize"
    AGENT_START = "agent_start"
    AGENT_STOP = "agent_stop"
    AGENT_ERROR = "agent_error"

    # 任务事件
    TASK_CREATE = "task_create"
    TASK_ASSIGN = "task_assign"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_FAIL = "task_fail"

    # 工具使用事件(类似PAI的PreToolUse/PostToolUse)
    TOOL_USE_PRE = "tool_use_pre"  # 工具使用前
    TOOL_USE_POST = "tool_use_post"  # 工具使用后

    # 会话事件
    SESSION_START = "session_start"
    SESSION_END = "session_end"

    # 消息事件
    MESSAGE_SEND = "message_send"
    MESSAGE_RECEIVE = "message_receive"
    USER_PROMPT_SUBMIT = "user_prompt_submit"

    # 自定义事件
    CUSTOM = "custom"


class MiddlewarePriority(Enum):
    """中间件优先级"""

    CRITICAL = 0  # 关键中间件(如安全验证)
    HIGH = 1  # 高优先级(如日志)
    NORMAL = 2  # 普通优先级
    LOW = 3  # 低优先级(如统计)


@dataclass
class Event:
    """事件对象"""

    type: EventType
    source: str
    data: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # 使用uuid4更安全高效
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class MiddlewareResult:
    """中间件执行结果"""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    should_continue: bool = True  # 是否继续执行后续中间件
    modified_event: Event | None = None  # 修改后的事件


class BaseMiddleware(ABC):
    """中间件基类"""

    def __init__(self, name: str, priority: MiddlewarePriority = MiddlewarePriority.NORMAL):
        self.name = name
        self.priority = priority
        self.enabled = True
        self.execution_count = 0
        self.execution_time_ms = 0.0

    @abstractmethod
    async def process(self, event: Event) -> MiddlewareResult:
        """
        处理事件

        Args:
            event: 事件对象

        Returns:
            中间件执行结果
        """
        pass

    def can_handle(self, event_type: EventType) -> bool:
        """
        判断是否可以处理该事件类型

        Args:
            event_type: 事件类型

        Returns:
            是否可以处理
        """
        return True

    async def before_process(self, event: Event):
        """处理前钩子"""
        pass

    async def after_process(self, event: Event, result: MiddlewareResult):
        """处理后钩子"""
        pass

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "name": self.name,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "execution_count": self.execution_count,
            "avg_execution_time_ms": (
                self.execution_time_ms / self.execution_count if self.execution_count > 0 else 0
            ),
        }


class EventMiddleware:
    """
    事件中间件系统

    管理所有中间件的注册、执行和生命周期
    """

    def __init__(self):
        self.middlewares: list[BaseMiddleware] = []
        self.event_history: list[Event] = []
        self.max_history_size = 1000
        self.stats = {
            "total_events_processed": 0,
            "total_execution_time_ms": 0.0,
            "events_by_type": {},
        }
        # 添加锁保护并发访问
        self._lock = asyncio.Lock()
        self._history_lock = asyncio.Lock()
        self._stats_lock = asyncio.Lock()

    def register(self, middleware: BaseMiddleware) -> bool:
        """
        注册中间件

        Args:
            middleware: 中间件实例

        Returns:
            是否注册成功
        """
        try:
            # 按优先级插入
            inserted = False
            for i, existing in enumerate(self.middlewares):
                if middleware.priority.value < existing.priority.value:
                    self.middlewares.insert(i, middleware)
                    inserted = True
                    break

            if not inserted:
                self.middlewares.append(middleware)

            logger.info(f"✅ 中间件已注册: {middleware.name} (优先级: {middleware.priority.name})")
            return True

        except Exception as e:
            logger.error(f"❌ 注册中间件失败: {e}")
            return False

    def unregister(self, middleware_name: str) -> bool:
        """
        取消注册中间件

        Args:
            middleware_name: 中间件名称

        Returns:
            是否取消成功
        """
        for i, middleware in enumerate(self.middlewares):
            if middleware.name == middleware_name:
                self.middlewares.pop(i)
                logger.info(f"✅ 中间件已取消注册: {middleware_name}")
                return True

        logger.warning(f"⚠️ 中间件不存在: {middleware_name}")
        return False

    async def emit(
        self, event_type: EventType, source: str, data: dict[str, Any]
    ) -> list[MiddlewareResult]:
        """
        发送事件(线程安全)

        Args:
            event_type: 事件类型
            source: 事件源
            data: 事件数据

        Returns:
            所有中间件的执行结果列表
        """
        event = Event(type=event_type, source=source, data=data)

        # 记录事件历史(使用锁保护)
        async with self._history_lock:
            self._record_event(event)

        # 更新统计(使用锁保护)
        async with self._stats_lock:
            self.stats["total_events_processed"] += 1
            event_type_str = event_type.value
            self.stats["events_by_type"][event_type_str] = (
                self.stats["events_by_type"].get(event_type_str, 0) + 1
            )

        # 执行中间件(读取middlewares,使用锁保护快照)
        async with self._lock:
            middlewares_snapshot = self.middlewares.copy()

        results = []
        current_event = event

        for middleware in middlewares_snapshot:
            if not middleware.enabled:
                continue

            if not middleware.can_handle(event_type):
                continue

            try:
                start_time = time.time()

                # 执行前后钩子
                await middleware.before_process(current_event)

                # 执行中间件
                result = await middleware.process(current_event)

                # 执行后钩子
                await middleware.after_process(current_event, result)

                # 更新统计
                execution_time = (time.time() - start_time) * 1000
                middleware.execution_count += 1
                middleware.execution_time_ms += execution_time

                # 检查是否继续
                if not result.should_continue:
                    logger.warning(f"⚠️ 中间件 {middleware.name} 中断了事件处理")
                    break

                # 如果中间件修改了事件,使用修改后的事件
                if result.modified_event:
                    current_event = result.modified_event

                results.append(result)

            except Exception as e:
                logger.error(f"❌ 中间件 {middleware.name} 执行失败: {e}")
                results.append(
                    MiddlewareResult(
                        success=False, error_message=str(e), should_continue=True  # 出错不中断
                    )
                )

        return results

    def _record_event(self, event: Event) -> Any:
        """记录事件到历史(内部方法,调用前应获取锁)"""
        self.event_history.append(event)

        # 限制历史大小
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size :]

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        middleware_stats = [m.get_stats() for m in self.middlewares]

        return {
            "total_events_processed": self.stats["total_events_processed"],
            "total_execution_time_ms": self.stats["total_execution_time_ms"],
            "events_by_type": self.stats["events_by_type"],
            "registered_middlewares": len(self.middlewares),
            "middleware_stats": middleware_stats,
            "event_history_size": len(self.event_history),
        }

    def get_event_history(
        self, event_type: EventType | None = None, limit: int = 100
    ) -> list[Event]:
        """
        获取事件历史

        Args:
            event_type: 可选,按事件类型过滤
            limit: 返回的最大数量

        Returns:
            事件列表
        """
        history = self.event_history

        if event_type:
            history = [e for e in history if e.type == event_type]

        return history[-limit:]


# ========== 内置中间件 ==========


class SecurityValidationMiddleware(BaseMiddleware):
    """
    安全验证中间件

    在工具使用前进行安全检查(类似PAI的security-validator)
    """

    def __init__(self):
        super().__init__(name="security_validation", priority=MiddlewarePriority.CRITICAL)

        # 危险命令黑名单
        self.dangerous_commands = [
            "rm -rf",
            "mkfs",
            "dd if=/dev/zero",
            "chmod 000",
            "> /dev/sda",
            "curl http://",
            "wget http://",
        ]

        # 敏感操作
        self.sensitive_operations = ["delete", "drop", "truncate", "destroy", "remove"]

    async def process(self, event: Event) -> MiddlewareResult:
        """处理事件(加强安全检查)"""
        if event.type != EventType.TOOL_USE_PRE:
            return MiddlewareResult(success=True, should_continue=True)

        tool_name = event.data.get("tool_name", "")
        tool_args = event.data.get("tool_args", {})

        # 检查危险命令 - 使用更严格的检查
        if tool_name == "bash":
            command = tool_args.get("command", "")
            if self._is_dangerous_command(command):
                logger.error(f"🚫 拒绝执行危险命令: {command[:100]}")
                return MiddlewareResult(
                    success=False,
                    error_message="危险命令被拦截",
                    should_continue=False,  # 中断执行
                )

        # 检查敏感操作
        for sensitive in self.sensitive_operations:
            if sensitive in tool_name.lower() or sensitive in str(tool_args).lower():
                logger.warning(f"⚠️ 敏感操作: {sensitive}")
                # 可以添加额外的确认逻辑

        return MiddlewareResult(
            success=True, data={"security_check": "passed"}, should_continue=True
        )

    def _is_dangerous_command(self, command: str) -> bool:
        """
        使用更严格的方法检查危险命令

        Args:
            command: 要检查的命令字符串

        Returns:
            是否为危险命令
        """
        if not command:
            return False

        try:
            # 使用shlex正确分词
            tokens = shlex.split(command)
            if not tokens:
                return False

            cmd = tokens[0].lower()

            # 检查危险命令
            dangerous_cmds = {
                "rm",
                "mkfs",
                "dd",
                "fdisk",
                "format",
                "shutdown",
                "reboot",
                "halt",
                "poweroff",
                "su",
                "sudo",
                "chmod",
                "chown",
                "curl",
                "wget",
                "nc",
                "netcat",
            }

            if cmd in dangerous_cmds:
                return True

            # 检查危险参数组合
            if cmd == "rm":
                # 检查是否有 -rf, -r, -f 等危险参数
                dangerous_flags = ["-rf", "-fr", "-r", "-f", "-rf/", "-r/*"]
                cmd_lower = command.lower()
                for flag in dangerous_flags:
                    if flag in cmd_lower:
                        return True

            # 检查路径遍历
            if "../" in command or "..\\" in command:
                return True

            # 检查可能的命令注入
            if ";" in command or "&" in command or "|" in command:
                # 简单检查,实际应该更严格
                return True

        except (ValueError, Exception) as e:
            # 解析失败,视为危险
            logger.warning(f"⚠️ 命令解析失败,视为危险: {e}")
            return True

        return False


class LoggingMiddleware(BaseMiddleware):
    """
    日志中间件

    记录所有事件到日志系统
    """

    def __init__(self, log_level: str = "INFO"):
        super().__init__(name="logging", priority=MiddlewarePriority.HIGH)
        self.log_level = getattr(logging, log_level.upper())

    async def process(self, event: Event) -> MiddlewareResult:
        """处理事件"""
        log_message = f"[{event.type.value}] from {event.source}"

        if event.data:
            log_message += f" | Data: {json.dumps(event.data, ensure_ascii=False)[:200]}"

        logger.log(self.log_level, log_message)

        return MiddlewareResult(success=True, should_continue=True)


class PerformanceMonitoringMiddleware(BaseMiddleware):
    """
    性能监控中间件

    记录每个操作的执行时间
    """

    def __init__(self):
        super().__init__(name="performance_monitoring", priority=MiddlewarePriority.LOW)
        self.operation_times: dict[str, list[float]] = {}

    async def process(self, event: Event) -> MiddlewareResult:
        """处理事件"""
        operation = event.data.get("operation", "unknown")

        if "duration_ms" in event.data:
            duration = event.data["duration_ms"]

            if operation not in self.operation_times:
                self.operation_times[operation] = []

            self.operation_times[operation].append(duration)

            # 检查是否超过阈值
            if duration > 5000:  # 5秒
                logger.warning(f"⚠️ 操作耗时过长: {operation} - {duration:.2f}ms")

        return MiddlewareResult(success=True, should_continue=True)

    def get_performance_stats(self) -> dict[str, dict[str, float]]:
        """获取性能统计"""
        stats = {}

        for operation, times in self.operation_times.items():
            if times:
                stats[operation] = {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                }

        return stats


class MetricsCollectionMiddleware(BaseMiddleware):
    """
    指标收集中间件

    收集各种指标用于监控和分析
    """

    def __init__(self):
        super().__init__(name="metrics_collection", priority=MiddlewarePriority.LOW)
        self.metrics = {
            "agent_starts": 0,
            "agent_errors": 0,
            "task_completions": 0,
            "task_failures": 0,
            "tool_uses": 0,
        }

    async def process(self, event: Event) -> MiddlewareResult:
        """处理事件"""
        # 更新指标
        if event.type == EventType.AGENT_START:
            self.metrics["agent_starts"] += 1
        elif event.type == EventType.AGENT_ERROR:
            self.metrics["agent_errors"] += 1
        elif event.type == EventType.TASK_COMPLETE:
            self.metrics["task_completions"] += 1
        elif event.type == EventType.TASK_FAIL:
            self.metrics["task_failures"] += 1
        elif event.type == EventType.TOOL_USE_PRE:
            self.metrics["tool_uses"] += 1

        return MiddlewareResult(success=True, should_continue=True)

    def get_metrics(self) -> dict[str, int]:
        """获取当前指标"""
        return self.metrics.copy()


# ========== 全局中间件系统 ==========

_middleware_system = None


def get_middleware_system() -> EventMiddleware:
    """获取全局中间件系统实例"""
    global _middleware_system
    if _middleware_system is None:
        _middleware_system = EventMiddleware()

        # 注册默认中间件
        _middleware_system.register(SecurityValidationMiddleware())
        _middleware_system.register(LoggingMiddleware())
        _middleware_system.register(PerformanceMonitoringMiddleware())
        _middleware_system.register(MetricsCollectionMiddleware())

        logger.info("✅ 事件中间件系统初始化完成")

    return _middleware_system


# ========== 便捷函数 ==========


async def emit_event(
    event_type: EventType, source: str, data: dict[str, Any]
) -> list[MiddlewareResult]:
    """
    发送事件(便捷函数)

    Args:
        event_type: 事件类型
        source: 事件源
        data: 事件数据

    Returns:
        所有中间件的执行结果列表
    """
    system = get_middleware_system()
    return await system.emit(event_type, source, data)


def register_middleware(middleware: BaseMiddleware) -> bool:
    """
    注册中间件(便捷函数)

    Args:
        middleware: 中间件实例

    Returns:
        是否注册成功
    """
    system = get_middleware_system()
    return system.register(middleware)


if __name__ == "__main__":
    # 测试代码
    async def test():
        # 测试事件发送
        results = await emit_event(
            EventType.AGENT_START, "test_agent", {"agent_id": "agent_001", "config": {}}
        )

        print(f"执行了{len(results)}个中间件")

        # 查看统计
        system = get_middleware_system()
        stats = system.get_stats()
        print(f"统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")

    asyncio.run(test())
