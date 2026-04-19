#!/usr/bin/env python3
from __future__ import annotations
"""
小诺智能体模块 (XiaonuoAgent Module)
完整的AI智能体实现

架构组成:
├── memory/           # 三层记忆系统
├── reasoning/        # ReAct推理引擎
├── planning/         # HTN层次规划器
├── emotion/          # PAD情感系统
├── learning/         # 强化学习引擎
├── metacognition/    # 元认知系统
├── tools/            # Function Calling工具系统
└── xiaonuo_agent.py  # 主智能体类

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

from core.xiaonuo_agent.xiaonuo_agent import (
    AgentProfile,
    AgentResponse,
    AgentState,
    XiaonuoAgent,
    create_xiaonuo_agent,
)

__all__ = ["AgentProfile", "AgentResponse", "AgentState", "XiaonuoAgent", "create_xiaonuo_agent"]

__version__ = "2.0.0"
__author__ = "Athena平台团队"
