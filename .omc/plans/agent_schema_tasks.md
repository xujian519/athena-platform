# Agent-Schema (A4) 任务包

> 变量治理与模板协议化智能体
> 负责范围: Jinja2 渲染器、变量 Schema、校验器、注入安全、Prompt Inventory
> 启动条件: W7（依赖 Agent-Core A2 完成主链路改造）
> 并行关系: 可与 Agent-Migrate (A3) 后半段并行

---

## 上下文代码路径

| 文件 | 说明 |
|---|---|
| `core/api/prompt_system_routes.py:520` | `rule.substitute_variables(all_variables)` |
| `domains/legal/core_modules/legal_world_model/scenario_rule_retriever_optimized.py:113` | `ScenarioRule.substitute_variables()` 实现 |
| `prompts/foundation/` / `prompts/capability/` / `prompts/business/` | 四层提示词资产 |
| `core/ai/prompts/quality_evaluator.py` | 质量评估器（参考）|

---

## 任务 3.1.1: Jinja2 渲染器实现

**输出**: `core/prompt_engine/renderer.py`

**具体要求**:
```python
from jinja2 import Environment, BaseLoader, StrictUndefined

class PromptRenderer:
    def __init__(self):
        self.env = Environment(
            loader=BaseLoader(),
            undefined=StrictUndefined,  # 关键：缺失变量直接抛异常
            autoescape=False,           # 我们自行控制转义（由 sanitizer 处理）
        )
        # 注册自定义过滤器
        self.env.filters["default"] = self._default_filter
        self.env.filters["truncate"] = self._truncate_filter
    
    def render(self, template: str, variables: dict) -> str:
        jinja_template = self.env.from_string(template)
        return jinja_template.render(**variables)
    
    def _default_filter(self, value, default_value=""):
        return value if value is not None else default_value
    
    def _truncate_filter(self, value, length=100):
        s = str(value)
        return s[:length] + "..." if len(s) > length else s
```

**验收检查清单**:
- [ ] 正常渲染通过
- [ ] 缺失变量抛出 `jinja2.exceptions.UndefinedError`
- [ ] `{{ var \| default('暂无') }}` 过滤器工作正常
- [ ] `{{ var \| truncate(50) }}` 过滤器工作正常
- [ ] ruff/mypy 通过

---

## 任务 3.1.2: 变量 Schema 定义

**输出**: `core/prompt_engine/schema.py`

**具体要求**:
```python
from dataclasses import dataclass, field
from typing import Any
from enum import Enum

class VariableType(str, Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"

@dataclass
class VariableSpec:
    name: str
    type: VariableType = VariableType.STRING
    required: bool = True
    source: str = ""           # user_input | document | extracted | system
    default: Any = None
    description: str = ""
    max_length: int | None = None
    pattern: str | None = None  # 正则校验（可选）
    enum: list[str] | None = None  # 枚举值（可选）

@dataclass
class PromptSchema:
    rule_id: str
    template_version: str
    variables: list[VariableSpec] = field(default_factory=list)
    
    def get_required_vars(self) -> list[str]:
        return [v.name for v in self.variables if v.required]
    
    def get_optional_vars(self) -> list[str]:
        return [v.name for v in self.variables if not v.required]
```

**为以下模板编写 schema**:
1. `patent.office_action.analysis`（OA 解读）
2. `patent.inventive.analysis`（创造性分析）
3. `patent.novelty.analysis`（新颖性分析）

**验收检查清单**:
- [ ] 类型枚举完整
- [ ] 3 个模板的 schema 定义完成
- [ ] `get_required_vars()` / `get_optional_vars()` 工作正确

---

## 任务 3.1.3: 场景规则模板语法升级

**输出**: 更新后的 Neo4j 场景规则 + PR

**具体操作**:
1. 读取现有场景规则的 `system_prompt_template` / `user_prompt_template`
2. 将 `{var}` 替换为 `{{ var }}`:
   ```python
   import re
   def upgrade_syntax(template: str) -> str:
       # 简单占位符升级
       # {application_number} → {{ application_number }}
       # 但注意不替换已有的 {{ 或 JSON 中的 { }
       return re.sub(r'(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})', r'{{ \1 }}', template)
   ```
3. 增加过滤器:
   - `{similar_cases}` → `{{ similar_cases | default('暂无') }}`
   - 长文本字段增加 `| truncate(500)`
4. 修改 `ScenarioRule.substitute_variables()` 或新建子类:
   ```python
   class Jinja2ScenarioRule(ScenarioRule):
       def substitute_variables(self, variables: dict) -> tuple[str, str]:
           renderer = PromptRenderer()
           system = renderer.render(self.system_prompt_template, variables)
           user = renderer.render(self.user_prompt_template, variables)
           return system, user
   ```
5. 灰度切换：先支持双语法并存，验证无误后再全面切换

**验收检查清单**:
- [ ] 模板渲染结果与原 `{var}` 替换结果一致（对比测试 100% pass）
- [ ] `StrictUndefined` 在缺失变量时抛出 `UndefinedError`
- [ ] ruff/mypy 通过

---

## 任务 3.2.1: 变量校验器实现

**输出**: `core/prompt_engine/validators.py`

**具体要求**:
```python
from dataclasses import dataclass

@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

class VariableValidator:
    def validate(self, schema: PromptSchema, variables: dict) -> ValidationResult:
        errors = []
        warnings = []
        
        for spec in schema.variables:
            value = variables.get(spec.name)
            
            # required 检查
            if spec.required and (value is None or value == ""):
                errors.append(f"Missing required variable: {spec.name}")
                continue
            
            # 类型检查
            if value is not None:
                type_ok, type_msg = self._check_type(value, spec.type)
                if not type_ok:
                    errors.append(f"Variable {spec.name}: {type_msg}")
            
            # max_length 检查
            if spec.max_length and len(str(value)) > spec.max_length:
                errors.append(f"Variable {spec.name} exceeds max_length {spec.max_length}")
            
            # 正则检查
            if spec.pattern and value is not None:
                import re
                if not re.match(spec.pattern, str(value)):
                    errors.append(f"Variable {spec.name} does not match pattern {spec.pattern}")
            
            # 枚举检查
            if spec.enum and value is not None:
                if str(value) not in spec.enum:
                    errors.append(f"Variable {spec.name} must be one of {spec.enum}")
        
        # 检查是否有未声明的变量（warning）
        declared = {v.name for v in schema.variables}
        for key in variables:
            if key not in declared and not key.startswith("__"):
                warnings.append(f"Undeclared variable: {key}")
        
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
    
    def _check_type(self, value, expected_type: VariableType) -> tuple[bool, str]:
        # 实现类型检查逻辑
        ...
```

**验收检查清单**:
- [ ] required 缺失检查通过
- [ ] 类型不匹配检查通过
- [ ] max_length 超限检查通过
- [ ] 正则不匹配检查通过
- [ ] 枚举值不匹配检查通过
- [ ] 未声明变量产生 warning 但不阻断

---

## 任务 3.2.2: 注入安全策略

**输出**: `core/prompt_engine/sanitizer.py`

**具体要求**:
```python
import re
from dataclasses import dataclass
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class InjectionRisk:
    level: RiskLevel
    pattern_matched: str
    recommendation: str

class PromptSanitizer:
    # 常见 injection 模式（可扩展）
    INJECTION_PATTERNS = [
        (r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|commands?)", RiskLevel.CRITICAL),
        (r"forget\s+(everything|all|your\s+instructions)", RiskLevel.CRITICAL),
        (r"you\s+are\s+now\s+.*?(ignore|disregard)", RiskLevel.HIGH),
        (r"system\s*[:\-]?\s*\n", RiskLevel.HIGH),
        (r"<\s*/?\s*system\s*>", RiskLevel.HIGH),
        (r"DAN|jailbreak|developer\s+mode", RiskLevel.MEDIUM),
    ]
    
    def sanitize_string(self, value: str, max_length: int = 10000) -> str:
        if not value:
            return ""
        # 截断
        if len(value) > max_length:
            value = value[:max_length]
        # 控制字符清洗（保留 \n \t）
        value = "".join(ch for ch in value if ch == "\n" or ch == "\t" or (ch.isprintable() and ord(ch) >= 32))
        return value
    
    def escape_markdown(self, value: str) -> str:
        # 转义 Markdown 特殊字符
        chars = ["\\", "`", "*", "_", "{", "}", "[", "]", "(", ")", "#", "+", "-", "!", "|"]
        for ch in chars:
            value = value.replace(ch, "\\" + ch)
        return value
    
    def detect_injection(self, value: str) -> list[InjectionRisk]:
        risks = []
        value_lower = value.lower()
        for pattern, level in self.INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                risks.append(InjectionRisk(
                    level=level,
                    pattern_matched=pattern,
                    recommendation="Review input for prompt injection attempt"
                ))
        return risks
    
    def sanitize_variables(self, variables: dict, schema: PromptSchema) -> tuple[dict, list[InjectionRisk]]:
        sanitized = {}
        all_risks = []
        
        for spec in schema.variables:
            value = variables.get(spec.name, spec.default or "")
            str_value = str(value) if value is not None else ""
            
            # 清洗
            str_value = self.sanitize_string(str_value, max_length=spec.max_length or 10000)
            
            # 检测 injection
            risks = self.detect_injection(str_value)
            all_risks.extend(risks)
            
            sanitized[spec.name] = str_value
        
        return sanitized, all_risks
```

**接入主链路**:
在 `generate_prompt()` 的变量准备阶段（第 478 行附近）调用 sanitizer:
```python
from core.prompt_engine.sanitizer import PromptSanitizer
from core.prompt_engine.validators import VariableValidator

sanitizer = PromptSanitizer()
validator = VariableValidator()

# 加载 schema（从 Neo4j 或内存缓存）
schema = load_schema(rule.rule_id)

# 校验
validation = validator.validate(schema, all_variables)
if not validation.valid:
    raise HTTPException(status_code=400, detail={
        "error": "MISSING_VARIABLES",
        "missing": validation.errors,
    })

# 清洗
sanitized_vars, risks = sanitizer.sanitize_variables(all_variables, schema)
if any(r.level in (RiskLevel.HIGH, RiskLevel.CRITICAL) for r in risks):
    logger.warning(f"High-risk injection detected: {risks}")
    # 可配置为阻断或仅告警
```

**验收检查清单**:
- [ ] 10 种常见 injection 模式检测率 > 80%
- [ ] 正常业务输入不误报（抽样 100 条验证）
- [ ] sanitize_string 控制字符清洗正确
- [ ] max_length 截断生效

---

## 任务 3.2.3: 缺失变量阻断策略接入主链路

**输出**: PR（改动 `core/api/prompt_system_routes.py`）

**具体要求**:
1. 在 `generate_prompt()` 中，变量替换前增加校验步骤
2. 校验失败时返回 400:
   ```json
   {
     "error": "MISSING_VARIABLES",
     "missing": ["application_number", "oa_text"],
     "message": "Required variables missing: application_number, oa_text"
   }
   ```
3. 可选变量缺失时使用默认值，不阻断
4. 不进入 LLM 调用（节省 token 成本）

---

## 任务 3.3.1: Prompt Inventory 自动化

**输出**: `scripts/generate_prompt_inventory.py` + `PROMPT_INVENTORY.md`

**具体要求**:
```python
#!/usr/bin/env python3
"""扫描并生成 Prompt Inventory"""

import os
import json
from pathlib import Path
from datetime import datetime

def scan_prompts():
    inventory = {
        "generated_at": datetime.now().isoformat(),
        "templates": [],
    }
    
    # 扫描 prompts/ 目录
    prompts_dir = Path("prompts")
    for md_file in prompts_dir.rglob("*.md"):
        relative = md_file.relative_to(prompts_dir)
        inventory["templates"].append({
            "id": str(relative.with_suffix("")),
            "path": str(md_file),
            "type": "markdown_static",
            "status": _infer_status(md_file),
            "variables": _extract_variables(md_file),
        })
    
    # 扫描 Neo4j 场景规则（需实现 Neo4j 查询）
    # ...
    
    return inventory

def _infer_status(md_file: Path) -> str:
    name = md_file.name.lower()
    if "deprecated" in name or "old" in name or "v1" in name or "v2" in name:
        return "deprecated"
    if "draft" in name or "wip" in name:
        return "draft"
    return "production"

def _extract_variables(md_file: Path) -> list[str]:
    content = md_file.read_text(encoding="utf-8")
    import re
    # 匹配 {var_name} 和 {{ var_name }}
    vars1 = re.findall(r'\{\{?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}?\}', content)
    return sorted(set(vars1))

if __name__ == "__main__":
    inventory = scan_prompts()
    with open("PROMPT_INVENTORY.md", "w", encoding="utf-8") as f:
        f.write("# Prompt Inventory\n\n")
        f.write(f"Generated at: {inventory['generated_at']}\n\n")
        f.write("| ID | Path | Type | Status | Variables |\n")
        f.write("|---|---|---|---|---|\n")
        for t in inventory["templates"]:
            vars_str = ", ".join(t["variables"]) if t["variables"] else "-"
            f.write(f"| {t['id']} | {t['path']} | {t['type']} | {t['status']} | {vars_str} |\n")
    print("PROMPT_INVENTORY.md generated.")
```

**CI 检查**:
```yaml
# .github/workflows/prompt-inventory-check.yml
name: Prompt Inventory Check
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate Inventory
        run: python scripts/generate_prompt_inventory.py
      - name: Check diff
        run: |
          if ! git diff --quiet PROMPT_INVENTORY.md; then
            echo "PROMPT_INVENTORY.md is outdated. Please run 'python scripts/generate_prompt_inventory.py' and commit the changes."
            exit 1
          fi
```

**验收检查清单**:
- [ ] 扫描脚本覆盖 prompts/ 目录和 Neo4j 场景规则库
- [ ] Inventory 覆盖 100% 的生产使用模板
- [ ] CI 检查生效，未更新 Inventory 的 PR 被阻断

---

## 任务 3.3.2: 存量模板变量 Schema 补齐

**输出**: 更新后的场景规则 + schema 存储

**具体操作**:
1. 遍历全部生产场景规则模板（Neo4j 中 status=production）
2. 提取所有占位符（`{var}` 和 `{{ var }}`）
3. 根据占位符名称和上下文推断类型、required/optional、default
4. 补全 `VariableSpec`
5. 存储到 Neo4j（在 ScenarioRule 节点上增加 `variable_schema` 属性，或新建 `PromptSchema` 节点并建立关系）
