#!/usr/bin/env python3
"""
上下文模块
Context Module

提供智能上下文管理、检索和注入功能

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""


from .context_manager import (
    ContextManager,
    get_context_manager,
    shutdown_all_context_managers,
)

__all__ = ["ContextManager", "get_context_manager", "shutdown_all_context_managers"]
