#!/usr/bin/env python3
from __future__ import annotations
"""
专利审查指南知识图谱导入器
"""

import json
import logging
import os
import re
from typing import Any

from arango_engine import ArangoGraphEngine, GraphEdge, GraphNode, GraphType

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentGuidelineImporter:
    """专利审查指南导入器"""

    def __init__(self):
        """初始化导入器"""
        self.engine = ArangoGraphEngine()
        self.graph_type = GraphType.PATENT_GUIDELINE

        # 创建图
        self.engine.create_graph(self.graph_type)

        # 知识提取规则
        self.concept_patterns = [
            r'([^，。；：！\n]+)(的概念|的定义)',
            r'([^，。；：！\n]+)(是指|指的是|定义为)',
            r'本发明公开了?(.+)',
            r'本发明涉及(.+)',
        ]

        # 引用关系模式
        self.reference_patterns = [
            r'参见(第[一二三四五六七八九十]+章|第\d+条)',
            r'根据(专利法|专利法实施细则)第\d+条',
            r'((?:CN|ZL)\d+\.?\d*)',  # 专利号
            r'审查指南.*部分',
        ]

    def import_from_parsed_data(self, json_path: str):
        """从解析的JSON数据导入

        Args:
            json_path: JSON文件路径
        """
        logger.info(f"开始导入审查指南数据: {json_path}")

        # 加载数据
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)

        # 导入文档节点
        self._import_document(data.get('document_info', {}))

        # 导入章节节点和关系
        if 'structure' in data:
            self._import_sections(data['structure'])

        # 导入引用关系
        if 'references' in data:
            self._import_references(data['references'])

        logger.info("✅ 审查指南导入完成")

    def _import_document(self, doc_info: dict[str, Any]):
        """导入文档节点

        Args:
            doc_info: 文档信息
        """
        doc_node = GraphNode(
            id="patent_guideline_root",
            type="document",
            properties={
                "title": doc_info.get("title", "专利审查指南"),
                "version": doc_info.get("version", "最新版"),
                "total_pages": doc_info.get("total_pages", 0),
                "publication_date": doc_info.get("publication_date", ""),
            },
            content=doc_info.get("description", ""),
            metadata={
                "source": "patent_guideline",
                "import_time": doc_info.get("import_time", ""),
            }
        )

        self.engine.add_node(self.graph_type, doc_node)

    def _import_sections(self, sections: list[dict[str, Any]]):
        """导入章节节点

        Args:
            sections: 章节列表
        """
        # 批量创建节点
        nodes = []
        for section in sections:
            if 'id' not in section:
                continue

            # 提取概念
            concepts = self._extract_concepts(section.get('content', ''))

            # 创建节点
            node = GraphNode(
                id=section['id'],
                type=section.get('type', 'section'),
                properties={
                    "title": section.get('title', ''),
                    "level": section.get('level', 0),
                    "page_number": section.get('page_number', 0),
                    "parent_id": section.get('parent_id', ''),
                    "concepts": concepts,
                },
                content=section.get('content', '')[:1000],  # 限制内容长度
                metadata={
                    "hierarchy_path": section.get('hierarchy_path', []),
                    "word_count": len(section.get('content', '')),
                }
            )
            nodes.append(node)

        # 批量插入
        for node in nodes:
            self.engine.add_node(self.graph_type, node)

        # 创建层次关系
        for section in sections:
            if 'parent_id' in section and section['parent_id']:
                edge = GraphEdge(
                    from_node=section['parent_id'],
                    to_node=section['id'],
                    relation_type="HAS_CHILD",
                    properties={
                        "level": section.get('level', 0),
                    },
                    weight=1.0
                )
                self.engine.add_edge(self.graph_type, edge)

    def _import_references(self, references: list[dict[str, Any]]):
        """导入引用关系

        Args:
            references: 引用列表
        """
        for ref in references:
            # 创建引用节点
            if ref.get('type') == 'law':
                ref_node = GraphNode(
                    id=f"law_{ref.get('article', '')}",
                    type="law_article",
                    properties={
                        "article": ref.get('article', ''),
                        "law_name": ref.get('law_name', ''),
                        "content": ref.get('content', ''),
                    },
                    content=ref.get('content', ''),
                )
                self.engine.add_node(self.graph_type, ref_node)

            elif ref.get('type') == 'case':
                ref_node = GraphNode(
                    id=f"case_{ref.get('case_id', '')}",
                    type="case",
                    properties={
                        "case_id": ref.get('case_id', ''),
                        "title": ref.get('title', ''),
                        "court": ref.get('court', ''),
                        "date": ref.get('date', ''),
                    },
                    content=ref.get('content', ''),
                )
                self.engine.add_node(self.graph_type, ref_node)

    def _extract_concepts(self, text: str) -> list[str]:
        """从文本中提取概念

        Args:
            text: 输入文本

        Returns:
            概念列表
        """
        concepts = []

        for pattern in self.concept_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    concept = match[0].strip()
                else:
                    concept = match.strip()

                if len(concept) > 2 and concept not in concepts:
                    concepts.append(concept)

        return concepts

    def import_technical_terms(self, terms_file: str):
        """导入技术术语

        Args:
            terms_file: 技术术语文件路径
        """
        logger.info(f"导入技术术语: {terms_file}")

        # 创建技术术语图
        self.engine.create_graph(GraphType.TECH_TERMS)

        # 加载术语数据
        with open(terms_file, encoding='utf-8') as f:
            terms_data = json.load(f)

        # 导入术语节点
        for category, terms in terms_data.items():
            for term in terms:
                term_node = GraphNode(
                    id=f"term_{term.get('name', '')}",
                    type="technical_term",
                    properties={
                        "name": term.get('name', ''),
                        "category": category,
                        "definition": term.get('definition', ''),
                        "synonyms": term.get('synonyms', []),
                        "related_terms": term.get('related_terms', []),
                    },
                    content=term.get('definition', ''),
                    metadata={
                        "source": "technical_dictionary",
                    }
                )
                self.engine.add_node(GraphType.TECH_TERMS, term_node)

        logger.info(f"✅ 技术术语导入完成，共导入 {len(terms_data)} 个类别")

def main():
    """主函数"""
    importer = PatentGuidelineImporter()

    # 导入审查指南
    json_path = "/Users/xujian/Athena工作平台/patent-guideline-system/data/processed/test_parse_result.json"
    importer.import_from_parsed_data(json_path)

    # 导入技术术语（如果存在）
    terms_file = "/Users/xujian/Athena工作平台/knowledge_graph/data/tech_terms.json"
    if os.path.exists(terms_file):
        importer.import_technical_terms(terms_file)

    # 打印统计信息
    for graph_type in [GraphType.PATENT_GUIDELINE, GraphType.TECH_TERMS]:
        stats = importer.engine.get_graph_statistics(graph_type)
        if stats:
            print(f"\n📊 {stats['graph_type']} 统计信息:")
            print(f"  节点数: {stats['nodes']}")
            print(f"  边数: {stats['edges']}")

if __name__ == "__main__":
    main()
