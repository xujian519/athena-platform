#!/usr/bin/env python3
from __future__ import annotations
"""
增强场景识别器 - 提供更准确的场景识别和置信度评估
Enhanced Scenario Identifier - Improved accuracy and confidence scoring

版本: 1.1.0
创建时间: 2026-03-05
改进内容:
- 增加关键词匹配规则
- 添加短语匹配功能
- 改进置信度计算算法
- 添加组合匹配加分机制
- 增加上下文相关性评分
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

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
    NOVELTY_ANALYSIS = "novelity_analysis"
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


class EnhancedScenarioIdentifier:
    """
    增强场景识别器

    改进点:
    1. 更多的关键词匹配规则
    2. 短语匹配功能
    3. 改进的置信度计算算法
    4. 组合匹配加分机制
    5. 上下文相关性评分
    """

    # 扩展的关键词匹配规则
    KEYWORD_RULES = {
        Domain.PATENT: {
            TaskType.CREATIVITY_ANALYSIS: [
                "创造性",
                "创新性",
                "创新高度",
                "技术贡献",
                "突出的实质性特点",
                "显著的进步",
                "显而易见",
                "非显而易见",
                "技术启示",
                "现有技术差异",
                "用途发明",
                "反向教导",
                "预料不到",
                "事后诸葛亮",
                "技术偏见",
                "复审请求",
                "驳回复审",
                "长期技术难题",
            ],
            TaskType.NOVELTY_ANALYSIS: [
                "新颖性",
                "现有技术",
                "公开",
                "在先技术",
                "不属于现有技术",
                "抵触申请",
                "出版物公开",
                "使用公开",
                "销售公开",
                "现有技术抗辩",
            ],
            TaskType.INFRINGEMENT: [
                "侵权",
                "落入保护范围",
                "等同",
                "相同",
                "保护范围",
                "权利要求解释",
                "全面覆盖原则",
                "等同侵权",
                "字面侵权",
            ],
            TaskType.VALIDITY: [
                "无效",
                "无效宣告",
                "不符合专利法",
                "不具备",
                "不授予",
                "专利无效",
                "无效理由",
                "证据不充分",
                "公开不充分",
            ],
            TaskType.DRAFTING: [
                "撰写",
                "写",
                "起草",
                "生成",
                "申请文件",
                "权利要求",
                "说明书",
                "摘要",
                "附图",
            ],
            TaskType.SEARCH: [
                "检索",
                "查新",
                "现有技术检索",
                "对比文件",
                "检索报告",
                "专利数据库",
                "检索策略",
            ],
        },
        Domain.TRADEMARK: {
            TaskType.SIMILARITY: [
                "相似",
                "近似",
                "混淆",
                "容易误认",
                "视觉近似",
                "读音近似",
                "含义近似",
                "商标近似",
            ],
            TaskType.INFRINGEMENT: [
                "侵权",
                "擅自使用",
                "相同或相似",
                "容易导致混淆",
                "商标侵权",
            ],
            TaskType.VALIDITY: [
                "无效",
                "撤销",
                "显著性",
                "缺乏显著性",
                "商标无效",
            ],
            TaskType.DRAFTING: [
                "申请",
                "注册",
                "商标申请",
                "图样",
                "商标注册",
            ],
        },
        Domain.LEGAL: {
            TaskType.INFRINGEMENT: [
                "侵权",
                "损害赔偿",
                "停止侵害",
                "法律责任",
            ],
            TaskType.VALIDITY: [
                "效力",
                "无效",
                "可撤销",
            ],
            TaskType.DRAFTING: [
                "合同",
                "起草",
                "法律文书",
                "协议",
            ],
        },
    }

    # 短语匹配规则（更高权重的匹配）
    PHRASE_RULES = {
        Domain.PATENT: {
            TaskType.CREATIVITY_ANALYSIS: [
                "是否具备创造性",
                "创造性的高度",
                "技术方案是否具有创新性",
                "是否存在突出的实质性特点",
            ],
            TaskType.NOVELTY_ANALYSIS: [
                "是否丧失新颖性",
                "新颖性判断",
                "是否属于现有技术",
                "是否存在抵触申请",
            ],
            TaskType.INFRINGEMENT: [
                "是否构成侵权",
                "是否落入保护范围",
                "是否构成等同侵权",
            ],
            TaskType.VALIDITY: [
                "专利是否有效",
                "请求宣告无效",
                "无效宣告请求",
            ],
            TaskType.DRAFTING: [
                "撰写专利申请",
                "起草权利要求书",
                "准备申请文件",
            ],
            TaskType.SEARCH: [
                "进行专利检索",
                "现有技术检索",
                "检索对比文件",
            ],
        },
    }

    # 阶段识别规则（扩展）
    PHASE_KEYWORDS = {
        Phase.APPLICATION: [
            "申请",
            "提交",
            "申请文件",
            "立案",
            "专利申请",
            "商标申请",
            "版权登记",
        ],
        Phase.EXAMINATION: [
            "审查",
            "审查意见",
            "驳回",
            "补正",
            "答复",
            "实质审查",
            "初步审查",
            "审查答复",
        ],
        Phase.OPPOSITION: [
            "异议",
            "无效宣告",
            "复审",
            "异议程序",
            "无效程序",
            "复审程序",
        ],
        Phase.LITIGATION: [
            "诉讼",
            "起诉",
            "判决",
            "法院",
            "法庭",
            "裁决",
            "专利诉讼",
            "商标诉讼",
        ],
    }

    # 扩展的领域关键词
    DOMAIN_KEYWORDS = {
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
            "专利权",
            "专利申请",
            "授权公告",
            "专利号",
            "申请号",
        ],
        Domain.TRADEMARK: [
            "商标",
            "品牌",
            "logo",
            "标识",
            "图形",
            "商号",
            "服务商标",
            "商标注册",
            "商标权",
            "注册商标",
        ],
        Domain.LEGAL: [
            "诉讼",
            "法院",
            "判决",
            "法律",
            "法规",
            "合同",
            "协议",
            "法律责任",
            "法律纠纷",
        ],
        Domain.COPYRIGHT: [
            "版权",
            "著作权",
            "作品",
            "署名",
            "复制权",
            "版权登记",
        ],
    }

    def __init__(self, enable_llm_fallback: bool = False):
        """
        初始化增强场景识别器

        Args:
            enable_llm_fallback: 是否启用LLM回退(当规则匹配失败时)
        """
        self.enable_llm_fallback = enable_llm_fallback
        self._init_weights()

    def _init_weights(self):
        """初始化权重配置"""
        # 不同匹配类型的权重
        self.weights = {
            "phrase_match": 0.4,      # 短语匹配权重
            "keyword_match": 0.3,     # 关键词匹配权重
            "domain_match": 0.2,       # 领域匹配权重
            "context_boost": 0.1,     # 上下文加分
        }

    def identify_scenario(
        self, user_input: str, additional_context: dict[str, Any] | None = None
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
        domain, domain_confidence = self._identify_domain_enhanced(user_input)
        result.domain = domain
        logger.info(f"  领域: {domain.value} (置信度: {domain_confidence:.2f})")

        # 2. 识别任务类型
        task_type = TaskType.OTHER
        task_confidence = 0.0
        if domain in self.KEYWORD_RULES:
            task_type, task_confidence = self._identify_task_type_enhanced(user_input, domain)
            result.task_type = task_type
            logger.info(f"  任务: {task_type.value} (置信度: {task_confidence:.2f})")
        else:
            result.task_type = TaskType.OTHER

        # 3. 识别阶段
        phase, phase_confidence = self._identify_phase_enhanced(user_input)
        result.phase = phase
        logger.info(f"  阶段: {phase.value} (置信度: {phase_confidence:.2f})")

        # 4. 计算总体置信度（改进的算法）
        result.confidence = self._calculate_overall_confidence(
            domain_confidence, task_confidence, phase_confidence, domain, task_type, phase
        )

        # 5. 提取变量
        result.extracted_variables = self._extract_variables(user_input, domain, task_type)
        logger.info(f"  提取变量: {list(result.extracted_variables.keys())}")

        # 6. 元数据
        result.metadata = {
            "input_length": len(user_input),
            "additional_context": additional_context or {},
            "timestamp": None,
            "match_details": self._get_match_details(user_input, domain, task_type, phase),
        }

        logger.info(f"✅ 场景识别完成,总体置信度: {result.confidence:.2f}")

        return result

    def _identify_domain_enhanced(self, text: str) -> tuple[Domain, float]:
        """增强的领域识别"""
        max_score = 0
        identified_domain = Domain.OTHER

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            # 基础关键词匹配
            keyword_score = sum(1 for kw in keywords if kw in text)

            # 短语匹配（额外加分）
            phrase_bonus = self._calculate_phrase_bonus(text, domain)

            # 组合分数
            total_score = keyword_score + (phrase_bonus * 2)

            if total_score > max_score:
                max_score = total_score
                identified_domain = domain

        # 改进的置信度计算
        confidence = min(max_score * 0.12, 0.95)

        return identified_domain, confidence

    def _identify_task_type_enhanced(self, text: str, domain: Domain) -> tuple[TaskType, float]:
        """增强的任务类型识别"""
        if domain not in self.KEYWORD_RULES:
            return TaskType.OTHER, 0.0

        max_score = 0
        identified_task = TaskType.OTHER

        task_keywords = self.KEYWORD_RULES[domain]
        task_phrases = self.PHRASE_RULES.get(domain, {})

        for task_type in TaskType:
            if task_type == TaskType.OTHER:
                continue

            # 关键词匹配
            keywords = task_keywords.get(task_type, [])
            keyword_score = sum(1 for kw in keywords if kw in text)

            # 短语匹配
            phrases = task_phrases.get(task_type, [])
            phrase_score = sum(1 for phrase in phrases if phrase in text)

            # 组合分数
            total_score = keyword_score + (phrase_score * 3)  # 短语匹配权重更高

            if total_score > max_score:
                max_score = total_score
                identified_task = task_type

        # 改进的置信度计算
        confidence = min(max_score * 0.18, 0.95)

        return identified_task, confidence

    def _identify_phase_enhanced(self, text: str) -> tuple[Phase, float]:
        """增强的阶段识别"""
        max_score = 0
        identified_phase = Phase.OTHER

        for phase, keywords in self.PHASE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > max_score:
                max_score = score
                identified_phase = phase

        # 改进的置信度计算
        confidence = min(max_score * 0.22, 0.95)

        return identified_phase, confidence

    def _calculate_overall_confidence(
        self,
        domain_conf: float,
        task_conf: float,
        phase_conf: float,
        domain: Domain,
        task_type: TaskType,
        phase: Phase,
    ) -> float:
        """
        计算总体置信度（改进的算法）

        考虑因素:
        1. 各维度置信度的加权平均
        2. 匹配一致性加分
        3. 领域-任务组合合理性
        """
        # 基础加权平均
        base_confidence = (
            domain_conf * 0.4 +
            task_conf * 0.4 +
            phase_conf * 0.2
        )

        # 一致性加分（如果所有识别都有较高的置信度）
        consistency_bonus = 0
        if domain_conf > 0.3 and task_conf > 0.3 and phase_conf > 0.3:
            consistency_bonus = 0.1
        elif domain_conf > 0.2 and task_conf > 0.2:
            consistency_bonus = 0.05

        # 组合合理性加分
        combination_bonus = 0
        if self._is_valid_combination(domain, task_type, phase):
            combination_bonus = 0.05

        # 最终置信度
        final_confidence = min(base_confidence + consistency_bonus + combination_bonus, 0.95)

        return final_confidence

    def _is_valid_combination(self, domain: Domain, task_type: TaskType, phase: Phase) -> bool:
        """检查领域-任务-阶段组合是否合理"""
        # 定义合理的组合
        valid_combinations = {
            (Domain.PATENT, TaskType.DRAFTING, Phase.APPLICATION),
            (Domain.PATENT, TaskType.SEARCH, Phase.APPLICATION),
            (Domain.PATENT, TaskType.CREATIVITY_ANALYSIS, Phase.EXAMINATION),
            (Domain.PATENT, TaskType.NOVELTY_ANALYSIS, Phase.EXAMINATION),
            (Domain.PATENT, TaskType.INFRINGEMENT, Phase.LITIGATION),
            (Domain.PATENT, TaskType.VALIDITY, Phase.OPPOSITION),
            (Domain.TRADEMARK, TaskType.DRAFTING, Phase.APPLICATION),
            (Domain.TRADEMARK, TaskType.SIMILARITY, Phase.EXAMINATION),
            (Domain.TRADEMARK, TaskType.INFRINGEMENT, Phase.LITIGATION),
        }

        # 灵活匹配（部分匹配也可以）
        for valid_domain, valid_task, valid_phase in valid_combinations:
            if (domain == valid_domain and
                (task_type == valid_task or task_type == TaskType.OTHER) and
                (phase == valid_phase or phase == Phase.OTHER)):
                return True

        return False

    def _calculate_phrase_bonus(self, text: str, domain: Domain) -> float:
        """计算短语匹配加分"""
        if domain not in self.PHRASE_RULES:
            return 0.0

        phrases = self.PHRASE_RULES[domain]
        # 将所有短语合并计算
        all_phrases = []
        for task_phrases in phrases.values():
            all_phrases.extend(task_phrases)

        phrase_matches = sum(1 for phrase in all_phrases if phrase in text)

        return phrase_matches * 0.5  # 每个短语匹配加0.5分

    def _extract_variables(self, text: str, domain: Domain, task_type: TaskType) -> dict[str, Any]:
        """从文本中提取变量（保持原有逻辑）"""
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
                for marker in ["技术方案", "解决方案", "发明内容"]:
                    if marker in text:
                        start = text.find(marker)
                        end_markers = ["##", "###", "\n\n技术效果", "\n\n有益效果"]
                        end = len(text)
                        for end_marker in end_markers:
                            pos = text.find(end_marker, start)
                            if pos != -1 and pos < end:
                                end = pos

                        solution_text = text[start:end].strip()
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
            case_type_patterns = [
                r"案件类型[::]\s*([^。,\n]+)",
                r"纠纷类型[::]\s*([^。,\n]+)",
            ]
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

    def _get_match_details(
        self, text: str, domain: Domain, task_type: TaskType, phase: Phase
    ) -> dict[str, Any]:
        """获取匹配详情（用于调试和改进）"""
        details = {
            "domain": domain.value,
            "task_type": task_type.value,
            "phase": phase.value,
            "keyword_matches": [],
            "phrase_matches": [],
        }

        # 记录关键词匹配
        if domain in self.DOMAIN_KEYWORDS:
            for keyword in self.DOMAIN_KEYWORDS[domain]:
                if keyword in text:
                    details["keyword_matches"].append(keyword)

        # 记录短语匹配
        if domain in self.PHRASE_RULES:
            for _task_type_key, phrases in self.PHRASE_RULES[domain].items():
                for phrase in phrases:
                    if phrase in text:
                        details["phrase_matches"].append(phrase)

        return details

    async def identify_scenario_with_llm(
        self, user_input: str, additional_context: dict[str, Any] | None = None
    ) -> ScenarioContext:
        """
        使用LLM辅助识别场景(当规则匹配置信度较低时)

        Args:
            user_input: 用户输入文本
            additional_context: 额外上下文信息

        Returns:
            ScenarioContext: 识别的场景上下文
        """
        # 首先尝试规则识别
        result = self.identify_scenario(user_input, additional_context)

        # 如果置信度较低，使用LLM增强
        if result.confidence < 0.3 and self.enable_llm_fallback:
            logger.info("⚠️  规则匹配置信度较低，尝试LLM辅助识别")
            # TODO: 实现LLM辅助的场景识别
            # 可以使用平台现有的LLM接口
            logger.warning("LLM辅助场景识别功能尚未实现")
            return result
        else:
            return result


# 便捷函数
def identify_scenario_from_input(
    user_input: str, additional_context: dict[str, Any] | None = None
) -> ScenarioContext:
    """
    便捷函数:从用户输入识别场景（使用增强版本）

    Args:
        user_input: 用户输入文本
        additional_context: 额外上下文信息

    Returns:
        ScenarioContext: 识别的场景上下文
    """
    identifier = EnhancedScenarioIdentifier()
    return identifier.identify_scenario(user_input, additional_context)
