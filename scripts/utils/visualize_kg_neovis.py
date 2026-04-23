#!/usr/bin/env python3
"""
Neo4j知识图谱可视化 - Neovis.js版本
在浏览器中展示交互式知识图谱
"""

import logging

from flask import Flask, jsonify, render_template_string
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Neo4j连接
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "athena_neo4j_2024")


# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Athena知识图谱可视化</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/neovis.js/2.0.2/neovis.min.js"></script>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 0;
        }
        #header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        #header h1 {
            margin: 0;
            font-size: 28px;
        }
        #header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        #controls {
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        #query-container {
            max-width: 800px;
            margin: 0 auto;
        }
        #query-input {
            width: 70%;
            padding: 10px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 14px;
        }
        button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-left: 10px;
        }
        button:hover {
            background: #5568d3;
        }
        #stats {
            padding: 15px 20px;
            background: #fff;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-around;
        }
        .stat-item {
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 12px;
            color: #6c757d;
            margin-top: 5px;
        }
        #viz {
            width: 100%;
            height: 600px;
            border: 1px solid #dee2e6;
        }
        .legend {
            padding: 20px;
            background: #f8f9fa;
        }
        .legend-item {
            display: inline-block;
            margin: 0 15px 10px 0;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
        }
        .legend-entity {
            background: #667eea;
            color: white;
        }
        .legend-openclaw {
            background: #f093fb;
            color: white;
        }
    </style>
</head>
<body>
    <div id="header">
        <h1>🌸 Athena知识图谱可视化</h1>
        <p>本项目判决数据 + OpenClaw法律世界模型 | 93万节点 + 6万关系</p>
    </div>

    <div id="controls">
        <div id="query-container">
            <input type="text" id="query-input" placeholder="输入Cypher查询语句..." value="MATCH (n:Entity {type: 'PATENT_NUMBER'})-[r:RELATION]->(m) RETURN n,r,m LIMIT 50">
            <button onclick="runQuery()">🔍 查询</button>
            <button onclick="loadRandom()">🎲 随机样本</button>
            <button onclick="showEntityTypes()">📊 实体类型</button>
            <button onclick="showOpenClawGraph()">🔗 OpenClaw关系</button>
        </div>
    </div>

    <div id="stats">
        <div class="stat-item">
            <div class="stat-value" id="node-count">0</div>
            <div class="stat-label">节点</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" id="edge-count">0</div>
            <div class="stat-label">关系</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" id="entity-count">0</div>
            <div class="stat-label">Entity</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" id="openclaw-count">0</div>
            <div class="stat-label">OpenClawNode</div>
        </div>
    </div>

    <div id="viz"></div>

    <div class="legend">
        <strong>图例：</strong>
        <span class="legend-item legend-entity">Entity (本项目判决数据)</span>
        <span class="legend-item legend-openclaw">OpenClawNode (法律世界模型)</span>
    </div>

    <script type="text/javascript">
        let viz;

        // 定义节点样式
        const nodeStyles = [
            {
                selector: 'node',
                style: {
                    'background-color': '#667eea',
                    'label': 'data(label)',
                    'font-size': '12px',
                    'width': '30px',
                    'height': '30px'
                }
            },
            {
                selector: 'node[labels[0]="Entity"]',
                style: {
                    'background-color': '#667eea',
                    'border-color': '#5568d3',
                    'border-width': '2px'
                }
            },
            {
                selector: 'node[labels[0]="OpenClawNode"]',
                style: {
                    'background-color': '#f093fb',
                    'border-color': '#ed64a6',
                    'border-width': '2px'
                }
            }
        ];

        // 定义关系样式
        const linkStyles = [
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#ccc',
                    'target-arrow-color': '#ccc',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier'
                }
            },
            {
                selector: 'edge[type="RELATION"]',
                style: {
                    'line-color': '#667eea',
                    'target-arrow-color': '#667eea',
                    'width': 2
                }
            },
            {
                selector: 'edge[type="RELATED_TO"]',
                style: {
                    'line-color': '#f093fb',
                    'target-arrow-color': '#f093fb',
                    'width': 2
                }
            },
            {
                selector: 'edge[type="CITES"]',
                style: {
                    'line-color': '#4facfe',
                    'target-arrow-color': '#4facfe',
                    'width': 2
                }
            }
        ];

        // 初始化可视化
        function initViz() {
            const vizDiv = document.getElementById("viz");
            const config = {
                container: vizDiv,
                nodes: {
                    data: {
                        nodes: [],
                        edges: []
                    }
                },
                layout: {
                    hierarchical: {
                        enabled: false,
                        levelSeparation: 150,
                        nodeSpacing: 100
                    },
                    randomize: false,
                    improvedLayout: true
                },
                physics: {
                    barnesHut: {
                        gravitationalConstant: -8000,
                        centralGravity: 0.3,
                        springLength: 150,
                        springConstant: 0.04
                    },
                    stabilityThreshold: 1000
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 200,
                    zoomView: true
                }
            };

            viz = new Neovis.default(config, nodeStyles, linkStyles);

            // 监听完成事件
            viz.network.on(" stabilized ", function(params) {
                updateStats();
            });
        }

        // 运行查询
        function runQuery() {
            const query = document.getElementById("query-input").value;
            loadGraph(query);
        }

        // 加载图数据
        function loadGraph(query) {
            fetch('/api/graph', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            })
            .then(response => response.json())
            .then(data => {
                viz.setData(data);
                updateStats();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('查询失败: ' + error);
            });
        }

        // 更新统计信息
        function updateStats() {
            const nodes = viz.network.getData().nodes;
            const edges = viz.network.getData().edges;

            let entityCount = 0;
            let openclawCount = 0;

            nodes.forEach(node => {
                const labels = node.labels || [];
                if (labels.includes('Entity')) {
                    entityCount++;
                } else if (labels.includes('OpenClawNode')) {
                    openclawCount++;
                }
            });

            document.getElementById("node-count").textContent = nodes.length;
            document.getElementById("edge-count").textContent = edges.length;
            document.getElementById("entity-count").textContent = entityCount;
            document.getElementById("openclaw-count").textContent = openclawCount;
        }

        // 随机样本
        function loadRandom() {
            const queries = [
                "MATCH (n:Entity {type: 'PATENT_NUMBER'})-[r:RELATION]->(m) RETURN n,r,m LIMIT 30",
                "MATCH (n:Entity {type: 'PERSON'})-[r:RELATION]->(m) RETURN n,r,m LIMIT 30",
                "MATCH (n:Entity {type: 'COURT'})-[r:RELATION]->(m) RETURN n,r,m LIMIT 30",
                "MATCH (n:OpenClawNode)-[r:RELATED_TO]->(m:OpenClawNode) RETURN n,r,m LIMIT 30",
                "MATCH (n:OpenClawNode)-[r:CITES]->(m:OpenClawNode) RETURN n,r,m LIMIT 30"
            ];
            const randomQuery = queries[Math.floor(Math.random() * queries.length)];
            document.getElementById("query-input").value = randomQuery;
            loadGraph(randomQuery);
        }

        // 显示实体类型
        function showEntityTypes() {
            const query = `
                MATCH (e:Entity)
                WITH e.type AS type, count(e) AS count
                MATCH (n:Entity {type: type})-[r:RELATION]->(m)
                RETURN n,r,m LIMIT 50
            `;
            document.getElementById("query-input").value = query;
            loadGraph(query);
        }

        // 显示OpenClaw关系
        function showOpenClawGraph() {
            const query = `
                MATCH (n:OpenClawNode)-[r:RELATED_TO|CITES]->(m:OpenClawNode)
                RETURN n,r,m LIMIT 50
            `;
            document.getElementById("query-input").value = query;
            loadGraph(query);
        }

        // 页面加载时初始化
        window.onload = function() {
            initViz();
            // 自动加载默认查询
            runQuery();
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/graph', methods=['POST'])
def get_graph():
    """获取图数据API"""
    from flask import request

    data = request.get_json()
    query = data.get('query', '')

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

        with driver.session() as session:
            result = session.run(query)

            nodes = {}
            edges = []

            for record in result:
                for key in record.keys():
                    value = record[key]

                    if isinstance(value, (dict,)) and 'element_id' in str(value):
                        # 这是一个节点
                        node_id = str(value.element_id)
                        if node_id not in nodes:
                            node_data = dict(value)
                            nodes[node_id] = {
                                'id': node_id,
                                'labels': list(value.labels) if hasattr(value, 'labels') else ['Unknown'],
                                'data': {}
                            }

                            # 添加属性
                            for prop_key, prop_value in node_data.items():
                                if prop_key not in ['element_id', 'identity']:
                                    if prop_key == 'labels':
                                        nodes[node_id]['data']['label'] = str(prop_value[0]) if prop_value else 'Unknown'
                                    else:
                                        nodes[node_id]['data'][prop_key] = prop_value

                    elif hasattr(value, 'type') and hasattr(value, 'start') and hasattr(value, 'end'):
                        # 这是一条关系
                        edge_id = str(value.element_id)
                        source_id = str(value.start_node.element_id)
                        target_id = str(value.end_node.element_id)

                        edge_data = {
                            'from': source_id,
                            'to': target_id,
                            'id': edge_id,
                            'label': value.type,
                            'data': dict(value)
                        }

                        # 移除不需要的属性
                        for prop_key in ['element_id', 'identity', 'start', 'end', 'type']:
                            edge_data['data'].pop(prop_key, None)

                        edges.append(edge_data)

            driver.close()

            # 转换节点列表
            nodes_list = list(nodes.values())

            return jsonify({
                'nodes': nodes_list,
                'edges': edges
            })

    except Exception as e:
        logger.error(f"查询失败: {e}")
        return jsonify({'error': str(e)}), 500


def main():
    """启动Flask服务器"""
    logger.info("🚀 启动Athena知识图谱可视化服务器...")
    logger.info("📍 访问地址: http://localhost:5000")
    logger.info("⚠️  确保Neo4j容器正在运行")
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == "__main__":
    main()
