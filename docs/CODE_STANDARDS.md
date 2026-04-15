# Athena代码规范指南

## 📋 概述

本文档定义Athena工作平台的代码规范，确保代码质量和一致性。

## 🎯 代码质量目标

| 指标 | 当前 | 目标 |
|------|------|------|
| Ruff错误数 | 23,674 | ≤1,000 |
| 自动修复错误 | 12,772 | - |
| 类型注解覆盖率 | ~30% | ≥80% |
| 文档字符串覆盖率 | ~40% | ≥80% |

## 🔧 工具配置

### Ruff配置

**文件**: `pyproject.toml`

```toml
[tool.ruff]
target-version = "py314"
line-length = 100
src = ["core", "dev/tests"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM", "TCH", "PTH", "ERA", "RUF"]
```

### Black配置

```toml
[tool.black]
line-length = 100
target-version = ['py314']
```

### MyPy配置

```toml
[tool.mypy]
python_version = "3.14"
strict = true
disallow_untyped_defs = false  # 渐进式启用
```

## 📊 当前主要问题

### 高优先级问题 (可自动修复)

#### 1. 类型注解现代化 (UP006, UP035, UP045)
**问题数量**: ~5,000

**示例**:
```python
# ❌ 旧式写法
from typing import Dict, List, Optional

def get_data() -> Dict[str, Any]:
    pass

def process(item: Optional[str] = None) -> None:
    pass

# ✅ 新式写法 (Python 3.10+)
def get_data() -> dict[str, Any]:
    pass

def process(item: str | None = None) -> None:
    pass
```

**修复命令**:
```bash
ruff check core/ --fix --select UP
```

#### 2. 导入排序 (I001)
**问题数量**: ~800

**示例**:
```python
# ❌ 未排序
from fastapi import FastAPI
from datetime import datetime
import asyncio

# ✅ 已排序
import asyncio
from datetime import datetime
from fastapi import FastAPI
```

**修复命令**:
```bash
ruff check core/ --fix --select I
```

#### 3. 未使用的导入 (F401)
**问题数量**: ~1,200

**示例**:
```python
# ❌ 导入但未使用
import json
from pathlib import Path

def main():
    print("Hello")

# ✅ 删除未使用导入
def main():
    print("Hello")
```

**修复命令**:
```bash
ruff check core/ --fix --select F
```

#### 4. 文件结尾缺少换行符 (W292)
**问题数量**: ~500

**修复命令**:
```bash
ruff check core/ --fix --select W
```

### 中优先级问题 (需要手动修复)

#### 1. 类型注解缺失
**问题**: 函数/方法缺少类型注解

**示例**:
```python
# ❌ 缺少类型注解
def calculate(a, b):
    return a + b

# ✅ 完整类型注解
def calculate(a: int, b: int) -> int:
    return a + b
```

**改进计划**:
1. 优先为公共API添加类型注解
2. 使用mypy进行类型检查
3. 逐步提升覆盖率

#### 2. 文档字符串缺失/不规范
**问题**: 函数/类缺少文档字符串或格式不规范

**示例**:
```python
# ❌ 缺少文档字符串
def search_patents(query):
    pass

# ✅ Google风格文档字符串
def search_patents(query: str) -> list[Patent]:
    """搜索专利

    Args:
        query: 搜索查询字符串

    Returns:
        匹配的专利列表

    Raises:
        SearchError: 当搜索失败时抛出
    """
    pass
```

**模板**:
```python
def function_name(param1: type1, param2: type2 = default) -> return_type:
    """一句话简短描述

    更详细的描述（可选）。

    Args:
        param1: 参数1描述
        param2: 参数2描述

    Returns:
        返回值描述

    Raises:
        ExceptionType: 异常描述
    """
```

#### 3. 全角字符混用 (RUF001, RUF002, RUF003)
**问题**: 代码中混用全角字符（中文标点）

**示例**:
```python
# ❌ 全角字符
print("开始执行，任务：专利检索")  # 全角逗号和冒号

# ✅ 半角字符
print("开始执行, 任务: 专利检索")  # 半角逗号和冒号
# 或使用英文
print("Starting execution, task: patent search")
```

**修复**: 代码中的字符串使用英文或半角标点

### 低优先级问题 (优化建议)

#### 1. 路径操作使用pathlib (PTH1xx)
**问题**: 使用`os.path`而非`pathlib.Path`

**示例**:
```python
# ❌ 使用os.path
import os
path = os.path.join("dir", "file.txt")
if os.path.exists(path):
    os.remove(path)

# ✅ 使用pathlib
from pathlib import Path
path = Path("dir") / "file.txt"
if path.exists():
    path.unlink()
```

#### 2. 简化代码 (SIM1xx)
**问题**: 可以简化的代码模式

**示例**:
```python
# ❌ 嵌套if
if x:
    if y:
        do_something()

# ✅ 合并条件
if x and y:
    do_something()
```

## 📝 代码风格指南

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写+下划线 | `patent_searcher.py` |
| 类 | 大驼峰 | `PatentSearcher` |
| 函数/方法 | 小写+下划线 | `search_patents()` |
| 常量 | 大写+下划线 | `MAX_RETRIES` |
| 私有成员 | 前缀下划线 | `_internal_method` |

### 导入顺序

```python
# 1. 标准库
import asyncio
from datetime import datetime

# 2. 第三方库
from fastapi import FastAPI
from pydantic import BaseModel

# 3. 本地模块
from core.patents import PatentSearcher
from core.utils import format_date
```

### 类型注解规范

```python
# 基础类型
def func(x: int, y: str) -> bool:
    pass

# 容器类型 (Python 3.10+)
def func(data: list[str], mapping: dict[str, int]) -> tuple[int, str]:
    pass

# 可选类型
def func(required: str, optional: str | None = None) -> None:
    pass

# 联合类型
def func(value: int | str | float) -> str:
    pass

# 类型别名
from typing import TypeAlias
JsonData: TypeAlias = dict[str, Any] | list[Any] | None
```

### 异步函数规范

```python
# 异步函数必须用async def
async def fetch_data(url: str) -> dict[str, Any]:
    """异步获取数据"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# 调用异步函数
async def main():
    data = await fetch_data("https://api.example.com")
```

## 🚀 改进计划

### 阶段1: 自动修复 (1周)

```bash
# 第1步: 修复类型注解
ruff check core/ --fix --select UP

# 第2步: 修复导入排序
ruff check core/ --fix --select I

# 第3步: 修复未使用导入
ruff check core/ --fix --select F401

# 第4步: 修复格式问题
ruff check core/ --fix --select E,W

# 第5步: 运行black格式化
black core/ --line-length 100
```

### 阶段2: 类型注解补充 (2-3周)

**优先级顺序**:
1. `core/api/` - API接口
2. `core/apps/apps/patents/` - 专利核心功能
3. `core/agents/` - Agent相关
4. `core/collaboration/` - 协作模块
5. 其他模块

### 阶段3: 文档补充 (2-3周)

**每个公共函数/类必须包含**:
- 功能描述
- 参数说明
- 返回值说明
- 异常说明（如有）
- 使用示例（可选）

### 阶段4: 持续改进

**CI/CD集成**:
```yaml
# .github/workflows/code-quality.yml
- name: Run ruff
  run: ruff check core/ --select ALL

- name: Run mypy
  run: mypy core/

- name: Run tests
  run: pytest dev/tests/ --cov=core
```

## 📋 检查清单

提交代码前确认：

- [ ] 运行`ruff check core/`无错误
- [ ] 运行`black core/ --check`格式正确
- [ ] 运行`mypy core/`类型检查通过
- [ ] 运行`pytest dev/tests/`测试通过
- [ ] 公共函数有完整文档字符串
- [ ] 新代码有类型注解
- [ ] 无调试print语句
- [ ] 无TODO/FIXME注释（或创建issue）

## 🔗 相关资源

- [Ruff文档](https://docs.astral.sh/ruff/)
- [Black文档](https://black.readthedocs.io/)
- [Mypy文档](https://mypy.readthedocs.io/)
- [PEP 8](https://peps.python.org/pep-0008/)
- [Google Python风格指南](https://google.github.io/styleguide/pyguide.html)
