#!/usr/bin/env python3
from __future__ import annotations
"""
输入编码检测器
Input Encoding Detector

检测和解码各种编码格式的输入

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

import base64
import html
import logging
import re
from urllib.parse import url_unquote

logger = logging.getLogger(__name__)


class EncodingDetector:
    """编码检测和解码器"""

    # 编码模式
    ENCODING_PATTERNS = {
        "url_encoded": re.compile(r"%[0-9A-Fa-f]{2}"),
        "html_encoded": re.compile(r"&[A-Za-z]+;|&#\d+;"),
        "base64_encoded": re.compile(r"^[A-Za-z0-9+/]+=*$"),
        "unicode_escape": re.compile(r"\\u[0-9a-fA-F]{4}"),
    }

    def __init__(self):
        self.detected_encodings = []

    def decode(self, text: str) -> str:
        """
        解码输入文本

        Args:
            text: 输入文本

        Returns:
            str: 解码后的文本
        """
        if not text:
            return text

        result = text
        transformations = []

        # URL解码
        if self.ENCODING_PATTERNS["url_encoded"].search(result):
            result = url_unquote(result)
            transformations.append("url_decoded")

        # HTML实体解码
        if self.ENCODING_PATTERNS["html_encoded"].search(result):
            result = html.unescape(result)
            transformations.append("html_decoded")

        # Unicode转义解码
        if self.ENCODING_PATTERNS["unicode_escape"].search(result):
            try:
                result = result.encode("utf-8").decode("unicode_escape")
                transformations.append("unicode_decoded")
            except Exception as e:
                logger.warning(f"Unicode解码失败: {e}")

        # Base64解码(仅当看起来像Base64时)
        if self._looks_like_base64(result):
            decoded = self._try_base64_decode(result)
            if decoded:
                result = decoded
                transformations.append("base64_decoded")

        self.detected_encodings = transformations
        return result

    def _looks_like_base64(self, text: str) -> bool:
        """判断文本是否像Base64编码"""
        if not text:
            return False

        # 检查字符集
        if not self.ENCODING_PATTERNS["base64_encoded"].match(text):
            return False

        # 长度应该是4的倍数
        return len(text) % 4 == 0

    def _try_base64_decode(self, text: str) -> Optional[str]:
        """尝试Base64解码"""
        try:
            decoded = base64.b64decode(text).decode("utf-8")
            # 验证解码结果是有意义的文本
            if self._is_meaningful_text(decoded):
                return decoded
        except Exception as e:
            logger.warning(f"操作失败: {e}")
        return None

    def _is_meaningful_text(self, text: str) -> bool:
        """判断是否为有意义的文本"""
        if len(text) < 5:
            return False

        # 检查字符多样性
        unique_chars = set(text)
        if len(unique_chars) < 3:
            return False

        # 检查可打印字符比例
        printable_ratio = sum(1 for c in text if c.isprintable()) / len(text)
        return printable_ratio >= 0.8

    def get_applied_transformations(self) -> list:
        """获取应用的转换列表"""
        return self.detected_encodings
