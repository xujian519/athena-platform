#!/usr/bin/env python3
"""
智能决定要点提取器
从复审决定书和无效宣告决定书中智能提取决定要点
"""

from __future__ import annotations
import re
from typing import Any


class SmartKeypointsExtractor:
    """智能决定要点提取器"""

    def __init__(self):
        # 决定要点的各种识别模式
        self.keypoint_patterns = {
            # 明确的决定要点标记
            'explicit': [
                re.compile(r'决定要点[：:：]\s*'),
                re.compile(r'本决定要点[：:：]\s*'),
                re.compile(r'要点[：:：]\s*'),
                re.compile(r'【要点】\s*'),
                re.compile(r'【决定要点】\s*'),
            ],
            # 结论性段落标记
            'conclusion': [
                re.compile(r'综上[，,]?[^\n]{0,50}'),
                re.compile(r'基于上述[，,]?[^\n]{0,50}'),
                re.compile(r'综上所述[，,]?[^\n]{0,50}'),
                re.compile(r'因此[，,]?[^\n]{0,30}'),
            ],
            # 编号列表（可能的决定要点）
            'numbered': [
                re.compile(r'^[一二三四五六七八九十]+[、.．]\s*.{10,}'),
                re.compile(r'^\d+[、.．]\s*.{10,}'),
                re.compile(r'^\([一二三四五六七八九十]+\)[、.．]?\s*.{10,}'),
            ],
        }

    def extract_keypoints_from_text(self, text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """
        从文本中智能提取决定要点

        Args:
            text: 文档全文
            metadata: 元数据

        Returns:
            提取的决定要点列表
        """
        lines = text.split('\n')

        # 策略1: 尝试识别明确的决定要点章节
        explicit_keypoints = self._extract_explicit_keypoints(lines, metadata)
        if explicit_keypoints:
            return explicit_keypoints

        # 策略2: 提取决定的理由中的结论段落
        conclusion_keypoints = self._extract_conclusion_keypoints(text, lines, metadata)
        if conclusion_keypoints:
            return conclusion_keypoints

        # 策略3: 从决定的末尾提取
        ending_keypoints = self._extract_ending_keypoints(text, lines, metadata)
        if ending_keypoints:
            return ending_keypoints

        return []

    def _extract_explicit_keypoints(self, lines: list[str], metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """提取明确标记的决定要点"""
        for pattern in self.keypoint_patterns['explicit']:
            for i, line in enumerate(lines):
                if pattern.search(line):
                    # 找到决定要点开始，提取内容
                    return self._extract_section_content(lines, i, 'keypoints', metadata)
        return []

    def _extract_conclusion_keypoints(self, text: str, lines: list[str], metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """提取决定的理由中的结论段落作为决定要点"""
        keypoints = []

        # 查找"决定的理由"或"理由"部分
        reasoning_start = -1
        for i, line in enumerate(lines):
            if re.search(r'决定的理由[：:：]\s*|理由[：:：]\s*|二、[^\n]{0,10}理由', line):
                reasoning_start = i
                break

        if reasoning_start == -1:
            return []

        # 从理由部分开始向后查找结论性段落
        for i in range(reasoning_start + 1, len(lines)):
            line = lines[i].strip()
            if not line:
                continue

            # 检查是否是结论性段落
            for pattern in self.keypoint_patterns['conclusion']:
                if pattern.search(line):
                    # 提取这一段和接下来的几行
                    keypoint_content = [line]
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if not next_line:
                            continue
                        # 遇到新的章节标记就停止
                        if re.search(r'^[一二三四五六七八九十]+[、.．]\s*(案由|理由|决定)', next_line):
                            break
                        keypoint_content.append(next_line)

                    if keypoint_content:
                        keypoints.append(self._create_keypoint_chunk(
                            '\n'.join(keypoint_content),
                            'conclusion',
                            metadata
                        ))
                    return keypoints

        return []

    def _extract_ending_keypoints(self, text: str, lines: list[str], metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """提取文档末尾的决定性段落"""
        keypoints = []

        # 查找末尾的"综上所述"等段落
        for i in range(len(lines) - 1, max(0, len(lines) - 20), -1):
            line = lines[i].strip()
            if not line:
                continue

            # 检查是否是总结段落
            for pattern in self.keypoint_patterns['conclusion']:
                if pattern.search(line) and len(line) > 20:
                    # 提取这一段和后面的内容
                    keypoint_content = []
                    for j in range(i, min(i + 3, len(lines))):
                        if lines[j].strip():
                            keypoint_content.append(lines[j].strip())

                    if keypoint_content:
                        keypoints.append(self._create_keypoint_chunk(
                            '\n'.join(keypoint_content),
                            'ending',
                            metadata
                        ))
                    return keypoints

        return []

    def _extract_section_content(self, lines: list[str], start_idx: int,
                                section_type: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """提取章节内容"""
        content = []

        for i in range(start_idx + 1, len(lines)):
            line = lines[i].strip()
            if not line:
                continue

            # 遇到新的主要章节就停止
            if re.search(r'^[一二三四五六七八九十]+[、.．]\s*(案由|理由|决定|要点)', line):
                break

            content.append(line)

            # 限制长度
            if len(content) > 20:
                break

        if content:
            return [self._create_keypoint_chunk('\n'.join(content), section_type, metadata)]
        return []

    def _create_keypoint_chunk(self, text: str, source_type: str,
                              metadata: dict[str, Any]) -> dict[str, Any]:
        """创建决定要点块"""

        # 使用安全哈希函数替代不安全的MD5/SHA1
        from production.utils.security_helpers import short_hash

        doc_id = metadata.get('doc_id', 'unknown')
        chunk_hash = short_hash(f"{doc_id}_keypoints_{len(text)}".encode())[:8]
        chunk_id = f"dec_{doc_id}_kp_{chunk_hash}"

        # 提取法律引用
        law_refs = self._extract_law_references(text)

        return {
            'chunk_id': chunk_id,
            'doc_id': doc_id,
            'block_type': 'keypoints',
            'section': '决定要点',
            'text': text,
            'metadata': {
                'filename': metadata.get('filename', ''),
                'decision_date': metadata.get('decision_date', ''),
                'decision_number': metadata.get('decision_number', ''),
                'char_count': len(text),
                'law_references': law_refs,
                'related_laws': [ref for ref in law_refs
                                if '专利法' in ref or '实施细则' in ref],
                'keypoint_source': source_type  # 标记来源
            }
        }

    def _extract_law_references(self, text: str) -> list[str]:
        """提取法律引用"""
        law_refs = []

        # 匹配专利法条款
        pattern = re.compile(r'(专利法|实施细则)[\s\u3000]*第?([\d一二三四五六七八九十]+)[条条款款]')
        matches = pattern.findall(text)
        for law, art in matches:
            law_refs.append(f"{law} {art}")

        return law_refs


def enhance_pipeline_with_smart_keypoints(pipeline):
    """增强管道，添加智能决定要点提取"""

    # 保存原始的分块方法
    original_chunk_method = pipeline.chunk_decision_text

    def enhanced_chunk_decision_text(text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """增强的分块方法"""
        # 首先使用原始方法分块
        chunks = original_chunk_method(text, metadata)

        # 检查是否有决定要点
        has_keypoints = any(c.get('block_type') == 'keypoints' for c in chunks)

        if not has_keypoints:
            # 没有决定要点，使用智能提取
            extractor = SmartKeypointsExtractor()
            keypoints = extractor.extract_keypoints_from_text(text, metadata)

            if keypoints:
                chunks.extend(keypoints)

        return chunks

    # 替换方法
    pipeline.chunk_decision_text = enhanced_chunk_decision_text

    return pipeline


# 测试代码
if __name__ == "__main__":
    from pathlib import Path

    from docx import Document

    # 测试文件
    file_path = Path("/Volumes/AthenaData/语料/专利/专利复审决定原文/2010101258192.docx")

    if file_path.exists():
        doc = Document(str(file_path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)

        metadata = {
            'doc_id': file_path.stem,
            'filename': file_path.name,
            'decision_number': 'W566036',
            'decision_date': '2024-01-01'
        }

        extractor = SmartKeypointsExtractor()
        keypoints = extractor.extract_keypoints_from_text(text, metadata)

        print('='*70)
        print('📌 提取的决定要点')
        print('='*70)
        print()

        for i, kp in enumerate(keypoints, 1):
            print(f'决定要点 {i}:')
            print(f'  来源: {kp["metadata"].get("keypoint_source", "unknown")}')
            print(f'  内容: {kp["text"][:300]}...')

            law_refs = kp['metadata'].get('law_references', [])
            if law_refs:
                print(f'  法律引用: {law_refs}')
            print()
    else:
        print(f'文件不存在: {file_path}')
