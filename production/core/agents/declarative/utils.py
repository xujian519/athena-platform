"""
Frontmatter 解析工具

提供 YAML frontmatter 的统一解析功能，供 loader.py 和 output_styles.py 复用。

Author: Athena Team
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("utils.frontmatter")


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    解析 Markdown 文件中的 YAML frontmatter

    支持格式：
        ---
        key: value
        ---

        正文内容

    Args:
        content: 文件完整内容

    Returns:
        (metadata_dict, body_content) 元组。
        如果没有 frontmatter，metadata 为空字典，body 为原始内容。
    """
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    yaml_str = parts[1].strip()
    body = parts[2].strip()

    if not yaml_str:
        return {}, body

    try:
        import yaml
        metadata = yaml.safe_load(yaml_str)
        if not isinstance(metadata, dict):
            metadata = {}
    except ImportError:
        logger.warning("PyYAML 未安装，无法解析 frontmatter")
        metadata = {}
    except Exception as e:
        logger.warning(f"解析 frontmatter 失败: {e}")
        metadata = {}

    return metadata, body
