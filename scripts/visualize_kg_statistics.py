#!/usr/bin/env python3
"""
知识图谱统计可视化 - 使用ECharts生成统计图表
"""

import logging
from neo4j import GraphDatabase
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j连接
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "athena_neo4j_2024")


def generate_statistics_html():
    """生成统计图表HTML"""

    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    try:
        with driver.session() as session:
            # 1. 节点类型分布
            result = session.run("""
                MATCH (n)
                WITH labels(n) as labels, count(*) as count
                RETURN labels[0] as label, count
                ORDER BY count DESC
            """)

            node_labels = []
            node_counts = []

            for record in result:
                node_labels.append(record['label'])
                node_counts.append(record['count'])

            # 2. 实体类型分布
            result = session.run("""
                MATCH (e:Entity)
                WITH e.type as type, count(*) as count
                RETURN type, count
                ORDER BY count DESC
                LIMIT 10
            """)

            entity_types = []
            entity_counts = []

            for record in result:
                entity_types.append(record['type'] or 'Unknown')
                entity_counts.append(record['count'])

            # 3. 关系类型分布
            result = session.run("""
                MATCH ()-[r]->()
                WITH type(r) as type, count(*) as count
                RETURN type, count
                ORDER BY count DESC
            """)

            rel_types = []
            rel_counts = []

            for record in result:
                rel_types.append(record['type'])
                rel_counts.append(record['count'])

            driver.close()

            # 生成HTML
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Athena知识图谱统计</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f7fa;
        }}
        #header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #6c757d;
            font-size: 14px;
        }}
        .chart-container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }}
        .chart {{
            width: 100%;
            height: 400px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🌸 Athena知识图谱统计</h1>
        <p class="subtitle">本项目判决数据 + OpenClaw法律世界模型 | 93万节点 + 6万关系</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{sum(node_counts):,}</div>
            <div class="stat-label">总节点数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{sum(rel_counts):,}</div>
            <div class="stat-label">总关系数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{node_counts[0]:,}</div>
            <div class="stat-label">主要节点类型</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{rel_counts[0]:,}</div>
            <div class="stat-label">主要关系类型</div>
        </div>
    </div>

    <div class="chart-container">
        <h2>📊 节点类型分布</h2>
        <div id="nodeChart" class="chart"></div>
    </div>

    <div class="chart-container">
        <h2>🏷️ 实体类型分布（Top 10）</h2>
        <div id="entityChart" class="chart"></div>
    </div>

    <div class="chart-container">
        <h2>🔗 关系类型分布</h2>
        <div id="relChart" class="chart"></div>
    </div>

    <script type="text/javascript">
        // 节点类型分布
        var nodeChart = echarts.init(document.getElementById('nodeChart'));
        nodeChart.setOption({{
            tooltip: {{
                trigger: 'item',
                formatter: '{{a}} <br/>{{b}}: {{c}} ({{d}}%)'
            }},
            legend: {{
                top: '5%',
                left: 'center'
            }},
            series: [
                {{
                    name: '节点类型',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: false,
                    itemStyle: {{
                        borderRadius: 10,
                        borderColor: '#fff',
                        borderWidth: 2
                    }},
                    label: {{
                        show: false,
                        position: 'center'
                    }},
                    emphasis: {{
                        label: {{
                            show: true,
                            fontSize: '20',
                            fontWeight: 'bold'
                        }}
                    }},
                    labelLine: {{
                        show: false
                    }},
                    data: {json.dumps([
                        {{'value': {node_counts[0]}, 'name': '{node_labels[0]}'}},
                        {{'value': {node_counts[1]}, 'name': '{node_labels[1]}'}}
                    ])}
                }}
            ]
        }});

        // 实体类型分布
        var entityChart = echarts.init(document.getElementById('entityChart'));
        entityChart.setOption({{
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{
                    type: 'shadow'
                }}
            }},
            xAxis: {{
                type: 'category',
                data: {json.dumps(entity_types)},
                axisLabel: {{
                    rotate: 45,
                    fontSize: 10
                }}
            }},
            yAxis: {{
                type: 'value',
                axisLabel: {{
                    formatter: function(value) {{
                        return (value / 1000).toFixed(1) + 'K';
                    }}
                }}
            }},
            series: [
                {{
                    name: '实体数量',
                    type: 'bar',
                    data: {json.dumps(entity_counts)},
                    itemStyle: {{
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            {{offset: 0, color: '#667eea'}},
                            {{offset: 1, color: '#764ba2'}}
                        ])
                    }}
                }}
            ]
        }});

        // 关系类型分布
        var relChart = echarts.init(document.getElementById('relChart'));
        relChart.setOption({{
            tooltip: {{
                trigger: 'item',
                formatter: '{{a}} <br/>{{b}}: {{c}} ({{d}}%)'
            }},
            legend: {{
                top: '5%',
                left: 'center'
            }},
            series: [
                {{
                    name: '关系类型',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    data: {json.dumps([
                        {{'value': {rel_counts[0]}, 'name': '{rel_types[0]}'}},
                        {{'value': {rel_counts[1]}, 'name': '{rel_types[1]}'}},
                        {{'value': {rel_counts[2]}, 'name': '{rel_types[2]}'}},
                        {{'value': {rel_counts[3]}, 'name': '{rel_types[3]}' if len({json.dumps(rel_counts)}) > 3 else 'Other'}}
                    ])}
                }}
            ]
        }});

        // 响应式
        window.addEventListener('resize', function() {{
            nodeChart.resize();
            entityChart.resize();
            relChart.resize();
        }});
    </script>
</body>
</html>
"""
            return html

    except Exception as e:
        logger.error(f"生成统计失败: {e}")
        raise


def main():
    """生成并保存统计HTML"""
    logger.info("📊 生成知识图谱统计可视化...")

    html_content = generate_statistics_html()

    # 保存HTML文件
    output_file = "/Users/xujian/Athena工作平台/kg_statistics.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"✅ 统计HTML已生成: {output_file}")
    logger.info("📍 在浏览器中打开该文件查看统计图表")


if __name__ == "__main__":
    main()
