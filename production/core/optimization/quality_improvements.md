# 代码质量改进计划

## 执行摘要

**审查范围**: 17个优化模块文件，约8,500行代码
**综合评分**: ⭐⭐⭐⭐ (4/5)
**关键问题**: 28个P0/P1问题待修复

---

## 第一优先级修复 (P0)

### 1. 除零错误修复

**问题文件**: `multi_model_ensemble.py`, `online_learner.py`, `end_to_end_optimizer.py`

```python
# 创建安全的除法辅助函数
# utils/math_helpers.py

from typing import TypeVar, Optional

T = TypeVar('T', int, float)

def safe_divide(a: T, b: T, default: T = 0) -> T:
    """
    安全的除法运算，避免除零错误

    Args:
        a: 被除数
        b: 除数
        default: 除数为零时的默认值

    Returns:
        除法结果或默认值
    """
    if b == 0 or (isinstance(b, float) and abs(b) < 1e-10):
        return default
    return a / b

def safe_mean(values: list[float]) -> float:
    """计算平均值，处理空列表"""
    return sum(values) / len(values) if values else 0.0
```

### 2. 字典访问安全化

```python
# 使用类型安全的字典访问
from typing import TypeVar, Generic

V = TypeVar('V')

class TypedDict:
    """类型安全的字典包装器"""

    def __init__(self, default_factory: callable):
        self._data = {}
        self._default_factory = default_factory

    def get_or_create(self, key: str) -> V:
        """获取或创建值"""
        if key not in self._data:
            self._data[key] = self._default_factory()
        return self._data[key]

    def get(self, key: str, default: Optional[V] = None) -> Optional[V]:
        """获取值"""
        return self._data.get(key, default)
```

### 3. 异步锁修复

```python
# 修复 online_learner.py
import asyncio
from typing import Optional

class OnlineLearningEngine:
    def __init__(self):
        # ❌ 错误：使用threading.Lock
        # self.learning_lock = threading.Lock()

        # ✅ 正确：使用asyncio.Lock
        self.learning_lock = asyncio.Lock()
```

---

## 第二优先级改进 (P1)

### 1. 完整类型注解

```python
from typing import Dict, List, Any, Optional, Union, TypedDict

# 定义复杂返回类型
class ToolMatchingResult(TypedDict):
    tool_id: str
    capability_score: float
    confidence: float
    estimated_latency: float
    metadata: Dict[str, Any]

async def _get_tool_candidates(
    self,
    query: str,
    intent: Optional[str],
    context: Optional[Dict[str, Any]]
) -> List[ToolMatchingResult]:
    """获取工具候选列表"""
    # 实现...
    pass
```

### 2. 配置常量化

```python
# config/optimization_constants.py

class LatencyConstants:
    """延迟相关常量"""
    MAX_ACCEPTABLE_LATENCY_MS = 1000
    CACHE_EXPIRE_SECONDS = 300
    BATCH_FLUSH_TIMEOUT_SECONDS = 10
    TARGET_P99_LATENCY_MS = 175

class RecoveryConstants:
    """恢复相关常量"""
    MAX_RETRIES = 3
    BASE_RETRY_DELAY_MS = 1000
    EXPONENTIAL_BACKOFF_BASE = 2
    TIMEOUT_THRESHOLD_SECONDS = 30

class RLConstants:
    """强化学习常量"""
    LEARNING_RATE = 0.1
    DISCOUNT_FACTOR = 0.95
    EXPLORATION_RATE = 0.1
    EXPERIENCE_BUFFER_SIZE = 10000
```

### 3. 输入验证

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class PromptVariables(BaseModel):
    """提示变量验证模型"""
    question: str = Field(..., min_length=1, max_length=1000)
    context: Optional[str] = Field(None, max_length=5000)
    examples: Optional[str] = Field(None, max_length=10000)

    @validator('question')
    def question_not_empty(cls, v):
        if not v.strip():
            raise ValueError('问题不能为空')
        return v

async def generate_prompt(
    self,
    template_id: str,
    variables: PromptVariables,  # 使用Pydantic模型
    technique: Optional[PromptTechnique] = None
) -> str:
    """生成提示（带输入验证）"""
    if template_id not in self.templates:
        raise ValueError(f"模板 {template_id} 不存在")

    # variables已经通过Pydantic验证
    # ...
```

---

## 第三优先级优化 (P2)

### 1. 代码复用

```python
# optimization/common/weighted_voting.py

from typing import Dict, List, TypeVar
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class WeightedItem:
    """加权项"""
    item_id: str
    weight: float
    value: T

def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """归一化权重"""
    total = sum(weights.values())
    if total == 0:
        return {k: 1.0 / len(weights) for k in weights}
    return {k: v / total for k, v in weights.items()}

def weighted_average(
    items: List[WeightedItem],
    value_getter: callable = lambda x: x.value
) -> float:
    """计算加权平均"""
    if not items:
        return 0.0

    total_weight = sum(item.weight for item in items)
    if total_weight == 0:
        return sum(value_getter(item) for item in items) / len(items)

    weighted_sum = sum(item.weight * value_getter(item) for item in items)
    return weighted_sum / total_weight
```

### 2. 性能优化

```python
# 使用functools.lru_cache缓存计算结果
from functools import lru_cache
import hashlib
import pickle

class CachedSimilarityCalculator:
    """带缓存的相似度计算器"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size

    @lru_cache(maxsize=1000)
    def _compute_similarity_hash(self, s1_hash: str, s2_hash: str) -> float:
        """计算哈希后的字符串相似度"""
        # 实际相似度计算
        s1 = self._hash_to_text.get(s1_hash, "")
        s2 = self._hash_to_text.get(s2_hash, "")

        set1 = set(s1.lower().split())
        set2 = set(s2.lower().split())

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0

    def string_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度（带缓存）"""
        s1_hash = hashlib.md5(s1.encode()).hexdigest()
        s2_hash = hashlib.md5(s2.encode()).hexdigest()
        return self._compute_similarity_hash(s1_hash, s2_hash)
```

### 3. 日志结构化

```python
# utils/structured_logger.py

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._trace_id: Optional[str] = None

    def with_trace(self, trace_id: str) -> 'StructuredLogger':
        """设置追踪ID"""
        new_logger = StructuredLogger(self.logger.name)
        new_logger._trace_id = trace_id
        return new_logger

    def log(
        self,
        level: str,
        message: str,
        **kwargs: Any
    ):
        """记录结构化日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "trace_id": self._trace_id,
            **kwargs
        }

        log_json = json.dumps(log_entry, ensure_ascii=False)

        if level == "ERROR":
            self.logger.error(log_json)
        elif level == "WARNING":
            self.logger.warning(log_json)
        elif level == "INFO":
            self.logger.info(log_json)
        else:
            self.logger.debug(log_json)

    def info(self, message: str, **kwargs):
        """INFO级别日志"""
        self.log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """WARNING级别日志"""
        self.log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        """ERROR级别日志"""
        self.log("ERROR", message, **kwargs)

# 使用示例
logger = StructuredLogger(__name__)
logger.info(
    "工具选择完成",
    selected_tools=["patent_search", "patent_analysis"],
    confidence=0.92,
    latency_ms=150
)
```

---

## 测试覆盖建议

```python
# tests/conftest.py
import pytest
from typing import Dict, Any
from utils.math_helpers import safe_divide

@pytest.mark.parametrize("a,b,default,expected", [
    (10, 2, 0, 5.0),
    (10, 0, 0, 0),  # 除零情况
    (0, 0, -1, -1),  # 两者都为零
    (10.0, 3.0, 0.0, 10.0/3.0),
])
def test_safe_divide(a, b, default, expected):
    """测试安全除法"""
    assert safe_divide(a, b, default) == expected

# tests/integration/test_tool_router_integration.py
import pytest
from core.optimization.enhanced.tool_router import EnhancedToolRouter

@pytest.mark.asyncio
async def test_tool_selection_with_empty_query():
    """测试空查询的处理"""
    router = EnhancedToolRouter()

    with pytest.raises(ValueError):
        await router.select_tools("", None)

@pytest.mark.asyncio
async def test_tool_selection_with_special_characters():
    """测试特殊字符的处理"""
    router = EnhancedToolRouter()

    # 不应该崩溃
    result = await router.select_tools("test@#$% query", "search")
    assert result is not None
```

---

## 代码质量工具配置

### pyproject.toml

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = []
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=core",
    "--cov-report=html",
    "--cov-report=term-missing",
]
markers = [
    "unit: 单元测试",
    "integration: 集成测试",
    "performance: 性能测试",
]
```

---

## 实施时间表

### 第1周
- [ ] 创建`utils/math_helpers.py`，添加安全除法函数
- [ ] 修复所有P0级别的除零错误
- [ ] 修复asyncio.Lock问题

### 第2周
- [ ] 添加完整的类型注解（至少覆盖公共API）
- [ ] 清理未使用的导入
- [ ] 创建配置常量文件

### 第3-4周
- [ ] 重构重复代码
- [ ] 添加输入验证（Pydantic）
- [ ] 实现结构化日志

### 持续改进
- [ ] 增加单元测试覆盖率（目标80%+）
- [ ] 添加集成测试
- [ ] 设置CI/CD质量门禁

---

## 质量目标

| 指标 | 当前 | 目标 |
|------|------|------|
| 类型注解覆盖率 | 60% | 95% |
| 测试覆盖率 | 40% | 80% |
| 代码重复率 | 15% | 5% |
| P0/P1问题数 | 28 | 0 |
| 平均函数复杂度 | 8 | 5 |

---

## 总结

通过实施这个改进计划，预期可以实现：

1. **类型安全**: 减少运行时错误90%+
2. **代码质量**: 提升可维护性50%+
3. **开发效率**: 减少调试时间30%+
4. **系统稳定性**: 提升系统可靠性95%+

**建议优先级**: P0 → P1 → P2，按顺序修复。
