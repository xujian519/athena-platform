# Athena工作平台 - 生产环境部署指南

> **版本**: v1.0.0
> **更新日期**: 2026-02-03
> **部署内容**: 动态提示词系统修复

## 📋 部署概述

本次部署包含以下修复内容：

### 修复内容清单

| 文件 | 修复内容 | 严重级别 |
|------|---------|---------|
| `core/database/connection_manager.py` | Neo4j导入遮蔽问题 | P0 |
| `core/legal_world_model/scenario_rule_retriever_optimized.py` | JSON解析问题 | P0 |
| `core/api/prompt_system_routes.py` | API路由注册问题 | P0 |
| `core/patent_deep_comparison_analyzer.py` | 21个语法错误 | P1 |
| `core/performance/context_compressor.py` | 参数类型错误 | P1 |
| `core/embedding/bge_embedding_service.py` | 缺失numpy导入 | P1 |
| `core/vector/unified_vector_manager.py` | 缺失numpy导入 | P1 |

### 新增文件

| 文件 | 用途 |
|------|------|
| `scripts/init_prompt_rules.py` | Neo4j规则初始化脚本 |
| `scripts/verification/*` | 模块验证脚本集合 |
| `docs/OPENCLAW_INTEGRATION_PROGRESS.md` | 集成进度文档 |

## 🚀 快速部署

### 方式1: 自动部署脚本（推荐）

```bash
# 执行部署脚本
./scripts/deploy_prompt_system_fixes.sh

# 跳过规则初始化（如果已初始化）
./scripts/deploy_prompt_system_fixes.sh --skip-init

# 模拟运行（不实际部署）
./scripts/deploy_prompt_system_fixes.sh --dry-run
```

### 方式2: 手动部署

#### 步骤1: 拉取最新代码

```bash
# 确保在main分支
git checkout main

# 拉取最新提交
git pull origin main

# 查看今天的提交
git log --since="1 day ago" --oneline
```

#### 步骤2: 初始化Neo4j规则（首次部署）

```bash
# 运行初始化脚本
python3 scripts/init_prompt_rules.py

# 验证规则已创建
curl -s http://localhost:8000/api/v1/prompt-system/health | python3 -m json.tool
```

#### 步骤3: 重启API服务

```bash
# 方式A: 使用PM2（推荐）
pm2 restart athena-api
pm2 logs athena-api --lines 50

# 方式B: 使用systemctl（系统服务）
sudo systemctl restart athena-api
sudo journalctl -u athena-api -f

# 方式C: 使用Docker Compose
docker-compose restart api
docker-compose logs -f api

# 方式D: 手动重启（开发环境）
pkill -f "uvicorn.*core.api.main:app"
nohup python3 -m uvicorn core.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  > /tmp/athena-api.log 2>&1 &
```

#### 步骤4: 验证部署

```bash
# 1. 检查服务健康状态
curl http://localhost:8000/health

# 2. 检查动态提示词系统
curl http://localhost:8000/api/v1/prompt-system/health

# 3. 测试提示词生成功能
curl -X POST http://localhost:8000/api/v1/prompt-system/prompt/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "请帮我撰写一份农业专利的权利要求书"
  }'

# 4. 运行验证脚本
./scripts/verification/verify_all.sh
```

## 🔄 回滚方案

如果部署后出现问题，可以使用以下回滚方案：

### 快速回滚

```bash
# 回滚到上一个版本
git log --oneline -5
git revert HEAD
git push origin main

# 重启服务
pm2 restart athena-api
```

### 使用备份回滚

```bash
# 如果在部署前创建了备份
cd /tmp/athena-backups/athena-backup-YYYYMMDD-HHMMSS

# 恢复核心文件
cp -r core/database /Users/xujian/Athena工作平台/core/
cp -r core/legal_world_model /Users/xujian/Athena工作平台/core/

# 重启服务
pm2 restart athena-api
```

### Git回滚到指定版本

```bash
# 查看提交历史
git log --oneline -10

# 回滚到指定提交
git reset --hard <commit-hash>

# 强制推送（谨慎使用）
git push -f origin main
```

## 🐳 Docker部署方案

### 使用Docker Compose部署

```bash
# 1. 构建新镜像
cd /Users/xujian/Athena工作平台
docker-compose build api

# 2. 停止旧容器
docker-compose stop api

# 3. 启动新容器
docker-compose up -d api

# 4. 查看日志
docker-compose logs -f api
```

### 使用独立Docker容器

```bash
# 1. 构建镜像
docker build -t athena-api:latest -f production/config/docker/Dockerfile.production .

# 2. 停止旧容器
docker stop athena-api
docker rm athena-api

# 3. 启动新容器
docker run -d \
  --name athena-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /Users/xujian/Athena工作平台:/app \
  -v /tmp/athena-api.log:/app/logs/api.log \
  athena-api:latest

# 4. 查看日志
docker logs -f athena-api
```

## 📊 监控和验证

### 健康检查端点

```bash
# 主健康检查
curl http://localhost:8000/health

# 动态提示词系统健康检查
curl http://localhost:8000/api/v1/prompt-system/health

# Prometheus指标
curl http://localhost:8000/metrics
```

### 日志查看

```bash
# API日志
tail -f /tmp/athena-api.log

# PM2日志
pm2 logs athena-api

# Docker日志
docker logs -f athena-api

# systemd日志
journalctl -u athena-api -f
```

### Grafana监控

访问 Grafana 查看系统状态：
- URL: http://localhost:3000
- 默认用户名: admin
- 默认密码: admin（首次登录后需修改）

## ⚠️ 故障排查

### 问题1: Neo4j连接失败

```bash
# 检查Neo4j容器状态
docker ps | grep neo4j

# 检查Neo4j日志
docker logs athena-neo4j

# 测试Neo4j连接
curl -u neo4j:athena_neo4j_2024 http://localhost:7474

# 重启Neo4j
docker-compose restart neo4j
```

### 问题2: 提示词生成失败

```bash
# 检查Neo4j规则是否存在
python3 -c "
from core.database import get_sync_db_manager
db = get_sync_db_manager()
with db.neo4j_session() as session:
    result = session.run('MATCH (r:ScenarioRule) RETURN count(r) as count')
    print('规则数量:', result.single()['count'])
"

# 重新初始化规则
python3 scripts/init_prompt_rules.py
```

### 问题3: API启动失败

```bash
# 检查端口占用
lsof -i:8000

# 检查Python依赖
pip list | grep -E "(fastapi|uvicorn|neo4j)"

# 检查语法错误
python3 -m py_compile core/api/main.py

# 查看详细错误
python3 -m uvicorn core.api.main:app --host 0.0.0.0 --port 8000
```

### 问题4: 性能下降

```bash
# 检查API响应时间
curl -w "@-" -o /dev/null -s "http://localhost:8000/health"

# 查看系统资源
top
htop

# 检查数据库连接数
curl http://localhost:8000/api/v1/prompt-system/cache/stats
```

## 📋 部署检查清单

### 部署前

- [ ] 确认当前分支为 `main`
- [ ] 确认无未提交的修改
- [ ] 备份当前版本
- [ ] 通知用户部署计划

### 部署中

- [ ] 拉取最新代码
- [ ] 初始化Neo4j规则（首次）
- [ ] 重启API服务
- [ ] 等待服务启动（10-30秒）

### 部署后

- [ ] 检查服务健康状态
- [ ] 测试提示词生成功能
- [ ] 检查日志无错误
- [ ] 验证性能正常
- [ ] 通知用户部署完成

## 📞 支持和联系

如有问题，请联系：
- **技术支持**: xujian519@gmail.com
- **文档**: `/docs/deployment/`
- **日志**: `/logs/deployment/`

---

**部署完成后，请记得测试核心功能：**

```bash
# 测试农业专利权利要求书撰写
curl -X POST http://localhost:8000/api/v1/prompt-system/prompt/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "请帮我撰写一份农业领域关于智能温室控制系统的权利要求书",
    "additional_context": {
      "title": "智能温室环境控制系统",
      "field": "农业自动化"
    }
  }' | python3 -m json.tool
```

预期输出应包含完整的 `system_prompt` 和 `user_prompt`，说明部署成功！
