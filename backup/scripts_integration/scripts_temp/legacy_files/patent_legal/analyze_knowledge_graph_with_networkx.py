#!/usr/bin/env python3
"""
使用NetworkX分析专利法律法规知识图谱
Analyze Patent Legal Knowledge Graph with NetworkX

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import os
import json
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path
import networkx as nx
import numpy as np
from collections import Counter

# 尝试导入matplotlib
try:
    import matplotlib.pyplot as plt
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️ matplotlib未安装，将跳过可视化部分")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentLegalKGAnalyzer:
    """专利法律法规知识图谱NetworkX分析器"""

    def __init__(self):
        """初始化"""
        self.graph = nx.DiGraph()
        self.entities = {}
        self.relationships = []
        self.data_dir = Path("/Users/xujian/Athena工作平台/data/patent_legal_kg_simple")

    def load_knowledge_graph(self):
        """加载知识图谱数据"""
        logger.info("加载知识图谱数据...")

        # 加载实体
        entities_path = self.data_dir / "entities.json"
        if entities_path.exists():
            with open(entities_path, 'r', encoding='utf-8') as f:
                self.entities = json.load(f)
            logger.info(f"加载了 {len(self.entities)} 个实体")
        else:
            logger.error(f"实体文件不存在: {entities_path}")
            return False

        # 加载关系
        relationships_path = self.data_dir / "relationships.json"
        if relationships_path.exists():
            with open(relationships_path, 'r', encoding='utf-8') as f:
                self.relationships = json.load(f)
            logger.info(f"加载了 {len(self.relationships)} 个关系")
        else:
            logger.error(f"关系文件不存在: {relationships_path}")
            return False

        # 构建NetworkX图
        self._build_networkx_graph()
        return True

    def _build_networkx_graph(self):
        """构建NetworkX图"""
        # 添加节点
        for entity_id, entity in self.entities.items():
            self.graph.add_node(
                entity_id,
                name=entity.get('name', ''),
                type=entity.get('type', ''),
                description=entity.get('description', ''),
                **entity.get('properties', {})
            )

        # 添加边
        for rel in self.relationships:
            self.graph.add_edge(
                rel.get('source'),
                rel.get('target'),
                type=rel.get('type', ''),
                description=rel.get('description', ''),
                **rel.get('properties', {})
            )

        logger.info(f"构建NetworkX图: {self.graph.number_of_nodes()} 个节点, {self.graph.number_of_edges()} 条边")

    def analyze_graph_structure(self):
        """分析图结构"""
        logger.info("\n=== 图结构分析 ===")

        # 基本统计
        print(f"节点数量: {self.graph.number_of_nodes()}")
        print(f"边数量: {self.graph.number_of_edges()}")
        print(f"图类型: {'有向图' if self.graph.is_directed() else '无向图'}")
        print(f"是否连通: {nx.is_weakly_connected(self.graph)}")

        # 密度
        density = nx.density(self.graph)
        print(f"图密度: {density:.4f}")

        # 连通分量
        if self.graph.is_directed():
            weakly_connected = nx.number_weakly_connected_components(self.graph)
            strongly_connected = nx.number_strongly_connected_components(self.graph)
            print(f"弱连通分量数: {weakly_connected}")
            print(f"强连通分量数: {strongly_connected}")
        else:
            connected_components = nx.number_connected_components(self.graph)
            print(f"连通分量数: {connected_components}")

    def analyze_node_types(self):
        """分析节点类型分布"""
        logger.info("\n=== 节点类型分布 ===")

        type_counts = Counter()
        for node in self.graph.nodes(data=True):
            node_type = node[1].get('type', 'unknown')
            type_counts[node_type] += 1

        print("\n节点类型统计:")
        for node_type, count in type_counts.most_common():
            print(f"  {node_type}: {count} 个")

        return type_counts

    def analyze_relationship_types(self):
        """分析关系类型分布"""
        logger.info("\n=== 关系类型分布 ===")

        rel_counts = Counter()
        for u, v, data in self.graph.edges(data=True):
            rel_type = data.get('type', 'unknown')
            rel_counts[rel_type] += 1

        print("\n关系类型统计:")
        for rel_type, count in rel_counts.most_common():
            print(f"  {rel_type}: {count} 条")

        return rel_counts

    def find_important_nodes(self):
        """找出重要节点"""
        logger.info("\n=== 重要节点分析 ===")

        # 计算中心性指标
        in_degree = dict(self.graph.in_degree())
        out_degree = dict(self.graph.out_degree())

        # PageRank
        pagerank = nx.pagerank(self.graph)

        # betweenness centrality
        betweenness = nx.betweenness_centrality(self.graph)

        # 整理结果
        important_nodes = []
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            important_nodes.append({
                'id': node_id,
                'name': node_data.get('name', ''),
                'type': node_data.get('type', ''),
                'in_degree': in_degree.get(node_id, 0),
                'out_degree': out_degree.get(node_id, 0),
                'pagerank': pagerank.get(node_id, 0),
                'betweenness': betweenness.get(node_id, 0)
            })

        # 排序并展示
        print("\n入度最高的节点:")
        for node in sorted(important_nodes, key=lambda x: x['in_degree'], reverse=True)[:5]:
            print(f"  {node['name']} ({node['type']}): {node['in_degree']}")

        print("\n出度最高的节点:")
        for node in sorted(important_nodes, key=lambda x: x['out_degree'], reverse=True)[:5]:
            print(f"  {node['name']} ({node['type']}): {node['out_degree']}")

        print("\nPageRank最高的节点:")
        for node in sorted(important_nodes, key=lambda x: x['pagerank'], reverse=True)[:5]:
            print(f"  {node['name']} ({node['type']}): {node['pagerank']:.4f}")

        return important_nodes

    def find_patterns(self):
        """发现图中的模式"""
        logger.info("\n=== 模式发现 ===")

        # 找出三角形
        triangles = list(nx.cycle_basis(self.graph.to_undirected()))
        print(f"\n三角形数量: {len(triangles)}")

        # 找出最长路径
        try:
            longest_path = max(nx.all_simple_paths(self.graph,
                                                  source=list(self.graph.nodes())[0],
                                                  target=list(self.graph.nodes())[-1]),
                             key=len)
            print(f"\n最长路径长度: {len(longest_path)-1}")
        except:
            print("\n无法计算最长路径（图可能不连通）")

        # 找出hub节点（高度连接的节点）
        degree_centrality = nx.degree_centrality(self.graph)
        hubs = [node for node, centrality in degree_centrality.items() if centrality > 0.5]
        print(f"\nHub节点数量: {len(hubs)}")
        for hub in hubs[:3]:
            print(f"  - {self.graph.nodes[hub].get('name', hub)}")

    def visualize_graph(self, save_path: str = None, max_nodes: int = 50):
        """可视化知识图谱"""
        if not HAS_MATPLOTLIB:
            logger.warning("matplotlib未安装，无法可视化")
            return

        logger.info("\n=== 图谱可视化 ===")

        # 如果节点太多，只显示最重要的节点
        if self.graph.number_of_nodes() > max_nodes:
            # 使用PageRank选择最重要的节点
            pagerank = nx.pagerank(self.graph)
            top_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
            top_node_ids = [node[0] for node in top_nodes]

            # 创建子图
            subgraph = self.graph.subgraph(top_node_ids)
        else:
            subgraph = self.graph

        # 设置画布
        plt.figure(figsize=(15, 12))

        # 选择布局
        if subgraph.number_of_nodes() < 20:
            pos = nx.spring_layout(subgraph, k=2, iterations=50)
        else:
            pos = nx.spring_layout(subgraph, k=1, iterations=50)

        # 节点颜色映射
        node_colors = []
        color_map = {
            'law': '#FF6B6B',        # 红色
            'regulation': '#4ECDC4', # 青色
            'concept': '#45B7D1',    # 蓝色
            'article': '#96CEB4',    # 浅绿色
            'procedure': '#FFEAA7',  # 黄色
            'case': '#DDA0DD',       # 紫色
            'unknown': '#95A5A6'     # 灰色
        }

        for node in subgraph.nodes():
            node_type = subgraph.nodes[node].get('type', 'unknown')
            node_colors.append(color_map.get(node_type, color_map['unknown']))

        # 绘制节点
        nx.draw_networkx_nodes(subgraph, pos,
                              node_color=node_colors,
                              node_size=500,
                              alpha=0.8)

        # 绘制边
        nx.draw_networkx_edges(subgraph, pos,
                              alpha=0.3,
                              width=1,
                              edge_color='gray',
                              arrows=True,
                              arrowsize=20)

        # 绘制标签
        labels = {node: subgraph.nodes[node].get('name', node)[:10]
                 for node in subgraph.nodes()}
        nx.draw_networkx_labels(subgraph, pos, labels, font_size=8)

        # 添加图例
        legend_elements = []
        for node_type, color in color_map.items():
            if node_type != 'unknown':
                count = sum(1 for n in subgraph.nodes()
                          if subgraph.nodes[n].get('type', 'unknown') == node_type)
                if count > 0:
                    legend_elements.append(plt.Line2D([0], [0], marker='o', color='w',
                                                    markerfacecolor=color,
                                                    label=f'{node_type} ({count})',
                                                    markersize=10))
        plt.legend(handles=legend_elements, loc='upper right')

        plt.title("专利法律法规知识图谱", fontsize=16)
        plt.axis('off')

        # 保存或显示
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"图谱已保存到: {save_path}")
        else:
            plt.show()

    def export_analysis_report(self, output_path: str):
        """导出分析报告"""
        logger.info("\n=== 导出分析报告 ===")

        report = {
            "timestamp": "2024-12-15",
            "graph_statistics": {
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges(),
                "density": nx.density(self.graph),
                "is_connected": nx.is_weakly_connected(self.graph)
            },
            "node_types": list(dict(nx.get_node_attributes(self.graph, 'type')).values()),
            "edge_types": [data.get('type', 'unknown') for _, _, data in self.graph.edges(data=True)],
            "important_nodes": self.find_important_nodes()[:10]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"分析报告已保存到: {output_path}")

def main():
    """主函数"""
    logger.info("开始使用NetworkX分析专利法律法规知识图谱...")

    # 创建分析器
    analyzer = PatentLegalKGAnalyzer()

    # 加载知识图谱
    if not analyzer.load_knowledge_graph():
        logger.error("加载知识图谱失败")
        return

    # 执行分析
    analyzer.analyze_graph_structure()
    node_types = analyzer.analyze_node_types()
    rel_types = analyzer.analyze_relationship_types()
    important_nodes = analyzer.find_important_nodes()
    analyzer.find_patterns()

    # 可视化
    output_dir = Path("/Users/xujian/Athena工作平台/data/patent_legal_kg_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存可视化图片
    viz_path = output_dir / "knowledge_graph_visualization.png"
    analyzer.visualize_graph(save_path=str(viz_path))

    # 导出分析报告
    report_path = output_dir / "analysis_report.json"
    analyzer.export_analysis_report(str(report_path))

    logger.info("\n✅ NetworkX分析完成！")
    logger.info(f"\n输出文件:")
    logger.info(f"  可视化图片: {viz_path}")
    logger.info(f"  分析报告: {report_path}")

if __name__ == "__main__":
    main()