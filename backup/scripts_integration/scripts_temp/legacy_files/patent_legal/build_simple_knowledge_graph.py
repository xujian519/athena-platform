#!/usr/bin/env python3
"""
构建简化版专利法律法规知识图谱
Build Simple Patent Legal Knowledge Graph

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import os
import json
import logging
import re
import networkx as nx
from typing import List, Dict, Any, Tuple, Set
from datetime import datetime
from pathlib import Path
import aiofiles

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplePatentLegalKGBuilder:
    """简化版专利法律法规知识图谱构建器"""

    def __init__(self):
        """初始化"""
        self.graph = nx.DiGraph()
        self.entity_types = {
            "law": "法律",
            "regulation": "法规",
            "article": "条款",
            "concept": "概念",
            "procedure": "程序",
            "case": "案例"
        }

        # 关键法律术语
        self.legal_terms = {
            # 法律类型
            "专利法", "著作权法", "商标法", "反不正当竞争法",

            # 专利类型
            "发明专利", "实用新型专利", "外观设计专利", "国防专利",

            # 专利要件
            "新颖性", "创造性", "实用性", "优先权", "现有技术",

            # 审查程序
            "初步审查", "实质审查", "复审", "无效宣告", "行政复议",

            # 专利文档
            "权利要求书", "说明书", "附图", "摘要", "请求书",

            # 法律概念
            "侵权", "假冒", "许可", "转让", "质押", "强制许可",

            # 审查指南相关
            "审查指南", "实施细则", "操作规程", "标准", "规范"
        }

    async def load_documents(self, folder_path: str) -> List[Dict[str, Any]]:
        """加载文档"""
        folder_path = Path(folder_path)
        documents = []

        # 遍历所有文件
        for file_path in folder_path.glob("*"):
            if file_path.is_file():
                content = await self._extract_content(file_path)
                if content and len(content.strip()) > 100:
                    documents.append({
                        "file_name": file_path.name,
                        "file_path": str(file_path),
                        "content": content,
                        "type": self._classify_document(file_path.name, content)
                    })

        logger.info(f"加载了 {len(documents)} 个文档")
        return documents

    async def _extract_content(self, file_path: Path) -> str:
        """提取文件内容"""
        try:
            if file_path.suffix.lower() == '.md':
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    return await f.read()
            elif file_path.suffix.lower() == '.docx':
                from docx import Document
                doc = Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
            elif file_path.suffix.lower() == '.pdf':
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    content = []
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text and text.strip():
                            content.append(text)
                    return '\n'.join(content)
            else:
                return ""
        except Exception as e:
            logger.error(f"读取文件 {file_path} 失败: {e}")
            return ""

    def _classify_document(self, file_name: str, content: str) -> str:
        """分类文档类型"""
        if "法" in file_name or "法律" in content:
            return "law"
        elif "条例" in file_name or "规定" in file_name:
            return "regulation"
        elif "指南" in file_name or "审查" in content:
            return "procedure"
        elif "解释" in file_name or "案例" in content:
            return "case"
        else:
            return "concept"

    def extract_entities(self, documents: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """提取实体"""
        entities = {}
        entity_id = 0

        # 从文件名创建实体
        for doc in documents:
            entity_id += 1
            entities[f"entity_{entity_id}"] = {
                "id": f"entity_{entity_id}",
                "name": doc["file_name"].replace('.docx', '').replace('.pdf', '').replace('.md', ''),
                "type": doc["type"],
                "description": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                "source": doc["file_path"],
                "properties": {
                    "file_type": doc["file_name"].split('.')[-1] if '.' in doc["file_name"] else "unknown",
                    "content_length": len(doc["content"]),
                    "created_at": datetime.now().isoformat()
                }
            }

        # 提取关键术语作为概念实体
        concept_entities = set()
        for doc in documents:
            content = doc["content"]
            for term in self.legal_terms:
                if term in content:
                    concept_entities.add(term)

        for term in concept_entities:
            entity_id += 1
            entities[f"entity_{entity_id}"] = {
                "id": f"entity_{entity_id}",
                "name": term,
                "type": "concept",
                "description": f"专利法律术语: {term}",
                "source": "extracted",
                "properties": {
                    "category": "legal_term",
                    "created_at": datetime.now().isoformat()
                }
            }

        logger.info(f"提取了 {len(entities)} 个实体")
        return entities

    def extract_relationships(self, documents: List[Dict[str, Any]], entities: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取关系"""
        relationships = []
        rel_id = 0

        # 创建文档与术语之间的关系
        for doc in documents:
            doc_entity = None
            # 找到对应的文档实体
            for entity in entities.values():
                if entity.get("source") == doc["file_path"]:
                    doc_entity = entity
                    break

            if not doc_entity:
                continue

            # 查找文档中包含的术语
            content = doc["content"]
            for term in self.legal_terms:
                if term in content:
                    # 找到术语实体
                    term_entity = None
                    for entity in entities.values():
                        if entity["name"] == term and entity["type"] == "concept":
                            term_entity = entity
                            break

                    if term_entity:
                        rel_id += 1
                        relationships.append({
                            "id": f"rel_{rel_id}",
                            "source": doc_entity["id"],
                            "target": term_entity["id"],
                            "type": "contains",
                            "description": f"{doc_entity['name']} 包含术语 {term}",
                            "properties": {
                                "frequency": content.count(term),
                                "confidence": 1.0,
                                "created_at": datetime.now().isoformat()
                            }
                        })

        # 创建术语之间的关系
        related_terms = {
            ("专利法", "实施细则"): "defines",
            ("发明专利", "新颖性"): "requires",
            ("发明专利", "创造性"): "requires",
            ("发明专利", "实用性"): "requires",
            ("实用新型专利", "新颖性"): "requires",
            ("实用新型专利", "实用性"): "requires",
            ("外观设计专利", "新颖性"): "requires",
            ("权利要求书", "说明书"): "accompanies",
            ("侵权", "专利权"): "relates_to",
            ("许可", "转让"): "similar_to"
        }

        for (term1, term2), rel_type in related_terms.items():
            entity1 = None
            entity2 = None

            for entity in entities.values():
                if entity["name"] == term1:
                    entity1 = entity
                if entity["name"] == term2:
                    entity2 = entity

            if entity1 and entity2:
                rel_id += 1
                relationships.append({
                    "id": f"rel_{rel_id}",
                    "source": entity1["id"],
                    "target": entity2["id"],
                    "type": rel_type,
                    "description": f"{term1} {rel_type} {term2}",
                    "properties": {
                        "source": "predefined",
                        "confidence": 0.9,
                        "created_at": datetime.now().isoformat()
                    }
                })

        logger.info(f"提取了 {len(relationships)} 个关系")
        return relationships

    def build_networkx_graph(self, entities: Dict[str, Dict[str, Any]], relationships: List[Dict[str, Any]]):
        """构建NetworkX图"""
        # 添加节点
        for entity in entities.values():
            self.graph.add_node(
                entity["id"],
                name=entity["name"],
                type=entity["type"],
                description=entity.get("description", ""),
                **entity.get("properties", {})
            )

        # 添加边
        for rel in relationships:
            self.graph.add_edge(
                rel["source"],
                rel["target"],
                type=rel["type"],
                description=rel.get("description", ""),
                **rel.get("properties", {})
            )

        logger.info(f"构建了包含 {len(self.graph.nodes)} 个节点和 {len(self.graph.edges)} 条边的图")

    async def save_results(self, entities: Dict[str, Dict[str, Any]], relationships: List[Dict[str, Any]]):
        """保存结果"""
        output_dir = Path("/Users/xujian/Athena工作平台/data/patent_legal_kg_simple")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存实体
        entities_path = output_dir / "entities.json"
        async with aiofiles.open(entities_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(entities, ensure_ascii=False, indent=2))

        # 保存关系
        relationships_path = output_dir / "relationships.json"
        async with aiofiles.open(relationships_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(relationships, ensure_ascii=False, indent=2))

        # 保存图结构（NetworkX格式）
        graph_path = output_dir / "knowledge_graph.graphml"
        nx.write_graphml(self.graph, graph_path)

        # 保存统计信息
        stats = {
            "total_entities": len(entities),
            "total_relationships": len(relationships),
            "entity_types": list(set(e["type"] for e in entities.values())),
            "relationship_types": list(set(r["type"] for r in relationships)),
            "created_at": datetime.now().isoformat()
        }

        stats_path = output_dir / "stats.json"
        async with aiofiles.open(stats_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(stats, ensure_ascii=False, indent=2))

        logger.info(f"知识图谱数据已保存到: {output_dir}")

    def prepare_janusgraph_data(self, entities: Dict[str, Dict[str, Any]], relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """准备JanusGraph导入数据"""
        janus_data = {
            "vertices": [],
            "edges": []
        }

        # 准备顶点数据
        for entity in entities.values():
            vertex = {
                "label": entity["type"],
                "properties": {
                    "name": entity["name"],
                    "id": entity["id"],
                    "description": entity.get("description", ""),
                    "type": entity["type"],
                    **entity.get("properties", {})
                }
            }
            janus_data["vertices"].append(vertex)

        # 准备边数据
        for rel in relationships:
            edge = {
                "label": rel["type"],
                "source_vertex": rel["source"],
                "target_vertex": rel["target"],
                "properties": {
                    "description": rel.get("description", ""),
                    **rel.get("properties", {})
                }
            }
            janus_data["edges"].append(edge)

        # 保存JanusGraph导入数据
        output_dir = Path("/Users/xujian/Athena工作平台/data/patent_legal_kg_simple")
        janus_path = output_dir / "janusgraph_import.json"

        with open(janus_path, 'w', encoding='utf-8') as f:
            json.dump(janus_data, f, ensure_ascii=False, indent=2)

        logger.info(f"JanusGraph导入数据已保存到: {janus_path}")
        return janus_data

async def main():
    """主函数"""
    logger.info("开始构建简化版专利法律法规知识图谱...")

    # 创建构建器
    builder = SimplePatentLegalKGBuilder()

    # 加载文档
    documents = await builder.load_documents("/Users/xujian/学习资料/专利/专利法律法规")

    if not documents:
        logger.error("没有找到有效的文档")
        return

    # 提取实体
    entities = builder.extract_entities(documents)

    # 提取关系
    relationships = builder.extract_relationships(documents, entities)

    # 构建图
    builder.build_networkx_graph(entities, relationships)

    # 保存结果
    await builder.save_results(entities, relationships)

    # 准备JanusGraph数据
    builder.prepare_janusgraph_data(entities, relationships)

    logger.info("\n✅ 简化版专利法律法规知识图谱构建完成！")
    logger.info(f"\n处理统计:")
    logger.info(f"  处理文档数: {len(documents)}")
    logger.info(f"  实体数量: {len(entities)}")
    logger.info(f"  关系数量: {len(relationships)}")
    logger.info(f"  图节点数: {len(builder.graph.nodes)}")
    logger.info(f"  图边数: {len(builder.graph.edges)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())