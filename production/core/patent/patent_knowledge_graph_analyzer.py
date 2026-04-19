from __future__ import annotations
"""
专利知识图谱分析器 - 集成增强检索模块
结合知识图谱技术和专利检索,实现高质量的专利分析

核心功能:
1. 自动从专利文本提取技术三元组
2. 构建文档间技术关系网络
3. 自动化新颖性/创造性分析
4. 生成可视化分析报告

作者:Athena平台团队
版本:1.0.0
日期:2026-01-07
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# 导入增强检索模块
from core.patent.enhanced_patent_retriever_v2 import EnhancedPatentRetriever, PatentInfo

# 导入知识图谱模块
from core.patent.patent_knowledge_graph import (
    FeatureRelation,
    PatentKnowledgeGraph,
    RelationType,
    TechnicalTriple,
)


@dataclass
class PatentTextAnalysis:
    """专利文本分析结果"""

    application_number: str
    patent_name: str
    abstract: str | None = None
    claims_content: str | None = None
    extracted_problems: list[str] | None = None
    extracted_features: list[str] | None = None
    extracted_effects: list[str] | None = None

    def __post_init__(self):
        if self.extracted_problems is None:
            self.extracted_problems = []
        if self.extracted_features is None:
            self.extracted_features = []
        if self.extracted_effects is None:
            self.extracted_effects = []


class PatentKnowledgeGraphAnalyzer:
    """
    专利知识图谱分析器

    集成功能:
    1. 专利文本自动解析和信息提取
    2. 技术三元组自动构建
    3. 基于知识图谱的对比分析
    4. 智能新颖性/创造性评估
    """

    def __init__(self):
        """初始化分析器"""
        self.kg = PatentKnowledgeGraph()
        self.retriever = EnhancedPatentRetriever()

        # 技术问题关键词模式
        self.problem_patterns = [
            r"解决.*?(?:问题|缺陷|不足|困难)",
            r"避免.*?(?:污染|泄漏|混合|干扰)",
            r"防止.*?(?:问题|缺陷|故障)",
            r"克服.*?(?:技术难题|技术瓶颈)",
            r"现有技术.*?(?:存在.*?问题|具有.*?缺陷)",
        ]

        # 技术效果关键词模式
        self.effect_patterns = [
            r"(?:能够|可以)?(?:实现|达到|获得).*?(?:效果|目的)",
            r"(?:提高|改善|增强|优化).*?(?:性能|质量|效率)",
            r"(?:降低|减少|节约).*?(?:成本|能耗|时间)",
            r"(?:延长|增加).*?(?:寿命|使用时间)",
            r"(?:简化|方便|便于).*?(?:操作|使用|维护)",
        ]

    def __enter__(self):
        """上下文管理器入口"""
        self.retriever.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.retriever.close()

    # ==================== 文档分析功能 ====================

    def analyze_patent_from_database(
        self, application_number: str, auto_extract: bool = True
    ) -> dict | None:
        """
        从数据库读取专利并分析

        Args:
            application_number: 申请号
            auto_extract: 是否自动提取技术要素

        Returns:
            分析结果字典
        """
        # 从数据库检索专利
        patent_info = self.retriever.search_by_application_number(application_number)

        if not patent_info:
            print(f"未找到专利: {application_number}")
            return None

        return self.analyze_patent_from_info(patent_info, auto_extract)

    def analyze_patent_from_info(self, patent_info: PatentInfo, auto_extract: bool = True) -> dict:
        """
        从PatentInfo对象分析专利

        Args:
            patent_info: 专利信息对象
            auto_extract: 是否自动提取技术要素

        Returns:
            分析结果字典
        """
        print(f"\n分析专利: {patent_info.patent_name}")
        print(f"申请号: {patent_info.application_number}")

        # 自动提取技术要素
        if auto_extract:
            problems, features, effects = self._extract_technical_elements(patent_info)
        else:
            problems, features, effects = [], [], []

        # 构建技术三元组
        triples = self._build_triples(
            patent_info.application_number, problems, features, effects, patent_info.claims_content
        )

        # 提取特征关系
        feature_relations = self._extract_feature_relations(patent_info.abstract or "", features)

        # 添加到知识图谱
        analysis = self.kg.analyze_document(
            document_id=patent_info.application_number,
            document_name=patent_info.patent_name,
            triples=triples,
            feature_relations=feature_relations,
            ipc_classifications=(
                [patent_info.ipc_classification] if patent_info.ipc_classification else []
            ),
            document_type=patent_info.patent_type,
        )

        return {
            "patent_info": patent_info,
            "extracted_problems": problems,
            "extracted_features": features,
            "extracted_effects": effects,
            "triples": triples,
            "feature_relations": feature_relations,
            "kg_analysis": analysis,
        }

    def _extract_technical_elements(
        self, patent_info: PatentInfo
    ) -> tuple[list[str], list[str], list[str]]:
        """
        从专利文本中提取技术要素

        提取策略:
        1. 从摘要中提取主要技术问题和效果
        2. 从权利要求书中提取技术特征
        3. 从说明书标题中提取关键信息
        """
        problems = set()
        features = set()
        effects = set()

        # 1. 分析摘要
        if patent_info.abstract:
            abstract_problems, abstract_features, abstract_effects = self._analyze_text(
                patent_info.abstract
            )
            problems.update(abstract_problems)
            features.update(abstract_features)
            effects.update(abstract_effects)

        # 2. 分析权利要求书
        if patent_info.claims_content:
            claims_features = self._extract_features_from_claims(patent_info.claims_content)
            features.update(claims_features)

        # 3. 从专利名称提取特征
        if patent_info.patent_name:
            name_features = self._extract_features_from_name(patent_info.patent_name)
            features.update(name_features)

        return list(problems), list(features), list(effects)

    def _analyze_text(self, text: str) -> tuple[set, set, set]:
        """分析文本提取问题、特征、效果"""
        problems = set()
        features = set()
        effects = set()

        # 提取技术问题
        for pattern in self.problem_patterns:
            matches = re.findall(pattern, text)
            problems.update(matches)

        # 提取技术效果
        for pattern in self.effect_patterns:
            matches = re.findall(pattern, text)
            effects.update(matches)

        # 提取技术特征(名词短语)
        # 简单策略:提取包含技术词汇的名词短语
        feature_patterns = [
            r"([^,。;!?\s]{2,8})(?:装置|机构|结构|组件|部件|元件|部分|区域|位置)",
            r"(?:设置|配置|安装|配备)([^,。;!?\s]{2,12})",
            r"([^,。;!?\s]{2,8})(?:孔|槽|通道|腔|室|臂|板|件|层)",
        ]

        for pattern in feature_patterns:
            matches = re.findall(pattern, text)
            features.update(matches)

        return problems, features, effects

    def _extract_features_from_claims(self, claims_text: str) -> list[str]:
        """从权利要求书中提取技术特征"""
        features = set()

        # 分割权利要求
        claims = re.split(r"\d+\.\s*", claims_text)
        claims = [c.strip() for c in claims if c.strip()]

        for claim in claims[:5]:  # 只分析前5个权利要求
            # 提取关键特征
            # 1. 包括/包含特征
            include_matches = re.findall(r"(?:包括|包含|设有|配置)[^,。;!?]{2,20}", claim)
            features.update(include_matches)

            # 2. 其中/所述特征
            where_matches = re.findall(r"(?:其中|所述)[^,。;!?]{2,15}", claim)
            features.update(where_matches)

        return list(features)

    def _extract_features_from_name(self, patent_name: str) -> list[str]:
        """从专利名称提取特征"""
        features = []

        # 提取主要技术对象
        # 示例:"一种色带盒及打印机" -> "色带盒", "打印机"
        main_objects = re.findall(r"一种(.+?)(?:及|和|的|.?$)", patent_name)

        for obj in main_objects:
            if obj:
                features.append(obj.strip())

        return features

    def _build_triples(
        self,
        doc_id: str,
        problems: list[str],
        features: list[str],
        effects: list[str],
        claims_text: str | None = None,
    ) -> list[TechnicalTriple]:
        """构建技术三元组"""
        triples = []

        # 如果没有明确的问题和效果,构建通用三元组
        if not problems:
            problems = ["现有技术存在的问题"]

        if not effects:
            effects = ["达到技术效果"]

        # 为每个问题-效果对构建三元组
        for i, (problem, effect) in enumerate(
            zip(problems, effects or [effects[0] if effects else ""], strict=False)
        ):
            # 选择相关特征
            selected_features = features[:5] if features else ["技术特征"]

            triple = TechnicalTriple(
                problem=problem, features=selected_features, effect=effect, source_claim=i + 1
            )
            triples.append(triple)

        # 如果没有三元组,创建默认的
        if not triples and features:
            triples.append(
                TechnicalTriple(
                    problem="技术问题", features=features[:5], effect="技术效果", source_claim=1
                )
            )

        return triples

    def _extract_feature_relations(self, text: str, features: list[str]) -> list[FeatureRelation]:
        """提取特征之间的关系"""
        relations = []

        # 简单策略:查找文本中的连接词
        if not features or len(features) < 2:
            return relations

        # 查找组合关系
        combined_patterns = [
            r"([^,。]{2,8})和([^,。]{2,8})组合",
            r"([^,。]{2,8})与([^,。]{2,8})配合",
        ]

        for pattern in combined_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 2:
                    relations.append(
                        FeatureRelation(
                            source_feature=match[0],
                            target_feature=match[1],
                            relation_type=RelationType.COMBINED_WITH,
                            description=f"{match[0]}与{match[1]}组合使用",
                        )
                    )

        return relations

    # ==================== 对比分析功能 ====================

    def compare_with_prior_art(
        self,
        target_application_number: str,
        prior_art_numbers: list[str],
        similarity_threshold: float = 0.3,
    ) -> dict:
        """
        与现有技术进行对比分析

        Args:
            target_application_number: 目标专利申请号
            prior_art_numbers: 现有技术专利号列表
            similarity_threshold: 相似度阈值

        Returns:
            对比分析结果
        """
        print("\n开始对比分析...")
        print(f"目标专利: {target_application_number}")
        print(f"对比文献: {len(prior_art_numbers)} 件")

        # 分析目标专利
        target_analysis = self.analyze_patent_from_database(target_application_number)

        if not target_analysis:
            return {"error": "无法分析目标专利"}

        # 分析所有现有技术
        prior_analyses = []
        for prior_num in prior_art_numbers:
            prior_analysis = self.analyze_patent_from_database(prior_num)
            if prior_analysis:
                prior_analyses.append(prior_analysis)

        if not prior_analyses:
            return {"error": "无法分析现有技术"}

        # 执行对比分析
        comparison_results = []
        for prior_analysis in prior_analyses:
            prior_num = prior_analysis["patent_info"].application_number
            try:
                comparison = self.kg.compare_documents(
                    target_application_number, prior_num, similarity_threshold
                )
                comparison_results.append(comparison)
            except Exception as e:
                print(f"对比 {prior_num} 时出错: {e}")
                continue

        # 汇总结果
        return {
            "target_patent": {
                "application_number": target_application_number,
                "patent_name": target_analysis["patent_info"].patent_name,
                "features_count": len(target_analysis["extracted_features"]),
                "problems_count": len(target_analysis["extracted_problems"]),
            },
            "prior_art_count": len(prior_analyses),
            "comparisons": comparison_results,
            "overall_assessment": self._generate_overall_assessment(comparison_results),
        }

    def _generate_overall_assessment(self, comparisons: list[dict]) -> dict:
        """生成整体评估"""
        if not comparisons:
            return {
                "novelty": "无法判断",
                "inventiveness": "无法判断",
                "recommendation": "需要更多对比文献",
            }

        # 统计新颖性
        novelty_high = sum(1 for c in comparisons if c["novelty_analysis"]["novelty_level"] == "高")
        novelty_low = sum(1 for c in comparisons if c["novelty_analysis"]["novelty_level"] == "低")

        # 统计创造性
        inventiveness_high = sum(
            1 for c in comparisons if c["inventiveness_analysis"]["inventiveness_level"] == "高"
        )

        # 判断
        novelty = (
            "高" if novelty_high >= len(comparisons) * 0.7 else "中" if novelty_low == 0 else "低"
        )
        inventiveness = "高" if inventiveness_high >= len(comparisons) * 0.5 else "中"

        return {
            "novelty": novelty,
            "inventiveness": inventiveness,
            "novelty_high_count": novelty_high,
            "inventiveness_high_count": inventiveness_high,
            "total_comparisons": len(comparisons),
            "recommendation": (
                "专利具有较好的授权前景"
                if novelty == "高" and inventiveness == "高"
                else "需要进一步分析区别技术特征"
            ),
        }

    # ==================== 批量分析功能 ====================

    def batch_analyze_from_search(
        self, keywords: list[str], target_application_number: str, limit: int = 10
    ) -> dict:
        """
        从检索结果批量分析对比文献

        Args:
            keywords: 检索关键词
            target_application_number: 目标专利申请号
            limit: 检索数量限制

        Returns:
            批量分析结果
        """
        print("\n执行批量检索分析...")
        print(f"关键词: {', '.join(keywords)}")

        # 检索相关专利
        patents = self.retriever.search_by_keywords(
            keywords=keywords, limit=limit, require_publication_number=True
        )

        if not patents:
            return {"error": "未检索到相关专利"}

        print(f"检索到 {len(patents)} 件专利")

        # 筛选排除目标专利本身
        prior_art_numbers = [
            p.application_number
            for p in patents
            if p.application_number != target_application_number
        ]

        # 执行对比分析
        return self.compare_with_prior_art(target_application_number, prior_art_numbers)

    # ==================== 导出和可视化 ====================

    def export_analysis_report(self, comparison_result: dict, output_path: str):
        """导出分析报告"""
        report = {
            "metadata": {
                "analyzer": "PatentKnowledgeGraphAnalyzer",
                "version": "1.0.0",
                "target_patent": comparison_result.get("target_patent", {}),
                "prior_art_count": comparison_result.get("prior_art_count", 0),
            },
            "overall_assessment": comparison_result.get("overall_assessment", {}),
            "detailed_comparisons": comparison_result.get("comparisons", []),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"分析报告已导出: {output_path}")

    def visualize_all_comparisons(self, target_application_number: str, output_dir: str = "/tmp"):
        """可视化所有对比图谱"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 获取所有文档ID
        doc_ids = list(self.kg.document_analyses.keys())

        for doc_id in doc_ids:
            if doc_id != target_application_number:
                fig_path = output_path / f"comparison_{target_application_number}_vs_{doc_id}.png"
                self.kg.visualize_comparison(target_application_number, doc_id, str(fig_path))

        print(f"对比图谱已导出到: {output_dir}")

    def print_kg_summary(self) -> Any:
        """打印知识图谱摘要"""
        self.kg.print_summary()


# ==================== 使用示例 ====================


def example_usage() -> Any:
    """使用示例"""

    with PatentKnowledgeGraphAnalyzer() as analyzer:
        # 场景1:分析单件专利
        print("=" * 60)
        print("场景1:分析单件专利")
        print("=" * 60)

        result = analyzer.analyze_patent_from_database("CN217373946U")
        if result:
            print("✅ 成功分析专利")
            print(f"   提取问题: {len(result['extracted_problems'])} 个")
            print(f"   提取特征: {len(result['extracted_features'])} 个")
            print(f"   提取效果: {len(result['extracted_effects'])} 个")
            print(f"   构建三元组: {len(result['triples'])} 个")

        # 场景2:与现有技术对比
        print("\n" + "=" * 60)
        print("场景2:与现有技术对比")
        print("=" * 60)

        comparison = analyzer.compare_with_prior_art(
            target_application_number="CN217373946U",
            prior_art_numbers=["CN97207103.2"],
            similarity_threshold=0.3,
        )

        if "error" not in comparison:
            print("✅ 对比分析完成")
            assessment = comparison["overall_assessment"]
            print(f"   新颖性: {assessment['novelty']}")
            print(f"   创造性: {assessment['inventiveness']}")
            print(f"   建议: {assessment['recommendation']}")

        # 场景3:从检索结果批量分析
        print("\n" + "=" * 60)
        print("场景3:从检索结果批量分析")
        print("=" * 60)

        batch_result = analyzer.batch_analyze_from_search(
            keywords=["色带盒", "隔离"], target_application_number="CN217373946U", limit=10
        )

        if "error" not in batch_result:
            print("✅ 批量分析完成")
            print(f"   检索到对比文献: {batch_result['prior_art_count']} 件")

        # 打印知识图谱统计
        print("\n" + "=" * 60)
        print("知识图谱统计")
        print("=" * 60)
        analyzer.print_kg_summary()

        # 导出可视化
        analyzer.visualize_all_comparisons("CN217373946U", output_dir="/tmp/patent_kg_analysis")


if __name__ == "__main__":
    example_usage()
