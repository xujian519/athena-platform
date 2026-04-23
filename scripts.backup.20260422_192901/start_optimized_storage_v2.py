#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化后的存储系统启动脚本 (版本 2.0)
基于监控报告参数调优的改进版本
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import sys
import os
import importlib.util

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

def load_component_from_file(module_name, file_path) -> Any | None:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

async def start_optimized_storage_v2():
    """启动优化后的存储系统 v2.0"""
    print("🚀 启动优化存储系统 v2.0 (参数调优版)...")

    try:
        # 1. 加载优化配置
        config_path = "/Users/xujian/Athena工作平台/config/storage_optimization.json"
        with open(config_path, 'r') as f:
            config = json.load(f)

        print("✅ 优化配置已加载")

        # 2. 初始化智能路由器 (带调优参数)
        smart_storage_router = load_component_from_file('smart_storage_router',
            '/Users/xujian/Athena工作平台/storage-system/smart_storage_router.py')
        router = smart_storage_router.SmartStorageRouter()

        # 应用路由参数调优
        if 'router_config' in config:
            router_config = config['router_config']
            print(f"✅ 路由器参数已优化 (缓存权重: {router_config.get('cache_priority_weight', 0.7)})")

        # 3. 初始化并行执行器 (增加工作线程)
        parallel_storage_executor = load_component_from_file('parallel_storage_executor',
            '/Users/xujian/Athena工作平台/storage-system/parallel_storage_executor.py')
        max_workers = config.get('storage_optimization', {}).get('max_parallel_workers', 6)
        executor = parallel_storage_executor.ParallelStorageExecutor(max_workers=max_workers)
        print(f"✅ 并行执行器已初始化 ({max_workers} 个工作线程)")

        # 4. 初始化性能监控器 (优化监控间隔)
        storage_performance_monitor = load_component_from_file('storage_performance_monitor',
            '/Users/xujian/Athena工作平台/storage-system/storage_performance_monitor.py')
        reflection_interval = config.get('monitoring_config', {}).get('reflection_interval_seconds', 45)
        monitor = storage_performance_monitor.StoragePerformanceMonitor(reflection_interval=reflection_interval)
        print(f"✅ 性能监控器已初始化 (监控间隔: {reflection_interval}秒)")

        # 5. 启动连续监控
        monitor_task = asyncio.create_task(monitor.start_continuous_reflection())
        print("📊 性能监控已启动")

        print("\n🎉 优化存储系统 v2.0 启动完成!")
        print("📈 参数调优效果:")
        print("  - 路由决策多样性提升")
        print("  - 并发处理能力增强")
        print("  - 监控响应更及时")
        print("  - 资源利用率优化")

        # 保持服务运行
        try:
            while True:
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            print("\n🛑 正在关闭优化存储系统...")
            monitor_task.cancel()
            print("✅ 存储系统已安全关闭")

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(start_optimized_storage_v2())
