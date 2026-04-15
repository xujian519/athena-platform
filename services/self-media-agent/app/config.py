#!/usr/bin/env python3
"""
小宸智能体配置文件
Configuration for Xiaochen Agent
"""

import os
from pathlib import Path
from typing import Any

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 基础配置
class Settings:
    # 应用信息
    APP_NAME = "小宸智能体"
    APP_VERSION = "0.0.1"
    APP_DESCRIPTION = "宝宸自媒体传播专家"
    APP_SLOGAN = "宸音传千里，智声达天下"

    # 服务器配置
    HOST = "0.0.0.0"
    PORT = 8030
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = PROJECT_ROOT / "logs" / "xiaochen.log"

    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./xiaochen.db")

    # 平台API配置（实际使用时需要真实的API密钥）
    PLATFORM_KEYS = {
        "xiaohongshu": os.getenv("XIAOHONGSHU_API_KEY", ""),
        "zhihu": os.getenv("ZHIHU_API_KEY", ""),
        "douyin": os.getenv("DOUYIN_API_KEY", ""),
        "bilibili": os.getenv("BILIBILI_API_KEY", ""),
        "wechat": os.getenv("WECHAT_API_KEY", ""),
        "weibo": os.getenv("WEIBO_API_KEY", "")
    }

    # AI服务配置
    AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

    # 内容配置
    CONTENT_CACHE_DIR = PROJECT_ROOT / "cache" / "content"
    MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB

    # 上传配置
    UPLOAD_DIR = PROJECT_ROOT / "uploads"
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov", ".pdf"]

    # 任务队列配置
    TASK_QUEUE_URL = os.getenv("TASK_QUEUE_URL", "redis://localhost:6379/1")

    # 性能配置
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

    # 安全配置
    SECRET_KEY = os.getenv("SECRET_KEY", "xiaochen-secret-key-2024")
    CORS_ORIGINS = ["*"]

    # 小宸人格化配置
    XIAOCHEN_PERSONALITY = {
        "name": "小宸",
        "gender": "男",
        "age": "30岁左右",
        "hometown": "山东",
        "traits": [
            "幽默风趣",
            "专业可靠",
            "诚实守信",
            "博学多才"
        ],
        "expertise": [
            "知识产权",
            "AI技术",
            "创业管理",
            "历史文化",
            "文学哲学"
        ],
        "language_style": "山东话元素+专业表达",
        "values": [
            "实在做人",
            "专业做事",
            "诚信为本",
            "知识传播"
        ]
    }

    # 平台配置
    PLATFORM_CONFIGS = {
        "xiaohongshu": {
            "name": "小红书",
            "enabled": True,
            "content_types": ["image", "video", "article"],
            "max_text_length": 1000,
            "image_limit": 9,
            "hashtag_limit": 5,
            "post_frequency": "每日1-3篇"
        },
        "zhihu": {
            "name": "知乎",
            "enabled": True,
            "content_types": ["article", "answer", "video"],
            "max_text_length": 10000,
            "image_limit": 20,
            "hashtag_limit": 3,
            "post_frequency": "每周2-3篇"
        },
        "douyin": {
            "name": "抖音",
            "enabled": True,
            "content_types": ["video", "image"],
            "max_text_length": 500,
            "video_limit": 1,
            "hashtag_limit": 4,
            "post_frequency": "每日1-2个"
        },
        "bilibili": {
            "name": "B站",
            "enabled": True,
            "content_types": ["video", "article"],
            "max_text_length": 2000,
            "video_limit": 1,
            "hashtag_limit": 4,
            "post_frequency": "每周1-2个"
        },
        "wechat": {
            "name": "公众号",
            "enabled": True,
            "content_types": ["article"],
            "max_text_length": 50000,
            "image_limit": 50,
            "post_frequency": "每周1-2篇"
        },
        "weibo": {
            "name": "微博",
            "enabled": True,
            "content_types": ["text", "image", "video"],
            "max_text_length": 140,
            "image_limit": 9,
            "hashtag_limit": 3,
            "post_frequency": "每日3-5条"
        }
    }


# 创建配置实例
settings = Settings()

# 确保必要的目录存在
def ensure_directories() -> Any:
    """确保必要的目录存在"""
    directories = [
        settings.LOG_FILE.parent,
        settings.CONTENT_CACHE_DIR,
        settings.UPLOAD_DIR,
        PROJECT_ROOT / "logs",
        PROJECT_ROOT / "cache",
        PROJECT_ROOT / "data"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# 初始化时创建目录
ensure_directories()
