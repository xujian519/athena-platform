#!/usr/bin/env python3
from __future__ import annotations
"""
JSON处理工具模块
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def safe_loads(text: str, default: Any = None, log_error: bool = True) -> Any:
    """安全地加载JSON"""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        if log_error:
            logger.debug(f"JSON解析失败: {e}")
        return default if default is not None else {}


def safe_dumps(obj: Any, indent: int = 2, ensure_ascii: bool = False) -> str:
    """安全地序列化为JSON"""
    try:
        return json.dumps(obj, indent=indent, ensure_ascii=ensure_ascii)
    except (TypeError, ValueError) as e:
        logger.error(f"JSON序列化失败: {e}")
        return "{}"


def load_json_file(file_path: str | Path, default: Any = None) -> Any:
    """从文件加载JSON"""
    try:
        path = Path(file_path)
        if not path.exists():
            return default if default is not None else {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"加载JSON文件失败 {file_path}: {e}")
        return default if default is not None else {}


def save_json_file(file_path: str | Path, data: Any, indent: int = 2) -> bool:
    """保存JSON到文件"""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=indent, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败 {file_path}: {e}")
        return False


__all__ = ["load_json_file", "safe_dumps", "safe_loads", "save_json_file"]
