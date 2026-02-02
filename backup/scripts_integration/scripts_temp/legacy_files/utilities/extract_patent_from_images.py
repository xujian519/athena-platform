#!/usr/bin/env python3
"""
从转换后的图片中提取专利信息
"""

import logging
import os
import re

import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

def extract_text_from_image(image_path):
    """使用OCR从图片中提取文字"""
    try:
        # 设置中文识别
        text = pytesseract.image_to_string(
            Image.open(image_path),
            lang='chi_sim+eng',
            config='--psm 6 --oem 1'
        )
        return text
    except Exception as e:
        logger.info(f"OCR提取失败: {e}")
        return None

def parse_patent_info(text):
    """解析专利信息"""
    info = {}

    # 提取专利名称
    title_patterns = [
        r'实用新型名称[：:]\s*(.*?)(?=\n|$)',
        r'发明名称[：:]\s*(.*?)(?=\n|$)',
        r'名称[：:]\s*(.*?)(?=\n|$)'
    ]
    for pattern in title_patterns:
        match = re.search(pattern, text)
        if match:
            info['title'] = match.group(1).strip()
            break

    # 提取专利号
    patent_num_match = re.search(r'CN(\d+U)', text)
    if patent_num_match:
        info['patent_number'] = 'CN' + patent_num_match.group(1)

    # 提取申请人
    applicant_match = re.search(r'申请人[：:]\s*(.*?)(?=\n|地址|$)', text)
    if applicant_match:
        info['applicant'] = applicant_match.group(1).strip()

    # 提取发明人
    inventor_match = re.search(r'发明人[：:]\s*(.*?)(?=\n|$)', text)
    if inventor_match:
        info['inventor'] = inventor_match.group(1).strip()

    # 提取申请日
    date_match = re.search(r'申请日[：:]\s*(\d{4}\.\d{2}\.\d{2})', text)
    if date_match:
        info['application_date'] = date_match.group(1)

    # 提取摘要
    abstract_match = re.search(r'摘要[：:]\s*(.*?)(?=\n\n|权利要求书|$)', text, re.DOTALL)
    if abstract_match:
        info['abstract'] = abstract_match.group(1).strip()

    # 提取权利要求书
    claims_match = re.search(r'权利要求书[：:]?\s*(.*?)(?=说明书|$)', text, re.DOTALL)
    if claims_match:
        claims_text = claims_match.group(1)
        info['claims_text'] = claims_text.strip()

        # 提取权利要求1
        claim1_match = re.search(r'1[\.、]\s*(.*?)(?=2[\.、]|$)', claims_text, re.DOTALL)
        if claim1_match:
            info['claim_1'] = claim1_match.group(1).strip()

        # 提取权利要求2
        claim2_match = re.search(r'2[\.、]\s*(.*?)(?=3[\.、]|$)', claims_text, re.DOTALL)
        if claim2_match:
            info['claim_2'] = claim2_match.group(1).strip()

    return info

def main():
    image_dir = '/tmp/patent_pages'

    # 安装pytesseract（如果未安装）
    try:
        import pytesseract
    except ImportError:
        logger.info('正在安装pytesseract...')
        os.system('pip install pytesseract')
        import pytesseract

    # 处理每一页图片
    all_text = ''
    for i in range(1, 4):  # 处理前3页
        image_path = os.path.join(image_dir, f'page_{i}.png')
        if os.path.exists(image_path):
            logger.info(f"正在处理第{i}页...")
            text = extract_text_from_image(image_path)
            if text:
                all_text += f"\n=== 第{i}页 ===\n"
                all_text += text + "\n"

    # 保存提取的文本
    with open('/tmp/patent_extracted_text.txt', 'w', encoding='utf-8') as f:
        f.write(all_text)
    logger.info('提取的文本已保存到 /tmp/patent_extracted_text.txt')

    # 解析专利信息
    patent_info = parse_patent_info(all_text)

    # 打印关键信息
    logger.info("\n=== 专利信息提取结果 ===")
    logger.info(f"专利名称: {patent_info.get('title', '未提取到')}")
    logger.info(f"专利号: {patent_info.get('patent_number', '未提取到')}")
    logger.info(f"申请日: {patent_info.get('application_date', '未提取到')}")
    logger.info(f"申请人: {patent_info.get('applicant', '未提取到')}")
    logger.info(f"发明人: {patent_info.get('inventor', '未提取到')}")

    logger.info("\n=== 摘要 ===")
    print(patent_info.get('abstract', '未提取到')[:500] + '...' if patent_info.get('abstract') else '未提取到')

    logger.info("\n=== 权利要求1 ===")
    print(patent_info.get('claim_1', '未提取到'))

    logger.info("\n=== 权利要求2 ===")
    print(patent_info.get('claim_2', '未提取到'))

    return patent_info

if __name__ == '__main__':
    main()