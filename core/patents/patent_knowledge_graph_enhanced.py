from __future__ import annotations
"""
增强型专利知识图谱分析器
支持PDF、数据库、文本等多种输入格式
定位:现有技术分析的增强工具,而非替代

核心特性:
1. 多格式输入支持(PDF、数据库、文本)
2. 灵活的增强模式(标准/增强/完整)
3. 保留人工分析环节
4. 质量控制和验证机制

作者:Athena平台团队
版本:1.0.0
日期:2026年1月7日
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 导入增强检索模块
from core.patents.enhanced_patent_retriever_v2 import EnhancedPatentRetriever, PatentInfo

# 导入知识图谱核心模块（统一架构）
from core.kg_unified.models.patent import (
    FeatureRelation,
    PatentKnowledgeGraph,
    RelationType,
    TechnicalTriple,
)

# ==================== 输入适配器 ====================


class PatentDocumentInput(ABC):
    """专利文档输入抽象基类"""

    @staticmethod
    @abstractmethod
    def from_input(input_source: str | Path | dict) -> PatentInfo:
        """从输入源创建PatentInfo对象"""
        pass


class PDFInputAdapter(PatentDocumentInput):
    """PDF文件输入适配器"""

    @staticmethod
    def from_input(pdf_path: str | Path) -> PatentInfo | None:
        """
        从PDF文件提取专利信息

        Args:
            pdf_path: PDF文件路径

        Returns:
            PatentInfo对象
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        # 根据文件名提取申请号
        # 示例: CN217373946U.pdf -> CN217373946U
        application_number = pdf_path.stem

        # TODO: 实际PDF解析(需要集成PDF解析库)
        # 这里提供简化版本,假设PDF已解析为文本
        # 实际应用中可以集成:
        # - PyPDF2
        # - PyMuPDF (fitz)
        # - pdfplumber

        print(f"⚠️  PDF解析功能待实现: {pdf_path}")
        print(f"   当前使用文件名作为申请号: {application_number}")

        # 返回基础PatentInfo对象
        return PatentInfo(
            patent_name=f"专利 {application_number}",
            application_number=application_number,
            patent_type="未知",
            publication_number=None,
            abstract=None,
            claims_content=None,
        )


class DatabaseInputAdapter(PatentDocumentInput):
    """数据库输入适配器"""

    def __init__(self):
        self.retriever = EnhancedPatentRetriever()

    def from_input(self, application_number: str) -> PatentInfo | None:
        """
        从数据库查询专利信息

        Args:
            application_number: 申请号

        Returns:
            PatentInfo对象
        """
        # 连接数据库
        self.retriever.connect()

        try:
            # 查询专利
            patent_info = self.retriever.search_by_application_number(application_number)
            return patent_info
        finally:
            self.retriever.close()


class TextInputAdapter(PatentDocumentInput):
    """文本输入适配器"""

    @staticmethod
    def from_input(text_input: str | dict) -> PatentInfo | None:
        """
        从文本输入创建专利信息

        Args:
            text_input: 文本内容或包含专利信息的字典

        Returns:
            PatentInfo对象
        """
        if isinstance(text_input, dict):
            # 从字典构建
            return PatentInfo(
                patent_name=text_input.get("patent_name", ""),
                application_number=text_input.get("application_number", ""),
                patent_type=text_input.get("patent_type", "未知"),
                publication_number=text_input.get("publication_number"),
                abstract=text_input.get("abstract"),
                claims_content=text_input.get("claims_content"),
            )
        else:
            # 从纯文本解析(简化版)
            # TODO: 实现智能文本解析
            lines = text_input.strip().split("\n")

            return PatentInfo(
                patent_name=lines[0] if lines else "", application_number="", patent_type="未知"
            )


# ==================== 增强分析器 ====================


@dataclass
class AnalysisResult:
    """分析结果"""

    patent_info: PatentInfo

    # 标准分析结果
    standard_features: list[str] = field(default_factory=list)
    standard_problems: list[str] = field(default_factory=list)
    standard_effects: list[str] = field(default_factory=list)

    # 知识图谱增强结果
    kg_triples: list[TechnicalTriple] = field(default_factory=list)
    kg_feature_relations: list[FeatureRelation] = field(default_factory=list)

    # 对比分析结果
    comparison_results: list[dict] = field(default_factory=list)

    # 量化指标
    novelty_score: float | None = None
    inventiveness_score: float | None = None

    # 质量指标
    confidence_level: float = 0.8  # 置信度
    coverage_rate: float = 0.9  # 覆盖率(相对于人工分析)


class EnhancedPatentAnalyzer:
    """
    增强型专利分析器

    核心理念:
    - 传统人工分析为主(核心)
    - 知识图谱分析为辅(增强)
    - 保留人工判断环节
    - 提供量化指标和可视化支持
    """

    def __init__(self, use_kg: bool = True, auto_adapt: bool = True):
        """
        Args:
            use_kg: 是否启用知识图谱增强
            auto_adapt: 是否自动适配输入格式
        """
        self.use_kg = use_kg
        self.auto_adapt = auto_adapt

        # 知识图谱实例
        self.kg = PatentKnowledgeGraph() if use_kg else None

        # 输入适配器
        self.adapters = {
            "pdf": PDFInputAdapter(),
            "database": DatabaseInputAdapter(),
            "text": TextInputAdapter(),
        }

    # ==================== 输入处理 ====================

    def _adapt_input(self, input_source: str | Path | dict) -> PatentInfo | None:
        """
        自动适配输入格式

        Args:
            input_source: 输入源(文件路径、申请号、或字典)

        Returns:
            PatentInfo对象
        """
        # 字典输入
        if isinstance(input_source, dict):
            return self.adapters["text"].from_input(input_source)

        # 字符串/路径输入
        input_str = str(input_source)

        # PDF文件
        if input_str.endswith(".pdf"):
            return self.adapters["pdf"].from_input(input_str)

        # 申请号(数据库查询)
        elif re.match(r"^CN\d+", input_str):
            return self.adapters["database"].from_input(input_str)

        # 纯文本
        else:
            return self.adapters["text"].from_input(input_str)

    # ==================== 分析功能 ====================

    def analyze_patent(
        self,
        patent_input: str | Path | dict,
        analysis_type: str = "kg_enhanced",
        manual_features: list[str] = None,
    ) -> AnalysisResult | None:
        """
        分析专利

        Args:
            patent_input: 专利输入
                - PDF文件路径: "/path/to/patent.pdf"
                - 申请号: "CN217373946U"
                - 字典: {"patent_name": "...", "abstract": "..."}
            analysis_type: 分析类型
                - "standard": 仅标准分析(传统方法)
                - "kg_enhanced": 知识图谱增强(推荐)
                - "kg_full": 完整知识图谱分析
            manual_features: 人工提取的特征(用于校验和补充)

        Returns:
            AnalysisResult对象
        """
        print(f"\n分析专利: {patent_input}")
        print(f"分析类型: {analysis_type}")

        # 1. 输入适配
        patent_info = self._adapt_input(patent_input)

        if not patent_info:
            print("❌ 无法解析输入")
            return None

        # 2. 标准分析(传统方法)
        print("\n[1/3] 执行标准分析...")
        standard_result = self._standard_analysis(patent_info)

        # 3. 知识图谱增强(可选)
        kg_result = None
        if self.use_kg and analysis_type in ["kg_enhanced", "kg_full"]:
            print("\n[2/3] 执行知识图谱增强分析...")
            kg_result = self._kg_enhanced_analysis(patent_info, manual_features=manual_features)

        # 4. 合并结果
        print("\n[3/3] 合并分析结果...")
        final_result = self._merge_results(patent_info, standard_result, kg_result, analysis_type)

        # 5. 质量验证
        if manual_features and kg_result:
            final_result.confidence_level = self._validate_quality(final_result, manual_features)

        return final_result

    def _standard_analysis(self, patent_info: PatentInfo) -> dict:
        """
        标准分析(传统方法)

        这是人工分析的自动化版本,保留人工分析的专业性
        """
        features = set()
        problems = set()
        effects = set()

        # 从摘要提取
        if patent_info.abstract:
            abstract_problems, abstract_features, abstract_effects = self._analyze_text(
                patent_info.abstract
            )
            problems.update(abstract_problems)
            features.update(abstract_features)
            effects.update(abstract_effects)

        # 从权利要求书提取
        if patent_info.claims_content:
            claims_features = self._extract_features_from_claims(patent_info.claims_content)
            features.update(claims_features)

        # 从专利名称提取
        if patent_info.patent_name:
            name_features = self._extract_features_from_name(patent_info.patent_name)
            features.update(name_features)

        return {"features": list(features), "problems": list(problems), "effects": list(effects)}

    def _kg_enhanced_analysis(
        self, patent_info: PatentInfo, manual_features: list[str] = None
    ) -> dict:
        """
        知识图谱增强分析
        """
        # 1. 自动提取技术要素
        auto_problems, auto_features, auto_effects = self._extract_technical_elements(patent_info)

        # 2. 如果有人工特征,合并并优先使用人工特征
        if manual_features:
            # 合并特征(人工优先)
            all_features = set(manual_features) | set(auto_features)
            print(
                f"   特征合并: 人工{len(manual_features)} + 自动{len(auto_features)} = 总计{len(all_features)}"
            )
        else:
            all_features = set(auto_features)

        # 3. 构建技术三元组
        triples = self._build_triples(
            patent_info.application_number,
            list(auto_problems),
            list(all_features),
            list(auto_effects),
            patent_info.claims_content,
        )

        # 4. 提取特征关系
        feature_relations = self._extract_feature_relations(
            patent_info.abstract or "", list(all_features)
        )

        # 5. 添加到知识图谱
        if self.kg:
            self.kg.analyze_document(
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
            "triples": triples,
            "feature_relations": feature_relations,
            "auto_features": auto_features,
            "all_features": list(all_features),
        }

    def _merge_results(
        self,
        patent_info: PatentInfo,
        standard_result: dict,
        kg_result: dict,
        analysis_type: str,
    ) -> AnalysisResult:
        """合并标准分析和知识图谱分析结果"""

        result = AnalysisResult(patent_info=patent_info)

        # 标准分析结果
        result.standard_features = standard_result["features"]
        result.standard_problems = standard_result["problems"]
        result.standard_effects = standard_result["effects"]

        # 知识图谱结果
        if kg_result:
            result.kg_triples = kg_result["triples"]
            result.kg_feature_relations = kg_result["feature_relations"]

        return result

    def _validate_quality(self, result: AnalysisResult, manual_features: list[str]) -> float:
        """
        验证知识图谱分析质量

        对比自动提取和人工提取的特征,计算置信度
        """
        auto_features = set(result.standard_features)
        manual_set = set(manual_features)

        # 计算覆盖率(自动提取覆盖人工提取的比例)
        if manual_set:
            coverage = len(auto_features & manual_set) / len(manual_set)
            result.coverage_rate = coverage

            # 计算置信度
            confidence = min(coverage * 1.2, 1.0)  # 覆盖率越高,置信度越高
            return confidence

        return 0.8  # 默认置信度

    # ==================== 对比分析 ====================

    def compare_with_prior_art(
        self,
        target_patent_input: str | Path | dict,
        prior_art_inputs: list[str | Path | dict],
        similarity_threshold: float = 0.3,
    ) -> dict | None:
        """
        与现有技术进行对比分析

        Args:
            target_patent_input: 目标专利
            prior_art_inputs: 现有技术列表
            similarity_threshold: 相似度阈值

        Returns:
            对比分析结果
        """
        if not self.kg:
            print("❌ 知识图谱未启用,无法执行对比分析")
            return None

        print("\n开始对比分析...")
        print(f"目标专利: {target_patent_input}")
        print(f"对比文献: {len(prior_art_inputs)} 件")

        # 分析目标专利
        target_result = self.analyze_patent(target_patent_input)
        if not target_result:
            return None

        # 分析现有技术
        prior_results = []
        for prior_input in prior_art_inputs:
            prior_result = self.analyze_patent(prior_input)
            if prior_result:
                prior_results.append(prior_result)

        if not prior_results:
            return {"error": "无法分析现有技术"}

        # 执行对比
        comparison_results = []
        target_id = target_result.patent_info.application_number

        for prior_result in prior_results:
            prior_id = prior_result.patent_info.application_number
            try:
                comparison = self.kg.compare_documents(target_id, prior_id, similarity_threshold)
                comparison_results.append(comparison)
            except Exception as e:
                print(f"对比 {prior_id} 时出错: {e}")
                continue

        return {
            "target_patent": {
                "application_number": target_id,
                "patent_name": target_result.patent_info.patent_name,
                "features_count": len(target_result.standard_features),
            },
            "prior_art_count": len(prior_results),
            "comparisons": comparison_results,
        }

    # ==================== 辅助方法 ====================

    def _analyze_text(self, text: str) -> tuple[set, set, set]:
        """分析文本提取问题、特征、效果"""
        problems = set()
        features = set()
        effects = set()

        # 简化版正则提取
        # TODO: 可以集成NLP模型提升提取质量

        problem_patterns = [
            r"解决.*?(?:问题|缺陷|不足)",
            r"避免.*?(?:污染|泄漏|混合)",
            r"防止.*?(?:问题|故障)",
        ]

        for pattern in problem_patterns:
            matches = re.findall(pattern, text)
            problems.update(matches)

        feature_patterns = [
            r"([^,。]{2,8})(?:装置|机构|结构|组件|部件)",
            r"(?:设置|配置)([^,。]{2,12})",
            r"([^,。]{2,8})(?:孔|槽|通道|腔|室)",
        ]

        for pattern in feature_patterns:
            matches = re.findall(pattern, text)
            features.update(matches)

        effect_patterns = [
            r"(?:能够|可以)?(?:实现|达到)([^,。]{2,15})",
            r"(?:提高|改善|增强)([^,。]{2,10})",
        ]

        for pattern in effect_patterns:
            matches = re.findall(pattern, text)
            effects.update(matches)

        return problems, features, effects

    def _extract_features_from_claims(self, claims_text: str) -> list[str]:
        """从权利要求书提取特征"""
        features = set()

        claims = re.split(r"\d+\.\s*", claims_text)
        claims = [c.strip() for c in claims if c.strip()]

        for claim in claims[:5]:
            include_matches = re.findall(r"(?:包括|包含|设有)([^,。]{2,20})", claim)
            features.update(include_matches)

        return list(features)

    def _extract_features_from_name(self, patent_name: str) -> list[str]:
        """从专利名称提取特征"""
        features = []

        main_objects = re.findall(r"一种(.+?)(?:及|和|的|.?$)", patent_name)

        for obj in main_objects:
            if obj:
                features.append(obj.strip())

        return features

    def _extract_technical_elements(
        self, patent_info: PatentInfo
    ) -> tuple[list[str], list[str], list[str]]:
        """提取技术要素"""
        return self._analyze_text(
            (patent_info.abstract or "") + " " + (patent_info.patent_name or "")
        )

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

        if not problems:
            problems = ["技术问题"]
        if not effects:
            effects = ["技术效果"]
        if not features:
            features = ["技术特征"]

        for i, (problem, effect) in enumerate(zip(problems, effects or [effects[0]], strict=False)):
            selected_features = features[:5] if features else ["技术特征"]

            triple = TechnicalTriple(
                problem=problem, features=selected_features, effect=effect, source_claim=i + 1
            )
            triples.append(triple)

        return triples

    def _extract_feature_relations(self, text: str, features: list[str]) -> list[FeatureRelation]:
        """提取特征关系"""
        relations = []

        if not features or len(features) < 2:
            return relations

        # 简化版:查找组合关系
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

    # ==================== 报告生成 ====================

    def generate_report(
        self,
        analysis_result: AnalysisResult,
        output_format: str = "markdown",
        output_path: str | None = None,
    ) -> str | None:
        """
        生成分析报告

        Args:
            analysis_result: 分析结果
            output_format: 输出格式 ("markdown", "json", "text")
            output_path: 输出文件路径(可选)

        Returns:
            报告内容字符串
        """
        if output_format == "markdown":
            report = self._generate_markdown_report(analysis_result)
        elif output_format == "json":
            report = json.dumps(self._result_to_dict(analysis_result), ensure_ascii=False, indent=2)
        else:
            report = self._generate_text_report(analysis_result)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"✅ 报告已保存: {output_path}")

        return report

    def _generate_markdown_report(self, result: AnalysisResult) -> str:
        """生成Markdown报告"""
        lines = []

        lines.append("# 专利分析报告(知识图谱增强)")
        lines.append("")
        lines.append("## 专利基本信息")
        lines.append("")
        lines.append(f"- **专利名称**: {result.patent_info.patent_name}")
        lines.append(f"- **申请号**: {result.patent_info.application_number}")
        lines.append(f"- **公开号**: {result.patent_info.publication_number or '无'}")
        lines.append("")

        lines.append("## 标准分析(传统方法)")
        lines.append("")
        lines.append(f"### 技术问题 ({len(result.standard_problems)} 个)")
        for i, p in enumerate(result.standard_problems, 1):
            lines.append(f"{i}. {p}")
        lines.append("")

        lines.append(f"### 技术特征 ({len(result.standard_features)} 个)")
        for i, f in enumerate(result.standard_features, 1):
            lines.append(f"{i}. {f}")
        lines.append("")

        lines.append(f"### 技术效果 ({len(result.standard_effects)} 个)")
        for i, e in enumerate(result.standard_effects, 1):
            lines.append(f"{i}. {e}")
        lines.append("")

        if result.kg_triples:
            lines.append("## 知识图谱增强分析")
            lines.append("")
            lines.append(f"### 技术三元组 ({len(result.kg_triples)} 个)")
            for i, triple in enumerate(result.kg_triples, 1):
                lines.append(f"{i}. **问题**: {triple.problem}")
                lines.append(f"   **特征**: {', '.join(triple.features)}")
                lines.append(f"   **效果**: {triple.effect}")
                lines.append("")

        lines.append("## 质量指标")
        lines.append("")
        lines.append(f"- **置信度**: {result.confidence_level:.1%}")
        lines.append(f"- **覆盖率**: {result.coverage_rate:.1%}")
        lines.append("")

        return "\n".join(lines)

    def _generate_text_report(self, result: AnalysisResult) -> str:
        """生成文本报告"""
        lines = []

        lines.append("=" * 60)
        lines.append("专利分析报告(知识图谱增强)")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"专利名称: {result.patent_info.patent_name}")
        lines.append(f"申请号: {result.patent_info.application_number}")
        lines.append("")

        lines.append("技术特征:")
        for i, f in enumerate(result.standard_features, 1):
            lines.append(f"  {i}. {f}")

        lines.append("")
        lines.append(f"置信度: {result.confidence_level:.1%}")
        lines.append(f"覆盖率: {result.coverage_rate:.1%}")

        return "\n".join(lines)

    def _result_to_dict(self, result: AnalysisResult) -> dict:
        """将结果转换为字典"""
        return {
            "patent_info": {
                "patent_name": result.patent_info.patent_name,
                "application_number": result.patent_info.application_number,
                "publication_number": result.patent_info.publication_number,
            },
            "standard_analysis": {
                "features": result.standard_features,
                "problems": result.standard_problems,
                "effects": result.standard_effects,
            },
            "kg_enhancement": {
                "triples": [
                    {"problem": t.problem, "features": t.features, "effect": t.effect}
                    for t in result.kg_triples
                ],
                "feature_relations": [
                    {
                        "source": r.source_feature,
                        "target": r.target_feature,
                        "type": r.relation_type.value,
                    }
                    for r in result.kg_feature_relations
                ],
            },
            "quality_metrics": {
                "confidence_level": result.confidence_level,
                "coverage_rate": result.coverage_rate,
            },
        }

    # ==================== 可视化 ====================

    def visualize(self, analysis_result: AnalysisResult, output_path: str | None = None):
        """可视化分析结果"""
        if not self.kg:
            print("❌ 知识图谱未启用,无法生成可视化")
            return

        if output_path:
            self.kg.visualize_graph(output_path=output_path)
            print(f"✅ 知识图谱已生成: {output_path}")


# ==================== 使用示例 ====================


def example_usage() -> Any:
    """使用示例"""

    # 创建增强分析器
    analyzer = EnhancedPatentAnalyzer(use_kg=True)

    # 示例1:从数据库分析
    print("=" * 60)
    print("示例1:从数据库分析")
    print("=" * 60)

    result1 = analyzer.analyze_patent(patent_input="CN217373946U", analysis_type="kg_enhanced")

    if result1:
        print("\n✅ 分析完成")
        print(f"   特征数: {len(result1.standard_features)}")
        print(f"   三元组数: {len(result1.kg_triples)}")
        print(f"   置信度: {result1.confidence_level:.1%}")

        # 生成报告
        analyzer.generate_report(
            result1, output_format="markdown", output_path="/tmp/CN217373946U_enhanced_analysis.md"
        )

    # 示例2:从PDF文件分析(待实现)
    print("\n" + "=" * 60)
    print("示例2:从PDF文件分析")
    print("=" * 60)

    # result2 = analyzer.analyze_patent(
    #     patent_input="/path/to/CN217373946U.pdf",
    #     analysis_type="kg_enhanced"
    # )

    # 示例3:对比分析
    print("\n" + "=" * 60)
    print("示例3:对比分析")
    print("=" * 60)

    comparison = analyzer.compare_with_prior_art(
        target_patent_input="CN217373946U",
        prior_art_inputs=["CN97207103.2"],
        similarity_threshold=0.3,
    )

    if comparison and "error" not in comparison:
        print("\n✅ 对比分析完成")
        print(f"   对比文献数: {comparison['prior_art_count']}")

        for comp in comparison["comparisons"]:
            print(f"\n   新颖性: {comp['novelty_analysis']['novelty_level']}")
            print(f"   创造性: {comp['inventiveness_analysis']['inventiveness_level']}")

    # 示例4:生成可视化
    if analyzer.kg:
        print("\n" + "=" * 60)
        print("示例4:生成可视化")
        print("=" * 60)

        analyzer.kg.visualize_graph(output_path="/tmp/enhanced_patent_kg.png")
        print("✅ 知识图谱已生成")


if __name__ == "__main__":
    example_usage()
