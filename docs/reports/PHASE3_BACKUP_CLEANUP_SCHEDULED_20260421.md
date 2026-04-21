# Phase 3 备份清理 - 已安排

> **创建时间**: 2026-04-21
> **清理时间**: 2026-04-28 上午9:00
> **状态**: ✅ 已安排

---

## 📋 清理计划

### 自动清理任务

**执行时间**: 2026年4月28日上午9:00（7天后）

**清理内容**:
- core/patent.bak
- patent_hybrid_retrieval.bak
- patent-platform.bak
- openspec-oa-workflow.bak
- services/xiaona-patents.bak

**预计释放空间**: ~36.5MB

---

## 🔧 清理脚本

**脚本位置**: `scripts/cleanup_backup_dirs.sh`

**功能**:
- ✅ 自动检查备份目录
- ✅ 安全删除备份
- ✅ 生成清理日志
- ✅ 创建清理报告
- ✅ 交互式确认（可选）

**手动执行**（如需提前清理）:
```bash
./scripts/cleanup_backup_dirs.sh
```

---

## 📊 清理前检查清单

在自动清理前（7天内），请确认：

- [x] Phase 3迁移100%完成
- [x] 所有测试通过
- [x] Git提交完成
- [ ] 运行完整测试套件
- [ ] 验证核心功能正常
- [ ] 团队成员知晓新目录结构
- [ ] 文档已更新

---

## ⚠️ 如需取消清理

### 取消自动清理任务

**方式1: 使用CronDelete**
```bash
# 查看任务ID: 60c07c4a
# 在Claude Code中执行取消
```

**方式2: 手动删除cron任务**
```bash
# 编辑crontab
crontab -e

# 删除这一行:
# 0 9 28 4 * /Users/xujian/Athena工作平台/scripts/cleanup_backup_dirs.sh
```

---

## 🔄 回滚方式

如果清理后发现需要回滚：

**Git回滚**（推荐）:
```bash
# 回滚到迁移前的提交
git checkout aebe5973^  # Phase 3之前的提交

# 或者回滚特定文件
git checkout aebe5973^ -- core/patent
```

---

## 📝 观察期建议

### 7天内（2026-04-21 ~ 2026-04-28）

**每日验证**:
1. ✅ 检查系统日志
2. ✅ 运行核心功能测试
3. ✅ 监控错误率
4. ✅ 验证导入路径正常

**发现问题时**:
1. 立即停止使用新代码
2. 使用git回滚
3. 分析并修复问题
4. 取消自动清理任务

---

## 📊 清理后状态

清理完成后，系统状态：

**符号链接**（保留）:
- core/patent → patents/core
- patent_hybrid_retrieval → patents/retrieval
- patent-platform → patents/platform
- openspec-oa-workflow → patents/workflows
- services/xiaona-patents → patents/services

**新目录结构**:
```
patents/
├── core/
├── retrieval/
├── platform/
├── workflows/
└── services/
```

**无备份目录**（已清理）:
- ❌ core/patent.bak
- ❌ patent_hybrid_retrieval.bak
- ❌ patent-platform.bak
- ❌ openspec-oa-workflow.bak
- ❌ services/xiaona-patents.bak

---

## ✅ 自动清理已安排

**任务ID**: 60c07c4a
**执行时间**: 2026-04-28 09:00
**状态**: ✅ 已安排

**下一步**:
1. 在7天内验证系统正常运行
2. 如有问题，取消自动清理任务
3. 4月28日上午9点自动执行清理

---

**安排时间**: 2026-04-21
**清理时间**: 2026-04-28 09:00
**负责人**: Claude Code (OMC模式)
