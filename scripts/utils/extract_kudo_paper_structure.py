#!/usr/bin/env python3
"""
从PDF提取Kudo论文的完整结构化内容
生成适合翻译的Markdown模板
"""

import re
from datetime import datetime

# 读取提取的文本
with open("/tmp/kudo_paper.txt", encoding='utf-8') as f:
    content = f.read()

# 解析论文结构
lines = content.split('\n')

# 元信息
metadata = {
    "title": "Sulfonate Ionic Liquid as a Stable and Active Catalyst for Levoglucosenone Production from Saccharides via Catalytic Pyrolysis",
    "journal": "Catalysts",
    "year": "2013",
    "volume": "3",
    "issue": "4",
    "pages": "757-773",
    "doi": "10.3390/catal3040757",
    "authors": "Shinji Kudo, Zhenwei Zhou, Kento Yamasaki, Koyo Norinaga, Jun-ichiro Hayashi",
}

# 提取各部分
sections = {}
current_section = None
current_content = []

for line in lines:
    line = line.strip()
    if not line:
        continue

    # 检测章节标题
    if line == "Abstract":
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content)
        current_section = "Abstract"
        current_content = []
    elif line == "Keywords:":
        # 上一行应该是摘要的最后一句
        continue
    elif line == "1. Introduction":
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content)
        current_section = "Introduction"
        current_content = []
    elif re.match(r'^2\.\s+', line):
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content)
        current_section = f"Section_{line}"
        current_content = []
    elif re.match(r'^2\.\d+\.', line):
        # 子章节，合并到父章节
        current_content.append(f"\n### {line}\n")
        continue
    elif line == "References":
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content)
        current_section = "References"
        current_content = []
    elif line.startswith("Figure"):
        # 图表说明
        current_content.append(f"\n**{line}**\n")
        continue
    elif line.startswith("Table"):
        # 表格说明
        current_content.append(f"\n**{line}**\n")
        continue
    elif re.match(r'^\d+$', line):
        # 跳过页码
        continue
    elif line in ["Catalysts 2013, 3"]:
        continue
    elif len(line) <= 4 and line.isalpha():
        # 可能是页眉
        continue
    else:
        current_content.append(line)

# 保存最后一部分
if current_section and current_content:
    sections[current_section] = "\n".join(current_content)

# 生成Markdown模板
output = []
output.append("---")
output.append(f"title: {metadata['title']}")
output.append(f"journal: {metadata['journal']} {metadata['year']}, {metadata['volume']}({metadata['issue']}), {metadata['pages']}")
output.append(f"doi: {metadata['doi']}")
output.append(f"authors: {metadata['authors']}")
output.append(f"translation_date: {datetime.now().strftime('%Y-%m-%d')}")
output.append("---")
output.append("")
output.append("# 论文翻译模板")
output.append("")
output.append("## 使用说明")
output.append("")
output.append("1. 将英文段落翻译为中文，保留在对应段落的下方")
output.append("2. 保留所有图表、公式、参考文献的原始格式")
output.append("3. 专业术语请保持一致性")
output.append("")
output.append("---")
output.append("")

# 输出标题
output.append(f"# {metadata['title']}")
output.append("")
output.append("**中文标题：** 磺酸基离子液体作为稳定高效催化剂用于糖类催化热解制备左旋葡聚糖酮")
output.append("")
output.append("---")
output.append("")

# 输出各部分
section_titles = {
    "Abstract": "摘要",
    "Introduction": "1. 引言",
}

for section_key, content in sections.items():
    if section_key == "Abstract":
        output.append("## Abstract")
        output.append("")
        output.append("### 英文原文")
        output.append("")
        output.append(content)
        output.append("")
        output.append("### 中文翻译")
        output.append("")
        output.append("<!-- 请在此处翻译摘要 -->")
        output.append("")
        output.append("---")
        output.append("")
    elif section_key == "Introduction":
        output.append("## Introduction")
        output.append("")
        output.append("### 英文原文")
        output.append("")
        output.append(content)
        output.append("")
        output.append("### 中文翻译")
        output.append("")
        output.append("<!-- 请在此处翻译引言 -->")
        output.append("")
        output.append("---")
        output.append("")
    elif section_key == "References":
        output.append("## References")
        output.append("")
        output.append(content)
        output.append("")
    else:
        # 其他章节
        title = section_key.replace("Section_", "")
        output.append(f"## {title}")
        output.append("")
        output.append("### 英文原文")
        output.append("")
        output.append(content)
        output.append("")
        output.append("### 中文翻译")
        output.append("")
        output.append("<!-- 请在此处翻译 -->")
        output.append("")
        output.append("---")
        output.append("")

# 保存文件
output_path = "/Users/xujian/工作/04_审查意见/03_特殊程序/淄博千汇驳回复审/Kudo_2013_论文翻译模板.md"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(output))

print("="*80)
print("✅ 翻译模板已生成")
print("="*80)
print(f"\n📄 文件路径：{output_path}")
print("\n📋 使用说明：")
print("1. 打开生成的Markdown文件")
print("2. 将英文段落复制到DeepL、Google翻译等工具")
print("3. 将翻译结果粘贴到对应区域")
print("4. 保存即可")
