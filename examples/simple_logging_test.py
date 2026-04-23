#!/usr/bin/env python3
"""
简单的日志测试
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging import LogLevel, get_logger

# 测试基础日志
logger = get_logger("test", level=LogLevel.INFO)

logger.info("测试开始")
logger.add_context("request_id", "req-001")
logger.info("请求处理中")
logger.warning("这是一个警告")
logger.error("这是一个错误")
logger.info("测试完成")
