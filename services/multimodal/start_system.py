#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态文件系统启动脚本
Multimodal File System Startup Script
"""

import os
from core.async_main import async_main
import sys
import asyncio
import logging
from core.logging_config import setup_logging
from pathlib import Path

# 添加路径
sys.path.append(str(Path(__file__).parent))

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

async def main():
    """主启动函数"""
    print("🚀 启动 Athena 多模态文件系统...")
    print("=" * 50)

    try:
        # 导入主应用
        from secure_multimodal_api import app, start_services

        # 启动所有服务
        await start_services()

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("\n请确保以下文件存在:")
        print("- secure_multimodal_api.py")
        print("- security/auth_manager.py")
        print("- monitoring/performance_monitor.py")
        print("- ai/ai_processor.py")
        print("- 其他必要模块")
        return

    except Exception as e:
        logger.error(f"启动失败: {e}")
        return

# 入口点: @async_main装饰器已添加到main函数