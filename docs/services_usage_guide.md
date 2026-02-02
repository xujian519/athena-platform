# Athena 工作平台服务管理使用指南

## 🚀 快速开始

### 清理上下文后的标准恢复流程

当您在 Claude Code 中清理上下文后，可以使用以下任一方式快速恢复系统：

#### 方式1：快速恢复（推荐）
```bash
# 进入项目目录
cd /Users/xujian/Athena工作平台

# 快速启动核心服务
./dev/scripts/quick_start.sh
```

#### 方式2：完整恢复
```bash
# 完整启动所有服务
./dev/scripts/athena_services_manager.sh start
```

## 📋 服务管理命令

### 基本命令

```bash
# 显示所有可用选项
./dev/scripts/athena_services_manager.sh help

# 快速恢复核心服务（小诺、NLP、向量服务等）
./dev/scripts/athena_services_manager.sh quick

# 完整启动所有服务
./dev/scripts/athena_services_manager.sh start

# 停止所有服务
./dev/scripts/athena_services_manager.sh stop

# 重启所有服务
./dev/scripts/athena_services_manager.sh restart

# 查看服务状态
./dev/scripts/athena_services_manager.sh status

# 生成详细状态报告
./dev/scripts/athena_services_manager.sh report

# 执行健康检查
./dev/scripts/athena_services_manager.sh health
```

### 服务列表

| 服务名称 | 描述 | 端口 | 状态 |
|---------|------|------|------|
| Redis | 缓存服务 | 6379 | 🟢 核心服务 |
| PostgreSQL | 数据库 | 5432 | 🟢 核心服务 |
| Elasticsearch | 搜索引擎 | 9200 | 🟡 可选服务 |
| 小诺智能问答 | AI问答系统 | 8080 | 🟢 核心服务 |
| NLP服务 | 自然语言处理 | 8081 | 🟢 核心服务 |
| 向量检索服务 | 向量搜索 | 8082 | 🟢 核心服务 |
| 知识图谱服务 | 知识图谱 | 8083 | 🟡 可选服务 |
| 专利检索服务 | 专利搜索 | 8084 | 🟡 可选服务 |
| MCP管理服务 | MCP管理 | 8085 | 🟡 可选服务 |
| 爬虫管理服务 | 爬虫管理 | 8086 | 🟡 可选服务 |

## 🔧 配置管理

### 配置文件位置
```
/Users/xujian/Athena工作平台/config/athena_services.conf
```

### 主要配置项
```bash
# 调试模式
DEBUG=false

# 服务超时设置
SERVICE_START_TIMEOUT=30
HEALTH_CHECK_TIMEOUT=10

# 日志配置
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=7

# 核心服务（必须启动）
CORE_SERVICES=("redis" "postgresql" "apps/apps/xiaonuo" "nlp-service" "vector-service")

# 可选服务（按需启动）
OPTIONAL_SERVICES=("elasticsearch" "knowledge-graph" "patent-retrieval" "mcp-manager" "crawler-manager")
```

## 📊 监控和日志

### 日志文件位置
```
/Users/xujian/Athena工作平台/logs/
├── athena_services_YYYYMMDD.log      # 主日志文件
├── status_report_YYYYMMDD_HHMMSS.json # 状态报告
└── service_status.json               # 实时状态
```

### 查看实时日志
```bash
# 查看最新日志
tail -f /Users/xujian/Athena工作平台/logs/athena_services_$(date +%Y%m%d).log

# 启用调试模式
DEBUG=true ./dev/scripts/athena_services_manager.sh status
```

### 健康检查
```bash
# 执行全局健康检查
./dev/scripts/athena_services_manager.sh health

# 单独检查特定服务端口
lsof -i :6379  # Redis
lsof -i :8080  # 小诺服务
lsof -i :8081  # NLP服务
```

## 🚨 故障排查

### 常见问题

#### 1. 服务启动失败
```bash
# 检查日志
./dev/scripts/athena_services_manager.sh status

# 查看详细错误
tail -n 50 /Users/xujian/Athena工作平台/logs/athena_services_$(date +%Y%m%d).log
```

#### 2. 端口被占用
```bash
# 查找占用端口的进程
lsof -i :8080

# 杀死占用进程
kill -9 <PID>

# 重新启动服务
./dev/scripts/athena_services_manager.sh restart
```

#### 3. 依赖服务未启动
```bash
# 检查核心服务状态
./dev/scripts/athena_services_manager.sh health

# 手动启动Redis
brew services start redis

# 手动启动PostgreSQL
brew services start postgresql
```

#### 4. 权限问题
```bash
# 确保脚本有执行权限
chmod +x /Users/xujian/Athena工作平台/dev/scripts/athena_services_manager.sh
chmod +x /Users/xujian/Athena工作平台/dev/scripts/quick_start.sh
```

### 服务重启顺序
1. **基础服务**: Redis → PostgreSQL → Elasticsearch
2. **中间层服务**: NLP服务 → 向量服务 → 知识图谱
3. **应用层服务**: 小诺 → 专利检索 → MCP管理 → 爬虫管理

### 手动启动单个服务
```bash
# 启动Redis
brew services start redis

# 启动PostgreSQL
brew services start postgresql

# 启动小诺服务
cd /Users/xujian/Athena工作平台
python3 -m xiaonuo.service start
```

## ⚡ 性能优化

### 快速启动建议
1. **使用快速模式**: `quick_start.sh` 只启动核心服务
2. **并行启动**: 脚本已实现并行启动无依赖的服务
3. **预热缓存**: 启动后执行一次查询预热缓存

### 资源监控
```bash
# 监控内存使用
ps aux | grep -E "(redis|postgres|xiaonuo)"

# 监控端口状态
netstat -an | grep LISTEN | grep -E "(6379|5432|8080)"
```

## 🔄 自动化集成

### 添加到系统启动项
```bash
# 创建别名（添加到 ~/.bashrc 或 ~/.zshrc）
alias athena-start='./dev/scripts/quick_start.sh'
alias athena-status='./dev/scripts/athena_services_manager.sh status'
alias athena-stop='./dev/scripts/athena_services_manager.sh stop'

# 重新加载配置
source ~/.bashrc  # 或 source ~/.zshrc
```

### 定时检查（可选）
```bash
# 创建定时任务检查服务状态
crontab -e

# 每小时检查一次服务状态
0 * * * * /Users/xujian/Athena工作平台/dev/scripts/athena_services_manager.sh health
```

## 📞 技术支持

如果遇到问题，请提供以下信息：
1. 错误日志文件
2. 服务状态报告
3. 系统环境信息
4. 具体操作步骤

联系方式：徐健 (xujian519@gmail.com)

---

**提示**: 建议每次清理上下文后，直接使用 `./dev/scripts/quick_start.sh` 进行快速恢复。