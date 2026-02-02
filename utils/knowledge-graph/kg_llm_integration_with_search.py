#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena知识图谱LLM集成系统 - 搜索引擎增强版
Knowledge Graph LLM Integration with Search Engine Enhancement

集成外部搜索引擎的智能问答和推理系统

作者: Athena AI系统
创建时间: 2025-12-08
版本: 2.0.0
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from external_search_engine import SearchIntegrationService, SearchScope
    from neo4j import GraphDatabase
    LLM_SEARCH_INTEGRATION_AVAILABLE = True
except ImportError:
    logger.info('⚠️ 依赖库未安装')
    LLM_SEARCH_INTEGRATION_AVAILABLE = False

@dataclass
class EnhancedQARequest:
    """增强问答请求"""
    question: str
    scope: str = 'general'
    include_external_search: bool = True
    include_knowledge_graph: bool = True
    search_depth: int = 3  # 搜索深度

@dataclass
class EnhancedQAResponse:
    """增强问答响应"""
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    knowledge_graph_insights: Dict[str, Any]
    external_search_results: List[Dict[str, Any]]
    reasoning_process: List[str]
    confidence_score: float
    execution_time: float
    timestamp: str

class EnhancedKnowledgeGraphLLMIntegration:
    """集成搜索引擎的知识图谱LLM系统"""

    def __init__(self):
        self.driver = None
        self.search_service = None

        if LLM_SEARCH_INTEGRATION_AVAILABLE:
            self.setup_neo4j()
            self.setup_search_service()
            self.setup_llm_clients()

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

    def setup_search_service(self) -> Any:
        """设置搜索服务"""
        try:
            self.search_service = SearchIntegrationService()
            logger.info('✅ 搜索服务初始化成功')
        except Exception as e:
            logger.info(f"❌ 搜索服务初始化失败: {str(e)}")
            self.search_service = None

    def setup_llm_clients(self) -> Any:
        """设置LLM客户端"""
        # 这里可以集成不同的LLM服务
        self.llm_clients = {
            'claude': self._claude_client,
            'openai': self._openai_client,
            'local': self._local_client,
            'enhanced': self._enhanced_client  # 基于搜索的增强客户端
        }

    def _claude_client(self, prompt: str) -> str:
        """Claude客户端"""
        # 模拟Claude的响应，可以集成真实的Claude API
        return self._simulate_llm_response('Claude', prompt)

    def _openai_client(self, prompt: str) -> str:
        """OpenAI客户端"""
        # 模拟GPT的响应
        return self._simulate_llm_response('GPT', prompt)

    def _local_client(self, prompt: str) -> str:
        """本地模型客户端"""
        # 模拟本地模型的响应
        return self._simulate_llm_response('Local', prompt)

    def _enhanced_client(self, prompt: str, context: Dict = None) -> str:
        """基于搜索的增强客户端"""
        # 利用搜索结果增强回答
        if context and 'external_search_results' in context:
            enhanced_prompt = f"""
基于以下搜索结果和知识图谱信息，请提供详细准确的回答：

搜索结果：
{json.dumps(context['external_search_results'][:3], ensure_ascii=False, indent=2)}

知识图谱信息：
{json.dumps(context.get('knowledge_graph_insights', {}), ensure_ascii=False, indent=2)}

用户问题：{prompt}

请提供：
1. 基于搜索结果的专业回答
2. 知识图谱的补充信息
3. 相关建议和见解
"""
            return self._simulate_llm_response('Enhanced', enhanced_prompt)

        return self._simulate_llm_response('Enhanced', prompt)

    def _simulate_llm_response(self, model_name: str, prompt: str) -> str:
        """模拟LLM响应"""
        # 基于提示内容生成合适的响应
        if '专利' in prompt:
            return f"基于{model_name}的分析，关于专利的问题，建议：\n1. 查询专利数据库获取详细信息\n2. 分析专利的技术要点和创新点\n3. 关注专利的法律状态和保护范围"
        elif '技术' in prompt:
            return f"根据{model_name}的理解，相关技术包括：\n1. 核心技术原理和应用场景\n2. 技术发展趋势和前景\n3. 相关标准和规范"
        elif '法律' in prompt:
            return f"{model_name}分析认为：\n1. 需要查看相关法律条文\n2. 参考类似案例的判决结果\n3. 咨询专业法律人士获取准确建议"
        else:
            return f"{model_name}将基于搜索结果和知识图谱为您提供专业的综合分析。"

    async def enhanced_intelligent_qa(self, request: EnhancedQARequest) -> EnhancedQAResponse:
        """增强智能问答"""
        if not self.driver and not self.search_service:
            return EnhancedQAResponse(
                question=request.question,
                answer='抱歉，知识图谱和搜索服务都不可用。',
                sources=[],
                knowledge_graph_insights={},
                external_search_results=[],
                reasoning_process=['服务不可用'],
                confidence_score=0.0,
                execution_time=0.0,
                timestamp=datetime.now().isoformat()
            )

        start_time = time.time()
        reasoning_process = []

        try:
            # 步骤1：理解问题意图
            reasoning_process.append('1. 分析用户问题和意图')
            content_analysis = await self._analyze_question(request.question)

            # 步骤2：知识图谱查询
            kg_insights = {}
            if request.include_knowledge_graph and self.driver:
                reasoning_process.append('2. 查询知识图谱相关信息')
                kg_insights = await self._query_knowledge_graph(request.question, content_analysis)

            # 步骤3：外部搜索引擎查询
            search_results = []
            if request.include_external_search and self.search_service:
                reasoning_process.append('3. 进行外部搜索引擎查询')
                search_results = await self._search_external_information(
                    request.question, request.scope
                )

            # 步骤4：综合推理和生成回答
            reasoning_process.append('4. 综合信息并进行智能推理')
            enhanced_answer = await self._generate_enhanced_answer(
                request.question, kg_insights, search_results, content_analysis
            )

            # 步骤5：构建响应
            execution_time = time.time() - start_time
            confidence_score = self._calculate_confidence(kg_insights, search_results)

            # 收集所有来源
            all_sources = []
            if kg_insights.get('nodes'):
                all_sources.extend([{'type': 'knowledge_graph', 'data': node} for node in kg_insights['nodes']])
            if search_results:
                all_sources.extend([{'type': 'external_search', 'data': result} for result in search_results[:5]])

            return EnhancedQAResponse(
                question=request.question,
                answer=enhanced_answer,
                sources=all_sources,
                knowledge_graph_insights=kg_insights,
                external_search_results=search_results[:10],  # 限制返回数量
                reasoning_process=reasoning_process,
                confidence_score=confidence_score,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            reasoning_process.append(f"执行过程中出现错误: {str(e)}")
            return EnhancedQAResponse(
                question=request.question,
                answer=f"抱歉，处理您的问题时遇到了错误: {str(e)}",
                sources=[],
                knowledge_graph_insights={},
                external_search_results=[],
                reasoning_process=reasoning_process,
                confidence_score=0.0,
                execution_time=time.time() - start_time,
                timestamp=datetime.now().isoformat()
            )

    async def _analyze_question(self, question: str) -> Dict:
        """分析问题"""
        if not self.search_service:
            return {'key_concepts': [], 'entities': [], 'intent': 'unknown'}

        try:
            # 使用搜索服务的内容理解功能
            scope_map = {
                'general': SearchScope.GENERAL,
                'professional': SearchScope.PROFESSIONAL,
                'academic': SearchScope.ACADEMIC,
                'legal': SearchScope.LEGAL,
                'technical': SearchScope.TECHNICAL
            }

            scope = scope_map.get('general', SearchScope.GENERAL)
            analysis = await self.search_service.search_engine.understand_content(question, scope)

            return {
                'key_concepts': analysis.key_concepts,
                'entities': [{'type': e['type'], 'value': e['value']} for e in analysis.entities],
                'intent': analysis.intent,
                'suggestions': analysis.suggestions
            }
        except Exception as e:
            logger.info(f"问题分析失败: {e}")
            return {'key_concepts': [], 'entities': [], 'intent': 'unknown'}

    async def _query_knowledge_graph(self, question: str, content_analysis: Dict) -> Dict:
        """查询知识图谱"""
        if not self.driver:
            return {}

        insights = {
            'nodes': [],
            'relationships': [],
            'statistics': {},
            'insights': []
        }

        try:
            with self.driver.session() as session:
                # 基于关键概念搜索
                for concept in content_analysis.get('key_concepts', [])[:3]:
                    # 搜索专利
                    patent_query = """
                    MATCH (p:Patent)
                    WHERE p.title CONTAINS $concept OR p.abstract CONTAINS $concept
                    RETURN p.id as id, p.title as title, p.abstract as abstract, labels(p) as type
                    LIMIT 3
                    """

                    patent_result = session.run(patent_query, concept=concept)
                    for record in patent_result:
                        insights['nodes'].append({
                            'id': record['id'],
                            'title': record['title'],
                            'abstract': record['abstract'][:200] + '...',
                            'type': record['type'][0]
                        })

                    # 搜索技术
                    tech_query = """
                    MATCH (t:Technology)
                    WHERE t.name CONTAINS $concept
                    OPTIONAL MATCH (t)<-[:USES_TECHNOLOGY]-(p:Patent)
                    RETURN t.id as id, t.name as name, t.description as description,
                           labels(t) as type, count(p) as patent_count
                    LIMIT 3
                    """

                    tech_result = session.run(tech_query, concept=concept)
                    for record in tech_result:
                        insights['nodes'].append({
                            'id': record['id'],
                            'name': record['name'],
                            'description': record.get('description', ''),
                            'type': record['type'][0],
                            'patent_count': record['patent_count']
                        })

                # 生成洞察
                insights['insights'] = self._generate_insights(insights['nodes'], question)

        except Exception as e:
            logger.info(f"知识图谱查询失败: {e}")

        return insights

    async def _search_external_information(self, question: str, scope: str) -> List[Dict]:
        """搜索外部信息"""
        if not self.search_service:
            return []

        try:
            scope_map = {
                'general': SearchScope.GENERAL,
                'professional': SearchScope.PROFESSIONAL,
                'academic': SearchScope.ACADEMIC,
                'legal': SearchScope.LEGAL,
                'technical': SearchScope.TECHNICAL
            }

            search_scope = scope_map.get(scope, SearchScope.GENERAL)
            result = await self.search_service.enhanced_search(question, search_scope)

            # 合并内部和外部结果
            combined_results = []

            # 添加知识图谱结果
            for kg_result in result.get('knowledge_graph_results', []):
                combined_results.append({
                    'title': kg_result.get('title', ''),
                    'content': kg_result.get('content', ''),
                    'type': kg_result.get('type', ''),
                    'source': 'knowledge_graph',
                    'relevance': 0.9
                })

            # 添加外部搜索结果
            for ext_result in result.get('external_search_results', []):
                combined_results.append({
                    'title': ext_result.get('title', ''),
                    'url': ext_result.get('url', ''),
                    'snippet': ext_result.get('snippet', ''),
                    'source': 'external_search',
                    'relevance': ext_result.get('relevance_score', 0.5)
                })

            # 按相关性排序
            combined_results.sort(key=lambda x: x.get('relevance', 0), reverse=True)

            return combined_results[:10]

        except Exception as e:
            logger.info(f"外部搜索失败: {e}")
            return []

    async def _generate_enhanced_answer(self, question: str, kg_insights: Dict,
                                        search_results: List[Dict], content_analysis: Dict) -> str:
        """生成增强回答"""
        # 使用增强的LLM客户端
        context = {
            'knowledge_graph_insights': kg_insights,
            'external_search_results': search_results,
            'content_analysis': content_analysis
        }

        # 构建增强提示
        enhanced_prompt = f"""
用户问题：{question}

请基于以下信息提供专业、详细的回答：

内容分析：
- 用户意图：{content_analysis.get('intent', '未知')}
- 关键概念：{content_analysis.get('key_concepts', [])[:5]}
- 识别实体：{[f'{e['type']}:{e['value']}' for e in content_analysis.get('entities', [])[:3]]}

知识图谱信息：{len(kg_insights.get('nodes', []))}个相关节点

外部搜索结果：{len(search_results)}条相关信息

请提供：
1. 直接回答用户问题
2. 基于知识图谱和搜索结果的专业见解
3. 相关建议和后续行动
"""

        try:
            # 使用增强客户端生成回答
            enhanced_client = self.llm_clients.get('enhanced', self._claude_client)
            answer = enhanced_client(enhanced_prompt, context)
            return answer
        except Exception as e:
            logger.info(f"增强回答生成失败: {e}")
            return '基于可用信息，我为您提供了一些分析和建议，但可能需要更多信息来完整回答您的问题。'

    def _generate_insights(self, nodes: List[Dict], question: str) -> List[str]:
        """生成洞察"""
        insights = []

        if not nodes:
            insights.append('在知识图谱中没有找到直接相关的信息')
            return insights

        # 分析节点类型分布
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1

        if len(node_types) > 1:
            insights.append(f"发现了多种类型的相关实体：{', '.join(node_types.keys())}")

        # 基于问题类型生成特定洞察
        if '专利' in question:
            patent_count = node_types.get('Patent', 0)
            if patent_count > 0:
                insights.append(f"找到了{patent_count}个相关专利，建议查看具体的技术方案和保护范围")

        if '技术' in question:
            tech_count = node_types.get('Technology', 0)
            if tech_count > 0:
                insights.append(f"发现了{tech_count}项相关技术，建议关注其应用场景和发展趋势")

        return insights

    def _calculate_confidence(self, kg_insights: Dict, search_results: List[Dict]) -> float:
        """计算置信度"""
        confidence = 0.0

        # 基于知识图谱结果
        kg_nodes = len(kg_insights.get('nodes', []))
        if kg_nodes > 0:
            confidence += min(0.5, kg_nodes * 0.1)

        # 基于搜索结果
        search_count = len(search_results)
        if search_count > 0:
            confidence += min(0.4, search_count * 0.05)

        # 基于结果质量（相关性分数）
        if search_results:
            avg_relevance = sum(r.get('relevance', 0.5) for r in search_results) / len(search_results)
            confidence += avg_relevance * 0.1

        return min(confidence, 1.0)

    async def knowledge_synthesis(self, topic: str, scope: str = 'professional') -> Dict:
        """知识综合分析"""
        if not self.search_service:
            return {'error': '搜索服务不可用'}

        try:
            # 执行增强搜索
            search_scope = SearchScope.PROFESSIONAL if scope == 'professional' else SearchScope.GENERAL
            search_result = await self.search_service.enhanced_search(topic, search_scope)

            # 生成综合分析
            synthesis = {
                'topic': topic,
                'scope': scope,
                'summary': '',
                'key_findings': [],
                'knowledge_graph_insights': search_result.get('knowledge_graph_results', []),
                'external_insights': search_result.get('external_search_results', [])[:5],
                'recommendations': [],
                'confidence': 0.0,
                'timestamp': datetime.now().isoformat()
            }

            # 生成总结
            kg_count = len(search_result.get('knowledge_graph_results', []))
            ext_count = len(search_result.get('external_search_results', []))

            synthesis['summary'] = f"关于'{topic}'的{scope}分析，找到了{kg_count}个知识图谱实体和{ext_count}条外部搜索结果。"

            # 生成关键发现
            if kg_count > 0:
                synthesis['key_findings'].append(f"知识图谱中有{kg_count}个直接相关的实体")

            if ext_count > 0:
                synthesis['key_findings'].append(f"外部搜索提供了{ext_count}条补充信息")

            # 生成建议
            if scope == 'professional':
                synthesis['recommendations'].extend([
                    '建议深入研究相关技术标准',
                    '考虑查询最新的研究报告',
                    '关注行业发展趋势'
                ])

            # 计算置信度
            synthesis['confidence'] = min(1.0, (kg_count * 0.1 + ext_count * 0.05))

            return synthesis

        except Exception as e:
            return {'error': f"知识综合分析失败: {str(e)}"}

    def close(self) -> Any:
        """关闭连接"""
        if self.search_service:
            self.search_service.close()
        if self.driver:
            self.driver.close()

async def main():
    """主函数演示"""
    logger.info('🧠 Athena知识图谱LLM集成系统 - 搜索引擎增强版')
    logger.info(str('=' * 60))

    integrator = EnhancedKnowledgeGraphLLMIntegration()

    if not LLM_SEARCH_INTEGRATION_AVAILABLE:
        logger.info('❌ 依赖库未安装，无法运行集成示例')
        return

    # 示例1：增强智能问答
    logger.info("\n1. 增强智能问答示例")
    qa_requests = [
        EnhancedQARequest(
            question='深度学习在专利分析中有什么应用？',
            scope='professional',
            include_external_search=True,
            include_knowledge_graph=True
        ),
        EnhancedQARequest(
            question='人工智能技术的最新发展趋势',
            scope='technical',
            include_external_search=True
        ),
        EnhancedQARequest(
            question='如何申请软件专利？',
            scope='legal',
            include_knowledge_graph=True
        )
    ]

    for request in qa_requests:
        logger.info(f"\n❓ 问题: {request.question}")
        response = await integrator.enhanced_intelligent_qa(request)
        logger.info(f"🤖️ 回答: {response.answer[:200]}...")
        logger.info(f"📊 置信度: {response.confidence_score:.2f}")
        logger.info(f"📚 信息来源: {len(response.sources)}条")
        logger.info(f"⏱️ 执行时间: {response.execution_time:.2f}秒")

    # 示例2：知识综合分析
    logger.info("\n2. 知识综合分析示例")
    topics = ['区块链技术', '人工智能专利', '云计算发展']

    for topic in topics:
        logger.info(f"\n📋 主题: {topic}")
        synthesis = await integrator.knowledge_synthesis(topic, 'professional')

        if 'error' not in synthesis:
            logger.info(f"📊 总结: {synthesis['summary']}")
            logger.info(f"🔍 关键发现: {synthesis['key_findings']}")
            logger.info(f"💡 建议: {synthesis['recommendations'][:2]}")
            logger.info(f"📈 置信度: {synthesis['confidence']:.2f}")
        else:
            logger.info(f"❌ 分析失败: {synthesis['error']}")

    logger.info("\n✅ 知识图谱LLM集成系统演示完成")
    integrator.close()

if __name__ == '__main__':
    asyncio.run(main())