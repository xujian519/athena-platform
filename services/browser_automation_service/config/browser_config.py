#!/usr/bin/env python3
"""
浏览器配置模块
Browser Configuration for Browser Automation Service

作者: 小诺·双鱼公主
版本: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BrowserConfig:
    """浏览器配置类"""

    # 浏览器类型
    browser_type: str = "chromium"  # chromium, firefox, webkit

    # 启动参数
    headless: bool = True
    window_width: int = 1920
    window_height: int = 1080
    disable_security: bool = True

    # 下载路径
    downloads_path: str = "./downloads"

    # 用户代理
    user_agent: str | None = None

    # 启动参数
    launch_args: list[str] = field(default_factory=lambda: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-web-security",
    ])

    # 视口配置
    viewport: dict[str, int] = field(default_factory=lambda: {
        "width": 1920,
        "height": 1080,
    })

    # 超时配置
    navigation_timeout: int = 30000  # 毫秒
    default_timeout: int = 5000  # 毫秒

    def get_launch_options(self) -> dict[str, Any]:
        """获取浏览器启动选项"""
        options = {
            "headless": self.headless,
            "args": self.launch_args,
        }

        # 添加视口配置
        if not self.headless:
            options["viewport"] = self.viewport

        # 如果设置了用户代理
        if self.user_agent:
            options["user_agent"] = self.user_agent

        return options


# 预定义的浏览器配置
CHROMIUM_CONFIG = BrowserConfig(
    browser_type="chromium",
    headless=True,
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)

FIREFOX_CONFIG = BrowserConfig(
    browser_type="firefox",
    headless=True,
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
)

WEBKIT_CONFIG = BrowserConfig(
    browser_type="webkit",
    headless=True,
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
)


def get_browser_config(browser_type: str = "chromium") -> BrowserConfig:
    """获取浏览器配置"""
    configs = {
        "chromium": CHROMIUM_CONFIG,
        "firefox": FIREFOX_CONFIG,
        "webkit": WEBKIT_CONFIG,
    }
    return configs.get(browser_type, CHROMIUM_CONFIG)


# 导出
__all__ = [
    "BrowserConfig",
    "CHROMIUM_CONFIG",
    "FIREFOX_CONFIG",
    "WEBKIT_CONFIG",
    "get_browser_config",
]
