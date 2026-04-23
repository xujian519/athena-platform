#!/usr/bin/env python3
"""
Hook系统集成模块

提供Hook系统与Skills、Plugins等系统的集成。

Author: Athena平台团队
创建时间: 2026-04-20
版本: 2.0.0
"""
from __future__ import annotations

from .skills_hooks import (
    SkillHookIntegration,
    SkillHookType,
    SkillExecutorWithHooks,
    create_skill_hook_integration,
    wrap_skill_with_hooks,
)
from .plugins_hooks import (
    PluginHookIntegration,
    PluginHookType,
    PluginLoaderWithHooks,
    create_plugin_hook_integration,
    wrap_plugin_loader_with_hooks,
)

__all__ = [
    # Skills集成
    "SkillHookType",
    "SkillHookIntegration",
    "SkillExecutorWithHooks",
    "create_skill_hook_integration",
    "wrap_skill_with_hooks",
    # Plugins集成
    "PluginHookType",
    "PluginHookIntegration",
    "PluginLoaderWithHooks",
    "create_plugin_hook_integration",
    "wrap_plugin_loader_with_hooks",
]
