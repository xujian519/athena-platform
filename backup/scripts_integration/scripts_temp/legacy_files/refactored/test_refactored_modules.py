#!/usr/bin/env python3
"""
测试重构后的模块
演示新架构的使用方法
"""

import sys
import os
import asyncio

# 添加核心库路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.config import config
from utils.logger import ScriptLogger
from utils.progress_tracker import ProgressTracker
from utils.file_manager import FileManager


def test_config():
    """测试配置管理"""
    print("\n=== 测试配置管理 ===")
    print(f"数据库主机: {config.get('database.host')}")
    print(f"Redis端口: {config.get('redis.port')}")
    print(f"日志级别: {config.get('logging.level')}")
    print(f"环境: {config.env.name}")


def test_logger():
    """测试日志记录"""
    print("\n=== 测试日志记录 ===")
    logger = ScriptLogger("TestModule")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")


def test_progress_tracker():
    """测试进度跟踪"""
    print("\n=== 测试进度跟踪 ===")
    tracker = ProgressTracker(50, "测试任务")

    for i in range(50):
        # 模拟工作
        import time
        time.sleep(0.02)
        tracker.update(1, f"处理第 {i+1} 项")

    tracker.complete()


def test_file_manager():
    """测试文件管理"""
    print("\n=== 测试文件管理 ===")
    file_manager = FileManager()

    # 获取当前目录统计
    stats = file_manager.get_directory_stats('.')
    print(f"文件数: {stats['files']}")
    print(f"目录数: {stats['directories']}")
    print(f"总大小: {stats['size'] / 1024 / 1024:.2f} MB")

    # 查找Python文件
    py_files = list(file_manager.find_files('.', pattern="*.py", max_depth=2))
    print(f"Python文件数: {len(py_files)}")


def test_service_manager():
    """测试服务管理"""
    print("\n=== 测试服务管理 ===")
    from services.manager import ServiceManager

    manager = ServiceManager.instance()

    # 列出配置的服务
    print("\n配置的服务:")
    manager.list_services()

    # 获取所有服务状态
    print("\n服务状态:")
    status = manager.get_all_status()
    for name, info in status.items():
        print(f"  - {name}: {info['status']}")


def test_health_checker():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    from services.health_checker import health_checker

    # 注册一个测试健康检查
    health_checker.register_check('test_service', {
        'url': 'http://httpbin.org/status/200',
        'interval': 30
    })

    # 手动执行一次检查
    async def check():
        result = await health_checker.check_service('test_service')
        print(f"健康检查结果: {result.status} - {result.message}")

    asyncio.run(check())


def test_monitoring():
    """测试监控服务"""
    print("\n=== 测试系统监控 ===")
    from services.monitoring import monitoring_service

    # 收集一次系统指标
    asyncio.run(monitoring_service.collect_system_metrics())

    # 获取指标摘要
    summary = monitoring_service.get_metrics_summary()
    print("系统指标:")
    for metric_name, metric_info in summary.items():
        if 'current' in metric_info:
            print(f"  - {metric_name}: {metric_info['current']:.1f}")


def main():
    """主测试函数"""
    print("🚀 开始测试重构后的模块...\n")

    # 测试各个组件
    test_config()
    test_logger()
    test_progress_tracker()
    test_file_manager()
    test_service_manager()
    test_health_checker()
    test_monitoring()

    print("\n✅ 所有测试完成！")


if __name__ == "__main__":
    main()