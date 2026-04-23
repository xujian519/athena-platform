"""
异步日志处理器
Asynchronous Log Handler

使用队列实现异步日志写入，避免阻塞主线程
"""
import queue
import logging
import threading
from typing import Optional


class AsyncLogHandler(logging.Handler):
    """异步日志处理器

    使用后台线程和队列实现异步日志写入
    适用于高并发场景，避免I/O阻塞主线程

    性能特性:
    - 非阻塞: 日志调用立即返回
    - 缓冲: 内置队列缓冲（默认1000条）
    - 批量: 可选批量写入优化
    """

    def __init__(
        self,
        handler: logging.Handler,
        capacity: int = 1000,
        batch_size: int = 10
    ):
        """初始化异步处理器

        Args:
            handler: 底层实际处理器（FileHandler, StreamHandler等）
            capacity: 队列容量（默认1000）
            batch_size: 批量写入大小（默认10，0表示不批量）
        """
        super().__init__()

        self.handler = handler
        self.capacity = capacity
        self.batch_size = batch_size

        # 创建队列
        self.queue: queue.Queue = queue.Queue(maxsize=capacity)

        # 启动后台线程
        self._thread = threading.Thread(
            target=self._worker,
            name="AsyncLogHandler",
            daemon=True
        )
        self._thread.start()

        # 统计信息
        self.stats = {
            "processed": 0,
            "dropped": 0,
            "queue_full": 0
        }

    def emit(self, record: logging.LogRecord) -> None:
        """发送日志记录（非阻塞）

        如果队列满，根据策略处理：
        - 可选：丢弃最旧的日志
        - 可选：阻塞等待
        - 当前实现：非阻塞，队列满时丢弃
        """
        try:
            # 非阻塞放入队列
            self.queue.put_nowait(record)
            self.stats["processed"] += 1
        except queue.Full:
            # 队列满时丢弃
            self.stats["dropped"] += 1
            self.stats["queue_full"] += 1

            # 可选：记录队列满事件
            # 注意：这里不能再记录日志，否则会形成死循环
            pass

    def _worker(self) -> None:
        """后台工作线程

        从队列中取出日志记录并处理
        支持批量写入优化
        """
        batch = []

        while True:
            try:
                # 获取日志记录
                record = self.queue.get()

                # 检查停止信号（None）
                if record is None:
                    # 处理剩余批次
                    if batch:
                        self._process_batch(batch)
                    break

                # 添加到批次
                batch.append(record)

                # 批量处理或立即处理
                if self.batch_size > 0 and len(batch) >= self.batch_size:
                    self._process_batch(batch)
                    batch = []
                else:
                    # 立即处理单条
                    self.handler.emit(record)

                # 标记任务完成
                self.queue.task_done()

            except Exception as e:
                # 避免工作线程异常退出
                # 可以记录到stderr或内部错误日志
                print(f"AsyncLogHandler error: {e}")

    def _process_batch(self, batch: list) -> None:
        """批量处理日志记录

        Args:
            batch: 日志记录列表
        """
        for record in batch:
            try:
                self.handler.emit(record)
            except Exception:
                # 单条记录失败不影响其他记录
                pass

    def close(self) -> None:
        """关闭处理器

        发送停止信号并等待工作线程结束
        """
        # 发送停止信号
        self.queue.put(None)

        # 等待队列清空
        self.queue.join()

        # 等待线程结束（最多等待5秒）
        self._thread.join(timeout=5.0)

        # 关闭底层处理器
        self.handler.close()

        # 调用父类关闭
        super().close()

    def get_stats(self) -> dict:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            **self.stats,
            "queue_size": self.queue.qsize(),
            "queue_capacity": self.capacity,
            "queue_usage": self.queue.qsize() / self.capacity
        }
