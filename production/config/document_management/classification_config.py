#!/usr/bin/env python3
"""
文档自动分类配置

Author: 小诺·双鱼公主 💖
Version: 1.0.0
Created: 2026-01-07
"""

from __future__ import annotations
from pathlib import Path
from typing import Any

# 文档根目录配置
DOCS_ROOT = Path("/Users/xujian/Athena工作平台/docs")

# 分类目录配置
CLASSIFICATION_DIRS = {
    "architecture": "01-architecture",
    "implementation": "02-implementation",
    "reports": "03-reports",
    "guides": "04-guides",
    "optimization": "05-optimization",
    "reference": "06-reference",
    "projects": "07-projects",
    "business": "08-business",
    "archive": "99-archive",
}

# 自定义分类规则配置
CUSTOM_RULES = {
    # 特定项目报告的规则
    "yunpat_reports": {
        "patterns": [r".*yunpat.*", r".*云pat.*"],
        "category": "07-projects/patents",
        "priority": 9
    },

    # MCP相关报告
    "mcp_reports": {
        "patterns": [r".*mcp.*", r".*MCP.*"],
        "category": "03-reports/{year}-{month:02d}",
        "priority": 10
    },

    # 知识库相关
    "knowledge_base": {
        "patterns": [r".*知识库.*", r".*knowledge.*base.*"],
        "category": "07-projects/knowledge-graph",
        "priority": 9
    },

    # 意图识别相关
    "intent_recognition": {
        "patterns": [r".*intent.*", r".*意图.*"],
        "category": "07-projects/nlp",
        "priority": 9
    },

    # 工具治理相关
    "tool_governance": {
        "patterns": [r".*tool.*governance.*"],
        "category": "07-projects/tool-governance",
        "priority": 9
    },

    # 生产环境相关
    "production": {
        "patterns": [r".*production.*", r".*生产.*"],
        "category": "07-projects/production",
        "priority": 8
    },
}

# 报告类型映射
REPORT_TYPE_MAPPING = {
    "investigation": "03-reports/{year}-{month:02d}",
    "optimization": "05-optimization/phases",
    "integration": "02-implementation",
    "deployment": "02-implementation/deployment",
    "cleanup": "03-reports/{year}-{month:02d}",
    "analysis": "03-reports/{year}-{month:02d}",
    "completion": "03-reports/{year}-{month:02d}",
    "comparison": "03-reports/{year}-{month:02d}",
    "architecture": "01-architecture",
    "guide": "04-guides/user-guides",
    "reference": "06-reference/technical",
    "project": "07-projects",
}

# 文件名生成规则
FILENAME_PATTERNS = {
    "report": "{title}_{date}.md",
    "guide": "{title}_guide.md",
    "reference": "{title}_reference.md",
    "architecture": "{title}_architecture.md",
}

# 保留在根目录的文件
KEEP_IN_ROOT = [
    "README.md",
    "CLAUDE.md",
    "DOCS_CLEANUP_*.md",
]

# 自动分类开关
AUTO_CLASSIFICATION_ENABLED = True

# 分类后是否移动文件
MOVE_FILES_AFTER_CLASSIFICATION = True

# 是否记录分类历史
LOG_CLASSIFICATION_HISTORY = True

# 分类历史记录文件
CLASSIFICATION_LOG_FILE = DOCS_ROOT / ".classification_history.json"


# 使用示例
def get_custom_rules_config() -> Any | None:
    """获取自定义规则配置"""
    return CUSTOM_RULES


def get_report_type_mapping() -> Any | None:
    """获取报告类型映射"""
    return REPORT_TYPE_MAPPING


def get_docs_root() -> Any | None:
    """获取文档根目录"""
    return DOCS_ROOT


def is_auto_classification_enabled() -> bool:
    """检查是否启用自动分类"""
    return AUTO_CLASSIFICATION_ENABLED


def should_move_files() -> Any:
    """检查是否应该移动文件"""
    return MOVE_FILES_AFTER_CLASSIFICATION


def should_log_history() -> Any:
    """检查是否应该记录历史"""
    return LOG_CLASSIFICATION_HISTORY


# 使用示例
if __name__ == "__main__":
    print("文档自动分类配置")
    print("=" * 50)
    print(f"文档根目录: {DOCS_ROOT}")
    print(f"自动分类启用: {AUTO_CLASSIFICATION_ENABLED}")
    print(f"移动文件: {MOVE_FILES_AFTER_CLASSIFICATION}")
    print(f"记录历史: {LOG_CLASSIFICATION_HISTORY}")
    print("\n自定义规则:")
    for name, rule in CUSTOM_RULES.items():
        print(f"  {name}: {rule}")
    print("\n报告类型映射:")
    for report_type, category in REPORT_TYPE_MAPPING.items():
        print(f"  {report_type}: {category}")
