# Athena平台代码质量标准

> **版本**: v1.0
> **生效日期**: 2026-04-19
> **适用范围**: Athena平台所有Python代码
> **目的**: 确保代码质量，避免重复错误

---

## 📋 总体原则

### 1. Python版本要求

- **目标版本**: Python 3.11+
- **最低兼容**: Python 3.9
- **类型注解**: 使用现代类型注解 `dict[str, Any]` 而非 `dict`
- **兼容性**: 避免使用Python 3.10+特性（如 `dict[str, int] | None`），使用 `Optional[dict[str, int]]`

### 2. 代码风格

- **遵循PEP 8**: 使用Black和Ruff进行代码格式化
- **行长度**: 100字符（在pyproject.toml中配置）
- **导入顺序**: stdlib → third-party → local
- **Docstrings**: Google风格，所有公共函数必须有

### 3. 类型注解标准

```python
# ✅ 正确: 完整的类型注解
from typing import Any, Optional, List, Dict

def process_task(task: Dict[str, Any]) -> Optional[str]:
    """处理任务"""
    return task.get("result")

# ❌ 错误: 缺少类型注解
def process_task(task):  # 类型缺失
    return task.get("result")

# ❌ 错误: 使用dict而非Dict[str, Any]
def process_task(task: dict) -> str:  # 不完整
    return task.get("result")
```

### 4. 异步编程规范

```python
# ✅ 正确: 只在真正需要异步I/O时使用async
async def fetch_data(url: str) -> Dict[str, Any]:
    """异步获取数据"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# ❌ 错误: 同步代码使用async
async def process_string(text: str) -> str:  # 不需要async
    return text.upper()  # 没有await
```

**规则**:
- 只在包含`await`或异步I/O操作时使用`async def`
- 纯计算或字符串拼接使用普通`def`
- 如果未来可能需要异步，先添加TODO注释

---

## 🔒 错误处理标准

### 1. JSON解析

```python
# ✅ 正确: 完整的错误处理
import json

def parse_input(input_text: str) -> Dict[str, Any]:
    """解析输入为字典"""
    if input_text.strip().startswith("{"):
        try:
            task = json.loads(input_text)
            if not isinstance(task, dict):
                raise ValueError("JSON输入必须是一个对象（字典）")
            return task
        except json.JSONDecodeError as e:
            raise ValueError(f"无效的JSON格式: {e}") from e
    
    # 普通文本处理
    return {"type": "general", "description": input_text}

# ❌ 错误: 缺少错误处理
def parse_input(input_text: str):
    task = json.loads(input_text)  # 可能抛出异常
    return task
```

### 2. 异常捕获

```python
# ✅ 正确: 捕获具体异常
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"值错误: {e}")
    raise
except Exception as e:
    logger.error(f"未知错误: {e}")
    raise

# ❌ 错误: 过于宽泛的异常捕获
try:
    result = risky_operation()
except:  # 不推荐
    pass
```

### 3. 日志记录

```python
# ✅ 正确: 使用适当的日志级别
logger.debug("调试信息")  # 详细调试信息
logger.info("一般信息")   # 重要流程节点
logger.warning("警告信息")  # 潜在问题
logger.error("错误信息")   # 错误和异常

# ❌ 错误: 使用print
print("错误信息")  # 不推荐
```

---

## 🏗️ 架构设计原则

### 1. 继承和组合

```python
# ✅ 正确: 明确的继承关系
class XiaonaAgent(BaseAgent):
    def __init__(self, name: str, role: str):
        super().__init__(name, role, model="gpt-4")

# ❌ 错误: 不完整的初始化
class XiaonaAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)  # 缺少role参数
```

### 2. 方法签名

```python
# ✅ 正确: 完整的方法签名
def process(
    self,
    input_text: str,
    **kwargs: Any
) -> str:
    """处理输入并返回结果"""
    pass

# ❌ 错误: 不完整的签名
def process(self, input_text, **kwargs):  # 缺少类型注解
    pass
```

### 3. 返回类型

```python
# ✅ 正确: 明确的返回类型
from typing import Dict, Any, Optional

def get_result() -> Optional[Dict[str, Any]]:
    """获取结果，可能返回None"""
    return None if error else {"result": "success"}

# ❌ 错误: 返回类型不明确
def get_result():  # 缺少返回类型
    return None if error else {"result": "success"}
```

---

## 🧪 测试标准

### 1. 测试覆盖率

- **目标覆盖率**: >70% overall, >80% for core modules
- **单元测试**: 所有核心模块必须有单元测试
- **集成测试**: 跨模块功能需要集成测试

### 2. 测试命名

```python
# ✅ 正确: 清晰的测试命名
def test_patent_analysis_returns_dict():
    """测试专利分析返回字典"""
    result = analyze_patent("CN123456")
    assert isinstance(result, dict)

def test_patent_analysis_with_invalid_input_raises_error():
    """测试无效输入会抛出错误"""
    with pytest.raises(ValueError):
        analyze_patent("")
```

### 3. 测试文件组织

```
tests/
├── unit/              # 单元测试（无外部依赖）
│   ├── test_agents/
│   └── test_prompt_loader/
├── integration/       # 集成测试（需要外部服务）
│   ├── test_database/
│   └── test_vector_search/
└── e2e/              # 端到端测试（完整流程）
    └── test_patent_workflow/
```

---

## 📝 文档标准

### 1. 代码文档

```python
# ✅ 正确: 完整的函数文档字符串
def analyze_patent_creativity(
    patent_id: str,
    prior_arts: List[str],
    strict_mode: bool = False
) -> Dict[str, Any]:
    """
    分析专利创造性
    
    使用三步法分析专利相对于现有技术的创造性。
    
    Args:
        patent_id: 专利号（如CN123456789A）
        prior_arts: 对比文件列表
        strict_mode: 是否使用严格模式（默认False）
    
    Returns:
        包含分析结果的字典，包含：
        - 'conclusion': 结论（具备/不具备创造性）
        - 'confidence': 置信度（0-1）
        - 'reasoning': 推理过程
    
    Raises:
        ValueError: 如果patent_id格式无效
        DatabaseError: 如果数据库查询失败
    
    Examples:
        >>> analyze_patent_creativity('CN123456A', ['D1'])
        {'conclusion': '具备', 'confidence': 0.75}
    
    Note:
        创造性分析基于《专利法》第22条第3款
    """
    pass
```

### 2. README文档

每个模块和目录都应有README.md说明：

```markdown
# 模块名称

> 简短描述

## 功能
- 功能1
- 功能2

## 使用示例
```python
code example
```

## 依赖
- 依赖1
- 依赖2

## 测试
```bash
pytest tests/
```
```

---

## ✅ 代码审查检查清单

### 提交前检查

- [ ] **代码风格**: 运行`black .`和`ruff check .`
- [ ] **类型检查**: 运行`mypy core/`
- [ ] **测试**: 运行`pytest tests/ -v`
- [ ] **文档**: 更新相关文档
- [ ] **Git状态**: 检查`git status`

### 质量门禁

**必须通过**:
- ✅ 代码风格检查（Black + Ruff）
- ✅ 类型检查（mypy，核心模块）
- ✅ 单元测试（核心模块）
- ✅ 语法检查（py_compile）

**建议通过**:
- ⚠️ 集成测试
- ⚠️ 代码覆盖率 >70%

---

## 🚫 常见错误和避免方法

### 错误1: 缺少类型注解

```python
# ❌ 错误
def process(task):
    return task["result"]

# ✅ 正确
from typing import Dict, Any

def process(task: Dict[str, Any]) -> Any:
    return task["result"]
```

### 错误2: 不必要的async

```python
# ❌ 错误
async def compute(text: str) -> str:
    return text.upper()

# ✅ 正确
def compute(text: str) -> str:
    return text.upper()
```

### 错误3: 不完整的错误处理

```python
# ❌ 错误
task = json.loads(user_input)

# ✅ 正确
try:
    task = json.loads(user_input)
except json.JSONDecodeError as e:
    raise ValueError(f"无效的JSON: {e}") from e
```

### 错误4: Python 3.10+特性

```python
# ❌ 错误（Python 3.9不支持）
def get_result() -> dict[str, int] | None:
    return None

# ✅ 正确（Python 3.9兼容）
from typing import Optional

def get_result() -> Optional[Dict[str, int]]:
    return None
```

### 错误5: 事件循环处理不当

```python
# ❌ 错误（在嵌套循环中会失败）
result = asyncio.run(async_function())

# ✅ 正确（检测并处理嵌套循环）
try:
    loop = asyncio.get_running_loop()
    if loop and loop.is_running():
        # 使用nest_asyncio或其他方案
        pass
except RuntimeError:
    result = asyncio.run(async_function())
```

---

## 📊 代码质量指标

### 目标指标

| 指标 | 目标 | 当前 | 状态 |
|------|------|------|------|
| **代码风格** | 100% Black合规 | 100% | ✅ |
| **类型注解覆盖** | >80% | >85% | ✅ |
| **测试覆盖率** | >70% | >70% | ✅ |
| **Ruff错误数** | 0 | 0 | ✅ |
| **mypy错误** | 仅已知问题 | 0 | ✅ |

### 质量趋势

- **技术债务**: 持续降低
- **Bug率**: 持续降低
- **代码复用**: 持续提升
- **文档完整性**: 持续提升

---

## 🔧 工具配置

### Black配置

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']
```

### Ruff配置

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "N",      # pep8 naming
    "UP",     # pyupgrade
    "ANN",    # flake8-annotations
]
ignore = []
```

### mypy配置

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## 📚 参考资源

### 官方文档
- [PEP 8 - Style Guide for Python Code](https://pep8.org/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

### 平台文档
- [Athena CLAUDE.md](../CLAUDE.md)
- [Athena项目README.md](../README.md)
- [本文件更新记录](./CHANGELOG.md)

---

## 🔄 更新日志

### v1.0 (2026-04-19)

- ✅ 初始版本
- ✅ 基于代码质量审查结果制定
- ✅ 覆盖Python 3.9+兼容性
- ✅ 包含异步编程规范
- ✅ 包含错误处理标准

---

**维护者**: 徐健 (xujian519@gmail.com)  
**最后更新**: 2026-04-19  
**下次审查**: 2026-05-19
