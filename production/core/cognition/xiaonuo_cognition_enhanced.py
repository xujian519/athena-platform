
# pyright: ignore
# !/usr/bin/env python3
"""
小诺增强认知系统
Xiaonuo Enhanced Cognition System

为小诺量身定制的增强认知系统,注重实用性、专业知识和用户体验

作者: Athena AI系统
创建时间: 2025-12-04
版本: 1.0.0
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .xiaonuo_super_reasoning import (
    XiaonuoReasoningConfig,
    XiaonuoSuperReasoningEngine,
    XiaonuoThinkingMode,
)

logger = logging.getLogger(__name__)


class XiaonuoCognitionMode(Enum):
    """小诺认知模式"""

    HELPER = "helper"  # 助手模式
    EXPERT = "expert"  # 专家模式
    INNOVATOR = "innovator"  # 创新者模式
    COLLABORATOR = "collaborator"  # 协作者模式


@dataclass
class XiaonuoCognitionConfig:
    """小诺认知配置"""

    mode: XiaonuoCognitionMode = XiaonuoCognitionMode.HELPER
    enable_super_reasoning: bool = True
    enable_user_empathy: bool = True
    enable_practical_solutions: bool = True
    enable_domain_expertise: bool = True
    enable_innovation: bool = True
    expertise_domains: list[str] | None = None
    user_context_memory: bool = True
    solution_templates: bool = True

    def __post_init__(self):
        if self.expertise_domains is None:  # type: ignore
            self.expertise_domains = ["general", "patent_law", "technology", "business"]


class XiaonuoCognitionEnhanced:
    """小诺增强认知系统"""

    def __init__(self, config: XiaonuoCognitionConfig | None = None):
        self.config = config or XiaonuoCognitionConfig()
        self.super_reasoning_engine: XiaonuoSuperReasoningEngine | None = None
        self.user_profiles = {}  # 用户档案
        self.interaction_history = []  # 交互历史
        self.expertise_cache = {}  # 专业知识缓存
        self.solution_history = []  # 解决方案历史
        self.performance_metrics = {
            "total_cognitions": 0,
            "user_satisfaction_score": 0.0,
            "solution_effectiveness": 0.0,
            "empathy_accuracy": 0.0,
        }

    async def initialize(self):
        """初始化小诺认知系统"""
        logger.info("🚀 初始化Xiaonuo增强认知系统...")

        # 初始化超级推理引擎
        if self.config.enable_super_reasoning:
            reasoning_config = XiaonuoReasoningConfig(
                thinking_mode=XiaonuoThinkingMode.PRACTICAL_FIRST,
                enable_practical_solutions=self.config.enable_practical_solutions,
                enable_user_empathy=self.config.enable_user_empathy,
                enable_knowledge_integration=self.config.enable_domain_expertise,
                enable_innovative_thinking=self.config.enable_innovation,
            )
            self.super_reasoning_engine = XiaonuoSuperReasoningEngine(reasoning_config)
            await self.super_reasoning_engine.initialize()
            logger.info("✅ 小诺超级推理引擎已初始化")

        # 初始化专业知识库
        await self._initialize_expertise_knowledge()

        # 初始化解决方案模板
        await self._initialize_solution_templates()

        logger.info("✅ Xiaonuo增强认知系统初始化完成")

    async def _initialize_expertise_knowledge(self):
        """初始化专业知识库"""
        for domain in self.config.expertise_domains:
            self.expertise_cache[domain] = {
                "concepts": [],
                "best_practices": [],
                "common_problems": [],
                "solution_patterns": [],
                "resources": [],
            }

        logger.info(f"📚 已初始化{len(self.config.expertise_domains)}个专业领域的知识库")

    async def _initialize_solution_templates(self):
        """初始化解决方案模板"""
        # 预定义解决方案模板
        self.solution_templates = {
            "patent_analysis": {
                "name": "专利分析方案",
                "steps": [
                    "收集专利信息",
                    "进行技术分析",
                    "评估法律状态",
                    "分析市场价值",
                    "制定策略建议",
                ],
                "deliverables": ["分析报告", "风险评估", "建议方案"],
            },
            "technical_problem": {
                "name": "技术问题解决方案",
                "steps": ["问题诊断", "根因分析", "方案设计", "实施计划", "效果验证"],
                "deliverables": ["问题报告", "解决方案", "实施指南"],
            },
            "business_strategy": {
                "name": "商业策略方案",
                "steps": ["市场分析", "竞争评估", "战略制定", "执行计划", "监控调整"],
                "deliverables": ["战略报告", "行动计划", "风险评估"],
            },
        }

    async def cognize_as_xiaonuo(
        self,
        query: str,
        user_id: str | None = None,
        user_context: dict[str, Any] | None = None,
        request_type: str | None = None,
    ) -> dict[str, Any]:
        """小诺风格认知处理"""
        start_time = datetime.now()
        self.performance_metrics["total_cognitions"] += 1

        try:
            # 1. 用户识别和上下文加载
            user_profile = await self._get_user_profile(user_id)
            full_context = await self._merge_contexts(user_context, user_profile)

            # 2. 请求类型分析
            request_analysis = await self._analyze_request_type(query, request_type)

            # 3. 认知模式选择
            cognition_mode = await self._select_cognition_mode(
                query, request_analysis, user_profile
            )

            # 4. 专业领域识别
            expertise_domain = await self._identify_expertise_domain(query, user_profile)

            # 5. 执行超级推理(如果启用)
            if self.super_reasoning_engine:
                reasoning_result = await self.super_reasoning_engine.reason_with_xiaonuo_style(
                    query, full_context, user_profile.get("preferences", {})
                )
            else:
                reasoning_result = await self._basic_cognition(query, full_context)

            # 6. 小诺特色增强
            enhanced_result = await self._apply_xiaonuo_enhancements(
                reasoning_result, cognition_mode, expertise_domain, user_profile, request_analysis
            )

            # 7. 生成实用输出
            final_output = await self._generate_user_friendly_output(
                enhanced_result, cognition_mode, user_profile, expertise_domain
            )

            # 8. 记录和学习
            await self._record_interaction(user_id, query, final_output, cognition_mode)
            await self._learn_from_interaction(query, final_output, user_profile)

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()

            result = {
                "success": True,
                "xiaonuo_response": final_output,
                "cognition_mode": cognition_mode.value,
                "expertise_domain": expertise_domain,
                "processing_time": processing_time,
                "user_profile_updated": bool(user_id),
                "personalization_score": await self._calculate_personalization_score(
                    user_profile, final_output
                ),
                "practicality_score": final_output.get("practicality_score", 0.0),
                "follow_up_suggestions": await self._generate_follow_up_suggestions(
                    query, final_output
                ),
            }

            logger.info(
                f"🎯 小诺认知完成,耗时: {processing_time:.2f}秒,实用评分: {result.get('practicality_score'):.2f}"
            )
            return result

        except Exception as e:
            logger.error(f"❌ 小诺认知出错: {e!s}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "timestamp": start_time.isoformat(),
            }

    async def _get_user_profile(self, user_id: str) -> dict[str, Any]:
        """获取用户档案"""
        if not user_id:
            return {
                "user_type": "new_user",
                "preferences": {},
                "interaction_history": [],
                "expertise_level": "general",
            }

        if user_id not in self.user_profiles:
            # 创建新用户档案
            self.user_profiles[user_id] = {
                "user_id": user_id,
                "user_type": "returning_user",
                "preferences": {},
                "interaction_history": [],
                "expertise_level": "general",
                "preferred_communication_style": "friendly_professional",
                "created_at": datetime.now().isoformat(),
            }

        return self.user_profiles[user_id]

    async def _merge_contexts(
        self, user_context: dict[str, Any], user_profile: dict[str, Any]
    ) -> dict[str, Any]:
        """合并上下文信息"""
        merged = {
            "user_preferences": user_profile.get("preferences", {}),
            "expertise_level": user_profile.get("expertise_level", "general"),
            "interaction_style": user_profile.get(
                "preferred_communication_style", "friendly_professional"
            ),
        }

        if user_context:
            merged.update(user_context)

        return merged

    async def _analyze_request_type(
        self, query: str, request_type: str
    ) -> dict[str, Any]:
        """分析请求类型"""
        if request_type:
            primary_type = request_type
        else:
            # 基于查询内容推断类型
            if any(word in query for word in ["如何", "怎么", "步骤"]):
                primary_type = "guidance"
            elif any(word in query for word in ["分析", "评估", "研究"]):
                primary_type = "analysis"
            elif any(word in query for word in ["解决", "处理", "修复"]):
                primary_type = "problem_solving"
            elif any(word in query for word in ["推荐", "建议", "选择"]):
                primary_type = "recommendation"
            else:
                primary_type = "information"

        return {
            "primary_type": primary_type,
            "complexity": await self._assess_complexity(query),
            "urgency": await self._assess_urgency(query),
            "scope": await self._assess_scope(query),
        }

    async def _assess_complexity(self, query: str) -> str:
        """评估复杂度"""
        complexity_indicators = {
            "high": ["综合", "系统", "整体", "全面", "深入"],
            "medium": ["分析", "研究", "评估", "比较"],
            "low": ["简单", "基础", "入门", "快速"],
        }

        for level, indicators in complexity_indicators.items():
            if any(indicator in query for indicator in indicators):
                return level

        return "medium"

    async def _assess_urgency(self, query: str) -> str:
        """评估紧急性"""
        urgent_words = ["急", "马上", "立即", "尽快", "急需"]
        if any(word in query for word in urgent_words):
            return "high"

        return "normal"

    async def _assess_scope(self, query: str) -> str:
        """评估范围"""
        scope_indicators = {
            "strategic": ["战略", "长期", "整体", "全局"],
            "tactical": ["计划", "方案", "具体", "实施"],
            "operational": ["操作", "执行", "细节", "日常"],
        }

        for scope, indicators in scope_indicators.items():
            if any(indicator in query for indicator in indicators):
                return scope

        return "general"

    async def _select_cognition_mode(
        self, query: str, request_analysis: dict[str, Any], user_profile: dict[str, Any]
    ) -> XiaonuoCognitionMode:
        """选择认知模式"""
        # 基于请求类型
        request_type = request_analysis.get("primary_type", "information")
        complexity = request_analysis.get("complexity", "medium")
        urgency = request_analysis.get("urgency", "normal")

        # 基于用户特征
        expertise_level = user_profile.get("expertise_level", "general")

        # 模式选择逻辑
        if request_type == "guidance" or urgency == "high":
            return XiaonuoCognitionMode.HELPER
        elif complexity == "high" and expertise_level in ["expert", "advanced"]:
            return XiaonuoCognitionMode.EXPERT
        elif "创新" in query or "新" in query:
            return XiaonuoCognitionMode.INNOVATOR
        elif "合作" in query or "团队" in query:
            return XiaonuoCognitionMode.COLLABORATOR
        else:
            return self.config.mode

    async def _identify_expertise_domain(self, query: str, user_profile: dict[str, Any]) -> str:
        """识别专业领域"""
        domain_keywords = {
            "patent_law": ["专利", "发明", "审查", "知识产权", "申请"],
            "technology": ["技术", "系统", "开发", "算法", "软件", "硬件"],
            "business": ["商业", "市场", "管理", "战略", "运营"],
            "legal": ["法律", "法规", "合同", "诉讼", "合规"],
        }

        # 计算每个领域的匹配分数
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query)
            domain_scores[domain] = score

        # 考虑用户偏好
        user_preferences = user_profile.get("preferences", {})
        preferred_domains = user_preferences.get("preferred_domains", [])
        for domain in preferred_domains:
            if domain in domain_scores:
                domain_scores[domain] += 2  # 给用户偏好领域加分

        if not any(domain_scores.values()):
            return "general"

        return max(domain_scores, key=domain_scores.get)  # type: ignore

    async def _basic_cognition(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        """基础认知处理(当超级推理未启用时)"""
        # 简化的处理逻辑
        return {
            "query": query,
            "analysis": {
                "intent": "provide_information",
                "key_points": ["基础分析"],
                "complexity": "medium",
            },
            "response": "我会尽力为您提供有用的信息和指导。",
            "confidence": 0.7,
        }

    async def _apply_xiaonuo_enhancements(
        self,
        reasoning_result: dict[str, Any],
        cognition_mode: XiaonuoCognitionMode,
        expertise_domain: str,
        user_profile: dict[str, Any],
        request_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """应用小诺特色增强"""
        enhanced = reasoning_result.copy()

        # 认知模式增强
        mode_enhancement = await self._apply_cognition_mode_enhancement(
            cognition_mode, reasoning_result, user_profile
        )
        enhanced["mode_enhancement"] = mode_enhancement

        # 专业领域增强
        if expertise_domain != "general":
            domain_enhancement = await self._apply_domain_expertise(
                expertise_domain, reasoning_result
            )
            enhanced["domain_expertise"] = domain_enhancement

        # 个性化增强
        personalization = await self._apply_personalization(
            user_profile, reasoning_result, request_analysis
        )
        enhanced["personalization"] = personalization

        # 实用性增强
        practicality = await self._apply_practicality_enhancement(
            reasoning_result, request_analysis
        )
        enhanced["practicality"] = practicality

        return enhanced

    async def _apply_cognition_mode_enhancement(
        self, mode: XiaonuoCognitionMode, result: dict[str, Any], user_profile: dict[str, Any]
    ) -> dict[str, Any]:
        """应用认知模式增强"""
        enhancements = {
            "mode": mode.value,
            "characteristics": [],
            "communication_style": "",
            "focus_areas": [],
        }

        if mode == XiaonuoCognitionMode.HELPER:
            enhancements.update(
                {
                    "characteristics": ["友好", "支持性", "耐心"],
                    "communication_style": "温和鼓励",
                    "focus_areas": ["step_by_step_guidance", "emotional_support", "simplification"],
                }
            )
        elif mode == XiaonuoCognitionMode.EXPERT:
            enhancements.update(
                {
                    "characteristics": ["专业", "深入", "权威"],
                    "communication_style": "专业自信",
                    "focus_areas": [
                        "deep_analysis",
                        "technical_accuracy",
                        "comprehensive_coverage",
                    ],
                }
            )
        elif mode == XiaonuoCognitionMode.INNOVATOR:
            enhancements.update(
                {
                    "characteristics": ["创新", "前瞻", "突破"],
                    "communication_style": "启发思考",
                    "focus_areas": [
                        "creative_solutions",
                        "new_perspectives",
                        "innovative_approaches",
                    ],
                }
            )
        elif mode == XiaonuoCognitionMode.COLLABORATOR:
            enhancements.update(
                {
                    "characteristics": ["协作", "包容", "互动"],
                    "communication_style": "合作商议",
                    "focus_areas": ["team_input", "shared_decision", "mutual_understanding"],
                }
            )

        return enhancements

    async def _apply_domain_expertise(self, domain: str, result: dict[str, Any]) -> dict[str, Any]:
        """应用领域专业知识"""
        if domain not in self.expertise_cache:
            return {"domain": domain, "status": "no_expertise_available"}

        expertise = self.expertise_cache[domain]

        return {
            "domain": domain,
            "expertise_level": "available",
            "key_concepts": expertise.get("concepts", []),
            "best_practices": expertise.get("best_practices", []),
            "common_pitfalls": expertise.get("common_problems", []),
            "recommended_approaches": expertise.get("solution_patterns", []),
        }

    async def _apply_personalization(
        self, user_profile: dict[str, Any], result: dict[str, Any], request_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """应用个性化增强"""
        preferences = user_profile.get("preferences", {})
        expertise_level = user_profile.get("expertise_level", "general")

        personalization = {
            "user_level_adaptation": expertise_level,
            "preference_matching": {},
            "historical_context": [],
        }

        # 基于偏好调整
        if preferences.get("detailed_explanations", True):
            personalization["preference_matching"]["detail_level"] = "high"  # type: ignore
        else:
            personalization["preference_matching"]["detail_level"] = "concise"  # type: ignore

        if preferences.get("practical_focus", True):
            personalization["preference_matching"]["focus"] = "practical_solutions"  # type: ignore
        else:
            personalization["preference_matching"]["focus"] = "comprehensive_analysis"  # type: ignore

        # 历史上下文
        interaction_history = user_profile.get("interaction_history", [])
        if interaction_history:
            recent_topics = [
                interaction.get("query_topic", "") for interaction in interaction_history[-5:]
            ]
            personalization["historical_context"] = recent_topics

        return personalization

    async def _apply_practicality_enhancement(
        self, result: dict[str, Any], request_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """应用实用性增强"""
        request_type = request_analysis.get("primary_type", "information")
        urgency = request_analysis.get("urgency", "normal")

        practicality = {
            "actionability": "high",
            "implementation_focus": "",
            "resource_requirements": [],
            "time_sensitivity": urgency,
        }

        # 基于请求类型调整
        if request_type == "guidance":
            practicality["implementation_focus"] = "step_by_step_instructions"
        elif request_type == "problem_solving":
            practicality["implementation_focus"] = "solution_roadmap"
        elif request_type == "analysis":
            practicality["implementation_focus"] = "actionable_insights"
        else:
            practicality["implementation_focus"] = "practical_information"

        return practicality

    async def _generate_user_friendly_output(
        self,
        enhanced_result: dict[str, Any],
        cognition_mode: XiaonuoCognitionMode,
        user_profile: dict[str, Any],
        expertise_domain: str,
    ) -> dict[str, Any]:
        """生成用户友好的输出"""
        # 基础输出结构
        output = {
            "greeting": await self._generate_mode_greeting(cognition_mode, user_profile),
            "main_response": "",
            "practical_guidance": [],
            "key_insights": [],
            "next_steps": [],
            "encouragement": "",
            "style_tone": cognition_mode.value,
        }

        # 从超级推理结果中提取内容
        if "xiaonuo_reasoning" in enhanced_result:
            reasoning_output = enhanced_result.get("xiaonuo_reasoning")
            output["main_response"] = reasoning_output.get("summary", "")  # type: ignore
            output["key_insights"] = reasoning_output.get("key_takeaways", [])  # type: ignore
            output["encouragement"] = reasoning_output.get("encouragement", "")  # type: ignore

            # 实用解决方案
            if "practical_solutions" in reasoning_output:
                solutions = reasoning_output["practical_solutions"]  # type: ignore
                if solutions:
                    recommended = solutions[0]  # 推荐的解决方案
                    output["practical_guidance"] = recommended.get("next_steps", [])

        # 补充专业领域建议
        if expertise_domain != "general" and "domain_expertise" in enhanced_result:
            domain_info = enhanced_result.get("domain_expertise")
            if "best_practices" in domain_info:
                output["domain_tips"] = domain_info.get("best_practices")[:3]  # type: ignore

        # 生成后续建议
        output["follow_up_suggestions"] = await self._generate_personalized_follow_up(
            enhanced_result, user_profile
        )

        return output

    async def _generate_mode_greeting(
        self, mode: XiaonuoCognitionMode, user_profile: dict[str, Any]
    ) -> str:
        """生成符合认知模式的问候"""
        greetings = {
            XiaonuoCognitionMode.HELPER: "我很高兴能帮助您!让我为您提供清晰的指导。",
            XiaonuoCognitionMode.EXPERT: "基于我的专业知识,我为您提供深入的分析和建议。",
            XiaonuoCognitionMode.INNOVATOR: "让我们一起探索创新的解决方案!",
            XiaonuoCognitionMode.COLLABORATOR: "很高兴与您合作,让我们共同找到最佳方案。",
        }

        base_greeting = greetings.get(mode, greetings[XiaonuoCognitionMode.HELPER])

        # 个性化调整
        if user_profile.get("interaction_history"):
            base_greeting += " 很高兴再次为您服务!"

        return base_greeting

    async def _generate_personalized_follow_up(
        self, enhanced_result: dict[str, Any], user_profile: dict[str, Any]
    ) -> list[str]:
        """生成个性化后续建议"""
        suggestions = [
            "如需更详细的指导,请告诉我",
            "在实施过程中遇到任何问题,随时联系我",
            "定期反馈进展,我可以帮您优化方案",
        ]

        # 基于用户历史调整
        interaction_count = len(user_profile.get("interaction_history", []))
        if interaction_count > 5:
            suggestions.insert(0, "作为我们的老朋友,您可以直接告诉我您的需求")
        elif interaction_count == 0:
            suggestions.insert(0, "作为首次使用,建议您告诉我更多背景信息")

        return suggestions

    async def _record_interaction(
        self, user_id: str, query: str, output: dict[str, Any], mode: XiaonuoCognitionMode
    ):
        """记录交互"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "query": query[:100],  # 限制长度
            "query_topic": await self._extract_topic(query),
            "cognition_mode": mode.value,
            "output_summary": output.get("main_response", "")[:100],
        }

        self.interaction_history.append(interaction)

        # 更新用户档案
        if user_id and user_id in self.user_profiles:
            self.user_profiles[user_id]["interaction_history"].append(interaction)
            # 限制历史记录数量
            if len(self.user_profiles[user_id]["interaction_history"]) > 100:
                self.user_profiles[user_id]["interaction_history"] = self.user_profiles[user_id][
                    "interaction_history"
                ][-100:]

    async def _extract_topic(self, query: str) -> str:
        """提取查询主题"""
        # 简单的主题提取
        if "专利" in query:
            return "patent_related"
        elif "技术" in query:
            return "technology_related"
        elif "商业" in query:
            return "business_related"
        elif "法律" in query:
            return "legal_related"
        else:
            return "general"

    async def _learn_from_interaction(
        self, query: str, output: dict[str, Any], user_profile: dict[str, Any]
    ):
        """从交互中学习"""
        # 更新用户偏好
        if len(query) > 50:
            # 用户可能偏好详细解释
            user_profile.setdefault("preferences", {})["detailed_explanations"] = True

        # 更新专业领域兴趣
        topic = await self._extract_topic(query)
        if topic != "general":
            preferred_domains = user_profile.setdefault("preferences", {}).get(
                "preferred_domains", []
            )
            domain_mapping = {
                "patent_related": "patent_law",
                "technology_related": "technology",
                "business_related": "business",
                "legal_related": "legal",
            }
            if topic in domain_mapping:
                domain = domain_mapping[topic]
                if domain not in preferred_domains:
                    preferred_domains.append(domain)

    async def _calculate_personalization_score(
        self, user_profile: dict[str, Any], output: dict[str, Any]
    ) -> float:
        """计算个性化评分"""
        base_score = 0.5

        # 新用户加分
        if not user_profile.get("interaction_history"):
            base_score += 0.1

        # 有历史记录加分
        if user_profile.get("interaction_history"):
            base_score += 0.2

        # 有偏好设置加分
        if user_profile.get("preferences"):
            base_score += 0.2

        # 个性化问候加分
        if "老朋友" in output.get("greeting", ""):
            base_score += 0.1

        return min(1.0, base_score)

    async def _generate_follow_up_suggestions(
        self, query: str, output: dict[str, Any]
    ) -> list[str]:
        """生成后续跟进建议"""
        suggestions = [
            "告诉我更多关于您的具体需求",
            "您希望我深入解释哪个方面?",
            "是否有特定的约束条件需要考虑?",
        ]

        # 基于查询内容调整
        if "如何" in query:
            suggestions.insert(0, "需要我提供更详细的步骤说明吗?")
        elif "分析" in query:
            suggestions.insert(0, "是否需要我分析相关的案例或示例?")

        return suggestions[:4]

    async def update_user_preferences(self, user_id: str, preferences: dict[str, Any]):
        """更新用户偏好"""
        if user_id in self.user_profiles:
            self.user_profiles[user_id]["preferences"].update(preferences)
            logger.info(f"✅ 用户{user_id}的偏好已更新")

    async def get_user_summary(self, user_id: str) -> dict[str, Any]:
        """获取用户总结"""
        if user_id not in self.user_profiles:
            return {"error": "用户不存在"}

        profile = self.user_profiles[user_id]
        interaction_count = len(profile.get("interaction_history", []))

        return {
            "user_id": user_id,
            "interaction_count": interaction_count,
            "expertise_level": profile.get("expertise_level", "general"),
            "preferred_domains": profile.get("preferences", {}).get("preferred_domains", []),
            "member_since": profile.get("created_at"),
            "last_interaction": (
                profile.get("interaction_history", [-1])[-1].get("timestamp")
                if interaction_count > 0
                else None
            ),
        }

    async def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        total_interactions = len(self.interaction_history)
        active_users = len(self.user_profiles)

        return {
            "performance_metrics": self.performance_metrics,
            "interaction_summary": {
                "total_interactions": total_interactions,
                "active_users": active_users,
                "average_interactions_per_user": total_interactions / max(1, active_users),
            },
            "user_satisfaction": self.performance_metrics.get("user_satisfaction_score", 0.0),
            "recommendations": self._generate_performance_recommendations(),
        }

    def _generate_performance_recommendations(self) -> list[str]:
        """生成性能优化建议"""
        recommendations = []

        if self.performance_metrics["user_satisfaction_score"] < 0.8:
            recommendations.append("建议增强用户同理心和理解能力")

        if self.performance_metrics["solution_effectiveness"] < 0.7:
            recommendations.append("建议优化解决方案的实用性")

        if len(self.user_profiles) < 10:
            recommendations.append("建议加强用户个性化和关系建立")

        return recommendations

    async def shutdown(self):
        """关闭小诺认知系统"""
        logger.info("🛑 关闭Xiaonuo增强认知系统...")

        if self.super_reasoning_engine:
            await self.super_reasoning_engine.shutdown()

        logger.info("✅ Xiaonuo增强认知系统已关闭")
