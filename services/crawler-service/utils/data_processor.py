#!/usr/bin/env python3
"""
数据处理器
Data Processor for Universal Crawler
"""

import json
import logging
import re
from datetime import datetime
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class DataProcessor:
    """数据处理器"""

    @staticmethod
    def extract_text(soup: BeautifulSoup, selector: str = None,
                     clean: bool = True) -> str:
        """
        提取文本内容

        Args:
            soup: BeautifulSoup对象
            selector: CSS选择器
            clean: 是否清理文本

        Returns:
            提取的文本
        """
        if selector:
            elements = soup.select(selector)
        else:
            elements = [soup]

        texts = []
        for element in elements:
            text = element.get_text(separator=' ', strip=True)
            if clean:
                text = DataProcessor.clean_text(text)
            if text:
                texts.append(text)

        return ' '.join(texts)

    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ''

        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除特殊字符但保留中文、英文、数字和基本标点
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,;:!?()[\]{}"\'-]', '', text)
        return text.strip()

    @staticmethod
    def extract_attributes(soup: BeautifulSoup, selector: str,
                          attributes: list[str]) -> dict[str, str]:
        """
        提取元素属性

        Args:
            soup: BeautifulSoup对象
            selector: CSS选择器
            attributes: 要提取的属性列表

        Returns:
            属性字典
        """
        element = soup.select_one(selector)
        if not element:
            return {}

        result = {}
        for attr in attributes:
            value = element.get(attr)
            if value:
                result[attr] = value

        return result

    @staticmethod
    def extract_table(soup: BeautifulSoup, selector: str = 'table',
                     headers: bool = True) -> pd.DataFrame:
        """
        提取表格数据

        Args:
            soup: BeautifulSoup对象
            selector: 表格选择器
            headers: 是否包含表头

        Returns:
            DataFrame对象
        """
        table = soup.select_one(selector)
        if not table:
            return pd.DataFrame()

        rows = []
        thead = table.find('thead')
        tbody = table.find('tbody')

        # 提取表头
        if headers and thead:
            header_row = []
            for th in thead.find_all('th'):
                header_text = DataProcessor.clean_text(th.get_text())
                header_row.append(header_text)
        else:
            header_row = None

        # 提取数据行
        if tbody:
            for tr in tbody.find_all('tr'):
                row_data = []
                for td in tr.find_all(['td', 'th']):
                    cell_text = DataProcessor.clean_text(td.get_text())
                    row_data.append(cell_text)
                rows.append(row_data)
        else:
            for tr in table.find_all('tr'):
                row_data = []
                for td in tr.find_all(['td', 'th']):
                    cell_text = DataProcessor.clean_text(td.get_text())
                    row_data.append(cell_text)
                rows.append(row_data)

        if rows:
            df = pd.DataFrame(rows)
            if header_row and len(df.columns) == len(header_row):
                df.columns = header_row
            return df

        return pd.DataFrame()

    @staticmethod
    def extract_json_data(text: str) -> dict[str, Any | None]:
        """
        从文本中提取JSON数据

        Args:
            text: 包含JSON的文本

        Returns:
            解析后的JSON数据
        """
        try:
            # 尝试直接解析
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试提取JSON字符串
            json_pattern = r'\{.*\}|\[.*\]'
            matches = re.findall(json_pattern, text, re.DOTALL)

            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        return None

    @staticmethod
    def extract_links(soup: BeautifulSoup, base_url: str = None,
                      pattern: str = None) -> list[dict[str, str]:
        """
        提取链接信息

        Args:
            soup: BeautifulSoup对象
            base_url: 基础URL用于处理相对链接
            pattern: 链接匹配模式

        Returns:
            链接信息列表
        """
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            text = DataProcessor.clean_text(link.get_text())

            # 处理相对URL
            if base_url and not href.startswith(('http://', 'https://')):
                from urllib.parse import urljoin
                href = urljoin(base_url, href)

            # 应用匹配模式
            if pattern:
                import re
                if not re.search(pattern, href):
                    continue

            link_info = {
                'url': href,
                'text': text,
                'title': link.get('title', '')
            }
            links.append(link_info)

        return links

    @staticmethod
    def extract_images(soup: BeautifulSoup, base_url: str = None) -> list[dict[str, str]:
        """
        提取图片信息

        Args:
            soup: BeautifulSoup对象
            base_url: 基础URL

        Returns:
            图片信息列表
        """
        images = []

        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            title = img.get('title', '')

            # 处理相对URL
            if base_url and src and not src.startswith(('http://', 'https://')):
                from urllib.parse import urljoin
                src = urljoin(base_url, src)

            if src:
                image_info = {
                    'src': src,
                    'alt': DataProcessor.clean_text(alt),
                    'title': DataProcessor.clean_text(title)
                }
                images.append(image_info)

        return images

    @staticmethod
    def extract_meta_tags(soup: BeautifulSoup) -> dict[str, str]:
        """
        提取meta标签信息

        Args:
            soup: BeautifulSoup对象

        Returns:
            meta标签信息
        """
        meta_info = {}

        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
            content = meta.get('content')

            if name and content:
                meta_info[name] = content

        return meta_info

    @staticmethod
    def save_to_csv(data: list[dict] | pd.DataFrame, filename: str,
                    index: bool = False):
        """
        保存数据到CSV文件

        Args:
            data: 要保存的数据
            filename: 文件名
            index: 是否包含索引
        """
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data

        df.to_csv(filename, index=index, encoding='utf-8')
        logger.info(f"数据已保存到: {filename}")

    @staticmethod
    def save_to_json(data: Any, filename: str, indent: int = 2) -> None:
        """
        保存数据到JSON文件

        Args:
            data: 要保存的数据
            filename: 文件名
            indent: JSON缩进
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        logger.info(f"数据已保存到: {filename}")

    @staticmethod
    def parse_date(date_str: str, formats: list[str] = None) -> datetime | None:
        """
        解析日期字符串

        Args:
            date_str: 日期字符串
            formats: 日期格式列表

        Returns:
            解析后的日期对象
        """
        if not date_str:
            return None

        if formats is None:
            formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%Y年%m月%d日',
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S'
            ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None
