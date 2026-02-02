#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用OCR提取专利信息
Extract Patent Information with OCR
"""

import io
import logging
import re
from typing import Dict, List

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

def extract_patent_with_ocr(pdf_path: str, max_pages: int = 10) -> Dict:
    """使用OCR从PDF中提取专利信息"""
    logger.info(f"正在解析PDF: {pdf_path}")
    logger.info(f"最多处理 {max_pages} 页...")

    doc = fitz.open(pdf_path)
    full_text = ''

    # 获取页数
    total_pages = doc.page_count
    pages_to_process = min(total_pages, max_pages)

    # 逐页OCR
    for page_num in range(pages_to_process):
        logger.info(f"正在处理第 {page_num + 1} 页...")

        page = doc[page_num]

        # 转换为图片
        mat = fitz.Matrix(2.0, 2.0)  # 2倍放大
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes('png')
        img = Image.open(io.BytesIO(img_data))

        # OCR识别（支持中英文）
        page_text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        full_text += f"\n\n=== 第{page_num + 1}页 ===\n\n{page_text}"

        logger.info(f"第 {page_num + 1} 页OCR完成")

    # 关闭文档
    doc.close()

    # 解析提取的文本
    patent_info = {
        'file_name': pdf_path,
        'pages_processed': pages_to_process,
        'total_pages': total_pages,
        'full_text': full_text,
        'ocr_text': full_text
    }

    # 提取专利号
    patent_num = re.search(r'CN(\d{9}\.\d)', full_text)
    if patent_num:
        patent_info['patent_number'] = f"CN{patent_num.group(1)}"
        logger.info(f"找到专利号: {patent_info['patent_number']}")

    # 提取申请号
    app_num = re.search(r'申请号[：:]?\s*(\d{9,}\.\d)', full_text)
    if app_num:
        patent_info['application_number'] = app_num.group(1)
        logger.info(f"找到申请号: {patent_info['application_number']}")

    # 提取申请日
    app_date = re.search(r'申请日[：:]?\s*(\d{4}[\.年]\d{1,2}[\.月]\d{1,2}[日]?)', full_text)
    if app_date:
        patent_info['application_date'] = app_date.group(1)
        logger.info(f"找到申请日: {patent_info['application_date']}")

    # 提取专利名称
    title_patterns = [
        r'实用新型名称[：:]?\s*(.+?)(?=\n|$)',
        r'发明名称[：:]?\s*(.+?)(?=\n|$)',
        r'名称[：:]?\s*(.+?)(?=\n|$)',
        r'(.{10,50})(?=\n实用新型)',
        r'(.{10,50})(?=\n发明创造)',
        r'(.{10,50})(?=\n权利要求)'
    ]
    for pattern in title_patterns:
        match = re.search(pattern, full_text)
        if match:
            patent_info['title'] = match.group(1).strip()
            logger.info(f"找到专利名称: {patent_info['title']}")
            break

    # 提取权利要求
    claims_start = full_text.find('权利要求书')
    if claims_start != -1:
        claims_section = full_text[claims_start:claims_start+2000]
        patent_info['claims_section'] = claims_section

        # 提取各个权利要求
        claims = extract_claims(claims_section)
        patent_info['claims'] = claims
        logger.info(f"找到 {len(claims)} 个权利要求")

    # 提取技术领域
    field_match = re.search(r'技术领域[：:]?\s*(.+?)(?=\n|$)', full_text)
    if field_match:
        patent_info['technical_field'] = field_match.group(1).strip()
        logger.info(f"找到技术领域: {patent_info['technical_field']}")

    # 提取背景技术
    background_start = full_text.find('背景技术')
    if background_start != -1:
        background_end = full_text.find('发明内容', background_start)
        if background_end != -1:
            background_section = full_text[background_start:background_end]
            patent_info['background_art'] = background_section[:500] + '...' if len(background_section) > 500 else background_section

    # 提取发明内容
    invention_start = full_text.find('发明内容')
    if invention_start != -1:
        invention_end = full_text.find('有益效果', invention_start)
        if invention_end != -1:
            invention_section = full_text[invention_start:invention_end]
            patent_info['invention_content'] = invention_section[:500] + '...' if len(invention_section) > 500 else invention_section

    # 提取有益效果
    effects_patterns = [
        r'有益效果[：:]?\s*(.+?)(?=\n|$)',
        r'有益效果是[：:]?\s*(.+?)(?=\n|$)',
        r'本实用新型的有益效果[：:]?\s*(.+?)(?=\n|$)'
    ]
    for pattern in effects_patterns:
        match = re.search(pattern, full_text)
        if match:
            patent_info['beneficial_effects'] = match.group(1).strip()
            logger.info(f"找到有益效果: {patent_info['beneficial_effects'][:50]}...")
            break

    # 保存OCR文本
    with open(f"patent_ocr_text.txt', 'w', encoding='utf-8") as f:
        f.write(full_text)
    logger.info(f"\nOCR文本已保存到 patent_ocr_text.txt")

    return patent_info

def extract_claims(claims_section: str) -> List[Dict]:
    """提取权利要求"""
    claims = []

    # 查找所有权利要求
    claim_pattern = r'(\d+\.[^。]*。[^。]*)'
    matches = re.findall(claim_pattern, claims_section)

    for match in matches:
        claim_text = match.strip()

        # 提取权利要求编号
        claim_num_match = re.match(r'(\d+)\.', claim_text)
        if claim_num_match:
            claim_num = int(claim_num_match.group(1))

            # 判断是否为独立权利要求
            is_independent = claim_num == 1 or not re.search(r'根据权利要求\d', claim_text)

            claims.append({
                'claim_number': claim_num,
                'text': claim_text,
                'is_independent': is_independent
            })

    return claims

if __name__ == '__main__':
    # 设置tesseract路径（如果需要）
    # pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

    pdf_path = '/Users/xujian/Athena工作平台/tests/04CN200920113915-拉紧器-实用新型.pdf'

    try:
        patent_info = extract_patent_with_ocr(pdf_path, max_pages=5)

        logger.info(str("\n" + '='*60))
        logger.info('专利基本信息:')
        logger.info(str('='*60))
        logger.info(f"专利名称: {patent_info.get('title', '未知')}")
        logger.info(f"专利号: {patent_info.get('patent_number', '未知')}")
        logger.info(f"申请号: {patent_info.get('application_number', '未知')}")
        logger.info(f"申请日: {patent_info.get('application_date', '未知')}")

        logger.info("\n技术领域:")
        logger.info(str('='*60))
        print(patent_info.get('technical_field', '未找到'))

        logger.info("\n有益效果:")
        logger.info(str('='*60))
        print(patent_info.get('beneficial_effects', '未找到'))

        logger.info("\n权利要求:")
        logger.info(str('='*60))
        claims = patent_info.get('claims', [])
        if claims:
            for claim in claims:
                claim_type = '独立权利要求' if claim['is_independent'] else '从属权利要求'
                logger.info(f"\n{claim_type} {claim['claim_number']}:")
                logger.info(str(claim['text']))
        else:
            logger.info('未找到权利要求')

    except Exception as e:
        logger.info(f"处理失败: {str(e)}")
        import traceback
        traceback.print_exc()