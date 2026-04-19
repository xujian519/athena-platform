# 工具注册表迁移 - 快速参考指南

**版本**: v1.0
**更新时间**: 2026-04-19
**负责人**: Agent 4 🔄 迁移专家

---

## 🚀 快速启动

### 前置条件检查

```bash
# 1. 检查Agent 3是否完成核心实现
ls -l core/tools/centralized_registry.py
ls -l core/tools/decorators.py
ls -l core/tools/discovery.py
ls -l core/tools/lifecycle.py

# 2. 如果所有文件存在，则可以开始迁移
# 3. 如果文件不存在，继续等待Agent 3完成
```

### 迁移执行命令

```bash
# 阶段1: 核心工具迁移（手动执行，见详细计划）
# 阶段2: 分析工具迁移（手动执行，见详细计划）
# 阶段3: 外部服务迁移（手动执行，见详细计划）
# 阶段4: 智能体更新（手动执行，见详细计划）

# 阶段5: 导入路径迁移（自动化）
cd /Users/xujian/Athena工作平台
python3 scripts/migrate_registry_imports.py --dry-run  # 预览
python3 scripts/migrate_registry_imports.py            # 执行
python3 scripts/migrate_registry_imports.py --verify   # 验证

# 阶段6: 验证和测试（自动化）
python3 scripts/verify_migration.py --all
```

---

## 📊 工具清单速查

### P0: 核心工具（19个）- 必须迁移

**专利检索（8个）**:
- `patent_retrieval` - 专利检索引擎
- `patent_download` - 专利PDF下载
- `patent_search_cn` - 中国专利搜索
- `patent_search_us` - 美国专利搜索
- `patent_parser` - 专利文档解析
- `patent_claim_analyzer` - 权利要求分析
- `patent_fee_manager` - 专利费用管理
- `patent_statistics` - 专利统计分析

**学术搜索（5个）**:
- `scholar_search` - Google学术搜索
- `semantic_scholar` - Semantic Scholar
- `arxiv_search` - arXiv论文搜索
- `pubmed_search` - PubMed文献搜索
- `citation_analyzer` - 引文分析器

**向量搜索（6个）**:
- `bge_m3_embedder` - BGE-M3嵌入服务
- `qdrant_search` - Qdrant向量检索
- `similarity_search` - 相似度搜索
- `hybrid_search` - 混合检索
- `vector_store` - 向量存储管理
- `semantic_search` - 语义搜索

### P1: 分析工具（26个）- 重要

**文档处理（12个）**:
- `pdf_parser`, `docx_parser`, `html_parser`, `markdown_parser`
- `document_converter`, `text_extractor`, `metadata_extractor`
- `table_extractor`, `image_extractor`, `chunking_tool`
- `summarization_tool`, `translation_tool`

**法律分析（9个）**:
- `legal_analyzer`, `patent_infringement`, `claim_interpretation`
- `prior_art_search`, `legal_knowledge_graph`, `case_law_search`
- `statute_analyzer`, `legal_doc_generator`, `inventive_step`

**语义分析（5个）**:
- `sentiment_analyzer`, `entity_extractor`, `relation_extractor`
- `topic_modeler`, `text_classifier`

### P2: 服务工具（11个）- 次要

**MCP服务（7个）**:
- `gaode_maps`, `academic_search_mcp`, `jina_ai_search`
- `jina_ai_embedding`, `jina_ai_rerank`, `memory_graph`, `local_search`

**Web搜索（4个）**:
- `web_search`, `web_scraper`, `web_monitor`, `browser_automation`

---

## 🔧 工具注册模板

### 标准工具注册

```python
from core.tools.decorators import register_tool
from core.tools.base import ToolCategory, ToolPriority

@register_tool(
    tool_id="your_tool_id",
    name="工具名称",
    description="工具描述",
    category=ToolCategory.PATENT_SEARCH,
    priority=ToolPriority.HIGH,
    domains=["patent", "legal"],
    task_types=["search", "analysis"]
)
async def your_tool_handler(params: dict, context: dict) -> dict:
    """
    工具处理函数

    Args:
        params: 参数字典
        context: 上下文字典

    Returns:
        结果字典
    """
    # 实现你的工具逻辑
    result = {"status": "success", "data": {}}
    return result
```

### 带配置的工具注册

```python
@register_tool(
    tool_id="configurable_tool",
    name="可配置工具",
    category=ToolCategory.API_INTEGRATION,
    config={
        "api_key": "your_api_key",
        "timeout": 30,
        "max_retries": 3
    },
    required_params=["query"],
    optional_params=["limit", "offset"]
)
async def configurable_tool_handler(params, context):
    # 实现逻辑
    pass
```

---

## 📝 智能体集成模板

### 获取工具的方式

```python
# 旧方式（将被替换）
from core.tools.tool_manager import get_tool_manager
tools = get_tool_manager().get_tools()

# 新方式（使用新注册表）
from core.tools.centralized_registry import get_centralized_registry

def get_available_tools(self):
    """获取智能体可用的工具"""
    registry = get_centralized_registry()

    # 按领域查找工具
    tools = registry.find_by_domain("patent")

    # 或按分类查找
    # tools = registry.find_by_category(ToolCategory.PATENT_SEARCH)

    return [t for t in tools if t.enabled]
```

### 调用工具的方式

```python
async def use_tool(self, tool_id: str, params: dict):
    """调用工具"""
    from core.tools.centralized_registry import get_centralized_registry

    registry = get_centralized_registry()
    tool = registry.get_tool(tool_id)

    if not tool:
        raise ValueError(f"工具不存在: {tool_id}")

    if not tool.enabled:
        raise ValueError(f"工具未启用: {tool_id}")

    # 调用工具处理函数
    result = await tool.handler(params, context=self.context)

    # 更新性能指标
    execution_time = time.time() - start_time
    registry.update_tool_performance(
        tool_id,
        execution_time,
        success=True
    )

    return result
```

---

## ⚠️ 常见问题和解决方案

### 问题1: 循环导入错误

**症状**:
```
ImportError: cannot import name 'get_centralized_registry' from partially initialized module
```

**解决方案**:
```python
# ❌ 错误：模块级别导入
from core.tools.centralized_registry import get_centralized_registry

# ✅ 正确：函数级别导入
def get_tool(tool_id: str):
    from core.tools.centralized_registry import get_centralized_registry
    return get_centralized_registry().get_tool(tool_id)
```

### 问题2: 工具注册失败

**症状**:
```
ValueError: tool_id already registered
```

**解决方案**:
```python
# 检查工具是否已注册
from core.tools.centralized_registry import get_centralized_registry

registry = get_centralized_registry()
existing_tool = registry.get_tool("your_tool_id")

if existing_tool:
    # 工具已存在，更新而不是重新注册
    existing_tool.enabled = True
else:
    # 工具不存在，执行注册
    @register_tool(...)
    async def your_tool_handler(params, context):
        pass
```

### 问题3: 工具调用超时

**症状**:
```
TimeoutError: Tool execution timed out
```

**解决方案**:
```python
# 增加超时时间
@register_tool(
    tool_id="slow_tool",
    timeout=60.0,  # 增加到60秒
    max_retries=2
)
async def slow_tool_handler(params, context):
    # 实现逻辑
    pass
```

---

## 📈 性能优化技巧

### 1. 使用LRU缓存

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_expensive_resource(key):
    # 缓存昂贵的资源
    return expensive_operation(key)
```

### 2. 批量操作

```python
# ❌ 低效：逐个处理
for item in items:
    result = await process_item(item)

# ✅ 高效：批量处理
results = await process_batch(items)
```

### 3. 异步并发

```python
import asyncio

# ❌ 低效：串行执行
for tool_id in tool_ids:
    result = await call_tool(tool_id, params)

# ✅ 高效：并发执行
tasks = [call_tool(tid, params) for tid in tool_ids]
results = await asyncio.gather(*tasks)
```

---

## 🧪 测试命令速查

### 单元测试

```bash
# 测试工具注册
pytest tests/core/tools/test_registry.py -v

# 测试特定工具
pytest tests/core/tools/test_patent_tools.py -v

# 测试智能体集成
pytest tests/core/agents/test_xiaona_tools.py -v
```

### 集成测试

```bash
# 测试端到端流程
pytest tests/integration/test_tool_workflow.py -v

# 测试MCP服务集成
pytest tests/integration/test_mcp_integration.py -v
```

### 性能测试

```bash
# 运行性能基准
python3 scripts/verify_migration.py --check-performance

# 压力测试
pytest tests/performance/test_tool_stress.py -v
```

---

## 📚 文档索引

### 详细文档

1. **准备工作报告** (`agent-4-preparation-report.md`)
   - 工具生态系统分析
   - 迁移策略
   - 潜在问题和缓解措施

2. **工具分类清单** (`tool-inventory.md`)
   - 252个工具的详细分类
   - 工具依赖关系图
   - 迁移检查清单

3. **详细迁移计划** (`migration-plan.md`)
   - 6阶段详细时间表
   - 每个任务的具体步骤
   - 验收标准

4. **最终准备报告** (`agent-4-final-report.md`)
   - 执行摘要
   - 核心发现
   - 交付物总结

### API文档

1. **工具注册表API** (`docs/api/TOOL_REGISTRY_API.md`)
2. **工具管理API** (`docs/api/TOOL_MANAGER_API.md`)
3. **权限系统API** (`docs/api/PERMISSION_SYSTEM_API.md`)

### 开发指南

1. **工具系统指南** (`docs/guides/TOOL_SYSTEM_GUIDE.md`)
2. **迁移指南** (`docs/guides/TOOL_MIGRATION_GUIDE.md`)
3. **测试指南** (`docs/guides/TESTING_GUIDE.md`)

---

## 🎯 检查清单

### 迁移前检查

- [ ] Agent 3核心实现已完成
- [ ] 所有依赖文件存在
- [ ] 测试环境已准备
- [ ] 备份已完成
- [ ] 迁移计划已审阅

### 迁移中检查

- [ ] 每个工具已注册
- [ ] 单元测试通过
- [ ] 无循环导入
- [ ] 性能基准达标
- [ ] 文档已更新

### 迁移后检查

- [ ] 所有工具可调用
- [ ] 智能体集成正常
- [ ] 端到端测试通过
- [ ] 性能无回归
- [ ] 用户验收通过

---

## 📞 紧急联系

**技术问题**: Agent 4（迁移专家）
**测试问题**: Agent 5（测试专家）
**架构问题**: Agent 3（核心架构师）
**项目协调**: 项目负责人

---

**快速参考版本**: v1.0
**最后更新**: 2026-04-19
**维护者**: Agent 4 🔄 迁移专家
