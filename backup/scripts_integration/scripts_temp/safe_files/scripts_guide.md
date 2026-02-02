# Scripts 目录使用指南

## 🗂️ 目录结构

### 📦 部署相关 (deployment/)
- `automated_deployment.sh` - 自动部署脚本
- `build_docker_images.sh` - 构建Docker镜像
- `start_*.sh` - 各种启动脚本

### 🗄️ 数据库操作 (database/)
- `activate_*_db.py` - 激活各种数据库
- `migrate_*.sql` - 数据库迁移脚本
- `cleanup_postgres*.sh` - PostgreSQL清理

### 🔧 系统维护 (maintenance/)
- `cleanup_*.sh` - 清理脚本
- `health_check*.sh` - 健康检查
- `backup*.sh` - 备份脚本

### 📊 数据处理 (data_processing/)
- `batch_process_*.sh` - 批量处理
- `import_*.py` - 数据导入
- `export_*.py` - 数据导出

### 🔍 分析工具 (analysis/)
- `analyze_*.py` - 各种分析脚本
- `check_*.py` - 检查脚本
- `stats*.py` - 统计脚本

### 🤖 知识图谱 (knowledge_graph/)
- `graph_*.py` - 图操作脚本
- `vector*.py` - 向量处理
- `embed*.py` - 嵌入处理

### 🛠️ 工具集 (utilities/)
- `utils*.py` - 通用工具
- `helper*.py` - 辅助脚本
- `tool*.py` - 专用工具

### 📝 文档 (docs/)
- 各种项目文档和报告
- 使用指南和说明

### 📚 归档 (archive/)
- 旧版本脚本
- 不再使用的脚本
- 备份文件

## 🚀 常用命令

### 快速部署
```bash
cd /Users/xujian/Athena工作平台/scripts/deployment
./automated_deployment.sh
```

### 数据库操作
```bash
# 激活法律条款数据库
python3 database/activate_local_legal_clauses_db.py

# 清理PostgreSQL
./database/cleanup_postgres_database.sh
```

### 系统维护
```bash
# 清理临时文件
./maintenance/cleanup_temp_files.sh

# 系统健康检查
./maintenance/health_check.sh
```

## 💡 使用提示

1. **执行权限**：确保shell脚本有执行权限
   ```bash
   chmod +x scripts/**/*.sh
   ```

2. **Python环境**：使用正确的Python环境
   ```bash
   export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH
   python3 scripts/<category>/<script>.py
   ```

3. **查看脚本说明**：各目录下都有README.md文件

4. **备份重要数据**：执行大规模操作前请备份

## 📝 脚本命名规范

- `start_*.sh` - 启动类脚本
- `stop_*.sh` - 停止类脚本
- `deploy_*.sh` - 部署类脚本
- `cleanup_*.sh` - 清理类脚本
- `backup_*.sh` - 备份类脚本
- `analyze_*.py` - 分析类Python脚本
- `process_*.py` - 处理类Python脚本
- `utils_*.py` - 工具类Python脚本

## 🔧 维护建议

1. 新脚本请放入合适的分类目录
2. 脚本名应清晰表达其功能
3. 添加必要的注释和说明
4. 定期清理不再使用的脚本
5. 重要脚本请添加到版本控制