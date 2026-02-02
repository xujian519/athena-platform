#!/usr/bin/env python3
"""
重构前后对比示例
展示脚本模块化的效果
"""

def show_refactoring_comparison():
    """展示重构前后的对比"""

    print("=" * 80)
    print("📊 Scripts模块重构对比")
    print("=" * 80)

    print("\n📝 1. 数据库操作对比")
    print("-" * 50)

    print("\n❌ 重构前（每个脚本重复代码）：")
    print("""
import psycopg2

# 每个脚本都要写这些
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'athena',
    'user': 'postgres',
    'password': 'password'
}

def cleanup_logs():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM logs WHERE created_at < NOW() - INTERVAL '30 days'")

    conn.commit()
    cursor.close()
    conn.close()

def backup_table():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 备份逻辑...

    cursor.close()
    conn.close()
    """)

    print("\n✅ 重构后（使用统一管理器）：")
    print("""
from core.database import db_manager
from utils.progress_tracker import ProgressTracker
from utils.logger import ScriptLogger

class DatabaseService:
    """使用统一管理器的数据库服务"""

    @staticmethod
    def cleanup_logs():
        with db_manager.get_cursor() as cursor:
            rows = db_manager.execute_update(
                "DELETE FROM logs WHERE created_at < NOW() - INTERVAL '30 days'"
            )
            return rows

    @staticmethod
    def backup_table(table_name):
        tracker = ProgressTracker(100, f"备份{table_name}")
        # 使用连接池和事务管理
        with db_manager.transaction():
            # 备份逻辑...
            tracker.complete()

# 使用示例
service = DatabaseService()
deleted_count = service.cleanup_logs()
    """)

    print("\n📝 2. 配置管理对比")
    print("-" * 50)

    print("\n❌ 重构前（配置分散）：")
    print("""
# 每个脚本都有自己的配置
API_KEY = "xxx"
DB_HOST = "localhost"
DB_PORT = 5432
LOG_LEVEL = "INFO"
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
    """")

    print("\n✅ 重构后（统一配置）：")
    print("""
from core.config import config

# 从配置中心获取
api_key = config.get('api.key')
db_config = config.get_database_config()
log_level = config.get('logging.level', 'INFO')
redis_config = config.get('redis', {})

# 支持环境变量覆盖
db_host = os.getenv('DB_HOST', db_config.get('host'))
    """)

    print("\n📝 3. 日志管理对比")
    print("-" * 50)

    print("\n❌ 重构前（每个脚本独立配置）：")
    print("""
import logging

# 每个脚本都要配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def some_function():
    logger.info("开始执行")
    # ...
    logger.info("执行完成")
    """")

    print("\n✅ 重构后（统一日志管理）：")
    print("""
from utils.logger import ScriptLogger

class MyService:
    def __init__(self):
        self.logger = ScriptLogger("MyService")

    def some_function(self):
        self.logger.info("开始执行")
        # ...
        self.logger.info("执行完成")

    def error_handling(self):
        try:
            # 业务逻辑
            pass
        except Exception as e:
            self.logger.error(f"执行失败: {e}")
            raise

# 自动记录执行时间和上下文
@track_progress
def some_function():
    # 自动记录开始和结束
    pass
    """)

    print("\n📊 重构效果总结")
    print("-" * 50)
    print("""
✅ 代码减少30-40%
✅ 配置统一管理
✅ 错误处理标准化
✅ 日志格式一致
✅ 进度跟踪自动化
✅ 数据库连接池化
✅ 事务管理自动化
✅ 单元测试更容易
✅ 维护成本降低
    """)

    print("\n🚀 使用示例")
    print("-" * 50)
    print("""
# 简化的使用方式
from core.database import db_manager
from core.config import config
from utils.progress_tracker import ProgressTracker
from utils.logger import ScriptLogger

class MyTask:
    def __init__(self):
        self.logger = ScriptLogger("MyTask")

    def run(self):
        total_items = 1000
        tracker = ProgressTracker(total_items, "数据处理")

        # 使用统一数据库管理
        with db_manager.transaction() as conn:
            # 批量处理
            self._batch_process(conn, tracker)

        tracker.complete()

    def _batch_process(self, conn, tracker):
        batch_size = 100
        for i in range(0, 1000, batch_size):
            # 处理逻辑
            tracker.update(batch_size, f"处理第{i+1}-{i+batch_size}条")

# 使用统一的配置
service_config = config.get_service_config('my_service')
    """")

if __name__ == "__main__":
    show_refactoring_comparison()