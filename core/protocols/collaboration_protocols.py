#!/usr/bin/env python3
from __future__ import annotations
"""
协作协议 - 向后兼容重定向
Collaboration Protocols - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.protocols.collaboration

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0-refactored

--- 迁移指南 ---

旧导入:
  from core.protocols.collaboration_protocols import BaseProtocol
  from core.protocols.collaboration_protocols import CommunicationProtocol

新导入:
  from core.protocols.collaboration import BaseProtocol
  from core.protocols.collaboration import CommunicationProtocol
  # 或
  from core.protocols.collaboration import (
      BaseProtocol,
      CommunicationProtocol,
      CoordinationProtocol,
      DecisionProtocol,
      ProtocolManager,
      create_protocol_session,
  )

--- 文件结构 ---

core/protocols/collaboration/
├── __init__.py              # 公共接口导出
├── types.py                 # 数据类型定义
├── base.py                  # 基础协议类 (353行)
├── manager.py               # 协议管理器 (143行)
├── utils.py                 # 工具函数 (26行)
└── protocols/               # 协议实现
    ├── __init__.py
    ├── communication.py     # 通信协议 (235行)
    ├── coordination.py      # 协调协议 (520行)
    └── decision.py          # 决策协议 (460行)

总计: ~1737行 (原文件: 1739行)

--- 使用示例 ---

# 推荐导入方式
from core.protocols.collaboration import (
    BaseProtocol,
    CommunicationProtocol,
    CoordinationProtocol,
    DecisionProtocol,
    ProtocolManager,
    create_protocol_session,
)

# 使用协议管理器
manager = ProtocolManager()
protocol_id = manager.create_communication_protocol(
    participants=["agent1", "agent2"]
)

# 使用便捷函数
protocol_id = create_protocol_session(
    protocol_type="communication",
    participants=["agent1", "agent2"]
)

"""

import logging
import warnings

logger = logging.getLogger(__name__)

# 向后兼容重定向
# 便捷函数从protocols主模块导入
from core.protocols import (
    create_communication_protocol,
    create_coordination_protocol,
    create_decision_protocol,
)
from core.protocols.collaboration import (  # type: ignore
    BaseProtocol,
    CommunicationProtocol,
    CoordinationProtocol,
    DecisionProtocol,
    ProtocolContext,
    ProtocolManager,
    ProtocolMessage,
    ProtocolPhase,
    ProtocolStatus,
    ProtocolType,
    create_protocol_session,
    get_protocol_session_status,
    protocol_manager,
    shutdown_protocol_manager,
    start_protocol_session,
)

# 发出迁移警告
warnings.warn(
    "collaboration_protocols.py 已重构，请使用新导入路径: "
    "from core.protocols.collaboration import CommunicationProtocol",
    DeprecationWarning,
    stacklevel=2,
)

logger.info("⚠️  使用已重构的collaboration_protocols.py，建议更新导入路径")

# 导出所有公共接口以保持向后兼容
__all__ = [
    # 基础类
    "BaseProtocol",
    # 协议实现
    "CommunicationProtocol",
    "CoordinationProtocol",
    "DecisionProtocol",
    # 数据类
    "ProtocolContext",
    "ProtocolMessage",
    "ProtocolPhase",
    "ProtocolStatus",
    "ProtocolType",
    # 管理器
    "ProtocolManager",
    "protocol_manager",
    # 便捷函数
    "create_communication_protocol",
    "create_coordination_protocol",
    "create_decision_protocol",
    "create_protocol_session",
    "start_protocol_session",
    "get_protocol_session_status",
    "shutdown_protocol_manager",
]
