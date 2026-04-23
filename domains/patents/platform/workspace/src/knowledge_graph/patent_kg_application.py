#!/usr/bin/env python3
"""
专利知识图谱应用系统
Patent Knowledge Graph Application System

提供完整的专利知识图谱构建、查询和可视化应用
Provides complete patent knowledge graph construction, query and visualization application

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

# Web框架
try:
    from flask import Flask, jsonify, render_template, request, send_file
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger.info('警告: flask库未安装，Web应用功能不可用')

# 数据处理库
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.info('警告: pandas库未安装，数据分析功能不可用')

# 可视化库
try:
    import matplotlib.pyplot as plt
    import plotly.express as px
    import plotly.graph_objects as go
    import seaborn as sns
    from plotly.offline import plot
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logger.info('警告: 可视化库未安装，图表功能不可用')

from neo4j_manager import Neo4jManager

# 本地模块
from patent_knowledge_extractor import ExtractionResult, PatentKnowledgeExtractor
from patent_knowledge_graph_schema import EntityType

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PatentKnowledgeGraphApplication:
    """专利知识图谱应用系统"""

    def __init__(self, config: dict[str, Any] = None):
        """
        初始化应用系统

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 初始化组件
        self.extractor = None
        self.neo4j_manager = None
        self.flask_app = None

        # 应用状态
        self.is_extracting = False
        self.extraction_progress = 0
        self.extraction_results = []

        # 统计信息
        self.app_stats = {
            'start_time': datetime.now(),
            'total_processed': 0,
            'total_entities': 0,
            'total_relations': 0,
            'last_update': None
        }

    def initialize_components(self):
        """初始化所有组件"""
        logger.info('初始化应用组件...')

        # 初始化知识抽取器
        self.extractor = PatentKnowledgeExtractor(self.config.get('extraction', {}))

        # 初始化Neo4j管理器
        if 'neo4j' in self.config:
            neo4j_config = self.config['neo4j']
            self.neo4j_manager = Neo4jManager(
                uri=neo4j_config.get('uri', 'bolt://localhost:7687'),
                username=neo4j_config.get('username', 'neo4j'),
                password=neo4j_config.get('password', 'password'),
                database=neo4j_config.get('database', 'patent_kg')
            )

            if self.neo4j_manager.connect():
                self.neo4j_manager.create_schema()
                logger.info('Neo4j连接和模式创建成功')

        logger.info('应用组件初始化完成')

    def setup_flask_app(self):
        """设置Flask应用"""
        if not FLASK_AVAILABLE:
            raise ImportError('Flask库未安装，无法创建Web应用')

        self.flask_app = Flask(__name__,
                               template_folder='templates',
                               static_folder='static')

        # 启用CORS
        CORS(self.flask_app)

        # 设置路由
        self._setup_routes()

        logger.info('Flask应用设置完成')

    def _setup_routes(self):
        """设置API路由"""
        app = self.flask_app

        @app.route('/')
        def index():
            """主页"""
            return render_template('index.html')

        @app.route('/api/stats')
        def get_stats():
            """获取统计信息"""
            try:
                if self.neo4j_manager:
                    kg_stats = self.neo4j_manager.get_knowledge_graph_statistics()
                else:
                    kg_stats = {}

                stats = {
                    'app_stats': self.app_stats,
                    'knowledge_graph': kg_stats,
                    'extraction_progress': {
                        'is_extracting': self.is_extracting,
                        'progress': self.extraction_progress,
                        'results_count': len(self.extraction_results)
                    }
                }
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @app.route('/api/extract', methods=['POST'])
        def extract_knowledge():
            """抽取知识"""
            try:
                data = request.get_json()
                directory = data.get('directory')
                recursive = data.get('recursive', True)
                max_files = data.get('max_files', 100)

                if not directory or not os.path.exists(directory):
                    return jsonify({'error': '无效的目录路径'}), 400

                if self.is_extracting:
                    return jsonify({'error': '正在处理其他抽取任务'}), 409

                # 异步执行抽取
                import threading
                thread = threading.Thread(
                    target=self._async_extract,
                    args=(directory, recursive, max_files)
                )
                thread.start()

                return jsonify({'message': '抽取任务已开始'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @app.route('/api/search/entities')
        def search_entities():
            """搜索实体"""
            try:
                entity_type = request.args.get('type')
                name_pattern = request.args.get('q', '')
                limit = int(request.args.get('limit', 50))

                if not self.neo4j_manager:
                    return jsonify({'error': 'Neo4j未连接'}), 503

                entities = self.neo4j_manager.search_entities(
                    entity_type=entity_type,
                    name_pattern=name_pattern,
                    limit=limit
                )

                return jsonify({'entities': entities, 'count': len(entities)})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @app.route('/api/entity/<entity_id>')
        def get_entity(entity_id):
            """获取实体详情"""
            try:
                if not self.neo4j_manager:
                    return jsonify({'error': 'Neo4j未连接'}), 503

                entity = self.neo4j_manager.query_entity(entity_id)
                if not entity:
                    return jsonify({'error': '实体未找到'}), 404

                relations = self.neo4j_manager.query_relations(entity_id)

                return jsonify({
                    'entity': entity,
                    'relations': relations,
                    'relations_count': len(relations)
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @app.route('/api/visualization/overview')
        def get_overview_visualization():
            """获取概览可视化数据"""
            try:
                if not self.neo4j_manager:
                    return jsonify({'error': 'Neo4j未连接'}), 503

                stats = self.neo4j_manager.get_knowledge_graph_statistics()

                # 生成图表数据
                charts_data = {
                    'entity_distribution': stats.get('entity_types', {}),
                    'relation_distribution': stats.get('relation_types', {}),
                    'graph_metrics': {
                        'total_entities': stats.get('total_entities', 0),
                        'total_relations': stats.get('total_relations', 0),
                        'graph_density': stats.get('graph_density', 0)
                    }
                }

                return jsonify(charts_data)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @app.route('/api/visualization/network/<entity_id>')
        def get_entity_network(entity_id):
            """获取实体网络图"""
            try:
                if not self.neo4j_manager:
                    return jsonify({'error': 'Neo4j未连接'}), 503

                # 获取实体及其关系
                entity = self.neo4j_manager.query_entity(entity_id)
                relations = self.neo4j_manager.query_relations(entity_id, max_depth=2)

                if not entity:
                    return jsonify({'error': '实体未找到'}), 404

                # 构建网络数据
                nodes = [{'id': entity['id'], 'label': entity['name'], 'type': entity['type']}]
                edges = []
                added_nodes = {entity['id']}

                for rel in relations:
                    source_id = rel['source']['id']
                    target_id = rel['target']['id']

                    if source_id not in added_nodes:
                        nodes.append({
                            'id': source_id,
                            'label': rel['source']['name'],
                            'type': rel['source']['type']
                        })
                        added_nodes.add(source_id)

                    if target_id not in added_nodes:
                        nodes.append({
                            'id': target_id,
                            'label': rel['target']['name'],
                            'type': rel['target']['type']
                        })
                        added_nodes.add(target_id)

                    edges.append({
                        'source': source_id,
                        'target': target_id,
                        'type': rel['relation']['type'],
                        'confidence': rel['relation'].get('confidence', 0)
                    })

                return jsonify({
                    'nodes': nodes,
                    'edges': edges,
                    'center_entity': entity
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @app.route('/api/export/csv')
        def export_csv():
            """导出CSV格式数据"""
            try:
                if not self.neo4j_manager:
                    return jsonify({'error': 'Neo4j未连接'}), 503

                # 生成CSV数据
                entities_data = []
                relations_data = []

                # 导出所有实体
                entity_types = [et.value for et in EntityType]
                for entity_type in entity_types:
                    entities = self.neo4j_manager.get_entities_by_type(
                        EntityType(entity_type), limit=10000
                    )
                    for entity in entities:
                        entities_data.append(entity)

                # 导出所有关系
                cypher = """
                MATCH ()-[r]-()
                RETURN r
                LIMIT 50000
                """
                relations = self.neo4j_manager.execute_cypher_query(cypher)
                for record in relations:
                    relations_data.append(dict(record['r']))

                # 创建CSV文件
                import tempfile
                import zipfile
                from io import StringIO

                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                    with zipfile.ZipFile(temp_file.name, 'w') as zip_file:
                        # 导出实体CSV
                        if entities_data:
                            entities_df = pd.DataFrame(entities_data)
                            entities_csv = StringIO()
                            entities_df.to_csv(entities_csv, index=False)
                            zip_file.writestr('entities.csv', entities_csv.getvalue())

                        # 导出关系CSV
                        if relations_data:
                            relations_df = pd.DataFrame(relations_data)
                            relations_csv = StringIO()
                            relations_df.to_csv(relations_csv, index=False)
                            zip_file.writestr('relations.csv', relations_csv.getvalue())

                return send_file(temp_file.name,
                               as_attachment=True,
                               download_name='patent_knowledge_graph.csv')
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @app.route('/api/query', methods=['POST'])
        def execute_query():
            """执行自定义查询"""
            try:
                data = request.get_json()
                cypher = data.get('cypher', '')
                params = data.get('params', {})

                if not cypher:
                    return jsonify({'error': 'Cypher查询不能为空'}), 400

                # 安全检查：限制查询类型
                forbidden_keywords = ['DELETE', 'DROP', 'CREATE', 'REMOVE', 'MERGE']
                cypher_upper = cypher.upper()
                for keyword in forbidden_keywords:
                    if keyword in cypher_upper:
                        return jsonify({'error': f'不允许使用{keyword}操作'}), 403

                if not self.neo4j_manager:
                    return jsonify({'error': 'Neo4j未连接'}), 503

                results = self.neo4j_manager.execute_cypher_query(cypher, params)

                return jsonify({'results': results, 'count': len(results)})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def _async_extract(self, directory: str, recursive: bool, max_files: int):
        """异步执行知识抽取"""
        try:
            self.is_extracting = True
            self.extraction_progress = 0

            logger.info(f"开始抽取知识: {directory}")

            # 执行抽取
            results = self.extractor.process_directory(
                directory, recursive=recursive, max_files=max_files
            )

            # 更新进度
            total_files = len(results)

            # 导入到Neo4j
            if self.neo4j_manager:
                import_result = self.neo4j_manager.import_extraction_results(results)
                logger.info(f"导入结果: {import_result}")

            # 更新统计
            total_entities = sum(len(r.entities) for r in results)
            total_relations = sum(len(r.relations) for r in results)

            self.app_stats.update({
                'total_processed': self.app_stats['total_processed'] + total_files,
                'total_entities': self.app_stats['total_entities'] + total_entities,
                'total_relations': self.app_stats['total_relations'] + total_relations,
                'last_update': datetime.now()
            })

            self.extraction_results.extend(results)
            self.extraction_progress = 100

            logger.info(f"知识抽取完成: {total_files}个文件, {total_entities}个实体, {total_relations}个关系")

        except Exception as e:
            logger.error(f"知识抽取失败: {str(e)}")
        finally:
            self.is_extracting = False

    def generate_dashboard_html(self) -> str:
        """生成仪表板HTML"""
        dashboard_html = """
<!DOCTYPE html>
<html lang='zh-CN'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>专利知识图谱仪表板</title>
    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
    <script src='https://unpkg.com/vis-network/standalone/umd/vis-network.min.js'></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .chart-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        #network-graph {
            height: 600px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .control-panel {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .btn {
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 10px;
        }
        .btn:hover {
            background: #5a6fd8;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #ddd;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class='container'>
        <div class='header'>
            <h1>🏛️ 专利知识图谱仪表板</h1>
            <p>智能专利知识管理系统</p>
        </div>

        <div class='stats-grid' id='statsGrid'>
            <div class='stat-card'>
                <div class='stat-number' id='totalEntities'>-</div>
                <div class='stat-label'>实体总数</div>
            </div>
            <div class='stat-card'>
                <div class='stat-number' id='totalRelations'>-</div>
                <div class='stat-label'>关系总数</div>
            </div>
            <div class='stat-card'>
                <div class='stat-number' id='processedFiles'>-</div>
                <div class='stat-label'>已处理文件</div>
            </div>
            <div class='stat-card'>
                <div class='stat-number' id='graphDensity'>-</div>
                <div class='stat-label'>图谱密度</div>
            </div>
        </div>

        <div class='control-panel'>
            <h3>知识抽取控制</h3>
            <div class='form-group'>
                <label for='directoryInput'>文档目录:</label>
                <input type='text' id='directoryInput' placeholder='/path/to/documents'
                       value='/Users/xujian/学习资料/专利'>
            </div>
            <div class='form-group'>
                <label for='maxFilesInput'>最大文件数:</label>
                <input type='number' id='maxFilesInput' value='10' min='1' max='1000'>
            </div>
            <button class='btn' onclick='startExtraction()'>开始抽取</button>
            <button class='btn' onclick='refreshStats()'>刷新统计</button>

            <div class='progress-bar' id='progressBar' style='display: none;'>
                <div class='progress-fill' id='progressFill'></div>
            </div>
            <div id='extractionStatus'></div>
        </div>

        <div class='chart-row'>
            <div class='chart-container'>
                <h3>实体类型分布</h3>
                <canvas id='entityChart'></canvas>
            </div>
            <div class='chart-container'>
                <h3>关系类型分布</h3>
                <canvas id='relationChart'></canvas>
            </div>
        </div>

        <div class='chart-container'>
            <h3>知识网络图</h3>
            <div id='network-graph'></div>
        </div>
    </div>

    <script>
        let entityChart, relationChart, network;

        // 初始化图表
        function initCharts() {
            // 实体类型饼图
            const entityCtx = document.getElementById('entityChart').getContext('2d');
            entityChart = new Chart(entityCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });

            // 关系类型饼图
            const relationCtx = document.getElementById('relationChart').getContext('2d');
            relationChart = new Chart(relationCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#FF9F40', '#4BC0C0', '#9966FF', '#FF6384',
                            '#36A2EB', '#FFCE56', '#C9CBCF', '#FF9F40'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        // 更新统计数据
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    const kg = data.knowledge_graph || {};

                    document.getElementById('totalEntities').textContent = kg.total_entities || 0;
                    document.getElementById('totalRelations').textContent = kg.total_relations || 0;
                    document.getElementById('processedFiles').textContent = data.app_stats?.total_processed || 0;
                    document.getElementById('graphDensity').textContent = (kg.graph_density || 0).toFixed(4);

                    // 更新图表数据
                    if (entityChart && kg.entity_types) {
                        entityChart.data.labels = Object.keys(kg.entity_types);
                        entityChart.data.datasets[0].data = Object.values(kg.entity_types);
                        entityChart.update();
                    }

                    if (relationChart && kg.relation_types) {
                        relationChart.data.labels = Object.keys(kg.relation_types);
                        relationChart.data.datasets[0].data = Object.values(kg.relation_types);
                        relationChart.update();
                    }
                });
        }

        // 开始抽取
        function startExtraction() {
            const directory = document.getElementById('directoryInput').value;
            const maxFiles = parseInt(document.getElementById('maxFilesInput').value);

            if (!directory) {
                alert('请输入文档目录');
                return;
            }

            const progressBar = document.getElementById('progressBar');
            const progressFill = document.getElementById('progressFill');
            const statusDiv = document.getElementById('extractionStatus');

            progressBar.style.display = 'block';
            progressFill.style.width = '0%';
            statusDiv.textContent = '正在开始抽取...';

            fetch('/api/extract', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    directory: directory,
                    maxFiles: maxFiles,
                    recursive: true
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    statusDiv.textContent = '错误: ' + data.error;
                    progressBar.style.display = 'none';
                } else {
                    statusDiv.textContent = data.message;
                    // 启动进度监控
                    monitorProgress();
                }
            })
            .catch(error => {
                statusDiv.textContent = '网络错误: ' + error.message;
                progressBar.style.display = 'none';
            });
        }

        // 监控抽取进度
        function monitorProgress() {
            const progressBar = document.getElementById('progressBar');
            const progressFill = document.getElementById('progressFill');
            const statusDiv = document.getElementById('extractionStatus');

            const interval = setInterval(() => {
                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => {
                        const progress = data.extraction_progress;
                        progressFill.style.width = progress.progress + '%';

                        if (progress.is_extracting) {
                            statusDiv.textContent = `正在处理... ${progress.progress.toFixed(1)}% (${progress.results_count} 个文件)`;
                        } else {
                            statusDiv.textContent = '抽取完成！';
                            progressBar.style.display = 'none';
                            clearInterval(interval);
                            updateStats();
                        }
                    });
            }, 2000);
        }

        // 刷新统计
        function refreshStats() {
            updateStats();
        }

        // 初始化网络图
        function initNetworkGraph() {
            const container = document.getElementById('network-graph');
            const data = {
                nodes: [
                    {id: 1, label: '专利法', type: 'law'},
                    {id: 2, label: '第22条', type: 'article'},
                    {id: 3, label: '无效宣告案例', type: 'case'}
                ],
                edges: [
                    {from: 1, to: 2},
                    {from: 3, to: 2}
                ]
            };

            const options = {
                nodes: {
                    shape: 'dot',
                    size: 16,
                    font: {
                        size: 14
                    },
                    borderWidth: 2
                },
                edges: {
                    width: 2,
                    color: {inherit: 'from'},
                    smooth: {
                        type: 'continuous'
                    }
                },
                physics: {
                    enabled: true,
                    barnesHut: {
                        gravitationalConstant: -2000,
                        centralGravity: 0.3,
                        springLength: 120,
                        springConstant: 0.04,
                        damping: 0.09,
                        avoidOverlap: 0
                    }
                }
            };

            network = new vis.Network(container, data, options);
        }

        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            initCharts();
            initNetworkGraph();
            updateStats();
        });
    </script>
</body>
</html>
        """
        return dashboard_html

    def create_templates_and_static_dirs(self, base_path: str):
        """创建模板和静态文件目录"""
        # 创建目录
        templates_dir = os.path.join(base_path, 'templates')
        static_dir = os.path.join(base_path, 'static')

        os.makedirs(templates_dir, exist_ok=True)
        os.makedirs(static_dir, exist_ok=True)

        # 创建主页模板
        index_template = """<!DOCTYPE html>
<html lang='zh-CN'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>专利知识图谱系统</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .description { text-align: center; color: #666; margin-bottom: 40px; }
        .feature { margin: 20px 0; padding: 20px; border-left: 4px solid #667eea; background: #f8f9ff; }
        .btn { display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 5px; }
        .btn:hover { background: #5a6fd8; }
        .center { text-align: center; margin-top: 30px; }
    </style>
</head>
<body>
    <div class='container'>
        <h1>🏛️ 专利知识图谱系统</h1>
        <p class='description'>智能专利知识管理与分析平台</p>

        <div class='feature'>
            <h3>📊 知识图谱构建</h3>
            <p>从专利法律法规、审查指南、复审无效决定文书中自动抽取实体和关系，构建完整的知识图谱</p>
        </div>

        <div class='feature'>
            <h3>🔍 智能查询分析</h3>
            <p>支持实体搜索、关系查询、路径分析等多种查询方式，快速获取所需知识</p>
        </div>

        <div class='feature'>
            <h3>📈 可视化展示</h3>
            <p>提供直观的图表和网络图展示，帮助用户理解复杂的知识关系</p>
        </div>

        <div class='center'>
            <a href='/dashboard' class='btn'>进入仪表板</a>
            <a href='/api/stats' class='btn'>查看统计</a>
        </div>
    </div>
</body>
</html>"""

        with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_template)

        # 创建仪表板模板
        dashboard_template = self.generate_dashboard_html()
        with open(os.path.join(templates_dir, 'dashboard.html'), 'w', encoding='utf-8') as f:
            f.write(dashboard_template)

        logger.info(f"模板文件已创建在: {templates_dir}")
        logger.info(f"静态文件目录已创建: {static_dir}")

    def run_web_server(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """运行Web服务器"""
        if not FLASK_AVAILABLE:
            raise ImportError('Flask库未安装，无法运行Web服务器')

        if not self.flask_app:
            self.setup_flask_app()

        logger.info(f"启动Web服务器: http://{host}:{port}")
        self.flask_app.run(host=host, port=port, debug=debug)

    def create_complete_pipeline(self, source_directory: str, output_directory: str):
        """创建完整的处理流程"""
        logger.info('开始完整的专利知识图谱构建流程...')

        # 1. 知识抽取
        logger.info('步骤1: 执行知识抽取')
        extraction_results = self.extractor.process_directory(
            source_directory, recursive=True, max_files=1000
        )

        # 2. 导出抽取结果
        logger.info('步骤2: 导出抽取结果')
        os.makedirs(output_directory, exist_ok=True)
        self.extractor.export_results(extraction_results, output_directory)

        # 3. 导入Neo4j
        if self.neo4j_manager:
            logger.info('步骤3: 导入Neo4j数据库')
            import_result = self.neo4j_manager.import_extraction_results(extraction_results)
            logger.info(f"导入结果: {import_result}")

        # 4. 生成报告
        logger.info('步骤4: 生成处理报告')
        self._generate_pipeline_report(extraction_results, output_directory, import_result)

        logger.info(f"完整流程完成！结果保存在: {output_directory}")

    def _generate_pipeline_report(self, results: list[ExtractionResult], output_dir: str, import_result: dict[str, Any]):
        """生成处理流程报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'processed_files': len(results),
                'total_entities': sum(len(r.entities) for r in results),
                'total_relations': sum(len(r.relations) for r in results),
                'extraction_time': sum(r.processing_stats.get('processing_time', 0) for r in results)
            },
            'import_result': import_result,
            'file_details': []
        }

        for result in results:
            report['file_details'].append({
                'source_file': result.source_file,
                'entities_count': len(result.entities),
                'relations_count': len(result.relations),
                'processing_stats': result.processing_stats
            })

        report_file = os.path.join(output_dir, 'pipeline_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"处理报告已生成: {report_file}")

# ============================================================================
# 主程序和使用示例
# ============================================================================

def main():
    """主程序"""
    logger.info('🏛️ 专利知识图谱应用系统')
    logger.info(str('=' * 50))

    # 配置
    config = {
        'extraction': {
            'batch_size': 1000,
            'confidence_threshold': 0.6
        },
        'neo4j': {
            'uri': 'bolt://localhost:7687',
            'username': 'neo4j',
            'password': 'your_password',  # 请修改为实际密码
            'database': 'patent_kg'
        }
    }

    # 创建应用实例
    app = PatentKnowledgeGraphApplication(config)

    # 初始化组件
    app.initialize_components()

    # 创建模板文件
    base_path = os.path.dirname(os.path.abspath(__file__))
    templates_path = os.path.join(base_path, 'templates')
    app.create_templates_and_static_dir(templates_path)

    # 用户选择
    logger.info("\n请选择操作:")
    logger.info('1. 运行完整的知识图谱构建流程')
    logger.info('2. 启动Web服务器')
    logger.info('3. 仅执行知识抽取')
    logger.info('4. 仅导入Neo4j数据库')

    choice = input("\n请输入选择 (1-4): ").strip()

    if choice == '1':
        source_dir = input('请输入源文档目录 (/Users/xujian/学习资料/专利): ').strip()
        if not source_dir:
            source_dir = '/Users/xujian/学习资料/专利'

        output_dir = input('请输入输出目录 (/tmp/patent_kg_output): ').strip()
        if not output_dir:
            output_dir = '/tmp/patent_kg_output'

        app.create_complete_pipeline(source_dir, output_dir)

    elif choice == '2':
        host = input('请输入主机地址 (0.0.0.0): ').strip() or '0.0.0.0'
        port = int(input('请输入端口号 (5000): ').strip() or '5000')

        app.run_web_server(host=host, port=port, debug=True)

    elif choice == '3':
        source_dir = input('请输入源文档目录: ').strip()
        max_files = int(input('请输入最大文件数 (100): ').strip() or '100')

        results = app.extractor.process_directory(source_dir, max_files=max_files)
        output_dir = f"/tmp/extraction_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        app.extractor.export_results(results, output_dir)

        logger.info(f"抽取完成，结果保存在: {output_dir}")

    elif choice == '4':
        entities_file = input('请输入实体JSON文件路径: ').strip()
        relations_file = input('请输入关系JSON文件路径: ').strip()

        if app.neo4j_manager and entities_file and relations_file:
            result = app.neo4j_manager.import_from_json(entities_file, relations_file)
            logger.info(f"导入结果: {result}")

    else:
        logger.info('无效选择')

if __name__ == '__main__':
    main()
