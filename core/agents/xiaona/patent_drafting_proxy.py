"""
专利撰写智能体

专注于专利申请文件的撰写，确保申请文件符合规范要求并提供充分保护。
"""

import json
import logging
from typing import Any, Optional

from core.agents.xiaona.base_component import BaseXiaonaComponent
from core.agents.xiaona.patent_drafting_prompts import PatentDraftingPrompts

logger = logging.getLogger(__name__)


class PatentDraftingProxy(BaseXiaonaComponent):
    """
    专利撰写智能体

    核心能力：
    - 分析技术交底书
    - 评估可专利性
    - 撰写说明书
    - 撰写权利要求书
    - 优化保护范围
    - 审查充分公开
    - 检测常见错误
    """

    def __init__(
        self, agent_id: str = "patent_drafting_proxy", config: Optional[dict[str, Any]] = None
    ):
        """
        初始化专利撰写智能体

        Args:
            agent_id: 智能体唯一标识
            config: 配置参数
        """
        super().__init__(agent_id, config)

    def _initialize(self) -> None:
        """初始化专利撰写智能体"""
        self._register_capabilities(
            [
                {
                    "name": "analyze_disclosure",
                    "description": "分析技术交底书",
                    "input_types": ["技术交底书"],
                    "output_types": ["交底书分析报告"],
                    "estimated_time": 15.0,
                },
                {
                    "name": "assess_patentability",
                    "description": "评估可专利性",
                    "input_types": ["技术交底书", "现有技术"],
                    "output_types": ["可专利性评估报告"],
                    "estimated_time": 20.0,
                },
                {
                    "name": "draft_specification",
                    "description": "撰写说明书",
                    "input_types": ["技术交底书", "可专利性评估"],
                    "output_types": ["说明书草稿"],
                    "estimated_time": 30.0,
                },
                {
                    "name": "draft_claims",
                    "description": "撰写权利要求书",
                    "input_types": ["技术交底书", "说明书"],
                    "output_types": ["权利要求书草稿"],
                    "estimated_time": 25.0,
                },
                {
                    "name": "optimize_protection_scope",
                    "description": "优化保护范围",
                    "input_types": ["权利要求书", "现有技术"],
                    "output_types": ["优化建议"],
                    "estimated_time": 20.0,
                },
                {
                    "name": "review_adequacy",
                    "description": "审查充分公开",
                    "input_types": ["说明书", "权利要求书"],
                    "output_types": ["充分公开审查报告"],
                    "estimated_time": 15.0,
                },
                {
                    "name": "detect_common_errors",
                    "description": "检测常见错误",
                    "input_types": ["说明书", "权利要求书"],
                    "output_types": ["错误检测报告"],
                    "estimated_time": 10.0,
                },
            ]
        )

    def get_system_prompt(self, task_type: str = "comprehensive") -> str:
        """
        获取系统提示词

        Args:
            task_type: 任务类型

        Returns:
            系统提示词
        """
        # 使用新的优化提示词系统
        prompt_config = PatentDraftingPrompts.get_prompt(task_type)
        return prompt_config.get(
            "system_prompt",
            """
你是一位专业的专利撰写专家，具备深厚的专利法知识和丰富的撰写经验。

请以专业、严谨的态度进行工作，并提供明确的建议。
输出必须是严格的JSON格式，不要添加任何额外的文字说明。
""",
        )

    async def execute(self, context) -> Any:
        """
        执行智能体任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        # 验证输入
        if not self.validate_input(context):
            from core.agents.xiaona.base_component import AgentExecutionResult, AgentStatus

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message="输入验证失败",
            )

        # 根据任务类型执行相应的任务
        task_type = context.config.get("task_type", "comprehensive")

        try:
            from core.agents.xiaona.base_component import AgentStatus

            output_data = None
            if task_type == "analyze_disclosure":
                output_data = await self.analyze_disclosure(context.input_data)
            elif task_type == "assess_patentability":
                output_data = await self.assess_patentability(context.input_data)
            elif task_type == "draft_specification":
                output_data = await self.draft_specification(context.input_data)
            elif task_type == "draft_claims":
                output_data = await self.draft_claims(context.input_data)
            elif task_type == "optimize_protection_scope":
                output_data = await self.optimize_protection_scope(context.input_data)
            elif task_type == "review_adequacy":
                output_data = await self.review_adequacy(context.input_data)
            elif task_type == "detect_common_errors":
                output_data = await self.detect_common_errors(context.input_data)
            else:
                # 完整撰写流程
                output_data = await self.draft_patent_application(context.input_data)

            # 返回统一格式的结果
            from core.agents.xiaona.base_component import AgentExecutionResult

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=output_data,
                error_message=None,
            )
        except Exception as e:
            self.logger.error(f"执行任务失败: {e}")
            from core.agents.xiaona.base_component import AgentExecutionResult, AgentStatus

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
            )

    async def analyze_disclosure(self, disclosure_data: dict[str, Any]) -> dict[str, Any]:
        """
        分析技术交底书

        Args:
            disclosure_data: 技术交底书数据

        Returns:
            交底书分析报告
        """
        try:
            prompt = self._build_disclosure_analysis_prompt(disclosure_data)
            response = await self._call_llm_with_fallback(
                prompt=prompt, task_type="analyze_disclosure"
            )

            # 解析LLM响应
            result = self._parse_analysis_response(response)

            # 如果解析失败，降级到规则分析
            if "error" in result:
                self.logger.warning("LLM响应解析失败，降级到规则-based分析")
                return self._analyze_disclosure_by_rules(disclosure_data)

            return result

        except Exception as e:
            self.logger.warning(f"LLM交底书分析失败: {e}，使用规则-based分析")
            return self._analyze_disclosure_by_rules(disclosure_data)

    def _analyze_disclosure_by_rules(self, disclosure_data: dict[str, Any]) -> dict[str, Any]:
        """
        基于规则的交底书分析（降级方案）

        Args:
            disclosure_data: 技术交底书数据

        Returns:
            交底书分析报告
        """
        # 第1步：解析文档内容（支持多种格式）
        content = self._extract_document_content(disclosure_data)

        # 第2步：提取关键信息
        extracted_info = self._extract_key_information(content, disclosure_data)

        # 第3步：完整性检查
        completeness = self._check_completeness(extracted_info)

        # 第4步：质量评估
        quality_assessment = self._assess_quality(extracted_info, completeness)

        # 第5步：生成建议
        recommendations = self._generate_disclosure_recommendations_detailed(
            extracted_info, completeness, quality_assessment
        )

        return {
            "disclosure_id": disclosure_data.get("disclosure_id", "未知"),
            "extracted_information": extracted_info,
            "completeness": completeness,
            "quality_assessment": quality_assessment,
            "recommendations": recommendations,
            "analyzed_at": self._get_timestamp(),
        }

    def _extract_document_content(self, disclosure_data: dict[str, Any]) -> str:
        """
        提取文档内容（支持多种格式）

        Args:
            disclosure_data: 交底书数据

        Returns:
            提取的文本内容
        """
        # 情况1：直接提供文本内容
        if "content" in disclosure_data:
            return disclosure_data["content"]

        # 情况2：提供文件路径
        if "file_path" in disclosure_data:
            return self._read_text_file(disclosure_data["file_path"])

        # 情况3：从各字段拼接
        fields = [
            "title",
            "technical_field",
            "background_art",
            "invention_summary",
            "technical_problem",
            "technical_solution",
            "beneficial_effects",
        ]
        content_parts = []
        for field in fields:
            value = disclosure_data.get(field, "")
            if value:
                content_parts.append(f"{field}: {value}")

        return "\n\n".join(content_parts) if content_parts else ""

    def _read_text_file(self, file_path: str) -> str:
        """
        读取文本文件

        Args:
            file_path: 文件路径

        Returns:
            文件内容
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"读取文件失败 {file_path}: {e}")
            return ""

    def _extract_key_information(
        self, content: str, disclosure_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        提取关键信息（规则引擎）

        Args:
            content: 文档内容
            disclosure_data: 原始数据

        Returns:
            提取的关键信息
        """
        # 优先使用显式提供的字段
        extracted = {
            "发明名称": self._extract_invention_name(content, disclosure_data),
            "技术领域": self._identify_technical_field(content, disclosure_data),
            "背景技术": self._extract_background_art(content, disclosure_data),
            "技术问题": self._extract_technical_problem(content, disclosure_data),
            "技术方案": self._extract_technical_solution(content, disclosure_data),
            "有益效果": self._extract_beneficial_effects(content, disclosure_data),
            "实施例": self._extract_examples(content, disclosure_data),
        }

        return extracted

    def _extract_invention_name(self, content: str, disclosure_data: dict[str, Any]) -> str:
        """
        提取发明名称

        Args:
            content: 文档内容
            disclosure_data: 原始数据

        Returns:
            发明名称
        """
        # 优先级1：直接提供
        if "title" in disclosure_data and disclosure_data["title"]:
            return disclosure_data["title"]

        # 优先级2：从content中提取（使用规则）
        import re

        # 规则1：匹配"发明名称"、"名称"等关键词
        patterns = [
            r"发明名称[：:]\s*([^\n]+)",
            r"名称[：:]\s*([^\n]+)",
            r"标题[：:]\s*([^\n]+)",
            r"专利名称[：:]\s*([^\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                title = match.group(1).strip()
                # 过滤掉过短的标题
                if len(title) >= 5:
                    return title

        # 优先级3：使用第一段非空文本
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) >= 5 and len(line) <= 50:
                return line

        return ""

    def _identify_technical_field(
        self, content: str, disclosure_data: dict[str, Any]
    ) -> dict[str, str]:
        """
        识别技术领域和IPC分类

        Args:
            content: 文档内容
            disclosure_data: 原始数据

        Returns:
            技术领域信息（包含领域描述和IPC分类）
        """
        result = {
            "技术领域": "",
            "IPC分类": [],
            "关键词": [],
        }

        # 优先使用直接提供的信息
        if "technical_field" in disclosure_data and disclosure_data["technical_field"]:
            result["技术领域"] = disclosure_data["technical_field"]
        else:
            # 从content中提取
            import re

            match = re.search(r"技术领域[：:]\s*([^\n]+)", content)
            if match:
                result["技术领域"] = match.group(1).strip()

        # IPC分类推断（基于关键词）
        ipc_keywords = self._get_ipc_classification_keywords()
        # 确保技术领域是字符串类型
        technical_field = result.get("技术领域", "")
        if not isinstance(technical_field, str):
            technical_field = str(technical_field)
        text = technical_field + " " + content[:500]

        matched_ipc = []
        for ipc_section, keywords in ipc_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    matched_ipc.append(f"{ipc_section}: {keyword}")
                    break

        result["IPC分类"] = matched_ipc[:3]  # 限制前3个

        return result

    def _get_ipc_classification_keywords(self) -> dict[str, list[str]]:
        """
        获取IPC分类关键词映射

        Returns:
            IPC分类关键词字典
        """
        return {
            "A部（人类生活需要）": ["食品", "烟草", "个人或家用物品", "健康", "救生", "娱乐"],
            "B部（作业；运输）": ["分离", "混合", "成型", "打印", "交通运输"],
            "C部（化学；冶金）": ["化学", "冶金", "有机化学", "高分子"],
            "D部（纺织；造纸）": ["纺织", "缝纫", "造纸"],
            "E部（固定建筑物）": ["建筑", "采矿"],
            "F部（机械工程；照明；加热；武器；爆破）": ["发动机", "泵", "机械元件", "照明", "加热"],
            "G部（物理）": ["仪器", "摄影", "计算", "信号", "核物理"],
            "H部（电学）": ["电气", "电子通信", "电路"],
        }

    def _extract_background_art(
        self, content: str, disclosure_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        提取背景技术

        Args:
            content: 文档内容
            disclosure_data: 原始数据

        Returns:
            背景技术信息
        """
        result = {
            "现有技术描述": "",
            "现有技术问题": [],
            "改进方向": "",
        }

        # 优先使用直接提供的信息
        if "background_art" in disclosure_data and disclosure_data["background_art"]:
            background_text = disclosure_data["background_art"]
            result["现有技术描述"] = background_text
            # 尝试提取问题
            result["现有技术问题"] = self._extract_problems_from_text(background_text)
        else:
            # 从content中提取
            import re

            match = re.search(r"背景技术[：:]\s*([\s\S]*?)(?=发明内容|技术问题|$)", content)
            if match:
                background_text = match.group(1).strip()
                result["现有技术描述"] = background_text
                result["现有技术问题"] = self._extract_problems_from_text(background_text)

        return result

    def _extract_problems_from_text(self, text: str) -> list[str]:
        """
        从文本中提取技术问题

        Args:
            text: 文本内容

        Returns:
            问题列表
        """
        import re

        problems = []

        # 规则1：查找问题关键词
        problem_patterns = [
            r"(?:问题|缺陷|不足|缺点)[：:]\s*([^\n。]+)",
            r"(?:存在|具有)(?:的)?(?:问题|缺陷|不足|缺点)[：:]?\s*([^\n。]+)",
            r"(?:然而|但是|但)[，,]\s*([^\n。]*?(?:问题|不足|缺陷))",
        ]

        for pattern in problem_patterns:
            matches = re.findall(pattern, text)
            problems.extend(matches)

        # 规则2：查找负面描述
        negative_keywords = ["效率低", "成本高", "精度差", "稳定性差", "复杂", "不便"]
        for keyword in negative_keywords:
            if keyword in text:
                # 提取包含关键词的句子
                sentences = re.split(r"[。！？]", text)
                for sentence in sentences:
                    if keyword in sentence:
                        problems.append(sentence.strip())

        return problems[:5]  # 限制前5个

    def _extract_technical_problem(self, content: str, disclosure_data: dict[str, Any]) -> str:
        """
        提取技术问题

        Args:
            content: 文档内容
            disclosure_data: 原始数据

        Returns:
            技术问题描述
        """
        if "technical_problem" in disclosure_data and disclosure_data["technical_problem"]:
            return disclosure_data["technical_problem"]

        # 从content中提取
        import re

        patterns = [
            r"技术问题[：:]\s*([^\n]+)",
            r"要解决的技术问题[：:]\s*([^\n]+)",
            r"发明目的[：:]\s*([^\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        # 从背景技术问题中提炼
        background = self._extract_background_art(content, disclosure_data)
        if background["现有技术问题"]:
            return "；".join(background["现有技术问题"][:3])

        return ""

    def _extract_technical_solution(
        self, content: str, disclosure_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        提取技术方案

        Args:
            content: 文档内容
            disclosure_data: 原始数据

        Returns:
            技术方案信息
        """
        result = {
            "技术方案概述": "",
            "核心特征": [],
            "关键技术步骤": [],
        }

        if "technical_solution" in disclosure_data and disclosure_data["technical_solution"]:
            solution_text = disclosure_data["technical_solution"]
            result["技术方案概述"] = solution_text
            result["核心特征"] = self._extract_features_from_text(solution_text)
        else:
            # 从content中提取
            import re

            match = re.search(r"技术方案[：:]\s*([\s\S]*?)(?=有益效果|实施方式|$)", content)
            if match:
                solution_text = match.group(1).strip()
                result["技术方案概述"] = solution_text
                result["核心特征"] = self._extract_features_from_text(solution_text)

        return result

    def _extract_features_from_text(self, text: str) -> list[str]:
        """
        从文本中提取技术特征

        Args:
            text: 文本内容

        Returns:
            技术特征列表
        """
        import re

        features = []

        # 规则1：查找特征列表（数字编号）
        numbered_patterns = [
            r"\d+[、.]\s*([^\n]+)",
            r"[①②③④⑤]\s*([^\n]+)",
        ]

        for pattern in numbered_patterns:
            matches = re.findall(pattern, text)
            if len(matches) >= 2:  # 至少2个才算列表
                features.extend(matches)
                break

        # 规则2：查找包含"包括"的句子
        if not features:
            sentences = re.split(r"[。；;]", text)
            for sentence in sentences:
                if "包括" in sentence or "设置" in sentence or "配置" in sentence:
                    features.append(sentence.strip())

        return features[:10]  # 限制前10个

    def _extract_beneficial_effects(
        self, content: str, disclosure_data: dict[str, Any]
    ) -> list[str]:
        """
        提取有益效果

        Args:
            content: 文档内容
            disclosure_data: 原始数据

        Returns:
            有益效果列表
        """
        # 优先使用直接提供的beneficial_effects
        if "beneficial_effects" in disclosure_data and disclosure_data["beneficial_effects"]:
            effects = disclosure_data["beneficial_effects"]

            # 如果是列表，直接返回
            if isinstance(effects, list):
                return effects

            # 如果是字符串，提取效果
            if isinstance(effects, str):
                return self._extract_effects_from_text(effects)

        # 从content中提取
        import re

        match = re.search(r"有益效果[：:]\s*([\s\S]*?)(?=实施方式|具体实施方式|$)", content)
        if match:
            return self._extract_effects_from_text(match.group(1))

        return []

    def _extract_effects_from_text(self, text: str) -> list[str]:
        """
        从文本中提取效果列表

        Args:
            text: 文本内容

        Returns:
            效果列表
        """
        import re

        effects = []

        # 规则1：查找效果列表（数字编号）
        numbered = re.findall(r"\d+[、.]\s*([^\n]+)", text)
        if len(numbered) >= 2:
            effects.extend(numbered)

        # 规则2：查找正面效果关键词
        positive_keywords = ["提高", "降低", "减少", "增加", "改善", "优化", "增强"]
        if not effects:
            sentences = re.split(r"[。；;]", text)
            for sentence in sentences:
                for keyword in positive_keywords:
                    if keyword in sentence:
                        effects.append(sentence.strip())
                        break

        return effects[:8]  # 限制前8个

    def _extract_examples(
        self, content: str, disclosure_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        提取实施例

        Args:
            content: 文档内容
            disclosure_data: 原始数据

        Returns:
            实施例列表
        """
        examples = []

        # 优先使用直接提供的实施例
        if "examples" in disclosure_data and disclosure_data["examples"]:
            return disclosure_data["examples"]

        # 从content中提取
        import re

        # 规则1：查找"实施例"章节
        example_sections = re.findall(r"实施例?\s*\d*[：:]\s*([\s\S]*?)(?=实施例|具体实施方式|权利要求|$)", content)

        for idx, section in enumerate(example_sections[:3], 1):  # 限制前3个
            example = {
                "实施例编号": idx,
                "描述": section.strip()[:500],  # 限制长度
                "关键参数": self._extract_parameters_from_text(section),
            }
            examples.append(example)

        return examples

    def _extract_parameters_from_text(self, text: str) -> dict[str, str]:
        """
        从文本中提取关键参数

        Args:
            text: 文本内容

        Returns:
            参数字典
        """
        import re

        parameters = {}

        # 查找参数定义（如：温度=100℃，压力=0.5MPa）
        param_patterns = [
            r"(\w+)\s*[=＝]\s*([^，,。。\n]+)",
            r"(\w+)\s*[：:]\s*([^，,。。\n]+)",
        ]

        for pattern in param_patterns:
            matches = re.findall(pattern, text)
            for key, value in matches:
                if len(key) <= 10 and len(value) <= 50:  # 合理性检查
                    parameters[key] = value

        return parameters

    def _check_completeness(self, extracted_info: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """
        检查完整性

        Args:
            extracted_info: 提取的信息

        Returns:
            完整性检查结果
        """
        completeness = {}

        # 检查每个字段的完整性
        for field, value in extracted_info.items():
            is_complete = bool(value)

            # 特殊检查
            if field == "技术领域":
                is_complete = bool(value.get("技术领域"))
            elif field == "背景技术":
                is_complete = bool(value.get("现有技术描述"))
            elif field == "技术方案":
                is_complete = bool(value.get("技术方案概述"))
            elif field == "实施例":
                is_complete = len(value) > 0

            completeness[field] = {
                "完整": is_complete,
                "缺失内容": "" if is_complete else f"缺少{field}",
            }

        return completeness

    def _assess_quality(
        self, extracted_info: dict[str, Any], completeness: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """
        评估质量

        Args:
            extracted_info: 提取的信息
            completeness: 完整性检查结果

        Returns:
            质量评估结果
        """
        # 完整性评分
        complete_count = sum(1 for v in completeness.values() if v["完整"])
        completeness_score = complete_count / len(completeness)

        # 详细程度评分
        detail_score = self._assess_detail_level(extracted_info)

        # 清晰度评分
        clarity_score = self._assess_clarity(extracted_info)

        # 综合评分
        overall_score = completeness_score * 0.4 + detail_score * 0.3 + clarity_score * 0.3

        return {
            "完整性评分": completeness_score,
            "详细程度评分": detail_score,
            "清晰度评分": clarity_score,
            "综合评分": overall_score,
            "质量等级": self._get_quality_level(overall_score),
        }

    def _assess_detail_level(self, extracted_info: dict[str, Any]) -> float:
        """
        评估详细程度

        Args:
            extracted_info: 提取的信息

        Returns:
            详细程度评分（0-1）
        """
        total_length = 0
        field_count = 0

        for _value in extracted_info.values():
            if isinstance(_value, str):
                total_length += len(_value)
                field_count += 1
            elif isinstance(_value, dict):
                # 对于字典类型，统计主要字段的长度
                for k, v in _value.items():
                    if isinstance(v, str) and k not in ["IPC分类", "关键词"]:
                        total_length += len(v)
                        field_count += 1
            elif isinstance(_value, list):
                # 对于列表类型，统计元素数量
                total_length += len(_value) * 20  # 每个元素假设20字符
                field_count += 1

        if field_count == 0:
            return 0.0

        avg_length = total_length / field_count

        # 评分标准：平均长度>100字符为满分
        return min(avg_length / 100, 1.0)

    def _assess_clarity(self, extracted_info: dict[str, Any]) -> float:
        """
        评估清晰度

        Args:
            extracted_info: 提取的信息

        Returns:
            清晰度评分（0-1）
        """
        clarity_indicators = {
            "发明名称": len(extracted_info.get("发明名称", "")) >= 5,
            "技术问题": "；" not in extracted_info.get("技术问题", ""),  # 避免多个问题混杂
            "技术方案": len(extracted_info.get("技术方案", {}).get("核心特征", [])) >= 3,
            "有益效果": len(extracted_info.get("有益效果", [])) >= 2,
        }

        clarity_count = sum(clarity_indicators.values())
        return clarity_count / len(clarity_indicators)

    def _generate_disclosure_recommendations_detailed(
        self,
        extracted_info: dict[str, Any],
        completeness: dict[str, dict[str, Any]],
        quality_assessment: dict[str, Any],
    ) -> list[str]:
        """
        生成详细的改进建议

        Args:
            extracted_info: 提取的信息
            completeness: 完整性检查结果
            quality_assessment: 质量评估结果

        Returns:
            建议列表
        """
        recommendations = []

        # 1. 完整性建议
        missing_fields = [
            f"{field}（{v['缺失内容']}）" for field, v in completeness.items() if not v["完整"]
        ]
        if missing_fields:
            recommendations.append(f"【完整性】补充缺失内容：{', '.join(missing_fields)}")

        # 2. 详细程度建议
        detail_score = quality_assessment["详细程度评分"]
        if detail_score < 0.6:
            recommendations.append("【详细程度】技术描述过于简略，建议补充具体技术参数、" "实施细节等，建议每部分不少于100字")

        # 3. 清晰度建议
        clarity_score = quality_assessment["清晰度评分"]
        if clarity_score < 0.6:
            recommendations.append("【清晰度】技术描述不够清晰，建议使用分点描述，" "避免冗长句子混杂")

        # 4. 技术方案建议
        technical_solution = extracted_info.get("技术方案", {})
        if len(technical_solution.get("核心特征", [])) < 3:
            recommendations.append("【技术方案】核心特征数量不足，建议提炼3个以上必要技术特征")

        # 5. 有益效果建议
        beneficial_effects = extracted_info.get("有益效果", [])
        if len(beneficial_effects) < 2:
            recommendations.append("【有益效果】有益效果描述不足，建议至少列出2个具体的有益效果")

        # 6. 实施例建议
        examples = extracted_info.get("实施例", [])
        if len(examples) == 0:
            recommendations.append("【实施例】缺少实施例，建议补充至少1个具体实施方式")

        # 如果没有问题
        if not recommendations:
            recommendations.append("技术交底书质量良好，建议进行现有技术检索后进入撰写阶段")

        return recommendations

    async def assess_patentability(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        评估可专利性

        Args:
            data: 包含技术交底书和现有技术的数据

        Returns:
            可专利性评估报告
        """
        try:
            prompt = self._build_patentability_assessment_prompt(data)
            response = await self._call_llm_with_fallback(
                prompt=prompt, task_type="assess_patentability"
            )

            return self._parse_analysis_response(response)

        except Exception as e:
            self.logger.warning(f"LLM可专利性评估失败: {e}，使用规则-based评估")
            return self._assess_patentability_by_rules(data)

    def _assess_patentability_by_rules(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        基于规则的可专利性评估（降级方案）

        Args:
            data: 评估数据

        Returns:
            可专利性评估报告
        """
        disclosure = data.get("disclosure", {})
        prior_art = data.get("prior_art", [])

        # 简化版可专利性评估
        novelty_score = 0.7 if len(prior_art) < 5 else 0.5
        creativity_score = 0.7 if disclosure.get("technical_solution") else 0.4
        practicality_score = 0.8 if disclosure.get("beneficial_effects") else 0.6

        overall_score = (novelty_score + creativity_score + practicality_score) / 3

        return {
            "disclosure_id": disclosure.get("disclosure_id", "未知"),
            "novelty_assessment": {
                "score": novelty_score,
                "description": "新颖性评估",
            },
            "creativity_assessment": {
                "score": creativity_score,
                "description": "创造性评估",
            },
            "practicality_assessment": {
                "score": practicality_score,
                "description": "实用性评估",
            },
            "overall_score": overall_score,
            "patentability_level": self._get_quality_level(overall_score),
            "recommendations": ["建议进行现有技术检索"] if overall_score < 0.7 else [],
            "assessed_at": self._get_timestamp(),
        }

    async def draft_specification(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        撰写说明书

        Args:
            data: 包含技术交底书和可专利性评估的数据

        Returns:
            说明书草稿
        """
        try:
            prompt = self._build_specification_draft_prompt(data)
            response = await self._call_llm_with_fallback(
                prompt=prompt, task_type="draft_specification"
            )

            return {
                "specification_draft": response,
                "drafted_at": self._get_timestamp(),
            }

        except Exception as e:
            self.logger.warning(f"LLM说明书撰写失败: {e}，使用模板生成")
            return self._draft_specification_by_template(data)

    def _draft_specification_by_template(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        基于模板撰写说明书（降级方案）

        Args:
            data: 包含技术交底书和可专利性评估的数据

        Returns:
            说明书草稿
        """
        disclosure = data.get("disclosure", {})

        # 构建说明书各部分
        specification_parts = {
            "发明名称": self._generate_title(disclosure),
            "技术领域": self._draft_technical_field(disclosure),
            "背景技术": self._draft_background_art(disclosure),
            "发明内容": self._draft_invention_content(disclosure),
            "附图说明": self._draft_drawing_description(disclosure),
            "具体实施方式": self._draft_detailed_description(disclosure),
        }

        # 组装完整说明书
        full_specification = self._assemble_specification(specification_parts)

        return {
            "specification_draft": full_specification,
            "specification_parts": specification_parts,
            "drafted_at": self._get_timestamp(),
        }

    def _generate_title(self, disclosure: dict[str, Any]) -> str:
        """
        生成发明名称

        规则：
        - 简洁准确（通常<25字）
        - 包含技术领域
        - 体现技术特点
        - 避免"新型"、"改进"等词汇

        Args:
            disclosure: 技术交底书

        Returns:
            发明名称
        """
        # 优先使用提供的标题
        if "title" in disclosure and disclosure["title"]:
            title = disclosure["title"]
            # 清理标题
            title = title.replace("新型", "").replace("改进", "").strip()
            return title

        # 从技术方案提炼
        technical_solution = disclosure.get("technical_solution", "")
        if technical_solution:
            # 提取关键词
            import re

            # 查找"一种..."模式
            match = re.search(r"一种(.{5,30})(?:装置|方法|系统|设备)", technical_solution)
            if match:
                return match.group(0)

        # 使用技术领域+核心特征
        technical_field = disclosure.get("technical_field", "")
        if technical_field:
            return f"一种{technical_field}相关装置"

        return "未命名发明"

    def _draft_technical_field(self, disclosure: dict[str, Any]) -> str:
        """
        撰写技术领域

        格式："本发明涉及...技术领域，具体涉及..."

        Args:
            disclosure: 技术交底书

        Returns:
            技术领域描述
        """
        technical_field = disclosure.get("technical_field", "")

        if not technical_field:
            return "本发明涉及机械制造技术领域。"

        # 标准化格式
        if not technical_field.startswith("本发明"):
            technical_field = f"本发明涉及{technical_field}。"

        return technical_field

    def _draft_background_art(self, disclosure: dict[str, Any]) -> str:
        """
        撰写背景技术

        结构：
        1. 技术领域概述
        2. 现有技术描述
        3. 现有技术问题（层次化）

        Args:
            disclosure: 技术交底书

        Returns:
            背景技术描述
        """
        background = disclosure.get("background_art", "")

        if not background:
            # 基于技术问题生成简化版背景
            technical_problem = disclosure.get("technical_problem", "")
            return f"现有技术中，存在{technical_problem}等问题。"

        # 检查是否已包含标准结构
        if "现有技术" in background or "背景技术" in background:
            return background

        # 标准化格式
        background_text = f"现有技术中，{background}"

        return background_text

    def _draft_invention_content(self, disclosure: dict[str, Any]) -> str:
        """
        撰写发明内容（三段式）

        结构：
        1. 技术问题（要解决的技术问题）
        2. 技术方案（完整描述解决方案）
        3. 技术效果（有益效果，具体可量化）

        Args:
            disclosure: 技术交底书

        Returns:
            发明内容描述
        """
        parts = []

        # 第1段：技术问题
        technical_problem = disclosure.get("technical_problem", "")
        if technical_problem:
            parts.append(f"为了解决上述技术问题，本发明提供{technical_problem}。")
        else:
            parts.append("为了解决现有技术中的问题，本发明提供以下技术方案。")

        # 第2段：技术方案
        technical_solution = disclosure.get("technical_solution", "")
        if technical_solution:
            # 标准化开头
            if not technical_solution.startswith("本发明"):
                technical_solution = f"本发明{technical_solution}"
            parts.append(technical_solution)

        # 第3段：技术效果
        beneficial_effects = disclosure.get("beneficial_effects", "")
        if beneficial_effects:
            if isinstance(beneficial_effects, list):
                effects_text = "；".join(beneficial_effects)
            else:
                effects_text = beneficial_effects

            if not effects_text.startswith("与现有技术相比"):
                effects_text = f"与现有技术相比，本发明{effects_text}"

            parts.append(effects_text)

        return "\n\n".join(parts)

    def _draft_drawing_description(self, disclosure: dict[str, Any]) -> str:
        """
        撰写附图说明

        格式：
        "图1是...示意图；
        图2是...示意图；"

        Args:
            disclosure: 技术交底书

        Returns:
            附图说明
        """
        # 检查是否提供附图信息
        drawings = disclosure.get("drawings", [])

        if not drawings:
            # 默认附图说明
            return "图1是本发明实施例的结构示意图；"

        # 生成附图说明
        drawing_descriptions = []
        for idx, drawing in enumerate(drawings, 1):
            if isinstance(drawing, str):
                drawing_descriptions.append(f"图{idx}是{drawing}；")
            elif isinstance(drawing, dict):
                desc = drawing.get("description", f"本发明实施例{idx}的结构示意图")
                drawing_descriptions.append(f"图{idx}是{desc}；")

        return "\n".join(drawing_descriptions)

    def _draft_detailed_description(self, disclosure: dict[str, Any]) -> str:
        """
        撰写具体实施方式

        结构：
        1. 实施方式概述
        2. 具体实施例（可选）
        3. 实现细节

        Args:
            disclosure: 技术交底书

        Returns:
            具体实施方式描述
        """
        # 优先使用提供的实施方式
        detailed_desc = disclosure.get("detailed_description", "")
        if detailed_desc:
            return detailed_desc

        # 基于技术方案生成实施方式
        technical_solution = disclosure.get("technical_solution", "")
        examples = disclosure.get("examples", [])

        if not technical_solution:
            return "下面结合附图和具体实施例对本发明作进一步详细说明。"

        # 构建实施方式
        parts = ["下面结合附图和具体实施例对本发明作进一步详细说明。"]

        # 添加实施例
        if examples and len(examples) > 0:
            for idx, example in enumerate(examples, 1):
                if isinstance(example, str):
                    parts.append(f"\n实施例{idx}：\n{example}")
                elif isinstance(example, dict):
                    desc = example.get("description", "")
                    parts.append(f"\n实施例{idx}：\n{desc}")

        # 如果没有实施例，添加技术方案细化
        if not examples:
            parts.append(f"\n具体地，{technical_solution}")

        return "\n".join(parts)

    def _assemble_specification(self, parts: dict[str, str]) -> str:
        """
        组装完整说明书

        Args:
            parts: 说明书各部分

        Returns:
            完整说明书
        """
        # 标准说明书结构
        structure = [
            ("发明名称", parts.get("发明名称", "")),
            ("技术领域", parts.get("技术领域", "")),
            ("背景技术", parts.get("背景技术", "")),
            ("发明内容", parts.get("发明内容", "")),
            ("附图说明", parts.get("附图说明", "")),
            ("具体实施方式", parts.get("具体实施方式", "")),
        ]

        # 组装
        lines = []
        for section_name, content in structure:
            if content:
                lines.append(f"\n【{section_name}】")
                lines.append(content)

        return "\n".join(lines)

    async def draft_claims(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        撰写权利要求书

        Args:
            data: 包含技术交底书和说明书的数据

        Returns:
            权利要求书草稿
        """
        try:
            prompt = self._build_claims_draft_prompt(data)
            response = await self._call_llm_with_fallback(prompt=prompt, task_type="draft_claims")

            return {
                "claims_draft": response,
                "drafted_at": self._get_timestamp(),
            }

        except Exception as e:
            self.logger.warning(f"LLM权利要求书撰写失败: {e}，使用模板生成")
            return self._draft_claims_by_template(data)

    def _draft_claims_by_template(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        基于模板撰写权利要求书（降级方案）

        Args:
            data: 包含技术交底书和说明书的数据

        Returns:
            权利要求书草稿
        """
        disclosure = data.get("disclosure", {})

        # 第1步：提取必要技术特征
        essential_features = self._extract_essential_features(disclosure)

        # 第2步：提取优选技术特征
        preferred_features = self._extract_preferred_features(disclosure)

        # 第3步：生成独立权利要求
        independent_claim = self._generate_independent_claim(disclosure, essential_features)

        # 第4步：生成从属权利要求
        dependent_claims = self._generate_dependent_claims(
            preferred_features, len([independent_claim])  # 起始编号
        )

        # 第5步：编号和组装
        all_claims = [independent_claim] + dependent_claims
        numbered_claims = self._number_claims(all_claims)

        # 组装权利要求书
        claims_text = "\n\n".join(numbered_claims)

        return {
            "claims_draft": claims_text,
            "独立权利要求": independent_claim,
            "从属权利要求数量": len(dependent_claims),
            "必要技术特征": essential_features,
            "优选技术特征": preferred_features,
            "drafted_at": self._get_timestamp(),
        }

    def _extract_essential_features(self, disclosure: dict[str, Any]) -> list[str]:
        """
        提取必要技术特征

        方法：
        - 从技术方案中提取
        - 去除非必要特征
        - 按重要性排序

        Args:
            disclosure: 技术交底书

        Returns:
            必要技术特征列表
        """
        technical_solution = disclosure.get("technical_solution", "")

        if not technical_solution:
            return []

        # 提取特征
        features = self._extract_features_from_text(technical_solution)

        # 评估必要性（基于关键词和上下文）
        essential_keywords = ["包括", "设置", "配置", "具有", "特征在于"]
        essential_features = []

        for feature in features:
            # 包含必要关键词的特征
            if any(keyword in feature for keyword in essential_keywords):
                essential_features.append(feature)

        # 限制数量（独立权利要求通常5-10个特征）
        return essential_features[:10]

    def _extract_preferred_features(self, disclosure: dict[str, Any]) -> list[str]:
        """
        提取优选技术特征

        Args:
            disclosure: 技术交底书

        Returns:
            优选技术特征列表
        """
        preferred = []

        # 从有益效果中反推特征
        beneficial_effects = disclosure.get("beneficial_effects", [])
        if isinstance(beneficial_effects, list):
            for effect in beneficial_effects:
                if "优选" in effect or "进一步" in effect:
                    preferred.append(effect)

        # 从实施例中提取
        examples = disclosure.get("examples", [])
        if isinstance(examples, list) and len(examples) > 1:
            # 有多个实施例，说明有优选方案
            preferred.append("根据实施例2所述的进一步优化方案")

        return preferred

    def _generate_independent_claim(
        self, disclosure: dict[str, Any], essential_features: list[str]
    ) -> str:
        """
        生成独立权利要求

        结构：
        前序部分：一种[名称]，其特征在于，
        特征部分：包括...；...；...

        Args:
            disclosure: 技术交底书
            essential_features: 必要技术特征

        Returns:
            独立权利要求文本
        """
        # 生成标题
        title = self._generate_title(disclosure)

        # 判断类型（装置/方法）
        claim_type = self._determine_claim_type(disclosure)

        if claim_type == "method":
            return self._format_independent_method_claim(title, essential_features)
        else:
            return self._format_independent_device_claim(title, essential_features)

    def _determine_claim_type(self, disclosure: dict[str, Any]) -> str:
        """
        判断权利要求类型

        Args:
            disclosure: 技术交底书

        Returns:
            "method" 或 "device"
        """
        technical_solution = disclosure.get("technical_solution", "")

        # 方法类关键词
        method_keywords = ["方法", "工艺", "步骤", "流程", "处理方法"]
        for keyword in method_keywords:
            if keyword in technical_solution:
                return "method"

        # 默认为装置类
        return "device"

    def _format_independent_method_claim(self, title: str, features: list[str]) -> str:
        """
        格式化方法独立权利要求

        Args:
            title: 标题
            features: 技术特征

        Returns:
            权利要求文本
        """
        # 前序部分
        preamble = f"一种{title}，其特征在于，包括："

        # 特征部分（转换为步骤）
        steps = []
        for feature in features:
            # 清理特征描述（移除末尾标点）
            feature_clean = feature.strip()
            # 移除中文标点符号
            for char in "，。；；":
                feature_clean = feature_clean.rstrip(char)
            # 添加步骤序号
            steps.append(f"{feature_clean}；")

        # 组装
        claim = preamble + "\n    " + "\n    ".join(steps)

        return claim

    def _format_independent_device_claim(self, title: str, features: list[str]) -> str:
        """
        格式化装置独立权利要求

        Args:
            title: 标题
            features: 技术特征

        Returns:
            权利要求文本
        """
        # 前序部分
        preamble = f"一种{title}，其特征在于，包括："

        # 特征部分
        components = []
        for feature in features:
            feature_clean = feature.strip()
            # 移除中文标点符号
            for char in "，。；；":
                feature_clean = feature_clean.rstrip(char)
            components.append(f"{feature_clean}；")

        # 组装
        claim = preamble + "\n    " + "\n    ".join(components)

        return claim

    def _generate_dependent_claims(
        self, preferred_features: list[str], start_number: int
    ) -> list[str]:
        """
        生成从属权利要求

        规则：
        - 优选实施例提炼
        - 细化附加特征
        - 层次化布局
        - 引用关系正确

        Args:
            preferred_features: 优选技术特征
            start_number: 起始编号

        Returns:
            从属权利要求列表
        """
        dependent_claims = []

        for idx, feature in enumerate(preferred_features, start=start_number):
            # 引用前一项权利要求
            reference = idx - 1

            # 格式化从属权利要求
            claim = f"{idx}. 根据权利要求{reference}所述的发明，其特征在于，{feature}。"

            dependent_claims.append(claim)

        return dependent_claims

    def _number_claims(self, claims: list[str]) -> list[str]:
        """
        权利要求编号

        规则：
        - 阿拉伯数字连续编号
        - 独立权利要求：1
        - 从属权利要求：2-N

        Args:
            claims: 权利要求列表

        Returns:
            编号后的权利要求列表
        """
        numbered = []

        for idx, claim in enumerate(claims, 1):
            # 如果已经有编号，跳过
            if claim.startswith(f"{idx}."):
                numbered.append(claim)
            else:
                numbered.append(f"{idx}. {claim}")

        return numbered

    async def optimize_protection_scope(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        优化保护范围

        Args:
            data: 包含权利要求书和现有技术的数据

        Returns:
            优化建议
        """
        try:
            prompt = self._build_optimization_prompt(data)
            response = await self._call_llm_with_fallback(
                prompt=prompt, task_type="optimize_protection_scope"
            )

            return self._parse_analysis_response(response)

        except Exception as e:
            self.logger.error(f"保护范围优化失败: {e}")
            return {
                "optimization_suggestions": [],
                "error": str(e),
            }

    async def review_adequacy(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        审查充分公开

        Args:
            data: 包含说明书和权利要求书的数据

        Returns:
            充分公开审查报告
        """
        try:
            prompt = self._build_adequacy_review_prompt(data)
            response = await self._call_llm_with_fallback(
                prompt=prompt, task_type="review_adequacy"
            )

            return self._parse_analysis_response(response)

        except Exception as e:
            self.logger.error(f"充分公开审查失败: {e}")
            return {
                "adequacy_review": {},
                "error": str(e),
            }

    async def detect_common_errors(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        检测常见错误

        Args:
            data: 包含说明书和权利要求书的数据

        Returns:
            错误检测报告
        """
        try:
            prompt = self._build_error_detection_prompt(data)
            response = await self._call_llm_with_fallback(
                prompt=prompt, task_type="detect_common_errors"
            )

            return self._parse_analysis_response(response)

        except Exception as e:
            self.logger.error(f"常见错误检测失败: {e}")
            return {
                "detected_errors": [],
                "error": str(e),
            }

    async def draft_patent_application(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        完整专利申请撰写流程

        Args:
            data: 技术交底书数据

        Returns:
            完整的专利申请文件
        """
        # 1. 分析技术交底书
        disclosure_analysis = await self.analyze_disclosure(data)

        # 2. 评估可专利性
        patentability_assessment = await self.assess_patentability(
            {
                "disclosure": data,
                "prior_art": data.get("prior_art", []),
            }
        )

        # 3. 撰写说明书
        specification_result = await self.draft_specification(
            {
                "disclosure": data,
                "patentability": patentability_assessment,
            }
        )

        # 4. 撰写权利要求书
        claims_result = await self.draft_claims(
            {
                "disclosure": data,
                "specification": specification_result.get("specification_draft", ""),
            }
        )

        # 5. 审查充分公开
        adequacy_review = await self.review_adequacy(
            {
                "specification": specification_result.get("specification_draft", ""),
                "claims": claims_result.get("claims_draft", ""),
            }
        )

        # 6. 检测常见错误
        error_detection = await self.detect_common_errors(
            {
                "specification": specification_result.get("specification_draft", ""),
                "claims": claims_result.get("claims_draft", ""),
            }
        )

        return {
            "disclosure_analysis": disclosure_analysis,
            "patentability_assessment": patentability_assessment,
            "specification": specification_result,
            "claims": claims_result,
            "adequacy_review": adequacy_review,
            "error_detection": error_detection,
            "completed_at": self._get_timestamp(),
        }

    # ========== 辅助方法 ==========

    def _build_disclosure_analysis_prompt(self, disclosure_data: dict[str, Any]) -> str:
        """
        构建交底书分析提示词

        使用优化后的提示词模板(v2.0),包含Few-shot示例和CoT推理步骤
        """
        return PatentDraftingPrompts.format_user_prompt(
            "disclosure_analysis",
            disclosure_data=json.dumps(disclosure_data, ensure_ascii=False, indent=2),
        )

    def _build_patentability_assessment_prompt(self, data: dict[str, Any]) -> str:
        """
        构建可专利性评估提示词

        使用优化后的提示词模板(v2.0),包含Few-shot示例和CoT推理步骤
        """
        disclosure = data.get("disclosure", {})
        prior_art = data.get("prior_art", [])

        return PatentDraftingPrompts.format_user_prompt(
            "patentability_assessment",
            disclosure_data=json.dumps(disclosure, ensure_ascii=False, indent=2),
            prior_art=json.dumps(prior_art, ensure_ascii=False, indent=2),
        )

    def _build_specification_draft_prompt(self, data: dict[str, Any]) -> str:
        """
        构建说明书撰写提示词

        使用优化后的提示词模板(v2.0),包含Few-shot示例和CoT推理步骤
        """
        disclosure = data.get("disclosure", {})
        patentability = data.get("patentability", {})

        return PatentDraftingPrompts.format_user_prompt(
            "specification_draft",
            disclosure_data=json.dumps(disclosure, ensure_ascii=False, indent=2),
            patentability_assessment=json.dumps(patentability, ensure_ascii=False, indent=2),
        )

    def _build_claims_draft_prompt(self, data: dict[str, Any]) -> str:
        """
        构建权利要求书撰写提示词

        使用优化后的提示词模板(v2.0),包含Few-shot示例和CoT推理步骤
        """
        disclosure = data.get("disclosure", {})
        specification = data.get("specification", "")

        return PatentDraftingPrompts.format_user_prompt(
            "claims_draft",
            disclosure_data=json.dumps(disclosure, ensure_ascii=False, indent=2),
            specification=specification,
        )

    def _build_optimization_prompt(self, data: dict[str, Any]) -> str:
        """
        构建保护范围优化提示词

        使用优化后的提示词模板(v2.0),包含Few-shot示例和CoT推理步骤
        """
        claims = data.get("claims", "")
        prior_art = data.get("prior_art", [])

        return PatentDraftingPrompts.format_user_prompt(
            "optimize_protection_scope",
            claims=claims,
            prior_art=json.dumps(prior_art, ensure_ascii=False, indent=2),
        )

    def _build_adequacy_review_prompt(self, data: dict[str, Any]) -> str:
        """
        构建充分公开审查提示词

        使用优化后的提示词模板(v2.0),包含Few-shot示例和CoT推理步骤
        """
        specification = data.get("specification", "")
        claims = data.get("claims", "")

        return PatentDraftingPrompts.format_user_prompt(
            "adequacy_review", specification=specification, claims=claims
        )

    def _build_error_detection_prompt(self, data: dict[str, Any]) -> str:
        """
        构建常见错误检测提示词

        使用优化后的提示词模板(v2.0),包含Few-shot示例和CoT推理步骤
        """
        specification = data.get("specification", "")
        claims = data.get("claims", "")

        return PatentDraftingPrompts.format_user_prompt(
            "error_detection", specification=specification, claims=claims
        )

    def _parse_analysis_response(self, response: str) -> dict[str, Any]:
        """解析LLM分析响应"""
        try:
            import re

            # 提取JSON
            json_match = re.search(r"```json\s*([\s\S]*?)```", response)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)
            return result

        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"解析LLM响应失败: {e}")
            return {
                "error": "LLM响应解析失败",
                "raw_response": response,
            }

    def _get_quality_level(self, score: float) -> str:
        """获取质量等级"""
        if score >= 0.9:
            return "优秀"
        elif score >= 0.75:
            return "良好"
        elif score >= 0.6:
            return "合格"
        else:
            return "待改进"

    def _generate_disclosure_recommendations(self, completeness: dict[str, bool]) -> list[str]:
        """生成交底书改进建议"""
        recommendations = []

        field_names = {
            "title": "标题",
            "technical_field": "技术领域",
            "background_art": "背景技术",
            "invention_summary": "发明摘要",
            "technical_problem": "技术问题",
            "technical_solution": "技术方案",
            "beneficial_effects": "有益效果",
        }

        missing = [field_names[field] for field, complete in completeness.items() if not complete]

        if missing:
            recommendations.append(f"补充缺失内容：{', '.join(missing)}")

        if not recommendations:
            recommendations.append("技术交底书内容完整，质量良好")

        return recommendations

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()
