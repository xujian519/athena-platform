#!/usr/bin/env python3
"""
Athena平台快速启动脚本
"""

import os
import sys
from typing import Any

# 添加核心库路径
sys.path.append(os.path.dirname(__file__) + '/..')

import asyncio

from athena import AthenaController


def quick_start() -> Any:
    """快速启动选项"""
    print("\n🚀 Athena平台快速启动")
    print("=" * 40)
    print("1. 完整平台 (所有服务)")
    print("2. 核心服务 (core_server)")
    print("3. AI服务 (core_server + ai_service)")
    print("4. 自定义选择")
    print("5. 仅查看状态")
    print("6. 退出")
    print("=" * 40)

    choice = input("\n请选择 (1-6): ").strip()

    controller = AthenaController()

    async def execute():
        if choice == '1':
            await controller.start()
        elif choice == '2':
            await controller.start(services=['core_server'])
        elif choice == '3':
            await controller.start(services=['core_server', 'ai_service'])
        elif choice == '4':
            print("\n可用服务:")
            print("- core_server (核心服务)")
            print("- ai_service (AI服务)")
            print("- patent_api (专利API)")
            print("- storage_service (存储服务)")
            services = input("\n输入服务名 (用空格分隔): ").strip()
            if services:
                service_list = services.split()
                await controller.start(services=service_list)
            else:
                print("未指定服务")
        elif choice == '5':
            await controller.status()
        elif choice == '6':
            print("退出")
        else:
            print("无效选择")

    if choice in ['1', '2', '3', '4', '5']:
        asyncio.run(execute())


if __name__ == '__main__':
    try:
        quick_start()
    except KeyboardInterrupt:
        print("\n\n已取消")
