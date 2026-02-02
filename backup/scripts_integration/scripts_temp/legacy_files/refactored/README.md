# Scripts模块重构使用指南

## 概述

重构后的Scripts模块提供了统一的基础设施和工具，大幅减少了代码重复，提高了可维护性和可扩展性。

## 快速开始

### 1. 启动平台

```bash
# 启动所有服务
python3 scripts/refactored/start_platform.py

# 启动指定服务
python3 scripts/refactored/start_platform.py --services core_server ai_service

# 禁用监控
python3 scripts/refactored/start_platform.py --no-monitoring

# 使用自定义配置
python3 scripts/refactored/start_platform.py --config config/production.yaml
```

### 2. 部署平台

```bash
# 部署到生产环境
python3 scripts/refactored/deploy_platform.py deploy athena_platform --version v2.1.0

# 部署到测试环境
python3 scripts/refactored/deploy_platform.py deploy athena_platform --env testing

# 回滚到上一版本
python3 scripts/refactored/deploy_platform.py rollback athena_platform

# 查看部署历史
python3 scripts/refactored/deploy_platform.py list
```

### 3. 数据库维护

```bash
# 清理旧数据（默认保留30天）
python3 scripts/refactored/database_cleanup.py

# 自定义清理天数
python3 scripts/refactored/database_cleanup.py --days 90
```

## 核心组件使用

### 配置管理

```python
from core.config import config

# 获取配置值
db_host = config.get('database.host')
api_port = config.get('api.port', 8000)  # 带默认值

# 获取完整数据库配置
db_config = config.get_database_config()

# 获取环境信息
env_name = config.env.name
is_debug = config.env.debug
```

### 数据库操作

```python
from core.database import db_manager

# 简单查询
result = db_manager.execute_query("SELECT * FROM users WHERE id = %s", (1,))

# 批量操作
affected = db_manager.execute_update("DELETE FROM logs WHERE created_at < NOW() - INTERVAL '30 days'")

# 使用事务
with db_manager.transaction() as conn:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO audit_log (action) VALUES (%s)", ('test',))
```

### 日志记录

```python
from utils.logger import ScriptLogger

class MyService:
    def __init__(self):
        self.logger = ScriptLogger("MyService")

    def do_something(self):
        self.logger.info("开始执行任务")
        try:
            # 业务逻辑
            self.logger.info("任务执行成功")
        except Exception as e:
            self.logger.error(f"任务执行失败: {e}")
```

### 进度跟踪

```python
from utils.progress_tracker import ProgressTracker

# 基本使用
tracker = ProgressTracker(1000, "数据处理")

for i in range(1000):
    # 处理数据
    tracker.update(1, f"处理第 {i+1} 条")

tracker.complete()

# 使用上下文管理器
with track_progress(100, "批量处理") as tracker:
    for item in items:
        process(item)
        tracker.update(1)
```

### 文件管理

```python
from utils.file_manager import FileManager

fm = FileManager()

# 获取目录统计
stats = fm.get_directory_stats('/path/to/dir')
print(f"文件数: {stats['files']}, 大小: {stats['size']} bytes")

# 查找文件
for file_path in fm.find_files('/path', pattern="*.py"):
    print(f"Python文件: {file_path}")

# 备份文件
backup_path = fm.backup_file('/path/to/important.txt', '/backup/dir')

# 同步目录
fm.sync_directories('/source', '/target', exclude_patterns=['*.tmp', '__pycache__'])
```

### 邮件通知

```python
from utils.email_notifier import email_notifier

# 发送简单邮件
email_notifier.send_email(
    to_emails=['user@example.com'],
    subject='任务完成',
    body='您的任务已成功完成'
)

# 发送带附件的邮件
email_notifier.send_email(
    to_emails=['user@example.com'],
    subject='数据报告',
    body='请查收附件中的数据报告',
    attachments=['/path/to/report.pdf']
)

# 使用装饰器自动通知
@email_notification_on_success(['admin@example.com'])
def critical_task():
    # 执行关键任务
    pass
```

## 服务管理

### 服务配置

在 `config.yaml` 中定义服务：

```yaml
services:
  my_service:
    command: python -m my_service.main
    port: 8080
    dependencies: [database, redis]
    health_check: http://localhost:8080/health
```

### 服务生命周期

```python
from services.manager import ServiceManager

manager = ServiceManager.instance()

# 启动服务
success = manager.start_service('my_service')

# 获取服务状态
status = manager.get_service_status('my_service')
print(f"服务状态: {status.status}")

# 停止服务
manager.stop_service('my_service')
```

### 健康检查

```python
from services.health_checker import health_checker

# 注册健康检查
health_checker.register_check('my_api', {
    'url': 'http://localhost:8080/health',
    'interval': 30,
    'timeout': 5
})

# 检查所有服务
results = await health_checker.check_all_services()

# 获取不健康的服务
unhealthy = health_checker.get_unhealthy_services()
```

### 系统监控

```python
from services.monitoring import monitoring_service

# 添加告警规则
monitoring_service.add_rule('high_memory', {
    'metric': 'system_memory_percent',
    'condition': 'gt',
    'threshold': 85,
    'level': 'warning',
    'message': '内存使用率过高'
})

# 获取系统指标
metrics = monitoring_service.get_metrics_summary()

# 获取活跃告警
alerts = monitoring_service.get_active_alerts()
```

## 最佳实践

### 1. 错误处理

```python
from utils.logger import ScriptLogger

class MyService:
    def __init__(self):
        self.logger = ScriptLogger("MyService")

    def process(self):
        try:
            # 业务逻辑
            result = self._do_work()
            return result
        except DatabaseError as e:
            self.logger.error(f"数据库错误: {e}")
            raise
        except Exception as e:
            self.logger.error(f"未知错误: {e}")
            # 可以选择发送告警邮件
            email_notifier.send_email(
                to_emails=['admin@example.com'],
                subject='服务异常',
                body=f"服务执行出错: {e}"
            )
            raise
```

### 2. 配置外部化

```yaml
# config.yaml
database:
  host: ${DB_HOST:localhost}
  port: ${DB_PORT:5432}
  name: ${DB_NAME:athena}

logging:
  level: ${LOG_LEVEL:INFO}
  file: ${LOG_FILE:logs/athena.log}
```

### 3. 使用依赖注入

```python
class MyService:
    def __init__(self, db_manager=None, logger=None):
        self.db = db_manager or db_manager
        self.logger = logger or ScriptLogger("MyService")

    # 便于测试
    def get_user(self, user_id):
        return self.db.execute_query(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
```

### 4. 批量操作优化

```python
def batch_insert(items, batch_size=1000):
    with db_manager.transaction() as conn:
        cursor = conn.cursor()

        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            values = [(item['name'], item['email']) for item in batch]

            cursor.executemany(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                values
            )

            conn.commit()  # 每批提交一次
```

## 迁移现有脚本

按照 `migration_guide.md` 中的步骤，逐步迁移现有脚本：

1. 更新导入语句
2. 替换数据库操作
3. 使用统一配置
4. 添加日志和进度跟踪
5. 利用服务管理框架

## 故障排除

### 常见问题

1. **导入错误**
   - 确保 `PYTHONPATH` 包含项目根目录
   - 检查模块路径是否正确

2. **数据库连接失败**
   - 检查配置文件中的数据库信息
   - 确保数据库服务正在运行

3. **服务启动失败**
   - 检查服务命令是否正确
   - 查看服务日志获取详细错误

### 调试技巧

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看详细配置
config = settings()
print(f"配置: {config._config}")
```

## 贡献

欢迎提交Issue和Pull Request来改进这个模块化架构。

## 许可证

本项目遵循MIT许可证。