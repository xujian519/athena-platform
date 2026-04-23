from __future__ import annotations

"""
知识激活诊断系统 v1.0

基于论文"Missing vs. Unused Knowledge in Large Language Models"(2025)

核心功能:
1. 错误类型诊断 - 区分知识缺失与知识未激活
2. 澄清问题生成 - 生成针对性的澄清问题
3. 自答激活机制 - 通过自问自答激活潜在知识
4. 优化策略推荐 - 根据错误类型推荐改进策略

关键发现:
- 许多LLM错误不是知识缺失，而是知识未被激活
- 通过澄清问题可以激活潜在知识
- 自答机制显著提高回答质量

使用模型: deepseek-reasoner (复杂诊断), qwen3.5 (快速分析)

作者: Athena平台
版本: v1.0
日期: 2026-03-23
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型"""
    KNOWLEDGE_MISSING = "knowledge_missing"      # 知识缺失 - LLM确实不知道
    KNOWLEDGE_UNUSED = "knowledge_unused"        # 知识未激活 - LLM知道但未使用
    KNOWLEDGE_MISAPPLIED = "knowledge_misapplied"  # 知识误用 - LLM使用错误
    REASONING_ERROR = "reasoning_error"          # 推理错误 - 逻辑问题
    AMBIGUITY = "ambiguity"                      # 歧义 - 问题不清晰
    UNKNOWN = "unknown"                          # 未知类型


class DiagnosisSeverity(Enum):
    """诊断严重程度"""
    CRITICAL = "critical"    # 严重错误，必须修复
    HIGH = "high"           # 高优先级
    MEDIUM = "medium"       # 中等优先级
    LOW = "low"             # 低优先级
    INFO = "info"           # 仅提示


class ActivationStrategy(Enum):
    """激活策略"""
    CLARIFICATION = "clarification"      # 澄清问题
    SELF_ANSWERING = "self_answering"    # 自答激活
    DECOMPOSITION = "decomposition"      # 问题分解
    EXAMPLE = "example"                  # 示例引导
    REPHRASING = "rephrasing"            # 重新表述
    CHAIN_OF_THOUGHT = "chain_of_thought"  # 思维链


@dataclass
class ClarificationQuestion:
    """澄清问题"""
    question_id: str              # 问题ID
    question: str                 # 问题内容
    purpose: str                  # 问题目的
    expected_info: str            # 期望获取的信息
    priority: int = 1             # 优先级 (1-5, 1最高)

    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "question": self.question,
            "purpose": self.purpose,
            "expected_info": self.expected_info,
            "priority": self.priority
        }


@dataclass
class SelfAnsweringPrompt:
    """自答提示"""
    prompt_id: str                # 提示ID
    original_question: str        # 原始问题
    clarification: str            # 澄清说明
    self_question: str            # 自问问题
    expected_self_answer: str = ""  # 期望的自答内容

    def to_dict(self) -> dict:
        return {
            "prompt_id": self.prompt_id,
            "original_question": self.original_question,
            "clarification": self.clarification,
            "self_question": self.self_question
        }


@dataclass
class OptimizationRecommendation:
    """优化建议"""
    recommendation_id: str        # 建议ID
    strategy: ActivationStrategy  # 激活策略
    description: str              # 建议描述
    implementation: str           # 实施方法
    expected_improvement: str     # 预期改进
    priority: DiagnosisSeverity   # 优先级

    def to_dict(self) -> dict:
        return {
            "recommendation_id": self.recommendation_id,
            "strategy": self.strategy.value,
            "description": self.description,
            "implementation": self.implementation,
            "expected_improvement": self.expected_improvement,
            "priority": self.priority.value
        }


@dataclass
class DiagnosisResult:
    """诊断结果"""
    diagnosis_id: str                     # 诊断ID

    # 错误分析
    error_type: ErrorType                 # 错误类型
    severity: DiagnosisSeverity           # 严重程度
    error_description: str                # 错误描述

    # 诊断依据
    evidence: list[str]                   # 诊断依据
    confidence: float = 0.8               # 置信度

    # 澄清问题
    clarification_questions: list[ClarificationQuestion] = field(default_factory=list)

    # 自答激活
    self_answering_prompts: list[SelfAnsweringPrompt] = field(default_factory=list)

    # 优化建议
    recommendations: list[OptimizationRecommendation] = field(default_factory=list)

    # 元数据
    processing_time_ms: float = 0.0
    model_used: str = ""

    def to_dict(self) -> dict:
        return {
            "diagnosis_id": self.diagnosis_id,
            "error_type": self.error_type.value,
            "severity": self.severity.value,
            "error_description": self.error_description,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "clarification_questions": [q.to_dict() for q in self.clarification_questions],
            "self_answering_prompts": [p.to_dict() for p in self.self_answering_prompts],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "processing_time_ms": self.processing_time_ms,
            "model_used": self.model_used
        }


@dataclass
class ActivationSession:
    """激活会话"""
    session_id: str                       # 会话ID
    original_query: str                   # 原始查询
    original_response: str                # 原始响应

    # 诊断结果
    diagnosis: DiagnosisResult | None = None

    # 激活后的改进
    improved_response: str = ""
    improvement_score: float = 0.0

    # 激活历史
    activation_history: list[dict] = field(default_factory=list)

    # 元数据
    created_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "original_query": self.original_query,
            "original_response": self.original_response,
            "diagnosis": self.diagnosis.to_dict() if self.diagnosis else None,
            "improved_response": self.improved_response,
            "improvement_score": self.improvement_score,
            "activation_history": self.activation_history
        }


class KnowledgeActivationDiagnoser:
    """
    知识激活诊断系统

    基于论文发现，区分知识缺失和知识未激活两种错误类型，
    并提供针对性的激活策略。
    """

    # 模型配置
    MODEL_CONFIG = {
        "diagnosis": {
            "model": "deepseek-reasoner",
            "provider": "deepseek",
            "temperature": 0.2,
            "max_tokens": 2000
        },
        "clarification": {
            "model": "qwen3.5",
            "provider": "ollama",
            "temperature": 0.3,
            "max_tokens": 1500
        },
        "activation": {
            "model": "deepseek-reasoner",
            "provider": "deepseek",
            "temperature": 0.3,
            "max_tokens": 3000
        }
    }

    # 错误类型判断规则
    ERROR_INDICATORS = {
        ErrorType.KNOWLEDGE_MISSING: [
            "我不知道", "无法确定", "没有相关信息",
            "超出了我的知识范围", "我没有关于"
        ],
        ErrorType.KNOWLEDGE_UNUSED: [
            "可能", "也许", "我认为", "应该是",
            "不确定", "可能是"
        ],
        ErrorType.KNOWLEDGE_MISAPPLIED: [
            "但是", "然而", "错误地", "不正确"
        ],
        ErrorType.AMBIGUITY: [
            "你是指", "需要更多信息", "取决于"
        ]
    }

    def __init__(self, llm_manager=None):
        """
        初始化诊断器

        Args:
            llm_manager: LLM管理器实例
        """
        self.llm_manager = llm_manager
        self._init_prompts()

    def _init_prompts(self):
        """初始化提示词模板"""
        self.diagnosis_prompt = """你是一位AI错误诊断专家，精通分析大语言模型的回答错误。

请分析以下问题和回答，诊断错误的根本原因。

【问题】
{query}

【回答】
{response}

【正确答案】(如果有)
{ground_truth}

【诊断要求】
1. 判断错误类型:
   - knowledge_missing: LLM确实不知道这个知识
   - knowledge_unused: LLM知道但未正确使用
   - knowledge_misapplied: LLM使用了错误的知识
   - reasoning_error: 推理逻辑错误
   - ambiguity: 问题本身有歧义

2. 提供诊断依据

3. 建议澄清问题（2-3个）

4. 建议激活策略

【输出格式】(JSON)
```json
{{
  "error_type": "knowledge_missing/knowledge_unused/...",
  "severity": "critical/high/medium/low",
  "error_description": "错误描述",
  "evidence": ["依据1", "依据2"],
  "clarification_questions": [
    {{
      "question": "澄清问题",
      "purpose": "问题目的",
      "expected_info": "期望信息"
    }}
  ],
  "activation_strategy": "clarification/self_answering/decomposition/...",
  "recommendations": [
    {{
      "strategy": "策略类型",
      "description": "建议描述",
      "implementation": "实施方法"
    }}
  ]
}}
```

只输出JSON，不要其他内容。
"""

        self.clarification_prompt = """请为以下问题生成澄清问题。

【原始问题】
{query}

【原始回答】
{response}

【诊断结果】
{diagnosis}

【生成要求】
1. 生成2-3个澄清问题
2. 每个问题应该帮助消除歧义或激活相关知识
3. 问题应该具体且易于回答

【输出格式】(JSON)
```json
{{
  "questions": [
    {{
      "id": "Q1",
      "question": "问题内容",
      "purpose": "问题目的",
      "expected_info": "期望获取的信息",
      "priority": 1
    }}
  ]
}}
```
"""

        self.self_answering_prompt = """请生成自问自答提示来激活相关知识。

【原始问题】
{query}

【识别的潜在知识】
{potential_knowledge}

【生成要求】
1. 将原始问题转化为自问形式
2. 添加相关的背景知识激活
3. 引导模型回忆相关知识

【输出格式】
自问: [转化的自问问题]
激活提示: [相关的知识提示]
预期自答: [预期的回答方向]
"""

    # ==================== 主要公共接口 ====================

    async def diagnose(
        self,
        query: str,
        response: str,
        ground_truth: str | None = None
    ) -> DiagnosisResult:
        """
        诊断回答错误

        Args:
            query: 原始问题
            response: 模型回答
            ground_truth: 正确答案（可选）

        Returns:
            DiagnosisResult: 诊断结果
        """
        start_time = time.time()
        diagnosis_id = f"diag_{int(time.time() * 1000)}"

        logger.info(f"开始诊断: {diagnosis_id}")

        # 1. 快速错误类型判断（基于规则）
        initial_error_type = self._quick_error_classification(response)

        # 2. LLM深度诊断
        if self.llm_manager:
            diagnosis_result = await self._llm_diagnose(
                query, response, ground_truth, diagnosis_id
            )
        else:
            diagnosis_result = self._heuristic_diagnose(
                query, response, ground_truth, diagnosis_id, initial_error_type
            )

        # 3. 计算处理时间
        diagnosis_result.processing_time_ms = (time.time() - start_time) * 1000

        return diagnosis_result

    async def generate_clarification_questions(
        self,
        query: str,
        response: str,
        diagnosis: DiagnosisResult | None = None
    ) -> list[ClarificationQuestion]:
        """
        生成澄清问题

        Args:
            query: 原始问题
            response: 模型回答
            diagnosis: 诊断结果（可选）

        Returns:
            List[ClarificationQuestion]: 澄清问题列表
        """
        if self.llm_manager is None:
            return self._heuristic_clarification_questions(query, response)

        try:
            diagnosis_text = ""
            if diagnosis:
                diagnosis_text = f"错误类型: {diagnosis.error_type.value}, 描述: {diagnosis.error_description}"

            prompt = self.clarification_prompt.format(
                query=query,
                response=response[:1000],
                diagnosis=diagnosis_text
            )

            response_result = await self.llm_manager.generate(
                message=prompt,
                task_type="clarification_generation",
                model_id=self.MODEL_CONFIG["clarification"]["model"],
                temperature=self.MODEL_CONFIG["clarification"]["temperature"]
            )

            response_text = response_result.content if hasattr(response_result, 'content') else str(response_result)
            result = self._parse_json_response(response_text)

            if result and "questions" in result:
                return [
                    ClarificationQuestion(
                        question_id=q.get("id", f"Q{i}"),
                        question=q.get("question", ""),
                        purpose=q.get("purpose", ""),
                        expected_info=q.get("expected_info", ""),
                        priority=q.get("priority", 1)
                    )
                    for i, q in enumerate(result["questions"])
                ]

        except Exception as e:
            logger.warning(f"生成澄清问题失败: {e}")

        return self._heuristic_clarification_questions(query, response)

    async def activate_knowledge(
        self,
        query: str,
        response: str,
        diagnosis: DiagnosisResult
    ) -> str:
        """
        激活知识，生成改进回答

        Args:
            query: 原始问题
            response: 原始回答
            diagnosis: 诊断结果

        Returns:
            str: 激活后的改进回答
        """
        if self.llm_manager is None:
            return self._heuristic_activation(query, response, diagnosis)

        try:
            # 根据错误类型选择激活策略
            strategy = self._select_activation_strategy(diagnosis)

            # 构建激活提示
            activation_prompt = self._build_activation_prompt(
                query, response, diagnosis, strategy
            )

            response_result = await self.llm_manager.generate(
                message=activation_prompt,
                task_type="knowledge_activation",
                model_id=self.MODEL_CONFIG["activation"]["model"],
                temperature=self.MODEL_CONFIG["activation"]["temperature"]
            )

            return response_result.content if hasattr(response_result, 'content') else str(response_result)

        except Exception as e:
            logger.warning(f"知识激活失败: {e}")
            return self._heuristic_activation(query, response, diagnosis)

    async def create_activation_session(
        self,
        query: str,
        response: str,
        ground_truth: str | None = None
    ) -> ActivationSession:
        """
        创建完整的激活会话

        Args:
            query: 原始问题
            response: 原始回答
            ground_truth: 正确答案

        Returns:
            ActivationSession: 激活会话
        """
        import datetime

        session_id = f"session_{int(time.time() * 1000)}"

        session = ActivationSession(
            session_id=session_id,
            original_query=query,
            original_response=response,
            created_at=datetime.datetime.now().isoformat()
        )

        # 1. 诊断
        diagnosis = await self.diagnose(query, response, ground_truth)
        session.diagnosis = diagnosis

        # 2. 生成澄清问题
        questions = await self.generate_clarification_questions(
            query, response, diagnosis
        )
        diagnosis.clarification_questions = questions

        # 3. 知识激活
        improved_response = await self.activate_knowledge(
            query, response, diagnosis
        )
        session.improved_response = improved_response

        # 4. 计算改进分数
        session.improvement_score = self._calculate_improvement(
            response, improved_response, ground_truth
        )

        session.completed_at = datetime.datetime.now().isoformat()

        return session

    # ==================== 私有方法 ====================

    def _quick_error_classification(self, response: str) -> ErrorType:
        """快速错误类型分类（基于规则）"""
        response_lower = response.lower()

        for error_type, indicators in self.ERROR_INDICATORS.items():
            for indicator in indicators:
                if indicator in response_lower:
                    return error_type

        return ErrorType.UNKNOWN

    async def _llm_diagnose(
        self,
        query: str,
        response: str,
        ground_truth: str | None,
        diagnosis_id: str
    ) -> DiagnosisResult:
        """LLM深度诊断"""
        try:
            prompt = self.diagnosis_prompt.format(
                query=query[:1000],
                response=response[:1000],
                ground_truth=ground_truth[:500] if ground_truth else "未提供"
            )

            response_result = await self.llm_manager.generate(
                message=prompt,
                task_type="error_diagnosis",
                model_id=self.MODEL_CONFIG["diagnosis"]["model"],
                temperature=self.MODEL_CONFIG["diagnosis"]["temperature"]
            )

            response_text = response_result.content if hasattr(response_result, 'content') else str(response_result)
            result = self._parse_json_response(response_text)

            if result:
                return self._build_diagnosis_result(result, diagnosis_id)

        except Exception as e:
            logger.warning(f"LLM诊断失败: {e}")

        return self._heuristic_diagnose(query, response, ground_truth, diagnosis_id, ErrorType.UNKNOWN)

    def _heuristic_diagnose(
        self,
        query: str,
        response: str,
        ground_truth: str | None,
        diagnosis_id: str,
        error_type: ErrorType
    ) -> DiagnosisResult:
        """启发式诊断"""
        # 基于响应长度和内容判断严重程度
        severity = DiagnosisSeverity.MEDIUM
        if len(response) < 50:
            severity = DiagnosisSeverity.HIGH
        elif "我不知道" in response or "无法" in response:
            severity = DiagnosisSeverity.CRITICAL

        # 生成基本的澄清问题
        questions = self._heuristic_clarification_questions(query, response)

        # 生成优化建议
        recommendations = self._generate_recommendations(error_type, severity)

        return DiagnosisResult(
            diagnosis_id=diagnosis_id,
            error_type=error_type,
            severity=severity,
            error_description=f"检测到{error_type.value}类型的错误",
            evidence=["基于启发式规则判断"],
            confidence=0.6,
            clarification_questions=questions,
            recommendations=recommendations,
            model_used="heuristic"
        )

    def _build_diagnosis_result(self, result: dict, diagnosis_id: str) -> DiagnosisResult:
        """构建诊断结果"""
        try:
            error_type = ErrorType(result.get("error_type", "unknown"))
        except ValueError:
            error_type = ErrorType.UNKNOWN

        try:
            severity = DiagnosisSeverity(result.get("severity", "medium"))
        except ValueError:
            severity = DiagnosisSeverity.MEDIUM

        questions = [
            ClarificationQuestion(
                question_id=f"Q{i}",
                question=q.get("question", ""),
                purpose=q.get("purpose", ""),
                expected_info=q.get("expected_info", "")
            )
            for i, q in enumerate(result.get("clarification_questions", []))
        ]

        recommendations = [
            OptimizationRecommendation(
                recommendation_id=f"R{i}",
                strategy=ActivationStrategy(
                    r.get("strategy", "clarification")
                ) if r.get("strategy") in [s.value for s in ActivationStrategy] else ActivationStrategy.CLARIFICATION,
                description=r.get("description", ""),
                implementation=r.get("implementation", ""),
                expected_improvement="提高回答质量",
                priority=severity
            )
            for i, r in enumerate(result.get("recommendations", []))
        ]

        return DiagnosisResult(
            diagnosis_id=diagnosis_id,
            error_type=error_type,
            severity=severity,
            error_description=result.get("error_description", ""),
            evidence=result.get("evidence", []),
            confidence=0.85,
            clarification_questions=questions,
            recommendations=recommendations,
            model_used=self.MODEL_CONFIG["diagnosis"]["model"]
        )

    def _heuristic_clarification_questions(
        self,
        query: str,
        response: str
    ) -> list[ClarificationQuestion]:
        """启发式生成澄清问题"""
        questions = []

        # 基于问题类型生成通用澄清问题
        if "专利" in query:
            questions.append(ClarificationQuestion(
                question_id="Q1",
                question="您是指发明专利、实用新型还是外观设计专利？",
                purpose="确定专利类型",
                expected_info="专利类型信息",
                priority=1
            ))

        if "权利要求" in query:
            questions.append(ClarificationQuestion(
                question_id="Q2",
                question="您关注的是独立权利要求还是从属权利要求？",
                purpose="确定权利要求类型",
                expected_info="权利要求类型",
                priority=2
            ))

        # 通用澄清问题
        questions.append(ClarificationQuestion(
            question_id="Q3",
            question="能否提供更多上下文或具体场景？",
            purpose="获取更多上下文",
            expected_info="背景信息",
            priority=3
        ))

        return questions

    def _select_activation_strategy(self, diagnosis: DiagnosisResult) -> ActivationStrategy:
        """选择激活策略"""
        strategy_mapping = {
            ErrorType.KNOWLEDGE_MISSING: ActivationStrategy.DECOMPOSITION,
            ErrorType.KNOWLEDGE_UNUSED: ActivationStrategy.CLARIFICATION,
            ErrorType.KNOWLEDGE_MISAPPLIED: ActivationStrategy.EXAMPLE,
            ErrorType.REASONING_ERROR: ActivationStrategy.CHAIN_OF_THOUGHT,
            ErrorType.AMBIGUITY: ActivationStrategy.REPHRASING
        }
        return strategy_mapping.get(diagnosis.error_type, ActivationStrategy.CLARIFICATION)

    def _build_activation_prompt(
        self,
        query: str,
        response: str,
        diagnosis: DiagnosisResult,
        strategy: ActivationStrategy
    ) -> str:
        """构建激活提示"""
        strategy_descriptions = {
            ActivationStrategy.CLARIFICATION: "首先回答澄清问题，然后重新回答原问题",
            ActivationStrategy.SELF_ANSWERING: "自问自答，先思考相关知识再回答",
            ActivationStrategy.DECOMPOSITION: "将问题分解为子问题逐一回答",
            ActivationStrategy.EXAMPLE: "参考相似案例，然后回答问题",
            ActivationStrategy.REPHRASING: "用不同方式重新表述问题后回答",
            ActivationStrategy.CHAIN_OF_THOUGHT: "使用思维链逐步推理"
        }

        return f"""请使用{strategy_descriptions.get(strategy, "澄清问题")}策略改进以下回答。

【原始问题】
{query}

【原始回答】
{response}

【诊断结果】
错误类型: {diagnosis.error_type.value}
描述: {diagnosis.error_description}

【改进要求】
1. 应用{strategy.value}策略
2. 提供更准确、完整的回答
3. 说明改进的关键点

请直接输出改进后的回答。
"""

    def _heuristic_activation(
        self,
        query: str,
        response: str,
        diagnosis: DiagnosisResult
    ) -> str:
        """启发式知识激活"""
        # 简单的改进策略
        improvements = []

        if diagnosis.error_type == ErrorType.KNOWLEDGE_UNUSED:
            improvements.append("让我重新思考这个问题...")
            improvements.append("考虑到更多因素，")
        elif diagnosis.error_type == ErrorType.AMBIGUITY:
            improvements.append("让我先澄清一下问题的含义。")

        improved = " ".join(improvements) + " " + response
        return improved

    def _generate_recommendations(
        self,
        error_type: ErrorType,
        severity: DiagnosisSeverity
    ) -> list[OptimizationRecommendation]:
        """生成优化建议"""
        recommendations = []

        if error_type == ErrorType.KNOWLEDGE_MISSING:
            recommendations.append(OptimizationRecommendation(
                recommendation_id="R1",
                strategy=ActivationStrategy.DECOMPOSITION,
                description="将复杂问题分解为更简单的子问题",
                implementation="逐步提问，先问基础概念再问具体问题",
                expected_improvement="激活相关知识",
                priority=severity
            ))

        if error_type == ErrorType.KNOWLEDGE_UNUSED:
            recommendations.append(OptimizationRecommendation(
                recommendation_id="R2",
                strategy=ActivationStrategy.CLARIFICATION,
                description="添加澄清问题以激活潜在知识",
                implementation="在回答前先问澄清问题",
                expected_improvement="提高知识激活率",
                priority=severity
            ))

        recommendations.append(OptimizationRecommendation(
            recommendation_id="R3",
            strategy=ActivationStrategy.CHAIN_OF_THOUGHT,
            description="使用思维链引导推理",
            implementation="要求逐步思考和推理",
            expected_improvement="提高推理准确性",
            priority=DiagnosisSeverity.LOW
        ))

        return recommendations

    def _calculate_improvement(
        self,
        original: str,
        improved: str,
        ground_truth: str | None
    ) -> float:
        """计算改进分数"""
        if not ground_truth:
            # 无标准答案时，基于长度和信息量估计
            length_ratio = len(improved) / max(len(original), 1)
            return min(1.0, length_ratio * 0.5 + 0.3)

        # 有标准答案时，计算相似度（简化版）
        original_overlap = len(set(original.split()) & set(ground_truth.split()))
        improved_overlap = len(set(improved.split()) & set(ground_truth.split()))

        if original_overlap == 0:
            return 0.5 if improved_overlap > 0 else 0.0

        return min(1.0, improved_overlap / original_overlap)

    def _parse_json_response(self, response_text: str) -> dict | None:
        """解析JSON响应"""
        try:
            import json
            json_match = response_text
            if "```json" in response_text:
                json_match = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_match = response_text.split("```")[1].split("```")[0]

            return json.loads(json_match.strip())
        except Exception as e:
            logger.error(f"JSON解析失败: {e}")
            return None


# ==================== 便捷函数 ====================

async def diagnose_response(
    query: str,
    response: str,
    ground_truth: str | None = None,
    llm_manager=None
) -> DiagnosisResult:
    """
    便捷函数: 诊断回答错误

    Args:
        query: 原始问题
        response: 模型回答
        ground_truth: 正确答案
        llm_manager: LLM管理器

    Returns:
        DiagnosisResult: 诊断结果
    """
    diagnoser = KnowledgeActivationDiagnoser(llm_manager=llm_manager)
    return await diagnoser.diagnose(query, response, ground_truth)


async def activate_and_improve(
    query: str,
    response: str,
    llm_manager=None
) -> ActivationSession:
    """
    便捷函数: 激活知识并改进回答

    Args:
        query: 原始问题
        response: 原始回答
        llm_manager: LLM管理器

    Returns:
        ActivationSession: 激活会话
    """
    diagnoser = KnowledgeActivationDiagnoser(llm_manager=llm_manager)
    return await diagnoser.create_activation_session(query, response)


def format_diagnosis_report(result: DiagnosisResult) -> str:
    """
    格式化诊断报告

    Args:
        result: 诊断结果

    Returns:
        str: 格式化的报告
    """
    lines = [
        "=" * 60,
        "知识激活诊断报告",
        "=" * 60,
        "",
        f"【诊断ID】 {result.diagnosis_id}",
        f"【错误类型】 {result.error_type.value}",
        f"【严重程度】 {result.severity.value}",
        f"【置信度】 {result.confidence:.0%}",
        "",
        "【错误描述】",
        f"  {result.error_description}",
        "",
        "【诊断依据】"
    ]

    for evidence in result.evidence:
        lines.append(f"  • {evidence}")

    if result.clarification_questions:
        lines.extend(["", "【澄清问题】"])
        for q in result.clarification_questions:
            lines.append(f"  Q: {q.question}")
            lines.append(f"     目的: {q.purpose}")

    if result.recommendations:
        lines.extend(["", "【优化建议】"])
        for r in result.recommendations:
            lines.append(f"  策略: {r.strategy.value}")
            lines.append(f"  描述: {r.description}")
            lines.append(f"  实施: {r.implementation}")
            lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)
