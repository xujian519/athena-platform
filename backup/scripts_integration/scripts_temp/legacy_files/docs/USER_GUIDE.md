# Scripts文件夹使用指南

## 🎯 快速导航

### 📂 常用脚本快速查找

| 需求 | 脚本位置 | 推荐脚本 |
|------|----------|----------|
| **启动服务** | `system_operations/infrastructure/` | `start_knowledge_graph.sh` |
| **数据导入** | `import_export/database_import/` | `enhanced_knowledge_graph_importer.py` |
| **专利分析** | `legal_intelligence/patent_analysis/` | `super_fast_patent_processor.py` |
| **系统监控** | `system_operations/monitoring/` | `check_core_services.py` |
| **工具脚本** | `utils/` | `tool_finder.py` |

## 🏗️ 目录详解

### 1. 📥 import_export/ - 数据导入导出

#### database_import/ - 数据库导入
```bash
# 快速导入知识图谱
cd scripts_new/import_export/database_import/
python3 enhanced_knowledge_graph_importer.py

# 批量导入专利数据
python3 import_all_patent_triples.py
```

#### vector_migration/ - 向量数据迁移
```bash
# 创建向量索引
cd scripts_new/import_export/vector_migration/
python3 create_vector_indexes.py

# 优化向量数据库
python3 vector_database_optimizer.py
```

### 2. 🚀 services/ - 服务管理

#### api_services/ - API服务
```bash
# 启动知识图谱API服务
cd scripts_new/services/api_services/
python3 knowledge_graph_api_service.py

# 启动专利感知服务
python3 enhanced_patent_perception_service.py
```

#### crawler_services/ - 爬虫服务
```bash
# 启动生产环境爬虫
cd scripts_new/services/crawler_services/
python3 production_crawler_launcher.py
```

### 3. ⚖️ legal_intelligence/ - 法律智能

#### knowledge_graph/ - 知识图谱构建
```bash
# 构建法律知识图谱
cd scripts_new/legal_intelligence/knowledge_graph/
python3 legal_knowledge_graph_builder.py

# 优化知识图谱
python3 legal_knowledge_graph_optimizer.py
```

#### patent_analysis/ - 专利分析
```bash
# 快速专利处理
cd scripts_new/legal_intelligence/patent_analysis/
python3 super_fast_patent_processor.py

# 更新专利规则
python3 update_patent_rules_complete.py
```

### 4. 🔧 system_operations/ - 系统运维

#### infrastructure/ - 基础设施
```bash
# 启动完整系统
cd scripts_new/system_operations/infrastructure/
bash start_intelligence_system.sh

# 拉取Docker镜像
bash pull_essential_images.sh
```

#### monitoring/ - 系统监控
```bash
# 检查核心服务
cd scripts_new/system_operations/monitoring/
python3 check_core_services.py

# 执行计划维护
python3 scheduled_maintenance.py
```

### 5. 🛠️ utils/ - 工具脚本

```bash
# 查找工具脚本
cd scripts_new/utils/
python3 tool_finder.py

# 组织项目结构
python3 organize_root_directory.py

# 管理SQLite知识图谱
python3 sqlite_knowledge_graph_manager.py
```

## 💡 使用技巧

### 1. 快速启动脚本
```bash
# 创建快捷方式
echo 'alias sscripts="cd /Users/xujian/Athena工作平台/scripts_new"' >> ~/.zshrc

# 重新加载配置
source ~/.zshrc
```

### 2. 批量执行脚本
```bash
# 批量启动服务
cd scripts_new/system_operations/infrastructure/
for script in start_*.sh; do bash "$script"; done
```

### 3. 查看脚本帮助
```bash
# 查看脚本说明
cd scripts_new/
find . -name "*.py" -exec head -10 {} \; | grep -E "(\"\"\"|#.*功能|def.*help)"
```

## ⚠️ 重要提醒

### 安全使用
1. **备份**: 执行重要脚本前先备份数据
2. **测试**: 在测试环境验证脚本功能
3. **权限**: 确保脚本具有执行权限
4. **依赖**: 检查Python环境和依赖包

### 常见问题

**Q: 脚本执行权限问题？**
```bash
# 添加执行权限
chmod +x scripts_new/**/*.sh
```

**Q: Python路径问题？**
```bash
# 使用项目Python环境
PYTHONPATH=/Users/xujian/Athena工作平台 python3 script.py
```

**Q: 依赖包缺失？**
```bash
# 安装依赖
pip3 install -r requirements.txt
```

## 📚 最佳实践

### 1. 脚本执行流程
1. **检查环境** → `check_core_services.py`
2. **准备数据** → `import_export/database_import/`
3. **启动服务** → `system_operations/infrastructure/`
4. **监控系统** → `system_operations/monitoring/`

### 2. 开发新脚本
- 放在合适的分类目录下
- 添加详细的注释和说明
- 遵循项目命名规范
- 提供使用示例

### 3. 维护脚本
- 定期检查脚本功能
- 更新过期的依赖
- 清理冗余代码
- 优化性能

## 🆘 获取帮助

### 1. 查看脚本信息
```bash
# 查看脚本目录结构
cd scripts_new && tree -L 2

# 搜索特定功能脚本
find . -name "*.py" | xargs grep -l "关键词"
```

### 2. 联系支持
- **技术文档**: 查看各目录下的README.md
- **问题反馈**: 创建GitHub Issue
- **紧急支持**: 联系Athena AI团队

---

**最后更新**: 2025-12-08
**适用版本**: scripts_new v1.0
**维护团队**: Athena AI团队