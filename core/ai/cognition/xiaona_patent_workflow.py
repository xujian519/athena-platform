
#!/usr/bin/env python3

# pyright: ignore
"""
小娜专利分析工作流
Xiaona Patent Analysis Workflow

集成专家团队、LLM和知识库的完整专利分析工作流

作者: 小娜·天秤女神
创建时间: 2025-12-16
版本: v1.0 Patent Workflow
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from expert_prompt_generator import ExpertPromptGenerator
from knowledge_connector import KnowledgeConnector, KnowledgeQuery, KnowledgeResult

# 导入系统模块
from llm_interface import LLMInterface, LLMRequest
from top_patent_expert_system import ExpertTeamAnalysis, PatentContext, TopPatentExpertSystem

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class PatentAnalysisRequest:
    """专利分析请求"""

    request_id: str
    invention_title: str
    technology_field: str
    invention_description: str
    analysis_type: str  # comprehensive, novelty, inventive_step, infringement
    user_requirements: list[str] = field(default_factory=list)
    priority: str = "normal"  # high, normal, low
    target_jurisdiction: str = "中国"
    deadline_requirement: Optional[str] = None
    existing_art: Optional[str] = None
    background_art: Optional[str] = None
    specific_questions: list[str] = field(default_factory=list)


@dataclass
class PatentAnalysisResult:
    """专利分析结果"""

    request_id: str
    analysis_summary: dict[str, Any]
    expert_team_analysis: ExpertTeamAnalysis
    patentability_analysis: dict[str, Any]
    risk_assessment: dict[str, Any]
    recommendations: list[str]
    next_steps: list[str]
    supporting_documents: list[dict[str, Any]
    confidence_scores: dict[str, float]
    processing_time: float
    timestamp: datetime


class XiaonaPatentWorkflow:
    """小娜专利分析工作流"""

    def __init__(self):
        self.llm_interface = LLMInterface()
        self.prompt_generator = ExpertPromptGenerator()
        self.knowledge_connector = KnowledgeConnector()
        self.expert_system = TopPatentExpertSystem()
        self.workflow_history = []

    async def initialize(self):
        """初始化工作流组件"""
        await self.knowledge_connector.initialize()
        await self.expert_system.initialize()
        logger.info("小娜专利分析工作流初始化完成")

    async def process_patent_analysis(self, request: PatentAnalysisRequest) -> PatentAnalysisResult:
        """处理专利分析请求"""
        start_time = datetime.now()

        logger.info(f"开始处理专利分析请求: {request.request_id}")
        logger.info(f"发明名称: {request.invention_title}")
        logger.info(f"技术领域: {request.technology_field}")

        try:
            # 第一步:知识库检索
            logger.info("步骤1: 执行知识库检索...")
            knowledge_results = await self._knowledge_retrieval(request)

            # 第二步:专家团队分析
            logger.info("步骤2: 启动专家团队分析...")
            expert_analysis = await self._expert_team_analysis(request, knowledge_results)

            # 第三步:LLM增强分析
            logger.info("步骤3: 执行LLM增强分析...")
            llm_results = await self._llm_enhanced_analysis(
                request, expert_analysis, knowledge_results
            )

            # 第四步:综合专利性分析
            logger.info("步骤4: 进行综合专利性分析...")
            patentability = await self._patentability_analysis(
                request, expert_analysis, llm_results
            )

            # 第五步:风险评估
            logger.info("步骤5: 执行风险评估...")
            risk_assessment = await self._risk_assessment(
                request, expert_analysis, knowledge_results
            )

            # 第六步:生成建议和行动计划
            logger.info("步骤6: 生成建议和行动计划...")
            recommendations, next_steps = await self._generate_recommendations(
                request, patentability, risk_assessment
            )

            # 第七步:准备支持文档
            logger.info("步骤7: 准备支持文档...")
            supporting_docs = await self._prepare_supporting_documents(
                request, expert_analysis, knowledge_results
            )

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()

            # 构建分析摘要
            analysis_summary = {
                "invention_title": request.invention_title,
                "technology_field": request.technology_field,
                "analysis_type": request.analysis_type,
                "expert_team_size": len(expert_analysis.team_composition),
                "patentability_score": patentability.get("overall_score", 0),
                "risk_level": risk_assessment.get("overall_risk", "unknown"),
                "key_findings": patentability.get("key_findings", []),
                "major_risks": risk_assessment.get("major_risks", []),
                "success_probability": patentability.get("success_probability", 0),
            }

            # 计算置信度分数
            confidence_scores = {
                "patentability": patentability.get("confidence", 0.7),
                "risk_assessment": risk_assessment.get("confidence", 0.7),
                "expert_consensus": expert_analysis.confidence_score,
                "llm_analysis": llm_results.get("confidence", 0.7),
                "overall": self._calculate_overall_confidence(
                    patentability, risk_assessment, expert_analysis
                ),
            }

            # 创建结果对象
            result = PatentAnalysisResult(
                request_id=request.request_id,
                analysis_summary=analysis_summary,
                expert_team_analysis=expert_analysis,
                patentability_analysis=patentability,
                risk_assessment=risk_assessment,
                recommendations=recommendations,
                next_steps=next_steps,
                supporting_documents=supporting_docs,
                confidence_scores=confidence_scores,
                processing_time=processing_time,
                timestamp=datetime.now(),
            )

            # 记录工作流历史
            workflow_record = {
                "request_id": request.request_id,
                "processing_time": processing_time,
                "analysis_type": request.analysis_type,
                "expert_team_size": len(expert_analysis.team_composition),
                "patentability_score": patentability.get("overall_score", 0),
                "risk_level": risk_assessment.get("overall_risk", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }
            self.workflow_history.append(workflow_record)

            logger.info(f"专利分析完成: {request.request_id}, 耗时: {processing_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"专利分析处理失败: {e!s}")
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def _knowledge_retrieval(
        self, request: PatentAnalysisRequest
    ) -> dict[str, KnowledgeResult]:
        """知识库检索"""
        knowledge_results = {}

        # 构建查询
        query = KnowledgeQuery(
            query_text=request.invention_description,
            query_type="hybrid",
            technology_field=request.technology_field,
            limit=10,
        )

        # 执行混合搜索
        hybrid_result = await self.knowledge_connector.hybrid_search(query)
        knowledge_results["hybrid_search"] = hybrid_result

        # 执行专项搜索
        similar_patents = await self.knowledge_connector.search_similar_patents(query)
        knowledge_results["similar_patents"] = similar_patents

        legal_precedents = await self.knowledge_connector.search_legal_precedents(query)
        knowledge_results["legal_precedents"] = legal_precedents

        technical_insights = await self.knowledge_connector.search_technical_insights(query)
        knowledge_results["technical_insights"] = technical_insights

        # 获取领域知识
        domain_knowledge = await self.knowledge_connector.get_domain_knowledge(
            request.technology_field
        )
        knowledge_results["domain_knowledge"] = domain_knowledge

        return knowledge_results

    async def _expert_team_analysis(
        self, request: PatentAnalysisRequest, knowledge_results: dict[str, KnowledgeResult]
    ) -> ExpertTeamAnalysis:
        """专家团队分析"""
        # 创建专利上下文
        PatentContext(
            technology_field=request.technology_field,
            patent_type="发明专利",
            analysis_stage=request.analysis_type,
            user_intent=f"分析{request.invention_title}的专利前景",
            technical_complexity=self._assess_technical_complexity(request),
            deadline_requirement=request.deadline_requirement or "正常",
            target_jurisdiction=request.target_jurisdiction,
        )

        # 构建增强的技术描述
        enhanced_description = request.invention_description

        if knowledge_results.get("domain_knowledge"):
            domain_knowledge = knowledge_results.get("domain_knowledge")
            enhanced_description += "\n\n[领域背景]\n"
            enhanced_description += (
                f"关键概念: {', '.join(domain_knowledge.get('key_concepts', []))}\n"  # type: ignore
            )
            enhanced_description += (
                f"常见问题: {', '.join(domain_knowledge.get('common_issues', []))}\n"  # type: ignore
            )

        if knowledge_results.get("similar_patents"):
            similar_patents = knowledge_results.get("similar_patents").results[:3]  # type: ignore
            enhanced_description += "\n[相关技术参考]\n"
            for patent in similar_patents:
                enhanced_description += f"- {patent['title']}: {patent['abstract'][:100]}...\n"

        # 执行专家团队分析
        team_analysis = await self.expert_system.analyze_with_expert_team(
            technology_field=request.technology_field,
            ipc_section=self._get_ipc_section(request.technology_field),
            patent_type="发明专利",
            analysis_type=request.analysis_type,
            technical_description=enhanced_description,
            user_requirements=request.user_requirements,
        )

        return team_analysis

    async def _llm_enhanced_analysis(
        self,
        request: PatentAnalysisRequest,
        expert_analysis: ExpertTeamAnalysis,
        knowledge_results: dict[str, KnowledgeResult],
    ) -> dict[str, Any]:
        """LLM增强分析"""
        # 构建专家上下文
        expert_context = {
            "team_composition": [
                f"{expert['name']}({expert['type']})" for expert in expert_analysis.team_composition
            ],
            "expert_opinions": expert_analysis.individual_opinions,
            "consensus": expert_analysis.consensus_opinion,
            "confidence": expert_analysis.confidence_score,
        }

        # 构建知识库上下文
        knowledge_context = {}
        if "similar_patents" in knowledge_results:
            knowledge_context["similar_patents"] = knowledge_results.get("similar_patents").results  # type: ignore
        if "legal_precedents" in knowledge_results:
            knowledge_context["legal_precedents"] = knowledge_results.get("legal_precedents").results  # type: ignore
        if "technical_insights" in knowledge_results:
            knowledge_context["technical_insights"] = knowledge_results[
                "technical_insights"
            ].results

        # 构建LLM提示词
        prompt = f"""
请基于专家团队分析和知识库检索结果,对以下发明进行专利性分析:

[发明信息]
- 发明名称: {request.invention_title}
- 技术领域: {request.technology_field}
- 技术描述: {request.invention_description}
- 用户需求: {', '.join(request.user_requirements)}

[专家团队共识]
{expert_analysis.consensus_opinion}

[分析要求]
请从以下角度进行分析:
1. 新颖性分析
2. 创造性分析
3. 实用性分析
4. 专利申请策略
5. 风险评估

请提供详细的分析结论和具体建议。
        """

        # 创建LLM请求
        llm_request = LLMRequest(
            prompt=prompt,
            expert_context=expert_context,
            knowledge_context=knowledge_context,
            system_message="你是星河系列专利专家团队的AI助手,具有深厚的专利分析专业知识。",
        )

        # 调用LLM
        async with self.llm_interface as llm:
            llm_response = await llm.call_llm(llm_request)

        return {
            "llm_content": llm_response.content,
            "confidence": llm_response.confidence_score,
            "reasoning_chain": llm_response.reasoning_chain,
            "expert_analysis": llm_response.expert_analysis,
        }

    async def _patentability_analysis(
        self,
        request: PatentAnalysisRequest,
        expert_analysis: ExpertTeamAnalysis,
        llm_results: dict[str, Any],    ) -> dict[str, Any]:
        """专利性分析"""
        # 提取专家和LLM的关键结论
        expert_conclusions = (
            expert_analysis.conclusions if hasattr(expert_analysis, "conclusions") else []
        )
        llm_content = llm_results.get("llm_content", "")

        # 分析新颖性
        novelty_score = self._analyze_novelty(request, expert_analysis, knowledge_results=None)

        # 分析创造性
        inventive_score = self._analyze_inventive_step(request, expert_analysis, llm_content)

        # 分析实用性
        utility_score = self._analyze_utility(request, expert_analysis)

        # 综合评分
        overall_score = (novelty_score + inventive_score + utility_score) / 3

        # 确定成功概率
        success_probability = self._calculate_success_probability(
            overall_score, expert_analysis.confidence_score
        )

        # 提取关键发现
        key_findings = [
            f"新颖性评分: {novelty_score:.2f}/1.0",
            f"创造性评分: {inventive_score:.2f}/1.0",
            f"实用性评分: {utility_score:.2f}/1.0",
            f"专家团队置信度: {expert_analysis.confidence_score:.2f}",
        ]

        return {
            "novelty_score": novelty_score,
            "inventive_score": inventive_score,
            "utility_score": utility_score,
            "overall_score": overall_score,
            "success_probability": success_probability,
            "key_findings": key_findings,
            "conclusions": expert_conclusions,
            "confidence": expert_analysis.confidence_score,
        }

    async def _risk_assessment(
        self,
        request: PatentAnalysisRequest,
        expert_analysis: ExpertTeamAnalysis,
        knowledge_results: dict[str, KnowledgeResult],
    ) -> dict[str, Any]:
        """风险评估"""
        risks = []

        # 分析现有技术风险
        similar_patents = knowledge_results.get(
            "similar_patents",
            KnowledgeResult(
                query_id="",
                results=[],
                query_time=0,
                total_found=0,
                source_types=[],
                relevance_scores=[],
            ),
        )
        if similar_patents.results:
            high_similarity_patents = [
                p for p in similar_patents.results if p.get("similarity_score", 0) > 0.7
            ]
            if high_similarity_patents:
                risks.append(
                    {
                        "type": "novelty_risk",
                        "description": f"发现{len(high_similarity_patents)}件高相似度专利",
                        "severity": "high",
                        "mitigation": "需要进行详细的现有技术对比分析",
                    }
                )

        # 分析法律风险
        legal_precedents = knowledge_results.get(
            "legal_precedents",
            KnowledgeResult(
                query_id="",
                results=[],
                query_time=0,
                total_found=0,
                source_types=[],
                relevance_scores=[],
            ),
        )
        if legal_precedents.results:
            risks.append(
                {
                    "type": "legal_risk",
                    "description": f"相关法律先例{len(legal_precedents.results)}项",
                    "severity": "medium",
                    "mitigation": "需要评估法律先例对本案的影响",
                }
            )

        # 分析技术实施风险
        technical_complexity = self._assess_technical_complexity(request)
        if technical_complexity == "高":
            risks.append(
                {
                    "type": "technical_risk",
                    "description": "技术方案复杂度高",
                    "severity": "medium",
                    "mitigation": "需要确保技术方案的充分公开",
                }
            )

        # 分析专家识别的风险
        if hasattr(expert_analysis, "risk_assessment") and expert_analysis.risk_assessment:
            expert_risks = expert_analysis.risk_assessment
            if isinstance(expert_risks, dict):  # type: ignore
                for risk_type, risk_list in expert_risks.items():
                    if risk_type != "overall_risk_level" and isinstance(risk_list, list):
                        for risk_item in risk_list:
                            if isinstance(risk_item, str):
                                risks.append(
                                    {
                                        "type": f"expert_{risk_type}",
                                        "description": risk_item,
                                        "severity": "medium",
                                        "mitigation": "根据专家建议制定应对策略",
                                    }
                                )

        # 计算整体风险等级
        high_risks = [r for r in risks if r["severity"] == "high"]
        medium_risks = [r for r in risks if r["severity"] == "medium"]

        if high_risks:
            overall_risk = "high"
        elif medium_risks:
            overall_risk = "medium"
        else:
            overall_risk = "low"

        # 提取主要风险
        major_risks = [
            risk["description"] for risk in risks if risk["severity"] in ["high", "medium"]
        ]

        return {
            "overall_risk": overall_risk,
            "risk_list": risks,
            "major_risks": major_risks,
            "risk_mitigation_strategies": [r["mitigation"] for r in risks],
            "confidence": expert_analysis.confidence_score,
        }

    async def _generate_recommendations(
        self,
        request: PatentAnalysisRequest,
        patentability: dict[str, Any],        risk_assessment: dict[str, Any],    ) -> tuple[list[str], list[str]]:
        """生成建议和下一步行动"""
        recommendations = []
        next_steps = []

        # 基于专利性评分生成建议
        overall_score = patentability.get("overall_score", 0)

        if overall_score >= 0.8:
            recommendations.append("建议尽快提交专利申请,技术方案具备较高的专利价值")
            next_steps.append("准备专利申请文件")
            next_steps.append("进行现有技术检索")
        elif overall_score >= 0.6:
            recommendations.append("技术方案具备一定的专利性,建议优化后申请")
            next_steps.append("完善技术方案细节")
            next_steps.append("增强创新点")
        else:
            recommendations.append("建议重新评估技术方案的创新性和实用性")
            next_steps.append("进行技术改进")
            next_steps.append("寻找新的创新点")

        # 基于风险评估生成建议
        overall_risk = risk_assessment.get("overall_risk", "low")

        if overall_risk == "high":
            recommendations.append("存在较高风险,建议进行全面的风险管控")
            next_steps.append("制定风险缓解策略")
            next_steps.append("加强现有技术检索")
        elif overall_risk == "medium":
            recommendations.append("存在中等风险,建议采取预防措施")
            next_steps.append("监控相关技术发展")
            next_steps.append("准备应对策略")

        # 添加通用建议
        recommendations.extend(
            ["建议咨询专业的专利代理人", "考虑进行专利布局规划", "重视技术细节的充分公开"]
        )

        next_steps.extend(
            ["联系专利代理人进行详细咨询", "制定专利申请策略", "建立技术文档管理体系"]
        )

        return recommendations[:8], next_steps[:8]  # 限制数量

    async def _prepare_supporting_documents(
        self,
        request: PatentAnalysisRequest,
        expert_analysis: ExpertTeamAnalysis,
        knowledge_results: dict[str, KnowledgeResult],
    ) -> list[dict[str, Any]]:
        """准备支持文档"""
        documents = []

        # 专家团队分析报告
        documents.append(
            {
                "type": "expert_analysis",
                "title": "专家团队分析报告",
                "content": expert_analysis.consensus_opinion,
                "format": "markdown",
                "confidence": expert_analysis.confidence_score,
            }
        )

        # 相似专利检索报告
        if "similar_patents" in knowledge_results:
            patents_result = knowledge_results.get("similar_patents")
            documents.append(
                {
                    "type": "patent_search",
                    "title": "相似专利检索报告",
                    "content": f"找到{patents_result.total_found}件相关专利",  # type: ignore
                    "details": patents_result.results[:5],  # type: ignore
                    "format": "json",
                    "confidence": 0.8,
                }
            )

        # 法律先例分析报告
        if "legal_precedents" in knowledge_results:
            legal_result = knowledge_results.get("legal_precedents")
            documents.append(
                {
                    "type": "legal_analysis",
                    "title": "相关法律先例分析",
                    "content": f"找到{legal_result.total_found}项相关法律先例",  # type: ignore
                    "details": legal_result.results[:3],  # type: ignore
                    "format": "json",
                    "confidence": 0.7,
                }
            )

        # 技术洞察报告
        if "technical_insights" in knowledge_results:
            tech_result = knowledge_results.get("technical_insights")
            documents.append(
                {
                    "type": "technical_insights",
                    "title": "技术发展洞察",
                    "content": f"找到{tech_result.total_found}项相关技术洞察",  # type: ignore
                    "details": tech_result.results[:3],  # type: ignore
                    "format": "json",
                    "confidence": 0.8,
                }
            )

        return documents

    def _assess_technical_complexity(self, request: PatentAnalysisRequest) -> str:
        """评估技术复杂度"""
        complexity_keywords = {
            "high": ["深度学习", "神经网络", "量子", "人工智能", "生物技术", "纳米技术"],
            "medium": ["机器学习", "算法", "系统", "平台", "优化"],
            "low": ["方法", "装置", "结构", "简单", "基础"],
        }

        description_lower = request.invention_description.lower()

        for level, keywords in complexity_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    return level

        return "medium"

    def _get_ipc_section(self, technology_field: str) -> str:
        """获取IPC分类号"""
        field_mapping = {
            "人工智能": "G",
            "医疗AI": "G",
            "通信技术": "H",
            "化学工程": "C",
            "机械制造": "F",
            "建筑": "E",
            "纺织": "D",
            "农业": "A",
        }
        return field_mapping.get(technology_field, "G")

    def _analyze_novelty(
        self,
        request: PatentAnalysisRequest,
        expert_analysis: ExpertTeamAnalysis,
        knowledge_results=None,  # type: ignore
    ) -> float:
        """分析新颖性"""
        base_score = 0.7

        # 基于专家团队置信度调整
        base_score += expert_analysis.confidence_score * 0.2

        # 基于专家共识调整
        if (
            "新颖" in expert_analysis.consensus_opinion
            or "创新" in expert_analysis.consensus_opinion
        ):
            base_score += 0.1

        return min(base_score, 1.0)

    def _analyze_inventive_step(
        self, request: PatentAnalysisRequest, expert_analysis: ExpertTeamAnalysis, llm_content: str
    ) -> float:
        """分析创造性"""
        base_score = 0.6

        # 基于LLM分析内容
        if "创造性" in llm_content and "显著" in llm_content:
            base_score += 0.2

        # 基于专家分析
        if "创造性" in expert_analysis.consensus_opinion:
            base_score += 0.2

        return min(base_score, 1.0)

    def _analyze_utility(
        self, request: PatentAnalysisRequest, expert_analysis: ExpertTeamAnalysis
    ) -> float:
        """分析实用性"""
        # 通常实用性问题较少,给较高基础分
        base_score = 0.8

        # 检查是否有实用性相关的讨论
        if (
            "实用" in expert_analysis.consensus_opinion
            or "应用" in expert_analysis.consensus_opinion
        ):
            base_score += 0.1

        return min(base_score, 1.0)

    def _calculate_success_probability(
        self, patentability_score: float, confidence_score: float
    ) -> float:
        """计算成功概率"""
        # 综合专利性评分和置信度计算成功概率
        return patentability_score * 0.7 + confidence_score * 0.3

    def _calculate_overall_confidence(
        self,
        patentability: dict[str, Any],        risk_assessment: dict[str, Any],        expert_analysis: ExpertTeamAnalysis,
    ) -> float:
        """计算整体置信度"""
        patentability_conf = patentability.get("confidence", 0.7)
        risk_conf = risk_assessment.get("confidence", 0.7)
        expert_conf = expert_analysis.confidence_score

        return (patentability_conf + risk_conf + expert_conf) / 3

    def get_workflow_statistics(self) -> dict[str, Any]:
        """获取工作流统计信息"""
        if not self.workflow_history:
            return {"total_processed": 0}

        total_processed = len(self.workflow_history)
        avg_processing_time = (
            sum(record["processing_time"] for record in self.workflow_history) / total_processed
        )

        analysis_types = {}
        for record in self.workflow_history:
            analysis_type = record["analysis_type"]
            analysis_types[analysis_type] = analysis_types.get(analysis_type, 0) + 1

        avg_patentability_score = (
            sum(record["patentability_score"] for record in self.workflow_history) / total_processed
        )

        return {
            "total_processed": total_processed,
            "average_processing_time": avg_processing_time,
            "analysis_types": analysis_types,
            "average_patentability_score": avg_patentability_score,
            "most_common_analysis_type": (
                max(analysis_types.items(), key=lambda x: x[1]) if analysis_types else None  # type: ignore
            ),
            "latest_analysis": (
                self.workflow_history[-1]["timestamp"] if self.workflow_history else None
            ),
        }

    async def cleanup(self):
        """清理资源"""
        await self.knowledge_connector.cleanup()
        await self.expert_system.cleanup()
        logger.info("小娜专利分析工作流资源清理完成")


# 便捷函数
async def analyze_patent_with_experts(
    invention_title: str,
    technology_field: str,
    invention_description: str,
    user_requirements: Optional[list[str]] = None,
) -> PatentAnalysisResult:
    """便捷的专利分析函数"""
    workflow = XiaonaPatentWorkflow()
    await workflow.initialize()

    request = PatentAnalysisRequest(
        request_id=f"REQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        invention_title=invention_title,
        technology_field=technology_field,
        invention_description=invention_description,
        analysis_type="comprehensive",
        user_requirements=user_requirements or [],
    )

    return await workflow.process_patent_analysis(request)

