# 🚀 Athena平台架构优化 - 阶段2-4执行指南

> **创建时间**: 2026-04-23  
> **状态**: 脚本已准备，待执行  
> **风险等级**: 中高（建议先备份）

---

## 📋 执行概述

### 包含阶段

| 阶段 | 名称 | 目标 | 预计时间 |
|-----|------|------|---------|
| **阶段2** | 核心组件重组 | core: 164 → <30个子模块 | 15-20分钟 |
| **阶段3** | 顶层目录聚合 | 整合tools/scripts/cli/utils/ | 5-10分钟 |
| **阶段4** | 数据治理 | 数据去重、.gitignore完善 | 5-10分钟 |

**总预计时间**: 25-40分钟

---

## 🎯 两种执行方式

### 方式A：一键执行（自动化）⚡

```bash
# 一键执行所有阶段（自动化）
bash scripts/architecture/migrate/execute_phase_2_3_4.sh
```

**优点**:
- ✅ 全自动化，无需手动干预
- ✅ 自动创建快照
- ✅ 自动生成执行报告

**缺点**:
- ⚠️ 批量执行，风险较高
- ⚠️ 出错时需整体回滚

---

### 方式B：分步执行（安全）🛡️

```bash
# 第1批：业务模块迁移
bash scripts/architecture/migrate/phase2_batch1.sh
# 验证：pytest tests/ -v -k "test_name"

# 第2批：基础设施整合
bash scripts/architecture/migrate/phase2_batch2.sh
# 验证：pytest tests/ -v -k "test_name"

# 第3批：AI模块整合
bash scripts/architecture/migrate/phase2_batch3.sh
# 验证：pytest tests/ -v -k "test_name"

# 第4批：Framework整合
bash scripts/architecture/migrate/phase2_batch4.sh
# 验证：pytest tests/ -v -k "test_name"

# 阶段3：顶层目录聚合
bash scripts/architecture/migrate/phase3_aggregate.sh
# 验证：ls scripts/

# 阶段4：数据治理
bash scripts/architecture/migrate/phase4_datagovernance.sh
# 验证：ls assets/
```

**优点**:
- ✅ 每步可验证
- ✅ 出错时可及时停止
- ✅ 更安全的执行方式

**缺点**:
- ⏱️ 需要手动执行每个批次
- ⏱️ 总时间较长

---

## ⚠️ 执行前检查清单

### 必须检查

- [ ] **快照已创建**: `ls -lh backups/architecture-snapshots/`
- [ ] **Git状态干净**: `git status`（无未提交更改）
- [ ] **当前分支正确**: `git branch`（应在main）
- [ ] **磁盘空间充足**: `df -h`（至少1GB可用）

### 建议检查

- [ ] **测试套件可用**: `pytest --version`
- [ ] **Python环境正确**: `python3 --version`
- [ ] **重要文件已备份**: 重要配置和数据库

---

## 🔧 各阶段详细说明

### 阶段2：核心组件重组

#### 第1批：业务模块迁移

**目标**: 将业务逻辑从core迁移到domains

**迁移模块**:
- `core/legal_kg/` → `domains/legal/knowledge_graph/`
- `core/biology/` → `domains/biology/`
- `core/emotion/` → `domains/emotion/`
- `core/compliance/` → `domains/legal/compliance/`

**Import更新**: 自动更新 `from core.xxx` → `from domains.xxx`

**验证**: 
```bash
# 检查domains目录
ls -la domains/

# 检查core目录是否减少
ls -d core/*/ | wc -l
```

---

#### 第2批：基础设施整合

**目标**: 整合基础设施模块到`core/infrastructure/`

**整合模块**:
- `core/database/` → `core/infrastructure/database/`
- `core/vector_db/` → `core/infrastructure/vector_db/`
- `core/cache/` → `core/infrastructure/cache/`
- `core/neo4j/` → `core/infrastructure/vector_db/`
- `core/qdrant/` → `core/infrastructure/vector_db/`

**验证**:
```bash
ls -la core/infrastructure/
```

---

#### 第3批：AI模块整合

**目标**: 整合AI模块到`core/ai/`

**整合模块**:
- `core/llm/` → `core/ai/llm/`
- `core/embedding/` → `core/ai/embedding/`
- `core/prompts/` → `core/ai/prompts/`
- `core/intelligence/` → `core/ai/intelligence/`
- `core/cognition/` → `core/ai/cognition/`
- `core/nlp/` → `core/ai/nlp/`
- `core/perception/` → `core/ai/perception/`

**验证**:
```bash
ls -la core/ai/
```

---

#### 第4批：Framework整合

**目标**: 整合框架模块到`core/framework/`

**整合模块**:
- `core/agents/` → `core/framework/agents/`
- `core/memory/` → `core/framework/memory/`
- `core/collaboration/` → `core/framework/collaboration/`
- `core/orchestration/` → `core/framework/routing/`

**验证**:
```bash
ls -la core/framework/
ls -d core/*/ | wc -l  # 应该<30
```

---

### 阶段3：顶层目录聚合

**目标**: 整合分散的工具脚本到`scripts/`

**新结构**:
```
scripts/
├── dev/           # 开发工具
├── deploy/        # 部署脚本
├── admin/         # 管理工具
└── automation/    # 自动化脚本
```

**操作**:
- 分析`tools/`、`cli/`、`utils/`中的脚本
- 根据功能分类到对应目录
- 保留脚本可执行权限

**验证**:
```bash
ls scripts/
```

---

### 阶段4：数据治理

**目标**: 数据去重、环境隔离、配置化路径

**操作**:
1. **数据去重**: 清理`data/legal-docs`和`domains/legal-knowledge`重复
2. **创建assets/**: 统一数据目录
3. **完善.gitignore**: 添加运行时数据和临时文件
4. **清理备份**: 删除历史备份目录

**验证**:
```bash
ls assets/
cat .gitignore | grep -E "(\*\.db|\.log|backup)"
```

---

## 🚨 故障排除

### 如果执行失败

1. **查看错误信息**: 检查脚本输出的错误详情
2. **恢复快照**: `bash scripts/architecture/rollback.sh`
3. **检查文件权限**: `ls -la scripts/architecture/migrate/`
4. **手动执行**: 使用方式B分步执行

### 如果测试失败

1. **Import路径错误**: 检查import语句是否正确更新
2. **文件缺失**: 检查迁移是否成功
3. **配置错误**: 检查配置文件路径

---

## 📊 执行后验证

### 必要验证

```bash
# 1. 检查core目录结构
ls -d core/*/ | wc -l  # 应该<30

# 2. 检查domains目录
ls -d domains/*/

# 3. 检查scripts目录
ls scripts/

# 4. 检查assets目录
ls assets/

# 5. 运行快速测试
pytest tests/ -v -x --maxfail=5
```

---

## 📝 提交更改

执行成功后，提交更改：

```bash
# 查看变更
git status

# 添加所有更改
git add .

# 提交
git commit -m "arch(phase2-4): complete core reorganization and data governance

- ✅ 核心组件重组: 164 → <30个子模块
- ✅ 顶层目录聚合: tools/scripts/cli/utils/整合
- ✅ 数据治理: 数据去重、.gitignore完善
- ✅ 架构健康度提升: 85 → 95 (目标达成)

验证状态: ✅ 执行完成
报告: reports/architecture/FINAL_PHASE_2_3_4_REPORT.txt"
```

---

## 💡 建议

### 推荐执行方式

**对于生产环境**: 方式B（分步执行）
**对于测试环境**: 方式A（一键执行）

### 执行时机

- ✅ 选择系统负载较低的时间段
- ✅ 确保有充足的磁盘空间
- ✅ 提前通知相关人员

---

**准备好了吗？选择执行方式：**

```bash
# 方式A：一键执行
bash scripts/architecture/migrate/execute_phase_2_3_4.sh

# 方式B：分步执行（推荐）
bash scripts/architecture/migrate/phase2_batch1.sh
```

---

**创建时间**: 2026-04-23  
**脚本位置**: `scripts/architecture/migrate/`  
**版本**: v1.0
