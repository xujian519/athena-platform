#!/usr/bin/env python3
"""快速测试专利规则解析器"""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from production.scripts.patent_rules_system.patent_rules_processor import (
    DocumentType,
    PatentDocumentParser,
    Priority,
)

# 测试解析专利法
parser = PatentDocumentParser()
patent_law = Path("/Users/xujian/Athena工作平台/data/专利/中华人民共和国专利法_20201017.md")

if patent_law.exists():
    print(f"测试解析: {patent_law.name}")
    print(f"文件大小: {patent_law.stat().st_size / 1024:.1f} KB")

    result = parser.parse_document(patent_law, DocumentType.PATENT_LAW, Priority.P0)

    print("\n✅ 解析完成!")
    print(f"提取规则数: {len(result.rules)}")
    print(f"处理时间: {result.processing_time:.2f}秒")

    if result.rules:
        print("\n前5条规则:")
        for i, rule in enumerate(result.rules[:5], 1):
            print(f"\n{i}. {rule.hierarchy_path}")
            print(f"   内容: {rule.content[:80]}...")
else:
    print(f"文件不存在: {patent_law}")
