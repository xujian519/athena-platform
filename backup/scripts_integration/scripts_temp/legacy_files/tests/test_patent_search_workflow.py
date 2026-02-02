#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利检索工作流测试案例
Test Cases for Patent Search Workflow
"""

import json
import logging
from datetime import datetime

from patent_search_workflow import PatentSearchWorkflow

logger = logging.getLogger(__name__)

def test_creativity_search():
    """测试创造性检索"""
    logger.info(str('='*80))
    logger.info('测试案例 1：创造性检索')
    logger.info(str('='*80))

    # 创建工作流实例
    workflow = PatentSearchWorkflow()

    # 目标专利：CN200920113915.8 拉紧器
    target_patent = {
        'patent_number': 'CN200920113915.8',
        'publication_number': 'CN201390190Y',
        'title': '拉紧器',
        'ipc_classes': ['B65P 7/06'],
        'application_date': '2009-01-24',
        'publication_date': '2010-06-23',
        'applicant': '浙江双友物流器械股份有限公司',
        'abstract': '一种拉紧器，包括连接件和调节件，通过螺纹联接，具有手柄和双挂钩结构。'
    }

    # 执行创造性检索工作流
    result = workflow.execute_search_workflow(target_patent, 'creativity')

    # 输出关键结果
    logger.info(str("\n" + '='*80))
    logger.info('检索结果摘要')
    logger.info(str('='*80))
    logger.info(f"工作流ID: {result['workflow_id']}")
    logger.info(f"检索类型: {result['search_type']}")
    logger.info(f"有效现有技术数量: {len(result['search_results'])}")

    # 显示验证报告
    validation_report = result.get('validation_report', {})
    logger.info("\n验证报告:")
    logger.info(f"- 总检索结果: {validation_report.get('summary', {}).get('total_results', 0)}")
    logger.info(f"- 有效现有技术: {validation_report.get('summary', {}).get('valid_prior_art', 0)}")
    logger.info(f"- 验证通过率: {validation_report.get('summary', {}).get('validation_rate', 0):.2%}")

    # 显示时间分析
    time_analysis = validation_report.get('time_analysis', {})
    if time_analysis:
        logger.info("\n时间分析:")
        logger.info(f"- 最早的现有技术: {time_analysis.get('earliest_prior_art', 0)} 天前")
        logger.info(f"- 最晚的现有技术: {time_analysis.get('latest_prior_art', 0)} 天前")
        logger.info(f"- 平均时间差: {time_analysis.get('average_gap', 0):.0f} 天")

        dist = time_analysis.get('time_distribution', {})
        if dist:
            logger.info('- 时间分布:')
            logger.info(f"  - 1年内: {dist.get('within_1_year', 0)} 项")
            logger.info(f"  - 3年内: {dist.get('within_3_years', 0)} 项")
            logger.info(f"  - 5年内: {dist.get('within_5_years', 0)} 项")
            logger.info(f"  - 5年以上: {dist.get('more_than_5_years', 0)} 项")

    # 显示质量评估
    quality_report = result.get('quality_report', {})
    logger.info("\n质量评估:")
    logger.info(f"- 总体质量分数: {quality_report.get('overall_score', 0):.1f}/100")
    logger.info(f"- 检索覆盖度: {quality_report.get('search_coverage', 0):.2%}")
    logger.info(f"- 结果相关性: {quality_report.get('result_relevance', 0):.2%}")
    logger.info(f"- 数据完整性: {quality_report.get('data_integrity', 0):.2%}")

    return result

def test_novelty_search():
    """测试新颖性检索"""
    logger.info(str("\n\n" + '='*80))
    logger.info('测试案例 2：新颖性检索')
    logger.info(str('='*80))

    # 创建工作流实例
    workflow = PatentSearchWorkflow()

    # 使用同样的目标专利，但进行新颖性检索
    target_patent = {
        'patent_number': 'CN200920113915.8',
        'title': '拉紧器',
        'ipc_classes': ['B65P 7/06'],
        'application_date': '2009-01-24',
        'abstract': '一种拉紧器，包括连接件和调节件，通过螺纹联接。'
    }

    # 执行新颖性检索工作流
    result = workflow.execute_search_workflow(target_patent, 'novelty')

    # 输出关键结果
    logger.info(str("\n" + '='*80))
    logger.info('检索结果摘要')
    logger.info(str('='*80))

    # 显示验证报告（包含抵触申请）
    validation_report = result.get('validation_report', {})
    logger.info('验证报告:')
    logger.info(f"- 总检索结果: {validation_report.get('summary', {}).get('total_results', 0)}")
    logger.info(f"- 有效现有技术: {validation_report.get('summary', {}).get('valid_prior_art', 0)}")
    logger.info(f"- 抵触申请: {validation_report.get('summary', {}).get('conflicting_applications', 0)}")
    logger.info(f"- 验证通过率: {validation_report.get('summary', {}).get('validation_rate', 0):.2%}")

    return result

def demonstrate_time_validation_rules():
    """演示时间验证规则"""
    logger.info(str("\n\n" + '='*80))
    logger.info('时间验证规则说明')
    logger.info(str('='*80))

    logger.info(str("""
1. 创造性检索的时间要求：
   - 必须检索目标专利申请日之前公开的全部专利
   - 现有技术的公开日必须早于目标专利的申请日
   - 抵触申请不用于创造性判断

2. 新颖性检索的时间要求：
   - 检索目标专利申请日之前的全部专利
   - 特别关注抵触申请（在后申请但在先公开的专利）
   - 抵触申请可以破坏新颖性

3. 本案例说明：
   - 目标专利申请日：2009年1月24日
   - 需要检索2009年1月24日之前的所有相关专利
   - 无效决定中引用的证据1（CN2444027Y）公开日为2002年9月25日，符合要求
   - 无效决定中引用的证据3（CN201367540Y）公开日为2009年12月23日，不符合要求
    """))

def main():
    """主函数"""
    logger.info('专利检索工作流测试')
    logger.info(str('='*80))
    logger.info('目标专利：CN200920113915.8 拉紧器')
    logger.info('目标专利申请日：2009-01-24')
    logger.info(str('='*80))

    # 执行测试
    creativity_result = test_creativity_search()
    novelty_result = test_novelty_search()

    # 说明时间验证规则
    demonstrate_time_validation_rules()

    # 保存测试结果
    test_results = {
        'creativity_search': creativity_result,
        'novelty_search': novelty_result,
        'test_timestamp': datetime.now().isoformat()
    }

    output_file = '/Users/xujian/Athena工作平台/test_workflow_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)

    logger.info(f"\n✅ 测试完成！结果已保存到: {output_file}")


if __name__ == '__main__':
    main()