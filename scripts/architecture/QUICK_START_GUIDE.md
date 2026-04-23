# Athena平台架构优化 - 快速启动指南

> **最后更新**: 2026-04-23
> **当前阶段**: 阶段0-1（80%完成）
> **下一阶段**: 完成阶段1剩余工作

---

## 🚀 快速开始

### 查看执行摘要
```bash
cat scripts/architecture/ARCHITECTURE_OPTIMIZATION_EXECUTION_SUMMARY.md
```

### 查看完整路线图
```bash
cat scripts/architecture/IMPLEMENTATION_ROADMAP.md
```

### 创建新快照
```bash
bash scripts/architecture/create_snapshot.sh
```

### 回滚到快照
```bash
bash scripts/architecture/rollback.sh
```

---

## 📊 当前状态

| 阶段 | 名称 | 状态 | 完成度 |
|-----|------|------|--------|
| 0 | 准备工作 - 建立安全网 | ✅ 完成 | 100% |
| 1 | 消除循环依赖 - 依赖倒置 | ⚠️ 部分完成 | 80% |
| 2 | 核心组件重组 - 领域划分 | ⏳ 待开始 | 0% |
| 3 | 顶层目录聚合 - 高内聚 | ⏳ 待开始 | 0% |
| 4 | 数据治理 - 存储优化 | ⏳ 待开始 | 0% |

---

## 🔧 常用命令

### 依赖分析
```bash
# 运行完整依赖分析
python3 scripts/architecture/analyze_dependencies.py

# 查看JSON报告
cat reports/architecture/dependency_graph.json | jq '.stats'

# 查看循环依赖
cat reports/architecture/dependency_graph.json | jq '.circular_dependencies'

# 查看架构违规
cat reports/architecture/dependency_graph.json | jq '.violations'
```

### Import迁移
```bash
# 运行阶段1修复
python3 scripts/architecture/migrate/phase1_fix_imports.py

# 验证阶段1
bash scripts/architecture/migrate/verify_phase1.sh
```

### 验证检查
```bash
# 检查services依赖
grep -r "from services\." core/ --include="*.py"

# 检查domains依赖
grep -r "from domains\." core/ --include="*.py"

# 统计core子目录数
ls -d core/*/ | wc -l
```

---

## 📁 关键文件位置

### 配置文件
- `config/dependency_injection.py` - 依赖注入配置
- `config/agent_registry.json` - 智能体注册表

### 接口定义
- `core/interfaces/__init__.py` - 接口导出
- `core/interfaces/vector_store.py` - 向量存储接口
- `core/interfaces/knowledge_base.py` - 知识库接口
- `core/interfaces/patent_service.py` - 专利服务接口

### 报告文件
- `reports/architecture/dependency_graph.json` - 依赖关系
- `reports/architecture/dependency_matrix.csv` - 依赖矩阵
- `reports/architecture/phase1/migration_report_*.md` - 迁移报告

### 备份文件
- `backups/architecture-snapshots/snapshot-*.tar.gz` - 代码快照
- `backups/phase1-migration/` - 阶段1文件备份

---

## ⚠️ 故障排除

### 问题：验证失败
```bash
# 检查剩余违规
grep -r "from services\." core/ --include="*.py" | wc -l

# 查看具体违规
grep -r "from services\." core/ --include="*.py"
```

### 问题：需要回滚
```bash
# 查看可用快照
ls -lh backups/architecture-snapshots/

# 执行回滚
bash scripts/architecture/rollback.sh
```

### 问题：语法错误导致迁移失败
```bash
# 检查语法错误
python3 -m py_compile core/vector_db/hybrid_storage_manager.py

# 跳过该文件，手动处理
```

---

## 📞 获取帮助

- **完整文档**: `scripts/architecture/IMPLEMENTATION_ROADMAP.md`
- **执行摘要**: `scripts/architecture/ARCHITECTURE_OPTIMIZATION_EXECUTION_SUMMARY.md`
- **维护者**: 徐健 (xujian519@gmail.com)

---

## 🎯 下一步行动

1. ✅ 查看执行摘要
2. ⏳ 完成阶段1剩余8个违规（可选）
3. ⏳ 运行测试验证
4. ⏳ 启动阶段2：核心组件重组

---

**快速命令**:
```bash
# 一键查看状态
echo "阶段状态:" && \
echo "0: $(ls backups/architecture-snapshots/ | wc -l) 个快照" && \
echo "1: $(grep -r "from services\." core/ --include="*.py" | wc -l) 个违规" && \
echo "core: $(ls -d core/*/ | wc -l) 个子目录"
```

*更新时间: 2026-04-23*
