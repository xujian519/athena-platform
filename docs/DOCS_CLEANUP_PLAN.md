# Docs目录整理计划

> **创建时间**: 2026-04-22
> **目标**: 将混乱的docs目录整理为清晰、可维护的文档体系

---

## 📊 当前状况

### 统计数据
- 总MD文件: 1094个
- 根目录MD文件: 204个 ⚠️
- 子目录: 50+个
- 主要问题: 文件堆积、分类混乱、过期文档未清理

### 核心问题
1. ❌ 根目录文件过多（204个）
2. ❌ 临时报告未归档（大量`*_report_*.md`）
3. ❌ 重复版本文档（多个v1/v2/v3）
4. ❌ 命名不统一（大小写混杂）
5. ❌ 中英文文档混合

---

## 🎯 整理目标

### 第一阶段: 分类归档（紧急）
- 将根目录204个文件按类型分类
- 临时报告移至 `archive/`
- 重复文档合并或删除旧版

### 第二阶段: 结构优化（重要）
- 建立清晰的目录层次
- 统一命名规范
- 创建索引文件

### 第三阶段: 维护规范（持续）
- 建立文档编写规范
- 定期归档机制
- 自动化整理脚本

---

## 📁 新目录结构设计

```
docs/
├── README.md                          # 文档导航首页
├── INDEX.md                           # 快速索引
│
├── architecture/                      # ✅ 架构文档
│   ├── system/                        #    系统架构
│   ├── microservices/                 #    微服务架构
│   ├── agents/                        #    智能体架构
│   └── database/                      #    数据库架构
│
├── guides/                            # ✅ 使用指南
│   ├── quick-start/                   #    快速开始
│   ├── installation/                  #    安装部署
│   ├── user-guide/                    #    用户手册
│   └── development/                   #    开发指南
│
├── api/                               # ✅ API文档
│   ├── rest/                          #    REST API
│   ├── websocket/                     #    WebSocket API
│   └── examples/                      #    API示例
│
├── agents/                            # ✅ 智能体文档
│   ├── xiaona/                        #    小娜智能体
│   ├── xiaonuo/                       #    小诺智能体
│   └── yunxi/                         #    云熙智能体
│
├── reports/                           # ✅ 报告（已存在，需整理）
│   ├── 2026-04/                       #    按月归档
│   ├── 2026-03/
│   └── archive/                       #    历史归档
│
├── reference/                         # ✅ 参考文档（已存在）
│   ├── configuration/                 #    配置参考
│   ├── cli/                           #    CLI参考
│   └── troubleshooting/               #    故障排查
│
├── deployment/                        # ✅ 部署文档（已存在）
│   ├── production/                    #    生产部署
│   ├── development/                   #    开发环境
│   └── docker/                        #    Docker部署
│
├── training/                          # ✅ 培训文档（已存在）
│   ├── exercises/                     #    练习
│   └── slides/                        #    幻灯片
│
├── archive/                           # ✅ 归档（已存在，需扩充）
│   ├── legacy/                        #    遗留文档
│   ├── temp-reports/                  #    临时报告
│   └── old-versions/                  #    旧版本文档
│
└── projects/                          # ✅ 项目文档（已存在）
    ├── production/                    #    生产项目
    └── experimental/                  #    实验项目
```

---

## 🔄 文件分类规则

### 1. 按文件名模式分类

| 模式 | 目标目录 | 示例 |
|-----|---------|------|
| `*_architecture*.md` | `architecture/` | `system_architecture.md` |
| `*_guide*.md` | `guides/` | `user_guide.md` |
| `QUICK_*.md` | `guides/quick-start/` | `QUICK_START.md` |
| `API_*.md` | `api/` | `API_DOCUMENTATION_V5.md` |
| `*_REPORT*.md` | `reports/` + 按日期归档 | `CODE_QUALITY_REPORT_20260224.md` |
| `*_PLAN*.md` | `plans/` | `implementation_plan.md` |
| `*_OPTIMIZATION*.md` | `archive/legacy/` | `xiaonuo_optimization_*.md` |
| `*_migration*.md` | `migration/` | `gateway_migration_plan.md` |
| `xiaona*.md` | `agents/xiaona/` | `xiaona_nlp_integration_summary.md` |
| `xiaonuo*.md` | `agents/xiaonuo/` | `xiaonuo_identity_profile.md` |

### 2. 按内容类型分类

**核心文档**（保留在根目录或适当子目录）:
- `README.md` - 文档导航
- `INDEX.md` - 快速索引
- `PROJECT_SUMMARY_*.md` - 项目摘要（最新版）

**过时文档**（移至archive）:
- 2025年12月及之前的临时报告
- 已废弃功能的文档
- 重复版本的旧版

**临时报告**（移至reports按月归档）:
- 所有 `*_report_YYYYMMDD*.md` 文件
- 测试报告、修复报告

---

## 🗂️ 具体整理操作

### 操作1: 归档临时报告

```bash
# 创建归档目录
mkdir -p docs/archive/temp-reports/2026-01
mkdir -p docs/archive/temp-reports/2026-02
mkdir -p docs/archive/temp-reports/2026-03
mkdir -p docs/archive/temp-reports/2026-04

# 移动报告文件（示例）
mv docs/*_report_202601*.md docs/archive/temp-reports/2026-01/
mv docs/*_report_202602*.md docs/archive/temp-reports/2026-02/
mv docs/*_report_202603*.md docs/archive/temp-reports/2026-03/
mv docs/*_report_202604*.md docs/archive/temp-reports/2026-04/
```

### 操作2: 归档过时文档

```bash
# 移动2025年遗留文档
mkdir -p docs/archive/legacy-2025
mv docs/xiaona_optimization_report.md docs/archive/legacy-2025/
mv docs/Xiaona增强系统使用指南.md docs/archive/legacy-2025/
mv docs/xiaonuo_optimization_*.md docs/archive/legacy-2025/
```

### 操作3: 整理API文档

```bash
# 移动API相关文档到api/目录
mv docs/API_*.md docs/api/
mv docs/api_*.md docs/api/
mv docs/*_api_*.md docs/api/
```

### 操作4: 整理架构文档

```bash
# 移动架构相关文档
mv docs/*_architecture*.md docs/architecture/
mv docs/*_ARCHITECTURE*.md docs/architecture/
```

### 操作5: 整理智能体文档

```bash
# 移动小娜相关文档
mv docs/xiaona*.md docs/agents/xiaona/
mv docs/Xiaona*.md docs/agents/xiaona/

# 移动小诺相关文档
mv docs/xiaonuo*.md docs/agents/xiaonuo/
mv docs/Xiaonuo*.md docs/agents/xiaonuo/
```

---

## 📋 文件清单（待整理）

### 需要归档的文件（204个根目录文件中）

**临时报告**（约30个）:
- `*_report_202601*.md` → `archive/temp-reports/2026-01/`
- `*_report_202602*.md` → `archive/temp-reports/2026-02/`
- `*_report_202603*.md` → `archive/temp-reports/2026-03/`
- `*_report_202604*.md` → `archive/temp-reports/2026-04/`

**过时优化文档**（约10个）:
- `xiaona_optimization_*.md` → `archive/legacy-2025/`
- `xiaonuo_optimization_*.md` → `archive/legacy-2025/`
- `*三阶段优化*.md` → `archive/legacy-2025/`

**迁移相关**（约15个）:
- `*_migration*.md` → `migration/` 或 `archive/`
- `gateway_migration_plan.md` → `deployment/migration/`

**网关相关**（约10个）:
- `gateway_*.md` → `architecture/gateway/`
- `athena-api-gateway-*.md` → `architecture/gateway/`

**企业级架构**（约7个）:
- `enterprise-multi-agent-*.md` → `architecture/enterprise/`

**Istio/Service Mesh**（约10个）:
- `Istio_*.md` → `archive/legacy/` （已废弃）
- `*mesh*.md` → `archive/legacy/`

**技术栈选择**（约3个）:
- `*_TECH_STACK_SELECTION.md` → `reference/technical-stack/`

**中文专利文档**（约10个）:
- `专利*.md` → `projects/patents/`
- `*.md` (中文专利相关) → `projects/patents/`

---

## ✅ 整理后的预期效果

| 指标 | 整理前 | 整理后 | 改善 |
|-----|--------|--------|------|
| 根目录文件数 | 204个 | <20个 | ↓90% |
| 目录层次 | 混乱 | 清晰3-4层 | ✅ |
| 文档可发现性 | 困难 | 容易 | ✅ |
| 命名规范 | 不统一 | 统一 | ✅ |
| 过期文档 | 未清理 | 已归档 | ✅ |

---

## 🔧 维护规范

### 新文档规范

**命名规范**:
```
[类型]_[主题]_[版本].[扩展名]

示例:
- GUIDE_quick-start_v1.0.md
- API_rest_v2.0.md
- ARCHITECTURE_system_v1.0.md
- REPORT_monthly_2026-04.md
```

**存放规范**:
- 所有新文档必须放入合适的子目录
- 根目录只保留索引和导航文件
- 临时报告直接放入 `reports/YYYY-MM/`

**定期清理**:
- 每季度清理一次临时报告
- 每半年归档一次旧版本文档
- 每年审查一次文档有效性

---

## 📅 执行时间表

### 阶段1: 自动化脚本（1小时）
- [ ] 创建整理脚本
- [ ] 测试脚本（dry-run）
- [ ] 执行整理

### 阶段2: 手动调整（30分钟）
- [ ] 检查分类结果
- [ ] 处理特殊情况
- [ ] 更新索引

### 阶段3: 文档更新（30分钟）
- [ ] 创建新的README
- [ ] 更新INDEX.md
- [ ] 添加维护规范

**总时间**: 约2小时

---

## 🚀 开始执行

准备好后，运行整理脚本：

```bash
# 查看整理计划（dry-run）
bash scripts/docs_cleanup.sh --dry-run

# 执行整理
bash scripts/docs_cleanup.sh

# 查看整理报告
cat docs/DOCS_CLEANUP_REPORT.md
```

---

**创建者**: 徐健 (xujian519@gmail.com)
**创建时间**: 2026-04-22
**状态**: 📋 计划中
