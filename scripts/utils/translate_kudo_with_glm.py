#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用GLM-4.7翻译Kudo论文为中文
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path

import httpx

# API配置
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY", "54a69837dfd643d8ab7a7a72756ef837.uWBCuChZSM4aDRyq")
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 文件路径
INPUT_FILE = "/tmp/kudo_paper.txt"
OUTPUT_DIR = "/Users/xujian/工作/04_审查意见/03_特殊程序/淄博千汇驳回复审"


async def translate_text(text: str, source_lang: str = "English", target_lang: str = "中文") -> str:
    """
    使用GLM-4.7翻译文本

    Args:
        text: 要翻译的文本
        source_lang: 源语言
        target_lang: 目标语言

    Returns:
        翻译结果
    """
    if not text or not text.strip():
        return ""

    # 构建翻译提示词
    prompt = f"""请将以下{source_lang}学术论文段落翻译为{target_lang}。

要求：
1. 保持专业术语的准确性
2. 保持学术语言风格
3. 数字、公式、化学式保持原样
4. 人名、机构名保留原文或音译
5. 确保语句通顺、逻辑清晰

待翻译文本：
{text}

请直接输出翻译结果，不要添加任何解释。"""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "Authorization": f"Bearer {ZHIPUAI_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "glm-4-plus",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 8000,
            }

            response = await client.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            translated_text = result["choices"][0]["message"]["content"].strip()

            return translated_text

    except Exception as e:
        print(f"❌ 翻译失败: {e}")
        return f"[翻译失败: {str(e)}] {text}"


def parse_paper_sections(content: str) -> dict:
    """解析论文章节结构"""
    lines = content.split('\n')

    sections = {
        "title": "",
        "abstract": "",
        "introduction": "",
        "results": [],
        "conclusion": "",
        "references": "",
    }

    current_section = None
    current_content = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 跳过页码
        if re.match(r'^\d+$', line):
            continue

        # 检测章节标题
        if line == "Abstract":
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "abstract"
            current_content = []
        elif line == "Keywords:":
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "keywords"
            current_content = []
            continue
        elif line == "1. Introduction":
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "introduction"
            current_content = []
        elif re.match(r'^2\.\s+Results and Discussion', line):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "results_discussion"
            current_content = []
        elif re.match(r'^2\.\d+\.', line):
            # 结果部分的子章节
            if current_section == "results_discussion":
                # 开始新的子章节
                if current_content:
                    sections["results"].append({
                        "title": line,
                        "content": "\n".join(current_content)
                    })
                current_content = []
                continue
        elif line == "References":
            if current_section and current_content:
                if current_section == "results_discussion" and current_content:
                    sections["results"].append({
                        "title": "",
                        "content": "\n".join(current_content)
                    })
                else:
                    sections[current_section] = "\n".join(current_content)
            current_section = "references"
            current_content = []
        else:
            if current_section == "keywords":
                # 处理关键词
                sections["keywords"] = line
            elif line.startswith("Figure") or line.startswith("Table"):
                # 图表说明，保留
                current_content.append(f"\n**{line}**\n")
            elif line.startswith("Catalysts 2013"):
                continue
            elif len(line) < 5 and line.isalpha():
                continue
            else:
                current_content.append(line)

    # 保存最后一部分
    if current_section and current_content:
        if current_section == "results_discussion":
            sections["results"].append({
                "title": "",
                "content": "\n".join(current_content)
            })
        else:
            sections[current_section] = "\n".join(current_content)

    # 提取标题
    for line in lines[:50]:
        if "Sulfonate Ionic Liquid" in line and "Catalyst" in line:
            sections["title"] = line
            break

    return sections


async def translate_section(section_name: str, content: str, progress_callback=None):
    """翻译一个章节"""
    if not content or not content.strip():
        return ""

    # 如果内容太长，分段翻译
    if len(content) > 3000:
        # 按段落分段
        paragraphs = content.split('\n\n')
        translated_paragraphs = []

        for i, para in enumerate(paragraphs):
            if para.strip():
                translated = await translate_text(para.strip())
                translated_paragraphs.append(translated)

                if progress_callback:
                    progress_callback(section_name, i + 1, len(paragraphs))

        return "\n\n".join(translated_paragraphs)
    else:
        return await translate_text(content)


async def main():
    print("="*80)
    print("📄 使用GLM-4.7翻译Kudo 2013论文")
    print("="*80)

    # 1. 读取PDF提取的文本
    print("\n1️⃣ 读取原始文本...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"   ✓ 读取了 {len(content.split(chr(10)))} 行文本")

    # 2. 解析论文结构
    print("\n2️⃣ 解析论文结构...")
    sections = parse_paper_sections(content)
    print(f"   ✓ 识别到 {len([s for s in [sections.get('abstract'), sections.get('introduction')] if s])} 个主要部分")
    print(f"   ✓ 结果部分有 {len(sections.get('results', []))} 个子章节")

    # 3. 翻译各部分
    print("\n3️⃣ 开始翻译...")
    translated = {}

    # 翻译标题
    print("\n   [1/7] 翻译标题...")
    translated["title"] = "磺酸基离子液体作为稳定高效催化剂用于糖类催化热解制备左旋葡聚糖酮"

    # 翻译摘要
    print("   [2/7] 翻译摘要...")
    if sections.get("abstract"):
        translated["abstract"] = await translate_section("摘要", sections["abstract"])

    # 翻译关键词
    print("   [3/7] 翻译关键词...")
    if sections.get("keywords"):
        keywords_text = sections["keywords"]
        translated["keywords"] = await translate_text(f"Keywords: {keywords_text}")

    # 翻译引言
    print("   [4/7] 翻译引言...")
    if sections.get("introduction"):
        translated["introduction"] = await translate_section("引言", sections["introduction"])

    # 翻译结果部分
    print("   [5/7] 翻译结果与讨论...")
    translated_results = []
    for i, section in enumerate(sections.get("results", [])[:5]):  # 限制前5个章节
        print(f"      - 翻译第 {i+1} 部分...")
        title = section.get("title", "")
        content = section.get("content", "")

        if content:
            translated_content = await translate_section(f"结果-{i+1}", content)
            translated_results.append({
                "title": title,
                "content": translated_content
            })
    translated["results"] = translated_results

    # 翻译结论（如果有）
    if sections.get("conclusion"):
        print("   [6/7] 翻译结论...")
        translated["conclusion"] = await translate_section("结论", sections["conclusion"])

    # 翻译参考文献
    print("   [7/7] 处理参考文献...")
    translated["references"] = sections.get("references", "")

    # 4. 生成Markdown
    print("\n4️⃣ 生成Markdown文档...")
    md_lines = []

    # 文档头部
    md_lines.append("---")
    md_lines.append(f"title: {translated['title']}")
    md_lines.append("original_title: Sulfonate Ionic Liquid as a Stable and Active Catalyst for Levoglucosenone Production from Saccharides via Catalytic Pyrolysis")
    md_lines.append(f"translation_date: {datetime.now().strftime('%Y-%m-%d')}")
    md_lines.append("translator: GLM-4.7 (智谱AI)")
    md_lines.append("journal: Catalysts 2013, 3(4), 757-773")
    md_lines.append("doi: 10.3390/catal3040757")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append(f"# {translated['title']}")
    md_lines.append("")
    md_lines.append("**作者：** Shinji Kudo, Zhenwei Zhou, Kento Yamasaki, Koyo Norinaga, Jun-ichiro Hayashi")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # 摘要
    if translated.get("abstract"):
        md_lines.append("## 摘要")
        md_lines.append("")
        md_lines.append(translated["abstract"])
        md_lines.append("")

    # 关键词
    if translated.get("keywords"):
        md_lines.append("**关键词：** " + translated["keywords"].replace("Keywords:", "").strip())
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    # 引言
    if translated.get("introduction"):
        md_lines.append("## 1. 引言")
        md_lines.append("")
        md_lines.append(translated["introduction"])
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    # 结果部分
    if translated.get("results"):
        md_lines.append("## 2. 结果与讨论")
        md_lines.append("")

        for section in translated["results"]:
            if section.get("title"):
                md_lines.append(f"### {section['title']}")
                md_lines.append("")
            md_lines.append(section.get("content", ""))
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

    # 参考文献
    if translated.get("references"):
        md_lines.append("## 参考文献")
        md_lines.append("")
        md_lines.append(translated["references"])
        md_lines.append("")

    # 保存文件
    output_path = os.path.join(OUTPUT_DIR, "Kudo_2013_磺酸基离子液体催化剂_中文翻译_GLM47.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))

    print(f"   ✓ 翻译文件已保存至：")
    print(f"   {output_path}")

    print("\n" + "="*80)
    print("✅ 翻译完成！")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
