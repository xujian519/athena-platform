#!/usr/bin/env python3
"""
功能门控系统测试

测试功能开关的注册、状态切换和使用统计。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import os

from core.tools.feature_gates import (
    FeatureState,
    FeatureGate,
    FeatureGates,
    get_feature_gates,
    feature,
)


class TestFeatureGates:
    """功能门控系统测试"""

    def test_get_global_instance(self):
        """测试获取全局单例"""
        gates1 = get_feature_gates()
        gates2 = get_feature_gates()
        assert gates1 is gates2

    def test_default_flags_registered(self):
        """测试默认功能标志已注册"""
        gates = get_feature_gates()

        # 检查部分默认标志
        assert gates.is_enabled("parallel_tool_execution") == True
        assert gates.is_enabled("tool_cache") == True
        assert gates.is_enabled("rate_limit") == True
        assert gates.is_enabled("performance_monitoring") == True

    def test_feature_disabled_by_default(self):
        """测试默认禁用的功能"""
        gates = get_feature_gates()

        # 这些功能默认禁用
        assert gates.is_enabled("permission_system") == False
        assert gates.is_enabled("hook_system") == False
        assert gates.is_enabled("verbose_logging") == False

    def test_set_state(self):
        """测试设置功能状态"""
        gates = get_feature_gates()

        # 测试启用
        gates.set_state("verbose_logging", FeatureState.ENABLED)
        assert gates.is_enabled("verbose_logging") == True

        # 测试禁用
        gates.set_state("verbose_logging", FeatureState.DISABLED)
        assert gates.is_enabled("verbose_logging") == False

    def test_get_state(self):
        """测试获取功能状态"""
        gates = get_feature_gates()

        state = gates.get_state("parallel_tool_execution")
        assert state in (FeatureState.ENABLED, FeatureState.TESTING)

    def test_usage_recording(self):
        """测试使用记录"""
        gates = get_feature_gates()

        # 多次检查功能（会记录使用）
        for _ in range(5):
            gates.is_enabled("parallel_tool_execution")

        stats = gates.get_statistics()
        assert stats["usage_stats"]["parallel_tool_execution"]["usage_count"] >= 5

    def test_statistics(self):
        """测试统计信息"""
        gates = get_feature_gates()
        stats = gates.get_statistics()

        assert stats["total_features"] > 0
        assert stats["enabled_count"] > 0
        assert stats["disabled_count"] >= 0
        assert stats["testing_count"] >= 0
        assert "enabled_features" in stats
        assert "disabled_features" in stats
        assert "testing_features" in stats
        assert "usage_stats" in stats

    def test_list_features(self):
        """测试列出所有功能"""
        gates = get_feature_gates()
        features = gates.list_features()

        assert len(features) > 0
        assert all(
            "name" in f and "description" in f and "state" in f for f in features
        )

    def test_custom_feature_registration(self):
        """测试自定义功能注册"""
        gates = get_feature_gates()

        custom_gate = FeatureGate(
            name="test_feature",
            description="测试功能",
            default_state=FeatureState.DISABLED,
        )

        gates.register(custom_gate)

        assert gates.is_enabled("test_feature") == False

        # 启用后
        gates.set_state("test_feature", FeatureState.ENABLED)
        assert gates.is_enabled("test_feature") == True

    def test_feature_convenience_function(self):
        """测试便捷函数"""
        # 使用便捷函数检查功能
        assert feature("parallel_tool_execution") == True
        assert feature("permission_system") == False

    def test_environment_variable_override(self):
        """测试环境变量覆盖"""
        # 设置环境变量
        os.environ["ATHENA_FLAG_TEST_ENV_VAR"] = "TRUE"

        # 创建新的功能门控
        gate = FeatureGate(
            name="test_env_var",
            description="环境变量测试",
            default_state=FeatureState.DISABLED,
        )

        # 应该被环境变量启用
        assert gate.is_enabled() == True

        # 清理
        del os.environ["ATHENA_FLAG_TEST_ENV_VAR"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
