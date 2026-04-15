#!/usr/bin/env python3
"""
文章撰写服务配置
Article Writer Service Configuration
"""

import os
from pathlib import Path


class Config:
    """基础配置"""

    # 服务配置
    SERVICE_NAME = "Athena Article Writer Service"
    SERVICE_VERSION = "1.0.0"
    SERVICE_PORT = 8031

    # 路径配置
    BASE_DIR = Path(__file__).parent.parent
    ROOT_DIR = Path(__file__).parent.parent.parent.parent

    # OpenClaw配置
    OPENCLAW_MEDIA_PATH = Path("/Users/xujian/Documents/自媒体运营")
    OPENCLAW_HANDOVER_ENABLED = True

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS配置
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8030",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8030"
    ]

    # 文章配置
    ARTICLE_MIN_LENGTH = 500
    ARTICLE_MAX_LENGTH = 10000
    SUMMARY_MAX_LENGTH = 200

    # 配图配置
    IMAGE_GENERATION_ENABLED = False  # 配图生成功能（需要AI图像服务）
    DEFAULT_IMAGE_STYLE = "专业风格"

    # 平台配置
    PLATFORM_LIMITS = {
        "微信公众号": {
            "min_length": 1000,
            "max_length": 50000,
            "image_count": 50
        },
        "小红书": {
            "min_length": 300,
            "max_length": 1000,
            "image_count": 9
        },
        "知乎": {
            "min_length": 500,
            "max_length": 10000,
            "image_count": 20
        },
        "今日头条": {
            "min_length": 500,
            "max_length": 2000,
            "image_count": 20
        },
        "微博": {
            "min_length": 10,
            "max_length": 140,
            "image_count": 9
        }
    }


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    RELOAD = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    RELOAD = False


# 根据环境变量选择配置
def get_config() -> Config:
    """获取配置"""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()


# 全局配置实例
settings = get_config()
