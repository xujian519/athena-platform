# Athena工作平台 - 部署检查清单

> **版本**: v1.0.0
> **更新日期**: 2026-02-03
> **用途**: 确保生产部署的安全性和完整性

## 📋 部署前检查

### 代码状态

- [ ] 当前在 `main` 分支
  ```bash
  git branch --show-current
  ```

- [ ] 所有修改已提交
  ```bash
  git status
  git log --oneline -5
  ```

- [ ] 确认要部署的提交
  ```bash
  # 今天的提交应该包含：
  # 37a9e09 fix: 修复动态提示词系统Neo4j连接和JSON解析问题
  # 93bda27 fix: 修复模块验证中发现的语法错误并添加验证脚本
  # b21110e fix: 修复API路由注册和配置获取问题
  ```

### 备份

- [ ] 创建代码备份
  ```bash
  git archive --format=tar.gz --output=athena-backup-$(date +%Y%m%d).tar.gz HEAD
  ```

- [ ] 备份Neo4j规则数据
  ```bash
  docker exec athena-neo4j cypher-shell -u neo4j -p athena_neo4j_2024 \
    "MATCH (r:ScenarioRule) RETURN r" > neo4j_rules_backup.json
  ```

- [ ] 备份环境配置
  ```bash
  cp .env .env.backup-$(date +%Y%m%d)
  ```

### 依赖检查

- [ ] Python版本正确 (3.11+)
  ```bash
  python3 --version
  ```

- [ ] 所有依赖已安装
  ```bash
  pip list | grep -E "(fastapi|uvicorn|neo4j)"
  ```

- [ ] Neo4j容器运行中
  ```bash
  docker ps | grep neo4j
  ```

## 🚀 部署执行

### 代码同步

- [ ] 拉取最新代码
  ```bash
  git pull origin main
  ```

- [ ] 验证文件已更新
  ```bash
  # 检查修复的文件
  git diff HEAD~3 HEAD --stat
  ```

### 规则初始化

- [ ] 运行初始化脚本
  ```bash
  python3 scripts/init_prompt_rules.py
  ```

- [ ] 验证规则已创建
  ```bash
  python3 -c "
  from core.database import get_sync_db_manager
  db = get_sync_db_manager()
  with db.neo4j_session() as session:
      result = session.run('MATCH (r:ScenarioRule) RETURN count(r) as count')
      print('规则数量:', result.single()['count'])
  "
  ```

### 服务重启

- [ ] 停止旧API服务
  ```bash
  # 选择一种方式：
  pm2 stop athena-api
  # 或
  docker-compose stop api
  # 或
  pkill -f "uvicorn.*core.api.main:app"
  ```

- [ ] 等待进程完全停止
  ```bash
  sleep 5
  lsof -i:8000
  ```

- [ ] 启动新API服务
  ```bash
  # 选择一种方式：
  pm2 start athena-api
  # 或
  docker-compose up -d api
  # 或
  nohup python3 -m uvicorn core.api.main:app --host 0.0.0.0 --port 8000 > /tmp/athena-api.log 2>&1 &
  ```

## ✅ 部署后验证

### 基础健康检查

- [ ] API服务响应正常
  ```bash
  curl -s http://localhost:8000/health
  ```

- [ ] API文档可访问
  ```bash
  curl -s http://localhost:8000/docs
  ```

- [ ] 无启动错误
  ```bash
  tail -50 /tmp/athena-api.log
  ```

### 功能验证

- [ ] 动态提示词系统健康
  ```bash
  curl -s http://localhost:8000/api/v1/prompt-system/health | python3 -m json.tool
  ```

- [ ] 场景识别功能
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/prompt-system/scenario/identify \
    -H "Content-Type: application/json" \
    -d '{"user_input": "请分析专利创造性"}'
  ```

- [ ] 规则检索功能
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/prompt-system/rules/retrieve \
    -H "Content-Type: application/json" \
    -d '{"domain": "patent", "task_type": "drafting"}'
  ```

- [ ] 提示词生成功能
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/prompt-system/prompt/generate \
    -H "Content-Type: application/json" \
    -d '{"user_input": "请撰写专利权利要求书"}'
  ```

### 农业专利场景测试

- [ ] 测试农业专利权利要求书撰写
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/prompt-system/prompt/generate \
    -H "Content-Type: application/json" \
    -d '{
    "user_input": "请帮我撰写一份农业领域关于智能温室控制系统的权利要求书",
    "additional_context": {
      "title": "智能温室环境控制系统",
      "field": "农业自动化"
    }
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ 成功' if d.get('system_prompt') else '❌ 失败')"
  ```

- [ ] 验证变量替换正确
  ```bash
  # 检查返回的 user_prompt 是否包含实际的 title 和 field
  ```

### 数据库连接验证

- [ ] Neo4j连接正常
  ```bash
  python3 -c "
  from core.database import get_sync_db_manager
  db = get_sync_db_manager()
  with db.neo4j_session() as session:
      result = session.run('RETURN 1')
      print('Neo4j连接:', '正常' if result.single()[0] == 1 else '异常')
  "
  ```

- [ ] PostgreSQL连接正常
  ```bash
  python3 -c "
  from core.database import get_sync_db_manager
  db = get_sync_db_manager()
  health = db.health_check()
  print('PostgreSQL:', health.get('postgresql', {}).get('status'))
  "
  ```

- [ ] Redis连接正常
  ```bash
  redis-cli -a redis123 ping
  ```

### 性能验证

- [ ] API响应时间正常 (< 200ms)
  ```bash
  time curl -s http://localhost:8000/health
  ```

- [ ] 无明显内存泄漏
  ```bash
  pm2 monit
  # 或
  docker stats athena-api
  ```

## 🔧 故障排查准备

### 回滚方案准备

- [ ] 备份文件位置已记录
  ```bash
  ls -lh /tmp/athena-backups/
  ```

- [ ] 回滚脚本已准备
  ```bash
  # 快速回滚命令
  git revert HEAD
  pm2 restart athena-api
  ```

### 日志收集

- [ ] 部署日志已保存
  ```bash
  mkdir -p logs/deployment
  cp /tmp/athena-api.log logs/deployment/deploy_$(date +%Y%m%d_%H%M%S).log
  ```

- [ ] 错误日志已检查
  ```bash
  grep -i "error" /tmp/athena-api.log | tail -20
  ```

## 📊 部署报告

### 部署信息

| 项目 | 内容 |
|------|------|
| 部署版本 | v1.0.0 |
| 部署日期 | 2026-02-03 |
| 部署人员 | [填写] |
| Git提交 | 37a9e09, 93bda27, b21110e |

### 修复内容

| 组件 | 修复内容 | 状态 |
|------|---------|------|
| Neo4j连接 | 导入遮蔽问题 | ✅ |
| JSON解析 | 列表/字符串处理 | ✅ |
| API路由 | 注册方式修复 | ✅ |
| 语法错误 | 21处修复 | ✅ |

### 验证结果

| 测试项 | 状态 | 备注 |
|-------|------|------|
| 健康检查 | ⬜ | 待测试 |
| 场景识别 | ⬜ | 待测试 |
| 规则检索 | ⬜ | 待测试 |
| 提示词生成 | ⬜ | 待测试 |
| 农业专利场景 | ⬜ | 待测试 |
| 数据库连接 | ⬜ | 待测试 |
| 性能指标 | ⬜ | 待测试 |

## ✍️ 签字确认

| 角色 | 姓名 | 签名 | 日期 |
|------|------|------|------|
| 部署执行人 |  |  |  |
| 技术审核人 |  |  |  |
| 验收人 |  |  |  |

---

**备注**:
- 部署时间窗口: [填写]
- 影响范围: 动态提示词系统相关API
- 回滚时间: 预计 < 5分钟
