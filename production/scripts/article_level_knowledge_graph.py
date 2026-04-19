#!/usr/bin/env python3
"""
条款级知识图谱构建器
Article-Level Knowledge Graph Builder

构建基于条款的法律知识图谱

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KGNode:
    """知识图谱节点"""
    node_id: str
    node_type: str  # Article, Entity, Law, Concept
    label: str
    properties: dict
    embeddings: list[float] | None = None

@dataclass
class KGEdge:
    """知识图谱边"""
    edge_id: str
    edge_type: str  # REFERENCES, MODIFIES, DEFINES, CONTAINS, etc.
    source_id: str
    target_id: str
    properties: dict
    weight: float = 1.0

class ArticleLevelKnowledgeGraph:
    """条款级知识图谱构建器"""

    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.qdrant_url = "http://localhost:6333"

        # 节点类型定义
        self.node_types = {
            "Article": "法律条款",
            "Entity": "实体",
            "Law": "法律文件",
            "Concept": "法律概念",
            "Institution": "机构",
            "Time": "时间",
            "Amount": "金额",
            "Location": "地点"
        }

        # 边类型定义
        self.edge_types = {
            "REFERENCES": "引用",
            "MODIFIES": "修改",
            "REPLACES": "替代",
            "ABOLISHES": "废止",
            "DEFINES": "定义",
            "CONTAINS": "包含",
            "APPLIES_TO": "适用于",
            "IMPOSES": "规定",
            "PROHIBITS": "禁止",
            "PERMITS": "允许",
            "REGULATES": "监管",
            "INTERPRETS": "解释"
        }

    def load_data(self) -> dict:
        """加载已提取的数据"""
        # 加载条款向量数据
        articles_response = requests.post(
            f"{self.qdrant_url}/collections/legal_articles_v3_1024/points/scroll",
            json={
                "limit": 1000,
                "with_payload": True,
                "with_vector": True
            }
        )

        # 加载实体数据
        entities_file = sorted(
            Path("/Users/xujian/Athena工作平台/production/data/knowledge_graph").glob("legal_entities_v2_*.json")
        )[-1]

        # 加载关系数据
        relations_file = sorted(
            Path("/Users/xujian/Athena工作平台/production/data/knowledge_graph").glob("legal_relations_v2_*.json")
        )[-1]

        data = {
            "articles": [],
            "entities": [],
            "relations": []
        }

        # 处理条款数据
        if articles_response.status_code == 200:
            points = articles_response.json().get('result', {}).get('points', [])
            for point in points:
                payload = point.get('payload', {})
                data["articles"].append({
                    "id": point.get('id'),
                    "vector": point.get('vector'),
                    "article_number": payload.get('article_number'),
                    "title": payload.get('title'),
                    "content": payload.get('content'),
                    "file_title": payload.get('file_title'),
                    "chapter": payload.get('chapter'),
                    "section": payload.get('section')
                })

        # 处理实体数据
        if entities_file.exists():
            with open(entities_file, encoding='utf-8') as f:
                data["entities"] = json.load(f)

        # 处理关系数据
        if relations_file.exists():
            with open(relations_file, encoding='utf-8') as f:
                data["relations"] = json.load(f)

        logger.info(f"加载完成: {len(data['articles'])} 条款, {len(data['entities'])} 实体, {len(data['relations'])} 关系")

        return data

    def build_nodes(self, data: dict) -> Any:
        """构建知识图谱节点"""
        logger.info("\n🏗️ 构建知识图谱节点...")

        # 1. 条款节点
        for article in data["articles"]:
            node_id = article["id"]
            node = KGNode(
                node_id=node_id,
                node_type="Article",
                label=f'{article["file_title"]} - 第{article["article_number"]}条',
                properties={
                    "article_number": article["article_number"],
                    "title": article["title"],
                    "content": article["content"],
                    "file_title": article["file_title"],
                    "chapter": article.get("chapter", ""),
                    "section": article.get("section", ""),
                    "text_length": len(article.get("content", "")),
                    "has_keywords": len(article.get("keywords", [])),
                    "domain": self.identify_article_domain(article.get("title", "") + article.get("content", ""))
                },
                embeddings=article.get("vector")
            )
            self.nodes[node_id] = node

        # 2. 实体节点（去重）
        entity_map = {}
        for entity in data["entities"]:
            # 使用标准化名称去重
            normalized_name = entity.get("normalized_name", entity["entity_name"])
            if normalized_name not in entity_map:
                entity_id = f"entity_{len(entity_map)}"
                entity_map[normalized_name] = entity_id

                node = KGNode(
                    node_id=entity_id,
                    node_type=self.get_node_type(entity["entity_type"]),
                    label=normalized_name,
                    properties={
                        "original_name": entity["entity_name"],
                        "entity_type": entity["entity_type"],
                        "category": entity.get("attributes", {}).get("category", ""),
                        "confidence": entity.get("confidence", 0.0),
                        "occurrences": 1,
                        "contexts": [entity.get("context", "")]
                    }
                )
                self.nodes[entity_id] = node
            else:
                # 更新已有实体
                entity_id = entity_map[normalized_name]
                node = self.nodes[entity_id]
                node.properties["occurrences"] += 1
                if entity.get("context") not in node.properties["contexts"]:
                    node.properties["contexts"].append(entity.get("context", ""))

        # 3. 法律文件节点
        law_titles = {article["file_title"] for article in data["articles"]}
        for title in law_titles:
            law_id = f"law_{hash(title) % 10000}"
            node = KGNode(
                node_id=law_id,
                node_type="Law",
                label=title,
                properties={
                    "title": title,
                    "article_count": len([a for a in data["articles"] if a["file_title"] == title]),
                    "law_type": self.identify_law_type(title),
                    "status": "active"
                }
            )
            self.nodes[law_id] = node

        # 4. 概念节点（从条款标题中提取）
        concepts = self.extract_concepts(data["articles"])
        for concept, properties in concepts.items():
            concept_id = f"concept_{hash(concept) % 10000}"
            node = KGNode(
                node_id=concept_id,
                node_type="Concept",
                label=concept,
                properties=properties
            )
            self.nodes[concept_id] = node

        logger.info(f"  节点构建完成: {len(self.nodes)} 个节点")
        logger.info(f"    - 条款节点: {len([n for n in self.nodes.values() if n.node_type == 'Article'])}")
        logger.info(f"    - 实体节点: {len([n for n in self.nodes.values() if n.node_type.startswith('Entity')])}")
        logger.info(f"    - 法律文件节点: {len([n for n in self.nodes.values() if n.node_type == 'Law'])}")
        logger.info(f"    - 概念节点: {len([n for n in self.nodes.values() if n.node_type == 'Concept'])}")

    def get_node_type(self, entity_type: str) -> str:
        """获取节点类型"""
        type_mapping = {
            "机构": "Institution",
            "地点": "Location",
            "时间": "Time",
            "金额": "Amount",
            "人物": "Entity",
            "法律文件": "Law"
        }
        return type_mapping.get(entity_type, "Entity")

    def identify_article_domain(self, text: str) -> str:
        """识别条款领域"""
        domain_keywords = {
            "民法": ["民事", "合同", "侵权", "物权", "债权", "人格权", "婚姻", "继承"],
            "刑法": ["犯罪", "刑罚", "刑事责任", "故意", "过失", "正当防卫"],
            "行政法": ["行政", "处罚", "许可", "复议", "诉讼"],
            "宪法": ["宪法", "公民", "基本权利", "义务", "国家机构"],
            "商法": ["公司", "企业", "破产", "保险", "票据", "证券"],
            "经济法": ["市场", "竞争", "消费者", "产品质量", "价格"],
            "诉讼法": ["诉讼", "审判", "证据", "执行", "仲裁", "管辖"],
            "知识产权": ["专利", "商标", "著作权", "版权", "知识产权"]
        }

        scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[domain] = score

        return max(scores, key=scores.get) if scores else "其他"

    def identify_law_type(self, title: str) -> str:
        """识别法律类型"""
        if "法" in title and "中华人民共和国" in title:
            return "法律"
        elif "条例" in title:
            return "行政法规"
        elif "规定" in title or "办法" in title:
            return "部门规章"
        elif "司法解释" in title:
            return "司法解释"
        else:
            return "其他"

    def extract_concepts(self, articles: list[dict]) -> dict:
        """提取法律概念"""
        concepts = {}
        concept_patterns = [
            "民事权利", "民事义务", "刑事责任", "行政责任", "违约责任", "侵权责任",
            "正当防卫", "紧急避险", "不可抗力", "善意取得", "诉讼时效",
            "合同效力", "物权变动", "知识产权", "商标权", "专利权", "著作权",
            "行政处罚", "行政许可", "行政复议", "行政诉讼", "国家赔偿"
        ]

        for article in articles:
            text = f"{article.get('title', '')} {article.get('content', '')}"
            for concept in concept_patterns:
                if concept in text:
                    if concept not in concepts:
                        concepts[concept] = {
                            "occurrences": 0,
                            "article_count": 0,
                            "related_laws": set(),
                            "definition": ""
                        }
                    concepts[concept]["occurrences"] += 1
                    concepts[concept]["related_laws"].add(article["file_title"])

        # 转换set为list
        for concept in concepts:
            concepts[concept]["related_laws"] = list(concepts[concept]["related_laws"])

        return concepts

    def build_edges(self, data: dict) -> Any:
        """构建知识图谱边"""
        logger.info("\n🔗 构建知识图谱边...")

        edge_counter = 0

        # 1. 法律文件 -> 条款 (CONTAINS)
        law_to_articles = {}
        for article in data["articles"]:
            law_title = article["file_title"]
            law_id = f"law_{hash(law_title) % 10000}"
            if law_id not in law_to_articles:
                law_to_articles[law_id] = []
            law_to_articles[law_id].append(article["id"])

        for law_id, article_ids in law_to_articles.items():
            for article_id in article_ids:
                edge = KGEdge(
                    edge_id=f"edge_{edge_counter}",
                    edge_type="CONTAINS",
                    source_id=law_id,
                    target_id=article_id,
                    properties={"relationship": "法律包含条款"},
                    weight=1.0
                )
                self.edges[edge.edge_id] = edge
                edge_counter += 1

        # 2. 条款 -> 实体 (CONTAINS)
        # 基于实体出现的条款建立关系
        entity_articles = {}
        for entity in data["entities"]:
            article_id = entity["article_id"]
            normalized_name = entity.get("normalized_name", entity["entity_name"])

            # 查找对应的实体节点
            entity_node_id = None
            for node_id, node in self.nodes.items():
                if node.node_type.startswith("Entity") and node.label == normalized_name:
                    entity_node_id = node_id
                    break

            if entity_node_id and article_id in self.nodes:
                edge_id = f"edge_{edge_counter}"
                edge = KGEdge(
                    edge_id=edge_id,
                    edge_type="CONTAINS",
                    source_id=article_id,
                    target_id=entity_node_id,
                    properties={
                        "relationship": "条款包含实体",
                        "context": entity.get("context", ""),
                        "confidence": entity.get("confidence", 0.0)
                    },
                    weight=entity.get("confidence", 0.5)
                )
                self.edges[edge_id] = edge
                edge_counter += 1

        # 3. 实体 -> 实体 (RELATED_TO)
        # 基于共现关系
        entity_cooccurrence = {}
        for entity in data["entities"]:
            article_id = entity["article_id"]
            normalized_name = entity.get("normalized_name", entity["entity_name"])

            if article_id not in entity_cooccurrence:
                entity_cooccurrence[article_id] = []
            entity_cooccurrence[article_id].append(normalized_name)

        for article_id, entities_in_article in entity_cooccurrence.items():
            # 同一文章中的实体建立关系
            for i, entity1 in enumerate(entities_in_article):
                for entity2 in entities_in_article[i+1:]:
                    entity1_id = None
                    entity2_id = None

                    # 查找实体节点ID
                    for node_id, node in self.nodes.items():
                        if node.label == entity1 and node.node_type.startswith("Entity"):
                            entity1_id = node_id
                        if node.label == entity2 and node.node_type.startswith("Entity"):
                            entity2_id = node_id

                    if entity1_id and entity2_id:
                        edge_id = f"edge_{edge_counter}"
                        edge = KGEdge(
                            edge_id=edge_id,
                            edge_type="RELATED_TO",
                            source_id=entity1_id,
                            target_id=entity2_id,
                            properties={
                                "relationship": "实体共现",
                                "co_article": article_id,
                                "strength": 0.3
                            },
                            weight=0.3
                        )
                        self.edges[edge_id] = edge
                        edge_counter += 1

        # 4. 处理已提取的关系
        for relation in data["relations"]:
            # 根据关系类型映射
            relation_type_mapping = {
                "引用": "REFERENCES",
                "修改": "MODIFIES",
                "废止": "ABOLISHES",
                "解释": "INTERPRETS",
                "执行": "REGULATES"
            }

            mapped_type = relation_type_mapping.get(
                relation["relation_type"].split("_")[0],
                "REFERENCES"
            )

            # 查找对应的节点
            source_id = relation.get("source_article", relation.get("source_entity"))
            target_entity = relation.get("target_entity", "")

            # 跳过无效的关系
            if source_id not in self.nodes:
                continue

            # 如果目标是实体，查找实体节点
            target_id = None
            if target_entity.startswith("《"):
                # 法律文件
                target_law = target_entity.strip("《》")
                for node_id, node in self.nodes.items():
                    if node.node_type == "Law" and target_law in node.label:
                        target_id = node_id
                        break
            else:
                # 实体
                for node_id, node in self.nodes.items():
                    if node.node_type.startswith("Entity") and node.label == target_entity:
                        target_id = node_id
                        break

            if target_id:
                edge_id = f"edge_{edge_counter}"
                edge = KGEdge(
                    edge_id=edge_id,
                    edge_type=mapped_type,
                    source_id=source_id,
                    target_id=target_id,
                    properties={
                        "relationship": relation.get("description", ""),
                        "strength": relation.get("strength", 0.7)
                    },
                    weight=relation.get("strength", 0.7)
                )
                self.edges[edge_id] = edge
                edge_counter += 1

        logger.info(f"  边构建完成: {len(self.edges)} 条边")

        # 统计边类型
        edge_type_stats = {}
        for edge in self.edges.values():
            edge_type_stats[edge.edge_type] = edge_type_stats.get(edge.edge_type, 0) + 1

        logger.info("  边类型分布:")
        for edge_type, count in edge_type_stats.items():
            logger.info(f"    {edge_type}: {count}")

    def export_knowledge_graph(self) -> dict:
        """导出知识图谱"""
        logger.info("\n📤 导出知识图谱...")

        # 转换为可序列化格式
        kg_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "v2.0",
                "description": "条款级法律知识图谱",
                "statistics": {
                    "node_count": len(self.nodes),
                    "edge_count": len(self.edges),
                    "node_types": {},
                    "edge_types": {}
                }
            },
            "nodes": [],
            "edges": []
        }

        # 统计节点类型
        for node in self.nodes.values():
            kg_data["metadata"]["statistics"]["node_types"][node.node_type] = \
                kg_data["metadata"]["statistics"]["node_types"].get(node.node_type, 0) + 1

            kg_data["nodes"].append({
                "id": node.node_id,
                "type": node.node_type,
                "label": node.label,
                "properties": node.properties,
                "embeddings": node.embeddings
            })

        # 统计边类型
        for edge in self.edges.values():
            kg_data["metadata"]["statistics"]["edge_types"][edge.edge_type] = \
                kg_data["metadata"]["statistics"]["edge_types"].get(edge.edge_type, 0) + 1

            kg_data["edges"].append({
                "id": edge.edge_id,
                "type": edge.edge_type,
                "source": edge.source_id,
                "target": edge.target_id,
                "properties": edge.properties,
                "weight": edge.weight
            })

        # 保存知识图谱
        kg_file = Path("/Users/xujian/Athena工作平台/production/data/knowledge_graph") / \
                  f"article_level_kg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        kg_file.parent.mkdir(parents=True, exist_ok=True)

        with open(kg_file, 'w', encoding='utf-8') as f:
            json.dump(kg_data, f, ensure_ascii=False, indent=2)

        logger.info(f"  知识图谱已保存: {kg_file}")

        # 保存简化的Cypher脚本（用于导入Neo4j）
        self.export_cypher_script(kg_data)

        return kg_data

    def export_cypher_script(self, kg_data: dict) -> Any:
        """导出Cypher脚本"""
        logger.info("\n💾 生成Cypher脚本...")

        cypher_file = Path("/Users/xujian/Athena工作平台/production/data/knowledge_graph") / \
                    f"import_kg_cypher_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cypher"

        with open(cypher_file, 'w', encoding='utf-8') as f:
            f.write("// 创建知识图谱约束\n")
            f.write("CREATE CONSTRAINT ON (n:Article) REQUIRE n.id IS UNIQUE;\n")
            f.write("CREATE CONSTRAINT ON (n:Entity) REQUIRE n.id IS UNIQUE;\n")
            f.write("CREATE CONSTRAINT ON (n:Law) REQUIRE n.id IS UNIQUE;\n")
            f.write("CREATE CONSTRAINT ON (n:Concept) REQUIRE n.id IS UNIQUE;\n\n")

            # 创建节点
            f.write("// 创建节点\n")
            for node in kg_data["nodes"]:
                label = node["type"]
                properties = json.dumps(node["properties"], ensure_ascii=False)
                f.write(f'CREATE (:{label} {{id: "{node["id"]}", label: "{node["label"]}", properties: {properties}}});\n')

            f.write("\n// 创建关系\n")
            for edge in kg_data["edges"]:
                properties = json.dumps(edge["properties"], ensure_ascii=False)
                f.write(f'MATCH (a), (b) WHERE a.id = "{edge["source"]}" AND b.id = "{edge["target"]}" ')
                f.write(f'CREATE (a)-[:{edge["type"]} {{properties: {properties}, weight: {edge["weight"]}}}]->(b);\n')

        logger.info(f"  Cypher脚本已保存: {cypher_file}")

    def visualize_sample(self, kg_data: dict) -> Any:
        """可视化样本图谱"""
        logger.info("\n🎨 生成样本可视化...")

        # 生成Dot格式的图谱描述
        dot_file = Path("/Users/xujian/Athena工作平台/production/data/knowledge_graph") / \
                  f"kg_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dot"

        with open(dot_file, 'w', encoding='utf-8') as f:
            f.write("digraph LegalKG {\n")
            f.write("  rankdir=LR;\n")
            f.write("  node [shape=box];\n\n")

            # 只显示前50个节点和边
            sample_nodes = list(kg_data["nodes"])[:50]
            sample_edges = list(kg_data["edges"])[:50]

            # 节点定义
            for node in sample_nodes:
                color = {
                    "Article": "lightblue",
                    "Law": "lightgreen",
                    "Entity": "lightyellow",
                    "Concept": "lightpink",
                    "Institution": "orange",
                    "Location": "purple",
                    "Time": "cyan"
                }.get(node["type"], "gray")

                label = node["label"][:20]  # 限制长度
                f.write(f'  "{node["id"]}" [label="{label}", fillcolor="{color}", style=filled];\n')

            f.write("\n")

            # 边定义
            for edge in sample_edges:
                if edge["source"] in [n["id"] for n in sample_nodes] and \
                   edge["target"] in [n["id"] for n in sample_nodes]:
                    f.write(f'  "{edge["source"]}" -> "{edge["target"]} [label="{edge["type"]}"];\n')

            f.write("}\n")

        logger.info(f"  样本图谱已保存: {dot_file}")

def main() -> None:
    """主函数"""
    print("="*100)
    print("🕸️ 条款级知识图谱构建器 🕸️")
    print("="*100)

    kg_builder = ArticleLevelKnowledgeGraph()

    # 加载数据
    data = kg_builder.load_data()

    if not data["articles"]:
        logger.warning("没有找到条款数据，请先运行条款级向量化")
        return

    # 构建知识图谱
    kg_builder.build_nodes(data)
    kg_builder.build_edges(data)

    # 导出知识图谱
    kg_data = kg_builder.export_knowledge_graph()

    # 可视化样本
    kg_builder.visualize_sample(kg_data)

    print("\n✅ 条款级知识图谱构建完成！")
    print("📊 图谱统计:")
    print(f"   节点总数: {kg_data['metadata']['statistics']['node_count']}")
    print(f"   边总数: {kg_data['metadata']['statistics']['edge_count']}")
    print(f"   节点类型: {kg_data['metadata']['statistics']['node_types']}")
    print(f"   边类型: {kg_data['metadata']['statistics']['edge_types']}")

if __name__ == "__main__":
    main()
