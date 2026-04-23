#!/usr/bin/env python3
"""
扫描并生成 Prompt Inventory。

用法:
    python scripts/generate_prompt_inventory.py

输出:
    PROMPT_INVENTORY.md（项目根目录）
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
OUTPUT_FILE = PROJECT_ROOT / "PROMPT_INVENTORY.md"


@dataclass
class InventoryItem:
    id: str
    path: str
    type: str
    status: str
    variables: List[str] = field(default_factory=list)


def infer_status(md_file: Path) -> str:
    name = md_file.name.lower()
    if "deprecated" in name or "_old_" in name:
        return "deprecated"
    if "draft" in name or "wip" in name or "_v0" in name:
        return "draft"
    if "_v1." in name or "_v2." in name:
        return "production"
    return "staging"


def extract_variables(text: str) -> List[str]:
    # 匹配 {var} 和 {{ var }}
    found = set()
    for pat in (r"\{\{?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}?\}", r"\[([^\]\n]+?)\]"):
        found.update(re.findall(pat, text))
    # 过滤掉非变量占位符
    filtered = [f for f in found if not f.startswith("http") and len(f) < 50]
    return sorted(set(filtered))


def scan_markdown_prompts() -> List[InventoryItem]:
    items: List[InventoryItem] = []
    for md_file in sorted(PROMPTS_DIR.rglob("*.md")):
        relative = md_file.relative_to(PROMPTS_DIR)
        content = md_file.read_text(encoding="utf-8")
        items.append(InventoryItem(
            id=str(relative.with_suffix("")),
            path=str(md_file.relative_to(PROJECT_ROOT)),
            type="markdown_static",
            status=infer_status(md_file),
            variables=extract_variables(content),
        ))
    return items


def scan_scenario_rules() -> List[InventoryItem]:
    items: List[InventoryItem] = []
    rules_dir = PROJECT_ROOT / "domains/legal/core_modules/legal_world_model/scenario_rules"
    for py_file in sorted(rules_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        content = py_file.read_text(encoding="utf-8")
        # 提取 rule_id
        m = re.search(r'rule_id="([^"]+)"', content)
        rule_id = m.group(1) if m else py_file.stem
        # 提取变量（从 user_prompt_template 中）
        vars_found = extract_variables(content)
        items.append(InventoryItem(
            id=rule_id,
            path=str(py_file.relative_to(PROJECT_ROOT)),
            type="scenario_rule",
            status="production",
            variables=vars_found,
        ))
    return items


def main() -> None:
    md_items = scan_markdown_prompts()
    rule_items = scan_scenario_rules()
    all_items = md_items + rule_items

    lines = [
        "# Prompt Inventory",
        "",
        f"> Generated at: {datetime.now().isoformat()}",
        f"> Total templates: {len(all_items)}",
        "",
        "| ID | Path | Type | Status | Variables |",
        "|---|---|---|---|---|",
    ]

    for item in all_items:
        vars_str = ", ".join(item.variables[:5])
        if len(item.variables) > 5:
            vars_str += f" (+{len(item.variables) - 5} more)"
        if not vars_str:
            vars_str = "-"
        lines.append(
            f"| {item.id} | `{item.path}` | {item.type} | {item.status} | {vars_str} |"
        )

    lines.append("")
    lines.append("## Status Legend")
    lines.append("")
    lines.append("- **production**: 已在生产环境使用")
    lines.append("- **staging**: 测试中，尚未全量上线")
    lines.append("- **draft**: 草稿，未完成")
    lines.append("- **deprecated**: 已废弃，准备移除")
    lines.append("")
    lines.append("## Update Instructions")
    lines.append("")
    lines.append("运行以下命令更新本清单:")
    lines.append("```bash")
    lines.append("python scripts/generate_prompt_inventory.py")
    lines.append("```")
    lines.append("")
    lines.append("CI 检查: 修改提示词文件的 PR 必须同步更新本清单。")
    lines.append("")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"PROMPT_INVENTORY.md generated: {len(all_items)} items")


if __name__ == "__main__":
    main()
