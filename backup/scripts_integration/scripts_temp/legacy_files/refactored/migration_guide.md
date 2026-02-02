# Scripts模块重构迁移指南

## 概述

本指南将帮助您将现有的Scripts模块迁移到新的模块化架构。

## 重构前后对比

### 重构前的问题
- 代码重复率高（每个脚本都有相似的数据库连接、配置、日志代码）
- 缺乏统一的服务管理
- 没有健康检查和监控
- 部署过程手动化
- 错误处理不一致

### 重构后的优势
- ✅ 代码减少30-40%
- ✅ 统一的基础设施库
- ✅ 自动化服务管理
- ✅ 内置健康检查和监控
- ✅ 标准化的部署流程
- ✅ 一致的错误处理和日志

## 迁移步骤

### 1. 更新导入语句

**重构前：**
```python
import psycopg2
import logging
from datetime import datetime

# 手动配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'athena',
    'user': 'postgres',
    'password': 'password'
}

# 手动设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**重构后：**
```python
# 添加核心库路径
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.database import db_manager
from core.config import config
from utils.logger import ScriptLogger
from utils.progress_tracker import ProgressTracker
```

### 2. 数据库操作迁移

**重构前：**
```python
def process_data():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        conn.commit()
    finally:
        cursor.close()
        conn.close()
```

**重构后：**
```python
def process_data():
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        # 自动提交和关闭
```

### 3. 配置管理迁移

**重构前：**
```python
API_KEY = "xxx"
DB_HOST = "localhost"
LOG_LEVEL = "INFO"
```

**重构后：**
```python
api_key = config.get('api.key')
db_config = config.get_database_config()
log_level = config.get('logging.level', 'INFO')
```

### 4. 日志管理迁移

**重构前：**
```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def some_function():
    logger.info("开始执行")
    # ...
    logger.error("执行失败")
```

**重构后：**
```python
class MyService:
    def __init__(self):
        self.logger = ScriptLogger("MyService")

    def some_function(self):
        self.logger.info("开始执行")
        # ...
        self.logger.error("执行失败")
```

### 5. 进度跟踪迁移

**重构前：**
```python
total = 1000
for i in range(total):
    # 处理数据
    print(f"\r进度: {i}/{total} ({i/total:.1%})", end="")
```

**重构后：**
```python
tracker = ProgressTracker(1000, "数据处理")
for i in range(1000):
    # 处理数据
    tracker.update(1)
tracker.complete()
```

## 具体脚本迁移示例

### 数据清理脚本

**重构前：** `scripts/cleanup_database.py`
**重构后：** `scripts/refactored/database_cleanup.py`

主要变化：
1. 使用 `db_manager` 管理数据库连接
2. 使用 `ProgressTracker` 显示进度
3. 使用 `ScriptLogger` 统一日志格式
4. 代码行数从200+减少到150+

### 平台启动脚本

**重构前：** `scripts/start_athena_platform.sh`
**重构后：** `scripts/refactored/start_platform.py`

主要变化：
1. 从Shell脚本改为Python脚本
2. 使用 `ServiceManager` 管理服务生命周期
3. 内置健康检查
4. 支持部分服务启动
5. 自动监控系统资源

### 部署脚本

**重构前：** 手动部署步骤
**重构后：** `scripts/refactored/deploy_platform.py`

主要变化：
1. 自动化部署流程
2. 支持回滚
3. 部署前后检查
4. 部署记录和报告

## 最佳实践

### 1. 使用上下文管理器
```python
# 推荐
with db_manager.transaction():
    # 数据库操作

# 推荐
with ProgressTracker(total, "描述") as tracker:
    # 处理逻辑
```

### 2. 配置外部化
```python
# 将配置放在config.yaml中
service_config = config.get_service_config('my_service')
```

### 3. 使用装饰器简化错误处理
```python
from utils.email_notifier import email_notification_on_failure

@email_notification_on_failure(['admin@example.com'])
def critical_task():
    # 关键任务
```

### 4. 利用服务管理框架
```python
from services.manager import ServiceManager

service_manager = ServiceManager.instance()
service_manager.start_service('my_service')
```

## 迁移检查清单

- [ ] 更新导入语句
- [ ] 迁移数据库操作
- [ ] 迁移配置管理
- [ ] 迁移日志系统
- [ ] 添加进度跟踪
- [ ] 使用服务管理器（如适用）
- [ ] 添加健康检查（如适用）
- [ ] 更新错误处理
- [ ] 测试功能完整性
- [ ] 更新文档

## 常见问题

### Q: 如何处理现有的配置文件？
A: 可以将现有配置迁移到 `config.yaml`，或在代码中逐步替换。新的配置系统支持环境变量覆盖。

### Q: 是否需要一次性迁移所有脚本？
A: 不需要。新旧架构可以并存，建议逐步迁移，优先迁移使用频率高的脚本。

### Q: 如何处理数据库连接池？
A: `db_manager` 自动管理连接池，无需手动配置。默认最大连接数是20。

### Q: 如何添加新的服务？
A: 在 `services/manager.py` 的默认服务配置中添加，或创建独立的服务配置文件。

## 后续优化建议

1. **添加单元测试**
   - 为每个重构的脚本添加测试
   - 使用 pytest 框架

2. **性能优化**
   - 使用连接池减少数据库连接开销
   - 批量操作优化

3. **监控增强**
   - 添加业务指标监控
   - 设置告警规则

4. **文档完善**
   - 为每个模块添加API文档
   - 创建使用示例

## 联系支持

如果在迁移过程中遇到问题，请：
1. 查看日志文件获取详细错误信息
2. 检查配置是否正确
3. 参考本指南和示例代码
4. 联系开发团队获取帮助