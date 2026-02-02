#!/usr/bin/env python3
"""
OCR专利PDF解析工具
使用OCR技术解析扫描版专利PDF
"""

import io
import json
import logging
import re
from typing import Dict, List, Optional

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

class OCRPatentParser:
    """OCR专利解析器"""

    def __init__(self):
        # 设置tesseract路径（如果需要）
        # pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'
        pass

    def parse_patent_pdf_ocr(self, pdf_path: str, max_pages: int = 5) -> Dict:
        """
        使用OCR解析专利PDF
        Args:
            pdf_path: PDF文件路径
            max_pages: 最大解析页数
        Returns:
            Dict: 解析结果
        """
        try:
            doc = fitz.open(pdf_path)
            full_text = ''

            # 逐页OCR
            for page_num in range(min(len(doc), max_pages)):
                page = doc[page_num]

                # 转换为图片
                mat = fitz.Matrix(2.0, 2.0)  # 2倍放大
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes('png')
                img = Image.open(io.BytesIO(img_data))

                # OCR识别
                page_text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                full_text += f"\n\n--- 第{page_num+1}页 ---\n\n{page_text}"

                logger.info(f"已解析第{page_num+1}页")

            doc.close()

            # 解析专利信息
            patent_info = self.extract_info_from_text(full_text)

            # 提取权利要求
            claims = self.extract_claims_from_text(full_text)
            patent_info['claims'] = claims

            # 保存OCR文本
            patent_info['ocr_text'] = full_text

            return patent_info

        except Exception as e:
            logging.error(f"OCR解析失败: {e}")
            return {'error': str(e)}

    def extract_info_from_text(self, text: str) -> Dict:
        """从OCR文本中提取专利信息"""
        info = {}

        # 提取专利号
        cn_patent = re.search(r'CN(\d+[A-Z])', text)
        if cn_patent:
            info['patent_number'] = cn_patent.group(1)

        # 提取专利名称（通常在首页上方）
        title_patterns = [
            r'实用新型[：:]?\s*(.+?)(?=\n|$)',
            r'发明名称[：:]?\s*(.+?)(?=\n|$)',
            r'(.{10,30})(?=\n实用新型)',
        ]
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                title = match.group(1).strip()
                if len(title) > 3:
                    info['title'] = title
                    break

        # 提取申请日
        date_match = re.search(r'申请日[：:]?\s*(\d{4}[\.年]\d{1,2}[\.月]\d{1,2}[日]?)', text)
        if date_match:
            info['application_date'] = date_match.group(1)

        return info

    def extract_claims_from_text(self, text: str) -> List[Dict]:
        """从OCR文本中提取权利要求"""
        claims = []

        # 查找权利要求部分
        # 权利要求通常从"权利要求书"或"权利要求"开始
        claims_start = re.search(r'权\s*利\s*要\s*求[书]?', text, re.IGNORECASE)

        if not claims_start:
            # 尝试其他模式
            claims_start = re.search(r'权\s*利\s*要\s*求\s*\d+', text, re.IGNORECASE)

        if claims_start:
            # 截取权利要求部分
            claims_text = text[claims_start.start():]

            # 查找每个权利要求
            # 权利要求通常以数字开头，如"1. "、"1、"等
            claim_pattern = r'(\d+)\s*[、.]\s*(.*?)(?=\n\s*\d+[、.]|\Z)'
            claim_matches = re.findall(claim_pattern, claims_text, re.DOTALL)

            for claim_num, claim_text in claim_matches:
                # 清理文本
                claim_text = re.sub(r'\s+', ' ', claim_text.strip())

                # 跳过过短的内容
                if len(claim_text) < 10:
                    continue

                claim = {
                    'number': int(claim_num),
                    'text': claim_text,
                    'features': self.extract_features(claim_text)
                }

                claims.append(claim)

        # 如果没找到，尝试简单分割
        if not claims:
            # 查找带编号的段落
            numbered_text = re.findall(r'\n\s*(\d+)\s*[、.]\s*([^\n]+)', text)
            for num, txt in numbered_text:
                if len(txt) > 20 and any(k in txt for k in ['包括', '其特征在于', '所述的', '通过', '利用']):
                    claims.append({
                        'number': int(num),
                        'text': txt.strip(),
                        'features': self.extract_features(txt)
                    })

        return claims

    def extract_features(self, claim_text: str) -> List[str]:
        """从权利要求中提取技术特征"""
        features = []

        # 技术特征关键词
        feature_keywords = [
            '包括', '包含', '设有', '设置', '安装', '配置',
            '其特征在于', '其中', '所述的', '通过', '利用',
            '连接', '固定', '支撑', '驱动', '控制', '实现'
        ]

        # 分句并提取包含特征关键词的句子
        sentences = re.split(r'[，。；；\n]', claim_text)
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence for keyword in feature_keywords) and len(sentence) > 5:
                features.append(sentence)

        return features[:8]  # 最多返回8个特征

    def save_result(self, data: Dict, output_path: str) -> None:
        """保存解析结果"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# 执行OCR解析
if __name__ == '__main__':
    parser = OCRPatentParser()

    pdf_path = '/Users/xujian/Athena工作平台/patent-platform/workspace/data/raw/disclosures/CN201815134U.pdf'
    output_path = '/tmp/patent_claims.json'

    logger.info(f"\n🔍 开始OCR解析专利: {pdf_path}")
    result = parser.parse_patent_pdf_ocr(pdf_path)

    if 'error' not in result:
        logger.info(f"\n✅ OCR解析成功!")
        logger.info(f"专利号: {result.get('patent_number', '未找到')}")
        logger.info(f"专利名称: {result.get('title', '未找到')}")
        logger.info(f"申请日: {result.get('application_date', '未找到')}")

        claims = result.get('claims', [])
        logger.info(f"\n📋 找到权利要求数量: {len(claims)}")

        # 显示权利要求1和2
        for claim in claims:
            if claim['number'] in [1, 2]:
                logger.info(f"\n{'='*60}")
                logger.info(f"权利要求{claim['number']}:")
                logger.info(f"{'='*60}")
                logger.info(f"\n{claim['text']}\n")

                logger.info(f"\n技术特征 ({len(claim['features'])}个):")
                for i, feature in enumerate(claim['features'], 1):
                    logger.info(f"  {i}. {feature}")

        # 保存解析结果
        parser.save_result(result, output_path)
        logger.info(f"\n💾 解析结果已保存至: {output_path}")

    else:
        logger.info(f"\n❌ OCR解析失败: {result['error']}")