#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利知识图谱记忆集成器
Patent Knowledge Graph Memory Integration

将现有的专利规则向量库与记忆系统进行深度集成，
实现智能的知识检索、关联分析和决策支持。

Created by Athena + 小诺 (AI助手)
Date: 2025-12-05
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PatentRule:
    """专利规则知识"""
    rule_id: str
    text: str
    category: str  # patent_law, examination_guide, court_interpretation, etc.
    vector: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    relationships: List[Dict[str, Any] = field(default_factory=list)
    embedding_timestamp: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime | None = None

@dataclass
class PatentCase:
    """专利案例知识"""
    case_id: str
    title: str
    abstract: str
    analysis_result: Dict[str, Any]
    decision_factors: List[str]
    outcome: str
    lessons_learned: List[str]
    related_rules: List[str]  # 关联的专利规则ID
    vector: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.0

@dataclass
class PatentKnowledgeQuery:
    """专利知识查询"""
    query_id: str
    query_text: str
    query_type: str  # similar_rules, related_cases, legal_interpretation, etc.
    context: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    max_results: int = 10
    similarity_threshold: float = 0.7

class PatentKnowledgeMemoryIntegrator:
    """专利知识图谱记忆集成器"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PatentKnowledgeMemoryIntegrator")

        # 知识库
        self.patent_rules: Dict[str, PatentRule] = {}
        self.patent_cases: Dict[str, PatentCase] = {}

        # 知识图谱关系
        self.knowledge_graph: Dict[str, List[Dict[str, Any]] = defaultdict(list)

        # 向量数据库路径
        self.vector_db_path = '/Users/xujian/Athena工作平台/data/professional_patent/vectors/patent_rules_vectors_20251205_080132.json'

        # 记忆系统API地址
        self.memory_athena_url = 'http://localhost:8008'
        self.memory_nuo_url = 'http://localhost:8083'

        # 缓存
        self.query_cache: Dict[str, Dict[str, Any] = {}
        self.similarity_cache: Dict[str, float] = {}

        # 统计信息
        self.stats = {
            'total_rules_loaded': 0,
            'total_cases_created': 0,
            'queries_processed': 0,
            'similarity_calculations': 0
        }

        self.logger.info('专利知识图谱记忆集成器初始化完成')

    async def load_patent_rules_from_vector_db(self):
        """从向量数据库加载专利规则"""
        try:
            self.logger.info(f"开始加载专利规则向量数据库: {self.vector_db_path}")

            with open(self.vector_db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            metadata = data.get('metadata', {})
            vectors = data.get('vectors', [])

            self.logger.info(f"向量数据库信息: {metadata}")
            self.logger.info(f"向量总数: {len(vectors)}")

            loaded_count = 0
            for vector_data in vectors:
                try:
                    rule = PatentRule(
                        rule_id=vector_data['id'],
                        text=vector_data['text'],
                        category=self._extract_category(vector_data['text']),
                        vector=vector_data['vector'],
                        metadata={
                            'source': 'vector_database',
                            'vector_dimension': metadata.get('vector_dimension', 1024),
                            'model': metadata.get('model', 'unknown')
                        }
                    )

                    self.patent_rules[rule.rule_id] = rule
                    loaded_count += 1

                except Exception as e:
                    self.logger.error(f"加载专利规则失败 {vector_data.get('id', 'unknown')}: {str(e)}")

            self.stats['total_rules_loaded'] = loaded_count
            self.logger.info(f"成功加载 {loaded_count} 个专利规则")

            # 构建知识图谱关系
            await self._build_knowledge_relationships()

        except Exception as e:
            self.logger.error(f"加载专利规则向量数据库失败: {str(e)}")
            raise

    def _extract_category(self, text: str) -> str:
        """从文本中提取专利规则类别"""
        text_lower = text.lower()

        # 关键词映射到类别
        category_keywords = {
            '专利法': 'patent_law',
            '专利法解释': 'patent_law_interpretation',
            '专利法实施细则': 'patent_law_implementation',
            '专利审查指南': 'examination_guide',
            '审查指南': 'examination_guide',
            '专利审查': 'patent_examination',
            '法院解释': 'court_interpretation',
            '最高人民法院': 'court_interpretation',
            '司法解释': 'judicial_interpretation',
            '专利纠纷': 'patent_dispute',
            '侵权纠纷': 'infringement_dispute',
            '专利侵权': 'patent_infringement',
            '专利无效': 'patent_invalidity',
            '专利权': 'patent_rights',
            '专利申请': 'patent_application',
            '发明专利': 'invention_patent',
            '实用新型': 'utility_model',
            '外观设计': 'design_patent'
        }

        # 寻找匹配的类别
        for keyword, category in category_keywords.items():
            if keyword in text_lower:
                return category

        # 默认类别
        return 'other'

    async def _build_knowledge_relationships(self):
        """构建知识图谱关系"""
        self.logger.info('开始构建知识图谱关系...')

        relationship_count = 0

        for rule_id, rule in self.patent_rules.items():
            # 基于内容相似性建立关系
            similar_rules = await self._find_similar_rules(rule, threshold=0.8)
            for similar_rule_id, similarity in similar_rules:
                if similar_rule_id != rule_id:
                    self.knowledge_graph[rule_id].append({
                        'target_id': similar_rule_id,
                        'relationship_type': 'content_similarity',
                        'similarity_score': similarity,
                        'created_at': datetime.now().isoformat()
                    })
                    relationship_count += 1

            # 基于类别建立关系
            category_rules = [rid for rid, r in self.patent_rules.items() if r.category == rule.category and rid != rule_id]
            for related_rule_id in category_rules:
                self.knowledge_graph[rule_id].append({
                    'target_id': related_rule_id,
                    'relationship_type': 'category_association',
                    'similarity_score': 0.9,
                    'created_at': datetime.now().isoformat()
                })
                relationship_count += 1

        self.logger.info(f"构建了 {relationship_count} 个知识关系")

    async def _find_similar_rules(self, rule: PatentRule, threshold: float = 0.8) -> List[Tuple[str, float]:
        """查找相似的专利规则"""
        similar_rules = []

        for rule_id, other_rule in self.patent_rules.items():
            if rule_id == other_rule.rule_id:
                continue

            # 计算相似度
            similarity = await self._calculate_similarity(rule.vector, other_rule.vector)

            if similarity >= threshold:
                similar_rules.append((other_rule_id, similarity))

        # 按相似度排序
        similar_rules.sort(key=lambda x: x[1], reverse=True)

        return similar_rules[:10]  # 返回最相似的10个

    async def _calculate_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """计算向量相似度"""
        if not vector1 or not vector2:
            return 0.0

        # 计算余弦相似度
        dot_product = sum(a * b for a, b in zip(vector1, vector2))
        magnitude1 = sum(a * a for a in vector1) ** 0.5
        magnitude2 = sum(b * b for b in vector2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        similarity = dot_product / (magnitude1 * magnitude2)
        self.stats['similarity_calculations'] += 1

        return similarity

    async def search_similar_patent_rules(self, query: PatentKnowledgeQuery) -> List[Dict[str, Any]:
        """搜索相似的专利规则"""
        self.logger.info(f"搜索相似专利规则: {query.query_id}")

        cache_key = f"rules_search_{hashlib.md5(query.query_text.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]}"

        # 检查缓存
        if cache_key in self.query_cache:
            self.logger.debug(f"从缓存返回查询结果: {cache_key}")
            self.query_cache[cache_key]['accessed_at'] = datetime.now()
            return self.query_cache[cache_key]['results']

        # 生成查询向量（简化版本，实际应使用嵌入模型）
        query_vector = await self._generate_query_vector(query.query_text)

        # 计算相似度
        results = []
        for rule_id, rule in self.patent_rules.items():
            # 应用过滤条件
            if query.filters:
                if 'category' in query.filters and rule.category != query.filters['category']:
                    continue
                if 'keywords' in query.filters:
                    if not any(keyword in rule.text.lower() for keyword in query.filters['keywords']):
                        continue

            similarity = await self._calculate_similarity(query_vector, rule.vector)

            if similarity >= query.similarity_threshold:
                # 更新访问统计
                rule.access_count += 1
                rule.last_accessed = datetime.now()

                results.append({
                    'rule_id': rule.rule_id,
                    'text': rule.text[:200] + '...' if len(rule.text) > 200 else rule.text,
                    'category': rule.category,
                    'similarity_score': similarity,
                    'metadata': rule.metadata,
                    'access_count': rule.access_count
                })

        # 按相似度排序
        results.sort(key=lambda x: x['similarity_score'], reverse=True)

        # 限制结果数量
        results = results[:query.max_results]

        # 缓存结果
        self.query_cache[cache_key] = {
            'results': results,
            'query_type': query.query_type,
            'created_at': datetime.now(),
            'accessed_at': datetime.now()
        }

        self.stats['queries_processed'] += 1

        self.logger.info(f"搜索完成，返回 {len(results)} 个相似规则")
        return results

    async def _generate_query_vector(self, query_text: str) -> List[float]:
        """生成查询向量（简化版本）"""
        # 这里应该使用与生成专利规则向量相同的模型
        # 为了演示，我们使用文本哈希生成简化向量

        # 生成文本哈希
        hash_obj = hashlib.md5(query_text.encode('utf-8', usedforsecurity=False)
        hash_hex = hash_obj.hexdigest()

        # 转换为1024维向量（简化示例）
        vector = []
        for i in range(0, 1024, 4):
            byte_pair = hash_hex[i:i+2] if i+2 < len(hash_hex) else hash_hex[-2:]
            vector.append(int(byte_pair, 16) / 255.0 - 1.0)

        # 归一化向量
        magnitude = sum(x * x for x in vector) ** 0.5
        if magnitude > 0:
            vector = [x / magnitude for x in vector]

        return vector

    async def store_patent_case(self, case: PatentCase) -> Dict[str, Any]:
        """存储专利案例"""
        self.logger.info(f"存储专利案例: {case.case_id}")

        # 生成案例向量
        case_text = f"{case.title} {case.abstract}"
        case.vector = await self._generate_query_vector(case_text)

        # 关联相关专利规则
        if case.related_rules:
            for rule_id in case.related_rules:
                if rule_id in self.patent_rules:
                    # 建立案例与规则的关系
                    self.knowledge_graph[case.case_id].append({
                        'target_id': rule_id,
                        'relationship_type': 'case_rule_association',
                        'relevance_score': case.confidence_score,
                        'created_at': datetime.now().isoformat()
                    })

                    # 建立规则与案例的反向关系
                    self.knowledge_graph[rule_id].append({
                        'target_id': case.case_id,
                        'relationship_type': 'rule_case_association',
                        'relevance_score': case.confidence_score,
                        'created_at': datetime.now().isoformat()
                    })

        # 存储案例
        self.patent_cases[case.case_id] = case
        self.stats['total_cases_created'] += 1

        # 存储到记忆系统
        memory_data = {
            'type': 'patent_case',
            'id': case.case_id,
            'title': case.title,
            'content': {
                'abstract': case.abstract,
                'analysis_result': case.analysis_result,
                'decision_factors': case.decision_factors,
                'outcome': case.outcome,
                'lessons_learned': case.lessons_learned,
                'confidence_score': case.confidence_score
            },
            'metadata': {
                'created_at': case.created_at.isoformat(),
                'related_rules': case.related_rules,
                'vector_dimension': len(case.vector)
            }
        }

        try:
            # 存储到Athena记忆系统
            await self._store_to_memory_system(self.memory_athena_url, memory_data)

            # 如果案例重要性高，也存储到小诺记忆系统
            if case.confidence_score >= 0.8:
                await self._store_to_memory_system(self.memory_nuo_url, memory_data)

            return {
                'success': True,
                'case_id': case.case_id,
                'stored_athena': True,
                'stored_nuo': case.confidence_score >= 0.8
            }

        except Exception as e:
            self.logger.error(f"存储专利案例到记忆系统失败: {str(e)}")
            return {
                'success': False,
                'case_id': case.case_id,
                'error': str(e)
            }

    async def get_related_patent_knowledge(self, case_id: str) -> Dict[str, Any]:
        """获取相关的专利知识"""
        self.logger.info(f"获取专利相关知识: {case_id}")

        if case_id not in self.patent_cases:
            return {
                'success': False,
                'error': f"案例不存在: {case_id}"
            }

        case = self.patent_cases[case_id]

        # 获取相关规则
        related_rules = []
        if case.related_rules:
            for rule_id in case.related_rules:
                if rule_id in self.patent_rules:
                    rule = self.patent_rules[rule_id]
                    related_rules.append({
                        'rule_id': rule.rule_id,
                        'text': rule.text[:200] + '...' if len(rule.text) > 200 else rule.text,
                        'category': rule.category,
                        'relevance': 0.9  # 简化处理
                    })

        # 获取相关案例
        related_cases = []
        case_vector = case.vector

        for other_case_id, other_case in self.patent_cases.items():
            if other_case_id == case_id:
                continue

            similarity = await self._calculate_similarity(case_vector, other_case.vector)

            if similarity >= 0.7:  # 相关性阈值
                related_cases.append({
                    'case_id': other_case.case_id,
                    'title': other_case.title,
                    'abstract': other_case.abstract[:150] + '...' if len(other_case.abstract) > 150 else other_case.abstract,
                    'similarity': similarity,
                    'outcome': other_case.outcome,
                    'confidence_score': other_case.confidence_score
                })

        # 按相关性排序
        related_cases.sort(key=lambda x: x['similarity'], reverse=True)

        return {
            'success': True,
            'case_id': case_id,
            'case': {
                'title': case.title,
                'abstract': case.abstract,
                'outcome': case.outcome,
                'confidence_score': case.confidence_score
            },
            'related_rules': related_rules[:5],  # 最多5个相关规则
            'related_cases': related_cases[:5],  # 最多5个相关案例
            'knowledge_graph_connections': len(self.knowledge_graph.get(case_id, []))
        }

    async def get_knowledge_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取知识洞察"""
        self.logger.info('获取专利知识洞察')

        insights = []

        # 基于上下文分析可能的知识需求
        if context.get('patent_id'):
            patent_id = context['patent_id']
            # 可以针对特定专利提供建议
            insights.append({
                'type': 'similar_patent_rules',
                'recommendation': f"建议查询与专利 {patent_id} 相似的法律条款",
                'confidence': 0.8
            })

        if context.get('analysis_type'):
            analysis_type = context['analysis_type']
            insights.append({
                'type': 'case_based_insights',
                'recommendation': f"建议参考历史上{analysis_type}的成功案例",
                'confidence': 0.75
            })

        if context.get('legal_issues'):
            legal_issues = context['legal_issues']
            insights.append({
                'type': 'legal_precedents',
                'recommendation': f"建议查询相关的{legal_issues}的法律解释和判例",
                'confidence': 0.85
            })

        return {
            'total_insights': len(insights),
            'insights': insights,
            'knowledge_stats': self.stats,
            'available_categories': list(set(rule.category for rule in self.patent_rules.values()))
        }

    async def _store_to_memory_system(self, memory_url: str, data: Dict[str, Any]) -> bool:
        """存储到记忆系统"""
        try:
            import requests

            # 构建完整的记忆数据
            memory_payload = {
                'content_type': 'patent_knowledge',
                'content_id': data['id'],
                'title': data.get('title', ''),
                'content': json.dumps(data, ensure_ascii=False),
                'metadata': {
                    'source': 'patent_knowledge_integrator',
                    'timestamp': datetime.now().isoformat(),
                    'tags': ['patent', 'legal', 'knowledge'],
                    **data.get('metadata', {})
                },
                'priority': 'medium'
            }

            response = requests.put(
                f"{memory_url}/api/v1/memory/store",
                json=memory_payload,
                timeout=30
            )

            if response.status_code == 200:
                return True
            else:
                self.logger.error(f"记忆系统存储失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"存储到记忆系统异常: {str(e)}")
            return False

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆系统统计信息"""
        stats = self.stats.copy()

        # 添加分类统计
        category_stats = {}
        for rule in self.patent_rules.values():
            category = rule.category
            category_stats[category] = category_stats.get(category, 0) + 1

        stats['categories'] = category_stats
        stats['total_rules'] = len(self.patent_rules)
        stats['total_cases'] = len(self.patent_cases)
        stats['total_relationships'] = sum(len(rels) for rels in self.knowledge_graph.values())
        stats['cache_size'] = len(self.query_cache)

        return stats

    async def test_knowledge_integration(self):
        """测试知识集成"""
        self.logger.info('开始测试专利知识图谱记忆集成...')

        # 测试搜索相似规则
        test_query = PatentKnowledgeQuery(
            query_id='test_001',
            query_text='专利申请的新颖性审查标准',
            query_type='similar_rules',
            filters={'category': 'examination_guide'},
            max_results=5,
            similarity_threshold=0.7
        )

        search_results = await self.search_similar_patent_rules(test_query)
        self.logger.info(f"搜索测试结果: {len(search_results)} 个相似规则")

        # 创建测试案例
        test_case = PatentCase(
            case_id='test_case_001',
            title='AI算法专利申请案例',
            abstract='一种基于深度学习的图像识别算法专利申请',
            analysis_result={
                'novelty_assessment': '具有较好的新颖性',
                'inventiveness_assessment': '创造性显著',
                'industrial_applicability': '实用性明确'
            },
            decision_factors=['技术先进性', '创新程度', '市场需求'],
            outcome='授权',
            lessons_learned=['技术描述要清晰', '权利要求要全面'],
            related_rules=['rule_001', 'rule_050'],  # 假设存在相关规则
            confidence_score=0.92
        )

        case_result = await self.store_patent_case(test_case)
        self.logger.info(f"案例存储测试结果: {case_result}")

        # 测试知识关联
        insight_result = await self.get_knowledge_insights({
            'patent_id': 'CN202410001234.5',
            'analysis_type': 'novelty_analysis',
            'legal_issues': ['专利性判断']
        })
        self.logger.info(f"知识洞察测试结果: {len(insight_result['insights'])} 个洞察")

        return {
            'search_results': len(search_results),
            'case_stored': case_result['success'],
            'insights_generated': len(insight_result['insights']),
            'memory_stats': await self.get_memory_statistics()
        }


# 测试代码
async def test_patent_knowledge_integration():
    """测试专利知识图谱记忆集成"""
    integrator = PatentKnowledgeMemoryIntegrator()

    # 加载专利规则
    await integrator.load_patent_rules_from_vector_db()

    # 测试集成功能
    test_results = await integrator.test_knowledge_integration()

    logger.info('专利知识图谱记忆集成测试结果:')
    logger.info(f"  搜索结果: {test_results['search_results']} 个相似规则")
    logger.info(f"  案例存储: {test_results['case_stored']}")
    logger.info(f"  洞察生成: {test_results['insights_generated']} 个洞察")
    logger.info(f"  记忆统计: {test_results['memory_stats']}")

    return test_results


if __name__ == '__main__':
    asyncio.run(test_patent_knowledge_integration())