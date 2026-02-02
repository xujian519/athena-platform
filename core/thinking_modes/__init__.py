#!/usr/bin/env python3
"""
思考模式模块
Thinking Modes Module - 多种思考模式的选择和执行

支持5种思考模式(来自JoyAgent):
1. ReAct: 推理-行动循环
2. Plan: 先规划后执行
3. SOPPlan: 标准作业程序
4. Executor: 直接执行
5. TreeOfThought: 树状推理

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

from .mode_selector import (
    ModeCharacteristics,
    ThinkingMode,
    ThinkingModeExecutor,
    ThinkingModeSelector,
    execute_with_best_mode,
    select_thinking_mode,
)

__all__ = [
    "ModeCharacteristics",
    "ThinkingMode",
    "ThinkingModeExecutor",
    "ThinkingModeSelector",
    "execute_with_best_mode",
    "select_thinking_mode",
]
