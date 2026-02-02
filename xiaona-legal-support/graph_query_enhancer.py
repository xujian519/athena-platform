#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱查询增强器
增强NebulaGraph查询能力，支持复杂推理
作者: 小诺·双鱼座
"""

import logging
import json
import re
from typing import Dict, List, Tuple, Optional, Any, Set
from legal_kg_support import LegalKnowledgeGraphSupport
from collections import defaultdict, deque
import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)

class GraphQueryEnhancer:
    """知识图谱查询增强器"""

    def __init__(self, kg_support: LegalKnowledgeGraphSupport):
        """初始化查询增强器"""
        self.kg_support = kg_support
        self.query_cache = {}
        self.graph_cache = None
        self.last_update_time = None

        # 预定义的查询模板
        self.query_templates = {
            "find_related_laws": {
                "description": "查找相关法律",
                "template": '''
                MATCH (doc1:legal_document)-[:belongs_to]->(cat:legal_category)
                <-[:belongs_to]-(doc2:legal_document)
                WHERE doc1.title CONTAINS "{law_name}"
                RETURN DISTINCT doc2.title, doc2.doc_id
                ''',
                "params": ["law_name"]
            },
            "find_articles_in_law": {
                "description": "查找法律中的条文",
                "template": '''
                MATCH (doc:legal_document)-[:contains]->(article:legal_article)
                WHERE doc.title CONTAINS "{law_name}"
                RETURN article.article_id, article.content
                ORDER BY article.article_id
                ''',
                "params": ["law_name"]
            },
            "find_law_by_category": {
                "description": "按分类查找法律",
                "template": '''
                MATCH (cat:legal_category)<-[:belongs_to]-(doc:legal_document)
                WHERE cat.name CONTAINS "{category_name}"
                RETURN doc.title, doc.doc_id
                ''',
                "params": ["category_name"]
            },
            "find_references": {
                "description": "查找引用关系",
                "template": '''
                MATCH (doc1:legal_document)-[:references]->(doc2:legal_document)
                WHERE doc1.title CONTAINS "{law_name}"
                RETURN doc2.title, doc2.doc_id
                ''',
                "params": ["law_name"]
            }
        }

    def enhance_query(self, query: str, query_type: str = None) -> Dict:
        """增强查询"""
        logger.info(f"🔍 增强查询: {query}")

        # 识别查询意图
        intent = self._identify_query_intent(query)

        # 根据意图选择增强策略
        if intent["type"] == "relationship_query":
            return self._enhance_relationship_query(query, intent)
        elif intent["type"] == "path_query":
            return self._enhance_path_query(query, intent)
        elif intent["type"] == "aggregation_query":
            return self._enhance_aggregation_query(query, intent)
        elif intent["type"] == "reasoning_query":
            return self._enhance_reasoning_query(query, intent)
        else:
            return self._enhance_general_query(query, intent)

    def _identify_query_intent(self, query: str) -> Dict:
        """识别查询意图"""
        query_lower = query.lower()

        # 关系查询关键词
        relation_keywords = ["相关", "关联", "属于", "包含", "引用", "修改", "解释"]

        # 路径查询关键词
        path_keywords = ["路径", "连接", "传导", "影响", "链条"]

        # 聚合查询关键词
        aggregation_keywords = ["统计", "数量", "多少", "计数", "汇总", "平均"]

        # 推理查询关键词
        reasoning_keywords = ["推理", "推断", "为什么", "原因", "导致", "证明"]

        if any(kw in query for kw in reasoning_keywords):
            return {"type": "reasoning_query", "complexity": "high"}
        elif any(kw in query for kw in path_keywords):
            return {"type": "path_query", "complexity": "medium"}
        elif any(kw in query for kw in relation_keywords):
            return {"type": "relationship_query", "complexity": "medium"}
        elif any(kw in query for kw in aggregation_keywords):
            return {"type": "aggregation_query", "complexity": "low"}
        else:
            return {"type": "general_query", "complexity": "low"}

    def _enhance_relationship_query(self, query: str, intent: Dict) -> Dict:
        """增强关系查询"""
        # 提取实体
        entities = self._extract_entities(query)

        # 构建关系查询
        enhanced_queries = []

        for entity in entities:
            # 查找同分类法律
            enhanced_queries.append({
                "query": self.query_templates["find_related_laws"]["template"].format(
                    law_name=entity
                ),
                "description": f"查找与《{entity}》相关的法律",
                "weight": 0.8
            })

            # 查找包含的条文
            enhanced_queries.append({
                "query": self.query_templates["find_articles_in_law"]["template"].format(
                    law_name=entity
                ),
                "description": f"查找《{entity}》中的条文",
                "weight": 0.7
            })

        return {
            "enhanced_queries": enhanced_queries,
            "query_type": "relationship",
            "entities": entities,
            "suggestions": self._generate_relationship_suggestions(entities)
        }

    def _enhance_path_query(self, query: str, intent: Dict) -> Dict:
        """增强路径查询"""
        entities = self._extract_entities(query)

        if len(entities) >= 2:
            # 构建实体间路径查询
            path_query = f'''
            MATCH p = shortestPath((a:legal_document)-[*..5]-(b:legal_document))
            WHERE a.title CONTAINS "{entities[0]}" AND b.title CONTAINS "{entities[1]}"
            RETURN p, length(p) as path_length
            '''

            return {
                "path_query": path_query,
                "entities": entities,
                "query_type": "path",
                "max_depth": 5
            }

        return {
            "query_type": "path",
            "message": "需要更多实体信息来构建路径查询",
            "entities": entities
        }

    def _enhance_aggregation_query(self, query: str, intent: Dict) -> Dict:
        """增强聚合查询"""
        # 根据查询类型生成不同的聚合查询
        aggregation_queries = []

        # 统计各类型法律数量
        if "数量" in query or "多少" in query:
            aggregation_queries.append({
                "query": '''
                MATCH (doc:legal_document)
                RETURN doc.doc_type, count(doc) as count
                ''',
                "description": "统计各类型法律数量"
            })

        # 统计分类分布
        aggregation_queries.append({
            "query": '''
            MATCH (cat:legal_category)<-[:belongs_to]-(doc:legal_document)
            RETURN cat.name, count(doc) as count
            ORDER BY count DESC
            ''',
            "description": "统计法律分类分布"
        })

        return {
            "aggregation_queries": aggregation_queries,
            "query_type": "aggregation"
        }

    def _enhance_reasoning_query(self, query: str, intent: Dict) -> Dict:
        """增强推理查询"""
        # 提取推理要素
        reasoning_elements = self._extract_reasoning_elements(query)

        # 构建推理链
        reasoning_chain = self._build_reasoning_chain(reasoning_elements)

        return {
            "reasoning_chain": reasoning_chain,
            "query_type": "reasoning",
            "elements": reasoning_elements,
            "confidence": self._calculate_reasoning_confidence(reasoning_chain)
        }

    def _enhance_general_query(self, query: str, intent: Dict) -> Dict:
        """增强一般查询"""
        # 使用混合搜索
        search_results = self.kg_support.hybrid_search(query, top_k=10)

        # 提取关键信息
        key_info = self._extract_key_info(search_results)

        return {
            "search_results": search_results,
            "key_info": key_info,
            "query_type": "general"
        }

    def _extract_entities(self, text: str) -> List[str]:
        """提取法律实体"""
        # 使用正则表达式提取可能的法律名称
        patterns = [
            r'《([^》]+)》',  # 《法律名》
            r'([^，。！？、]+法)',  # xxx法
            r'([^，。！？、]+条例)',  # xxx条例
            r'([^，。！？、]+规定)',  # xxx规定
        ]

        entities = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            entities.update(matches)

        return list(entities)

    def _extract_reasoning_elements(self, query: str) -> Dict:
        """提取推理要素"""
        elements = {
            "conditions": [],
            "actions": [],
            "consequences": [],
            "subjects": []
        }

        # 条件关键词
        condition_keywords = ["如果", "当", "在...情况下", "符合"]

        # 行为关键词
        action_keywords = ["应当", "必须", "可以", "有权", "义务"]

        # 结果关键词
        consequence_keywords = ["导致", "造成", "结果是", "因此"]

        # 主体关键词
        subject_keywords = ["公民", "法人", "组织", "部门", "机关"]

        for keyword in condition_keywords:
            if keyword in query:
                elements["conditions"].append(keyword)

        for keyword in action_keywords:
            if keyword in query:
                elements["actions"].append(keyword)

        for keyword in consequence_keywords:
            if keyword in query:
                elements["consequences"].append(keyword)

        for keyword in subject_keywords:
            if keyword in query:
                elements["subjects"].append(keyword)

        return elements

    def _build_reasoning_chain(self, elements: Dict) -> List[Dict]:
        """构建推理链"""
        chain = []

        # 条件 -> 行为 -> 结果
        if elements["conditions"] and elements["actions"]:
            chain.append({
                "step": 1,
                "type": "condition_action",
                "description": "基于特定条件采取相应行为",
                "query": f'''
                MATCH (cond)-[:leads_to]->(action)
                WHERE cond.name IN {[f"'{c}'" for c in elements["conditions"]]}
                AND action.name IN {[f"'{a}'" for a in elements["actions"]]}
                RETURN cond, action
                '''
            })

        if elements["actions"] and elements["consequences"]:
            chain.append({
                "step": 2,
                "type": "action_consequence",
                "description": "行为导致的法律后果",
                "query": f'''
                MATCH (action)-[:results_in]->(consequence)
                WHERE action.name IN {[f"'{a}'" for a in elements["actions"]]}
                AND consequence.name IN {[f"'{c}'" for c in elements["consequences"]]}
                RETURN action, consequence
                '''
            })

        return chain

    def _calculate_reasoning_confidence(self, reasoning_chain: List[Dict]) -> float:
        """计算推理置信度"""
        if not reasoning_chain:
            return 0.3

        # 基于推理链长度和完整性计算
        base_confidence = 0.5
        chain_bonus = min(len(reasoning_chain) * 0.1, 0.3)

        return min(base_confidence + chain_bonus, 0.9)

    def _generate_relationship_suggestions(self, entities: List[str]) -> List[str]:
        """生成关系查询建议"""
        suggestions = []

        for entity in entities:
            suggestions.extend([
                f"查找引用《{entity}》的其他法律",
                f"查找《{entity}》修改的法律",
                f"查找与《{entity}》同一分类的法律",
                f"查找解释《{entity}》的司法解释"
            ])

        return suggestions[:5]

    def _extract_key_info(self, search_results: List[Dict]) -> Dict:
        """提取关键信息"""
        key_info = {
            "laws_mentioned": set(),
            "categories": set(),
            "key_terms": set(),
            "relationships": []
        }

        for result in search_results:
            # 提取法律名称
            if result.get("title"):
                key_info["laws_mentioned"].add(result["title"])

            # 提取关键术语
            content = result.get("content", "")
            terms = self._extract_legal_terms(content)
            key_info["key_terms"].update(terms)

        return {
            "laws_mentioned": list(key_info["laws_mentioned"])[:5],
            "categories": list(key_info["categories"])[:3],
            "key_terms": list(key_info["key_terms"])[:10],
            "total_results": len(search_results)
        }

    def _extract_legal_terms(self, text: str) -> List[str]:
        """提取法律术语"""
        # 常见法律术语模式
        term_patterns = [
            r'权利义务',
            r'法律责任',
            r'民事责任',
            r'刑事责任',
            r'行政责任',
            r'违约责任',
            r'侵权责任',
            r'诉讼时效',
            r'管辖权',
            r'举证责任'
        ]

        terms = []
        for pattern in term_patterns:
            if re.search(pattern, text):
                terms.append(pattern)

        return terms

    def visualize_subgraph(self, center_entity: str, depth: int = 2) -> Dict:
        """可视化子图"""
        # 构建子图查询
        subgraph_query = f'''
        MATCH (center:legal_document)
        WHERE center.title CONTAINS "{center_entity}"
        OPTIONAL MATCH (center)-[r*1..{depth}]-(related)
        RETURN center, r, related
        '''

        # 执行查询
        success, output, _ = self.kg_support._execute_nebula(subgraph_query)

        if success:
            # 构建图数据结构
            graph_data = self._parse_graph_output(output)

            # 计算图统计
            stats = self._calculate_graph_stats(graph_data)

            return {
                "graph_data": graph_data,
                "stats": stats,
                "center_entity": center_entity,
                "depth": depth
            }

        return {"error": "Failed to retrieve subgraph"}

    def _parse_graph_output(self, output: str) -> Dict:
        """解析图输出"""
        # 这里需要解析NebulaGraph的输出格式
        # 简化实现
        nodes = []
        edges = []

        lines = output.split('\n')
        for line in lines:
            if '|' in line and not line.startswith(('+', '|')):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    nodes.append({
                        "id": parts[0],
                        "label": parts[1],
                        "type": "legal_document"
                    })

        return {
            "nodes": nodes,
            "edges": edges
        }

    def _calculate_graph_stats(self, graph_data: Dict) -> Dict:
        """计算图统计信息"""
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "density": len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0,
            "avg_degree": 2 * len(edges) / len(nodes) if len(nodes) > 0 else 0
        }

    def execute_enhanced_query(self, enhanced_query: Dict) -> List[Dict]:
        """执行增强查询"""
        results = []

        if "enhanced_queries" in enhanced_query:
            # 执行多个查询
            for query_info in enhanced_query["enhanced_queries"]:
                success, output, _ = self.kg_support._execute_nebula(query_info["query"])
                if success:
                    parsed_results = self._parse_query_results(output)
                    results.extend(parsed_results)

        elif "path_query" in enhanced_query:
            # 执行路径查询
            success, output, _ = self.kg_support._execute_nebula(enhanced_query["path_query"])
            if success:
                results = self._parse_path_results(output)

        elif "aggregation_queries" in enhanced_query:
            # 执行聚合查询
            for query_info in enhanced_query["aggregation_queries"]:
                success, output, _ = self.kg_support._execute_nebula(query_info["query"])
                if success:
                    parsed_results = self._parse_aggregation_results(output)
                    results.append({
                        "description": query_info["description"],
                        "results": parsed_results
                    })

        return results

    def _parse_query_results(self, output: str) -> List[Dict]:
        """解析查询结果"""
        results = []
        lines = output.split('\n')

        for line in lines:
            if '|' in line and not line.strip().startswith(('+', '|', 'Got', '---')):
                parts = [p.strip().strip('"') for p in line.split('|') if p.strip()]
                if parts:
                    results.append({
                        "data": parts
                    })

        return results

    def _parse_path_results(self, output: str) -> List[Dict]:
        """解析路径结果"""
        # 路径结果解析逻辑
        return self._parse_query_results(output)

    def _parse_aggregation_results(self, output: str) -> List[Dict]:
        """解析聚合结果"""
        results = []
        lines = output.split('\n')

        for line in lines:
            if '|' in line and not line.strip().startswith(('+', '|', 'Got', '---')):
                parts = [p.strip().strip('"') for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    try:
                        # 尝试转换数字
                        value = int(parts[1]) if parts[1].isdigit() else parts[1]
                        results.append({
                            "category": parts[0],
                            "value": value
                        })
                    except:
                        results.append({
                            "category": parts[0],
                            "value": parts[1]
                        })

        return results


# 使用示例
if __name__ == "__main__":
    from legal_kg_support import LegalKnowledgeGraphSupport

    # 初始化
    kg_support = LegalKnowledgeGraphSupport()
    enhancer = GraphQueryEnhancer(kg_support)

    # 测试各种查询
    test_queries = [
        "查找与民法典相关的法律",
        "从民法典到刑法的路径",
        "统计各类法律的数量",
        "如果违反合同会有什么后果"
    ]

    for query in test_queries:
        print(f"\n=== 查询: {query} ===")
        enhanced = enhancer.enhance_query(query)
        print(f"查询类型: {enhanced['query_type']}")

        # 执行增强查询
        if "enhanced_queries" in enhanced:
            results = enhancer.execute_enhanced_query(enhanced)
            print(f"找到 {len(results)} 个结果")

    kg_support.close()