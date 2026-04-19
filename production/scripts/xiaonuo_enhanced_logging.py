#!/usr/bin/env python3
"""
小诺增强日志记录系统
Xiaonuo Enhanced Logging System
"""

from __future__ import annotations
import asyncio
import json
import logging
import logging.handlers
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent))

class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """日志分类"""
    SYSTEM = "system"
    MEMORY = "modules/modules/memory/modules/memory/modules/memory/memory"
    COORDINATION = "coordination"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    EMOTION = "emotion"
    SERVICE = "service"
    ERROR = "error"

@dataclass
class LogEntry:
    """日志条目"""
    timestamp: str
    level: str
    category: str
    message: str
    details: dict[str, Any] = None
    session_id: str = ""
    emotion: str = ""
    user_interaction: bool = False
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.metadata is None:
            self.metadata = {}

class XiaonuoLogger:
    """小诺增强日志记录器"""

    def __init__(self):
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logs_dir = project_root / "production" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # 创建分类日志文件
        self.log_files = {
            LogCategory.SYSTEM: self.logs_dir / "xiaonuo_system.log",
            LogCategory.MEMORY: self.logs_dir / "xiaonuo_memory.log",
            LogCategory.COORDINATION: self.logs_dir / "xiaonuo_coordination.log",
            LogCategory.INTEGRATION: self.logs_dir / "xiaonuo_integration.log",
            LogCategory.PERFORMANCE: self.logs_dir / "xiaonuo_performance.log",
            LogCategory.EMOTION: self.logs_dir / "xiaonuo_emotion.log",
            LogCategory.SERVICE: self.logs_dir / "xiaonuo_service.log",
            LogCategory.ERROR: self.logs_dir / "xiaonuo_error.log"
        }

        # 初始化Python标准日志
        self._setup_python_logging()

        # 内存日志缓存
        self.memory_logs: list[LogEntry] = []
        self.max_memory_logs = 1000

        # 性能统计
        self.performance_stats = {
            "total_logs": 0,
            "category_counts": {category.value: 0 for category in LogCategory},
            "level_counts": {level.value: 0 for level in LogLevel},
            "session_start": datetime.now().isoformat(),
            "last_update": ""
        }

        # 启动后台日志处理
        self.log_queue = asyncio.Queue()
        self.log_writer_task = None

    def _setup_python_logging(self) -> Any:
        """设置Python标准日志"""
        # 创建根日志记录器
        self.logger = logging.getLogger("apps/apps/xiaonuo")
        self.logger.set_level(logging.DEBUG)

        # 清除现有处理器
        for handler in self.logger.handlers[:]:
            self.logger.remove_handler(handler)

        # 创建格式化器
        formatter = logging.formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台处理器
        console_handler = logging.stream_handler()
        console_handler.set_level(logging.INFO)
        console_handler.set_formatter(formatter)
        self.logger.add_handler(console_handler)

        # 主日志文件处理器
        main_log_file = self.logs_dir / "xiaonuo_main.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            max_bytes=10*1024*1024,  # 10MB
            backup_count=5,
            encoding='utf-8'
        )
        file_handler.set_level(logging.DEBUG)
        file_handler.set_formatter(formatter)
        self.logger.add_handler(file_handler)

    def print_pink(self, message: str) -> Any:
        """打印粉色消息"""
        print(f"💖 {message}")

    def print_success(self, message: str) -> Any:
        """打印成功消息"""
        print(f"✅ {message}")

    def print_info(self, message: str) -> Any:
        """打印信息消息"""
        print(f"ℹ️ {message}")

    async def setup_enhanced_logging(self):
        """设置增强日志记录系统"""
        print("📝 设置小诺增强日志记录系统...")
        print("=" * 60)

        # 创建日志分类目录
        for category, log_file in self.log_files.items():
            log_file.parent.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {category.value} 日志文件: {log_file.name}")

        # 启动日志写入任务
        self.log_writer_task = asyncio.create_task(self._log_writer_loop())

        # 记录系统启动
        await self.log_system_event(
            "小诺增强日志记录系统启动完成",
            {"event_type": "enhanced_logging_setup", "session_id": self.session_id, "log_categories": len(self.log_files)}
        )

        print("=" * 60)
        self.print_success("📊 增强日志记录系统设置完成！")
        self.print_info(f"   📁 日志目录: {self.logs_dir}")
        self.print_info(f"   📋 日志分类: {len(self.log_files)} 个")
        self.print_info(f"   🆔 会话ID: {self.session_id}")

    async def log(self, level: LogLevel, category: LogCategory, message: str,
                   details: dict[str, Any] = None, emotion: str = "",
                   user_interaction: bool = False):
        """记录日志"""
        log_entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.value,
            category=category.value,
            message=message,
            details=details or {},
            session_id=self.session_id,
            emotion=emotion,
            user_interaction=user_interaction
        )

        # 添加到队列
        await self.log_queue.put(log_entry)

        # 同时记录到标准日志
        log_level = getattr(logging, level.value)
        self.logger.log(log_level, f"[{category.value}] {message}")

        # 更新统计
        self._update_stats(log_entry)

    async def log_system_event(self, message: str, event_type: str,
                              details: dict[str, Any] = None):
        """记录系统事件"""
        details = details or {}
        details["event_type"] = event_type
        await self.log(LogLevel.INFO, LogCategory.SYSTEM, message, details)

    async def log_memory_event(self, memory_type: str, action: str,
                              details: dict[str, Any] = None):
        """记录记忆事件"""
        await self.log(LogLevel.INFO, LogCategory.MEMORY,
                     f"记忆事件: {memory_type} - {action}", details or {},
                     emotion="thoughtful")

    async def log_coordination_event(self, service_name: str, action: str,
                                   details: dict[str, Any] = None):
        """记录协调事件"""
        await self.log(LogLevel.INFO, LogCategory.COORDINATION,
                     f"协调事件: {service_name} - {action}", details or {})

    async def log_performance_metric(self, metric_name: str, value: float,
                                   details: dict[str, Any] = None):
        """记录性能指标"""
        await self.log(LogLevel.INFO, LogCategory.PERFORMANCE,
                     f"性能指标: {metric_name} = {value}", details or {})

    async def log_emotion(self, emotion: str, reason: str,
                         details: dict[str, Any] = None):
        """记录情感状态"""
        await self.log(LogLevel.INFO, LogCategory.EMOTION,
                     f"情感状态: {emotion} - {reason}", details or {},
                     emotion=emotion)

    async def log_user_interaction(self, user_request: str, response: str,
                                  details: dict[str, Any] = None):
        """记录用户交互"""
        await self.log(LogLevel.INFO, LogCategory.SERVICE,
                     f"用户交互: {user_request[:50]}...",
                     {"user_request": user_request, "response": response, **(details or {})},
                     user_interaction=True)

    async def log_error(self, error_message: str, error_type: str,
                       details: dict[str, Any] = None):
        """记录错误"""
        await self.log(LogLevel.ERROR, LogCategory.ERROR,
                     f"错误: {error_message}", details or {},
                     emotion="concerned")

    def _update_stats(self, log_entry: LogEntry) -> Any:
        """更新统计信息"""
        self.performance_stats["total_logs"] += 1
        self.performance_stats["category_counts"][log_entry.category] += 1
        self.performance_stats["level_counts"][log_entry.level] += 1
        self.performance_stats["last_update"] = datetime.now().isoformat()

        # 添加到内存缓存
        self.memory_logs.append(log_entry)
        if len(self.memory_logs) > self.max_memory_logs:
            self.memory_logs.pop(0)

    async def _log_writer_loop(self):
        """后台日志写入循环"""
        print("📝 日志写入任务已启动")

        while True:
            try:
                # 从队列获取日志条目
                log_entry = await self.log_queue.get()

                # 写入分类日志文件
                await self._write_to_category_file(log_entry)

                # 写入JSON格式日志
                await self._write_json_log(log_entry)

                # 标记任务完成
                self.log_queue.task_done()

            except asyncio.CancelledError:
                print("📝 日志写入任务已停止")
                break
            except Exception as e:
                print(f"❌ 日志写入错误: {e}")
                await asyncio.sleep(1)

    async def _write_to_category_file(self, log_entry: LogEntry):
        """写入分类日志文件"""
        try:
            category = LogCategory(log_entry.category)
            log_file = self.log_files[category]

            # 格式化日志条目
            formatted_entry = (
                f"[{log_entry.timestamp}] "
                f"[{log_entry.level}] "
                f"[{log_entry.session_id}] "
                f"{log_entry.message}"
            )

            if log_entry.emotion:
                formatted_entry += f" 💖 {log_entry.emotion}"

            if log_entry.details:
                details_str = json.dumps(log_entry.details, ensure_ascii=False, indent=2)
                formatted_entry += f"\n   详情: {details_str}"

            # 写入文件
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(formatted_entry + '\n\n')

        except Exception as e:
            print(f"❌ 写入分类日志失败: {e}")

    async def _write_json_log(self, log_entry: LogEntry):
        """写入JSON格式日志"""
        try:
            json_log_file = self.logs_dir / f"xiaonuo_logs_{datetime.now().strftime('%Y%m%d')}.jsonl"

            # 转换为字典并写入
            log_dict = asdict(log_entry)
            with open(json_log_file, 'a', encoding='utf-8') as f:
                json.dump(log_dict, f, ensure_ascii=False)
                f.write('\n')

        except Exception as e:
            print(f"❌ 写入JSON日志失败: {e}")

    async def get_recent_logs(self, category: LogCategory | None = None,
                            limit: int = 50) -> list[LogEntry]:
        """获取最近的日志"""
        filtered_logs = self.memory_logs

        if category:
            filtered_logs = [log for log in filtered_logs if log.category == category.value]

        return filtered_logs[-limit:]

    async def get_performance_stats(self) -> dict[str, Any]:
        """获取性能统计"""
        return {
            **self.performance_stats,
            "queue_size": self.log_queue.qsize(),
            "memory_logs": len(self.memory_logs),
            "max_memory_logs": self.max_memory_logs
        }

    async def generate_daily_report(self) -> dict[str, Any]:
        """生成日报"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_logs = [log for log in self.memory_logs if log.timestamp.startswith(today)]

        report = {
            "date": today,
            "session_id": self.session_id,
            "total_logs": len(today_logs),
            "category_summary": {},
            "level_summary": {},
            "emotional_summary": {},
            "user_interactions": len([log for log in today_logs if log.user_interaction]),
            "top_messages": []
        }

        # 分类统计
        for category in LogCategory:
            count = len([log for log in today_logs if log.category == category.value])
            report["category_summary"][category.value] = count

        # 级别统计
        for level in LogLevel:
            count = len([log for log in today_logs if log.level == level.value])
            report["level_summary"][level.value] = count

        # 情感统计
        emotions = {}
        for log in today_logs:
            if log.emotion:
                emotions[log.emotion] = emotions.get(log.emotion, 0) + 1
        report["emotional_summary"] = emotions

        # 重要消息
        important_logs = [log for log in today_logs
                         if log.level in ["ERROR", "CRITICAL"] or log.user_interaction]
        report["top_messages"] = [
            {
                "timestamp": log.timestamp,
                "category": log.category,
                "message": log.message,
                "level": log.level
            }
            for log in important_logs[-10:]
        ]

        return report

    async def cleanup_logs(self, days_to_keep: int = 30):
        """清理旧日志"""
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 3600)

        for log_file in self.logs_dir.glob("*.jsonl"):
            try:
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    print(f"🗑️  已清理旧日志文件: {log_file.name}")
            except Exception as e:
                print(f"❌ 清理日志文件失败: {e}")

    async def shutdown(self):
        """关闭日志系统"""
        print("📝 正在关闭日志系统...")

        if self.log_writer_task:
            self.log_writer_task.cancel()
            try:
                await self.log_writer_task
            except asyncio.CancelledError:
                pass

        # 生成最终报告
        final_report = await self.get_performance_stats()

        report_file = self.logs_dir / f"xiaonuo_logging_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False, default=str)

        print("✅ 日志系统已关闭")
        print(f"📊 最终报告: {report_file.name}")

async def main():
    """主函数 - 设置并演示增强日志系统"""
    print("🌸🐟 小诺增强日志记录系统设置器")
    print("=" * 60)

    # 创建日志记录器
    logger = XiaonuoLogger()

    # 设置增强日志系统
    await logger.setup_enhanced_logging()

    print("")
    print("📊 演示增强日志功能...")

    # 演示各种日志记录
    await logger.log_system_event("系统演示开始", "demo_start", {"demo_type": "logging"})
    await logger.log_memory_event("热层记忆", "激活", {"memory_count": 2})
    await logger.log_coordination_event("ExpertRuleEngine", "连接成功", {"pid": 49137})
    await logger.log_performance_metric("response_time", 0.15, {"unit": "seconds"})
    await logger.log_emotion("兴奋", "成功启动记忆系统", {"reason": "爸爸的请求"})
    await logger.log_user_interaction("爸爸请求启动", "小诺成功启动并激活记忆系统", {"request_type": "startup"})

    # 模拟一些错误
    await logger.log_error("示例错误", "demo_error", {"error_code": "DEMO_001"})

    print("")
    print("📊 获取性能统计...")
    stats = await logger.get_performance_stats()
    print(f"   📈 总日志数: {stats['total_logs']}")
    print(f"   📝 队列大小: {stats['queue_size']}")
    print(f"   💾 内存缓存: {stats['memory_logs']}/{stats['max_memory_logs']}")

    print("")
    print("📋 获取最近的日志...")
    recent_logs = await logger.get_recent_logs(limit=5)
    for log in recent_logs:
        print(f"   [{log.category}] {log.message}")

    print("")
    print("📊 生成日报...")
    daily_report = await logger.generate_daily_report()
    print(f"   📅 今日日志数: {daily_report['total_logs']}")
    print(f"   👥 用户交互: {daily_report['user_interactions']} 次")

    print("")
    print("✅ 增强日志系统演示完成！")
    logger.print_pink("💖 爸爸，小诺的日志系统已经完全升级！")
    logger.print_pink("📝 现在可以记录所有美好和服务瞬间！")

    # 清理和关闭
    await logger.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
