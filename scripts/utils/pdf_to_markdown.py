#!/usr/bin/env python3
"""
PDF转优雅Markdown工具 V4 - 终极版
- 提取PDF文本内容
- 清洗页眉、页脚、页码
- 格式化为优雅的Markdown
- 智能识别段落合并
- 处理特殊符号和列表
- 精确的标题识别
"""

import re
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("请安装 pdfplumber: pip install pdfplumber")
    exit(1)


class PDFToMarkdownConverter:
    """PDF到Markdown转换器"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_name = Path(pdf_path).stem

    # 页眉页脚模式
    HEADER_FOOTER_PATTERNS = [
        r'^\s*-\s*\d+\s*-\s*$',  # - 1 - 页码
        r'^\s*[―—－]\s*\d+\s*[―—－]\s*$',  # — 1 — 页码
        r'^第\s*\d+\s*页\s*$',  # 第1页
        r'^Page\s*\d+\s*(of|/)\s*\d+\s*$',  # Page 1 of 10
        r'^P\s*\d+\s*$',  # P1
        r'^\d+\s*/\s*\d+\s*$',  # 1/10
        r'^国家知识产权局.*$',  # 政府页眉
        r'^专利.*审查评议.*$',  # 重复标题
        r'^用户手册\s*$',  # 重复手册标题
    ]

    def is_header_footer(self, text: str) -> bool:
        """判断文本是否为页眉页脚"""
        text = text.strip()
        if not text:
            return True
        for pattern in self.HEADER_FOOTER_PATTERNS:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        if len(text) <= 3 and text.isdigit():
            return True
        return False

    def extract_text_from_pdf(self) -> list[str]:
        """从PDF提取文本内容，返回清洗后的行列表"""
        all_lines = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split('\n')

                # 过滤页眉页脚
                filtered = []
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    if not self.is_header_footer(stripped):
                        filtered.append(stripped)

                all_lines.extend(filtered)

        return all_lines

    def classify_line(self, line: str) -> tuple[str, int]:
        """
        分类每一行
        返回: (类型, 级别)
        类型: 'title', 'subtitle', 'list', 'text'
        级别: 标题层级 (1-6)，其他为0
        """
        line = line.strip()

        # 一级标题：中文数字序号 + 短文本（精确匹配）
        if re.match(r'^[一二三四五六七八九十]+[、.．]\s*\S{2,20}$', line):
            return 'title', 2

        # 二级标题：（一）（二）短标题
        if re.match(r'^[（\(][一二三四五六七八九十][）\)]\s*\S{2,15}$', line):
            return 'subtitle', 3

        # 三级标题：（1）（2）短标题
        if re.match(r'^[（\(]\d+[）\)]\s*\S{2,20}$', line):
            return 'subtitle', 4

        # 列表项
        if re.match(r'^[・·●○]\s*\S+', line):
            return 'list', 0

        # 关键词标题（精确匹配）
        keywords = ['使用须知', '操作说明', '登陆系统', '进入评议平台',
                   '意见录入', '查看意见', '注意事项', '办理流程',
                   '申请条件', '所需材料', '办理时限', '提交意见',
                   '草稿提交', '草稿编辑', '草稿删除', '撤回意见',
                   '待答复意见查看', '已答复意见查看', '意见处理详情查看',
                   '登陆系统', '进入评议平台']
        if line in keywords:
            return 'subtitle', 3

        # 默认为正文
        return 'text', 0

    def process_content(self, lines: list[str]) -> list[str]:
        """处理内容，合并段落并格式化"""
        if not lines:
            return []

        result = []
        current_buffer = []
        current_type = 'text'

        for line in lines:
            line_type, level = self.classify_line(line)

            # 如果是标题或子标题，先处理缓冲区
            if line_type in ['title', 'subtitle']:
                # 处理缓冲区内容
                if current_buffer:
                    content = ' '.join(current_buffer).strip()
                    if content:
                        result.append(('text', 0, content))
                    current_buffer = []
                    current_type = 'text'

                # 添加标题
                result.append((line_type, level, line))
                current_type = line_type

            # 如果是列表项
            elif line_type == 'list':
                # 处理缓冲区
                if current_buffer:
                    content = ' '.join(current_buffer).strip()
                    if content:
                        result.append(('text', 0, content))
                    current_buffer = []

                # 添加列表项
                result.append(('list', 0, line))

            # 如果是正文
            else:
                # 判断是否需要分段
                needs_break = False

                # 如果之前是标题，开始新段落
                if current_type in ['title', 'subtitle', 'list']:
                    needs_break = True
                    current_type = 'text'

                # 如果缓冲区内容以句号结尾，可能需要分段
                if current_buffer and current_buffer[-1].rstrip().endswith('。'):
                    # 检查当前行是否以大写字母或特定词开头
                    if re.match(r'^[A-Z《「『]', line) or re.match(r'^(以下|上述|因此|综上)', line):
                        needs_break = True

                if needs_break and current_buffer:
                    content = ' '.join(current_buffer).strip()
                    if content:
                        result.append(('text', 0, content))
                    current_buffer = []

                current_buffer.append(line)

        # 处理最后的缓冲区
        if current_buffer:
            content = ' '.join(current_buffer).strip()
            if content:
                result.append(('text', 0, content))

        return result

    def format_to_markdown(self, processed: list[tuple[str, int, str]) -> str:
        """将处理后的内容格式化为Markdown"""
        lines = []

        for item_type, level, content in processed:
            if item_type == 'title':
                lines.append('')
                lines.append('#' * level + ' ' + content)
                lines.append('')
            elif item_type == 'subtitle':
                lines.append('')
                lines.append('#' * level + ' ' + content)
                lines.append('')
            elif item_type == 'list':
                # 转换为标准列表格式
                content = re.sub(r'^[・·●○]\s*', '- ', content)
                lines.append(content)
            else:
                # 正文内容
                lines.append(content)
                lines.append('')

        return '\n'.join(lines)

    def clean_special_chars(self, text: str) -> str:
        """清理特殊字符"""
        # 清除 (cid:xxx) 类型的标记，替换为 •
        text = re.sub(r'\(cid:\d+\)', '', text)

        # 清理多余空格
        text = re.sub(r' +', ' ', text)

        # 清理多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    def add_document_header(self, text: str) -> str:
        """添加文档头部信息"""
        header = f"""# {self.pdf_name}

> 本文档由PDF自动转换生成

---

"""
        return header + text

    def convert(self) -> str:
        """执行完整的转换流程"""
        print(f"正在处理: {self.pdf_name}.pdf")

        # 1. 提取文本
        print("  - 提取文本内容...")
        raw_lines = self.extract_text_from_pdf()

        # 2. 处理内容（分类和合并）
        print("  - 处理文档结构...")
        processed = self.process_content(raw_lines)

        # 3. 格式化
        print("  - 格式化Markdown...")
        formatted_text = self.format_to_markdown(processed)

        # 4. 清理特殊字符
        print("  - 清理特殊字符...")
        cleaned_text = self.clean_special_chars(formatted_text)

        # 5. 添加头部
        final_text = self.add_document_header(cleaned_text)

        print("  ✓ 完成!")
        return final_text

    def save(self, output_path: str):
        """保存转换结果"""
        content = self.convert()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  → 已保存到: {output_path}")


def process_directory(directory: str):
    """处理目录中的所有PDF文件"""
    pdf_files = list(Path(directory).glob('*.pdf'))

    if not pdf_files:
        print(f"未找到PDF文件: {directory}")
        return

    print(f"找到 {len(pdf_files)} 个PDF文件\n")

    for pdf_file in pdf_files:
        output_path = pdf_file.with_suffix('.md')

        converter = PDFToMarkdownConverter(str(pdf_file))
        converter.save(str(output_path))
        print()

    print("=" * 50)
    print("转换完成!")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = '/Users/xujian/Documents/问答库'

    process_directory(target_dir)
