"""
灰度配置管理 —— Stub 版本

由 A1 负责实现完整生产逻辑。当前实现仅覆盖测试所需的最小接口：
  - global_enabled   总开关
  - domain_whitelist domain 白名单
  - traffic_percentage 流量百分比（0~100）
  - user_hash_prefixes 用户 hash 前缀强制启用列表
  - reload()         配置热重载

待 A1 完善：动态文件监听、持久化、版本回滚、Schema 校验等。
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RolloutConfig:
    """
    灰度配置管理器。

    控制功能模块按 domain、按流量百分比、按用户 hash 前缀的灰度发布。
    """

    config_path: str = ""
    _config: dict[str, Any] = field(default_factory=dict)
    _last_modified: float = 0.0

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or os.getenv("ROLLOUT_CONFIG_PATH", "")
        self._config = self._default_config()
        self._load()

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------
    def _default_config(self) -> dict[str, Any]:
        return {
            "global_enabled": True,
            "domain_whitelist": ["patent", "trademark", "legal"],
            "traffic_percentage": 100,
            "user_hash_prefixes": [],
        }

    def _load(self) -> None:
        if self.config_path and Path(self.config_path).exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            self._last_modified = Path(self.config_path).stat().st_mtime

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------
    def is_enabled(self, domain: str, user_id: str = "") -> bool:
        """
        判断指定 domain 与用户是否启用灰度功能。

        判定优先级：
        1. global_enabled == False → 直接返回 False
        2. domain 不在白名单 → False
        3. user_hash_prefixes 匹配 → True（强制启用）
        4. traffic_percentage 采样 → 按 hash 确定性判定
        """
        if not self._config.get("global_enabled", True):
            return False

        whitelist = self._config.get("domain_whitelist", [])
        if whitelist and domain not in whitelist:
            return False

        # 用户 hash 前缀强制启用
        hash_prefixes = self._config.get("user_hash_prefixes", [])
        if hash_prefixes and user_id:
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()
            if any(user_hash.startswith(prefix) for prefix in hash_prefixes):
                return True

        # 流量百分比采样
        percentage = self._config.get("traffic_percentage", 100)
        if percentage <= 0:
            return False
        if percentage >= 100:
            return True

        if not user_id:
            # 无 user_id 时无法做确定性采样，保守返回 False
            return False

        hash_val = int(
            hashlib.sha256(f"{user_id}:{domain}".encode()).hexdigest(), 16
        )
        return (hash_val % 100) < percentage

    def reload(self) -> None:
        """手动重载配置文件。"""
        self._load()

    def get_config(self) -> dict[str, Any]:
        """获取当前配置副本。"""
        return self._config.copy()
