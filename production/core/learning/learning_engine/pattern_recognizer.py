#!/usr/bin/env python3
"""
学习引擎 - 模式识别器
Learning Engine - Pattern Recognizer

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

from __future__ import annotations
import logging
from collections import Counter
from datetime import datetime
from typing import Any

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class PatternRecognizer:
    """模式识别器"""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000, stop_words="english", ngram_range=(1, 2)
        )
        self.pattern_models: dict[str, Any] = {}
        self.pattern_history: list[dict[str, Any]] = []

    async def recognize_patterns(
        self, data: list[dict[str, Any]], context_type: str
    ) -> list[dict[str, Any]]:
        """识别模式"""
        if not data:
            return []

        try:
            # 提取文本特征
            texts = [item.get("text", "") or str(item.get("content", "")) for item in data]
            texts = [text for text in texts if text.strip()]

            if len(texts) < 2:
                return []

            # 向量化
            if context_type not in self.pattern_models:
                self.vectorizer.fit(texts)
                vectors = self.vectorizer.transform(texts)
            else:
                vectors = self.vectorizer.transform(texts)

            # 聚类分析
            n_clusters = min(5, len(texts) // 2)
            if n_clusters >= 2:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                # 处理稀疏矩阵和稠密矩阵
                vectors_array = vectors.toarray() if hasattr(vectors, "toarray") else vectors  # type: ignore
                cluster_labels = kmeans.fit_predict(vectors_array)

                # 生成模式
                patterns = []
                for cluster_id in range(n_clusters):
                    cluster_texts = [
                        texts[i] for i in range(len(texts)) if cluster_labels[i] == cluster_id
                    ]

                    pattern = {
                        "pattern_id": f"{context_type}_cluster_{cluster_id}",
                        "type": context_type,
                        "cluster_id": cluster_id,
                        "texts": cluster_texts,
                        "count": len(cluster_texts),
                        "keywords": self._extract_keywords(cluster_texts),
                        "confidence": len(cluster_texts) / len(texts),
                    }
                    patterns.append(pattern)

                # 保存模式历史
                self.pattern_history.append(
                    {
                        "timestamp": datetime.now(),
                        "context_type": context_type,
                        "patterns": patterns,
                    }
                )

                return patterns

        except Exception as e:
            logger.error(f"模式识别失败: {e}")

        return []

    def _extract_keywords(self, texts: list[str], top_k: int = 5) -> list[str]:
        """提取关键词"""
        try:
            all_text = " ".join(texts)
            # 使用新API (scikit-learn 1.0+)
            if hasattr(self.vectorizer, "get_feature_names_out"):
                self.vectorizer.get_feature_names_out()  # type: ignore
            else:
                # 兼容旧版本
                self.vectorizer.get_feature_names()  # type: ignore

            # 简单的词频统计
            words = all_text.lower().split()
            word_freq = Counter(word for word in words if len(word) > 2)

            return [word for word, _ in word_freq.most_common(top_k)]

        except Exception:
            return []


__all__ = ["PatternRecognizer"]
