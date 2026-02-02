#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利审查指南PDF解析器
Patent Guideline PDF Parser

解析专利审查指南PDF，提取层级结构和内容
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class DocumentNode:
    """文档节点"""
    id: str
    title: str
    level: int  # 1=部分, 2=章, 3=节, 4=条, 5=段落
    content: str
    parent_id: str | None = None
    children_ids: Optional[List[str] = None
    page_number: int | None = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []
        if self.metadata is None:
            self.metadata = {}

class PatentGuidelineParser:
    """专利审查指南解析器"""

    def __init__(self, pdf_path: str):
        """初始化解析器

        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = pdf_path
        self.document_tree = []

        # 定义层级识别模式
        self.patterns = {
            'part': {
                'pattern': r'^第([一二三四五六七八九十]+)部分\s*(.*)',
                'level': 1,
                'example': '第二部分 实质审查'
            },
            'chapter': {
                'pattern': r'^第([一二三四五六七八九十]+)章\s*(.*)',
                'level': 2,
                'example': '第四章 创造性'
            },
            'section': {
                'pattern': r'^(\d+)\.(.*)',
                'level': 3,
                'example': '3.2 创造性的概念'
            },
            'subsection': {
                'pattern': r'^(\d+)\.(\d+)\.(.*)',
                'level': 4,
                'example': '3.2.1 创造性的判断原则'
            },
            'subsubsection': {
                'pattern': r'^(\d+)\.(\d+)\.(\d+)\.(.*)',
                'level': 5,
                'example': '3.2.1.1 判断方法'
            },
            'case': {
                'pattern': r'^【(例\d+)】\s*(.*)',
                'level': 6,
                'example': '【例1】'
            },
            'law_reference': {
                'pattern': r'专利法第(\d+)条',
                'level': None,
                'example': '专利法第二十二条'
            }
        }

    def parse(self) -> Dict[str, Any]:
        """解析PDF文档

        Returns:
            解析后的结构化数据
        """
        logger.info(f"开始解析专利审查指南: {self.pdf_path}")

        # 使用pdfplumber解析PDF
        with pdfplumber.open(self.pdf_path) as pdf:
            all_text = []
            page_contents = []

            # 提取每页文本，保持页码信息
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text.strip():
                    page_contents.append({
                        'page_number': page_num,
                        'text': text
                    })
                    all_text.append(text)

        # 合并所有文本
        full_text = '\n'.join(all_text)

        # 解析结构
        structured_data = self._parse_structure(full_text, page_contents)

        # 提取引用关系
        references = self._extract_references(full_text)

        # 构建文档树
        self.document_tree = self._build_document_tree(structured_data)

        result = {
            'document_info': {
                'title': '专利审查指南（最新版）',
                'total_pages': len(page_contents),
                'total_sections': len(structured_data),
                'parsed_at': self._get_timestamp()
            },
            'structure': structured_data,
            'document_tree': self._serialize_tree(),
            'references': references,
            'statistics': self._get_statistics()
        }

        logger.info(f"解析完成: {result['statistics']}")
        return result

    def _parse_structure(self, text: str, page_contents: List[Dict]) -> List[Dict[str, Any]]:
        """解析文档结构

        Args:
            text: 完整文本
            page_contents: 每页内容列表

        Returns:
            结构化章节列表
        """
        sections = []
        lines = text.split('\n')

        current_section = None
        section_buffer = []
        section_start_page = 1

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 检查是否是章节标题
            section_match = self._match_section_pattern(line)

            if section_match:
                # 保存上一个section的内容
                if current_section and section_buffer:
                    current_section['content'] = '\n'.join(section_buffer)
                    current_section['end_page'] = self._find_page_number(line, page_contents)
                    sections.append(current_section)

                # 创建新section
                section_type, number, title = section_match
                section_id = self._generate_section_id(section_type, number)

                current_section = {
                    'id': section_id,
                    'type': section_type,
                    'number': number,
                    'title': title,
                    'level': self.patterns[section_type]['level'],
                    'content': '',
                    'start_page': self._find_page_number(line, page_contents),
                    'parent_id': None,
                    'children': [],
                    'references': []
                }

                section_buffer = []
            else:
                # 添加内容到当前section
                if current_section:
                    section_buffer.append(line)

        # 处理最后一个section
        if current_section and section_buffer:
            current_section['content'] = '\n'.join(section_buffer)
            current_section['end_page'] = self._find_page_number(line, page_contents)
            sections.append(current_section)

        return sections

    def _match_section_pattern(self, line: str) -> Tuple[str, str, str | None]:
        """匹配章节标题模式

        Args:
            line: 文本行

        Returns:
            (section_type, number, title) 或 None
        """
        line = line.strip()

        for pattern_name, pattern_info in self.patterns.items():
            if pattern_info['level'] is None:
                continue  # 跳过非章节模式

            match = re.match(pattern_info['pattern'], line)
            if match:
                if pattern_name in ['section', 'subsection', 'subsubsection']:
                    # 处理数字层级
                    parts = match.groups()
                    if pattern_name == 'section':
                        number = parts[0]
                        title = parts[1]
                    elif pattern_name == 'subsection':
                        number = f"{parts[0]}.{parts[1]}"
                        title = parts[2]
                    else:  # subsubsection
                        number = f"{parts[0]}.{parts[1]}.{parts[2]}"
                        title = parts[3]
                else:
                    # 处理中文层级
                    number = match.group(1)
                    title = match.group(2).strip()

                return pattern_name, number, title

        return None

    def _generate_section_id(self, section_type: str, number: str) -> str:
        """生成section ID

        Args:
            section_type: 章节类型
            number: 章节编号

        Returns:
            唯一ID
        """
        # 简化处理，实际应根据层级生成更精确的ID
        type_map = {
            'part': 'P',
            'chapter': 'C',
            'section': 'S',
            'subsection': 'SS',
            'subsubsection': 'SSS'
        }

        prefix = type_map.get(section_type, 'X')
        # 清理编号，只保留数字和点
        clean_number = re.sub(r'[^\d.]', '', number)

        return f"{prefix}{clean_number}"

    def _find_page_number(self, line: str, page_contents: List[Dict]) -> int:
        """查找文本行所在的页码

        Args:
            line: 文本行
            page_contents: 每页内容

        Returns:
            页码
        """
        # 简化实现：假设按顺序查找
        line_short = line[:50]  # 使用前50个字符匹配

        for page in page_contents:
            if line_short in page['text']:
                return page['page_number']

        return 1  # 默认返回第1页

    def _extract_references(self, text: str) -> List[Dict[str, Any]]:
        """提取引用关系

        Args:
            text: 文本内容

        Returns:
            引用列表
        """
        references = []

        # 查找"参见"引用
        see_also_pattern = r'参见([^。\n]*第([^。\n]*?)节)'
        for match in re.finditer(see_also_pattern, text):
            references.append({
                'type': 'see_also',
                'target': match.group(2),
                'context': match.group(0),
                'position': match.start()
            })

        # 查找法条引用
        law_pattern = r'(专利法|实施细则)第(\d+)条'
        for match in re.finditer(law_pattern, text):
            references.append({
                'type': 'law_reference',
                'law': match.group(1),
                'article': match.group(2),
                'context': match.group(0),
                'position': match.start()
            })

        # 查找案例引用
        case_pattern = r'【(例\d+)】'
        for match in re.finditer(case_pattern, text):
            references.append({
                'type': 'case_reference',
                'case_id': match.group(1),
                'context': match.group(0),
                'position': match.start()
            })

        return references

    def _build_document_tree(self, sections: List[Dict]) -> List[DocumentNode]:
        """构建文档树结构

        Args:
            sections: 章节列表

        Returns:
            文档树节点列表
        """
        nodes = []
        node_dict = {}

        # 创建所有节点
        for section in sections:
            node = DocumentNode(
                id=section['id'],
                title=section['title'],
                level=section['level'],
                content=section['content'],
                metadata={
                    'type': section['type'],
                    'number': section['number'],
                    'start_page': section['start_page'],
                    'end_page': section['end_page']
                }
            )
            nodes.append(node)
            node_dict[node.id] = node

        # 建立父子关系
        stack = []
        for node in sorted(nodes, key=lambda x: (x.level, x.metadata['number'])):
            # 清理栈中比当前级别高的节点
            while stack and stack[-1].level >= node.level:
                stack.pop()

            # 设置父节点
            if stack:
                parent = stack[-1]
                node.parent_id = parent.id
                parent.children_ids.append(node.id)

            stack.append(node)

        self.nodes = node_dict
        return nodes

    def _serialize_tree(self) -> Dict[str, Any]:
        """序列化树结构

        Returns:
            序列化的树结构
        """
        if not hasattr(self, 'nodes'):
            return {}

        # 找到根节点
        roots = [node for node in self.nodes.values() if node.parent_id is None]

        def serialize_node(node):
            return {
                'id': node.id,
                'title': node.title,
                'level': node.level,
                'content': node.content,
                'metadata': node.metadata,
                'children': [serialize_node(self.nodes[child_id])
                            for child_id in node.children_ids]
            }

        return {
            'roots': [serialize_node(root) for root in roots],
            'total_nodes': len(self.nodes)
        }

    def _get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        if not hasattr(self, 'nodes'):
            return {}

        stats = {
            'total_nodes': len(self.nodes),
            'nodes_by_level': {}
        }

        # 按级别统计
        for node in self.nodes.values():
            level = node.level
            if level not in stats['nodes_by_level']:
                stats['nodes_by_level'][level] = 0
            stats['nodes_by_level'][level] += 1

        return stats

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def save_to_json(self, output_path: str):
        """保存解析结果到JSON文件

        Args:
            output_path: 输出文件路径
        """
        data = self.parse()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"解析结果已保存到: {output_path}")

# 测试函数
def test_parser():
    """测试解析器"""
    pdf_path = '/Users/xujian/Athena工作平台/规则/专利审查指南（最新版）.pdf'

    if not Path(pdf_path).exists():
        logger.info(f"错误: 文件不存在 - {pdf_path}")
        return

    parser = PatentGuidelineParser(pdf_path)

    # 解析文档
    data = parser.parse()

    # 显示统计信息
    logger.info("\n=== 解析统计 ===")
    logger.info(f"文档标题: {data['document_info']['title']}")
    logger.info(f"总页数: {data['document_info']['total_pages']}")
    logger.info(f"章节数量: {data['document_info']['total_sections']}")
    logger.info(f"引用数量: {len(data['references'])}")

    # 显示层级分布
    logger.info("\n=== 层级分布 ===")
    for level, count in data['statistics']['nodes_by_level'].items():
        level_name = ['部分', '章', '节', '条', '段落'][level-1] if level <= 5 else f'Level{level}'
        logger.info(f"{level_name}: {count} 个")

    # 显示前5个章节
    logger.info("\n=== 前5个章节 ===")
    for i, section in enumerate(data['structure'][:5], 1):
        logger.info(f"\n{i}. [{section['type'].upper()}] {section['number']}")
        logger.info(f"   标题: {section['title']}")
        logger.info(f"   级别: {section['level']}")
        logger.info(f"   内容长度: {len(section['content'])} 字符")
        if section['content']:
            preview = section['content'][:100]
            logger.info(f"   预览: {preview}...")

    # 保存完整结果
    parser.save_to_json('/Users/xujian/Athena工作平台/patent_guideline_system/data/processed/guideline_structure.json')

if __name__ == '__main__':
    test_parser()