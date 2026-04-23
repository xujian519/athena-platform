#!/usr/bin/env python3
"""
专利相关性分析工具
用于专利无效分析中的证据筛选
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


class PatentRelevanceAnalyzer:
    """专利相关性分析器"""

    # 目标专利核心特征
    TARGET_PATENT_FEATURES = {
        "patent_number": "CN210456236U",
        "application_date": "2019-08-27",
        "ipc_classification": "B65G 21/20",
        "core_keywords": [
            "斜向", "滑轨", "导轨", "间距", "调节", "联动",
            "纵向", "横向", "限位", "物料", "传送", "包装机",
            "滑动", "驱动", "传动"
        ],
        "core_structures": [
            "斜向滑轨", "滑动座", "纵向调节", "间距调节",
            "驱动单元", "定位架", "滑动轴", "伞齿轮", "螺杆"
        ]
    }

    def __init__(self, features_dir: str, output_dir: str):
        self.features_dir = Path(features_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 加载所有专利特征
        self.patents = self._load_patents()

    def _load_patents(self) -> list[dict]:
        """加载所有专利特征"""
        patents = []
        feature_files = list(self.features_dir.glob("*_features.json"))

        for feature_file in feature_files:
            try:
                with open(feature_file, encoding='utf-8') as f:
                    data = json.load(f)
                    patents.append(data)
            except Exception as e:
                print(f"  ⚠️  加载失败 {feature_file.name}: {e}")

        return patents

    def calculate_ipc_similarity(self, patent: dict) -> float:
        """计算IPC分类相似度"""
        patent_ipc = patent["info"].get("ipc_classification", "")

        if not patent_ipc:
            return 0.0

        target_ipc = self.TARGET_PATENT_FEATURES["ipc_classification"]

        # 完全匹配
        if patent_ipc == target_ipc:
            return 1.0

        # 部分匹配（大类相同）
        target_main_class = target_ipc.split()[0] if " " in target_ipc else target_ipc[:4]
        patent_main_class = patent_ipc.split()[0] if " " in patent_ipc else patent_ipc[:4]

        if target_main_class in patent_ipc or patent_main_class in target_ipc:
            return 0.7

        # 同一大部（B65）
        if target_ipc[:3] == patent_ipc[:3]:
            return 0.4

        return 0.0

    def calculate_keyword_similarity(self, patent: dict) -> float:
        """计算关键词相似度"""
        sections = patent.get("sections", {})
        all_text = ""

        # 合并所有section的文本
        for _section_name, section_text in sections.items():
            if section_text:
                all_text += section_text + " "

        target_keywords = self.TARGET_PATENT_FEATURES["core_keywords"]

        # 计算匹配的关键词数量
        match_count = 0
        for keyword in target_keywords:
            if keyword in all_text:
                match_count += 1

        # 计算相似度（匹配关键词/总关键词）
        similarity = match_count / len(target_keywords)

        # 额外权重：核心关键词
        core_terms = ["斜向", "滑轨", "间距渐变", "联动", "纵向"]
        core_match = sum(1 for term in core_terms if term in all_text)
        similarity += core_match * 0.1

        return min(similarity, 1.0)

    def calculate_structure_similarity(self, patent: dict) -> float:
        """计算结构相似度"""
        sections = patent.get("sections", {})
        claims_text = sections.get("claims", "")
        detailed_text = sections.get("detailed_description", "")
        all_text = claims_text + detailed_text

        target_structures = self.TARGET_PATENT_FEATURES["core_structures"]

        # 计算匹配的结构组件数量
        match_count = 0
        for structure in target_structures:
            if structure in all_text:
                match_count += 1

        similarity = match_count / len(target_structures)

        # 额外权重：核心结构（斜向滑轨、联动）
        if "斜向滑轨" in all_text or "斜向" in all_text and "滑轨" in all_text:
            similarity += 0.2
        if "联动" in all_text:
            similarity += 0.1
        if "间距" in all_text and "调节" in all_text:
            similarity += 0.1

        return min(similarity, 1.0)

    def calculate_technical_effect_similarity(self, patent: dict) -> float:
        """计算技术效果相似度"""
        sections = patent.get("sections", {})
        summary = sections.get("summary", "")
        effects = patent["features"].get("technical_effects", [])

        # 目标专利的技术效果
        target_effects = [
            "同步调节", "间距", "纵向", "联动", "方便", "快速"
        ]

        all_text = summary + " ".join(effects)

        match_count = 0
        for effect in target_effects:
            if effect in all_text:
                match_count += 1

        return match_count / len(target_effects)

    def check_time_window(self, patent: dict) -> bool:
        """检查时间窗口"""
        application_date = patent["info"].get("application_date", "")

        if not application_date:
            return True  # 无法确定日期，保守处理

        # 目标专利申请日
        target_date = datetime.strptime(self.TARGET_PATENT_FEATURES["application_date"], "%Y-%m-%d")

        # 解析专利申请日
        try:
            patent_date = datetime.strptime(application_date, "%Y.%m.%d")
        except:
            try:
                patent_date = datetime.strptime(application_date, "%Y-%m-%d")
            except:
                return True  # 解析失败，保守处理

        # 专利申请日必须早于目标专利
        return patent_date < target_date

    def calculate_overall_relevance(self, patent: dict) -> dict[str, Any]:
        """计算综合相关性得分"""
        # 各维度得分
        ipc_score = self.calculate_ipc_similarity(patent)
        keyword_score = self.calculate_keyword_similarity(patent)
        structure_score = self.calculate_structure_similarity(patent)
        effect_score = self.calculate_technical_effect_similarity(patent)

        # 权重配置
        weights = {
            "ipc": 0.15,           # IPC分类权重
            "keyword": 0.35,       # 关键词权重
            "structure": 0.40,     # 结构相似度权重
            "effect": 0.10         # 技术效果权重
        }

        # 计算加权得分
        overall_score = (
            ipc_score * weights["ipc"] +
            keyword_score * weights["keyword"] +
            structure_score * weights["structure"] +
            effect_score * weights["effect"]
        )

        # 检查时间窗口
        time_valid = self.check_time_window(patent)

        return {
            "patent_number": patent["info"]["patent_number"],
            "publication_number": patent["info"].get("publication_number", ""),
            "application_date": patent["info"].get("application_date", ""),
            "ipc_classification": patent["info"].get("ipc_classification", ""),
            "patent_name": self._extract_patent_name(patent),
            "applicant": self._extract_applicant(patent),
            "scores": {
                "overall": round(overall_score * 100, 2),
                "ipc": round(ipc_score * 100, 2),
                "keyword": round(keyword_score * 100, 2),
                "structure": round(structure_score * 100, 2),
                "effect": round(effect_score * 100, 2)
            },
            "time_valid": time_valid,
            "key_features": self._extract_key_features(patent),
            "relevance_level": self._get_relevance_level(overall_score)
        }

    def _extract_patent_name(self, patent: dict) -> str:
        """提取专利名称"""
        sections = patent.get("sections", {})
        abstract = sections.get("abstract", "")

        # 从摘要中提取第一句话作为专利名称
        if abstract:
            match = re.search(r'([^。，\n]{5,30}(?:机构|装置|系统|设备|方法))', abstract)
            if match:
                return match.group(1)

        return patent["info"].get("patent_name", "-")

    def _extract_applicant(self, patent: dict) -> str:
        """提取申请人"""
        # 尝试从特征中提取
        return patent["info"].get("applicant", "-")

    def _extract_key_features(self, patent: dict) -> list[str]:
        """提取关键特征"""
        features = []
        sections = patent.get("sections", {})

        # 从技术领域提取
        technical_field = sections.get("technical_field", "")
        if "包装机" in technical_field:
            features.append("包装机相关")
        if "输送" in technical_field or "传送" in technical_field:
            features.append("输送/传送装置")
        if "调节" in technical_field:
            features.append("具有调节功能")

        # 从权利要求提取
        claims = sections.get("claims", "")
        if "滑轨" in claims or "导轨" in claims:
            features.append("滑轨/导轨结构")
        if "驱动" in claims:
            features.append("驱动装置")
        if "电机" in claims:
            features.append("电机驱动")
        if "手动" in claims or "手轮" in claims:
            features.append("手动调节")
        if "伺服" in claims:
            features.append("伺服控制")

        # 从具体实施方式提取
        detailed = sections.get("detailed_description", "")
        if "联动" in detailed or "同步" in detailed:
            features.append("联动/同步调节")

        return features[:10]  # 最多返回10个特征

    def _get_relevance_level(self, score: float) -> str:
        """获取相关性等级"""
        if score >= 0.7:
            return "极高相关"
        elif score >= 0.5:
            return "高相关"
        elif score >= 0.3:
            return "中等相关"
        elif score >= 0.15:
            return "低相关"
        else:
            return "无相关"

    def analyze_all(self) -> list[dict]:
        """分析所有专利"""
        print(f"\n🔍 开始分析 {len(self.patents)} 篇专利...")

        results = []
        for i, patent in enumerate(self.patents, 1):
            print(f"[{i}/{len(self.patents)}] 分析 {patent['info']['patent_number']}", end=" ")
            result = self.calculate_overall_relevance(patent)
            results.append(result)
            print(f"✓ 得分: {result['scores']['overall']}%")

        # 按得分排序
        results.sort(key=lambda x: x["scores"]["overall"], reverse=True)

        return results

    def generate_comparison_table(self, top_n: int = 30) -> str:
        """生成对比表"""
        results = self.analyze_all()
        top_results = results[:top_n]

        table = "| 排名 | 专利号 | 专利名称 | 申请日 | IPC分类 | 综合得分 | 相关性 |\n"
        table += "|------|--------|----------|--------|---------|----------|--------|\n"

        for i, result in enumerate(top_results, 1):
            name = result.get("patent_name", "-")[:25]
            table += f"| {i} | {result['patent_number']} | {name} | {result.get('application_date', '-')} | {result.get('ipc_classification', '-')} | {result['scores']['overall']}% | {result['relevance_level']} |\n"

        return table

    def save_analysis_results(self, results: list[dict]):
        """保存分析结果"""
        # 保存JSON
        json_path = self.output_dir / "relevance_analysis.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 保存Markdown报告
        md_path = self.output_dir / "relevance_analysis_report.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_markdown_report(results))

        print("\n✅ 分析结果已保存:")
        print(f"   - JSON: {json_path}")
        print(f"   - Markdown: {md_path}")

    def _generate_markdown_report(self, results: list[dict]) -> str:
        """生成Markdown报告"""
        report = f"""# 专利相关性分析报告

## 分析概要

| 项目 | 内容 |
|------|------|
| **分析时间** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| **分析专利数** | {len(results)} |
| **目标专利** | {self.TARGET_PATENT_FEATURES['patent_number']} |
| **目标IPC** | {self.TARGET_PATENT_FEATURES['ipc_classification']} |
| **时间窗口** | 申请日 < {self.TARGET_PATENT_FEATURES['application_date']} |

---

## 相关性得分分布

| 相关性等级 | 数量 | 占比 |
|------------|------|------|
| 极高相关 (≥70%) | {sum(1 for r in results if r['scores']['overall'] >= 70)} | {sum(1 for r in results if r['scores']['overall'] >= 70)/len(results)*100:.1f}% |
| 高相关 (50-70%) | {sum(1 for r in results if 50 <= r['scores']['overall'] < 70)} | {sum(1 for r in results if 50 <= r['scores']['overall'] < 70)/len(results)*100:.1f}% |
| 中等相关 (30-50%) | {sum(1 for r in results if 30 <= r['scores']['overall'] < 50)} | {sum(1 for r in results if 30 <= r['scores']['overall'] < 50)/len(results)*100:.1f}% |
| 低相关 (15-30%) | {sum(1 for r in results if 15 <= r['scores']['overall'] < 30)} | {sum(1 for r in results if 15 <= r['scores']['overall'] < 30)/len(results)*100:.1f}% |
| 无相关 (<15%) | {sum(1 for r in results if r['scores']['overall'] < 15)} | {sum(1 for r in results if r['scores']['overall'] < 15)/len(results)*100:.1f}% |

---

## Top 30 高相关专利

{self.generate_comparison_table(30)}

---

## Top 20 详细分析

"""

        for i, result in enumerate(results[:20], 1):
            report += f"### {i}. {result['patent_number']} - {result.get('patent_name', '未知')}\n\n"
            report += f"**综合得分**: {result['scores']['overall']}%  \n"
            report += f"**相关性等级**: {result['relevance_level']}  \n"
            report += f"**申请日**: {result.get('application_date', '-')}  \n"
            report += f"**IPC分类**: {result.get('ipc_classification', '-')}  \n"
            report += f"**时间窗口有效**: {'✅' if result['time_valid'] else '⚠️'}\n\n"

            report += "**得分明细**:\n\n"
            report += f"- IPC相似度: {result['scores']['ipc']}%\n"
            report += f"- 关键词相似度: {result['scores']['keyword']}%\n"
            report += f"- 结构相似度: {result['scores']['structure']}%\n"
            report += f"- 技术效果相似度: {result['scores']['effect']}%\n\n"

            if result['key_features']:
                report += "**关键特征**:\n\n"
                for feature in result['key_features']:
                    report += f"- {feature}\n"
                report += "\n"

            report += "---\n\n"

        return report


def main():
    """主函数"""
    # 配置路径
    features_dir = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/专利提取结果/features"
    output_dir = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/相关性分析结果"

    # 创建分析器
    analyzer = PatentRelevanceAnalyzer(features_dir, output_dir)

    # 执行分析
    results = analyzer.analyze_all()

    # 保存结果
    analyzer.save_analysis_results(results)

    # 输出摘要
    print("\n" + "=" * 60)
    print("📊 分析完成！")
    print("=" * 60)
    print("\nTop 10 最高相关专利:")
    for i, result in enumerate(results[:10], 1):
        print(f"  {i}. {result['patent_number']} - 得分: {result['scores']['overall']}% - {result['relevance_level']}")


if __name__ == "__main__":
    main()
