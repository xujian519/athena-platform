#!/usr/bin/env python3
"""
统一日志系统集成示例
Unified Logging System Integration Example

展示如何在现有服务中集成统一日志系统
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging import (
    get_logger,
    LogLevel,
    LoggingConfigLoader,
    AsyncLogHandler,
    RotatingFileHandler,
    SensitiveDataFilter
)


def example_basic_integration():
    """示例1: 基础集成"""
    print("\n=== 示例1: 基础集成 ===\n")

    # 获取logger
    logger = get_logger("test_service", level=LogLevel.INFO)

    # 添加上下文
    logger.add_context("request_id", "req-001")
    logger.add_context("user_id", "user-123")

    # 记录日志
    logger.info("服务启动")
    logger.debug("调试信息", extra={"debug_key": "debug_value"})
    logger.warning("警告信息")
    logger.error("错误信息")

    print("✓ 基础集成完成")


def example_file_logging():
    """示例2: 文件日志集成"""
    print("\n=== 示例2: 文件日志集成 ===\n")

    logger = get_logger("file_service", level=LogLevel.INFO)

    # 添加文件处理器
    file_handler = RotatingFileHandler(
        filename="logs/file_service.log",
        maxBytes=1024 * 1024,  # 1MB
        backupCount=3,
        compress=True
    )
    logger.add_handler(file_handler)

    # 记录日志
    for i in range(10):
        logger.info(f"日志记录 {i}", extra={"iteration": i})

    print("✓ 文件日志集成完成")


def example_async_logging():
    """示例3: 异步日志集成"""
    print("\n=== 示例3: 异步日志集成 ===\n")

    from core.logging import TextFormatter
    import logging

    logger = get_logger("async_service", level=LogLevel.INFO)

    # 创建底层handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(TextFormatter())

    # 包装为异步handler
    async_handler = AsyncLogHandler(
        handler=stream_handler,
        capacity=1000,
        batch_size=10
    )
    logger.add_handler(async_handler)

    # 记录大量日志
    for i in range(100):
        logger.info(f"异步日志 {i}", extra={"async": True})

    # 查看统计信息
    stats = async_handler.get_stats()
    print(f"✓ 异步日志统计: {stats}")

    # 关闭handler
    async_handler.close()


def example_sensitive_filter():
    """示例4: 敏感信息过滤"""
    print("\n=== 示例4: 敏感信息过滤 ===\n")

    logger = get_logger("secure_service", level=LogLevel.INFO)

    # 添加敏感信息过滤器
    sensitive_filter = SensitiveDataFilter(
        mask_char="*",
        mask_ratio=0.6
    )
    logger.add_filter(sensitive_filter)

    # 记录包含敏感信息的日志
    logger.info("用户登录", extra={
        "username": "test_user",
        "phone": "13800138000",
        "email": "test@example.com",
        "id_card": "110101199001011234"
    })

    logger.info("API调用", extra={
        "token": "sk-1234567890abcdef",
        "api_key": "ak_123456"
    })

    print("✓ 敏感信息过滤完成")


def example_config_based():
    """示例5: 基于配置的集成"""
    print("\n=== 示例5: 基于配置的集成 ===\n")

    # 从配置文件创建logger
    config_path = "config/base/logging.yml"

    try:
        logger = LoggingConfigLoader.create_logger(
            service_name="xiaona",
            config_path=config_path
        )

        logger.info("从配置文件创建的logger")
        logger.debug("调试信息")
        logger.warning("警告信息")

        print("✓ 基于配置的集成完成")

    except FileNotFoundError:
        print("✗ 配置文件不存在，跳过此示例")


def example_service_integration():
    """示例6: 服务集成（模拟FastAPI服务）"""
    print("\n=== 示例6: 服务集成 ===\n")

    # 模拟FastAPI服务
    class MockService:
        def __init__(self):
            self.logger = get_logger("mock_service", level=LogLevel.INFO)

            # 添加文件日志
            file_handler = RotatingFileHandler(
                filename="logs/mock_service.log",
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=5,
                compress=True
            )
            self.logger.add_handler(file_handler)

            # 添加敏感信息过滤
            self.logger.add_filter(SensitiveDataFilter())

        async def handle_request(self, request_id: str, user_data: dict):
            """处理请求（带日志）"""
            self.logger.add_context("request_id", request_id)

            self.logger.info("收到请求", extra={"endpoint": "/api/test"})

            try:
                # 业务逻辑
                result = self._process_data(user_data)
                self.logger.info("请求处理成功", extra={"result": result})
                return result

            except Exception as e:
                self.logger.error("请求处理失败", exception=e)
                raise

        def _process_data(self, data: dict) -> str:
            """处理数据"""
            self.logger.debug("处理数据", extra={"data": data})
            return "processed"

    # 使用服务
    import asyncio

    async def test_service():
        service = MockService()

        # 模拟请求
        result = await service.handle_request(
            request_id="req-001",
            user_data={
                "username": "test_user",
                "phone": "13800138000"
            }
        )

        print(f"✓ 服务集成完成，结果: {result}")

    asyncio.run(test_service())


def example_migration_guide():
    """示例7: 迁移指南"""
    print("\n=== 示例7: 迁移指南 ===\n")

    print("旧代码:")
    print("""
import logging

logger = logging.getLogger(__name__)
logger.info("消息")
""")

    print("\n新代码:")
    print("""
from core.logging import get_logger, LogLevel

logger = get_logger(__name__, level=LogLevel.INFO)
logger.info("消息")
""")

    print("\n✓ 迁移指南完成")


def main():
    """主函数"""
    print("=" * 60)
    print("统一日志系统集成示例")
    print("=" * 60)

    # 运行所有示例
    example_basic_integration()
    example_file_logging()
    example_async_logging()
    example_sensitive_filter()
    example_config_based()
    example_service_integration()
    example_migration_guide()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
