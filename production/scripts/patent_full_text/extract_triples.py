#!/usr/bin/env python3
"""
专利三元组提取脚本
Patent Triple Extraction Script

从已处理的专利文件中提取问题-特征-效果三元组
"""

from __future__ import annotations
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 设置路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
PATENT_PROCESSED_DIR = PROJECT_ROOT / "apps/apps/patents" / "processed"
TRIPLE_OUTPUT_DIR = PATENT_PROCESSED_DIR / "triples"

sys.path.insert(0, str(PROJECT_ROOT / "production/dev/scripts/patent_full_text/phase3"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_processed_patents() -> list[dict]:
    """加载已处理的专利数据"""
    patent_files = list(PATENT_PROCESSED_DIR.glob("[A-Z]*.json"))
    patents = []

    for patent_file in patent_files:
        if "processing_report" in patent_file.name:
            continue

        try:
            with open(patent_file, encoding='utf-8') as f:
                patent_data = json.load(f)

                # 只处理有足够文本的专利
                if patent_data.get('text_length', 0) > 100:
                    patents.append(patent_data)
                    logger.info(f"加载: {patent_data['patent_number']} ({patent_data['text_length']} 字符)")
        except Exception as e:
            logger.error(f"加载失败 {patent_file.name}: {e}")

    return patents


def extract_triples_for_patent(patent_data: dict) -> dict:
    """
    为单个专利提取三元组

    Returns:
        提取结果字典
    """
    patent_number = patent_data['patent_number']
    full_text = patent_data.get('full_text', '')

    logger.info(f"\n{'='*60}")
    logger.info(f"提取三元组: {patent_number}")
    logger.info(f"{'='*60}")

    result = {
        'patent_number': patent_number,
        'success': False,
        'problems': [],
        'features': [],
        'effects': [],
        'triples': [],
        'feature_relations': [],
        'processing_time': 0,
        'error': None
    }

    if not full_text:
        result['error'] = "无文本内容"
        logger.warning("  ⚠️  无文本内容，跳过")
        return result

    try:
        import time

        from rule_extractor import RuleExtractor

        start_time = time.time()

        # 初始化提取器
        extractor = RuleExtractor()

        # 执行提取
        extraction_result = extractor.extract(
            patent_number=patent_number,
            patent_text=full_text
        )

        # 转换结果为字典
        if extraction_result.success:
            result['success'] = True
            result['problems'] = [p.to_dict() for p in extraction_result.problems]
            result['features'] = [f.to_dict() for f in extraction_result.features]
            result['effects'] = [e.to_dict() for e in extraction_result.effects]
            result['triples'] = [t.to_dict() for t in extraction_result.triples]
            result['feature_relations'] = [r.to_dict() for r in extraction_result.feature_relations]
            result['processing_time'] = extraction_result.processing_time
            result['extraction_confidence'] = extraction_result.extraction_confidence

            logger.info("  ✅ 提取完成:")
            logger.info(f"     - 问题: {len(result['problems'])}")
            logger.info(f"     - 特征: {len(result['features'])}")
            logger.info(f"     - 效果: {len(result['effects'])}")
            logger.info(f"     - 三元组: {len(result['triples'])}")
            logger.info(f"     - 特征关系: {len(result['feature_relations'])}")
            logger.info(f"     - 置信度: {result['extraction_confidence']:.2f}")
        else:
            result['error'] = extraction_result.error_message
            logger.error(f"  ❌ 提取失败: {result['error']}")

    except Exception as e:
        result['error'] = str(e)
        logger.error(f"  ❌ 提取异常: {e}")

    result['processing_time'] = time.time() - start_time
    return result


def save_triple_results(patent_number: str, triple_result: dict, patent_data: dict) -> None:
    """保存三元组提取结果"""
    TRIPLE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = TRIPLE_OUTPUT_DIR / f"{patent_number}_triples.json"

    # 合并专利数据和三元组数据
    combined_data = {
        'patent_info': {
            'patent_number': patent_data['patent_number'],
            'title': patent_data.get('title', '')[:200],
            'abstract': patent_data.get('abstract', '')[:500],
            'text_length': patent_data.get('text_length', 0),
            'extraction_method': patent_data.get('extraction_method', ''),
            'pages_processed': patent_data.get('pages_processed', 0)
        },
        'triple_extraction': triple_result,
        'timestamp': datetime.now().isoformat()
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)

    return output_file


def main() -> None:
    """主流程"""
    logger.info("="*70)
    logger.info("专利三元组提取")
    logger.info("="*70)

    # 加载已处理的专利
    patents = load_processed_patents()

    if not patents:
        logger.warning("没有找到已处理的专利数据")
        return

    logger.info(f"\n共 {len(patents)} 个专利待提取三元组")

    # 提取每个专利的三元组
    results = []
    for patent in patents:
        triple_result = extract_triples_for_patent(patent)
        results.append(triple_result)

        # 保存结果
        if triple_result['success']:
            output_file = save_triple_results(
                patent['patent_number'],
                triple_result,
                patent
            )
            logger.info(f"  💾 已保存: {output_file.name}")

    # 保存总结报告
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_patents': len(patents),
        'successful': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success']),
        'total_problems': sum(len(r.get('problems', [])) for r in results),
        'total_features': sum(len(r.get('features', [])) for r in results),
        'total_effects': sum(len(r.get('effects', [])) for r in results),
        'total_triples': sum(len(r.get('triples', [])) for r in results),
        'total_feature_relations': sum(len(r.get('feature_relations', [])) for r in results),
        'reports/reports/results': results
    }

    summary_file = TRIPLE_OUTPUT_DIR / "extraction_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 打印总结
    logger.info(f"\n{'='*70}")
    logger.info("三元组提取完成")
    logger.info(f"{'='*70}")
    logger.info(f"成功: {summary['successful']}/{summary['total_patents']}")
    logger.info(f"总问题数: {summary['total_problems']}")
    logger.info(f"总特征数: {summary['total_features']}")
    logger.info(f"总效果数: {summary['total_effects']}")
    logger.info(f"总三元组数: {summary['total_triples']}")
    logger.info(f"总特征关系数: {summary['total_feature_relations']}")
    logger.info(f"输出目录: {TRIPLE_OUTPUT_DIR}")
    logger.info(f"总结报告: {summary_file}")
    logger.info("")

    # 显示失败的专利
    if summary['failed'] > 0:
        logger.info("❌ 失败的专利:")
        for result in results:
            if not result['success']:
                logger.info(f"   - {result['patent_number']}: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()
