#!/usr/bin/env python3
from __future__ import annotations
"""
路径处理工具模块
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_dir(path: str | Path) -> Path:
    """确保目录存在"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_exists(path: str | Path) -> bool:
    """安全地检查路径是否存在"""
    try:
        return Path(path).exists()
    except Exception:
        return False


def safe_read(file_path: str | Path, encoding: str = "utf-8") -> str | None:
    """安全地读取文件"""
    try:
        return Path(file_path).read_text(encoding=encoding)
    except Exception as e:
        logger.error(f"读取文件失败 {file_path}: {e}")
        return None


def safe_write(file_path: str | Path, content: str, encoding: str = "utf-8") -> bool:
    """安全地写入文件"""
    try:
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding=encoding)
        return True
    except Exception as e:
        logger.error(f"写入文件失败 {file_path}: {e}")
        return False


def get_ext(path: str | Path) -> str:
    """获取文件扩展名"""
    return Path(path).suffix.lower()


def get_stem(path: str | Path) -> str:
    """获取文件名(不含扩展名)"""
    return Path(path).stem


__all__ = ["ensure_dir", "get_ext", "get_stem", "safe_exists", "safe_read", "safe_write"]
