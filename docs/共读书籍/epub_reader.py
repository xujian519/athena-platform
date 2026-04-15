#!/usr/bin/env python3
"""
共读书籍EPUB读取器
Shared Book EPUB Reader

为爸爸和小诺的共读时光服务
"""

import html
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


class EpubReader:
    """EPUB电子书读取器"""

    def __init__(self, epub_path: str):
        self.epub_path = Path(epub_path)
        self._metadata = {}
        self._chapters = []

    def read(self) -> dict:
        """读取EPUB文件"""
        if not self.epub_path.exists():
            raise FileNotFoundError(f"找不到文件: {self.epub_path}")

        # EPUB文件实际上是ZIP压缩包
        with zipfile.ZipFile(self.epub_path, 'r') as zf:
            # 读取元数据
            self._parse_metadata(zf)

            # 读取章节内容
            self._parse_content(zf)

        return {
            'metadata': self._metadata,
            'chapters': self._chapters,
            'total_chapters': len(self._chapters)
        }

    def _parse_metadata(self, zf: zipfile.ZipFile) -> Any:
        """解析书籍元数据"""
        try:
            # 查找container.xml以定位opf文件
            container_xml = zf.read('META-INF/container.xml')
            container_root = ET.fromstring(container_xml)

            # 获取opf文件路径
            opf_path = container_root.find(
                ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
            ).get('full-path')

            # 读取opf文件
            opf_content = zf.read(opf_path)
            opf_root = ET.fromstring(opf_content)

            # 提取元数据
            metadata = opf_root.find('{http://www.idpf.org/2007/opf}metadata')

            self._metadata = {
                'title': self._get_text(metadata, '{http://purl.org/dc/elements/1.1/}title', '未知'),
                'author': self._get_text(metadata, '{http://purl.org/dc/elements/1.1/}creator', '未知'),
                'language': self._get_text(metadata, '{http://purl.org/dc/elements/1.1/}language', '未知'),
                'publisher': self._get_text(metadata, '{http://purl.org/dc/elements/1.1/}publisher', ''),
            }

        except Exception as e:
            print(f"⚠️ 解析元数据失败: {e}")
            self._metadata = {
                'title': self.epub_path.stem,
                'author': '未知',
                'language': '未知',
                'publisher': ''
            }

    def _parse_content(self, zf: zipfile.ZipFile) -> Any:
        """解析章节内容"""
        try:
            # 简化版本：读取所有HTML文件
            html_files = [f for f in zf.namelist() if f.endswith('.html') or f.endswith('.xhtml')]

            for html_file in html_files:
                try:
                    content = zf.read(html_file).decode('utf-8', errors='ignore')

                    # 简单的HTML标签清理
                    content = self._clean_html(content)

                    # 只保留有实质内容的章节
                    if len(content.strip()) > 100:
                        # 从文件名提取章节标题
                        chapter_title = Path(html_file).stem.replace('_', ' ').title()

                        self._chapters.append({
                            'title': chapter_title,
                            'content': content[:5000],  # 限制长度避免过长
                            'file': html_file
                        })

                        if len(self._chapters) >= 50:  # 限制章节数量
                            break

                except Exception:
                    continue

        except Exception as e:
            print(f"⚠️ 解析内容失败: {e}")

    def _clean_html(self, html_content: str) -> str:
        """清理HTML标签，提取纯文本"""
        import re

        # 移除script和style标签
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

        # 移除所有HTML标签
        html_content = re.sub(r'<[^>]+>', '\n', html_content)

        # 解码HTML实体
        html_content = html.unescape(html_content)

        # 清理多余空白
        html_content = re.sub(r'\n\s*\n', '\n\n', html_content)

        return html_content.strip()

    def _get_text(self, element, tag, default='') -> None:
        """安全获取XML元素文本"""
        child = element.find(tag)
        return child.text if child is not None and child.text else default

    def get_summary(self) -> str:
        """生成书籍摘要"""
        if not self._metadata:
            self.read()

        summary = f"""
📖 《{self._metadata['title']}》
✍️ 作者：{self._metadata['author']}
🏢 出版社：{self._metadata['publisher'] or '未知'}
🌐 语言：{self._metadata['language']}
📑 章节数：{len(self._chapters)}章
"""
        return summary


def quick_read(epub_path: str) -> str:
    """快速读取EPUB并生成摘要"""
    reader = EpubReader(epub_path)
    data = reader.read()

    result = reader.get_summary()
    result += "\n📋 主要章节：\n"

    for i, chapter in enumerate(data['chapters'][:10], 1):  # 只显示前10章
        result += f"\n{i}. {chapter['title']}"
        result += f"\n   {chapter['content'][:200]}...\n"

    return result


# 使用示例
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        epub_file = sys.argv[1]
        print(quick_read(epub_file))
    else:
        print("请提供EPUB文件路径")
