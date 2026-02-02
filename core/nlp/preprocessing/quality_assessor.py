#!/usr/bin/env python3
"""
文本质量评估器
Text Quality Assessor

评估输入文本的质量

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

import logging
import re
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class InputQualityLevel(Enum):
    """输入质量等级"""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


class QualityAssessor:
    """质量评估器"""

    def __init__(self):
        self.quality_score = 0.0
        self.detected_issues = []
        self.metadata = {}

    def assess(self, text: str) -> dict[str, Any]:
        """
        评估文本质量

        Args:
            text: 输入文本

        Returns:
            Dict: 评估结果
        """
        self.quality_score = 1.0
        self.detected_issues = []
        self.metadata = {}

        if not text:
            return self._create_result(InputQualityLevel.INVALID)

        # 长度检查
        self._check_length(text)

        # 字符多样性检查
        self._check_character_diversity(text)

        # 语言混合检查
        self._check_language_mix(text)

        # 可读性检查
        self._check_readability(text)

        # 特殊字符检查
        self._check_special_chars(text)

        # 确定质量等级
        level = self._determine_quality_level()

        return self._create_result(level)

    def _check_length(self, text: str) -> Any:
        """检查长度"""
        if len(text) < 3:
            self.detected_issues.append("文本过短")
            self.quality_score -= 0.3
        elif len(text) > 10000:
            self.detected_issues.append("文本过长")
            self.quality_score -= 0.2

        self.metadata["length"] = len(text)

    def _check_character_diversity(self, text: str) -> Any:
        """检查字符多样性"""
        unique_chars = set(text)
        diversity_ratio = len(unique_chars) / len(text) if text else 0

        self.metadata["unique_chars"] = len(unique_chars)
        self.metadata["diversity_ratio"] = diversity_ratio

        if len(unique_chars) < 3:
            self.detected_issues.append("字符多样性不足")
            self.quality_score -= 0.4
        elif diversity_ratio < 0.1:
            self.detected_issues.append("字符多样性较低")
            self.quality_score -= 0.1

    def _check_language_mix(self, text: str) -> Any:
        """检查语言混合"""
        # 简化的语言检测
        patterns = {
            "chinese": re.compile(r"[\u4e00-\u9fff]"),
            "english": re.compile(r"[A-Za-z]"),
            "numbers": re.compile(r"[0-9]"),
        }

        detected = []
        for lang, pattern in patterns.items():
            if pattern.search(text):
                detected.append(lang)

        self.metadata["detected_languages"] = detected

        if len(detected) > 3:
            self.detected_issues.append("语言混合过多")
            self.quality_score -= 0.2

    def _check_readability(self, text: str) -> Any:
        """检查可读性"""
        readable_chars = sum(
            1 for c in text if c.isalnum() or c.isspace() or c in ".,!?;:()[]{}\"'-"
        )
        readability = readable_chars / len(text) if text else 0

        self.metadata["readability_ratio"] = readability

        if readability < 0.5:
            self.detected_issues.append("可读性较差")
            self.quality_score -= 0.3

    def _check_special_chars(self, text: str) -> Any:
        """检查特殊字符比例"""
        special_count = sum(1 for c in text if not c.isalnum() and not c.isspace())
        special_ratio = special_count / len(text) if text else 0

        self.metadata["special_char_ratio"] = special_ratio

        if special_ratio > 0.3:
            self.detected_issues.append("特殊字符过多")
            self.quality_score -= 0.2

    def _determine_quality_level(self) -> InputQualityLevel:
        """确定质量等级"""
        if self.quality_score >= 0.9:
            return InputQualityLevel.EXCELLENT
        elif self.quality_score >= 0.7:
            return InputQualityLevel.GOOD
        elif self.quality_score >= 0.5:
            return InputQualityLevel.FAIR
        elif self.quality_score >= 0.3:
            return InputQualityLevel.POOR
        else:
            return InputQualityLevel.INVALID

    def _create_result(self, level: InputQualityLevel) -> dict[str, Any]:
        """创建评估结果"""
        return {
            "quality_level": level,
            "quality_score": max(0.0, self.quality_score),
            "issues": self.detected_issues.copy(),
            "metadata": self.metadata.copy(),
        }
