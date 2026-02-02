"""
Scripts模块
提供统一的脚本管理和运行时环境
"""

# 导出主要组件
from .core.config import config, settings
from .core.database import db_manager
from .services.manager import ServiceManager, service_manager
from .services.health_checker import health_checker
from .services.monitoring import monitoring_service
from .services.deployment import deployment_manager

__version__ = "1.0.0"
__author__ = "Athena Platform Team"