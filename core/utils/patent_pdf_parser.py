#!/usr/bin/env python3
from __future__ import annotations
"""
专利PDF解析工具
用于从专利PDF文件中提取权利要求
"""

import json
import logging
import re

import pdfplumber

logger = logging.getLogger(__name__)

class PatentPDFParser:
    """专利PDF解析器"""

    def __init__(self):
        self.claim_patterns = [
            r'权\s*利\s*要\s*求[：:]?\s*(.*?)(?=\n\s*\d+[、,.]',
            r'权\s*利\s*要\s*求\s*(\d+)[、.]\s*(.*?)(?=\n\s*\d+[、,.]|$)',
            r'(\d+)\s*[、.]\s*([^.\n]*(?:\.[^.\n]*)*)',
        ]

    def parse_patent_pdf(self, pdf_path: str) -> dict:
        """
        解析专利PDF文件
        Args:
            pdf_path: PDF文件路径
        Returns:
            Dict: 包含专利信息的字典
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 提取所有文本
                full_text = ''
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += "\n" + text

                # 解析专利信息
                patent_info = self.extract_patent_info(full_text)

                # 提取权利要求
                claims = self.extract_claims(full_text)
                patent_info['claims'] = claims

                # 提取技术领域
                patent_info['technical_field'] = self.extract_technical_field(full_text)

                # 提取背景技术
                patent_info['background'] = self.extract_background(full_text)

                # 提取发明内容
                patent_info['summary'] = self.extract_summary(full_text)

                return patent_info

        except Exception as e:
            logging.error(f"解析PDF失败 {pdf_path}: {e}")
            return {'error': str(e)}

    def extract_patent_info(self, text: str) -> dict:
        """提取专利基本信息"""
        info = {}

        # 提取专利号
        patent_no_patterns = [
            r'CN(\d+[A-Z])',
            r'专\s*利\s*号[：:]?\s*(CN\d+[A-Z])',
            r'申\s*请\s*号[：:]?\s*(\d{13,})',
        ]
        for pattern in patent_no_patterns:
            match = re.search(pattern, text)
            if match:
                info['patent_number'] = match.group(1)
                break

        # 提取专利名称
        title_patterns = [
            r'发\s*明\s*名\s*称[：:]?\s*(.*?)(?=\n|$)',
            r'实\s*用\s*新\s*型\s*名\s*称[：:]?\s*(.*?)(?=\n|$)',
            r'专\s*利\s*名\s*称[：:]?\s*(.*?)(?=\n|$)',
        ]
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                info['title'] = match.group(1).strip()
                break

        # 提取申请日
        date_patterns = [
            r'申\s*请\s*日[：:]?\s*(\d{4}[\.年]\d{1,2}[\.月]\d{1,2}[日]?)',
            r'公\s*开\s*日[：:]?\s*(\d{4}[\.年]\d{1,2}[\.月]\d{1,2}[日]?)',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                info['application_date'] = match.group(1)
                break

        return info

    def extract_claims(self, text: str) -> list[dict]:
        """提取权利要求"""
        claims = []

        # 查找权利要求部分
        claims_section_pattern = r'权\s*利\s*要\s*求[：:]?\s*\n(.*?)(?=\n\s*说\s*明\s*书|\n\s*附\s*图|\Z)'
        claims_match = re.search(claims_section_pattern, text, re.DOTALL | re.IGNORECASE)

        if not claims_match:
            return []

        claims_text = claims_match.group(1)

        # 分割各个权利要求
        claim_pattern = r'(\d+)\s*[、.]\s*(.*?)(?=\n\s*\d+[、.]|\n\s*$|$)'
        claim_matches = re.findall(claim_pattern, claims_text, re.DOTALL)

        for claim_num, claim_text in claim_matches:
            # 清理文本
            claim_text = claim_text.strip()

            # 分句
            sentences = re.split(r'[；;。]\s*', claim_text)
            sentences = [s.strip() for s in sentences if s.strip()]

            claim = {
                'number': int(claim_num),
                'text': claim_text,
                'sentences': sentences,
                'features': self.extract_features_from_text(claim_text)
            }

            claims.append(claim)

        return claims

    def extract_features_from_text(self, text: str) -> list[str]:
        """从权利要求文本中提取技术特征"""
        features = []

        # 技术特征模式
        feature_patterns = [
            r'包括\s*[:：]?\s*([^，。；；\n]+)',  # 包括的特征
            r'其特征在于\s*[:：]?\s*([^，。；；\n]+)',  # 其特征在于
            r'所述\s*的\s*([^，。；；\n]+)',  # 所述的特征
            r'通过\s*([^，。；；\n]+)',  # 通过的特征
            r'利用\s*([^，。；；\n]+)',  # 利用的方法
        ]

        for pattern in feature_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                feature = match.strip()
                if len(feature) > 2 and feature not in features:
                    features.append(feature)

        return features[:10]  # 最多返回10个特征

    def extract_technical_field(self, text: str) -> str:
        """提取技术领域"""
        field_patterns = [
            r'技\s*术\s*领\s*域[：:]?\s*(.*?)(?=\n\n|\n[一二三四五六七八九十]|$)',
            r'所\s*属\s*技\s*术\s*领\s*域[：:]?\s*(.*?)(?=\n\n|\n[一二三四五六七八九十]|$)',
        ]
        for pattern in field_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()[:200]  # 限制长度
        return ''

    def extract_background(self, text: str) -> str:
        """提取背景技术"""
        bg_patterns = [
            r'背\s*景\s*技\s*术[：:]?\s*(.*?)(?=\n\n\s*发\s*明|\n\s*[一二三四五六七八九十]、|$)',
        ]
        for pattern in bg_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()[:500]  # 限制长度
        return ''

    def extract_summary(self, text: str) -> str:
        """提取发明内容"""
        summary_patterns = [
            r'发\s*明\s*内\s*容[：:]?\s*(.*?)(?=\n\n\s*附\s*图|\n\s*[一二三四五六七八九十]、|$)',
        ]
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()[:500]  # 限制长度
        return ''

    def save_parsed_data(self, data: dict, output_path: str) -> None:
        """保存解析结果"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# 测试解析器
if __name__ == '__main__':
    parser = PatentPDFParser()

    # 解析测试专利
    pdf_path = '/Users/xujian/Athena工作平台/patent-platform/workspace/data/raw/disclosures/CN201815134U.pdf'

    logger.info(f"\n📄 开始解析专利PDF: {pdf_path}")
    result = parser.parse_patent_pdf(pdf_path)

    if 'error' not in result:
        logger.info("\n✅ 解析成功!")
        logger.info(f"专利号: {result.get('patent_number', '未找到')}")
        logger.info(f"专利名称: {result.get('title', '未找到')}")
        logger.info(f"申请日: {result.get('application_date', '未找到')}")

        logger.info(f"\n📋 权利要求数量: {len(result.get('claims', []))}")

        # 显示前两个权利要求
        claims = result.get('claims', [])
        for i, claim in enumerate(claims[:2], 1):
            logger.info(f"\n权利要求{i}:")
            logger.info(f"文本: {claim['text'][:200]}...")
            logger.info(f"特征数量: {len(claim['features'])}")
            for j, feature in enumerate(claim['features'][:5], 1):
                logger.info(f"  特征{j}: {feature}")
    else:
        logger.info(f"❌ 解析失败: {result['error']}")
