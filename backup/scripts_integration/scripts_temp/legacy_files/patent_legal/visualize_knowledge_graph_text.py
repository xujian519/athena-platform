#!/usr/bin/env python3
"""
文字可视化专利法律法规知识图谱
Text-based Visualization of Patent Legal Knowledge Graph

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import json
import logging
from typing import Dict, List, Any
from pathlib import Path
import networkx as nx

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeGraphTextVisualizer:
    """知识图谱文字可视化器"""

    def __init__(self):
        """初始化"""
        self.graph = nx.DiGraph()
        self.data_dir = Path("/Users/xujian/Athena工作平台/data/patent_legal_kg_simple")

    def load_graph(self):
        """加载知识图谱"""
        # 加载NetworkX图
        graph_path = self.data_dir / "knowledge_graph.graphml"
        if graph_path.exists():
            self.graph = nx.read_graphml(graph_path)
            logger.info(f"从GraphML加载图: {self.graph.number_of_nodes()} 个节点, {self.graph.number_of_edges()} 条边")
            return True
        else:
            # 从JSON构建
            entities_path = self.data_dir / "entities.json"
            relationships_path = self.data_dir / "relationships.json"

            with open(entities_path, 'r', encoding='utf-8') as f:
                entities = json.load(f)
            with open(relationships_path, 'r', encoding='utf-8') as f:
                relationships = json.load(f)

            # 构建图
            for entity_id, entity in entities.items():
                self.graph.add_node(
                    entity_id,
                    name=entity.get('name', ''),
                    type=entity.get('type', ''),
                    description=entity.get('description', '')[:100]
                )

            for rel in relationships:
                self.graph.add_edge(
                    rel.get('source'),
                    rel.get('target'),
                    type=rel.get('type', ''),
                    description=rel.get('description', '')
                )

            logger.info(f"从JSON构建图: {self.graph.number_of_nodes()} 个节点, {self.graph.number_of_edges()} 条边")
            return True

    def generate_ascii_graph(self, max_nodes: int = 20):
        """生成ASCII艺术图"""
        print("\n" + "="*80)
        print("📊 专利法律法规知识图谱 (可视化)")
        print("="*80)

        # 选择重要节点
        pagerank = nx.pagerank(self.graph)
        top_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
        top_node_ids = [node[0] for node in top_nodes]

        # 创建子图
        subgraph = self.graph.subgraph(top_node_ids)

        # 打印节点列表
        print("\n📝 核心节点列表:")
        print("-"*40)
        for i, node_id in enumerate(top_node_ids[:10]):
            node_data = subgraph.nodes[node_id]
            icon = self._get_type_icon(node_data.get('type', ''))
            print(f"{i+1:2d}. {icon} {node_data.get('name', node_id)[:30]} ({node_data.get('type', '')})")

        # 打印关系结构
        print("\n🔗 关系结构:")
        print("-"*40)
        count = 0
        for u, v, data in subgraph.edges(data=True):
            if count >= 15:  # 限制显示数量
                break
            u_name = subgraph.nodes[u].get('name', u)[:20]
            v_name = subgraph.nodes[v].get('name', v)[:20]
            rel_type = data.get('type', 'relates')
            print(f"   {u_name} ──[{rel_type}]──> {v_name}")
            count += 1

        # 打印统计信息
        print("\n📈 图谱统计:")
        print("-"*40)
        print(f"   总节点数: {self.graph.number_of_nodes()}")
        print(f"   总关系数: {self.graph.number_of_edges()}")
        print(f"   连通性: {'是' if nx.is_weakly_connected(self.graph) else '否'}")
        print(f"   图密度: {nx.density(self.graph):.4f}")

    def _get_type_icon(self, node_type: str) -> str:
        """获取节点类型图标"""
        icons = {
            'law': '⚖️',      # 法律
            'regulation': '📋',  # 法规
            'article': '📄',     # 条款
            'concept': '💡',     # 概念
            'procedure': '🔄',   # 程序
            'case': '🏛️'        # 案例
        }
        return icons.get(node_type, '📌')

    def generate_node_details(self):
        """生成节点详细信息"""
        print("\n" + "="*80)
        print("📋 节点详细信息")
        print("="*80)

        # 按类型分组
        type_groups = {}
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            if node_type not in type_groups:
                type_groups[node_type] = []
            type_groups[node_type].append((node_id, data))

        # 打印每种类型的节点
        for node_type, nodes in sorted(type_groups.items()):
            icon = self._get_type_icon(node_type)
            print(f"\n{icon} {node_type.upper()} ({len(nodes)}个):")
            print("-"*40)
            for node_id, data in nodes[:5]:  # 每种类型最多显示5个
                name = data.get('name', 'Unknown')
                desc = data.get('description', '')
                if desc:
                    desc = desc[:80] + "..." if len(desc) > 80 else desc
                    print(f"   • {name}")
                    print(f"     {desc}")
                else:
                    print(f"   • {name}")
            if len(nodes) > 5:
                print(f"   ... 还有{len(nodes)-5}个节点")

    def generate_relationship_analysis(self):
        """生成关系分析"""
        print("\n" + "="*80)
        print("🔗 关系分析")
        print("="*80)

        # 统计关系类型
        rel_counts = {}
        rel_examples = {}
        for u, v, data in self.graph.edges(data=True):
            rel_type = data.get('type', 'unknown')
            rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1
            if rel_type not in rel_examples and len(rel_examples) < 20:
                u_name = self.graph.nodes[u].get('name', u)[:20]
                v_name = self.graph.nodes[v].get('name', v)[:20]
                rel_examples[rel_type] = f"{u_name} → {v_name}"

        print("\n关系类型统计:")
        print("-"*40)
        for rel_type, count in sorted(rel_counts.items(), key=lambda x: x[1], reverse=True):
            example = rel_examples.get(rel_type, '')
            print(f"   {rel_type}: {count}条")
            if example:
                print(f"     例: {example}")

    def generate_path_analysis(self):
        """生成路径分析"""
        print("\n" + "="*80)
        print("🛤️ 路径分析")
        print("="*80)

        # 找出入度和出度最高的节点
        in_degrees = dict(self.graph.in_degree())
        out_degrees = dict(self.graph.out_degree())

        print("\n📥 入度最高的节点 (被引用最多):")
        print("-"*40)
        for node_id, degree in sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]:
            name = self.graph.nodes[node_id].get('name', node_id)
            print(f"   {name}: {degree}")

        print("\n📤 出度最高的节点 (引用其他最多):")
        print("-"*40)
        for node_id, degree in sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:5]:
            name = self.graph.nodes[node_id].get('name', node_id)
            print(f"   {name}: {degree}")

        # 找出hub节点
        degree_centrality = nx.degree_centrality(self.graph)
        hubs = [(node, centrality) for node, centrality in degree_centrality.items() if centrality > 0.3]
        hubs.sort(key=lambda x: x[1], reverse=True)

        if hubs:
            print("\n🌟 Hub节点 (高度连接):")
            print("-"*40)
            for node_id, centrality in hubs[:5]:
                name = self.graph.nodes[node_id].get('name', node_id)
                node_type = self.graph.nodes[node_id].get('type', '')
                print(f"   {name} ({node_type}): {centrality:.3f}")

    def save_text_visualization(self, output_path: str):
        """保存文字可视化结果"""
        with open(output_path, 'w', encoding='utf-8') as f:
            import sys
            from io import StringIO

            # 重定向输出到文件
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()

            # 生成可视化
            self.generate_ascii_graph()
            self.generate_node_details()
            self.generate_relationship_analysis()
            self.generate_path_analysis()

            # 恢复输出
            sys.stdout = old_stdout

            # 写入文件
            content = mystdout.getvalue()
            f.write(content)

        logger.info(f"文字可视化已保存到: {output_path}")

    def interactive_explore(self):
        """交互式探索"""
        print("\n" + "="*80)
        print("🔍 交互式探索模式")
        print("="*80)
        print("输入节点名称进行探索 (输入 'quit' 退出)")

        # 创建名称到ID的映射
        name_to_id = {}
        for node_id, data in self.graph.nodes(data=True):
            name = data.get('name', '')
            if name:
                name_to_id[name.lower()] = node_id

        while True:
            query = input("\n请输入节点名称: ").strip()
            if query.lower() == 'quit':
                break

            # 查找匹配的节点
            matches = []
            for name, node_id in name_to_id.items():
                if query.lower() in name:
                    matches.append((node_id, name))

            if not matches:
                print(f"未找到包含 '{query}' 的节点")
                continue

            # 显示匹配结果
            print(f"\n找到 {len(matches)} 个匹配的节点:")
            for i, (node_id, name) in enumerate(matches[:5]):
                print(f"  {i+1}. {name}")

            # 选择第一个匹配项进行展示
            if matches:
                node_id, name = matches[0]
                self._show_node_details(node_id)

    def _show_node_details(self, node_id: str):
        """显示节点详细信息"""
        data = self.graph.nodes[node_id]
        print(f"\n📌 节点详情: {data.get('name', 'Unknown')}")
        print("-"*40)
        print(f"类型: {data.get('type', 'Unknown')}")
        desc = data.get('description', '')
        if desc:
            print(f"描述: {desc[:200]}...")

        # 显示关系
        print("\n传入关系:")
        in_edges = list(self.graph.in_edges(node_id, data=True))
        for u, v, data in in_edges[:5]:
            u_name = self.graph.nodes[u].get('name', u)
            rel_type = data.get('type', 'relates')
            print(f"  ←[{rel_type}] {u_name}")

        print("\n传出关系:")
        out_edges = list(self.graph.out_edges(node_id, data=True))
        for u, v, data in out_edges[:5]:
            v_name = self.graph.nodes[v].get('name', v)
            rel_type = data.get('type', 'relates')
            print(f"  [{rel_type}]→ {v_name}")

def main():
    """主函数"""
    logger.info("开始文字可视化专利法律法规知识图谱...")

    # 创建可视化器
    visualizer = KnowledgeGraphTextVisualizer()

    # 加载图谱
    if not visualizer.load_graph():
        logger.error("加载知识图谱失败")
        return

    # 生成可视化
    visualizer.generate_ascii_graph()
    visualizer.generate_node_details()
    visualizer.generate_relationship_analysis()
    visualizer.generate_path_analysis()

    # 保存结果
    output_dir = Path("/Users/xujian/Athena工作平台/data/patent_legal_kg_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "text_visualization.txt"

    visualizer.save_text_visualization(str(output_path))

    print("\n" + "="*80)
    print("✅ 文字可视化完成！")
    print(f"📄 详细报告已保存到: {output_path}")
    print("="*80)

    # 交互式探索（可选）
    try:
        response = input("\n是否进入交互式探索模式？(y/n): ").strip().lower()
        if response == 'y':
            visualizer.interactive_explore()
    except KeyboardInterrupt:
        print("\n退出探索模式")

if __name__ == "__main__":
    main()