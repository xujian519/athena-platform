# Scripts 目录

本目录包含Athena项目的各种脚本工具。

## 分类说明

- **deployment** (68个文件) - 部署和启动脚本
- **data_processing** (1个文件) - 数据处理脚本
- **database** (16个文件) - 数据库相关脚本
- **maintenance** (10个文件) - 系统维护脚本
- **analysis** (6个文件) - 分析和统计脚本
- **crawlers** (0个文件) - 爬虫相关脚本
- **tests** (25个文件) - 测试脚本（保留但不使用）
- **ai_models** (11个文件) - AI模型脚本（已存在）
- **knowledge_graph** (10个文件) - 知识图谱相关脚本
- **utilities** (38个文件) - 通用工具脚本
- **archive** (28个文件) - 归档脚本（已存在）

## 使用方式

### 部署脚本
```bash
# 自动部署
./deployment/automated_deployment.sh

# 构建Docker镜像
./deployment/build_docker_images.sh

# 启动服务
./deployment/start_services.sh
```

### 数据处理
```bash
# 批量处理专利
./data_processing/batch_process_patents.sh

# 数据库激活
./database/activate_local_legal_clauses_db.py
```

### 系统维护
```bash
# 清理系统
./maintenance/cleanup_temp_files.sh

# 健康检查
./maintenance/health_check.sh
```

## 注意事项

1. 运行前确保脚本有执行权限：`chmod +x scripts/*.sh`
2. 查看各分类目录下的README获取详细信息
3. 重要操作前请备份数据

## 维护指南

- 新增脚本时，请按功能放入相应分类
- 不确定分类的脚本放入utilities目录
- 定期清理不再使用的脚本
