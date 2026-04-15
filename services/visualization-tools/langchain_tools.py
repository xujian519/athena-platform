"""
LangChain可视化工具封装
将draw.io、ECharts和Excalidraw封装为LangChain工具
"""

import json
import tempfile
from datetime import datetime
from typing import Any

try:
    from langchain.tools import BaseTool
except ImportError:
    BaseTool = None  # type: ignore[assignment,misc]  # 可选依赖未安装

# 导入分析器
from visualization_insights import VisualizationAnalyzer


class DrawIOTool(BaseTool):
    """Draw.io流程图工具"""
    name: str = 'drawio_diagram_creator'
    description: str = """
    创建专业的流程图、架构图、UML图和技术图表。
    适用于：系统架构设计、业务流程建模、技术方案图解。

    输入要求：
    - diagram_type: 图表类型（flowchart, uml, architecture, network等）
    - content: 图表内容的详细描述
    - style: 样式偏好（professional, modern, simple等）

    输出：图表的SVG/PNG格式数据和可编辑的draw.io链接。
    """
    analyzer: 'VisualizationAnalyzer' = None

    def __init__(self):
        super().__init__()
        self.analyzer = VisualizationAnalyzer()

    def _run(self, query: str) -> str:
        """执行Draw.io图表创建"""
        try:
            # 解析查询参数
            params = self._parse_query(query)

            # 生成draw.io XML
            diagram_xml = self._generate_diagram_xml(params)

            # 创建临时文件保存图表
            temp_file = self._save_diagram(diagram_xml, params.get('format', 'svg'))

            # 生成可分享链接
            share_link = self._generate_share_link(diagram_xml)

            result = {
                'success': True,
                'tool': 'drawio',
                'diagram_type': params.get('diagram_type', 'flowchart'),
                'output_file': temp_file,
                'share_link': share_link,
                'created_at': datetime.now().isoformat()
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e),
                'tool': 'drawio'
            }, ensure_ascii=False)

    async def _arun(self, query: str) -> str:
        """异步执行"""
        return self._run(query)

    def _parse_query(self, query: str) -> dict[str, Any]:
        """解析查询参数"""
        # 简化的参数解析（实际实现中可以使用NLP）
        params = {
            'diagram_type': 'flowchart',
            'content': query,
            'style': 'professional',
            'format': 'svg'
        }

        # 检测图表类型
        if 'architecture' in query.lower() or '架构' in query:
            params['diagram_type'] = 'architecture'
        elif 'uml' in query.lower():
            params['diagram_type'] = 'uml'
        elif 'network' in query.lower() or '网络' in query:
            params['diagram_type'] = 'network'

        return params

    def _generate_diagram_xml(self, params: dict[str, Any]) -> str:
        """生成draw.io XML格式的图表"""
        # 简化的XML生成（实际实现中需要更复杂的逻辑）
        diagram_type = params.get('diagram_type', 'flowchart')
        content = params.get('content', '')

        # 基于类型生成不同的XML结构
        if diagram_type == 'flowchart':
            return self._create_flowchart_xml(content)
        elif diagram_type == 'architecture':
            return self._create_architecture_xml(content)
        elif diagram_type == 'uml':
            return self._create_uml_xml(content)
        else:
            return self._create_generic_xml(content)

    def _create_flowchart_xml(self, content: str) -> str:
        """创建流程图XML"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host='app.diagrams.net'>
  <diagram name='Page-1' id='page-1'>
    <mx_graph_model dx='1422' dy='762' grid='1' grid_size='10' guides='1' tooltips='1' connect='1' arrows='1' fold='1' page='1' page_scale='1' page_width='827' page_height='1169' math='0' shadow='0'>
      <root>
        <mx_cell id='0' />
        <mx_cell id='1' parent='0' />
        <mx_cell id='2' value='{content}' style='rounded=0;white_space=wrap;html=1;' vertex='1' parent='1'>
          <mx_geometry x='160' y='200' width='120' height='60' as='geometry' />
        </mx_cell>
        <mx_cell id='3' value='下一步' style='rounded=0;white_space=wrap;html=1;' vertex='1' parent='1'>
          <mx_geometry x='360' y='200' width='120' height='60' as='geometry' />
        </mx_cell>
        <mx_cell id='4' edge='1' parent='1' source='2' target='3'>
          <mx_geometry relative='1' as='geometry' />
        </mx_cell>
      </root>
    </mx_graph_model>
  </diagram>
</mxfile>'''

    def _create_architecture_xml(self, content: str) -> str:
        """创建架构图XML"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host='app.diagrams.net'>
  <diagram name='Architecture' id='arch-page'>
    <mx_graph_model dx='1422' dy='762' grid='1' grid_size='10' guides='1' tooltips='1' connect='1' arrows='1' fold='1' page='1' page_scale='1' page_width='827' page_height='1169'>
      <root>
        <mx_cell id='0' />
        <mx_cell id='1' parent='0' />
        <mx_cell id='2' value='前端层' style='rounded=1;white_space=wrap;html=1;fill_color=#dae8fc;stroke_color=#6c8ebf;' vertex='1' parent='1'>
          <mx_geometry x='120' y='120' width='120' height='60' as='geometry' />
        </mx_cell>
        <mx_cell id='3' value='API网关' style='rounded=1;white_space=wrap;html=1;fill_color=#d5e8d4;stroke_color=#82b366;' vertex='1' parent='1'>
          <mx_geometry x='320' y='120' width='120' height='60' as='geometry' />
        </mx_cell>
        <mx_cell id='4' value='后端服务' style='rounded=1;white_space=wrap;html=1;fill_color=#fff2cc;stroke_color=#d6b656;' vertex='1' parent='1'>
          <mx_geometry x='520' y='120' width='120' height='60' as='geometry' />
        </mx_cell>
        <mx_cell id='5' value='数据库' style='shape=cylinder3;white_space=wrap;html=1;bounded_lbl=1;background_outline=1;fill_color=#f8cecc;stroke_color=#b85450;' vertex='1' parent='1'>
          <mx_geometry x='720' y='120' width='120' height='60' as='geometry' />
        </mx_cell>
      </root>
    </mx_graph_model>
  </diagram>
</mxfile>'''

    def _create_uml_xml(self, content: str) -> str:
        """创建UML图XML"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host='app.diagrams.net'>
  <diagram name='UML' id='uml-page'>
    <mx_graph_model dx='1422' dy='762' grid='1' grid_size='10' guides='1' tooltips='1' connect='1' arrows='1' fold='1' page='1' page_scale='1' page_width='827' page_height='1169'>
      <root>
        <mx_cell id='0' />
        <mx_cell id='1' parent='0' />
        <mx_cell id='2' value='User Class' style='swimlane;font_style=1;align=center;vertical_align=top;child_layout=stack_layout;horizontal=1;start_size=30;horizontal_stack=0;resize_parent=1;resize_parent_max=0;resize_last=0;collapsible=1;margin_bottom=0;' vertex='1' parent='1'>
          <mx_geometry x='100' y='100' width='200' height='150' as='geometry' />
        </mx_cell>
        <mx_cell id='3' value='+ name: String' style='text;stroke_color=none;fill_color=none;align=left;vertical_align=top;spacing_left=4;spacing_right=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];port_constraint=eastwest;' vertex='1' parent='2'>
          <mx_geometry y='30' width='200' height='26' as='geometry' />
        </mx_cell>
        <mx_cell id='4' value='+ login()' style='text;stroke_color=none;fill_color=none;align=left;vertical_align=top;spacing_left=4;spacing_right=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];port_constraint=eastwest;' vertex='1' parent='2'>
          <mx_geometry y='56' width='200' height='26' as='geometry' />
        </mx_cell>
      </root>
    </mx_graph_model>
  </diagram>
</mxfile>'''

    def _create_generic_xml(self, content: str) -> str:
        """创建通用图表XML"""
        return self._create_flowchart_xml(content)

    def _save_diagram(self, xml_content: str, format_type: str) -> str:
        """保存图表到临时文件"""
        temp_file = tempfile.NamedTemporaryFile(
            suffix=f'.{format_type}',
            delete=False,
            mode='w',
            encoding='utf-8'
        )
        temp_file.write(xml_content)
        temp_file.close()
        return temp_file.name

    def _generate_share_link(self, xml_content: str) -> str:
        """生成可分享的draw.io链接"""
        # 实际实现中需要将XML编码并生成URL
        encoded_xml = xml_content.replace('\n', '').replace(' ', '%20')
        return f"https://app.diagrams.net/?xml={encoded_xml}"


class EChartsTool(BaseTool):
    """ECharts数据可视化工具"""
    name: str = 'echarts_visualizer'
    description: str = """
    创建专业的数据图表和可视化仪表板。
    适用于：数据分析、业务报表、实时监控、统计展示。

    输入要求：
    - chart_type: 图表类型（line, bar, pie, scatter等）
    - data: 数据内容（JSON格式或描述）
    - title: 图表标题
    - style: 样式配置（颜色、主题等）

    输出：交互式HTML图表和配置代码。
    """
    analyzer: 'VisualizationAnalyzer' = None

    def __init__(self):
        super().__init__()
        self.analyzer = VisualizationAnalyzer()

    def _run(self, query: str) -> str:
        """执行ECharts图表创建"""
        try:
            # 解析查询参数
            params = self._parse_query(query)

            # 生成ECharts配置
            chart_config = self._generate_chart_config(params)

            # 创建HTML文件
            html_file = self._create_html_chart(chart_config, params)

            result = {
                'success': True,
                'tool': 'echarts',
                'chart_type': params.get('chart_type', 'line'),
                'html_file': html_file,
                'config': chart_config,
                'created_at': datetime.now().isoformat()
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e),
                'tool': 'echarts'
            }, ensure_ascii=False)

    async def _arun(self, query: str) -> str:
        """异步执行"""
        return self._run(query)

    def _parse_query(self, query: str) -> dict[str, Any]:
        """解析查询参数"""
        params = {
            'chart_type': 'line',
            'data': [],
            'title': '数据图表',
            'style': 'modern'
        }

        # 检测图表类型
        chart_types = {
            'line': ['line', '折线', '趋势'],
            'bar': ['bar', '柱状', '条形'],
            'pie': ['pie', '饼图', '占比'],
            'scatter': ['scatter', '散点', '分布'],
            'area': ['area', '面积', '区域']
        }

        for chart_type, keywords in chart_types.items():
            if any(keyword in query.lower() for keyword in keywords):
                params['chart_type'] = chart_type
                break

        # 模拟数据提取（实际实现中需要更复杂的数据解析）
        params['data'] = self._extract_data_from_query(query)

        return params

    def _extract_data_from_query(self, query: str) -> list[dict[str, Any]]:
        """从查询中提取数据"""
        # 简化的数据提取（实际实现中需要NLP）
        if 'sales' in query.lower() or '销售' in query:
            return [
                {'name': 'Q1', 'value': 120},
                {'name': 'Q2', 'value': 200},
                {'name': 'Q3', 'value': 150},
                {'name': 'Q4', 'value': 280}
            ]
        elif 'user' in query.lower() or '用户' in query:
            return [
                {'name': '1月', 'value': 1000},
                {'name': '2月', 'value': 1200},
                {'name': '3月', 'value': 1500},
                {'name': '4月', 'value': 1800}
            ]
        else:
            return [
                {'name': 'A', 'value': 10},
                {'name': 'B', 'value': 20},
                {'name': 'C', 'value': 30},
                {'name': 'D', 'value': 40}
            ]

    def _generate_chart_config(self, params: dict[str, Any]) -> dict[str, Any]:
        """生成ECharts配置"""
        chart_type = params.get('chart_type', 'line')
        data = params.get('data', [])
        title = params.get('title', '数据图表')

        # 基础配置
        config = {
            'title': {'text': title, 'left': 'center'},
            'tooltip': {'trigger': 'item'},
            'legend': {'data': [item['name'] for item in data]},
            'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'contain_label': True}
        }

        # 根据图表类型生成不同配置
        if chart_type == 'line':
            config.update({
                'x_axis': {
                    'type': 'category',
                    'data': [item['name'] for item in data]
                },
                'y_axis': {'type': 'value'},
                'series': [{
                    'name': '数值',
                    'type': 'line',
                    'data': [item['value'] for item in data],
                    'smooth': True
                }]
            })
        elif chart_type == 'bar':
            config.update({
                'x_axis': {
                    'type': 'category',
                    'data': [item['name'] for item in data]
                },
                'y_axis': {'type': 'value'},
                'series': [{
                    'name': '数值',
                    'type': 'bar',
                    'data': [item['value'] for item in data]
                }]
            })
        elif chart_type == 'pie':
            config['series'] = [{
                'name': '数值',
                'type': 'pie',
                'radius': '50%',
                'data': data
            }]
            # 饼图不需要坐标轴
            if 'x_axis' in config:
                del config['x_axis']
            if 'y_axis' in config:
                del config['y_axis']
            if 'grid' in config:
                del config['grid']

        return config

    def _create_html_chart(self, config: dict[str, Any], params: dict[str, Any]) -> str:
        """创建HTML图表文件"""
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <title>ECharts图表</title>
    <script src='https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js'></script>
</head>
<body>
    <div id='chart' style='width: 800px; height: 600px;'></div>
    <script>
        // 初始化图表
        var my_chart = echarts.init(document.get_element_by_id('chart'));

        // 配置项
        var option = {json.dumps(config, ensure_ascii=False)};

        // 使用配置项显示图表
        my_chart.set_option(option);

        // 响应式
        window.add_event_listener('resize', function() {{
            my_chart.resize();
        }});
    </script>
</body>
</html>'''

        temp_file = tempfile.NamedTemporaryFile(
            suffix='.html',
            delete=False,
            mode='w',
            encoding='utf-8'
        )
        temp_file.write(html_content)
        temp_file.close()
        return temp_file.name


class ExcalidrawTool(BaseTool):
    """Excalidraw手绘图工具"""
    name: str = 'excalidraw_sketch'
    description: str = """
    创建手绘风格的草图、思维导图和协作白板。
    适用于：UI设计草图、团队协作、思维导图、创意表达。

    输入要求：
    - sketch_type: 草图类型（mindmap, wireframe, whiteboard等）
    - content: 草图内容描述
    - style: 手绘风格（rough, clean, colorful等）

    输出：Excalidraw可编辑链接和JSON文件。
    """
    analyzer: 'VisualizationAnalyzer' = None

    def __init__(self):
        super().__init__()
        self.analyzer = VisualizationAnalyzer()

    def _run(self, query: str) -> str:
        """执行Excalidraw草图创建"""
        try:
            # 解析查询参数
            params = self._parse_query(query)

            # 生成Excalidraw JSON
            excalidraw_json = self._generate_excalidraw_json(params)

            # 保存JSON文件
            json_file = self._save_excalidraw_json(excalidraw_json)

            # 生成协作链接
            collaboration_link = self._generate_collaboration_link(excalidraw_json)

            result = {
                'success': True,
                'tool': 'excalidraw',
                'sketch_type': params.get('sketch_type', 'whiteboard'),
                'json_file': json_file,
                'collaboration_link': collaboration_link,
                'created_at': datetime.now().isoformat()
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e),
                'tool': 'excalidraw'
            }, ensure_ascii=False)

    async def _arun(self, query: str) -> str:
        """异步执行"""
        return self._run(query)

    def _parse_query(self, query: str) -> dict[str, Any]:
        """解析查询参数"""
        params = {
            'sketch_type': 'whiteboard',
            'content': query,
            'style': 'rough'
        }

        # 检测草图类型
        if 'mindmap' in query.lower() or '思维导图' in query:
            params['sketch_type'] = 'mindmap'
        elif 'wireframe' in query.lower() or '线框' in query:
            params['sketch_type'] = 'wireframe'
        elif 'ui' in query.lower() or '界面' in query:
            params['sketch_type'] = 'ui_mockup'

        return params

    def _generate_excalidraw_json(self, params: dict[str, Any]) -> dict[str, Any]:
        """生成Excalidraw JSON格式"""
        sketch_type = params.get('sketch_type', 'whiteboard')
        content = params.get('content', '')

        if sketch_type == 'mindmap':
            return self._create_mindmap_json(content)
        elif sketch_type == 'wireframe':
            return self._create_wireframe_json(content)
        elif sketch_type == 'ui_mockup':
            return self._create_ui_mockup_json(content)
        else:
            return self._create_whiteboard_json(content)

    def _create_mindmap_json(self, content: str) -> dict[str, Any]:
        """创建思维导图JSON"""
        return {
            'type': 'excalidraw',
            'version': 2,
            'source': 'https://excalidraw.com',
            'elements': [
                {
                    'id': 'center',
                    'type': 'text',
                    'x': 400,
                    'y': 300,
                    'width': 200,
                    'height': 50,
                    'text': content,
                    'font_size': 20,
                    'font_family': 1,
                    'text_align': 'center',
                    'vertical_align': 'middle'
                },
                {
                    'id': 'branch1',
                    'type': 'text',
                    'x': 200,
                    'y': 200,
                    'width': 150,
                    'height': 40,
                    'text': '分支1',
                    'font_size': 16
                },
                {
                    'id': 'branch2',
                    'type': 'text',
                    'x': 600,
                    'y': 200,
                    'width': 150,
                    'height': 40,
                    'text': '分支2',
                    'font_size': 16
                }
            ]
        }

    def _create_wireframe_json(self, content: str) -> dict[str, Any]:
        """创建线框图JSON"""
        return {
            'type': 'excalidraw',
            'version': 2,
            'source': 'https://excalidraw.com',
            'elements': [
                {
                    'id': 'header',
                    'type': 'rectangle',
                    'x': 100,
                    'y': 100,
                    'width': 600,
                    'height': 80,
                    'stroke_color': '#1e1e1e',
                    'background_color': '#f5f5f5',
                    'fill_style': 'hachure'
                },
                {
                    'id': 'content',
                    'type': 'rectangle',
                    'x': 100,
                    'y': 200,
                    'width': 600,
                    'height': 400,
                    'stroke_color': '#1e1e1e',
                    'background_color': '#ffffff',
                    'fill_style': 'hachure'
                },
                {
                    'id': 'footer',
                    'type': 'rectangle',
                    'x': 100,
                    'y': 620,
                    'width': 600,
                    'height': 60,
                    'stroke_color': '#1e1e1e',
                    'background_color': '#f5f5f5',
                    'fill_style': 'hachure'
                }
            ]
        }

    def _create_ui_mockup_json(self, content: str) -> dict[str, Any]:
        """创建UI原型JSON"""
        return self._create_wireframe_json(content)

    def _create_whiteboard_json(self, content: str) -> dict[str, Any]:
        """创建白板JSON"""
        return {
            'type': 'excalidraw',
            'version': 2,
            'source': 'https://excalidraw.com',
            'elements': [
                {
                    'id': 'note1',
                    'type': 'rectangle',
                    'x': 200,
                    'y': 200,
                    'width': 200,
                    'height': 150,
                    'stroke_color': '#e03131',
                    'background_color': '#ffec99',
                    'fill_style': 'hachure'
                },
                {
                    'id': 'text1',
                    'type': 'text',
                    'x': 250,
                    'y': 250,
                    'width': 100,
                    'height': 50,
                    'text': content,
                    'font_size': 16,
                    'font_family': 1
                }
            ]
        }

    def _save_excalidraw_json(self, json_data: dict[str, Any]) -> str:
        """保存Excalidraw JSON文件"""
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.json',
            delete=False,
            mode='w',
            encoding='utf-8'
        )
        json.dump(json_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        return temp_file.name

    def _generate_collaboration_link(self, json_data: dict[str, Any]) -> str:
        """生成协作链接"""
        # 实际实现中需要将JSON编码并生成Excalidraw链接
        json_str = json.dumps(json_data)
        encoded_json = json_str.replace('\n', '').replace(' ', '%20')
        return f"https://excalidraw.com/#json={encoded_json}"


class VisualizationToolManager:
    """可视化工具管理器"""

    def __init__(self):
        self.tools = [
            DrawIOTool(),
            EChartsTool(),
            ExcalidrawTool()
        ]
        self.analyzer = VisualizationAnalyzer()

    def get_all_tools(self) -> list[BaseTool]:
        """获取所有工具"""
        return self.tools

    def recommend_tool(self, query: str) -> BaseTool:
        """基于查询推荐最合适的工具"""
        # 使用分析器推荐工具
        tool_name = self.analyzer.get_tool_recommendation(query, {})

        for tool in self.tools:
            if tool_name.lower() in tool.name.lower():
                return tool

        return self.tools[0]  # 默认返回第一个工具

    def get_tool_by_name(self, name: str) -> BaseTool | None:
        """根据名称获取工具"""
        for tool in self.tools:
            if name.lower() in tool.name.lower():
                return tool
        return None

# 全局工具管理器实例
visualization_tool_manager = VisualizationToolManager()
