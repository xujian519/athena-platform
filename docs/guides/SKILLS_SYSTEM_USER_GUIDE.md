# Skills系统使用指南

**版本**: 1.0.0
**更新日期**: 2026-04-21
**适用对象**: Agent开发者、平台管理员

---

## 📚 目录

1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [技能定义](#技能定义)
4. [注册表使用](#注册表使用)
5. [工具映射](#工具映射)
6. [Agent集成](#agent集成)
7. [最佳实践](#最佳实践)
8. [故障排查](#故障排查)

---

## 系统概述

Skills系统是Athena平台的核心扩展机制，允许将Agent能力组织为可重用的技能模块。

### 核心特性

- 🔌 **插件化**: 技能独立于Agent，可动态加载
- 🏗️ **可组合**: 多个技能可组合完成复杂任务
- 🔍 **可发现**: 支持按类别、工具、名称查找技能
- 📊 **可观测**: 提供工具使用统计和依赖分析

### 架构组件

```
┌─────────────────┐
│  SkillLoader    │ ← 从YAML文件加载技能
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ SkillRegistry   │ ← 管理技能注册和查询
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ SkillToolMapper │ ← 管理技能-工具映射
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│     Agent       │ ← 使用技能
└─────────────────┘
```

---

## 快速开始

### 1. 加载内置技能

```python
from core.skills.loader import SkillLoader
from core.skills.registry import SkillRegistry

# 创建加载器
loader = SkillLoader()

# 加载内置技能
skills = loader.load_from_directory("core/skills/bundled")

print(f"✅ 加载了 {len(skills)} 个技能")
# 输出: ✅ 加载了 4 个技能
```

### 2. 查询技能

```python
# 获取注册表
registry = loader.registry

# 按ID获取
patent_skill = registry.get_skill("patent_analysis")
print(patent_skill.name)  # 专利分析技能

# 按类别列出
from core.skills.types import SkillCategory
analysis_skills = registry.list_skills(category=SkillCategory.ANALYSIS)
print(f"分析类技能: {[s.name for s in analysis_skills]}")

# 按工具查找
skills_with_search = registry.get_skills_by_tool("patent_search")
print(f"使用patent_search的技能: {[s.name for s in skills_with_search]}")
```

### 3. 在Agent中使用

```python
from core.agents.base_agent import BaseAgent
from core.skills.registry import get_registry

class XiaonaAgent(BaseAgent):
    def __init__(self):
        super().__init__("小娜")
        self.skill_registry = get_registry()

    def analyze_patent(self, patent_id: str):
        # 获取专利分析技能
        patent_skill = self.skill_registry.get_skill("patent_analysis")

        # 执行技能所需的工具
        results = {}
        for tool_id in patent_skill.tools:
            tool = self.tool_registry.get(tool_id)
            results[tool_id] = tool.execute(patent_id=patent_id)

        return results
```

---

## 技能定义

### YAML格式

技能定义使用YAML格式：

```yaml
id: patent_analysis
name: 专利分析技能
category: analysis
description: 深度分析专利的技术方案、创新点和法律状态
tools:
  - patent_search
  - patent_analyzer
  - case_search
metadata:
  author: Athena平台团队
  version: 1.0.0
  tags:
    - patent
    - analysis
    - legal
  enabled: true
  priority: 9
content: |
  # 专利分析技能

  本技能用于深度分析专利的技术方案、创新点和法律状态。

  ## 功能

  - 技术方案分析
  - 创造性评估
  - 法律状态查询
  - 同族专利检索
  - 引用分析
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 技能唯一标识 |
| `name` | string | ✅ | 技能名称 |
| `category` | string | ✅ | 技能类别：`analysis`/`writing`/`search`/`coordination`/`automation` |
| `description` | string | ✅ | 技能描述 |
| `tools` | list[string] | ❌ | 关联的工具ID列表 |
| `metadata` | object | ❌ | 技能元数据 |
| `content` | string | ❌ | 技能详细说明（Markdown） |

### 元数据字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `author` | string | `null` | 作者 |
| `version` | string | `"1.0.0"` | 版本号 |
| `tags` | list[string] | `[]` | 标签 |
| `enabled` | boolean | `true` | 是否启用 |
| `priority` | integer | `5` | 优先级（1-10） |

---

## 注册表使用

### 基本操作

```python
from core.skills.registry import SkillRegistry
from core.skills.types import SkillDefinition, SkillCategory

# 创建注册表
registry = SkillRegistry()

# 创建技能
skill = SkillDefinition(
    id="my_skill",
    name="我的技能",
    category=SkillCategory.SEARCH,
    description="一个示例技能",
    tools=["tool1", "tool2"],
)

# 注册技能
registry.register(skill)

# 获取技能
retrieved = registry.get_skill("my_skill")
assert retrieved.id == "my_skill"

# 列出所有技能
all_skills = registry.list_skills()

# 按类别筛选
search_skills = registry.list_skills(category=SkillCategory.SEARCH)

# 只列出启用的技能
enabled_skills = registry.list_skills(enabled_only=True)

# 注销技能
registry.unregister("my_skill")
```

### 高级查询

```python
# 按名称模式查找
skills = registry.find_skills(name_pattern="*分析")

# 按类别和名称查找
from core.skills.types import SkillCategory
skills = registry.find_skills(
    name_pattern="专利*",
    category=SkillCategory.ANALYSIS
)

# 获取使用特定工具的技能
skills = registry.get_skills_by_tool("patent_search")

# 获取统计信息
stats = registry.get_stats()
print(f"总技能数: {stats['total_skills']}")
print(f"按类别: {stats['by_category']}")
```

---

## 工具映射

### 基本映射

```python
from core.skills.tool_mapper import SkillToolMapper

# 创建映射器
mapper = SkillToolMapper(registry)

# 获取技能的工具
tools = mapper.get_tools_for_skill("patent_analysis")
# 返回: ["patent_search", "patent_analyzer", "case_search"]

# 获取工具的技能
skills = mapper.get_skills_for_tool("patent_search")
# 返回: [SkillDefinition对象列表]
```

### 冲突检测

```python
# 检测工具版本冲突
conflicts = mapper.detect_tool_conflicts()
for conflict in conflicts:
    print(f"工具 {conflict['tool']} 存在版本冲突:")
    print(f"  技能: {conflict['skills']}")
    print(f"  版本: {conflict['versions']}")
```

### 依赖分析

```python
# 检测技能依赖关系
dependencies = mapper.detect_tool_dependencies()
for skill_id, deps in dependencies.items():
    print(f"{skill_id} 依赖于: {deps}")
```

### 使用统计

```python
# 获取工具使用统计
stats = mapper.get_tool_usage_stats()
for tool_id, stat in stats.items():
    print(f"{tool_id}: 被 {stat['count']} 个技能使用")
    print(f"  技能: {stat['skill_ids']}")
```

### 未使用工具

```python
# 查找未使用的工具
all_tools = ["tool1", "tool2", "tool3", "tool4"]
unused = mapper.find_unused_tools(all_tools)
print(f"未使用的工具: {unused}")
```

---

## Agent集成

### 集成方式1：直接使用注册表

```python
from core.agents.base_agent import BaseAgent
from core.skills.registry import get_registry

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__("MyAgent")
        self.skill_registry = get_registry()

    def process_with_skill(self, skill_id: str, **kwargs):
        # 获取技能
        skill = self.skill_registry.get_skill(skill_id)
        if not skill:
            raise ValueError(f"技能不存在: {skill_id}")

        # 执行技能的工具
        results = {}
        for tool_id in skill.tools:
            tool = self.tool_registry.get(tool_id)
            if tool:
                results[tool_id] = tool.execute(**kwargs)

        return results
```

### 集成方式2：技能选择器

```python
from core.skills.registry import get_registry
from core.skills.types import SkillCategory

class SmartAgent(BaseAgent):
    def __init__(self):
        super().__init__("SmartAgent")
        self.skill_registry = get_registry()
        self.tool_mapper = SkillToolMapper(self.skill_registry)

    def auto_select_skill(self, task_description: str) -> str:
        """根据任务描述自动选择技能"""
        # 简单示例：基于关键词匹配
        if "专利" in task_description and "分析" in task_description:
            return "patent_analysis"
        elif "案例" in task_description and "检索" in task_description:
            return "case_retrieval"
        elif "文书" in task_description:
            return "document_writing"
        else:
            return "task_coordination"

    def process(self, task: str):
        # 自动选择技能
        skill_id = self.auto_select_skill(task)
        return self.process_with_skill(skill_id, task=task)
```

### 集成方式3：多技能组合

```python
class AdvancedAgent(BaseAgent):
    def __init__(self):
        super().__init__("AdvancedAgent")
        self.skill_registry = get_registry()
        self.tool_mapper = SkillToolMapper(self.skill_registry)

    def compose_skills(self, skill_ids: list[str]):
        """组合多个技能"""
        # 检查技能冲突
        for skill_id in skill_ids:
            skill = self.skill_registry.get_skill(skill_id)
            if not skill:
                raise ValueError(f"技能不存在: {skill_id}")

        # 检查工具冲突
        conflicts = self.tool_mapper.detect_tool_conflicts()
        if conflicts:
            logger.warning(f"发现工具冲突: {conflicts}")

        return skill_ids

    def execute_workflow(self, skill_ids: list[str], **kwargs):
        """执行技能工作流"""
        results = {}
        for skill_id in skill_ids:
            result = self.process_with_skill(skill_id, **kwargs)
            results[skill_id] = result

        return results
```

---

## 最佳实践

### 1. 技能设计原则

- **单一职责**: 每个技能只做一件事
- **高内聚**: 技能内的工具应该紧密相关
- **低耦合**: 技能之间应该尽量独立

### 2. 工具选择

- 只包含必需的工具
- 避免工具版本冲突
- 使用标准化的工具ID

### 3. 元数据填写

- `author`: 标明作者便于维护
- `version`: 使用语义化版本号
- `tags`: 使用一致的标签体系
- `priority`: 设置合理的优先级

### 4. 错误处理

```python
try:
    skill = registry.get_skill("nonexistent")
    if skill is None:
        logger.error("技能不存在")
        return None
except Exception as e:
    logger.error(f"加载技能失败: {e}")
    return None
```

### 5. 性能优化

```python
# 使用缓存避免重复映射
mapper = SkillToolMapper(registry)
mapping = mapper.map_tools_to_skills()  # 第一次调用会缓存

# 注册表变更后清除缓存
mapper.invalidate_cache()
```

---

## 故障排查

### 问题1：技能加载失败

**症状**: `FileNotFoundError` 或 `ValueError`

**原因**:
- YAML文件路径错误
- YAML格式错误
- 缺少必需字段

**解决**:
```python
# 检查文件是否存在
from pathlib import Path
file_path = Path("core/skills/bundled/patent_analysis.yaml")
print(file_path.exists())

# 验证YAML格式
import yaml
with open(file_path) as f:
    data = yaml.safe_load(f)
    print(data)
```

### 问题2：工具冲突

**症状**: 多个技能使用同一工具的不同版本

**解决**:
```python
# 检测冲突
mapper = SkillToolMapper(registry)
conflicts = mapper.detect_tool_conflicts()

# 统一工具版本
for conflict in conflicts:
    print(f"冲突: {conflict['tool']}")
    print(f"  需要统一版本: {conflict['versions']}")
```

### 问题3：技能未启用

**症状**: `list_skills(enabled_only=True)` 返回空列表

**解决**:
```python
# 检查技能元数据
skill = registry.get_skill("my_skill")
print(f"启用状态: {skill.is_enabled()}")

# 启用技能
skill.metadata.enabled = True
```

### 问题4：循环依赖

**症状**: 技能A依赖B，B依赖A

**解决**:
```python
# 检测循环依赖
deps = mapper.detect_tool_dependencies()

# 重构技能，消除循环
# 例如：将共同依赖提取到新技能
```

---

## API参考

### SkillRegistry

| 方法 | 说明 |
|------|------|
| `register(skill)` | 注册技能 |
| `get_skill(skill_id)` | 获取技能 |
| `unregister(skill_id)` | 注销技能 |
| `list_skills(category, enabled_only)` | 列出技能 |
| `find_skills(name_pattern, category)` | 查找技能 |
| `get_skills_by_tool(tool_id)` | 按工具获取技能 |
| `get_stats()` | 获取统计信息 |

### SkillLoader

| 方法 | 说明 |
|------|------|
| `load_from_file(file_path)` | 从文件加载 |
| `load_from_directory(directory, recursive, register)` | 从目录加载 |

### SkillToolMapper

| 方法 | 说明 |
|------|------|
| `map_tools_to_skills()` | 映射工具到技能 |
| `get_tools_for_skill(skill_id)` | 获取技能的工具 |
| `get_skills_for_tool(tool_id)` | 获取工具的技能 |
| `detect_tool_conflicts()` | 检测工具冲突 |
| `detect_tool_dependencies()` | 检测工具依赖 |
| `get_tool_usage_stats()` | 获取使用统计 |
| `find_unused_tools(all_tools)` | 查找未使用工具 |

---

**作者**: Athena平台团队
**最后更新**: 2026-04-21
