#!/usr/bin/env python3
from __future__ import annotations
"""
可解释认知模块 - 可视化器
Explainable Cognition Module - Visualizer

负责推理路径和决策因子的可视化

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.1.0
"""

import base64
import io
from typing import Any

# 尝试导入可视化依赖
try:
    import matplotlib.pyplot as plt
    import networkx as nx
    from matplotlib.patches import FancyBboxPatch, Patch

    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    plt = None  # type: ignore
    nx = None  # type: ignore
    FancyBboxPatch = None  # type: ignore
    Patch = None  # type: ignore

from core.cognition.explainable.types import (
    DecisionFactor,
    ReasoningPath,
    ReasoningStep,
    ReasoningStepType,
)
from core.logging_config import setup_logging

logger = setup_logging()


class ReasoningPathVisualizer:
    """推理路径可视化器"""

    def __init__(self, config: dict[str, Any]):
        if not VISUALIZATION_AVAILABLE:
            logger.warning("⚠️  可视化依赖不可用，可视化功能将被禁用")
            return

        self.config = config
        self.graph_layout = config.get("graph_layout", "hierarchical")
        self.show_confidence = config.get("show_confidence", True)
        self.show_factors = config.get("show_factors", True)
        self.color_scheme = config.get("color_scheme", "default")

    def generate_path_diagram(self, reasoning_path: ReasoningPath) -> str:
        """生成推理路径图(返回base64编码的图片)"""
        if not VISUALIZATION_AVAILABLE:
            logger.warning("⚠️  可视化功能不可用")
            return ""

        try:
            G = nx.DiGraph()  # type: ignore

            # 添加节点和边
            for step in reasoning_path.steps:
                G.add_node(
                    step.step_id,
                    label=step.description[:30] + "...",
                    type=step.step_type.value,
                    confidence=step.confidence,
                    execution_time=step.execution_time,
                )

                # 添加边
                for child_id in step.child_steps:
                    G.add_edge(step.step_id, child_id)

            # 设置布局
            if self.graph_layout == "hierarchical":
                pos = self._hierarchical_layout(G, reasoning_path.steps)
            else:
                pos = nx.spring_layout(G, k=2, iterations=50)  # type: ignore

            # 创建图形
            plt.figure(figsize=(12, 8))  # type: ignore
            plt.title(f"推理路径图: {reasoning_path.query[:50]}...", fontsize=14, fontweight="bold")  # type: ignore

            # 绘制节点
            for step in reasoning_path.steps:
                node_pos = pos[step.step_id]

                # 根据步骤类型选择颜色
                color = self._get_step_color(step.step_type)

                # 根据置信度调整透明度
                alpha = 0.5 + step.confidence * 0.5

                # 绘制节点
                bbox = FancyBboxPatch(
                    (node_pos[0] - 0.1, node_pos[1] - 0.05),
                    0.2,
                    0.1,
                    boxstyle="round,pad=0.01",
                    facecolor=color,
                    edgecolor="black",
                    alpha=alpha,
                    linewidth=2,
                )
                plt.gca().add_patch(bbox)  # type: ignore

                # 添加标签
                plt.text(  # type: ignore
                    node_pos[0],
                    node_pos[1],
                    step.step_type.value[:3].upper(),
                    ha="center",
                    va="center",
                    fontsize=8,
                    fontweight="bold",
                )

                # 添加置信度(如果启用)
                if self.show_confidence:
                    plt.text(  # type: ignore
                        node_pos[0],
                        node_pos[1] - 0.08,
                        f"置信度: {step.confidence:.2f}",
                        ha="center",
                        va="center",
                        fontsize=6,
                    )

            # 绘制边
            for edge in G.edges():
                start_pos = pos[edge[0]]
                end_pos = pos[edge[1]]
                plt.annotate(  # type: ignore
                    "",
                    xy=end_pos,
                    xytext=start_pos,
                    arrowprops={"arrowstyle": "->", "lw": 2, "color": "gray"},
                )

            # 添加图例
            self._add_legend()

            plt.tight_layout()  # type: ignore

            # 转换为base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")  # type: ignore
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()  # type: ignore

            return image_base64

        except Exception as e:
            logger.error(f"生成推理路径图失败: {e}")
            return ""

    def _hierarchical_layout(
        self, G: nx.DiGraph, steps: list[ReasoningStep]  # type: ignore
    ) -> dict[str, tuple[float, float]]:
        """层次化布局"""
        if not VISUALIZATION_AVAILABLE:
            return {}

        pos = {}
        level_mapping = {}

        # 计算每个节点的层级
        for i, step in enumerate(steps):
            level_mapping[step.step_id] = i

        # 分配位置
        max_level = max(level_mapping.values()) if level_mapping else 1
        for step_id, level in level_mapping.items():
            x = level / max(max_level, 1) * 4  # 水平位置
            y = 0  # 同一层的y坐标相同
            pos[step_id] = (x, y)

        # 调整同层节点的y坐标
        level_nodes: dict[int, list[str]] = {}
        for step_id, level in level_mapping.items():
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(step_id)

        for level, nodes in level_nodes.items():
            num_nodes = len(nodes)
            for i, node in enumerate(nodes):
                y = (i - num_nodes / 2) * 0.3
                pos[node] = (pos[node][0], y)

        return pos

    def _get_step_color(self, step_type: ReasoningStepType) -> str:
        """获取步骤类型的颜色"""
        color_map = {
            ReasoningStepType.INPUT_PROCESSING: "#FFD700",  # 金色
            ReasoningStepType.EVIDENCE_GATHERING: "#87CEEB",  # 天蓝色
            ReasoningStepType.KNOWLEDGE_RETRIEVAL: "#98FB98",  # 浅绿色
            ReasoningStepType.INFERENCE: "#DDA0DD",  # 梅红色
            ReasoningStepType.CONSIDERATION: "#F0E68C",  # 卡其色
            ReasoningStepType.EVALUATION: "#FFB6C1",  # 浅粉色
            ReasoningStepType.DECISION: "#FF6B6B",  # 红色
            ReasoningStepType.EXPLANATION: "#B0C4DE",  # 浅钢蓝色
        }
        return color_map.get(step_type, "#D3D3D3")  # 浅灰色

    def _add_legend(self) -> Any:
        """添加图例"""
        if not VISUALIZATION_AVAILABLE:
            return None

        legend_elements = []
        for step_type, color in {
            ReasoningStepType.INPUT_PROCESSING: "#FFD700",
            ReasoningStepType.EVIDENCE_GATHERING: "#87CEEB",
            ReasoningStepType.KNOWLEDGE_RETRIEVAL: "#98FB98",
            ReasoningStepType.INFERENCE: "#DDA0DD",
            ReasoningStepType.DECISION: "#FF6B6B",
        }.items():
            legend_elements.append(Patch(color=color, label=step_type.value))  # type: ignore

        plt.legend(handles=legend_elements, loc="upper right", fontsize=8)  # type: ignore

    def generate_factor_analysis_chart(self, factors: list[DecisionFactor]) -> str:
        """生成决策因子分析图"""
        if not VISUALIZATION_AVAILABLE:
            logger.warning("⚠️  可视化功能不可用")
            return ""

        # TODO: 实现因子分析图表生成
        logger.info("📊 生成因子分析图表 (待实现)")
        return ""
