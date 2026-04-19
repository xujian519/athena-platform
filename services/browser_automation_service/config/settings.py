#!/usr/bin/env python3
"""
配置管理模块
Configuration Settings for Browser Automation Service

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import logging
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 服务基础配置
    SERVICE_NAME: str = Field(default="browser_automation_service", description="服务名称")
    VERSION: str = Field(default="1.0.0", description="服务版本")
    ENVIRONMENT: str = Field(default="development", description="运行环境")

    HOST: str = Field(default="0.0.0.0", description="监听地址")
    PORT: int = Field(default=8030, description="监听端口")
    WORKERS: int = Field(default=1, description="工作进程数")
    LOG_LEVEL: str = Field(default="info", description="日志级别")

    # 浏览器配置
    BROWSER_TYPE: str = Field(default="chromium", description="默认浏览器类型")
    BROWSER_HEADLESS: bool = Field(default=True, description="是否无头模式")
    BROWSER_WINDOW_WIDTH: int = Field(default=1920, description="窗口宽度")
    BROWSER_WINDOW_HEIGHT: int = Field(default=1080, description="窗口高度")
    BROWSER_DISABLE_SECURITY: bool = Field(default=True, description="禁用安全限制")
    BROWSER_DOWNLOADS_PATH: str = Field(default="./downloads", description="下载路径")

    # 会话配置
    MAX_CONCURRENT_SESSIONS: int = Field(default=10, description="最大并发会话数")
    SESSION_TIMEOUT: int = Field(default=3600, description="会话超时时间(秒)")
    SESSION_CLEANUP_INTERVAL: int = Field(default=300, description="会话清理间隔(秒)")

    # 任务配置
    MAX_CONCURRENT_TASKS: int = Field(default=5, description="最大并发任务数")
    TASK_TIMEOUT: int = Field(default=300, description="任务超时时间(秒)")
    TASK_MAX_STEPS: int = Field(default=50, description="任务最大步数")

    # 功能开关
    ENABLE_AUTH: bool = Field(default=False, description="启用认证")
    ENABLE_SCREENSHOTS: bool = Field(default=True, description="启用截图")
    ENABLE_VIDEO_RECORDING: bool = Field(default=False, description="启用视频录制")
    ENABLE_WEBSOCKET: bool = Field(default=True, description="启用WebSocket")
    ENABLE_BACKGROUND_TASKS: bool = Field(default=True, description="启用后台任务")
    ENABLE_METRICS: bool = Field(default=True, description="启用监控指标")

    # CORS配置
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8010,http://localhost:8030",
        description="允许的CORS来源",
    )

    # 安全配置
    SECRET_KEY: str = Field(default="athena_browser_secret_key", description="密钥")
    ALGORITHM: str = Field(default="HS256", description="算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="令牌过期时间(分钟)")

    # Redis配置
    REDIS_URL: str = Field(default="redis://localhost:6379/1", description="Redis连接URL")
    REDIS_PASSWORD: str = Field(default="", description="Redis密码")

    # 数据库配置
    DATABASE_URL: str = Field(
        default="sqlite:///./browser_automation.db", description="数据库连接URL"
    )

    # 日志配置
    LOG_FILE: str = Field(default="./logs/browser_automation.log", description="日志文件路径")
    LOG_ROTATION: str = Field(default="1 week", description="日志轮转周期")
    LOG_RETENTION: str = Field(default="4 weeks", description="日志保留时间")

    # 监控配置
    METRICS_PORT: int = Field(default=9010, description="监控端口")

    # API限流配置
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="每分钟请求限制")
    RATE_LIMIT_BURST: int = Field(default=10, description="突发请求限制")

    # 代理配置
    HTTP_PROXY: str = Field(default="", description="HTTP代理")
    HTTPS_PROXY: str = Field(default="", description="HTTPS代理")
    NO_PROXY: str = Field(default="localhost,127.0.0.1", description="不使用代理的地址")

    # 集成配置
    ATHENA_IDENTITY_URL: str = Field(
        default="http://localhost:8010", description="Athena身份服务URL"
    )
    ATHENA_MEMORY_URL: str = Field(
        default="http://localhost:8008", description="Athena记忆服务URL"
    )
    XIAONUO_MEMORY_URL: str = Field(
        default="http://localhost:8083", description="小诺记忆服务URL"
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """获取允许的来源列表"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# 全局配置实例
settings = Settings()


def setup_logging() -> logging.Logger:
    """设置日志配置"""
    # 确保日志目录存在
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建日志记录器
    logger = logging.getLogger("browser_automation")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # 文件处理器
    file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # 格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# 预配置日志记录器
logger = setup_logging()


# 导出
__all__ = ["settings", "logger", "setup_logging"]
