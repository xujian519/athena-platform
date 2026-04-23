#!/usr/bin/env python3
"""
从 PROMPT_INVENTORY.md 和实际模板文件生成 PromptSchema 定义。

用法:
    python scripts/generate_schemas.py
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

os.environ["DISABLE_TOOL_AUTO_REGISTER"] = "1"

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType


# ---------------------------------------------------------------------------
# 变量名清洗与类型推断
# ---------------------------------------------------------------------------

def sanitize_var_name(name: str) -> str:
    """将描述性变量名转换为合法的 Jinja2/Python 标识符。"""
    name = name.strip().strip('"').strip("'")
    name = re.sub(r'^[,\s]+', '', name)
    name = re.sub(r'^例如[:：]\s*', '', name)
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        return name
    name = re.sub(r'[\s/\\|.-]+', '_', name)
    name = re.sub(r'[^\w\u4e00-\u9fff]', '', name)
    if re.match(r'^[\u4e00-\u9fff]+$', name):
        return name
    if not name:
        return "param"
    if name[0].isdigit():
        name = "p_" + name
    return name


def infer_type(name: str, sample_value: Optional[str] = None) -> VariableType:
    """基于变量名和样本值推断 VariableType。"""
    name_lower = name.lower()

    # 已知字段强制类型
    if name_lower == "application_number":
        return VariableType.STRING
    if name_lower in ("claims", "description", "abstract", "oa_content", "application_file"):
        return VariableType.STRING
    if name_lower in ("user_input", "technical_field", "office_action_summary"):
        return VariableType.STRING

    if sample_value:
        sv = sample_value.strip().lower()
        if sv in ("true", "false", "是", "否", "具备", "不具备"):
            return VariableType.BOOL
        try:
            int(sv)
            return VariableType.INT
        except ValueError:
            pass
        try:
            float(sv)
            return VariableType.FLOAT
        except ValueError:
            pass

    bool_indicators = [
        "is_", "has_", "enable_", "valid", "flag", "check", "confirm",
        "具备", "是否", "可用", "启用"
    ]
    for ind in bool_indicators:
        if ind in name_lower:
            return VariableType.BOOL

    list_indicators = ["list", "items", "docs", "documents", "files", "results", "steps"]
    for ind in list_indicators:
        if ind in name_lower:
            return VariableType.LIST

    int_indicators = ["count", "num", "size", "length", "year", "version", "level"]
    for ind in int_indicators:
        if ind in name_lower:
            return VariableType.INT

    return VariableType.STRING


def infer_source(name: str) -> str:
    """推断变量来源。"""
    name_lower = name.lower()
    if any(k in name_lower for k in ["user_input", "user_query", "query", "需求", "问题", "user"]):
        return "user_input"
    if any(k in name_lower for k in ["document", "file", "content", "text", "pdf", "说明书", "权利要求", "oa_content"]):
        return "document"
    if any(k in name_lower for k in ["extracted", "extract", "识别", "提取"]):
        return "extracted"
    return "system"


# ---------------------------------------------------------------------------
# 模板变量提取（增强版）
# ---------------------------------------------------------------------------

def extract_jinja2_vars_from_template(template: str) -> list[tuple[str, bool]]:
    """从 Jinja2 模板字符串中提取变量名和是否可选（有 default 过滤器）。"""
    pattern = re.compile(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\b([^}]*)\}\}')
    results = []
    seen = set()
    for m in pattern.finditer(template):
        name = m.group(1)
        filters = m.group(2)
        has_default = "default" in filters if filters else False
        if name not in seen:
            seen.add(name)
            results.append((name, has_default))
    return results


def extract_template_from_python(content: str) -> str:
    """从 ScenarioRule Python 文件中提取 system_prompt_template 和 user_prompt_template。"""
    templates = []
    # 匹配 triple-quoted strings after system_prompt_template= or user_prompt_template=
    for attr in ("system_prompt_template", "user_prompt_template"):
        # 寻找属性后的字符串
        pattern = re.compile(
            rf'{attr}\s*=\s*("""|\'\'\')(.*?)\1',
            re.DOTALL
        )
        for m in pattern.finditer(content):
            templates.append(m.group(2))
    return "\n".join(templates)


def read_template_file(path: Path) -> Optional[str]:
    """尝试读取模板文件内容，返回可用于 Jinja2 变量提取的模板字符串。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None

    if path.suffix == ".py":
        return extract_template_from_python(content)
    return content


# ---------------------------------------------------------------------------
# Inventory 解析
# ---------------------------------------------------------------------------

def parse_inventory(inventory_path: Path) -> list[dict[str, Any]]:
    """解析 PROMPT_INVENTORY.md，返回提示词条目列表。"""
    with open(inventory_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = [l for l in content.split("\n") if l.startswith("|") and not l.startswith("|---")]
    entries = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        if len(parts) >= 4:
            entries.append({
                "id": parts[0],
                "path": parts[1].strip("`"),
                "type": parts[2],
                "status": parts[3],
                "variables_raw": parts[4] if len(parts) >= 5 else "-",
            })
    return entries


def parse_inventory_vars(raw: str) -> list[tuple[str, Optional[str]]]:
    """从 inventory Variables 列解析变量名列表。"""
    if raw == "-" or not raw:
        return []

    raw = re.sub(r'\(\+\d+ more\)', '', raw)

    results = []
    parts = re.split(r'[,，、]+', raw)
    for part in parts:
        part = part.strip()
        if not part or part in ("... 中间内容 ...", "中间内容", "同上结构", "继续列出"):
            continue
        m = re.match(r'^["\'](.+)["\']$', part)
        if m:
            results.append((m.group(1), None))
            continue
        m = re.match(r'^例如[:：]\s*(.+)$', part)
        if m:
            results.append((m.group(1), None))
            continue
        if part:
            results.append((part, None))

    return results


# ---------------------------------------------------------------------------
# Schema 生成
# ---------------------------------------------------------------------------

def build_variables_for_entry(entry: dict[str, Any]) -> list[VariableSpec]:
    """为单个 inventory 条目构建 VariableSpec 列表。"""
    schema_id = entry["id"]
    template_path = PROJECT_ROOT / entry["path"]
    template_content = read_template_file(template_path)

    var_map: dict[str, dict[str, Any]] = {}

    # 1. 从实际模板提取 Jinja2 变量（最准确）
    if template_content:
        jinja_vars = extract_jinja2_vars_from_template(template_content)
        for name, has_default in jinja_vars:
            var_map[name] = {
                "name": name,
                "type": infer_type(name),
                "required": not has_default,
                "source": infer_source(name),
                "description": "",
            }

    # 2. 从 inventory 解析变量（仅当没有 Jinja2 变量时补充，或补充描述）
    inventory_vars = parse_inventory_vars(entry["variables_raw"])
    has_jinja2 = bool(var_map)

    for iv_name, iv_sample in inventory_vars:
        sanitized = sanitize_var_name(iv_name)
        if not sanitized:
            continue
        if sanitized in var_map:
            if iv_sample and not var_map[sanitized].get("description"):
                var_map[sanitized]["description"] = iv_sample
            continue
        if re.match(r'^\d+$', sanitized):
            continue
        if sanitized.startswith("p_") and sanitized[2:].isdigit():
            continue
        # 如果已有 Jinja2 变量，则不再添加 inventory 推断的变量（避免误报）
        if has_jinja2:
            continue
        var_map[sanitized] = {
            "name": sanitized,
            "type": infer_type(sanitized, iv_sample),
            "required": True,
            "source": infer_source(sanitized),
            "description": iv_sample or "",
        }

    variables = []
    for name in sorted(var_map.keys()):
        info = var_map[name]
        variables.append(VariableSpec(
            name=info["name"],
            type=info["type"],
            required=info["required"],
            source=info["source"],
            description=info.get("description", ""),
        ))

    return variables


def generate_schema_for_entry(entry: dict[str, Any]) -> Optional[PromptSchema]:
    schema_id = entry["id"]
    status = entry["status"]
    variables = build_variables_for_entry(entry)

    version_map = {"production": "1.0.0", "staging": "0.9.0", "draft": "0.1.0", "deprecated": "0.0.0"}
    version = version_map.get(status, "0.1.0")

    return PromptSchema(
        rule_id=schema_id,
        template_version=version,
        variables=variables,
    )


# ---------------------------------------------------------------------------
# 文件生成
# ---------------------------------------------------------------------------

def group_by_domain(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for e in entries:
        domain = e["id"].split("/")[0] if "/" in e["id"] else "root"
        groups.setdefault(domain, []).append(e)
    return groups


def escape_string(s: str) -> str:
    return s.replace('"', '\\"').replace("\n", "\\n")


def main():
    inventory_path = PROJECT_ROOT / "PROMPT_INVENTORY.md"
    schemas_dir = PROJECT_ROOT / "core" / "prompt_engine" / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    init_path = schemas_dir / "__init__.py"
    with open(init_path, "w", encoding="utf-8") as f:
        f.write('"""Prompt Schema definitions organized by domain."""\n')

    entries = parse_inventory(inventory_path)
    groups = group_by_domain(entries)

    all_schemas: list[PromptSchema] = []
    generated_files: list[str] = []

    for domain, domain_entries in groups.items():
        module_name = domain.replace("-", "_").replace(".", "_")
        file_path = schemas_dir / f"{module_name}.py"

        lines = [
            f'"""',
            f'Domain: {domain}',
            f'Generated schemas for {len(domain_entries)} prompt(s).',
            f'"""',
            "",
            "from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType",
            "",
        ]

        for entry in domain_entries:
            schema = generate_schema_for_entry(entry)
            if schema is None:
                continue
            all_schemas.append(schema)

            const_name = (
                schema.rule_id.upper()
                .replace(".", "_")
                .replace("/", "_")
                .replace("-", "_")
                + "_SCHEMA"
            )
            lines.append(f"# --- {schema.rule_id} ({entry['status']}) ---")
            lines.append(f"{const_name} = PromptSchema(")
            lines.append(f'    rule_id="{schema.rule_id}",')
            lines.append(f'    template_version="{schema.template_version}",')
            lines.append("    variables=[")
            for v in schema.variables:
                args = [f'name="{escape_string(v.name)}"']
                if v.type != VariableType.STRING:
                    args.append(f"type=VariableType.{v.type.name}")
                if not v.required:
                    args.append("required=False")
                if v.source:
                    args.append(f'source="{escape_string(v.source)}"')
                if v.description:
                    args.append(f'description="{escape_string(v.description)}"')
                lines.append("        VariableSpec(")
                for arg in args:
                    lines.append(f"            {arg},")
                lines.append("        ),")
            lines.append("    ],")
            lines.append(")")
            lines.append("")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        generated_files.append(str(file_path.relative_to(PROJECT_ROOT)))

    # 生成注册表
    registry_path = PROJECT_ROOT / "core" / "prompt_engine" / "registry.py"
    registry_lines = [
        '"""',
        "PromptSchemaRegistry - 提示词 Schema 注册表与版本管理",
        '"""',
        "",
        "from typing import Any, Dict, List, Optional",
        "",
        "from core.prompt_engine.schema import PromptSchema",
        "",
        "# Import all domain schemas",
    ]

    for domain in sorted(groups.keys()):
        module_name = domain.replace("-", "_").replace(".", "_")
        registry_lines.append(f"from core.prompt_engine.schemas.{module_name} import *  # noqa: F401,F403")

    registry_lines.extend([
        "",
        "",
        "class VersionCompatibilityError(Exception):",
        '    """版本不兼容异常。"""',
        "    pass",
        "",
        "",
        "class PromptSchemaRegistry:",
        '    """提示词 Schema 注册表。',
        "",
        "    支持功能:",
        "    - 通过 schema_id 检索 Schema",
        "    - 按 domain / status 过滤",
        "    - 版本兼容性检查（向后兼容原则）",
        "    - 变量升级迁移",
        '    """',
        "",
        "    def __init__(self) -> None:",
        '        self._schemas: Dict[str, PromptSchema] = {}',
        '        self._domain_index: Dict[str, List[str]] = {}',
        "        self._register_builtin_schemas()",
        "",
        "    def _register_builtin_schemas(self) -> None:",
        '        """自动注册所有内置 Schema（从各 domain 模块导入）。"""',
    ])

    for schema in all_schemas:
        const_name = (
            schema.rule_id.upper()
            .replace(".", "_")
            .replace("/", "_")
            .replace("-", "_")
            + "_SCHEMA"
        )
        registry_lines.append(f"        self.register({const_name})")

    registry_lines.extend([
        "",
        "    def register(self, schema: PromptSchema) -> None:",
        '        """注册一个 Schema。"""',
        "        self._schemas[schema.rule_id] = schema",
        "        domain = schema.rule_id.split('/')[0] if '/' in schema.rule_id else 'root'",
        "        self._domain_index.setdefault(domain, []).append(schema.rule_id)",
        "",
        "    def get(self, schema_id: str) -> Optional[PromptSchema]:",
        '        """通过 schema_id 获取 Schema。"""',
        "        return self._schemas.get(schema_id)",
        "",
        "    def list_all(self) -> List[str]:",
        '        """返回所有已注册的 schema_id 列表。"""',
        "        return list(self._schemas.keys())",
        "",
        "    def list_by_domain(self, domain: str) -> List[str]:",
        '        """返回指定 domain 下的所有 schema_id。"""',
        "        return self._domain_index.get(domain, [])",
        "",
        "    def get_by_status(self, status: str) -> List[PromptSchema]:",
        '        """按状态过滤 Schema（基于 template_version 前缀推断）。',
        "",
        "        状态与版本映射:",
        "        - production  -> 1.0.x",
        "        - staging     -> 0.9.x",
        "        - draft       -> 0.1.x",
        "        - deprecated  -> 0.0.x",
        '        """',
        "        result: List[PromptSchema] = []",
        '        version_map = {"production": "1.0", "staging": "0.9", "draft": "0.1", "deprecated": "0.0"}',
        "        prefix = version_map.get(status, '')",
        "        for schema in self._schemas.values():",
        "            if schema.template_version.startswith(prefix):",
        "                result.append(schema)",
        "        return result",
        "",
        "    def is_compatible(",
        "        self,",
        "        schema_id: str,",
        "        target_version: str,",
        "    ) -> bool:",
        '        """检查目标版本是否与当前注册版本向后兼容。',
        "",
        "        向后兼容原则（语义化版本）:",
        "        - 主版本号（MAJOR）必须相同",
        "        - 当前次版本号（MINOR） >= 目标次版本号",
        "        - 修订号（PATCH）不参与兼容性判断",
        '        """',
        "        schema = self.get(schema_id)",
        "        if schema is None:",
        "            return False",
        "        return schema.is_compatible_with(target_version)",
        "",
        "    def upgrade_variables(",
        "        self,",
        "        schema_id: str,",
        "        variables: Dict[str, Any],",
        "    ) -> Dict[str, Any]:",
        '        """根据 Schema 定义升级/规范化变量字典。',
        "",
        "        - 填充默认值（对可选变量）",
        "        - 保留已传入的值",
        '        """',
        "        schema = self.get(schema_id)",
        "        if schema is None:",
        "            return variables",
        "        return schema.upgrade_variables(variables)",
        "",
        "    def get_coverage_report(self) -> Dict[str, Any]:",
        '        """生成 Schema 覆盖率报告。"""',
        "        total = len(self._schemas)",
        "        with_vars = sum(1 for s in self._schemas.values() if s.variables)",
        "        without_vars = total - with_vars",
        "        domains = {d: len(ids) for d, ids in self._domain_index.items()}",
        "        return {",
        '            "total_schemas": total,',
        '            "schemas_with_variables": with_vars,',
        '            "schemas_without_variables": without_vars,',
        '            "coverage_rate": round(with_vars / total, 4) if total else 0.0,',
        '            "domains": domains,',
        "        }",
        "",
    ])

    with open(registry_path, "w", encoding="utf-8") as f:
        f.write("\n".join(registry_lines))
    generated_files.append(str(registry_path.relative_to(PROJECT_ROOT)))

    print(f"Generated {len(all_schemas)} schemas in {len(groups)} domain files.")
    print("Files:")
    for gf in generated_files:
        print(f"  - {gf}")


if __name__ == "__main__":
    main()
