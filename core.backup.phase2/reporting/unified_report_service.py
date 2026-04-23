#!/usr/bin/env python3
from __future__ import annotations
"""
统一报告服务 (Unified Report Service)

整合Dolphin文档解析、NetworkX技术分析和Athena报告生成的完整工作流。

工作流程:
    1. Dolphin解析: 图片/PDF → 结构化Markdown
    2. NetworkX分析: 技术深度分析 → 知识图谱
    3. Athena生成: AI+模板 → 专业报告
    4. 多格式输出: DOCX/PDF/HTML

Author: Athena工作平台
Date: 2026-01-16
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal

# 导入核心组件
from core.perception.dolphin_client import DolphinDocumentParser
from core.perception.dolphin_networkx_integration import DolphinNetworkXAnalyzer

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """报告类型枚举"""
    PATENT_TECHNICAL_ANALYSIS = "patent_technical_analysis"  # 专利技术分析报告
    PATENT_COMPARISON = "patent_comparison"  # 专利对比报告
    PATENT_PORTFOLIO = "patent_portfolio"  # 专利组合分析
    LEGAL_OPINION = "legal_opinion"  # 法律意见书
    OA_RESPONSE = "oa_response"  # OA答复建议
    TECHNICAL_TRENDS = "technical_trends"  # 技术趋势报告
    DOCUMENT_CONVERSION = "document_conversion"  # 文档转换


class OutputFormat(Enum):
    """输出格式枚举"""
    MARKDOWN = "md"
    DOCX = "docx"
    PDF = "pdf"
    HTML = "html"
    JSON = "json"


@dataclass
class ReportConfig:
    """报告配置"""
    # 解析配置
    enable_dolphin_parsing: bool = True
    enable_networkx_analysis: bool = True
    enable_ai_generation: bool = True

    # Dolphin配置
    dolphin_output_format: Literal["json", "markdown", "both"] = "both"
    dolphin_max_batch_size: int = 8

    # NetworkX配置
    networkx_build_graph: bool = True
    networkx_export_graph: bool = False

    # AI生成配置
    ai_model: str = "gpt-4"
    ai_temperature: float = 0.7
    ai_max_tokens: int = 4096

    # 输出配置
    output_formats: list[OutputFormat] = field(default_factory=lambda: [OutputFormat.MARKDOWN, OutputFormat.DOCX])
    include_original_markdown: bool = True
    include_technical_graph: bool = True
    include_quality_metrics: bool = True


@dataclass
class ReportResult:
    """报告结果"""
    report_type: ReportType
    input_source: str
    output_dir: str

    # 各阶段结果
    dolphin_result: dict | None = None
    networkx_result: dict | None = None
    athena_result: dict | None = None

    # 输出文件
    output_files: dict[str, str] = field(default_factory=dict)

    # 元数据
    generation_time: datetime = field(default_factory=datetime.now)
    processing_time_seconds: float = 0.0
    quality_score: float = 0.0


class UnifiedReportService:
    """
    统一报告服务

    整合Dolphin + NetworkX + Athena的完整报告生成流程。
    """

    def __init__(
        self,
        config: ReportConfig | None = None,
        dolphin_client: DolphinDocumentParser | None = None,
        networkx_analyzer: DolphinNetworkXAnalyzer | None = None,
    ):
        """
        初始化统一报告服务

        Args:
            config: 报告配置
            dolphin_client: Dolphin文档解析客户端
            networkx_analyzer: NetworkX技术分析器
        """
        self.config = config or ReportConfig()

        # 初始化各组件
        self.dolphin_client = dolphin_client or DolphinDocumentParser()
        self.networkx_analyzer = networkx_analyzer or DolphinNetworkXAnalyzer(
            dolphin_client=self.dolphin_client
        )

        logger.info("📋 统一报告服务初始化完成")
        logger.info(f"   - Dolphin解析: {'启用' if self.config.enable_dolphin_parsing else '禁用'}")
        logger.info(f"   - NetworkX分析: {'启用' if self.config.enable_networkx_analysis else '禁用'}")
        logger.info(f"   - AI生成: {'启用' if self.config.enable_ai_generation else '禁用'}")

    async def generate_from_document(
        self,
        document_path: str,
        report_type: ReportType = ReportType.PATENT_TECHNICAL_ANALYSIS,
        output_dir: str | None = None,
        custom_data: dict | None = None,
    ) -> ReportResult:
        """
        从文档生成完整报告

        工作流程:
            1. Dolphin解析文档
            2. NetworkX技术深度分析
            3. Athena AI生成报告
            4. 多格式输出

        Args:
            document_path: 文档路径(图片/PDF)
            report_type: 报告类型
            output_dir: 输出目录
            custom_data: 自定义数据

        Returns:
            ReportResult: 报告结果
        """
        import time
        start_time = time.time()

        logger.info(f"🚀 开始生成报告: {report_type.value}")
        logger.info(f"   输入文档: {document_path}")

        # 创建结果对象
        result = ReportResult(
            report_type=report_type,
            input_source=document_path,
            output_dir=output_dir or self._get_default_output_dir(document_path),
        )

        try:
            # 阶段1: Dolphin文档解析
            if self.config.enable_dolphin_parsing:
                logger.info("📄 阶段1: Dolphin文档解析...")
                result.dolphin_result = await self._dolphin_parse(document_path)
            else:
                logger.info("⏭️  跳过Dolphin解析")
                result.dolphin_result = None

            # 阶段2: NetworkX技术深度分析
            if self.config.enable_networkx_analysis:
                logger.info("🕸️  阶段2: NetworkX技术深度分析...")
                result.networkx_result = await self._networkx_analyze(document_path)
            else:
                logger.info("⏭️  跳过NetworkX分析")
                result.networkx_result = None

            # 阶段3: Athena AI生成报告
            if self.config.enable_ai_generation:
                logger.info("🤖 阶段3: Athena AI生成报告...")
                result.athena_result = await self._athena_generate(
                    report_type,
                    result.dolphin_result,
                    result.networkx_result,
                    custom_data
                )
            else:
                logger.info("⏭️  跳过AI生成")
                result.athena_result = None

            # 阶段4: 多格式输出
            logger.info("💾 阶段4: 多格式输出...")
            await self._export_report(result)

            # 计算处理时间
            result.processing_time_seconds = time.time() - start_time

            # 计算质量分数
            result.quality_score = self._calculate_quality_score(result)

            logger.info("✅ 报告生成完成!")
            logger.info(f"   处理时间: {result.processing_time_seconds:.2f}秒")
            logger.info(f"   质量分数: {result.quality_score:.2f}/100")

        except Exception as e:
            logger.error(f"❌ 报告生成失败: {e}")
            raise

        return result

    async def generate_from_data(
        self,
        data: dict,
        report_type: ReportType,
        output_dir: str | None = None,
    ) -> ReportResult:
        """
        从数据直接生成报告(跳过Dolphin解析和NetworkX分析)

        Args:
            data: 输入数据
            report_type: 报告类型
            output_dir: 输出目录

        Returns:
            ReportResult: 报告结果
        """
        import time
        start_time = time.time()

        logger.info(f"🚀 从数据生成报告: {report_type.value}")

        result = ReportResult(
            report_type=report_type,
            input_source="data_input",
            output_dir=output_dir or self._get_default_output_dir("data_report"),
        )

        try:
            # 直接使用Athena生成
            result.athena_result = await self._athena_generate(
                report_type,
                None,  # 无Dolphin结果
                None,  # 无NetworkX结果
                data
            )

            # 导出报告
            await self._export_report(result)

            result.processing_time_seconds = time.time() - start_time
            result.quality_score = self._calculate_quality_score(result)

            logger.info("✅ 报告生成完成!")
            logger.info(f"   处理时间: {result.processing_time_seconds:.2f}秒")

        except Exception as e:
            logger.error(f"❌ 报告生成失败: {e}")
            raise

        return result

    async def compare_documents(
        self,
        doc1_path: str,
        doc2_path: str,
        output_dir: str | None = None,
    ) -> ReportResult:
        """
        对比两个文档并生成对比报告

        Args:
            doc1_path: 文档1路径
            doc2_path: 文档2路径
            output_dir: 输出目录

        Returns:
            ReportResult: 对比报告结果
        """
        import time
        start_time = time.time()

        logger.info("🔍 对比文档分析")
        logger.info(f"   文档1: {doc1_path}")
        logger.info(f"   文档2: {doc2_path}")

        result = ReportResult(
            report_type=ReportType.PATENT_COMPARISON,
            input_source=f"{doc1_path} vs {doc2_path}",
            output_dir=output_dir or self._get_default_output_dir("comparison"),
        )

        try:
            # 使用NetworkX对比分析
            logger.info("🕸️  执行技术对比分析...")
            comparison = await self.networkx_analyzer.compare_technical_depth(
                doc1_path,
                doc2_path
            )

            result.networkx_result = comparison

            # 生成对比报告
            result.athena_result = await self._athena_generate(
                ReportType.PATENT_COMPARISON,
                None,
                comparison,
                {"doc1_path": doc1_path, "doc2_path": doc2_path}
            )

            # 导出报告
            await self._export_report(result)

            result.processing_time_seconds = time.time() - start_time
            result.quality_score = self._calculate_quality_score(result)

            logger.info("✅ 对比报告生成完成!")

        except Exception as e:
            logger.error(f"❌ 对比报告生成失败: {e}")
            raise

        return result

    async def _dolphin_parse(self, document_path: str) -> dict:
        """Dolphin文档解析"""
        result = await self.dolphin_client.parse_document(
            file_path=document_path,
            output_format=self.config.dolphin_output_format,
            max_batch_size=self.config.dolphin_max_batch_size,
        )

        logger.info(f"✅ Dolphin解析完成: {result.get('file_name', 'unknown')}")

        return result

    async def _networkx_analyze(self, document_path: str) -> dict:
        """NetworkX技术深度分析"""
        result = await self.networkx_analyzer.analyze_patent_technical_depth(
            document_path=document_path,
            build_knowledge_graph=self.config.networkx_build_graph,
        )

        logger.info(f"✅ NetworkX分析完成: {result['entities_count']}个实体, {result['relations_count']}个关系")

        # 导出技术图谱
        if self.config.networkx_export_graph:
            output_dir = Path(result.get('output_dir', '/tmp'))
            graph_path = output_dir / "technical_graph.gexf"
            self.networkx_analyzer.export_technical_graph(str(graph_path), format="gexf")
            logger.info(f"✅ 技术图谱已导出: {graph_path}")

        return result

    async def _athena_generate(
        self,
        report_type: ReportType,
        dolphin_result: dict | None,
        networkx_result: dict | None,
        custom_data: dict | None,
    ) -> dict:
        """Athena AI生成报告"""
        # 准备报告数据
        report_data = self._prepare_report_data(
            report_type,
            dolphin_result,
            networkx_result,
            custom_data
        )

        # 选择报告模板
        template = self._get_report_template(report_type)

        # 渲染报告内容
        markdown_content = self._render_report(template, report_data)

        logger.info(f"✅ Athena报告生成完成: {len(markdown_content)}字符")

        return {
            "markdown_content": markdown_content,
            "report_data": report_data,
            "template_used": template.get("name", "custom"),
        }

    def _prepare_report_data(
        self,
        report_type: ReportType,
        dolphin_result: dict | None,
        networkx_result: dict | None,
        custom_data: dict | None,
    ) -> dict:
        """准备报告数据"""
        data = {
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_type": report_type.value,
            "report_title": self._get_report_title(report_type),
        }

        # 添加Dolphin解析结果
        if dolphin_result:
            data.update({
                "original_markdown": dolphin_result.get("markdown", ""),
                "parse_result": dolphin_result,
            })

        # 添加NetworkX分析结果
        if networkx_result:
            data.update({
                "technical_entities_count": networkx_result.get("entities_count", 0),
                "technical_relations_count": networkx_result.get("relations_count", 0),
                "innovation_points": networkx_result.get("innovations", [])[:10],
                "technical_metrics": networkx_result.get("metrics", {}),
                "evolution_analysis": networkx_result.get("evolution", {}),
                "graph_statistics": networkx_result.get("graph_stats", {}),
            })

        # 添加自定义数据
        if custom_data:
            data.update(custom_data)

        return data

    def _get_report_title(self, report_type: ReportType) -> str:
        """获取报告标题"""
        titles = {
            ReportType.PATENT_TECHNICAL_ANALYSIS: "专利技术深度分析报告",
            ReportType.PATENT_COMPARISON: "专利技术对比分析报告",
            ReportType.PATENT_PORTFOLIO: "专利组合分析报告",
            ReportType.LEGAL_OPINION: "法律意见书",
            ReportType.OA_RESPONSE: "OA答复建议书",
            ReportType.TECHNICAL_TRENDS: "技术趋势分析报告",
            ReportType.DOCUMENT_CONVERSION: "文档转换报告",
        }
        return titles.get(report_type, "分析报告")

    def _get_report_template(self, report_type: ReportType) -> dict:
        """获取报告模板"""
        # 这里返回模板内容
        # 实际实现可以从文件加载或使用数据库
        return {
            "name": report_type.value,
            "sections": self._get_template_sections(report_type),
        }

    def _get_template_sections(self, report_type: ReportType) -> list[str]:
        """获取模板章节"""
        sections = {
            ReportType.PATENT_TECHNICAL_ANALYSIS: [
                "executive_summary",
                "original_content",
                "technical_analysis",
                "innovation_points",
                "importance_assessment",
                "evolution_analysis",
                "comprehensive_evaluation",
                "conclusion",
            ],
            ReportType.PATENT_COMPARISON: [
                "executive_summary",
                "comparison_overview",
                "technical_comparison",
                "innovation_comparison",
                "conclusion",
            ],
        }
        return sections.get(report_type, ["executive_summary", "analysis", "conclusion"])

    def _render_report(self, template: dict, data: dict) -> str:
        """渲染报告内容"""
        # 简化实现:直接生成markdown
        # 实际实现可以使用Jinja2模板引擎
        report_type = data.get("report_type", "analysis")

        if report_type == "patent_technical_analysis":
            return self._render_patent_technical_analysis(data)
        elif report_type == "patent_comparison":
            return self._render_patent_comparison(data)
        else:
            return self._render_generic_report(data)

    def _render_patent_technical_analysis(self, data: dict) -> str:
        """渲染专利技术分析报告"""
        lines = []

        # 标题
        lines.append(f"# {data['report_title']}\n")

        # 生成时间
        lines.append(f"**报告生成时间**: {data['generation_time']}\n")
        lines.append("**分析工具**: Athena工作平台 v2.0 (Dolphin + NetworkX)\n")

        # 1. 执行摘要
        lines.append("## 1. 执行摘要\n")

        # 技术实体统计
        entities_count = data.get("technical_entities_count", 0)
        relations_count = data.get("technical_relations_count", 0)

        lines.append("本报告基于Dolphin高精度文档解析和NetworkX深度技术分析,对专利文档进行了全面的技术分析。")
        lines.append("\n### 1.1 核心数据")
        lines.append(f"\n- **技术实体总数**: {entities_count}个")
        lines.append(f"- **技术关系总数**: {relations_count}个")
        lines.append(f"- **核心创新点**: {len(data.get('innovation_points', []))}个\n")

        # 2. 核心创新点
        lines.append("## 2. 核心创新点\n")

        innovations = data.get("innovation_points", [])
        if innovations:
            lines.append("### 2.1 Top 创新点\n")
            for i, innovation in enumerate(innovations[:5], 1):
                lines.append(f"\n**创新点#{i}**: {innovation.get('text', 'N/A')[:80]}...")
                lines.append(f"\n- **实体类型**: {innovation.get('entity_type', 'N/A')}")
                lines.append(f"- **创新分数**: {innovation.get('innovation_score', 0):.4f}")
                scores = innovation.get('scores', {})
                if scores:
                    lines.append(f"- **PageRank**: {scores.get('pagerank', 0):.4f}")
                    lines.append(f"- **Authority**: {scores.get('authority', 0):.4f}")
                    lines.append(f"- **Betweenness**: {scores.get('betweenness', 0):.4f}")
        else:
            lines.append("未识别到显著创新点。\n")

        # 3. 技术重要性评估
        lines.append("\n## 3. 技术重要性评估\n")

        metrics = data.get("technical_metrics", {})
        if metrics:
            # PageRank分析
            pagerank = metrics.get("pagerank", {})
            if pagerank:
                lines.append("### 3.1 核心技术识别 (PageRank)\n")
                sorted_pr = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
                lines.append("\n| 排名 | 技术实体 | PageRank分数 |")
                lines.append("|------|---------|-------------|")
                for i, (node_id, score) in enumerate(sorted_pr, 1):
                    lines.append(f"| {i} | {node_id} | {score:.4f} |")
                lines.append("")

            # HITS分析
            authorities = metrics.get("authorities", {})
            if authorities:
                lines.append("### 3.2 技术权威性 (HITS Authorities)\n")
                sorted_auth = sorted(authorities.items(), key=lambda x: x[1], reverse=True)[:5]
                lines.append("\n| 排名 | 技术实体 | Authority分数 |")
                lines.append("|------|---------|--------------|")
                for i, (node_id, score) in enumerate(sorted_auth, 1):
                    lines.append(f"| {i} | {node_id} | {score:.4f} |")
                lines.append("")

        # 4. 技术演化路径
        lines.append("\n## 4. 技术演化路径\n")

        evolution = data.get("evolution_analysis", {})
        if evolution:
            chain_length = evolution.get("evolution_chain_length", 0)
            lines.append("### 4.1 演化链分析")
            lines.append(f"\n- **演化链长度**: {chain_length}层")

            longest_path = evolution.get("longest_path", [])
            if longest_path:
                lines.append(f"- **演化路径**: {' → '.join(longest_path[:5])}")
                if len(longest_path) > 5:
                    lines.append(f"  ... (共{len(longest_path)}个节点)")
            lines.append("")

        # 5. 原始文档内容
        if self.config.include_original_markdown and data.get("original_markdown"):
            lines.append("\n## 5. 原始文档内容 (Dolphin解析)\n")
            lines.append("---\n")
            lines.append(data["original_markdown"])
            lines.append("\n---\n")

        # 6. 结论
        lines.append("\n## 6. 结论\n")

        quality_score = self._calculate_quality_score_from_data(data)
        lines.append(f"### 综合评分: {quality_score:.2f}/100\n")

        if quality_score >= 80:
            lines.append("✅ **技术价值高**: 该专利具有显著的技术创新性和实用价值。")
        elif quality_score >= 60:
            lines.append("⚠️ **技术价值中等**: 该专利具有一定的技术创新,但仍有提升空间。")
        else:
            lines.append("❌ **技术价值较低**: 该专利技术创新性有限,建议谨慎评估。")

        lines.append("\n**建议**: 基于Dolphin+NetworkX+Athena的综合分析,建议重点关注核心技术实体的保护和应用。")

        # 页脚
        lines.append("\n---\n")
        lines.append(f"**报告生成时间**: {data['generation_time']}\n")
        lines.append("**分析工具**: Athena工作平台 v2.0\n")
        lines.append("**技术栈**: Dolphin文档解析 + NetworkX图分析 + Athena报告生成\n")

        return "\n".join(lines)

    def _render_patent_comparison(self, data: dict) -> str:
        """渲染专利对比报告"""
        lines = []

        lines.append(f"# {data['report_title']}\n")
        lines.append(f"**报告生成时间**: {data['generation_time']}\n")

        # 对比概述
        comparison = data.get("comparison", {})
        if comparison:
            lines.append("## 1. 对比概述\n")
            lines.append(f"- **复杂度差异**: {comparison.get('complexity_diff', 0)}")
            lines.append(f"- **创新差异**: {comparison.get('innovation_diff', 0)}\n")

        return "\n".join(lines)

    def _render_generic_report(self, data: dict) -> str:
        """渲染通用报告"""
        lines = []

        lines.append(f"# {data['report_title']}\n")
        lines.append(f"**生成时间**: {data['generation_time']}\n")
        lines.append("## 分析内容\n")
        lines.append("报告内容生成中...\n")

        return "\n".join(lines)

    async def _export_report(self, result: ReportResult):
        """导出报告到多种格式"""
        output_dir = Path(result.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = Path(result.input_source).stem or "report"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 导出Markdown
        if OutputFormat.MARKDOWN in self.config.output_formats and result.athena_result:
            md_path = output_dir / f"{base_name}_{timestamp}.md"
            md_content = result.athena_result.get("markdown_content", "")

            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)

            result.output_files["markdown"] = str(md_path)
            logger.info(f"✅ Markdown已导出: {md_path}")

            # 尝试转换为DOCX
            if OutputFormat.DOCX in self.config.output_formats:
                try:
                    docx_path = await self._convert_to_docx(md_path)
                    if docx_path:
                        result.output_files["docx"] = docx_path
                        logger.info(f"✅ DOCX已导出: {docx_path}")
                except Exception as e:
                    logger.warning(f"⚠️  DOCX转换失败: {e}")

        # 导出JSON
        if OutputFormat.JSON in self.config.output_formats:
            json_path = output_dir / f"{base_name}_{timestamp}.json"
            import json

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({
                    "report_type": result.report_type.value,
                    "input_source": result.input_source,
                    "generation_time": result.generation_time.isoformat(),
                    "processing_time_seconds": result.processing_time_seconds,
                    "quality_score": result.quality_score,
                    "dolphin_result": result.dolphin_result,
                    "networkx_result": result.networkx_result,
                    "athena_result": result.athena_result,
                }, f, ensure_ascii=False, indent=2, default=str)

            result.output_files["json"] = str(json_path)
            logger.info(f"✅ JSON已导出: {json_path}")

    async def _convert_to_docx(self, md_path: Path) -> str | None:
        """转换Markdown为DOCX"""
        try:
            # 使用PasteMD核心模块
            from core.document_export.pastemd_core import PasteMDCore

            pastemd = PasteMDCore()
            docx_path = md_path.with_suffix(".docx")

            # 读取markdown内容
            with open(md_path, encoding="utf-8") as f:
                md_content = f.read()

            # 转换为DOCX
            pastemd.markdown_to_docx(md_content, str(docx_path))

            return str(docx_path)

        except Exception as e:
            logger.warning(f"DOCX转换失败: {e}")
            return None

    def _get_default_output_dir(self, input_path: str) -> str:
        """获取默认输出目录"""
        from datetime import datetime

        base_dir = Path("/Users/xujian/Athena工作平台/data/reports")
        date_dir = datetime.now().strftime("%Y-%m")
        full_dir = base_dir / date_dir
        full_dir.mkdir(parents=True, exist_ok=True)

        return str(full_dir)

    def _calculate_quality_score(self, result: ReportResult) -> float:
        """计算报告质量分数"""
        score = 0.0

        # Dolphin解析质量 (30分)
        if result.dolphin_result:
            score += 30.0

        # NetworkX分析质量 (30分)
        if result.networkx_result:
            entities = result.networkx_result.get("entities_count", 0)
            relations = result.networkx_result.get("relations_count", 0)
            innovations = len(result.networkx_result.get("innovations", []))

            # 根据数据量评分
            if entities > 0:
                score += min(10, entities / 10)
            if relations > 0:
                score += min(10, relations / 20)
            if innovations > 0:
                score += min(10, innovations * 2)

        # Athena生成质量 (40分)
        if result.athena_result:
            markdown_len = len(result.athena_result.get("markdown_content", ""))
            if markdown_len > 1000:
                score += 20.0
            elif markdown_len > 500:
                score += 10.0
            score += 20.0  # 基础生成质量分

        return min(100.0, score)

    def _calculate_quality_score_from_data(self, data: dict) -> float:
        """从数据计算质量分数"""
        score = 0.0

        # 技术实体数量 (30分)
        entities = data.get("technical_entities_count", 0)
        score += min(30.0, entities * 0.5)

        # 技术关系数量 (20分)
        relations = data.get("technical_relations_count", 0)
        score += min(20.0, relations * 0.2)

        # 创新点数量 (30分)
        innovations = len(data.get("innovation_points", []))
        score += min(30.0, innovations * 5)

        # 内容完整性 (20分)
        if data.get("original_markdown"):
            score += 10.0
        if data.get("technical_metrics"):
            score += 10.0

        return min(100.0, score)


# 便捷函数
async def generate_report_from_document(
    document_path: str,
    report_type: ReportType = ReportType.PATENT_TECHNICAL_ANALYSIS,
    output_dir: str | None = None,
) -> ReportResult:
    """
    便捷函数:从文档生成报告

    Args:
        document_path: 文档路径
        report_type: 报告类型
        output_dir: 输出目录

    Returns:
        ReportResult: 报告结果
    """
    service = UnifiedReportService()
    return await service.generate_from_document(
        document_path=document_path,
        report_type=report_type,
        output_dir=output_dir,
    )


async def compare_documents(
    doc1_path: str,
    doc2_path: str,
    output_dir: str | None = None,
) -> ReportResult:
    """
    便捷函数:对比两个文档

    Args:
        doc1_path: 文档1路径
        doc2_path: 文档2路径
        output_dir: 输出目录

    Returns:
        ReportResult: 对比报告结果
    """
    service = UnifiedReportService()
    return await service.compare_documents(
        doc1_path=doc1_path,
        doc2_path=doc2_path,
        output_dir=output_dir,
    )
