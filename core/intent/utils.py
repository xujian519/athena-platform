from __future__ import annotations
"""
意图识别服务 - 公共工具函数模块

提供文本预处理、实体提取、关键词匹配等公共工具方法。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""

import re
import string
from typing import Any

# ========================================================================
# 文本预处理工具
# ========================================================================


class TextPreprocessor:
    """
    文本预处理器

    提供各种文本清洗和标准化方法。
    """

    # 常见的中英文停用词
    CHINESE_STOP_WORDS = {
        "的",
        "了",
        "在",
        "是",
        "我",
        "有",
        "和",
        "就",
        "不",
        "人",
        "都",
        "一",
        "一个",
        "上",
        "也",
        "很",
        "到",
        "说",
        "要",
        "去",
        "你",
        "会",
        "着",
        "没有",
        "看",
        "好",
        "自己",
        "这",
    }

    ENGLISH_STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "that",
        "the",
        "to",
        "was",
        "will",
        "with",
    }

    @staticmethod
    def clean_text(text: str) -> str:
        """
        清洗文本

        去除特殊字符、多余空白等。

        Args:
            text: 原始文本

        Returns:
            清洗后的文本
        """
        if not text:
            return ""

        # 去除HTML标签
        text = re.sub(r"<[^>]+>", "", text)

        # 去除URL
        text = re.sub(
            r"http[s]?://(?:[a-z_a-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-f_a-F][0-9a-f_a-F]))+",
            "",
            text,
        )

        # 去除邮箱
        text = re.sub(r"\S+@\S+", "", text)

        # 去除多余空白
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        标准化空白字符

        将各种空白字符统一为空格。

        Args:
            text: 原始文本

        Returns:
            标准化后的文本
        """
        # 统一换行符
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 制表符转空格
        text = text.replace("\t", " ")

        # 多个空格合并为一个
        text = re.sub(r" +", " ", text)

        # 多个换行合并为一个
        text = re.sub(r"\n+", "\n", text)

        return text.strip()

    @staticmethod
    def remove_punctuation(text: str, keep: Optional[str] = None) -> str:
        """
        去除标点符号

        Args:
            text: 原始文本
            keep: 要保留的标点符号

        Returns:
            去除标点后的文本
        """
        keep_set = set(keep) if keep else set()

        # 创建要去除的标点集合
        remove_set = set(string.punctuation) - keep_set

        # 转换为正则表达式
        if remove_set:
            pattern = f"[{''.join(re.escape(c) for c in remove_set)}"
            text = re.sub(pattern, "", text)

        return text

    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """
        截断文本

        Args:
            text: 原始文本
            max_length: 最大长度
            suffix: 截断后缀

        Returns:
            截断后的文本
        """
        if len(text) <= max_length:
            return text

        return text[: max_length - len(suffix)] + suffix


# ========================================================================
# 实体提取工具
# ========================================================================


class EntityExtractor:
    """
    实体提取器

    从文本中提取各种类型的实体。
    """

    # 专利号正则模式
    PATENT_PATTERNS = {
        "CN": r"CN\d{7,}[A-Z]?",  # 中国专利
        "US": r"US\d{7,}[B1-9]?",  # 美国专利
        "EP": r"EP\d{7,}[A-Z]\d?",  # 欧洲专利
        "WO": r"WO\d{8,}[A-Z]\d?",  # PCT专利
        "JP": r"JP\d{8,}[A-Z]\d?",  # 日本专利
        "KR": r"KR\d{7,}[A-Z]\d?",  # 韩国专利
    }

    # 数字模式
    NUMBER_PATTERNS = {
        "year": r"(19|20)\d{2}",  # 年份
        "amount": r"\d{1,3}(,\d{3})*",  # 金额(带逗号)
        "large_number": r"\d{4,}",  # 大数字
    }

    # 技术术语模式
    TECH_PATTERNS = {
        "chemical": r"[A-Z][a-z]?\d+",  # 化学式(如C12)
        "algorithm": r"[A-Z]{2,}(?:\d+)?",  # 算法名(如BERT, SVM)
    }

    @classmethod
    def extract_patents(cls, text: str) -> list[str]:
        """
        提取专利号

        Args:
            text: 输入文本

        Returns:
            专利号列表
        """
        patents = []

        # 尝试所有专利模式
        for _country, pattern in cls.PATENT_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            patents.extend([m.upper() for m in matches])

        # 去重并返回
        return list(set(patents))

    @classmethod
    def extract_numbers(cls, text: str) -> dict[str, list[str]]:
        """
        提取数字

        Args:
            text: 输入文本

        Returns:
            数字字典,按类型分组
        """
        numbers = {}

        for num_type, pattern in cls.NUMBER_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                numbers[num_type] = matches

        return numbers

    @classmethod
    def extract_technical_terms(cls, text: str) -> list[str]:
        """
        提取技术术语

        Args:
            text: 输入文本

        Returns:
            技术术语列表
        """
        terms = []

        for _term_type, pattern in cls.TECH_PATTERNS.items():
            matches = re.findall(pattern, text)
            terms.extend(matches)

        return list(set(terms))

    @classmethod
    def extract_entities(cls, text: str) -> dict[str, list]:
        """
        提取所有实体

        Args:
            text: 输入文本

        Returns:
            实体字典
        """
        return {
            "patents": cls.extract_patents(text),
            "numbers": cls.extract_numbers(text),
            "technical_terms": cls.extract_technical_terms(text),
        }


# ========================================================================
# 关键词匹配工具
# ========================================================================


class KeywordMatcher:
    """
    关键词匹配器

    提供基于关键词的意图识别辅助方法。
    """

    # 专利相关关键词
    PATENT_KEYWORDS = {
        "search": ["检索", "搜索", "查找", "查询", "寻找"],
        "analysis": ["分析", "评估", "审查", "判断", "研究"],
        "drafting": ["撰写", "起草", "写", "生成"],
        "comparison": ["对比", "比较", "区别", "差异"],
        "translation": ["翻译", "中译英", "英译中"],
    }

    # 法律相关关键词
    LEGAL_KEYWORDS = {
        "consulting": ["咨询", "建议", "顾问", "意见"],
        "research": ["检索", "调研", "查找"],
        "litigation": ["诉讼", "起诉", "维权", "侵权"],
    }

    # 代码相关关键词
    CODE_KEYWORDS = {
        "generation": ["写", "生成", "创建", "开发"],
        "review": ["审查", "检查", "优化"],
        "debugging": ["调试", "修复", "排错"],
        "refactoring": ["重构", "优化", "改进"],
    }

    @classmethod
    def match_keywords(cls, text: str, keyword_dict: dict[str, list[str]]) -> dict[str, int]:
        """
        匹配关键词

        Args:
            text: 输入文本
            keyword_dict: 关键词字典

        Returns:
            匹配结果字典 {category: count}
        """
        results = {}

        for category, keywords in keyword_dict.items():
            count = 0
            for keyword in keywords:
                count += text.count(keyword)
            if count > 0:
                results[category] = count

        return results

    @classmethod
    def detect_intent_from_keywords(cls, text: str) -> Optional[str]:
        """
        从关键词检测意图

        Args:
            text: 输入文本

        Returns:
            检测到的意图,如果没有检测到返回None
        """
        text = text.lower()

        # 检查各类别关键词
        patent_matches = cls.match_keywords(text, cls.PATENT_KEYWORDS)
        legal_matches = cls.match_keywords(text, cls.LEGAL_KEYWORDS)
        code_matches = cls.match_keywords(text, cls.CODE_KEYWORDS)

        # 判断主要意图
        if code_matches and sum(code_matches.values()) >= 2:
            return "CODE"

        if legal_matches and sum(legal_matches.values()) >= 1:
            return "LEGAL"

        if patent_matches and sum(patent_matches.values()) >= 1:
            if "search" in patent_matches:
                return "PATENT_SEARCH"
            elif "analysis" in patent_matches:
                return "PATENT_ANALYSIS"
            elif "drafting" in patent_matches:
                return "PATENT_DRAFTING"

        return None


# ========================================================================
# 文本相似度工具
# ========================================================================


class TextSimilarity:
    """
    文本相似度计算工具

    提供各种文本相似度计算方法。
    """

    @staticmethod
    def jaccard_similarity(text1: str, text2: str) -> float:
        """
        计算Jaccard相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度(0-1)
        """
        set1 = set(text1.split())
        set2 = set(text2.split())

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def levenshtein_distance(text1: str, text2: str) -> int:
        """
        计算编辑距离

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            编辑距离
        """
        m, n = len(text1), len(text2)

        # 创建距离矩阵
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # 初始化
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        # 填充矩阵
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if text1[i - 1] == text2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]  # 删除  # 插入  # 替换
                    )

        return dp[m][n]

    @staticmethod
    def levenshtein_similarity(text1: str, text2: str) -> float:
        """
        计算基于编辑距离的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度(0-1)
        """
        max_len = max(len(text1), len(text2))
        if max_len == 0:
            return 1.0

        distance = TextSimilarity.levenshtein_distance(text1, text2)
        return 1.0 - (distance / max_len)


# ========================================================================
# 缓存工具
# ========================================================================


class SimpleCache:
    """
    简单的内存缓存实现

    用于缓存意图识别结果。
    """

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        初始化缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 生存时间(秒)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: dict[str, tuple] = {}
        self._access_times: dict[str, float] = {}

    def get(self, key: str) -> Any | None:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值,如果不存在或已过期返回None
        """
        import time

        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]

        # 检查是否过期
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]
            return None

        # 更新访问时间
        self._access_times[key] = time.time()

        return value

    def set(self, key: str, value: Any) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        import time

        # 如果缓存已满,删除最久未访问的条目
        if len(self._cache) >= self.max_size and self._access_times:
            oldest_key = min(self._access_times, key=self._access_times.get)
            del self._cache[oldest_key]
            del self._access_times[oldest_key]

        # 存储值
        self._cache[key] = (value, time.time())
        self._access_times[key] = time.time()

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._access_times.clear()

    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


# ========================================================================
# 性能监控工具
# ========================================================================


class PerformanceMonitor:
    """
    性能监控工具

    用于监控意图识别的性能指标。
    """

    def __init__(self):
        """初始化监控器"""
        self._timings: dict[str, list] = {}

    def start(self, operation: str) -> float:
        """
        开始计时

        Args:
            operation: 操作名称

        Returns:
            开始时间戳
        """
        import time

        return time.perf_counter()

    def end(self, operation: str, start_time: float) -> float:
        """
        结束计时

        Args:
            operation: 操作名称
            start_time: 开始时间戳

        Returns:
            耗时(秒)
        """
        import time

        elapsed = time.perf_counter() - start_time

        if operation not in self._timings:
            self._timings[operation] = []

        self._timings[operation].append(elapsed)

        return elapsed

    def get_stats(self, operation: str) -> dict[str, float]:
        """
        获取操作统计信息

        Args:
            operation: 操作名称

        Returns:
            统计信息字典
        """
        if operation not in self._timings:
            return {}

        timings = self._timings[operation]

        return {
            "count": len(timings),
            "total": sum(timings),
            "avg": sum(timings) / len(timings),
            "min": min(timings),
            "max": max(timings),
        }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """
        获取所有操作的统计信息

        Returns:
            所有操作的统计信息
        """
        return {op: self.get_stats(op) for op in self._timings}


# ========================================================================
# 导出公共接口
# ========================================================================

__all__ = [
    "EntityExtractor",
    "KeywordMatcher",
    "PerformanceMonitor",
    "SimpleCache",
    "TextPreprocessor",
    "TextSimilarity",
]
