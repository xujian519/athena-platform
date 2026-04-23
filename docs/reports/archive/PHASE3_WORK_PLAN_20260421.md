# 第3阶段：核心整合 - 工作计划

> **开始时间**: 2026-04-21
> **阶段**: 第3阶段 - 核心整合
> **周期**: 4-6周（2026-04-21 ~ 2026-05-31）
> **风险**: ★★★★☆（高）
> **收益**: ★★★★★（整合专利代码，优化LLM服务）

---

## 📊 目录分析结果

### 专利相关目录统计

**总计**: 37个专利相关目录

**主要目录**（按代码量排序）:

| 目录 | 代码行数 | 大小 | 说明 |
|------|---------|------|------|
| patent-platform | 79,061 | 7.1M | 专利平台应用（最大） |
| core/patent | 53,617 | 29M | 核心专利处理（第二） |
| patent_hybrid_retrieval | 7,715 | 372K | 专利混合检索 |
| tests/unit/patent | 4,584 | 172K | 专利单元测试 |
| tools/patent-guideline-system | 3,409 | 23M | 专利指南系统 |
| core/knowledge/patent_analysis | 3,113 | 196K | 专利分析知识 |
| apps/patent-platform | 955 | 96K | 专利平台应用（新版） |
| services/xiaona-patents | 366 | 12K | 小娜专利服务 |
| tests/patent | 721 | 28K | 专利测试 |

**总代码量**: 约150,000+行

---

## 🎯 工作目标

### 主要目标
1. 创建patents/统一目录
2. 整合所有专利相关代码（37个目录 → 1个目录）
3. 更新所有导入路径
4. 保持功能完整性
5. 提高代码可维护性

### 成功标准
- ✅ 所有专利代码整合到patents/目录
- ✅ 导入路径全部更新
- ✅ 测试套件全部通过
- ✅ 功能验证通过
- ✅ 性能无明显下降

---

## 🏗️ 新目录结构设计

### patents/ 统一目录

```
patents/
├── README.md                           # 迁移指南和说明
├── core/                              # 核心专利处理
│   ├── __init__.py
│   ├── analyzer/                      # 专利分析
│   │   ├── __init__.py
│   │   ├── patent_analyzer.py
│   │   ├── novelty_analyzer.py
│   │   └── creativity_analyzer.py
│   ├── drawing/                       # 专利附图
│   │   ├── __init__.py
│   │   ├── drawing_parser.py
│   │   └── drawing_generator.py
│   ├── retrieval/                     # 专利检索
│   │   ├── __init__.py
│   │   ├── patent_retriever.py
│   │   └── patent_searcher.py
│   ├── translation/                   # 专利翻译
│   │   ├── __init__.py
│   │   └── patent_translator.py
│   ├── validation/                    # 专利验证
│   │   ├── __init__.py
│   │   └── patent_validator.py
│   └── knowledge/                     # 专利知识图谱
│       ├── __init__.py
│       └── patent_kg.py
│
├── retrieval/                         # 检索引擎
│   ├── __init__.py
│   ├── hybrid/                        # 混合检索
│   │   ├── __init__.py
│   │   ├── hybrid_retriever.py
│   │   └── query_processor.py
│   ├── vector/                        # 向量检索
│   │   ├── __init__.py
│   │   └── vector_retriever.py
│   └── keyword/                       # 关键词检索
│       ├── __init__.py
│       └── keyword_retriever.py
│
├── platform/                          # 平台应用
│   ├── __init__.py
│   ├── api/                           # API层
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── models.py
│   ├── services/                      # 业务逻辑
│   │   ├── __init__.py
│   │   ├── patent_service.py
│   │   └── analysis_service.py
│   └── models/                        # 数据模型
│       ├── __init__.py
│       └── patent_model.py
│
├── webui/                             # Web界面
│   ├── __init__.py
│   ├── frontend/                      # 前端代码
│   │   ├── src/
│   │   ├── package.json
│   │   └── vite.config.js
│   └── backend/                       # 后端API
│       ├── __init__.py
│       └── api.py
│
├── workflows/                         # 工作流
│   ├── __init__.py
│   ├── oa_review/                     # 审查意见
│   │   ├── __init__.py
│   │   └── oa_review_workflow.py
│   ├── invalidation/                  # 无效宣告
│   │   ├── __init__.py
│   │   └── invalidation_workflow.py
│   └── litigation/                    # 诉讼支持
│       ├── __init__.py
│       └── litigation_workflow.py
│
├── integrations/                      # 第三方集成
│   ├── __init__.py
│   ├── pqai/                          # PQAI集成
│   │   ├── __init__.py
│   │   └── pqai_client.py
│   ├── google_patents/                 # Google专利集成
│   │   ├── __init__.py
│   │   └── google_client.py
│   └── cipo/                          # CIPO集成
│       ├── __init__.py
│       └── cipo_client.py
│
├── services/                          # 服务层
│   ├── __init__.py
│   ├── xiaona_patents/               # 小娜专利服务
│   │   ├── __init__.py
│   │   └── api.py
│   └── patent_downloader/            # 专利下载器MCP
│       ├── __init__.py
│       └── downloader.py
│
├── tools/                             # 工具集
│   ├── __init__.py
│   ├── guideline_system/             # 指南系统
│   │   ├── __init__.py
│   │   └── guideline_checker.py
│   └── patent_search/                 # 专利搜索工具
│       ├── __init__.py
│       └── search_cli.py
│
├── tests/                             # 测试
│   ├── __init__.py
│   ├── unit/                          # 单元测试
│   │   ├── __init__.py
│   │   └── test_patent_analyzer.py
│   └── integration/                   # 集成测试
│       ├── __init__.py
│       └── test_retriever.py
│
└── docs/                              # 文档
    ├── README.md                       # 总览
    ├── guides/                        # 使用指南
    │   ├── retrieval_guide.md
    │   ├── analysis_guide.md
    │   └── platform_guide.md
    └── api/                           # API文档
        ├── retrieval_api.md
        └── platform_api.md
```

---

## 📋 迁移计划

### Week 1: Day 3-5 - 迁移核心模块

**目标**: 迁移core/patent/到patents/core/

**步骤**:
1. 创建patents/目录结构
2. 复制core/patent/到patents/core/
3. 更新导入路径
4. 运行测试验证

### Week 1: Day 6-7 - 迁移检索引擎

**目标**: 迁移patent_hybrid_retrieval/到patents/retrieval/

**步骤**:
1. 复制检索代码
2. 更新导入路径
3. 验证检索功能

### Week 2: Day 8-14 - 迁移平台和应用

**目标**: 迁移patent-platform/、apps/patent-platform/

**步骤**:
1. 迁移平台代码
2. 迁移Web界面
3. 更新服务配置

### Week 2: Day 15-21 - 迁移工作流和集成

**目标**: 迁移openspec-oa-workflow/、services/

**步骤**:
1. 迁移工作流代码
2. 迁移MCP服务器
3. 验证集成

### Week 2: Day 22- 完成整合

**目标**: 清理旧目录，验证系统

**步骤**:
1. 删除符号链接
2. 删除旧目录
3. 运行完整测试
4. 部署验证

---

## ⚠️ 风险控制

### 回滚策略

**每个迁移步骤都可回滚**:

```bash
# 如果迁移失败
rm -rf patents/
git checkout <commit-before-migration>

# 从备份恢复
cp -r /tmp/patent_migration_backup_*/* .
```

### 验证检查点

每个迁移完成后：
- [ ] 运行单元测试
- [ ] 运行集成测试
- [ ] 验证功能正常
- [ ] 检查性能无明显下降

---

## 📊 预期收益

### 代码组织
- **迁移前**: 37个分散目录
- **迁移后**: 1个统一patents/目录
- **改善**: 代码集中度提升100%

### 可维护性
- **导入路径**: 统一到patents.*
- **文档**: 集中在patents/docs/
- **测试**: 集中在patents/tests/

### 性能
- **预期影响**: 性能无明显下降
- **优化机会**: 整合后可优化导入路径

---

**计划创建时间**: 2026-04-21
**计划执行周期**: 4-6周
**下一步**: 开始迁移核心模块（core/patent/）
