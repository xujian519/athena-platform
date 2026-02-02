#!/usr/bin/env python3
"""
文件验证器 - 多模态文件系统安全验证
File Validator - Multimodal File System Security Validation

提供文件上传安全性验证,防止恶意文件上传和攻击

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# 支持的文件魔术数字(文件头标识)
ALLOWED_MAGIC_NUMBERS: dict[bytes, str] = {
    b"\xff\xd8\xff": "image/jpeg",  # JPEG
    b"\x89PNG": "image/png",  # PNG
    b"GIF8": "image/gif",  # GIF
    b"%PDF": "application/pdf",  # PDF
    b"PK\x03\x04": "application/zip",  # PDF (另一种表示)
    b"II*\x00": "image/tiff",  # TIFF (little-endian)
    b"MM\x00*": "image/tiff",  # TIFF (big-endian)
    b"BM": "image/bmp",  # BMP
    b"RIFF": "video/webp",  # WebP (AVI格式)
}

# 危险的文件扩展名黑名单
DANGEROUS_EXTENSIONS: set[str] = {
    ".exe",
    ".bat",
    ".cmd",
    ".com",
    ".scr",
    ".pif",
    ".vbs",
    ".js",
    ".jar",
    ".sh",
    ".ps1",
    ".vb",
    ".wsf",
    ".deb",
    ".rpm",
    ".dmg",
    ".pkg",
    ".app",
}

# 允许的MIME类型白名单
ALLOWED_MIME_TYPES: set[str] = {
    # 图片
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/webp",
    "image/tiff",
    # 文档
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/markdown",
    "text/csv",
    # 音频
    "audio/mpeg",
    "audio/wav",
    "audio/flac",
    "audio/aac",
    "audio/ogg",
    # 视频
    "video/mp4",
    "video/avi",
    "video/quicktime",
    "video/x-matroska",
    "video/webm",
    # 数据
    "application/json",
    "application/xml",
    "text/xml",
    # 压缩
    "application/zip",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
    "application/x-tar",
    "application/gzip",
    "application/x-gzip",
}

# 文件名长度限制
MAX_FILENAME_LENGTH = 255

# 文件扩展名正则(只允许字母、数字、点、下划线、连字符)
SAFE_FILENAME_PATTERN = re.compile(r"^[\w\-\.\u4e00-\u9fff]+$")


def validate_file_upload(
    filename: str,
    content_type: str | None = None,
    content: bytes | None = None,
    max_size: int | None = None,
) -> dict[str, Any]:
    """
    验证上传文件的安全性

    Args:
        filename: 文件名
        content_type: MIME类型
        content: 文件内容(用于魔术数字检查)
        max_size: 最大允许文件大小(字节)

    Returns:
        验证结果字典:
        {
            'valid': bool,           # 是否通过验证
            'reason': str,           # 未通过的原因
            'detected_type': str,   # 检测到的文件类型
            'sanitized_filename': str  # 清理后的文件名
        }
    """
    result = {
        "valid": True,
        "reason": "",
        "detected_type": content_type or "application/octet-stream",
        "sanitized_filename": sanitize_filename(filename),
    }

    # 1. 验证文件名
    if not filename:
        result["valid"] = False
        result["reason"] = "文件名不能为空"
        return result

    # 检查路径遍历攻击
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        result["valid"] = False
        result["reason"] = "文件名包含非法字符或路径遍历序列"
        return result

    # 检查文件名长度
    if len(filename) > MAX_FILENAME_LENGTH:
        result["valid"] = False
        result["reason"] = f"文件名过长,最大允许{MAX_FILENAME_LENGTH}个字符"
        return result

    # 2. 验证文件扩展名
    file_ext = Path(filename).suffix.lower()
    if file_ext in DANGEROUS_EXTENSIONS:
        result["valid"] = False
        result["reason"] = f"不允许的文件类型: {file_ext}"
        return result

    # 3. 验证MIME类型
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        # 某些情况下可能允许不在白名单中的类型(如自定义类型)
        logger.warning(f"MIME类型不在白名单中: {content_type}")

    # 4. 验证文件内容(魔术数字)
    if content and len(content) >= 4:
        detected_type = detect_file_type_by_magic_number(content)
        if detected_type:
            result["detected_type"] = detected_type

            # 检查魔术数字与MIME类型是否匹配
            if content_type and content_type != detected_type:
                # 某些特殊情况下允许不匹配(如zip格式的docx)
                if not _is_valid_mime_mismatch(content_type, detected_type):
                    result["valid"] = False
                    result["reason"] = (
                        f"文件内容与声明类型不匹配: {detected_type} vs {content_type}"
                    )
                    return result

    # 5. 验证文件大小
    if max_size is not None and content is not None and len(content) > max_size:
        size_mb = len(content) / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)
        result["valid"] = False
        result["reason"] = f"文件过大: {size_mb:.2f}MB,最大允许{max_mb:.2f}MB"
        return result

    return result


def sanitize_filename(filename: str) -> str:
    """
    清理文件名,防止路径遍历攻击

    Args:
        filename: 原始文件名

    Returns:
        清理后的安全文件名
    """
    if not filename:
        return "unnamed_file"

    # 移除路径分隔符,只保留文件名部分
    filename = Path(filename).name

    # 如果文件名以点开头(隐藏文件),添加下划线前缀
    if filename.startswith("."):
        filename = "_" + filename

    # 移除或替换不安全字符
    # 保留:字母、数字、中文、下划线、点、连字符
    filename = re.sub(r"[^\w\-\.\u4e00-\u9fff]", "_", filename)

    # 移除连续的点(防止...攻击)
    filename = re.sub(r"\.+", ".", filename)

    # 限制长度
    if len(filename) > MAX_FILENAME_LENGTH:
        name, ext = Path(filename).stem, Path(filename).suffix
        max_name_length = MAX_FILENAME_LENGTH - len(ext)
        filename = name[:max_name_length] + ext

    # 如果处理后为空,使用默认文件名
    if not filename or filename == ".":
        filename = "unnamed_file"

    return filename


def detect_file_type_by_magic_number(content: bytes) -> str | None:
    """
    通过魔术数字检测文件类型

    Args:
        content: 文件内容(至少前4字节)

    Returns:
        检测到的MIME类型,如果无法检测则返回None
    """
    if len(content) < 4:
        return None

    # 检查已知的魔术数字
    for magic_number, mime_type in ALLOWED_MAGIC_NUMBERS.items():
        if content.startswith(magic_number):
            return mime_type

    # 尝试检测文本文件
    try:
        # 如果是ASCII文本
        if all(32 <= b < 127 or b in b"\n\r\t" for b in content[:100]):
            return "text/plain"
    except KeyError as e:
        logger.warning(f"缺少必要的数据字段: {e}")
    except Exception as e:
        logger.error(f"处理数据时发生错误: {e}")

    return None


def _is_valid_mime_mismatch(declared_mime: str, detected_mime: str) -> bool:
    """
    检查MIME类型不匹配是否合理

    某些情况下,声明类型与检测类型不同是合理的:
    - application/zip vs application/vnd.openxmlformats-officedocument.wordprocessingml.document (docx)

    Args:
        declared_mime: 声明的MIME类型
        detected_mime: 检测到的MIME类型

    Returns:
        是否是有效的类型不匹配
    """
    # docx, xlsx, pptx 实际上是zip格式
    zip_based_formats = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    if declared_mime in zip_based_formats and detected_mime == "application/zip":
        return True

    if detected_mime in zip_based_formats and declared_mime == "application/zip":
        return True

    # 允许 application/octet-stream 作为通用类型
    return declared_mime == "application/octet-stream"


def validate_batch_upload(
    files: list[dict[str, Any]], max_total_size: int | None = None, max_file_count: int = 100
) -> dict[str, Any]:
    """
    验证批量上传

    Args:
        files: 文件列表,每个文件包含filename, content_type, content
        max_total_size: 最大总文件大小
        max_file_count: 最大文件数量

    Returns:
        验证结果
    """
    if len(files) > max_file_count:
        return {"valid": False, "reason": f"文件数量超过限制: {len(files)} > {max_file_count}"}

    total_size = 0
    invalid_files = []

    for i, file_info in enumerate(files):
        result = validate_file_upload(
            filename=file_info.get("filename", ""),
            content_type=file_info.get("content_type"),
            content=file_info.get("content"),
        )

        if not result["valid"]:
            invalid_files.append(
                {"index": i, "filename": file_info.get("filename"), "reason": result["reason"]}
            )

        if file_info.get("content"):
            total_size += len(file_info["content"])

    if invalid_files:
        return {"valid": False, "reason": "部分文件验证失败", "invalid_files": invalid_files}

    if max_total_size and total_size > max_total_size:
        total_mb = total_size / (1024 * 1024)
        max_mb = max_total_size / (1024 * 1024)
        return {"valid": False, "reason": f"总文件大小超过限制: {total_mb:.2f}MB > {max_mb:.2f}MB"}

    return {"valid": True, "reason": "", "total_size": total_size, "file_count": len(files)}


# 导出
__all__ = [
    "ALLOWED_MAGIC_NUMBERS",
    "ALLOWED_MIME_TYPES",
    "DANGEROUS_EXTENSIONS",
    "MAX_FILENAME_LENGTH",
    "detect_file_type_by_magic_number",
    "sanitize_filename",
    "validate_batch_upload",
    "validate_file_upload",
]
