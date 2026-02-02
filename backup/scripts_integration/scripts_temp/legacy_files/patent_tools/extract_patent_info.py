#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利信息提取工具
Extract Patent Information
"""

import logging
import re
from typing import Dict, List

import fitz

logger = logging.getLogger(__name__)

def extract_patent_info(pdf_path: str) -> Dict:
    """从PDF中提取专利信息"""
    doc = fitz.open(pdf_path)

    # 提取全部文本
    full_text = ''
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        full_text += text + "\n"

    # 基本信息
    patent_info = {
        'file_name': pdf_path,
        'pages': len(doc),
        'full_text': full_text
    }

    # 提取专利号
    patent_num = re.search(r'CN(\d+\.\d[A-Z]?)', full_text)
    if patent_num:
        patent_info['patent_number'] = f"CN{patent_num.group(1)}"

    # 提取申请号
    app_num = re.search(r'申请号[：:]?\s*(\d{9,}\.\d)', full_text)
    if app_num:
        patent_info['application_number'] = app_num.group(1)

    # 提取申请日
    app_date = re.search(r'申请日[：:]?\s*(\d{4}[\.年]\d{1,2}[\.月]\d{1,2}[日]?)', full_text)
    if app_date:
        patent_info['application_date'] = app_date.group(1)

    # 提取专利名称
    title_patterns = [
        r'实用新型名称[：:]?\s*(.+?)(?=\n|$)',
        r'发明名称[：:]?\s*(.+?)(?=\n|$)',
        r'名称[：:]?\s*(.+?)(?=\n|$)'
    ]
    for pattern in title_patterns:
        match = re.search(pattern, full_text)
        if match:
            patent_info['title'] = match.group(1).strip()
            break

    # 提取权利要求书
    claims_start = full_text.find('权利要求书')
    specification_end = full_text.find('说明书')

    if claims_start != -1:
        claims_end = full_text.find('说明书', claims_start) if claims_start < specification_end else -1
        if claims_end == -1:
            claims_section = full_text[claims_start:]
        else:
            claims_section = full_text[claims_start:claims_end]
        patent_info['claims_section'] = claims_section

        # 提取各个权利要求
        claims = extract_claims(claims_section)
        patent_info['claims'] = claims

    # 提取说明书部分
    if specification_end != -1:
        patent_info['specification'] = full_text[specification_end:]

    # 提取技术领域
    field_match = re.search(r'技术领域[：:]?\s*(.+?)(?=\n|$)', full_text)
    if field_match:
        patent_info['technical_field'] = field_match.group(1).strip()

    # 提取背景技术
    background_start = full_text.find('背景技术')
    if background_start != -1:
        background_end = full_text.find('发明内容', background_start)
        if background_end != -1:
            background_section = full_text[background_start:background_end]
            patent_info['background_art'] = background_section[:1000] + '...' if len(background_section) > 1000 else background_section

    # 提取发明内容
    invention_start = full_text.find('发明内容')
    if invention_start != -1:
        invention_end = full_text.find('附图说明', invention_start)
        if invention_end != -1:
            invention_section = full_text[invention_start:invention_end]
            patent_info['invention_content'] = invention_section[:1000] + '...' if len(invention_section) > 1000 else invention_section

    # 提取有益效果
    effects_match = re.search(r'有益效果[：:]?\s*(.+?)(?=\n|$)', full_text)
    if effects_match:
        patent_info['beneficial_effects'] = effects_match.group(1).strip()

    doc.close()
    return patent_info

def extract_claims(claims_section: str) -> List[Dict]:
    """提取权利要求"""
    claims = []

    # 查找所有权利要求
    claim_pattern = r'(\d+\..+?)(?=\n\d+\.|\n说明书|$)'
    matches = re.findall(claim_pattern, claims_section, re.DOTALL)

    for match in matches:
        claim_text = match.strip()

        # 提取权利要求编号
        claim_num_match = re.match(r'(\d+)\.', claim_text)
        if claim_num_match:
            claim_num = int(claim_num_match.group(1))

            # 判断是否为独立权利要求
            is_independent = claim_num == 1 or re.search(r'^\d+\.[^（]*$', claim_text)

            claims.append({
                'claim_number': claim_num,
                'text': claim_text,
                'is_independent': is_independent
            })

    return claims

if __name__ == '__main__':
    # 测试提取
    pdf_path = '/Users/xujian/Athena工作平台/tests/04CN200920113915-拉紧器-实用新型.pdf'

    patent_info = extract_patent_info(pdf_path)

    logger.info('专利基本信息:')
    logger.info(str('='*50))
    logger.info(f"专利名称: {patent_info.get('title', '未知')}")
    logger.info(f"专利号: {patent_info.get('patent_number', '未知')}")
    logger.info(f"申请号: {patent_info.get('application_number', '未知')}")
    logger.info(f"申请日: {patent_info.get('application_date', '未知')}")
    print()

    logger.info('技术领域:')
    logger.info(str('='*50))
    print(patent_info.get('technical_field', '未找到'))
    print()

    logger.info('有益效果:')
    logger.info(str('='*50))
    print(patent_info.get('beneficial_effects', '未找到'))
    print()

    logger.info('权利要求:')
    logger.info(str('='*50))
    claims = patent_info.get('claims', [])
    for claim in claims:
        claim_type = '独立权利要求' if claim['is_independent'] else '从属权利要求'
        logger.info(f"\n{claim_type} {claim['claim_number']}:")
        logger.info(str(claim['text'][:200] + '...' if len(claim['text'])) > 200 else claim['text'])