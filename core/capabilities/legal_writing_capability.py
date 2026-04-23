#!/usr/bin/env python3
from __future__ import annotations
"""
专业法律写作能力
Professional Legal Writing Capability

提供高质量的法律文档生成服务,支持研究报告、法律文书、意见书等多种类型。
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LegalWritingCapability:
    """
    专业法律写作能力

    支持多种写作场景:
    - 法律研究报告(research_report)
    - 代理词/答辩状(legal_brief)
    - 法律意见书(opinion_letter)
    - OA答复(oa_response)
    - 裁判文书(judgment)
    """

    # 写作角色定义
    ROLES = {
        "patent_attorney": {
            "name": "专利代理师",
            "tone": "技术精准、逻辑严密",
            "focus": ["技术特征分析", "权利要求解释", "审查指南适用"],
            "keywords": ["权利要求", "技术特征", "实施例", "创造性", "新颖性"],
        },
        "lawyer": {
            "name": "律师",
            "tone": "论证有力、说服力强",
            "focus": ["法律适用", "争议焦点", "利益保护"],
            "keywords": ["侵权", "权利义务", "法律责任", "法律适用", "证据"],
        },
        "judge": {
            "name": "法官",
            "tone": "客观公正、释法说理",
            "focus": ["事实认定", "法律适用", "裁判要旨"],
            "keywords": ["认定", "判决", "裁判", "释法说理", "定分止争"],
        },
        "scholar": {
            "name": "学者",
            "tone": "批判创新、理论建构",
            "focus": ["问题意识", "理论分析", "制度完善"],
            "keywords": ["理论", "制度", "问题", "建议", "完善"],
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

    def __init__(self, llm_manager=None, rag_manager=None):
        """
        初始化写作能力

        Args:
            llm_manager: LLM管理器
            rag_manager: RAG管理器(用于检索相关案例和法条)
        """
        self.llm_manager = llm_manager
        self.rag_manager = rag_manager

        # 加载写作风格模板
        self.style_template_path = (
            Path(__file__).parent.parent.parent / "config/prompts/legal_writing_style_prompt.md"
        )
        self.style_template = self._load_style_template()

        logger.info("✅ LegalWritingCapability 初始化完成")

    def _load_style_template(self) -> str:
        """加载写作风格模板"""
        try:
            if self.style_template_path.exists():
                with open(self.style_template_path, encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"⚠️ 加载写作风格模板失败: {e}")

        # 返回默认模板
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

    async def generate(
        self,
        topic: str,
        task_type: str = "research_report",
        role: str = "scholar",
        word_count: int = 5000,
        structure: Optional[list[str]] = None,
        context: Optional[dict[str, Any]] = None,
        enable_rag: bool = True,
        enable_iteration: bool = True,
    ) -> dict[str, Any]:
        """
        生成法律文档

        Args:
            topic: 文档主题
            task_type: 任务类型(research_report, legal_brief等)
            role: 写作角色(patent_attorney, lawyer, judge, scholar)
            word_count: 目标字数
            structure: 自定义结构(可选)
            context: 额外上下文信息
            enable_rag: 是否启用RAG检索
            enable_iteration: 是否启用迭代优化

        Returns:
            生成结果,包含文档内容和质量报告
        """
        start_time = datetime.now()

        logger.info("📝 开始生成法律文档")
        logger.info(f"   主题: {topic}")
        logger.info(f"   类型: {task_type}")
        logger.info(f"   角色: {role}")
        logger.info(f"   字数: {word_count}")

        try:
            # 1. 验证参数
            self._validate_parameters(task_type, role)

            # 2. 获取文档结构
            document_structure = self._get_document_structure(task_type, structure)

            # 3. 生成写作风格提示词
            style_prompt = self._generate_style_prompt(role, task_type)

            # 4. 检索相关资料
            materials = {}
            if enable_rag and self.rag_manager:
                materials = await self._retrieve_materials(topic, task_type)

            # 5. 分章节生成内容
            content_sections = {}
            context_accumulator = {
                "previous_sections": [],
                "materials": materials,
                "user_context": context or {},
            }

            for i, section in enumerate(document_structure):
                logger.info(f"   生成章节 {i+1}/{len(document_structure)}: {section}")

                section_content = await self._generate_section(
                    section=section,
                    topic=topic,
                    task_type=task_type,
                    role=role,
                    style_prompt=style_prompt,
                    context=context_accumulator,
                    target_words=word_count // len(document_structure),
                )

                content_sections[section] = section_content
                context_accumulator["previous_sections"].append(
                    {"section": section, "content": section_content}
                )

            # 6. 组装完整文档
            full_document = self._assemble_document(
                content_sections, document_structure, topic, task_type
            )

            # 7. 质量评估
            quality_report = self._assess_quality(
                full_document, task_type, role, document_structure
            )

            # 8. 迭代优化(可选)
            if enable_iteration and quality_report["overall_score"] < 0.85:
                logger.info(f"   质量评分 {quality_report['overall_score']:.2f},启动迭代优化")
                full_document, quality_report = await self._iterative_optimize(
                    full_document, quality_report, topic, task_type, role
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
                    "word_count": len(full_document),
                    "structure": document_structure,
                    "processing_time": processing_time,
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
        self, task_type: str, custom_structure: Optional[list[str]] = None
    ) -> list[str]:
        """获取文档结构"""
        if custom_structure:
            return custom_structure

        return self.DOCUMENT_TYPES[task_type]["default_structure"]

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
            return materials

        try:
            # 使用RAG检索
            from core.llm.rag_manager import RAGQuery

            query = RAGQuery(text=topic, task_type=task_type, top_k=10)

            rag_context = await self.rag_manager.retrieve(query)
            materials["rag_results"] = rag_context.retrieval_results

            logger.info(f"   RAG检索到 {len(materials['rag_results'])} 条相关资料")

        except Exception as e:
            logger.warning(f"⚠️ RAG检索失败: {e}")

        return materials

    async def _generate_section(
        self,
        section: str,
        topic: str,
        task_type: str,
        role: str,
        style_prompt: str,
        context: dict[str, Any],        target_words: int,
    ) -> str:
        """
        生成单个章节内容

        注意:这里需要集成实际的LLM调用
        当前返回占位符内容
        """
        # 生成章节提示词
        if context["previous_sections"]:
            "\n".join(
                [f"- {s['section']}: 已完成" for s in context["previous_sections"][-3:]]
            )

        if context["materials"].get("rag_results"):
            f"""
参考资料:
{chr(10).join([f"- {r.source}: {r.content[:100]}..."
               for r in context["materials"]["rag_results"][:5]])}
"""


        # TODO: 这里需要调用实际的LLM
        # 当前返回占位符
        return f"## {section}\n\n(本章节内容待生成,目标字数:{target_words}字)\n\n"

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

        # 添加摘要(如果是研究报告)
        if task_type == "research_report":
            document_parts.append("## 摘要\n")
            document_parts.append("\n(摘要内容待补充)\n\n")

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
        citation_indicators = ["《", "》", "第", "条", "法释"]
        citation_score = sum(1 for indicator in citation_indicators if indicator in document)
        quality_report["citation_accuracy"] = min(citation_score / 3, 1.0)

        # 3. 检查法言法语
        role_info = self.ROLES.get(role, {})
        legal_terms = role_info.get("keywords", [])
        term_count = sum(1 for term in legal_terms if term in document)
        quality_report["language_standard"] = min(term_count / max(len(legal_terms), 1), 1.0)

        # 4. 检查逻辑一致性(简化版)
        logic_indicators = ["因此", "所以", "基于", "根据", "综上"]
        logic_count = sum(1 for indicator in logic_indicators if indicator in document)
        quality_report["logical_consistency"] = min(logic_count / 3, 1.0)

        # 5. 检查批判性思维(简化版)
        critical_indicators = ["问题", "争议", "不足", "建议", "完善"]
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
            suggestions.append("建议补充缺失的章节")

        if quality_report["citation_accuracy"] < 0.7:
            suggestions.append("建议增加更多法条和案例引用")

        if quality_report["language_standard"] < 0.7:
            suggestions.append("建议使用更规范的法律术语")

        if quality_report["critical_thinking"] < 0.7:
            suggestions.append("建议加强问题意识和批判性分析")

        if quality_report["overall_score"] < 0.8:
            suggestions.append("建议进行迭代优化以提高整体质量")

        quality_report["suggestions"] = suggestions

    async def _iterative_optimize(
        self,
        document: str,
        quality_report: dict[str, Any],        topic: str,
        task_type: str,
        role: str,
        max_iterations: int = 2,
    ) -> tuple:
        """迭代优化文档"""
        logger.info(f"   🔄 开始迭代优化(最多{max_iterations}轮)")

        for iteration in range(max_iterations):
            logger.info(f"   第{iteration + 1}轮优化...")

            # 根据质量报告生成改进建议
            if quality_report["suggestions"]:
                logger.info(f"   改进建议: {quality_report['suggestions']}")

            # TODO: 实际调用LLM进行优化
            # optimized_document = await self._optimize_with_llm(...)
            optimized_document = document  # 占位符

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


# 便捷函数
async def generate_legal_report(topic: str, role: str = "scholar", word_count: int = 6000) -> str:
    """
    生成法律研究报告的便捷函数

    Args:
        topic: 研究主题
        role: 写作角色(默认为学者)
        word_count: 目标字数(默认6000字)

    Returns:
        生成的报告内容
    """
    capability = LegalWritingCapability()

    result = await capability.generate(
        topic=topic, task_type="research_report", role=role, word_count=word_count
    )

    if result["success"]:
        return result["document"]
    else:
        raise Exception(f"生成失败: {result.get('error')}")


if __name__ == "__main__":
    # 测试代码
    async def test():
        capability = LegalWritingCapability()

        result = await capability.generate(
            topic="专利全面覆盖原则深度研究",
            task_type="research_report",
            role="scholar",
            word_count=6000,
        )

        if result["success"]:
            print("✅ 生成成功!")
            print(f"字数: {result['metadata']['word_count']}")
            print(f"质量: {result['quality_report']['overall_score']:.2f}")

            # 保存文档
            output_path = "/tmp/legal_writing_test.md"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result["document"])
            print(f"已保存到: {output_path}")
        else:
            print(f"❌ 生成失败: {result.get('error')}")

    asyncio.run(test())
