#!/usr/bin/env python3
"""
上下文压缩插件 - Phase 2.3示例插件

Compression Plugin - 压缩上下文内容，减少Token使用

功能:
- 智能压缩长文本
- 保留关键信息
- 可配置压缩比例

作者: Athena平台团队
创建时间: 2026-04-24
"""

import logging
import re
from typing import Any, Dict, List, Optional

from ..base_context import BaseContextPlugin, BaseContext

logger = logging.getLogger(__name__)


class CompressionPlugin(BaseContextPlugin):
    """
    上下文压缩插件

    通过智能算法压缩上下文内容，减少Token使用量。

    配置参数:
    - ratio: 压缩比例 (0.1-1.0，默认0.5)
    - preserve_keywords: 保留的关键词列表
    - min_length: 最小保留长度（默认100字符）
    """

    def __init__(self):
        super().__init__(
            plugin_name="compression",
            plugin_version="1.0.0",
            dependencies=[],
        )
        self._compression_ratio = 0.5
        self._preserve_keywords = []
        self._min_length = 100

    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化压缩插件

        Args:
            config: 配置参数
                - ratio: 压缩比例
                - preserve_keywords: 保留关键词
                - min_length: 最小长度
        """
        await super().initialize(config)

        self._compression_ratio = config.get("ratio", 0.5)
        self._preserve_keywords = config.get("preserve_keywords", [])
        self._min_length = config.get("min_length", 100)

        logger.info(
            f"✅ 压缩插件初始化: ratio={self._compression_ratio}, "
            f"keywords={len(self._preserve_keywords)}"
        )

    async def execute(self, context: BaseContext, **kwargs) -> dict[str, Any]:
        """
        执行压缩

        Args:
            context: 上下文对象
            **kwargs: 执行参数
                - target: 压缩目标字段（默认"content"）

        Returns:
            dict[str, Any]: 压缩结果
                - original_length: 原始长度
                - compressed_length: 压缩后长度
                - compression_ratio: 实际压缩比例
                - compressed_content: 压缩后的内容
        """
        target_field = kwargs.get("target", "content")

        # 获取内容
        if hasattr(context, target_field):
            content = getattr(context, target_field)
        elif target_field in context.metadata:
            content = context.metadata[target_field]
        else:
            content = str(context.to_dict())

        original_length = len(content)

        # 如果内容太短，不需要压缩
        if original_length <= self._min_length:
            return {
                "original_length": original_length,
                "compressed_length": original_length,
                "compression_ratio": 1.0,
                "compressed_content": content,
                "skipped": True,
            }

        # 执行压缩
        compressed = await self._compress(content)

        # 更新上下文
        if hasattr(context, target_field):
            setattr(context, target_field, compressed)
        else:
            context.metadata[f"{target_field}_compressed"] = compressed

        compressed_length = len(compressed)
        actual_ratio = compressed_length / original_length if original_length > 0 else 1.0

        logger.debug(
            f"🗜️ 压缩完成: {original_length} -> {compressed_length} "
            f"({actual_ratio:.1%})"
        )

        return {
            "original_length": original_length,
            "compressed_length": compressed_length,
            "compression_ratio": actual_ratio,
            "compressed_content": compressed,
            "skipped": False,
        }

    async def _compress(self, content: str) -> str:
        """
        执行压缩算法

        Args:
            content: 原始内容

        Returns:
            str: 压缩后的内容
        """
        # 1. 移除多余空白
        compressed = re.sub(r"\s+", " ", content)
        compressed = compressed.strip()

        # 2. 保留包含关键词的句子
        if self._preserve_keywords:
            sentences = re.split(r"[。！？.!?]", compressed)
            important = []
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                if any(keyword in sentence for keyword in self._preserve_keywords):
                    important.append(sentence)

            # 计算需要保留的普通句子数量
            target_length = int(len(compressed) * self._compression_ratio)
            important_length = sum(len(s) for s in important)

            if important_length < target_length:
                # 需要添加更多句子
                remaining_length = target_length - important_length
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and sentence not in important:
                        important.append(sentence)
                        remaining_length -= len(sentence)
                        if remaining_length <= 0:
                            break

            compressed = "。".join(important[: int(len(sentences) * self._compression_ratio)])

        # 3. 按比例截断
        target_length = int(len(content) * self._compression_ratio)
        if len(compressed) > target_length:
            compressed = compressed[:target_length] + "..."

        return compressed


__all__ = ["CompressionPlugin"]
