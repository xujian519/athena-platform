"""
命令模块初始化
Commands Module Initialization
"""

from athena_cli.commands.search import app as search_app
from athena_cli.commands.analyze import app as analyze_app
from athena_cli.commands.batch import app as batch_app
from athena_cli.commands.config import app as config_app

__all__ = [
    "search_app",
    "analyze_app",
    "batch_app",
    "config_app",
]
