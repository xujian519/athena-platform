# 统一撰写代理合并项目 - 检查清单

> **用途**: 确保每个阶段的质量和完整性
> **更新频率**: 每完成一个任务更新一次

---

## ✅ 阶段1：准备阶段检查清单

### 1.1 目录结构创建

- [ ] **modules目录存在**
  - [ ] 路径: `/Users/xujian/Athena工作平台/core/agents/xiaona/modules/`
  - [ ] 权限: rwxr-xr-x
  - [ ] 包含: `.gitkeep`（如果为空）

- [ ] **__init__.py 创建**
  - [ ] 文件存在
  - [ ] 包含模块docstring
  - [ ] 导出所有模块类
  - [ ] 版本信息: `__version__ = "1.0.0"`

- [ ] **drafting_module.py 创建**
  - [ ] 文件存在
  - [ ] 包含`PatentDraftingModule`类定义
  - [ ] 继承自`object`
  - [ ] 包含TODO注释列出7个能力
  - [ ] Docstring说明：专利申请撰写模块

- [ ] **response_module.py 创建**
  - [ ] 文件存在
  - [ ] 包含`ResponseModule`类定义
  - [ ] 继承自`object`
  - [ ] 包含TODO注释列出2个能力
  - [ ] Docstring说明：答复撰写模块

- [ ] **orchestration_module.py 创建**
  - [ ] 文件存在
  - [ ] 包含`OrchestrationModule`类定义
  - [ ] 继承自`object`
  - [ ] 包含TODO注释列出2个能力
  - [ ] Docstring说明：流程编排模块

- [ ] **utility_module.py 创建**
  - [ ] 文件存在
  - [ ] 包含`UtilityModule`类定义
  - [ ] 继承自`object`
  - [ ] 包含TODO注释列出3个能力
  - [ ] Docstring说明：辅助工具模块

### 1.2 文件备份

- [ ] **writer_agent.py.backup 创建**
  - [ ] 备份文件存在
  - [ ] 原文件行数 = 备份文件行数（516行）
  - [ ] 文件大小一致

- [ ] **patent_drafting_proxy.py.backup 创建**
  - [ ] 备份文件存在
  - [ ] 原文件行数 = 备份文件行数（1907行）
  - [ ] 文件大小一致

- [ ] **BACKUP_MANIFEST.txt 创建**
  - [ ] 文件存在
  - [ ] 包含备份时间戳
  - [ ] 包含原文件和备份文件的路径
  - [ ] 包含文件大小和校验和（md5）

### 1.3 测试用例编写

- [ ] **test_unified_writer_migration.py 创建**
  - [ ] 文件存在于正确的测试目录
  - [ ] 包含pytest导入
  - [ ] 包含必要的fixtures

- [ ] **WriterAgent测试用例**（4个）
  - [ ] `test_writer_agent_claims_drafting`
  - [ ] `test_writer_agent_description_drafting`
  - [ ] `test_writer_agent_office_action_response`
  - [ ] `test_writer_agent_invalidation_petition`

- [ ] **PatentDraftingProxy测试用例**（7个）
  - [ ] `test_patent_drafting_analyze_disclosure`
  - [ ] `test_patent_drafting_assess_patentability`
  - [ ] `test_patent_drafting_claims`
  - [ ] `test_patent_drafting_specification`
  - [ ] `test_patent_drafting_optimize_scope`
  - [ ] `test_patent_drafting_review_adequacy`
  - [ ] `test_patent_drafting_detect_errors`

- [ ] **测试fixtures**
  - [ ] `fixtures/` 目录存在
  - [ ] 包含mock_disclosure.json
  - [ ] 包含mock_office_action.json
  - [ ] 包含mock_patent_data.json

- [ ] **测试可运行**
  - [ ] `pytest tests/agents/xiaona/test_unified_writer_migration.py --collect-only` 成功
  - [ ] 显示11个测试用例收集成功

---

## ✅ 阶段2：模块拆分检查清单

### 2.1 PatentDraftingProxy → drafting_module.py

- [ ] **类迁移**
  - [ ] `PatentDraftingModule`类定义完整
  - [ ] 包含`__init__`方法
  - [ ] 包含`execute`方法

- [ ] **方法迁移**（7个能力）
  - [ ] `analyze_disclosure()` - 完整实现
  - [ ] `assess_patentability()` - 完整实现
  - [ ] `draft_specification()` - 完整实现
  - [ ] `draft_claims()` - 完整实现
  - [ ] `optimize_protection_scope()` - 完整实现
  - [ ] `review_adequacy()` - 完整实现
  - [ ] `detect_common_errors()` - 完整实现

- [ ] **依赖保留**
  - [ ] LLM管理器正确导入
  - [ ] 提示词系统正确导入
  - [ ] 辅助函数正确迁移

- [ ] **测试通过**
  - [ ] 所有7个方法的单元测试通过
  - [ ] 与原始PatentDraftingProxy行为一致

### 2.2 WriterAgent → response_module.py

- [ ] **类迁移**
  - [ ] `ResponseModule`类定义完整
  - [ ] 包含`__init__`方法
  - [ ] 包含`execute`方法

- [ ] **方法迁移**（2个能力）
  - [ ] `draft_office_action_response()` - 完整实现
  - [ ] `draft_invalidation_petition()` - 完整实现

- [ ] **依赖保留**
  - [ ] LLM管理器正确导入
  - [ ] 系统提示词正确迁移

- [ ] **测试通过**
  - [ ] 所有2个方法的单元测试通过
  - [ ] 与原始WriterAgent行为一致

### 2.3 orchestration_module.py

- [ ] **类定义**
  - [ ] `OrchestrationModule`类定义完整
  - [ ] 包含`__init__`方法
  - [ ] 包含`execute`方法

- [ ] **方法实现**（2个能力）
  - [ ] `draft_full_application()` - 完整实现
    - [ ] 步骤1: analyze_disclosure
    - [ ] 步骤2: assess_patentability
    - [ ] 步骤3: draft_claims
    - [ ] 步骤4: draft_specification
    - [ ] 步骤5: review_adequacy
    - [ ] 步骤6: detect_common_errors
    - [ ] 返回完整结果字典
  - [ ] `orchestrate_response()` - 完整实现
    - [ ] 检索→分析→答复流程

- [ ] **测试通过**
  - [ ] 流程编排测试通过
  - [ ] 各步骤正确调用对应模块

### 2.4 utility_module.py

- [ ] **类定义**
  - [ ] `UtilityModule`类定义完整
  - [ ] 包含`__init__`方法
  - [ ] 包含`execute`方法

- [ ] **方法实现**（3个能力）
  - [ ] `format_document()` - 格式化输出
  - [ ] `calculate_quality_score()` - 质量评分算法
  - [ ] `compare_versions()` - 版本对比

- [ ] **测试通过**
  - [ ] 所有工具方法测试通过

---

## ✅ 阶段3：统一入口检查清单

### 3.1 unified_patent_writer.py

- [ ] **文件创建**
  - [ ] 文件存在于正确位置
  - [ ] 包含完整的类定义

- [ ] **类结构**
  - [ ] `UnifiedPatentWriter`类定义
  - [ ] 继承自`BaseXiaonaComponent`
  - [ ] 包含4个子模块实例
    - [ ] `self.drafting_module`
    - [ ] `self.response_module`
    - [ ] `self.orchestration_module`
    - [ ] `self.utility_module`

- [ ] **能力注册**（13个）
  - [ ] 模块1: 7个撰写能力
  - [ ] 模块2: 2个答复能力
  - [ ] 模块3: 2个编排能力
  - [ ] 模块4: 3个工具能力

- [ ] **路由逻辑**
  - [ ] `execute()`方法实现
  - [ ] 根据task_type正确路由到模块
  - [ ] 错误处理完整

- [ ] **测试通过**
  - [ ] 所有13个能力可调用
  - [ ] 路由逻辑测试通过
  - [ ] 集成测试通过

---

## ✅ 阶段4：向后兼容检查清单

### 4.1 WriterAgent适配器

- [ ] **适配器实现**
  - [ ] `writer_agent.py`修改为适配器
  - [ ] 内部实例化`UnifiedPatentWriter`
  - [ ] 保留原有方法签名

- [ ] **任务类型映射**
  - [ ] `claims` → `draft_claims`
  - [ ] `description` → `draft_specification`
  - [ ] `office_action_response` → `draft_office_action_response`
  - [ ] `invalidation` → `draft_invalidation_petition`

- [ ] **向后兼容测试**
  - [ ] 旧代码调用WriterAgent成功
  - [ ] 输出格式一致
  - [ ] 所有原有测试通过

### 4.2 PatentDraftingProxy适配器

- [ ] **适配器实现**
  - [ ] `patent_drafting_proxy.py`修改为适配器
  - [ ] 内部实例化`UnifiedPatentWriter`
  - [ ] 保留原有方法签名

- [ ] **向后兼容测试**
  - [ ] 旧代码调用PatentDraftingProxy成功
  - [ ] 输出格式一致
  - [ ] 所有原有测试通过

### 4.3 配置更新

- [ ] **agent_registry.json更新**
  - [ ] 添加`UnifiedPatentWriter`到sub_agents
  - [ ] 标记`WriterAgent`为deprecated
  - [ ] 标记`PatentDraftingProxy`为deprecated
  - [ ] 更新capabilities配置

- [ ] **配置验证**
  - [ ] JSON格式正确
  - [ ] 配置可正确加载
  - [ ] 新代理可被发现

---

## ✅ 阶段5：清理优化检查清单

### 5.1 代码清理

- [ ] **重复代码移除**
  - [ ] WriterAgent适配器无重复实现
  - [ ] PatentDraftingProxy适配器无重复实现
  - [ ] 代码行数减少~200行

- [ ] **导入优化**
  - [ ] 移除未使用的导入
  - [ ] 优化导入顺序
  - [ ] 符合PEP 8规范

### 5.2 性能优化

- [ ] **基准测试**
  - [ ] 运行性能基准测试
  - [ ] 对比旧版本和新版本
  - [ ] 性能不下降（±5%）

- [ ] **优化点**
  - [ ] 模块初始化优化
  - [ ] LLM调用优化
  - [ ] 缓存策略（如适用）

### 5.3 文档更新

- [ ] **CLAUDE.md更新**
  - [ ] 10个代理 → 9个代理
  - [ ] 更新代理列表表格
  - [ ] 添加UnifiedPatentWriter说明
  - [ ] 更新架构图

- [ ] **架构文档更新**
  - [ ] 更新XIAONA_SPECIALIZED_AGENTS_ARCHITECTURE.md
  - [ ] 添加合并说明
  - [ ] 更新代理协作模式

- [ ] **API文档**
  - [ ] 更新API文档
  - [ ] 添加迁移指南

### 5.4 质量检查

- [ ] **代码格式化**
  - [ ] `black . --line-length 100` 通过
  - [ ] `ruff check .` 通过
  - [ ] `mypy core/` 通过

- [ ] **测试覆盖率**
  - [ ] `pytest --cov=core/agents/xiaona` 运行
  - [ ] 覆盖率 >80%
  - [ ] 所有测试通过

- [ ] **代码审查**
  - [ ] 完成代码审查
  - [ ] 修复所有审查意见
  - [ ] 获得批准

---

## 📊 总体完成标准

### 功能完整性
- [ ] 所有9个核心能力可用
- [ ] 向后兼容性保持
- [ ] 所有测试通过

### 代码质量
- [ ] 无ruff错误
- [ ] 无mypy错误
- [ ] 测试覆盖率>80%

### 文档完整性
- [ ] CLAUDE.md更新
- [ ] 架构文档更新
- [ ] API文档更新
- [ ] 迁移指南提供

### 性能标准
- [ ] 性能不下降
- [ ] 内存使用合理
- [ ] 无明显性能瓶颈

---

**最后更新**: 2026-04-23
**审查者**: 待指定
