#!/usr/bin/env python3
"""
高德地图MCP服务器启动文件
Gaode Maps MCP Server Launcher
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入服务器主模块
from src.amap_mcp_server.server import main

if __name__ == '__main__':
    # 设置环境变量
    os.environ.setdefault('PYTHONPATH', str(current_dir))

    # 运行服务器
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n服务器已停止")
    except Exception as e:
        logger.info(f"服务器启动失败: {e}")
        sys.exit(1)
