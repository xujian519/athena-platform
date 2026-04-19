# 统一工具注册表实施方案

> 项目: Athena工作平台
> 目标: 统一工具注册表，解决"工具找不准"问题
> 实施方式: 6个子智能体串行+并行协同
> 预计时间: 5-7天

---

## 一、任务总览

### 1.1 阶段划分

| 阶段 | 智能体 | 模式 | 任务数 | 预计时间 |
|-----|-------|------|-------|---------|
| 阶段1: 准备 | Agent 1-2 | 并行 | 8 | 1天 |
| 阶段2: 实施 | Agent 3-4 | 串行+并行 | 12 | 2-3天 |
| 阶段3: 验证 | Agent 5 | 独立 | 6 | 1-2天 |
| 阶段4: 清理 | Agent 6 | 独立 | 5 | 1天 |
| **总计** | **6个智能体** | **混合** | **31** | **5-7天** |

### 1.2 智能体角色分配

| 编号 | 名称 | 角色 | 主要职责 |
|-----|-----|------|---------|
| Agent 1 | 📦 备份专家 | 准备阶段 | 代码备份、分支创建、回滚准备 |
| Agent 2 | 🔍 分析专家 | 准备阶段 | 依赖分析、影响评估、环境检查 |
| Agent 3 | 🏗️ 架构师 | 实施阶段 | 核心注册表实现、API设计 |
| Agent 4 | 🔄 迁移专家 | 实施阶段 | 工具迁移、注册更新、脚本执行 |
| Agent 5 | 🧪 测试专家 | 验证阶段 | 单元测试、集成测试、性能测试 |
| Agent 6 | 📝 文档专家 | 清理阶段 | 文档更新、旧代码清理、知识转移 |

---

## 二、阶段1: 准备阶段（并行）

### Agent 1: 📦 备份专家

#### 任务清单

- [ ] **任务1.1**: 创建feature分支
  - 分支名称: `feature/unified-tool-registry`
  - 基于分支: `main`
  - 验证: 分支创建成功

- [ ] **任务1.2**: 备份现有注册表文件
  - 备份位置: `backup/registries_YYYYMMDD/`
  - 包含文件:
    - `core/tools/registry.py`
    - `core/governance/unified_tool_registry.py`
    - `core/registry/tool_registry_center.py`
    - `core/search/registry/tool_registry.py`
    - `core/tools/base.py`
    - `core/tools/enhanced_tool_system.py`

- [ ] **任务1.3**: 创建回滚脚本
  - 脚本路径: `scripts/rollback_unified_registry.sh`
  - 功能: 一键回滚到备份状态
  - 测试: 验证回滚脚本可用

- [ ] **任务1.4**: 依赖快照
  - 导出当前Python依赖: `pip freeze > requirements_backup.txt`
  - 记录Python版本: `python --version`
  - 记录系统环境: `uname -a`

#### 检查清单

```bash
# 分支检查
✅ git branch | grep feature/unified-tool-registry
✅ git log --oneline -1

# 备份检查
✅ ls -lh backup/registries_YYYYMMDD/
✅ ls -lh backup/registries_YYYYMMDD/*registry*.py

# 回滚脚本检查
✅ test -f scripts/rollback_unified_registry.sh
✅ bash -n scripts/rollback_unified_registry.sh

# 依赖检查
✅ test -f requirements_backup.txt
✅ cat requirements_backup.txt | grep -i "tool\|registry"
```

---

### Agent 2: 🔍 分析专家

#### 任务清单

- [ ] **任务2.1**: 扫描现有工具注册表
  - 输出: `docs/reports/registry_inventory.md`
  - 内容:
    - 各注册表类的方法和属性
    - 注册的工具列表
    - 依赖关系图

- [ ] **任务2.2**: 分析工具使用情况
  - 输出: `docs/reports/tool_usage_analysis.md`
  - 内容:
    - 哪些智能体使用哪些注册表
    - 工具调用频率统计
    - 关键路径识别

- [ ] **任务2.3**: 依赖关系分析
  - 输出: `docs/reports/dependency_graph.md`
  - 内容:
    - 模块导入关系
    - 循环依赖检测
    - 关键依赖路径

- [ ] **任务2.4**: 风险评估
  - 输出: `docs/reports/risk_assessment.md`
  - 内容:
    - 高风险模块识别
    - 破坏性变更评估
    - 回滚预案

- [ ] **任务2.5**: 环境检查
  - 检查项:
    - Python版本 (需要3.11+)
    - 必要的库 (dataclasses, typing, pathlib)
    - 测试框架 (pytest)
    - 代码质量工具 (ruff, mypy)

#### 检查清单

```bash
# 报告生成检查
✅ test -f docs/reports/registry_inventory.md
✅ test -f docs/reports/tool_usage_analysis.md
✅ test -f docs/reports/dependency_graph.md
✅ test -f docs/reports/risk_assessment.md

# 环境检查
✅ python --version | grep "3.11"
✅ pip list | grep -E "pytest|ruff|mypy"
✅ python -c "from dataclasses import dataclass; print('✓ dataclasses OK')"
✅ python -c "from typing import Callable; print('✓ typing OK')"
```

---

## 三、阶段2: 实施阶段（串行+并行）

### Agent 3: 🏗️ 架构师（核心实现）

#### 任务清单

- [ ] **任务3.1**: 实现统一工具注册表核心
  - 文件: `core/tools/unified_registry.py`
  - 类: `UnifiedToolRegistry`
  - 功能:
    - 单例模式
    - 懒加载机制
    - 健康状态管理
    - 自动发现机制

- [ ] **任务3.2**: 实现@tool装饰器
  - 文件: `core/tools/decorators.py`
  - 功能:
    - 工具标记
    - 元数据提取
    - 懒加载支持

- [ ] **任务3.3**: 实现工具迁移脚本
  - 文件: `scripts/migrate_tool_registry.py`
  - 功能:
    - 扫描旧注册表
    - 迁移工具定义
    - 生成迁移报告

- [ ] **任务3.4**: 实现导入迁移脚本
  - 文件: `scripts/migrate_registry_imports.py`
  - 功能:
    - 替换旧import语句
    - 更新类名引用
    - 生成迁移日志

- [ ] **任务3.5**: 实现生产环境同步脚本
  - 文件: `scripts/sync_production.py`
  - 功能:
    - 同步core/到production/core/
    - 版本控制
    - 变更检测

- [ ] **任务3.6**: 更新基础工具类
  - 文件: `core/tools/base.py`
  - 变更:
    - 保留向后兼容shim
    - 添加类型注解
    - 更新文档字符串

#### 检查清单

```python
# 核心实现检查
✅ from core.tools.unified_registry import UnifiedToolRegistry
✅ registry = UnifiedToolRegistry.get_instance()
✅ registry.list_tools()  # 返回工具列表

# 装饰器检查
✅ from core.tools.decorators import tool
✅ @tool(name="test", tags=["test"])
✅ def test_fn(): pass
✅ hasattr(test_fn, '_is_tool')

# 脚本检查
✅ test -f scripts/migrate_tool_registry.py
✅ test -f scripts/migrate_registry_imports.py
✅ test -f scripts/sync_production.py
✅ python -m py_compile scripts/*.py
```

---

### Agent 4: 🔄 迁移专家（工具迁移）

#### 任务清单

- [ ] **任务4.1**: 迁移核心工具（并行）
  - 专利检索工具
  - 学术搜索工具
  - 向量搜索工具
  - 文档处理工具

- [ ] **任务4.2**: 迁移分析工具（并行）
  - 专利分析工具
  - 法律分析工具
  - 语义分析工具

- [ ] **任务4.3**: 迁移外部服务工具（串行）
  - MCP服务工具
  - Web搜索工具
  - API集成工具

- [ ] **任务4.4**: 更新智能体代码（串行）
  - 小娜智能体
  - 小诺智能体
  - 云熙智能体

- [ ] **任务4.5**: 执行导入迁移（串行）
  - 运行: `python3 scripts/migrate_registry_imports.py --dry-run`
  - 审查变更
  - 执行: `python3 scripts/migrate_registry_imports.py`

- [ ] **任务4.6**: 验证迁移结果
  - 检查: 所有工具已注册
  - 检查: 智能体可以获取工具
  - 检查: 无循环导入

#### 检查清单

```python
# 工具迁移检查
✅ from core.tools.unified_registry import UnifiedToolRegistry
✅ registry = UnifiedToolRegistry.get_instance()
✅ registry.get("patent_search")  # 核心工具
✅ registry.get("academic_search")  # 核心工具
✅ registry.get("patent_analysis")  # 分析工具
✅ registry.get("mcp_service")  # 外部服务

# 智能体更新检查
✅ grep -r "from core.tools.unified_registry import" core/agents/
✅ grep -r "UnifiedToolRegistry" core/agents/ | wc -l  # 应该>0

# 导入迁移检查
✅ git diff | grep "from core.tools.registry import ToolRegistry"
✅ git diff | grep "from core.governance" | wc -l  # 应该=0（已替换）
```

---

## 四、阶段3: 验证阶段（独立）

### Agent 5: 🧪 测试专家

#### 任务清单

- [ ] **任务5.1**: 编写单元测试
  - 文件: `tests/tools/test_unified_registry.py`
  - 测试用例:
    - 单例模式测试
    - 工具注册测试
    - 懒加载测试
    - 健康状态测试
    - 错误处理测试

- [ ] **任务5.2**: 编写集成测试
  - 文件: `tests/integration/test_tool_integration.py`
  - 测试场景:
    - 智能体工具调用
    - 跨模块工具使用
    - 错误恢复机制

- [ ] **任务5.3**: 编写性能测试
  - 文件: `tests/performance/test_registry_performance.py`
  - 测试指标:
    - 启动时间（懒加载 vs 全量加载）
    - 工具查找延迟
    - 内存占用

- [ ] **任务5.4**: 执行测试套件
  ```bash
  # 单元测试
  pytest tests/tools/test_unified_registry.py -v

  # 集成测试
  pytest tests/integration/test_tool_integration.py -v

  # 性能测试
  pytest tests/performance/test_registry_performance.py -v

  # 覆盖率测试
  pytest --cov=core.tools.unified_registry --cov-report=html
  ```

- [ ] **任务5.5**: 压力测试
  - 场景:
    - 1000个工具同时注册
    - 并发工具调用
    - 长时间运行稳定性

- [ ] **任务5.6**: 生成测试报告
  - 文件: `docs/reports/unified_registry_test_report.md`
  - 内容:
    - 测试通过率
    - 性能对比
    - 问题清单
    - 改进建议

#### 检查清单

```bash
# 测试执行检查
✅ pytest tests/tools/test_unified_registry.py -v | grep "passed"
✅ pytest tests/integration/test_tool_integration.py -v | grep "passed"
✅ pytest tests/performance/test_registry_performance.py -v | grep "passed"

# 覆盖率检查
✅ pytest --cov=core.tools.unified_registry --cov-report=term
✅ coverage report | grep "TOTAL" | awk '{print $4}' | grep -E "[8-9][0-9]%|100%"

# 报告检查
✅ test -f docs/reports/unified_registry_test_report.md
✅ grep -E "通过率|性能对比" docs/reports/unified_registry_test_report.md
```

---

## 五、阶段4: 清理阶段（独立）

### Agent 6: 📝 文档专家

#### 任务清单

- [ ] **任务6.1**: 更新项目文档
  - 文件: `CLAUDE.md`
  - 更新:
    - 工具系统说明
    - API文档
    - 示例代码

- [ ] **任务6.2**: 编写迁移指南
  - 文件: `docs/guides/TOOL_REGISTRY_MIGRATION_GUIDE.md`
  - 内容:
    - 迁移步骤
    - 常见问题
    - 故障排查

- [ ] **任务6.3**: 更新API文档
  - 文件: `docs/api/UNIFIED_TOOL_REGISTRY_API.md`
  - 内容:
    - 类和方法签名
    - 参数说明
    - 返回值说明
    - 使用示例

- [ ] **任务6.4**: 清理旧代码
  - 删除/标记废弃:
    - 旧的注册表实现
    - 未使用的导入
    - 重复的工具定义
  - 保留:
    - 向后兼容shim
    - 历史备份

- [ ] **任务6.5**: 知识转移
  - 文件: `docs/training/TOOL_REGISTRY_TRAINING.md`
  - 内容:
    - 新架构讲解
    - 最佳实践
    - 常见陷阱
    - 视频教程链接

#### 检查清单

```bash
# 文档更新检查
✅ grep -E "UnifiedToolRegistry|统一工具注册表" CLAUDE.md
✅ test -f docs/guides/TOOL_REGISTRY_MIGRATION_GUIDE.md
✅ test -f docs/api/UNIFIED_TOOL_REGISTRY_API.md
✅ test -f docs/training/TOOL_REGISTRY_TRAINING.md

# 代码清理检查
✅ git status | grep "deleted:.*old.*registry"
✅ grep -r "deprecated" core/tools/registry.py
✅ grep -r "向后兼容" docs/guides/

# 文档质量检查
✅ grep -E "## 使用示例|## API参考|## 常见问题" docs/api/UNIFIED_TOOL_REGISTRY_API.md
✅ wc -l docs/guides/TOOL_REGISTRY_MIGRATION_GUIDE.md | awk '{if($1>100) print "✓ 文档长度足够"}'
```

---

## 六、协同流程

### 6.1 串行流程

```
Agent 1 (备份) → Agent 2 (分析) → Agent 3 (架构) → Agent 4 (迁移) → Agent 5 (测试) → Agent 6 (文档)
```

### 6.2 并行流程

```
阶段1: Agent 1 (备份) ╱ ╲ Agent 2 (分析)
                          ↓
阶段2: Agent 3 (架构) → Agent 4 (迁移)
                          ↓
阶段3:              Agent 5 (测试)
                          ↓
阶段4:              Agent 6 (文档)
```

### 6.3 依赖关系

| 智能体 | 前置依赖 | 后续依赖 |
|-------|---------|---------|
| Agent 1 | 无 | Agent 2-6 |
| Agent 2 | Agent 1 | Agent 3-4 |
| Agent 3 | Agent 1-2 | Agent 4-5 |
| Agent 4 | Agent 1-3 | Agent 5 |
| Agent 5 | Agent 1-4 | Agent 6 |
| Agent 6 | Agent 1-5 | 无 |

---

## 七、质量门禁

### 7.1 阶段门禁

| 阶段 | 门禁标准 | 负责人 |
|-----|---------|-------|
| 准备阶段 | ✅ 备份完成<br>✅ 分析报告完整<br>✅ 环境检查通过 | Agent 1-2 |
| 实施阶段 | ✅ 核心代码实现<br>✅ 工具迁移完成<br>✅ 无编译错误 | Agent 3-4 |
| 验证阶段 | ✅ 单元测试通过率>95%<br>✅ 集成测试通过<br>✅ 性能无退化 | Agent 5 |
| 清理阶段 | ✅ 文档完整<br>✅ 旧代码清理<br>✅ 知识转移完成 | Agent 6 |

### 7.2 发布门禁

```
✅ 所有阶段门禁通过
✅ 代码审查完成
✅ 测试覆盖率 >85%
✅ 性能基准达标
✅ 文档审查通过
✅ 产品负责人批准
```

---

## 八、风险应对

### 8.1 高风险场景

| 风险 | 概率 | 影响 | 应对措施 |
|-----|-----|------|---------|
| 破坏现有功能 | 中 | 高 | ✅ 完整回滚脚本<br>✅ 分阶段发布 |
| 性能退化 | 低 | 中 | ✅ 性能基准测试<br>✅ 懒加载机制 |
| 工具遗漏 | 中 | 中 | ✅ 自动发现机制<br>✅ 完整测试覆盖 |
| 循环依赖 | 低 | 高 | ✅ 依赖分析工具<br>✅ 延迟导入 |

### 8.2 回滚预案

```bash
# 快速回滚命令
./scripts/rollback_unified_registry.sh

# 手动回滚步骤
git checkout main
git branch -D feature/unified-tool-registry
cp -r backup/registries_YYYYMMDD/* core/
```

---

## 九、成功标准

### 9.1 技术指标

| 指标 | 目标 | 测量方法 |
|-----|------|---------|
| 工具查找成功率 | >95% | 集成测试 |
| 启动时间 | <0.5s | 性能测试 |
| 内存占用 | <100MB | 资源监控 |
| 测试覆盖率 | >85% | pytest --cov |
| 代码行数 | -30% | 代码统计 |

### 9.2 业务指标

| 指标 | 目标 | 测量方法 |
|-----|------|---------|
| 工具调用错误率 | <5% | 生产监控 |
| 智能体可用性 | 100% | 智能体测试 |
| 开发效率提升 | +50% | 开发者反馈 |

---

## 十、总结

### 10.1 实施优势

- ✅ **并行加速**: 准备阶段并行，节省时间
- ✅ **专业分工**: 每个智能体专注特定领域
- ✅ **质量保证**: 完整的测试和验证流程
- ✅ **风险可控**: 完整的备份和回滚机制

### 10.2 预期收益

- **短期**: 解决"工具找不准"问题
- **中期**: 提升开发效率和系统稳定性
- **长期**: 为工具生态系统奠定基础

---

**维护者**: 徐健 (xujian519@gmail.com)
**制定者**: Claude Code (Sonnet 4.6)
**最后更新**: 2026-04-19 21:40
