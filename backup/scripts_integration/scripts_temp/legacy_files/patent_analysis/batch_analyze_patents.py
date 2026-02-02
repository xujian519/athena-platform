#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量专利分析脚本
Batch Patent Analysis Script

自动分析指定目录中的所有专利文件
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

sys.path.append('/Users/xujian/Athena工作平台')

# 导入分析器
from comprehensive_patent_analyzer import ComprehensivePatentAnalyzer


def analyze_all_patents():
    """分析所有专利文件"""
    # 专利文件目录
    patent_dir = Path('/Users/xujian/Athena工作平台/工作/专利分析/2025.12.12三件')
    
    # 找出所有.doc文件
    patent_files = list(patent_dir.glob('*.doc'))
    
    logger.info(f"找到 {len(patent_files)} 个专利文件:")
    for i, file in enumerate(patent_files, 1):
        logger.info(f"  {i}. {file.name}")
    
    # 创建分析器
    analyzer = ComprehensivePatentAnalyzer()
    
    # 分析每个文件
    for patent_file in patent_files:
        logger.info(f"\n{'='*80}")
        logger.info(f"\n正在分析: {patent_file.name}")
        logger.info(f"{'='*80}")
        
        # 加载文档
        patent_doc = analyzer.load_patent_document(str(patent_file))
        
        if patent_doc:
            # 执行各项分析
            logger.info("\n[1/6] 分析说明书摘要...")
            analyzer.analyze_abstract(patent_doc)
            
            logger.info('[2/6] 分析权利要求书...')
            analyzer.analyze_claims(patent_doc)
            
            logger.info('[3/6] 分析说明书...')
            analyzer.analyze_description(patent_doc)
            
            logger.info('[4/6] 分析说明书附图...')
            analyzer.analyze_drawings_description(patent_doc)
            
            logger.info('[5/6] 进行创造性分析（含专利检索）...')
            analyzer.analyze_creativity_with_search(patent_doc)
            
            logger.info('[6/6] 分析专利法第26条符合性...')
            analyzer.analyze_article_26_compliance(patent_doc)
            
            # 生成报告
            report = analyzer.generate_comprehensive_report(patent_doc)
            
            # 保存报告
            report_path = patent_file.with_suffix('_分析报告.md')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"\n✅ 分析完成! 报告已保存至: {report_path}")
            
            # 显示简要结果
            abs_score = analyzer.analysis_results['abstract'].get('score', 0)
            claims_score = analyzer.analysis_results['claims'].get('score', 0)
            desc_score = analyzer.analysis_results['description'].get('score', 0)
            draw_score = analyzer.analysis_results['drawings'].get('score', 0)
            creat_score = analyzer.analysis_results['creativity'].get('score', 0)
            art26_score = analyzer.analysis_results['article_26'].get('overall_score', 0)
            
            # 计算综合得分
            total_score = (abs_score * 0.15 + claims_score * 0.30 + 
                          desc_score * 0.25 + draw_score * 0.10 + 
                          creat_score * 0.15 + art26_score * 0.05)
            
            logger.info("\n📊 分析结果摘要:")
            logger.info(f"  说明书摘要:     {abs_score:>3}/100")
            logger.info(f"  权利要求书:     {claims_score:>3}/100")
            logger.info(f"  说明书:         {desc_score:>3}/100")
            logger.info(f"  说明书附图:     {draw_score:>3}/100")
            logger.info(f"  创造性分析:     {creat_score:>3}/100")
            logger.info(f"  专利法第26条:   {art26_score:>3}/100")
            logger.info(f"  综合得分:       {total_score:>5.1f}/100")
            
            # 显示关键问题
            issues = []
            if abs_score < 70:
                issues.append('摘要需要改进')
            if claims_score < 70:
                issues.append('权利要求书需要完善')
            if desc_score < 70:
                issues.append('说明书存在问题')
            if creat_score < 70:
                issues.append('创造性需要加强')
            if art26_score < 70:
                issues.append('不符合专利法第26条要求')
            
            if issues:
                logger.info(f"\n⚠️  主要问题: {', '.join(issues)}")
            
        else:
            logger.info(f"\n❌ 文件加载失败: {patent_file.name}")

if __name__ == '__main__':
    analyze_all_patents()
