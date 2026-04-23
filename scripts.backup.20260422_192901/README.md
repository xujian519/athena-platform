# Athena Scripts 新架构

## 概述

这是Athena平台Scripts模块的全新架构，采用模块化设计，大幅简化了脚本管理，提高了可维护性和可扩展性。

## 🚀 快速开始

### 1. 环境准备

```bash
# 复制环境配置模板
cp .env.template .env

# 编辑配置文件
vim .env

# 创建日志目录
mkdir -p logs
```

### 2. 基本命令

```bash
# 查看帮助
python3 athena.py --help

# 启动完整平台
python3 athena.py start

# 启动特定服务
python3 athena.py start --services core_server ai_service

# 查看平台状态
python3 athena.py status

# 实时监控
python3 athena.py monitor

# 快速启动（交互式）
python3 start.py
```

## 📋 命令参考

### 启动控制

```bash
# 启动命令
python3 athena.py start [选项]
  --services [服务名...]  指定要启动的服务
  --no-monitor           禁用监控
  --env <环境名>         指定环境

# 停止命令
python3 athena.py stop

# 重启命令
python3 athena.py restart [选项]
  --services [服务名...]  指定要重启的服务
```

### 部署管理

```bash
# 部署
python3 athena.py deploy <配置名> [选项]
  --version <版本号>    指定版本
  --env <环境名>       指定环境

# 回滚
python3 athena.py rollback <配置名> [选项]
  --version <版本号>    回滚到指定版本

# 查看部署历史
python3 athena.py list [选项]
  --config <配置名>    指定配置
```

### 系统维护

```bash
# 清理系统
python3 athena.py cleanup [选项]
  --days <天数>       清理多少天前的数据（默认30天）
  --dry-run           预览模式

# 查看日志
python3 athena.py logs [选项]
  --service <服务名>   查看特定服务日志
  --tail <行数>       显示最后N行（默认100）

# 查看配置
python3 athena.py config [键名]
```

## 🏗️ 架构设计

### 核心组件

1. **配置管理 (core.config)**
   - 统一的配置获取
   - 支持环境变量覆盖
   - 多环境配置支持

2. **数据库管理 (core.database)**
   - 连接池管理
   - 事务支持
   - 自动重连

3. **服务管理 (services)**
   - 服务生命周期管理
   - 依赖关系处理
   - 健康检查

4. **工具类 (utils)**
   - 日志记录
   - 进度跟踪
   - 文件管理
   - 邮件通知

### 服务列表

| 服务名 | 端口 | 依赖 | 描述 |
|--------|------|------|------|
| core_server | 8000 | - | 核心服务 |
| ai_service | 8001 | core_server | AI服务 |
| patent_api | 8002 | core_server | 专利API |
| storage_service | - | core_server | 存储服务 |
| memory_service | 8003 | core_server, storage_service | 记忆服务 |
| agent_service | 8004 | core_server, ai_service | 智能体服务 |

## 📊 监控和告警

### 系统指标

- CPU使用率
- 内存使用率
- 磁盘使用率
- 网络IO

### 告警规则

```yaml
alerts:
  high_cpu:
    threshold: 80%
    level: warning
  high_memory:
    threshold: 85%
    level: warning
  high_disk:
    threshold: 90%
    level: critical
```

### 健康检查

```python
# 检查所有服务
health_checker.check_all_services()

# 检查特定服务
health_checker.check_service('core_server')

# 获取不健康的服务
health_checker.get_unhealthy_services()
```

## 🔧 配置详解

### 主配置文件 (config.yaml)

```yaml
# 环境配置
environment:
  name: "${ATHENA_ENV:development}"
  debug: ${DEBUG:false}

# 数据库配置
database:
  host: "${DB_HOST:localhost}"
  port: ${DB_PORT:5432}
  ...

# 服务配置
services:
  core_server:
    command: "python -m core.app"
    port: 8000
    dependencies: []
    health_check: "http://localhost:8000/health"
```

### 环境变量 (.env)

```bash
# 必填项
DB_PASSWORD=your_password
JWT_SECRET=your_secret_key

# 可选项
API_PORT=8000
LOG_LEVEL=INFO
```

## 📝 使用示例

### 1. 启动开发环境

```bash
# 设置环境变量
export ATHENA_ENV=development
export DEBUG=true

# 启动核心服务和AI服务
python3 athena.py start --services core_server ai_service --no-monitor
```

### 2. 部署到生产环境

```bash
# 设置生产环境
export ATHENA_ENV=production

# 部署
python3 athena.py deploy athena_platform --env production --version v2.1.0

# 检查部署状态
python3 athena.py status
```

### 3. 系统维护

```bash
# 查看系统状态
python3 athena.py status

# 清理30天前的数据
python3 athena.py cleanup --days 30

# 查看最近的错误日志
python3 athena.py logs --tail 50
```

## 🔄 迁移指南

### 从旧脚本迁移

| 旧脚本 | 新命令 |
|--------|--------|
| `./start_athena.sh` | `python3 athena.py start` |
| `./start_xiaonuo_integrated.sh` | `python3 athena.py start --services core_server ai_service patent_api` |
| `./deployment/deploy.sh` | `python3 athena.py deploy athena_platform` |
| `./database/cleanup.sh` | `python3 athena.py cleanup` |

### 迁移步骤

1. 备份现有脚本
   ```bash
   python3 migrate.py
   ```

2. 更新cron任务
   ```bash
   # 旧命令
   0 2 * * * /path/to/scripts/database/cleanup.sh

   # 新命令
   0 2 * * * cd /path/to/scripts_new && python3 athena.py cleanup
   ```

3. 更新启动脚本路径
   ```bash
   # 旧路径
   /scripts/start_athena.sh

   # 新路径
   /scripts_new/athena.py start
   ```

## 🛠️ 开发指南

### 添加新服务

1. 在配置文件中添加服务定义
   ```yaml
   services:
     new_service:
       command: "python -m new_service.main"
       port: 8005
       dependencies: ["core_server"]
       health_check: "http://localhost:8005/health"
   ```

2. 实现健康检查端点
   ```python
   from flask import Flask
   app = Flask(__name__)

   @app.route('/health')
   def health():
       return {"status": "healthy"}
   ```

### 自定义告警规则

```python
from services.monitoring import monitoring_service

monitoring_service.add_rule('custom_alert', {
    'metric': 'custom_metric',
    'condition': 'gt',
    'threshold': 100,
    'level': 'warning',
    'message': '自定义指标告警'
})
```

### 扩展日志

```python
from utils.logger import ScriptLogger

class MyService:
    def __init__(self):
        self.logger = ScriptLogger("MyService")

    def process(self):
        self.logger.info("开始处理")
        # ...
        self.logger.info("处理完成")
```

## 🔍 故障排除

### 常见问题

1. **服务启动失败**
   - 检查端口是否被占用
   - 查看服务日志：`python3 athena.py logs --service <服务名>`
   - 确认依赖服务已启动

2. **数据库连接失败**
   - 检查数据库服务状态
   - 验证配置文件中的数据库信息
   - 确认网络连通性

3. **配置不生效**
   - 确认环境变量设置正确
   - 检查配置文件路径
   - 验证YAML语法

### 调试技巧

```bash
# 启用调试模式
export DEBUG=true
export LOG_LEVEL=DEBUG

# 查看完整配置
python3 athena.py config

# 单独测试服务
python3 athena.py start --services core_server
```

## 📚 API参考

### ServiceManager

```python
from services.manager import ServiceManager

manager = ServiceManager.instance()

# 启动服务
manager.start_service('core_server')

# 获取状态
status = manager.get_all_status()

# 停止服务
manager.stop_service('core_server')
```

### DatabaseManager

```python
from core.database import db_manager

# 执行查询
results = db_manager.execute_query("SELECT * FROM users")

# 执行更新
count = db_manager.execute_update("UPDATE users SET active = true")

# 使用事务
with db_manager.transaction():
    # 批量操作
    pass
```

### 其他工具

详见各个模块的文档字符串。

## 📞 支持

如有问题，请：
1. 查看日志获取详细错误信息
2. 参考故障排除章节
3. 提交Issue到项目仓库

## 📄 许可证

MIT License