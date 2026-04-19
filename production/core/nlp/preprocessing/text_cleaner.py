#!/usr/bin/env python3
"""
文本清理器
Text Cleaner

清理和规范化文本输入

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

from __future__ import annotations
import logging
import re
import unicodedata

logger = logging.getLogger(__name__)


class TextCleaner:
    """文本清理器"""

    # 噪声模式
    NOISE_PATTERNS = {
        "repeated_chars": re.compile(r"(.)\1{3,}"),  # 重复字符
        "repeated_words": re.compile(r"\b(\w+)(\s+\1)+"),  # 重复单词 (修改为匹配2次及以上)
        "excessive_punctuation": re.compile(r"[!?。!]{3,}"),  # 过多标点
        "mixed_whitespace": re.compile(r"\s+"),  # 混合空白
        "control_chars": re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"),  # 控制字符
        "zero_width_chars": re.compile(r"[\u200B-\u200F\ufeff]"),  # 零宽字符
    }

    # 标点符号映射
    PUNCTUATION_MAP = {
        ",": ",",
        "。": ".",
        "!": "!",
        "?": "?",
        ":": ":",
        ";": ";",
        '"': '"',
        """: "'",
        """: "'",
        "(": "(",
        ")": ")",
        "[": "[",
        "]": "]",
    }

    def __init__(self):
        # 生成全角半角转换映射
        self.fullwidth_to_halfwidth = {}
        self.halfwidth_to_fullwidth = {}
        for i in range(33, 127):
            half = chr(i)
            full = chr(i + 65248)
            self.fullwidth_to_halfwidth[full] = half
            self.halfwidth_to_fullwidth[half] = full

        self.applied_transformations = []

    def clean(self, text: str) -> str:
        """
        执行完整的文本清理

        Args:
            text: 输入文本

        Returns:
            str: 清理后的文本
        """
        if not text:
            return text

        self.applied_transformations = []

        # 步骤1: 基础清理
        text = self._basic_cleanup(text)

        # 步骤2: 格式标准化
        text = self._standardize_format(text)

        # 步骤3: 高级清理
        text = self._advanced_cleanup(text)

        return text

    def _basic_cleanup(self, text: str) -> str:
        """基础清理"""
        # 移除控制字符
        text = self.NOISE_PATTERNS["control_chars"].sub("", text)
        self.applied_transformations.append("removed_control_chars")

        # 移除零宽字符
        text = self.NOISE_PATTERNS["zero_width_chars"].sub("", text)
        self.applied_transformations.append("removed_zero_width_chars")

        # 标准化空白字符
        text = self.NOISE_PATTERNS["mixed_whitespace"].sub(" ", text)
        text = text.strip()
        self.applied_transformations.append("normalized_whitespace")

        return text

    def _standardize_format(self, text: str) -> str:
        """格式标准化"""
        # 全角转半角
        fullwidth_found = False
        for full, half in self.fullwidth_to_halfwidth.items():
            if full in text:
                text = text.replace(full, half)
                fullwidth_found = True

        if fullwidth_found:
            self.applied_transformations.append("fullwidth_to_halfwidth")

        # 中文标点转英文标点
        chinese_punct_found = False
        for chinese, english in self.PUNCTUATION_MAP.items():
            if chinese in text:
                text = text.replace(chinese, english)
                chinese_punct_found = True

        if chinese_punct_found:
            self.applied_transformations.append("chinese_punctuation_normalized")

        # Unicode标准化
        normalized_text = unicodedata.normalize("NFKC", text)
        if normalized_text != text:
            text = normalized_text
            self.applied_transformations.append("unicode_normalized")

        return text

    def _advanced_cleanup(self, text: str) -> str:
        """高级清理"""

        # 处理重复字符
        def replace_repeated_chars(match) -> None:
            char = match.group(1)
            return char * 2  # 保留最多2个

        if self.NOISE_PATTERNS["repeated_chars"].search(text):
            text = self.NOISE_PATTERNS["repeated_chars"].sub(replace_repeated_chars, text)
            self.applied_transformations.append("reduced_repeated_chars")

        # 处理重复单词
        if self.NOISE_PATTERNS["repeated_words"].search(text):
            text = self.NOISE_PATTERNS["repeated_words"].sub(r"\1", text)
            self.applied_transformations.append("removed_repeated_words")

        # 处理过多标点
        if self.NOISE_PATTERNS["excessive_punctuation"].search(text):
            text = self.NOISE_PATTERNS["excessive_punctuation"].sub("!!!", text)
            self.applied_transformations.append("reduced_excessive_punctuation")

        return text

    def get_applied_transformations(self) -> list[str]:
        """获取应用的转换列表"""
        return self.applied_transformations
