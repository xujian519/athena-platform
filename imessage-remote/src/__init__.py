"""
Athena iMessage Remote Control Module
通过 iMessage 远程控制 Athena 工作平台

Version: 0.1.0
Author: Xu Jian
"""

__version__ = "0.1.0"
__author__ = "Xu Jian"

from .core.imessage_client import IMessageClient
from .core.command_parser import CommandParser
from .core.command_router import CommandRouter
from .agents.xiaonuo_agent import XiaonuoAgent
from .agents.athena_agent import AthenaAgent
from .obsidian.writer import ObsidianWriter

__all__ = [
    "IMessageClient",
    "CommandParser",
    "CommandRouter",
    "XiaonuoAgent",
    "AthenaAgent",
    "ObsidianWriter",
]
