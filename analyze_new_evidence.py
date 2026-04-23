#!/usr/bin/env python3
"""
济南力邦专利无效案件 - 新增证据深度分析
"""
import sys
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')

try:
    import PyPDF2
    PdfReaderClass = PyPDF2.PdfReader
except ImportError:
    print("PyPDF2不可用")
    sys.exit(1)

# PDF文件目录
pdf_dir = Path("/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9无效材料/补充证据和理由2026.4.22/2026-04-22/")
pdf_files = sorted(pdf_dir.glob("*.pdf"))

print("=" * 80)
print("济南力邦专利无效案件 - 新增证据深度分析")
print("=" * 80)
print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"文件数量: {len(pdf_files)}")
print()

# 分析每个PDF
for pdf_file in pdf_files:
    print(f"\n{'=' * 80}")
    print(f"分析文件: {pdf_file.name}")
    print(f"文件大小: {pdf_file.stat().st_size / 1024:.1f} KB")
    print('=' * 80)

    try:
        # 读取PDF
        with open(pdf_file, 'rb') as f:
            pdf_doc = PdfReaderClass(f)
            num_pages = len(pdf_doc.pages)

            print(f"\n📄 基本信息:")
            print(f"  总页数: {num_pages}")

            # 提取文本（前3页，通常包含关键信息）
            full_text = ""
            max_pages = min(3, num_pages)

            for page_num in range(max_pages):
                page = pdf_doc.pages[page_num]
                try:
                    text = page.extract_text()
                    full_text += text
                except Exception as e:
                    print(f"  ⚠️ 第{page_num+1}页提取失败: {e}")

            # 提取专利号
            patent_match = re.search(r'(CN\d{8,9}[A-Z]?)', pdf_file.name)
            if patent_match:
                patent_number = patent_match.group(1)
                print(f"  专利号: {patent_number}")

            # 提取标题（从文本中）
            title_match = re.search(r'发明名称[：:]\s*(.+?)[\n\r]', full_text)
            if not title_match:
                title_match = re.search(r'Title[：:]\s*(.+?)[\n\r]', full_text)
            if title_match:
                title = title_match.group(1).strip()
                print(f"  标题: {title}")

            # 提取摘要
            abstract_match = re.search(r'摘要[：:]\s*(.+?)(?:权利要求|说明书|$)', full_text, re.DOTALL)
            if abstract_match:
                abstract = abstract_match.group(1).strip()
                # 清理摘要文本
                abstract = re.sub(r'\s+', ' ', abstract)
                abstract = abstract[:500] + "..." if len(abstract) > 500 else abstract
                print(f"\n📝 摘要:")
                print(f"  {abstract}")

            # 提取权利要求（第一项）
            claims_match = re.search(r'权利要求[：:]\s*(.+?)(?:说明书|权利要求|Abstract|$)', full_text, re.DOTALL)
            if claims_match:
                claims_text = claims_match.group(1).strip()
                claim1_match = re.search(r'1\..*?(?=\n\s*2\.|$)', claims_text, re.DOTALL)
                if claim1_match:
                    claim1 = claim1_match.group(0).strip()
                    claim1 = re.sub(r'\s+', ' ', claim1)
                    print(f"\n⚖️  权利要求1:")
                    print(f"  {claim1[:300]}...")

            # 提取申请人和发明人
            applicant_match = re.search(r'申请人[：:]\s*(.+?)[\n\r]', full_text)
            if applicant_match:
                applicant = applicant_match.group(1).strip()
                print(f"\n👤 申请人: {applicant}")

            inventor_match = re.search(r'发明人[：:]\s*(.+?)[\n\r]', full_text)
            if inventor_match:
                inventor = inventor_match.group(1).strip()
                print(f"  发明人: {inventor}")

            # 提取申请日
            date_match = re.search(r'申请日[：:]\s*(\d{4}[\.]\d{1,2}[\.]\d{1,2})', full_text)
            if date_match:
                app_date = date_match.group(1)
                print(f"📅 申请日: {app_date}")

            # 技术领域关键词
            keywords = []
            keyword_patterns = [
                r'包装机|packaging|packer',
                r'传送装置|输送|conveyor|transport',
                r'限位|调节|adjust|regulat',
                r'导轨|guide|rail',
                r'物料|material',
                r'斜向|oblique|angled'
            ]

            for pattern in keyword_patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    keywords.append(pattern.split('|')[0])

            if keywords:
                print(f"\n🔑 技术关键词: {', '.join(set(keywords))}")

            # 评估证据价值
            print(f"\n💡 初步评估:")

            # 检查是否包含目标专利的关键技术特征
            key_features = [
                "间距", "逐渐", "减小", "调节", "限位",
                "导轨", "斜向", "物料", "传送", "包装机"
            ]

            matched_features = []
            for feature in key_features:
                if feature in full_text:
                    matched_features.append(feature)

            if matched_features:
                print(f"  ✅ 发现相关技术特征: {', '.join(matched_features[:5])}")
                print(f"  ⭐ 证据价值: 高（与目标专利技术领域相关）")
            else:
                print(f"  ⚠️ 未发现明显相关技术特征")
                print(f"  ⭐ 证据价值: 待评估（需要详细分析技术方案）")

    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("分析完成")
print("=" * 80)
