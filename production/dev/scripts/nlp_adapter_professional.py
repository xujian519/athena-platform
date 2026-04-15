#!/usr/bin/env python3
"""
Athena平台 - 专业级NLP适配器
Professional NLP Adapter for Athena Platform

提供统一的自然语言处理接口，支持：
- 中文分词 (jieba)
- 命名实体识别 (NER)
- 词性标注
- 关键词提取
- 文本向量化
- 语义相似度计算

作者: Athena平台团队
版本: v1.0.0
"""

from __future__ import annotations
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

# 中文分词
try:
    import jieba
    import jieba.analyse
    import jieba.posseg as pseg
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

# NumPy
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NLPMethod(Enum):
    """NLP处理方法"""
    TOKENIZE = "tokenize"          # 分词
    POS_TAGGING = "pos_tagging"    # 词性标注
    NER = "ner"                    # 命名实体识别
    KEYWORD_EXTRACT = "keyword"    # 关键词提取
    VECTORIZATION = "vectorize"    # 向量化
    SIMILARITY = "similarity"      # 相似度计算


@dataclass
class Token:
    """分词结果"""
    text: str                    # 词文本
    pos: str                     # 词性
    start: int                   # 起始位置
    end: int                     # 结束位置
    frequency: int = 1           # 词频


@dataclass
class Entity:
    """命名实体"""
    text: str                    # 实体文本
    label: str                   # 实体标签
    start: int                   # 起始位置
    end: int                     # 结束位置
    confidence: float = 0.0      # 置信度


@dataclass
class Keyword:
    """关键词"""
    text: str                    # 关键词
    weight: float                # 权重


@dataclass
class TextVector:
    """文本向量"""
    vector: list[float]           # 向量值
    dimension: int                # 维度
    model: str                    # 模型名称


class NLPBackend(ABC):
    """NLP后端抽象基类"""

    @abstractmethod
    def tokenize(self, text: str) -> list[Token]:
        """分词"""
        pass

    @abstractmethod
    def extract_entities(self, text: str) -> list[Entity]:
        """实体识别"""
        pass

    @abstractmethod
    def extract_keywords(self, text: str, top_k: int = 10) -> list[Keyword]:
        """关键词提取"""
        pass


class JiebaBackend(NLPBackend):
    """jieba分词后端"""

    def __init__(self):
        """初始化jieba后端"""
        self.name = "jieba"
        if JIEBA_AVAILABLE:
            jieba.initialize()
            logger.info("✅ jieba后端初始化成功")
        else:
            logger.warning("❌ jieba未安装")

    def tokenize(self, text: str) -> list[Token]:
        """分词"""
        if not JIEBA_AVAILABLE:
            return []

        tokens = []
        position = 0

        for word, pos in pseg.cut(text):
            start = text.find(word, position)
            end = start + len(word)
            tokens.append(Token(
                text=word,
                pos=pos,
                start=start,
                end=end
            ))
            position = end

        return tokens

    def extract_entities(self, text: str) -> list[Entity]:
        """实体识别 (基于规则)"""
        entities = []

        # 识别人名 (简单规则)
        person_pattern = r'[张李王刘陈杨赵黄周吴][\u4e00-\u9fa5]{1,2}'
        for match in re.finditer(person_pattern, text):
            entities.append(Entity(
                text=match.group(),
                label="PERSON",
                start=match.start(),
                end=match.end(),
                confidence=0.7
            ))

        # 识别地名
        location_pattern = r'(北京|上海|广州|深圳|杭州|成都|武汉|西安|南京)'
        for match in re.finditer(location_pattern, text):
            entities.append(Entity(
                text=match.group(),
                label="LOCATION",
                start=match.start(),
                end=match.end(),
                confidence=0.9
            ))

        # 识别机构名
        org_pattern = r'([^\u3002\uff0c\uff1f\uff01]*(?:公司|集团|大学|研究所|医院))'
        for match in re.finditer(org_pattern, text):
            entities.append(Entity(
                text=match.group(),
                label="ORGANIZATION",
                start=match.start(),
                end=match.end(),
                confidence=0.6
            ))

        return entities

    def extract_keywords(self, text: str, top_k: int = 10) -> list[Keyword]:
        """关键词提取"""
        if not JIEBA_AVAILABLE:
            return []

        try:
            keywords_with_weights = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
            return [Keyword(text=kw, weight=weight) for kw, weight in keywords_with_weights]
        except Exception as e:
            logger.warning(f"关键词提取失败: {e}")
            return []


class NLPAdapter:
    """
    专业级NLP适配器

    提供统一的NLP处理接口，自动选择最佳后端。
    """

    def __init__(self, backend: NLPBackend | None = None):
        """
        初始化NLP适配器

        Args:
            backend: NLP后端，默认使用jieba后端
        """
        self.backend = backend or JiebaBackend()
        self._initialized = True

        # 自定义词典
        self.custom_words = set()

        # 停用词
        self.stopwords = self._load_stopwords()

    def _load_stopwords(self) -> set:
        """加载停用词"""
        # 中文常用停用词
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这'
        }
        return stopwords

    def add_word(self, word: str, freq: int = 0, tag: str = None):
        """
        添加自定义词

        Args:
            word: 词语
            freq: 词频
            tag: 词性标签
        """
        if JIEBA_AVAILABLE:
            jieba.add_word(word, freq, tag)
        self.custom_words.add(word)

    def load_userdict(self, filepath: str):
        """
        加载用户词典

        Args:
            filepath: 词典文件路径
        """
        if JIEBA_AVAILABLE:
            jieba.load_userdict(filepath)
        logger.info(f"✅ 加载用户词典: {filepath}")

    def tokenize(self, text: str, cut_all: bool = False) -> list[str]:
        """
        分词

        Args:
            text: 输入文本
            cut_all: 是否使用全模式

        Returns:
            分词结果列表
        """
        if not JIEBA_AVAILABLE:
            return list(text)

        return list(jieba.cut(text, cut_all=cut_all))

    def tokenize_detail(self, text: str) -> list[Token]:
        """
        详细分词 (包含词性)

        Args:
            text: 输入文本

        Returns:
            Token列表
        """
        return self.backend.tokenize(text)

    def extract_entities(self, text: str) -> list[Entity]:
        """
        提取命名实体

        Args:
            text: 输入文本

        Returns:
            实体列表
        """
        return self.backend.extract_entities(text)

    def extract_keywords(
        self,
        text: str,
        top_k: int = 10,
        with_weight: bool = True
    ) -> list[str] | list[Keyword]:
        """
        提取关键词

        Args:
            text: 输入文本
            top_k: 返回前K个关键词
            with_weight: 是否返回权重

        Returns:
            关键词列表或Keyword对象列表
        """
        keywords = self.backend.extract_keywords(text, top_k)

        if with_weight:
            return keywords
        else:
            return [kw.text for kw in keywords]

    def pos_tagging(self, text: str) -> list[tuple[str, str]]:
        """
        词性标注

        Args:
            text: 输入文本

        Returns:
            (词, 词性) 列表
        """
        if not JIEBA_AVAILABLE:
            return []

        return list(pseg.cut(text))

    def compute_similarity(
        self,
        text1: str,
        text2: str,
        method: str = "jaccard"
    ) -> float:
        """
        计算文本相似度

        Args:
            text1: 文本1
            text2: 文本2
            method: 相似度计算方法 (jaccard/cosine/dice)

        Returns:
            相似度分数 (0-1)
        """
        words1 = set(self.tokenize(text1))
        words2 = set(self.tokenize(text2))

        if method == "jaccard":
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            return intersection / union if union > 0 else 0.0

        elif method == "dice":
            intersection = len(words1 & words2)
            return 2 * intersection / (len(words1) + len(words2)) if (len(words1) + len(words2)) > 0 else 0.0

        else:
            return 0.0

    def remove_stopwords(self, words: list[str]) -> list[str]:
        """
        移除停用词

        Args:
            words: 词列表

        Returns:
            过滤后的词列表
        """
        return [w for w in words if w not in self.stopwords and w.strip()]

    def get_word_frequency(self, text: str) -> dict[str, int]:
        """
        获取词频统计

        Args:
            text: 输入文本

        Returns:
            词频字典
        """
        words = self.tokenize(text)
        freq = {}

        for word in words:
            if word not in self.stopwords:
                freq[word] = freq.get(word, 0) + 1

        return freq

    def summarize(self, text: str, num_sentences: int = 3) -> str:
        """
        简单摘要提取

        Args:
            text: 输入文本
            num_sentences: 返回句子数量

        Returns:
            摘要文本
        """
        # 按句子分割
        sentences = re.split(r'[。！？\n]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= num_sentences:
            return text

        # 简单策略：返回前面的句子
        # 更好的实现可以使用TextRank等算法
        return '。'.join(sentences[:num_sentences]) + '。'

    async def process_batch(
        self,
        texts: list[str],
        method: NLPMethod,
        **kwargs
    ) -> list[Any]:
        """
        批量处理文本

        Args:
            texts: 文本列表
            method: 处理方法
            **kwargs: 额外参数

        Returns:
            处理结果列表
        """
        results = []

        for text in texts:
            if method == NLPMethod.TOKENIZE:
                result = self.tokenize(text)
            elif method == NLPMethod.NER:
                result = self.extract_entities(text)
            elif method == NLPMethod.KEYWORD_EXTRACT:
                result = self.extract_keywords(text, **kwargs)
            elif method == NLPMethod.POS_TAGGING:
                result = self.pos_tagging(text)
            else:
                result = None

            results.append(result)

        return results

    def __repr__(self) -> str:
        """字符串表示"""
        return f"NLPAdapter(backend={self.backend.name}, initialized={self._initialized})"


# 单例模式
_instance: NLPAdapter | None = None


def get_nlp_adapter() -> NLPAdapter:
    """
    获取NLP适配器单例

    Returns:
        NLP适配器实例
    """
    global _instance
    if _instance is None:
        _instance = NLPAdapter()
    return _instance


# 便捷函数
def tokenize(text: str) -> list[str]:
    """分词便捷函数"""
    return get_nlp_adapter().tokenize(text)


def extract_keywords(text: str, top_k: int = 10) -> list[Keyword]:
    """关键词提取便捷函数"""
    return get_nlp_adapter().extract_keywords(text, top_k)


def extract_entities(text: str) -> list[Entity]:
    """实体识别便捷函数"""
    return get_nlp_adapter().extract_entities(text)


# 主程序测试
if __name__ == "__main__":
    print("🚀 Athena平台 - NLP适配器测试")
    print("=" * 60)

    # 创建适配器
    adapter = get_nlp_adapter()
    print(f"{adapter}")
    print()

    # 测试文本
    test_text = """
    专利法是保护发明创造的重要法律。张三在北京的华为公司
    工作多年，负责人工智能相关的技术研发。
    """

    # 分词测试
    print("📝 分词测试:")
    words = adapter.tokenize(test_text)
    print(f"  {words}")
    print()

    # 词性标注测试
    print("🏷️ 词性标注测试:")
    pos_tags = adapter.pos_tagging(test_text)
    for word, pos in pos_tags[:10]:
        print(f"  {word} / {pos}")
    print()

    # 关键词提取测试
    print("🔑 关键词提取测试:")
    keywords = adapter.extract_keywords(test_text, top_k=5)
    for kw in keywords:
        print(f"  {kw.text}: {kw.weight:.4f}")
    print()

    # 实体识别测试
    print("🏢 实体识别测试:")
    entities = adapter.extract_entities(test_text)
    for entity in entities:
        print(f"  {entity.text} ({entity.label}) - 置信度: {entity.confidence}")
    print()

    print("=" * 60)
    print("✅ 测试完成！")
