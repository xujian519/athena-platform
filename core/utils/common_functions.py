#!/usr/bin/env python3
"""
常见工具函数集合 - 减少代码重复
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ==================== 日志相关 ====================


def get_logger(name: str | None = None) -> logging.Logger:
    """获取logger实例"""
    if name is None:
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "__main__") if frame else "__main__"
    return logging.getLogger(name)


def setup_basic_logger(level: int = logging.INFO) -> None:
    """设置基础日志配置(向后兼容)"""
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )


# ==================== 时间相关 ====================


def get_timestamp(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """获取当前时间戳"""
    return datetime.now().strftime(fmt)


def get_timestamp_iso() -> str:
    """获取ISO格式时间戳"""
    return datetime.now().isoformat()


def current_time() -> datetime:
    """获取当前时间"""
    return datetime.now()


def now() -> datetime:
    """获取当前时间(别名)"""
    return datetime.now()


# ==================== 文件路径相关 ====================


def ensure_dir(path: Any) -> Path:
    """确保目录存在"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def mkdir(path: Any) -> Path:
    """创建目录(别名)"""
    return ensure_dir(path)


def file_exists(path: Any) -> bool:
    """检查文件是否存在"""
    try:
        return Path(path).exists()
    except Exception:
        return False


# ==================== JSON相关 ====================


def read_json(file_path: Any, default: Any = None) -> Any:
    """读取JSON文件"""
    try:
        path = Path(file_path)
        if not path.exists():
            return default if default is not None else {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"读取JSON失败 {file_path}: {e}")
        return default if default is not None else {}


def load_json(file_path: Any, default: Any = None) -> Any:
    """加载JSON(别名)"""
    return read_json(file_path, default)


def write_json(file_path: Any, data: Any, indent: int = 2) -> bool:
    """写入JSON文件"""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=indent, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"写入JSON失败 {file_path}: {e}")
        return False


def save_json(file_path: Any, data: Any, indent: int = 2) -> bool:
    """保存JSON(别名)"""
    return write_json(file_path, data, indent)


# ==================== 配置相关 ====================


def load_config(config_path: Any, default: Any = None) -> dict[str, Any]:
    """加载配置文件"""
    return read_json(config_path, default or {})


def save_config(config_path: Any, config: dict[str, Any], indent: int = 2) -> bool:
    """保存配置文件"""
    return write_json(config_path, config, indent)


# ==================== 字符串相关 ====================


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """清理文件名中的非法字符"""
    import re

    # 移除或替换非法字符
    sanitized = re.sub(r'[<>:"/\|?*]', replacement, filename)
    # 移除首尾空格和点
    sanitized = sanitized.strip(". ")
    # 限制长度
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    return sanitized or "unnamed"


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


# ==================== 验证相关 ====================


def is_empty(value: Any) -> bool:
    """检查值是否为空"""
    if value is None:
        return True
    if isinstance(value, (str, list, dict, tuple, set)):
        return len(value) == 0
    return False


def is_not_empty(value: Any) -> bool:
    """检查值是否非空"""
    return not is_empty(value)


__all__ = [
    "current_time",
    # 路径
    "ensure_dir",
    "file_exists",
    # 日志
    "get_logger",
    # 时间
    "get_timestamp",
    "get_timestamp_iso",
    # 验证
    "is_empty",
    "is_not_empty",
    # 配置
    "load_config",
    "load_json",
    "mkdir",
    "now",
    # JSON
    "read_json",
    # 字符串
    "sanitize_filename",
    "save_config",
    "save_json",
    "setup_basic_logger",
    "truncate",
    "write_json",
]
