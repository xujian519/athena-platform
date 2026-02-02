#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入解析后的审查指南数据到Neo4j
Import parsed guideline data to Neo4j
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.models.graph_schema import Neo4jSchemaManager, NodeType, RelationshipType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GuidelineImporter:
    """审查指南导入器"""

    def __init__(self):
        """初始化导入器"""
        self.schema_manager = Neo4jSchemaManager()
        self.processed_sections = {}
        self.concept_cache = {}
        self.law_cache = {}
        self.case_cache = {}

    def import_from_json(self, json_path: str):
        """从JSON文件导入数据

        Args:
            json_path: JSON文件路径
        """
        logger.info(f"开始导入审查指南数据: {json_path}")

        # 加载JSON数据
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 创建约束和索引
        logger.info('创建数据库约束和索引...')
        self.schema_manager.create_constraints()
        self.schema_manager.create_indexes()

        # 导入文档信息
        logger.info('导入文档信息...')
        self._import_document(data['document_info'])

        # 导入结构化章节
        logger.info('导入章节结构...')
        self._import_sections(data['structure'])

        # 导入引用关系
        logger.info('导入引用关系...')
        self._import_references(data['references'])

        logger.info('✅ 导入完成！')

    def _import_document(self, doc_info: Dict[str, Any]):
        """导入文档节点

        Args:
            doc_info: 文档信息
        """
        from src.models.graph_schema import DocumentNode

        doc_node = DocumentNode(
            id='guideline_2024',
            title=doc_info['title'],
            version='2024版',
            publication_date=doc_info.get('parsed_at', ''),
            total_pages=doc_info.get('total_pages', 0)
        )

        self.schema_manager.create_document_node(doc_node)

    def _import_sections(self, sections: List[Dict[str, Any]]):
        """导入章节节点

        Args:
            sections: 章节列表
        """
        from src.models.graph_schema import ChapterNode, PartNode, SectionNode

        # 按级别分组
        parts = []
        chapters = []
        section_nodes = []

        for section in sections:
            section_type = section['type']
            level = section['level']

            # 构建层级路径
            hierarchy_path = self._build_hierarchy_path(section, sections)
            section['hierarchy_path'] = hierarchy_path

            if section_type == 'part':
                parts.append(section)
            elif section_type == 'chapter':
                chapters.append(section)
            else:
                section_nodes.append(section)

        # 导入部分
        for part in parts:
            part_node = PartNode(
                id=part['id'],
                number=self._chinese_to_number(part['number']),
                title=part['title'],
                description=part.get('content', '')[:200]  # 前200字符作为描述
            )
            self.schema_manager.create_part_node(part_node, 'guideline_2024')

        # 导入章节
        for chapter in chapters:
            # 找到所属部分
            parent_id = self._find_parent(chapter, parts)

            chapter_node = ChapterNode(
                id=chapter['id'],
                number=self._chinese_to_number(chapter['number']),
                title=chapter['title'],
                summary=chapter.get('content', '')[:300]  # 前300字符作为摘要
            )
            self.schema_manager.create_chapter_node(chapter_node, parent_id)

        # 导入节
        for section in section_nodes:
            # 找到父节点
            parent_id = self._find_parent(section, chapters + section_nodes)

            # 限制内容长度
            content = section.get('content', '')
            if len(content) > 5000:
                content = content[:5000] + '...'

            section_node = SectionNode(
                id=section['id'],
                number=section['number'],
                title=section['title'],
                content=content,
                level=section['level'],
                start_page=section.get('start_page'),
                end_page=section.get('end_page'),
                parent_id=parent_id,
                hierarchy_path=section['hierarchy_path']
            )
            self.schema_manager.create_section_node(section_node, parent_id)

            # 提取并导入概念
            self._extract_and_import_concepts(section)

    def _build_hierarchy_path(self, section: Dict, all_sections: List) -> List[str]:
        """构建层级路径

        Args:
            section: 当前章节
            all_sections: 所有章节列表

        Returns:
            层级路径
        """
        path = [section['title']]
        current_level = section['level']

        # 简化处理：使用章节标题构建路径
        # 实际应该根据父子关系构建
        if current_level > 1:
            # 查找可能的父级
            for other in all_sections:
                if other['level'] == current_level - 1:
                    path.insert(0, other['title'])
                    break

        return path

    def _find_parent(self, section: Dict, potential_parents: List[Dict]) -> str:
        """查找父节点ID

        Args:
            section: 当前章节
            potential_parents: 潜在父节点列表

        Returns:
            父节点ID
        """
        # 简化处理：根据级别和编号推断
        for parent in potential_parents:
            if parent['level'] == section['level'] - 1:
                # 检查编号是否匹配
                if '.' in section['number']:
                    parent_num = section['number'].split('.')[0]
                    if parent_num == parent['number'].split('.')[-1]:
                        return parent['id']

        # 默认返回第一个匹配级别的
        for parent in potential_parents:
            if parent['level'] == section['level'] - 1:
                return parent['id']

        return None

    def _chinese_to_number(self, chinese_num: str) -> int:
        """中文数字转阿拉伯数字

        Args:
            chinese_num: 中文数字

        Returns:
            阿拉伯数字
        """
        mapping = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }

        # 处理"第十一"这样的
        if '十' in chinese_num and len(chinese_num) > 1:
            if chinese_num == '十':
                return 10
            elif chinese_num.startswith('十'):
                return mapping.get(chinese_num[1], 0) + 10
            else:
                return mapping.get(chinese_num[0], 0) * 10 + mapping.get(chinese_num[2:], 0)
        else:
            return mapping.get(chinese_num, 0)

    def _extract_and_import_concepts(self, section: Dict[str, Any]):
        """提取并导入概念

        Args:
            section: 章节信息
        """
        content = section.get('content', '')
        title = section.get('title', '')

        # 从标题中提取概念
        if len(title) > 2 and not any(x in title for x in ['第', '章', '节', '部分']):
            self._import_concept(title, section['id'])

        # 从内容中提取定义
        import re

        # 查找"XX是指"、"XX定义为"等模式
        patterns = [
            r'([^，。；：！''\n]{2,10})(是指|指的是|定义为|定义为：)',
            r'([^，。；：！''\n]{2,10})(的概念|的定义)'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                concept = match.group(1).strip()
                if len(concept) > 1 and not concept.isdigit():
                    self._import_concept(concept, section['id'])

    def _import_concept(self, concept_name: str, section_id: str):
        """导入概念节点

        Args:
            concept_name: 概念名称
            section_id: 章节ID
        """
        if concept_name not in self.concept_cache:
            from src.models.graph_schema import ConceptNode

            concept_node = ConceptNode(
                id=concept_name,
                name=concept_name,
                category='专利概念',
                synonyms=[]
            )
            self.schema_manager.create_concept_node(concept_node)
            self.concept_cache[concept_name] = concept_name

        # 创建关系
        self.schema_manager.create_reference_relationship(
            source_id=section_id,
            target_id=concept_name,
            reference_type='DEFINES'
        )

    def _import_references(self, references: List[Dict[str, Any]]):
        """导入引用关系

        Args:
            references: 引用列表
        """
        from src.models.graph_schema import CaseNode, LawArticleNode

        for ref in references:
            ref_type = ref['type']

            if ref_type == 'law_reference':
                # 导入法条
                law_name = ref.get('law', '专利法')
                article_num = int(ref.get('article', 0))

                if article_num > 0:
                    law_id = f"{law_name}_第{article_num}条"

                    if law_id not in self.law_cache:
                        law_node = LawArticleNode(
                            id=law_id,
                            law_name=law_name,
                            article_number=article_num,
                            article_type='法律条款'
                        )
                        self.schema_manager.create_law_article_node(law_node)
                        self.law_cache[law_id] = law_id

                    # 创建引用关系（这里需要找到源section）
                    # 简化处理，实际应该根据位置查找

            elif ref_type == 'case_reference':
                # 导入案例
                case_id = ref.get('case_id', '')

                if case_id and case_id not in self.case_cache:
                    case_node = CaseNode(
                        id=case_id,
                        case_id=case_id,
                        title=case_id,
                        content='',  # 需要从文档中提取
                        summary=''
                    )
                    self.schema_manager.create_case_node(case_node)
                    self.case_cache[case_id] = case_id

                    # 创建引用关系

    def close(self):
        """关闭连接"""
        self.schema_manager.close()

def main():
    """主函数"""
    # 配置文件路径
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'processed', 'test_parse_result.json')

    # 检查文件是否存在
    if not os.path.exists(json_path):
        logger.error(f"文件不存在: {json_path}")
        logger.info('请先运行解析脚本生成数据文件')
        return

    # 创建导入器
    importer = GuidelineImporter()

    try:
        # 执行导入
        importer.import_from_json(json_path)

        # 统计信息
        logger.info("\n=== 导入统计 ===")
        logger.info(f"导入的概念数: {len(importer.concept_cache)}")
        logger.info(f"导入的法条数: {len(importer.law_cache)}")
        logger.info(f"导入的案例数: {len(importer.case_cache)}")

    except Exception as e:
        logger.error(f"导入失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 关闭连接
        importer.close()

if __name__ == '__main__':
    main()