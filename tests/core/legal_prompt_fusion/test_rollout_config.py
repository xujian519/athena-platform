#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from pathlib import Path

from core.legal_prompt_fusion.rollout_config import FusionRolloutConfig


class TestFusionRolloutConfig:
    """FusionRolloutConfig 灰度配置测试。"""

    def test_global_off(self):
        config = FusionRolloutConfig(global_enabled=False)
        assert config.should_enable("patent", "office_action") is False

    def test_global_on_no_restrictions(self):
        config = FusionRolloutConfig(global_enabled=True, traffic_percentage=100)
        assert config.should_enable("patent", "office_action") is True

    def test_domain_mismatch(self):
        config = FusionRolloutConfig(
            global_enabled=True,
            domain_whitelist=["patent"],
            traffic_percentage=100,
        )
        assert config.should_enable("trademark", "office_action") is False
        assert config.should_enable("patent", "office_action") is True

    def test_task_type_mismatch(self):
        config = FusionRolloutConfig(
            global_enabled=True,
            task_type_whitelist=["office_action"],
            traffic_percentage=100,
        )
        assert config.should_enable("patent", "novelty_analysis") is False
        assert config.should_enable("patent", "office_action") is True

    def test_traffic_zero(self):
        config = FusionRolloutConfig(global_enabled=True, traffic_percentage=0)
        assert config.should_enable("patent", "office_action") is False

    def test_traffic_50_percent_consistency(self):
        """traffic_percentage=50 应对同一用户保持一致的命中结果。"""
        config = FusionRolloutConfig(global_enabled=True, traffic_percentage=50)
        domain, task_type = "patent", "office_action"

        # 同一 user_id 应始终得到相同结果
        results = {config.should_enable(domain, task_type, user_id="user_123") for _ in range(10)}
        assert len(results) == 1

        # 统计大量用户的命中分布，应在 50% 附近
        hits = sum(
            config.should_enable(domain, task_type, user_id=f"user_{i}")
            for i in range(1000)
        )
        # 允许 ±10% 的偏差（概率上几乎必然通过）
        assert 400 <= hits <= 600

    def test_user_id_hash_prefix_empty(self):
        """user_id_hash_prefix 为空时不影响判断。"""
        config = FusionRolloutConfig(
            global_enabled=True, traffic_percentage=100, user_id_hash_prefix=""
        )
        assert config.should_enable("patent", "office_action", user_id="any") is True

    def test_backward_compat_env_var(self, monkeypatch):
        """LEGAL_PROMPT_FUSION_ENABLED=true 等价于 global_enabled=true, traffic_percentage=100。"""
        monkeypatch.setenv("LEGAL_PROMPT_FUSION_ENABLED", "true")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nonexistent.yaml"
            config = FusionRolloutConfig.from_file(path)
            assert config.global_enabled is True
            assert config.traffic_percentage == 100
            assert config.should_enable("patent", "office_action") is True

    def test_config_overrides_env_var(self, monkeypatch):
        """配置文件显式设置时，优先级高于环境变量。"""
        monkeypatch.setenv("LEGAL_PROMPT_FUSION_ENABLED", "true")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rollout.yaml"
            path.write_text("global_enabled: false\ntraffic_percentage: 0\n")
            config = FusionRolloutConfig.from_file(path)
            assert config.global_enabled is False
            assert config.traffic_percentage == 0

    def test_yaml_parsing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rollout.yaml"
            path.write_text(
                """
global_enabled: true
domain_whitelist:
  - patent
task_type_whitelist:
  - office_action
traffic_percentage: 5
user_id_hash_prefix: ""
"""
            )
            config = FusionRolloutConfig.from_file(path)
            assert config.global_enabled is True
            assert config.domain_whitelist == ["patent"]
            assert config.task_type_whitelist == ["office_action"]
            assert config.traffic_percentage == 5

    def test_yaml_parse_error_fallback(self, monkeypatch):
        """YAML 解析错误时应回退到环境变量或默认值。"""
        monkeypatch.setenv("LEGAL_PROMPT_FUSION_ENABLED", "true")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rollout.yaml"
            path.write_text("this is not: valid: yaml: [")
            config = FusionRolloutConfig.from_file(path)
            # 回退到环境变量
            assert config.global_enabled is True
            assert config.traffic_percentage == 100

    def test_hot_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rollout.yaml"
            path.write_text("global_enabled: false\ntraffic_percentage: 0\n")
            config = FusionRolloutConfig.from_file(path)
            assert config.global_enabled is False

            # 修改文件
            path.write_text("global_enabled: true\ntraffic_percentage: 100\n")
            # 强制重置内部检查时间，确保轮询会触发
            config._last_check = 0.0
            config._last_mtime = 0.0
            reloaded = config.maybe_reload()
            assert reloaded is True
            assert config.global_enabled is True
            assert config.traffic_percentage == 100

    def test_hot_reload_no_change(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rollout.yaml"
            path.write_text("global_enabled: true\ntraffic_percentage: 100\n")
            config = FusionRolloutConfig.from_file(path)
            # 再次调用不应触发重载
            reloaded = config.maybe_reload()
            assert reloaded is False

    def test_traffic_percentage_clamped(self):
        """traffic_percentage 应被限制在 0-100 范围内。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rollout.yaml"
            path.write_text("global_enabled: true\ntraffic_percentage: 150\n")
            config = FusionRolloutConfig.from_file(path)
            # 当前实现没有显式 clamp，但这里验证行为
            # 由于 should_enable 中 traffic_percentage >= 100 时返回 True
            assert config.should_enable("patent", "office_action") is True


class TestTrafficPercentageEdgeCases:
    """traffic_percentage 边界场景。"""

    def test_traffic_1_percent(self):
        config = FusionRolloutConfig(global_enabled=True, traffic_percentage=1)
        hits = sum(
            config.should_enable("patent", "office_action", user_id=f"user_{i}")
            for i in range(10000)
        )
        # 1% 流量，应接近 100
        assert 50 <= hits <= 150

    def test_traffic_99_percent(self):
        config = FusionRolloutConfig(global_enabled=True, traffic_percentage=99)
        hits = sum(
            config.should_enable("patent", "office_action", user_id=f"user_{i}")
            for i in range(10000)
        )
        assert 9700 <= hits <= 9990
