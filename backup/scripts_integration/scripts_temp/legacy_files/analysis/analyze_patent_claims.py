#!/usr/bin/env python3
"""
分析专利CN201815134U的权利要求1和2的新颖性和创造性
"""

import logging
import os
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 尝试多种方法提取PDF内容
def extract_pdf_content(pdf_path):
    """尝试使用多种方法提取PDF内容"""

    # 方法1: 尝试使用pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = ''
            for page in pdf.pages[:5]:  # 读取前5页
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            if text.strip():
                return text
    except Exception as e:
        logger.info(f"pdfplumber提取失败: {e}")

    # 方法2: 尝试使用PyPDF2
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page_num in range(min(5, len(pdf_reader.pages))):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            if text.strip():
                return text
    except Exception as e:
        logger.info(f"PyPDF2提取失败: {e}")

    # 方法3: 使用OCR
    try:
        import easyocr
        import fitz  # PyMuPDF

        # 将PDF转换为图片
        doc = fitz.open(pdf_path)
        reader = easyocr.Reader(['ch_sim', 'en'])

        text = ''
        for page_num in range(min(3, len(doc))):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img_path = f"/tmp/page_{page_num}.png"
            pix.save(img_path)

            # 使用OCR识别文字
            result = reader.readtext(img_path)
            for (bbox, extracted_text, confidence) in result:
                if confidence > 0.5:
                    text += extracted_text + "\n"

            # 删除临时图片
            os.remove(img_path)

        if text.strip():
            return text
    except Exception as e:
        logger.info(f"OCR提取失败: {e}")

    return None

def parse_claims(text):
    """解析权利要求内容"""
    claims = []

    # 查找权利要求书部分
    claims_section_match = re.search(r'权利要求书.*?(?=说明书|$)', text, re.DOTALL)
    if claims_section_match:
        claims_text = claims_section_match.group(0)
    else:
        # 如果没有找到权利要求书，使用整个文本
        claims_text = text

    # 提取权利要求1和2
    claim1_match = re.search(r'1[\.、]\s*(.*?)(?=2[\.、]|权利要求|$)', claims_text, re.DOTALL)
    claim2_match = re.search(r'2[\.、]\s*(.*?)(?=3[\.、]|权利要求|$)', claims_text, re.DOTALL)

    if claim1_match:
        claims.append(('权利要求1', claim1_match.group(1).strip()))
    if claim2_match:
        claims.append(('权利要求2', claim2_match.group(1).strip()))

    return claims

def extract_patent_info(text):
    """提取专利基本信息"""
    info = {}

    # 提取专利名称
    title_match = re.search(r'实用新型名称[：:]\s*(.*?)(?=\n|$)', text)
    if title_match:
        info['title'] = title_match.group(1).strip()

    # 提取申请人
    applicant_match = re.search(r'申请人[：:]\s*(.*?)(?=\n|$)', text)
    if applicant_match:
        info['applicant'] = applicant_match.group(1).strip()

    # 提取发明人
    inventor_match = re.search(r'发明人[：:]\s*(.*?)(?=\n|$)', text)
    if inventor_match:
        info['inventor'] = inventor_match.group(1).strip()

    # 提要技术领域
    field_match = re.search(r'技术领域.*?(?=\n|$)', text, re.DOTALL)
    if field_match:
        info['technical_field'] = field_match.group(0).strip()

    # 提取技术方案
    solution_match = re.search(r'技术方案.*?(?=有益效果|$)', text, re.DOTALL)
    if solution_match:
        info['technical_solution'] = solution_match.group(0).strip()

    return info

def analyze_novelty_creativity(claims, patent_info):
    """分析权利要求的新颖性和创造性"""
    analysis = {
        '权利要求1': {'新颖性': '', '创造性': ''},
        '权利要求2': {'新颖性': '', '创造性': ''}
    }

    for claim_num, claim_text in claims:
        # 基于权利要求内容进行初步分析
        logger.info(f"\n=== {claim_num}分析 ===")
        logger.info(f"内容: {claim_text[:200]}...")

        # 新颖性分析要点
        novelty_points = [
            '1. 检索现有技术，查看是否存在完全相同的技术方案',
            '2. 对比技术特征，确定是否存在区别',
            '3. 分析这些区别是否属于本领域的常规技术手段'
        ]

        # 创造性分析要点
        creativity_points = [
            '1. 确定最接近的现有技术',
            '2. 分析区别技术特征',
            '3. 判断这些区别是否具有实质性特点',
            '4. 评估是否能够带来有益效果'
        ]

        # 存储分析结果
        analysis[claim_num]['新颖性'] = "\n".join(novelty_points)
        analysis[claim_num]['创造性'] = "\n".join(creativity_points)

    return analysis

def main():
    pdf_path = '/Users/xujian/Athena工作平台/patent-platform/workspace/data/raw/disclosures/CN201815134U.pdf'

    if not os.path.exists(pdf_path):
        logger.info(f"文件不存在: {pdf_path}")
        return

    logger.info('正在提取PDF内容...')
    text = extract_pdf_content(pdf_path)

    if not text:
        logger.info('无法提取PDF内容')
        return

    logger.info('提取专利基本信息...')
    patent_info = extract_patent_info(text)

    logger.info("\n=== 专利基本信息 ===")
    for key, value in patent_info.items():
        logger.info(f"{key}: {value}")

    logger.info("\n解析权利要求...")
    claims = parse_claims(text)

    if not claims:
        logger.info('未找到权利要求1和2')
        return

    logger.info("\n=== 权利要求内容 ===")
    for claim_num, claim_text in claims:
        logger.info(f"\n{claim_num}:")
        logger.info(str(claim_text))

    logger.info("\n分析新颖性和创造性...")
    analysis = analyze_novelty_creativity(claims, patent_info)

    # 生成分析报告
    report = f"""
专利分析报告 - CN201815134U

一、专利基本信息
专利名称: {patent_info.get('title', '未知')}
申请人: {patent_info.get('applicant', '未知')}
发明人: {patent_info.get('inventor', '未知')}

二、权利要求分析

"""

    for claim_num, claim_text in claims:
        report += f"""
{claim_num}:

权利要求内容:
{claim_text}

新颖性分析:
{analysis[claim_num]['新颖性']}

创造性分析:
{analysis[claim_num]['创造性']}

"""

    # 保存报告
    report_path = '/Users/xujian/Athena工作平台/patent_analysis_CN201815134U.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"\n分析报告已保存到: {report_path}")

if __name__ == '__main__':
    main()