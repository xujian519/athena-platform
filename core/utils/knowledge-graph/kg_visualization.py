#!/usr/bin/env python3
from __future__ import annotations
"""
Athena知识图谱可视化工具
Knowledge Graph Visualization Tool

提供基础的知识图谱可视化和分析功能

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import matplotlib.pyplot as plt
    import networkx as nx
    from matplotlib.patches import Patch
    from neo4j import GraphDatabase
    VISUALIZATION_AVAILABLE = True
except ImportError:
    logger.info('⚠️ 可视化依赖未安装，请运行: pip install matplotlib networkx neo4j')
    VISUALIZATION_AVAILABLE = False

class KnowledgeGraphVisualizer:
    """知识图谱可视化器"""

    def __init__(self):
        self.driver = None
        if VISUALIZATION_AVAILABLE:
            self.setup_neo4j()
            # 设置中文字体支持
            plt.rc_params['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Arial']
            plt.rc_params['axes.unicode_minus'] = False

    def setup_neo4j(self) -> Any:
        """设置Neo4j连接"""
        try:
            self.driver = GraphDatabase.driver(
                'bolt://localhost:7687',
                auth=('neo4j', 'password')
            )
            logger.info('✅ Neo4j连接成功')
        except Exception as e:
            logger.info(f"❌ Neo4j连接失败: {str(e)}")
            self.driver = None

    def get_graph_data(self, limit: int = 50) -> tuple[list[dict], list[dict]]:
        """获取图数据"""
        if not self.driver:
            return [], []

        nodes = []
        edges = []

        with self.driver.session() as session:
            # 获取节点
            node_query = """
            MATCH (n)
            RETURN n.id as id,
                   labels(n) as labels,
                   n.title as title,
                   n.name as name
            LIMIT $limit
            """
            node_result = session.run(node_query, limit=limit)

            for record in node_result:
                node_id = record['id']
                labels = record['labels']
                title = record.get('title', '')
                name = record.get('name', '')

                # 确定节点显示名称
                display_name = title or name or str(node_id)

                # 确定节点类型和颜色
                node_type = labels[0] if labels else 'Unknown'
                color = self.get_node_color(node_type)

                nodes.append({
                    'id': node_id,
                    'label': display_name,
                    'type': node_type,
                    'color': color
                })

            # 获取边
            edge_query = """
            MATCH (n1)-[r]->(n2)
            RETURN n1.id as source,
                   n2.id as target,
                   type(r) as relationship,
                   r.weight as weight
            LIMIT $limit
            """
            edge_result = session.run(edge_query, limit=limit)

            for record in edge_result:
                edges.append({
                    'source': record['source'],
                    'target': record['target'],
                    'label': record['relationship'],
                    'weight': record.get('weight', 1)
                })

        return nodes, edges

    def get_node_color(self, node_type: str) -> str:
        """获取节点颜色"""
        color_map = {
            'Patent': '#FF6B6B',      # 红色
            'Technology': '#4ECDC4',  # 青色
            'Law': '#45B7D1',        # 蓝色
            'Article': '#96CEB4',    # 浅绿色
            'Company': '#FFEAA7',    # 黄色
            'Inventor': '#DDA0DD',   # 紫色
            'Keyword': '#F8B500',    # 橙色
            'Case': '#FF7675'        # 浅红色
        }
        return color_map.get(node_type, '#95A5A6')  # 默认灰色

    def create_networkx_graph(self, nodes: list[dict], edges: list[dict]) -> nx.Graph:
        """创建NetworkX图"""
        G = nx.Graph()

        # 添加节点
        for node in nodes:
            G.add_node(node['id'],
                        label=node['label'],
                        color=node['color'],
                        type=node['type'])

        # 添加边
        for edge in edges:
            G.add_edge(edge['source'], edge['target'],
                      label=edge['label'],
                      weight=edge['weight'])

        return G

    def visualize_basic_graph(self, nodes: list[dict], edges: list[dict],
                              title: str = 'Athena知识图谱', save_path: str = None):
        """基础图可视化"""
        if not VISUALIZATION_AVAILABLE:
            logger.info('❌ 可视化库未安装')
            return

        # 创建图
        G = self.create_networkx_graph(nodes, edges)

        # 创建可视化
        plt.figure(figsize=(15, 10))
        pos = nx.spring_layout(G, k=1, iterations=50)

        # 绘制节点
        node_colors = [G.nodes[node]['color'] for node in G.nodes()]
        nx.draw_networkx_nodes(G, pos,
                             node_color=node_colors,
                             node_size=300,
                             alpha=0.8)

        # 绘制边
        nx.draw_networkx_edges(G, pos,
                             alpha=0.6,
                             width=1)

        # 绘制标签
        labels = nx.get_node_attributes(G, 'label')
        nx.draw_networkx_labels(G, pos, labels, font_size=8)

        plt.title(title, fontsize=16, fontweight='bold')
        plt.axis('off')

        # 创建图例
        node_types = {G.nodes[node]['type'] for node in G.nodes()}
        legend_elements = []
        for node_type in node_types:
            color = self.get_node_color(node_type)
            legend_elements.append(Patch(facecolor=color, label=node_type))

        plt.legend(handles=legend_elements, loc='upper right')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"✅ 图谱可视化已保存到: {save_path}")

        plt.show()

    def analyze_graph_statistics(self, nodes: list[dict], edges: list[dict]) -> dict[str, Any]:
        """分析图统计信息"""
        G = self.create_networkx_graph(nodes, edges)

        # 基础统计
        stats = {
            'total_nodes': G.number_of_nodes(),
            'total_edges': G.number_of_edges(),
            'density': nx.density(G),
            'is_connected': nx.is_connected(G),
            'node_types': {},
            'edge_types': {}
        }

        # 节点类型统计
        for node in G.nodes():
            node_type = G.nodes[node]['type']
            stats['node_types'][node_type] = stats['node_types'].get(node_type, 0) + 1

        # 边类型统计
        for edge in G.edges():
            edge_label = G.edges[edge]['label']
            stats['edge_types'][edge_label] = stats['edge_types'].get(edge_label, 0) + 1

        # 图的连通性
        if G.number_of_nodes() > 0:
            stats['average_degree'] = sum(dict(G.degree()).values()) / G.number_of_nodes()
            stats['clustering_coefficient'] = nx.average_clustering(G)
        else:
            stats['average_degree'] = 0
            stats['clustering_coefficient'] = 0

        return stats

    def generate_patent_technology_network(self, save_path: str = None) -> Any:
        """生成专利技术关系网络图"""
        if not self.driver:
            logger.info('❌ Neo4j未连接')
            return

        logger.info('🔍 分析专利技术关系网络...')

        with self.driver.session() as session:
            # 获取专利和技术关系数据
            query = """
            MATCH (p:Patent)-[:USES_TECHNOLOGY]->(t:Technology)
            OPTIONAL MATCH (p)-[:ASSIGNED_TO]->(c:Company)
            RETURN p.id as patent_id,
                   p.title as patent_title,
                   t.name as technology,
                   t.category as tech_category,
                   c.name as company
            LIMIT 30
            """

            result = session.run(query)

            patents = []
            technologies = []
            relationships = []

            for record in result:
                patent_id = record['patent_id']
                patent_title = record['patent_title']
                technology = record['technology']
                record['tech_category']
                record.get('company', '')

                # 添加专利节点
                if not any(p['id'] == patent_id for p in patents):
                    patents.append({
                        'id': patent_id,
                        'label': patent_title[:20] + '...',
                        'type': 'Patent',
                        'color': '#FF6B6B'
                    })

                # 添加技术节点
                if not any(t['id'] == technology for t in technologies):
                    technologies.append({
                        'id': technology,
                        'label': technology,
                        'type': 'Technology',
                        'color': '#4ECDC4'
                    })

                # 添加关系
                relationships.append({
                    'source': patent_id,
                    'target': technology,
                    'label': 'USES',
                    'weight': 1
                })

        # 合并节点
        all_nodes = patents + technologies

        # 创建可视化
        logger.info(f"📊 找到 {len(patents)} 个专利和 {len(technologies)} 个技术")
        logger.info(f"🔗 {len(relationships)} 个使用关系")

        self.visualize_basic_graph(
            all_nodes,
            relationships,
            title='专利技术关系网络图',
            save_path=save_path or '/Users/xujian/Athena工作平台/patent_tech_network.png'
        )

    def generate_legal_relationship_network(self, save_path: str = None) -> Any:
        """生成法律关系网络图"""
        if not self.driver:
            logger.info('❌ Neo4j未连接')
            return

        logger.info('⚖️ 分析法律关系网络...')

        with self.driver.session() as session:
            # 获取法律关系数据
            query = """
            MATCH (l:Law)
            OPTIONAL MATCH (l)-[:HAS_ARTICLE]->(a:Article)
            OPTIONAL MATCH (c:Case)-[:REFERENCES]->(l)
            RETURN l.id as law_id,
                   l.name as law_name,
                   l.year as law_year,
                   a.number as article_number,
                   c.name as case_name,
                   c.court as court
            LIMIT 20
            """

            result = session.run(query)

            laws = []
            articles = []
            cases = []
            relationships = []

            for record in result:
                law_id = record['law_id']
                law_name = record['law_name']
                article_number = record.get('article_number')
                case_name = record.get('case_name')

                # 添加法律节点
                if not any(l['id'] == law_id for l in laws):
                    laws.append({
                        'id': law_id,
                        'label': law_name[:15] + '...',
                        'type': 'Law',
                        'color': '#45B7D1'
                    })

                # 添加法条节点
                if article_number and not any(a['id'] == article_number for a in articles):
                    articles.append({
                        'id': article_number,
                        'label': article_number,
                        'type': 'Article',
                        'color': '#96CEB4'
                    })

                    # 添加法律-法条关系
                    relationships.append({
                        'source': law_id,
                        'target': article_number,
                        'label': 'HAS_ARTICLE',
                        'weight': 1
                    })

                # 添加案例节点
                if case_name and not any(c['id'] == case_name for c in cases):
                    cases.append({
                        'id': case_name,
                        'label': case_name[:15] + '...',
                        'type': 'Case',
                        'color': '#FF7675'
                    })

                    # 添加案例-法律关系
                    relationships.append({
                        'source': case_name,
                        'target': law_id,
                        'label': 'REFERENCES',
                        'weight': 1
                    })

        # 合并节点
        all_nodes = laws + articles + cases

        # 创建可视化
        logger.info(f"📊 找到 {len(laws)} 部法律、{len(articles)} 条法条、{len(cases)} 个案例")
        logger.info(f"🔗 {len(relationships)} 个关系")

        self.visualize_basic_graph(
            all_nodes,
            relationships,
            title='法律关系网络图',
            save_path=save_path or '/Users/xujian/Athena工作平台/legal_network.png'
        )

    def generate_interactive_report(self) -> Any:
        """生成交互式分析报告"""
        logger.info('📈 生成知识图谱分析报告...')

        # 获取图数据
        nodes, edges = self.get_graph_data(limit=100)

        if not nodes:
            logger.info('❌ 没有找到知识图谱数据')
            return

        # 分析统计
        stats = self.analyze_graph_statistics(nodes, edges)

        logger.info("\n📊 知识图谱统计报告")
        logger.info(str('=' * 50))
        logger.info(f"总节点数: {stats['total_nodes']}")
        logger.info(f"总关系数: {stats['total_edges']}")
        logger.info(f"图密度: {stats['density']:.4f}")
        logger.info(f"连通性: {'是' if stats['is_connected'] else '否'}")
        logger.info(f"平均度数: {stats['average_degree']:.2f}")
        logger.info(f"聚类系数: {stats['clustering_coefficient']:.4f}")

        logger.info("\n🏷️ 节点类型分布:")
        total_nodes = sum(stats['node_types'].values())
        for node_type, count in stats['node_types'].items():
            percentage = (count / total_nodes) * 100
            logger.info(f"  {node_type}: {count} ({percentage:.1f}%)")

        logger.info("\n🔗 关系类型分布:")
        total_edges = sum(stats['edge_types'].values())
        for edge_type, count in stats['edge_types'].items():
            percentage = (count / total_edges) * 100
            logger.info(f"  {edge_type}: {count} ({percentage:.1f}%)")

        # 生成可视化
        logger.info("\n🎨 生成网络可视化...")
        self.visualize_basic_graph(
            nodes, edges,
            title='Athena知识图谱完整视图',
            save_path='/Users/xujian/Athena工作平台/knowledge_graph_overview.png'
        )

        # 保存报告
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': stats,
            'node_count': len(nodes),
            'edge_count': len(edges),
            'visualizations': [
                '/Users/xujian/Athena工作平台/knowledge_graph_overview.png'
            ]
        }

        with open('/Users/xujian/Athena工作平台/kg_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info("\n💾 分析报告已保存到: /Users/xujian/Athena工作平台/kg_analysis_report.json")

def main() -> None:
    """主函数"""
    visualizer = KnowledgeGraphVisualizer()

    if not VISUALIZATION_AVAILABLE:
        logger.info('请先安装可视化依赖:')
        logger.info('pip install matplotlib networkx')
        return

    logger.info('🚀 Athena知识图谱可视化分析')
    logger.info(str('=' * 60))

    # 生成专利技术网络图
    logger.info("\n1. 生成专利技术关系网络")
    visualizer.generate_patent_technology_network()

    # 生成法律关系网络图
    logger.info("\n2. 生成法律关系网络")
    visualizer.generate_legal_relationship_network()

    # 生成完整分析报告
    logger.info("\n3. 生成完整分析报告")
    visualizer.generate_interactive_report()

    logger.info("\n✅ 知识图谱可视化分析完成！")
    logger.info("\n📁 生成的文件:")
    logger.info('  - /Users/xujian/Athena工作平台/patent_tech_network.png')
    logger.info('  - /Users/xujian/Athena工作平台/legal_network.png')
    logger.info('  - /Users/xujian/Athena工作平台/knowledge_graph_overview.png')
    logger.info('  - /Users/xujian/Athena工作平台/kg_analysis_report.json')

if __name__ == '__main__':
    main()
