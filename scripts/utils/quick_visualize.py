#!/usr/bin/env python3
"""
简化版知识图谱可视化 - 使用pyvis生成HTML
无需Web服务器，直接生成HTML文件
"""

import logging

from neo4j import GraphDatabase
from pyvis.network import Network

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j连接
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "athena_neo4j_2024")


def create_sample_visualization():
    """创建样本可视化"""

    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    try:
        logger.info("🔍 从Neo4j获取样本数据...")

        with driver.session() as session:
            # 查询样本数据
            query = """
            MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT 50
            """

            result = session.run(query)

            # 创建网络
            net = Network(
                height="750px",
                width="100%",
                bgcolor="#1a1a2e",
                font_color="white",
                directed=True,
                heading="Athena知识图谱 - 样本数据（50个节点）"
            )

            # 配置物理引擎
            net.set_options("""
            {
              "nodes": {
                "borderWidth": 2,
                "size": 20
              },
              "edges": {
                "width": 1,
                "smooth": true,
                "arrows": {
                  "to": {
                    "enabled": true,
                    "scaleFactor": 0.3
                  }
                }
              },
              "physics": {
                "forceAtlas2Based": {
                  "gravitationalConstant": -30,
                  "centralGravity": 0.01,
                  "springLength": 150,
                  "springConstant": 0.05
                },
                "maxVelocity": 50,
                "solver": "forceAtlas2Based",
                "timestep": 0.5
              }
            }
            """)

            nodes = {}
            edges = []

            for record in result:
                # 处理起始节点
                start_node = record['n']
                start_id = str(start_node.element_id)

                if start_id not in nodes:
                    labels = list(start_node.labels) if hasattr(start_node, 'labels') else ['Unknown']
                    label = labels[0] if labels else 'Unknown'

                    # 提取显示标签
                    if hasattr(start_node, 'text') and start_node.text:
                        display_label = str(start_node.text)[:25]
                    elif hasattr(start_node, 'title') and start_node.title:
                        display_label = str(start_node.title)[:25]
                    elif hasattr(start_node, 'id') and start_node.id:
                        display_label = str(start_node.id)[:25]
                    else:
                        display_label = f"{label[:10]}..."

                    # 设置颜色
                    if label == "Entity":
                        color = "#667eea"
                        title = f"Entity\\n类型: {start_node.get('type', 'N/A')}"
                    elif label == "OpenClawNode":
                        color = "#f093fb"
                        title = f"OpenClawNode\\nID: {start_node.get('_original_id', start_node.get('id', 'N/A'))}"
                    else:
                        color = "#ffd93d"
                        title = label

                    nodes[start_id] = {
                        'id': start_id,
                        'label': display_label,
                        'title': title,
                        'color': color
                    }

                # 处理结束节点
                end_node = record['m']
                end_id = str(end_node.element_id)

                if end_id not in nodes:
                    labels = list(end_node.labels) if hasattr(end_node, 'labels') else ['Unknown']
                    label = labels[0] if labels else 'Unknown'

                    # 提取显示标签
                    if hasattr(end_node, 'text') and end_node.text:
                        display_label = str(end_node.text)[:25]
                    elif hasattr(end_node, 'title') and end_node.title:
                        display_label = str(end_node.title)[:25]
                    elif hasattr(end_node, 'id') and end_node.id:
                        display_label = str(end_node.id)[:25]
                    else:
                        display_label = f"{label[:10]}..."

                    # 设置颜色
                    if label == "Entity":
                        color = "#667eea"
                        title = f"Entity\\n类型: {end_node.get('type', 'N/A')}"
                    elif label == "OpenClawNode":
                        color = "#f093fb"
                        title = f"OpenClawNode\\nID: {end_node.get('_original_id', end_node.get('id', 'N/A'))}"
                    else:
                        color = "#ffd93d"
                        title = label

                    nodes[end_id] = {
                        'id': end_id,
                        'label': display_label,
                        'title': title,
                        'color': color
                    }

                # 处理关系
                rel = record['r']
                rel_type = rel.type
                start_id = str(start_node.element_id)
                end_id = str(end_node.element_id)

                # 设置关系颜色
                if rel_type == "RELATION":
                    color = "#667eea"
                elif rel_type == "RELATED_TO":
                    color = "#f093fb"
                elif rel_type == "CITES":
                    color = "#4facfe"
                else:
                    color = "#95e1d3"

                edges.append({
                    'from': start_id,
                    'to': end_id,
                    'title': rel_type,
                    'color': color
                })

            driver.close()

            # 添加节点和边
            for node_id, node_data in nodes.items():
                net.add_node(node_id, **node_data)

            for edge in edges:
                net.add_edge(edge['from'], edge['to'], title=edge['title'], color=edge['color'])

            # 保存HTML
            output_file = "/Users/xujian/Athena工作平台/kg_visualization.html"
            logger.info(f"💾 保存可视化到: {output_file}")

            net.show(output_file)

            logger.info("✅ 可视化完成!")
            logger.info(f"📍 在浏览器中打开: {output_file}")
            logger.info("💡 提示: 图谱是完全交互式的，可以拖拽、缩放、点击节点查看详情")

    except Exception as e:
        logger.error(f"❌ 可视化失败: {e}")
        raise


def main():
    """主函数"""
    logger.info("🎨 生成Athena知识图谱可视化...")
    logger.info("📊 数据: 93万节点 + 6万关系")
    logger.info("🔍 查询: 50个样本节点")

    create_sample_visualization()

    logger.info("\n🎉 可视化已生成!")
    logger.info("📖 更多可视化方案请查看: docs/guides/KG_VISUALIZATION_GUIDE.md")


if __name__ == "__main__":
    main()
