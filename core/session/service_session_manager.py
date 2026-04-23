#!/usr/bin/env python3
from __future__ import annotations
"""
服务会话管理器 - 60分钟不使用自动释放
Service Session Manager - Auto-release after 60 minutes of inactivity

统一管理所有后台服务的会话生命周期，实现：
1. 会话活动跟踪
2. 空闲超时自动释放
3. 资源使用监控
4. 优雅关闭机制

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-02-09
"""

import asyncio
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import psutil

# 导入配置管理器
try:
    from core.session.auto_release_config import get_auto_release_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """服务类型"""
    # 核心服务
    GATEWAY = "gateway"           # Gateway网关服务
    API = "api"                   # API主服务
    AGENT = "agent"               # 智能体服务

    # 智能体
    XIAONUO = "xiaonuo"           # 小诺 - 调度官
    XIAONA = "xiaona"             # 小娜 - 法律专家
    XIAOCHEN = "xiaochen"         # 小宸 - 自媒体

    # 支撑服务
    CACHE = "cache"               # 缓存服务
    NLP = "nlp"                   # NLP服务
    MONITOR = "monitor"           # 监控系统
    OPTIMIZATION = "optimization" # 优化服务

    # 其他
    UNKNOWN = "unknown"


@dataclass
class ServiceSession:
    """服务会话信息"""
    service_type: ServiceType
    process_id: int
    service_name: str
    started_at: datetime
    last_activity: datetime
    memory_mb: float = 0.0
    auto_stop: bool = True
    custom_timeout: Optional[int] = None  # 自定义超时时间（秒），None使用默认60分钟

    @property
    def idle_time_seconds(self) -> float:
        """获取空闲时间（秒）"""
        return (datetime.now() - self.last_activity).total_seconds()

    def is_expired(self, default_timeout: int = 3600) -> bool:
        """检查会话是否过期"""
        timeout = self.custom_timeout if self.custom_timeout is not None else default_timeout
        if not self.auto_stop:
            return False
        return self.idle_time_seconds > timeout

    @property
    def is_process_alive(self) -> bool:
        """检查进程是否存活"""
        try:
            return psutil.pid_exists(self.process_id)
        except Exception:
            return False

    def update_activity(self):
        """更新活动时间"""
        self.last_activity = datetime.now()

    def get_memory_usage(self) -> float:
        """获取内存使用量（MB）"""
        try:
            if not self.is_process_alive:
                return 0.0
            process = psutil.Process(self.process_id)
            return process.memory_info().rss / 1024 / 1024  # 转换为MB
        except Exception:
            return 0.0


@dataclass
class ServiceConfig:
    """服务配置"""
    service_type: ServiceType
    service_name: str
    default_timeout: int = 3600  # 默认60分钟
    auto_stop: bool = True
    priority: int = 5  # 优先级，1-10，数字越小优先级越高


class ServiceSessionManager:
    """
    服务会话管理器

    统一管理所有后台服务的会话生命周期，实现60分钟不使用自动释放。
    """

    # 默认配置
    DEFAULT_IDLE_TIMEOUT = 3600  # 60分钟
    CLEANUP_INTERVAL = 300       # 5分钟检查一次

    def __init__(
        self,
        idle_timeout: Optional[int] = None,
        cleanup_interval: Optional[int] = None,
        config_file: Optional[str] = None,
        preset: Optional[str] = None
    ):
        """
        初始化服务会话管理器

        Args:
            idle_timeout: 空闲超时时间（秒），None表示从配置加载
            cleanup_interval: 清理检查间隔（秒），None表示从配置加载
            config_file: YAML配置文件路径
            preset: 预设配置名称（development/testing/production/long_running）
        """
        # 加载配置
        if CONFIG_AVAILABLE and (idle_timeout is None or cleanup_interval is None):
            config = get_auto_release_config(config_file, preset)
            if idle_timeout is None:
                idle_timeout = config.get_idle_timeout()
            if cleanup_interval is None:
                cleanup_interval = config.get_cleanup_interval()

        # 使用默认值
        if idle_timeout is None:
            idle_timeout = self.DEFAULT_IDLE_TIMEOUT
        if cleanup_interval is None:
            cleanup_interval = self.CLEANUP_INTERVAL

        self.idle_timeout = idle_timeout
        self.cleanup_interval = cleanup_interval

        # 会话存储
        self._sessions: dict[int, ServiceSession] = {}  # pid -> session
        self._service_names: dict[str, set[int]] = {}   # service_name -> set of pids

        # 回调函数
        self._on_session_expire: Callable[[ServiceSession], None] | None = None

        # 后台任务
        self._cleanup_task: asyncio.Task | None = None
        self._running = False

        # 统计信息
        self._stats = {
            "total_sessions": 0,
            "expired_sessions": 0,
            "total_memory_freed_mb": 0.0,
            "last_cleanup_time": None
        }

        logger.info(
            f"🎭 服务会话管理器已初始化 "
            f"(超时: {idle_timeout}秒, 检查间隔: {cleanup_interval}秒)"
        )

    def register_session(
        self,
        process_id: int,
        service_type: ServiceType,
        service_name: str,
        auto_stop: bool = True,
        custom_timeout: Optional[int] = None
    ) -> ServiceSession:
        """
        注册服务会话

        Args:
            process_id: 进程ID
            service_type: 服务类型
            service_name: 服务名称
            auto_stop: 是否自动停止
            custom_timeout: 自定义超时时间（秒）

        Returns:
            创建的会话对象
        """
        now = datetime.now()

        # 创建会话
        session = ServiceSession(
            service_type=service_type,
            process_id=process_id,
            service_name=service_name,
            started_at=now,
            last_activity=now,
            auto_stop=auto_stop,
            custom_timeout=custom_timeout
        )

        # 获取初始内存使用
        session.memory_mb = session.get_memory_usage()

        # 存储会话
        self._sessions[process_id] = session
        if service_name not in self._service_names:
            self._service_names[service_name] = set()
        self._service_names[service_name].add(process_id)

        # 更新统计
        self._stats["total_sessions"] += 1

        logger.info(
            f"✅ 会话已注册: {service_name} (PID: {process_id}, "
            f"内存: {session.memory_mb:.1f}MB, 自动停止: {auto_stop})"
        )

        return session

    def update_activity(self, process_id: int) -> bool:
        """
        更新服务活动时间

        Args:
            process_id: 进程ID

        Returns:
            是否更新成功
        """
        session = self._sessions.get(process_id)
        if session:
            session.update_activity()
            logger.debug(f"🔄 活动时间已更新: {session.service_name} (PID: {process_id})")
            return True
        return False

    def get_session(self, process_id: int) -> ServiceSession | None:
        """
        获取会话信息

        Args:
            process_id: 进程ID

        Returns:
            会话对象，如果不存在返回None
        """
        return self._sessions.get(process_id)

    def get_sessions_by_service(self, service_name: str) -> list[ServiceSession]:
        """
        获取指定服务的所有会话

        Args:
            service_name: 服务名称

        Returns:
            会话列表
        """
        pids = self._service_names.get(service_name, set())
        return [self._sessions[pid] for pid in pids if pid in self._sessions]

    def get_all_sessions(self) -> list[ServiceSession]:
        """获取所有活动会话"""
        return list(self._sessions.values())

    def get_active_sessions(self) -> list[ServiceSession]:
        """获取所有活动会话（进程存活的）"""
        return [s for s in self._sessions.values() if s.is_process_alive]

    def get_expired_sessions(self) -> list[ServiceSession]:
        """获取所有过期会话"""
        return [
            s for s in self._sessions.values()
            if s.is_expired(self.idle_timeout) and s.is_process_alive
        ]

    async def start_monitoring(self):
        """启动监控任务"""
        if self._running:
            logger.warning("⚠️ 监控任务已在运行")
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"👁️ 监控任务已启动 (检查间隔: {self.cleanup_interval}秒)")

    async def stop_monitoring(self):
        """停止监控任务"""
        if not self._running:
            return

        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        logger.info("🛑 监控任务已停止")

    async def _monitoring_loop(self):
        """监控循环"""
        logger.info("🔄 监控循环已启动")

        while self._running:
            try:
                # 等待检查间隔
                await asyncio.sleep(self.cleanup_interval)

                # 执行清理
                await self._cleanup_expired()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 监控循环错误: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再继续

    async def _cleanup_expired(self) -> int:
        """
        清理过期会话

        Returns:
            清理的会话数量
        """
        expired_sessions = self.get_expired_sessions()

        if not expired_sessions:
            return 0

        logger.info(f"🧹 发现 {len(expired_sessions)} 个过期会话")

        count = 0
        for session in expired_sessions:
            try:
                # 停止进程
                await self._stop_session(session)
                count += 1
            except Exception as e:
                logger.error(f"❌ 停止会话失败: {session.service_name}, 错误: {e}")

        # 更新统计
        self._stats["expired_sessions"] += count
        self._stats["last_cleanup_time"] = datetime.now().isoformat()

        return count

    async def _stop_session(self, session: ServiceSession):
        """
        停止会话

        Args:
            session: 要停止的会话
        """
        memory_before = session.get_memory_usage()
        service_name = session.service_name
        process_id = session.process_id

        try:
            # 尝试优雅关闭
            process = psutil.Process(process_id)

            # 先发送SIGTERM
            process.terminate()

            # 等待进程结束（最多5秒）
            try:
                process.wait(timeout=5)
                logger.info(f"✅ 优雅关闭: {service_name} (PID: {process_id})")
            except psutil.TimeoutExpired:
                # 如果进程没有结束，强制杀死
                process.kill()
                logger.warning(f"⚠️ 强制关闭: {service_name} (PID: {process_id})")

            # 从会话中移除
            del self._sessions[process_id]
            if service_name in self._service_names:
                self._service_names[service_name].discard(process_id)
                if not self._service_names[service_name]:
                    del self._service_names[service_name]

            # 计算释放的内存
            memory_freed = memory_before
            self._stats["total_memory_freed_mb"] += memory_freed

            logger.info(
                f"🧹 会话已清理: {service_name} "
                f"(释放内存: {memory_freed:.1f}MB)"
            )

            # 调用回调函数
            if self._on_session_expire:
                try:
                    self._on_session_expire(session)
                except Exception as e:
                    logger.error(f"❌ 回调函数执行失败: {e}")

        except psutil.NoSuchProcess:
            logger.info(f"ℹ️ 进程已不存在: {service_name} (PID: {process_id})")
            # 从会话中移除
            del self._sessions[process_id]
        except Exception as e:
            logger.error(f"❌ 停止会话异常: {service_name}, 错误: {e}")
            raise

    def set_on_session_expire(self, callback: Callable[[ServiceSession], None]):
        """
        设置会话过期回调函数

        Args:
            callback: 回调函数，接收过期会话作为参数
        """
        self._on_session_expire = callback
        logger.info("📞 会话过期回调函数已设置")

    def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        active_sessions = self.get_active_sessions()
        total_memory = sum(s.get_memory_usage() for s in active_sessions)

        return {
            "active_sessions": len(active_sessions),
            "total_sessions_registered": self._stats["total_sessions"],
            "expired_sessions_cleaned": self._stats["expired_sessions"],
            "total_memory_freed_mb": round(self._stats["total_memory_freed_mb"], 2),
            "current_memory_usage_mb": round(total_memory, 2),
            "idle_timeout_seconds": self.idle_timeout,
            "last_cleanup_time": self._stats["last_cleanup_time"],
            "sessions": [
                {
                    "service_name": s.service_name,
                    "pid": s.process_id,
                    "idle_time_seconds": round(s.idle_time_seconds, 1),
                    "memory_mb": round(s.get_memory_usage(), 1),
                    "auto_stop": s.auto_stop
                }
                for s in active_sessions
            ]
        }

    async def cleanup_all(self):
        """清理所有会话"""
        logger.info("🧹 正在清理所有会话...")

        sessions = list(self._sessions.values())
        for session in sessions:
            try:
                await self._stop_session(session)
            except Exception as e:
                logger.error(f"❌ 清理会话失败: {session.service_name}, 错误: {e}")

        logger.info("✅ 所有会话已清理")


# =============================================================================
# === 全局实例和便捷函数 ===
# =============================================================================

_global_manager: ServiceSessionManager | None = None


def get_service_session_manager(
    idle_timeout: int = ServiceSessionManager.DEFAULT_IDLE_TIMEOUT,
    cleanup_interval: int = ServiceSessionManager.CLEANUP_INTERVAL
) -> ServiceSessionManager:
    """
    获取或创建全局服务会话管理器实例

    Args:
        idle_timeout: 空闲超时时间（秒），默认3600秒（60分钟）
        cleanup_interval: 清理检查间隔（秒），默认300秒（5分钟）

    Returns:
        ServiceSessionManager 实例
    """
    global _global_manager

    if _global_manager is None:
        _global_manager = ServiceSessionManager(
            idle_timeout=idle_timeout,
            cleanup_interval=cleanup_interval
        )

    return _global_manager


async def auto_register_current_process(
    service_type: ServiceType,
    service_name: str,
    auto_stop: bool = True,
    custom_timeout: Optional[int] = None
) -> ServiceSession:
    """
    自动注册当前进程

    Args:
        service_type: 服务类型
        service_name: 服务名称
        auto_stop: 是否自动停止
        custom_timeout: 自定义超时时间（秒）

    Returns:
        创建的会话对象
    """
    manager = get_service_session_manager()
    current_pid = os.getpid()

    session = manager.register_session(
        process_id=current_pid,
        service_type=service_type,
        service_name=service_name,
        auto_stop=auto_stop,
        custom_timeout=custom_timeout
    )

    # 启动监控（如果还没启动）
    if not manager._running:
        await manager.start_monitoring()

    return session


__all__ = [
    "ServiceType",
    "ServiceSession",
    "ServiceConfig",
    "ServiceSessionManager",
    "get_service_session_manager",
    "auto_register_current_process",
]
