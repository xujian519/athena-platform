#!/usr/bin/env python3
from __future__ import annotations
"""
专业法律写作能力 - 增强版
Professional Legal Writing Capability - Enhanced

集成LLM客户端和RAG检索,实现真正的智能法律文档生成。
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 导入写作素材管理器(增强版,支持缓存)
from core.llm.writing_materials_manager_v3 import get_materials_manager_enhanced


class LegalWritingCapabilityEnhanced:
    """
    专业法律写作能力 - 增强版

    新增功能:
    - 集成GLM-4.7和DeepSeek双LLM引擎
    - 集成RAG检索相关案例和法条
    - 智能内容扩充和优化
    - 用户反馈收集机制
    """

    # 写作角色定义
    ROLES = {
        "patent_attorney": {
            "name": "专利代理师",
            "tone": "技术精准、逻辑严密",
            "focus": ["技术特征分析", "权利要求解释", "审查指南适用"],
            "keywords": ["权利要求", "技术特征", "实施例", "创造性", "新颖性"],
            "model_preference": "glm-4-plus",  # 偏好GLM-4用于技术性写作
        },
        "lawyer": {
            "name": "律师",
            "tone": "论证有力、说服力强",
            "focus": ["法律适用", "争议焦点", "利益保护"],
            "keywords": ["侵权", "权利义务", "法律责任", "法律适用", "证据"],
            "model_preference": "deepseek-chat",  # 偏好DeepSeek用于论证
        },
        "judge": {
            "name": "法官",
            "tone": "客观公正、释法说理",
            "focus": ["事实认定", "法律适用", "裁判要旨"],
            "keywords": ["认定", "判决", "裁判", "释法说理", "定分止争"],
            "model_preference": "glm-4-plus",
        },
        "scholar": {
            "name": "学者",
            "tone": "批判创新、理论建构",
            "focus": ["问题意识", "理论分析", "制度完善"],
            "keywords": ["理论", "制度", "问题", "建议", "完善"],
            "model_preference": "deepseek-chat",  # 偏好DeepSeek用于深度分析
        },
    }

    # 文档类型定义
    DOCUMENT_TYPES = {
        "research_report": {
            "name": "法律研究报告",
            "default_structure": [
                "摘要",
                "一、原则法理",
                "二、法律依据",
                "三、案例演进",
                "四、争议分析",
                "五、比较法视角",
                "六、完善建议",
                "结论",
            ],
            "word_per_section": 800,
        },
        "legal_brief": {
            "name": "代理词/答辩状",
            "default_structure": ["基本情况", "案件事实", "法律依据", "代理意见/答辩意见", "结论"],
            "word_per_section": 600,
        },
        "opinion_letter": {
            "name": "法律意见书",
            "default_structure": ["背景说明", "事实梳理", "法律分析", "风险评估", "专业建议"],
            "word_per_section": 500,
        },
        "oa_response": {
            "name": "审查意见答复",
            "default_structure": [
                "总体意见",
                "关于新颖性的答复",
                "关于创造性的答复",
                "修改说明",
                "结语",
            ],
            "word_per_section": 800,
        },
        "judgment": {
            "name": "裁判文书",
            "default_structure": [
                "当事人信息",
                "案件由来",
                "事实认定",
                "法律适用",
                "裁判结果",
                "裁判理由",
            ],
            "word_per_section": 700,
        },
    }

    def __init__(self, llm_client=None, rag_manager=None, materials_path=None):
        """
        初始化增强版写作能力

        Args:
            llm_client: LLM客户端(GLM或DeepSeek)
            rag_manager: RAG管理器(也用于素材检索)
            materials_path: 写作素材路径(默认为/Users/xujian/语料)
        """
        self.llm_client = llm_client
        self.rag_manager = rag_manager

        # 初始化写作素材管理器(增强版,支持缓存)
        self.materials_manager = get_materials_manager_enhanced(
            rag_manager=rag_manager,
            materials_path=materials_path,
            cache_size=100,  # 缓存100个文档
            cache_ttl_hours=24,  # 缓存24小时
        )

        # 加载写作风格模板
        self.style_template_path = (
            Path(__file__).parent.parent.parent / "config/prompts/legal_writing_style_prompt.md"
        )
        self.style_template = self._load_style_template()

        # 用户反馈存储路径
        self.feedback_storage_path = (
            Path(__file__).parent.parent.parent / "data/legal_writing_feedback.json"
        )
        self._ensure_feedback_storage()

        logger.info("✅ LegalWritingCapabilityEnhanced 初始化完成")
        logger.info(f"   LLM客户端: {'已配置' if llm_client else '未配置'}")
        logger.info(f"   RAG管理器: {'已配置' if rag_manager else '未配置'}")
        logger.info(
            f"   写作素材库: {'已配置(增强版+缓存)' if self.materials_manager else '未配置'}"
        )

    def _load_style_template(self) -> str:
        """加载写作风格模板"""
        try:
            if self.style_template_path.exists():
                with open(self.style_template_path, encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"⚠️ 加载写作风格模板失败: {e}")

        return self._get_default_style_template()

    def _get_default_style_template(self) -> str:
        """获取默认写作风格模板"""
        return """
## 法律专业文书写作要求

### 语言规范
- 使用法言法语,避免口语化表达
- 逻辑严密,前后一致
- 概念清晰,定义统一

### 结构要求
- 标题层次清晰
- 段落长度适中
- 重点内容突出

### 引用规范
- 法条引用:先法律名称,再条款号,最后内容
- 案例引用:案号、法院、裁判日期、核心要旨
"""

    def _ensure_feedback_storage(self):
        """确保反馈存储文件存在"""
        self.feedback_storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.feedback_storage_path.exists():
            with open(self.feedback_storage_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    async def generate(
        self,
        topic: str,
        task_type: str = "research_report",
        role: str = "scholar",
        word_count: int = 5000,
        structure: list[str] | None = None,
        context: dict[str, Any] | None = None,
        enable_rag: bool = True,
        enable_iteration: bool = True,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        生成法律文档(增强版)

        Args:
            topic: 文档主题
            task_type: 任务类型
            role: 写作角色
            word_count: 目标字数
            structure: 自定义结构
            context: 额外上下文
            enable_rag: 是否启用RAG检索
            enable_iteration: 是否启用迭代优化
            model: 指定使用的模型(可选)

        Returns:
            生成结果
        """
        start_time = datetime.now()

        logger.info("📝 开始生成法律文档(增强版)")
        logger.info(f"   主题: {topic}")
        logger.info(f"   类型: {task_type}")
        logger.info(f"   角色: {role}")
        logger.info(f"   字数: {word_count}")
        logger.info(f"   RAG: {enable_rag}")
        logger.info(f"   模型: {model or '自动选择'}")

        try:
            # 1. 验证参数
            self._validate_parameters(task_type, role)

            # 2. 获取文档结构
            document_structure = self._get_document_structure(task_type, structure)

            # 3. 选择模型
            selected_model = model or self._select_model(role, task_type)
            logger.info(f"   选择模型: {selected_model}")

            # 4. 生成写作风格提示词
            style_prompt = self._generate_style_prompt(role, task_type)

            # 5. 检索相关资料
            materials = {}
            if enable_rag and self.rag_manager:
                materials = await self._retrieve_materials(topic, task_type)
                logger.info(f"   检索到 {len(materials.get('rag_results', []))} 条相关资料")

            # 6. 分章节生成内容
            content_sections = {}
            context_accumulator = {
                "previous_sections": [],
                "materials": materials,
                "user_context": context or {},
                "style_prompt": style_prompt,
            }

            for i, section in enumerate(document_structure):
                logger.info(f"   生成章节 {i+1}/{len(document_structure)}: {section}")

                section_content = await self._generate_section(
                    section=section,
                    topic=topic,
                    task_type=task_type,
                    role=role,
                    context=context_accumulator,
                    target_words=word_count // len(document_structure),
                    model=selected_model,
                )

                content_sections[section] = section_content
                context_accumulator["previous_sections"].append(
                    {"section": section, "content": section_content}
                )

            # 7. 组装完整文档
            full_document = self._assemble_document(
                content_sections, document_structure, topic, task_type
            )

            # 8. 质量评估
            quality_report = self._assess_quality(
                full_document, task_type, role, document_structure
            )

            # 9. 迭代优化(可选)
            if enable_iteration and quality_report["overall_score"] < 0.85:
                logger.info(f"   质量评分 {quality_report['overall_score']:.2f},启动迭代优化")
                full_document, quality_report = await self._iterative_optimize(
                    full_document,
                    quality_report,
                    topic,
                    task_type,
                    role,
                    context_accumulator,
                    selected_model,
                )

            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info("✅ 文档生成完成")
            logger.info(f"   字符数: {len(full_document)}")
            logger.info(f"   耗时: {processing_time:.2f}秒")
            logger.info(f"   质量评分: {quality_report['overall_score']:.2f}")

            return {
                "success": True,
                "document": full_document,
                "metadata": {
                    "topic": topic,
                    "task_type": task_type,
                    "role": role,
                    "model_used": selected_model,
                    "word_count": len(full_document),
                    "structure": document_structure,
                    "processing_time": processing_time,
                    "rag_enabled": enable_rag,
                    "materials_count": len(materials.get("rag_results", [])),
                    "timestamp": datetime.now().isoformat(),
                },
                "materials_used": materials,
                "quality_report": quality_report,
            }

        except Exception as e:
            logger.error(f"❌ 文档生成失败: {e}")
            import traceback

            traceback.print_exc()

            return {"success": False, "error": str(e), "document": None, "metadata": {}}

    def _validate_parameters(self, task_type: str, role: str):
        """验证参数"""
        if task_type not in self.DOCUMENT_TYPES:
            raise ValueError(
                f"不支持的文档类型: {task_type}," f"支持的类型: {list(self.DOCUMENT_TYPES.keys())}"
            )

        if role not in self.ROLES:
            raise ValueError(f"不支持的角色: {role}," f"支持的角色: {list(self.ROLES.keys())}")

    def _get_document_structure(
        self, task_type: str, custom_structure: list[str] | None = None
    ) -> list[str]:
        """获取文档结构"""
        if custom_structure:
            return custom_structure

        return self.DOCUMENT_TYPES[task_type]["default_structure"]

    def _select_model(self, role: str, task_type: str) -> str:
        """
        选择合适的模型

        Args:
            role: 写作角色
            task_type: 任务类型

        Returns:
            模型名称
        """
        # 优先使用角色偏好模型
        role_preference = self.ROLES[role].get("model_preference")
        if role_preference:
            return role_preference

        # 根据任务类型选择
        if task_type in ["oa_response", "legal_brief"]:
            return "glm-4-plus"  # 技术性写作用GLM
        elif task_type in ["research_report", "opinion_letter"]:
            return "deepseek-chat"  # 深度分析用DeepSeek
        else:
            return "glm-4-plus"  # 默认用GLM

    def _generate_style_prompt(self, role: str, task_type: str) -> str:
        """生成写作风格提示词"""
        role_info = self.ROLES[role]

        # 基础风格模板
        base_style = self.style_template

        # 角色特定要求
        role_specific = f"""
## {role_info['name']}写作风格

### 角色定位
你是一位{role_info['name']},具有丰富的专业经验。

### 写作特点
- 语气风格:{role_info['tone']}
- 关注重点:{', '.join(role_info['focus'])}
- 常用术语:{', '.join(role_info['keywords'])}

### 写作要求
根据{role_info['name']}的视角,重点关注{', '.join(role_info['focus'][:-1])}等核心问题。
"""

        return base_style + role_specific

    async def _retrieve_materials(self, topic: str, task_type: str) -> dict[str, Any]:
        """检索相关资料"""
        materials = {"cases": [], "laws": [], "academic_papers": [], "rag_results": []}

        if not self.rag_manager:
            logger.warning("RAG管理器未配置,跳过资料检索")
            return materials

        try:
            # 使用RAG检索
            rag_context = await self.rag_manager.retrieve(query=topic, task_type=task_type)
            materials["rag_results"] = rag_context.retrieval_results

            logger.info(f"   RAG检索成功: {len(materials['rag_results'])} 条结果")

        except Exception as e:
            logger.warning(f"⚠️ RAG检索失败: {e}")

        return materials

    async def _generate_section(
        self,
        section: str,
        topic: str,
        task_type: str,
        role: str,
        context: dict[str, Any],        target_words: int,
        model: str,
    ) -> str:
        """
        生成单个章节内容(集成LLM)

        Args:
            section: 章节名称
            topic: 主题
            task_type: 任务类型
            role: 角色
            context: 上下文
            target_words: 目标字数
            model: 使用的模型

        Returns:
            章节内容
        """
        if not self.llm_client:
            # LLM客户端未配置,返回占位符
            return f"## {section}\n\n(LLM客户端未配置,无法生成真实内容。目标字数:{target_words}字)\n\n"

        # 生成章节提示词
        previous_summary = ""
        if context["previous_sections"]:
            recent = context["previous_sections"][-2:]
            previous_summary = "\n".join([f"- {s['section']}: 已完成" for s in recent])

        # 格式化检索到的资料(RetrievalResult是数据类,不是字典)
        materials_hint = ""
        if context["materials"].get("rag_results"):
            top_results = context["materials"]["rag_results"][:5]
            materials_list = []
            for r in top_results:
                # RetrievalResult是数据类,直接访问属性
                materials_list.append(f"- [{r.source}]: {r.content[:150]}...")
            materials_hint = "\n### 参考资料\n" + "\n".join(materials_list)

        # 获取写作素材库中的相关示例(使用RAG检索)
        examples_hint = ""
        if self.materials_manager and self.rag_manager:
            try:
                # 直接使用await获取相关示例(在async上下文中)
                examples = await self.materials_manager.search_relevant_examples(
                    topic=topic, section=section, role=role, top_k=2
                )

                if examples:
                    examples_hint = "\n### 参考示例\n\n"
                    examples_hint += (
                        "以下是从平台真实法律文档中提取的相关示例,供您参考写作风格和结构:\n\n"
                    )
                    for i, example in enumerate(examples, 1):
                        examples_hint += f"#### 示例 {i}: {example['title']}\n\n"
                        examples_hint += f"**来源**: {example['source']}\n\n"
                        examples_hint += f"```\n{example['content']}\n```\n\n"
                    logger.info(f"      已添加 {len(examples)} 个素材示例")
            except Exception as e:
                logger.debug(f"      写作素材库检索失败: {e}")

        # 构建完整的提示词
        base_style_prompt = context.get("style_prompt", "")
        user_context = context.get("user_context", {})

        section_prompt = f"""{base_style_prompt}

## 写作任务

请为"{topic}"撰写"{section}"章节。

### 上下文信息
{previous_summary}

{materials_hint}
{examples_hint}

### 用户提供的额外信息
{json.dumps(user_context, ensure_ascii=False, indent=2) if user_context else "无"}

### 写作要求
1. 字数:约{target_words}字(可根据内容重要性适当调整)
2. 使用专业的法言法语
3. 逻辑严密,论证充分
4. 如有引用,请标注来源
5. 内容要有深度,避免泛泛而谈
6. 保持客观中立的立场
7. 参考上述示例的写作风格和结构,但不要抄袭具体内容

### 输出格式
请直接输出{section}章节的完整内容,使用markdown格式:
## {section}

[章节内容]
"""

        try:
            # 调用LLM生成内容
            if hasattr(self.llm_client, "_call_llm"):
                # GLM客户端
                messages = [
                    {
                        "role": "system",
                        "content": "你是一位资深的法律学者,擅长撰写专业的法律文档。",
                    },
                    {"role": "user", "content": section_prompt},
                ]

                content = await self.llm_client._call_llm(
                    messages=messages, temperature=0.7, max_tokens=min(target_words * 2, 4000)
                )

            elif hasattr(self.llm_client, "client") and hasattr(self.llm_client.client, "chat"):
                # DeepSeek客户端(使用AsyncOpenAI)
                messages = [
                    {
                        "role": "system",
                        "content": "你是一位资深的法律学者,擅长撰写专业的法律文档。",
                    },
                    {"role": "user", "content": section_prompt},
                ]

                response = await self.llm_client.client.chat.completions.create(
                    model=self.llm_client.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=min(target_words * 2, 4000),
                )
                content = response.choices[0].message.content

            elif hasattr(self.llm_client, "chat"):
                # 其他OpenAI兼容客户端
                response = await self.llm_client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一位资深的法律学者,擅长撰写专业的法律文档。",
                        },
                        {"role": "user", "content": section_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=min(target_words * 2, 4000),
                )
                content = response.choices[0].message.content
            else:
                raise ValueError(f"不支持的LLM客户端类型: {type(self.llm_client)}")

            # 清理输出
            content = content.strip()

            # 确保以章节标题开头
            if not content.startswith(f"## {section}"):
                content = f"## {section}\n\n{content}"

            logger.info(f"      生成成功: {len(content)} 字符")
            return content

        except Exception as e:
            logger.error(f"      生成失败: {e}")
            # 降级到占位符
            return f"## {section}\n\n(生成失败: {e!s}。目标字数:{target_words}字)\n\n"

    def _assemble_document(
        self, content_sections: dict[str, str], structure: list[str], topic: str, task_type: str
    ) -> str:
        """组装完整文档"""
        document_parts = []

        # 添加标题
        doc_type_name = self.DOCUMENT_TYPES[task_type]["name"]
        document_parts.append(f"# {topic}\n")
        document_parts.append(f"**文档类型**: {doc_type_name}\n")
        document_parts.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        document_parts.append("**生成方式**: AI辅助生成,仅供参考\n")

        # 添加摘要(如果是研究报告)
        if task_type == "research_report" and "摘要" in structure:
            # 摘要会在content_sections中,不需要额外添加
            pass

        # 添加各章节
        for section in structure:
            if section in content_sections:
                document_parts.append(content_sections[section])

        return "\n".join(document_parts)

    def _assess_quality(
        self, document: str, task_type: str, role: str, structure: list[str]
    ) -> dict[str, Any]:
        """评估文档质量"""
        quality_report = {
            "structure_completeness": 0.0,
            "citation_accuracy": 0.0,
            "logical_consistency": 0.0,
            "language_standard": 0.0,
            "critical_thinking": 0.0,
            "overall_score": 0.0,
            "suggestions": [],
            "details": {},
        }

        # 1. 检查结构完整性
        missing_sections = []
        for section in structure:
            if section not in document:
                missing_sections.append(section)

        quality_report["structure_completeness"] = max(
            0.0, 1.0 - len(missing_sections) / len(structure)
        )
        quality_report["details"]["missing_sections"] = missing_sections

        # 2. 检查引用格式
        citation_indicators = ["《", "》", "第", "条", "法释", "民申", "民再"]
        citation_score = sum(1 for indicator in citation_indicators if indicator in document)
        quality_report["citation_accuracy"] = min(citation_score / 4, 1.0)

        # 3. 检查法言法语
        role_info = self.ROLES.get(role, {})
        legal_terms = role_info.get("keywords", [])
        term_count = sum(1 for term in legal_terms if term in document)
        quality_report["language_standard"] = min(term_count / max(len(legal_terms), 1), 1.0)

        # 4. 检查逻辑一致性(简化版)
        logic_indicators = ["因此", "所以", "基于", "根据", "综上", "首先", "其次", "最后"]
        logic_count = sum(1 for indicator in logic_indicators if indicator in document)
        quality_report["logical_consistency"] = min(logic_count / 4, 1.0)

        # 5. 检查批判性思维(简化版)
        critical_indicators = ["问题", "争议", "不足", "建议", "完善", "挑战", "困境"]
        critical_count = sum(1 for indicator in critical_indicators if indicator in document)
        quality_report["critical_thinking"] = min(critical_count / 3, 1.0)

        # 6. 计算总分
        quality_report["overall_score"] = (
            quality_report["structure_completeness"] * 0.25
            + quality_report["citation_accuracy"] * 0.15
            + quality_report["logical_consistency"] * 0.20
            + quality_report["language_standard"] * 0.20
            + quality_report["critical_thinking"] * 0.20
        )

        # 7. 生成改进建议
        self._generate_suggestions(quality_report)

        return quality_report

    def _generate_suggestions(self, quality_report: dict[str, Any]):
        """生成改进建议"""
        suggestions = []

        if quality_report["structure_completeness"] < 0.9:
            missing = quality_report["details"].get("missing_sections", [])
            if missing:
                suggestions.append(f"建议补充缺失的章节: {', '.join(missing)}")

        if quality_report["citation_accuracy"] < 0.7:
            suggestions.append("建议增加更多法条和案例引用,使用规范的引用格式")

        if quality_report["language_standard"] < 0.7:
            suggestions.append("建议使用更规范的法律术语和法言法语")

        if quality_report["critical_thinking"] < 0.7:
            suggestions.append("建议加强问题意识和批判性分析,提出真问题和创新观点")

        if quality_report["overall_score"] < 0.8:
            suggestions.append("建议进行迭代优化以提高整体质量")

        quality_report["suggestions"] = suggestions

    async def _iterative_optimize(
        self,
        document: str,
        quality_report: dict[str, Any],        topic: str,
        task_type: str,
        role: str,
        context: dict[str, Any],        model: str,
        max_iterations: int = 2,
    ) -> tuple:
        """迭代优化文档"""
        logger.info(f"   🔄 开始迭代优化(最多{max_iterations}轮)")

        for iteration in range(max_iterations):
            logger.info(f"   第{iteration + 1}轮优化...")

            # 根据质量报告生成改进建议
            if quality_report["suggestions"]:
                logger.info(f"   改进建议: {quality_report['suggestions']}")

            # 使用LLM进行优化
            if self.llm_client:
                optimized_document = await self._optimize_with_llm(
                    document, quality_report, topic, task_type, role, model
                )
            else:
                optimized_document = document

            # 重新评估
            new_quality_report = self._assess_quality(
                optimized_document, task_type, role, self._get_document_structure(task_type)
            )

            # 检查是否有改进
            if new_quality_report["overall_score"] > quality_report["overall_score"]:
                document = optimized_document
                quality_report = new_quality_report
                logger.info(f"   ✅ 质量提升: {quality_report['overall_score']:.2f}")
            else:
                logger.info("   ⏹️ 质量未提升,停止优化")
                break

        return document, quality_report

    async def _optimize_with_llm(
        self,
        document: str,
        quality_report: dict[str, Any],        topic: str,
        task_type: str,
        role: str,
        model: str,
    ) -> str:
        """使用LLM优化文档"""
        suggestions = quality_report.get("suggestions", [])

        optimization_prompt = f"""
请优化以下法律文档,使其更加专业和完善。

## 改进建议
{chr(10).join([f"{i+1}. {s}" for i, s in enumerate(suggestions)])}

## 原文档
{document[:3000]}...

[注:只显示了文档前3000字,请根据改进建议优化整个文档]

## 优化要求
1. 保持原有的结构和核心内容
2. 根据改进建议进行针对性优化
3. 增强论证的深度和严密性
4. 完善引用和格式
5. 输出完整的优化后文档
"""

        try:
            if hasattr(self.llm_client, "_call_llm"):
                messages = [
                    {
                        "role": "system",
                        "content": "你是一位资深的法律学者,擅长优化和改进法律文档。",
                    },
                    {"role": "user", "content": optimization_prompt},
                ]

                content = await self.llm_client._call_llm(
                    messages=messages, temperature=0.6, max_tokens=6000
                )
                return content

            elif hasattr(self.llm_client, "client") and hasattr(self.llm_client.client, "chat"):
                # DeepSeek客户端(使用AsyncOpenAI)
                messages = [
                    {
                        "role": "system",
                        "content": "你是一位资深的法律学者,擅长优化和改进法律文档。",
                    },
                    {"role": "user", "content": optimization_prompt},
                ]

                response = await self.llm_client.client.chat.completions.create(
                    model=self.llm_client.model, messages=messages, temperature=0.6, max_tokens=6000
                )
                return response.choices[0].message.content

            elif hasattr(self.llm_client, "chat"):
                response = await self.llm_client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一位资深的法律学者,擅长优化和改进法律文档。",
                        },
                        {"role": "user", "content": optimization_prompt},
                    ],
                    temperature=0.6,
                    max_tokens=6000,
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.warning(f"LLM优化失败: {e}")
            return document

    # ========== 用户反馈机制 ==========

    async def collect_feedback(
        self,
        document_id: str,
        rating: int,
        feedback_text: str = "",
        improvement_suggestions: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        收集用户反馈

        Args:
            document_id: 文档ID
            rating: 评分(1-5)
            feedback_text: 反馈文本
            improvement_suggestions: 改进建议列表

        Returns:
            反馈记录
        """
        feedback_record = {
            "document_id": document_id,
            "rating": rating,
            "feedback_text": feedback_text,
            "improvement_suggestions": improvement_suggestions or [],
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # 读取现有反馈
            with open(self.feedback_storage_path, encoding="utf-8") as f:
                all_feedback = json.load(f)
        except Exception:
            all_feedback = {}

        # 添加新反馈
        all_feedback[document_id] = feedback_record

        # 保存反馈
        with open(self.feedback_storage_path, "w", encoding="utf-8") as f:
            json.dump(all_feedback, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 用户反馈已保存: {document_id}, 评分: {rating}")

        return {"success": True, "feedback": feedback_record}

    async def get_feedback_statistics(self) -> dict[str, Any]:
        """
        获取反馈统计信息

        Returns:
            统计信息
        """
        try:
            with open(self.feedback_storage_path, encoding="utf-8") as f:
                all_feedback = json.load(f)
        except Exception:
            return {"total_feedbacks": 0, "average_rating": 0, "rating_distribution": {}}

        if not all_feedback:
            return {"total_feedbacks": 0, "average_rating": 0, "rating_distribution": {}}

        # 计算统计
        ratings = [f["rating"] for f in all_feedback.values()]
        average_rating = sum(ratings) / len(ratings) if ratings else 0

        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[str(i)] = sum(1 for r in ratings if r == i)

        # 提取常见改进建议
        all_suggestions = []
        for f in all_feedback.values():
            all_suggestions.extend(f.get("improvement_suggestions", []))

        from collections import Counter

        suggestion_counts = Counter(all_suggestions)
        top_suggestions = suggestion_counts.most_common(5)

        return {
            "total_feedbacks": len(all_feedback),
            "average_rating": round(average_rating, 2),
            "rating_distribution": rating_distribution,
            "top_improvement_suggestions": [
                {"suggestion": s, "count": c} for s, c in top_suggestions
            ],
        }


# 便捷函数
async def generate_legal_report_enhanced(
    topic: str,
    role: str = "scholar",
    word_count: int = 6000,
    llm_client=None,
    rag_manager=None,
    enable_rag: bool = True,
) -> str:
    """
    生成法律研究报告的便捷函数(增强版)

    Args:
        topic: 研究主题
        role: 写作角色
        word_count: 目标字数
        llm_client: LLM客户端
        rag_manager: RAG管理器
        enable_rag: 是否启用RAG

    Returns:
        生成的报告内容
    """
    capability = LegalWritingCapabilityEnhanced(llm_client=llm_client, rag_manager=rag_manager)

    result = await capability.generate(
        topic=topic,
        task_type="research_report",
        role=role,
        word_count=word_count,
        enable_rag=enable_rag,
    )

    if result["success"]:
        return result["document"]
    else:
        raise Exception(f"生成失败: {result.get('error')}")


if __name__ == "__main__":
    # 测试代码
    async def test():
        print("专业法律写作能力 - 增强版测试")
        print("=" * 70)

        # 不配置LLM和RAG,测试基础功能
        capability = LegalWritingCapabilityEnhanced()

        result = await capability.generate(
            topic="专利全面覆盖原则深度研究",
            task_type="research_report",
            role="scholar",
            word_count=6000,
            enable_rag=False,
        )

        if result["success"]:
            print("\n✅ 生成成功!")
            print(f"字数: {result['metadata']['word_count']}")
            print(f"质量: {result['quality_report']['overall_score']:.2f}")

            # 测试用户反馈收集
            print("\n📝 测试用户反馈收集...")
            feedback_result = await capability.collect_feedback(
                document_id="test_001",
                rating=4,
                feedback_text="整体质量不错,但案例分析可以更深入",
                improvement_suggestions=["增加更多真实案例", "加强比较法视角"],
            )
            print(f"反馈保存: {feedback_result['success']}")

            # 测试反馈统计
            print("\n📊 反馈统计:")
            stats = await capability.get_feedback_statistics()
            print(f"总反馈数: {stats['total_feedbacks']}")
            print(f"平均评分: {stats['average_rating']}")
        else:
            print(f"\n❌ 生成失败: {result.get('error')}")

    asyncio.run(test())
