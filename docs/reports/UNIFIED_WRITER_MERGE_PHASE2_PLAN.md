# 阶段2执行计划 - 模块拆分

> **准备时间**: 2026-04-23
> **依赖**: 阶段1完成（目录结构、备份、测试用例）

---

## 🎯 阶段2目标

将PatentDraftingProxy和WriterAgent的功能拆分为4个独立模块：
1. **drafting_module.py** - 专利申请撰写（7个能力）
2. **response_module.py** - 答复撰写（2个能力）
3. **orchestration_module.py** - 流程编排（2个能力）
4. **utility_module.py** - 辅助工具（3个能力）

---

## 👥 团队配置

### 新增Teammates

| 成员 | 角色 | 颜色 | 任务 |
|------|------|------|------|
| drafting-extractor | 撰写逻辑提取专家 | 🔵 蓝色 | 从PatentDraftingProxy提取7个方法 |
| response-extractor | 答复逻辑提取专家 | 🟢 绿色 | 从WriterAgent提取2个方法 |
| orchestration-builder | 编排模块构建师 | 🟡 黄色 | 创建流程编排模块 |
| utility-builder | 工具模块构建师 | 🟣 紫色 | 创建辅助工具模块 |

---

## 📋 任务分配

### 任务1: drafting-extractor（撰写逻辑提取）

**输入**:
- 源文件: `core/agents/xiaona/patent_drafting_proxy.py` (1907行)
- 目标文件: `core/agents/xiaona/modules/drafting_module.py`

**需要提取的方法**:
1. `analyze_disclosure()` + `_analyze_disclosure_by_rules()` + 辅助方法
2. `assess_patentability()` + 辅助方法
3. `draft_specification()` + 辅助方法
4. `draft_claims()` + 辅助方法
5. `optimize_protection_scope()` + 辅助方法
6. `review_adequacy()` + 辅助方法
7. `detect_common_errors()` + 辅助方法

**提取步骤**:
1. 分析PatentDraftingProxy的依赖
2. 提取核心方法实现
3. 提取私有辅助方法
4. 保留LLM调用逻辑
5. 保留提示词系统
6. 创建PatentDraftingModule类

**验证**:
- 运行测试: `pytest tests/agents/xiaona/test_unified_writer_migration.py::test_patent_drafting_*`
- 确保所有7个方法可调用
- 与原始PatentDraftingProxy行为一致

---

### 任务2: response-extractor（答复逻辑提取）

**输入**:
- 源文件: `core/agents/xiaona/writer_agent.py` (516行)
- 目标文件: `core/agents/xiaona/modules/response_module.py`

**需要提取的方法**:
1. `_draft_response()` - 审查意见答复
2. `_draft_invalidation()` - 无效宣告请求书

**提取步骤**:
1. 分析WriterAgent的依赖
2. 提取核心方法实现
3. 保留LLM调用逻辑
4. 保留系统提示词
5. 创建ResponseModule类

**验证**:
- 运行测试: `pytest tests/agents/xiaona/test_unified_writer_migration.py::test_writer_agent_*`
- 确保所有2个方法可调用
- 与原始WriterAgent行为一致

---

### 任务3: orchestration-builder（编排模块构建）

**输入**:
- 目标文件: `core/agents/xiaona/modules/orchestration_module.py`
- 依赖: drafting_module, response_module

**需要实现的方法**:
1. `draft_full_application()` - 完整申请流程
   - 调用drafting_module.analyze_disclosure()
   - 调用drafting_module.assess_patentability()
   - 调用drafting_module.draft_claims()
   - 调用drafting_module.draft_specification()
   - 调用drafting_module.review_adequacy()
   - 调用drafting_module.detect_common_errors()
   - 返回完整结果

2. `orchestrate_response()` - 答复流程编排
   - 调用retriever（如需要）
   - 调用analyzer（如需要）
   - 调用response_module.draft_office_action_response()
   - 返回完整结果

**实现步骤**:
1. 创建OrchestrationModule类
2. 实现流程编排逻辑
3. 添加错误处理
4. 添加进度跟踪
5. 编写测试

**验证**:
- 流程编排测试通过
- 各步骤正确调用
- 错误处理正确

---

### 任务4: utility-builder（工具模块构建）

**输入**:
- 目标文件: `core/agents/xiaona/modules/utility_module.py`

**需要实现的方法**:
1. `format_document()` - 文档格式化
   - 输入: document_type, content
   - 输出: 格式化的文档字符串
   - 支持: claims, specification, response, petition

2. `calculate_quality_score()` - 质量评分
   - 输入: document_content, review_result
   - 输出: quality_score (0-100)
   - 评分维度: 完整性、规范性、逻辑性

3. `compare_versions()` - 版本对比
   - 输入: version1, version2
   - 输出: diff_report
   - 对比维度: 新增、删除、修改

**实现步骤**:
1. 创建UtilityModule类
2. 实现格式化逻辑
3. 实现评分算法
4. 实现对比算法
5. 编写测试

**验证**:
- 所有工具方法测试通过
- 输出格式正确

---

## 🔄 并行执行策略

### 第1轮并行（4个任务同时进行）

```
时间: T0 → T0+2小时
┌─────────────────────┐
│ drafting-extractor  │ → 提取PatentDraftingProxy (预计90分钟)
├─────────────────────┤
│ response-extractor  │ → 提取WriterAgent (预计60分钟)
├─────────────────────┤
│orchestration-builder│ → 构建编排模块 (预计90分钟)
├─────────────────────┤
│  utility-builder    │ → 构建工具模块 (预计60分钟)
└─────────────────────┘
```

### 第2轮验证（串行）

```
时间: T0+2小时 → T0+3小时
1. drafting-extractor 验证 (15分钟)
2. response-extractor 验证 (15分钟)
3. orchestration-builder 验证 (15分钟)
4. utility-builder 验证 (15分钟)
```

---

## 📊 完成标准

### drafting-extractor
- [ ] drafting_module.py创建成功
- [ ] 7个方法完整迁移
- [ ] 所有测试通过
- [ ] 与原始行为一致

### response-extractor
- [ ] response_module.py创建成功
- [ ] 2个方法完整迁移
- [ ] 所有测试通过
- [ ] 与原始行为一致

### orchestration-builder
- [ ] orchestration_module.py创建成功
- [ ] 2个编排方法实现
- [ ] 流程测试通过
- [ ] 错误处理正确

### utility-builder
- [ ] utility_module.py创建成功
- [ ] 3个工具方法实现
- [ ] 所有测试通过
- [ ] 输出格式正确

---

## ⚠️ 风险和缓解

### 风险1: 依赖复杂
**风险**: PatentDraftingProxy有复杂的内部依赖
**缓解**:
- 先分析依赖图
- 按依赖顺序提取
- 保留所有辅助方法

### 风险2: 测试失败
**风险**: 提取后测试不通过
**缓解**:
- 先运行测试建立基准
- 逐个方法验证
- 保留原有行为

### 风险3: 并行冲突
**风险**: 4个teammates可能产生冲突
**缓解**:
- 独立文件，无冲突
- 统一代码风格
- 最后统一验证

---

## 🚀 启动指令

**条件**: 阶段1全部完成

**启动命令**:
```python
# Spawn 4个teammates
Agent(
    subagent_type="general-purpose",
    name="drafting-extractor",
    description="提取PatentDraftingProxy撰写逻辑",
    team_name="unified-writer-merge",
    prompt="..."
)

Agent(
    subagent_type="general-purpose",
    name="response-extractor",
    description="提取WriterAgent答复逻辑",
    team_name="unified-writer-merge",
    prompt="..."
)

Agent(
    subagent_type="general-purpose",
    name="orchestration-builder",
    description="构建流程编排模块",
    team_name="unified-writer-merge",
    prompt="..."
)

Agent(
    subagent_type="general-purpose",
    name="utility-builder",
    description="构建辅助工具模块",
    team_name="unified-writer-merge",
    prompt="..."
)
```

---

**准备就绪**: 等待阶段1完成通知
**预计完成**: T0 + 3小时
