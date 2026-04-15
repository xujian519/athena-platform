"""
智能路由引擎配置管理
"""

from __future__ import annotations
import hashlib
import random
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


class RoutingStrategy(Enum):
    """路由策略"""

    SEMANTIC_MATCH = "semantic_match"
    KEYWORD_MATCH = "keyword_match"
    HYBRID = "hybrid"
    CONFIDENCE_BASED = "confidence_based"
    LEARNING_BASED = "learning_based"


@dataclass
class RouterConfig:
    """路由引擎配置"""

    # 特性开关
    enabled: bool = True  # 是否启用新路由引擎
    traffic_percentage: float = 0.0  # 流量百分比(0-100)
    enable_fallback: bool = True  # 是否启用降级

    # 路由策略
    strategy: str = RoutingStrategy.HYBRID.value

    # 性能配置
    cache_enabled: bool = True  # 是否启用缓存
    cache_ttl: int = 3600  # 缓存过期时间(秒)
    max_concurrent_requests: int = 100  # 最大并发请求数

    # 决策阈值
    min_confidence_threshold: float = 0.3  # 最低置信度阈值
    max_results: int = 5  # 最多返回结果数

    # 学习配置
    enable_learning: bool = True  # 是否启用学习
    learning_rate: float = 0.1  # 学习率
    feedback_weight: float = 0.2  # 反馈权重

    # 监控配置
    enable_monitoring: bool = True  # 是否启用监控
    log_decisions: bool = True  # 是否记录决策
    log_level: str = "INFO"  # 日志级别

    # 服务配置
    service_kg_path: str = "data/service_kg.json"
    routing_history_path: str = "data/routing_history.json"
    max_history_size: int = 1000  # 最大历史记录数

    # 超时配置
    request_timeout: int = 30  # 请求超时(秒)
    decision_timeout: int = 5  # 决策超时(秒)

    # 灰度发布配置
    canary_rules: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, config_path: str) -> "RouterConfig":
        """从YAML文件加载配置"""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"配置文件不存在: {config_path},使用默认配置")
            return cls()

        try:
            with open(config_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return cls(**data)
        except (yaml.YAMLError, TypeError, ValueError) as e:
            logger.error(f"配置文件加载失败: {e},使用默认配置")
            return cls()

    def to_yaml(self, config_path: str):
        """保存配置到YAML文件"""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(self.__dict__, f, allow_unicode=True, default_flow_style=False)

    def is_enabled_for_user(self, user_id: str | None = None) -> bool:
        """检查用户是否启用新路由"""
        if not self.enabled:
            return False

        if self.traffic_percentage >= 100:
            return True

        if self.traffic_percentage <= 0:
            return False

        # 灰度规则检查
        if user_id and self.canary_rules:
            # 白名单用户
            whitelist = self.canary_rules.get("whitelist", [])
            if user_id in whitelist:
                return True

            # 黑名单用户
            blacklist = self.canary_rules.get("blacklist", [])
            if user_id in blacklist:
                return False

        # 基于用户ID的哈希分流
        if user_id:
            hash_value = int(hashlib.md5(user_id.encode('utf-8'), usedforsecurity=False).hexdigest(), 16)
            return (hash_value % 100) < self.traffic_percentage

        # 随机分流
        return random.random() * 100 < self.traffic_percentage


# 默认配置
DEFAULT_CONFIG = RouterConfig()

# 开发环境配置
DEV_CONFIG = RouterConfig(
    enabled=True,
    traffic_percentage=100,
    enable_fallback=True,
    strategy=RoutingStrategy.HYBRID.value,
    cache_enabled=True,
    enable_learning=True,
    log_decisions=True,
    log_level="DEBUG",
)

# 生产环境配置(影子模式)
PROD_SHADOW_CONFIG = RouterConfig(
    enabled=True,
    traffic_percentage=0,  # 仅记录,不实际路由
    enable_fallback=True,
    strategy=RoutingStrategy.HYBRID.value,
    cache_enabled=True,
    enable_learning=True,
    log_decisions=True,
    log_level="INFO",
)

# 生产环境配置(灰度模式)
PROD_CANARY_CONFIG = RouterConfig(
    enabled=True,
    traffic_percentage=5,  # 5%流量
    enable_fallback=True,
    strategy=RoutingStrategy.HYBRID.value,
    cache_enabled=True,
    enable_learning=True,
    log_decisions=True,
    log_level="INFO",
    canary_rules={"whitelist": ["test_user_1", "test_user_2"], "blacklist": []},
)

# 生产环境配置(全量模式)
PROD_FULL_CONFIG = RouterConfig(
    enabled=True,
    traffic_percentage=100,
    enable_fallback=False,
    strategy=RoutingStrategy.HYBRID.value,
    cache_enabled=True,
    enable_learning=True,
    log_decisions=True,
    log_level="INFO",
)


def load_config(env: str = "production") -> RouterConfig:
    """加载配置"""
    config_path = Path(f"config/router_{env}.yaml")

    if config_path.exists():
        return RouterConfig.from_yaml(str(config_path))

    # 返回默认配置
    configs = {
        "development": DEV_CONFIG,
        "shadow": PROD_SHADOW_CONFIG,
        "canary": PROD_CANARY_CONFIG,
        "production": PROD_FULL_CONFIG,
    }

    return configs.get(env, PROD_SHADOW_CONFIG)


def save_config(config: RouterConfig, env: str = "production"):
    """保存配置"""
    config_path = Path(f"config/router_{env}.yaml")
    config.to_yaml(str(config_path))


# 全局配置实例
_current_config: RouterConfig | None = None


def get_config(env: str | None = None) -> RouterConfig:
    """获取当前配置"""
    global _current_config

    if _current_config is None:
        env = env or "production"
        _current_config = load_config(env)

    return _current_config


def set_config(config: RouterConfig):
    """设置当前配置"""
    global _current_config
    _current_config = config


# 配置热更新支持
def reload_config(env: str = "production"):
    """重新加载配置"""
    global _current_config
    _current_config = load_config(env)
    return _current_config
