#!/usr/bin/env python3
"""
使用pyvis生成交互式知识图谱HTML
"""

import logging

from neo4j import GraphDatabase
from pyvis.network import Network

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j连接
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "athena_neo4j_2024")


def visualize_sample(query, output_file, title="知识图谱"):
    """可视化查询结果"""

    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    try:
        logger.info(f"🔍 执行查询: {query}")

        with driver.session() as session:
            result = session.run(query)

            # 创建pyvis网络
            net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", directed=True)
            net.set_options("""
            {
              "nodes": {
                "borderWidth": 2,
                "size": 20
              },
              "edges": {
                "width": 2,
                "smooth": false,
                "arrows": {
                  "to": {
                    "enabled": true,
                    "scaleFactor": 0.5
                  }
                }
              },
              "physics": {
                "forceAtlas2Based": {
                  "gravitationalConstant": -50,
                  "centralGravity": 0.01,
                  "springLength": 200,
                  "springConstant": 0.08
                },
                "maxVelocity": 50,
                "solver": "forceAtlas2Based",
                "timestep": 0.5,
                "stabilization": {
                  "iterations": 200
                }
              }
            }
            """)

            nodes = {}
            edges = []

            for record in result:
                for key in record.keys():
                    value = record[key]

                    if isinstance(value, (dict,)) and 'element_id' in str(value):
                        # 节点
                        node_id = str(value.element_id)
                        if node_id not in nodes:
                            labels = list(value.labels) if hasattr(value, 'labels') else ['Unknown']
                            label = labels[0] if labels else 'Unknown'

                            # 提取显示标签
                            display_label = label
                            if hasattr(value, 'text'):
                                display_label = str(value.text)[:30]
                            elif hasattr(value, 'title'):
                                display_label = str(value.title)[:30]
                            elif hasattr(value, 'name'):
                                display_label = str(value.name)[:30]

                            # 设置颜色
                            color = "#667eea" if label == "Entity" else "#f093fb"

                            nodes[node_id] = {
                                'id': node_id,
                                'label': display_label,
                                'title': f"{label}\\nID: {node_id}",
                                'color': color
                            }

                    elif hasattr(value, 'type') and hasattr(value, 'start') and hasattr(value, 'end'):
                        # 关系
                        str(value.element_id)
                        source_id = str(value.start_node.element_id)
                        target_id = str(value.end_node.element_id)

                        # 设置颜色
                        color = "#667eea" if value.type == "RELATION" else "#f093fb"
                        if value.type == "CITES":
                            color = "#4facfe"

                        edges.append({
                            'from': source_id,
                            'to': target_id,
                            'title': value.type,
                            'color': color,
                            'width': 2
                        })

            # 添加节点和边
            for node_id, node_data in nodes.items():
                net.add_node(node_id, **node_data)

            for edge in edges:
                net.add_edge(edge['from'], edge['to'], title=edge['title'], color=edge['color'], width=edge['width'])

            driver.close()

            # 保存HTML
            logger.info(f"💾 保存可视化到: {output_file}")
            net.show(output_file)

            logger.info(f"✅ 可视化完成! 节点: {len(nodes)}, 关系: {len(edges)}")

    except Exception as e:
        logger.error(f"❌ 可视化失败: {e}")
        raise


def main():
    """主函数"""
    logger.info("🎨 生成知识图谱可视化...")

    # 1. 实体关系图
    logger.info("\n📊 生成1: 实体关系图")
    visualize_sample(
        "MATCH (n:Entity {type: 'PATENT_NUMBER'})-[r:RELATION]->(m) RETURN n,r,m LIMIT 50",
        "/Users/xujian/Athena工作平台/kg_entity_relations.html",
        "实体关系图"
    )

    # 2. 人物关系图
    logger.info("\n📊 生成2: 人物关系图")
    visualize_sample(
        "MATCH (n:Entity {type: 'PERSON'})-[r:RELATION]->(m) RETURN n,r,m LIMIT 50",
        "/Users/xujian/Athena工作平台/kg_person_relations.html",
        "人物关系图"
    )

    # 3. OpenClaw关系图
    logger.info("\n📊 生成3: OpenClaw关系图")
    visualize_sample(
        "MATCH (n:OpenClawNode)-[r:RELATED_TO|CITES]->(m:OpenClawNode) RETURN n,r,m LIMIT 50",
        "/Users/xujian/Athena工作平台/kg_openclaw_relations.html",
        "OpenClaw关系图"
    )

    # 4. 混合关系图
    logger.info("\n📊 生成4: 混合关系图")
    visualize_sample(
        "MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100",
        "/Users/xujian/Athena工作平台/kg_mixed_relations.html",
        "混合关系图"
    )

    logger.info("\n🎉 所有可视化已生成!")
    logger.info("📍 在浏览器中打开HTML文件查看交互式图谱")


if __name__ == "__main__":
    main()
