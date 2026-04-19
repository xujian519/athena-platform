#!/usr/bin/env python3
"""
PDF文件监控服务
PDF File Monitoring Service

监测指定目录中的新增PDF文件，自动触发专利全文处理

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import hashlib
import json
import logging
import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# 使用安全哈希函数替代不安全的MD5/SHA1

logger = logging.getLogger(__name__)


class FileEventType(Enum):
    """文件事件类型"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


class ProcessingStatus(Enum):
    """处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class FileEvent:
    """文件事件"""
    event_type: FileEventType
    file_path: str
    file_size: int = 0
    detected_at: float = field(default_factory=time.time)
    checksum: str | None = None


@dataclass
class ProcessingTask:
    """处理任务"""
    file_path: str
    patent_number: str
    status: ProcessingStatus
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    error_message: str | None = None
    result: Any | None = None


class PDFMonitorService:
    """
    PDF文件监控服务

    功能:
    - 监控目录增量变化
    - PDF文件检测和验证
    - 任务队列管理
    - 自动处理触发
    - 状态持久化
    """

    def __init__(
        self,
        watch_directory: str = "/Users/xujian/apps/patents",
        recursive: bool = True,
        file_pattern: str = "*.pdf",
        check_interval: float = 5.0,
        state_file: str = ".pdf_monitor_state.json"
    ):
        """
        初始化监控服务

        Args:
            watch_directory: 监控目录路径
            recursive: 是否递归监控子目录
            file_pattern: 文件匹配模式
            check_interval: 检查间隔（秒）
            state_file: 状态文件路径
        """
        self.watch_directory = Path(watch_directory)
        self.recursive = recursive
        self.file_pattern = file_pattern
        self.check_interval = check_interval
        self.state_file = Path(watch_directory) / state_file

        # 文件追踪
        self.known_files: dict[str, dict[str, Any]] = {}
        self.pending_events: queue.Queue = queue.Queue()

        # 任务管理
        self.tasks: dict[str, ProcessingTask] = {}
        self.task_lock = threading.Lock()

        # 控制标志
        self.running = False
        self.monitor_thread: threading.Thread | None = None
        self.processor_thread: threading.Thread | None = None

        # 处理器回调
        self.processing_callback: Callable | None = None

        # 统计
        self.stats = {
            "total_detected": 0,
            "total_processed": 0,
            "total_success": 0,
            "total_failed": 0,
            "start_time": None
        }

    def load_state(self) -> Any | None:
        """加载状态文件"""
        if self.state_file.exists():
            try:
                with open(self.state_file, encoding='utf-8') as f:
                    state = json.load(f)
                    self.known_files = state.get("known_files", {})
                    logger.info(f"✅ 已加载状态文件: {len(self.known_files)}个已知文件")
            except Exception as e:
                logger.warning(f"⚠️  加载状态文件失败: {e}")

    def save_state(self) -> None:
        """保存状态文件"""
        try:
            state = {
                "known_files": self.known_files,
                "last_updated": time.time()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存状态文件失败: {e}")

    def get_file_checksum(self, file_path: str) -> str | None:
        """
        计算文件校验和

        Args:
            file_path: 文件路径

        Returns:
            MD5校验和
        """
        try:
            md5 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception as e:
            logger.error(f"❌ 计算校验和失败: {file_path}: {e}")
            return None

    def extract_patent_number(self, file_path: str) -> str | None:
        """
        从文件名提取专利号

        Args:
            file_path: 文件路径

        Returns:
            专利号
        """
        filename = Path(file_path).stem

        # 移除常见前缀
        for prefix in ["CN", "US", "EP", "JP", "KR"]:
            if filename.startswith(prefix):
                filename = filename[len(prefix):]
                break

        # 简单的专利号格式验证
        # 支持格式: 112233445A, 112233445.B, 等
        patent_number = filename.upper().replace(".", "").replace("-", "")

        return patent_number if len(patent_number) >= 9 else None

    def scan_directory(self) -> list[FileEvent]:
        """
        扫描目录检测变化

        Returns:
            文件事件列表
        """
        events = []
        current_files = {}

        # 扫描当前目录
        try:
            if self.recursive:
                pattern = f"**/{self.file_pattern}"
            else:
                pattern = self.file_pattern

            for file_path in self.watch_directory.glob(pattern):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        file_size = stat.st_size
                        file_mtime = stat.st_mtime

                        # 计算校验和
                        checksum = self.get_file_checksum(str(file_path))

                        file_key = str(file_path)
                        current_files[file_key] = {
                            "size": file_size,
                            "mtime": file_mtime,
                            "checksum": checksum
                        }

                        # 检查是否为新文件
                        if file_key not in self.known_files:
                            events.append(FileEvent(
                                event_type=FileEventType.CREATED,
                                file_path=file_key,
                                file_size=file_size,
                                checksum=checksum
                            ))
                            self.stats["total_detected"] += 1
                            logger.info(f"📄 检测到新文件: {file_path.name} ({file_size} bytes)")

                        # 检查文件是否修改
                        elif self.known_files[file_key].get("checksum") != checksum:
                            events.append(FileEvent(
                                event_type=FileEventType.MODIFIED,
                                file_path=file_key,
                                file_size=file_size,
                                checksum=checksum
                            ))
                            logger.info(f"📝 检测到文件修改: {file_path.name}")

                    except Exception as e:
                        logger.error(f"❌ 处理文件失败: {file_path}: {e}")

        except Exception as e:
            logger.error(f"❌ 扫描目录失败: {e}")

        # 检查删除的文件
        for file_key in list(self.known_files.keys()):
            if file_key not in current_files:
                events.append(FileEvent(
                    event_type=FileEventType.DELETED,
                    file_path=file_key
                ))
                logger.info(f"🗑️  检测到文件删除: {Path(file_key).name}")
                del self.known_files[file_key]

        # 更新已知文件
        self.known_files.update(current_files)

        return events

    def monitor_loop(self) -> Any:
        """监控循环"""
        logger.info(f"🔍 开始监控目录: {self.watch_directory}")
        logger.info(f"   递归模式: {self.recursive}")
        logger.info(f"   检查间隔: {self.check_interval}秒")

        while self.running:
            try:
                # 扫描目录
                events = self.scan_directory()

                # 处理事件
                for event in events:
                    if event.event_type in [FileEventType.CREATED, FileEventType.MODIFIED]:
                        self.pending_events.put(event)

                # 定期保存状态
                self.save_state()

                # 等待下次检查
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"❌ 监控循环异常: {e}")
                time.sleep(self.check_interval)

        logger.info("🛑 监控循环已停止")

    def processing_loop(self) -> Any:
        """处理循环"""
        logger.info("⚙️  开始处理循环")

        while self.running:
            try:
                # 获取事件（带超时）
                try:
                    event = self.pending_events.get(timeout=1.0)
                except queue.Empty:
                    continue

                # 创建处理任务
                patent_number = self.extract_patent_number(event.file_path)
                if not patent_number:
                    logger.warning(f"⚠️  无法提取专利号: {event.file_path}")
                    continue

                task = ProcessingTask(
                    file_path=event.file_path,
                    patent_number=patent_number,
                    status=ProcessingStatus.PROCESSING,
                    started_at=time.time()
                )

                with self.task_lock:
                    self.tasks[patent_number] = task

                logger.info(f"🔄 开始处理: {patent_number}")

                try:
                    # 调用处理回调
                    if self.processing_callback:
                        result = self.processing_callback(event.file_path, patent_number)

                        task.status = ProcessingStatus.SUCCESS
                        task.completed_at = time.time()
                        task.result = result

                        self.stats["total_processed"] += 1
                        self.stats["total_success"] += 1

                        logger.info(f"✅ 处理成功: {patent_number}")
                    else:
                        logger.warning("⚠️  未设置处理回调，跳过处理")
                        task.status = ProcessingStatus.PENDING

                except Exception as e:
                    task.status = ProcessingStatus.FAILED
                    task.completed_at = time.time()
                    task.error_message = str(e)

                    self.stats["total_processed"] += 1
                    self.stats["total_failed"] += 1

                    logger.error(f"❌ 处理失败: {patent_number}: {e}")

            except Exception as e:
                logger.error(f"❌ 处理循环异常: {e}")

        logger.info("🛑 处理循环已停止")

    def set_processing_callback(self, callback: Callable[[str, str], Any]) -> None:
        """
        设置处理回调函数

        Args:
            callback: 回调函数 (file_path, patent_number) -> result
        """
        self.processing_callback = callback
        logger.info("✅ 已设置处理回调函数")

    def start(self) -> None:
        """启动监控服务"""
        if self.running:
            logger.warning("⚠️  监控服务已在运行")
            return

        logger.info("=" * 70)
        logger.info("PDF文件监控服务启动")
        logger.info("=" * 70)

        # 加载状态
        self.load_state()

        # 设置控制标志
        self.running = True
        self.stats["start_time"] = time.time()

        # 启动监控线程
        self.monitor_thread = threading.Thread(
            target=self.monitor_loop,
            name="PDFMonitor",
            daemon=True
        )
        self.monitor_thread.start()

        # 启动处理线程
        self.processor_thread = threading.Thread(
            target=self.processing_loop,
            name="PDFProcessor",
            daemon=True
        )
        self.processor_thread.start()

        logger.info("✅ 监控服务已启动")

    def stop(self) -> None:
        """停止监控服务"""
        if not self.running:
            return

        logger.info("🛑 正在停止监控服务...")
        self.running = False

        # 等待线程结束
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        if self.processor_thread:
            self.processor_thread.join(timeout=10)

        # 保存状态
        self.save_state()

        logger.info("✅ 监控服务已停止")

    def get_status(self) -> dict[str, Any]:
        """
        获取服务状态

        Returns:
            状态信息
        """
        uptime = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0

        with self.task_lock:
            pending_count = sum(1 for t in self.tasks.values() if t.status == ProcessingStatus.PENDING)
            processing_count = sum(1 for t in self.tasks.values() if t.status == ProcessingStatus.PROCESSING)
            success_count = sum(1 for t in self.tasks.values() if t.status == ProcessingStatus.SUCCESS)
            failed_count = sum(1 for t in self.tasks.values() if t.status == ProcessingStatus.FAILED)

        return {
            "running": self.running,
            "watch_directory": str(self.watch_directory),
            "uptime_seconds": uptime,
            "known_files_count": len(self.known_files),
            "tasks": {
                "pending": pending_count,
                "processing": processing_count,
                "success": success_count,
                "failed": failed_count,
                "total": len(self.tasks)
            },
            "stats": self.stats
        }

    def get_recent_tasks(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        获取最近的任务

        Args:
            limit: 返回数量

        Returns:
            任务列表
        """
        with self.task_lock:
            tasks = list(self.tasks.values())

        # 按创建时间排序
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return [
            {
                "patent_number": t.patent_number,
                "file_path": t.file_path,
                "status": t.status.value,
                "created_at": datetime.fromtimestamp(t.created_at).isoformat(),
                "started_at": datetime.fromtimestamp(t.started_at).isoformat() if t.started_at else None,
                "completed_at": datetime.fromtimestamp(t.completed_at).isoformat() if t.completed_at else None,
                "error_message": t.error_message
            }
            for t in tasks[:limit]
        ]


# ========== 便捷函数 ==========

def create_pdf_monitor(
    watch_directory: str = "/Users/xujian/apps/patents",
    **kwargs
) -> PDFMonitorService:
    """
    创建PDF监控服务

    Args:
        watch_directory: 监控目录
        **kwargs: 其他参数

    Returns:
        PDFMonitorService
    """
    return PDFMonitorService(watch_directory=watch_directory, **kwargs)


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""

    print("=" * 70)
    print("PDF文件监控服务示例")
    print("=" * 70)

    # 创建监控服务
    monitor = create_pdf_monitor(
        watch_directory="/Users/xujian/apps/patents",
        recursive=True,
        check_interval=5.0
    )

    # 设置处理回调（示例）
    def process_pdf(file_path: str, patent_number: str) -> Any | None:
        print(f"\n📄 处理文件: {file_path}")
        print(f"🔢 专利号: {patent_number}")
        # 这里集成实际的专利处理逻辑
        # 例如: process_patent_with_pdf(file_path, patent_number)
        return {"success": True, "message": "处理完成"}

    monitor.set_processing_callback(process_pdf)

    # 启动服务
    monitor.start()

    print("\n✅ 监控服务已启动，按Ctrl+C停止...")
    print(f"📁 监控目录: {monitor.watch_directory}")
    print(f"⏱️  检查间隔: {monitor.check_interval}秒")

    try:
        # 定期打印状态
        while True:
            time.sleep(30)
            status = monitor.get_status()
            print("\n📊 服务状态:")
            print(f"  运行时间: {status['uptime_seconds']:.0f}秒")
            print(f"  已知文件: {status['known_files_count']}")
            print(f"  检测到: {status['stats']['total_detected']}")
            print(f"  已处理: {status['stats']['total_processed']}")
            print(f"  成功: {status['stats']['total_success']}")
            print(f"  失败: {status['stats']['total_failed']}")

    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信号...")
        monitor.stop()

        # 打印最终状态
        status = monitor.get_status()
        print("\n📊 最终统计:")
        print(f"  总运行时间: {status['uptime_seconds']:.0f}秒")
        print(f"  检测文件: {status['stats']['total_detected']}")
        print(f"  处理文件: {status['stats']['total_processed']}")
        print(f"  成功: {status['stats']['total_success']}")
        print(f"  失败: {status['stats']['total_failed']}")

        # 最近任务
        recent = monitor.get_recent_tasks(5)
        if recent:
            print("\n📋 最近任务:")
            for task in recent:
                status_emoji = "✅" if task['status'] == 'success' else "❌"
                print(f"  {status_emoji} {task['patent_number']}: {task['status']}")


if __name__ == "__main__":
    main()
