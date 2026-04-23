#!/usr/bin/env python3
from __future__ import annotations
"""
BGE-M3长文本处理器
Long Text Processor for BGE-M3

利用BGE-M3的8192 token能力处理长文档,无需分段
"""

import re
from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

from core.logging_config import setup_logging

logger = setup_logging()


class ModelLoader(Protocol):
    """模型加载器协议"""

    @property
    def is_loaded(self) -> bool:
        """模型是否已加载"""
        ...

    def encode_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """编码单个文本"""
        ...

    def encode(self, texts: list[str], show_progress: bool = False) -> list[np.ndarray]:
        """批量编码文本"""
        ...


@dataclass
class TextSegment:
    """文本段"""

    content: str
    start_pos: int
    end_pos: int
    token_count: int


@dataclass
class ProcessingResult:
    """处理结果"""

    embedding: np.ndarray
    segments: list[TextSegment]
    total_tokens: int
    processing_time: float
    strategy: str


class LongTextProcessor:
    """BGE-M3长文本处理器

    利用BGE-M3的8192 token最大长度处理长文档
    """

    def __init__(self, model_loader: ModelLoader | None = None, max_tokens: int = 8192):
        """初始化处理器

        Args:
            model_loader: BGE-M3模型加载器
            max_tokens: 最大token数量(默认8192)
        """
        self.model_loader: ModelLoader | None = model_loader
        self.max_tokens: int = max_tokens
        self.recommended_tokens: int = int(max_tokens * 0.9)  # 建议使用90%

        # 统计信息
        self.stats: dict[str, Any] = {
            "total_texts_processed": 0,
            "total_tokens_processed": 0,
            "total_segments": 0,
            "avg_tokens_per_text": 0,
        }

    def estimate_token_count(self, text: str) -> int:
        """估算文本的token数量

        对于中文,大致按字符数估算
        对于英文,大致按单词数*1.3估算

        Args:
            text: 文本内容

        Returns:
            估算的token数量
        """
        # 检测中英文比例
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        total_chars = len(text)

        if total_chars == 0:
            return 0

        chinese_ratio = chinese_chars / total_chars

        # 中文主导:按字符数估算
        if chinese_ratio > 0.5:
            return len(text)
        # 英文主导:按单词数估算
        else:
            words = len(text.split())
            return int(words * 1.3)

    def truncate_text(
        self, text: str, max_tokens: Optional[int] = None, strategy: str = "middle"
    ) -> tuple[str, int]:
        """截断文本到指定token数量

        Args:
            text: 原始文本
            max_tokens: 最大token数量
            strategy: 截断策略 ('head', 'tail', 'middle')

        Returns:
            (截断后的文本, 实际token数量)
        """
        max_tokens = max_tokens or self.recommended_tokens
        current_tokens = self.estimate_token_count(text)

        if current_tokens <= max_tokens:
            return text, current_tokens

        # 需要截断
        if strategy == "head":
            # 保留开头
            truncated = text[: int(len(text) * max_tokens / current_tokens)]
        elif strategy == "tail":
            # 保留结尾
            truncated = text[-int(len(text) * max_tokens / current_tokens) :]
        elif strategy == "middle":
            # 保留中间(丢弃开头和结尾各一半)
            keep_ratio = max_tokens / current_tokens
            start_pos = int(len(text) * (1 - keep_ratio) / 2)
            end_pos = int(len(text) * (1 + keep_ratio) / 2)
            truncated = text[start_pos:end_pos]
        else:
            # 默认保留开头
            truncated = text[: int(len(text) * max_tokens / current_tokens)]

        actual_tokens = self.estimate_token_count(truncated)
        return truncated, actual_tokens

    def process_single(
        self,
        text: str,
        normalize: bool = True,
        auto_truncate: bool = True,
        truncate_strategy: str = "middle",
    ) -> ProcessingResult:
        """处理单个长文本

        Args:
            text: 输入文本
            normalize: 是否归一化向量
            auto_truncate: 是否自动截断超长文本
            truncate_strategy: 截断策略

        Returns:
            处理结果
        """
        import time

        if not self.model_loader or not self.model_loader.is_loaded:
            raise RuntimeError("模型未加载,请先加载BGE-M3模型")

        start_time = time.time()

        # 估算token数量
        token_count = self.estimate_token_count(text)

        segments = []
        processed_text = text

        # 自动截断
        if auto_truncate and token_count > self.recommended_tokens:
            logger.info(
                f"⚠️  文本过长 ({token_count} tokens),"
                f"将截断到 {self.recommended_tokens} tokens"
            )
            processed_text, actual_tokens = self.truncate_text(
                text,
                max_tokens=self.recommended_tokens,
                strategy=truncate_strategy,
            )

            segments.append(
                TextSegment(
                    content=processed_text,
                    start_pos=0,
                    end_pos=len(processed_text),
                    token_count=actual_tokens,
                )
            )
        else:
            segments.append(
                TextSegment(
                    content=text,
                    start_pos=0,
                    end_pos=len(text),
                    token_count=token_count,
                )
            )

        # 编码
        embedding = self.model_loader.encode_single(
            processed_text,
            normalize=normalize,
        )

        processing_time = time.time() - start_time

        # 更新统计
        self.stats["total_texts_processed"] += 1
        self.stats["total_tokens_processed"] += token_count
        self.stats["total_segments"] += len(segments)

        return ProcessingResult(
            embedding=embedding,
            segments=segments,
            total_tokens=token_count,
            processing_time=processing_time,
            strategy="single" if len(segments) == 1 else "truncated",
        )

    def process_with_chunking(
        self,
        text: str,
        chunk_size: int = 4000,
        overlap: int = 200,
        normalize: bool = True,
        aggregate: str = "mean",
    ) -> ProcessingResult:
        """分块处理超长文本并聚合

        Args:
            text: 输入文本
            chunk_size: 每块token数量
            overlap: 块间重叠token数量
            normalize: 是否归一化向量
            aggregate: 聚合策略 ('mean', 'max', 'weighted')

        Returns:
            处理结果
        """
        import time

        if not self.model_loader or not self.model_loader.is_loaded:
            raise RuntimeError("模型未加载,请先加载BGE-M3模型")

        start_time = time.time()
        total_tokens = self.estimate_token_count(text)

        # 分块
        segments = []
        embeddings = []
        position = 0

        while position < len(text):
            # 计算块结束位置
            end_pos = min(position + int(len(text) * chunk_size / total_tokens), len(text))

            # 提取文本块
            chunk = text[position:end_pos]
            chunk_tokens = self.estimate_token_count(chunk)

            # 编码
            embedding = self.model_loader.encode_single(chunk, normalize=normalize)
            embeddings.append(embedding)

            segments.append(
                TextSegment(
                    content=chunk,
                    start_pos=position,
                    end_pos=end_pos,
                    token_count=chunk_tokens,
                )
            )

            # 移动到下一块(考虑重叠)
            position = end_pos - int(len(text) * overlap / total_tokens)

            # 避免死循环
            if position <= 0:
                position = end_pos

        # 聚合向量
        if aggregate == "mean":
            final_embedding = np.mean(embeddings, axis=0)
        elif aggregate == "max":
            final_embedding = np.max(embeddings, axis=0)
        elif aggregate == "weighted":
            # 按token数量加权
            weights = np.array([s.token_count for s in segments])
            weights = weights / weights.sum()
            final_embedding = np.average(embeddings, axis=0, weights=weights)
        else:
            final_embedding = np.mean(embeddings, axis=0)

        processing_time = time.time() - start_time

        # 更新统计
        self.stats["total_texts_processed"] += 1
        self.stats["total_tokens_processed"] += total_tokens
        self.stats["total_segments"] += len(segments)

        return ProcessingResult(
            embedding=final_embedding,
            segments=segments,
            total_tokens=total_tokens,
            processing_time=processing_time,
            strategy=f"chunked_{aggregate}",
        )

    def process_batch(
        self,
        texts: list[str],
        normalize: bool = True,
        auto_truncate: bool = True,
        show_progress: bool = False,
    ) -> list[ProcessingResult]:
        """批量处理文本

        Args:
            texts: 文本列表
            normalize: 是否归一化向量
            auto_truncate: 是否自动截断
            show_progress: 是否显示进度

        Returns:
            处理结果列表
        """
        results = []

        # 直接使用model_loader的批量编码
        if self.model_loader and self.model_loader.is_loaded:
            # 预处理:检查是否需要截断
            processed_texts = []
            segment_lists = []
            token_counts = []

            for text in texts:
                token_count = self.estimate_token_count(text)
                token_counts.append(token_count)

                if auto_truncate and token_count > self.recommended_tokens:
                    truncated, _ = self.truncate_text(text, max_tokens=self.recommended_tokens)
                    processed_texts.append(truncated)
                    segment_lists.append(
                        [
                            TextSegment(
                                content=truncated,
                                start_pos=0,
                                end_pos=len(truncated),
                                token_count=self.estimate_token_count(truncated),
                            )
                        ]
                    )
                else:
                    processed_texts.append(text)
                    segment_lists.append(
                        [
                            TextSegment(
                                content=text,
                                start_pos=0,
                                end_pos=len(text),
                                token_count=token_count,
                            )
                        ]
                    )

            # 批量编码
            import time

            start_time = time.time()
            embeddings = self.model_loader.encode(processed_texts, show_progress=show_progress)
            processing_time = time.time() - start_time

            # 构建结果
            for _i, (text, embedding, segments, tokens) in enumerate(
                zip(texts, embeddings, segment_lists, token_counts, strict=False)
            ):
                results.append(
                    ProcessingResult(
                        embedding=embedding,
                        segments=segments,
                        total_tokens=tokens,
                        processing_time=processing_time / len(texts),  # 平均时间
                        strategy="batch",
                    )
                )

                # 更新统计
                self.stats["total_texts_processed"] += 1
                self.stats["total_tokens_processed"] += tokens
                self.stats["total_segments"] += len(segments)

        return results

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        stats = self.stats.copy()

        if stats["total_texts_processed"] > 0:
            stats["avg_tokens_per_text"] = (
                stats["total_tokens_processed"] / stats["total_texts_processed"]
            )
        else:
            stats["avg_tokens_per_text"] = 0

        stats["max_tokens"] = self.max_tokens
        stats["recommended_tokens"] = self.recommended_tokens

        return stats

    def print_stats(self) -> Any:
        """打印统计信息"""
        stats = self.get_stats()

        logger.info("\n" + "=" * 60)
        logger.info("📊 长文本处理器统计")
        logger.info("=" * 60)
        logger.info(f"📄 处理文本数: {stats['total_texts_processed']}")
        logger.info(f"🔢 总token数: {stats['total_tokens_processed']}")
        logger.info(f"📊 总段落数: {stats['total_segments']}")
        logger.info(f"📏 平均tokens/文本: {stats['avg_tokens_per_text']:.0f}")
        logger.info(f"⚙️  最大tokens: {stats['max_tokens']}")
        logger.info(f"💡 建议tokens: {stats['recommended_tokens']}")
        logger.info("=" * 60 + "\n")


def create_long_text_processor(model_loader: ModelLoader | None = None) -> LongTextProcessor:
    """创建长文本处理器的便捷函数

    Args:
        model_loader: BGE-M3模型加载器

    Returns:
        长文本处理器实例
    """
    return LongTextProcessor(model_loader=model_loader)


if __name__ == "__main__":
    # 测试长文本处理器
    # setup_logging()  # 日志配置已移至模块导入

    from core.nlp.bge_m3_loader import load_bge_m3_model

    # 加载模型
    logger.info("🚀 加载BGE-M3模型...")
    model_loader = load_bge_m3_model()

    if model_loader and model_loader.is_loaded:
        # 创建处理器
        processor = create_long_text_processor(model_loader)

        # 测试短文本
        short_text = "这是一个短文本测试。"
        logger.info(f"\n📝 测试短文本 ({len(short_text)} 字符)")
        result = processor.process_single(short_text)
        logger.info(f"✅ 处理成功: {result.total_tokens} tokens, 向量维度 {result.embedding.shape}")

        # 测试长文本
        long_text = "这是一个长文本。" * 1000  # 约7000字符
        logger.info(f"\n📝 测试长文本 ({len(long_text)} 字符)")
        result = processor.process_single(long_text, auto_truncate=True)
        logger.info(f"✅ 处理成功: {result.total_tokens} tokens, 策略 {result.strategy}")

        # 测试分块处理
        logger.info("\n📝 测试分块处理")
        result = processor.process_with_chunking(long_text, chunk_size=4000, overlap=200)
        logger.info(f"✅ 处理成功: {result.total_tokens} tokens, {len(result.segments)} 个块")

        # 打印统计
        processor.print_stats()
    else:
        logger.error("❌ 模型加载失败")
