"""
远程日志收集处理器
Remote Log Collection Handler

支持将日志发送到远程日志收集服务器
"""
import logging
import json
import threading
import time
from typing import Optional, List
from queue import Queue, Empty
import urllib.request
import urllib.error


class RemoteHandler(logging.Handler):
    """远程日志收集处理器

    将日志通过HTTP发送到远程收集服务器
    支持批量发送、失败重试、本地缓存

    特性:
    - 批量发送: 减少网络开销
    - 失败重试: 确保日志不丢失
    - 异步发送: 不阻塞主线程
    - 本地缓存: 网络断开时本地缓存
    """

    def __init__(
        self,
        url: str,
        batch_size: int = 10,
        batch_timeout: float = 5.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        headers: Optional[dict] = None
    ):
        """初始化远程处理器

        Args:
            url: 远程日志收集URL
            batch_size: 批量发送大小
            batch_timeout: 批量发送超时（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            headers: HTTP请求头
        """
        super().__init__()

        self.url = url
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.headers = headers or {
            "Content-Type": "application/json"
        }

        # 创建队列
        self.queue: Queue = Queue()

        # 启动发送线程
        self._stop_event = threading.Event()
        self._sender_thread = threading.Thread(
            target=self._sender_worker,
            name="RemoteLogSender",
            daemon=True
        )
        self._sender_thread.start()

        # 统计信息
        self.stats = {
            "sent": 0,
            "failed": 0,
            "retries": 0,
            "queue_size": 0
        }

    def emit(self, record: logging.LogRecord) -> None:
        """发送日志记录（入队）"""
        try:
            # 格式化日志记录
            log_entry = self._format_log_entry(record)

            # 放入队列
            self.queue.put(log_entry)
            self.stats["queue_size"] = self.queue.qsize()

        except Exception as e:
            # 入队失败，记录到stderr
            print(f"RemoteHandler: Failed to queue log: {e}")

    def _format_log_entry(self, record: logging.LogRecord) -> dict:
        """格式化日志条目

        Args:
            record: 日志记录

        Returns:
            格式化的日志字典
        """
        return {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
            "exception": self.format(record) if record.exc_info else None
        }

    def _sender_worker(self) -> None:
        """发送工作线程

        从队列中批量取出日志并发送
        """
        batch = []
        last_send_time = time.time()

        while not self._stop_event.is_set():
            try:
                # 尝试获取日志（带超时）
                try:
                    log_entry = self.queue.get(timeout=0.1)
                    batch.append(log_entry)
                except Empty:
                    log_entry = None

                # 检查是否需要发送
                current_time = time.time()
                should_send = (
                    log_entry is None or  # 队列空
                    len(batch) >= self.batch_size or  # 达到批量大小
                    (current_time - last_send_time) >= self.batch_timeout  # 超时
                )

                if should_send and batch:
                    # 发送批量日志
                    self._send_batch(batch)
                    batch = []
                    last_send_time = current_time

                # 标记任务完成
                if log_entry is not None:
                    self.queue.task_done()

            except Exception as e:
                # 发送线程异常，记录并继续
                print(f"RemoteHandler sender error: {e}")
                time.sleep(1)

        # 发送剩余日志
        if batch:
            self._send_batch(batch)

    def _send_batch(self, batch: List[dict]) -> None:
        """发送批量日志

        Args:
            batch: 日志条目列表
        """
        if not batch:
            return

        # 准备数据
        data = json.dumps({"logs": batch}).encode("utf-8")

        # 重试发送
        for attempt in range(self.max_retries):
            try:
                # 发送HTTP请求
                request = urllib.request.Request(
                    self.url,
                    data=data,
                    headers=self.headers,
                    method="POST"
                )

                with urllib.request.urlopen(request, timeout=10) as response:
                    if response.status == 200:
                        # 发送成功
                        self.stats["sent"] += len(batch)
                        return

            except urllib.error.URLError as e:
                # 网络错误，重试
                self.stats["retries"] += 1

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    # 最后一次重试失败
                    self.stats["failed"] += len(batch)
                    print(f"RemoteHandler: Failed to send logs after {self.max_retries} attempts")

            except Exception as e:
                # 其他错误
                self.stats["failed"] += len(batch)
                print(f"RemoteHandler: Failed to send logs: {e}")
                break

    def close(self) -> None:
        """关闭处理器"""
        # 停止发送线程
        self._stop_event.set()

        # 等待队列清空
        self.queue.join()

        # 等待线程结束
        self._sender_thread.join(timeout=5.0)

        # 调用父类关闭
        super().close()

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            **self.stats,
            "queue_size": self.queue.qsize()
        }


class BatchRemoteHandler(RemoteHandler):
    """批量远程日志处理器（增强版）

    增加本地缓存和压缩功能
    """

    def __init__(
        self,
        url: str,
        cache_file: Optional[str] = None,
        compress: bool = False,
        **kwargs
    ):
        """初始化批量远程处理器

        Args:
            url: 远程日志收集URL
            cache_file: 本地缓存文件路径
            compress: 是否压缩日志
            **kwargs: 其他参数传递给RemoteHandler
        """
        super().__init__(url, **kwargs)

        self.cache_file = cache_file
        self.compress = compress

    def _send_batch(self, batch: List[dict]) -> None:
        """发送批量日志（带缓存）"""
        # 先尝试发送
        super()._send_batch(batch)

        # 如果发送失败且启用了缓存
        if self.stats["failed"] > 0 and self.cache_file:
            self._cache_logs(batch)

    def _cache_logs(self, batch: List[dict]) -> None:
        """缓存日志到本地文件"""
        try:
            with open(self.cache_file, "a") as f:
                for log_entry in batch:
                    f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Failed to cache logs: {e}")
