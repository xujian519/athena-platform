# 测试驱动开发 (TDD) 实施指南

**适用项目**: Athena平台扩展功能开发
**开发模式**: 测试驱动开发 (Test-Driven Development)
**创建日期**: 2026-04-20

---

## 🎯 TDD 核心原则

### Red-Green-Refactor 循环

```
┌─────────┐    ┌─────────┐    ┌───────────┐
│   Red   │ -> │  Green  │ -> │ Refactor  │
│ 写测试   │    │  写代码   │    │  重构    │
└─────────┘    └─────────┘    └───────────┘
     ↓              ↓               ↓
  测试失败      测试通过        代码优化
```

### 三条法则

1. **不写生产代码，除非是为了让失败的测试通过**
2. **只写刚好足够的测试来失败**
3. **只写刚好足够的代码来让测试通过**

---

## 📋 TDD 实施步骤

### 步骤 1: 编写测试 (Red)

**目标**: 明确需求和接口

**示例** - Skills系统:
```python
# tests/skills/test_skill_registry.py

import pytest
from core.skills.types import SkillDefinition, SkillCategory
from core.skills.registry import SkillRegistry

def test_register_skill():
    """测试技能注册"""
    # Arrange
    registry = SkillRegistry()
    skill = SkillDefinition(
        id="test_skill",
        name="Test Skill",
        category=SkillCategory.ANALYSIS,
        description="A test skill",
        tools=["tool1", "tool2"],
    )
    
    # Act
    registry.register(skill)
    
    # Assert
    retrieved = registry.get_skill("test_skill")
    assert retrieved is not None
    assert retrieved.id == "test_skill"
    assert retrieved.name == "Test Skill"
    assert retrieved.category == SkillCategory.ANALYSIS

def test_get_nonexistent_skill():
    """测试获取不存在的技能"""
    registry = SkillRegistry()
    
    result = registry.get_skill("nonexistent")
    
    assert result is None

def test_list_skills_by_category():
    """测试按类别列出技能"""
    registry = SkillRegistry()
    
    skill1 = SkillDefinition(
        id="skill1",
        name="Skill 1",
        category=SkillCategory.ANALYSIS,
        description="",
        tools=[],
    )
    skill2 = SkillDefinition(
        id="skill2",
        name="Skill 2",
        category=SkillCategory.WRITING,
        description="",
        tools=[],
    )
    
    registry.register(skill1)
    registry.register(skill2)
    
    analysis_skills = registry.list_skills(category=SkillCategory.ANALYSIS)
    
    assert len(analysis_skills) == 1
    assert analysis_skills[0].id == "skill1"
```

**运行测试** (预期失败):
```bash
$ pytest tests/skills/test_skill_registry.py -v

=========================== short test summary ===========================
FAILED [errors/失败信息]
```

### 步骤 2: 实现代码 (Green)

**目标**: 让测试通过

**示例** - 实现 SkillRegistry:
```python
# core/skills/types.py

from dataclasses import dataclass
from enum import Enum

class SkillCategory(Enum):
    """技能类别"""
    ANALYSIS = "analysis"
    WRITING = "writing"
    SEARCH = "search"

@dataclass
class SkillDefinition:
    """技能定义"""
    id: str
    name: str
    category: SkillCategory
    description: str
    tools: list[str]
    metadata: dict | None = None

# core/skills/registry.py

from typing import Dict, Optional

class SkillRegistry:
    """技能注册表"""
    
    def __init__(self):
        self._skills: Dict[str, SkillDefinition] = {}
    
    def register(self, skill: SkillDefinition) -> None:
        """注册技能"""
        self._skills[skill.id] = skill
    
    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        """获取技能"""
        return self._skills.get(skill_id)
    
    def list_skills(self, category: Optional[SkillCategory] = None):
        """列出技能"""
        skills = list(self._skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        return skills
```

**运行测试** (预期通过):
```bash
$ pytest tests/skills/test_skill_registry.py -v

=========================== 3 passed in 0.05s ===========================
```

### 步骤 3: 重构优化 (Refactor)

**目标**: 改进代码质量

**重构示例**:
```python
# 重构前
class SkillRegistry:
    def list_skills(self, category=None):
        skills = list(self._skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        return skills

# 重构后 (添加类型注解和缓存)
from functools import lru_cache

class SkillRegistry:
    @lru_cache(maxsize=128)
    def list_skills(self, category: Optional[SkillCategory] = None) -> list[SkillDefinition]:
        """列出技能"""
        skills = list(self._skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        return skills
    
    def invalidate_cache(self) -> None:
        """清除缓存"""
        self.list_skills.cache_clear()
```

**验证重构**:
```bash
$ pytest tests/skills/test_skill_registry.py -v

=========================== 3 passed in 0.04s ===========================
```

---

## 🧪 测试组织结构

### 目录结构

```
tests/
├── skills/                    # Skills系统测试
│   ├── test_skill_registry.py
│   ├── test_skill_loader.py
│   └── test_skill_tool_mapping.py
├── plugins/                   # Plugins系统测试
│   ├── test_plugin_registry.py
│   ├── test_plugin_loader.py
│   └── test_plugin_tool_integration.py
├── memory/                    # 记忆系统测试
│   ├── test_file_memory.py
│   └── test_four_tier_integration.py
├── tasks/                     # 任务管理器测试
│   ├── test_task_manager.py
│   └── test_task_websocket.py
├── context/                   # 上下文压缩测试
│   ├── test_token_counter.py
│   ├── test_compactor.py
│   └── test_agent_loop_integration.py
├── hooks/                     # Hook系统测试
│   ├── test_hook_types.py
│   └── test_executor.py
├── query/                     # Query Engine测试
│   ├── test_query_engine.py
│   ├── test_cost_tracker.py
│   └── test_history.py
├── coordination/              # Coordinator测试
│   ├── test_coordinator.py
│   ├── test_task_decomposer.py
│   └── test_task_assignment.py
├── swarm/                     # Swarm测试
│   ├── test_swarm.py
│   ├── test_voting.py
│   └── test_instance_manager.py
├── ui_host/                   # UI测试
│   ├── test_renderer.py
│   └── test_components.py
├── integration/               # 集成测试
│   └── test_e2e.py
└── conftest.py                # pytest配置
```

### 测试配置

```python
# tests/conftest.py

import pytest
import asyncio
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

# 异步测试支持
@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# 共享fixtures
@pytest.fixture
def sample_skill():
    from core.skills.types import SkillDefinition, SkillCategory
    return SkillDefinition(
        id="sample",
        name="Sample Skill",
        category=SkillCategory.ANALYSIS,
        description="A sample skill for testing",
        tools=["tool1", "tool2"],
    )

@pytest.fixture
def sample_plugin():
    from core.plugins.types import PluginDefinition, PluginStatus
    return PluginDefinition(
        id="sample_plugin",
        name="Sample Plugin",
        version="1.0.0",
        status=PluginStatus.ACTIVE,
        skills=[],
    )
```

---

## 📊 测试覆盖率

### 覆盖率目标

| 模块类型 | 覆盖率目标 |
|---------|-----------|
| 核心逻辑 | > 90% |
| 工具函数 | > 85% |
| 数据类 | > 75% |
| 集成点 | > 70% |

### 覆盖率报告

```bash
# 生成覆盖率报告
pytest --cov=core --cov-report=html --cov-report=term

# 查看HTML报告
open htmlcov/index.html
```

### 覆盖率配置

```ini
# .coveragerc
[run]
source = core
omit = 
    */tests/*
    */test_*.py
    */__init__.py
    */migrations/*

[report]
precision = 2
show_missing = True
skip_covered = False
```

---

## 🔧 TDD 最佳实践

### 1. 测试命名规范

**好的命名**:
```python
def test_register_skill_with_valid_input()
def test_register_skill_with_duplicate_id_raises_error()
def test_get_skill_returns_none_for_nonexistent_id()
```

### 2. 测试独立性

```python
# 每个测试独立运行
def test_skill_a():
    registry = SkillRegistry()  # 独立实例
    skill = SkillDefinition(id="a", ...)
    registry.register(skill)
    assert registry.get_skill("a") is not None

def test_skill_b():
    registry = SkillRegistry()  # 独立实例
    skill = SkillDefinition(id="b", ...)
    registry.register(skill)
    assert registry.get_skill("b") is not None
```

### 3. 使用Fixture

```python
@pytest.fixture
def skill_registry():
    return SkillRegistry()

def test_with_fixture(skill_registry):
    skill = SkillDefinition(id="test", ...)
    skill_registry.register(skill)
    assert skill_registry.get_skill("test") is not None
```

### 4. 参数化测试

```python
@pytest.mark.parametrize("category,expected_count", [
    (SkillCategory.ANALYSIS, 2),
    (SkillCategory.WRITING, 1),
    (None, 3),
])
def test_list_skills_by_category(category, expected_count):
    registry = SkillRegistry()
    # 注册3个技能...
    skills = registry.list_skills(category=category)
    assert len(skills) == expected_count
```

### 5. 异步测试

```python
@pytest.mark.asyncio
async def test_async_skill_loading():
    loader = SkillLoader()
    skills = await loader.load_from_directory("/path/to/skills")
    assert len(skills) > 0
```

### 6. 异常测试

```python
def test_register_duplicate_skill_raises_error():
    registry = SkillRegistry()
    skill1 = SkillDefinition(id="dup", ...)
    skill2 = SkillDefinition(id="dup", ...)
    
    registry.register(skill1)
    
    with pytest.raises(ValueError, match="Duplicate skill ID"):
        registry.register(skill2)
```

---

## 🚫 反模式 (Anti-Patterns)

### ❌ 不要这样做

1. **不写测试先写代码**
   ```python
   # 错误: 直接实现
   class SkillRegistry:
       def register(self, skill): ...
   
   # 正确: 先写测试
   def test_register_skill(): ...
   ```

2. **测试实现细节而非行为**
   ```python
   # 错误: 测试内部实现
   def test_internal_dict_is_populated():
       registry = SkillRegistry()
       registry.register(skill)
       assert "test_skill" in registry._skills  # 测试内部
   
   # 正确: 测试公共接口
   def test_get_skill_returns_registered_skill():
       registry = SkillRegistry()
       registry.register(skill)
       assert registry.get_skill("test_skill") == skill
   ```

3. **测试过度耦合**
   ```python
   # 错误: 测试依赖其他模块
   def test_skill_integration():
       registry = SkillRegistry()
       tool_registry = ToolRegistry()  # 依赖其他模块
       # ...
   
   # 正确: 使用Mock隔离依赖
   def test_skill_registration():
       registry = SkillRegistry()
       mock_tool = MockTool()
       # ...
   ```

---

## 📝 TDD 检查清单

### 开发前
- [ ] 需求明确
- [ ] 接口设计完成
- [ ] 测试用例列出
- [ ] 测试文件创建

### 开发中
- [ ] 先写测试
- [ ] 运行测试(失败)
- [ ] 实现代码
- [ ] 运行测试(通过)
- [ ] 重构优化
- [ ] 运行测试(仍通过)

### 开发后
- [ ] 所有测试通过
- [ ] 覆盖率达标
- [ ] 代码审查通过
- [ ] 文档完整
- [ ] Git提交

---

## 🎯 TDD 示例：完整流程

### 场景：实现 Plugins 系统

#### 第1轮：Red
```python
# tests/plugins/test_plugin_registry.py

def test_register_plugin():
    registry = PluginRegistry()
    plugin = PluginDefinition(
        id="test_plugin",
        name="Test Plugin",
        version="1.0.0",
    )
    registry.register(plugin)
    
    retrieved = registry.get_plugin("test_plugin")
    assert retrieved.id == "test_plugin"
```

运行: `pytest tests/plugins/test_plugin_registry.py` (❌ 失败)

#### 第2轮：Green
```python
# core/plugins/types.py
@dataclass
class PluginDefinition:
    id: str
    name: str
    version: str
    status: PluginStatus = PluginStatus.ACTIVE

# core/plugins/registry.py
class PluginRegistry:
    def __init__(self):
        self._plugins = {}
    
    def register(self, plugin: PluginDefinition):
        self._plugins[plugin.id] = plugin
    
    def get_plugin(self, plugin_id):
        return self._plugins.get(plugin_id)
```

运行: `pytest tests/plugins/test_plugin_registry.py` (✅ 通过)

#### 第3轮：Refactor
```python
# 重构: 添加类型注解和错误处理
class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, PluginDefinition] = {}
    
    def register(self, plugin: PluginDefinition) -> None:
        if plugin.id in self._plugins:
            raise ValueError(f"Plugin {plugin.id} already registered")
        self._plugins[plugin.id] = plugin
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginDefinition]:
        return self._plugins.get(plugin_id)
```

运行: `pytest tests/plugins/test_plugin_registry.py` (✅ 仍通过)

---

## 📚 参考资源

### 书籍
- 《测试驱动开发的艺术》
- 《Python测试驱动开发》

### 在线资源
- Pytest文档: https://docs.pytest.org/
- TDD实践指南: https://martinfowler.com/bliki/TestDouble.html

---

**作者**: Claude Code
**最后更新**: 2026-04-20
