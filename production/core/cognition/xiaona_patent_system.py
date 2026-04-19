# pyright: ignore
# !/usr/bin/env python3
"""
小娜专利分析系统 - 集成主系统
Xiaona Patent Analysis System - Integrated Main System

整合专利分析、法律推理、撰写功能的完整系统

作者: 小娜·天秤女神
创建时间: 2025-12-16
版本: v1.0 Integrated System
"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from xiaona_patent_analyzer import PatentAnalysisRequest, PatentAnalysisResult, XiaonaPatentAnalyzer
from xiaona_patent_drafter import PatentDraftingRequest, PatentDraftingResult, XiaonaPatentDrafter
from xiaona_super_reasoning_engine import (
    LegalAnalysisResult,
    LegalCaseContext,
    LegalReasoningMode,
    XiaonaSuperReasoningEngine,
)

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class IntegratedPatentRequest:
    """集成专利请求"""

    # 基本信息
    invention_title: str
    technical_field: str
    invention_description: str

    # 分析类型
    analysis_type: str  # comprehensive_analysis, application_analysis, examination_reply

    # 优先级和要求
    priority: str = "medium"
    user_requirements: list[str] = field(default_factory=list)

    # 撰写相关(可选)
    background_art: str = ""
    detailed_description: str = ""
    claims: list[str] = field(default_factory=list)
    applicant: str = ""
    inventor: str = ""

    # 上下文信息
    context_info: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegratedPatentResult:
    """集成专利结果"""

    # 分析结果
    patent_analysis: PatentAnalysisResult | None = None

    # 法律推理结果
    legal_reasoning: LegalAnalysisResult | None = None

    # 撰写结果
    patent_draft: PatentDraftingResult | None = None

    # 综合评分和建议
    overall_score: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    # 元数据
    processing_time: float = 0.0
    system_confidence: float = 0.0

    # 输出格式
    markdown_report: str = ""
    json_output: str = ""


class XiaonaPatentSystem:
    """小娜专利分析系统 - 集成主系统"""

    def __init__(self):
        self.name = "小娜专利分析系统"
        self.version = "v1.0 Integrated System"

        # 子系统初始化
        self.patent_analyzer = XiaonaPatentAnalyzer()
        self.reasoning_engine = XiaonaSuperReasoningEngine()
        self.patent_drafter = XiaonaPatentDrafter()

        # 系统状态
        self.is_initialized = False

        # 统计信息
        self.processing_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "average_processing_time": 0.0,
            "user_satisfaction": 0.0,
        }

    async def initialize(self):
        """初始化整个系统"""
        logger.info("🌸 初始化小娜专利分析系统...")

        try:
            # 初始化各个子系统
            await self.patent_analyzer.initialize()
            logger.info("✅ 专利分析器初始化完成")

            await self.reasoning_engine.initialize()
            logger.info("✅ 法律推理引擎初始化完成")

            await self.patent_drafter.initialize()
            logger.info("✅ 专利撰写助手初始化完成")

            # 建立子系统间的连接
            await self._establish_subsystem_connections()

            # 加载专业知识和模板
            await self._load_knowledge_bases()

            self.is_initialized = True
            logger.info("🎉 小娜专利分析系统初始化完成!")

        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {e!s}")
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def process_patent_request(
        self, request: IntegratedPatentRequest
    ) -> IntegratedPatentResult:
        """处理专利请求的主入口"""
        if not self.is_initialized:
            raise RuntimeError("系统未初始化,请先调用initialize()")

        logger.info(f"🎯 开始处理专利请求: {request.invention_title}")
        start_time = datetime.now()

        # 更新统计信息
        self.processing_stats["total_requests"] += 1

        try:
            # 1. 专利分析
            patent_analysis_result = await self._perform_patent_analysis(request)

            # 2. 法律推理
            legal_reasoning_result = await self._perform_legal_reasoning(
                request, patent_analysis_result
            )

            # 3. 专利撰写(如果需要)
            patent_draft_result = None
            if request.analysis_type in ["application_analysis", "comprehensive_analysis"]:
                patent_draft_result = await self._perform_patent_drafting(
                    request, patent_analysis_result
                )

            # 4. 综合分析和建议
            overall_analysis = await self._perform_overall_analysis(
                request, patent_analysis_result, legal_reasoning_result, patent_draft_result
            )

            # 5. 生成报告
            markdown_report = await self._generate_markdown_report(
                request, patent_analysis_result, legal_reasoning_result, patent_draft_result
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            # 更新成功统计
            self.processing_stats["successful_requests"] += 1
            self._update_processing_time_stats(processing_time)

            result = IntegratedPatentResult(
                patent_analysis=patent_analysis_result,
                legal_reasoning=legal_reasoning_result,
                patent_draft=patent_draft_result,
                overall_score=overall_analysis["score"],
                recommendations=overall_analysis["recommendations"],
                next_steps=overall_analysis["next_steps"],
                processing_time=processing_time,
                system_confidence=overall_analysis["confidence"],
                markdown_report=markdown_report,
                json_output=json.dumps(
                    {
                        "request": request.__dict__,
                        "analysis": (
                            patent_analysis_result.__dict__ if patent_analysis_result else None
                        ),
                        "reasoning": (
                            legal_reasoning_result.__dict__ if legal_reasoning_result else None
                        ),
                        "draft": patent_draft_result.__dict__ if patent_draft_result else None,
                        "overall": overall_analysis,
                    },
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
            )

            logger.info(f"✅ 专利请求处理完成,耗时: {processing_time:.2f}秒")
            return result

        except Exception as e:
            # 分析失败，记录错误
            logger.error(f'专利分析失败: {e}', exc_info=True)
            # 返回部分结果或错误信息
            return IntegratedPatentResult(
                processing_time=(datetime.now() - start_time).total_seconds(),
                recommendations=[f"处理过程中出现错误: {e!s}"],
                next_steps=["请检查输入信息并重试"],
            )

    async def _perform_patent_analysis(
        self, request: IntegratedPatentRequest
    ) -> PatentAnalysisResult | None:
        """执行专利分析"""
        try:
            # 构建专利分析请求
            analysis_request = PatentAnalysisRequest(
                patent_type=request.analysis_type,
                technology_field=request.technical_field,
                invention_description=request.invention_description,
                priority=request.priority,
                user_requirements=request.user_requirements,
                context_info=request.context_info,
            )

            # 执行分析
            return await self.patent_analyzer.analyze_patent(analysis_request)

        except Exception:
            return None

    async def _perform_legal_reasoning(
        self, request: IntegratedPatentRequest, analysis_result: PatentAnalysisResult,
    ) -> LegalAnalysisResult | None:
        """执行法律推理"""
        try:
            # 构建法律案例上下文
            case_context = LegalCaseContext(
                case_type="patent_analysis",
                client_requirements=request.user_requirements,
                jurisdiction="中国",
                relevant_laws=["专利法", "专利法实施细则", "审查指南"],
                similar_cases=[],
                constraints=[],
                complexity_level=self._assess_case_complexity(request),
                deadline=None,
            )

            # 选择推理模式
            if request.analysis_type == "examination_reply":
                reasoning_mode = LegalReasoningMode.DRAFT_PREPARATION
            elif request.analysis_type == "application_analysis":
                reasoning_mode = LegalReasoningMode.STRATEGY_PLANNING
            else:
                reasoning_mode = LegalReasoningMode.CASE_ANALYSIS

            # 执行推理
            return await self.reasoning_engine.reason_about_case(case_context, reasoning_mode)

        except Exception:
            return None

    async def _perform_patent_drafting(
        self, request: IntegratedPatentRequest, analysis_result: PatentAnalysisResult,
    ) -> PatentDraftingResult | None:
        """执行专利撰写"""
        try:
            # 构建撰写请求
            drafting_request = PatentDraftingRequest(
                invention_title=request.invention_title,
                technical_field=request.technical_field,
                background_art=request.background_art,
                invention_summary=(
                    request.invention_description[:500] + "..."
                    if len(request.invention_description) > 500
                    else request.invention_description
                ),
                brief_description="",  # 将从详细描述中提取
                detailed_description=request.detailed_description or request.invention_description,
                claims=request.claims,
                abstract="",  # 将由系统生成
                applicant=request.applicant,
                inventor=request.inventor,
            )

            # 执行撰写
            return await self.patent_drafter.draft_patent_application(drafting_request)

        except Exception:
            return None

    async def _perform_overall_analysis(
        self,
        request: IntegratedPatentRequest,
        analysis_result: PatentAnalysisResult,
        reasoning_result: LegalAnalysisResult,
        draft_result: PatentDraftingResult,
    ) -> dict[str, Any]:
        """执行综合分析"""
        score = 0.0
        recommendations = []
        next_steps = []

        # 基于专利分析评分
        if analysis_result:
            score += analysis_result.confidence_score * 0.4
            recommendations.extend(analysis_result.recommendations[:3])
            next_steps.extend(analysis_result.next_steps[:3])

        # 基于法律推理评分
        if reasoning_result:
            score += reasoning_result.confidence_score * 0.3
            recommendations.extend(reasoning_result.recommendations[:3])
            next_steps.extend(reasoning_result.next_steps[:3])

        # 基于撰写质量评分
        if draft_result:
            score += draft_result.quality_score * 0.3
            recommendations.extend(draft_result.application_suggestions[:3])

        # 确保评分在合理范围
        score = min(100.0, max(0.0, score))

        # 生成下一步行动建议
        if not next_steps:
            next_steps = [
                "根据分析结果完善技术方案",
                "准备相关的技术交底材料",
                "考虑专利布局策略",
                "咨询专业专利代理人",
            ]

        return {
            "score": score,
            "recommendations": list(set(recommendations)),  # 去重
            "next_steps": next_steps[:5],  # 最多5个步骤
            "confidence": score / 100.0,
        }

    async def _generate_markdown_report(
        self,
        request: IntegratedPatentRequest,
        analysis_result: PatentAnalysisResult,
        reasoning_result: LegalAnalysisResult,
        draft_result: PatentDraftingResult,
    ) -> str:
        """生成Markdown格式报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""# 小娜专利分析报告

> 分析时间: {timestamp}
> 发明名称: {request.invention_title}
> 技术领域: {request.technical_field}
> 分析类型: {request.analysis_type}
> 分析师: 小娜·天秤女神

---

## 📋 执行摘要

"""

        # 专利分析摘要
        if analysis_result:
            report += "### 专利分析结果\n\n"
            report += f"**置信度**: {analysis_result.confidence_score:.2f}/100\n\n"
            if analysis_result.conclusions:
                report += "**主要结论**:\n"
                for i, conclusion in enumerate(analysis_result.conclusions, 1):
                    report += f"{i}. {conclusion}\n"
                report += "\n"

        # 法律推理摘要
        if reasoning_result:
            report += "### 法律分析结果\n\n"
            report += f"**结论**: {reasoning_result.conclusion}\n\n"
            if reasoning_result.recommendations:
                report += "**法律建议**:\n"
                for i, rec in enumerate(reasoning_result.recommendations, 1):
                    report += f"{i}. {rec}\n"
                report += "\n"

        # 专利撰写摘要
        if draft_result:
            report += "### 专利撰写结果\n\n"
            report += f"**撰写质量**: {draft_result.quality_score:.2f}/100\n"
            report += f"**优化标题**: {draft_result.title}\n\n"

            if draft_result.claims:
                report += "**权利要求概要**:\n"
                for i, claim in enumerate(draft_result.claims[:3], 1):  # 只显示前3个
                    report += f"{i}. {claim['text'][:100]}...\n"
                report += "\n"

        # 综合建议
        report += "## 💡 综合建议\n\n"
        if analysis_result and analysis_result.recommendations:
            report += "**技术建议**:\n"
            for i, rec in enumerate(analysis_result.recommendations[:3], 1):
                report += f"{i}. {rec}\n"
            report += "\n"

        if reasoning_result and reasoning_result.recommendations:
            report += "**法律建议**:\n"
            for i, rec in enumerate(reasoning_result.recommendations[:3], 1):
                report += f"{i}. {rec}\n"
            report += "\n"

        if draft_result and draft_result.application_suggestions:
            report += "**撰写建议**:\n"
            for i, rec in enumerate(draft_result.application_suggestions[:3], 1):
                report += f"{i}. {rec}\n"
            report += "\n"

        # 下一步行动
        report += "## 🎯 下一步行动\n\n"
        report += "建议按以下顺序进行:\n"
        report += "1. 完善技术方案细节\n"
        report += "2. 进行专业的专利检索\n"
        report += "3. 准备专利申请文件\n"
        report += "4. 提交专利申请\n"
        report += "5. 持续监控申请进程\n\n"

        # 风险提示
        report += "## ⚠️ 风险提示\n\n"
        report += "- 专利申请存在被驳回的风险\n"
        report += "- 技术方案可能需要进一步优化\n"
        report += "- 法律环境可能发生变化\n"
        report += "- 建议咨询专业专利代理人\n\n"

        report += "---\n"
        report += "*本报告由小娜专利分析系统自动生成*\n"
        report += f"*系统版本: {self.version}*\n"
        report += "*生成时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "*\n"

        return report

    async def _establish_subsystem_connections(self):
        """建立子系统间的连接"""
        # 设置子系统间的数据共享通道
        self.patent_analyzer.reasoning_engine = self.reasoning_engine
        self.reasoning_engine.patent_analyzer = self.patent_analyzer
        self.patent_drafter.analysis_engine = self.patent_analyzer

    async def _load_knowledge_bases(self):
        """加载知识库"""
        # 加载专利法律知识
        await self.reasoning_engine._load_legal_knowledge()

        # 加载专利分析知识
        await self.patent_analyzer._load_patent_knowledge_base()

        # 加载撰写模板
        await self.patent_drafter._load_patent_templates()  # type: ignore

    def _assess_case_complexity(self, request: IntegratedPatentRequest) -> int:
        """评估案件复杂度"""
        complexity = 3  # 基础复杂度

        # 根据描述长度调整
        if len(request.invention_description) > 1000:
            complexity += 1
        elif len(request.invention_description) < 200:
            complexity -= 1

        # 根据技术领域调整
        complex_fields = ["人工智能", "机器学习", "生物技术", "新材料", "量子计算"]
        if any(field in request.technical_field for field in complex_fields):
            complexity += 1

        # 根据用户要求数量调整
        complexity += min(len(request.user_requirements) // 3, 2)

        return max(1, min(5, complexity))

    def _update_processing_time_stats(self, processing_time: float) -> Any:
        """更新处理时间统计"""
        current_avg = self.processing_stats["average_processing_time"]
        total_requests = self.processing_stats["successful_requests"]

        # 计算新的平均值
        new_avg = (current_avg * (total_requests - 1) + processing_time) / total_requests
        self.processing_stats["average_processing_time"] = new_avg

    async def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        return {
            "system_name": self.name,
            "version": self.version,
            "is_initialized": self.is_initialized,
            "subsystems": {
                "patent_analyzer": (
                    self.patent_analyzer.is_initialized
                    if hasattr(self.patent_analyzer, "is_initialized")
                    else False
                ),
                "reasoning_engine": self.reasoning_engine.legal_knowledge_base != {},
                "patent_drafter": True,  # 简化检查
            },
            "processing_stats": self.processing_stats,
            "last_check": datetime.now().isoformat(),
        }

    async def cleanup(self):
        """清理系统资源"""
        logger.info("🧹 清理小娜专利分析系统资源...")

        try:
            if hasattr(self.patent_analyzer, "cleanup"):
                await self.patent_analyzer.cleanup()

            if hasattr(self.reasoning_engine, "cleanup"):
                await self.reasoning_engine.cleanup()

            if hasattr(self.patent_drafter, "cleanup"):
                await self.patent_drafter.cleanup()

            logger.info("✅ 系统资源清理完成")

        except Exception as e:
            # 清理失败，记录错误
            logger.error(f"系统资源清理失败: {e}", exc_info=True)


# 导出主类
__all__ = ["IntegratedPatentRequest", "IntegratedPatentResult", "XiaonaPatentSystem"]
