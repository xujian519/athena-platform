# 输入验证框架使用指南

# Input Validation Framework Guide

**版本**: v3.1.0
**作者**: Athena平台团队
**创建时间**: 2026-04-24
**状态**: Phase 3.1安全加固

---

## 目录

1. [概述](#概述)
2. [核心组件](#核心组件)
3. [快速开始](#快速开始)
4. [Schema验证](#schema验证)
5. [安全检查](#安全检查)
6. [配置管理](#配置管理)
7. [API文档](#api文档)
8. [安全最佳实践](#安全最佳实践)
9. [常见问题](#常见问题)

---

## 概述

Athena平台输入验证框架提供完整的输入验证和安全检查功能，保护上下文系统免受恶意输入攻击。

### 安全目标

- ✅ 检测100%的常见SQL注入模式
- ✅ 检测100%的常见XSS攻击向量
- ✅ 检测95%以上的命令注入模式
- ✅ 检测100%的路径遍历攻击
- ✅ 验证失败时返回详细的错误信息

### 核心特性

- 🏗️ **模块化设计**: 独立的验证器可以单独使用或组合使用
- 🔒 **多层防护**: Schema验证 + 安全检查双重保护
- ⚡ **高性能**: 支持快速失败模式，发现第一个问题就停止
- 📊 **详细报告**: 提供完整的验证报告和安全问题详情
- 🎯 **类型安全**: 完整的类型注解，支持Python 3.9+

---

## 核心组件

### 1. BaseContextValidator

基础验证器类，实现`IContextValidator`接口。

```python
from core.context_management.validation import BaseContextValidator

# 创建自定义验证器
class MyValidator(BaseContextValidator):
    async def _validate_context(self, context: IContext) -> None:
        # 实现验证逻辑
        pass

    async def _security_check_context(self, context: IContext) -> None:
        # 实现安全检查逻辑
        pass
```

### 2. SchemaValidator

Schema验证器，使用规则或Pydantic模型进行数据验证。

```python
from core.context_management.validation import SchemaValidator, FieldRule

# 创建验证规则
rule = FieldRule(
    field_name="username",
    required=True,
    field_type=str,
    min_length=3,
    max_length=20,
    pattern=r"^[a-zA-Z0-9_]+$"
)

validator = SchemaValidator(field_rules=[rule])
```

### 3. SecurityChecker

安全检查器，检测各种恶意输入和注入攻击。

```python
from core.context_management.validation import SecurityChecker

checker = SecurityChecker(
    enable_sql_check=True,
    enable_xss_check=True,
    enable_command_check=True,
    enable_path_check=True,
)
```

### 4. ContextValidator

通用上下文验证器，结合Schema验证和安全检查。

```python
from core.context_management.validation import ContextValidator

validator = ContextValidator(
    strict_mode=False,
    fail_fast=False,
    enable_security_check=True,
)
```

---

## 快速开始

### 基本使用

```python
from core.context_management.validation import ContextValidator
from core.context_management.interfaces import IContext

# 创建验证器
validator = ContextValidator()

# 验证上下文
is_valid = await validator.validate(context)

# 执行安全检查
issues = await validator.security_check(context)

# 获取验证报告
report = validator.get_validation_report()
```

### 处理验证结果

```python
# 检查是否有错误
if validator.has_errors():
    for error in validator.validation_errors:
        print(f"字段: {error.field}")
        print(f"错误: {error.message}")
        print(f"代码: {error.code}")

# 检查是否有安全问题
if validator.has_security_issues():
    for issue in validator.security_issues:
        print(f"严重程度: {issue.severity}")
        print(f"类别: {issue.category}")
        print(f"描述: {issue.description}")
        print(f"证据: {issue.evidence}")

# 检查严重安全问题
if validator.has_critical_issues():
    critical_issues = validator.get_critical_issues()
    # 处理严重问题...
```

---

## Schema验证

### 字段规则

```python
from core.context_management.validation import SchemaValidator, FieldRule

# 创建规则
rules = [
    # 字符串规则
    SchemaValidator.string_rule(
        "username",
        required=True,
        min_length=3,
        max_length=20,
    ),

    # 整数规则
    SchemaValidator.integer_rule(
        "age",
        required=True,
        min_value=18,
        max_value=120,
    ),

    # 邮箱规则
    SchemaValidator.email_rule("email", required=True),

    # URL规则
    SchemaValidator.url_rule("website", required=False),

    # UUID规则
    SchemaValidator.uuid_rule("session_id", required=True),

    # 枚举规则
    SchemaValidator.enum_rule(
        "status",
        allowed_values={"active", "inactive", "pending"},
        required=True,
    ),
]

validator = SchemaValidator(field_rules=rules)
```

### 使用Pydantic模型

```python
from pydantic import BaseModel, Field
from core.context_management.validation import SchemaValidator

class UserContextModel(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: str
    age: int = Field(..., ge=18, le=120)
    status: str = Field(default="active")

validator = SchemaValidator(pydantic_model=UserContextModel)
```

### 自定义验证器

```python
def even_number(value: int) -> bool:
    """验证是否为偶数"""
    return value % 2 == 0

rule = FieldRule(
    field_name="even_value",
    field_type=int,
    custom_validator=even_number,
)
```

---

## 安全检查

### SQL注入检测

检测以下SQL注入模式：
- 经典注入: `' OR '1'='1`
- UNION注入: `' UNION SELECT ...`
- 盲注: `' AND SLEEP(5)`
- 堆叠查询: `'; DROP TABLE ...`
- 注释注入: `--`, `/*`, `#`

```python
from core.context_management.validation import SecurityChecker

checker = SecurityChecker(enable_sql_check=True)

# 会被检测为SQL注入
malicious_input = "SELECT * FROM users WHERE id='1' OR '1'='1'"
```

### XSS检测

检测以下XSS攻击向量：
- Script标签: `<script>alert('XSS')</script>`
- 事件处理器: `<img onerror=alert('XSS')>`
- 危险协议: `javascript:`, `vbscript:`
- HTML实体编码: `&#x...;`

```python
checker = SecurityChecker(enable_xss_check=True)

# 会被检测为XSS
malicious_input = "<script>alert('XSS')</script>"
```

### 命令注入检测

检测以下命令注入模式：
- Shell元字符: `;`, `|`, `&`, `` ` ``, `$`
- 命令替换: `$(command)`, `` `command` ``
- 逻辑运算: `&&`, `||`

```python
checker = SecurityChecker(enable_command_check=True)

# 会被检测为命令注入
malicious_input = "file.txt; rm -rf /"
```

### 路径遍历检测

检测以下路径遍历攻击：
- 相对路径: `../`, `..\\`
- 编码变体: `%2e%2e/`, `..%255c`
- 绝对路径: `/etc/passwd`, `C:\Windows`

```python
checker = SecurityChecker(enable_path_check=True)

# 会被检测为路径遍历
malicious_input = "../../../etc/passwd"
```

---

## 配置管理

### 加载配置文件

```python
import yaml

with open("config/validation_rules.yaml", "r") as f:
    config = yaml.safe_load(f)

# 使用配置创建验证器
validator = ContextValidator(
    strict_mode=config["global"]["strict_mode"],
    fail_fast=config["global"]["fail_fast"],
)
```

### 配置文件结构

```yaml
global:
  strict_mode: false
  fail_fast: false

schema:
  length_limits:
    string:
      min_length: 0
      max_length: 10000

security:
  enabled_checks:
    sql_injection: true
    xss: true
    command_injection: true
    path_traversal: true
```

---

## API文档

### ValidationError

```python
@dataclass
class ValidationError:
    field: str              # 字段名
    message: str            # 错误消息
    code: str              # 错误代码
    value: Any = None      # 导致错误的值
    timestamp: str         # 时间戳

    def to_dict(self) -> Dict[str, Any]
    def __str__(self) -> str
```

### SecurityIssue

```python
@dataclass
class SecurityIssue:
    severity: str              # 严重程度
    category: str             # 安全类别
    description: str          # 问题描述
    evidence: str             # 证据
    location: Optional[str]   # 位置
    recommendation: Optional[str]  # 修复建议
    timestamp: str            # 时间戳

    # 严重程度常量
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    # 安全类别常量
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"

    def to_dict(self) -> Dict[str, Any]
    def __str__(self) -> str
    @classmethod
    def get_severity_level(severity: str) -> int
```

### ContextValidator

```python
class ContextValidator(BaseContextValidator):
    def __init__(
        self,
        strict_mode: bool = False,
        fail_fast: bool = False,
        enable_security_check: bool = True,
    )

    async def validate(self, context: IContext) -> bool
    async def security_check(self, context: IContext) -> List[str]
    def get_validation_report(self) -> Dict[str, Any]
    def clear_errors(self) -> None
    def has_errors(self) -> bool
    def has_security_issues(self) -> bool
    def has_critical_issues(self) -> bool
```

---

## 安全最佳实践

### 1. 始终验证用户输入

```python
# ❌ 错误：直接使用用户输入
query = f"SELECT * FROM users WHERE username='{user_input}'"

# ✅ 正确：先验证再使用
validator = ContextValidator()
await validator.validate(context)
if not validator.has_errors():
    # 安全地使用输入
```

### 2. 使用参数化查询

```python
# ❌ 错误：字符串拼接
query = f"SELECT * FROM users WHERE id='{user_id}'"

# ✅ 正确：参数化查询
cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
```

### 3. 输出时进行转义

```python
from core.context_management.validation import SecurityChecker

# 转义HTML输出
safe_html = SecurityChecker.sanitize_html(user_input)

# 清理文件名
safe_filename = SecurityChecker.sanitize_filename(user_input)
```

### 4. 实施深度防御

```python
# 多层验证
validator = ContextValidator(strict_mode=True)

# 第一层：Schema验证
schema_valid = await validator.validate(context)

# 第二层：安全检查
issues = await validator.security_check(context)

# 第三层：业务逻辑验证
business_valid = await business_logic_check(context)

# 所有层都通过才接受输入
if schema_valid and not issues and business_valid:
    # 安全地处理输入
```

### 5. 记录安全事件

```python
import logging

logger = logging.getLogger(__name__)

if validator.has_critical_issues():
    for issue in validator.get_critical_issues():
        logger.critical(
            f"Security issue detected: {issue.category} - {issue.description}",
            extra={
                "evidence": issue.evidence,
                "location": issue.location,
                "user_id": getattr(context, 'user_id', 'unknown'),
            }
        )
```

---

## 常见问题

### Q1: 为什么安全检查器检测到了"SELECT"关键字？

A: 当前实现使用模式匹配检测SQL关键字。如果你需要在文本中使用这些单词，请：
1. 使用白名单验证
2. 在安全上下文中使用（如内部字段）
3. 考虑使用更严格的上下文检测

### Q2: 如何处理误报？

A: 有几种方法：
1. 使用白名单过滤已知的合法输入
2. 调整验证器的严格程度
3. 为特定字段禁用某些检查
4. 使用自定义验证器

### Q3: 验证会影响性能吗？

A: 验证框架经过优化：
- 使用快速失败模式减少不必要的检查
- 编译后的正则表达式提高匹配速度
- 可以选择性启用/禁用特定检查

### Q4: 如何验证嵌套结构？

A: 验证框架自动递归检查所有嵌套的字典和列表：
```python
context = TestContext({
    "user": {
        "profile": {
            "bio": "<script>alert('xss')</script>"
        }
    }
})
# 会检测到深层嵌套中的XSS
```

### Q5: 支持哪些Python版本？

A: 框架完全兼容Python 3.9+，使用类型注解的兼容写法：
```python
# Python 3.9+兼容
from typing import Optional

def foo(value: Optional[str] = None) -> bool:
    return value is not None
```

---

## 参考资料

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [CWE-79: Cross-site Scripting](https://cwe.mitre.org/data/definitions/79.html)
- [CWE-89: SQL Injection](https://cwe.mitre.org/data/definitions/89.html)

---

**文档维护**: Athena平台团队
**最后更新**: 2026-04-24
