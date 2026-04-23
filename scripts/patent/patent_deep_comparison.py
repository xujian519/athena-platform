#!/usr/bin/env python3
"""
专利深度技术对比分析工具
用于专利无效分析中的证据详细对比
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class PatentDeepComparator:
    """专利深度对比分析器"""

    # 目标专利详细特征
    TARGET_PATENT = {
        "patent_number": "CN210456236U",
        "patent_name": "包装机物品传送装置的物料限位板自动调节机构",
        "application_date": "2019-08-27",
        "ipc_classification": "B65G 21/20",
        "independent_claim": {
            "premise": "一种包装机物品传送装置的物料限位板自动调节机构",
            "base_features": [
                "包括机架",
                "两块可滑动地安装在机架上的物料限位板",
                "机架具有用于安装物料传送带的物料传送带安装空间",
                "两块物料限位板分别位于物料传送带安装空间两侧"
            ],
            "characterizing_portion": [
                "包括物料限位板斜向间距调节机构",
                "斜向间距调节机构包括驱动单元、纵向调节单元、斜向调节单元",
                "纵向调节单元安装在机架上，连接两块物料限位板底面",
                "驱动单元安装在机架上，连接纵向调节单元",
                "斜向调节单元包括两个安装架、两条斜向滑轨、两个滑动座",
                "两条斜向滑轨分别安装在两个安装架上",
                "两个滑动座分别可滑动地套在两条斜向滑轨上",
                "两个滑动座分别固定在两块物料限位板底面上",
                "两条斜向滑轨的间距从左往右逐渐缩短"  # 核心创新点
            ]
        },
        "core_features": {
            "F1": {
                "name": "斜向滑轨间距渐变",
                "description": "两条斜向滑轨的间距从左往右逐渐缩短",
                "technical_effect": "实现限位板纵向运动时同步改变间距",
                "importance": "最高"
            },
            "F2": {
                "name": "纵向调节单元",
                "description": "包括定位架、纵向移动装置和两个滑动块",
                "components": ["定位架", "纵向移动装置", "滑动块"],
                "importance": "高"
            },
            "F3": {
                "name": "驱动单元",
                "description": "包括电机、皮带轮、传动皮带",
                "components": ["电机", "第一皮带轮", "第二皮带轮", "传动皮带"],
                "importance": "高"
            },
            "F4": {
                "name": "滑动轴反向延伸",
                "description": "两根滑动轴分别安装在支撑杆顶端并且反向延伸",
                "technical_effect": "实现横向和纵向运动的解耦",
                "importance": "中"
            },
            "F5": {
                "name": "伞齿轮传动",
                "description": "第一伞齿轮和第二伞齿轮相互啮合",
                "technical_effect": "实现转动方向的改变",
                "importance": "中"
            }
        },
        "technical_problem": "物品变小导致薄膜过多，影响包装质量",
        "technical_solution": "调节两块物料限位板的间距的同时，同步调节两块物料限位板纵向的位置",
        "technical_effects": [
            "能够在调节间距的同时同步调节纵向位置",
            "使之靠近或远离位于前方的成型器",
            "调节方便快速",
            "能够满足实际生产需求"
        ]
    }

    def __init__(self, features_dir: str, relevance_file: str, markdown_dir: str, output_dir: str):
        self.features_dir = Path(features_dir)
        self.relevance_file = Path(relevance_file)
        self.markdown_dir = Path(markdown_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 加载相关性分析结果
        with open(self.relevance_file, 'r', encoding='utf-8') as f:
            self.relevance_data = json.load(f)

        # 获取Top候选专利
        self.top_candidates = [p for p in self.relevance_data if p['patent_number'] != self.TARGET_PATENT['patent_number']][:10]

    def extract_claims_analysis(self, patent_number: str) -> Dict[str, Any]:
        """深度分析权利要求"""
        feature_file = self.features_dir / f"{patent_number}_features.json"

        if not feature_file.exists():
            return {"error": "特征文件不存在"}

        with open(feature_file, 'r', encoding='utf-8') as f:
            patent_data = json.load(f)

        sections = patent_data.get("sections", {})
        claims_text = sections.get("claims", "")
        detailed_text = sections.get("detailed_description", "")
        summary_text = sections.get("summary", "")

        # 提取独立权利要求
        independent_claim = self._extract_independent_claim(claims_text)

        # 提取从属权利要求
        dependent_claims = self._extract_dependent_claims(claims_text)

        # 提取技术方案要素
        technical_elements = self._extract_technical_elements(claims_text + detailed_text)

        # 提取技术问题
        technical_problem = self._extract_technical_problem(summary_text + detailed_text)

        # 提取技术效果
        technical_effects = self._extract_technical_effects(summary_text)

        return {
            "independent_claim": independent_claim,
            "dependent_claims": dependent_claims,
            "technical_elements": technical_elements,
            "technical_problem": technical_problem,
            "technical_effects": technical_effects,
            "full_text_length": len(claims_text)
        }

    def _extract_independent_claim(self, claims_text: str) -> str:
        """提取独立权利要求"""
        # 查找权利要求1
        patterns = [
            r'1[．.][\s\S]{100,2000}?=(?=\n2[．.]|\n$)',
            r'1[．.][\s\S]{100,2000}?=(?=\n根据权利要求|\(19\)|权[　]利[　]要[　]求)',
            r'1[．.][^。]{50,}(?:[。]|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, claims_text)
            if match:
                claim = match.group(0).strip()
                # 清理
                claim = re.sub(r'^1[．.]\s*', '', claim)
                return claim[:500]  # 限制长度

        return "无法提取独立权利要求"

    def _extract_dependent_claims(self, claims_text: str) -> List[str]:
        """提取从属权利要求"""
        claims = []
        lines = claims_text.split('\n')

        for line in lines:
            line = line.strip()
            # 匹配从属权利要求格式
            if re.match(r'^\d+[．.]\s*(?:根据)?', line) and not line.startswith('1'):
                if len(line) > 20:  # 过滤太短的行
                    claims.append(line[:200])

        return claims[:5]  # 最多返回5个从属权利要求

    def _extract_technical_elements(self, text: str) -> List[str]:
        """提取技术方案要素"""
        elements = []

        # 常见技术要素模式
        patterns = [
            r'包括[^。；]{10,60}',
            r'设有[^。；]{10,60}',
            r'安装有[^。；]{10,60}',
            r'连接有[^。；]{10,60}',
            r'[其其中所述][^。；]{10,60}'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) > 15 and '包括' in match or '设有' in match or '安装' in match:
                    elements.append(match.strip())

        return list(set(elements))[:15]  # 去重并限制数量

    def _extract_technical_problem(self, text: str) -> str:
        """提取技术问题"""
        patterns = [
            r'技术问题[：:]\s*([^\n]+)',
            r'所要解决[^\n]{20,100}',
            r'针对[^\n]{20,100}问题',
            r'存在的问题[：:]\s*[^\n]{10,100}'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip() if match.groups() else match.group(0).strip()

        return "未明确描述"

    def _extract_technical_effects(self, text: str) -> List[str]:
        """提取技术效果"""
        effects = []

        patterns = [
            r'有益效果[：:][^\n]{10,200}',
            r'优点[：:][^\n]{10,200}',
            r'优势[：:][^\n]{10,200}',
            r'能够[^\n]{10,100}',
            r'实现[^\n]{10,100}'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            effects.extend(matches)

        return list(set(effects))[:8]  # 去重并限制数量

    def compare_features(self, candidate_patent_number: str) -> Dict[str, Any]:
        """对比目标专利与候选专利的技术特征"""
        # 获取候选专利的深度分析
        candidate_analysis = self.extract_claims_analysis(candidate_patent_number)

        if "error" in candidate_analysis:
            return {"error": candidate_analysis["error"]}

        # 特征对比
        feature_comparison = {}

        for feature_key, feature_info in self.TARGET_PATENT["core_features"].items():
            target_feature = feature_info["description"]
            target_name = feature_info["name"]

            # 检查候选专利是否包含该特征
            candidate_text = (
                candidate_analysis.get("independent_claim", "") +
                " ".join(candidate_analysis.get("dependent_claims", [])) +
                " ".join(candidate_analysis.get("technical_elements", []))
            )

            # 判断是否包含
            is_present = self._check_feature_presence(target_feature, candidate_text)

            # 计算相似度
            similarity = self._calculate_feature_similarity(target_feature, candidate_text)

            feature_comparison[feature_key] = {
                "name": target_name,
                "target_feature": target_feature,
                "is_present": is_present,
                "similarity": similarity,
                "importance": feature_info["importance"],
                "candidate_evidence": self._extract_relevant_evidence(target_feature, candidate_text)
            }

        # 计算整体特征覆盖率
        total_features = len(feature_comparison)
        covered_features = sum(1 for f in feature_comparison.values() if f["is_present"])

        return {
            "patent_number": candidate_patent_number,
            "feature_comparison": feature_comparison,
            "coverage": {
                "total": total_features,
                "covered": covered_features,
                "rate": f"{covered_features/total_features*100:.1f}%"
            },
            "candidate_analysis": candidate_analysis
        }

    def _check_feature_presence(self, target_feature: str, candidate_text: str) -> bool:
        """检查特征是否存在"""
        # 提取关键术语
        key_terms = []

        if "斜向" in target_feature and "滑轨" in target_feature:
            key_terms.append("斜向滑轨")
        if "间距" in target_feature and "渐变" in target_feature:
            key_terms.append("间距渐变")
        if "纵向" in target_feature and "调节" in target_feature:
            key_terms.append("纵向调节")
        if "联动" in target_feature:
            key_terms.append("联动")
        if "驱动" in target_feature:
            key_terms.append("驱动")

        # 检查关键术语是否存在
        for term in key_terms:
            if term in candidate_text:
                return True

        return False

    def _calculate_feature_similarity(self, target_feature: str, candidate_text: str) -> float:
        """计算特征相似度"""
        # 简单的关键词重叠度计算
        target_words = set(target_feature)
        candidate_words_lower = candidate_text.lower()

        match_count = 0
        for word in target_words:
            if word in candidate_words_lower:
                match_count += 1

        return min(match_count / len(target_words) * 100, 100) if target_words else 0

    def _extract_relevant_evidence(self, target_feature: str, candidate_text: str) -> str:
        """提取相关证据片段"""
        # 找到包含相关关键词的句子
        sentences = re.split(r'[。；；\n]', candidate_text)

        key_terms = []
        if "斜向" in target_feature:
            key_terms.append("斜向")
        if "滑轨" in target_feature:
            key_terms.append("滑轨")
        if "间距" in target_feature:
            key_terms.append("间距")
        if "联动" in target_feature:
            key_terms.append("联动")

        for sentence in sentences:
            if any(term in sentence for term in key_terms) and len(sentence) > 10:
                return sentence.strip()[:100]

        return "未找到相关描述"

    def generate_comparison_matrix(self) -> str:
        """生成特征对比矩阵"""
        matrix = "\n## 技术特征对比矩阵\n\n"
        matrix += "| 特征 | 目标专利CN210456236U |"

        # 添加候选专利列头
        for i, candidate in enumerate(self.top_candidates[:5], 1):
            matrix += f" {candidate['patent_number']} |"

        matrix += "\n|" + "|".join(["------"] * (7)) + "|\n"
        matrix += "| 特征名称 | 描述 |"

        for candidate in self.top_candidates[:5]:
            matrix += f" 覆盖 |"

        matrix += "\n|" + "|".join(["------"] * (7)) + "|\n"

        # 添加各特征行
        for feature_key in ["F1", "F2", "F3", "F4", "F5"]:
            feature_info = self.TARGET_PATENT["core_features"][feature_key]
            matrix += f"| **{feature_key}** | {feature_info['name']} |"

            for candidate in self.top_candidates[:5]:
                comparison = self.compare_features(candidate['patent_number'])
                if "error" not in comparison:
                    is_covered = comparison["feature_comparison"][feature_key]["is_present"]
                    matrix += f" {'✅' if is_covered else '❌'} |"
                else:
                    matrix += f" ❓ |"

            matrix += "\n"

        return matrix

    def generate_detailed_report(self) -> str:
        """生成详细对比报告"""
        report = f"""# 专利深度技术对比分析报告

## 分析说明

本报告对Top 10候选专利进行深度技术对比分析，与目标专利CN210456236U的技术特征逐项对比。

**目标专利**: CN210456236U - 包装机物品传送装置的物料限位板自动调节机构
**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**对比专利数**: {len(self.top_candidates)}篇

---

## 目标专利技术特征分解

### 独立权利要求结构

**前序部分**:
- 包括机架
- 两块可滑动地安装在机架上的物料限位板
- 机架具有物料传送带安装空间
- 两块物料限位板分别位于安装空间两侧

**特征部分**:
- 包括物料限位板斜向间距调节机构
- 斜向间距调节机构包括：驱动单元、纵向调节单元、斜向调节单元
- 斜向调节单元包括：两个安装架、两条斜向滑轨、两个滑动座
- **核心特征**: 两条斜向滑轨的间距从左往右逐渐缩短

### 五大核心特征

| 特征代码 | 名称 | 重要性 | 技术效果 |
|----------|------|--------|----------|
| F1 | 斜向滑轨间距渐变 | 最高 | 实现纵向运动时同步改变间距 |
| F2 | 纵向调节单元 | 高 | 带动物料限位板纵向运动 |
| F3 | 驱动单元 | 高 | 提供驱动力 |
| F4 | 滑动轴反向延伸 | 中 | 实现横向纵向解耦 |
| F5 | 伞齿轮传动 | 中 | 改变转动方向 |

---

{self.generate_comparison_matrix()}

---

## Top 10候选专利详细分析

"""

        for i, candidate in enumerate(self.top_candidates, 1):
            patent_number = candidate['patent_number']
            relevance_score = candidate['scores']['overall']

            report += self._generate_candidate_section(i, patent_number, relevance_score)

        return report

    def _generate_candidate_section(self, rank: int, patent_number: str, relevance_score: float) -> str:
        """生成单个候选专利的分析部分"""
        comparison = self.compare_features(patent_number)

        if "error" in comparison:
            return f"\n### {rank}. {patent_number} - 分析失败\n\n{comparison['error']}\n\n"

        candidate_analysis = comparison["candidate_analysis"]

        section = f"""
### {rank}. {patent_number} - 相关性得分: {relevance_score}%

#### 基本信息

| 项目 | 内容 |
|------|------|
| **特征覆盖率** | {comparison['coverage']['rate']} ({comparison['coverage']['covered']}/{comparison['coverage']['total']}) |
| **技术问题** | {candidate_analysis.get('technical_problem', '未提取')} |
| **权利要求数** | {len(candidate_analysis.get('dependent_claims', [])) + 1} |

#### 独立权利要求摘要

{candidate_analysis.get('independent_claim', '无法提取')[:300]}...

#### 技术特征对比

| 特征 | 目标专利 | 候选专利 | 对比结果 |
|------|----------|----------|----------|
"""

        # 添加特征对比行
        for feature_key, feature_data in comparison["feature_comparison"].items():
            status = "✅ 公开" if feature_data["is_present"] else "❌ 未公开"
            similarity = feature_data["similarity"]
            evidence = feature_data["candidate_evidence"][:50] if feature_data["candidate_evidence"] else "无"

            section += f"| {feature_data['name']} | {feature_data['target_feature'][:30]} | {evidence} | {status} (相似度:{similarity:.0f}%) |\n"

        section += f"\n#### 技术效果\n\n"

        effects = candidate_analysis.get('technical_effects', [])
        if effects:
            for effect in effects[:5]:
                section += f"- {effect}\n"
        else:
            section += "- 未明确描述\n"

        section += "\n#### 证据评估\n\n"

        # 评估证据价值
        coverage_rate = float(comparison['coverage']['rate'].rstrip('%'))
        if coverage_rate >= 60:
            assessment = "**高价值证据** - 覆盖了大部分技术特征，可作为主证据使用"
        elif coverage_rate >= 40:
            assessment = "**中等价值证据** - 覆盖了部分技术特征，建议作为补充证据"
        elif coverage_rate >= 20:
            assessment = "**低价值证据** - 仅覆盖少数技术特征，可用于组合证据"
        else:
            assessment = "**极低价值证据** - 基本未覆盖核心技术特征"

        section += f"{assessment}\n\n"
        section += "---\n\n"

        return section

    def save_report(self, report: str):
        """保存报告"""
        # 保存Markdown
        md_path = self.output_dir / "deep_comparison_report.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✅ 深度对比报告已保存: {md_path}")

        # 同时保存JSON数据
        json_data = {
            "target_patent": self.TARGET_PATENT,
            "top_candidates": self.top_candidates,
            "analysis_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        json_path = self.output_dir / "deep_comparison_data.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 对比数据已保存: {json_path}")


import re

def main():
    """主函数"""
    # 配置路径
    features_dir = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/专利提取结果/features"
    relevance_file = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/相关性分析结果/relevance_analysis.json"
    markdown_dir = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/专利提取结果/markdown"
    output_dir = "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/深度对比结果"

    # 创建分析器
    comparator = PatentDeepComparator(features_dir, relevance_file, markdown_dir, output_dir)

    print("\n🔬 开始深度技术对比分析...")
    print(f"   分析候选专利数: {len(comparator.top_candidates)}")

    # 生成详细报告
    report = comparator.generate_detailed_report()

    # 保存报告
    comparator.save_report(report)

    print("\n" + "=" * 60)
    print("📊 深度对比分析完成！")
    print("=" * 60)

    # 输出摘要
    print("\n特征覆盖率摘要:")
    for i, candidate in enumerate(comparator.top_candidates[:5], 1):
        comparison = comparator.compare_features(candidate['patent_number'])
        if "error" not in comparison:
            print(f"  {i}. {candidate['patent_number']}: {comparison['coverage']['rate']} 特征覆盖")


if __name__ == "__main__":
    main()
