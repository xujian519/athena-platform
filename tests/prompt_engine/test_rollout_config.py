"""
灰度配置测试

为 A1 的 rollout_config.py 配套，验证全局开关、domain 白名单、
流量百分比、用户 hash 前缀匹配及配置热重载。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from core.config.rollout_config import RolloutConfig


class TestRolloutConfig:
    def test_global_disabled(self):
        """总开关关闭时，全部 domain 均不启用。"""
        config = RolloutConfig()
        config._config["global_enabled"] = False

        assert config.is_enabled("patent") is False
        assert config.is_enabled("trademark") is False
        assert config.is_enabled("legal") is False

    def test_domain_whitelist(self):
        """domain 不在白名单时不启用；在白名单时启用。"""
        config = RolloutConfig()
        config._config["domain_whitelist"] = ["patent"]
        config._config["traffic_percentage"] = 100

        assert config.is_enabled("patent") is True
        assert config.is_enabled("trademark") is False
        assert config.is_enabled("copyright") is False

    def test_traffic_percentage_zero(self):
        """流量 0% 时，无论 user_id 为何均不启用。"""
        config = RolloutConfig()
        config._config["traffic_percentage"] = 0

        assert config.is_enabled("patent", user_id="user1") is False
        assert config.is_enabled("patent", user_id="user2") is False

    def test_traffic_percentage_full(self):
        """流量 100% 时，全部用户均启用。"""
        config = RolloutConfig()
        config._config["traffic_percentage"] = 100

        assert config.is_enabled("patent", user_id="user1") is True
        assert config.is_enabled("trademark", user_id="user2") is True

    def test_traffic_percentage_half(self):
        """流量 50% 时，大约一半用户启用（多次调用统计）。"""
        config = RolloutConfig()
        config._config["traffic_percentage"] = 50
        config._config["domain_whitelist"] = ["patent"]

        enabled_count = sum(
            1
            for i in range(1000)
            if config.is_enabled("patent", user_id=f"user-{i}")
        )

        # 统计误差容忍 ±10%
        assert 400 <= enabled_count <= 600

    def test_user_hash_prefix(self):
        """用户 hash 前缀匹配时强制启用；不匹配时回退到百分比逻辑。"""
        config = RolloutConfig()
        config._config["traffic_percentage"] = 0  # 先关闭普通流量
        config._config["user_hash_prefixes"] = ["abc", "def"]

        # 找到一个 hash 以 abc 开头的 user_id
        user_abc = None
        for i in range(20000):
            uid = f"test-user-{i}"
            if hashlib.sha256(uid.encode()).hexdigest().startswith("abc"):
                user_abc = uid
                break

        assert user_abc is not None, "在 20000 次采样内未找到 hash 前缀为 abc 的用户"
        assert config.is_enabled("patent", user_id=user_abc) is True

        # 不匹配前缀且流量为 0，应不启用
        assert config.is_enabled("patent", user_id="user-no-match-12345") is False

    def test_config_hot_reload(self, tmp_path: Path):
        """配置文件修改后手动 reload() 生效。"""
        config_file = tmp_path / "rollout.json"
        initial = {
            "global_enabled": True,
            "domain_whitelist": ["patent"],
            "traffic_percentage": 100,
            "user_hash_prefixes": [],
        }
        config_file.write_text(json.dumps(initial), encoding="utf-8")

        config = RolloutConfig(config_path=str(config_file))
        assert config.is_enabled("patent") is True
        assert config.is_enabled("trademark") is False

        # 修改配置并写入
        updated = {
            "global_enabled": True,
            "domain_whitelist": ["trademark"],
            "traffic_percentage": 100,
            "user_hash_prefixes": [],
        }
        config_file.write_text(json.dumps(updated), encoding="utf-8")

        # 热重载
        config.reload()

        assert config.is_enabled("patent") is False
        assert config.is_enabled("trademark") is True
