#!/usr/bin/env python3

"""
输入类型检测器
Input Type Detector

检测输入数据的类型

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

import logging
import re
from enum import Enum

logger = logging.getLogger(__name__)


class InputType(Enum):
    """输入类型"""
    TEXT = "text"
    MIXED_LANG = "mixed_lang"
    CODE = "code"
    URL = "url"
    EMAIL = "email"
    NUMBER = "number"
    DATE = "date"
    STRUCTURED = "structured"
    NOISE = "noise"


class InputTypeDetector:
    """输入类型检测器"""

    # 特殊模式
    SPECIAL_PATTERNS = {
        'url': re.compile(r'https?://[^\s]+'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'(\+?86)?[-\s]?1[3-9]\d{9}'),
        'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
        'date': re.compile(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?'),
        'time': re.compile(r'\d{1,2}[::]\d{2}([::]\d{2})?'),
        'chinese_id': re.compile(r'\d{17}[\d_xx]'),
        'chinese_postcode': re.compile(r'\d{6}'),
    }

    # 语言检测模式
    LANGUAGE_PATTERNS = {
        'chinese': re.compile(r'[\u4e00-\u9fff]'),
        'english': re.compile(r'[A-Za-z]'),
        'numbers': re.compile(r'[0-9]'),
        'japanese': re.compile(r'[\u3040-\u309f\u30a0-\u30ff]'),
        'korean': re.compile(r'[\uac00-\ud7af]'),
        'arabic': re.compile(r'[\u0600-\u06ff]'),
        'russian': re.compile(r'[\u0400-\u04ff]'),
    }

    # 代码指示器
    CODE_INDICATORS = [
        'def ', 'function', 'var ', 'const', 'let ', 'import ', 'from ',
        'class ', 'if ', 'for ', 'while ', 'return', 'async ', 'await '
    ]

    def __init__(self):
        self.detected_languages = []

    def detect(self, text: str) -> InputType:
        """
        检测输入类型

        Args:
            text: 输入文本

        Returns:
            InputType: 检测到的输入类型
        """
        if not text:
            return InputType.NOISE

        # 检查特殊格式
        input_type = self._check_special_formats(text)
        if input_type != InputType.TEXT:
            return input_type

        # 检查是否为代码
        if self._is_code(text):
            return InputType.CODE

        # 检查是否为纯数字
        if text.replace('.', '').replace('-', '').isdigit():
            return InputType.NUMBER

        # 检查是否为结构化数据(在语言混合检查之前)
        if self._is_structured_data(text):
            return InputType.STRUCTURED

        # 检查语言混合
        self.detected_languages = self._detect_languages(text)
        if len(self.detected_languages) > 1:
            return InputType.MIXED_LANG

        return InputType.TEXT

    def _check_special_formats(self, text: str) -> InputType:
        """检查特殊格式"""
        if self.SPECIAL_PATTERNS['url'].search(text):
            return InputType.URL
        elif self.SPECIAL_PATTERNS['email'].search(text):
            return InputType.EMAIL
        elif self.SPECIAL_PATTERNS['date'].search(text):
            return InputType.DATE
        elif self.SPECIAL_PATTERNS['time'].search(text):
            return InputType.TEXT  # 时间当作文本处理

        return InputType.TEXT

    def _is_code(self, text: str) -> bool:
        """检查是否为代码"""
        # 简单检查:是否包含代码关键字
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in self.CODE_INDICATORS)

    def _is_structured_data(self, text: str) -> bool:
        """检查是否为结构化数据"""
        # 检查是否为JSON
        if ('{' in text and '}' in text) or ('[' in text and ']' in text):
            try:
                import json
                json.loads(text)
                return True
            except Exception as e:
                logger.warning(f'操作失败: {e}')

        return False

    def _detect_languages(self, text: str) -> list:
        """检测文本中的语言"""
        languages = []
        for lang, pattern in self.LANGUAGE_PATTERNS.items():
            if pattern.search(text):
                languages.append(lang)
        return languages

    def get_detected_languages(self) -> list:
        """获取检测到的语言列表"""
        return self.detected_languages

