#!/usr/bin/env python3
"""
存量模板 Jinja2 化升级脚本

功能：
- 扫描 prompts/ 和 scenario_rules/ 下的模板文件
- 将 legacy {var} 语法升级为 Jinja2 {{ var }} 语法
- 支持 --dry-run 预览改动
- 支持 --backup 备份原文件
- 智能跳过 Python f-string 和 JSON 对象语法
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Sequence

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# legacy 变量占位符正则（snake_case）
LEGACY_VAR_RE = (
    # 匹配 {var_name}，但排除 Jinja2 已有的 {{ 和 }}
    r"(?<!\{)\{([a-z_][a-z0-9_]*)\}(?!\})"
)

# 简单 f-string 检测（行级）
FSTRING_RE = r'f["\'][^"\']*\{[a-z_][a-z0-9_]*\}[^"\']*["\']'

# 需要处理的目录和扩展名
TARGET_PATHS = [
    PROJECT_ROOT / "prompts",
    PROJECT_ROOT / "domains" / "legal" / "core_modules" / "legal_world_model" / "scenario_rules",
]
TARGET_EXTENSIONS = {".md", ".py"}

# prompts/ 下的 .py 文件为纯 Python 代码（含 f-string），应跳过
SKIP_PY_PATHS = [PROJECT_ROOT / "prompts"]


def _is_fstring_line(line: str) -> bool:
    """粗略判断整行是否包含 Python f-string 语法。"""
    import re
    return bool(re.search(FSTRING_RE, line))


def _is_json_object_syntax(line: str, var_name: str) -> bool:
    """判断是否为 JSON 对象语法如 `{"key": "value"}` 中的大括号。"""
    import re
    # 匹配 `"key": {var}` 这种 JSON value 场景（不包括纯模板变量）
    pattern = rf'"[^"]*"\s*:\s*\{{{var_name}\}}'
    return bool(re.search(pattern, line))


def _is_inside_json_codeblock(lines: Sequence[str], idx: int) -> bool:
    """判断当前行是否位于 ```json 代码块内部。"""
    in_json_block = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```json") or stripped.startswith("``` json"):
            in_json_block = True
        elif stripped == "```" and in_json_block:
            in_json_block = False
        if i == idx:
            return in_json_block
    return False


def _looks_optional(line: str, var_name: str) -> bool:
    """根据上下文判断变量是否为可选。

    只有当可选标记出现在该变量之前或紧邻该变量时才生效。
    """
    optional_markers = ["（可选）", "(可选)", "(optional)", "【可选】", "[optional]"]
    # 找到变量在行中的位置
    import re

    var_pos = line.find("{" + var_name + "}")
    if var_pos == -1:
        return False
    for marker in optional_markers:
        marker_pos = line.find(marker)
        if marker_pos != -1 and marker_pos < var_pos:
            return True
    return False


def _escape_literal_braces(line: str) -> str:
    """将独立的 {{ 和 }} 转义为 Jinja2 字符串字面量。

    仅在行首或整行只有 {{ / }} 时触发，避免破坏已正确的 Jinja2 表达式。
    """
    import re

    stripped = line.strip()
    # 行首或整行独立的 {{
    if stripped == "{{":
        return line.replace("{{", "{{ '{{' }}")
    # 行首或整行独立的 }}
    if stripped == "}}":
        return line.replace("}}", "{{ '}}' }}")
    return line


def convert_content(text: str) -> str:
    """全文转换逻辑。

    步骤：
    1. 检测是否仍包含 legacy {var}；若无，直接返回（保证幂等）
    2. 将已有的字面量 {{ / }} 替换为临时占位符，避免与 Jinja2 表达式冲突
    3. 将 legacy {var} 替换为 Jinja2 {{ var }}
    4. 将临时占位符恢复为 Jinja2 字符串字面量
    """
    import re

    # 幂等性检查：若已无 legacy 变量，不再处理字面量大括号
    if not re.search(LEGACY_VAR_RE, text):
        return text

    # 步骤 2: 保护已有的字面量 {{ / }}
    text = text.replace("{{", "__LBRACE__")
    text = text.replace("}}", "__RBRACE__")

    lines = text.splitlines(keepends=True)
    new_lines: list[str] = []

    for line in lines:
        # 跳过 Python f-string
        if _is_fstring_line(line):
            new_lines.append(line)
            continue

        def _replace(match: re.Match) -> str:
            var_name = match.group(1)

            # 跳过 JSON 对象语法（如 `"key": {value}`）
            if _is_json_object_syntax(line, var_name):
                return match.group(0)

            # 为可选变量添加 default 过滤器
            if _looks_optional(line, var_name):
                return f"{{{{ {var_name} | default('') }}}}"
            return f"{{{{ {var_name} }}}}"

        new_line = re.sub(LEGACY_VAR_RE, _replace, line)
        new_lines.append(new_line)

    text = "".join(new_lines)

    # 步骤 4: 恢复字面量大括号为 Jinja2 兼容格式
    text = text.replace("__LBRACE__", "{{ '{{' }}")
    text = text.replace("__RBRACE__", "{{ '}}' }}")

    return text


def process_file(filepath: Path, dry_run: bool = False, backup: bool = False) -> tuple[bool, int]:
    """
    处理单个文件。

    Returns:
        (是否改动, 替换次数)
    """
    original_text = filepath.read_text(encoding="utf-8")
    new_text = convert_content(original_text)

    if new_text == original_text:
        return False, 0

    # 统计实际 legacy 变量替换次数（通过对比占位符数量）
    import re
    original_count = len(re.findall(LEGACY_VAR_RE, original_text))
    new_count = len(re.findall(LEGACY_VAR_RE, new_text))
    replacements = original_count - new_count

    if dry_run:
        print(f"\n[DRY-RUN] {filepath.relative_to(PROJECT_ROOT)}")
        _print_diff(original_text, new_text)
        return True, replacements

    if backup:
        backup_path = filepath.with_suffix(filepath.suffix + ".bak")
        shutil.copy2(filepath, backup_path)
        print(f"[BACKUP]  {backup_path.relative_to(PROJECT_ROOT)}")

    filepath.write_text(new_text, encoding="utf-8")
    print(f"[UPDATED] {filepath.relative_to(PROJECT_ROOT)} ({replacements} replacements)")
    return True, replacements


def _print_diff(original: str, modified: str) -> None:
    """简单行级 diff 输出。"""
    orig_lines = original.splitlines()
    mod_lines = modified.splitlines()
    max_lines = max(len(orig_lines), len(mod_lines))
    for i in range(max_lines):
        o = orig_lines[i] if i < len(orig_lines) else ""
        m = mod_lines[i] if i < len(mod_lines) else ""
        if o != m:
            print(f"  - {o}")
            print(f"  + {m}")


def _should_skip_file(filepath: Path) -> bool:
    """判断文件是否应被跳过。"""
    # 跳过 prompts/ 下的 .py 文件（纯 Python 代码，含 f-string）
    if filepath.suffix == ".py":
        for skip_path in SKIP_PY_PATHS:
            try:
                filepath.relative_to(skip_path)
                return True
            except ValueError:
                pass
    return False


def collect_target_files() -> list[Path]:
    """收集所有待处理文件。"""
    files: list[Path] = []
    for target in TARGET_PATHS:
        if not target.exists():
            continue
        if target.is_file():
            if not _should_skip_file(target):
                files.append(target)
        else:
            for ext in TARGET_EXTENSIONS:
                for f in target.rglob(f"*{ext}"):
                    if not _should_skip_file(f):
                        files.append(f)
    # 去重并保持顺序
    seen: set[Path] = set()
    unique_files: list[Path] = []
    for f in files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)
    return sorted(unique_files)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将 legacy {var} 模板语法升级为 Jinja2 {{ var }} 语法"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览改动，不实际写入文件",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="升级前备份原文件（.bak）",
    )
    parser.add_argument(
        "--path",
        type=Path,
        action="append",
        help="额外指定待处理的文件或目录（可多次使用）",
    )
    args = parser.parse_args()

    files = collect_target_files()
    if args.path:
        for p in args.path:
            p = p.resolve()
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                for ext in TARGET_EXTENSIONS:
                    files.extend(p.rglob(f"*{ext}"))
        # 再次去重
        seen: set[Path] = set()
        unique: list[Path] = []
        for f in files:
            if f not in seen:
                seen.add(f)
                unique.append(f)
        files = sorted(unique)

    if not files:
        print("未找到待处理文件。")
        return 0

    print(f"扫描到 {len(files)} 个待处理文件…\n")

    modified_count = 0
    total_replacements = 0
    for filepath in files:
        changed, count = process_file(filepath, dry_run=args.dry_run, backup=args.backup)
        if changed:
            modified_count += 1
            total_replacements += count

    print(
        f"\n完成: {modified_count}/{len(files)} 个文件发生改动, "
        f"共 {total_replacements} 处替换。"
    )
    if args.dry_run:
        print("(dry-run 模式，未实际写入)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
