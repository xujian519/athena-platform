from __future__ import annotations
"""
搜索引擎数据类型定义
"""

# Numpy兼容性导入
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from config.numpy_compatibility import np, zeros


class SearchType(Enum):
    """搜索类型"""

    FULLTEXT = "fulltext"  # 全文搜索
    SEMANTIC = "semantic"  # 语义搜索
    HYBRID = "hybrid"  # 混合搜索


@dataclass
class Document:
    """文档对象"""

    id: str
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: np.ndarray | None = None
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if self.embedding is None and self.content:
            # 自动生成向量嵌入
            self._generate_embedding()

    def _generate_embedding(self) -> Any:
        """生成文档的向量嵌入"""
        try:
            # 使用现有的嵌入模型
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("BAAI/bge-large-zh-v1.5")
            self.embedding = model.encode(self.content, convert_to_numpy=True)
        except Exception:
            # 如果无法生成,使用零向量
            self.embedding = zeros(1024, dtype=np.float32)


@dataclass
class SearchResult:
    """搜索结果"""

    documents: list[Document]
    scores: list[float]
    query: str
    search_type: SearchType
    total_time: float
    total_found: int

    @property
    def top_results(self, k: int = 5) -> list[tuple]:
        """返回前k个结果"""
        results = list(zip(self.documents, self.scores, strict=False))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
