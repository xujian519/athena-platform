# 学习模块 - CI/CD快速参考指南

> Athena智能工作平台 - 学习模块本地CI/CD部署指南

版本: 1.1.0
最后更新: 2026-01-28

---

## 目录

- [快速开始](#快速开始)
- [部署方式](#部署方式)
- [常用命令](#常用命令)
- [故障排查](#故障排查)
- [最佳实践](#最佳实践)

---

## 快速开始

### 一键部署

```bash
# 使用Makefile（推荐）
make -f Makefile.learning deploy

# 或直接使用部署脚本
./scripts/deploy_learning_module.sh
```

### 快速部署（跳过测试）

```bash
make -f Makefile.learning deploy-quick
```

---

## 部署方式

### 1. 本地CI/CD部署（推荐）

**优点：**
- 完全控制部署流程
- 快速迭代，无需网络等待
- 适合开发环境

**流程：**
```
预检查 → 运行测试 → 提交代码 → 构建镜像 → 部署服务 → 健康检查
```

**命令：**
```bash
# 完整部署
./scripts/deploy_learning_module.sh

# 跳过测试
./scripts/deploy_learning_module.sh --skip-tests

# 跳过构建
./scripts/deploy_learning_module.sh --skip-build

# 仅部署
./scripts/deploy_learning_module.sh --deploy-only
```

### 2. Makefile部署

**优点：**
- 简洁的命令
- 集成常用操作
- 适合日常开发

**命令：**
```bash
make -f Makefile.learning help          # 查看所有命令
make -f Makefile.learning test          # 运行测试
make -f Makefile.learning deploy        # 完整部署
make -f Makefile.learning health-check  # 健康检查
```

### 3. GitHub Actions CI/CD

**优点：**
- 自动化流程
- 代码质量检查
- 适合团队协作

**触发条件：**
- Push到main分支
- Pull Request
- 手动触发

**查看：**
```
https://github.com/your-repo/actions
```

---

## 常用命令

### 测试命令

```bash
# 运行所有测试
make -f Makefile.learning test

# 运行单元测试
make -f Makefile.learning test-unit

# 运行集成测试
make -f Makefile.learning test-integration

# 运行覆盖率测试
make -f Makefile.learning test-coverage

# 运行压力测试
make -f Makefile.learning test-stress
```

### 部署命令

```bash
# 完整部署
make -f Makefile.learning deploy

# 快速部署（跳过测试）
make -f Makefile.learning deploy-quick

# 仅运行测试
make -f Makefile.learning deploy-tests-only

# 本地部署（不提交到远程）
make -f Makefile.learning deploy-local
```

### Docker命令

```bash
# 构建Docker镜像
make -f Makefile.learning docker-build

# 推送Docker镜像
make -f Makefile.learning docker-push

# 运行Docker容器
make -f Makefile.learning docker-run

# 停止Docker容器
make -f Makefile.learning docker-stop
```

### 监控命令

```bash
# 健康检查
make -f Makefile.learning health-check

# 监控日志（实时）
make -f Makefile.learning monitor-logs

# 显示统计信息
make -f Makefile.learning monitor-stats
```

### 维护命令

```bash
# 清理临时文件
make -f Makefile.learning clean

# 清理日志文件（保留7天）
make -f Makefile.learning clean-logs

# 清理所有生成文件
make -f Makefile.learning clean-all

# 生成部署报告
make -f Makefile.learning report

# 备份到移动硬盘
make -f Makefile.learning backup
```

---

## 部署流程详解

### 预检查阶段

```bash
# 检查Python版本
python3 --version

# 检查Docker
docker --version

# 检查移动硬盘
ls -la /Volumes/AthenaData/Athena工作平台备份

# 检查Git远程仓库
git remote -v
```

### 测试阶段

```bash
# 单元测试
pytest tests/core/learning/test_*.py -v

# 集成测试
pytest tests/core/learning/integration/ -v

# 覆盖率测试
pytest tests/core/learning/ --cov=core.learning --cov-report=html
```

### 提交阶段

```bash
# 查看状态
git status

# 添加文件
git add .

# 提交
git commit -m "feat: 描述"

# 推送到远程
git push origin main
```

### 部署阶段

```bash
# 停止现有服务
pkill -f "athena.*learning"

# 启动新服务
nohup python3 -m core.learning.autonomous_learning_system \
    --config config/athena_production.yaml \
    --log-level INFO \
    > logs/learning_module.log 2>&1 &

# 保存PID
echo $! > logs/learning_module.pid
```

### 健康检查阶段

```bash
# 检查进程状态
ps -p $(cat logs/learning_module.pid)

# 运行烟雾测试
python3 -c "
import asyncio
from core.learning.autonomous_learning_system import AutonomousLearningSystem

async def test():
    system = AutonomousLearningSystem(agent_id='health_check')
    await system.learn_from_experience(
        context={'task': 'health_check'},
        action='check',
        result={'status': 'ok'},
        reward=0.8
    )
    print('✓ 健康检查通过')

asyncio.run(test())
"
```

---

## 故障排查

### 问题1: 测试失败

```bash
# 查看详细测试输出
pytest tests/core/learning/ -vv --tb=long

# 运行特定测试
pytest tests/core/learning/test_autonomous_learning_system.py::test_name -v

# 清理并重新运行
make -f Makefile.learning clean
make -f Makefile.learning test
```

### 问题2: 移动硬盘未挂载

```bash
# 检查挂载状态
ls /Volumes/AthenaData/

# 如果未挂载，重新挂载
# （通常需要手动操作或使用磁盘工具）

# 验证远程仓库
git remote -v
git fsck
```

### 问题3: 服务启动失败

```bash
# 查看日志
tail -f logs/learning_module.log

# 检查端口占用
lsof -i :8000

# 检查进程
ps aux | grep learning

# 手动启动测试
python3 -m core.learning.autonomous_learning_system \
    --config config/athena_production.yaml \
    --log-level DEBUG
```

### 问题4: Docker构建失败

```bash
# 清理Docker缓存
docker system prune -f

# 重新构建
docker build -f Dockerfile.learning -t athena-learning-module:latest .

# 查看构建日志
docker build -f Dockerfile.learning --no-cache --progress=plain .
```

### 问题5: 健康检查失败

```bash
# 检查服务状态
make -f Makefile.learning monitor-stats

# 查看最近的错误
grep ERROR logs/learning_module.log | tail -20

# 重启服务
pkill -f "athena.*learning"
make -f Makefile.learning deploy-local
```

---

## 最佳实践

### 1. 部署前检查清单

- [ ] 所有测试通过
- [ ] 代码已提交到Git
- [ ] 配置文件正确
- [ ] 移动硬盘已挂载
- [ ] 日志目录存在
- [ ] 数据库连接正常

### 2. 部署频率建议

- **开发环境**: 每次功能完成后
- **测试环境**: 每天至少一次
- **生产环境**: 每周或重大功能更新时

### 3. 回滚策略

```bash
# 保存部署前状态
cp logs/learning_module.pid logs/learning_module.pid.bak

# 如果部署失败，自动回滚
./scripts/deploy_learning_module.sh 会自动执行回滚

# 手动回滚
git revert HEAD
git push origin main
./scripts/deploy_learning_module.sh --skip-tests
```

### 4. 监控建议

```bash
# 定期检查服务状态
watch -n 60 'make -f Makefile.learning health-check'

# 监控日志
tail -f logs/learning_module.log | grep -E "ERROR|WARNING"

# 检查资源使用
ps aux | grep learning_module
```

### 5. 备份策略

```bash
# 每天自动备份
# 添加到crontab:
# 0 2 * * * cd /Users/xujian/Athena工作平台 && make -f Makefile.learning backup

# 手动备份
make -f Makefile.learning backup

# 数据库备份
make -f Makefile.learning db-backup
```

---

## 相关资源

- [API文档](../api/LEARNING_MODULE_API.md)
- [用户指南](./USER_GUIDE.md)
- [测试报告](../../tests/core/learning/TEST_REPORT.md)
- [部署日志](../../logs/deployments/)

---

## 支持

如有问题，请查看：
1. 日志文件: `logs/deployments/`
2. 服务日志: `logs/learning_module.log`
3. 部署报告: `logs/deployments/deploy_report_*.txt`
