# Athena工作平台 - 快速部署指南

## 概述

本指南描述如何使用本地CI/CD脚本将Athena工作平台部署到生产环境，使用本地PostgreSQL 17.7数据库。

## 前提条件

### 系统要求
- macOS 14+ (Sonoma or later)
- Python 3.10+
- PostgreSQL 17.7 (已安装)
- 20GB+ 可用磁盘空间
- 外部硬盘 (用于备份)

### 软件要求
```bash
# 检查PostgreSQL版本
psql --version
# 应输出: psql (PostgreSQL) 17.7

# 检查Python版本
python3 --version
# 应输出: Python 3.10+

# 检查Poetry (可选)
poetry --version
```

## 快速开始

### 1. 配置生产环境

编辑生产环境配置文件:

```bash
vim config/production.env
```

**必须修改的配置项:**
```bash
# PostgreSQL密码
POSTGRES_PASSWORD=your_secure_password

# Neo4j密码
NEO4J_PASSWORD=your_neo4j_password

# 应用密钥
SECRET_KEY=your_secret_key_change_this
JWT_SECRET_KEY=your_jwt_secret_key_change_this

# LLM API密钥
LLM_API_KEY=your_zhipu_api_key
```

### 2. 创建数据库

```bash
# 创建生产数据库
createdb -U postgres athena_production

# 验证数据库创建
psql -U postgres -d athena_production -c "\l"
```

### 3. 一键部署

选择以下任一方式执行部署:

#### 方式1: Python脚本 (推荐)

```bash
python3 scripts/deploy_to_production.py
```

#### 方式2: Bash脚本

```bash
./scripts/deploy.sh
```

## 部署流程

部署脚本会自动执行以下步骤:

### 步骤1: 验证环境 ✅
- 检查PostgreSQL 17.7版本
- 验证项目目录
- 检查Python和Poetry版本

### 步骤2: 运行测试 🧪
- 执行完整的pytest测试套件
- 运行单元测试和集成测试
- 测试失败则中止部署

### 步骤3: 备份生产环境 💾
- 备份PostgreSQL数据库到外部硬盘
- 备份配置文件
- 生成时间戳备份目录

### 步骤4: 部署代码 📦
- 同步core、config、scripts目录
- 安装生产依赖
- 配置环境变量

### 步骤5: 数据库迁移 🗄️
- 测试数据库连接
- 执行数据库迁移脚本
- 验证表结构

### 步骤6: 重启服务 🔄
- 停止现有服务进程
- 启动新的API服务
- 配置服务监控

### 步骤7: 验证部署 ✅
- 健康检查API端点
- 验证数据库连接
- 检查服务状态

### 步骤8: 清理旧备份 🧹
- 删除7天前的备份
- 释放外部硬盘空间

## 验证部署

部署完成后，访问以下URL验证:

```bash
# API根路径
curl http://localhost:8000/

# API文档 (Swagger UI)
open http://localhost:8000/docs

# 健康检查
curl http://localhost:8000/health
```

## 监控日志

```bash
# 查看API日志
tail -f production/logs/api.log

# 查看部署日志
tail -f logs/deployment_*.log

# 查看PostgreSQL日志
tail -f /usr/local/var/log/postgresql.log
```

## 服务管理

### 启动服务
```bash
cd production
python3 -m uvicorn core.api.main:app --host 0.0.0.0 --port 8000
```

### 停止服务
```bash
pkill -f 'uvicorn.*:8000'
```

### 重启服务
```bash
# 一键重启
./scripts/deploy.sh

# 或手动重启
pkill -f 'uvicorn.*:8000' && sleep 2 && \
cd production && \
python3 -m uvicorn core.api.main:app --host 0.0.0.0 --port 8000 &
```

## 数据库管理

### 连接数据库
```bash
psql -h localhost -U postgres -d athena_production
```

### 备份数据库
```bash
pg_dump -h localhost -U postgres athena_production > backup_$(date +%Y%m%d).sql
```

### 恢复数据库
```bash
psql -h localhost -U postgres athena_production < backup_20260126.sql
```

### 查看表结构
```bash
psql -U postgres -d athena_production -c "\dt"
```

## 故障排查

### 问题1: PostgreSQL连接失败

**症状:** `could not connect to server`

**解决方案:**
```bash
# 检查PostgreSQL状态
brew services list | grep postgresql

# 启动PostgreSQL
brew services start postgresql@17.7

# 验证端口
lsof -i :5432
```

### 问题2: API服务启动失败

**症状:** 端口已被占用

**解决方案:**
```bash
# 查找占用端口的进程
lsof -i :8000

# 终止进程
kill -9 <PID>

# 或使用pkill
pkill -9 -f "uvicorn.*:8000"
```

### 问题3: 测试失败

**症状:** pytest测试失败

**解决方案:**
```bash
# 查看详细错误信息
python3 -m pytest tests/ -v --tb=long

# 跳过慢速测试
python3 -m pytest tests/ -v -m "not slow"

# 只运行单元测试
python3 -m pytest tests/unit -v
```

### 问题4: 依赖安装失败

**症状:** Poetry或pip安装失败

**解决方案:**
```bash
# 清理缓存
poetry cache clear . --all

# 重新安装
poetry install --no-interaction

# 或使用pip
pip3 install -e . --no-deps
pip3 install -r <(poetry export -f requirements.txt)
```

## 生产环境检查清单

部署前检查:
- [ ] PostgreSQL 17.7正在运行
- [ ] 外部硬盘已挂载
- [ ] 配置文件已更新 (production.env)
- [ ] 数据库已创建
- [ ] 测试套件全部通过
- [ ] 备份目录有足够空间

部署后验证:
- [ ] API服务正常响应
- [ ] 数据库连接正常
- [ ] API文档可访问
- [ ] 日志文件正常写入
- [ ] 备份已完成

## 维护建议

### 日常维护
1. 每日检查日志文件
2. 监控磁盘空间使用
3. 检查服务运行状态
4. 验证数据库备份

### 每周维护
1. 清理旧日志文件
2. 分析性能指标
3. 检查更新和安全补丁
4. 审查备份策略

### 每月维护
1. 全系统备份验证
2. 性能优化审查
3. 容量规划评估
4. 文档更新

## 回滚操作

如果部署出现问题，可以快速回滚:

```bash
# 1. 停止服务
pkill -f 'uvicorn.*:8000'

# 2. 恢复数据库备份
psql -U postgres -d athena_production < /path/to/backup/database.sql

# 3. 恢复代码备份
cp -r /Volumes/AthenaData/Athena工作平台备份/backups/backup_<timestamp>/config/* production/

# 4. 重启服务
cd production
python3 -m uvicorn core.api.main:app --host 0.0.0.0 --port 8000
```

## 联系支持

如遇到部署问题，请:
1. 查看日志文件: `logs/deployment_*.log`
2. 检查GitHub Issues
3. 联系技术支持团队

## 更新日志

### v1.0.0 (2026-01-26)
- 初始版本
- 支持PostgreSQL 17.7
- 自动化CI/CD部署流程
- 完整的备份和回滚机制
