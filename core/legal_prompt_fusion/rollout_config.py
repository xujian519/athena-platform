#!/usr/bin/env python3

"""
法律提示词融合灰度配置 Schema 与热重载实现。

提供 FusionRolloutConfig 数据类与 RolloutConfigLoader 加载器，
支持基于 domain / task_type / traffic_percentage / user_id_hash 的分层灰度判断，
以及通过轮询 mtime 实现的热重载。
"""

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore[import-untyped]

    HAS_YAML = True
except ImportError:  # pragma: no cover - 依赖缺失时降级
    HAS_YAML = False

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.getenv(
    "LEGAL_FUSION_ROLLOUT_CONFIG",
    "config/prompt_fusion_rollout.yaml",
)
DEFAULT_POLL_INTERVAL_SECONDS = float(
    os.getenv("LEGAL_FUSION_ROLLOUT_POLL_INTERVAL", "10")
)

_ENV_LEGACY_KEY = "LEGAL_PROMPT_FUSION_ENABLED"


@dataclass
class FusionRolloutConfig:
    """灰度配置数据类。

    判断优先级（从高到低）：
    1. global_enabled – 总开关关闭时直接返回 False
    2. domain_whitelist – 不在白名单的 domain 直接返回 False
    3. task_type_whitelist – 不在白名单的 task_type 直接返回 False
    4. traffic_percentage – hash 取模决定是否命中
    5. user_id_hash_prefix – 若配置，则仅 hash 前缀匹配的 user_id 命中
    """

    global_enabled: bool = False
    domain_whitelist: list[str] = field(default_factory=list)
    task_type_whitelist: list[str] = field(default_factory=list)
    traffic_percentage: int = 0
    user_id_hash_prefix: str = ""

    # 内部状态（用于支持热重载的单例实例）
    _config_path: str = field(default=DEFAULT_CONFIG_PATH, repr=False)
    _last_mtime: float = field(default=0.0, repr=False)
    _last_check: float = field(default=0.0, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def should_enable(
        self,
        domain: str,
        task_type: str,
        user_id: str = "",
    ) -> bool:
        """分层判断是否对当前请求启用融合。

        Args:
            domain: 业务领域，如 "patent"
            task_type: 任务类型，如 "office_action"
            user_id: 用户标识，用于流量分割或前缀灰度

        Returns:
            True 表示当前请求应启用融合，False 表示不启用
        """
        if not self.global_enabled:
            return False

        if self.domain_whitelist and domain not in self.domain_whitelist:
            return False

        if self.task_type_whitelist and task_type not in self.task_type_whitelist:
            return False

        if self.traffic_percentage <= 0:
            return False

        hash_input = user_id if user_id else ""
        hash_hex = hashlib.md5(hash_input.encode("utf-8")).hexdigest()
        hash_value = int(hash_hex, 16)
        bucket = hash_value % 100

        if bucket >= self.traffic_percentage:
            return False

        if self.user_id_hash_prefix:
            if not hash_hex.startswith(self.user_id_hash_prefix.lower()):
                return False

        return True

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典。"""
        return {
            "global_enabled": self.global_enabled,
            "domain_whitelist": list(self.domain_whitelist),
            "task_type_whitelist": list(self.task_type_whitelist),
            "traffic_percentage": self.traffic_percentage,
            "user_id_hash_prefix": self.user_id_hash_prefix,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FusionRolloutConfig:
        """从字典反序列化，未知字段将被忽略。"""
        return cls(
            global_enabled=bool(data.get("global_enabled", False)),
            domain_whitelist=list(data.get("domain_whitelist", []) or []),
            task_type_whitelist=list(data.get("task_type_whitelist", []) or []),
            traffic_percentage=int(data.get("traffic_percentage", 0)),
            user_id_hash_prefix=str(data.get("user_id_hash_prefix", "")),
        )

    @classmethod
    def from_file(cls, path: str | Path = DEFAULT_CONFIG_PATH) -> FusionRolloutConfig:
        """从 YAML/JSON 文件加载配置，支持向后兼容环境变量。

        向后兼容: LEGAL_PROMPT_FUSION_ENABLED=true 等价于 global_enabled=true,
        traffic_percentage=100。配置文件显式设置时优先级高于环境变量。
        """
        config_path = Path(path)
        legacy_enabled = os.getenv(_ENV_LEGACY_KEY, "").lower() == "true"

        if not config_path.exists():
            if legacy_enabled:
                logger.info(
                    "灰度配置文件不存在，使用 %s 向后兼容模式 "
                    "(global_enabled=true, traffic_percentage=100)",
                    _ENV_LEGACY_KEY,
                )
                return cls(global_enabled=True, traffic_percentage=100, _config_path=str(config_path))
            logger.warning("灰度配置文件不存在且未设置 %s，融合功能关闭", _ENV_LEGACY_KEY)
            return cls(_config_path=str(config_path))

        raw = config_path.read_text(encoding="utf-8")
        return cls._from_raw(raw, str(config_path), legacy_enabled)

    @classmethod
    def _from_raw(cls, raw: str, config_path: str, legacy_enabled: bool) -> FusionRolloutConfig:
        if HAS_YAML:
            try:
                data: Any = yaml.safe_load(raw)
            except yaml.YAMLError as exc:
                logger.error("灰度配置文件 YAML 解析失败: %s", exc)
                data = None
        else:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                logger.error("灰度配置文件 JSON 解析失败: %s", exc)
                data = None

        if not isinstance(data, dict):
            logger.error("灰度配置文件根节点不是字典")
            if legacy_enabled:
                return cls(global_enabled=True, traffic_percentage=100, _config_path=config_path)
            return cls(_config_path=config_path)

        # 配置文件优先级高于环境变量：若配置文件中显式设置了 global_enabled，则使用配置文件的值
        global_enabled = data.get("global_enabled")
        if global_enabled is None:
            global_enabled = legacy_enabled
        else:
            global_enabled = bool(global_enabled)

        traffic_percentage = data.get("traffic_percentage")
        if traffic_percentage is None and legacy_enabled:
            traffic_percentage = 100
        else:
            traffic_percentage = int(traffic_percentage or 0)

        instance = cls(
            global_enabled=global_enabled,
            domain_whitelist=list(data.get("domain_whitelist") or []),
            task_type_whitelist=list(data.get("task_type_whitelist") or []),
            traffic_percentage=max(0, min(100, traffic_percentage)),
            user_id_hash_prefix=str(data.get("user_id_hash_prefix") or ""),
            _config_path=config_path,
            _last_mtime=Path(config_path).stat().st_mtime,
        )
        logger.info(
            "灰度配置加载完成: global_enabled=%s, traffic_percentage=%d, "
            "domain_whitelist=%s, task_type_whitelist=%s",
            instance.global_enabled,
            instance.traffic_percentage,
            instance.domain_whitelist,
            instance.task_type_whitelist,
        )
        return instance

    def maybe_reload(self) -> bool:
        """轮询检查配置文件是否需要重载。线程安全。"""
        now = time.monotonic()
        with self._lock:
            if now - self._last_check < DEFAULT_POLL_INTERVAL_SECONDS:
                return False
            self._last_check = now

        try:
            config_path = Path(self._config_path)
            if not config_path.exists():
                return False
            current_mtime = config_path.stat().st_mtime
            if current_mtime <= self._last_mtime:
                return False
        except OSError:
            return False

        logger.info("检测到灰度配置文件变更，触发重载: %s", self._config_path)
        try:
            raw = Path(self._config_path).read_text(encoding="utf-8")
            new_config = self._from_raw(raw, self._config_path, legacy_enabled=False)
        except Exception as exc:
            logger.error("灰度配置重载失败，保留当前配置: %s", exc)
            with self._lock:
                self._last_mtime = current_mtime
            return False

        with self._lock:
            self.global_enabled = new_config.global_enabled
            self.domain_whitelist = new_config.domain_whitelist
            self.task_type_whitelist = new_config.task_type_whitelist
            self.traffic_percentage = new_config.traffic_percentage
            self.user_id_hash_prefix = new_config.user_id_hash_prefix
            self._last_mtime = current_mtime

        logger.info(
            "灰度配置已重载: global_enabled=%s, traffic_percentage=%d",
            self.global_enabled,
            self.traffic_percentage,
        )
        return True


class RolloutConfigLoader:
    """支持热重载的灰度配置加载器。

    通过定时轮询配置文件的 mtime 检测变更，解析错误时保留上次有效配置。
    """

    def __init__(
        self,
        config_path: str | Path = DEFAULT_CONFIG_PATH,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    ):
        self._config_path = Path(config_path)
        self._poll_interval_seconds = poll_interval_seconds
        self._config = FusionRolloutConfig()
        self._last_mtime: float = 0.0
        self._lock = threading.RLock()
        self._load_error_count: int = 0

        # 首次加载
        self._load_once()

    @property
    def config(self) -> FusionRolloutConfig:
        """获取当前生效的配置（线程安全读）。"""
        with self._lock:
            return self._config

    def should_enable(
        self,
        domain: str,
        task_type: str,
        user_id: str = "",
    ) -> bool:
        """便捷方法：使用当前配置判断是否应该启用。"""
        return self.config.should_enable(domain, task_type, user_id)

    def check_and_reload(self) -> bool:
        """检查文件 mtime，如有变更则重新加载。

        Returns:
            True 表示配置已变更并成功重载，False 表示无变更或加载失败。
        """
        try:
            current_mtime = self._config_path.stat().st_mtime
        except FileNotFoundError:
            logger.warning("Rollout 配置文件不存在: %s", self._config_path)
            return False
        except OSError as exc:
            logger.error("读取 rollout 配置文件 mtime 失败: %s", exc)
            return False

        with self._lock:
            if current_mtime <= self._last_mtime:
                return False

            raw = self._config_path.read_text(encoding="utf-8")
            new_config = self._parse(raw)
            if new_config is None:
                self._load_error_count += 1
                logger.error(
                    "Rollout 配置解析失败（第 %d 次），保留旧配置: %s",
                    self._load_error_count,
                    self._config_path,
                )
                self._last_mtime = current_mtime  # 避免反复重试同一错误文件
                return False

            self._config = new_config
            self._last_mtime = current_mtime
            self._load_error_count = 0

        new_summary = self._summary(new_config)
        logger.info("Config reloaded: %s", new_summary)
        return True

    def start_background_polling(self) -> None:
        """启动后台线程进行周期性轮询（默认每 10 秒）。"""
        thread = threading.Thread(target=self._polling_loop, daemon=True)
        thread.start()
        logger.info(
            "Rollout 配置热重载轮询已启动: %s (interval=%.1fs)",
            self._config_path,
            self._poll_interval_seconds,
        )

    def _polling_loop(self) -> None:
        while True:
            time.sleep(self._poll_interval_seconds)
            self.check_and_reload()

    def _load_once(self) -> None:
        if not self._config_path.exists():
            logger.warning(
                "Rollout 配置文件不存在，使用默认全关配置: %s", self._config_path
            )
            return
        try:
            raw = self._config_path.read_text(encoding="utf-8")
            config = self._parse(raw)
            if config is not None:
                with self._lock:
                    self._config = config
                    self._last_mtime = self._config_path.stat().st_mtime
                logger.info("Rollout 配置首次加载成功: %s", self._summary(config))
            else:
                logger.error("Rollout 配置首次加载解析失败，使用默认全关配置")
        except OSError as exc:
            logger.error("Rollout 配置首次加载失败: %s", exc)

    def _parse(self, raw: str) -> FusionRolloutConfig | None:
        if not HAS_YAML:
            # 降级为 JSON 解析
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return None
        else:
            try:
                data = yaml.safe_load(raw)
            except yaml.YAMLError:
                return None

        if not isinstance(data, dict):
            return None

        try:
            return FusionRolloutConfig.from_dict(data)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _summary(config: FusionRolloutConfig) -> str:
        return (
            f"global_enabled={config.global_enabled}, "
            f"traffic_percentage={config.traffic_percentage}, "
            f"domains={len(config.domain_whitelist)}, "
            f"task_types={len(config.task_type_whitelist)}"
        )
