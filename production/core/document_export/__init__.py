#!/usr/bin/env python3
from __future__ import annotations
"""
文档导出模块 - Athena平台深度集成版
Document Export Module - Athena Platform Integration

基于PasteMD项目核心功能的深度集成,为Athena平台提供:
1. Markdown转Word/WPS文档
2. AI对话内容导出
3. 表格数据导出到Excel
4. 公式、代码高亮完美保留

模块组成:
- pastemd_core.py: PasteMD核心功能封装
- word_automation.py: Word/WPS自动化接口
- excel_exporter.py: Excel表格解析和导出
- xiaonuo_export_api.py: NLP服务API端点

使用方法:
```python

# 导出专利报告
exporter = get_document_exporter()
doc_path = exporter.export_patent_report(patent_data, analysis)
```

集成时间: 2025-12-24
版本: v1.0.0 "深度集成"
"""

from .word_automation import (
    AutomatedWordExporter,
    ClipboardManager,
    WordAutomation,
    WordDocumentInserter,
    get_word_automation,
)

__all__ = [
    "AthenaDocumentExporter",
    "AutomatedWordExporter",
    "ClipboardManager",
    "ExcelExporter",
    "PasteMDCore",
    "WordAutomation",
    "WordDocumentInserter",
    "get_document_exporter",
    "get_excel_exporter",
    "get_word_automation",
]

__version__ = "1.0.0"
__author__ = "小诺·双鱼公主"
