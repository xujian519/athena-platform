#!/usr/bin/env python3
"""
统一LLM管理器简化测试
Tests for core.llm.unified_llm_manager (Simple version)
"""

import pytest


class TestUnifiedLLMManager:
    """测试UnifiedLLMManager类"""

    def test_import_manager(self):
        """测试导入管理器模块"""
        from core.llm.unified_llm_manager import UnifiedLLMManager
        assert UnifiedLLMManager is not None

    def test_manager_initialization(self):
        """测试管理器初始化"""
        from core.llm.unified_llm_manager import UnifiedLLMManager
        manager = UnifiedLLMManager()
        assert manager is not None

    def test_manager_has_methods(self):
        """测试管理器具有必需的方法"""
        from core.llm.unified_llm_manager import UnifiedLLMManager
        manager = UnifiedLLMManager()
        # 验证关键方法存在
        assert hasattr(manager, 'generate')
        assert hasattr(manager, 'generate_stream')
        assert hasattr(manager, 'select_model')


class TestModelSelection:
    """测试模型选择"""

    def test_manager_has_select_model(self):
        """测试管理器有模型选择方法"""
        from core.llm.unified_llm_manager import UnifiedLLMManager
        manager = UnifiedLLMManager()
        assert hasattr(manager, 'select_model')


class TestLLMProviders:
    """测试LLM提供商"""

    def test_manager_exists(self):
        """测试管理器存在"""
        from core.llm.unified_llm_manager import UnifiedLLMManager
        manager = UnifiedLLMManager()
        assert manager is not None
