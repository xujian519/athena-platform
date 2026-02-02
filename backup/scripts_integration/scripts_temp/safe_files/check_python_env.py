#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Athena工作平台Python环境检查脚本"""

import sys
import subprocess
from pathlib import Path

def main():
    print("🐍 Athena工作平台Python环境检查")
    print("=" * 50)

    # Python版本信息
    print(f"\n📊 Python版本信息:")
    print(f"   版本: {sys.version.split()[0]}")
    print(f"   路径: {sys.executable}")
    print(f"   实现: {sys.implementation.name}")

    # 检查关键包
    packages = {
        'aiohttp': '异步HTTP服务器/客户端',
        'fastapi': '现代Web框架',
        'uvicorn': 'ASGI服务器',
        'asyncpg': 'PostgreSQL异步驱动',
        'redis': 'Redis客户端',
        'pydantic': '数据验证和序列化',
        'sqlalchemy': 'SQL工具包和ORM',
        'networkx': '图论和网络分析'
    }

    print(f"\n📦 核心包检查:")
    all_installed = True
    for package, description in packages.items():
        try:
            module = __import__(package)
            if hasattr(module, '__version__'):
                version = module.__version__
            else:
                version = '已安装'
            print(f"   ✅ {package:<15} - {description:<30} [{version}]")
        except ImportError as e:
            print(f"   ❌ {package:<15} - {description:<30} [未安装]")
            all_installed = False

    # 检查项目路径
    project_path = Path('/Users/xujian/Athena工作平台')
    print(f"\n📁 项目路径检查:")
    if project_path.exists():
        print(f"   ✅ 项目目录存在: {project_path}")
        if str(project_path) in sys.path:
            print(f"   ✅ 项目路径已在Python路径中")
        else:
            print(f"   ⚠️ 项目路径未在Python路径中")
    else:
        print(f"   ❌ 项目目录不存在")

    # 总结
    print(f"\n🎯 环境状态总结:")
    if all_installed and 'Python 3.14.0' in sys.version:
        print(f"   🟢 环境完美！可以启动小诺了！")
        print(f"   💡 运行: python3 /Users/xujian/Athena工作平台/start_xiaonuo_dialogue.py")
    else:
        print(f"   🟡 环境需要进一步配置")

    print(f"\n💡 提示:")
    print(f"   - 如需更新包: pip3 install --user --upgrade package_name")
    print(f"   - 如需安装新包: pip3 install --user package_name")

if __name__ == "__main__":
    main()