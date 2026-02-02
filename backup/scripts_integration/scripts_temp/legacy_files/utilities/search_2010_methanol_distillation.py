#!/usr/bin/env python3
"""
在2010年专利数据中检索甲醇精馏相关技术
用于专利CN201815134U的现有技术分析
"""

import json
import logging
import time
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

# API配置
API_URL = 'http://localhost:8030'

def search_patents(keyword, limit=20, start_date=None, end_date=None):
    """搜索专利"""
    url = f"{API_URL}/api/v2/patents/search"

    params = {
        'keyword': keyword,
        'limit': limit,
        'offset': 0
    }

    # 添加日期过滤
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('patents', [])
        else:
            logger.info(f"搜索失败: {response.status_code}")
            return []
    except Exception as e:
        logger.info(f"搜索错误: {e}")
        return []

def analyze_patent_for_prior_art(patent_data):
    """分析专利是否构成现有技术"""
    analysis = {
        '相关性': '',
        '技术特征': '',
        '公开时间': '',
        '影响评估': ''
    }

    # 基本信息提取
    app_date = patent_data.get('application_date', '')
    pub_date = patent_data.get('publication_date', '')
    title = patent_data.get('patent_name', '')
    abstract = patent_data.get('abstract', '')
    ipc = patent_data.get('ipc_code', '')

    # 时间判断（目标专利申请日：2010-09-17）
    is_prior_art = False
    if app_date and app_date < '2010-09-17':
        is_prior_art = True
    elif pub_date and pub_date < '2010-09-17':
        is_prior_art = True

    if is_prior_art:
        analysis['公开时间'] = f"申请日: {app_date}, 公开日: {pub_date}"
        analysis['影响评估'] = '✅ 构成现有技术'
    else:
        analysis['公开时间'] = f"申请日: {app_date}, 公开日: {pub_date}"
        analysis['影响评估'] = '⚠️ 不构成现有技术（时间晚于目标专利）'

    # 技术特征分析
    tech_features = []
    if '精馏' in title or '精馏' in abstract:
        tech_features.append('涉及精馏技术')
    if '甲醇' in title or '甲醇' in abstract:
        tech_features.append('涉及甲醇处理')
    if '气相' in title or '气相' in abstract:
        tech_features.append('涉及气相工艺')
    if '直接' in title or '直接' in abstract:
        tech_features.append('涉及直接工艺')
    if '酯化' in title or '酯化' in abstract:
        tech_features.append('涉及酯化反应')

    analysis['技术特征'] = '; '.join(tech_features) if tech_features else '无明显相关技术特征'

    # 相关性评估
    relevance_score = 0
    if '混二元酸' in title or 'DBE' in title:
        relevance_score += 5
    if '二甲酯' in title:
        relevance_score += 4
    if '甲醇' in title:
        relevance_score += 3
    if '精馏' in title:
        relevance_score += 3
    if '气相' in title:
        relevance_score += 2

    if relevance_score >= 7:
        analysis['相关性'] = '高度相关'
    elif relevance_score >= 4:
        analysis['相关性'] = '中等相关'
    elif relevance_score >= 2:
        analysis['相关性'] = '低度相关'
    else:
        analysis['相关性'] = '可能不相关'

    return analysis

def search_2010_methanol_distillation():
    """搜索2010年甲醇精馏相关专利"""
    logger.info(str('=' * 60))
    logger.info('2010年甲醇精馏技术现有技术检索报告')
    logger.info(str('=' * 60))
    logger.info(f"检索时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"目标专利: CN201815134U（申请日：2010-09-17）")
    logger.info(str('-' * 60))

    # 检索关键词组合
    search_keywords = [
        '甲醇 精馏',
        '甲醇 精馏 气相',
        '酯化 甲醇 精馏',
        '二甲酯 甲醇 精馏',
        '混二元酸 精馏',
        'DBE 精馏'
    ]

    all_results = []

    for keyword in search_keywords:
        logger.info(f"\n🔍 检索关键词: '{keyword}'")
        logger.info(str('-' * 40))

        # 检索2010年1月1日至2010年9月17日的专利
        results = search_patents(
            keyword=keyword,
            limit=50,
            start_date='2010-01-01',
            end_date='2010-09-17'
        )

        logger.info(f"找到 {len(results)} 条结果")

        for i, patent in enumerate(results[:5], 1):  # 只显示前5条
            logger.info(f"\n{i}. 专利名称: {patent.get('patent_name', 'N/A')}")
            logger.info(f"   申请号: {patent.get('application_number', 'N/A')}")
            logger.info(f"   申请日: {patent.get('application_date', 'N/A')}")
            logger.info(f"   申请人: {patent.get('applicant', 'N/A')}")
            logger.info(f"   IPC分类: {patent.get('ipc_code', 'N/A')[:50]}...")

            # 分析是否构成现有技术
            analysis = analyze_patent_for_prior_art(patent)
            logger.info(f"   相关性: {analysis['相关性']}")
            logger.info(f"   技术特征: {analysis['技术特征']}")
            logger.info(f"   影响评估: {analysis['影响评估']}")

        all_results.extend(results)
        time.sleep(1)  # 避免请求过快

    # 去重并统计
    unique_patents = {}
    for patent in all_results:
        app_num = patent.get('application_number')
        if app_num and app_num not in unique_patents:
            unique_patents[app_num] = patent

    logger.info(str("\n" + '=' * 60))
    logger.info('检索统计')
    logger.info(str('=' * 60))
    logger.info(f"总检索结果（含重复）: {len(all_results)} 条")
    logger.info(f"去重后专利数量: {len(unique_patents)} 条")

    # 统计构成现有技术的专利
    prior_art_count = 0
    highly_relevant = []

    for patent in unique_patents.values():
        analysis = analyze_patent_for_prior_art(patent)
        if '构成现有技术' in analysis['影响评估']:
            prior_art_count += 1
            if analysis['相关性'] == '高度相关':
                highly_relevant.append(patent)

    logger.info(f"构成现有技术的专利: {prior_art_count} 条")
    logger.info(f"高度相关的现有技术: {len(highly_relevant)} 条")

    # 输出高度相关的专利详情
    if highly_relevant:
        logger.info(str("\n" + '=' * 60))
        logger.info('高度相关的现有技术详情')
        logger.info(str('=' * 60))

        for i, patent in enumerate(highly_relevant, 1):
            logger.info(f"\n{i}. 【高度相关】{patent.get('patent_name', 'N/A')}")
            logger.info(f"   申请号: {patent.get('application_number', 'N/A')}")
            logger.info(f"   申请日: {patent.get('application_date', 'N/A')}")
            logger.info(f"   申请人: {patent.get('applicant', 'N/A')}")
            logger.info(f"   摘要: {patent.get('abstract', 'N/A')[:200]}...")

    # 结论
    logger.info(str("\n" + '=' * 60))
    logger.info('初步结论')
    logger.info(str('=' * 60))

    if prior_art_count == 0:
        logger.info('⚠️ 未检索到2010年1月1日至2010年9月17日期间的相关现有技术')
        logger.info('建议：')
        logger.info('1. 扩大检索范围，包括2009年及之前的专利')
        logger.info('2. 检索国际专利数据库（US、EP、JP等）')
        logger.info('3. 检索非专利文献')
    else:
        logger.info(f"✅ 检索到 {prior_art_count} 条可能构成现有技术的专利")
        logger.info(f"其中 {len(highly_relevant)} 条为高度相关")
        logger.info('建议进一步详细分析这些专利对CN201815134U新颖性和创造性的影响')

def main():
    """主函数"""
    # 等待API服务就绪
    logger.info('检查API服务状态...')
    try:
        response = requests.get(f"{API_URL}/api/v2/health", timeout=5)
        if response.status_code == 200:
            logger.info('✅ API服务正常运行')
        else:
            logger.info('⚠️ API服务可能未完全就绪')
    except:
        logger.info('❌ 无法连接到API服务，请确保专利搜索服务正在运行')
        return

    # 执行检索
    search_2010_methanol_distillation()

if __name__ == '__main__':
    main()