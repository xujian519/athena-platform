#!/usr/bin/env python3
from __future__ import annotations
"""
Athena知识图谱与大语言模型集成
Knowledge Graph and Large Language Model Integration

集成大语言模型实现智能问答和推理功能

作者: Athena AI系统
创建时间: 2025-12-08
版本: 1.0.0
"""

import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from neo4j import GraphDatabase
    LLM_INTEGRATION_AVAILABLE = True
except ImportError:
    LLM_INTEGRATION_AVAILABLE = False

class KnowledgeGraphLLMIntegration:
    """知识图谱与大语言模型集成"""

    def __init__(self):
        self.driver = None
        if LLM_INTEGRATION_AVAILABLE:
            self.setup_neo4j()
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

    def setup_llm_clients(self) -> Any:
        """设置大语言模型客户端"""
        # 这里可以集成不同的LLM服务
        # 比如OpenAI、Claude、本地模型等
        self.llm_clients = {
            'claude': self._claude_client,
            'openai': self._openai_client,
            'local': self._local_client
        }

    def _claude_client(self, prompt: str) -> str:
        """Claude客户端模拟"""
        # 模拟Claude的响应
        return self._simulate_llm_response('Claude', prompt)

    def _openai_client(self, prompt: str) -> str:
        """OpenAI客户端模拟"""
        # 模拟GPT的响应
        return self._simulate_llm_response('GPT', prompt)

    def _local_client(self, prompt: str) -> str:
        """本地模型客户端模拟"""
        # 模拟本地模型的响应
        return self._simulate_llm_response('Local', prompt)

    def _simulate_llm_response(self, model_name: str, prompt: str) -> str:
        """模拟LLM响应"""
        # 这里可以根据prompt生成合适的响应
        if '专利' in prompt:
            return f"基于{model_name}的分析，关于专利的问题，我建议..."
        elif '技术' in prompt:
            return f"根据{model_name}的理解，相关技术包括..."
        else:
            return f"{model_name}将为您提供专业的知识图谱分析。"

    def extract_entities_from_text(self, text: str) -> dict[str, list[str]]:
        """从文本中提取实体"""
        # 简单的实体提取逻辑
        entities = {
            'patents': [],
            'technologies': [],
            'companies': [],
            'laws': []
        }

        # 提取专利号
        patent_pattern = r'CN\d{13}[A-Z0-9]*'
        patents = re.findall(patent_pattern, text)
        entities['patents'] = patents

        # 提取技术关键词
        tech_keywords = ['深度学习', '人工智能', '区块链', '机器学习', '大数据', '云计算']
        for keyword in tech_keywords:
            if keyword in text:
                entities['technologies'].append(keyword)

        # 提取公司名称（简单实现）
        company_patterns = ['科技有限公司', '技术公司', '股份公司']
        for pattern in company_patterns:
            matches = re.findall(f'([^。]*?{pattern})', text)
            entities['companies'].extend(matches)

        return entities

    def generate_knowledge_graph_query(self, user_query: str) -> str:
        """生成知识图谱查询"""
        # 简单的查询生成逻辑
        if '专利' in user_query and '技术' in user_query:
            """
            MATCH (p:Patent)-[:USES_TECHNOLOGY]->(t:Technology)
            RETURN p.title, p.abstract, t.name as technology
            """
        elif '法律' in user_query and '第' in user_query:
            # 提取法条号
            article_match = re.search(r'第(\d+)条', user_query)
            if article_match:
                article_num = article_match.group(1)
                return f"""
                MATCH (l:Law)-[:HAS_ARTICLE]->(a:Article {{number: '第{article_num}条'}})
                RETURN l.name, a.content
                """
        elif '公司' in user_query:
            """
            MATCH (c:Company)<-[:ASSIGNED_TO]-(p:Patent)
            RETURN c.name, COUNT(p) as patent_count
            ORDER BY patent_count DESC
            LIMIT 10
            """
        else:
            """
            MATCH (n)
            RETURN labels(n) as type, count(n) as count
            ORDER BY count DESC
            LIMIT 10
            """

    def execute_query_and_format_response(self, query: str, user_query: str) -> str:
        """执行查询并格式化响应"""
        if not self.driver:
            return '抱歉，知识图谱服务暂时不可用。'

        try:
            with self.driver.session() as session:
                result = session.run(query)

                # 格式化结果
                response_parts = []
                response_parts.append(f"根据您的问题：\"{user_query}\"")

                # 提取结果
                records = list(result)
                if records:
                    response_parts.append('我找到了以下相关信息：')
                    for i, record in enumerate(records, 1):
                        response_parts.append(f"{i}. {dict(record)}")
                else:
                    response_parts.append('抱歉，没有找到相关信息。')

                return "\n".join(response_parts)

        except Exception as e:
            return f"查询执行失败：{str(e)}"

    def intelligent_kg_qa(self, user_query: str) -> str:
        """智能知识图谱问答"""
        if not self.driver:
            return '知识图谱服务未连接，请检查Neo4j服务状态。'

        # 步骤1：实体提取
        entities = self.extract_entities_from_text(user_query)

        # 步骤2：生成查询
        query = self.generate_knowledge_graph_query(user_query)

        # 步骤3：执行查询
        kg_response = self.execute_query_and_format_response(query, user_query)

        # 步骤4：LLM增强响应
        enhanced_response = self.enhance_response_with_llm(kg_response, entities, user_query)

        return enhanced_response

    def enhance_response_with_llm(self, base_response: str, entities: dict, user_query: str) -> str:
        """使用LLM增强响应"""
        # 选择LLM客户端
        llm_name = 'claude'  # 默认使用Claude
        llm_client = self.llm_clients.get(llm_name, self._local_client)

        # 构建增强提示
        enhancement_prompt = f"""
        用户问题：{user_query}
        知识图谱查询结果：{base_response}
        提取的实体：{json.dumps(entities, ensure_ascii=False, indent=2)}

        请基于知识图谱查询结果，提供一个更详细、更专业的回答。如果结果为空，请说明原因并提供相关建议。
        """

        try:
            enhanced = llm_client(enhancement_prompt)
            return enhanced
        except Exception as e:
            logger.info(f"LLM增强失败: {str(e)}")
            return base_response

    def build_knowledge_insights(self, entity_name: str) -> dict[str, Any]:
        """构建知识洞察"""
        if not self.driver:
            return {'error': 'Neo4j未连接'}

        insights = {
            'entity': entity_name,
            'timestamp': datetime.now().isoformat(),
            'connections': [],
            'statistics': {},
            'recommendations': []
        }

        try:
            with self.driver.session() as session:
                # 查询实体的连接
                connection_query = """
                MATCH (n {{name: $name}})
                OPTIONAL MATCH (n)-[r]-(connected)
                RETURN connected.name as connected_name,
                       labels(connected) as connected_type,
                       type(r) as relationship_type
                LIMIT 10
                """

                result = session.run(connection_query, name=entity_name)

                for record in result:
                    insights['connections'].append({
                        'name': record['connected_name'],
                        'type': record['connected_type'],
                        'relationship': record['relationship_type']
                    })

                # 生成统计信息
                insights['statistics'] = {
                    'total_connections': len(insights['connections']),
                    'connection_types': len({conn['relationship'] for conn in insights['connections']})
                }

                # 生成建议
                insights['recommendations'] = self._generate_recommendations(entity_name, insights['connections'])

        except Exception as e:
            insights['error'] = str(e)

        return insights

    def _generate_recommendations(self, entity: str, connections: list[dict]) -> list[str]:
        """生成推荐建议"""
        recommendations = []

        if not connections:
            recommendations.append(f"建议探索与{entity}相关的其他实体，可能包括技术、法律或专利信息")
            return recommendations

        # 基于连接类型生成建议
        relationship_types = [conn['relationship'] for conn in connections]

        if 'USES_TECHNOLOGY' in relationship_types:
            recommendations.append(f"建议深入了解{entity}所使用的技术，可能存在技术替代或改进机会")

        if 'ASSIGNED_TO' in relationship_types:
            recommendations.append(f"建议分析{entity}的所有权状况，可能涉及知识产权策略")

        if 'REFERENCES' in relationship_types:
            recommendations.append("建议研究相关法律条文，确保合规性")

        return recommendations

    def create_knowledge_summary(self, topic: str) -> dict[str, Any]:
        """创建知识摘要"""
        if not self.driver:
            return {'error': 'Neo4j未连接'}

        summary = {
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'summary': '',
            'key_entities': [],
            'relationships': [],
            'visual_data': {
                'nodes': [],
                'edges': []
            }
        }

        try:
            with self.driver.session() as session:
                # 获取相关节点
                node_query = """
                MATCH (n)
                WHERE n.title CONTAINS $topic OR n.name CONTAINS $topic
                RETURN n.id as id,
                       n.title as title,
                       n.name as name,
                       labels(n) as labels
                LIMIT 20
                """

                result = session.run(node_query, topic=topic)

                nodes = []
                for record in result:
                    node_id = record['id']
                    node_title = record.get('title', '') or record.get('name', '')
                    node_labels = record['labels']
                    node_type = node_labels[0] if node_labels else 'Unknown'

                    nodes.append({
                        'id': node_id,
                        'label': node_title[:30] + '...',
                        'type': node_type,
                        'color': self.get_node_color(node_type)
                    })

                    summary['key_entities'].append({
                        'id': node_id,
                        'type': node_type,
                        'name': node_title
                    })

                # 获取相关关系
                edge_query = """
                MATCH (n1)-[r]->(n2)
                WHERE (n1.title CONTAINS $topic OR n1.name CONTAINS $topic)
                   OR (n2.title CONTAINS $topic OR n2.name CONTAINS $topic)
                RETURN n1.id as source,
                       n2.id as target,
                       type(r) as relationship
                LIMIT 30
                """

                edge_result = session.run(edge_query, topic=topic)

                for record in edge_result:
                    summary['relationships'].append({
                        'source': record['source'],
                        'target': record['target'],
                        'type': record['relationship']
                    })

                # 生成文本摘要
                summary['visual_data']['nodes'] = nodes
                summary['visual_data']['edges'] = [
                    {
                        'source': edge['source'],
                        'target': edge['target'],
                        'label': edge['type']
                    }
                    for edge in summary['relationships']
                ]

                summary['summary'] = f"关于'{topic}'的知识图谱包含{len(nodes)}个节点和{len(summary['relationships'])}个关系。"

        except Exception as e:
            summary['error'] = str(e)

        return summary

    def get_node_color(self, node_type: str) -> str:
        """获取节点颜色"""
        color_map = {
            'Patent': '#FF6B6B',
            'Technology': '#4ECDC4',
            'Law': '#45B7D1',
            'Article': '#96CEB4',
            'Company': '#FFEAA7',
            'Inventor': '#DDA0DD',
            'Keyword': '#F8B500',
            'Case': '#FF7675'
        }
        return color_map.get(node_type, '#95A5A6')

def main() -> None:
    """主函数演示"""
    integrator = KnowledgeGraphLLMIntegration()

    if not LLM_INTEGRATION_AVAILABLE:
        logger.info('❌ 依赖库未安装，无法运行集成示例')
        return

    logger.info('🧠 Athena知识图谱与大语言模型集成演示')
    logger.info(str('=' * 60))

    # 示例1：智能问答
    logger.info("\n1. 智能问答示例")
    sample_queries = [
        '深度学习相关的专利有哪些？',
        '中华人民共和国专利法第26条的内容是什么？',
        '人工智能技术的应用公司有哪些？'
    ]

    for query in sample_queries:
        logger.info(f"\n❓ 问题: {query}")
        answer = integrator.intelligent_kg_qa(query)
        logger.info(f"🤖️ 回答: {answer}")

    # 示例2：知识洞察
    logger.info("\n2. 知识洞察示例")
    entity = '深度学习'
    logger.info(f"\n🔍 分析实体: {entity}")
    insights = integrator.build_knowledge_insights(entity)

    logger.info('💡 知识洞察:')
    if 'error' in insights:
        logger.info(f"  ❌ 分析失败: {insights['error']}")
    else:
        logger.info(f"  📊 连接数: {insights['statistics']['total_connections']}")
        logger.info(f"  🔗 关系类型数: {insights['statistics']['connection_types']}")
        logger.info('  💡 建议:')
        for rec in insights.get('recommendations', []):
            logger.info(f"    • {rec}")

    # 示例3：知识摘要
    logger.info("\n3. 知识摘要示例")
    topics = ['深度学习', '区块链', '人工智能']

    for topic in topics:
        logger.info(f"\n📋 生成摘要: {topic}")
        summary = integrator.create_knowledge_summary(topic)

        if 'error' in summary:
            logger.info(f"  ❌ 生成失败: {summary['error']}")
        else:
            logger.info(f"  📊 {summary['summary']}")
            logger.info(f"  🔑 关键实体: {len(summary['key_entities'])}个")
            logger.info(f"  🔗 关系数: {len(summary['relationships'])}个")

    logger.info("\n✅ 知识图谱与大语言模型集成演示完成")

if __name__ == '__main__':
    main()
