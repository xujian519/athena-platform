# 阶段4&5执行计划 - 向后兼容与优化

> **准备时间**: 2026-04-23 16:35
> **依赖**: 阶段3完成（unified_patent_writer.py创建完毕）

---

## 🎯 阶段4+5总目标

**阶段4**: 实现向后兼容
- 创建适配器
- 更新配置文件
- 验证兼容性

**阶段5**: 清理和优化
- 移除重复代码
- 性能优化
- 文档更新
- 质量检查

---

## 📋 阶段4详细计划

### 任务1: 创建WriterAgent适配器

**目标**: 修改`writer_agent.py`为适配器，内部调用`UnifiedPatentWriter`

**实现**:
```python
class WriterAgent(BaseXiaonaComponent):
    """
    WriterAgent适配器 - 向后兼容
    
    实际调用UnifiedPatentWriter
    """
    
    def __init__(self, agent_id: str = "writer_agent"):
        super().__init__(agent_id)
        # 内部使用统一代理
        self._unified_writer = None
    
    def _get_unified_writer(self):
        """延迟加载统一代理"""
        if self._unified_writer is None:
            from core.agents.xiaona.unified_patent_writer import UnifiedPatentWriter
            self._unified_writer = UnifiedPatentWriter()
        return self._unified_writer
    
    async def execute(self, context):
        """执行任务 - 路由到统一代理"""
        unified_writer = self._get_unified_writer()
        
        # 映射旧任务类型到新任务类型
        task_mapping = {
            "claims": "draft_claims",
            "description": "draft_specification",
            "office_action_response": "draft_office_action_response",
            "invalidation": "draft_invalidation_petition",
        }
        
        old_type = context.config.get("writing_type")
        new_type = task_mapping.get(old_type, old_type)
        
        # 更新context
        context.config["task_type"] = new_type
        
        # 调用统一代理
        return await unified_writer.execute(context)
```

**验证**:
- 旧代码调用WriterAgent成功
- 输出格式一致
- 所有原有测试通过

### 任务2: 创建PatentDraftingProxy适配器

**目标**: 修改`patent_drafting_proxy.py`为适配器

**实现**:
```python
class PatentDraftingProxy(BaseXiaonaComponent):
    """
    PatentDraftingProxy适配器 - 向后兼容
    
    实际调用UnifiedPatentWriter
    """
    
    def __init__(self, agent_id: str = "patent_drafting_proxy"):
        super().__init__(agent_id)
        self._unified_writer = None
    
    def _get_unified_writer(self):
        """延迟加载统一代理"""
        if self._unified_writer is None:
            from core.agents.xiaona.unified_patent_writer import UnifiedPatentWriter
            self._unified_writer = UnifiedPatentWriter()
        return self._unified_writer
    
    async def execute(self, context):
        """执行任务 - 直接转发到统一代理"""
        unified_writer = self._get_unified_writer()
        return await unified_writer.execute(context)
    
    # 保留原有方法签名（向后兼容）
    async def analyze_disclosure(self, disclosure_data):
        """分析技术交底书 - 向后兼容接口"""
        from core.agents.xiaona.base_component import AgentExecutionContext
        context = AgentExecutionContext(
            task_id="compatibility",
            config={"task_type": "analyze_disclosure"},
            input_data=disclosure_data
        )
        result = await self._get_unified_writer().execute(context)
        return result.output_data
    
    # ... 其他6个方法类似处理
```

**验证**:
- 旧代码调用PatentDraftingProxy成功
- 所有7个方法可调用
- 输出格式一致

### 任务3: 更新agent_registry.json

**修改**:
```json
{
  "agents": {
    "xiaona": {
      "sub_agents": [
        "RetrieverAgent",
        "AnalyzerAgent",
        "UnifiedPatentWriter",        // 新增
        "NoveltyAnalyzerProxy",
        "CreativityAnalyzerProxy",
        "InfringementAnalyzerProxy",
        "InvalidationAnalyzerProxy",
        "ApplicationReviewerProxy",
        "WritingReviewerProxy"
      ],
      "deprecated": [
        {
          "name": "WriterAgent",
          "replacement": "UnifiedPatentWriter",
          "version": "2.0.0",
          "note": "请使用UnifiedPatentWriter"
        },
        {
          "name": "PatentDraftingProxy",
          "replacement": "UnifiedPatentWriter",
          "version": "2.0.0",
          "note": "请使用UnifiedPatentWriter"
        }
      ]
    }
  }
}
```

**验证**:
- JSON格式正确
- 配置可加载
- 新代理可被发现

---

## 📋 阶段5详细计划

### 任务1: 移除重复代码

**目标**: 从适配器中移除重复的实现代码

**操作**:
- WriterAgent适配器: 保留路由逻辑，移除旧实现
- PatentDraftingProxy适配器: 保留方法签名，移除实现
- 代码行数减少~200行

**验证**:
- 适配器文件<100行
- 无重复逻辑
- 功能保持不变

### 任务2: 性能优化和基准测试

**基准测试**:
```python
# tests/performance/test_unified_writer_performance.py

async def test_performance_comparison():
    """对比新旧版本性能"""
    import time
    
    # 测试数据
    test_data = {...}
    
    # 测试旧版本
    start = time.time()
    old_result = await old_agent.execute(test_data)
    old_time = time.time() - start
    
    # 测试新版本
    start = time.time()
    new_result = await new_agent.execute(test_data)
    new_time = time.time() - start
    
    # 断言性能不下降
    assert new_time <= old_time * 1.05  # 允许5%误差
```

**优化点**:
- 模块延迟加载
- LLM调用缓存
- 结果缓存

**验证**:
- 性能不下降（±5%）
- 无明显瓶颈

### 任务3: 更新文档

**需要更新的文档**:

1. **CLAUDE.md**
   - 10个代理 → 9个代理
   - 更新代理列表表格
   - 添加UnifiedPatentWriter说明
   - 更新架构图

2. **docs/architecture/XIAONA_SPECIALIZED_AGENTS_ARCHITECTURE.md**
   - 添加合并说明章节
   - 更新代理列表
   - 添加使用示例

3. **创建迁移指南**
   - `docs/guides/UNIFIED_WRITER_MIGRATION_GUIDE.md`
   - 说明如何从旧代理迁移到新代理
   - 提供代码示例

**验证**:
- 所有文档更新
- 示例代码可运行
- 迁移指南清晰

### 任务4: 代码审查和质量检查

**质量检查**:

```bash
# 1. 代码格式化
black core/agents/xiaona/unified_patent_writer.py --line-length 100

# 2. Linting
ruff check core/agents/xiaona/unified_patent_writer.py
ruff check core/agents/xiaona/writer_agent.py
ruff check core/agents/xiaona/patent_drafting_proxy.py

# 3. 类型检查
mypy core/agents/xiaona/unified_patent_writer.py
mypy core/agents/xiaona/writer_agent.py
mypy core/agents/xiaona/patent_drafting_proxy.py

# 4. 测试
pytest tests/agents/xiaona/test_unified_writer*.py -v
pytest tests/agents/xiaona/test_unified_patent_writer.py -v

# 5. 测试覆盖率
pytest --cov=core/agents/xiaona --cov-report=html
```

**质量标准**:
- ✅ 无ruff错误
- ✅ 无mypy错误
- ✅ 测试覆盖率>80%
- ✅ 所有测试通过

---

## 👥 团队配置（阶段4+5）

### 阶段4团队成员（3个）

| 成员 | 角色 | 任务 | 预计时间 |
|------|------|------|---------|
| adapter-builder | 适配器构建师 | 创建2个适配器 | 45分钟 |
| config-updater | 配置更新专家 | 更新agent_registry.json | 15分钟 |
| compatibility-tester | 兼容性测试专家 | 验证向后兼容 | 30分钟 |

### 阶段5团队成员（4个）

| 成员 | 角色 | 任务 | 预计时间 |
|------|------|------|---------|
| code-cleaner | 代码清理专家 | 移除重复代码 | 30分钟 |
| performance-tuner | 性能优化专家 | 基准测试和优化 | 45分钟 |
| documentation-writer | 文档更新专家 | 更新所有文档 | 45分钟 |
| quality-checker | 质量检查专家 | 代码审查和测试 | 30分钟 |

---

## ⏱️ 时间估算

### 阶段4
| 任务 | 时间 |
|------|------|
| 创建WriterAgent适配器 | 20分钟 |
| 创建PatentDraftingProxy适配器 | 25分钟 |
| 更新agent_registry.json | 10分钟 |
| 兼容性测试 | 30分钟 |
| **总计** | **85分钟** |

### 阶段5
| 任务 | 时间 |
|------|------|
| 移除重复代码 | 30分钟 |
| 性能优化和基准测试 | 45分钟 |
| 更新文档 | 45分钟 |
| 代码审查和质量检查 | 30分钟 |
| **总计** | **150分钟** |

### 阶段4+5合计
**总计时间**: 约4小时

---

## ✅ 完成标准

### 功能完整性
- [ ] 所有9个代理可用
- [ ] 向后兼容性保持
- [ ] 所有测试通过

### 代码质量
- [ ] 无ruff错误
- [ ] 无mypy错误
- [ ] 测试覆盖率>80%

### 文档完整性
- [ ] CLAUDE.md更新
- [ ] 架构文档更新
- [ ] 迁移指南提供

### 性能标准
- [ ] 性能不下降
- [ ] 内存使用合理
- [ ] 无明显瓶颈

---

## 🚀 启动指令

### 阶段4启动（阶段3完成后）

```python
# Spawn 3个teammates
Agent(name="adapter-builder", ...)
Agent(name="config-updater", ...)
Agent(name="compatibility-tester", ...)
```

### 阶段5启动（阶段4完成后）

```python
# Spawn 4个teammates
Agent(name="code-cleaner", ...)
Agent(name="performance-tuner", ...)
Agent(name="documentation-writer", ...)
Agent(name="quality-checker", ...)
```

---

## 📊 完整时间表

| 阶段 | 任务 | 时间 | 累计时间 |
|------|------|------|---------|
| 阶段1 | 准备阶段 | 10分钟 | 0:10 |
| 阶段2 | 模块拆分 | 2小时 | 2:10 |
| 阶段3 | 统一入口 | 1.5小时 | 3:40 |
| 阶段4 | 向后兼容 | 1.5小时 | 5:10 |
| 阶段5 | 清理优化 | 2.5小时 | 7:40 |

**总计**: 约7小时40分钟

考虑到并行执行和优化，实际预计时间：**约5-6小时**

---

**准备就绪**: 等待阶段3完成通知
**预计完成**: T0 + 4小时
