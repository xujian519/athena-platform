#!/usr/bin/env python3
from __future__ import annotations
"""
场景识别器 - 识别用户输入的业务场景
Scenario Identifier - Identify business scenarios from user input

版本: 1.0.0
创建时间: 2026-01-23
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Tuple, Dict

logger = logging.getLogger(__name__)


class Domain(Enum):
    """业务领域"""

    PATENT = "patent"
    TRADEMARK = "trademark"
    LEGAL = "legal"
    COPYRIGHT = "copyright"
    OTHER = "other"


class TaskType(Enum):
    """任务类型"""

    CREATIVITY_ANALYSIS = "creativity_analysis"
    NOVELTY_ANALYSIS = "novelty_analysis"
    INFRINGEMENT = "infringement"
    SIMILARITY = "similarity"
    VALIDITY = "validity"
    DRAFTING = "drafting"
    SEARCH = "search"
    OTHER = "other"


class Phase(Enum):
    """业务阶段"""

    APPLICATION = "application"
    EXAMINATION = "examination"
    OPPOSITION = "opposition"
    LITIGATION = "litigation"
    OTHER = "other"


@dataclass
class ScenarioContext:
    """场景上下文"""

    domain: Domain
    task_type: TaskType
    phase: Phase
    confidence: float
    extracted_variables: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class ScenarioIdentifier:
    """
    场景识别器

    从用户输入中识别业务领域、任务类型和阶段
    支持变量提取和置信度评估
    """

    # 关键词匹配规则
    KEYWORD_RULES = {
        Domain.PATENT: {
            TaskType.CREATIVITY_ANALYSIS: [
                "创造性",
                "创新性",
                "创新高度",
                "技术贡献",
                "突出的实质性特点",
                "显著的进步",
                "用途发明",
                "反向教导",
                "技术启示",
                "预料不到",
                "事后诸葛亮",
                "技术偏见",
                "复审请求",
                "驳回复审",
            ],
            TaskType.NOVELTY_ANALYSIS: ["新颖性", "现有技术", "公开", "在先技术", "不属于现有技术"],
            TaskType.INFRINGEMENT: ["侵权", "落入保护范围", "等同", "相同", "保护范围"],
            TaskType.VALIDITY: ["无效", "无效宣告", "不符合专利法", "不具备", "不授予"],
            TaskType.DRAFTING: ["撰写", "写", "起草", "生成", "申请文件", "权利要求", "说明书", "摘要"],
            TaskType.SEARCH: ["检索", "查新", "现有技术检索", "对比文件"],
        },
        Domain.TRADEMARK: {
            TaskType.SIMILARITY: ["相似", "近似", "混淆", "容易误认", "视觉近似", "读音近似"],
            TaskType.INFRINGEMENT: ["侵权", "擅自使用", "相同或相似", "容易导致混淆"],
            TaskType.VALIDITY: ["无效", "撤销", "显著性", "缺乏显著性"],
            TaskType.DRAFTING: ["申请", "注册", "商标申请", "图样"],
        },
        Domain.LEGAL: {
            TaskType.INFRINGEMENT: ["侵权", "损害赔偿", "停止侵害", "法律责任"],
            TaskType.VALIDITY: ["效力", "无效", "可撤销"],
            TaskType.DRAFTING: ["合同", "起草", "法律文书", "协议"],
        },
    }

    # 阶段识别规则
    PHASE_KEYWORDS = {
        Phase.APPLICATION: ["申请", "提交", "申请文件", "立案"],
        Phase.EXAMINATION: ["审查", "审查意见", "驳回", "补正", "答复"],
        Phase.OPPOSITION: ["异议", "无效宣告", "复审"],
        Phase.LITIGATION: ["诉讼", "起诉", "判决", "法院", "法庭", "裁决"],
    }

    def __init__(self, enable_llm_fallback: bool = False):
        """
        初始化场景识别器

        Args:
            enable_llm_fallback: 是否启用LLM回退(当规则匹配失败时)
        """
        self.enable_llm_fallback = enable_llm_fallback

    def identify_scenario(
        self, user_input: str, additional_context: Optional[Dict[str, Any]] = None
    ) -> ScenarioContext:
        """
        识别用户输入的场景

        Args:
            user_input: 用户输入文本
            additional_context: 额外上下文信息(如历史对话、用户画像等)

        Returns:
            ScenarioContext: 识别的场景上下文
        """
        logger.info(f"🔍 开始场景识别: {user_input[:100]}...")

        result = ScenarioContext(
            domain=Domain.OTHER,
            task_type=TaskType.OTHER,
            phase=Phase.OTHER,
            confidence=0.0,
            extracted_variables={},
            metadata={},
        )

        # 1. 识别领域
        domain, domain_confidence = self._identify_domain(user_input)
        result.domain = domain
        logger.info(f"  领域: {domain.value} (置信度: {domain_confidence:.2f})")

        # 2. 识别任务类型
        task_type = TaskType.OTHER  # 默认值
        task_confidence = 0.0
        if domain in self.KEYWORD_RULES:
            task_type, task_confidence = self._identify_task_type(user_input, domain)
            result.task_type = task_type
            result.confidence = (domain_confidence + task_confidence) / 2
            logger.info(f"  任务: {task_type.value} (置信度: {task_confidence:.2f})")
        else:
            result.task_type = TaskType.OTHER
            result.confidence = domain_confidence

        # 3. 识别阶段
        phase, phase_confidence = self._identify_phase(user_input)
        result.phase = phase
        logger.info(f"  阶段: {phase.value} (置信度: {phase_confidence:.2f})")

        # 4. 提取变量
        result.extracted_variables = self._extract_variables(user_input, domain, task_type)
        logger.info(f"  提取变量: {list(result.extracted_variables.keys())}")

        # 5. 元数据
        result.metadata = {
            "input_length": len(user_input),
            "additional_context": additional_context or {},
            "timestamp": None,  # 可以在调用时设置
        }

        logger.info(f"✅ 场景识别完成,总体置信度: {result.confidence:.2f}")

        return result

    def _identify_domain(self, text: str) -> tuple[Domain, float]:
        """识别业务领域"""
        domain_keywords = {
            Domain.PATENT: [
                "专利",
                "发明",
                "实用新型",
                "外观设计",
                "外观",
                "设计",
                "技术方案",
                "权利要求",
                "说明书",
                "实施例",
            ],
            Domain.TRADEMARK: ["商标", "品牌", "logo", "标识", "图形", "商号", "服务商标"],
            Domain.LEGAL: ["诉讼", "法院", "判决", "法律", "法规", "合同", "协议"],
            Domain.COPYRIGHT: ["版权", "著作权", "作品", "署名", "复制权"],
        }

        max_score = 0
        identified_domain = Domain.OTHER

        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > max_score:
                max_score = score
                identified_domain = domain

        # 计算置信度:基于匹配的关键词数量
        confidence = min(max_score * 0.15, 1.0)

        return identified_domain, confidence

    def _identify_task_type(self, text: str, domain: Domain) -> tuple[TaskType, float]:
        """识别任务类型"""
        if domain not in self.KEYWORD_RULES:
            return TaskType.OTHER, 0.0

        task_keywords = self.KEYWORD_RULES[domain]
        max_score = 0
        identified_task = TaskType.OTHER

        for task_type, keywords in task_keywords.items():
            # 计算关键词匹配度
            score = sum(1 for kw in keywords if kw in text)
            if score > max_score:
                max_score = score
                identified_task = task_type

        # 计算置信度
        confidence = min(max_score * 0.2, 1.0)

        return identified_task, confidence

    def _identify_phase(self, text: str) -> tuple[Phase, float]:
        """识别业务阶段"""
        max_score = 0
        identified_phase = Phase.OTHER

        for phase, keywords in self.PHASE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > max_score:
                max_score = score
                identified_phase = phase

        confidence = min(max_score * 0.25, 1.0)

        return identified_phase, confidence

    def _extract_variables(self, text: str, domain: Domain, task_type: TaskType) -> dict[str, Any]:
        """从文本中提取变量"""
        variables = {}

        if domain == Domain.PATENT:
            # 提取技术领域
            tech_field_patterns = [
                r"技术领域[::]\s*([^。,\n]+)",
                r"属于\s*([^。,\n]+)\s*领域",
                r"在\s*([^。,\n]+)\s*领域",
            ]
            for pattern in tech_field_patterns:
                match = re.search(pattern, text)
                if match:
                    variables["technology_field"] = match.group(1).strip()
                    break

            # 提取技术问题
            problem_patterns = [
                r"技术问题[::]\s*([^。,\n]+)",
                r"解决\s*([^。,\n]+)\s*(的问题|难题)",
                r"针对\s*([^。,\n]+)\s*(的问题|难题)",
            ]
            for pattern in problem_patterns:
                match = re.search(pattern, text)
                if match:
                    variables["technical_problem"] = match.group(1).strip()
                    break

            # 提取技术方案
            if "技术方案" in text or "解决方案" in text or "发明内容" in text:
                # 查找技术方案部分
                for marker in ["技术方案", "解决方案", "发明内容"]:
                    if marker in text:
                        start = text.find(marker)
                        # 提取技术方案后的内容,直到遇到明确的结束标记
                        end_markers = ["##", "###", "\n\n技术效果", "\n\n有益效果"]
                        end = len(text)
                        for end_marker in end_markers:
                            pos = text.find(end_marker, start)
                            if pos != -1 and pos < end:
                                end = pos

                        solution_text = text[start:end].strip()
                        # 限制长度
                        variables["technical_solution"] = solution_text[:1000]
                        break

            # 提取技术效果
            effect_patterns = [
                r"技术效果[::]\s*([^。,\n]+)",
                r"有益效果[::]\s*([^。,\n]+)",
                r"达到\s*([^。,\n]+)\s*(的效果|目的)",
            ]
            for pattern in effect_patterns:
                match = re.search(pattern, text)
                if match:
                    variables["technical_effect"] = match.group(1).strip()
                    break

        elif domain == Domain.TRADEMARK:
            # 提取商标名称
            trademark_patterns = [
                r"商标[::]\s*([^。,\n]+)",
                r"品牌[::]\s*([^。,\n]+)",
                r"标识[::]\s*([^。,\n]+)",
            ]
            for pattern in trademark_patterns:
                match = re.search(pattern, text)
                if match:
                    variables["trademark_name"] = match.group(1).strip()
                    break

            # 提取商标类别
            category_match = re.search(r"第(\d+)类", text)
            if category_match:
                variables["trademark_category"] = category_match.group(1)

            # 提取商品/服务
            if "商品" in text or "服务" in text:
                goods_match = re.search(r"(商品|服务)[::]\s*([^。,\n]+)", text)
                if goods_match:
                    variables["goods_services"] = goods_match.group(2).strip()

        elif domain == Domain.LEGAL:
            # 提取案件类型
            case_type_patterns = [r"案件类型[::]\s*([^。,\n]+)", r"纠纷类型[::]\s*([^。,\n]+)"]
            for pattern in case_type_patterns:
                match = re.search(pattern, text)
                if match:
                    variables["case_type"] = match.group(1).strip()
                    break

            # 提取当事人
            party_match = re.search(r"(原告|申请人|上诉人)[::]\s*([^。,\n]+)", text)
            if party_match:
                variables["party_a"] = party_match.group(2).strip()

            party_match = re.search(r"(被告|被申请人|被上诉人)[::]\s*([^。,\n]+)", text)
            if party_match:
                variables["party_b"] = party_match.group(2).strip()

        # 通用:提取法律依据
        legal_basis_match = re.search(r"(法律依据|根据|依据)[::]\s*([^。,\n]+)", text)
        if legal_basis_match:
            variables["legal_basis"] = legal_basis_match.group(2).strip()

        return variables

    async def identify_scenario_with_llm(
        self, user_input: str, additional_context: Optional[Dict[str, Any]] = None
    ) -> ScenarioContext:
        """
        使用LLM辅助识别场景(当规则匹配置信度较低时)

        Args:
            user_input: 用户输入文本
            additional_context: 额外上下文信息

        Returns:
            ScenarioContext: 识别的场景上下文
        """
        try:
            # 尝试导入LLM管理器
            from core.llm.unified_llm_manager import UnifiedLLMManager

            llm_manager = UnifiedLLMManager()

            # 构建场景识别提示
            prompt = f"""请分析以下用户输入,识别其业务场景:

用户输入: {user_input}

请按以下格式输出:
1. 业务领域 (patent/trademark/legal/copyright/other)
2. 任务类型 (creativity_analysis/novelty_analysis/infringement/similarity/validity/drafting/search/other)
3. 业务阶段 (application/examination/opposition/litigation/other)
4. 置信度 (0.0-1.0)
5. 提取的关键变量 (JSON格式)

请直接输出JSON格式结果。"""

            # 调用LLM
            response = await llm_manager.generate(
                prompt=prompt,
                model_preference="fast",  # 使用快速模型
                max_tokens=500,
            )

            if response and response.get("text"):
                # 解析LLM响应
                result = self._parse_llm_response(response["text"], user_input)
                logger.info(f"✅ LLM辅助场景识别完成: {result.domain.value}/{result.task_type.value}")
                return result

        except Exception as e:
            logger.warning(f"⚠️ LLM辅助场景识别失败: {e}, 使用规则匹配")

        # 降级到规则匹配
        return self.identify_scenario(user_input, additional_context)

    def _parse_llm_response(self, llm_response: str, user_input: str) -> "ScenarioContext":
        """解析LLM响应并构建场景上下文"""
        import json

        try:
            # 尝试解析JSON
            # 移除可能的markdown代码块标记
            clean_response = llm_response.strip()
            if clean_response.startswith("```"):
                clean_response = re.sub(r"```\w*\n?", "", clean_response)
                clean_response = clean_response.rstrip("`").strip()

            parsed = json.loads(clean_response)

            # 构建场景上下文
            domain_str = parsed.get("业务领域", parsed.get("domain", "other"))
            task_type_str = parsed.get("任务类型", parsed.get("task_type", "other"))
            phase_str = parsed.get("业务阶段", parsed.get("phase", "other"))
            confidence = float(parsed.get("置信度", parsed.get("confidence", 0.5)))
            variables = parsed.get("提取的关键变量", parsed.get("variables", {}))

            # 转换为枚举
            domain = self._str_to_domain(domain_str)
            task_type = self._str_to_task_type(task_type_str)
            phase = self._str_to_phase(phase_str)

            return ScenarioContext(
                domain=domain,
                task_type=task_type,
                phase=phase,
                confidence=confidence,
                extracted_variables=variables,
                metadata={"source": "llm", "raw_response": llm_response[:200]},
            )

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"解析LLM响应失败: {e}")
            # 返回基于规则的结果
            return self.identify_scenario(user_input)

    def _str_to_domain(self, domain_str: str) -> Domain:
        """字符串转Domain枚举"""
        domain_map = {
            "patent": Domain.PATENT,
            "专利": Domain.PATENT,
            "trademark": Domain.TRADEMARK,
            "商标": Domain.TRADEMARK,
            "legal": Domain.LEGAL,
            "法律": Domain.LEGAL,
            "copyright": Domain.COPYRIGHT,
            "版权": Domain.COPYRIGHT,
            "著作权": Domain.COPYRIGHT,
        }
        return domain_map.get(domain_str.lower(), Domain.OTHER)

    def _str_to_task_type(self, task_type_str: str) -> TaskType:
        """字符串转TaskType枚举"""
        task_map = {
            "creativity_analysis": TaskType.CREATIVITY_ANALYSIS,
            "创造性分析": TaskType.CREATIVITY_ANALYSIS,
            "novelty_analysis": TaskType.NOVELTY_ANALYSIS,
            "新颖性分析": TaskType.NOVELTY_ANALYSIS,
            "infringement": TaskType.INFRINGEMENT,
            "侵权": TaskType.INFRINGEMENT,
            "similarity": TaskType.SIMILARITY,
            "相似性": TaskType.SIMILARITY,
            "validity": TaskType.VALIDITY,
            "无效": TaskType.VALIDITY,
            "drafting": TaskType.DRAFTING,
            "撰写": TaskType.DRAFTING,
            "search": TaskType.SEARCH,
            "检索": TaskType.SEARCH,
        }
        return task_map.get(task_type_str.lower(), TaskType.OTHER)

    def _str_to_phase(self, phase_str: str) -> Phase:
        """字符串转Phase枚举"""
        phase_map = {
            "application": Phase.APPLICATION,
            "申请": Phase.APPLICATION,
            "examination": Phase.EXAMINATION,
            "审查": Phase.EXAMINATION,
            "opposition": Phase.OPPOSITION,
            "异议": Phase.OPPOSITION,
            "litigation": Phase.LITIGATION,
            "诉讼": Phase.LITIGATION,
        }
        return phase_map.get(phase_str.lower(), Phase.OTHER)


# 便捷函数
def identify_scenario_from_input(
    user_input: str, additional_context: Optional[Dict[str, Any]] = None
) -> ScenarioContext:
    """
    便捷函数:从用户输入识别场景

    Args:
        user_input: 用户输入文本
        additional_context: 额外上下文信息

    Returns:
        ScenarioContext: 识别的场景上下文
    """
    identifier = ScenarioIdentifier()
    return identifier.identify_scenario(user_input, additional_context)
