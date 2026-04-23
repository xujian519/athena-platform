#!/usr/bin/env python3
"""
合同信息提取器
从结构化PDF数据中提取关键合同信息
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

class ContractInfoExtractor:
    """合同信息提取器"""

    def __init__(self, json_path: str):
        """初始化

        Args:
            json_path: 结构化合同JSON文件路径
        """
        with open(json_path, encoding='utf-8') as f:
            self.structured_data = json.load(f)

    def extract_all_info(self) -> dict[str, Any]:
        """提取所有合同信息

        Returns:
            提取的信息字典
        """
        # 合并所有页面的文本
        full_text = ''
        for page in self.structured_data['pages']:
            full_text += page['text'] + '\n'

        # 提取各类信息
        contract_info = {
            '基本信息': self._extract_basic_info(full_text),
            '合同主体': self._extract_parties(full_text),
            '服务内容': self._extract_services(full_text),
            '费用条款': self._extract_financial_terms(full_text),
            '期限条款': self._extract_timeline_terms(full_text),
            '权利义务': self._extract_rights_obligations(full_text),
            '保密条款': self._extract_confidentiality_terms(full_text),
            '违约责任': self._extract_liability_terms(full_text),
            '争议解决': self._extract_dispute_resolution(full_text),
            '关键日期': self._extract_key_dates(full_text),
            '联系人信息': self._extract_contacts(full_text)
        }

        return contract_info

    def _extract_basic_info(self, text: str) -> dict[str, str]:
        """提取基本信息"""
        info = {}

        # 合同标题
        title_patterns = [
            r'([^\\n]*委托代理合同[^\\n]*)',
            r'([^\\n]*技术服务合同[^\\n]*)',
            r'([^\\n]*合作协议[^\\n]*)'
        ]
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                info['合同标题'] = match.group(1).strip()
                break

        # 合同编号
        contract_no_match = re.search(r'合同编号[：:]\s*([^\\n\\s]{2,50})', text)
        if contract_no_match:
            info['合同编号'] = contract_no_match.group(1).strip()

        # 签订地点
        location_match = re.search(r'签订地点[：:]\s*([^\\n\\s]{2,100})', text)
        if location_match:
            info['签订地点'] = location_match.group(1).strip()

        # 签署日期
        date_patterns = [
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                info['签署日期'] = match.group(1)
                break

        return info

    def _extract_parties(self, text: str) -> dict[str, dict[str, str]:
        """提取合同主体信息"""
        parties = {}

        # 提取甲方信息
        party_a = self._extract_party_info(text, '甲方|委托方')
        if party_a:
            parties['甲方'] = party_a

        # 提取乙方信息
        party_b = self._extract_party_info(text, '乙方|受托方|代理方')
        if party_b:
            parties['乙方'] = party_b

        return parties

    def _extract_party_info(self, text: str, party_pattern: str) -> dict[str, str]:
        """提取单个合同方信息"""
        lines = text.split('\n')
        party_info = {}
        collecting = False

        for _i, line in enumerate(lines):
            line = line.strip()

            # 检测到合同方
            if re.search(party_pattern, line):
                collecting = True
                # 如果同一行有名称
                if '：' in line or ':' in line:
                    name = line.split('：')[-1].split(':')[-1].strip()
                    if name:
                        party_info['名称'] = name
                continue

            # 收集信息
            if collecting:
                # 检查下一个合同方或章节开始
                if re.search('(甲方|乙方|受托方|委托方|第一条|第1条)', line):
                    break

                # 提取地址
                if any(keyword in line for keyword in ['地址：', '住址：', 'Address:', '地址：']):
                    party_info['地址'] = line.split('：')[-1].split(':')[-1].strip()

                # 提取联系人
                elif any(keyword in line for keyword in ['联系人：', '代表：', 'Contact:', '法定代表人：']):
                    party_info['联系人'] = line.split('：')[-1].split(':')[-1].strip()

                # 提取电话
                elif any(keyword in line for keyword in ['电话：', 'Tel:', '手机：']):
                    party_info['电话'] = line.split('：')[-1].split(':')[-1].strip()

                # 提取邮箱
                elif '@' in line and '.' in line:
                    party_info['邮箱'] = line.strip()

                # 提取公司信息
                elif not party_info.get('名称') and len(line) > 5 and not any(char in line for char in '：:；;第条款'):
                    party_info['名称'] = line

        return party_info

    def _extract_services(self, text: str) -> list[dict[str, str]:
        """提取服务内容"""
        services = []

        # 服务关键词
        service_keywords = [
            '专利申请', '专利代理', '技术服务', '委托代理',
            '知识产权', '专利分析', '专利撰写', '专利检索',
            '专利答复', '专利无效', '专利诉讼', '专利维护'
        ]

        lines = text.split('\n')
        collecting = False
        current_service = []

        for line in lines:
            line = line.strip()

            # 检测服务内容
            if any(keyword in line for keyword in service_keywords):
                if collecting and current_service:
                    services.append({
                        '服务内容': '\n'.join(current_service),
                        '关键词': [kw for kw in service_keywords if kw in '\n'.join(current_service)]
                    })

                collecting = True
                current_service = [line]
                continue

            # 收集服务描述
            if collecting:
                # 检查其他章节开始
                if re.search('(费用|付款|期限|责任|违约|争议|第一条|第1条|甲方的权利|乙方的权利)', line):
                    if current_service:
                        services.append({
                            '服务内容': '\n'.join(current_service),
                            '关键词': [kw for kw in service_keywords if kw in '\n'.join(current_service)]
                        })
                    collecting = False
                    current_service = []
                elif line:
                    current_service.append(line)

        # 添加最后一个
        if collecting and current_service:
            services.append({
                '服务内容': '\n'.join(current_service),
                '关键词': [kw for kw in service_keywords if kw in '\n'.join(current_service)]
            })

        return services

    def _extract_financial_terms(self, text: str) -> dict[str, Any]:
        """提取费用条款"""
        financial = {
            '费用总额': '',
            '货币': '人民币',
            '付款方式': '',
            '付款期限': '',
            '发票': '',
            '税费': ''
        }

        # 提取金额
        amount_patterns = [
            r'总费用[：:]?\s*([\d,]+\.\d{2})\s*元',
            r'合同金额[：:]?\s*([\d,]+\.\d{2})\s*元',
            r'代理费[：:]?\s*([\d,]+\.\d{2})\s*元',
            r'服务费[：:]?\s*([\d,]+\.\d{2})\s*元'
        ]

        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                financial['费用总额'] = match.group(1)
                break

        # 提取付款方式
        payment_patterns = [
            r'付款方式[：:]?\s*([^\\n]{2,50})',
            r'支付方式[：:]?\s*([^\\n]{2,50})',
            r'结算方式[：:]?\s*([^\\n]{2,50})'
        ]

        for pattern in payment_patterns:
            match = re.search(pattern, text)
            if match:
                financial['付款方式'] = match.group(1).strip()
                break

        # 检查发票信息
        if '发票' in text:
            financial['发票'] = '需要提供发票'

        return financial

    def _extract_timeline_terms(self, text: str) -> dict[str, Any]:
        """提取期限条款"""
        timeline = {
            '开始日期': '',
            '结束日期': '',
            '服务期限': '',
            '里程碑': []
        }

        # 提取服务期限
        duration_patterns = [
            r'服务期限[：:]?\s*(\d+\s*年)',
            r'服务期限[：:]?\s*(\d+\s*个月)',
            r'服务期限[：:]?\s*(\d+\s*天)',
            r'合同期限[：:]?\s*(\d+\s*年)',
            r'合同期限[：:]?\s*(\d+\s*个月)'
        ]

        for pattern in duration_patterns:
            match = re.search(pattern, text)
            if match:
                timeline['服务期限'] = match.group(1)
                break

        return timeline

    def _extract_rights_obligations(self, text: str) -> dict[str, list[str]:
        """提取权利义务"""
        rights_obligations = {
            '甲方权利': [],
            '甲方义务': [],
            '乙方权利': [],
            '乙方义务': []
        }

        # 简单提取，可以进一步优化
        lines = text.split('\n')
        party = None
        collecting = False
        current_items = []

        for line in lines:
            line = line.strip()

            if '甲方的权利' in line or '甲方权利' in line:
                if collecting and current_items:
                    if party:
                        rights_obligations[party] = current_items
                party = '甲方权利'
                collecting = True
                current_items = []
            elif '甲方的义务' in line or '甲方义务' in line:
                if collecting and current_items:
                    if party:
                        rights_obligations[party] = current_items
                party = '甲方义务'
                collecting = True
                current_items = []
            elif '乙方的权利' in line or '乙方权利' in line:
                if collecting and current_items:
                    if party:
                        rights_obligations[party] = current_items
                party = '乙方权利'
                collecting = True
                current_items = []
            elif '乙方的义务' in line or '乙方义务' in line:
                if collecting and current_items:
                    if party:
                        rights_obligations[party] = current_items
                party = '乙方义务'
                collecting = True
                current_items = []
            elif collecting and line and re.match(r'^\d+[\.、]', line):
                current_items.append(line)
            elif collecting and not line:
                if party:
                    rights_obligations[party] = current_items
                collecting = False
                current_items = []

        # 添加最后一个
        if collecting and current_items and party:
            rights_obligations[party] = current_items

        return rights_obligations

    def _extract_confidentiality_terms(self, text: str) -> list[str]:
        """提取保密条款"""
        confidentiality = []

        if '保密' in text or '机密' in text:
            # 提取包含保密的段落
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if '保密' in line or '机密' in line:
                    # 收集前后几行
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    paragraph = '\n'.join(lines[start:end])
                    confidentiality.append(paragraph.strip())

        return list(set(confidentiality))  # 去重

    def _extract_liability_terms(self, text: str) -> list[str]:
        """提取违约责任"""
        liability = []

        if '违约' in text or '责任' in text:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if '违约' in line or '违约责任' in line:
                    # 收集相关段落
                    start = max(0, i-1)
                    end = min(len(lines), i+4)
                    paragraph = '\n'.join(lines[start:end])
                    liability.append(paragraph.strip())

        return list(set(liability))

    def _extract_dispute_resolution(self, text: str) -> dict[str, str]:
        """提取争议解决条款"""
        dispute = {}

        # 争议解决方式
        if '仲裁' in text:
            dispute['解决方式'] = '仲裁'
        elif '诉讼' in text:
            dispute['解决方式'] = '诉讼'
        elif '协商' in text:
            dispute['解决方式'] = '协商'

        # 适用法律
        if '中华人民共和国法律' in text:
            dispute['适用法律'] = '中华人民共和国法律'

        # 管辖法院
        court_match = re.search(r'(有管辖权的人民法院|.*人民法院)', text)
        if court_match:
            dispute['管辖法院'] = court_match.group(1)

        return dispute

    def _extract_key_dates(self, text: str) -> list[dict[str, str]:
        """提取关键日期"""
        dates = []

        date_patterns = [
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(自合同签订之日起)\s*(\d+\s*天|日)',
            r'(收到通知之日起)\s*(\d+\s*天|日)'
        ]

        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                dates.append({
                    '日期': match.group(1),
                    '类型': '重要日期'
                })

        return dates

    def _extract_contacts(self, text: str) -> list[dict[str, str]:
        """提取联系人信息"""
        contacts = []

        # 电话号码
        phone_patterns = [
            r'(\d{3,4}-\d{7,8})',
            r'(\d{11})',
            r'(\d{3}\s*\d{4}\s*\d{4})'
        ]

        # 邮箱
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'

        # 提取电话
        for pattern in phone_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                contacts.append({
                    '类型': '电话',
                    '信息': match.group(1)
                })

        # 提取邮箱
        matches = re.finditer(email_pattern, text)
        for match in matches:
            contacts.append({
                '类型': '邮箱',
                '信息': match.group(1)
            })

        return contacts

    def save_extracted_info(self, output_path: str):
        """保存提取的信息

        Args:
            output_path: 输出文件路径
        """
        extracted_info = self.extract_all_info()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_info, f, ensure_ascii=False, indent=2)

        logger.info(f"合同信息已保存到: {output_path}")

def main():
    """主函数"""
    # 输入文件路径
    structured_json = '/Users/xujian/Athena工作平台/reports/contract_structured.json'

    # 输出文件路径
    output_path = '/Users/xujian/Athena工作平台/reports/contract_extracted_info.json'

    # 提取信息
    extractor = ContractInfoExtractor(structured_json)

    # 打印关键信息摘要
    info = extractor.extract_all_info()

    logger.info("=== 合同信息提取摘要 ===\n")

    if '基本信息' in info:
        basic = info['基本信息']
        logger.info(f"合同标题: {basic.get('合同标题', '未找到')}")
        logger.info(f"合同编号: {basic.get('合同编号', '未找到')}")
        logger.info(f"签署日期: {basic.get('签署日期', '未找到')}")

    if '合同主体' in info:
        parties = info['合同主体']
        logger.info("\n=== 合同主体 ===")
        for role, party in parties.items():
            logger.info(f"{role}:")
            for key, value in party.items():
                logger.info(f"  {key}: {value}")

    if '服务内容' in info and info['服务内容']:
        logger.info("\n=== 服务内容 ===")
        for i, service in enumerate(info['服务_content'], 1):
            logger.info(f"{i}. {service.get('服务内容', '')[:100]}...")

    if '费用条款' in info:
        financial = info['费用条款']
        logger.info("\n=== 费用条款 ===")
        logger.info(f"费用总额: {financial.get('费用总额', '')}")
        logger.info(f"付款方式: {financial.get('付款方式', '')}")

    # 保存完整信息
    extractor.save_extracted_info(output_path)

if __name__ == '__main__':
    main()
