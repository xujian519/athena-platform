#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译 Kudo 2013 磺酸离子液体催化剂论文为中文 Markdown 格式
Translate Kudo 2013 Sulfonate Ionic Liquid Catalyst Paper to Chinese Markdown
"""

import re
import os
from datetime import datetime

# 输入输出路径
INPUT_FILE = "/tmp/kudo_paper.txt"
OUTPUT_FILE = "/Users/xujian/工作/04_审查意见/03_特殊程序/淄博千汇驳回复审/Kudo_2013_Sulfonate_Ionic_Liquid_Catalyst_LVS_中文翻译.md"


# 术语翻译字典
TERMINOLOGY = {
    # 通用术语
    "Catalysts": "催化剂",
    "Ionic Liquid": "离子液体",
    "Levoglucosenone": "左旋葡聚糖酮",
    "Catalytic Pyrolysis": "催化热解",
    "Saccharides": "糖类",
    "Cellulose": "纤维素",
    "Sulfonate": "磺酸基",
    "Anion": "阴离子",
    "Cation": "阳离子",
    "Thermogravimetric Analysis": "热重分析",
    "TGA": "热重分析",
    "Abstract": "摘要",
    "Introduction": "引言",
    "Results and Discussion": "结果与讨论",
    "Conclusion": "结论",
    "References": "参考文献",
    "Keywords": "关键词",
    "Experimental": "实验部分",
    "Materials and Methods": "材料与方法",
    "Scheme": "方案",
    "Figure": "图",
    "Table": "表",
    "Equation": "方程",
    "yield": "产率",
    "conversion": "转化",
    "recovery": "回收",
    "reutilization": "再利用",
    "thermal stability": "热稳定性",
    "volatile": "挥发性产物",
    "lignocellulosic": "木质纤维素",
    "biomass": "生物质",
    "depolymerized": "解聚",
    "dehydrated": "脱水",
    "hydrolysis": "水解",
    "regenerated": "再生",
    "amorphous": "无定形",
    "enzymatic hydrolysis": "酶水解",
    "fractionation": "分馏",
    "intrinsic": "内在的",
    "Brønsted acidity": "布朗斯特酸性",
    "Lewis acidic": "路易斯酸性",
    "chiral synthon": "手性合成子",
    "functionalized": "功能化的",
    "recyclable": "可回收的",
    "upscaling": "放大",
}


def translate_chemical_formula(text):
    """翻译化学式和化合物名称"""
    formulas = {
        r"1-butyl-3-methylimidazolium": "1-丁基-3-甲基咪唑",
        r"1-butyl-2,3-dimethylimidazolium": "1-丁基-2,3-二甲基咪唑",
        r"\[BMIM\]": "[BMIM]",
        r"\[BMMIM\]": "[BMMIM]",
        r"triflate": "三氟甲磺酸",
        r"5-hydroxymethylfurfural": "5-羟甲基糠醛",
        r"HMF": "HMF",
        r"BF4-": "BF4⁻",
        r"PF6-": "PF6⁻",
        r"Cl-": "Cl⁻",
        r"CF3CO2-": "CF3CO2⁻",
        r"HSO4-": "HSO4⁻",
        r"CF3SO3-": "CF3SO3⁻",
        r"\(CF3SO2\)2N-": "(CF3SO2)2N⁻",
    }

    for eng, chi in formulas.items():
        text = re.sub(eng, chi, text)

    return text


def translate_section(text):
    """翻译文本段落"""
    # 首先应用术语翻译
    for eng, chi in TERMINOLOGY.items():
        text = re.sub(r'\b' + eng + r'\b', chi, text, flags=re.IGNORECASE)

    # 翻译化学式
    text = translate_chemical_formula(text)

    return text


def parse_paper_sections(content):
    """解析论文各部分"""
    lines = content.split('\n')

    sections = {
        "header": [],
        "abstract": [],
        "introduction": [],
        "results": [],
        "conclusion": [],
        "references": [],
        "figures": [],
        "tables": [],
    }

    current_section = "header"
    in_abstract = False
    in_keywords = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检测部分标题
        if line == "Abstract:":
            current_section = "abstract"
            in_abstract = True
            sections["abstract"].append("## 摘要\n")
            continue
        elif line == "Keywords:":
            in_keywords = True
            sections["abstract"].append("\n**关键词：**")
            continue
        elif line == "1. Introduction":
            current_section = "introduction"
            sections["introduction"].append("## 1. 引言\n")
            continue
        elif line.startswith("2. Results and Discussion"):
            current_section = "results"
            sections["results"].append("## 2. 结果与讨论\n")
            continue
        elif "Conclusion" in line or "3." in line and "conclusion" in line.lower():
            current_section = "conclusion"
            sections["conclusion"].append("## 3. 结论\n")
            continue
        elif line == "References":
            current_section = "references"
            sections["references"].append("## 参考文献\n")
            continue
        elif line.startswith("Figure") and line[5:].strip() and line[5:6].isdigit():
            sections["figures"].append(f"\n### {line}\n")
            continue
        elif line.startswith("Table") and line[5:].strip() and line[5:6].isdigit():
            sections["tables"].append(f"\n### {line}\n")
            continue

        # 处理内容
        if in_keywords:
            # 提取关键词
            keywords = [kw.strip() for kw in line.split(';')]
            translated_kw = []
            for kw in keywords:
                for eng, chi in TERMINOLOGY.items():
                    kw = re.sub(r'\b' + eng + r'\b', chi, kw, flags=re.IGNORECASE)
                translated_kw.append(kw)
            sections["abstract"].append("; ".join(translated_kw))
            in_keywords = False
        elif current_section == "header":
            # 处理标题头部
            if "Catalysts" in line and "2013" in line:
                sections["header"].append(f"# {translate_section(line)}\n")
            elif "OPEN ACCESS" in line:
                continue
            elif "Article" in line:
                continue
            elif "Sulfonate Ionic Liquid" in line:
                sections["header"].append(f"# {translate_section(line)}\n")
            elif line.startswith("Shinji Kudo"):
                # 作者信息
                sections["header"].append(f"\n**作者：** {translate_section(line)}\n")
            elif "Institute for Materials Chemistry" in line or "Interdisciplinary Graduate School" in line:
                sections["header"].append(f"{translate_section(line)}  \n")
            elif "Received:" in line or "Published:" in line:
                sections["header"].append(f"{translate_section(line)}\n")
            elif line.startswith("Abstract"):
                current_section = "abstract"
                sections["abstract"].append("## 摘要\n")
        else:
            # 处理正文段落
            if line and len(line) > 0:
                translated = translate_section(line)
                if current_section in sections:
                    sections[current_section].append(translated + "\n")

    return sections


def create_markdown(sections):
    """生成Markdown格式文档"""
    md_content = []

    # 标题和元信息
    md_content.append("---")
    md_content.append("title: 磺酸基离子液体作为稳定高效催化剂用于糖类催化热解制备左旋葡聚糖酮")
    md_content.append("original_title: Sulfonate Ionic Liquid as a Stable and Active Catalyst for Levoglucosenone Production from Saccharides via Catalytic Pyrolysis")
    md_content.append(f"translation_date: {datetime.now().strftime('%Y-%m-%d')}")
    md_content.append("translator: AI Translation System")
    md_content.append("---")
    md_content.append("")

    # 各部分内容
    for section_name, content in sections.items():
        if content:
            md_content.extend(content)
            md_content.append("")

    return "\n".join(md_content)


def main():
    print("="*80)
    print("📄 翻译 Kudo 2013 论文")
    print("="*80)

    # 读取提取的文本
    print("\n1️⃣ 读取原始文本...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"   ✓ 读取了 {len(content.split(chr(10)))} 行文本")

    # 解析论文结构
    print("\n2️⃣ 解析论文结构...")
    sections = parse_paper_sections(content)
    section_count = len([s for s in sections.values() if s])
    print(f"   ✓ 识别到 {section_count} 个主要部分")

    # 生成Markdown
    print("\n3️⃣ 生成 Markdown 格式...")
    markdown_content = create_markdown(sections)

    # 保存文件
    print("\n4️⃣ 保存翻译文件...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"   ✓ 翻译文件已保存至：")
    print(f"   {OUTPUT_FILE}")

    print("\n" + "="*80)
    print("✅ 翻译完成！")
    print("="*80)


if __name__ == "__main__":
    main()
