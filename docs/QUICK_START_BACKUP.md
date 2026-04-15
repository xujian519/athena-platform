# 🛡️ Athena安全备份与回滚 - 快速启动指南

> **5分钟上手，保护您的核心数据资产**

---

## 🚀 立即开始 (5分钟)

### 步骤1: 创建备份目录 (1分钟)

```bash
# 创建备份根目录
sudo mkdir -p /backup/{postgres,neo4j,qdrant,legal_world_model,logs,cloud_backup,verification}

# 设置权限
sudo chown -R $USER:$USER /backup

# 验证
ls -la /backup
```

### 步骤2: 执行首次备份 (2分钟)

```bash
# 进入Athena工作平台目录
cd /Users/xujian/Athena工作平台

# 执行全量备份
./scripts/backup/backup_all.sh
```

### 步骤3: 验证备份 (1分钟)

```bash
# 验证备份完整性
./scripts/backup/verify_backups.sh

# 查看备份报告
ls -lh /backup/postgres/
ls -lh /backup/legal_world_model/
```

### 步骤4: 测试回滚 (1分钟)

```bash
# 模拟回滚测试（不实际执行）
./scripts/migration/emergency_rollback.sh --help

# 查看可用备份
ls -lht /backup/postgres/*.sql | head -5
```

---

## 📋 每日检查清单

### 每日必做 (2分钟)

```bash
# 1. 检查备份状态
ls -lht /backup/postgres/ | head -3
ls -lht /backup/legal_world_model/ | head -3

# 2. 验证最新备份
./scripts/backup/verify_backups.sh

# 3. 查看备份日志
tail -20 /backup/logs/backup_*.log | tail -20
```

### 每周必做 (10分钟)

```bash
# 1. 执行完整备份验证
./scripts/backup/verify_backups.sh --full

# 2. 测试恢复流程
./scripts/backup/test_restore.sh --dry-run

# 3. 检查磁盘空间
df -h /backup

# 4. 清理旧备份
find /backup -name "*.sql" -mtime +30 -delete
```

---

## 🚨 应急回滚流程

### 场景1: 快速回滚 (最常用)

**适用情况**: 新Gateway有问题，需要立即切回旧系统

```bash
# 执行快速回滚（只切换流量，不回滚代码和数据）
./scripts/migration/emergency_rollback.sh --quick
```

**预期结果**:
- ✅ 流量切换回旧系统 (< 30秒)
- ✅ Gateway服务停止
- ✅ 代码和数据保持不变

### 场景2: 完整回滚

**适用情况**: 迁移完全失败，需要恢复到迁移前状态

```bash
# 执行完整回滚（包括代码和数据）
./scripts/migration/emergency_rollback.sh --full
```

**预期结果**:
- ✅ 流量切换
- ✅ 代码回滚到Git标签 `pre-migration-baseline-YYYYMMDD`
- ✅ 数据库回滚到最新备份

### 场景3: 仅回滚数据

**适用情况**: 代码没问题，但数据有异常

```bash
# 只回滚数据库
./scripts/migration/emergency_rollback.sh --data-only
```

---

## 📊 监控和告警

### 设置自动备份 (推荐)

```bash
# 添加到crontab
crontab -e

# 每天凌晨2点执行全量备份
0 2 * * * /Users/xujian/Athena工作平台/scripts/backup/backup_all.sh

# 每6小时执行增量备份
0 */6 * * * /Users/xujian/Athena工作平台/scripts/backup/backup_incremental.sh

# 每周日凌晨3点验证备份
0 3 * * 0 /Users/xujian/Athena工作平台/scripts/backup/verify_backups.sh
```

### 备份成功检查

```bash
# 检查今天的备份是否存在
TODAY=$(date +%Y%m%d)
ls -lh /backup/postgres/*${TODAY}*.sql
ls -lh /backup/legal_world_model/${TODAY}

# 查看验证状态
cat /backup/verification/status_${TODAY}.txt
```

---

## 🔍 故障排查

### 问题1: 备份失败

**症状**: 执行 `backup_all.sh` 报错

**排查步骤**:

```bash
# 1. 检查备份目录权限
ls -ld /backup
# 应该显示你的用户名，而不是root

# 2. 检查磁盘空间
df -h /backup
# 确保有足够的可用空间（至少20GB）

# 3. 检查PostgreSQL连接
pg_isready -h localhost -p 5432
# 应该返回: accepting connections

# 4. 查看错误日志
tail -50 /backup/logs/backup_*.log
```

### 问题2: 回滚失败

**症状**: 执行 `emergency_rollback.sh` 报错

**排查步骤**:

```bash
# 1. 检查备份文件是否存在
ls -lh /backup/postgres/*.sql | head -5

# 2. 检查Docker服务状态
docker ps

# 3. 手动停止Gateway
docker stop athena-gateway

# 4. 手动重启旧系统
docker-compose restart web
```

### 问题3: 数据库连接失败

**症状**: 回滚后无法连接数据库

**解决方法**:

```bash
# 1. 检查PostgreSQL容器状态
docker ps | grep postgres

# 2. 重启PostgreSQL
docker-compose restart postgres

# 3. 测试连接
psql -h localhost -U postgres -d athena_db -c "SELECT 1;"
```

---

## 📞 获取帮助

### 查看文档

```bash
# 查看完整迁移指南
cat /Users/xujian/Athena工作平台/docs/ATHENA_SAFE_MIGRATION_GUIDE.md

# 查看脚本帮助
./scripts/backup/backup_all.sh --help
./scripts/migration/emergency_rollback.sh --help
```

### 应急联系

- **项目负责人**: 徐健 (xujian519@gmail.com)
- **紧急回滚**: 执行 `emergency_rollback.sh --quick`
- **数据恢复**: 执行 `db_rollback.py` (需要Python环境)

---

## ✅ 验证清单

### 迁移前检查 (Phase 0)

- [ ] 备份目录已创建: `/backup`
- [ ] 首次备份已完成
- [ ] 备份验证已通过
- [ ] 回滚脚本已测试
- [ ] Git基线标签已创建
- [ ] 监控系统已部署

### 迁移中监控 (Phase 1-2)

- [ ] 每日备份成功
- [ ] 备份验证通过
- [ ] 系统健康正常
- [ ] 错误率 < 0.1%
- [ ] 性能无显著下降

### 迁移后验证 (Phase 3)

- [ ] 所有服务运行正常
- [ ] 数据完整性100%
- [ ] 回滚测试成功
- [ ] 性能达标
- [ ] 用户反馈良好

---

## 📚 相关文档

- [完整迁移指南](./ATHENA_SAFE_MIGRATION_GUIDE.md)
- [OpenClaw架构分析](./OPENCLAW_ARCHITECTURE_ANALYSIS.md)
- [备份策略详解](../docs/BACKUP_STRATEGY.md)

---

## 💡 最佳实践

1. **备份优先**: 在做任何改动前，先执行备份
2. **频繁验证**: 不要等需要恢复时才发现备份损坏
3. **测试回滚**: 在非紧急情况下定期测试回滚流程
4. **保留基线**: 永远保留一个已知可用的备份基线
5. **文档更新**: 每次修改备份策略后更新文档

---

**版本**: v1.0
**最后更新**: 2026-02-02
**维护者**: 徐健 (xujian519@gmail.com)

> 💡 **记住**: 好的备份策略是最好的保险！
