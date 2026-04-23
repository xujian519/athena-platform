#!/usr/bin/env python3
from __future__ import annotations
"""
小诺多语言处理器
Xiaonuo Multilingual Processor

处理多语言混合输入,识别方言和语言变体

功能:
1. 语言检测和识别
2. 方言和变体检测
3. 语言混合处理
4. 翻译和转换支持

作者: 小诺AI团队
日期: 2025-12-18
"""

import os
import re
import sys
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class Language(Enum):
    """支持的语言"""

    CHINESE_SIMPLIFIED = "zh-CN"  # 简体中文
    CHINESE_TRADITIONAL = "zh-TW"  # 繁体中文
    CHINESE_CLASSICAL = "zh-CC"  # 古文
    ENGLISH = "en"  # 英语
    JAPANESE = "ja"  # 日语
    KOREAN = "ko"  # 韩语
    ARABIC = "ar"  # 阿拉伯语
    RUSSIAN = "ru"  # 俄语
    SPANISH = "es"  # 西班牙语
    FRENCH = "fr"  # 法语
    GERMAN = "de"  # 德语
    PORTUGUESE = "pt"  # 葡萄牙语
    ITALIAN = "it"  # 意大利语
    THAI = "th"  # 泰语
    VIETNAMESE = "vi"  # 越南语
    HINDI = "hi"  # 印地语
    UNKNOWN = "unknown"  # 未知语言


class ChineseDialect(Enum):
    """中文方言"""

    MANDARIN = "mandarin"  # 普通话
    CANTONESE = "cantonese"  # 粤语
    SHANGHAINESE = "shanghainese"  # 上海话
    SICHUANESE = "sichuanese"  # 四川话
    HAKKA = "hakka"  # 客家话
    MINNAN = "minnan"  # 闽南语
    HUNANESE = "hunanese"  # 湖南话
    JIANGSU = "jiangsu"  # 江苏话
    BEIJING = "beijing"  # 北京话
    NORTHEAST = "northeast"  # 东北话
    TIANJIN = "tianjin"  # 天津话
    SHANDONG = "shandong"  # 山东话
    HENAN = "henan"  # 河南话
    UNKNOWN = "unknown"  # 未知方言


@dataclass
class LanguageDetectionResult:
    """语言检测结果"""

    primary_language: Language
    confidence: float  # 0.0-1.0
    detected_languages: list[tuple[Language, float]]  # (语言, 置信度)
    mixed_regions: list[tuple[int, int, Language]]  # (start, end, language)
    dialects: list[tuple[ChineseDialect, float]]  # (方言, 置信度)
    text_segments: list[tuple[int, int, str, Language]]  # (start, end, text, language)
    is_code_switched: bool  # 是否有代码转换
    metadata: dict[str, Any]
class MultilingualProcessor:
    """多语言处理器"""

    def __init__(self):
        """初始化多语言处理器"""
        # 语言字符范围定义
        self.language_ranges = {
            Language.CHINESE_SIMPLIFIED: {
                "blocks": ["\u4e00-\u9fff", "\u3400-\u4dbf"],  # CJK统一汉字、扩展A
                "special_chars": ',。!?;:""' "()[]",
                "common_words": ["的", "是", "在", "有", "和", "我", "你", "他", "她", "它"],
            },
            Language.CHINESE_TRADITIONAL: {
                "blocks": ["\u4e00-\u9fff", "\u3400-\u4dbf"],
                "special_chars": ',。!?;:""' "()[]",
                "common_words": ["的", "是", "在", "有", "和", "我", "你", "他", "她", "它"],
                "traditional_chars": ["繁體", "繁體中文", "臺灣", "香港", "馬來西亞"],
            },
            Language.ENGLISH: {
                "blocks": ["\u0041-\u005a", "\u0061-\u007a"],  # A-Z, a-z
                "special_chars": ",.!?;:\"'()[]",
                "common_words": ["the", "be", "to", "of", "and", "a", "in", "that", "have", "I"],
            },
            Language.JAPANESE: {
                "blocks": [
                    "\u3040-\u309f",
                    "\u30a0-\u30ff",
                    "\u4e00-\u9fff",
                ],  # 平假名、片假名、汉字
                "special_chars": '。,!?;:""' "()[]",
                "common_words": ["の", "に", "は", "を", "た", "が", "で", "て", "と", "し"],
            },
            Language.KOREAN: {
                "blocks": ["\uac00-\ud7af", "\u1100-\u11ff"],  # 韩文音节、字母
                "special_chars": ",.!?;:\"'()[]",
                "common_words": ["이", "가", "을", "는", "의", "에", "와", "과", "를", "도"],
            },
            Language.ARABIC: {
                "blocks": ["\u0600-\u06ff", "\u0750-\u077f"],  # 阿拉伯文、补充
                "special_chars": "،؟؛:「」",
                "common_words": ["في", "من", "إلى", "على", "هذا", "هذه", "مع", "كان", "تكون", "ال"],
            },
            Language.RUSSIAN: {
                "blocks": ["\u0400-\u04ff"],  # 西里尔文
                "special_chars": ",.!?;:\"'()[]",
                "common_words": ["и", "в", "не", "на", "я", "быть", "это", "он", "с", "что"],
            },
            Language.THAI: {
                "blocks": ["\u0e00-\u0e7f"],  # 泰文
                "special_chars": ",.!?;:[]",
                "common_words": [
                    "ที่",
                    "และ",
                    "ของ",
                    "ใน",
                    "กับ",
                    "เป็น",
                    "จะ",
                    "มี",
                    "ได้",
                    "ให้",
                ],
            },
        }

        # 方言特征词库
        self.dialect_features = {
            ChineseDialect.CANTONESE: {
                "special_words": [
                    "嘅",
                    "喺",
                    "冇",
                    "佢",
                    "我哋",
                    "你哋",
                    "邊個",
                    "點解",
                    "乜嘢",
                    "唔係",
                ],
                "patterns": ["(.+)嘅", "(.+)喺", "唔(.+)"],
                "common_phrases": ["你好", "多谢", "唔該", "對唔住", "再見"],
            },
            ChineseDialect.SHANGHAINESE: {
                "special_words": [
                    "伐",
                    "阿拉",
                    "侬",
                    "伊",
                    "搿个",
                    "啥",
                    "哪能",
                    "晓得",
                    "覅",
                    "扎劲",
                ],
                "patterns": ["(.+)伐", "阿拉(.+)", "侬(.+)"],
                "common_phrases": ["侬好", "谢谢侬", "对伐起", "再会"],
            },
            ChineseDialect.SICHUANESE: {
                "special_words": [
                    "啥子",
                    "啷个",
                    "巴适",
                    "安逸",
                    "搞快点",
                    "要得",
                    "莫得",
                    "晓得",
                    "雄起",
                ],
                "patterns": ["啥子", "啷个", "巴适"],
                "common_phrases": ["你好", "谢谢", "不好意思", "再见"],
            },
            ChineseDialect.NORTHEAST: {
                "special_words": [
                    "嘎哈",
                    "咋地",
                    "贼",
                    "老",
                    "那嘎达",
                    "这嘎达",
                    "整",
                    "忽悠",
                    "掰扯",
                ],
                "patterns": ["(.+)嘎哈", "咋地", "贼(.+)"],
                "common_phrases": ["你好啊", "谢谢", "不好意思", "回见"],
            },
            ChineseDialect.BEIJING: {
                "special_words": ["您", "您甭", "嘛", "呢", "嘿", "劳驾", "嘛", "甭"],
                "patterns": ["您(.+)", "(.+)嘛", "甭(.+)"],
                "common_phrases": ["您好", "劳驾", "谢谢您", "回见"],
            },
        }

        # 语言转换字典(简繁转换等)
        self.language_converters = {
            (
                Language.CHINESE_SIMPLIFIED,
                Language.CHINESE_TRADITIONAL,
            ): self._simplified_to_traditional,
            (
                Language.CHINESE_TRADITIONAL,
                Language.CHINESE_SIMPLIFIED,
            ): self._traditional_to_simplified,
        }

        # 混合语言检测模式
        self.mixed_language_patterns = [
            # 中英混合
            re.compile(r"[\u4e00-\u9fff]+\s+[a-z_a-Z]+"),
            re.compile(r"[a-z_a-Z]+\s+[\u4e00-\u9fff]+"),
            # 日英混合
            re.compile(r"[\u3040-\u309f\u30a0-\u30ff]+\s+[a-z_a-Z]+"),
            re.compile(r"[a-z_a-Z]+\s+[\u3040-\u309f\u30a0-\u30ff]+"),
        ]

        # 统计信息
        self.processing_stats = {
            "total_processed": 0,
            "language_distribution": Counter(),
            "dialect_distribution": Counter(),
            "mixed_language_count": 0,
            "conversion_count": 0,
        }

        # 缓存
        self.language_cache = {}
        self.cache_lock = threading.Lock()

        logger.info("🚀 多语言处理器初始化完成")

    def detect_language(self, text: str) -> LanguageDetectionResult:
        """检测文本语言"""
        if not text:
            return LanguageDetectionResult(
                primary_language=Language.UNKNOWN,
                confidence=0.0,
                detected_languages=[],
                mixed_regions=[],
                dialects=[],
                text_segments=[],
                is_code_switched=False,
                metadata={},
            )

        # 检查缓存
        cache_key = self._get_language_cache_key(text)
        if cache_key in self.language_cache:
            return self.language_cache[cache_key]

        # 分析文本字符组成
        char_analysis = self._analyze_characters(text)

        # 检测各语言置信度
        language_scores = self._calculate_language_scores(text, char_analysis)

        # 确定主要语言
        primary_language, confidence = self._determine_primary_language(language_scores)

        # 检测混合区域
        mixed_regions = self._detect_mixed_regions(text)

        # 检测方言
        dialects = self._detect_dialects(text, primary_language)

        # 分割文本段
        text_segments = self._segment_text_by_language(text, language_scores, mixed_regions)

        # 检测代码转换
        is_code_switched = len(mixed_regions) > 0 or len({lang for _, _, lang in text_segments}) > 1

        # 构建结果
        result = LanguageDetectionResult(
            primary_language=primary_language,
            confidence=confidence,
            detected_languages=language_scores,
            mixed_regions=mixed_regions,
            dialects=dialects,
            text_segments=text_segments,
            is_code_switched=is_code_switched,
            metadata={
                "char_analysis": char_analysis,
                "text_length": len(text),
                "unique_chars": len(set(text)),
                "processing_time": datetime.now().isoformat(),
            },
        )

        # 更新统计
        self._update_stats(result)

        # 缓存结果
        with self.cache_lock:
            if len(self.language_cache) < 1000:
                self.language_cache[cache_key] = result

        return result

    def convert_language(
        self, text: str, target_language: Language, source_language: Language = None
    ) -> str:
        """转换文本语言(如简繁转换)"""
        if source_language is None:
            # 自动检测源语言
            detection_result = self.detect_language(text)
            source_language = detection_result.primary_language

        # 检查是否支持转换
        conversion_key = (source_language, target_language)
        if conversion_key in self.language_converters:
            converted_text = self.language_converters[conversion_key](text)
            self.processing_stats["conversion_count"] += 1
            return converted_text
        else:
            logger.warning(
                f"⚠️ 不支持的语言转换: {source_language.value} -> {target_language.value}"
            )
            return text

    def normalize_mixed_text(self, text: str, target_language: Language = None) -> str:
        """标准化混合文本"""
        detection_result = self.detect_language(text)

        if target_language is None:
            target_language = detection_result.primary_language

        # 简单的标准化策略:保留主要语言,转换其他语言部分
        normalized_text = text

        for start, end, segment_lang in detection_result.text_segments:
            if segment_lang != target_language:
                # 尝试转换这部分文本
                if (segment_lang, target_language) in self.language_converters:
                    segment_text = text[start:end]
                    converted_segment = self.language_converters[segment_lang, target_language](
                        segment_text
                    )
                    normalized_text = (
                        normalized_text[:start] + converted_segment + normalized_text[end:]
                    )

        return normalized_text

    def _analyze_characters(self, text: str) -> dict[str, Any]:
        """分析文本字符组成"""
        char_counts = defaultdict(int)
        language_char_counts = dict.fromkeys(Language, 0)

        for char in text:
            char_code = ord(char)

            # 统计各语言字符
            for language, config in self.language_ranges.items():
                if language == Language.UNKNOWN:
                    continue

                for block in config.get("blocks", []):
                    if self._char_in_range(char_code, block):
                        language_char_counts[language] += 1
                        break

            char_counts[char] += 1

        total_chars = len(text)
        language_ratios = {
            lang: count / total_chars if total_chars > 0 else 0
            for lang, count in language_char_counts.items()
        }

        return {
            "total_chars": total_chars,
            "unique_chars": len(char_counts),
            "language_counts": language_char_counts,
            "language_ratios": language_ratios,
            "char_frequency": dict(char_counts.most_common(10)),
        }

    def _calculate_language_scores(
        self, text: str, char_analysis: dict[str, Any]
    ) -> list[tuple[Language, float]]:
        """计算各语言得分"""
        scores = []

        # 基于字符比例的基础分
        for language in Language:
            if language == Language.UNKNOWN:
                continue

            if language in char_analysis["language_ratios"]:
                base_score = char_analysis["language_ratios"][language]
            else:
                base_score = 0.0

            # 基于常用词的加分
            word_score = self._calculate_word_score(text, language)

            # 基于特殊字符的加分
            special_char_score = self._calculate_special_char_score(text, language)

            # 综合得分
            total_score = base_score * 0.5 + word_score * 0.3 + special_char_score * 0.2

            scores.append((language, total_score))

        # 排序并过滤低分语言
        scores = [(lang, score) for lang, score in scores if score > 0.05]
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores

    def _calculate_word_score(self, text: str, language: Language) -> float:
        """计算基于常用词的得分"""
        if language not in self.language_ranges:
            return 0.0

        common_words = self.language_ranges[language].get("common_words", [])
        if not common_words:
            return 0.0

        word_count = 0
        for word in common_words:
            if word in text:
                word_count += 1

        return min(word_count / len(common_words), 1.0)

    def _calculate_special_char_score(self, text: str, language: Language) -> float:
        """计算基于特殊字符的得分"""
        if language not in self.language_ranges:
            return 0.0

        special_chars = self.language_ranges[language].get("special_chars", "")
        if not special_chars:
            return 0.0

        special_char_count = sum(1 for char in text if char in special_chars)
        total_special_chars = len(special_chars)

        if total_special_chars == 0:
            return 0.0

        return min(special_char_count / total_special_chars, 1.0)

    def _determine_primary_language(
        self, language_scores: list[tuple[Language, float]]
    ) -> tuple[Language, float]:
        """确定主要语言"""
        if not language_scores:
            return Language.UNKNOWN, 0.0

        primary_language, confidence = language_scores[0]

        # 如果置信度过低,标记为未知
        if confidence < 0.3:
            return Language.UNKNOWN, 0.0

        return primary_language, confidence

    def _detect_mixed_regions(self, text: str) -> list[tuple[int, int, Language]]:
        """检测混合语言区域"""
        mixed_regions = []

        # 使用预定义模式检测
        for pattern in self.mixed_language_patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                # 确定这个区域的主要语言
                segment = text[start:end]
                segment_result = self.detect_language(segment)
                if segment_result.primary_language != Language.UNKNOWN:
                    mixed_regions.append((start, end, segment_result.primary_language))

        # 基于字符范围的精确检测
        char_languages = []
        for i, char in enumerate(text):
            char_lang = self._detect_char_language(char)
            char_languages.append(char_lang)

        # 合并连续相同语言区域
        if char_languages:
            current_lang = char_languages[0]
            start = 0

            for i in range(1, len(char_languages)):
                if char_languages[i] != current_lang:
                    if current_lang != Language.UNKNOWN:
                        mixed_regions.append((start, i, current_lang))
                    current_lang = char_languages[i]
                    start = i

            # 添加最后一个区域
            if current_lang != Language.UNKNOWN:
                mixed_regions.append((start, len(char_languages), current_lang))

        # 去重和排序
        mixed_regions = list(set(mixed_regions))
        mixed_regions.sort()

        return mixed_regions

    def _detect_char_language(self, char: str) -> Language:
        """检测单个字符的语言"""
        char_code = ord(char)

        for language, config in self.language_ranges.items():
            if language == Language.UNKNOWN:
                continue

            for block in config.get("blocks", []):
                if self._char_in_range(char_code, block):
                    return language

        return Language.UNKNOWN

    def _detect_dialects(
        self, text: str, primary_language: Language
    ) -> list[tuple[ChineseDialect, float]]:
        """检测方言"""
        dialects = []

        if primary_language not in [Language.CHINESE_SIMPLIFIED, Language.CHINESE_TRADITIONAL]:
            return dialects

        # 计算各方言得分
        for dialect, features in self.dialect_features.items():
            score = self._calculate_dialect_score(text, dialect, features)
            if score > 0.1:
                dialects.append((dialect, score))

        # 排序
        dialects.sort(key=lambda x: x[1], reverse=True)

        return dialects

    def _calculate_dialect_score(
        self, text: str, dialect: ChineseDialect, features: dict[str, Any]
    ) -> float:
        """计算方言得分"""
        score = 0.0

        # 基于特征词
        special_words = features.get("special_words", [])
        word_score = sum(1 for word in special_words if word in text)
        score += (word_score / len(special_words)) * 0.6 if special_words else 0

        # 基于模式匹配
        patterns = features.get("patterns", [])
        pattern_score = sum(1 for pattern in patterns if re.search(pattern, text))
        score += (pattern_score / len(patterns)) * 0.3 if patterns else 0

        # 基于常用短语
        common_phrases = features.get("common_phrases", [])
        phrase_score = sum(1 for phrase in common_phrases if phrase in text)
        score += (phrase_score / len(common_phrases)) * 0.1 if common_phrases else 0

        return min(score, 1.0)

    def _segment_text_by_language(
        self,
        text: str,
        language_scores: list[tuple[Language, float]],
        mixed_regions: list[tuple[int, int, Language]],
    ) -> list[tuple[int, int, str, Language]]:
        """按语言分割文本"""
        if not mixed_regions:
            return [
                (0, len(text), text, language_scores[0][0] if language_scores else Language.UNKNOWN)
            ]

        segments = []
        last_end = 0

        # 按顺序处理混合区域
        for start, end, language in sorted(mixed_regions):
            if start > last_end:
                # 添加间隔段
                segment_text = text[last_end:start]
                segment_lang = self.detect_language(segment_text).primary_language
                segments.append((last_end, start, segment_text, segment_lang))

            # 添加混合区域段
            segment_text = text[start:end]
            segments.append((start, end, segment_text, language))
            last_end = end

        # 添加最后一段
        if last_end < len(text):
            segment_text = text[last_end:]
            segment_lang = self.detect_language(segment_text).primary_language
            segments.append((last_end, len(text), segment_text, segment_lang))

        return segments

    def _char_in_range(self, char_code: int, range_str: str) -> bool:
        """检查字符是否在指定范围内"""
        if "-" not in range_str:
            return char_code == ord(range_str)

        start, end = range_str.split("-")
        return ord(start) <= char_code <= ord(end)

    def _simplified_to_traditional(self, text: str) -> str:
        """简体转繁体"""
        # 简化的简繁转换映射
        conversion_map = {
            "的": "的",
            "是": "是",
            "在": "在",
            "有": "有",
            "和": "和",
            "我": "我",
            "你": "你",
            "他": "他",
            "她": "她",
            "它": "它",
            "个": "個",
            "这": "這",
            "那": "那",
            "里": "裡",
            "们": "們",
            "发": "發",
            "后": "後",
            "会": "會",
            "机": "機",
            "开": "開",
        }

        # 更完整的转换表可以在此处扩展
        converted = []
        for char in text:
            converted.append(conversion_map.get(char, char))

        return "".join(converted)

    def _traditional_to_simplified(self, text: str) -> str:
        """繁体转简体"""
        # 简化的繁简转换映射
        conversion_map = {
            "個": "个",
            "這": "这",
            "裡": "里",
            "們": "们",
            "發": "发",
            "後": "后",
            "會": "会",
            "機": "机",
            "開": "开",
        }

        converted = []
        for char in text:
            converted.append(conversion_map.get(char, char))

        return "".join(converted)

    def _get_language_cache_key(self, text: str) -> str:
        """生成语言检测缓存键"""
        import hashlib

        return hashlib.md5(text.encode("utf-8", usedforsecurity=False), usedforsecurity=False).hexdigest()[:16]

    def _update_stats(self, result: LanguageDetectionResult) -> Any:
        """更新统计信息"""
        self.processing_stats["total_processed"] += 1

        # 语言分布
        self.processing_stats["language_distribution"][result.primary_language.value] += 1

        # 方言分布
        for dialect, _ in result.dialects:
            self.processing_stats["dialect_distribution"][dialect.value] += 1

        # 混合语言计数
        if result.is_code_switched:
            self.processing_stats["mixed_language_count"] += 1

    def get_processing_stats(self) -> dict[str, Any]:
        """获取处理统计"""
        return {
            "stats": self.processing_stats.copy(),
            "cache_size": len(self.language_cache),
            "timestamp": datetime.now().isoformat(),
        }

    def clear_cache(self) -> None:
        """清理缓存"""
        with self.cache_lock:
            self.language_cache.clear()
        logger.info("🧹 多语言处理缓存已清理")


# 使用示例
if __name__ == "__main__":
    print("🧪 测试多语言处理器...")

    processor = MultilingualProcessor()

    # 测试多语言文本
    test_texts = [
        "你好,我想查询机器学习资料",  # 简体中文
        "你好,我想查詢機器學習資料",  # 繁体中文
        "Hello, I want to search for machine learning papers",  # 英语
        "こんにちは、機械学習の論文を検索したいです",  # 日语
        "안녕하세요, 머신러닝 논문을 검색하고 싶습니다",  # 韩语
        "Hello 你好,I want to 学习 machine learning",  # 中英混合
        "雷猴,我想查嘢",  # 粤语
        "阿拉要查资料伐",  # 上海话
        "啥子东西嘛,要得",  # 四川话
        "您呐,劳驾,帮我整一下",  # 北京话
        "贼好,嘎哈呢",  # 东北话
        "مرحبا، أريد البحث عن أوراق التعلم الآلي",  # 阿拉伯语
        "Привет, я хочу найти статьи по машинному обучению",  # 俄语
        "สวัสดี ฉันต้องการค้นหาเอกสารการเรียนรู้ของเครื่อง",  # 泰语
        "",  # 空文本
    ]

    for i, text in enumerate(test_texts):
        print(f"\n📝 测试 {i+1}: {text!r}")

        result = processor.detect_language(text)

        print(f"   主要语言: {result.primary_language.value}")
        print(f"   置信度: {result.confidence:.3f}")

        if result.detected_languages:
            print(
                f"   检测到的语言: {[(lang.value, score) for lang, score in result.detected_languages[:3]]}"
            )

        if result.dialects:
            print(f"   方言: {[(dialect.value, score) for dialect, score in result.dialects]}")

        print(f"   代码转换: {'是' if result.is_code_switched else '否'}")

        if result.text_segments:
            print(f"   文本段: {len(result.text_segments)} 段")
            for j, (_start, _end, seg_text, lang) in enumerate(result.text_segments[:3]):
                print(f"     段{j+1}: {lang.value} ({seg_text[:20]}...)")

        # 测试语言转换
        if result.primary_language in [Language.CHINESE_SIMPLIFIED, Language.CHINESE_TRADITIONAL]:
            if result.primary_language == Language.CHINESE_SIMPLIFIED:
                converted = processor.convert_language(text, Language.CHINESE_TRADITIONAL)
                print(f"   繁体转换: {converted}")
            else:
                converted = processor.convert_language(text, Language.CHINESE_SIMPLIFIED)
                print(f"   简体转换: {converted}")

    # 显示统计
    print("\n📊 处理统计:")
    stats = processor.get_processing_stats()
    print(f"   总处理数: {stats['stats']['total_processed']}")
    print(f"   语言分布: {dict(stats['stats']['language_distribution'])}")
    print(f"   方言分布: {dict(stats['stats']['dialect_distribution'])}")
    print(f"   混合语言: {stats['stats']['mixed_language_count']}")
    print(f"   转换次数: {stats['stats']['conversion_count']}")

    print("\n✅ 多语言处理器测试完成!")
