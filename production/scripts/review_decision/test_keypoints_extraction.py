#!/usr/bin/env python3
"""
测试增强的决定要点提取逻辑
验证分块逻辑是否正确识别决定要点
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


from docx import Document


def test_keypoints_patterns() -> Any:
    """测试决定要点识别模式"""

    # 测试文本样本
    test_samples = [
        # 样本1: 标准格式
        """
        决定要点：
        1. 本专利权利要求1不具备创造性
        2. 说明书公开不充分

        案由：
        涉及一种机械装置...
        """,

        # 样本2: 变体格式
        """
        【要点】
        一、专利法第22条的新颖性
        二、创造性的判断标准

        理由：
        根据专利法...
        """,

        # 样本3: 编号格式
        """
        一、本决定要点如下：
        1. 权利要求1-3无效
        2. 权利要求4有效

        二、理由说明
        根据对比文件...
        """,

        # 样本4: 混合格式
        """
        本决定要点：
        关于权利要求的新颖性，现有技术...

        决定如下：
        1. 宣告专利权部分无效...
        """
    ]

    # 导入修复后的管道类
    from production.scripts.review_decision.docx_only_pipeline import DocxOnlyPipeline

    pipeline = DocxOnlyPipeline()

    print('='*70)
    print('🧪 测试决定要点提取逻辑')
    print('='*70)
    print()

    for i, sample_text in enumerate(test_samples, 1):
        print(f'📝 测试样本 {i}:')
        print('-'*70)

        # 模拟元数据
        mock_metadata = {
            'doc_id': f'test_doc_{i}',
            'filename': f'test_{i}.docx',
            'decision_number': f'W{i}0001',
            'decision_date': '2024-01-01'
        }

        # 测试分块
        chunks = pipeline.chunk_decision_text(sample_text.strip(), mock_metadata)

        print(f'  总块数: {len(chunks)}')

        for j, chunk in enumerate(chunks, 1):
            block_type = chunk.get('block_type', 'unknown')
            section = chunk.get('section', 'unknown')
            text_preview = chunk.get('text', '')[:100].replace('\n', ' ')

            law_refs = chunk.get('metadata', {}).get('law_references', [])
            related_laws = chunk.get('metadata', {}).get('related_laws', [])

            print(f'  块{j}: [{block_type}] {section}')
            print(f'    文本: {text_preview}...')
            if law_refs:
                print(f'    法律引用: {law_refs}')
            if related_laws:
                print(f'    相关法律: {related_laws}')
            print()

        # 统计决定要点
        keypoints_count = sum(1 for c in chunks if c.get('block_type') == 'keypoints')
        keypoints_with_law = sum(1 for c in chunks
                                  if c.get('block_type') == 'keypoints'
                                  and c.get('metadata', {}).get('law_references'))

        print(f'  ✅ 决定要点块: {keypoints_count}')
        print(f'  ✅ 有法律引用的决定要点: {keypoints_with_law}')
        print()
        print('='*70)
        print()


def test_real_docx_files() -> Any:
    """测试真实的复审决定书文件"""

    from production.scripts.review_decision.docx_only_pipeline import DocxOnlyPipeline

    pipeline = DocxOnlyPipeline()

    review_dir = Path("/Volumes/AthenaData/语料/专利/专利复审决定原文")

    # 获取前5个DOCX文件
    docx_files = list(review_dir.glob("*.docx"))[:5]

    if not docx_files:
        print("⚠️ 未找到DOCX文件")
        return

    print('='*70)
    print('📂 测试真实复审决定书文件')
    print('='*70)
    print()

    for file_path in docx_files:
        print(f'📄 文件: {file_path.name}')
        print('-'*70)

        # 提取文本
        try:
            doc = Document(str(file_path))
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            full_text = "\n".join(paragraphs)

            metadata = {
                'doc_id': file_path.stem,
                'filename': file_path.name,
                'file_size': file_path.stat().st_size,
                'paragraph_count': len(paragraphs)
            }

            # 测试分块
            chunks = pipeline.chunk_decision_text(full_text, metadata)

            print(f'  段落数: {len(paragraphs)}')
            print(f'  生成块数: {len(chunks)}')
            print()

            # 统计块类型
            block_types = {}
            for chunk in chunks:
                bt = chunk.get('block_type', 'unknown')
                block_types[bt] = block_types.get(bt, 0) + 1

            print('  块类型分布:')
            for bt, count in sorted(block_types.items()):
                print(f'    {bt}: {count}')

            # 检查决定要点
            keypoints_chunks = [c for c in chunks if c.get('block_type') == 'keypoints']
            if keypoints_chunks:
                print()
                print('  📌 决定要点示例:')
                for kp in keypoints_chunks[:2]:
                    text = kp.get('text', '')[:200].replace('\n', ' ')
                    law_refs = kp.get('metadata', {}).get('law_references', [])
                    print(f'    {text}...')
                    if law_refs:
                        print(f'    法律引用: {law_refs[:3]}')
            else:
                print()
                print('  ⚠️ 未识别到决定要点')

        except Exception as e:
            print(f'  ❌ 处理失败: {e}')

        print()
        print('='*70)
        print()


def save_test_results() -> None:
    """保存测试结果到文件"""
    timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'/Users/xujian/Athena工作平台/production/data/patent_decisions/test_keypoints_{timestamp}.json'

    # TODO: 实现测试结果保存逻辑
    pass


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 开始测试决定要点提取逻辑")
    print("="*70 + "\n")

    # 测试1: 模拟文本样本
    test_keypoints_patterns()

    # 测试2: 真实文件
    test_real_docx_files()

    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70 + "\n")
