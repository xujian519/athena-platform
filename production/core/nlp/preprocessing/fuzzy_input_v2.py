#!/usr/bin/env python3
from __future__ import annotations
"""
小诺模糊输入预处理器(重构版)
Xiaonuo Fuzzy Input Preprocessor (Refactored)

处理各种模糊、不规范、噪声输入,提升系统鲁棒性

重构说明:
- 拆分为多个职责单一的类
- 使用组合模式协调各个组件
- 提高代码可测试性和可维护性

作者: 小诺AI团队
日期: 2026-01-16
版本: 2.0.0 (重构版)
"""

import hashlib
import logging
import threading
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# 集成安全检查
from ...security.input_validator import SecurityLevel, get_input_validator

# 导入拆分后的组件
from .encoding_detector import EncodingDetector
from .input_type_detector import InputType, InputTypeDetector
from .quality_assessor import InputQualityLevel, QualityAssessor
from .text_cleaner import TextCleaner

logger = logging.getLogger(__name__)


@dataclass
class InputAnalysisResult:
    """输入分析结果"""

    original_text: str
    cleaned_text: str
    standardized_text: str
    input_type: InputType
    quality_level: InputQualityLevel
    quality_score: float
    issues: list[str]
    transformations: list[str]
    metadata: dict[str, Any]
    processing_time_ms: float


class FuzzyInputPreprocessor:
    """
    模糊输入预处理器(重构版)

    使用组合模式整合各个专门的处理组件
    """

    def __init__(self, security_level: str = "high"):
        """初始化预处理器"""
        # 创建各个组件
        self.encoding_detector = EncodingDetector()
        self.text_cleaner = TextCleaner()
        self.input_type_detector = InputTypeDetector()
        self.quality_assessor = QualityAssessor()
        self.security_validator = get_input_validator(SecurityLevel(security_level))

        # 统计信息
        self.processing_stats = {
            "total_processed": 0,
            "quality_distribution": Counter(),
            "type_distribution": Counter(),
            "common_issues": Counter(),
            "avg_processing_time": 0.0,
        }

        # 缓存
        self.processing_cache: dict[str, InputAnalysisResult] = {}
        self.cache_lock = threading.Lock()
        self.max_cache_size = 1000

        logger.info("🚀 模糊输入预处理器初始化完成(重构版 v2.0)")

    def preprocess(self, input_text: str) -> InputAnalysisResult:
        """
        预处理输入文本(主流程)

        Args:
            input_text: 输入文本

        Returns:
            InputAnalysisResult: 分析结果
        """
        start_time = datetime.now()

        try:
            # 检查缓存
            cache_key = self._get_cache_key(input_text)
            if cache_key in self.processing_cache:
                logger.debug(f"📋 使用缓存结果: {cache_key[:16]}...")
                cached_result = self.processing_cache[cache_key]
                cached_result.processing_time_ms = (
                    datetime.now() - start_time
                ).total_seconds() * 1000
                return cached_result

            # 初始分析
            original_text = input_text.strip()

            # 第一步:安全检查
            is_safe, security_issues = self.security_validator.validate(
                original_text, "fuzzy_input_preprocessor"
            )
            if not is_safe:
                logger.warning(f"🚨 安全检查失败: {security_issues}")
                return self._create_error_result(original_text, security_issues)

            # 第二步:解码处理
            decoded_text = self.encoding_detector.decode(original_text)

            # 第三步:基础清理
            cleaned_text = self.text_cleaner.clean(decoded_text)

            # 第四步:质量评估
            quality_result = self.quality_assessor.assess(cleaned_text)

            # 第五步:类型识别
            input_type = self.input_type_detector.detect(cleaned_text)

            # 收集所有转换信息
            all_transformations = []
            all_transformations.extend(self.encoding_detector.get_applied_transformations())
            all_transformations.extend(self.text_cleaner.get_applied_transformations())

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # 构建结果
            result = InputAnalysisResult(
                original_text=original_text,
                cleaned_text=cleaned_text,
                standardized_text=cleaned_text,  # 清理后即标准化
                input_type=input_type,
                quality_level=quality_result["quality_level"],
                quality_score=quality_result["quality_score"],
                issues=quality_result["issues"],
                transformations=all_transformations,
                metadata={
                    "detected_languages": self.input_type_detector.get_detected_languages(),
                    "detected_encodings": self.encoding_detector.get_applied_transformations(),
                    **quality_result["metadata"],
                },
                processing_time_ms=processing_time,
            )

            # 更新统计
            self._update_stats(result)

            # 缓存结果
            self._cache_result(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"❌ 预处理失败: {e}")
            # 返回基础结果
            return self._create_error_result(input_text, [str(e)])

    def _create_error_result(self, input_text: str, errors: list[str]) -> InputAnalysisResult:
        """创建错误结果"""
        return InputAnalysisResult(
            original_text=input_text,
            cleaned_text=input_text,
            standardized_text=input_text,
            input_type=InputType.NOISE,
            quality_level=InputQualityLevel.INVALID,
            quality_score=0.0,
            issues=errors,
            transformations=[],
            metadata={},
            processing_time_ms=0.0,
        )

    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode("utf-8", usedforsecurity=False), usedforsecurity=False).hexdigest()[:16]

    def _cache_result(self, cache_key: str, result: InputAnalysisResult) -> Any:
        """缓存结果"""
        with self.cache_lock:
            if len(self.processing_cache) >= self.max_cache_size:
                # 清理旧缓存
                oldest_keys = list(self.processing_cache.keys())[:10]
                for key in oldest_keys:
                    del self.processing_cache[key]
            self.processing_cache[cache_key] = result

    def _update_stats(self, result: InputAnalysisResult) -> Any:
        """更新统计信息"""
        self.processing_stats["total_processed"] += 1

        # 更新质量分布
        self.processing_stats["quality_distribution"][result.quality_level.value] += 1

        # 更新类型分布
        self.processing_stats["type_distribution"][result.input_type.value] += 1

        # 更新常见问题
        for issue in result.issues:
            self.processing_stats["common_issues"][issue] += 1

        # 更新平均处理时间
        current_avg = self.processing_stats["avg_processing_time"]
        count = self.processing_stats["total_processed"]
        self.processing_stats["avg_processing_time"] = (
            current_avg * (count - 1) + result.processing_time_ms
        ) / count

    def batch_preprocess(self, texts: list[str]) -> list[InputAnalysisResult]:
        """批量预处理"""
        return [self.preprocess(text) for text in texts]

    def get_processing_stats(self) -> dict[str, Any]:
        """获取处理统计"""
        return {
            "stats": self.processing_stats.copy(),
            "cache_size": len(self.processing_cache),
            "timestamp": datetime.now().isoformat(),
        }

    def clear_cache(self) -> None:
        """清理缓存"""
        with self.cache_lock:
            self.processing_cache.clear()
        logger.info("🧹 预处理缓存已清理")

    def validate_input(
        self, text: str, min_length: int = 1, max_length: int = 50000
    ) -> tuple[bool, list[str]]:
        """验证输入是否符合要求"""
        # 使用安全检查器
        is_safe, security_issues = self.security_validator.validate(text, "input_validation")

        errors = []
        if not is_safe:
            errors.extend(security_issues)

        # 额外的业务规则验证
        if not text:
            errors.append("输入不能为空")
            return False, errors

        if len(text) < min_length:
            errors.append(f"输入长度不能少于{min_length}个字符")

        if len(text) > max_length:
            errors.append(f"输入长度不能超过{max_length}个字符")

        return len(errors) == 0, errors

    def enhance_text(self, text: str) -> str:
        """增强文本质量"""
        # 自动添加缺失的标点
        if text and text[-1] not in ".!?。!?":
            # 扩展疑问词检测,包括"什么"、"怎么"、"为什么"等
            question_words = ["?", "吗", "呢", "什么", "怎么", "为什么", "哪", "几", "谁", "哪里"]
            if any(word in text for word in question_words):
                text += "?"
            elif "!" in text or "啊" in text or "呀" in text:
                text += "!"
            else:
                text += "。"

        # 修复常见拼写错误(简单版本)
        common_misspellings = {
            "的得": "的地得",
        }

        for wrong, right in common_misspellings.items():
            if wrong in text:
                text = text.replace(wrong, right)

        return text


# 便捷函数
_preprocessor: FuzzyInputPreprocessor | None = None


def get_fuzzy_input_preprocessor(security_level: str = "high") -> FuzzyInputPreprocessor:
    """获取预处理器单例"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = FuzzyInputPreprocessor(security_level)
    return _preprocessor
