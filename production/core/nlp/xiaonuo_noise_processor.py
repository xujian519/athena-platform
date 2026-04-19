#!/usr/bin/env python3
from __future__ import annotations
"""
小诺噪声和异常字符处理器
Xiaonuo Noise and Anomaly Character Processor

专门处理各种噪声数据和异常字符,提升文本质量

功能:
1. 智能噪声检测和过滤
2. 异常字符识别和处理
3. 文本平滑和修复
4. 多层次去噪策略

作者: 小诺AI团队
日期: 2025-12-18
"""

import base64
import html
import os
import re
import sys
import threading
import unicodedata
import urllib.parse
from collections import Counter
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

class NoiseType(Enum):
    """噪声类型"""
    CONTROL_CHARS = "control_chars"          # 控制字符
    ZERO_WIDTH = "zero_width"               # 零宽字符
    REPEATED_PATTERNS = "repeated_patterns"  # 重复模式
    MALFORMED_UNICODE = "malformed_unicode"  # 畸形Unicode
    ENCODING_ARTIFACTS = "encoding_artifacts" # 编码伪影
    HTML_ENTITIES = "html_entities"         # HTML实体
    URL_ENCODING = "url_encoding"           # URL编码
    BASE64_NOISE = "base64_noise"           # Base64噪声
    BINARY_DATA = "binary_data"             # 二进制数据
    FORMAT_CHARS = "format_chars"           # 格式字符
    PUNCTUATION_NOISE = "punctuation_noise" # 标点噪声
    WHITESPACE_NOISE = "whitespace_noise"   # 空白噪声
    MIXED_SCRIPT = "mixed_script"           # 混合脚本
    EMOTICON_SPAM = "emoticon_spam"         # 表情垃圾
    SPECIAL_CHAR_NOISE = "special_char_noise" # 特殊字符噪声

@dataclass
class NoiseDetectionResult:
    """噪声检测结果"""
    noise_types: list[NoiseType]
    noise_segments: list[tuple[int, int, str, NoiseType]]  # (start, end, content, type)
    noise_ratio: float  # 噪声比例
    severity: str       # 严重程度: low, medium, high, critical
    cleanable: bool     # 是否可清理
    suggestions: list[str]  # 处理建议

class NoiseProcessor:
    """噪声处理器"""

    def __init__(self):
        """初始化噪声处理器"""
        # 控制字符模式
        self.control_char_patterns = {
            'ascii_control': re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]'),
            'extended_control': re.compile(r'[\x80-\x9F]'),
            'format_control': re.compile(r'[\u200B-\u200F\u202A-\u202E\u2060-\u206F]'),
            'replacement_char': re.compile(r'�'),  # Unicode替换字符
        }

        # 零宽字符模式
        self.zero_width_patterns = {
            'zero_width_space': re.compile(r'[\u200B]'),
            'zero_width_non_joiner': re.compile(r'[\u200C]'),
            'zero_width_joiner': re.compile(r'[\u200D]'),
            'word_joiner': re.compile(r'[\u2060]'),
            'function_application': re.compile(r'[\u2061]'),
            'invisible_times': re.compile(r'[\u2062]'),
            'invisible_separator': re.compile(r'[\u2063]'),
            'invisible_plus': re.compile(r'[\u2064]'),
        }

        # 重复模式
        self.repetition_patterns = {
            'char_repetition': re.compile(r'(.)\1{4,}'),  # 5个以上相同字符
            'word_repetition': re.compile(r'\b(\w+)(\s+\1){3,}'),  # 3个以上相同单词
            'punctuation_repetition': re.compile(r'([!?。,!?;;])\1{3,}'),  # 重复标点
            'space_repetition': re.compile(r' {3,}'),  # 3个以上空格
            'newline_repetition': re.compile(r'\n{3,}'),  # 3个以上换行
        }

        # 编码伪影模式
        self.encoding_artifact_patterns = {
            'utf8_garbled': re.compile(r'[\xc0-\xc4][\x80-\xbf]|[\xe0-\xef][\x80-\xbf]{2}|[\xf0-\xf4][\x80-\xbf]{3}'),
            'latin1_errors': re.compile(r'[\x80-\x9F]'),
            'windows1252': re.compile(r'[\x80-\x9F]'),
            'mojibake_pattern': re.compile(r'[ÃÂ][©®ª±²³]'),  # 常见乱码模式
        }

        # HTML实体模式
        self.html_entity_patterns = {
            'named_entities': re.compile(r'&[a-z_a-Z]+;'),
            'numeric_entities': re.compile(r'&#\d+;'),
            'hex_entities': re.compile(r'&#x[0-9a-f_a-F]+;'),
            'malformed_entities': re.compile(r'&[^;\s]+'),
        }

        # 特殊字符噪声模式
        self.special_noise_patterns = {
            'diacritical_stacks': re.compile(r'[\u0300-\u036F]{3,}'),  # 3个以上变音符号
            'box_drawing': re.compile(r'[\u2500-\u257F]'),  # 制表符
            'block_elements': re.compile(r'[\u2580-\u259F]'),  # 块元素
            'geometric_shapes': re.compile(r'[\u25A0-\u25FF]'),  # 几何图形
            'misc_symbols': re.compile(r'[\u2600-\u26FF]'),  # 杂项符号
            'dingbats': re.compile(r'[\u2700-\u27BF]'),  # 装饰符号
            'emoticons': re.compile(r'[\u1F600-\u1F64F]'),  # 表情符号
            'transport_symbols': re.compile(r'[\u1F680-\u1F6FF]'),  # 交通符号
        }

        # 脚本混合模式
        self.script_patterns = {
            'latin': re.compile(r'[A-Za-z]'),
            'chinese': re.compile(r'[\u4e00-\u9fff]'),
            'arabic': re.compile(r'[\u0600-\u06ff]'),
            'cyrillic': re.compile(r'[\u0400-\u04ff]'),
            'japanese_hiragana': re.compile(r'[\u3040-\u309f]'),
            'japanese_katakana': re.compile(r'[\u30a0-\u30ff]'),
            'korean': re.compile(r'[\uac00-\ud7af]'),
            'hebrew': re.compile(r'[\u0590-\u05ff]'),
            'thai': re.compile(r'[\u0e00-\u0e7f]'),
        }

        # 清理策略配置
        self.cleaning_strategies = {
            NoiseType.CONTROL_CHARS: self._clean_control_chars,
            NoiseType.ZERO_WIDTH: self._clean_zero_width,
            NoiseType.REPEATED_PATTERNS: self._clean_repetitions,
            NoiseType.MALFORMED_UNICODE: self._clean_unicode_issues,
            NoiseType.ENCODING_ARTIFACTS: self._clean_encoding_artifacts,
            NoiseType.HTML_ENTITIES: self._clean_html_entities,
            NoiseType.URL_ENCODING: self._clean_url_encoding,
            NoiseType.BASE64_NOISE: self._clean_base64_noise,
            NoiseType.BINARY_DATA: self._clean_binary_data,
            NoiseType.FORMAT_CHARS: self._clean_format_chars,
            NoiseType.PUNCTUATION_NOISE: self._clean_punctuation_noise,
            NoiseType.WHITESPACE_NOISE: self._clean_whitespace_noise,
            NoiseType.MIXED_SCRIPT: self._clean_mixed_script,
            NoiseType.EMOTICON_SPAM: self._clean_emoticon_spam,
            NoiseType.SPECIAL_CHAR_NOISE: self._clean_special_char_noise,
        }

        # 统计信息
        self.processing_stats = {
            'total_processed': 0,
            'noise_type_counts': Counter(),
            'cleaning_success_rate': 0.0,
            'avg_noise_reduction': 0.0,
            'most_common_noises': Counter(),
        }

        # 缓存
        self.noise_cache = {}
        self.cache_lock = threading.Lock()

        logger.info("🚀 噪声和异常字符处理器初始化完成")

    def detect_noise(self, text: str) -> NoiseDetectionResult:
        """检测文本中的噪声"""
        if not text:
            return NoiseDetectionResult(
                noise_types=[],
                noise_segments=[],
                noise_ratio=0.0,
                severity="low",
                cleanable=True,
                suggestions=[]
            )

        # 检查缓存
        cache_key = self._get_noise_cache_key(text)
        if cache_key in self.noise_cache:
            return self.noise_cache[cache_key]

        noise_types = []
        noise_segments = []
        total_chars = len(text)
        noise_chars = 0

        # 检测各种噪声类型
        for noise_type, detection_func in self._get_detection_functions().items():
            segments = detection_func(text)
            if segments:
                noise_types.append(noise_type)
                noise_segments.extend(segments)
                noise_chars += sum(end - start for start, end, _, _ in segments)

        # 计算噪声比例
        noise_ratio = noise_chars / total_chars if total_chars > 0 else 0

        # 确定严重程度
        severity = self._determine_severity(noise_ratio, noise_types)

        # 确定是否可清理
        cleanable = self._assess_cleanability(noise_types, noise_ratio)

        # 生成处理建议
        suggestions = self._generate_suggestions(noise_types, severity)

        result = NoiseDetectionResult(
            noise_types=noise_types,
            noise_segments=noise_segments,
            noise_ratio=noise_ratio,
            severity=severity,
            cleanable=cleanable,
            suggestions=suggestions
        )

        # 缓存结果
        with self.cache_lock:
            if len(self.noise_cache) < 1000:
                self.noise_cache[cache_key] = result

        return result

    def clean_noise(self, text: str, aggressive: bool = False) -> tuple[str, NoiseDetectionResult]:
        """清理文本噪声"""
        if not text:
            return text, self.detect_noise(text)

        # 检测噪声
        noise_result = self.detect_noise(text)

        if not noise_result.noise_types:
            return text, noise_result

        cleaned_text = text
        applied_cleanings = []

        # 按优先级应用清理策略
        priority_order = [
            NoiseType.CONTROL_CHARS,
            NoiseType.ZERO_WIDTH,
            NoiseType.BINARY_DATA,
            NoiseType.ENCODING_ARTIFACTS,
            NoiseType.URL_ENCODING,
            NoiseType.HTML_ENTITIES,
            NoiseType.BASE64_NOISE,
            NoiseType.REPEATED_PATTERNS,
            NoiseType.WHITESPACE_NOISE,
            NoiseType.PUNCTUATION_NOISE,
            NoiseType.MALFORMED_UNICODE,
            NoiseType.SPECIAL_CHAR_NOISE,
            NoiseType.EMOTICON_SPAM,
            NoiseType.MIXED_SCRIPT,
            NoiseType.FORMAT_CHARS,
        ]

        for noise_type in priority_order:
            if noise_type in noise_result.noise_types:
                try:
                    old_text = cleaned_text
                    cleaned_text = self.cleaning_strategies[noise_type](cleaned_text, aggressive)
                    if old_text != cleaned_text:
                        applied_cleanings.append(noise_type.value)
                except Exception as e:
                    logger.warning(f"⚠️ 清理噪声类型 {noise_type.value} 时出错: {e}")

        # 更新统计
        self._update_cleaning_stats(text, cleaned_text, noise_result.noise_types)

        # 如果有应用清理,重新检测噪声
        if applied_cleanings:
            final_noise_result = self.detect_noise(cleaned_text)
            noise_result = final_noise_result

        return cleaned_text, noise_result

    def _get_detection_functions(self) -> dict[NoiseType, callable]:
        """获取检测函数"""
        return {
            NoiseType.CONTROL_CHARS: self._detect_control_chars,
            NoiseType.ZERO_WIDTH: self._detect_zero_width,
            NoiseType.REPEATED_PATTERNS: self._detect_repetitions,
            NoiseType.MALFORMED_UNICODE: self._detect_malformed_unicode,
            NoiseType.ENCODING_ARTIFACTS: self._detect_encoding_artifacts,
            NoiseType.HTML_ENTITIES: self._detect_html_entities,
            NoiseType.URL_ENCODING: self._detect_url_encoding,
            NoiseType.BASE64_NOISE: self._detect_base64_noise,
            NoiseType.BINARY_DATA: self._detect_binary_data,
            NoiseType.FORMAT_CHARS: self._detect_format_chars,
            NoiseType.PUNCTUATION_NOISE: self._detect_punctuation_noise,
            NoiseType.WHITESPACE_NOISE: self._detect_whitespace_noise,
            NoiseType.MIXED_SCRIPT: self._detect_mixed_script,
            NoiseType.EMOTICON_SPAM: self._detect_emoticon_spam,
            NoiseType.SPECIAL_CHAR_NOISE: self._detect_special_char_noise,
        }

    def _detect_control_chars(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测控制字符"""
        segments = []
        for _pattern_name, pattern in self.control_char_patterns.items():
            for match in pattern.finditer(text):
                segments.append((match.start(), match.end(), match.group(), NoiseType.CONTROL_CHARS))
        return segments

    def _detect_zero_width(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测零宽字符"""
        segments = []
        for _pattern_name, pattern in self.zero_width_patterns.items():
            for match in pattern.finditer(text):
                segments.append((match.start(), match.end(), match.group(), NoiseType.ZERO_WIDTH))
        return segments

    def _detect_repetitions(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测重复模式"""
        segments = []
        for _pattern_name, pattern in self.repetition_patterns.items():
            for match in pattern.finditer(text):
                segments.append((match.start(), match.end(), match.group(), NoiseType.REPEATED_PATTERNS))
        return segments

    def _detect_malformed_unicode(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测畸形Unicode"""
        segments = []

        # 检测孤立代理项
        for i, char in enumerate(text):
            if (0xD800 <= ord(char) <= 0xDFFF) and (
                i == len(text) - 1 or not (0xDC00 <= ord(text[i+1]) <= 0xDFFF)
            ):
                segments.append((i, i+1, char, NoiseType.MALFORMED_UNICODE))

        # 检测无效Unicode序列
        try:
            text.encode('utf-8')
        except UnicodeEncodeError as e:
            segments.append((e.start, e.end, text[e.end:]))

        return segments

    def _detect_encoding_artifacts(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测编码伪影"""
        segments = []
        for _pattern_name, pattern in self.encoding_artifact_patterns.items():
            for match in pattern.finditer(text):
                segments.append((match.start(), match.end(), match.group(), NoiseType.ENCODING_ARTIFACTS))
        return segments

    def _detect_html_entities(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测HTML实体"""
        segments = []
        for _pattern_name, pattern in self.html_entity_patterns.items():
            for match in pattern.finditer(text):
                segments.append((match.start(), match.end(), match.group(), NoiseType.HTML_ENTITIES))
        return segments

    def _detect_url_encoding(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测URL编码"""
        segments = []
        # 查找URL编码模式
        url_pattern = re.compile(r'%[0-9A-Fa-f]{2}')
        for match in url_pattern.finditer(text):
            segments.append((match.start(), match.end(), match.group(), NoiseType.URL_ENCODING))
        return segments

    def _detect_base64_noise(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测Base64噪声"""
        segments = []
        # 检测可能的Base64字符串
        base64_pattern = re.compile(r'[A-Za-z0-9+/]{20,}={0,2}')
        for match in base64_pattern.finditer(text):
            segment = match.group()
            # 验证是否为Base64
            if self._is_base64(segment):
                segments.append((match.start(), match.end(), segment, NoiseType.BASE64_NOISE))
        return segments

    def _detect_binary_data(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测二进制数据"""
        segments = []
        # 检测非打印字符比例高的段落
        words = text.split()
        for word in words:
            if len(word) > 10:  # 只检查较长的词
                non_printable = sum(1 for c in word if not c.isprintable())
                if non_printable / len(word) > 0.3:  # 超过30%非打印字符
                    start = text.find(word)
                    end = start + len(word)
                    segments.append((start, end, word, NoiseType.BINARY_DATA))
        return segments

    def _detect_format_chars(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测格式字符"""
        segments = []
        format_chars = [
            '\u200E', '\u200F',  # 方向标记
            '\u202A', '\u202B', '\u202C', '\u202D', '\u202E',  # 双向嵌入
            '\u2066', '\u2067', '\u2068', '\u2069',  # 双向隔离
        ]

        for char in format_chars:
            start = 0
            while True:
                pos = text.find(char, start)
                if pos == -1:
                    break
                segments.append((pos, pos + 1, char, NoiseType.FORMAT_CHARS))
                start = pos + 1

        return segments

    def _detect_punctuation_noise(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测标点噪声"""
        segments = []
        # 检测连续的标点符号
        punctuation_pattern = re.compile(r'[^\w\s]{5,}')
        for match in punctuation_pattern.finditer(text):
            segments.append((match.start(), match.end(), match.group(), NoiseType.PUNCTUATION_NOISE))
        return segments

    def _detect_whitespace_noise(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测空白噪声"""
        segments = []
        # 检测过长的空白序列
        whitespace_pattern = re.compile(r'\s{5,}')
        for match in whitespace_pattern.finditer(text):
            segments.append((match.start(), match.end(), match.group(), NoiseType.WHITESPACE_NOISE))
        return segments

    def _detect_mixed_script(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测混合脚本"""
        segments = []
        # 检测不合理的脚本混合
        scripts_found = []
        for script_name, pattern in self.script_patterns.items():
            if pattern.search(text):
                scripts_found.append(script_name)

        if len(scripts_found) > 3:  # 超过3种脚本
            # 找出混合区域
            chars = list(text)
            current_script = None
            start_idx = 0

            for i, char in enumerate(chars):
                char_script = self._get_char_script(char)
                if char_script != current_script:
                    if current_script and char_script and char_script != current_script:
                        if i - start_idx > 5:  # 只标记较长的混合区域
                            segments.append((
                                start_idx,
                                i,
                                text[start_idx:i],
                                NoiseType.MIXED_SCRIPT
                            ))
                    start_idx = i
                    current_script = char_script

        return segments

    def _detect_emoticon_spam(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测表情垃圾"""
        segments = []
        # 检测过度的表情符号
        emoticon_pattern = re.compile(r'[\u1F600-\u1F64F]{3,}')
        for match in emoticon_pattern.finditer(text):
            segments.append((match.start(), match.end(), match.group(), NoiseType.EMOTICON_SPAM))

        # 检测文本表情符号重复
        text_emoticon_pattern = re.compile(r'([:;=][)}D\]\(\[\]\/\\])')
        consecutive_emoticons = []

        for match in text_emoticon_pattern.finditer(text):
            consecutive_emoticons.append((match.start(), match.end()))

        # 检查连续的表情符号
        for i in range(len(consecutive_emoticons) - 2):
            if (consecutive_emoticons[i+1][0] - consecutive_emoticons[i][1] <= 1 and
                consecutive_emoticons[i+2][0] - consecutive_emoticons[i+1][1] <= 1):
                start = consecutive_emoticons[i][0]
                end = consecutive_emoticons[i+2][1]
                segments.append((start, end, text[start:end]))

        return segments

    def _detect_special_char_noise(self, text: str) -> list[tuple[int, int, str, NoiseType]]:
        """检测特殊字符噪声"""
        segments = []
        for _category_name, pattern in self.special_noise_patterns.items():
            for match in pattern.finditer(text):
                segments.append((match.start(), match.end(), match.group(), NoiseType.SPECIAL_CHAR_NOISE))
        return segments

    # 清理方法
    def _clean_control_chars(self, text: str, aggressive: bool = False) -> str:
        """清理控制字符"""
        cleaned = text
        for pattern in self.control_char_patterns.values():
            cleaned = pattern.sub('', cleaned)
        return cleaned

    def _clean_zero_width(self, text: str, aggressive: bool = False) -> str:
        """清理零宽字符"""
        cleaned = text
        for pattern in self.zero_width_patterns.values():
            cleaned = pattern.sub('', cleaned)
        return cleaned

    def _clean_repetitions(self, text: str, aggressive: bool = False) -> str:
        """清理重复模式"""
        cleaned = text

        # 重复字符
        if aggressive:
            cleaned = self.repetition_patterns['char_repetition'].sub(r'\1\1', cleaned)
        else:
            cleaned = self.repetition_patterns['char_repetition'].sub(r'\1\1\1', cleaned)

        # 重复单词
        cleaned = self.repetition_patterns['word_repetition'].sub(r'\1', cleaned)

        # 重复标点
        cleaned = self.repetition_patterns['punctuation_repetition'].sub(r'\1\1', cleaned)

        # 空白重复
        cleaned = self.repetition_patterns['space_repetition'].sub(' ', cleaned)
        cleaned = self.repetition_patterns['newline_repetition'].sub('\n\n', cleaned)

        return cleaned

    def _clean_unicode_issues(self, text: str, aggressive: bool = False) -> str:
        """清理Unicode问题"""
        # Unicode标准化
        cleaned = unicodedata.normalize('NFKC', text)

        # 移除替换字符
        cleaned = self.control_char_patterns['replacement_char'].sub('', cleaned)

        return cleaned

    def _clean_encoding_artifacts(self, text: str, aggressive: bool = False) -> str:
        """清理编码伪影"""
        cleaned = text

        # 尝试修复常见的编码问题
        try:
            # 尝试Latin-1解码
            decoded = cleaned.encode('latin1', errors='ignore').decode('utf-8', errors='ignore')
            if len(decoded) > len(cleaned) * 0.8:  # 如果解码结果合理
                cleaned = decoded
        except (TypeError, ZeroDivisionError) as e:
            logger.warning(f'计算时发生错误: {e}')
        except Exception as e:
            logger.error(f'未预期的错误: {e}')

        # 移除明显的编码错误
        for pattern in self.encoding_artifact_patterns.values():
            cleaned = pattern.sub('', cleaned)

        return cleaned

    def _clean_html_entities(self, text: str, aggressive: bool = False) -> str:
        """清理HTML实体"""
        # 解码HTML实体
        cleaned = html.unescape(text)

        # 移除格式错误的实体
        if aggressive:
            cleaned = re.sub(r'&[^;\s]*', '', cleaned)

        return cleaned

    def _clean_url_encoding(self, text: str, aggressive: bool = False) -> str:
        """清理URL编码"""
        try:
            # 尝试URL解码
            cleaned = urllib.parse.unquote(text)

            # 如果解码后的文本更合理,使用解码结果
            if self._is_cleaner(cleaned, text):
                return cleaned
        except Exception as e:
            logger.warning(f'操作失败: {e}')

        return text

    def _clean_base64_noise(self, text: str, aggressive: bool = False) -> str:
        """清理Base64噪声"""
        cleaned = text

        # 识别并尝试解码Base64
        base64_pattern = re.compile(r'[A-Za-z0-9+/]{20,}={0,2}')

        def replace_base64(match):
            segment = match.group()
            if self._is_base64(segment):
                try:
                    decoded = base64.b64decode(segment).decode('utf-8', errors='ignore')
                    if self._is_meaningful_text(decoded):
                        return decoded
                except (TypeError, ZeroDivisionError) as e:
                    logger.warning(f'计算时发生错误: {e}')
                except Exception as e:
                    logger.error(f'未预期的错误: {e}')
            return segment

        cleaned = base64_pattern.sub(replace_base64, cleaned)
        return cleaned

    def _clean_binary_data(self, text: str, aggressive: bool = False) -> str:
        """清理二进制数据"""
        cleaned = []

        for char in text:
            if char.isprintable() or char.isspace():
                cleaned.append(char)
            elif aggressive:
                # 跳过不可打印字符
                continue
            else:
                # 用替换符号表示
                cleaned.append('�')

        return ''.join(cleaned)

    def _clean_format_chars(self, text: str, aggressive: bool = False) -> str:
        """清理格式字符"""
        # 移除双向控制字符
        format_chars = '\u200E\u200F\u202A\u202B\u202C\u202D\u202E\u2066\u2067\u2068\u2069'
        translation_table = str.maketrans('', '', format_chars)
        return text.translate(translation_table)

    def _clean_punctuation_noise(self, text: str, aggressive: bool = False) -> str:
        """清理标点噪声"""
        if aggressive:
            # 更激进的标点清理
            cleaned = re.sub(r'[^\w\s]{3,}', '...', text)
        else:
            # 温和的标点清理
            cleaned = re.sub(r'[^\w\s]{5,}', '', text)

        return cleaned

    def _clean_whitespace_noise(self, text: str, aggressive: bool = False) -> str:
        """清理空白噪声"""
        cleaned = re.sub(r'\s{3,}', ' ', text)  # 多个空白替换为单个空格
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # 多个换行替换为两个
        return cleaned.strip()

    def _clean_mixed_script(self, text: str, aggressive: bool = False) -> str:
        """清理混合脚本"""
        # 这是一个简化的实现
        # 实际应用中可能需要更复杂的逻辑
        return text

    def _clean_emoticon_spam(self, text: str, aggressive: bool = False) -> str:
        """清理表情垃圾"""
        # 限制连续表情符号数量
        if aggressive:
            cleaned = re.sub(r'[\u1F600-\u1F64F]{2,}', '😊', text)
        else:
            cleaned = re.sub(r'[\u1F600-\u1F64F]{4,}', '', text)

        return cleaned

    def _clean_special_char_noise(self, text: str, aggressive: bool = False) -> str:
        """清理特殊字符噪声"""
        cleaned = text

        # 移除过多的装饰字符
        if aggressive:
            for pattern in self.special_noise_patterns.values():
                cleaned = pattern.sub('', cleaned)
        else:
            # 限制特殊字符的使用
            cleaned = re.sub(r'[\u2580-\u259F]{3,}', '', cleaned)  # 块元素
            cleaned = re.sub(r'[\u2600-\u26FF]{5,}', '', cleaned)  # 杂项符号

        return cleaned

    # 辅助方法
    def _is_base64(self, text: str) -> bool:
        """判断是否为Base64编码"""
        try:
            base64.b64decode(text + '==')  # 添加填充
            return True
        except Exception:
            return False

    def _is_meaningful_text(self, text: str) -> bool:
        """判断是否为有意义的文本"""
        if len(text) < 3:
            return False

        # 检查字符多样性
        unique_chars = set(text)
        if len(unique_chars) < 2:
            return False

        # 检查可读性
        readable = sum(1 for c in text if c.isalnum() or c.isspace())
        return readable / len(text) > 0.7

    def _is_cleaner(self, cleaned: str, original: str) -> bool:
        """判断清理后的文本是否更好"""
        # 简单的启发式判断
        if len(cleaned) < len(original) * 0.5:
            return False

        # 检查是否减少了特殊字符
        original_special = sum(1 for c in original if not c.isalnum() and not c.isspace())
        cleaned_special = sum(1 for c in cleaned if not c.isalnum() and not c.isspace())

        return cleaned_special < original_special

    def _get_char_script(self, char: str) -> str | None:
        """获取字符的脚本类型"""
        for script_name, pattern in self.script_patterns.items():
            if pattern.match(char):
                return script_name
        return None

    def _determine_severity(self, noise_ratio: float, noise_types: list[NoiseType]) -> str:
        """确定噪声严重程度"""
        if noise_ratio > 0.5 or len(noise_types) > 8:
            return "critical"
        elif noise_ratio > 0.3 or len(noise_types) > 5:
            return "high"
        elif noise_ratio > 0.1 or len(noise_types) > 2:
            return "medium"
        else:
            return "low"

    def _assess_cleanability(self, noise_types: list[NoiseType], noise_ratio: float) -> bool:
        """评估是否可清理"""
        # 某些类型的噪声较难清理
        hard_to_clean = {NoiseType.BINARY_DATA, NoiseType.MALFORMED_UNICODE}

        if any(nt in hard_to_clean for nt in noise_types):
            return noise_ratio < 0.3

        return noise_ratio < 0.7

    def _generate_suggestions(self, noise_types: list[NoiseType], severity: str) -> list[str]:
        """生成处理建议"""
        suggestions = []

        if NoiseType.CONTROL_CHARS in noise_types:
            suggestions.append("建议清理控制字符")

        if NoiseType.ZERO_WIDTH in noise_types:
            suggestions.append("建议移除零宽字符")

        if NoiseType.REPEATED_PATTERNS in noise_types:
            suggestions.append("建议减少重复内容")

        if NoiseType.ENCODING_ARTIFACTS in noise_types:
            suggestions.append("建议修复编码问题")

        if NoiseType.MIXED_SCRIPT in noise_types:
            suggestions.append("建议统一语言脚本")

        if severity in ["high", "critical"]:
            suggestions.append("建议使用激进清理模式")

        return suggestions

    def _get_noise_cache_key(self, text: str) -> str:
        """生成噪声检测缓存键"""
        import hashlib
        return hashlib.md5(text.encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

    def _update_cleaning_stats(self, original: str, cleaned: str, noise_types: list[NoiseType]):
        """更新清理统计"""
        self.processing_stats['total_processed'] += 1

        for noise_type in noise_types:
            self.processing_stats['noise_type_counts'][noise_type.value] += 1

        # 计算噪声减少率
        if original:
            noise_reduction = (len(original) - len(cleaned)) / len(original)
            current_avg = self.processing_stats['avg_noise_reduction']
            count = self.processing_stats['total_processed']
            self.processing_stats['avg_noise_reduction'] = (
                (current_avg * (count - 1) + noise_reduction) / count
            )

    def get_processing_stats(self) -> dict[str, Any]:
        """获取处理统计"""
        return {
            'stats': self.processing_stats.copy(),
            'cache_size': len(self.noise_cache),
            'timestamp': datetime.now().isoformat()
        }

    def clear_cache(self):
        """清理缓存"""
        with self.cache_lock:
            self.noise_cache.clear()
        logger.info("🧹 噪声处理缓存已清理")

# 使用示例
if __name__ == "__main__":
    print("🧪 测试噪声和异常字符处理器...")

    processor = NoiseProcessor()

    # 测试各种噪声类型
    test_texts = [
        "Hello\u200BWorld\u200C\u200D",  # 零宽字符
        "This has!!! lots??? of,, punctuation...",  # 标点噪声
        "Text with\x00\x01\x02 control characters",  # 控制字符
        "AAAAAABBBBBCCCCCC",  # 重复字符
        "Hello hello hello hello world",  # 重复单词
        "Some &lt;html&gt; entities &#65; here",  # HTML实体
        "URL encoded: %E4%B8%AD%E6%96%87",  # URL编码
        "Base64 noise: SGVsbG8gV29ybGQ=",  # Base64
        "Mixed 中文 English العربية текст",  # 混合脚本
        "😀😁😂🤣😃😄😅😆😉😊😋😎😍😘😗😙😚",  # 表情垃圾
        "   Multiple    spaces   ",  # 空白噪声
        "Binary \x80\x81\x82 data \x90\x91",  # 二进制数据
        "Malformed \\u_d800 Unicode",  # 畸形Unicode
        "Direction\u202B test",  # 格式字符
    ]

    for i, text in enumerate(test_texts):
        print(f"\n📝 测试 {i+1}: {text!r}")

        # 检测噪声
        noise_result = processor.detect_noise(text)
        print(f"   噪声类型: {[nt.value for nt in noise_result.noise_types]}")
        print(f"   噪声比例: {noise_result.noise_ratio:.2%}")
        print(f"   严重程度: {noise_result.severity}")
        print(f"   可清理: {noise_result.cleanable}")

        if noise_result.suggestions:
            print(f"   建议: {', '.join(noise_result.suggestions)}")

        # 清理噪声
        cleaned_text, final_result = processor.clean_noise(text)
        if cleaned_text != text:
            print(f"   清理后: {cleaned_text!r}")
            print(f"   最终噪声比例: {final_result.noise_ratio:.2%}")

    # 显示统计
    print("\n📊 处理统计:")
    stats = processor.get_processing_stats()
    print(f"   总处理数: {stats['stats']['total_processed']}")
    print(f"   平均噪声减少: {stats['stats']['avg_noise_reduction']:.2%}")
    print(f"   噪声类型分布: {dict(stats['stats']['noise_type_counts'])}")

    print("\n✅ 噪声和异常字符处理器测试完成!")
