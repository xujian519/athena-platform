#!/usr/bin/env python3
"""
专利近似分析工具 - 生产环境包装器
Production Wrapper for Patent Similarity Analysis Tool

作者: Athena AI系统
创建时间: 2026-01-27
版本: v2.0.0 - 更名: CAP02 → 专利近似分析工具
"""

from __future__ import annotations
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "services" / "patent-similarity-analysis" / "src"))

from main import BatchPatentSimilarityPreparer, PatentSimilarityPreparer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production/logs/patent_similarity_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def load_config():
    """加载配置文件"""
    config_path = Path('production/config/patent_similarity_config.json')

    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}")
        return {}

    with open(config_path) as f:
        return json.load(f)


def process_single_case(case_name, pdf_files, config):
    """处理单个案件"""
    logger.info(f"开始处理案件: {case_name}")
    logger.info(f"PDF文件: {len(pdf_files)}个")

    try:
        # 创建专利近似分析工具
        preparer = PatentSimilarityPreparer(
            bert_ner_model_path=config.get('models', {}).get('bert_ner', {}).get('model_path'),
            bge_m3_model=config.get('models', {}).get('bge_m3', {}).get('model_path'),
            device=config.get('models', {}).get('bert_ner', {}).get('device', 'cpu')
        )

        # 处理PDF
        logger.info("开始PDF解析和处理...")
        similarity_data = preparer.prepare_from_pdfs(pdf_files)

        # 导出结果
        output_dir = Path(config.get('output', {}).get('directory', 'production/output'))
        output_dir.mkdir(parents=True, exist_ok=True)

        json_output = output_dir / f"{case_name}_similarity_analysis.json"
        summary_output = output_dir / f"{case_name}_summary.txt"

        preparer.export_to_json(similarity_data, str(json_output))
        preparer.export_summary(similarity_data, str(summary_output))

        logger.info(f"✅ 案件处理完成: {case_name}")
        logger.info(f"  - JSON输出: {json_output}")
        logger.info(f"  - 摘要输出: {summary_output}")

        # 释放资源
        preparer.release_resources()
        logger.info("✅ 资源已释放")

        return True

    except Exception as e:
        logger.error(f"❌ 案件处理失败: {case_name} - {e}", exc_info=True)
        return False


def process_batch(cases, config):
    """批量处理案件"""
    logger.info(f"开始批量处理: {len(cases)}个案件")

    batch_config = config.get('processing', {})
    batch_processor = BatchPatentSimilarityPreparer(
        batch_size=batch_config.get('batch_size', 2),
        device=config.get('models', {}).get('bert_ner', {}).get('device', 'cpu')
    )

    output_dir = Path(config.get('output', {}).get('directory', 'production/output'))
    output_dir.mkdir(parents=True, exist_ok=True)

    results = batch_processor.process_batch(
        cases=cases,
        output_dir=str(output_dir),
        cleanup_between_batches=batch_config.get('cleanup_between_batches', True)
    )

    logger.info("=" * 60)
    logger.info("批量处理完成")
    logger.info(f"  - 总计: {results['total']} 个案件")
    logger.info(f"  - 成功: {results['success']} 个")
    logger.info(f"  - 失败: {results['failed']} 个")
    logger.info("=" * 60)

    return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='CAP02数据准备工具 - 生产环境',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:

  # 处理单个案件
  python patent_similarity_analysis.py single --name "案件A" --pdfs target.pdf d1.pdf

  # 批量处理
  python patent_similarity_analysis.py batch --cases cases.json

  # 查看状态
  python patent_similarity_analysis.py status
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 单个案件处理命令
    single_parser = subparsers.add_parser('single', help='处理单个案件')
    single_parser.add_argument('--name', required=True, help='案件名称')
    single_parser.add_argument('--pdfs', nargs='+', required=True, help='PDF文件列表')

    # 批量处理命令
    batch_parser = subparsers.add_parser('batch', help='批量处理案件')
    batch_parser.add_argument('--cases', required=True, help='案件定义JSON文件')

    # 状态命令
    subparsers.add_parser('status', help='查看处理状态')

    args = parser.parse_args()

    # 加载配置
    config = load_config()

    # 执行命令
    if args.command == 'single':
        success = process_single_case(args.name, args.pdfs, config)
        sys.exit(0 if success else 1)

    elif args.command == 'batch':
        # 加载案件定义
        with open(args.cases) as f:
            cases = json.load(f)

        results = process_batch(cases, config)
        sys.exit(0 if results['failed'] == 0 else 1)

    elif args.command == 'status':
        # 显示状态
        output_dir = Path(config.get('output', {}).get('directory', 'production/output'))

        print("专利近似分析工具 - 状态")
        print("=" * 60)

        if output_dir.exists():
            json_files = list(output_dir.glob("*_similarity_analysis.json"))
            print(f"已处理案件数: {len(json_files)}")
            print(f"输出目录: {output_dir}")

            if json_files:
                print("\n最近处理的案件:")
                for f in sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    size = f.stat().st_size / 1024
                    print(f"  - {f.stem}: {mtime.strftime('%Y-%m-%d %H:%M')} ({size:.1f}KB)")
        else:
            print("输出目录不存在")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
