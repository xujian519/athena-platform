#!/usr/bin/env python3
"""
注意力可视化器
Attention Visualizer

可视化模型在处理输入时的注意力分布
帮助理解模型关注的关键信息
"""

import html
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from core.async_main import async_main

logger = logging.getLogger(__name__)


class AttentionFormat(Enum):
    """注意力输出格式"""

    TEXT = "text"  # 文本
    HTML = "html"  # HTML(带高亮)
    HEATMAP = "heatmap"  # 热力图
    JSON = "json"  # JSON


@dataclass
class AttentionWeight:
    """注意力权重"""

    token: str  # 词元
    weight: float  # 权重
    position: int  # 位置
    layer: int = 0  # 层
    head: int = 0  # 头


@dataclass
class AttentionMap:
    """注意力图"""

    map_id: str
    input_text: str
    tokens: list[str]
    attention_weights: list[list[float]]  # [layer][token]
    metadata: dict[str, Any] = field(default_factory=dict)


class AttentionVisualizer:
    """
    注意力可视化器

    核心功能:
    1. 注意力权重解析
    2. 高亮显示
    3. 热力图生成
    4. 层级分析
    """

    def __init__(self):
        """初始化可视化器"""
        self.name = "注意力可视化器 v1.0"
        self.version = "1.0.0"

        # 颜色映射(从浅到深)
        self.color_map = [
            "#ffffff",  # 0%
            "#fffee0",  # 10%
            "#ffddba",  # 20%
            "#ffcc99",  # 30%
            "#ffbb77",  # 40%
            "#ffaa55",  # 50%
            "#ff9933",  # 60%
            "#ff8811",  # 70%
            "#ff7700",  # 80%
            "#ff6600",  # 90%
            "#ff5500",  # 100%
        ]

        # 注意力图历史
        self.attention_maps: list[AttentionMap] = []

    def create_attention_map(
        self,
        input_text: str,
        tokens: list[str],
        attention_weights: list[list[float]],
        metadata: dict[str, Any] | None = None,
    ) -> AttentionMap:
        """
        创建注意力图

        Args:
            input_text: 输入文本
            tokens: 词元列表
            attention_weights: 注意力权重 [layer][token]
            metadata: 元数据

        Returns:
            AttentionMap: 注意力图
        """
        attention_map = AttentionMap(
            map_id=f"attn_{int(datetime.now().timestamp())}",
            input_text=input_text,
            tokens=tokens,
            attention_weights=attention_weights,
            metadata=metadata or {},
        )

        self.attention_maps.append(attention_map)
        return attention_map

    def visualize(
        self,
        attention_map: AttentionMap,
        format: AttentionFormat = AttentionFormat.HTML,
        layer: int = -1,  # -1表示所有层
    ) -> str:
        """
        可视化注意力

        Args:
            attention_map: 注意力图
            format: 输出格式
            layer: 指定层(-1表示所有层)

        Returns:
            str: 可视化结果
        """
        if format == AttentionFormat.TEXT:
            return self._visualize_text(attention_map, layer)
        elif format == AttentionFormat.HTML:
            return self._visualize_html(attention_map, layer)
        elif format == AttentionFormat.HEATMAP:
            return self._visualize_heatmap(attention_map, layer)
        else:  # JSON
            return self._visualize_json(attention_map)

    def _visualize_text(self, attention_map: AttentionMap, layer: int) -> str:
        """文本格式可视化"""
        lines = [f"注意力可视化: {attention_map.map_id}"]
        lines.append("=" * 50)
        lines.append(f"输入: {attention_map.input_text}")
        lines.append("")

        weights = attention_map.attention_weights
        if layer >= 0 and layer < len(weights):
            weights = [weights[layer]]

        for i, layer_weights in enumerate(weights):
            if layer >= 0 and i != layer:
                continue

            lines.append(f"层 {i}:")

            # 按权重排序
            indexed_weights = list(enumerate(layer_weights))
            indexed_weights.sort(key=lambda x: x[1], reverse=True)

            for token_idx, weight in indexed_weights:
                if token_idx < len(attention_map.tokens):
                    token = attention_map.tokens[token_idx]
                    lines.append(f"  {token}: {weight:.3f}")

            lines.append("")

        return "\n".join(lines)

    def _visualize_html(self, attention_map: AttentionMap, layer: int) -> str:
        """HTML格式可视化(带高亮)"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            "<style>",
            "body { font-family: 'Courier New', monospace; padding: 20px; }",
            ".attention-container { margin: 20px 0; }",
            ".token { display: inline-block; padding: 2px 4px; margin: 2px; border-radius: 3px; }",
            ".legend { margin-top: 20px; }",
            ".legend-item { display: inline-block; width: 30px; height: 20px; margin-right: 10px; border: 1px solid #ccc; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h2>注意力可视化: {attention_map.map_id}</h2>",
            f"<p><strong>输入:</strong> {html.escape(attention_map.input_text)}</p>",
            "<div class='attention-container'>",
        ]

        weights = attention_map.attention_weights
        if layer >= 0 and layer < len(weights):
            weights = [weights[layer]]

        for i, layer_weights in enumerate(weights):
            if layer >= 0 and i != layer:
                continue

            html_parts.append(f"<h3>层 {i}</h3>")
            html_parts.append("<div>")

            # 归一化权重到0-1
            max_weight = max(layer_weights) if layer_weights else 1.0
            min_weight = min(layer_weights) if layer_weights else 0.0

            for token_idx, weight in enumerate(layer_weights):
                if token_idx >= len(attention_map.tokens):
                    continue

                token = attention_map.tokens[token_idx]

                # 计算归一化权重
                if max_weight > min_weight:
                    normalized = (weight - min_weight) / (max_weight - min_weight)
                else:
                    normalized = 0.5

                # 选择颜色
                color_idx = int(normalized * (len(self.color_map) - 1))
                color = self.color_map[color_idx]

                # 生成HTML
                escaped_token = html.escape(token)
                html_parts.append(
                    f"<span class='token' style='background-color: {color}' "
                    f"title='{weight:.3f}'>{escaped_token}</span>"
                )

            html_parts.append("</div>")

        # 添加图例
        html_parts.append("<div class='legend'>")
        html_parts.append("<p><strong>图例:</strong></p>")

        for i, color in enumerate(self.color_map):
            percentage = i * 10
            html_parts.append(
                f"<span class='legend-item' style='background-color: {color}' "
                f"title='{percentage}%'></span>{percentage}% "
            )

        html_parts.extend(["</div>", "</body>", "</html>"])

        return "\n".join(html_parts)

    def _visualize_heatmap(self, attention_map: AttentionMap, layer: int) -> str:
        """热力图格式可视化"""
        lines = [f"注意力热力图: {attention_map.map_id}"]
        lines.append("=" * 50)

        weights = attention_map.attention_weights
        if layer >= 0 and layer < len(weights):
            weights = [weights[layer]]

        # 构建热力图
        for i, layer_weights in enumerate(weights):
            if layer >= 0 and i != layer:
                continue

            lines.append(f"\n层 {i}:")
            lines.append("")

            # 找出最大权重用于缩放
            max_weight = max(layer_weights) if layer_weights else 1.0

            for token_idx, weight in enumerate(layer_weights):
                if token_idx >= len(attention_map.tokens):
                    continue

                token = attention_map.tokens[token_idx]

                # 生成条形图
                bar_length = int(weight / max_weight * 30)
                bar = "█" * bar_length

                lines.append(f"{token:15s} {bar} {weight:.3f}")

        return "\n".join(lines)

    def _visualize_json(self, attention_map: AttentionMap) -> str:
        """JSON格式可视化"""
        import json

        data = {
            "map_id": attention_map.map_id,
            "input_text": attention_map.input_text,
            "tokens": attention_map.tokens,
            "attention_weights": attention_map.attention_weights,
            "metadata": attention_map.metadata,
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def get_top_attention(
        self, attention_map: AttentionMap, top_n: int = 5, layer: int = 0
    ) -> list[tuple[str, float]]:
        """
        获取Top N注意力

        Args:
            attention_map: 注意力图
            top_n: 返回数量
            layer: 层索引

        Returns:
            list[tuple[str, float]]: (词元, 权重)列表
        """
        if layer >= len(attention_map.attention_weights):
            return []

        weights = attention_map.attention_weights[layer]
        indexed_weights = list(enumerate(weights))

        # 排序
        indexed_weights.sort(key=lambda x: x[1], reverse=True)

        # 提取Top N
        result = []
        for token_idx, weight in indexed_weights[:top_n]:
            if token_idx < len(attention_map.tokens):
                token = attention_map.tokens[token_idx]
                result.append((token, weight))

        return result

    def get_attention_map(self, map_id: str) -> AttentionMap | None:
        """获取注意力图"""
        for attention_map in self.attention_maps:
            if attention_map.map_id == map_id:
                return attention_map
        return None


# 单例实例
_visualizer_instance: AttentionVisualizer | None = None


def get_attention_visualizer() -> AttentionVisualizer:
    """获取注意力可视化器单例"""
    global _visualizer_instance
    if _visualizer_instance is None:
        _visualizer_instance = AttentionVisualizer()
        logger.info("注意力可视化器已初始化")
    return _visualizer_instance


@async_main
async def main():
    """测试主函数"""
    visualizer = get_attention_visualizer()

    print("=== 注意力可视化测试 ===\n")

    # 创建测试注意力图
    input_text = "帮我查一下专利CN123456789A的详细信息"
    tokens = ["帮我", "查", "一下", "专利", "CN123456789A", "的", "详细信息"]

    # 模拟3层的注意力权重
    attention_weights = [
        [0.05, 0.08, 0.06, 0.15, 0.45, 0.10, 0.11],  # 层0
        [0.03, 0.05, 0.04, 0.20, 0.55, 0.08, 0.05],  # 层1
        [0.02, 0.03, 0.03, 0.10, 0.70, 0.07, 0.05],  # 层2
    ]

    attention_map = visualizer.create_attention_map(
        input_text=input_text, tokens=tokens, attention_weights=attention_weights
    )

    # 文本可视化
    print("文本格式:")
    print(visualizer.visualize(attention_map, AttentionFormat.TEXT))

    # 热力图可视化
    print("\n热力图格式:")
    print(visualizer.visualize(attention_map, AttentionFormat.HEATMAP))

    # Top注意力
    print("\n_top 3注意力 (层2):")
    top_attention = visualizer.get_top_attention(attention_map, top_n=3, layer=2)
    for token, weight in top_attention:
        print(f"  {token}: {weight:.3f}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
