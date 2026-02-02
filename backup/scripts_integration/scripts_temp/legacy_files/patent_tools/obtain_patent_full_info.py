#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取目标专利的Google Patents全文信息
Obtain Full Patent Information from Google Patents via Meta Tags
"""

import json
import logging
import time
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def get_google_patent_info(publication_number: str) -> Dict | None:
    """通过Google Patents API获取专利全文信息"""

    # 构建Google Patents URL
    google_patents_url = f"https://patents.google.com/patent/{publication_number}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        logger.info(f"🔍 正在获取专利 {publication_number} 的详细信息...")

        # 发送请求
        response = requests.get(google_patents_url, headers=headers, timeout=30)
        response.raise_for_status()

        # 解析HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # 提取专利信息
        patent_info = {
            'publication_number': publication_number,
            'title': '',
            'abstract': '',
            'description': '',
            'claims': [],
            'inventors': [],
            'assignee': '',
            'application_date': '',
            'publication_date': '',
            'ipc_classifications': [],
            'citations': [],
            'cited_by': []
        }

        # 提取标题
        title_tag = soup.find('span', {'itemprop': 'title'})
        if title_tag:
            patent_info['title'] = title_tag.get_text().strip()

        # 提取摘要
        abstract_tag = soup.find('div', {'class': 'abstract'})
        if abstract_tag:
            patent_info['abstract'] = abstract_tag.get_text().strip().replace("Abstract\n", '')

        # 提取发明人
        inventor_tags = soup.find_all('dd', {'itemprop': 'inventor'})
        for inventor_tag in inventor_tags:
            inventor_name = inventor_tag.get_text().strip()
            if inventor_name:
                patent_info['inventors'].append(inventor_name)

        # 提取受让人
        assignee_tag = soup.find('dd', {'itemprop': 'assignee'})
        if assignee_tag:
            patent_info['assignee'] = assignee_tag.get_text().strip()

        # 提取申请日和公开日
        application_date_tag = soup.find('time', {'itemprop': 'dateFiled'})
        if application_date_tag:
            patent_info['application_date'] = application_date_tag.get_text().strip()

        publication_date_tag = soup.find('time', {'itemprop': 'publicationDate'})
        if publication_date_tag:
            patent_info['publication_date'] = publication_date_tag.get_text().strip()

        # 提取IPC分类
        ipc_tags = soup.find_all('span', {'itemprop': 'classificationCode'})
        for ipc_tag in ipc_tags:
            ipc_code = ipc_tag.get_text().strip()
            if ipc_code:
                patent_info['ipc_classifications'].append(ipc_code)

        # 提取权利要求（更详细的方法）
        claims_section = soup.find('section', {'itemprop': 'claims'})
        if claims_section:
            claims_text = claims_section.get_text()
            # 分割权利要求
            claims = claims_text.split('What is claimed is:')
            if len(claims) > 1:
                claims = claims[1].split("\n")
                for claim in claims:
                    claim = claim.strip()
                    if claim and claim.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '11.', '12.', '13.', '14.', '15.', '16.', '17.', '18.', '19.', '20.')):
                        patent_info['claims'].append(claim)

        # 提取描述
        description_section = soup.find('section', {'itemprop': 'description'})
        if description_section:
            patent_info['description'] = description_section.get_text().strip()[:2000] + '...'

        logger.info(f"✅ 成功获取专利 {publication_number} 的信息")
        return patent_info

    except Exception as e:
        logger.info(f"❌ 获取专利 {publication_number} 信息失败: {str(e)}")
        return None

def get_patents_with_meta_tags() -> List[Dict]:
    """为已检索到的专利获取Google Patents信息"""

    # 读取已检索到的专利
    with open('/Users/xujian/Athena工作平台/real_patents_search_results.json', 'r', encoding='utf-8') as f:
        patents = json.load(f)

    enhanced_patents = []

    for i, patent in enumerate(patents[:5], 1):  # 先处理前5个专利
        logger.info(f"\n{'='*60}")
        logger.info(f"处理第 {i}/5 个专利: {patent['patent_name']}")
        logger.info(f"{'='*60}")

        # 尝试不同的公开号格式
        possible_numbers = [
            patent.get('publication_number'),
            patent.get('application_number'),
            patent.get('patent_name').split(' ')[0] if patent.get('patent_name') else None
        ]

        patent_info = None

        for num in possible_numbers:
            if num and num != 'None' and num != '未知':
                # 格式化专利号
                if num.startswith('CN'):
                    # 移除CN前缀中的点，例如 CN201390190Y -> CN201390190
                    formatted_num = num.replace('CN', '').replace('.', '')
                    publication_number = f"CN{formatted_num}"
                else:
                    publication_number = f"CN{num}"

                patent_info = get_google_patent_info(publication_number)

                if patent_info:
                    break

                # 等待一下避免请求过快
                time.sleep(2)

        if patent_info:
            # 合并原始信息和新信息
            enhanced_patent = {
                'original_info': patent,
                'google_info': patent_info
            }
            enhanced_patents.append(enhanced_patent)
        else:
            logger.info(f"⚠️ 无法获取专利 {patent['patent_name']} 的详细信息")
            enhanced_patents.append({
                'original_info': patent,
                'google_info': None,
                'error': '无法获取Google Patents信息'
            })

        # 等待一下避免请求过快
        time.sleep(3)

    return enhanced_patents

def main():
    """主函数"""
    logger.info('🚀 获取专利全文信息')
    logger.info(str('='*60))

    # 获取增强的专利信息
    enhanced_patents = get_patents_with_meta_tags()

    # 保存结果
    output_file = 'patents_with_full_info.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_patents, f, ensure_ascii=False, indent=2)

    logger.info(f"\n✅ 专利全文信息已保存到 {output_file}")

    # 显示统计信息
    total = len(enhanced_patents)
    success = sum(1 for p in enhanced_patents if p.get('google_info'))
    logger.info(f"📊 处理完成: {total}/{5} 个专利, 成功获取 {success} 个专利的全文信息")

    if success > 0:
        logger.info("\n📋 成功获取的专利预览:")
        for patent in enhanced_patents[:3]:
            if patent.get('google_info'):
                info = patent['google_info']
                logger.info(f"\n  📄 {info.get('title', '未知标题')}")
                logger.info(f"     公开号: {info.get('publication_number', '未知')}")
                logger.info(f"     申请日: {info.get('application_date', '未知')}")
                logger.info(f"     IPC分类: {', '.join(info.get('ipc_classifications', [])[:3])}")
                logger.info(f"     权利要求数: {len(info.get('claims', []))}")

if __name__ == '__main__':
    main()