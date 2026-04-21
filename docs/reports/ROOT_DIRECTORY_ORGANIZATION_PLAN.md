# Athena平台根目录整理方案

> **日期**: 2026-04-21
> **目标**: 清理根目录散落文件，减少顶层文件夹数量

---

## 📊 当前问题分析

### 1. 散落文件统计

| 类型 | 数量 | 说明 |
|------|------|------|
| **Python脚本** | 8个 | 启动脚本、测试脚本散落在根目录 |
| **历史报告** | 19个 | PHASE1/PHASE2等历史报告 |
| **临时文件** | 4个 | coverage.json, .log等 |
| **配置文件** | 3个 | package.json, pyrightconfig.json |
| **重要文档** | 4个 | README, CLAUDE.md等 |
| **总计** | **38个** | 文件散落在根目录 |

### 2. 顶层文件夹统计

**当前**: 41个顶层文件夹（过多）

**建议**: 整合到15-20个核心文件夹

---

## 🎯 整理方案

### 阶段 1: 文件分类整理

#### 1.1 历史报告归档

**目标目录**: `docs/archive/phase_reports/`

**移动文件** (19个):
```
PHASE1_DAY1_2_CHECKLIST.md
PHASE1_DAY3_SUMMARY.md
PHASE1_DAY4_5_SUMMARY.md
PHASE1_DAY6_SUMMARY.md
PHASE1_DAY7_SUMMARY.md
PHASE1_FINAL_REPORT.md
PHASE1_VERIFICATION_REPORT.md
PHASE2_WEEK1_PLAN.md
PHASE2_WEEK1_PROGRESS.md
PROJECT_COMPLETE.md
PROJECT_CLEANUP_REPORT_20260419.md
REPORT_CLEANUP_SUMMARY_20260419.md
PATENT_WEBUI_BACKUP_COMPLETE_20260419.md
MIGRATION_REPORT_20260420.md
DOCKER_COMPOSE_MERGE_REPORT.md
DOCKER_COMPOSE_MIGRATION_GUIDE.md
DOCKER_COMPOSE_QUICK_REFERENCE.md
TEAM_NOTIFICATION_DOCKER_COMPOSE_MIGRATION.md
QUICK_START_MONITORING.md
Athena_项目现状扫描报告_20260421.md
cleanup_log_20260420.md
架构.md
```

#### 1.2 独立脚本整理

**目标目录**: `scripts/standalone/`

**移动文件** (7个):
```
enhanced_patent_search.py
google_patents_retriever_v2.py
simple_patent_search.py
google_patents_simple.py
athena_simplified_api.py
test_infringement_determiner.py
advanced_patent_search.py
```

**保留在根目录** (1个):
```
start_xiaona.py  # 主启动脚本
```

#### 1.3 临时文件清理

**处理方式**:
- `coverage*.json` → `build/coverage/`
- `*.log` → `logs/`
- 添加到`.gitignore`

#### 1.4 保留的重要文件

**保留在根目录** (8个):
```
README.md                      # 项目说明
QUICK_START.md                 # 快速开始
CLAUDE.md                      # Claude配置
Athena_渐进式重构计划_20260421.md  # 重构计划
start_xiaona.py                # 启动脚本
package.json                   # Node.js配置
package-lock.json              # Node.js锁文件
pyrightconfig.json             # Python类型检查
```

---

### 阶段 2: 顶层文件夹整合

#### 2.1 核心目录（保留）

**必须保留** (12个):
```
core/              # 核心系统模块
config/            # 统一配置文件
docs/              # 文档
tests/             # 测试
scripts/           # 脚本
services/          # 微服务
gateway-unified/   # Go网关
mcp-servers/       # MCP服务器
patents/           # 专利模块（统一目录）
domains/           # 业务领域
skills/            # 技能定义
prompts/           # 提示词
```

#### 2.2 可选目录（根据需要保留或归档）

**评估保留** (10个):
```
data/              # 数据（如果运行时需要）
models/            # AI模型（如果需要本地模型）
logs/              # 日志
deploy/            # 部署配置
docker/            # Docker相关
external_projects/ # 外部项目
examples/          # 示例
tools/             # 工具（如果不是core/tools的重复）
api/               # API（如果不是services的重复）
apps/              # 应用（如果不是services的重复）
```

#### 2.3 建议归档的目录

**移至 archive/** (19个):
```
archive/           # 新建归档目录
├── deprecated/
│   ├── memory/            # 被 core/memory 替代
│   ├── knowledge_graph/   # 被新系统替代
│   ├── intelligence/      # 被 core/cognition 替代
│   ├── collaboration/     # 被 core/collaboration 替代
│   ├── infrastructure/    # 已废弃
│   ├── athena_env_py311/  # 虚拟环境
│   ├── __pycache__/       # Python缓存
│   ├── htmlcov/           # 覆盖率HTML
│   └── test_results_e2e/  # 测试结果
├── legacy/
│   ├── knowledge/         # 旧知识系统
│   ├── judgment_vector_db/# 旧向量数据库
│   ├── personal_secure_storage/
│   └── fusion/            # 旧融合系统
└── temp/
    ├── .cleanup_backup_*/
    ├── .docker_backup_*/
    └── .benchmarks/
```

---

### 阶段 3: .gitignore 更新

**添加规则**:
```gitignore
# Root directory organization
*.log
coverage*.json
build/
scripts/standalone/*.py
!start_xiaona.py
docs/archive/phase_reports/

# Deprecated directories
archive/
memory/
knowledge_graph/
intelligence/
collaboration/
infrastructure/
```

---

## 🚀 执行步骤

### 自动化脚本执行

```bash
cd /Users/xujian/Athena工作平台
./scripts/organize_root_directory.sh
```

### 手动验证

```bash
# 1. 检查根目录文件数量
find . -maxdepth 1 -type f | wc -l

# 2. 检查顶层文件夹数量
find . -maxdepth 1 -type d ! -name ".*" | wc -l

# 3. 查看保留的重要文件
ls -1 *.md *.py 2>/dev/null
```

---

## 📊 整理前后对比

### 根目录文件

| 项目 | 整理前 | 整理后 | 改善 |
|------|--------|--------|------|
| **Python脚本** | 8个 | 1个 | 87.5% ↓ |
| **历史报告** | 19个 | 2个* | 89.5% ↓ |
| **临时文件** | 4个 | 0个 | 100% ↓ |
| **总文件数** | 38个 | 11个 | **71% ↓** |

*保留最新的重构计划和总体报告

### 顶层文件夹

| 项目 | 整理前 | 整理后 | 改善 |
|------|--------|--------|------|
| **核心目录** | 12个 | 12个 | 保持 |
| **可选目录** | 10个 | 5个 | 50% ↓ |
| **归档目录** | 19个 | 0个 | 100% ↓ |
| **总目录数** | 41个 | 17个 | **58.5% ↓** |

---

## ✅ 完成检查

整理完成后，确认：

- [ ] 根目录文件减少到15个以下
- [ ] 顶层文件夹减少到20个以下
- [ ] 历史报告已归档到docs/archive/
- [ ] 独立脚本已整理到scripts/standalone/
- [ ] 临时文件已清理
- [ ] .gitignore已更新
- [ ] 重要文件仍可访问（README, start_xiaona.py等）

---

## 🎯 后续维护

### 1. 定期清理

**频率**: 每月一次

**内容**:
- 清理根目录新增的散落文件
- 归档旧报告
- 清理临时文件

### 2. 文件组织规范

**根目录只保留**:
- README.md, QUICK_START.md
- CLAUDE.md（项目配置）
- 启动脚本（start_xiaona.py）
- 配置文件（package.json等）
- 最新计划文档

**其他文件**:
- 报告 → docs/reports/
- 脚本 → scripts/
- 数据 → data/
- 日志 → logs/

---

**生成时间**: 2026-04-21
**预期效果**: 根目录文件减少71%，顶层文件夹减少58.5%
