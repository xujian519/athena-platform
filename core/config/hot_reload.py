#!/usr/bin/env python3
"""
配置热更新系统
Hot Configuration Reload System

版本: 1.0.0
功能:
- 配置文件监听
- 无缝配置更新
- 配置变更通知
- 回滚支持
"""

import hashlib
import json
import logging
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml
from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


@dataclass
class ConfigChange:
    """配置变更记录"""

    timestamp: datetime = field(default_factory=datetime.now)
    file_path: str = ""
    old_hash: str = ""
    new_hash: str = ""
    changes: list[str] = field(default_factory=list)


class ConfigReloadHandler(FileSystemEventHandler):
    """
    配置文件变更处理器

    监听配置文件变化并触发重载
    """

    def __init__(
        self,
        config_path: str,
        reload_callback: Callable[[dict[str, Any], None],
        debounce_seconds: float = 1.0,
    ):
        """
        初始化处理器

        Args:
            config_path: 配置文件路径
            reload_callback: 配置重载回调函数
            debounce_seconds: 防抖延迟(秒)
        """
        self.config_path = os.path.abspath(config_path)
        self.reload_callback = reload_callback
        self.debounce_seconds = debounce_seconds
        self._last_reload_time = 0
        self._last_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """计算配置文件哈希"""
        try:
            with open(self.config_path, "rb") as f:
                return hashlib.md5(f.read(, usedforsecurity=False).hexdigest()
        except Exception as e:
            logger.error(f"❌ 计算配置文件哈希失败: {e}")
            return ""

    def on_modified(self, event: FileModifiedEvent):
        """
        文件修改事件处理

        Args:
            event: 文件事件
        """
        if event.is_directory:
            return

        if os.path.abspath(event.src_path) != self.config_path:
            return

        # 防抖处理
        current_time = datetime.now().timestamp()
        if current_time - self._last_reload_time < self.debounce_seconds:
            return

        # 检查文件是否真的改变了
        new_hash = self._compute_hash()
        if new_hash == self._last_hash:
            return

        logger.info(f"🔄 检测到配置文件变更: {self.config_path}")

        # 加载新配置
        try:
            new_config = self._load_config()
            changes = self._detect_changes(new_config)

            # 调用重载回调
            self.reload_callback(new_config)

            self._last_hash = new_hash
            self._last_reload_time = current_time

            logger.info(f"✅ 配置已重载,变更数: {len(changes)}")

        except Exception as e:
            logger.error(f"❌ 配置重载失败: {e}")

    def _load_config(self) -> dict[str, Any]:
        """加载配置文件"""
        ext = os.path.splitext(self.config_path)[1].lower()

        if ext in [".yml", ".yaml"]:
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        elif ext == ".json":
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)
        else:
            raise ValueError(f"不支持的配置文件类型: {ext}")

    def _detect_changes(self, new_config: dict[str, Any]) -> list[str]:
        """检测配置变更"""
        changes = []
        # 这里可以实现更复杂的变更检测逻辑
        # 目前只记录发生了变更
        changes.append("配置已更新")
        return changes


class ConfigManager:
    """
    配置管理器

    支持热更新和版本管理的配置管理
    """

    def __init__(self, config_path: str, enable_hot_reload: bool = True, backup_count: int = 5):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
            enable_hot_reload: 是否启用热更新
            backup_count: 保留的备份配置数量
        """
        self.config_path = os.path.abspath(config_path)
        self.enable_hot_reload = enable_hot_reload
        self.backup_count = backup_count

        # 当前配置
        self._current_config: dict[str, Any] = {}
        self._config_version = 0
        self._config_history: list[ConfigChange] = []

        # 文件监听
        self._observer: Observer | None = None
        self._lock = threading.RLock()

        # 变更订阅者
        self._subscribers: list[Callable[[dict[str, Any], dict[str, Any], None]] = []

        # 加载初始配置
        self._load_config()

        # 启动文件监听
        if self.enable_hot_reload:
            self._start_watching()

        logger.info(f"✅ 配置管理器初始化完成: {self.config_path}")

    def _load_config(self):
        """加载配置文件"""
        try:
            ext = os.path.splitext(self.config_path)[1].lower()

            if ext in [".yml", ".yaml"]:
                with open(self.config_path, encoding="utf-8") as f:
                    self._current_config = yaml.safe_load(f)
            elif ext == ".json":
                with open(self.config_path, encoding="utf-8") as f:
                    self._current_config = json.load(f)
            else:
                raise ValueError(f"不支持的配置文件类型: {ext}")

            self._config_version += 1
            logger.info(f"✅ 配置已加载 (v{self._config_version})")

        except Exception as e:
            logger.error(f"❌ 加载配置失败: {e}")
            raise

    def _start_watching(self):
        """启动文件监听"""
        try:
            self._observer = Observer()

            # 创建变更处理器
            handler = ConfigReloadHandler(self.config_path, self._on_config_reload)

            # 监听配置文件所在目录
            watch_dir = os.path.dirname(self.config_path)
            self._observer.schedule(handler, watch_dir, recursive=False)
            self._observer.start()

            logger.info(f"👀 开始监听配置文件: {self.config_path}")

        except Exception as e:
            logger.warning(f"⚠️ 启动文件监听失败: {e}")
            self._observer = None

    def _on_config_reload(self, new_config: dict[str, Any]):
        """
        配置重载回调

        Args:
            new_config: 新配置
        """
        with self._lock:
            old_config = self._current_config.copy()
            self._current_config = new_config
            self._config_version += 1

            # 记录变更历史
            change = ConfigChange(
                file_path=self.config_path,
                new_hash=hashlib.md5(json.dumps(new_config, usedforsecurity=False).encode()).hexdigest(),
            )
            self._config_history.append(change)

            # 限制历史记录数量
            if len(self._config_history) > self.backup_count:
                self._config_history.pop(0)

            # 通知订阅者
            self._notify_subscribers(old_config, new_config)

    def _notify_subscribers(self, old_config: dict[dict[str]:
        """通知配置变更订阅者"""
        for callback in self._subscribers:
            try:
                callback(old_config, new_config)
            except Exception as e:
                logger.error(f"❌ 配置变更通知失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键(支持点号分隔的嵌套键)
            default: 默认值

        Returns:
            配置值
        """
        with self._lock:
            keys = key.split(".")
            value = self._current_config

            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return default

            return value if value is not None else default

    def get_all(self) -> dict[str, Any]:
        """获取所有配置"""
        with self._lock:
            return self._current_config.copy()

    def reload(self):
        """手动重载配置"""
        logger.info("🔄 手动重载配置")
        self._load_config()
        self._notify_subscribers({}, self._current_config)

    def subscribe(self, callback: Callable[[dict[str, Any], dict[str, Any], None]):
        """
        订阅配置变更

        Args:
            callback: 回调函数,接收(old_config, new_config)
        """
        self._subscribers.append(callback)
        logger.info(f"✅ 配置变更订阅者已添加: {callback.__name__}")

    def unsubscribe(self, callback: Callable[[dict[str, Any], dict[str, Any], None]):
        """
        取消订阅配置变更

        Args:
            callback: 回调函数
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.info(f"❌ 配置变更订阅者已移除: {callback.__name__}")

    def get_history(self) -> list[ConfigChange]:
        """获取配置变更历史"""
        with self._lock:
            return self._config_history.copy()

    def rollback(self, version: int | None = None):
        """
        回滚到指定版本的配置

        Args:
            version: 配置版本(None表示上一个版本)
        """
        if version is None:
            # 回滚到上一个版本
            if len(self._config_history) < 2:
                logger.warning("⚠️ 没有可回滚的历史版本")
                return
            version = self._config_version - 2

        logger.info(f"🔄 回滚配置到版本: {version}")

        # 这里需要实现实际的回滚逻辑
        # 由于需要保存历史配置的完整内容,暂时只记录日志
        logger.warning("⚠️ 配置回滚功能需要实现历史配置存储")

    def update(self, updates: dict[str, Any], persist: bool = True):
        """
        更新配置值

        Args:
            updates: 要更新的配置字典
            persist: 是否持久化到文件
        """
        with self._lock:
            old_config = self._current_config.copy()

            # 递归更新配置
            def deep_update(target: dict, source: dict):
                for key, value in source.items():
                    if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                        deep_update(target[key], value)
                    else:
                        target[key] = value

            deep_update(self._current_config, updates)
            self._config_version += 1

            # 持久化到文件
            if persist:
                self._persist_config()

            # 通知订阅者
            self._notify_subscribers(old_config, self._current_config)

            logger.info(f"✅ 配置已更新: {list(updates.keys())}")

    def _persist_config(self):
        """持久化配置到文件"""
        try:
            ext = os.path.splitext(self.config_path)[1].lower()

            # 创建备份
            backup_path = f"{self.config_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists(self.config_path):
                import shutil

                shutil.copy2(self.config_path, backup_path)
                logger.debug(f"💾 配置备份已保存: {backup_path}")

            # 写入新配置
            with open(self.config_path, "w", encoding="utf-8") as f:
                if ext in [".yml", ".yaml"]:
                    yaml.dump(self._current_config, f, allow_unicode=True)
                elif ext == ".json":
                    json.dump(self._current_config, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 配置已保存到文件: {self.config_path}")

        except Exception as e:
            logger.error(f"❌ 持久化配置失败: {e}")
            raise

    def stop(self):
        """停止配置管理器(停止文件监听)"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            logger.info("🛑 配置文件监听已停止")


class ConfigValidator:
    """
    配置验证器

    验证配置的有效性和完整性
    """

    def __init__(self, schema: dict[str, Any] | None = None):
        """
        初始化验证器

        Args:
            schema: 配置模式(JSON Schema风格)
        """
        self.schema = schema or {}

    def validate(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        验证配置

        Args:
            config: 配置字典

        Returns:
            (is_valid, errors) 是否有效和错误列表
        """
        errors = []

        # 基础验证
        if not isinstance(config, dict):
            errors.append("配置必须是字典类型")
            return False, errors

        # 模式验证(如果提供了schema)
        if self.schema:
            schema_errors = self._validate_schema(config, self.schema)
            errors.extend(schema_errors)

        return len(errors) == 0, errors

    def _validate_schema(
        self, config: dict[str, Any], schema: dict[str, Any], prefix: str = ""
    ) -> list[str]:
        """根据模式验证配置"""
        errors = []

        for key, definition in schema.items():
            full_key = f"{prefix}.{key}" if prefix else key

            # 检查必需字段
            if definition.get("required", False) and key not in config:
                errors.append(f"缺少必需字段: {full_key}")
                continue

            if key not in config:
                continue

            value = config[key]
            expected_type = definition.get("type")

            # 类型验证
            if expected_type:
                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"{full_key} 应该是字符串类型")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"{full_key} 应该是数字类型")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"{full_key} 应该是布尔类型")
                elif expected_type == "array" and not isinstance(value, list):
                    errors.append(f"{full_key} 应该是数组类型")
                elif expected_type == "object" and not isinstance(value, dict):
                    errors.append(f"{full_key} 应该是对象类型")

            # 范围验证
            if "minimum" in definition and isinstance(value, (int, float)):
                if value < definition["minimum"]:
                    errors.append(f"{full_key} 小于最小值 {definition['minimum']}")

            if "maximum" in definition and isinstance(value, (int, float)):
                if value > definition["maximum"]:
                    errors.append(f"{full_key} 大于最大值 {definition['maximum']}")

            # 枚举验证
            if "enum" in definition and value not in definition["enum"]:
                errors.append(f"{full_key} 值无效,应该是: {definition['enum']}")

            # 嵌套对象验证
            if expected_type == "object" and isinstance(value, dict) and "properties" in definition:
                nested_errors = self._validate_schema(value, definition["properties"], full_key)
                errors.extend(nested_errors)

        return errors


# 便捷函数
def create_config_manager(config_path: str, enable_hot_reload: bool = True) -> ConfigManager:
    """
    创建配置管理器

    Args:
        config_path: 配置文件路径
        enable_hot_reload: 是否启用热更新

    Returns:
        ConfigManager实例
    """
    return ConfigManager(config_path=config_path, enable_hot_reload=enable_hot_reload)


# 全局配置管理器实例(可选)
_global_config_manager: ConfigManager | None = None


def get_global_config_manager(config_path: Optional[str | None = None) -> ConfigManager:
    """
    获取全局配置管理器

    Args:
        config_path: 配置文件路径(仅首次调用时需要)

    Returns:
        ConfigManager实例
    """
    global _global_config_manager

    if _global_config_manager is None:
        if config_path is None:
            raise ValueError("首次调用必须提供config_path参数")

        _global_config_manager = create_config_manager(config_path)

    return _global_config_manager
