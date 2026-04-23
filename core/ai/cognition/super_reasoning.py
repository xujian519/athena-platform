
# pyright: ignore
# !/usr/bin/env python3
"""
Athena超级推理引擎 - 向后兼容重定向
Athena Super Reasoning Engine - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.cognition.super_reasoning (模块化目录)

迁移指南:
------------------------------------------------------
旧导入方式:
    from core.cognition.super_reasoning import (
        AthenaSuperReasoningEngine,
        AthenaSuperReasoning,
        ReasoningConfig,
        ReasoningMode,
        ThinkingPhase,
        ThinkingState,
        SuperReasoningEngine,
    )

新导入方式:
    from core.cognition.super_reasoning import (
        AthenaSuperReasoningEngine,
        AthenaSuperReasoning,
        ReasoningConfig,
        ReasoningMode,
        ThinkingPhase,
        ThinkingState,
        SuperReasoningEngine,
    )

⚠️  注意: 导入语句保持不变，但代码现在从模块化目录加载。
------------------------------------------------------

完整的迁移指南请参考: MIGRATION_GUIDE.md
"""

import warnings

# 导入重构后的模块
from .super_reasoning import (
    AthenaSuperReasoning,
    AthenaSuperReasoningEngine,
    ReasoningConfig,
    ReasoningMode,
    SuperReasoningEngine,
)

# 发出弃用警告
warnings.warn(
    "super_reasoning.py 已重构为模块化目录 "
    "core.cognition.super_reasoning/。"
    "导入接口保持不变，代码现在从模块化目录加载。"
    "详细信息请参考 MIGRATION_GUIDE.md",
    DeprecationWarning,
    stacklevel=2,
)

# 导出公共接口以保持向后兼容
__all__ = [
    "AthenaSuperReasoning",
    "AthenaSuperReasoningEngine",
    "ReasoningConfig",
    "ReasoningMode",
    "SuperReasoningEngine",
]

