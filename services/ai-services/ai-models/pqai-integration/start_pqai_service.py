#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PQAI专利检索服务启动脚本
简化的服务启动程序，用于测试和部署
"""

import asyncio
from core.async_main import async_main
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import logging
from core.logging_config import setup_logging
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

async def test_import():
    """测试模块导入"""
    try:
        logger.info('测试导入核心模块...')
        from core.pqai_search import PQAIEnhancedPatentSearcher
        logger.info('✅ 核心模块导入成功')

        logger.info('测试初始化检索器...')
        searcher = PQAIEnhancedPatentSearcher()
        logger.info('✅ 检索器初始化成功')

        return searcher
    except Exception as e:
        logger.error(f"❌ 模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def start_simple_service():
    """启动简化版服务"""
    try:
        # 测试导入
        searcher = await test_import()
        if not searcher:
            logger.error('无法启动服务：模块导入失败')
            return False

        logger.info('正在启动PQAI专利检索服务...')

        # 导入FastAPI应用
        from api.pqai_service import app

        logger.info('✅ FastAPI应用加载成功')
        logger.info('🚀 PQAI专利检索服务启动成功!')
        logger.info('📍 服务地址: http://localhost:8030')
        logger.info('🎯 核心功能: 基于PQAI算法的增强专利检索')
        logger.info('📊 API文档: http://localhost:8030/docs')

        # 启动服务
        import uvicorn
        await uvicorn.run(app, host='0.0.0.0', port=8030, log_level='info')

        return True

    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main() -> None:
    """主函数"""
    logger.info('🚀 启动PQAI专利检索服务...')
    print('📍 项目路径:', os.path.dirname(os.path.abspath(__file__)))
    print('🐍 Python路径:', sys.path[0])

    # 检查必要文件
    required_files = [
        'core/pqai_search.py',
        'api/pqai_service.py'
    ]

    for file_path in required_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            logger.info(f"✅ {file_path} - 存在")
        else:
            logger.info(f"❌ {file_path} - 不存在")
            return False

    logger.info("\n🔄 启动服务...")

    try:
        asyncio.run(start_simple_service())
    except KeyboardInterrupt:
        logger.info("\n⏹️  服务已停止")
    except Exception as e:
        logger.info(f"\n❌ 服务启动失败: {e}")
        return False

    return True

if __name__ == '__main__':
    exit(main())