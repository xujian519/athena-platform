# 代码重复重构报告

## 执行时间
2026-01-25

## 重构目标
- **初始重复率**: 28.8% (282,556行重复代码)
- **目标重复率**: <10%
- **当前重复率**: 待最终验证

## 重构措施

### 1. 创建统一工具模块

#### core/logging_config.py
统一日志配置模块，替代各模块中重复的`logging.basicConfig`调用。

**功能**:
- `setup_logging()` - 标准日志配置
- `get_logger()` - 快速获取logger
- `setup_simple_logging()` - 简单配置
- `setup_verbose_logging()` - 详细配置
- `setup_file_logging()` - 文件日志
- `LogLevelContext` - 级别上下文管理器

**迁移前**:
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**迁移后**:
```python
from core.logging_config import setup_logging
logger = setup_logging()
```

**影响**: 1945处使用，减少~10,000行重复代码

#### core/async_main.py
统一异步入口模块，替代重复的`if __name__ == '__main__': asyncio.run(main())`模式。

**功能**:
- `@async_main` 装饰器
- `run_async()` 函数式API
- `AsyncMainContext` 上下文管理器
- `run_batch()` 批处理运行器

**迁移前**:
```python
async def main():
    ...

if __name__ == '__main__':
    asyncio.run(main())
```

**迁移后**:
```python
from core.async_main import async_main

@async_main
async def main():
    ...
```

**影响**: 889处使用，减少~5,000行重复代码

#### core/database/unified_connection.py
统一数据库连接管理，提供PostgreSQL和SQLite的统一接口。

**功能**:
- `PostgreSQLConnection` - asyncpg连接池封装
- `SQLiteConnection` - sqlite3连接封装
- `DatabaseConnection` - 统一接口工厂
- `postgres_context()` / `sqlite_context()` - 上下文管理器

**影响**: 30+处使用，减少~3,000行重复代码

## 迁移进度

### 统计数据（2026-01-25）
```
已迁移到新模块:
  - logging_config: 308 个文件
  - async_main: 471 个文件  
  - unified_connection: 14 个文件

仍使用旧模式:
  - logging.basicConfig: 223 个文件
  - asyncio.run(main()): 31 个文件
  - asyncpg.create_pool: 0 个文件

迁移进度: 793/1047 (75.7%)
```

### 备份文件
- 备份文件数: 555个 (*.bak)
- 回滚命令: `find . -name '*.bak' | xargs -I{} mv {} {%.bak}`

## 预期效果

### 代码减少量
| 模式 | 重复次数 | 减少行数 |
|------|---------|---------|
| logging配置 | 1945 | ~10,000 |
| async main | 889 | ~5,000 |
| 数据库连接 | 30+ | ~3,000 |
| **总计** | **2864+** | **~18,000** |

### 重复率改进
- **重构前**: 28.8% (282,556行)
- **预期**: ~15% (减少18,000行)
- **目标**: <10%

## 下一步计划

### 短期（立即执行）
1. ✅ 创建统一工具模块
2. ✅ 批量迁移core/目录
3. ⏳ 迁移services/目录剩余文件
4. ⏳ 最终验证重复率

### 中期（1-2周）
1. 提取通用工具函数到core/utils/
2. 统一配置加载机制
3. 重构高重复的特定模式

### 长期（持续优化）
1. 架构优化以减少代码耦合
2. 识别并消除新的重复模式
3. 建立代码审查机制防止重复

## 注意事项

### 兼容性
- 所有新模块保持向后兼容
- 旧代码继续工作，逐步迁移
- 备份文件保留以便回滚

### 测试
- 迁移后需运行完整测试套件
- 重点测试日志、异步入口、数据库连接
- 验证性能无退化

---

**报告生成时间**: 2026-01-25
**负责人**: Athena平台团队
