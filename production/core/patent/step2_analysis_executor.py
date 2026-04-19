#!/usr/bin/env python3
"""
步骤2智能分析执行器
Step 2 Intelligent Analysis Executor

整合小娜深度技术分析、增强分析和智能答复策略生成

增强功能:
- ML三元关系提取优化
- 大规模图谱优化
- 技术演化路径分析

作者: 小诺·双鱼公主
创建时间: 2026-01-24
版本: v0.2.0 "智能增强"
"""

from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class AnalysisExecutionResult:
    """分析执行结果"""

    success: bool
    stage: str  # 当前阶段

    # 小娜深度分析结果
    deep_analysis: dict[str, Any] | None = None
    deep_analysis_report_path: str = ""

    # 答复策略结果
    response_plan: dict[str, Any] | None = None

    # 增强分析结果（新增）
    enhanced_analysis: dict[str, Any] | None = None
    enhanced_analysis_time: float = 0.0

    # 输出文件
    json_report_path: str = ""
    markdown_report_path: str = ""

    # 统计
    total_time: float = 0.0
    deep_analysis_time: float = 0.0
    enhanced_analysis_time: float = 0.0
    strategy_generation_time: float = 0.0

    # 元数据
    started_at: str = field(default_factory=lambda: datetime.now().isoformat)
    completed_at: str = ""
    error: str = ""

    def to_markdown(self) -> str:
        """生成Markdown报告"""
        md = []

        md.append("# 📊 步骤2智能分析执行报告\n")
        md.append("---\n")

        # 执行状态
        md.append("## ✅ 执行状态\n")
        md.append(f"- **状态**: {'✅ 成功' if self.success else '❌ 失败'}\n")
        md.append(f"- **当前阶段**: {self.stage}\n")
        md.append(f"- **开始时间**: {self.started_at}\n")
        md.append(f"- **完成时间**: {self.completed_at}\n")
        md.append(f"- **总耗时**: {self.total_time:.1f}秒\n")
        md.append("")

        # 小娜深度分析结果
        if self.deep_analysis:
            md.append("## 🔬 小娜深度技术分析\n")
            target = self.deep_analysis.get("target_patent", "N/A")
            md.append(f"- **目标专利**: `{target}`\n")
            prior_count = len(self.deep_analysis.get("prior_art_analyses", {}))
            md.append(f"- **对比文件**: {prior_count}个\n")
            md.append(f"- **整体相似度**: {self.deep_analysis.get('overall_similarity', 0):.1%}\n")
            if self.deep_analysis_report_path:
                md.append(f"- **详细报告**: `{self.deep_analysis_report_path}`\n")
            md.append("")

        # 增强分析结果（新增）
        if self.enhanced_analysis:
            md.append("## 🚀 增强分析结果\n")

            # 1. ML三元关系提取
            if "ml_triple_extraction" in self.enhanced_analysis:
                ml_triple = self.enhanced_analysis["ml_triple_extraction"]
                md.append("### 🎯 ML三元关系提取\n")
                md.append(f"- **提取三元组数量**: {ml_triple.get('total_triples', 0)}\n")
                md.append(f"- **高置信度三元组**: {ml_triple.get('high_confidence_triples', 0)}\n")
                md.append(f"- **平均置信度**: {ml_triple.get('avg_confidence', 0):.1%}\n")

                # 显示前3个三元组
                triples = ml_triple.get("triples", [])[:3]
                if triples:
                    md.append("\n**主要三元关系**:\n")
                    for i, triple in enumerate(triples, 1):
                        md.append(f"{i}. **问题**: {triple.get('problem', 'N/A')}\n")
                        md.append(f"   **特征**: {triple.get('feature', 'N/A')}\n")
                        md.append(f"   **效果**: {triple.get('effect', 'N/A')}\n")
                        md.append(f"   **置信度**: {triple.get('confidence', 0):.1%}\n")
                        md.append(f"   **提取方法**: {triple.get('method', 'N/A')}\n")
                md.append("")

            # 2. 大规模图谱优化
            if "graph_optimization" in self.enhanced_analysis:
                graph_opt = self.enhanced_analysis["graph_optimization"]
                md.append("### ⚡ 大规模图谱优化\n")
                md.append(f"- **原始节点数**: {graph_opt.get('original_nodes', 0)}\n")
                md.append(f"- **优化后节点数**: {graph_opt.get('optimized_nodes', 0)}\n")
                md.append(f"- **原始边数**: {graph_opt.get('original_edges', 0)}\n")
                md.append(f"- **优化后边数**: {graph_opt.get('optimized_edges', 0)}\n")
                md.append(f"- **压缩率**: {graph_opt.get('compression_ratio', 0):.1%}\n")
                md.append(f"- **性能提升**: {graph_opt.get('performance_gain', 0):.1f}x\n")
                md.append(f"- **优化耗时**: {graph_opt.get('optimization_time', 0):.2f}秒\n")

                # 显示中心性最高的特征
                top_features = graph_opt.get("top_centrality_features", [])[:5]
                if top_features:
                    md.append("\n**核心技术特征（按PageRank排序）**:\n")
                    for i, (feature, score) in enumerate(top_features, 1):
                        md.append(f"{i}. `{feature}`: {score:.4f}\n")
                md.append("")

            # 3. 技术演化分析
            if "technology_evolution" in self.enhanced_analysis:
                evolution = self.enhanced_analysis["technology_evolution"]
                md.append("### 🔬 技术演化分析\n")
                md.append(f"- **演化路径数量**: {evolution.get('total_paths', 0)}\n")
                md.append(f"- **平均路径长度**: {evolution.get('avg_path_length', 0):.1f}个专利\n")

                # 高频演化特征
                evolved_features = evolution.get("most_evolved_features", [])
                if evolved_features:
                    md.append(f"- **高频演化特征**: {', '.join(evolved_features)}\n")

                # 未来趋势
                future_trends = evolution.get("future_trends", [])
                if future_trends:
                    md.append("\n**🔮 未来趋势预测**:\n")
                    for trend in future_trends[:5]:
                        md.append(f"- {trend}\n")

                # 关键转折点
                turning_points = evolution.get("key_turning_points", [])
                if turning_points:
                    md.append("\n**🔄 关键转折点**:\n")
                    for point in turning_points[:3]:
                        md.append(f"- **{point.get('patent_number', 'N/A')}** ({point.get('application_date', '')})\n")
                        md.append(f"  类型: {point.get('type', 'N/A')}, 变化幅度: {point.get('importance_change', 0):.2f}\n")
                md.append("")

        # 答复策略结果
        if self.response_plan:
            md.append("## 🎯 答复策略方案\n")
            md.append(f"- **推荐策略**: {self.response_plan.get('recommended_strategy', 'N/A')}\n")
            md.append(f"- **成功概率**: {self.response_plan.get('success_probability', 0):.1%}\n")
            md.append(f"- **置信度**: {self.response_plan.get('confidence', 0):.1%}\n")
            md.append("")

        # 输出文件
        md.append("## 📄 输出文件\n")
        if self.json_report_path:
            md.append(f"- **JSON报告**: `{self.json_report_path}`\n")
        if self.markdown_report_path:
            md.append(f"- **Markdown报告**: `{self.markdown_report_path}`\n")
        md.append("")

        # 时间统计
        md.append("## ⏱️ 时间统计\n")
        md.append(f"- **小娜深度分析**: {self.deep_analysis_time:.1f}秒\n")
        if self.enhanced_analysis_time > 0:
            md.append(f"- **增强分析**: {self.enhanced_analysis_time:.1f}秒\n")
        md.append(f"- **策略生成**: {self.strategy_generation_time:.1f}秒\n")
        md.append("")

        # 错误信息
        if self.error:
            md.append(f"## ❌ 错误信息\n{self.error}\n")

        return "".join(md)


class Step2AnalysisExecutor:
    """
    步骤2智能分析执行器

    整合:
    1. 小娜深度技术分析
    2. 增强分析（ML三元关系提取、图谱优化、演化分析）
    3. 智能答复策略生成
    4. 报告生成(JSON + Markdown)
    """

    def __init__(self, output_dir: str = "data/step2_analysis"):
        """
        初始化执行器

        Args:
            output_dir: 分析结果输出目录
        """
        self.name = "步骤2智能分析执行器"
        self.version = "v0.2.0"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化子系统
        self._init_subsystems()

        logger.info(f"🚀 {self.name} ({self.version}) 初始化完成")
        logger.info(f"📁 输出目录: {self.output_dir}")

    def _init_subsystems(self):
        """初始化子系统"""
        # 小娜深度技术分析器
        try:
            from core.patent.xiaona_deep_technical_analyzer import (
                get_xiaona_deep_analyzer,
            )

            self.deep_analyzer = get_xiaona_deep_analyzer(
                output_dir=str(self.output_dir / "deep_analysis")
            )
            logger.info("✅ 小娜深度技术分析器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 小娜深度技术分析器初始化失败: {e}")
            self.deep_analyzer = None

        # 智能答复系统
        try:
            from core.patent.smart_oa_responder import get_smart_oa_responder

            self.smart_responder = get_smart_oa_responder()
            logger.info("✅ 智能答复系统初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 智能答复系统初始化失败: {e}")
            self.smart_responder = None

        # 三元关系提取ML模型
        try:
            from core.patent.triple_relation_extractor_ml import (
                get_triple_extractor_ml,
            )

            self.triple_extractor = get_triple_extractor_ml(
                model_dir=str(self.output_dir / "ml_models")
            )
            logger.info("✅ 三元关系提取ML模型初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 三元关系提取ML模型初始化失败: {e}")
            self.triple_extractor = None

        # 大规模图谱优化器
        try:
            from core.patent.large_scale_graph_optimizer import (
                get_graph_optimizer,
            )

            self.graph_optimizer = get_graph_optimizer()
            logger.info("✅ 大规模图谱优化器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 大规模图谱优化器初始化失败: {e}")
            self.graph_optimizer = None

        # 技术演化分析器
        try:
            from core.patent.technology_evolution_analyzer import (
                get_evolution_analyzer,
            )

            self.evolution_analyzer = get_evolution_analyzer()
            logger.info("✅ 技术演化分析器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 技术演化分析器初始化失败: {e}")
            self.evolution_analyzer = None

    async def execute_full_analysis(
        self,
        target_patent_info: dict[str, Any],        prior_art_references: list[dict[str, Any]],        examination_opinions: list[dict[str, Any]] | None = None,
        target_patent_text: str = "",
        prior_art_texts: dict[str, str] | None = None,
    ) -> AnalysisExecutionResult:
        """
        执行完整的智能分析流程

        Args:
            target_patent_info: 目标专利信息
            prior_art_references: 对比文件列表
            examination_opinions: 审查意见列表
            target_patent_text: 目标专利全文
            prior_art_texts: 对比文件全文映射

        Returns:
            AnalysisExecutionResult: 分析执行结果
        """
        import time

        start_time = time.time()

        result = AnalysisExecutionResult(
            success=False, stage="init", started_at=datetime.now().isoformat()
        )

        logger.info("🚀 开始执行步骤2智能分析")
        logger.info(f"   目标专利: {target_patent_info.get('application_number', 'N/A')}")
        logger.info(f"   对比文件: {len(prior_art_references)}个")

        try:
            # 阶段1: 小娜深度技术分析
            result.stage = "deep_analysis"
            deep_start = time.time()

            if self.deep_analyzer:
                deep_result = await self.deep_analyzer.analyze_target_and_prior_art(
                    target_patent_info=target_patent_info,
                    prior_art_references=prior_art_references,
                    target_patent_text=target_patent_text,
                    prior_art_texts=prior_art_texts,
                )

                # 保存深度分析报告
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_base = f"deep_analysis_{timestamp}"

                deep_result.save_outputs(
                    output_dir=str(self.output_dir / "deep_analysis"),
                    base_filename=report_base,
                )

                result.deep_analysis = deep_result.to_dict()
                result.deep_analysis_report_path = (
                    str(self.output_dir / "deep_analysis" / f"{report_base}.md")
                )

                result.deep_analysis_time = time.time() - deep_start
                logger.info(f"✅ 小娜深度分析完成，耗时 {result.deep_analysis_time:.1f}秒")

            # 阶段1.5: 增强分析（新增）
            result.stage = "enhanced_analysis"
            enhanced_start = time.time()

            enhanced_analysis = {}

            # 1. 三元关系提取优化
            if self.triple_extractor and target_patent_text:
                try:
                    # 获取技术问题、特征、效果
                    kg = result.deep_analysis.get("knowledge_graph", {})
                    technical_problem = target_patent_info.get("technical_problem", "")
                    technical_features = kg.get("nodes", {}).keys() if kg else []
                    technical_effects = kg.get("problem_effect_triples", [])

                    # 执行ML增强的三元关系提取
                    ml_triples = self.triple_extractor.extract_triples(
                        patent_text=target_patent_text,
                        technical_problem=technical_problem,
                        technical_features=list(technical_features) if technical_features else None,
                        technical_effects=technical_effects[:5] if technical_effects else None,
                    )

                    enhanced_analysis["ml_triple_extraction"] = {
                        "total_triples": len(ml_triples),
                        "high_confidence_triples": len([t for t in ml_triples if t.confidence > 0.8]),
                        "avg_confidence": sum(t.confidence for t in ml_triples) / max(len(ml_triples), 1),
                        "triples": [
                            {
                                "problem": t.problem_text,
                                "feature": t.feature_text,
                                "effect": t.effect_text,
                                "confidence": t.confidence,
                                "method": t.extraction_method,
                            }
                            for t in ml_triples[:10]  # 保留前10个
                        ],
                    }
                    logger.info(f"   🎯 ML三元关系提取: {len(ml_triples)}个三元组")
                except Exception as e:
                    logger.warning(f"⚠️ ML三元关系提取失败: {e}")

            # 2. 大规模图谱优化
            if self.graph_optimizer and result.deep_analysis:
                try:
                    kg = result.deep_analysis.get("knowledge_graph", {})
                    if kg and kg.get("nodes"):
                        # 构建节点和边
                        nodes = [
                            {
                                "id": feature_id,
                                "name": feature_data.get("feature_name", feature_id),
                                "type": "technical_feature",
                                "importance": feature_data.get("importance_score", 0.5),
                            }
                            for feature_id, feature_data in kg.get("nodes", {}).items()
                        ]

                        edges = [
                            {
                                "source": relation.get("source_feature"),
                                "target": relation.get("target_feature"),
                                "relation_type": relation.get("relation_type", "related"),
                                "weight": relation.get("confidence", 1.0),
                            }
                            for relation in kg.get("edges", [])
                        ]

                        # 执行图谱优化
                        optimization_result = self.graph_optimizer.optimize_graph(
                            nodes=nodes,
                            edges=edges,
                            optimization_level="medium",
                        )

                        # 计算中心性
                        centrality = self.graph_optimizer.calculate_centrality_large_scale(
                            nodes=nodes,
                            edges=edges,
                            centrality_type="pagerank",
                        )

                        enhanced_analysis["graph_optimization"] = {
                            "original_nodes": optimization_result.original_nodes,
                            "optimized_nodes": optimization_result.optimized_nodes,
                            "original_edges": optimization_result.original_edges,
                            "optimized_edges": optimization_result.optimized_edges,
                            "compression_ratio": optimization_result.compression_ratio,
                            "performance_gain": optimization_result.performance_gain,
                            "optimization_time": optimization_result.optimization_time,
                            "top_centrality_features": sorted(
                                centrality.items(), key=lambda x: x[1], reverse=True
                            )[:10],
                            "recommendations": optimization_result.recommendations,
                        }
                        logger.info(
                            f"   ⚡ 图谱优化: {optimization_result.compression_ratio:.1%}压缩率, "
                            f"{optimization_result.performance_gain:.1f}x性能提升"
                        )
                except Exception as e:
                    logger.warning(f"⚠️ 图谱优化失败: {e}")

            # 3. 技术演化分析
            if self.evolution_analyzer and result.deep_analysis:
                try:
                    from core.patent.technology_evolution_analyzer import (
                        EvolutionNode,
                    )

                    # 构建目标专利节点
                    target_patent = EvolutionNode(
                        patent_id=target_patent_info.get("application_number", "target"),
                        patent_number=target_patent_info.get("application_number", "N/A"),
                        patent_title=target_patent_info.get("title", ""),
                        application_date=target_patent_info.get("application_date", "2024-01-01"),
                        technical_features=list(
                            result.deep_analysis.get("core_innovation_features", [])
                        ),
                        importance_score=result.deep_analysis.get("overall_importance", 0.7),
                    )

                    # 构建专利族节点（基于对比文件）
                    patent_family = []
                    for ref in prior_art_references:
                        family_node = EvolutionNode(
                            patent_id=ref.get("publication_number", ""),
                            patent_number=ref.get("publication_number", "N/A"),
                            patent_title=ref.get("title", ""),
                            application_date=ref.get("application_date", "2020-01-01"),
                            technical_features=ref.get("technical_features", []),
                            importance_score=ref.get("importance_score", 0.5),
                        )
                        patent_family.append(family_node)

                    # 执行演化分析
                    evolution_result = self.evolution_analyzer.analyze_evolution(
                        target_patent=target_patent,
                        patent_family=patent_family,
                    )

                    enhanced_analysis["technology_evolution"] = {
                        "total_paths": evolution_result.total_paths,
                        "avg_path_length": evolution_result.avg_path_length,
                        "most_evolved_features": evolution_result.most_evolved_features,
                        "future_trends": evolution_result.future_trends,
                        "key_turning_points": evolution_result.key_turning_points,
                    }
                    logger.info(
                        f"   🔬 演化分析: {evolution_result.total_paths}条路径, "
                        f"{len(evolution_result.future_trends)}个趋势预测"
                    )
                except Exception as e:
                    logger.warning(f"⚠️ 技术演化分析失败: {e}")

            # 保存增强分析结果
            if enhanced_analysis:
                result.enhanced_analysis = enhanced_analysis
                result.enhanced_analysis_time = time.time() - enhanced_start
                logger.info(f"✅ 增强分析完成，耗时 {result.enhanced_analysis_time:.1f}秒")

            # 阶段2: 智能答复策略生成
            result.stage = "strategy_generation"
            strategy_start = time.time()

            if self.smart_responder and examination_opinions:
                # 构建office_action字典
                office_action = {
                    "oa_id": f"OA_{timestamp}",
                    "rejection_type": examination_opinions[0].get("opinion_type", "unknown")
                    if examination_opinions
                    else "unknown",
                    "rejection_reason": examination_opinions[0].get("issue_description", "")
                    if examination_opinions
                    else "",
                    "prior_art_references": [
                        ref.get("publication_number", "") for ref in prior_art_references
                    ],
                    "cited_claims": [],
                    "examiner_arguments": [],
                    "missing_features": [],
                    "received_date": datetime.now().isoformat(),
                    "response_deadline": "",
                }

                # 构建知识图谱数据 (新增)
                knowledge_graph = None
                if result.deep_analysis and "target_patent" in result.deep_analysis:
                    # 从深度分析结果中提取知识图谱数据
                    knowledge_graph = {
                        "core_innovation_features": result.deep_analysis.get("core_innovation_features", []),
                        "graph_centrality_ranking": result.deep_analysis.get("graph_centrality_ranking", []),
                        "graph_density": result.deep_analysis.get("knowledge_graph", {}).get("graph_density", 0),
                        "problem_effect_triples": result.deep_analysis.get("problem_effect_triples", []),
                        "feature_relations": result.deep_analysis.get("feature_relations", []),
                    }

                # 生成答复方案 (增强：传递知识图谱)
                response_plan = await self.smart_responder.create_response_plan(
                    office_action=office_action,
                    knowledge_graph=knowledge_graph,  # 新增：传递知识图谱
                )

                result.response_plan = {
                    "plan_id": response_plan.plan_id,
                    "recommended_strategy": response_plan.recommended_strategy.value,
                    "strategy_rationale": response_plan.strategy_rationale,
                    "arguments": response_plan.arguments,
                    "claim_modifications": response_plan.claim_modifications,
                    "success_probability": response_plan.success_probability,
                    "confidence": response_plan.confidence,
                    "reference_cases": response_plan.reference_cases,
                }

                result.strategy_generation_time = time.time() - strategy_start
                logger.info(
                    f"✅ 策略生成完成，耗时 {result.strategy_generation_time:.1f}秒"
                )

            # 阶段3: 生成综合报告
            result.stage = "report_generation"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # JSON报告
            json_path = self.output_dir / f"step2_analysis_{timestamp}.json"
            self._save_json_report(result, json_path)
            result.json_report_path = str(json_path)

            # Markdown报告
            md_path = self.output_dir / f"step2_analysis_{timestamp}.md"
            self._save_markdown_report(result, md_path)
            result.markdown_report_path = str(md_path)

            # 完成统计
            result.total_time = time.time() - start_time
            result.completed_at = datetime.now().isoformat()
            result.success = True
            result.stage = "completed"

            logger.info(f"✅ 步骤2智能分析完成，总耗时 {result.total_time:.1f}秒")
            logger.info(f"📄 JSON报告: {json_path}")
            logger.info(f"📄 Markdown报告: {md_path}")

        except Exception as e:
            logger.error(f"❌ 智能分析执行失败: {e}")
            result.error = str(e)
            result.stage = "failed"
            result.total_time = time.time() - start_time
            result.completed_at = datetime.now().isoformat()

        return result

    def _save_json_report(self, result: AnalysisExecutionResult, file_path: Path):
        """保存JSON报告"""
        import json

        report_data = {
            "execution_info": {
                "success": result.success,
                "stage": result.stage,
                "started_at": result.started_at,
                "completed_at": result.completed_at,
                "total_time": result.total_time,
                "deep_analysis_time": result.deep_analysis_time,
                "enhanced_analysis_time": result.enhanced_analysis_time,
                "strategy_generation_time": result.strategy_generation_time,
            },
            "deep_analysis": result.deep_analysis,
            "enhanced_analysis": result.enhanced_analysis,  # 新增
            "response_plan": result.response_plan,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

    def _save_markdown_report(self, result: AnalysisExecutionResult, file_path: Path):
        """保存Markdown报告"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(result.to_markdown())


# 全局单例
_executor_instance: Step2AnalysisExecutor | None = None


def get_step2_executor(
    output_dir: str = "data/step2_analysis",
) -> Step2AnalysisExecutor:
    """获取执行器单例"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = Step2AnalysisExecutor(output_dir=output_dir)
    return _executor_instance


# 测试代码
async def main():
    """测试步骤2执行器"""

    print("\n" + "=" * 70)
    print("🚀 步骤2智能分析执行器测试")
    print("=" * 70 + "\n")

    executor = get_step2_executor()

    # 模拟测试数据
    target_info = {
        "application_number": "CN202310000001.X",
        "title": "基于深度学习的图像识别方法",
    }

    prior_refs = [
        {
            "publication_number": "CN112345678A",
            "title": "图像识别方法及装置",
        },
    ]

    exam_opinions = [
        {
            "opinion_type": "novelty",
            "issue_description": "权利要求1不具备新颖性",
        }
    ]

    # 执行分析
    result = await executor.execute_full_analysis(
        target_patent_info=target_info,
        prior_art_references=prior_refs,
        examination_opinions=exam_opinions,
    )

    # 输出结果
    print(result.to_markdown())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
