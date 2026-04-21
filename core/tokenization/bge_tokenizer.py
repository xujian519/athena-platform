#!/usr/bin/env python3
from __future__ import annotations
"""
BGE-M3 Tokenizer - 中文分词和文本预处理

利用项目已有的BGE-M3模型进行智能分词
与向量搜索使用相同的tokenizer,保持一致性

作者: Athena AI Team
创建时间: 2026-01-19
版本: v1.0.0
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


@dataclass
class TokenizationResult:
    """分词结果"""

    original: str  # 原始文本
    tokens: list[str]  # token列表
    tokenized_text: str  # 用于全文搜索的分词文本
    token_count: int  # token数量
    unique_tokens: set[str]  # 唯一token集合
    has_chinese: bool  # 是否包含中文
    has_english: bool  # 是否包含英文


class BGETokenizer:
    """
    BGE-M3分词器

    使用BGE-M3模型的tokenizer进行智能分词
    支持中英文混合、subword级别切分
    """

    # 需要过滤的特殊token
    SPECIAL_TOKENS = {"[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "<s>", "</s>", "<unk>", "<pad>"}

    # 需要过滤的subword前缀
    SUBWORD_PREFIXES = {"##", "▁"}

    def __init__(
        self,
        model_path: str = "http://127.0.0.1:8766/v1/embeddings",
        max_length: int = 512,
        remove_special_tokens: bool = True,
        keep_subword_prefix: bool = False,
    ):
        """
        初始化BGE-M3分词器

        Args:
            model_path: BGE-M3模型路径
            max_length: 最大文本长度
            remove_special_tokens: 是否移除特殊token
            keep_subword_prefix: 是否保留subword前缀(##)
        """
        self.model_path = model_path
        self.max_length = max_length
        self.remove_special_tokens = remove_special_tokens
        self.keep_subword_prefix = keep_subword_prefix

        logger.info("🔄 初始化BGE-M3 Tokenizer")
        logger.info(f"   模型路径: {model_path}")
        logger.info(f"   最大长度: {max_length}")

        # 加载模型和tokenizer
        self._load_tokenizer()

    def _load_tokenizer(self) -> Any:
        """加载BGE-M3 tokenizer"""
        try:
            logger.info("🔄 加载BGE-M3模型...")

            self.model = SentenceTransformer(self.model_path)
            self.tokenizer = self.model.tokenizer

            logger.info("✅ Tokenizer加载完成")
            logger.info(f"   词汇表大小: {len(self.tokenizer)}")
            logger.info(f"   模型类型: {type(self.tokenizer).__name__}")

        except Exception as e:
            logger.error(f"❌ Tokenizer加载失败: {e}")
            raise

    def tokenize(self, text: str, return_special_tokens: bool = False) -> TokenizationResult:
        """
        对文本进行分词

        Args:
            text: 待分词的文本
            return_special_tokens: 是否返回特殊token

        Returns:
            TokenizationResult: 分词结果
        """
        if not text or not text.strip():
            return TokenizationResult(
                original=text,
                tokens=[],
                tokenized_text="",
                token_count=0,
                unique_tokens=set(),
                has_chinese=False,
                has_english=False,
            )

        # 使用BGE tokenizer进行分词
        encoded = self.tokenizer.encode_plus(
            text, max_length=self.max_length, truncation=True, return_tensors=None
        )

        # 获取token IDs
        token_ids = encoded["input_ids"]

        # 转换为tokens
        tokens = self.tokenizer.convert_ids_to_tokens(token_ids)

        # 过滤特殊token
        if self.remove_special_tokens and not return_special_tokens:
            tokens = [t for t in tokens if t not in self.SPECIAL_TOKENS]

        # 清理subword前缀
        cleaned_tokens = []
        for token in tokens:
            if not self.keep_subword_prefix:
                # 移除subword前缀
                for prefix in self.SUBWORD_PREFIXES:
                    if token.startswith(prefix):
                        token = token[len(prefix) :]
                        break
            cleaned_tokens.append(token)

        # 移除空字符串
        tokens = [t for t in cleaned_tokens if t]

        # 检测语言
        has_chinese = any(self._is_chinese(t) for t in tokens)
        has_english = any(self._is_english(t) for t in tokens)

        # 生成用于全文搜索的文本
        tokenized_text = self._format_for_fulltext_search(tokens)

        return TokenizationResult(
            original=text,
            tokens=tokens,
            tokenized_text=tokenized_text,
            token_count=len(tokens),
            unique_tokens=set(tokens),
            has_chinese=has_chinese,
            has_english=has_english,
        )

    def tokenize_batch(
        self, texts: list[str], show_progress: bool = False
    ) -> list[TokenizationResult]:
        """
        批量分词

        Args:
            texts: 文本列表
            show_progress: 是否显示进度

        Returns:
            分词结果列表
        """
        results = []

        for i, text in enumerate(texts):
            if show_progress and (i + 1) % 100 == 0:
                logger.info(f"   处理进度: {i + 1}/{len(texts)}")

            result = self.tokenize(text)
            results.append(result)

        return results

    def _format_for_fulltext_search(self, tokens: list[str]) -> str:
        """
        格式化token用于全文搜索

        Args:
            tokens: token列表

        Returns:
            适合全文搜索的文本
        """
        # 策略:保留完整token,用空格连接
        # 这样可以保持语义单元的完整性
        return " ".join(tokens)

    def _is_chinese(self, text: str) -> bool:
        """检测是否包含中文字符"""
        return bool(re.search(r"[\u4e00-\u9fff]", text))

    def _is_english(self, text: str) -> bool:
        """检测是否包含英文字母"""
        return bool(re.search(r"[a-z_a-Z]", text))

    def extract_keywords(self, text: str, top_k: int = 10, min_length: int = 2) -> list[str]:
        """
        提取关键词

        基于token频率和长度提取关键词

        Args:
            text: 输入文本
            top_k: 返回前K个关键词
            min_length: 关键词最小长度

        Returns:
            关键词列表
        """
        result = self.tokenize(text)

        # 统计token频率
        token_freq = {}
        for token in result.tokens:
            if len(token) >= min_length:
                token_freq[token] = token_freq.get(token, 0) + 1

        # 按频率排序,取top_k
        sorted_tokens = sorted(token_freq.items(), key=lambda x: (x[1], len(x[0])), reverse=True)

        keywords = [token for token, _ in sorted_tokens[:top_k]]

        return keywords

    def get_token_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的token相似度(Jaccard相似度)

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数 (0-1)
        """
        result1 = self.tokenize(text1)
        result2 = self.tokenize(text2)

        # Jaccard相似度
        intersection = len(result1.unique_tokens & result2.unique_tokens)
        union = len(result1.unique_tokens | result2.unique_tokens)

        if union == 0:
            return 0.0

        return intersection / union


# 全局单例
_tokenizer_instance: BGETokenizer | None = None


def get_bge_tokenizer(
    model_path: str = "http://127.0.0.1:8766/v1/embeddings",
) -> BGETokenizer:
    """
    获取BGE-M3分词器单例

    Args:
        model_path: BGE-M3模型路径

    Returns:
        BGETokenizer实例
    """
    global _tokenizer_instance

    if _tokenizer_instance is None:
        _tokenizer_instance = BGETokenizer(model_path=model_path)

    return _tokenizer_instance


# 使用示例
if __name__ == "__main__":
    print("=" * 80)
    print("🧪 BGE-M3 Tokenizer 测试")
    print("=" * 80)
    print()

    # 创建分词器
    tokenizer = get_bge_tokenizer()

    # 测试文本
    test_texts = [
        "专利创造性判断标准",
        "专利法规定,授予专利权的发明和实用新型,应当具备新颖性、创造性和实用性。",
        "Invention patent application examination guidelines",
        "混合文本:专利法Patent Law规定",
    ]

    for text in test_texts:
        print(f"原文: {text}")
        print("-" * 80)

        result = tokenizer.tokenize(text)

        print(f"Tokens ({result.token_count}):")
        print(f"  {result.tokens[:20]}")  # 显示前20个

        print(f"全文搜索文本: {result.tokenized_text[:100]}...")

        if result.has_chinese:
            print("  ✅ 包含中文")
        if result.has_english:
            print("  ✅ 包含英文")

        # 提取关键词
        keywords = tokenizer.extract_keywords(text, top_k=5)
        print(f"关键词: {', '.join(keywords)}")

        print()

    # 测试相似度
    print("=" * 80)
    print("📊 相似度测试")
    print("=" * 80)
    print()

    text1 = "专利创造性判断标准"
    text2 = "判断发明创造性的标准"

    similarity = tokenizer.get_token_similarity(text1, text2)
    print(f"文本1: {text1}")
    print(f"文本2: {text2}")
    print(f"Token相似度: {similarity:.3f}")

    print()
    print("=" * 80)
