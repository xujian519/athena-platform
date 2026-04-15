#!/usr/bin/env python3
"""
专利知识库与工具库增强系统
Patent Knowledge Base and Tools Enhancement System

基于Athena工作平台现有的知识库与工具库基础设施，
为专利应用提供专门的知识管理和工具集成能力。

Created by Athena + 小诺 (AI助手)
Date: 2025-12-05
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    """知识类型"""
    PATENT_LAW = 'patent_law'
    EXAMINATION_GUIDE = 'examination_guide'
    COURT_INTERPRETATION = 'court_interpretation'
    TECHNICAL_STANDARD = 'technical_standard'
    PATENT_CASE = 'patent_case'
    PRACTICE_GUIDE = 'practice_guide'
    ANALYSIS_METHOD = 'analysis_method'
    FORM_TEMPLATE = 'form_template'

class ToolCategory(Enum):
    """工具类别"""
    PATENT_SEARCH = 'patent_search'
    TECHNICAL_ANALYSIS = 'technical_analysis'
    LEGAL_ANALYSIS = 'legal_analysis'
    COMMERCIAL_ANALYSIS = 'commercial_analysis'
    RISK_ASSESSMENT = 'risk_assessment'
    DOCUMENT_GENERATION = 'document_generation'
    DATA_VISUALIZATION = 'data_visualization'
    COLLABORATION = 'collaboration'

@dataclass
class PatentKnowledgeItem:
    """专利知识条目"""
    knowledge_id: str
    knowledge_type: KnowledgeType
    title: str
    content: str
    keywords: list[str] = field(default_factory=list)
    category: str = ''
    tags: list[str] = field(default_factory=list)
    relevance_score: float = 0.0
    access_count: int = 0
    last_accessed: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    author: str = ''
    source: str = ''
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class PatentTool:
    """专利工具"""
    tool_id: str
    name: str
    description: str
    category: ToolCategory
    version: str = '1.0'
    api_endpoint: str | None = None
    function_name: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    usage_count: int = 0
    success_rate: float = 1.0
    last_used: datetime | None = None
    integration_status: str = 'active'  # active, inactive, deprecated
    dependencies: list[str] = field(default_factory=list)
    documentation: str = ''
    examples: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class KnowledgeSearchQuery:
    """知识搜索查询"""
    query_id: str
    query_text: str
    knowledge_types: list[KnowledgeType] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    max_results: int = 10
    search_method: str = 'hybrid'  # text, vector, hybrid
    relevance_threshold: float = 0.3

class PatentKnowledgeToolsEnhancer:
    """专利知识库与工具库增强器"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PatentKnowledgeToolsEnhancer")

        # 知识库管理
        self.knowledge_items: dict[str, PatentKnowledgeItem] = {}
        self.knowledge_index: dict[str, list[str]] = {}  # 索引：类型、关键词、标签

        # 工具库管理
        self.patent_tools: dict[str, PatentTool] = {}
        self.tool_categories: dict[ToolCategory, list[PatentTool]] = {}

        # 现有向量数据库路径
        self.vector_db_path = '/Users/xujian/Athena工作平台/data/professional_patent/vectors/patent_rules_vectors_20251205_080132.json'

        # 统计信息
        self.stats = {
            'total_knowledge_items': 0,
            'knowledge_by_type': {},
            'total_tools': 0,
            'tools_by_category': {},
            'search_queries': 0,
            'successful_searches': 0,
            'tool_usage_count': 0
        }

        # 数据库路径
        self.db_path = '/Users/xujian/Athena工作平台/data/databases/patent_knowledge_tools.db'

        # 初始化数据库
        self._init_database()

        # 加载现有知识
        asyncio.create_task(self._load_existing_knowledge())

        # 初始化专利工具
        self._init_patent_tools()

        self.logger.info('专利知识库与工具库增强器初始化完成')

    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建知识条目表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patent_knowledge_items (
                    knowledge_id TEXT PRIMARY KEY,
                    knowledge_type TEXT,
                    title TEXT,
                    content TEXT,
                    keywords TEXT,
                    category TEXT,
                    tags TEXT,
                    relevance_score REAL,
                    access_count INTEGER,
                    last_accessed TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    author TEXT,
                    source TEXT,
                    metadata TEXT
                )
            ''')

            # 创建工具表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patent_tools (
                    tool_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    category TEXT,
                    version TEXT,
                    api_endpoint TEXT,
                    function_name TEXT,
                    parameters TEXT,
                    usage_count INTEGER,
                    success_rate REAL,
                    last_used TEXT,
                    integration_status TEXT,
                    dependencies TEXT,
                    documentation TEXT,
                    examples TEXT
                )
            ''')

            # 创建搜索日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_logs (
                    query_id TEXT PRIMARY KEY,
                    query_text TEXT,
                    knowledge_types TEXT,
                    keywords TEXT,
                    filters TEXT,
                    results_count INTEGER,
                    success INTEGER,
                    timestamp TEXT,
                    execution_time REAL
                )
            ''')

            conn.commit()
            conn.close()

            self.logger.info('专利知识库数据库初始化完成')

        except Exception as e:
            self.logger.error(f"数据库初始化失败: {str(e)}")

    async def _load_existing_knowledge(self):
        """加载现有知识"""
        try:
            self.logger.info(f"开始加载现有专利知识: {self.vector_db_path}")

            if not os.path.exists(self.vector_db_path):
                self.logger.warning(f"向量数据库文件不存在: {self.vector_db_path}")
                return

            with open(self.vector_db_path, encoding='utf-8') as f:
                data = json.load(f)

            metadata = data.get('metadata', {})
            vectors = data.get('vectors', [])

            self.logger.info(f"向量数据库信息: {metadata}")
            self.logger.info(f"向量总数: {len(vectors)}")

            loaded_count = 0
            for vector_data in vectors:
                try:
                    knowledge_type = self._determine_knowledge_type(vector_data['text'])
                    keywords = self._extract_keywords(vector_data['text'])

                    knowledge_item = PatentKnowledgeItem(
                        knowledge_id=f"vec_{vector_data['id']}",
                        knowledge_type=knowledge_type,
                        title=vector_data['text'][:100] + '...' if len(vector_data['text']) > 100 else vector_data['text'],
                        content=vector_data['text'],
                        keywords=keywords,
                        category=self._extract_category(vector_data['text']),
                        tags=[vector_data.get('category', 'patent')],
                        relevance_score=0.8,  # 默认相关性得分
                        source='vector_database',
                        author='system',
                        metadata={
                            'vector_id': vector_data['id'],
                            'vector_dimension': metadata.get('vector_dimension', 1024),
                            'model': metadata.get('model', 'unknown'),
                            'generation_time': metadata.get('generation_time', '')
                        }
                    )

                    self.knowledge_items[knowledge_item.knowledge_id] = knowledge_item
                    self._update_knowledge_index(knowledge_item)
                    loaded_count += 1

                except Exception as e:
                    self.logger.error(f"加载知识条目失败 {vector_data.get('id', 'unknown')}: {str(e)}")

            self.stats['total_knowledge_items'] = loaded_count
            self.logger.info(f"成功加载 {loaded_count} 个知识条目")

        except Exception as e:
            self.logger.error(f"加载现有知识失败: {str(e)}")

    def _determine_knowledge_type(self, content: str) -> KnowledgeType:
        """确定知识类型"""
        content_lower = content.lower()

        # 关键词映射到知识类型
        type_keywords = {
            KnowledgeType.PATENT_LAW: ['专利法', '专利法实施细则', '专利法解释'],
            KnowledgeType.EXAMINATION_GUIDE: ['审查指南', '审查规程', '审查标准'],
            KnowledgeType.COURT_INTERPRETATION: ['法院', '司法解释', '最高人民法院', '判例'],
            KnowledgeType.TECHNICAL_STANDARD: ['技术标准', '行业标准', '国家标准'],
            KnowledgeType.PATENT_CASE: ['案例', '判例', '事例', '实例'],
            KnowledgeType.PRACTICE_GUIDE: ['操作指南', '实务指南', '实践指南'],
            KnowledgeType.ANALYSIS_METHOD: ['分析方法', '评估方法', '分析方法'],
            KnowledgeType.FORM_TEMPLATE: ['模板', '格式', '范本', '表格']
        }

        # 寻找匹配的类型
        max_matches = 0
        best_type = KnowledgeType.PATENT_LAW

        for knowledge_type, keywords in type_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            if matches > max_matches:
                max_matches = matches
                best_type = knowledge_type

        return best_type

    def _extract_keywords(self, content: str) -> list[str]:
        """提取关键词"""
        # 简化的关键词提取
        common_patent_terms = [
            '新颖性', '创造性', '实用性', '专利性', '权利要求', '说明书',
            '现有技术', '对比文件', '技术方案', '技术创新', '审查意见',
            '驳回', '授权', '无效', '侵权', '诉讼', '和解', '许可',
            '专利申请', '发明专利', '实用新型', '外观设计',
            '优先权', '申请日', '公开日', '审查员', '代理机构'
        ]

        keywords = []
        content_lower = content.lower()

        for term in common_patent_terms:
            if term in content_lower:
                keywords.append(term)

        return list(set(keywords))  # 去重

    def _extract_category(self, content: str) -> str:
        """提取分类"""
        content_lower = content.lower()

        category_map = {
            '法律基础': ['专利法', '实施细则', '法律条文'],
            '审查指南': ['审查指南', '审查规程', '操作规程'],
            '司法实践': ['法院', '判例', '司法解释', '诉讼'],
            '技术标准': ['技术标准', '行业标准', '国家标凖'],
            '案例分析': ['案例', '判例', '事例', '实例'],
            '实务操作': ['操作指南', '实务指南', '实践'],
            '分析方法': ['分析方法', '评估方法', '分析技巧'],
            '文档模板': ['模板', '格式', '范本', '表格']
        }

        for category, keywords in category_map.items():
            if any(keyword in content_lower for keyword in keywords):
                return category

        return '其他'

    def _update_knowledge_index(self, knowledge_item: PatentKnowledgeItem):
        """更新知识索引"""
        # 按类型索引
        knowledge_type = knowledge_item.knowledge_type.value
        if knowledge_type not in self.knowledge_index:
            self.knowledge_index[knowledge_type] = []
        self.knowledge_index[knowledge_type].append(knowledge_item.knowledge_id)

        # 按关键词索引
        for keyword in knowledge_item.keywords:
            if f"keyword_{keyword}" not in self.knowledge_index:
                self.knowledge_index[f"keyword_{keyword}"] = []
            self.knowledge_index[f"keyword_{keyword}"].append(knowledge_item.knowledge_id)

        # 按标签索引
        for tag in knowledge_item.tags:
            if f"tag_{tag}" not in self.knowledge_index:
                self.knowledge_index[f"tag_{tag}"] = []
            self.knowledge_index[f"tag_{tag}"].append(knowledge_item.knowledge_id)

    def _init_patent_tools(self):
        """初始化专利工具"""
        tools = [
            PatentTool(
                tool_id='patent_search_cnipa',
                name='中国专利检索工具',
                description='检索中国国家知识产权局专利数据库',
                category=ToolCategory.PATENT_SEARCH,
                api_endpoint='http://pss-system.cnipa.gov.cn/',
                parameters={
                    'query': '检索关键词',
                    'field': '检索字段',
                    'date_range': '日期范围'
                },
                documentation='用于检索中国专利申请、授权专利等信息',
                examples=[
                    {
                        'name': '技术领域检索',
                        'description': '检索人工智能领域的专利',
                        'parameters': {'query': '人工智能', 'field': 'title_abstract'}
                    }
                ]
            ),
            PatentTool(
                tool_id='patent_analysis_ai',
                name='AI专利分析工具',
                description='使用AI技术进行专利分析',
                category=ToolCategory.TECHNICAL_ANALYSIS,
                function_name='analyze_patent_ai',
                parameters={
                    'patent_text': '专利文本',
                    'analysis_type': '分析类型',
                    'depth': '分析深度'
                },
                documentation='基于机器学习算法的专利智能分析',
                examples=[
                    {
                        'name': '新颖性分析',
                        'description': '分析专利的新颖性',
                        'parameters': {'patent_text': '专利内容', 'analysis_type': 'novelty'}
                    }
                ]
            ),
            PatentTool(
                tool_id='legal_risk_assessment',
                name='法律风险评估工具',
                description='评估专利的法律风险',
                category=ToolCategory.LEGAL_ANALYSIS,
                function_name='assess_legal_risk',
                parameters={
                    'patent_claims': '权利要求',
                    'prior_art': '现有技术',
                    'jurisdiction': '司法管辖区'
                },
                documentation='评估专利侵权风险、无效风险等',
                examples=[
                    {
                        'name': '侵权风险评估',
                        'description': '评估专利的侵权风险',
                        'parameters': {'patent_claims': '权利要求1', 'jurisdiction': 'CN'}
                    }
                ]
            ),
            PatentTool(
                tool_id='commercial_valuation',
                name='商业价值评估工具',
                description='评估专利的商业价值和市场潜力',
                category=ToolCategory.COMMERCIAL_ANALYSIS,
                function_name='valuate_patent',
                parameters={
                    'patent_data': '专利数据',
                    'market_info': '市场信息',
                    'technology_trend': '技术趋势'
                },
                documentation='基于市场分析和技术评估的商业价值模型',
                examples=[
                    {
                        'name': 'AI技术专利评估',
                        'description': '评估AI技术专利的商业价值',
                        'parameters': {'patent_data': '专利内容', 'market_info': '市场数据'}
                    }
                ]
            ),
            PatentTool(
                tool_id='patent_doc_generator',
                name='专利文档生成工具',
                description='自动生成专利申请文档',
                category=ToolCategory.DOCUMENT_GENERATION,
                function_name='generate_patent_docs',
                parameters={
                    'invention_title': '发明名称',
                    'technical_field': '技术领域',
                    'background': '背景技术',
                    'invention_content': '发明内容',
                    'claims': '权利要求'
                },
                documentation='根据输入信息生成规范的专利申请文件',
                examples=[
                    {
                        'name': '发明专利申请生成',
                        'description': '生成发明专利申请文件',
                        'parameters': {'invention_title': 'AI算法专利', 'invention_content': '技术方案'}
                    }
                ]
            ),
            PatentTool(
                tool_id='patent_risk_monitor',
                name='专利风险监控工具',
                description='监控专利相关的各种风险',
                category=ToolCategory.RISK_ASSESSMENT,
                function_name='monitor_patent_risks',
                parameters={
                    'patent_portfolio': '专利组合',
                    'monitoring_scope': '监控范围',
                    'alert_threshold': '告警阈值'
                },
                documentation='持续监控专利的法律、技术、市场风险',
                examples=[
                    {
                        'name': '专利组合风险监控',
                        'description': '监控专利组合的整体风险',
                        'parameters': {'patent_portfolio': '专利列表', 'monitoring_scope': 'full'}
                    }
                ]
            ),
            PatentTool(
                tool_id='patent_data_visualizer',
                name='专利数据可视化工具',
                description='专利数据的可视化展示',
                category=ToolCategory.DATA_VISUALIZATION,
                function_name='visualize_patent_data',
                parameters={
                    'patent_data': '专利数据',
                    'chart_type': '图表类型',
                    'visualization_options': '可视化选项'
                },
                documentation='将专利分析结果转化为可视化图表',
                examples=[
                    {
                        'name': '技术趋势图',
                        'description': '生成技术发展趋势图',
                        'parameters': {'patent_data': '专利数据', 'chart_type': 'trend'}
                    }
                ]
            ),
            PatentTool(
                tool_id='patent_collaboration',
                name='专利协作工具',
                description='支持多人协作的专利管理平台',
                category=ToolCategory.COLLABORATION,
                api_endpoint='http://patent-collaboration.platform/',
                parameters={
                    'project_id': '项目ID',
                    'team_members': '团队成员',
                    'collaboration_features': '协作功能'
                },
                documentation='提供专利申请的团队协作管理功能',
                examples=[
                    {
                        'name': '专利申请协作',
                        'description': '多人协作完成专利申请',
                        'parameters': {'project_id': 'proj_001', 'team_members': ['成员1', '成员2']}
                    }
                ]
            )
        ]

        for tool in tools:
            self.patent_tools[tool.tool_id] = tool
            if tool.category not in self.tool_categories:
                self.tool_categories[tool.category] = []
            self.tool_categories[tool.category].append(tool)

        self.stats['total_tools'] = len(tools)
        self.logger.info(f"初始化了 {len(tools)} 个专利工具")

    async def search_knowledge(self, query: KnowledgeSearchQuery) -> dict[str, Any]:
        """搜索知识"""
        try:
            start_time = time.time()
            self.logger.info(f"搜索知识: {query.query_text}")

            # 检查索引
            candidate_ids = set()

            # 基于知识类型过滤
            if query.knowledge_types:
                for knowledge_type in query.knowledge_types:
                    type_key = knowledge_type.value
                    if type_key in self.knowledge_index:
                        candidate_ids.update(self.knowledge_index[type_key])
            else:
                # 搜索所有知识
                for item in self.knowledge_items.values():
                    candidate_ids.add(item.knowledge_id)

            # 基于关键词过滤
            for keyword in query.keywords:
                key_key = f"keyword_{keyword}"
                if key_key in self.knowledge_index:
                    keyword_ids = set(self.knowledge_index[key_key])
                    candidate_ids = candidate_ids.intersection(keyword_ids)

            # 基于标签过滤
            if 'tags' in query.filters:
                for tag in query.filters['tags']:
                    tag_key = f"tag_{tag}"
                    if tag_key in self.knowledge_index:
                        tag_ids = set(self.knowledge_index[tag_key])
                        candidate_ids = candidate_ids.intersection(tag_ids)

            # 获取候选知识条目
            candidates = [
                self.knowledge_items[kid] for kid in candidate_ids
                if kid in self.knowledge_items
            ]

            # 计算相关性得分
            results = []
            for item in candidates:
                # 简化的相关性计算
                relevance = self._calculate_relevance(item, query.query_text, query.keywords)

                if relevance >= query.relevance_threshold:
                    # 更新访问统计
                    item.access_count += 1
                    item.last_accessed = datetime.now()

                    results.append({
                        'knowledge_id': item.knowledge_id,
                        'knowledge_type': item.knowledge_type.value,
                        'title': item.title,
                        'content_preview': item.content[:200] + '...' if len(item.content) > 200 else item.content,
                        'relevance_score': relevance,
                        'category': item.category,
                        'tags': item.tags,
                        'access_count': item.access_count,
                        'author': item.author,
                        'source': item.source
                    })

            # 按相关性排序
            results.sort(key=lambda x: x['relevance_score'], reverse=True)

            # 限制结果数量
            results = results[:query.max_results]

            # 记录搜索日志
            execution_time = time.time() - start_time
            await self._log_search(query, len(results), True, execution_time)

            self.stats['search_queries'] += 1
            self.stats['successful_searches'] += 1

            self.logger.info(f"知识搜索完成，返回 {len(results)} 个结果")
            return {
                'success': True,
                'query_id': query.query_id,
                'results': results,
                'total_found': len(results),
                'execution_time': execution_time
            }

        except Exception as e:
            self.logger.error(f"知识搜索失败: {str(e)}")
            await self._log_search(query, 0, False, 0)
            self.stats['search_queries'] += 1
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_relevance(self, item: PatentKnowledgeItem, query_text: str, keywords: list[str]) -> float:
        """计算相关性得分"""
        try:
            score = 0.0

            # 基于标题匹配
            query_words = set(query_text.lower().split())
            title_words = set(item.title.lower().split())
            title_match = len(query_words.intersection(title_words)) / len(query_words) if query_words else 0
            score += title_match * 0.4

            # 基于关键词匹配
            if keywords:
                item_keywords = set(item.keywords)
                keyword_match = len(set(keywords).intersection(item_keywords)) / len(keywords)
                score += keyword_match * 0.4

            # 基于访问频率（热门内容加分）
            if item.access_count > 0:
                popularity_score = min(item.access_count / 100.0, 1.0) * 0.2
                score += popularity_score

            return min(1.0, score)

        except Exception as e:
            self.logger.error(f"计算相关性失败: {str(e)}")
            return 0.0

    async def _log_search(self, query: KnowledgeSearchQuery, results_count: int, success: bool, execution_time: float):
        """记录搜索日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO search_logs
                (query_id, query_text, knowledge_types, keywords, filters, results_count, success, timestamp, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                query.query_id,
                query.query_text,
                json.dumps([kt.value for kt in query.knowledge_types], ensure_ascii=False),
                json.dumps(query.keywords, ensure_ascii=False),
                json.dumps(query.filters, ensure_ascii=False),
                results_count,
                int(success),
                datetime.now().isoformat(),
                execution_time
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"记录搜索日志失败: {str(e)}")

    async def get_patent_tools(self, category: ToolCategory | None = None) -> dict[str, Any]:
        """获取专利工具"""
        try:
            if category:
                tools = self.tool_categories.get(category, [])
            else:
                tools = list(self.patent_tools.values())

            tool_info = []
            for tool in tools:
                # 增加工具使用信息
                tool_usage = {
                    'tool_id': tool.tool_id,
                    'name': tool.name,
                    'description': tool.description,
                    'category': tool.category.value,
                    'version': tool.version,
                    'usage_count': tool.usage_count,
                    'success_rate': tool.success_rate,
                    'last_used': tool.last_used.isoformat() if tool.last_used else None,
                    'integration_status': tool.integration_status,
                    'documentation': tool.documentation,
                    'parameters': tool.parameters,
                    'examples': tool.examples
                }
                tool_info.append(tool_usage)

            return {
                'success': True,
                'tools': tool_info,
                'total_count': len(tool_info),
                'categories': list(self.tool_categories.keys()) if category is None else [category.value]
            }

        except Exception as e:
            self.logger.error(f"获取专利工具失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def use_patent_tool(self, tool_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """使用专利工具"""
        try:
            if tool_id not in self.patent_tools:
                return {
                    'success': False,
                    'error': f"工具不存在: {tool_id}"
                }

            tool = self.patent_tools[tool_id]

            # 检查工具状态
            if tool.integration_status != 'active':
                return {
                    'success': False,
                    'error': f"工具未激活: {tool.integration_status}"
                }

            # 模拟工具执行
            self.logger.info(f"使用专利工具: {tool.name}")

            # 更新使用统计
            tool.usage_count += 1
            tool.last_used = datetime.now()

            # 模拟执行结果
            result = {
                'success': True,
                'tool_id': tool_id,
                'tool_name': tool.name,
                'execution_id': f"exec_{tool_id}_{int(time.time())}",
                'parameters': parameters,
                'result': f"工具 {tool.name} 执行成功",
                'execution_time': 0.5,
                'timestamp': datetime.now().isoformat()
            }

            # 更新统计
            self.stats['tool_usage_count'] += 1

            return result

        except Exception as e:
            self.logger.error(f"使用专利工具失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()

        # 计算知识类型分布
        for item in self.knowledge_items.values():
            knowledge_type = item.knowledge_type.value
            stats['knowledge_by_type'][knowledge_type] = \
                stats['knowledge_by_type'].get(knowledge_type, 0) + 1

        # 计算工具类别分布
        for category, tools in self.tool_categories.items():
            stats['tools_by_category'][category.value] = len(tools)

        # 计算搜索成功率
        if stats['search_queries'] > 0:
            stats['search_success_rate'] = stats['successful_searches'] / stats['search_queries']
        else:
            stats['search_success_rate'] = 0.0

        return stats

    async def add_knowledge_item(self, knowledge_item: PatentKnowledgeItem) -> dict[str, Any]:
        """添加知识条目"""
        try:
            self.knowledge_items[knowledge_item.knowledge_id] = knowledge_item
            self._update_knowledge_index(knowledge_item)

            # 存储到数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO patent_knowledge_items
                (knowledge_id, knowledge_type, title, content, keywords, category, tags,
                 relevance_score, access_count, last_accessed, created_at, updated_at,
                 author, source, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                knowledge_item.knowledge_id,
                knowledge_item.knowledge_type.value,
                knowledge_item.title,
                knowledge_item.content,
                json.dumps(knowledge_item.keywords, ensure_ascii=False),
                knowledge_item.category,
                json.dumps(knowledge_item.tags, ensure_ascii=False),
                knowledge_item.relevance_score,
                knowledge_item.access_count,
                knowledge_item.last_accessed.isoformat() if knowledge_item.last_accessed else None,
                knowledge_item.created_at.isoformat(),
                knowledge_item.updated_at.isoformat(),
                knowledge_item.author,
                knowledge_item.source,
                json.dumps(knowledge_item.metadata, ensure_ascii=False)
            ))

            conn.commit()
            conn.close()

            # 更新统计
            self.stats['total_knowledge_items'] += 1

            self.logger.info(f"知识条目添加成功: {knowledge_item.knowledge_id}")
            return {
                'success': True,
                'knowledge_id': knowledge_item.knowledge_id
            }

        except Exception as e:
            self.logger.error(f"添加知识条目失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# 测试代码
async def test_patent_knowledge_tools_enhancer():
    """测试专利知识库与工具库增强系统"""
    enhancer = PatentKnowledgeToolsEnhancer()

    logger.info(str('=' * 60))
    logger.info('专利知识库与工具库增强系统测试')
    logger.info(str('=' * 60))

    # 等待知识加载完成
    await asyncio.sleep(1)

    # 测试知识搜索
    logger.info("\n1. 知识搜索测试:")
    search_query = KnowledgeSearchQuery(
        query_id='test_001',
        query_text='专利审查指南',
        keywords=['审查', '指南'],
        knowledge_types=[KnowledgeType.EXAMINATION_GUIDE],
        max_results=5
    )

    search_result = await enhancer.search_knowledge(search_query)
    logger.info(f"   搜索成功: {search_result['success']}")
    logger.info(f"   结果数量: {search_result.get('total_found', 0)}")
    logger.info(f"   执行时间: {search_result.get('execution_time', 0):.3f}秒")

    # 测试获取工具
    logger.info("\n2. 获取专利工具测试:")
    tools_result = await enhancer.get_patent_tools()
    logger.info(f"   获取成功: {tools_result['success']}")
    logger.info(f"   工具总数: {tools_result.get('total_count', 0)}")
    logger.info(f"   工具类别: {len(tools_result.get('categories', []))}")

    # 测试使用工具
    logger.info("\n3. 使用专利工具测试:")
    if tools_result['success'] and tools_result['tools']:
        test_tool = tools_result['tools'][0]
        use_result = await enhancer.use_patent_tool(
            test_tool['tool_id'],
            {'query': 'AI专利', 'field': 'title'}
        )
        logger.info(f"   工具使用成功: {use_result['success']}")
        logger.info(f"   工具名称: {use_result.get('tool_name', '')}")

    # 测试添加知识条目
    logger.info("\n4. 添加知识条目测试:")
    new_knowledge = PatentKnowledgeItem(
        knowledge_id='test_knowledge_001',
        knowledge_type=KnowledgeType.PRACTICE_GUIDE,
        title='专利申请实践指南',
        content='本文档提供了专利申请的详细操作指南...',
        keywords=['专利', '申请', '指南'],
        category='实务操作',
        tags=['新知识', '测试'],
        author='test_user',
        source='manual_input'
    )

    add_result = await enhancer.add_knowledge_item(new_knowledge)
    logger.info(f"   添加成功: {add_result['success']}")

    # 测试统计信息
    logger.info("\n5. 统计信息测试:")
    stats = enhancer.get_statistics()
    logger.info(f"   知识条目总数: {stats['total_knowledge_items']}")
    logger.info(f"   工具总数: {stats['total_tools']}")
    logger.info(f"   搜索查询数: {stats['search_queries']}")
    logger.info(f"   搜索成功率: {stats['search_success_rate']:.3f}")

    return {
        'knowledge_search': search_result['success'],
        'tools_retrieved': tools_result['success'],
        'tool_used': use_result.get('success', False),
        'knowledge_added': add_result['success'],
        'statistics_collected': True
    }


if __name__ == '__main__':
    asyncio.run(test_patent_knowledge_tools_enhancer())
