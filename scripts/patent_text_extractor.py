#!/usr/bin/env python3
"""
专利PDF文本提取和技术特征提取工具
用于专利无效分析的自动化处理
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import subprocess

try:
    import pdfplumber
except ImportError:
    print("正在安装 pdfplumber...")
    subprocess.check_call(["pip", "install", "pdfplumber"])
    import pdfplumber


class PatentTextExtractor:
    """专利文本提取器"""

    def __init__(self, pdf_dir: str, output_dir: str):
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        self.markdown_dir = self.output_dir / "markdown"
        self.features_dir = self.output_dir / "features"
        self.markdown_dir.mkdir(exist_ok=True)
        self.features_dir.mkdir(exist_ok=True)

    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """从PDF提取文本"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n\n".join(text_parts)
        except Exception as e:
            print(f"  ❌ 提取失败: {e}")
            return None

    def clean_text(self, text: str) -> str:
        """清理提取的文本"""
        # 移除多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 移除页码
        text = re.sub(r'第\s*\d+\s*页', '', text)
        # 移除页眉页脚常见内容
        text = re.sub(r'\(19\).*?中华人民共和国国家知识产权局', '', text)
        text = re.sub(r'\(12\).*?发明专利申请公开说明书', '', text)
        return text.strip()

    def extract_patent_info(self, text: str) -> Dict[str, Any]:
        """提取专利基本信息"""
        info = {
            "patent_number": "",
            "publication_number": "",
            "application_number": "",
            "application_date": "",
            "publication_date": "",
            "patent_name": "",
            "applicant": "",
            "inventor": "",
            "ipc_classification": "",
            "patent_type": "",
        }

        # 提取申请号
        app_num_match = re.search(r'申请号[：:]\s*([\d.]+)', text)
        if app_num_match:
            info["application_number"] = app_num_match.group(1)

        # 提取申请日
        app_date_match = re.search(r'申请日[：:]\s*(\d{4}\.?\d{1,2}\.?\d{1,2})', text)
        if app_date_match:
            info["application_date"] = app_date_match.group(1)

        # 提取公开号/公告号
        pub_num_match = re.search(r'(?:公开号|公告号|授权公告号)[：:]\s*([A-Z]?\s*[\d.]+[A-Z]?)', text)
        if pub_num_match:
            info["publication_number"] = pub_num_match.group(1).replace(" ", "")

        # 提取公开日/公告日
        pub_date_match = re.search(r'(?:公开日|公告日|授权公告日)[：:]\s*(\d{4}\.?\d{1,2}\.?\d{1,2})', text)
        if pub_date_match:
            info["publication_date"] = pub_date_match.group(1)

        # 提取专利名称
        name_patterns = [
            r'发明名称[：:]\s*(.+?)(?:\n|$)',
            r'实用新型名称[：:]\s*(.+?)(?:\n|$)',
            r'专利名称[：:]\s*(.+?)(?:\n|$)',
        ]
        for pattern in name_patterns:
            name_match = re.search(pattern, text)
            if name_match:
                info["patent_name"] = name_match.group(1).strip()
                break

        # 提取申请人
        applicant_match = re.search(r'申请人[：:]\s*(.+?)(?:\n|地址|邮编)', text)
        if applicant_match:
            info["applicant"] = applicant_match.group(1).strip()

        # 提取发明人
        inventor_match = re.search(r'发明人[：:]\s*(.+?)(?:\n|$)', text)
        if inventor_match:
            info["inventor"] = inventor_match.group(1).strip()

        # 提取IPC分类
        ipc_match = re.search(r'(?:IPC分类号|分类号)[：:]\s*([A-Z]\d+[A-Z]?\s*\d+/\d+)', text)
        if ipc_match:
            info["ipc_classification"] = ipc_match.group(1)

        # 判断专利类型
        if "发明专利" in text:
            info["patent_type"] = "发明"
        elif "实用新型" in text:
            info["patent_type"] = "实用新型"
        elif "外观设计" in text:
            info["patent_type"] = "外观设计"

        # 从文件名获取专利号
        return info

    def extract_sections(self, text: str) -> Dict[str, str]:
        """提取专利各部分内容"""
        sections = {
            "technical_field": "",
            "background_art": "",
            "summary": "",
            "brief_description": "",
            "detailed_description": "",
            "claims": "",
            "abstract": "",
        }

        # 提取技术领域
        field_match = re.search(r'【技术领域】\s*(.+?)(?=【背景技术】|$)', text, re.DOTALL)
        if not field_match:
            field_match = re.search(r'技术领域\s*(.+?)(?=背景技术|发明内容|$)', text, re.DOTALL)
        if field_match:
            sections["technical_field"] = field_match.group(1).strip()

        # 提取背景技术
        bg_match = re.search(r'【背景技术】\s*(.+?)(?=【发明内容】|$)', text, re.DOTALL)
        if not bg_match:
            bg_match = re.search(r'背景技术\s*(.+?)(?=发明内容|摘要|$)', text, re.DOTALL)
        if bg_match:
            sections["background_art"] = bg_match.group(1).strip()

        # 提取发明内容/摘要
        summary_match = re.search(r'【发明内容】\s*(.+?)(?=【附图说明】|$)', text, re.DOTALL)
        if not summary_match:
            summary_match = re.search(r'发明内容\s*(.+?)(?=附图说明|具体实施方式|$)', text, re.DOTALL)
        if summary_match:
            sections["summary"] = summary_match.group(1).strip()

        # 提取附图说明
        figures_match = re.search(r'【附图说明】\s*(.+?)(?=【具体实施方式】|$)', text, re.DOTALL)
        if not figures_match:
            figures_match = re.search(r'附图说明\s*(.+?)(?=具体实施方式|权利要求书|$)', text, re.DOTALL)
        if figures_match:
            sections["brief_description"] = figures_match.group(1).strip()

        # 提取具体实施方式
        detailed_match = re.search(r'【具体实施方式】\s*(.+?)(?=【权利要求书】|$)', text, re.DOTALL)
        if not detailed_match:
            detailed_match = re.search(r'具体实施方式\s*(.+?)(?=权利要求书|$)', text, re.DOTALL)
        if detailed_match:
            sections["detailed_description"] = detailed_match.group(1).strip()

        # 提取权利要求书
        claims_match = re.search(r'【权利要求书】\s*(.+?)(?=【摘要】|$)', text, re.DOTALL)
        if not claims_match:
            claims_match = re.search(r'权利要求书\s*(.+?)(?=摘要|$)', text, re.DOTALL)
        if claims_match:
            sections["claims"] = claims_match.group(1).strip()

        # 提取摘要
        abstract_match = re.search(r'【摘要】\s*(.+?)(?=|$)', text, re.DOTALL)
        if not abstract_match:
            abstract_match = re.search(r'摘要\s*(.+?)$', text, re.DOTALL)
        if abstract_match:
            sections["abstract"] = abstract_match.group(1).strip()

        return sections

    def extract_technical_features(self, text: str, sections: Dict[str, str]) -> Dict[str, Any]:
        """提取技术特征"""
        features = {
            "keywords": [],
            "technical_terms": [],
            "structural_components": [],
            "functional_features": [],
            "technical_problem": "",
            "technical_solution": "",
            "technical_effects": [],
        }

        # 从技术领域提取关键词
        if sections["technical_field"]:
            field_keywords = self._extract_keywords(sections["technical_field"])
            features["keywords"].extend(field_keywords)

        # 从发明内容提取技术问题
        problem_match = re.search(
            r'(?:所要解决的技术问题|技术问题|解决的问题)[：:：\s]*(.+?)(?:。|$|采用|提供)',
            sections["summary"], re.DOTALL
        )
        if problem_match:
            features["technical_problem"] = problem_match.group(1).strip()

        # 提取技术方案关键词
        solution_keywords = [
            "包括", "设置", "具有", "连接", "安装", "配置",
            "滑轨", "导轨", "调节", "驱动", "传动", "限位",
            "物料", "传送", "输送", "包装", "机构", "装置"
        ]

        # 从权利要求中提取结构组件
        claims_text = sections["claims"]
        if claims_text:
            # 提取独立权利要求
            independent_claim = re.search(r'1[．.]\s*(.+?)(?=2[．.]|$)', claims_text, re.DOTALL)
            if independent_claim:
                claim_text = independent_claim.group(1)
                features["technical_solution"] = claim_text[:500]  # 前500字符

                # 提取组件
                components = re.findall(r'([^，。；,;]{2,8}(?:机构|装置|单元|部件|组件|器件|板|杆|轴|轮|座|架))', claim_text)
                features["structural_components"] = list(set(components))

        # 提取技术效果
        effects = re.findall(
            r'(?:有益效果|技术效果|优点|优势)[：:：\s]*([^\n]+(?:。|[^\n]+))',
            sections["summary"]
        )
        features["technical_effects"] = [e.strip() for e in effects if e.strip()]

        # 提取技术术语
        technical_terms = set()
        for section_name, section_text in sections.items():
            if section_text:
                # 提取专业术语（2-6个字，包含技术关键词）
                terms = re.findall(r'([\u4e00-\u9fa5]{2,6}(?:机构|装置|系统|设备|组件|部件|单元|模块|机构))', section_text)
                technical_terms.update(terms)

        features["technical_terms"] = list(technical_terms)

        # 去重关键词
        features["keywords"] = list(set(features["keywords"]))

        return features

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简单的关键词提取：名词、技术术语
        keywords = []
        tech_words = [
            "包装机", "传送", "输送", "限位", "调节", "导向", "滑轨", "导轨",
            "物料", "物品", "驱动", "传动", "机构", "装置", "系统", "设备",
            "纵向", "横向", "斜向", "间距", "位置", "自动", "同步"
        ]
        for word in tech_words:
            if word in text:
                keywords.append(word)
        return keywords

    def process_single_patent(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
        """处理单个专利文件"""
        patent_number = pdf_path.stem

        print(f"  处理: {patent_number}")

        # 提取文本
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return None

        text = self.clean_text(text)

        # 提取基本信息
        info = self.extract_patent_info(text)
        info["patent_number"] = patent_number

        # 提取各部分内容
        sections = self.extract_sections(text)

        # 提取技术特征
        features = self.extract_technical_features(text, sections)

        # 组合结果
        result = {
            "info": info,
            "sections": sections,
            "features": features,
            "raw_text_length": len(text),
        }

        # 保存Markdown
        self._save_markdown(patent_number, info, sections, text)

        # 保存特征
        self._save_features(patent_number, result)

        return result

    def _save_markdown(self, patent_number: str, info: Dict, sections: Dict, raw_text: str):
        """保存为Markdown格式"""
        md_path = self.markdown_dir / f"{patent_number}.md"

        md_content = f"""# {info.get('patent_name', patent_number)}

## 基本信息

| 项目 | 内容 |
|------|------|
| **专利号** | {patent_number} |
| **申请号** | {info.get('application_number', '-')} |
| **公开/公告号** | {info.get('publication_number', '-')} |
| **申请日** | {info.get('application_date', '-')} |
| **公开/公告日** | {info.get('publication_date', '-')} |
| **专利类型** | {info.get('patent_type', '-')} |
| **申请人** | {info.get('applicant', '-')} |
| **发明人** | {info.get('inventor', '-')} |
| **IPC分类** | {info.get('ipc_classification', '-')} |

---

## 摘要

{sections.get('abstract', '暂无')}

---

## 技术领域

{sections.get('technical_field', '暂无')}

---

## 背景技术

{sections.get('background_art', '暂无')}

---

## 发明内容

{sections.get('summary', '暂无')}

---

## 附图说明

{sections.get('brief_description', '暂无')}

---

## 具体实施方式

{sections.get('detailed_description', '暂无')}

---

## 权利要求书

{sections.get('claims', '暂无')}

---

*由AI自动提取于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

    def _save_features(self, patent_number: str, result: Dict):
        """保存特征为JSON格式"""
        feature_path = self.features_dir / f"{patent_number}_features.json"

        with open(feature_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    def process_batch(self, limit: Optional[int] = None) -> List[Dict]:
        """批量处理专利文件"""
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        pdf_files.sort()

        if limit:
            pdf_files = pdf_files[:limit]

        print(f"\n📁 开始处理 {len(pdf_files)} 个专利文件...")
        print(f"   输入目录: {self.pdf_dir}")
        print(f"   输出目录: {self.output_dir}")
        print(f"   └─ markdown/: {self.markdown_dir}")
        print(f"   └─ features/: {self.features_dir}")
        print()

        results = []
        success_count = 0
        fail_count = 0

        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}]", end=" ")
            result = self.process_single_patent(pdf_file)
            if result:
                results.append(result)
                success_count += 1
            else:
                fail_count += 1

        # 保存汇总报告
        self._save_summary(results, success_count, fail_count)

        print()
        print("=" * 60)
        print(f"✅ 处理完成！")
        print(f"   成功: {success_count}")
        print(f"   失败: {fail_count}")
        print(f"   成功率: {success_count/(success_count+fail_count)*100:.1f}%")
        print("=" * 60)

        return results

    def _save_summary(self, results: List[Dict], success_count: int, fail_count: int):
        """保存处理汇总报告"""
        summary_path = self.output_dir / "extraction_summary.json"

        summary = {
            "processing_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "statistics": {
                "total_processed": success_count + fail_count,
                "successful": success_count,
                "failed": fail_count,
                "success_rate": f"{success_count/(success_count+fail_count)*100:.1f}%" if (success_count+fail_count) > 0 else "0%"
            },
            "patents": []
        }

        for result in results:
            patent_info = {
                "patent_number": result["info"]["patent_number"],
                "publication_number": result["info"].get("publication_number", ""),
                "patent_name": result["info"].get("patent_name", ""),
                "application_date": result["info"].get("application_date", ""),
                "applicant": result["info"].get("applicant", ""),
                "ipc_classification": result["info"].get("ipc_classification", ""),
                "keywords": result["features"]["keywords"],
                "structural_components": result["features"]["structural_components"],
            }
            summary["patents"].append(patent_info)

        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        # 同时生成Markdown报告
        md_summary_path = self.output_dir / "extraction_summary.md"
        with open(md_summary_path, 'w', encoding='utf-8') as f:
            f.write(f"""# 专利文本提取汇总报告

## 处理统计

| 项目 | 数量 |
|------|------|
| **处理时间** | {summary['processing_time']} |
| **总处理数** | {summary['statistics']['total_processed']} |
| **成功提取** | {summary['statistics']['successful']} |
| **提取失败** | {summary['statistics']['failed']} |
| **成功率** | {summary['statistics']['success_rate']} |

## 专利清单

以下是成功提取的专利列表：

| 序号 | 专利号 | 专利名称 | 申请人 | 申请日 | IPC分类 |
|------|--------|----------|--------|--------|---------|
""")

            for i, patent in enumerate(summary["patents"], 1):
                name = patent.get("patent_name", "-")[:30]
                applicant = patent.get("applicant", "-")[:20]
                f.write(f"| {i} | {patent['patent_number']} | {name} | {applicant} | {patent.get('application_date', '-')} | {patent.get('ipc_classification', '-')} |\n")


def main():
    """主函数"""
    import sys

    # 配置路径
    pdf_dir = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/下载专利PDF"
    output_dir = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/专利提取结果"

    # 检查参数
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"⚠️  限制处理数量: {limit}")
        except ValueError:
            pass

    # 创建提取器并处理
    extractor = PatentTextExtractor(pdf_dir, output_dir)
    results = extractor.process_batch(limit=limit)

    print(f"\n📊 输出文件:")
    print(f"   - Markdown: {extractor.markdown_dir}")
    print(f"   - Features: {extractor.features_dir}")
    print(f"   - Summary: {extractor.output_dir}/extraction_summary.md")


if __name__ == "__main__":
    main()
