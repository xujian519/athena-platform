#!/usr/bin/env python3

"""
小诺模糊输入预处理器
Xiaonuo Fuzzy Input Preprocessor

处理各种模糊、不规范、噪声输入,提升系统鲁棒性

功能:
1. 输入标准化和规范化
2. 文本清理和去噪
3. 格式转换和统一
4. 质量评估和验证

作者: 小诺AI团队
日期: 2025-12-18
"""

import base64
import hashlib
import html
import json
import os
import re
import sys
import threading
import unicodedata
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

class InputQualityLevel(Enum):
    """输入质量等级"""
    EXCELLENT = "excellent"    # 优秀:清晰、规范、完整
    GOOD = "good"            # 良好:基本清晰、轻微不规范
    FAIR = "fair"            # 一般:较模糊、需要处理
    POOR = "poor"            # 较差:很模糊、大量处理
    INVALID = "invalid"      # 无效:无法处理

class InputType(Enum):
    """输入类型"""
    TEXT = "text"                    # 纯文本
    MIXED_LANG = "mixed_lang"        # 混合语言
    CODE = "code"                    # 代码
    URL = "url"                      # URL链接
    EMAIL = "email"                  # 邮箱
    NUMBER = "number"                # 数字
    DATE = "date"                    # 日期
    STRUCTURED = "structured"        # 结构化数据
    NOISE = "noise"                  # 噪声数据

@dataclass
class InputAnalysisResult:
    """输入分析结果"""
    original_text: str
    cleaned_text: str
    standardized_text: str
    input_type: InputType
    quality_level: InputQualityLevel
    quality_score: float  # 0.0-1.0
    issues: list[str]     # 发现的问题
    transformations: list[str]  # 应用的转换
    metadata: dict[str, Any]
    processing_time_ms: float

class FuzzyInputPreprocessor:
    """模糊输入预处理器"""

    def __init__(self):
        """初始化预处理器"""
        # 编码模式
        self.encoding_patterns = {
            'url_encoded': re.compile(r'%[0-9A-Fa-f]{2}'),
            'html_encoded': re.compile(r'&[a-z_a-Z]+;|&#\d+;'),
            'base64_encoded': re.compile(r'^[A-Za-z0-9+/]+=*$'),
            'unicode_escape': re.compile(r'\\u[0-9a-f_a-F]{4}'),
        }

        # 噪声模式
        self.noise_patterns = {
            'repeated_chars': re.compile(r'(.)\1{3,}'),  # 重复字符
            'repeated_words': re.compile(r'\b(\w+)(\s+\1){2,}'),  # 重复单词
            'excessive_punctuation': re.compile(r'[!?。!]{3,}'),  # 过多标点
            'mixed_whitespace': re.compile(r'\s+'),  # 混合空白
            'control_chars': re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]'),  # 控制字符
            'zero_width_chars': re.compile(r'[\u200B-\u200F\u_feff]'),  # 零宽字符
        }

        # 格式标准化模式
        self.format_patterns = {
            'chinese_punctuation': {
                ',': ',', '。': '.', '!': '!', '?': '?', ':': ':', ';': ';',
                '"': '"', ''': "'", ''': "'", '(': '(', ')': ')', '[': '[', ']': ']'
            },
            'fullwidth_to_halfwidth': {},
            'halfwidth_to_fullwidth': {},
        }

        # 生成全角半角转换映射
        for i in range(33, 127):
            half = chr(i)
            full = chr(i + 65248)
            self.format_patterns['fullwidth_to_halfwidth'][full] = half
            self.format_patterns['halfwidth_to_fullwidth'][half] = full

        # 语言检测模式
        self.language_patterns = {
            'chinese': re.compile(r'[\u4e00-\u9fff]'),
            'english': re.compile(r'[a-z_a-Z]'),
            'numbers': re.compile(r'[0-9]'),
            'japanese': re.compile(r'[\u3040-\u309f\u30a0-\u30ff]'),
            'korean': re.compile(r'[\uac00-\ud7af]'),
            'arabic': re.compile(r'[\u0600-\u06ff]'),
            'russian': re.compile(r'[\u0400-\u04ff]'),
        }

        # 特殊模式
        self.special_patterns = {
            'url': re.compile(r'https?://[^\s]+'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'(\+?86)?[-\s]?1[3-9]\d{9}'),
            'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'date': re.compile(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?'),
            'time': re.compile(r'\d{1,2}[::]\d{2}([::]\d{2})?'),
            'chinese_id': re.compile(r'\d{17}[\d_xx]'),
            'chinese_postcode': re.compile(r'\d{6}'),
        }

        # 统计信息
        self.processing_stats = {
            'total_processed': 0,
            'quality_distribution': Counter(),
            'type_distribution': Counter(),
            'common_issues': Counter(),
            'avg_processing_time': 0.0,
        }

        # 缓存
        self.processing_cache: dict[str, Any] = {}
        self.cache_lock = threading.Lock()

        logger.info("🚀 模糊输入预处理器初始化完成")

    def preprocess(self, input_text: str) -> InputAnalysisResult:
        """预处理输入文本"""
        start_time = datetime.now()

        try:
            # 检查缓存
            cache_key = self._get_cache_key(input_text)
            if cache_key in self.processing_cache:
                logger.debug(f"📋 使用缓存结果: {cache_key[:16]}...")
                cached_result = self.processing_cache[cache_key]
                cached_result.processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                return cached_result

            # 初始分析
            original_text = input_text.strip()

            # 第一步:解码处理
            decoded_text = self._decode_input(original_text)

            # 第二步:基础清理
            cleaned_text = self._basic_cleanup(decoded_text)

            # 第三步:格式标准化
            standardized_text = self._standardize_format(cleaned_text)

            # 第四步:高级清理
            final_text = self._advanced_cleanup(standardized_text)

            # 第五步:质量评估
            quality_result = self._assess_quality(final_text)

            # 第六步:类型识别
            input_type = self._identify_input_type(final_text)

            # 构建结果
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            result = InputAnalysisResult(
                original_text=original_text,
                cleaned_text=cleaned_text,
                standardized_text=final_text,
                input_type=input_type,
                quality_level=quality_result['level'],
                quality_score=quality_result['score'],
                issues=quality_result['issues'],
                transformations=quality_result['transformations'],
                metadata=quality_result['metadata'],
                processing_time_ms=processing_time
            )

            # 更新统计
            self._update_stats(result)

            # 缓存结果
            with self.cache_lock:
                if len(self.processing_cache) < 1000:  # 限制缓存大小
                    self.processing_cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"❌ 预处理失败: {e}")
            # 返回基础结果
            return InputAnalysisResult(
                original_text=input_text,
                cleaned_text=input_text,
                standardized_text=input_text,
                input_type=InputType.NOISE,
                quality_level=InputQualityLevel.INVALID,
                quality_score=0.0,
                issues=[f"处理异常: {e!s}"],
                transformations=[],
                metadata={},
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    def _decode_input(self, text: str) -> str:
        """解码输入文本"""
        transformations = []

        try:
            # URL解码
            if self.encoding_patterns['url_encoded'].search(text):
                text = html.unquote(text)
                transformations.append("url_decoded")

            # HTML实体解码
            if self.encoding_patterns['html_encoded'].search(text):
                text = html.unescape(text)
                transformations.append("html_decoded")

            # Unicode转义解码
            if self.encoding_patterns['unicode_escape'].search(text):
                text = text.encode('utf-8').decode('unicode_escape')
                transformations.append("unicode_decoded")

            # Base64解码(仅当看起来像Base64时)
            if self.encoding_patterns['base64_encoded'].search(text) and len(text) % 4 == 0:
                try:
                    decoded = base64.b64decode(text).decode('utf-8')
                    if self._is_meaningful_text(decoded):
                        text = decoded
                        transformations.append("base64_decoded")
                except Exception:
                    pass  # 忽略Base64解码错误

            return text

        except Exception as e:
            logger.warning(f"⚠️ 解码时出现异常: {e}")
            return text

    def _basic_cleanup(self, text: str) -> str:
        """基础清理"""
        transformations = []

        # 移除控制字符
        text = self.noise_patterns['control_chars'].sub('', text)
        transformations.append("removed_control_chars")

        # 移除零宽字符
        text = self.noise_patterns['zero_width_chars'].sub('', text)
        transformations.append("removed_zero_width_chars")

        # 标准化空白字符
        text = self.noise_patterns['mixed_whitespace'].sub(' ', text)
        text = text.strip()
        transformations.append("normalized_whitespace")

        return text

    def _standardize_format(self, text: str) -> str:
        """格式标准化"""
        transformations = []

        # 全角转半角
        for full, half in self.format_patterns['fullwidth_to_halfwidth'].items():
            if full in text:
                text = text.replace(full, half)

        if any(full in text for full in self.format_patterns['fullwidth_to_halfwidth']):
            transformations.append("fullwidth_to_halfwidth")

        # 中文标点转英文标点
        for chinese, english in self.format_patterns['chinese_punctuation'].items():
            if chinese in text:
                text = text.replace(chinese, english)

        if any(chinese in text for chinese in self.format_patterns['chinese_punctuation']):
            transformations.append("chinese_punctuation_normalized")

        # Unicode标准化
        normalized_text = unicodedata.normalize('NFKC', text)
        if normalized_text != text:
            text = normalized_text
            transformations.append("unicode_normalized")

        return text

    def _advanced_cleanup(self, text: str) -> str:
        """高级清理"""
        transformations = []

        # 处理重复字符
        def replace_repeated_chars(match):
            char = match.group(1)
            return char * 2  # 保留最多2个

        if self.noise_patterns['repeated_chars'].search(text):
            text = self.noise_patterns['repeated_chars'].sub(replace_repeated_chars, text)
            transformations.append("reduced_repeated_chars")

        # 处理重复单词
        if self.noise_patterns['repeated_words'].search(text):
            text = self.noise_patterns['repeated_words'].sub(r'\1', text)
            transformations.append("removed_repeated_words")

        # 处理过多标点
        if self.noise_patterns['excessive_punctuation'].search(text):
            text = self.noise_patterns['excessive_punctuation'].sub('!!!', text)
            transformations.append("reduced_excessive_punctuation")

        return text

    def _assess_quality(self, text: str) -> dict[str, Any]:
        """评估文本质量"""
        issues = []
        transformations = []
        metadata = {}
        score = 1.0

        # 长度检查
        if len(text) == 0:
            issues.append("文本为空")
            score -= 0.8
            return {
                'level': InputQualityLevel.INVALID,
                'score': max(0.0, score),
                'issues': issues,
                'transformations': transformations,
                'metadata': metadata
            }

        if len(text) < 3:
            issues.append("文本过短")
            score -= 0.3
        elif len(text) > 10000:
            issues.append("文本过长")
            score -= 0.2

        # 字符多样性检查
        unique_chars = set(text)
        if len(unique_chars) < 3:
            issues.append("字符多样性不足")
            score -= 0.4

        # 语言混合检查
        languages = []
        for lang, pattern in self.language_patterns.items():
            if pattern.search(text):
                languages.append(lang)

        metadata['detected_languages'] = languages
        if len(languages) > 3:
            issues.append("语言混合过多")
            score -= 0.2

        # 可读性检查
        readable_chars = 0
        for char in text:
            if char.isalnum() or char.isspace() or char in '.,!?;:()[]{}"\'-':
                readable_chars += 1

        readability = readable_chars / len(text) if text else 0
        metadata['readability_ratio'] = readability
        if readability < 0.5:
            issues.append("可读性较差")
            score -= 0.3

        # 特殊字符比例
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text) if text else 0
        metadata['special_char_ratio'] = special_char_ratio
        if special_char_ratio > 0.3:
            issues.append("特殊字符过多")
            score -= 0.2

        # 确定质量等级
        if score >= 0.9:
            level = InputQualityLevel.EXCELLENT
        elif score >= 0.7:
            level = InputQualityLevel.GOOD
        elif score >= 0.5:
            level = InputQualityLevel.FAIR
        elif score >= 0.3:
            level = InputQualityLevel.POOR
        else:
            level = InputQualityLevel.INVALID

        return {
            'level': level,
            'score': max(0.0, score),
            'issues': issues,
            'transformations': transformations,
            'metadata': metadata
        }

    def _identify_input_type(self, text: str) -> InputType:
        """识别输入类型"""
        # 检查特殊格式
        if self.special_patterns['url'].search(text):
            return InputType.URL
        elif self.special_patterns['email'].search(text):
            return InputType.EMAIL
        elif self.special_patterns['phone'].search(text):
            return InputType.TEXT  # 电话号码当作文本处理
        elif self.special_patterns['date'].search(text):
            return InputType.DATE
        elif self.special_patterns['time'].search(text):
            return InputType.TEXT

        # 检查是否为代码
        code_indicators = ['def ', 'function', 'var ', 'const', 'let ', 'import ', 'from ', 'class ', 'if ', 'for ', 'while ']
        if any(indicator in text for indicator in code_indicators):
            return InputType.CODE

        # 检查是否为纯数字
        if text.replace('.', '').replace('-', '').isdigit():
            return InputType.NUMBER

        # 检查语言混合
        languages = []
        for lang, pattern in self.language_patterns.items():
            if pattern.search(text):
                languages.append(lang)

        if len(languages) > 1:
            return InputType.MIXED_LANG
        elif len(languages) == 1:
            return InputType.TEXT

        # 检查是否为结构化数据
        if ('{' in text and '}' in text) or ('[' in text and ']' in text):
            try:
                json.loads(text)
                return InputType.STRUCTURED
            except Exception as e:
                logger.warning(f'操作失败: {e}')

        # 默认为文本
        return InputType.TEXT

    def _is_meaningful_text(self, text: str) -> bool:
        """判断是否为有意义的文本"""
        if len(text) < 5:
            return False

        # 检查是否包含足够的多样的字符
        unique_chars = set(text)
        if len(unique_chars) < 3:
            return False

        # 检查是否为常见可打印字符
        printable_ratio = sum(1 for c in text if c.isprintable()) / len(text)
        return not printable_ratio < 0.8

    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

    def _update_stats(self, result: InputAnalysisResult):
        """更新统计信息"""
        self.processing_stats['total_processed'] += 1

        # 更新质量分布
        self.processing_stats['quality_distribution'][result.quality_level.value] += 1

        # 更新类型分布
        self.processing_stats['type_distribution'][result.input_type.value] += 1

        # 更新常见问题
        for issue in result.issues:
            self.processing_stats['common_issues'][issue] += 1

        # 更新平均处理时间
        current_avg = self.processing_stats['avg_processing_time']
        count = self.processing_stats['total_processed']
        self.processing_stats['avg_processing_time'] = (
            (current_avg * (count - 1) + result.processing_time_ms) / count
        )

    def batch_preprocess(self, texts: list[str]) -> list[InputAnalysisResult]:
        """批量预处理"""
        return [self.preprocess(text) for text in texts]

    def get_processing_stats(self) -> dict[str, Any]:
        """获取处理统计"""
        return {
            'stats': self.processing_stats.copy(),
            'cache_size': len(self.processing_cache),
            'timestamp': datetime.now().isoformat()
        }

    def clear_cache(self):
        """清理缓存"""
        with self.cache_lock:
            self.processing_cache.clear()
        logger.info("🧹 预处理缓存已清理")

    def validate_input(self, text: str, min_length: int = 1, max_length: int = 50000) -> tuple[bool, list[str]]:
        """验证输入是否符合要求"""
        errors = []

        # 长度验证
        if not text:
            errors.append("输入不能为空")
            return False, errors

        if len(text) < min_length:
            errors.append(f"输入长度不能少于{min_length}个字符")

        if len(text) > max_length:
            errors.append(f"输入长度不能超过{max_length}个字符")

        # 字符验证
        try:
            text.encode('utf-8')
        except UnicodeEncodeError:
            errors.append("包含无效的Unicode字符")

        # 安全性验证
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'javascript:',               # JavaScript协议
            r'on\w+\s*=',                # 事件处理器
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                errors.append("包含潜在的不安全内容")
                break

        return len(errors) == 0, errors

    def enhance_text(self, text: str) -> str:
        """增强文本质量"""
        # 自动添加缺失的标点
        if text and text[-1] not in '.!?。!?':
            if '?' in text or '吗' in text or '呢' in text:
                text += '?'
            elif '!' in text or '啊' in text or '呀' in text:
                text += '!'
            else:
                text += '。'

        # 修复常见拼写错误(简单版本)
        common_misspellings = {
            '的得': '的地得',
            '嗯恩': '嗯',
            '呵呵': '呵呵',
        }

        for wrong, right in common_misspellings.items():
            if wrong in text:
                text = text.replace(wrong, right)

        return text

# 使用示例
if __name__ == "__main__":
    print("🧪 测试模糊输入预处理器...")

    preprocessor = FuzzyInputPreprocessor()

    # 测试各种类型的输入
    test_inputs = [
        "你好,我想查询机器学习相关资料",                    # 正常中文
        "Hello, can you help me find AI papers?",           # 英文
        "帮我!!!搜索???深度学习!!!",                  # 过多标点
        "我我我我想要学习python编程",                        # 重复字符
        "https://www.example.com/search?q=机器学习",        # URL
        "test@example.com",                                # 邮箱
        "Hello世界!这是一个mixed language的测试",           # 混合语言
        "",                                                # 空输入
        "   ",                                             # 只有空白
        "%E4%BD%A0%E5%A5%BD",                              # URL编码
        "&lt;script&gt;alert(1)&lt;/script&gt;",            # HTML实体
        "这是一个测试\n\t\x00\x01\x02",                      # 包含控制字符
    ]

    for i, text in enumerate(test_inputs):
        print(f"\n📝 测试 {i+1}: {text!r}")
        result = preprocessor.preprocess(text)

        print(f"   输入类型: {result.input_type.value}")
        print(f"   质量等级: {result.quality_level.value}")
        print(f"   质量分数: {result.quality_score:.3f}")
        print(f"   处理时间: {result.processing_time_ms:.1f}ms")

        if result.issues:
            print(f"   发现问题: {', '.join(result.issues)}")

        if result.transformations:
            print(f"   应用转换: {', '.join(result.transformations)}")

        if result.standardized_text != result.original_text:
            print(f"   清理后: {result.standardized_text[:100]!r}")

    # 显示统计信息
    print("\n📊 处理统计:")
    stats = preprocessor.get_processing_stats()
    print(f"   总处理数: {stats['stats']['total_processed']}")
    print(f"   平均处理时间: {stats['stats']['avg_processing_time']:.1f}ms")
    print(f"   质量分布: {dict(stats['stats']['quality_distribution'])}")
    print(f"   类型分布: {dict(stats['stats']['type_distribution'])}")

    print("\n✅ 模糊输入预处理器测试完成!")

