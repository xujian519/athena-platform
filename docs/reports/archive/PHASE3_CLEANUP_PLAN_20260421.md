# Phase 3 清理计划

> **创建时间**: 2026-04-21
> **状态**: 待确认

---

## 📋 备份目录清单

### 已发现的备份目录 (5个)

| 备份目录 | 原始目录 | 大小 | 状态 |
|---------|---------|------|------|
| core/patent.bak | core/patent/ | ~29M | ✅ 已备份 |
| patent_hybrid_retrieval.bak | patent_hybrid_retrieval/ | ~372K | ✅ 已备份 |
| patent-platform.bak | patent-platform/ | ~7.1M | ✅ 已备份 |
| openspec-oa-workflow.bak | openspec-oa-workflow/ | ~192K | ✅ 已备份 |
| services/xiaona-patents.bak | services/xiaona-patents/ | ~12K | ✅ 已备份 |

**总大小**: ~36.5MB

---

## 🧹 清理选项

### 选项A: 立即删除备份（激进）

**优点**:
- ✅ 立即释放磁盘空间 (~36.5MB)
- ✅ 代码库更整洁
- ✅ 减少混淆

**缺点**:
- ⚠️ 无法快速回滚到旧目录
- ⚠️ 需要依赖git来回滚

**执行方式**:
```bash
# 删除所有备份
rm -rf core/patent.bak
rm -rf patent_hybrid_retrieval.bak
rm -rf patent-platform.bak
rm -rf openspec-oa-workflow.bak
rm -rf services/xiaona-patents.bak
```

---

### 选项B: 保留备份7天（保守）

**优点**:
- ✅ 可以快速回滚
- ✅ 有观察期验证迁移
- ✅ 更安全

**缺点**:
- ❌ 占用磁盘空间
- ❌ 代码库有额外目录

**执行方式**:
```bash
# 7天后删除
# 使用find命令自动清理
find . -maxdepth 1 -name "*.bak" -type d -mtime +7 -exec rm -rf {} \;
```

---

### 选项C: 移动到临时目录（折中）

**优点**:
- ✅ 保留备份但不影响项目
- ✅ 可以在需要时恢复
- ✅ 项目目录更整洁

**缺点**:
- ❌ 备份移到项目外
- ❌ 需要记住备份位置

**执行方式**:
```bash
# 创建临时备份目录
mkdir -p /tmp/patent_migration_backup_20260421

# 移动所有备份到临时目录
mv core/patent.bak /tmp/patent_migration_backup_20260421/
mv patent_hybrid_retrieval.bak /tmp/patent_migration_backup_20260421/
mv patent-platform.bak /tmp/patent_migration_backup_20260421/
mv openspec-oa-workflow.bak /tmp/patent_migration_backup_20260421/
mv services/xiaona-patents.bak /tmp/patent_migration_backup_20260421/
```

---

## 🎯 推荐方案

**推荐**: 选项B - 保留备份7天

**理由**:
1. **安全第一**: 有观察期可以验证迁移效果
2. **磁盘空间小**: 36.5MB对现代系统可忽略
3. **Git保护**: 即使删除备份，也可以通过git回滚
4. **自动化清理**: 7天后自动删除，无需手动管理

---

## 📊 验证检查清单

在删除备份前，请确认：

- [x] Phase 3迁移100%完成
- [x] 所有测试通过
- [x] Git提交完成
- [ ] 运行完整测试套件
- [ ] 验证核心功能正常
- [ ] 团队成员知晓新目录结构
- [ ] 文档已更新

---

## ⚠️ 回滚方式

如果删除备份后需要回滚：

**方式1: Git回滚（推荐）**
```bash
# 回滚到迁移前的提交
git checkout <commit-before-phase3>

# 或者回滚特定文件
git checkout <commit-before-phase3> -- core/patent
```

**方式2: 从备份恢复（如果备份存在）**
```bash
# 恢复特定备份
mv core/patent.bak/* core/patent/
```

---

## 🚀 执行建议

**如果一切正常**:
1. 运行完整测试套件（1-2天观察期）
2. 验证核心功能
3. 7天后自动删除备份

**如果发现问题**:
1. 立即停止使用新代码
2. 从备份或git恢复
3. 分析问题并修复

---

**建议**: 保守策略，保留备份7天 ✅

**创建时间**: 2026-04-21
**负责人**: Claude Code (OMC模式)
