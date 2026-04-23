#!/usr/bin/env python3
"""
合同文档解析工具
Contract Document Parser
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

class ContractParser:
    """合同解析器"""

    def __init__(self, pdf_path: str):
        """初始化

        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = Path(pdf_path)
        self.doc = None
        self.text_content = ''

    def parse(self) -> dict[str, Any]:
        """解析合同文档

        Returns:
            解析结果字典
        """
        try:
            # 打开PDF
            self.doc = fitz.open(self.pdf_path)

            # 提取文本
            self.text_content = ''
            for page in self.doc:
                self.text_content += page.get_text()

            # 解析各部分
            result = {
                'file_info': {
                    'path': str(self.pdf_path),
                    'pages': len(self.doc),
                    'parsed_at': datetime.now().isoformat()
                },
                'contract_info': self._extract_contract_info(),
                'parties': self._extract_parties(),
                'service_content': self._extract_service_content(),
                'terms': self._extract_key_terms(),
                'financial_terms': self._extract_financial_terms(),
                'timeline': self._extract_timeline()
            }

            return result

        except Exception as e:
            return {
                'error': str(e),
                'file_info': {
                    'path': str(self.pdf_path),
                    'parsed_at': datetime.now().isoformat()
                }
            }
        finally:
            if self.doc:
                self.doc.close()

    def _extract_contract_info(self) -> dict[str, Any]:
        """提取合同基本信息"""
        info = {}
        lines = self.text_content.split('\n')

        # 合同标题
        for line in lines:
            if '合同' in line or '协议' in line:
                info['title'] = line.strip()
                break

        # 合同编号
        for line in lines:
            if '合同编号' in line or '协议编号' in line:
                info['contract_number'] = line.split('：')[-1].split(':')[-1].strip()
                break

        # 签订日期
        date_patterns = [
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}-\d{1,2}-\d{1,2})',
            r'(\d{4}/\d{1,2}/\d{1,2})'
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, self.text_content)
            if matches:
                info['signing_date'] = matches[0]
                break

        return info

    def _extract_parties(self) -> list[dict[str, str]:
        """提取合同方信息"""
        parties = []
        lines = self.text_content.split('\n')

        # 查找甲方
        party_info = {
            'role': '',
            'name': '',
            'address': '',
            'contact': ''
        }

        collecting = False
        for _i, line in enumerate(lines):
            line = line.strip()

            # 识别甲方/乙方
            if '甲方' in line or '委托方' in line:
                if collecting and party_info['role']:
                    parties.append(party_info.copy())

                party_info = {
                    'role': '甲方',
                    'name': '',
                    'address': '',
                    'contact': ''
                }
                collecting = True

                # 如果同一行有名称
                if ':' in line or '：' in line:
                    party_info['name'] = line.split('：')[-1].split(':')[-1].strip()

            elif '乙方' in line or '受托方' in line:
                if collecting and party_info['role']:
                    parties.append(party_info.copy())

                party_info = {
                    'role': '乙方',
                    'name': '',
                    'address': '',
                    'contact': ''
                }
                collecting = True

                # 如果同一行有名称
                if ':' in line or '：' in line:
                    party_info['name'] = line.split('：')[-1].split(':')[-1].strip()

            elif collecting and line:
                # 收集地址、联系方式等信息
                if not party_info['name'] and len(line) > 2:
                    party_info['name'] = line
                elif '地址' in line or '地址：' in line:
                    party_info['address'] = line.split('：')[-1].split(':')[-1].strip()
                elif '电话' in line or '手机' in line:
                    party_info['contact'] = line
                elif len(line) > 10 and not any(kw in line for kw in ['第', '条', '款']):
                    if not party_info['address']:
                        party_info['address'] = line

        # 添加最后一个
        if collecting and party_info['role']:
            parties.append(party_info)

        return parties

    def _extract_service_content(self) -> list[str]:
        """提取服务内容"""
        content = []
        lines = self.text_content.split('\n')

        service_keywords = [
            '专利申请', '专利代理', '技术服务', '委托代理',
            '服务范围', '工作内容', '委托事项'
        ]

        for line in lines:
            for keyword in service_keywords:
                if keyword in line and len(line) < 200:
                    content.append(line.strip())
                    break

        return list(set(content))

    def _extract_key_terms(self) -> list[str]:
        """提取关键条款"""
        terms = []
        lines = self.text_content.split('\n')

        term_keywords = [
            '保密条款', '违约责任', '争议解决', '法律适用',
            '权利义务', '服务期限', '知识产权', '验收标准'
        ]

        collecting = False
        current_term = []

        for line in lines:
            line = line.strip()
            matched = False

            for keyword in term_keywords:
                if keyword in line:
                    if collecting and current_term:
                        terms.append('\n'.join(current_term))

                    collecting = True
                    current_term = [line]
                    matched = True
                    break

            if not matched and collecting:
                if line.startswith('第') and ('条' in line or '款' in line):
                    if current_term:
                        terms.append('\n'.join(current_term))
                    collecting = False
                    current_term = []
                elif line and len(line) > 2:
                    current_term.append(line)

        if collecting and current_term:
            terms.append('\n'.join(current_term))

        return terms

    def _extract_financial_terms(self) -> dict[str, Any]:
        """提取财务条款"""
        financial = {
            'amount': '',
            'payment_terms': '',
            'currency': '人民币'
        }

        # 查找金额
        amount_patterns = [
            r'([\d,]+\.\d{2})\s*元',
            r'([\d,]+)\s*元',
            r'人民币\s*([\d,]+\.\d{2})',
            r'费用[：:]?\s*([\d,]+\.\d{2})'
        ]

        for pattern in amount_patterns:
            matches = re.findall(pattern, self.text_content)
            if matches:
                financial['amount'] = matches[0]
                break

        # 查找付款方式
        payment_keywords = [
            '付款方式', '支付期限', '结算方式', '分期付款'
        ]

        for keyword in payment_keywords:
            if keyword in self.text_content:
                financial['payment_terms'] = keyword
                break

        return financial

    def _extract_timeline(self) -> dict[str, Any]:
        """提取时间信息"""
        timeline = {
            'start_date': '',
            'end_date': '',
            'duration': '',
            'milestones': []
        }

        # 查找期限
        duration_patterns = [
            r'(\d+)\s*年',
            r'(\d+)\s*个月',
            r'(\d+)\s*天'
        ]

        for pattern in duration_patterns:
            matches = re.findall(pattern, self.text_content)
            if matches:
                timeline['duration'] = matches[0]
                break

        return timeline

def main():
    """主函数"""
    contract_path = '/Users/xujian/Athena工作平台/工作/济南热力集团/专利委托代理合同.pdf'

    parser = ContractParser(contract_path)
    result = parser.parse()

    # 输出结果
    logger.info("=== 合同解析结果 ===\n")

    # 基本信息
    logger.info('【基本信息】')
    if 'contract_info' in result:
        info = result['contract_info']
        logger.info(f"标题: {info.get('title', '未找到')}")
        logger.info(f"合同编号: {info.get('contract_number', '未找到')}")
        logger.info(f"签署日期: {info.get('signing_date', '未找到')}")

    # 合同方
    logger.info("\n【合同方】")
    if 'parties' in result:
        for party in result['parties']:
            logger.info(f"{party['role']}: {party['name']}")
            if party['address']:
                logger.info(f"  地址: {party['address']}")
            if party['contact']:
                logger.info(f"  联系方式: {party['contact']}")

    # 服务内容
    logger.info("\n【服务内容】")
    if 'service_content' in result:
        for i, content in enumerate(result['service_content'][:5], 1):
            logger.info(f"{i}. {content}")

    # 财务条款
    logger.info("\n【财务条款】")
    if 'financial_terms' in result:
        financial = result['financial_terms']
        logger.info(f"金额: {financial['amount']}")
        logger.info(f"付款方式: {financial['payment_terms']}")

    # 时间信息
    logger.info("\n【时间信息】")
    if 'timeline' in result:
        timeline = result['timeline']
        logger.info(f"服务期限: {timeline['duration']}")

    # 保存完整结果
    output_path = Path('/Users/xujian/Athena工作平台/reports/contract_analysis_result.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"\n完整解析结果已保存到: {output_path}")

if __name__ == '__main__':
    main()
