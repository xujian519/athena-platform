#!/usr/bin/env python3
"""
索引更多专利数据到Elasticsearch
"""

import json
import logging
import time

import requests

logger = logging.getLogger(__name__)

def index_patents_batch():
    """批量索引专利数据"""
    base_url = 'http://localhost:5001'

    # 索引10万条专利
    logger.info('🚀 开始索引专利数据到Elasticsearch...')

    response = requests.post(
        f"{base_url}/api/data/index",
        json={'limit': 100000}
    )

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            logger.info(f"✅ 索引任务已启动")
            logger.info(f"📝 任务ID: {result.get('task_id')}")
            logger.info(f"📊 最多索引: 100,000 条专利")
            logger.info(f"🔄 请稍候等待后台任务完成...")

            # 等待索引完成
            time.sleep(60)

            # 检查索引状态
            status_response = requests.get(f"{base_url}/api/index/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get('success'):
                    status = status_data['index_status']
                    logger.info(f"\n📊 当前索引状态:")
                    logger.info(f"   文档数量: {status.get('document_count', 0):,}")
                    logger.info(f"   存储大小: {status.get('store_size', 0)/1024/1024:.2f} MB")
                    logger.info(f"   状态: {status.get('status', 'unknown')}")
        else:
            logger.info(f"❌ 索引失败: {result.get('error')}")
    else:
        logger.info(f"❌ 请求失败: {response.status_code}")
        logger.info(f"错误: {response.text}")

if __name__ == '__main__':
    index_patents_batch()