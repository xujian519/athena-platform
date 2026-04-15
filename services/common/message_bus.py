"""
Athena服务消息总线
Athena Service Message Bus
提供服务间异步通信和事件分发功能
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# 配置日志
logger = logging.getLogger(__name__)

class MessagePriority(str, Enum):
    """消息优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class MessageStatus(str, Enum):
    """消息状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Message:
    """消息模型"""
    id: str
    event_type: str
    source_service: str
    target_service: str | None  # None表示广播
    data: dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING
    created_at: datetime = None
    processed_at: datetime | None = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Subscription:
    """订阅信息"""
    service_name: str
    event_types: set[str]
    handler: Callable
    filter_func: Callable | None = None

class MessageBus:
    """消息总线实现"""

    def __init__(self):
        self.subscribers: dict[str, list[Subscription]] = defaultdict(list)
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self.processing_messages: dict[str, Message] = {}
        self.message_history: list[Message] = []
        self.max_history = 10000
        self.is_running = False
        self.worker_tasks: list[asyncio.Task] = []
        self.num_workers = 5

    def subscribe(
        self,
        service_name: str,
        event_types: list[str],
        handler: Callable,
        filter_func: Callable | None = None
    ) -> str:
        """订阅事件"""
        subscription_id = str(uuid.uuid4())

        subscription = Subscription(
            service_name=service_name,
            event_types=set(event_types),
            handler=handler,
            filter_func=filter_func
        )

        for event_type in event_types:
            self.subscribers[event_type].append(subscription)

        logger.info(f"服务 {service_name} 订阅事件: {event_types}")
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> Any:
        """取消订阅"""
        for event_type, subscriptions in self.subscribers.items():
            self.subscribers[event_type] = [
                sub for sub in subscriptions
                if str(id(sub)) != subscription_id
            ]
        logger.info(f"取消订阅: {subscription_id}")

    async def publish(
        self,
        event_type: str,
        source_service: str,
        data: dict[str, Any],
        target_service: str | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        max_retries: int = 3
    ) -> str:
        """发布消息"""
        message = Message(
            id=str(uuid.uuid4()),
            event_type=event_type,
            source_service=source_service,
            target_service=target_service,
            data=data,
            priority=priority,
            max_retries=max_retries
        )

        # 高优先级消息插入队列前面
        if priority in [MessagePriority.HIGH, MessagePriority.CRITICAL]:
            # 将高优先级消息插入队列前端
            temp_queue = asyncio.Queue()
            inserted = False

            while not self.message_queue.empty():
                try:
                    existing_message = self.message_queue.get_nowait()

                    if not inserted and existing_message.priority not in [MessagePriority.HIGH, MessagePriority.CRITICAL]:
                        await temp_queue.put(message)
                        inserted = True

                    await temp_queue.put(existing_message)
                except asyncio.QueueEmpty:
                    break

            if not inserted:
                await temp_queue.put(message)

            # 交换队列
            self.message_queue = temp_queue
        else:
            await self.message_queue.put(message)

        logger.debug(f"发布消息: {event_type} from {source_service} (ID: {message.id})")
        return message.id

    async def start(self):
        """启动消息总线"""
        if self.is_running:
            return

        self.is_running = True
        logger.info(f"启动消息总线，工作进程数: {self.num_workers}")

        # 创建工作进程
        for i in range(self.num_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(task)

        logger.info("消息总线启动完成")

    async def stop(self):
        """停止消息总线"""
        if not self.is_running:
            return

        logger.info("正在停止消息总线...")
        self.is_running = False

        # 取消所有工作进程
        for task in self.worker_tasks:
            task.cancel()

        # 等待所有任务完成
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()

        logger.info("消息总线已停止")

    async def _worker(self, worker_name: str):
        """消息处理工作进程"""
        logger.info(f"启动工作进程: {worker_name}")

        while self.is_running:
            try:
                # 获取消息，设置超时避免无限等待
                try:
                    message = await asyncio.wait_for(
                        self.message_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # 处理消息
                await self._process_message(message, worker_name)

            except Exception as e:
                logger.error(f"工作进程 {worker_name} 错误: {e}")

        logger.info(f"工作进程 {worker_name} 已停止")

    async def _process_message(self, message: Message, worker_name: str):
        """处理单个消息"""
        try:
            message.status = MessageStatus.PROCESSING
            message.processed_at = datetime.now()
            self.processing_messages[message.id] = message

            logger.debug(f"{worker_name} 处理消息: {message.id}")

            # 获取订阅者
            subscribers = self.subscribers.get(message.event_type, [])

            # 如果指定了目标服务，只发送给该服务
            if message.target_service:
                subscribers = [
                    sub for sub in subscribers
                    if sub.service_name == message.target_service
                ]

            if not subscribers:
                logger.debug(f"没有订阅者处理事件: {message.event_type}")
                message.status = MessageStatus.COMPLETED
                return

            # 并行调用所有订阅者
            tasks = []
            for subscription in subscribers:
                # 应用过滤器
                if subscription.filter_func and not subscription.filter_func(message):
                    continue

                task = self._call_handler(subscription, message)
                tasks.append(task)

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 检查处理结果
                failed_count = sum(1 for r in results if isinstance(r, Exception))

                if failed_count > 0:
                    logger.error(f"消息 {message.id} 处理失败数: {failed_count}")

                    # 如果有失败且未超过重试次数
                    if message.retry_count < message.max_retries:
                        message.retry_count += 1
                        message.status = MessageStatus.PENDING

                        # 延迟重试
                        await asyncio.sleep(2 ** message.retry_count)
                        await self.message_queue.put(message)
                        return

                message.status = MessageStatus.COMPLETED

        except Exception as e:
            logger.error(f"处理消息 {message.id} 时出错: {e}")
            message.status = MessageStatus.FAILED
            message.error = str(e)

            # 重试逻辑
            if message.retry_count < message.max_retries:
                message.retry_count += 1
                message.status = MessageStatus.PENDING
                await asyncio.sleep(2 ** message.retry_count)
                await self.message_queue.put(message)

        finally:
            # 从处理中移除
            self.processing_messages.pop(message.id, None)

            # 添加到历史记录
            self.message_history.append(message)
            if len(self.message_history) > self.max_history:
                self.message_history.pop(0)

    async def _call_handler(self, subscription: Subscription, message: Message):
        """调用处理器"""
        try:
            # 如果是协程函数
            if asyncio.iscoroutinefunction(subscription.handler):
                await subscription.handler(message)
            else:
                # 同步函数，在线程池中执行
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, subscription.handler, message)

        except Exception as e:
            logger.error(f"处理器错误 ({subscription.service_name}): {e}")
            raise

    # 监控和管理方法
    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.message_queue.qsize()

    def get_processing_count(self) -> int:
        """获取正在处理的消息数"""
        return len(self.processing_messages)

    def get_subscriber_count(self, event_type: str | None = None) -> int:
        """获取订阅者数量"""
        if event_type:
            return len(self.subscribers.get(event_type, []))

        return sum(len(subs) for subs in self.subscribers.values())

    def get_message_stats(self) -> dict[str, Any]:
        """获取消息统计"""
        status_counts = defaultdict(int)
        priority_counts = defaultdict(int)

        for message in self.message_history:
            status_counts[message.status.value] += 1
            priority_counts[message.priority.value] += 1

        return {
            "queue_size": self.get_queue_size(),
            "processing_count": self.get_processing_count(),
            "total_processed": len(self.message_history),
            "status_distribution": dict(status_counts),
            "priority_distribution": dict(priority_counts),
            "subscriber_count": self.get_subscriber_count()
        }

# 全局消息总线实例
_message_bus: MessageBus | None = None

def get_message_bus() -> MessageBus:
    """获取全局消息总线实例"""
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus

# 装饰器：事件发布
def publish_event(event_type: str, priority: MessagePriority = MessagePriority.NORMAL) -> Any:
    """事件发布装饰器"""
    def decorator(func) -> None:
        async def wrapper(self, *args, **kwargs):
            # 执行原函数
            result = await func(self, *args, **kwargs) if asyncio.iscoroutinefunction(func) else func(self, *args, **kwargs)

            # 发布事件
            message_bus = get_message_bus()
            service_name = getattr(self, 'service_name', self.__class__.__name__)

            await message_bus.publish(
                event_type=event_type,
                source_service=service_name,
                data={
                    "result": result,
                    "args": args,
                    "kwargs": kwargs
                },
                priority=priority
            )

            return result
        return wrapper
    return decorator

# 装饰器：事件订阅
def subscribe_event(event_types: list[str], filter_func: Callable | None = None) -> Any:
    """事件订阅装饰器"""
    def decorator(func) -> None:
        # 获取服务名称
        service_name = func.__self__.service_name if hasattr(func, '__self__') else func.__module__

        # 注册订阅
        message_bus = get_message_bus()
        message_bus.subscribe(
            service_name=service_name,
            event_types=event_types,
            handler=func,
            filter_func=filter_func
        )

        return func
    return decorator

# 使用示例
"""
# 启动消息总线
message_bus = get_message_bus()
await message_bus.start()

# 发布事件
await message_bus.publish(
    event_type="user_created",
    source_service="user-service",
    data={"user_id": 123, "email": "user@example.com"},
    priority=MessagePriority.HIGH
)

# 订阅事件
def handle_user_created(message: Message):
    print(f"新用户创建: {message.data}")

message_bus.subscribe(
    service_name="notification-service",
    event_types=["user_created"],
    handler=handle_user_created
)

# 使用装饰器
@publish_event("data_processed", priority=MessagePriority.HIGH)
async def process_data(data):
    # 处理数据
    return {"status": "success", "count": len(data)}

@subscribe_event(["user_created", "user_updated"])
async def send_notification(message: Message):
    # 发送通知
    pass
"""
