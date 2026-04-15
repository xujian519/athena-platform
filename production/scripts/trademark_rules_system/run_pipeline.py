#!/usr/bin/env python3
"""
商标规则数据库快速启动脚本
Quick Start Script for Trademark Rules Database

使用示例：
    python run_pipeline.py                    # 运行完整管道
    python run_pipeline.py --skip-pdf         # 跳过PDF处理
    python run_pipeline.py --skip-vector      # 跳过向量化
    python run_pipeline.py --skip-graph       # 跳过知识图谱

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from production.scripts.trademark_rules_system.pipeline import TrademarkRulesPipeline

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.stream_handler(),
        logging.file_handler('trademark_pipeline.log')
    ]
)
logger = logging.getLogger(__name__)


def get_default_config() -> Any | None:
    """获取默认配置"""
    return {
        'data_dir': str(project_root / 'data/商标'),
        'output_dir': str(project_root / 'data/trademark_rules'),
        'database': {
            'pg_host': os.getenv('PG_HOST', 'localhost'),
            'pg_port': int(os.getenv('PG_PORT', 5432)),  # 使用默认PostgreSQL端口
            'pg_database': os.getenv('PG_DATABASE', 'trademark_database'),
            'pg_user': os.getenv('PG_USER', os.getenv('USER', 'xujian')),  # 使用当前系统用户
            'pg_password': os.getenv('PG_PASSWORD', ''),  # 本地PostgreSQL通常不需要密码
            'qdrant_url': os.getenv('QDRANT_URL', 'http://localhost:6333'),
            'nebula_hosts': os.getenv('NEBULA_HOSTS', '127.0.0.1').split(','),
            'nebula_port': int(os.getenv('NEBULA_PORT', 9669)),
            'nebula_user': os.getenv('NEBULA_USER', 'root'),
            'nebula_password': os.getenv('NEBULA_PASSWORD', 'nebula'),
            'nebula_space': os.getenv('NEBULA_SPACE', 'trademark_graph')
        }
    }


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='商标规则数据库构建管道',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_pipeline.py                    # 运行完整管道
  python run_pipeline.py --skip-pdf         # 跳过PDF处理
  python run_pipeline.py --skip-vector      # 跳过向量化
  python run_pipeline.py --skip-graph       # 跳过知识图谱
  python run_pipeline.py --data-dir /path/to/data  # 指定数据目录
        """
    )

    parser.add_argument(
        '--data-dir',
        help='数据目录路径（默认: ./data/商标）'
    )
    parser.add_argument(
        '--output-dir',
        help='输出目录路径（默认: ./data/trademark_rules）'
    )
    parser.add_argument(
        '--skip-pdf',
        action='store_true',
        help='跳过大PDF文件处理'
    )
    parser.add_argument(
        '--skip-vector',
        action='store_true',
        help='跳过向量化处理'
    )
    parser.add_argument(
        '--skip-graph',
        action='store_true',
        help='跳过知识图谱构建'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='不清理临时文件'
    )

    args = parser.parse_args()

    # 加载配置
    config = get_default_config()

    # 命令行参数覆盖
    if args.data_dir:
        config['data_dir'] = args.data_dir
    if args.output_dir:
        config['output_dir'] = args.output_dir

    # 添加跳过选项
    config['skip_pdf'] = args.skip_pdf
    config['skip_vector'] = args.skip_vector
    config['skip_graph'] = args.skip_graph
    config['cleanup'] = not args.no_cleanup

    # 打印配置
    logger.info("="*60)
    logger.info("商标规则数据库构建管道")
    logger.info("="*60)
    logger.info(f"数据目录: {config['data_dir']}")
    logger.info(f"输出目录: {config['output_dir']}")
    logger.info(f"跳过PDF: {config['skip_pdf']}")
    logger.info(f"跳过向量化: {config['skip_vector']}")
    logger.info(f"跳过知识图谱: {config['skip_graph']}")
    logger.info("="*60)

    # 检查数据目录
    data_dir = Path(config['data_dir'])
    if not data_dir.exists():
        logger.error(f"❌ 数据目录不存在: {data_dir}")
        return 1

    # 统计文件
    md_files = list(data_dir.glob('*.md'))
    pdf_files = list(data_dir.glob('*.pdf'))

    logger.info(f"📁 找到 {len(md_files)} 个MD文件")
    logger.info(f"📄 找到 {len(pdf_files)} 个PDF文件")

    if not md_files and not pdf_files:
        logger.error("❌ 没有找到可处理的文件")
        return 1

    # 运行管道
    start_time = datetime.now()
    logger.info("🚀 开始执行管道...")

    try:
        pipeline = TrademarkRulesPipeline(config)
        result = await pipeline.run()

        if config['cleanup']:
            await pipeline.cleanup()

        # 打印结果
        duration = (datetime.now() - start_time).total_seconds()

        logger.info("="*60)
        logger.info("✅ 管道执行完成！")
        logger.info("="*60)
        logger.info(f"⏱️  执行时间: {duration:.2f} 秒")
        logger.info(f"📁 处理文件: {result.get('processed_files', 0)}")
        logger.info(f"📚 法规数量: {result.get('total_norms', 0)}")
        logger.info(f"📋 条款数量: {result.get('total_articles', 0)}")
        logger.info(f"🔢 向量数量: {result.get('total_vectors', 0)}")
        logger.info(f"🕸️  图谱节点: {result.get('total_graph_nodes', 0)}")

        errors = result.get('errors', [])
        if errors:
            logger.warning(f"⚠️  错误数量: {len(errors)}")
            for error in errors[:5]:  # 只显示前5个
                logger.warning(f"   - {error}")

        logger.info("="*60)

        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️  用户中断执行")
        return 130

    except Exception as e:
        logger.error(f"❌ 管道执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
