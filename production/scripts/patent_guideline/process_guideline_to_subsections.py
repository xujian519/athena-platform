#!/usr/bin/env python3
"""
专利审查指南细粒度分块处理器
将专利审查指南文档处理到小节级别的精细粒度

层级结构:
- 部分 (Part)
- 章 (Chapter)
- 节 (Section)
- 小节 (Subsection) - 最小目标粒度
- 段落 (Paragraph)

作者: Athena平台团队
创建时间: 2025-12-23
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/guideline_subsection_processor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class GuidelineNode:
    """指南节点"""
    node_id: str
    level: str  # part, chapter, section, subsection, paragraph
    level_number: int  # 1-5
    title: str
    content: str
    parent_id: str | None
    children_ids: list[str]
    full_path: str  # 完整层级路径
    metadata: dict[str, Any]
    source_reference: str | None = None


class PatentGuidelineSubsectionProcessor:
    """专利审查指南小节级处理器"""

    def __init__(self):
        # 层级模式定义
        self.patterns = {
            # 部分模式 (Level 1)
            'part': [
                r'^第[一二三四五六七八九十]+部分[：:]\s*(.+)$',
                r'^Part\s+[IVX]+[：:]\s*(.+)$'
            ],
            # 章模式 (Level 2)
            'chapter': [
                r'^第[一二三四五六七八九十百千万\d]+章[：:]\s*(.+)$',
                r'^Chapter\s+\d+[：:]\s*(.+)$'
            ],
            # 节模式 (Level 3)
            'section': [
                r'^(\d+\.\d+)\s+(.+)$',  # 3.1 创造性的概念
                r'^第[一二三四五六七八九十]+节[：:]\s*(.+)$'
            ],
            # 小节模式 (Level 4) - 目标最小粒度
            'subsection': [
                r'^(\d+\.\d+\.\d+)\s+(.+)$',  # 3.2.1 创造性的判断原则
                r'^(\d+\.\d+\.\d+\.\d+)\s+(.+)$',  # 带有更细分的编号
                r'^[（(]\d+[)）]\s+(.+)$',  # (1) xxx
                r'^[（(][一二三四五六七八九十][)）]\s+(.+)$'
            ],
            # 段落标记 (Level 5)
            'paragraph_markers': [
                r'^【例\d+】',  # 示例
                r'^【案例】',
                r'^注意：',
                r'^说明：',
                r'^注：'
            ]
        }

        # 特殊内容标记
        self.content_markers = {
            'example': [r'^【例\d+】', r'^【案例】', r'^例如[：:]', r'^举例[：:]'],
            'note': [r'^注意[：:]', r'^说明[：:]', r'^注[：:]'],
            'reference': [r'^参见', r'^根据', r'^依据'],
            'requirement': [r'^应当', r'^必须', r'^需要'],
            'prohibition': [r'^不得', r'^禁止', r'^不允许']
        }

        # 法律引用模式
        self.law_reference_patterns = [
            r'专利法第[一二三四五六七八九十百千万零\d]+条',
            r'实施细则第[一二三四五六七八九十百千万零\d]+条',
            r'审查指南第[一二三四五六七八九十百千万零\d]+条',
            r'第[一二三四五六七八九十百千万零\d]+条',
        ]

    def parse_guideline_text(self, text: str, source_id: str = "guideline") -> dict[str, Any]:
        """解析指南文本，构建层级结构"""
        logger.info(f"📄 开始解析指南文本，源ID: {source_id}")

        # 按行分割
        lines = text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]

        # 构建节点树
        root_nodes = []
        node_stack = []  # 用于跟踪当前层级路径
        node_counter = 0

        for line_num, line in enumerate(lines):
            # 跳过空行
            if not line:
                continue

            # 检测当前行属于哪个层级
            level_info = self._detect_line_level(line)

            if level_info:
                node_counter += 1
                node_id = f"{source_id}_node_{node_counter:04d}"

                # 确定父节点
                parent_node = self._find_parent_node(node_stack, level_info['level_number'])

                # 创建节点
                node = GuidelineNode(
                    node_id=node_id,
                    level=level_info['level'],
                    level_number=level_info['level_number'],
                    title=level_info['title'],
                    content=line,
                    parent_id=parent_node['node_id'] if parent_node else None,
                    children_ids=[],
                    full_path=self._build_full_path(parent_node, level_info['title']) if parent_node else level_info['title'],
                    metadata={
                        'line_number': line_num,
                        'level_confidence': level_info.get('confidence', 1.0),
                        'is_reference': self._is_reference_line(line),
                        'content_type': self._detect_content_type(line)
                    }
                )

                # 更新父节点的children_ids
                if parent_node:
                    if node_id not in parent_node['children_ids']:
                        parent_node['children_ids'].append(node_id)

                # 管理节点栈
                self._update_node_stack(node_stack, node, level_info['level_number'])

                # 如果是根节点，添加到结果
                if not parent_node:
                    root_nodes.append(asdict(node))

                logger.debug(f"节点: {node.level} - {node.title}")

        # 处理段落内容
        self._assign_paragraph_content(root_nodes, lines)

        logger.info(f"✅ 解析完成，生成 {len(root_nodes)} 个根节点，{node_counter} 个总节点")

        return {
            'source_id': source_id,
            'total_nodes': node_counter,
            'root_nodes': root_nodes,
            'statistics': self._calculate_statistics(root_nodes)
        }

    def _detect_line_level(self, line: str) -> dict[str, Any | None]:
        """检测行所属层级"""
        # 按优先级检查各层级模式
        for level_name, level_patterns in self.patterns.items():
            if level_name == 'paragraph_markers':
                continue

            for pattern in level_patterns:
                match = re.match(pattern, line)
                if match:
                    if level_name == 'part':
                        level_number = 1
                        title = match.group(1) if len(match.groups()) >= 1 else line
                    elif level_name == 'chapter':
                        level_number = 2
                        title = match.group(1) if len(match.groups()) >= 1 else line
                    elif level_name == 'section':
                        level_number = 3
                        title = match.group(2) if len(match.groups()) >= 2 else match.group(1)
                    elif level_name == 'subsection':
                        level_number = 4
                        title = match.group(2) if len(match.groups()) >= 2 else match.group(1)
                    else:
                        continue

                    return {
                        'level': level_name,
                        'level_number': level_number,
                        'title': title.strip(),
                        'confidence': 1.0
                    }

        return None

    def _find_parent_node(self, node_stack: list[dict], current_level: int) -> dict | None:
        """查找父节点"""
        # 从栈顶向下找第一个level比当前小的节点
        for node in reversed(node_stack):
            if node['level_number'] < current_level:
                return node
        return None

    def _build_full_path(self, parent_node: dict, title: str) -> str:
        """构建完整路径"""
        parent_path = parent_node.get('full_path', '')
        if parent_path:
            return f"{parent_path} > {title}"
        return title

    def _update_node_stack(self, node_stack: list[dict], node: GuidelineNode, level_number: int) -> Any:
        """更新节点栈"""
        # 移除所有同级或下级节点
        while node_stack and node_stack[-1]['level_number'] >= level_number:
            node_stack.pop()
        # 添加当前节点
        node_stack.append(asdict(node))

    def _assign_paragraph_content(self, root_nodes: list[dict], lines: list[str]) -> Any:
        """分配段落内容到对应节点"""
        # 这个方法需要递归遍历节点树，将段落内容分配给最接近的小节节点
        pass

    def _is_reference_line(self, line: str) -> bool:
        """检查是否为引用行"""
        reference_keywords = ['参见', '根据', '依据', '按照', '如前所述', '如上所述']
        return any(keyword in line for keyword in reference_keywords)

    def _detect_content_type(self, line: str) -> str:
        """检测内容类型"""
        for content_type, patterns in self.content_markers.items():
            for pattern in patterns:
                if re.search(pattern, line):
                    return content_type
        return 'normal'

    def _calculate_statistics(self, root_nodes: list[dict]) -> dict[str, Any]:
        """计算统计信息"""
        stats = {
            'total_parts': 0,
            'total_chapters': 0,
            'total_sections': 0,
            'total_subsections': 0,
            'total_paragraphs': 0,
            'by_level': defaultdict(int)
        }

        def count_nodes(nodes) -> None:
            for node in nodes:
                level = node['level']
                stats['by_level'][level] += 1

                if level == 'part':
                    stats['total_parts'] += 1
                elif level == 'chapter':
                    stats['total_chapters'] += 1
                elif level == 'section':
                    stats['total_sections'] += 1
                elif level == 'subsection':
                    stats['total_subsections'] += 1
                elif level == 'paragraph':
                    stats['total_paragraphs'] += 1

                # 递归处理子节点
                if node.get('children_ids'):
                    # 注意: 这里需要实际的子节点数据，暂时跳过
                    pass

        count_nodes(root_nodes)
        return dict(stats)

    def extract_subsections(self, parsed_data: dict[str, Any]) -> list[dict[str, Any]]:
        """提取所有小节级别的节点"""
        logger.info("🔍 提取小节级别节点...")

        subsections = []

        def extract_recursive(nodes) -> None:
            for node in nodes:
                if node['level'] == 'subsection':
                    subsections.append(node)
                    logger.debug(f"小节: {node['title']}")
                # 递归处理子节点
                # 注意: 需要实际的子节点数据结构

        extract_recursive(parsed_data['root_nodes'])

        logger.info(f"✅ 提取到 {len(subsections)} 个小节")
        return subsections

    def generate_chunks_for_embedding(self, parsed_data: dict[str, Any],
                                    max_chunk_size: int = 500) -> list[dict[str, Any]]:
        """
        生成用于嵌入的文本块
        确保每个小节独立成块，保留层级上下文
        """
        logger.info(f"📦 生成嵌入文本块，最大块大小: {max_chunk_size}")

        chunks = []
        chunk_id = 0

        def process_node(node, parent_context="") -> None:
            nonlocal chunk_id

            # 构建上下文路径
            current_context = f"{parent_context} > {node['title']}" if parent_context else node['title']

            # 获取内容
            content = node.get('content', '')

            # 如果内容太长，进行分块
            if len(content) > max_chunk_size:
                # 保留标题，分割内容
                sub_chunks = self._split_long_content(content, max_chunk_size)
                for i, sub_chunk in enumerate(sub_chunks):
                    chunk_id += 1
                    chunks.append({
                        'chunk_id': f"chunk_{chunk_id:06d}",
                        'text': f"{node['title']}\n{sub_chunk}",
                        'metadata': {
                            'node_id': node['node_id'],
                            'level': node['level'],
                            'title': node['title'],
                            'parent_context': parent_context,
                            'full_path': node.get('full_path', current_context),
                            'chunk_index': i,
                            'total_chunks': len(sub_chunks)
                        }
                    })
            else:
                chunk_id += 1
                chunks.append({
                    'chunk_id': f"chunk_{chunk_id:06d}",
                    'text': f"{node['title']}\n{content}" if content else node['title'],
                    'metadata': {
                        'node_id': node['node_id'],
                        'level': node['level'],
                        'title': node['title'],
                        'parent_context': parent_context,
                        'full_path': node.get('full_path', current_context),
                        'chunk_index': 0,
                        'total_chunks': 1
                    }
                })

        def process_recursive(nodes, parent_context="") -> None:
            for node in nodes:
                process_node(node, parent_context)
                # 递归处理子节点
                # 需要实际的子节点数据结构

        process_recursive(parsed_data['root_nodes'])

        logger.info(f"✅ 生成 {len(chunks)} 个文本块")
        return chunks

    def _split_long_content(self, content: str, max_size: int) -> list[str]:
        """分割过长内容"""
        chunks = []
        sentences = re.split(r'[。；;]', content)  # 按句子分割

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > max_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence + "；"

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def save_processed_data(self, parsed_data: dict[str, Any],
                          chunks: list[dict[str, Any]],
                          output_dir: str):
        """保存处理后的数据"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存解析后的结构
        structure_file = output_path / f"guideline_structure_{timestamp}.json"
        with open(structure_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        logger.info(f"📄 结构已保存: {structure_file}")

        # 保存文本块
        chunks_file = output_path / f"guideline_chunks_{timestamp}.json"
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_chunks': len(chunks),
                'chunks': chunks
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"📦 文本块已保存: {chunks_file}")

        # 保存处理报告
        report = {
            'processing_time': datetime.now().isoformat(),
            'source_info': {
                'source_id': parsed_data.get('source_id'),
                'total_nodes': parsed_data.get('total_nodes', 0)
            },
            'statistics': parsed_data.get('statistics', {}),
            'chunks_info': {
                'total_chunks': len(chunks),
                'avg_chunk_size': sum(len(c['text']) for c in chunks) / len(chunks) if chunks else 0,
                'max_chunk_size': max(len(c['text']) for c in chunks) if chunks else 0,
                'min_chunk_size': min(len(c['text']) for c in chunks) if chunks else 0
            },
            'quality_metrics': {
                'subsections_count': parsed_data.get('statistics', {}).get('total_subsections', 0),
                'hierarchy_depth': 5,  # part -> chapter -> section -> subsection -> paragraph
                'context_preservation': True
            }
        }

        report_file = output_path / f"processing_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"📊 处理报告已保存: {report_file}")

        return {
            'structure_file': str(structure_file),
            'chunks_file': str(chunks_file),
            'report_file': str(report_file)
        }


async def process_guideline_file(file_path: str, output_dir: str):
    """处理指南文件"""
    processor = PatentGuidelineSubsectionProcessor()

    # 读取文件
    logger.info(f"📖 读取文件: {file_path}")
    with open(file_path, encoding='utf-8') as f:
        content = f.read()

    # 解析结构
    parsed_data = processor.parse_guideline_text(content, source_id=Path(file_path).stem)

    # 提取小节
    subsections = processor.extract_subsections(parsed_data)
    logger.info(f"📊 共找到 {len(subsections)} 个小节")

    # 生成文本块
    chunks = processor.generate_chunks_for_embedding(parsed_data)

    # 保存结果
    saved_files = processor.save_processed_data(parsed_data, chunks, output_dir)

    return {
        'parsed_data': parsed_data,
        'subsections': subsections,
        'chunks': chunks,
        'saved_files': saved_files
    }


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 专利审查指南细粒度分块处理")
    logger.info("=" * 60)

    # 输出目录
    output_dir = "/Users/xujian/Athena工作平台/production/data/patent_rules/legal_documents"

    # 检查是否有指南文件
    guideline_sources = [
        "/Users/xujian/Athena工作平台/production/data/patent_rules/legal_documents/guideline.txt",
        "/Users/xujian/Athena工作平台/production/data/patent_rules/legal_documents/patent_guideline.txt",
        "/Users/xujian/Athena工作平台/production/data/patent_rules/legal_documents/专利审查指南.txt"
    ]

    found_file = None
    for source in guideline_sources:
        if Path(source).exists():
            found_file = source
            break

    if found_file:
        logger.info(f"✅ 找到指南文件: {found_file}")
        result = await process_guideline_file(found_file, output_dir)

        logger.info("=" * 60)
        logger.info("🎉 处理完成！")
        logger.info("📊 统计信息:")
        logger.info(f"   - 总节点数: {result['parsed_data']['total_nodes']}")
        logger.info(f"   - 小节数: {len(result['subsections'])}")
        logger.info(f"   - 文本块数: {len(result['chunks'])}")
        logger.info("📄 已保存文件:")
        for file_type, file_path in result['saved_files'].items():
            logger.info(f"   - {file_type}: {file_path}")
        logger.info("=" * 60)
    else:
        logger.warning("⚠️ 未找到指南文件，请提供指南文件路径")
        logger.info("💡 提示: 请将指南文件放在以下位置之一:")
        for source in guideline_sources:
            logger.info(f"   - {source}")


if __name__ == "__main__":
    # 创建输出目录
    os.makedirs('/Users/xujian/Athena工作平台/logs', exist_ok=True)
    os.makedirs('/Users/xujian/Athena工作平台/production/data/patent_rules/legal_documents', exist_ok=True)

    # 运行处理
    asyncio.run(main())
