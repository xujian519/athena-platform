#!/usr/bin/env python3
from __future__ import annotations
"""
协作协议 - 协议实现包
Collaboration Protocols - Protocol Implementations Package

包含所有协作协议的具体实现

作者: Athena AI系统
创建时间: 2026-01-26
版本: 2.1.0
"""

from .communication import CommunicationProtocol
from .coordination import CoordinationProtocol
from .decision import DecisionProtocol

__all__ = [
    "CommunicationProtocol",
    "CoordinationProtocol",
    "DecisionProtocol",
]
