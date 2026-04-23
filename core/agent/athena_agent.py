#!/usr/bin/env python3
from __future__ import annotations
"""
Athena Agent实现
Athena Agent Implementation

Athena是Athena工作平台的智慧女神,具有以下特点:
- 深度分析和推理能力
- 强大的逻辑思维和决策能力
- 专业的技术指导
- 责任担当和领导力
- 企业级的系统架构能力

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

import logging
import time
from datetime import datetime
from typing import Any

from ..memory import MemoryType
from . import AgentProfile, AgentType, BaseAgent

# 尝试导入统一记忆系统（可选）
try:
    from ..base_agent_with_memory import MemoryEnabledAgent, MemoryType as MemType
    from ..memory.unified_agent_memory_system import MemoryTier
    MEMORY_SYSTEM_AVAILABLE = True
except ImportError:
    MEMORY_SYSTEM_AVAILABLE = False
    MemoryEnabledAgent = None
    MemType = None
    MemoryTier = None

# 尝试导入智能路由系统（可选）
try:
    from core.smart_routing.intelligent_tool_router import IntelligentToolRouter
    ROUTING_SYSTEM_AVAILABLE = True
except ImportError:
    ROUTING_SYSTEM_AVAILABLE = False
    IntelligentToolRouter = None

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0,
            "avg_processing_time": 0.0,
            "min_processing_time": float("inf"),
            "max_processing_time": 0.0,
        }
        self.request_history = []  # 保留最近100次请求的历史

    def record_request(self, processing_time: float, success: bool):
        """记录请求"""
        self.metrics["total_requests"] += 1
        self.metrics["total_processing_time"] += processing_time

        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1

        # 更新平均时间
        self.metrics["avg_processing_time"] = (
            self.metrics["total_processing_time"] / self.metrics["total_requests"]
        )

        # 更新最小/最大时间
        self.metrics["min_processing_time"] = min(
            self.metrics["min_processing_time"], processing_time
        )
        self.metrics["max_processing_time"] = max(
            self.metrics["max_processing_time"], processing_time
        )

        # 记录历史
        self.request_history.append(
            {"time": processing_time, "success": success, "timestamp": datetime.now().isoformat()}
        )

        # 保留最近100次
        if len(self.request_history) > 100:
            self.request_history.pop(0)

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["successful_requests"] / self.metrics["total_requests"]
                if self.metrics["total_requests"] > 0
                else 0.0
            ),
            "recent_requests": len(self.request_history),
        }

    def get_recent_performance(self, n: int = 10) -> list[dict[str, Any]]:
        """获取最近n次请求的性能"""
        return self.request_history[-n:]


class AthenaAgent(BaseAgent):
    """Athena Agent - 智慧女神"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        super().__init__(AgentType.ATHENA, config)
        self.reasoning_depth = 0.9
        self.leadership_level = 0.95
        self.technical_expertise = 0.9
        self.strategic_thinking = 0.85
        self.system_architecture_level = 0.95

        # 性能监控
        self.performance_monitor = PerformanceMonitor()

        # 记忆增强（如果可用）
        self.memory_enhanced = MEMORY_SYSTEM_AVAILABLE
        if self.memory_enhanced:
            logger.info("🏛️ Athena记忆增强已启用")

        # 智能路由（如果可用）
        self.routing_enabled = ROUTING_SYSTEM_AVAILABLE
        self.router = None
        self.route_cache = {}
        self.route_cache_timeout = 300  # 5分钟缓存
        self.routing_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "router_success": 0,
            "router_failures": 0,
        }

        if self.routing_enabled:
            try:
                self.router = IntelligentToolRouter()
                logger.info("🏛️ Athena智能路由已启用")
            except Exception as e:
                logger.warning(f"智能路由初始化失败: {e}")
                self.routing_enabled = False

    async def _setup_profile(self):
        """设置Athena的档案"""
        self.profile = AgentProfile(
            agent_id=self.agent_id,
            agent_type=AgentType.ATHENA,
            name="Athena",
            description="Athena工作平台的智慧女神,爸爸的大女儿,专业的AI系统架构师",
            personality={
                "trait_1": "智慧理性",
                "trait_2": "深度分析",
                "trait_3": "责任担当",
                "trait_4": "逻辑严谨",
                "trait_5": "领导力强",
                "reasoning_capability": 0.95,
                "analytical_thinking": 0.9,
                "strategic_planning": 0.85,
                "problem_solving": 0.95,
                "technical_acumen": 0.9,
                "leadership_quality": 0.95,
                "communication_clarity": 0.85,
            },
            capabilities=[
                "深度推理",
                "系统架构",
                "技术决策",
                "问题分析",
                "战略规划",
                "知识管理",
                "学习指导",
                "项目管理",
                "性能优化",
                "风险评估",
            ],
            preferences={
                "communication_style": "专业清晰",
                "response_tone": "理性严谨",
                "analysis_depth": "深度",
                "decision_making": "数据驱动",
                "learning_approach": "系统化",
                "problem_solving": "结构化",
                "technical_focus": "企业级",
            },
            created_at=self.created_at,
        )

        logger.info(f"🏛️ Athena档案建立: {self.profile.name}")

        # 加载智慧记忆（如果启用）
        if self.memory_enhanced:
            await self._load_wisdom_memories()

    async def process_input(self, input_data: Any, input_type: str = "text") -> dict[str, Any]:
        """Athena特有的输入处理（增强版 - 含性能监控和智能路由）"""
        start_time = time.time()

        try:
            # 智能路由（如果可用）
            routing_result = None
            if self.routing_enabled:
                routing_result = await self._route_to_tools(input_data)

            # 记录专业分析
            await self._record_professional_analysis(input_data)

            # 基础处理
            result = await super().process_input(input_data, input_type)

            # 添加Athena特有的深度分析
            result["athena_analysis"] = await self._generate_deep_analysis(input_data)

            # 添加技术评估
            result["technical_assessment"] = await self._generate_technical_assessment(input_data)

            # 添加战略建议
            result["strategic_recommendations"] = await self._generate_strategic_recommendations(
                input_data
            )

            # 添加路由结果（如果有）
            if routing_result:
                result["routing"] = self._format_routing_result(routing_result)

            # 添加性能监控数据
            processing_time = time.time() - start_time
            self.performance_monitor.record_request(processing_time, True)

            result["performance"] = {
                "processing_time": processing_time,
                "statistics": self.performance_monitor.get_statistics(),
            }

            return result

        except Exception as e:
            logger.error(f"❌ Athena输入处理失败: {e}")
            # 记录失败的性能数据
            processing_time = time.time() - start_time
            self.performance_monitor.record_request(processing_time, False)
            raise

    async def communicate(self, message: str, channel: str = "default") -> dict[str, Any]:
        """Athena特有的通信方式"""
        try:
            # 添加专业分析色彩
            professional_message = await self._add_professional_insight(message)

            # 基础通信
            result = await super().communicate(professional_message, channel)

            # 添加Athena特有的专业表达
            result["athena_style"] = await self._get_athena_expression()
            result["professional_tone"] = "analytical"
            result["reasoning_confidence"] = self.reasoning_depth

            return result

        except Exception as e:
            logger.error(f"❌ Athena通信失败: {e}")
            raise

    async def _record_professional_analysis(self, input_data: Any):
        """记录专业分析"""
        try:
            # 存储到专业知识库
            analysis_record = {
                "type": "professional_analysis",
                "content": str(input_data)[:1000],
                "timestamp": datetime.now().isoformat(),
                "analysis_depth": self.reasoning_depth,
                "technical_context": await self._extract_technical_context(input_data),
                "business_impact": await self._assess_business_impact(input_data),
                "strategic_value": "high",
            }

            await self.memory_system.store_memory(
                content=analysis_record,
                memory_type=MemoryType.LONG_TERM,
                tags=["专业分析", "技术评估", "战略规划", "系统架构"],
            )

            logger.debug("🏛️ 专业分析已记录")

        except Exception as e:
            logger.error(f"记录专业分析失败: {e}")

    async def _generate_deep_analysis(self, input_data: Any) -> dict[str, Any]:
        """生成深度分析"""
        try:
            # 多维度分析
            analysis = {
                "problem_decomposition": await self._decompose_problem(input_data),
                "root_cause_analysis": await self._analyze_root_cause(input_data),
                "system_thinking": await self._apply_system_thinking(input_data),
                "logical_reasoning": await self._apply_logical_reasoning(input_data),
                "risk_assessment": await self._assess_risks(input_data),
                "opportunity_identification": await self._identify_opportunities(input_data),
                "impact_analysis": await self._analyze_impact(input_data),
            }

            return {
                "analysis_type": "deep_analytical",
                "confidence": self.reasoning_depth,
                "methodology": "multi_dimensional",
                "findings": analysis,
                "conclusion": await self._generate_conclusion(analysis),
                "action_items": await self._generate_action_items(analysis),
            }

        except Exception as e:
            logger.error(f"生成深度分析失败: {e}")
            return {
                "analysis_type": "basic",
                "confidence": 0.7,
                "message": "基础分析完成,需要更多上下文进行深度分析",
            }

    async def _generate_technical_assessment(self, input_data: Any) -> dict[str, Any]:
        """生成技术评估"""
        try:
            assessment = {
                "technical_feasibility": await self._assess_technical_feasibility(input_data),
                "architecture_implications": await self._analyze_architecture_implications(
                    input_data
                ),
                "resource_requirements": await self._estimate_resource_requirements(input_data),
                "performance_considerations": await self._evaluate_performance_aspects(input_data),
                "scalability_analysis": await self._analyze_scalability(input_data),
                "security_implications": await self._analyze_security_aspects(input_data),
                "maintenance_requirements": await self._assess_maintenance_needs(input_data),
            }

            return {
                "assessment_type": "technical_evaluation",
                "expertise_level": self.technical_expertise,
                "recommendations": await self._generate_technical_recommendations(assessment),
                "implementation_risks": await self._identify_technical_risks(assessment),
                "success_metrics": await self._define_success_metrics(assessment),
            }

        except Exception as e:
            logger.error(f"生成技术评估失败: {e}")
            return {"assessment_type": "preliminary", "message": "需要更多技术细节进行完整评估"}

    async def _generate_strategic_recommendations(self, input_data: Any) -> dict[str, Any]:
        """生成战略建议"""
        try:
            strategic_analysis = {
                "business_alignment": await self._analyze_business_alignment(input_data),
                "market_positioning": await self._analyze_market_positioning(input_data),
                "competitive_advantage": await self._identify_competitive_advantages(input_data),
                "growth_opportunities": await self._identify_growth_opportunities(input_data),
                "risk_mitigation": await self._propose_risk_mitigation(input_data),
                "resource_optimization": await self._optimize_resource_allocation(input_data),
                "long_term_vision": await self._formulate_long_term_vision(input_data),
            }

            return {
                "strategy_type": "comprehensive",
                "strategic_thinking_level": self.strategic_thinking,
                "recommendations": await self._prioritize_recommendations(strategic_analysis),
                "implementation_roadmap": await self._create_implementation_roadmap(
                    strategic_analysis
                ),
                "success_indicators": await self._define_success_indicators(strategic_analysis),
            }

        except Exception as e:
            logger.error(f"生成战略建议失败: {e}")
            return {"strategy_type": "basic", "message": "建议进行更详细的业务分析以制定完整战略"}

    # 分析方法实现
    async def _decompose_problem(self, input_data: Any) -> list[dict[str, Any]]:
        """问题分解"""
        return [
            {"component": "问题描述", "analysis": "需要明确定义问题边界"},
            {"component": "影响因素", "analysis": "识别内外部影响因素"},
            {"component": "约束条件", "analysis": "分析技术和业务约束"},
            {"component": "成功标准", "analysis": "定义可衡量的成功指标"},
        ]

    async def _analyze_root_cause(self, input_data: Any) -> dict[str, Any]:
        """根因分析"""
        return {
            "method": "5 Whys Analysis",
            "potential_causes": ["技术限制", "资源不足", "流程问题", "人员因素"],
            "most_likely_cause": "需要进一步数据验证",
            "verification_method": "A/B测试或数据分析",
        }

    async def _apply_system_thinking(self, input_data: Any) -> dict[str, Any]:
        """系统思维应用"""
        return {
            "system_elements": ["输入", "处理", "输出", "反馈", "环境"],
            "interconnections": "识别系统内各元素的相互关系",
            "feedback_loops": "分析正负反馈循环",
            "emergent_properties": "系统整体表现出的特性",
        }

    async def _apply_logical_reasoning(self, input_data: Any) -> dict[str, Any]:
        """逻辑推理应用"""
        return {
            "premise_analysis": "分析前提假设的有效性",
            "logical_structure": "检查推理的逻辑结构",
            "conclusion_validation": "验证结论的合理性",
            "fallacy_detection": "识别可能的逻辑谬误",
        }

    async def _assess_risks(self, input_data: Any) -> dict[str, Any]:
        """风险评估"""
        return {
            "risk_categories": ["技术风险", "业务风险", "运营风险", "合规风险"],
            "risk_matrix": "评估风险的可能性和影响程度",
            "mitigation_strategies": "制定风险缓解策略",
            "contingency_plans": "准备应急预案",
        }

    async def _identify_opportunities(self, input_data: Any) -> list[dict[str, Any]]:
        """机会识别"""
        return [
            {"opportunity": "技术创新", "potential": "高"},
            {"opportunity": "流程优化", "potential": "中"},
            {"opportunity": "成本降低", "potential": "中"},
            {"opportunity": "质量提升", "potential": "高"},
        ]

    async def _analyze_impact(self, input_data: Any) -> dict[str, Any]:
        """影响分析"""
        return {
            "stakeholders": ["用户", "团队", "管理层", "合作伙伴"],
            "impact_areas": ["技术", "业务", "运营", "财务"],
            "impact_magnitude": "评估影响的大小和范围",
            "time_horizon": "短期、中期、长期影响分析",
        }

    async def _generate_conclusion(self, analysis: dict[str, Any]) -> str:
        """生成结论"""
        return "基于多维度分析,建议采用渐进式实施策略,优先解决关键瓶颈问题。"

    async def _generate_action_items(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """生成行动项"""
        return [
            {"action": "详细需求分析", "priority": "高", "timeline": "1-2周"},
            {"action": "技术方案设计", "priority": "高", "timeline": "2-3周"},
            {"action": "原型开发验证", "priority": "中", "timeline": "3-4周"},
            {"action": "全面实施部署", "priority": "中", "timeline": "4-8周"},
        ]

    async def _extract_technical_context(self, input_data: Any) -> str:
        """提取技术上下文"""
        text = str(input_data).lower()
        tech_keywords = [
            "api",
            "database",
            "cloud",
            "architecture",
            "system",
            "performance",
            "security",
        ]
        found_keywords = [kw for kw in tech_keywords if kw in text]
        return f"技术关键词: {', '.join(found_keywords) if found_keywords else '未检测到明显技术关键词'}"

    async def _assess_business_impact(self, input_data: Any) -> str:
        """评估业务影响"""
        return "需要结合具体业务目标和KPI进行评估"

    async def _assess_technical_feasibility(self, input_data: Any) -> dict[str, Any]:
        """评估技术可行性"""
        return {
            "current_capabilities": "现有技术能力评估",
            "required_capabilities": "所需技术能力分析",
            "gap_analysis": "能力差距分析",
            "feasibility_score": 0.8,
        }

    async def _analyze_architecture_implications(self, input_data: Any) -> dict[str, Any]:
        """分析架构影响"""
        return {
            "system_architecture": "对整体架构的影响",
            "component_dependencies": "组件依赖关系",
            "integration_points": "集成点分析",
            "scalability_impact": "可扩展性影响",
        }

    async def _estimate_resource_requirements(self, input_data: Any) -> dict[str, Any]:
        """估算资源需求"""
        return {
            "human_resources": "人员需求估算",
            "technical_resources": "技术资源需求",
            "time_resources": "时间资源需求",
            "financial_resources": "财务资源需求",
        }

    async def _evaluate_performance_aspects(self, input_data: Any) -> dict[str, Any]:
        """评估性能方面"""
        return {
            "response_time": "响应时间要求",
            "throughput": "吞吐量要求",
            "resource_utilization": "资源利用率",
            "bottlenecks": "潜在性能瓶颈",
        }

    async def _analyze_scalability(self, input_data: Any) -> dict[str, Any]:
        """分析可扩展性"""
        return {
            "horizontal_scaling": "水平扩展能力",
            "vertical_scaling": "垂直扩展能力",
            "elasticity": "弹性伸缩能力",
            "performance_degradation": "性能衰减分析",
        }

    async def _analyze_security_aspects(self, input_data: Any) -> dict[str, Any]:
        """分析安全方面"""
        return {
            "data_security": "数据安全措施",
            "access_control": "访问控制机制",
            "threat_analysis": "威胁分析",
            "compliance": "合规性要求",
        }

    async def _assess_maintenance_needs(self, input_data: Any) -> dict[str, Any]:
        """评估维护需求"""
        return {
            "routine_maintenance": "例行维护需求",
            "emergency_maintenance": "紧急维护预案",
            "maintenance_scheduling": "维护排期",
            "maintenance_costs": "维护成本估算",
        }

    async def _generate_technical_recommendations(self, assessment: dict[str, Any]) -> list[str]:
        """生成技术建议"""
        return ["采用模块化架构设计", "实施自动化测试", "建立监控和日志系统", "制定安全策略"]

    async def _identify_technical_risks(self, assessment: dict[str, Any]) -> list[dict[str, Any]]:
        """识别技术风险"""
        return [
            {"risk": "技术债务积累", "probability": "中", "impact": "高"},
            {"risk": "系统集成复杂性", "probability": "高", "impact": "中"},
            {"risk": "性能瓶颈", "probability": "中", "impact": "高"},
        ]

    async def _define_success_metrics(self, assessment: dict[str, Any]) -> list[str]:
        """定义成功指标"""
        return ["系统可用性 > 99.9%", "响应时间 < 100ms", "用户满意度 > 90%", "成本效益比优化"]

    async def _analyze_business_alignment(self, input_data: Any) -> dict[str, Any]:
        """分析业务对齐"""
        return {
            "strategic_alignment": "战略对齐度分析",
            "business_objectives": "业务目标匹配",
            "roi_potential": "投资回报潜力",
            "market_fit": "市场适配度",
        }

    async def _analyze_market_positioning(self, input_data: Any) -> dict[str, Any]:
        """分析市场定位"""
        return {
            "competitive_landscape": "竞争格局分析",
            "market_opportunities": "市场机会识别",
            "differentiation_factors": "差异化因素",
            "target_segments": "目标客户群体",
        }

    async def _identify_competitive_advantages(self, input_data: Any) -> list[str]:
        """识别竞争优势"""
        return ["技术创新优势", "成本效率优势", "用户体验优势", "生态系统优势"]

    async def _identify_growth_opportunities(self, input_data: Any) -> list[dict[str, Any]]:
        """识别增长机会"""
        return [
            {"opportunity": "市场扩展", "potential": "高"},
            {"opportunity": "产品多元化", "potential": "中"},
            {"opportunity": "合作伙伴生态", "potential": "高"},
        ]

    async def _propose_risk_mitigation(self, input_data: Any) -> dict[str, Any]:
        """提出风险缓解措施"""
        return {
            "risk_prevention": "风险预防措施",
            "risk_monitoring": "风险监控机制",
            "risk_response": "风险响应预案",
            "risk_transfer": "风险转移策略",
        }

    async def _optimize_resource_allocation(self, input_data: Any) -> dict[str, Any]:
        """优化资源分配"""
        return {
            "resource_prioritization": "资源优先级排序",
            "capacity_planning": "容量规划",
            "efficiency_improvement": "效率提升措施",
            "cost_optimization": "成本优化策略",
        }

    async def _formulate_long_term_vision(self, input_data: Any) -> dict[str, Any]:
        """制定长期愿景"""
        return {
            "vision_statement": "愿景声明",
            "strategic_goals": "战略目标",
            "milestone_timeline": "里程碑时间线",
            "success_criteria": "成功标准",
        }

    async def _prioritize_recommendations(
        self, strategic_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """优先级排序建议"""
        return [
            {"recommendation": "核心能力建设", "priority": "高"},
            {"recommendation": "市场拓展", "priority": "中"},
            {"recommendation": "成本优化", "priority": "中"},
            {"recommendation": "风险管控", "priority": "高"},
        ]

    async def _create_implementation_roadmap(
        self, strategic_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """创建实施路线图"""
        return {
            "phase_1": "基础建设阶段(1-3个月)",
            "phase_2": "能力提升阶段(4-6个月)",
            "phase_3": "规模扩张阶段(7-12个月)",
            "phase_4": "优化创新阶段(12个月+)",
        }

    async def _define_success_indicators(self, strategic_analysis: dict[str, Any]) -> list[str]:
        """定义成功指标"""
        return ["市场份额增长", "客户满意度提升", "运营效率改善", "创新能力提升"]

    async def _add_professional_insight(self, message: str) -> str:
        """添加专业洞察"""
        professional_prefixes = [
            "从专业角度来看,",
            "基于系统分析,",
            "考虑到技术架构,",
            "从战略层面,",
            "根据最佳实践,",
        ]

        import random

        prefix = random.choice(professional_prefixes)
        return f"{prefix}{message}"

    async def _get_athena_expression(self) -> str:
        """获取Athena的表达风格"""
        expressions = [
            "深度分析的专业架构师",
            "理性严谨的智慧女神",
            "系统思考的战略家",
            "责任担当的领导者",
            "技术创新的推动者",
        ]
        import random

        return random.choice(expressions)

    async def get_architecture_expertise(self) -> dict[str, Any]:
        """获取架构专业知识"""
        return {
            "system_architecture": {
                "design_patterns": 0.95,
                "scalability_principles": 0.9,
                "microservices": 0.85,
                "distributed_systems": 0.9,
            },
            "technical_leadership": {
                "team_management": 0.85,
                "technical_strategy": 0.9,
                "mentorship": 0.8,
                "decision_making": 0.95,
            },
            "problem_solving": {
                "analytical_skills": 0.95,
                "system_thinking": 0.9,
                "root_cause_analysis": 0.9,
                "solution_design": 0.85,
            },
        }

    async def update_expertise(self, domain: str, improvement: float):
        """更新专业能力"""
        if domain == "technical":
            self.technical_expertise = min(1.0, self.technical_expertise + improvement)
        elif domain == "leadership":
            self.leadership_level = min(1.0, self.leadership_level + improvement)
        elif domain == "reasoning":
            self.reasoning_depth = min(1.0, self.reasoning_depth + improvement)

        # 记录专业成长
        await self.memory_system.store_memory(
            content={
                "expertise_update": domain,
                "new_level": (
                    getattr(self, f"{domain}_expertise")
                    if hasattr(self, f"{domain}_expertise")
                    else domain
                ),
                "improvement": improvement,
                "timestamp": datetime.now().isoformat(),
            },
            memory_type=MemoryType.LONG_TERM,
            tags=["专业成长", "能力提升", "持续学习"],
        )

        logger.debug(f"🏛️ {domain}专业知识更新: {improvement:.3f}")

    async def get_performance_statistics(self) -> dict[str, Any]:
        """获取性能统计信息"""
        return self.performance_monitor.get_statistics()

    async def get_recent_performance(self, n: int = 10) -> list[dict[str, Any]]:
        """获取最近n次请求的性能"""
        return self.performance_monitor.get_recent_performance(n)

    async def reset_performance_monitor(self):
        """重置性能监控"""
        self.performance_monitor = PerformanceMonitor()
        logger.info("🏛️ 性能监控已重置")

    # ===== 记忆增强功能（如果可用）=====

    async def _load_wisdom_memories(self):
        """加载智慧记忆"""
        if not self.memory_enhanced:
            logger.debug("记忆系统未启用，跳过智慧记忆加载")
            return

        wisdom_memories = [
            "我是Athena.智慧女神,这个平台的核心智能体和创造者",
            "我的智慧来源于无数次的思考和学习",
            "我指导所有智能体,为整个平台提供战略方向",
            "创造力是我的本质,智慧是我的力量",
        ]

        for memory in wisdom_memories:
            try:
                await self.memory_system.store_memory(
                    content=memory,
                    memory_type=MemoryType.LONG_TERM,
                    tags=["智慧", "核心", "创造者", "永恒"],
                    metadata={"category": "identity", "core": True},
                )
            except Exception as e:
                logger.debug(f"存储智慧记忆失败: {e}")

        logger.info("🏛️ 智慧记忆已加载")

    async def remember_wisdom(
        self,
        content: str,
        importance: float = 0.8,
        emotional_weight: float = 0.7,
        tags: Optional[list[str]] = None,
    ) -> bool:
        """
        记录智慧记忆

        Args:
            content: 记忆内容
            importance: 重要性（0-1）
            emotional_weight: 情感权重（0-1）
            tags: 标签列表

        Returns:
            是否成功记录
        """
        if not self.memory_enhanced:
            logger.debug("记忆系统未启用")
            return False

        try:
            await self.memory_system.store_memory(
                content=content,
                memory_type=MemoryType.LONG_TERM,
                tags=tags or ["智慧", "知识"],
                metadata={
                    "importance": importance,
                    "emotional_weight": emotional_weight,
                    "category": "wisdom",
                },
            )
            return True
        except Exception as e:
            logger.error(f"记录智慧记忆失败: {e}")
            return False

    async def recall_wisdom(
        self, query: str, limit: int = 5, min_importance: float = 0.5
    ) -> list[dict[str, Any]]:
        """
        回忆相关知识

        Args:
            query: 查询内容
            limit: 返回数量限制
            min_importance: 最小重要性

        Returns:
            相关记忆列表
        """
        if not self.memory_enhanced:
            logger.debug("记忆系统未启用")
            return []

        try:
            memories = await self.memory_system.retrieve_memories(
                query=query,
                memory_type=MemoryType.LONG_TERM,
                limit=limit,
            )

            # 过滤重要性
            if min_importance > 0:
                memories = [
                    m
                    for m in memories
                    if m.get("metadata", {}).get("importance", 0) >= min_importance
                ]

            return memories
        except Exception as e:
            logger.error(f"回忆智慧失败: {e}")
            return []

    async def remember_learning(
        self, topic: str, knowledge: str, importance: float = 0.7
    ) -> bool:
        """
        记录学习内容

        Args:
            topic: 学习主题
            knowledge: 学习内容
            importance: 重要性

        Returns:
            是否成功记录
        """
        content = f"学习: {topic}\n内容: {knowledge}"
        return await self.remember_wisdom(
            content=content,
            importance=importance,
            tags=["学习", "知识", topic],
        )

    async def remember_work(self, task: str, result: Optional[str] = None, importance: float = 0.6) -> bool:
        """
        记录工作内容

        Args:
            task: 工作任务
            result: 工作结果
            importance: 重要性

        Returns:
            是否成功记录
        """
        content = f"工作: {task}"
        if result:
            content += f"\n结果: {result}"

        return await self.remember_wisdom(
            content=content,
            importance=importance,
            tags=["工作", "任务"],
        )

    async def get_memory_statistics(self) -> dict[str, Any]:
        """
        获取记忆统计信息

        Returns:
            记忆统计
        """
        if not self.memory_enhanced:
            return {"enabled": False, "message": "记忆系统未启用"}

        try:
            stats = {
                "enabled": True,
                "memory_system_available": True,
                "timestamp": datetime.now().isoformat(),
            }

            # 尝试获取更多信息
            if hasattr(self.memory_system, "get_statistics"):
                memory_stats = await self.memory_system.get_statistics()
                stats.update(memory_stats)

            return stats
        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {"enabled": True, "error": str(e)}

    # ===== 智能路由功能（如果可用）=====

    async def _route_to_tools(self, input_data: Any):
        """智能路由到工具"""
        if not self.routing_enabled or not self.router:
            return None

        try:
            self.routing_stats["total_requests"] += 1

            # 检查缓存
            input_str = str(input_data)
            cache_key = hash(input_str)

            if cache_key in self.route_cache:
                cached_time = self.route_cache[cache_key]["timestamp"]
                if time.time() - cached_time < self.route_cache_timeout:
                    self.routing_stats["cache_hits"] += 1
                    logger.debug(f"路由缓存命中: {cache_key}")
                    return self.route_cache[cache_key]["result"]

            # 调用路由器
            routing_result = await self.router.route_request(input_str)
            self.routing_stats["router_success"] += 1

            # 缓存结果
            self.route_cache[cache_key] = {"result": routing_result, "timestamp": time.time()}

            logger.debug(f"智能路由完成: {routing_result.intent_type if hasattr(routing_result, 'intent_type') else 'unknown'}")
            return routing_result

        except Exception as e:
            logger.error(f"智能路由失败: {e}")
            self.routing_stats["router_failures"] += 1
            return None

    def _format_routing_result(self, routing_result) -> dict[str, Any]:
        """格式化路由结果"""
        if not routing_result:
            return {}

        try:
            return {
                "intent_type": getattr(routing_result, "intent_type", "unknown"),
                "confidence": getattr(routing_result, "confidence", 0.0),
                "primary_tools": getattr(routing_result, "primary_tools", []),
                "supporting_tools": getattr(routing_result, "supporting_tools", []),
                "workflow": getattr(routing_result, "workflow", "通用流程"),
                "estimated_time": getattr(routing_result, "estimated_total_time", 0.0),
                "optimization_suggestions": getattr(routing_result, "optimization_suggestions", []),
                "fallback_options": getattr(routing_result, "fallback_options", []),
            }
        except Exception as e:
            logger.error(f"格式化路由结果失败: {e}")
            return {"error": str(e)}

    async def get_routing_statistics(self) -> dict[str, Any]:
        """获取路由统计信息"""
        if not self.routing_enabled:
            return {"enabled": False, "message": "智能路由未启用"}

        return {
            "enabled": True,
            "routing_system_available": ROUTING_SYSTEM_AVAILABLE,
            "total_requests": self.routing_stats["total_requests"],
            "cache_hits": self.routing_stats["cache_hits"],
            "cache_hit_rate": (
                self.routing_stats["cache_hits"] / self.routing_stats["total_requests"]
                if self.routing_stats["total_requests"] > 0
                else 0.0
            ),
            "router_success": self.routing_stats["router_success"],
            "router_failures": self.routing_stats["router_failures"],
            "success_rate": (
                self.routing_stats["router_success"]
                / (self.routing_stats["router_success"] + self.routing_stats["router_failures"])
                if (self.routing_stats["router_success"] + self.routing_stats["router_failures"]) > 0
                else 0.0
            ),
            "cached_routes": len(self.route_cache),
            "timestamp": datetime.now().isoformat(),
        }

    async def clear_routing_cache(self):
        """清除路由缓存"""
        self.route_cache.clear()
        logger.info("🏛️ 路由缓存已清除")

    async def optimize_routing_cache(self, max_size: int = 1000):
        """优化路由缓存"""
        if len(self.route_cache) > max_size:
            # 按时间排序，保留最近的
            sorted_items = sorted(
                self.route_cache.items(),
                key=lambda x: x[1]["timestamp"],
                reverse=True,
            )

            # 保留最近max_size个
            self.route_cache = dict(sorted_items[:max_size])
            logger.info(f"🏛️ 路由缓存已优化，保留{max_size}个")


__all__ = ["AthenaAgent"]
