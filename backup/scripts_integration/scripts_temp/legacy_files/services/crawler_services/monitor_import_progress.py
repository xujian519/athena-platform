#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利知识图谱导入监控器
Monitor Patent Knowledge Graph Import Progress
"""

import logging
import os
import sqlite3
import time
from datetime import datetime

logger = logging.getLogger(__name__)

def monitor_import():
    """监控导入进度"""
    db_path = '/Users/xujian/Athena工作平台/data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db'

    logger.info('🔍 专利知识图谱导入监控器')
    logger.info(str('=' * 50))

    while True:
        try:
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # 获取基本统计
                cursor.execute('SELECT COUNT(*) FROM patent_entities')
                entity_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM patent_relations')
                relation_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(DISTINCT patent_id) FROM patent_entities WHERE patent_id IS NOT NULL')
                patent_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM batch_info')
                batch_count = cursor.fetchone()[0]

                # 获取批次状态
                cursor.execute("""
                    SELECT status, COUNT(*) FROM batch_info GROUP BY status
                """)
                batch_status = dict(cursor.fetchall())

                # 获取文件大小
                file_size = os.path.getsize(db_path) / 1024 / 1024  # MB

                # 清屏并显示进度
                os.system('clear' if os.name == 'posix' else 'cls')

                logger.info(f"🕐 监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(str('=' * 50))
                logger.info(f"📊 导入进度统计:")
                logger.info(f"   🎯 专利数量: {patent_count:,}")
                logger.info(f"   📋 实体数量: {entity_count:,}")
                logger.info(f"   🔗 关系数量: {relation_count:,}")
                logger.info(f"   📦 批次数量: {batch_count}")
                logger.info(f"   💾 数据库大小: {file_size:.2f} MB")

                logger.info(f"\n📈 批次状态:")
                status_icons = {
                    'pending': '⏳ 等待中',
                    'processing': '🔄 处理中',
                    'completed': '✅ 已完成',
                    'error': '❌ 错误'
                }

                for status, count in batch_status.items():
                    icon = status_icons.get(status, '❓ 未知')
                    logger.info(f"   {icon}: {count}")

                # 查看最新完成的批次
                cursor.execute("""
                    SELECT batch_number, status, entity_count, relation_count, completed_at
                    FROM batch_info
                    WHERE status = 'completed'
                    ORDER BY completed_at DESC
                    LIMIT 3
                """)
                recent_completed = cursor.fetchall()

                if recent_completed:
                    logger.info(f"\n✅ 最近完成批次:")
                    for batch in recent_completed:
                        logger.info(f"   批次{batch[0]}: 实体{batch[2]:,}, 关系{batch[3]:,} ({batch[4]})")

                # 预估进度
                cursor.execute('SELECT MAX(batch_number) FROM batch_info')
                max_batch = cursor.fetchone()[0] or 0

                total_expected_files = 25  # 根据之前的分析
                progress_percent = (max_batch / total_expected_files) * 100

                logger.info(f"\n📊 进度预估:")
                logger.info(f"   文件进度: {max_batch}/{total_expected_files} ({progress_percent:.1f}%)")

                # 生成进度条
                bar_length = 50
                filled_length = int(bar_length * progress_percent / 100)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                logger.info(f"   [{bar}] {progress_percent:.1f}%")

                conn.close()

                # 如果所有批次都完成，显示最终统计
                if batch_count >= total_expected_files and batch_status.get('completed', 0) >= total_expected_files - 1:
                    logger.info(f"\n🎉 导入完成!")
                    logger.info(f"   最终统计: {patent_count:,} 专利, {entity_count:,} 实体, {relation_count:,} 关系")
                    break

            else:
                logger.info(f"📁 数据库文件尚未创建，等待中...")

        except Exception as e:
            logger.info(f"❌ 监控错误: {e}")

        # 每5秒更新一次
        time.sleep(5)

if __name__ == '__main__':
    try:
        monitor_import()
    except KeyboardInterrupt:
        logger.info("\n👋 监控已停止")