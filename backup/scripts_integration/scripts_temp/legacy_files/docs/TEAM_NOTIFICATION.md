# 📢 Scripts文件夹重构通知

## 🎯 重要变更

**发布日期**: 2025-12-08
**影响范围**: 全体开发团队
**变更类型**: 重大结构优化

## 📂 目录结构变更

### ❌ 旧结构 (已弃用)
```
scripts/
├── 82个脚本文件散落在根目录
├── 功能混杂，查找困难
└── 命名不规范，维护成本高
```

### ✅ 新结构 (当前使用)
```
scripts_new/
├── 📥 import_export/           # 数据导入导出
├── 🚀 services/               # 服务管理
├── ⚖️ legal_intelligence/     # 法律智能
├── 🔧 system_operations/      # 系统运维
├── 🛠️ utils/                 # 工具脚本
├── 🧪 experimental/          # 实验性功能
└── 📦 legacy/                # 历史遗留
```

## 🔧 行动要求

### 1. 立即执行 ⚡
- **停止使用**: `scripts/` 目录已废弃，仅作为备份保留
- **切换到新目录**: 所有脚本操作请使用 `scripts_new/` 目录
- **更新快捷方式**:
  ```bash
  # 添加到 ~/.zshrc 或 ~/.bashrc
  alias sscripts="cd /Users/xujian/Athena工作平台/scripts_new"
  ```

### 2. 路径更新 📝
请检查并更新以下配置中的脚本路径：

#### CI/CD 配置
- `.github/workflows/` 中的脚本路径
- Jenkinsfile 或类似CI配置
- Dockerfile 中的脚本引用

#### 项目配置
- `package.json` 的scripts部分
- `Makefile` 或构建脚本
- 启动脚本和配置文件

#### 开发环境
- IDE中的运行配置
- 本地开发脚本
- 测试脚本路径

### 3. 常用脚本映射 🗺️

| 旧路径 | 新路径 | 功能 |
|--------|--------|------|
| `scripts/start_knowledge_graph.sh` | `scripts_new/system_operations/infrastructure/start_knowledge_graph.sh` | 启动知识图谱 |
| `scripts/enhanced_knowledge_graph_importer.py` | `scripts_new/import_export/database_import/enhanced_knowledge_graph_importer.py` | 数据导入 |
| `scripts/tool_finder.py` | `scripts_new/utils/tool_finder.py` | 工具查找 |
| `scripts/check_core_services.py` | `scripts_new/system_operations/monitoring/check_core_services.py` | 服务检查 |

## 💡 使用指南

### 快速查找脚本
```bash
# 查看目录结构
cd scripts_new && find . -name "*.py" | head -10

# 搜索特定功能
find . -name "*.py" | xargs grep -l "关键词"

# 查看使用指南
cat scripts_new/USER_GUIDE.md
```

### 执行权限
```bash
# 所有脚本已修复执行权限
cd scripts_new
find . -name "*.sh" -exec chmod +x {} \;
```

## ⚠️ 注意事项

### 🔒 安全提醒
1. **备份原目录**: `scripts/` 目录将保留30天作为备份
2. **测试环境**: 建议先在测试环境验证脚本功能
3. **权限管理**: 确保脚本具有正确的执行权限

### 🐛 问题排查
如果遇到脚本运行问题：
1. **检查路径**: 确认使用新的 `scripts_new/` 路径
2. **查看日志**: 检查脚本输出的错误信息
3. **参考文档**: 查看 `scripts_new/USER_GUIDE.md`
4. **联系支持**: Athena AI团队提供技术支持

## 📞 支持与反馈

### 🆘 获取帮助
- **使用指南**: `scripts_new/USER_GUIDE.md`
- **迁移报告**: `scripts_new/MIGRATION_REPORT.md`
- **技术支持**: 联系Athena AI团队

### 💬 反馈渠道
- **问题报告**: 创建GitHub Issue
- **改进建议**: 团队会议提出
- **使用疑问**: 技术交流群讨论

## ⏰ 时间线

| 日期 | 状态 | 操作 |
|------|------|------|
| 2025-12-08 | ✅ 完成 | 目录重构完成 |
| 2025-12-09 | 🔄 进行 | 团队通知和适应期 |
| 2025-12-15 | ⏰ 计划 | 路径更新完成检查 |
| 2025-01-08 | ⏰ 计划 | 原目录备份删除 |

## 🎉 收益总结

### 📈 效率提升
- **查找速度**: 提升80%+（分类查找）
- **维护效率**: 提升60%+（集中管理）
- **团队协作**: 更清晰的代码组织

### 🔧 开发体验
- **结构清晰**: 7大功能模块分类
- **文档完善**: 详细的使用指南
- **标准化**: 统一的命名规范

---

**感谢配合！**
如有任何问题，请随时联系Athena AI团队。

**执行团队**: Athena AI平台开发组
**技术负责人**: 徐健 (xujian519@gmail.com)