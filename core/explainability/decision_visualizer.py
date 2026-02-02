#!/usr/bin/env python3
"""
决策可视化器
Decision Visualizer

将决策链路可视化为易于理解的图表和流程
支持多种输出格式(HTML, JSON, 文本)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.async_main import async_main

logger = logging.getLogger(__name__)


class VisualizationFormat(Enum):
    """可视化格式"""

    TEXT = "text"  # 文本
    JSON = "json"  # JSON
    HTML = "html"  # HTML
    ASCII = "ascii"  # ASCII图


class NodeType(Enum):
    """节点类型"""

    INPUT = "input"  # 输入节点
    PROCESSING = "processing"  # 处理节点
    DECISION = "decision"  # 决策节点
    OUTPUT = "output"  # 输出节点
    ERROR = "error"  # 错误节点


@dataclass
class DecisionNode:
    """决策节点"""

    node_id: str
    node_type: NodeType
    label: str
    description: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_nodes: list[str] = field(default_factory=list)
    child_nodes: list[str] = field(default_factory=list)


@dataclass
class DecisionChain:
    """决策链"""

    chain_id: str
    nodes: list[DecisionNode]
    start_time: datetime
    end_time: datetime | None = None


class DecisionVisualizer:
    """
    决策可视化器

    核心功能:
    1. 决策链构建
    2. 多格式输出
    3. 样式定制
    4. 交互式可视化
    """

    def __init__(self):
        """初始化可视化器"""
        self.name = "决策可视化器 v1.0"
        self.version = "1.0.0"

        # 决策链历史
        self.chains: list[DecisionChain] = []

        # 样式配置
        self.styles = {
            NodeType.INPUT: {"color": "#4CAF50", "shape": "oval"},
            NodeType.PROCESSING: {"color": "#2196F3", "shape": "box"},
            NodeType.DECISION: {"color": "#FF9800", "shape": "diamond"},
            NodeType.OUTPUT: {"color": "#9C27B0", "shape": "oval"},
            NodeType.ERROR: {"color": "#F44336", "shape": "box"},
        }

    def create_chain(self, chain_id: str | None = None) -> DecisionChain:
        """
        创建决策链

        Args:
            chain_id: 链ID(自动生成)

        Returns:
            DecisionChain: 决策链
        """
        if chain_id is None:
            chain_id = f"chain_{int(datetime.now().timestamp())}"

        chain = DecisionChain(chain_id=chain_id, nodes=[], start_time=datetime.now())

        self.chains.append(chain)
        return chain

    def add_node(
        self,
        chain: DecisionChain,
        node_type: NodeType,
        label: str,
        description: str = "",
        confidence: float = 0.0,
        metadata: dict[str, Any] | None = None,
        parent_id: str | None = None,
    ) -> DecisionNode:
        """
        添加节点

        Args:
            chain: 决策链
            node_type: 节点类型
            label: 标签
            description: 描述
            confidence: 置信度
            metadata: 元数据
            parent_id: 父节点ID

        Returns:
            DecisionNode: 创建的节点
        """
        node_id = f"node_{len(chain.nodes)}"
        node = DecisionNode(
            node_id=node_id,
            node_type=node_type,
            label=label,
            description=description,
            confidence=confidence,
            metadata=metadata or {},
        )

        # 设置父节点
        if parent_id:
            node.parent_nodes.append(parent_id)
            # 更新父节点的子节点
            for parent in chain.nodes:
                if parent.node_id == parent_id:
                    parent.child_nodes.append(node_id)
                    break

        chain.nodes.append(node)
        return node

    def visualize(
        self, chain: DecisionChain, format: VisualizationFormat = VisualizationFormat.ASCII
    ) -> str:
        """
        可视化决策链

        Args:
            chain: 决策链
            format: 输出格式

        Returns:
            str: 可视化结果
        """
        if format == VisualizationFormat.TEXT:
            return self._visualize_text(chain)
        elif format == VisualizationFormat.JSON:
            return self._visualize_json(chain)
        elif format == VisualizationFormat.HTML:
            return self._visualize_html(chain)
        else:  # ASCII
            return self._visualize_ascii(chain)

    def _visualize_text(self, chain: DecisionChain) -> str:
        """文本格式可视化"""
        lines = [f"决策链: {chain.chain_id}"]
        lines.append("=" * 50)

        for i, node in enumerate(chain.nodes):
            lines.append(f"\n{i+1}. {node.label}")
            if node.description:
                lines.append(f"   描述: {node.description}")
            if node.confidence > 0:
                lines.append(f"   置信度: {node.confidence:.1%}")
            if node.metadata:
                lines.append(f"   详情: {json.dumps(node.metadata, ensure_ascii=False)}")

        return "\n".join(lines)

    def _visualize_json(self, chain: DecisionChain) -> str:
        """JSON格式可视化"""
        data = {
            "chain_id": chain.chain_id,
            "start_time": chain.start_time.isoformat(),
            "end_time": chain.end_time.isoformat() if chain.end_time else None,
            "nodes": [
                {
                    "id": node.node_id,
                    "type": node.node_type.value,
                    "label": node.label,
                    "description": node.description,
                    "confidence": node.confidence,
                    "metadata": node.metadata,
                    "parents": node.parent_nodes,
                    "children": node.child_nodes,
                }
                for node in chain.nodes
            ],
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def _visualize_html(self, chain: DecisionChain) -> str:
        """HTML格式可视化"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            ".chain { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }",
            ".node { margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }",
            ".node.input { border-color: #4CAF50; background: #f1f8f4; }",
            ".node.processing { border-color: #2196F3; background: #f0f7ff; }",
            ".node.decision { border-color: #FF9800; background: #fff8f0; }",
            ".node.output { border-color: #9C27B0; background: #f8f4fc; }",
            ".node.error { border-color: #F44336; background: #fef4f4; }",
            ".confidence { float: right; font-weight: bold; }",
            ".arrow { text-align: center; color: #999; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h2>决策链: {chain.chain_id}</h2>",
            "<div class='chain'>",
        ]

        for i, node in enumerate(chain.nodes):
            style_class = node.node_type.value
            html_parts.append(f"<div class='node {style_class}'>")
            html_parts.append(f"<strong>{i+1}. {node.label}</strong>")

            if node.confidence > 0:
                html_parts.append(f"<span class='confidence'>{node.confidence:.1%}</span>")

            if node.description:
                html_parts.append(f"<p>{node.description}</p>")

            if node.metadata:
                html_parts.append(f"<small>{json.dumps(node.metadata, ensure_ascii=False)}</small>")

            html_parts.append("</div>")

            if i < len(chain.nodes) - 1:
                html_parts.append("<div class='arrow'>↓</div>")

        html_parts.extend(["</div>", "</body>", "</html>"])

        return "\n".join(html_parts)

    def _visualize_ascii(self, chain: DecisionChain) -> str:
        """ASCII格式可视化"""
        lines = [f"决策链: {chain.chain_id}"]
        lines.append("=" * 60)

        for i, node in enumerate(chain.nodes):
            # 节点框
            box_width = max(len(node.label) + 4, 30)
            lines.append("┌" + "─" * box_width + "┐")

            # 标签行
            label_line = f"│ {node.ljust(box_width - 2)} │"
            lines.append(
                label_line.replace(node.ljust(box_width - 2), node.label.ljust(box_width - 2))
            )

            # 置信度行
            if node.confidence > 0:
                conf_str = f"置信度: {node.confidence:.1%}"
                conf_line = f"│ {conf_str.ljust(box_width - 2)} │"
                lines.append(conf_line)

            lines.append("└" + "─" * box_width + "┘")

            # 连接箭头
            if i < len(chain.nodes) - 1:
                lines.append("       ↓")

        return "\n".join(lines)

    def get_chain(self, chain_id: str) -> DecisionChain | None:
        """获取决策链"""
        for chain in self.chains:
            if chain.chain_id == chain_id:
                return chain
        return None

    def get_all_chains(self) -> list[DecisionChain]:
        """获取所有决策链"""
        return self.chains.copy()


# 单例实例
_visualizer_instance: DecisionVisualizer | None = None


def get_decision_visualizer() -> DecisionVisualizer:
    """获取决策可视化器单例"""
    global _visualizer_instance
    if _visualizer_instance is None:
        _visualizer_instance = DecisionVisualizer()
        logger.info("决策可视化器已初始化")
    return _visualizer_instance


@async_main
async def main():
    """测试主函数"""
    visualizer = get_decision_visualizer()

    print("=== 决策可视化测试 ===\n")

    # 创建决策链
    chain = visualizer.create_chain("test_chain")

    # 添加节点
    visualizer.add_node(chain, NodeType.INPUT, "用户输入", "帮我查专利CN123456789A")

    visualizer.add_node(
        chain,
        NodeType.PROCESSING,
        "意图识别",
        "识别为专利分析意图",
        confidence=0.95,
        parent_id=chain.nodes[0].node_id,
    )

    visualizer.add_node(
        chain,
        NodeType.DECISION,
        "工具选择",
        "选择专利检索工具",
        confidence=0.9,
        parent_id=chain.nodes[1].node_id,
    )

    visualizer.add_node(
        chain,
        NodeType.PROCESSING,
        "参数提取",
        "提取专利号CN123456789A",
        confidence=0.98,
        parent_id=chain.nodes[2].node_id,
    )

    visualizer.add_node(
        chain, NodeType.OUTPUT, "输出结果", "返回专利信息", parent_id=chain.nodes[3].node_id
    )

    chain.end_time = datetime.now()

    # ASCII可视化
    print("ASCII格式:")
    print(visualizer.visualize(chain, VisualizationFormat.ASCII))

    # 文本可视化
    print("\n\n文本格式:")
    print(visualizer.visualize(chain, VisualizationFormat.TEXT))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
