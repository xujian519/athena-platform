#!/usr/bin/env python3
"""
专利CLI工具 - 支持PDF专利文档的新颖性分析
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加src目录到Python路径
src_path = os.path.join(os.getcwd(), 'src', 'models')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import asyncio

from novelty_analyzer import NoveltyAnalyzer
from perception_layer import EnhancedPerceptionLayer


class PatentPDFCLI:
    """支持PDF的专利CLI工具"""

    def __init__(self):
        self.workspace = Path('.')
        self.tasks_dir = self.workspace / 'tasks'
        self.data_dir = self.workspace / 'data'
        self.perception = EnhancedPerceptionLayer()
        self.novelty_analyzer = NoveltyAnalyzer()

    def analyze_pdf_novelty(self, pdf_path: str, task_title: str = None):
        """
        分析PDF专利文档的新颖性

        Args:
            pdf_path: PDF文件路径
            task_title: 任务标题（可选）
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            logger.info(f"❌ PDF文件不存在: {pdf_path}")
            return

        # 生成任务ID和标题
        task_id = f"PDF_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not task_title:
            task_title = f"PDF专利分析 - {pdf_path.stem}"

        logger.info("🔍 开始分析PDF专利文档")
        logger.info(f"📄 文件: {pdf_path}")
        logger.info(f"🆔 任务ID: {task_id}")

        # 创建任务目录
        task_dir = self.tasks_dir / task_id
        os.makedirs(task_dir / 'raw', exist_ok=True)
        os.makedirs(task_dir / 'novelty', exist_ok=True)

        try:
            # 第一步：感知层 - 解析PDF并提取权利要求1特征
            logger.info("\n📋 步骤1: PDF解析和特征提取...")
            features = self.perception.get_claim_1_features(str(pdf_path))

            if not features:
                logger.info('❌ 未能提取到权利要求1的技术特征')
                return

            logger.info(f"✅ 提取到 {len(features)} 个技术特征:")
            for i, feature in enumerate(features, 1):
                logger.info(f"  {i}. {feature.description} ({feature.category})")

            # 保存特征提取结果
            features_data = {
                'task_id': task_id,
                'pdf_file': str(pdf_path),
                'claim_number': 1,
                'features': [
                    {
                        'feature_id': f.feature_id,
                        'description': f.description,
                        'category': f.category,
                        'importance': f.importance,
                        'keywords': f.keywords,
                        'confidence': f.confidence
                    } for f in features
                ],
                'extraction_time': datetime.now().isoformat()
            }

            features_file = task_dir / 'novelty' / 'claim1_features.json'
            with open(features_file, 'w', encoding='utf-8') as f:
                json.dump(features_data, f, ensure_ascii=False, indent=2)

            logger.info(f"💾 特征提取结果已保存到: {features_file}")

            # 第二步：新颖性分析
            logger.info("\n🔍 步骤2: 新颖性分析...")

            # 将特征转换为文本用于新颖性分析
            features_text = ' '.join([f.description for f in features])

            # 执行新颖性分析
            result = asyncio.run(self.novelty_analyzer.analyze_novelty(task_id, features_text))

            # 更新结果，包含权利要求1的详细信息
            result_dict = {
                'task_id': task_id,
                'pdf_file': str(pdf_path),
                'claim_number': 1,
                'overall_novelty': result.overall_novelty,
                'novelty_score': result.novelty_score,
                'extracted_features': features_data['features'],
                'closest_prior_art': {
                    'doc_id': result.closest_prior_art.doc_id if result.closest_prior_art else None,
                    'title': result.closest_prior_art.title if result.closest_prior_art else None,
                    'similarity_score': result.closest_prior_art.similarity_score if result.closest_prior_art else 0
                },
                'distinguishing_features': [
                    {
                        'feature_id': f.feature_id,
                        'description': f.description,
                        'category': f.category,
                        'importance': f.importance
                    } for f in result.distinguishing_features
                ],
                'evidence_chain': result.evidence_chain,
                'recommendation': result.recommendation,
                'analysis_time': datetime.now().isoformat()
            }

            # 保存新颖性分析结果
            result_file = task_dir / 'novelty' / 'analysis_result.json'
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)

            # 显示结果
            logger.info("\n🎯 新颖性分析完成!")
            logger.info(f"结果: {'✅ 具备新颖性' if result.overall_novelty else '❌ 不具备新颖性'}")
            logger.info(f"新颖性分数: {result.novelty_score:.2f}")
            logger.info(f"区别特征: {len(result.distinguishing_features)} 个")

            if result.closest_prior_art:
                logger.info(f"最接近现有技术: {result.closest_prior_art.title}")
                logger.info(f"相似度: {result.closest_prior_art.similarity_score:.2f}")

            logger.info(f"\n💡 建议: {result.recommendation}")
            logger.info(f"\n📁 结果文件: {result_file}")

            return result_dict

        except Exception as e:
            logger.info(f"❌ 分析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='专利PDF新颖性分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python patent_cli_pdf.py analyze /path/to/patent.pdf
  python patent_cli_pdf.py analyze /path/to/patent.pdf --title '我的专利分析'
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # analyze命令
    parser_analyze = subparsers.add_parser('analyze', help='分析PDF专利的新颖性')
    parser_analyze.add_argument('pdf_file', help='PDF专利文件路径')
    parser_analyze.add_argument('--title', '-t', help='分析任务标题')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = PatentPDFCLI()

    if args.command == 'analyze':
        result = cli.analyze_pdf_novelty(args.pdf_file, args.title)
        if result:
            logger.info("\n🎉 分析成功完成!")
        else:
            logger.info("\n❌ 分析失败!")

if __name__ == '__main__':
    main()
