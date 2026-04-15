#!/usr/bin/env python3
"""
Google专利全文获取工具
从Google Patents获取专利全文并进行结构化解析

作者: 小诺
创建时间: 2025-12-16
版本: v1.0.0
"""

import json
import re
import time
from dataclasses import dataclass
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


@dataclass
class PatentSection:
    """专利段落结构"""
    section_type: str  # abstract, claims, description等
    title: str
    content: str
    paragraphs: list[str]

@dataclass
class PatentMetadata:
    """专利元数据"""
    patent_number: str
    title: str
    abstract: str
    inventors: list[str]
    assignee: str
    filing_date: str
    publication_date: str
    family_id: str
    citations: list[str]

class GooglePatentsExtractor:
    """Google专利全文获取器"""

    def __init__(self):
        self.base_url = "https://patents.google.com/patent/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # 请求间隔（避免被封）
        self.request_delay = 2

    def normalize_patent_number(self, patent_number: str) -> str:
        """标准化专利号格式"""
        # 移除空格和特殊字符
        patent_number = re.sub(r'[^\w]', '', patent_number.upper())

        # 处理中国专利号格式
        if patent_number.startswith('CN'):
            # 确保有正确的后缀
            if len(patent_number) == 9 + 2:  # CN + 9位数字
                if not patent_number[-1].isalpha():
                    patent_number += 'A'
            elif len(patent_number) == 13 + 2:  # CN + 13位数字
                if not patent_number[-1].isalpha():
                    patent_number += 'A'

        return patent_number

    def extract_from_meta_tags(self, soup: BeautifulSoup) -> PatentMetadata:
        """从meta标签提取专利元数据"""
        metadata = PatentMetadata(
            patent_number="",
            title="",
            abstract="",
            inventors=[],
            assignee="",
            filing_date="",
            publication_date="",
            family_id="",
            citations=[]
        )

        try:
            # 从title标签获取专利号和标题
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text()
                if ' - Google Patents' in title_text:
                    title_text = title_text.replace(' - Google Patents', '')
                    parts = title_text.split(' - ', 1)
                    if len(parts) >= 2:
                        metadata.patent_number = parts[0].strip()
                        metadata.title = parts[1].strip()

            # 从meta标签提取信息
            meta_tags = soup.find_all('meta')
            for tag in meta_tags:
                name = tag.get('name', '').lower()
                property_attr = tag.get('property', '').lower()
                content = tag.get('content', '')

                # 不同meta标签的处理
                if 'description' in name and content:
                    metadata.abstract = content[:500]  # 限制长度

                elif 'citation' in property_attr:
                    metadata.citations.append(content)

                elif 'inventor' in name:
                    metadata.inventors.append(content)

                elif 'assignee' in name:
                    metadata.assignee = content

            # 从JSON-LD结构化数据提取
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # 提取各种字段
                        if 'title' in data:
                            metadata.title = data['title']
                        if 'abstract' in data:
                            metadata.abstract = data['abstract']
                        if 'inventor' in data:
                            if isinstance(data['inventor'], list):
                                metadata.inventors = [inv.get('name', str(inv)) for inv in data['inventor']]
                            else:
                                metadata.inventors.append(data['inventor'])
                        if 'assignee' in data:
                            assignee = data['assignee']
                            if isinstance(assignee, dict):
                                metadata.assignee = assignee.get('name', str(assignee))
                            else:
                                metadata.assignee = str(assignee)

                except json.JSONDecodeError:
                    continue

        except Exception as e:
            print(f"提取元数据时出错: {e}")

        return metadata

    def parse_patent_sections(self, soup: BeautifulSoup) -> list[PatentSection]:
        """解析专利各部分内容"""
        sections = []

        try:
            # 查找专利内容的主要容器
            content_div = soup.find('div', {'class': 'description'}) or soup.find('div', {'itemprop': 'description'})

            if content_div:
                # 解析各个部分
                content_div.find_all(['h2', 'h3', 'h4', 'strong'])

                current_section = None
                current_content = []

                for element in content_div.find_all(['p', 'div', 'h2', 'h3', 'h4', 'strong']):
                    tag_name = element.name.lower()
                    text = element.get_text().strip()

                    if not text:
                        continue

                    # 判断是否是新的段落标题
                    if tag_name in ['h2', 'h3', 'h4', 'strong']:
                        # 保存之前的段落
                        if current_section and current_content:
                            sections.append(PatentSection(
                                section_type=current_section,
                                title=current_section,
                                content='\n'.join(current_content),
                                paragraphs=current_content
                            ))

                        # 开始新段落
                        current_section = self._identify_section_type(text)
                        current_content = [text]

                    else:
                        # 内容段落
                        if current_section:
                            current_content.append(text)
                        else:
                            # 如果还没有确定段落，默认为描述
                            current_section = 'description'
                            current_content = [text]

                # 保存最后一个段落
                if current_section and current_content:
                    sections.append(PatentSection(
                        section_type=current_section,
                        title=current_section,
                        content='\n'.join(current_content),
                        paragraphs=current_content
                    ))

            # 特别处理权利要求（Claims）
            claims_section = self._extract_claims(soup)
            if claims_section:
                sections.insert(0, claims_section)  # 权利要求通常放在最前面

        except Exception as e:
            print(f"解析专利段落时出错: {e}")

        return sections

    def _identify_section_type(self, title: str) -> str:
        """识别段落类型"""
        title_lower = title.lower()

        section_mapping = {
            'abstract': ['abstract', '摘要'],
            'claims': ['claims', 'claim', '权利要求', '主权项'],
            'background': ['background', 'background art', '背景技术', '现有技术'],
            'summary': ['summary', 'summary of the invention', '发明内容', '技术方案'],
            'detailed_description': ['detailed description', 'description', '具体实施方式', '实施例'],
            'drawings': ['drawings', 'brief description of drawings', '附图说明'],
            'embodiments': ['embodiment', 'embodiments', '实施例', '具体实施方式']
        }

        for section_type, keywords in section_mapping.items():
            if any(keyword in title_lower for keyword in keywords):
                return section_type

        return 'other'

    def _extract_claims(self, soup: BeautifulSoup) -> PatentSection | None:
        """提取权利要求"""
        try:
            claims_div = soup.find('div', {'class': 'claims'}) or soup.find('section', {'itemprop': 'claims'})

            if claims_div:
                claims_text = claims_div.get_text(separator='\n', strip=True)

                # 分割各个权利要求
                claim_patterns = re.split(r'\n(?=\d+\.|1+\. )', claims_text)
                claims_list = []

                for claim in claim_patterns:
                    claim = claim.strip()
                    if claim and (claim.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or
                                re.match(r'^\d+\.', claim)):
                        claims_list.append(claim)

                if claims_list:
                    return PatentSection(
                        section_type='claims',
                        title='权利要求',
                        content='\n\n'.join(claims_list),
                        paragraphs=claims_list
                    )

        except Exception as e:
            print(f"提取权利要求时出错: {e}")

        return None

    def get_patent_full_text(self, patent_number: str) -> dict | None:
        """获取专利全文（结构化）"""
        try:
            # 标准化专利号
            normalized_number = self.normalize_patent_number(patent_number)

            # 构建URL
            url = self.base_url + quote(normalized_number)
            print(f"正在获取专利: {url}")

            # 发送请求
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # 检查是否找到专利
            if self._check_patent_not_found(soup):
                print(f"未找到专利: {patent_number}")
                return None

            # 提取数据
            metadata = self.extract_from_meta_tags(soup)
            sections = self.parse_patent_sections(soup)

            # 组装结果
            result = {
                'patent_number': metadata.patent_number or normalized_number,
                'title': metadata.title,
                'metadata': {
                    'inventors': metadata.inventors,
                    'assignee': metadata.assignee,
                    'filing_date': metadata.filing_date,
                    'publication_date': metadata.publication_date,
                    'family_id': metadata.family_id,
                    'citations': metadata.citations
                },
                'sections': [
                    {
                        'type': section.section_type,
                        'title': section.title,
                        'content': section.content,
                        'paragraphs': section.paragraphs
                    }
                    for section in sections
                ],
                'full_text': '\n\n'.join([
                    f"【{section.title}】\n{section.content}"
                    for section in sections
                ]),
                'extraction_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source_url': url
            }

            print(f"成功获取专利全文: {metadata.title}")
            return result

        except requests.RequestException as e:
            print(f"网络请求错误: {e}")
            return None
        except Exception as e:
            print(f"提取专利全文时出错: {e}")
            return None
        finally:
            # 请求间隔
            time.sleep(self.request_delay)

    def _check_patent_not_found(self, soup: BeautifulSoup) -> bool:
        """检查专利是否未找到"""
        # 检查页面中是否包含"未找到"相关内容
        not_found_indicators = [
            'patent not found',
            'no results found',
            'patent could not be found',
            '专利未找到',
            '无结果'
        ]

        page_text = soup.get_text().lower()
        return any(indicator in page_text for indicator in not_found_indicators)

    def batch_extract(self, patent_numbers: list[str], delay: int = 3) -> list[dict]:
        """批量获取专利"""
        results = []

        print(f"开始批量获取 {len(patent_numbers)} 个专利...")

        for i, patent_number in enumerate(patent_numbers, 1):
            print(f"\n进度: {i}/{len(patent_numbers)} - {patent_number}")

            result = self.get_patent_full_text(patent_number)
            if result:
                results.append(result)
            else:
                print(f"获取失败: {patent_number}")

            # 批量请求的额外延迟
            if i < len(patent_numbers):
                time.sleep(delay)

        print(f"\n批量获取完成！成功: {len(results)}/{len(patent_numbers)}")
        return results

    def save_to_file(self, patent_data: dict, filename: str = None):
        """保存专利数据到文件"""
        if not filename:
            patent_number = patent_data.get('patent_number', 'unknown')
            filename = f"patent_{patent_number}_{time.strftime('%Y%m%d_%H%M%S')}.json"

        filepath = f"/Users/xujian/Athena工作平台/data/patents/google_patents/{filename}"

        # 确保目录存在
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(patent_data, f, ensure_ascii=False, indent=2)

        print(f"专利数据已保存到: {filepath}")
        return filepath

def main():
    """测试函数"""
    extractor = GooglePatentsExtractor()

    # 测试单个专利获取
    test_patents = [
        "CN123456789A",  # 测试用专利号
        "CN108765432A",  # 另一个测试专利号
    ]

    for patent_number in test_patents:
        print(f"\n{'='*50}")
        print(f"测试专利: {patent_number}")
        print('='*50)

        result = extractor.get_patent_full_text(patent_number)

        if result:
            print(f"专利标题: {result['title']}")
            print(f"段落数量: {len(result['sections'])}")
            print(f"全文长度: {len(result['full_text'])} 字符")

            # 保存到文件
            extractor.save_to_file(result)

if __name__ == "__main__":
    main()
