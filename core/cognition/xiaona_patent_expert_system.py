
# pyright: ignore
# !/usr/bin/env python3
"""
小娜专利专家系统 - Lyra增强版
Xiaona Patent Expert System - Lyra Enhanced Version

基于Lyra提示词构建的专利专家系统,支持动态提示词生成和知识库集成

作者: 小娜·天秤女神
创建时间: 2025-12-16
版本: v1.0 Patent Expert System
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# 导入现有的Lyra系统
from memory.lyra_prompt_memory import get_lyra_memory

# 导入顶级专家系统
from top_patent_expert_system import ExpertTeamAnalysis, TopPatentExpertSystem

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class PatentContext:
    """专利上下文信息"""

    technology_field: str
    patent_type: str  # 发明专利、实用新型、外观设计
    analysis_stage: str  # 申请、检索、审查、维权
    user_intent: str
    technical_complexity: str  # 高、中、低
    deadline_requirement: str = "无特殊要求"
    target_jurisdiction: str = "中国"


@dataclass
class ExpertPrompt:
    """专家提示词"""

    prompt_id: str
    context_type: str
    dynamic_prompt: str
    base_template: str
    knowledge_sources: list[str]
    confidence_score: float
    generation_time: datetime
    optimization_applied: bool
    expert_team_analysis: ExpertTeamAnalysis | None = None


class PatentExpertSystem:
    """专利专家系统"""

    def __init__(self):
        self.name = "小娜专利专家系统"
        self.version = "v1.0 Patent Expert System"

        # 初始化Lyra记忆系统
        self.lyra_memory = get_lyra_memory()

        # 专利知识库路径
        self.knowledge_bases = {
            "patent_guidelines": "/Users/xujian/Athena工作平台/knowledge/patent_guidelines.json",  # TODO: 确保除数不为零
            "patent_rules": "/Users/xujian/Athena工作平台/knowledge/patent_rules.json",  # TODO: 确保除数不为零
            "patent_vector_db": "qdrant://patent_vectors",
            "knowledge_graph": "neo4j://patent_kg",
        }

        # 专家系统知识
        self.expert_knowledge = {}
        self.prompt_templates = {}
        self.case_database = {}

        # 缓存系统
        self.prompt_cache = {}
        self.knowledge_cache = {}

        # 顶级专家系统
        self.top_expert_system = TopPatentExpertSystem()

        self.is_initialized = False

    async def initialize(self):
        """初始化专利专家系统"""
        logger.info("🧠 初始化小娜专利专家系统...")

        try:
            # 1. 加载专利专业知识
            await self._load_patent_expertise()

            # 2. 初始化动态提示词生成器
            await self._initialize_prompt_generator()

            # 3. 连接知识库
            await self._connect_knowledge_bases()

            # 4. 构建专家规则库
            await self._build_expert_rules()

            # 5. 集成Lyra优化方法
            await self._integrate_lyra_optimization()

            # 6. 初始化顶级专家系统
            await self.top_expert_system.initialize()

            self.is_initialized = True
            logger.info("✅ 小娜专利专家系统初始化完成")

        except Exception as e:
            logger.error(f"❌ 专家系统初始化失败: {e!s}")
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def generate_expert_prompt(self, context: PatentContext, user_input: str) -> ExpertPrompt:
        """生成专家级专利分析提示词"""
        if not self.is_initialized:
            raise RuntimeError("专家系统未初始化")

        logger.info(f"🎯 生成专家提示词: {context.technology_field} - {context.analysis_stage}")

        # 1. 分析上下文和意图
        context_analysis = await self._analyze_context(context, user_input)

        # 2. 检索相关专业知识
        relevant_knowledge = await self._retrieve_relevant_knowledge(context)

        # 3. 调用顶级专家团队分析
        expert_team_analysis = await self._consult_top_expert_team(context, user_input)

        # 4. 选择基础模板
        base_template = await self._select_base_template(context)

        # 5. 应用Lyra优化
        lyra_optimized = await self._apply_lyra_optimization(user_input, context)

        # 6. 动态生成提示词
        dynamic_prompt = await self._generate_dynamic_prompt(
            base_template,
            context_analysis,
            relevant_knowledge,
            lyra_optimized,
            expert_team_analysis,
        )

        # 7. 应用专家规则
        expert_enhanced_prompt = await self._apply_expert_rules(dynamic_prompt, context)

        # 8. 质量评估
        confidence_score = await self._evaluate_prompt_quality(expert_enhanced_prompt, context)

        # 9. 创建提示词对象
        expert_prompt = ExpertPrompt(
            prompt_id=f"patent_expert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            context_type=f"{context.technology_field}_{context.analysis_stage}",
            dynamic_prompt=expert_enhanced_prompt,
            base_template=base_template,
            knowledge_sources=list(relevant_knowledge.keys()),
            confidence_score=confidence_score,
            generation_time=datetime.now(),
            optimization_applied=True,
            expert_team_analysis=expert_team_analysis,
        )

        # 10. 缓存提示词
        await self._cache_prompt(context, expert_prompt)

        logger.info(f"✅ 专家提示词生成完成,置信度: {confidence_score:.2f}")
        return expert_prompt

    async def _analyze_context(self, context: PatentContext, user_input: str) -> dict[str, Any]:
        """分析上下文"""
        analysis = {
            "domain_complexity": self._assess_domain_complexity(context.technology_field),
            "task_complexity": self._assess_task_complexity(context.analysis_stage),
            "user_expertise_level": self._infer_user_expertise(user_input),
            "required_depth": self._determine_required_depth(context),
            "key_concepts": await self._extract_key_concepts(user_input, context.technology_field),
            "potential_risks": await self._identify_potential_risks(context),
            "success_factors": await self._identify_success_factors(context),
        }

        return analysis

    async def _retrieve_relevant_knowledge(self, context: PatentContext) -> dict[str, Any]:
        """检索相关知识"""
        knowledge = {}

        # 1. 从专利审查指南检索
        guidelines_knowledge = await self._search_guidelines(context)
        if guidelines_knowledge:
            knowledge["guidelines"] = guidelines_knowledge

        # 2. 从专利规则检索
        rules_knowledge = await self._search_patent_rules(context)
        if rules_knowledge:
            knowledge["rules"] = rules_knowledge

        # 3. 从向量数据库检索相似案例
        vector_knowledge = await self._search_vector_database(context)
        if vector_knowledge:
            knowledge["vectors"] = vector_knowledge

        # 4. 从知识图谱检索关系网络
        graph_knowledge = await self._search_knowledge_graph(context)
        if graph_knowledge:
            knowledge["graph"] = graph_knowledge

        return knowledge

    async def _select_base_template(self, context: PatentContext) -> str:
        """选择基础模板"""
        template_key = f"{context.patent_type}_{context.analysis_stage}"

        # 基础模板库
        templates = {
            "发明_申请": """
作为资深专利代理人和技术专家,请基于中国专利法和审查指南的要求,对以下技术方案进行全面分析:

**技术领域**: {technology_field}
**技术复杂度**: {complexity}
**分析目标**: {goal}

请按照以下结构进行专业分析:
1. 技术方案理解与特征提取
2. 新颖性检索与分析
3. 创造性评估(三步法)
4. 实用性判断
5. 申请策略建议
6. 权利要求撰写建议

要求:
- 严格遵循《专利审查指南》相关规定
- 引用相关法律条文和审查标准
- 提供具体可操作的建议
- 识别潜在风险和规避策略
            """,
            "发明_检索": """
作为专利信息检索专家,请对以下技术方案进行专业的现有技术检索:

**检索目标**: {technology_field} 相关技术
**检索策略**: 精准检索 + 扩展检索
**检索范围**: 中国专利库 + 国际专利库

请执行:
1. 关键词提取与扩展
2. IPC分类号确定
3. 检索式构建
4. 结果筛选与去重
5. 相关性分析
6. 自由实施风险分析

输出格式:
- 检索策略说明
- 相关专利清单
- 对比分析报告
- 新颖性初步判断
            """,
            "发明_审查": """
作为专利审查专家,请基于审查员视角对以下专利申请进行专业分析:

**申请类型**: 发明专利
**技术领域**: {technology_field}
**审查重点**: {focus_points}

审查要点:
1. 权利要求书合法性审查
2. 说明书支持性分析
3. 新颖性、创造性、实用性审查
4. 修改超范围判断
5. 单一性原则检查
6. 形式要求合规性

请提供:
- 可能的审查意见
- 驳回风险分析
- 答复策略建议
- 修改建议方案
            """,
        }

        return templates.get(template_key, templates.get("发明_申请", ""))

    async def _apply_lyra_optimization(self, user_input: str, context: PatentContext) -> str:
        """应用Lyra优化方法"""
        # 构建专利特定的Lyra优化提示
        lyra_prompt = f"""
使用Lyra的4-D方法论,优化以下专利分析请求:

目标AI: Claude (高级推理)
优化模式: DETAIL (专业级)

1. DECONSTRUCT(解构):
- 用户核心意图:{user_input}
- 专利类型:{context.patent_type}
- 技术领域:{context.technology_field}
- 分析阶段:{context.analysis_stage}

2. DIAGNOSE(诊断):
- 识别技术描述中的模糊点
- 检查专业术语的准确性
- 评估技术特征的完整性

3. DEVELOP(开发):
- 应用专利专家角色(15年经验)
- 集成专利法律知识体系
- 增强技术理解的深度
- 添加审查标准参考

4. DELIVER(交付):
- 生成精准的专业提示词
- 确保符合专利分析标准
- 提供结构化的分析框架

原始请求: "{user_input}"

请生成优化后的专利分析提示词:
        """

        return lyra_prompt

    async def _consult_top_expert_team(
        self, context: PatentContext, user_input: str
    ) -> ExpertTeamAnalysis:
        """咨询顶级专家团队"""
        logger.info("👥 咨询顶级专家团队...")

        # 确定IPC分类
        ipc_section = self._determine_ipc_section(context.technology_field)

        # 调用顶级专家系统
        expert_team_analysis = await self.top_expert_system.analyze_with_expert_team(
            technology_field=context.technology_field,
            ipc_section=ipc_section,
            patent_type=context.patent_type,
            analysis_type=context.analysis_stage,
            technical_description=user_input,
            user_requirements=[f"技术复杂度: {context.technical_complexity}"],
        )

        return expert_team_analysis

    def _determine_ipc_section(self, technology_field: str) -> str:
        """根据技术领域确定IPC分类"""
        ipc_mapping = {
            "农业": "A",
            "食品": "A",
            "个人或家庭用品": "A",
            "健康": "A",
            "娱乐": "A",
            "运输": "B",
            "建筑": "E",
            "采矿": "E",
            "机械工程": "F",
            "照明": "F",
            "加热": "F",
            "武器": "F",
            "物理": "G",
            "仪表": "G",
            "核子学": "G",
            "化学": "C",
            "冶金": "C",
            "纺织": "D",
            "造纸": "D",
            "电学": "H",
        }

        for field, ipc in ipc_mapping.items():
            if field in technology_field:
                return ipc

        # 默认返回电学分类
        return "H"

    async def _generate_dynamic_prompt(
        self,
        base_template: str,
        context_analysis: dict,  # type: ignore
        knowledge: dict,  # type: ignore
        lyra_optimized: str,
        expert_team_analysis: ExpertTeamAnalysis = None,
    ) -> str:
        """动态生成提示词"""
        # 获取最相关的知识片段
        key_insights = await self._extract_key_insights(knowledge)

        # 获取最相关的知识片段
        key_insights = await self._extract_key_insights(knowledge)

        # 构建上下文信息
        context_info = {
            "domain_insights": key_insights.get("domain", []),
            "legal_rules": key_insights.get("rules", []),
            "similar_cases": key_insights.get("cases", []),
            "risk_factors": key_insights.get("risks", []),
            "success_patterns": key_insights.get("patterns", []),
        }

        # 动态组装提示词
        dynamic_prompt = f"""
{base_template}

**顶级专家团队分析**:
🌟 专家团队共识:
{expert_team_analysis.consensus_opinion if expert_team_analysis else "暂无专家团队分析"}

👥 专家团队构成:
{self._format_expert_team(expert_team_analysis.team_composition) if expert_team_analysis else "暂无专家团队"}

📊 专家团队风险评估:
{self._format_risk_assessment(expert_team_analysis.risk_assessment) if expert_team_analysis else "暂无风险评估"}

💡 专家团队建议:
{self._format_recommendations(expert_team_analysis.recommendations) if expert_team_analysis else "暂无具体建议"}

🎯 专家团队行动计划:
{self._format_next_steps(expert_team_analysis.next_steps) if expert_team_analysis else "暂无行动计划"}

**专家知识增强**:
📋 领域专家见解:
{self._format_insights(context_info.get("domain_insights"))}

⚖️ 相关法律规则:
{self._format_rules(context_info.get("legal_rules"))}

🔍 相似案例参考:
{self._format_cases(context_info.get("similar_cases"))}

⚠️ 风险提示:
{self._format_risks(context_info.get("risk_factors"))}

✅ 成功要素:
{self._format_patterns(context_info.get("success_patterns"))}

**Lyra优化增强**:
{lyra_optimized}

**分析要求**:
- 综合运用上述专业知识和规则
- 基于案例经验进行判断
- 关注风险点和成功要素
- 提供实用性和可操作的建议
- 输出专业、准确、全面的分析结果

**输出格式**:
使用结构化格式,包含明确的章节标题、逻辑清晰的论述、具体的数据支撑和可执行的建议。
        """

        return dynamic_prompt

    async def _apply_expert_rules(self, prompt: str, context: PatentContext) -> str:
        """应用专家规则"""
        # 定义专家规则
        expert_rules = {
            "novelty_emphasis": "强调新颖性判断标准",
            "inventive_step_focus": "突出创造性分析要点",
            "legal_compliance": "确保法律条款准确性",
            "technical_depth": "保证技术理解深度",
            "practical_guidance": "提供实用指导建议",
        }

        # 根据上下文应用相应规则
        if context.analysis_stage == "申请":
            prompt = self._apply_application_rules(prompt, expert_rules)
        elif context.analysis_stage == "检索":
            prompt = self._apply_search_rules(prompt, expert_rules)
        elif context.analysis_stage == "审查":
            prompt = self._apply_examination_rules(prompt, expert_rules)

        return prompt

    async def _evaluate_prompt_quality(self, prompt: str, context: PatentContext) -> float:
        """评估提示词质量"""
        score = 0.0
        max_score = 100.0

        # 1. 完整性评估 (20分)
        completeness_indicators = ["技术方案", "新颖性", "创造性", "实用性", "权利要求", "法律依据"]
        completeness_score = (
            sum(1 for indicator in completeness_indicators if indicator in prompt)
            / len(completeness_indicators)
            * 20
        )
        score += completeness_score

        # 2. 专业性评估 (25分)
        professional_terms = [
            "专利法",
            "审查指南",
            "权利要求书",
            "说明书",
            "IPC分类",
            "现有技术",
            "技术特征",
        ]
        professional_score = min(prompt.count(term) for term in professional_terms) * 5  # 最高25分
        score += professional_score

        # 3. 结构化评估 (20分)
        structure_indicators = ["1.", "2.", "###", "**", "- "]
        structure_score = min(
            sum(prompt.count(indicator) for indicator in structure_indicators), 20
        )
        score += structure_score

        # 4. 上下文适配性评估 (20分)
        context_adaptation = sum(
            1
            for term in [context.technology_field, context.patent_type, context.analysis_stage]
            if term in prompt
        )
        adaptation_score = (context_adaptation / 3) * 20
        score += adaptation_score

        # 5. 可操作性评估 (15分)
        actionable_indicators = ["建议", "策略", "步骤", "方法", "措施"]
        actionable_score = min(
            sum(prompt.count(indicator) for indicator in actionable_indicators), 15
        )
        score += actionable_score

        return min(max_score, score)

    async def _cache_prompt(self, context: PatentContext, prompt: ExpertPrompt):
        """缓存提示词"""
        cache_key = f"{context.technology_field}_{context.analysis_stage}_{context.patent_type}"
        self.prompt_cache[cache_key] = {
            "prompt": prompt,
            "cached_at": datetime.now(),
            "context": context,
        }

    # 辅助方法
    def _assess_domain_complexity(self, technology_field: str) -> str:
        """评估领域复杂度"""
        complex_fields = ["人工智能", "机器学习", "生物技术", "新材料", "量子计算", "基因工程"]
        return "高" if any(field in technology_field for field in complex_fields) else "中"

    def _assess_task_complexity(self, analysis_stage: str) -> str:
        """评估任务复杂度"""
        complexity_map = {"申请": "中", "检索": "高", "审查": "高", "维权": "高", "布局": "中"}
        return complexity_map.get(analysis_stage, "中")

    def _infer_user_expertise(self, user_input: str) -> str:
        """推断用户专业水平"""
        professional_terms = ["权利要求", "现有技术", "新颖性", "创造性", "IPC", "CPC"]
        term_count = sum(1 for term in professional_terms if term in user_input)

        if term_count >= 3:
            return "专业"
        elif term_count >= 1:
            return "中级"
        else:
            return "初级"

    def _determine_required_depth(self, context: PatentContext) -> str:
        """确定分析深度"""
        if context.technical_complexity == "高" and context.analysis_stage in ["检索", "审查"]:
            return "深度"
        elif context.technical_complexity == "中":
            return "中等"
        else:
            return "基础"

    async def _extract_key_concepts(self, user_input: str, technology_field: str) -> list[str]:
        """提取关键概念"""
        # 简化实现
        concepts = []
        words = user_input.split()
        for word in words:
            if len(word) > 3 and word not in concepts:
                concepts.append(word)
        return concepts[:10]

    async def _identify_potential_risks(self, context: PatentContext) -> list[str]:
        """识别潜在风险"""
        risk_map = {
            "申请": ["新颖性不足", "创造性缺陷", "公开不充分"],
            "检索": ["检索不全面", "关键词不准确", "遗漏重要对比文件"],
            "审查": ["审查意见答复不当", "修改超范围", "权利要求不支持"],
        }
        return risk_map.get(context.analysis_stage, ["一般风险"])

    async def _identify_success_factors(self, context: PatentContext) -> list[str]:
        """识别成功要素"""
        factor_map = {
            "申请": ["技术方案完整", "权利要求层次清晰", "说明书充分公开"],
            "检索": ["关键词精准", "检索式合理", "分析全面"],
            "审查": ["答复策略得当", "修改合法合规", "论证充分"],
        }
        return factor_map.get(context.analysis_stage, ["专业分析"])

    async def _format_insights(self, insights: list[str]) -> str:
        """格式化见解"""
        return "\n".join(f"• {insight}" for insight in insights) if insights else "暂无特定见解"

    async def _format_rules(self, rules: list[str]) -> str:
        """格式化规则"""
        return "\n".join(f"• {rule}" for rule in rules) if rules else "暂无相关规则"

    async def _format_cases(self, cases: list[str]) -> str:
        """格式化案例"""
        return "\n".join(f"• {case}" for case in cases) if cases else "暂无参考案例"

    async def _format_risks(self, risks: list[str]) -> str:
        """格式化风险"""
        return "\n".join(f"⚠️ {risk}" for risk in risks) if risks else "暂无特殊风险"

    async def _format_patterns(self, patterns: list[str]) -> str:
        """格式化模式"""
        return "\n".join(f"✅ {pattern}" for pattern in patterns) if patterns else "暂无特定模式"

    async def _format_expert_team(self, team_composition: list[dict]) -> str:  # type: ignore
        """格式化专家团队"""
        if not team_composition:
            return "暂无专家团队"

        formatted = []
        for expert in team_composition:
            formatted.append(f"• {expert['name']} ({expert['title']}) - {expert['type']}专家")

        return "\n".join(formatted)

    async def _format_risk_assessment(self, risk_assessment: dict) -> str:  # type: ignore
        """格式化风险评估"""
        if not risk_assessment:
            return "暂无风险评估"

        formatted = []
        risk_level = risk_assessment.get("overall_risk_level", "unknown")
        formatted.append(f"整体风险等级: {risk_level}")

        for risk_type, risks in risk_assessment.items():
            if risk_type != "overall_risk_level" and risks:
                formatted.append(f"{risk_type}: {', '.join(risks)}")

        return "\n".join(formatted)

    async def _format_recommendations(self, recommendations: list[str]) -> str:
        """格式化建议"""
        if not recommendations:
            return "暂无具体建议"

        return "\n".join(f"• {rec}" for rec in recommendations[:5])  # 只显示前5个

    async def _format_next_steps(self, next_steps: list[str]) -> str:
        """格式化下一步行动"""
        if not next_steps:
            return "暂无行动计划"

        return "\n".join(f"• {step}" for step in next_steps[:5])  # 只显示前5个

    # 占位符方法(将在后续实现)
    async def _load_patent_expertise(self):
        """加载专利专业知识"""
        pass

    async def _initialize_prompt_generator(self):
        """初始化提示词生成器"""
        pass

    async def _connect_knowledge_bases(self):
        """连接知识库"""
        pass

    async def _build_expert_rules(self):
        """构建专家规则库"""
        pass

    async def _integrate_lyra_optimization(self):
        """集成Lyra优化方法"""
        pass

    async def _search_guidelines(self, context: PatentContext) -> dict[str, Any]:
        """搜索审查指南"""
        return {}

    async def _search_patent_rules(self, context: PatentContext) -> dict[str, Any]:
        """搜索专利规则"""
        return {}

    async def _search_vector_database(self, context: PatentContext) -> dict[str, Any]:
        """搜索向量数据库"""
        return {}

    async def _search_knowledge_graph(self, context: PatentContext) -> dict[str, Any]:
        """搜索知识图谱"""
        return {}

    async def _extract_key_insights(self, knowledge: dict[str, Any]) -> dict[str, Any]:
        """提取关键见解"""
        return knowledge

    def _apply_application_rules(self, prompt: str, rules: dict) -> str:  # type: ignore
        """应用申请规则"""
        return prompt

    def _apply_search_rules(self, prompt: str, rules: dict) -> str:  # type: ignore
        """应用检索规则"""
        return prompt

    def _apply_examination_rules(self, prompt: str, rules: dict) -> str:  # type: ignore
        """应用审查规则"""
        return prompt


# 导出主类
__all__ = ["ExpertPrompt", "PatentContext", "PatentExpertSystem"]
