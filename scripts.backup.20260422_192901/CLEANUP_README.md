# Athena工作平台 - 项目清理脚本使用指南

> **版本**: v1.0
> **日期**: 2026-04-20
> **作者**: Claude Code

---

## 📋 概述

本项目包含两个自动化脚本，用于清理和回退项目中的废弃、冗余和过期文件：

1. **cleanup_project.sh** - 主清理脚本
2. **rollback_cleanup.sh** - 回滚脚本

---

## 🚀 快速开始

### 执行清理

```bash
cd /Users/xujian/Athena工作平台
./scripts/cleanup_project.sh
```

### 回滚操作

```bash
cd /Users/xujian/Athena工作平台
./scripts/rollback_cleanup.sh
```

---

## 📖 详细说明

### cleanup_project.sh - 清理脚本

#### 功能特性

✅ **安全备份**: 自动备份所有删除的文件
✅ **分步确认**: 每个关键步骤都需要用户确认
✅ **详细日志**: 记录所有操作到日志文件
✅ **智能检测**: 自动检测运行中的进程，避免误删
✅ **压缩备份**: 清理完成后自动压缩备份文件

#### 清理步骤

| 步骤 | 操作 | 说明 | 风险等级 |
|-----|------|------|---------|
| 1/6 | 清理备份文件 | 删除.bak/.backup文件 | 🟢 低 |
| 2/6 | 清理.backup目录 | 删除整个备份目录 | 🟢 低 |
| 3/6 | 清理PID文件 | 检查进程后删除过期PID | 🟡 中 |
| 4/6 | 清理临时数据 | 删除temp目录下的临时文件 | 🟡 中 |
| 5/6 | 清理测试报告 | 删除90天前的测试报告 | 🟢 低 |
| 6/6 | 清理Python缓存 | 删除__pycache__等缓存 | 🟢 低 |

#### 清理内容

**1. 备份文件**:
- `requirements_backup.txt`
- `core/llm/response_cache.py.backup`
- `core/patent/infringement/infringement_determiner.py.bak`
- `core/agents/xiaona_legal.py.bak`
- `core/search/enhanced_hybrid_search.py.backup`

**2. 备份目录**:
- `.backup/` (整个目录)

**3. PID文件**:
- `pids/memory_system.pid`
- `pids/knowledge_graph.pid`
- `pids/xiaonuo.pid`
- `pids/xiaona.pid`
- `tasks/**/*.pid`

**4. 临时数据**:
- `data/trademark_rules/temp/` (整个目录)

**5. 测试报告**:
- `tests/results/*.json` (90天前的文件)

**6. Python缓存**:
- `**/__pycache__/`
- `**/*.pyc`
- `**/*.pyo`

#### 执行流程

```
开始
  ↓
创建备份目录
  ↓
清理备份文件 (需确认)
  ↓
清理.backup目录
  ↓
清理PID文件 (检测进程状态)
  ↓
清理临时数据文件
  ↓
清理历史测试报告
  ↓
清理Python缓存 (需确认)
  ↓
修复Git状态 (可选，需确认)
  ↓
压缩备份文件
  ↓
生成清理报告
  ↓
完成
```

#### 输出文件

**日志文件**: `cleanup_log_YYYYMMDD_HHMMSS.log`
- 记录所有操作和决策
- 可用于审计和问题排查

**备份文件**: `.cleanup_backup_YYYYMMDD_HHMMSS.tar.gz`
- 包含所有被删除文件的完整备份
- 可用于回滚恢复

---

### rollback_cleanup.sh - 回滚脚本

#### 功能特性

✅ **备份列表**: 显示所有可用的备份
✅ **选择性恢复**: 选择特定备份进行恢复
✅ **安全检查**: 检测文件冲突，避免覆盖
✅ **详细报告**: 显示恢复和跳过的文件统计

#### 使用场景

- 误删了重要文件
- 清理后发现问题，需要恢复
- 需要查看被删除文件的内容

#### 执行流程

```
开始
  ↓
列出所有可用备份
  ↓
用户选择备份
  ↓
解压备份（如需要）
  ↓
确认回滚操作
  ↓
逐个恢复文件
  ↓
处理文件冲突
  ↓
删除已恢复的备份（可选）
  ↓
完成
```

---

## 🛡️ 安全机制

### 1. 自动备份

所有删除操作前都会先备份到：
```
.cleanup_backup_YYYYMMDD_HHMMSS/
├── requirements_backup.txt
├── core/
│   ├── llm/response_cache.py.backup
│   └── agents/xiaona_legal.py.bak
└── pids/
    └── xiaona.pid
```

### 2. 交互式确认

关键操作需要用户确认：
- 清理Python缓存
- 清理PID文件（检测到运行中的进程）
- 修复Git状态
- 回滚操作

### 3. 智能检测

- **进程检测**: 删除PID文件前检查进程是否运行
- **文件冲突**: 回滚时检测目标文件是否存在
- **自动跳过**: 不存在的文件会自动跳过并记录

### 4. 完整日志

所有操作都记录到日志文件，包括：
- 时间戳
- 操作类型
- 文件路径
- 文件大小
- 决策结果

---

## 📊 清理效果

### 预期收益

| 指标 | 清理前 | 清理后 | 改善 |
|-----|--------|--------|------|
| 废弃文件 | 30+ | 0 | ✅ 100% |
| 冗余配置 | 6个 | 0 | ✅ 100% |
| 磁盘空间 | - | -171MB | ✅ 节省 |
| Git状态 | 异常 | 正常 | ✅ 修复 |

### 清理报告示例

```
📊 清理统计
============
- 清理文件总数: 42
- 备份位置: .cleanup_backup_20260420_143022
- 备份大小: 125M
- 日志文件: cleanup_log_20260420_143022.log

✅ 清理完成！
如需回滚，请运行:
  tar -xzf ".cleanup_backup_20260420_143022.tar.gz" -C /
```

---

## ⚙️ 定制化

### 修改清理规则

编辑 `cleanup_project.sh`，修改以下数组：

```bash
# 添加自定义备份文件
local backup_files=(
    "your_backup_file.txt"
    "another_backup.dat"
)

# 添加自定义临时目录
local temp_dirs=(
    "data/your_temp_dir"
    "cache/another_temp"
)
```

### 调整保留时间

修改测试报告保留时间（默认90天）：

```bash
# 从90天改为30天
find tests/results/ -name "*.json" -type f -mtime +30
```

### 定时执行

添加到crontab，每月自动清理：

```bash
# 编辑crontab
crontab -e

# 添加以下行（每月1号凌晨执行）
0 0 1 * * /Users/xujian/Athena工作平台/scripts/cleanup_project.sh
```

---

## 🔧 故障排查

### 问题1: 权限错误

**错误信息**: `Permission denied`

**解决方案**:
```bash
chmod +x scripts/cleanup_project.sh
chmod +x scripts/rollback_cleanup.sh
```

### 问题2: Git状态异常

**错误信息**: 检测到已删除但未暂存的文件

**解决方案**:
1. 运行清理脚本时选择"修复Git状态"
2. 或手动执行：
   ```bash
   git status
   git rm $(git status | grep "deleted:" | awk '{print $2}')
   ```

### 问题3: 备份文件损坏

**错误信息**: 无法解压备份文件

**解决方案**:
1. 检查备份完整性：
   ```bash
   tar -tzf .cleanup_backup_*.tar.gz
   ```
2. 如果备份损坏，从Git历史恢复：
   ```bash
   git log --diff-filter=D --summary
   git checkout <commit>~1 -- <file>
   ```

### 问题4: 进程仍在运行

**警告信息**: 检测到运行中的进程

**解决方案**:
1. 先停止进程：
   ```bash
   # 查找进程
   ps aux | grep -E "(xiaona|xiaonuo)"

   # 停止进程
   kill <PID>
   ```
2. 然后重新运行清理脚本

---

## 📝 注意事项

### ⚠️ 执行前必读

1. **确认工作目录**: 必须在项目根目录执行脚本
2. **备份重要数据**: 脚本会自动备份，但建议手动备份关键数据
3. **停止运行中的服务**: 避免文件被占用
4. **检查Git状态**: 确保没有未提交的重要更改

### ⚠️ 清理后操作

1. **检查日志文件**: 确认所有操作符合预期
2. **测试系统功能**: 确保清理后系统正常运行
3. **提交Git更改**: 如果启用了Git状态修复
4. **保留备份文件**: 至少保留一周，确认无问题后再删除

### ⚠️ 不清理的内容

脚本**不会**清理以下内容：
- 代码文件（.py, .go, .js等）
- 配置文件（.env, config.yaml等）
- 文档文件（README.md, docs/等）
- 数据文件（.db, .json等，除非在temp目录）
- 模型文件（models/目录）

---

## 🎯 最佳实践

### 1. 定期清理

建议每月执行一次清理脚本：
```bash
# 添加到日历提醒
每月1号提醒：执行项目清理
```

### 2. 版本控制

将清理脚本纳入版本控制：
```bash
git add scripts/cleanup_project.sh
git add scripts/rollback_cleanup.sh
git add scripts/CLEANUP_README.md
git commit -m "docs: 添加项目清理脚本"
```

### 3. 监控磁盘空间

定期检查项目大小变化：
```bash
# 查看项目大小
du -sh /Users/xujian/Athena工作平台

# 查看最大目录
du -h --max-depth=2 /Users/xujian/Athena工作平台 | sort -hr | head -20
```

### 4. 维护.gitignore

确保.gitignore包含以下规则：
```gitignore
# Python缓存
__pycache__/
*.py[cod]
*.pyo

# 备份文件
*.bak
*.backup
.backup/

# PID文件
pids/*.pid
**/*.pid

# 临时文件
data/trademark_rules/temp/
*.tmp

# 测试报告
tests/results/*.json

# 清理备份
.cleanup_backup_*/
cleanup_log_*.log
```

---

## 📞 支持与反馈

### 获取帮助

如果遇到问题：
1. 查看日志文件：`cleanup_log_*.log`
2. 查看备份内容：`tar -tzf .cleanup_backup_*.tar.gz`
3. 查看Git状态：`git status`

### 改进建议

欢迎提出改进建议：
- 添加新的清理规则
- 优化清理策略
- 改进用户体验
- 增强安全性

---

## 📄 更新日志

### v1.0 (2026-04-20)

**初始版本发布**:
- ✅ 6大清理步骤
- ✅ 自动备份和压缩
- ✅ 完整的回滚支持
- ✅ 详细的日志记录
- ✅ 交互式确认机制

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-20
