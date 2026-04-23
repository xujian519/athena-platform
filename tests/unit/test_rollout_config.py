"""
Rollout 配置与热重载单元测试。
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from core.legal_prompt_fusion.rollout_config import (
    FusionRolloutConfig,
    RolloutConfigLoader,
)


class TestFusionRolloutConfigShouldEnable:
    """分层灰度判断逻辑测试。"""

    def test_global_off_returns_false(self):
        config = FusionRolloutConfig(global_enabled=False)
        assert config.should_enable("patent", "office_action") is False

    def test_domain_mismatch_returns_false(self):
        config = FusionRolloutConfig(
            global_enabled=True,
            domain_whitelist=["patent"],
            traffic_percentage=100,
        )
        assert config.should_enable("trademark", "office_action") is False

    def test_task_mismatch_returns_false(self):
        config = FusionRolloutConfig(
            global_enabled=True,
            domain_whitelist=["patent"],
            task_type_whitelist=["office_action"],
            traffic_percentage=100,
        )
        assert config.should_enable("patent", "novelty_analysis") is False

    def test_traffic_zero_returns_false(self):
        config = FusionRolloutConfig(
            global_enabled=True,
            traffic_percentage=0,
        )
        assert config.should_enable("patent", "office_action") is False

    def test_traffic_100_returns_true(self):
        config = FusionRolloutConfig(
            global_enabled=True,
            traffic_percentage=100,
        )
        assert config.should_enable("patent", "office_action") is True

    def test_traffic_50_distribution(self):
        """traffic_percentage=50 时，约一半 user_id 命中。"""
        config = FusionRolloutConfig(
            global_enabled=True,
            traffic_percentage=50,
        )
        hits = sum(
            1
            for i in range(1000)
            if config.should_enable("patent", "office_action", user_id=f"user_{i}")
        )
        # 1000 次采样中，命中次数应在 400-600 之间（99.9% 置信度）
        assert 400 < hits < 600

    def test_user_id_hash_prefix_match(self):
        """配置 user_id_hash_prefix 后仅匹配前缀的 user_id 命中。"""
        config = FusionRolloutConfig(
            global_enabled=True,
            traffic_percentage=100,
            user_id_hash_prefix="a",
        )
        # 找一个 md5 hash 以 "a" 开头的 user_id
        match_user = None
        no_match_user = None
        for i in range(10000):
            uid = f"user_{i}"
            import hashlib

            if hashlib.md5(uid.encode()).hexdigest().startswith("a"):
                if match_user is None:
                    match_user = uid
            else:
                if no_match_user is None:
                    no_match_user = uid
            if match_user and no_match_user:
                break

        assert match_user is not None
        assert no_match_user is not None
        assert config.should_enable("patent", "office_action", user_id=match_user) is True
        assert config.should_enable("patent", "office_action", user_id=no_match_user) is False

    def test_empty_whitelist_means_no_restriction(self):
        """domain_whitelist 和 task_type_whitelist 为空时不做限制。"""
        config = FusionRolloutConfig(
            global_enabled=True,
            domain_whitelist=[],
            task_type_whitelist=[],
            traffic_percentage=100,
        )
        assert config.should_enable("any_domain", "any_task") is True


class TestFusionRolloutConfigSerialization:
    """序列化与反序列化测试。"""

    def test_to_dict_roundtrip(self):
        config = FusionRolloutConfig(
            global_enabled=True,
            domain_whitelist=["patent"],
            task_type_whitelist=["office_action"],
            traffic_percentage=25,
            user_id_hash_prefix="ab",
        )
        d = config.to_dict()
        assert d["global_enabled"] is True
        assert d["domain_whitelist"] == ["patent"]
        assert d["traffic_percentage"] == 25
        assert d["user_id_hash_prefix"] == "ab"

    def test_from_dict_ignores_unknown_fields(self):
        data = {
            "global_enabled": True,
            "extra_field": "should_be_ignored",
            "traffic_percentage": "10",
        }
        config = FusionRolloutConfig.from_dict(data)
        assert config.global_enabled is True
        assert config.traffic_percentage == 10


class TestRolloutConfigLoaderHotReload:
    """热重载与错误恢复测试。"""

    def test_loads_default_when_file_missing(self, tmp_path: Path):
        missing_path = tmp_path / "nonexistent.yaml"
        loader = RolloutConfigLoader(config_path=missing_path)
        assert loader.config.global_enabled is False
        assert loader.config.traffic_percentage == 0

    def test_reload_on_mtime_change(self, tmp_path: Path):
        config_path = tmp_path / "rollout.yaml"
        config_path.write_text("global_enabled: true\ntraffic_percentage: 10\n")

        loader = RolloutConfigLoader(
            config_path=config_path,
            poll_interval_seconds=0.1,
        )
        assert loader.config.global_enabled is True
        assert loader.config.traffic_percentage == 10

        # 修改文件
        time.sleep(0.05)
        config_path.write_text("global_enabled: false\ntraffic_percentage: 5\n")
        reloaded = loader.check_and_reload()
        assert reloaded is True
        assert loader.config.global_enabled is False
        assert loader.config.traffic_percentage == 5

    def test_reload_keeps_old_config_on_parse_error(self, tmp_path: Path):
        config_path = tmp_path / "rollout.yaml"
        config_path.write_text("global_enabled: true\ntraffic_percentage: 10\n")

        loader = RolloutConfigLoader(
            config_path=config_path,
            poll_interval_seconds=0.1,
        )
        assert loader.config.global_enabled is True

        # 写入无效内容
        time.sleep(0.05)
        config_path.write_text("this is not: valid: yaml: {\n")
        reloaded = loader.check_and_reload()
        assert reloaded is False
        # 旧配置保留
        assert loader.config.global_enabled is True
        assert loader.config.traffic_percentage == 10

    def test_reload_idempotent_when_no_change(self, tmp_path: Path):
        config_path = tmp_path / "rollout.yaml"
        config_path.write_text("global_enabled: true\ntraffic_percentage: 10\n")

        loader = RolloutConfigLoader(
            config_path=config_path,
            poll_interval_seconds=0.1,
        )
        assert loader.check_and_reload() is False

    def test_should_enable_delegate(self, tmp_path: Path):
        config_path = tmp_path / "rollout.yaml"
        config_path.write_text(
            "global_enabled: true\ndomain_whitelist:\n  - patent\ntraffic_percentage: 100\n"
        )
        loader = RolloutConfigLoader(config_path=config_path)
        assert loader.should_enable("patent", "office_action") is True
        assert loader.should_enable("trademark", "office_action") is False
