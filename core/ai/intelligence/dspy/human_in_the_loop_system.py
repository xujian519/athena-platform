#!/usr/bin/env python3

"""
人机协作专利分析系统 - 原型实现
Human-in-the-Loop Patent Analysis System - Prototype

作者: Athena平台团队
创建时间: 2025-12-30
版本: 1.0.0-proto

本系统实现任务分解、AI自动执行、人类决策验证的完整工作流
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


# ===============================
# 1. 基础数据结构
# ===============================


class TaskType(Enum):
    """任务类型枚举"""

    AI_AUTOMATIC = "AI_AUTOMATIC"  # AI自动执行
    AI_WITH_VALIDATION = "AI_WITH_VALIDATION"  # AI执行+验证
    HUMAN_GUIDED_AI = "HUMAN_GUIDED_AI"  # 人类指导+AI填充
    HUMAN_DECISION = "HUMAN_DECISION"  # 人类决策


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_HUMAN = "awaiting_human"


@dataclass
class TaskResult:
    """任务执行结果"""

    task_id: str
    result: Any
    confidence: float  # 0.0 - 1.0
    validation: dict[str, Any]
    human_intervention: bool = False
    execution_time: float = 0.0
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "result": self.result,
            "confidence": self.confidence,
            "validation": self.validation,
            "human_intervention": self.human_intervention,
            "execution_time": self.execution_time,
            "error_message": self.error_message,
        }


@dataclass
class Task:
    """任务定义"""

    task_id: str
    sequence: int
    task_type: TaskType
    description: str
    input_data: dict[str, Any]
    output_schema: str
    validator_name: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "sequence": self.sequence,
            "task_type": self.task_type.value,
            "description": self.description,
            "input_data": self.input_data,
            "output_schema": self.output_schema,
            "validator_name": self.validator_name,
            "status": self.status.value,
            "dependencies": self.dependencies,
        }


# ===============================
# 2. 验证器系统
# ===============================


class BaseValidator:
    """验证器基类"""

    def validate(self, result: Any, expected_schema: str) -> dict[str, Any]:
        """
        验证结果

        Returns:
            {
                "valid": bool,
                "score": float,  # 0.0 - 1.0
                "errors": list[str],
                "warnings": list[str]
            }
        """
        raise NotImplementedError


class ClaimsValidator(BaseValidator):
    """权利要求提取验证器"""

    def validate(self, result: Any, expected_schema: str) -> dict[str, Any]:
        errors = []
        warnings = []
        score = 1.0

        if not isinstance(result, dict):
            return {"valid": False, "score": 0.0, "errors": ["结果必须是字典"], "warnings": []}

        # 检查必需字段
        if "claims" not in result:
            errors.append("缺少claims字段")
            score -= 0.5
        elif not isinstance(result["claims"], list):
            errors.append("claims必须是列表")
            score -= 0.3
        elif len(result["claims"]) == 0:
            warnings.append("权利要求列表为空")
            score -= 0.1

        # 检查编号格式
        if "claims" in result:
            for i, claim in enumerate(result["claims"]):
                if not isinstance(claim, dict):
                    errors.append(f"权利要求{i+1}格式错误")
                    score -= 0.1
                elif "number" not in claim:
                    warnings.append(f"权利要求{i+1}缺少编号")
                    score -= 0.05

        return {
            "valid": len(errors) == 0,
            "score": max(0.0, score),
            "errors": errors,
            "warnings": warnings,
        }


class EvidenceValidator(BaseValidator):
    """证据提取验证器"""

    def validate(self, result: Any, expected_schema: str) -> dict[str, Any]:
        errors = []
        warnings = []
        score = 1.0

        if not isinstance(result, dict):
            return {"valid": False, "score": 0.0, "errors": ["结果必须是字典"], "warnings": []}

        if "evidence_list" not in result:
            errors.append("缺少evidence_list字段")
            score -= 0.5
        elif not isinstance(result["evidence_list"], list):
            errors.append("evidence_list必须是列表")
            score -= 0.3

        # 检查证据格式
        if "evidence_list" in result:
            for i, ev in enumerate(result["evidence_list"]):
                if not isinstance(ev, dict):
                    errors.append(f"证据{i+1}格式错误")
                    score -= 0.1
                else:
                    if "number" not in ev:
                        warnings.append(f"证据{i+1}缺少编号")
                    if "content" not in ev:
                        warnings.append(f"证据{i+1}缺少内容")

        return {
            "valid": len(errors) == 0,
            "score": max(0.0, score),
            "errors": errors,
            "warnings": warnings,
        }


class LLMScorerValidator(BaseValidator):
    """LLM评分验证器 - 用于复杂任务"""

    def validate(self, result: Any, expected_schema: str) -> dict[str, Any]:
        """
        使用LLM对结果进行评分

        这里简化为基于规则的基本检查
        实际应用中可以调用LLM进行深度评估
        """
        errors = []
        warnings = []
        score = 0.8  # 默认给基础分

        if not isinstance(result, dict):
            return {"valid": False, "score": 0.0, "errors": ["结果必须是字典"], "warnings": []}

        # 检查是否有reasoning字段
        if "reasoning" not in result:
            errors.append("缺少reasoning字段")
            score -= 0.3
        elif not isinstance(result["reasoning"], str):
            errors.append("reasoning必须是字符串")
            score -= 0.2
        elif len(result["reasoning"]) < 50:
            warnings.append("推理过程过短")
            score -= 0.1

        # 检查是否有conclusion字段
        if "conclusion" not in result:
            errors.append("缺少conclusion字段")
            score -= 0.2
        elif not isinstance(result["conclusion"], str):
            errors.append("conclusion必须是字符串")
            score -= 0.1

        return {
            "valid": len(errors) == 0,
            "score": max(0.0, min(1.0, score)),
            "errors": errors,
            "warnings": warnings,
        }


class ValidatorRegistry:
    """验证器注册表"""

    def __init__(self):
        self._validators = {
            "ClaimsValidator": ClaimsValidator(),
            "EvidenceValidator": EvidenceValidator(),
            "LLMScorer": LLMScorerValidator(),
            "HumanExpert": None,  # 人类专家,不进行自动验证
        }

    def get(self, validator_name: str) -> Optional[BaseValidator]:
        """获取验证器"""
        return self._validators.get(validator_name)

    def register(self, name: str, validator: BaseValidator) -> Any:
        """注册新验证器"""
        self._validators[name] = validator


# ===============================
# 3. AI执行器
# ===============================


class AIExecutor:
    """AI任务执行器"""

    def __init__(self):
        # 在实际应用中,这里会加载DSPy训练好的模型
        self.models = {}
        logger.info("AI执行器初始化完成")

    def execute(self, task: Task, context: dict[str, Any]) -> TaskResult:
        """
        执行AI任务

        这里是模拟实现,实际应用中会调用DSPy训练的模型
        """
        import time

        start_time = time.time()

        try:
            logger.info(f"执行AI任务: {task.task_id} ({task.task_type.value})")

            if task.task_type == TaskType.AI_AUTOMATIC:
                result = self._execute_automatic(task, context)
            elif task.task_type == TaskType.AI_WITH_VALIDATION:
                result = self._execute_with_validation(task, context)
            elif task.task_type == TaskType.HUMAN_GUIDED_AI:
                result = self._execute_human_guided(task, context)
            else:
                raise ValueError(f"不支持的任务类型: {task.task_type}")

            execution_time = time.time() - start_time

            return TaskResult(
                task_id=task.task_id,
                result=result["output"],
                confidence=result.get("confidence", 0.8),
                validation=result.get("validation", {"valid": True, "score": 1.0}),
                human_intervention=False,
                execution_time=execution_time,
            )

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            return TaskResult(
                task_id=task.task_id,
                result=None,
                confidence=0.0,
                validation={"valid": False, "score": 0.0, "errors": [str(e)]},
                human_intervention=False,
                execution_time=time.time() - start_time,
                error_message=str(e),
            )

    def _execute_automatic(self, task: Task, context: dict[str, Any]) -> dict[str, Any]:
        """执行AI自动任务"""
        # 模拟AI执行
        if "extract" in task.task_id and "claim" in task.task_id:
            # 提取权利要求
            output = {
                "claims": [
                    {"number": "1", "content": "一种数据处理方法,包括..."},
                    {"number": "2", "content": "根据权利要求1所述的方法,其特征在于..."},
                ],
                "total_claims": 2,
            }
            confidence = 0.95

        elif "extract" in task.task_id and "evidence" in task.task_id:
            # 提取证据
            output = {
                "evidence_list": [
                    {"number": "证据1", "content": "CN1234567A", "type": "专利文献"},
                    {"number": "证据2", "content": "US2021000000A1", "type": "专利文献"},
                ],
                "total_evidence": 2,
            }
            confidence = 0.92

        else:
            output = {"message": f"AI自动完成任务: {task.description}"}
            confidence = 0.85

        return {"output": output, "confidence": confidence}

    def _execute_with_validation(self, task: Task, context: dict[str, Any]) -> dict[str, Any]:
        """执行需要验证的AI任务"""
        # 模拟AI执行
        if "comparison" in task.task_id:
            output = {
                "comparison_matrix": [
                    {"feature": "特征A", "claim": "包含", "evidence": "包含", "difference": "无"},
                    {"feature": "特征B", "claim": "包含", "evidence": "不包含", "difference": "有"},
                ],
                "conclusion": "存在区别特征",
            }
            confidence = 0.75
        else:
            output = {"message": f"AI验证完成任务: {task.description}"}
            confidence = 0.70

        return {"output": output, "confidence": confidence}

    def _execute_human_guided(self, task: Task, context: dict[str, Any]) -> dict[str, Any]:
        """执行人类指导的AI任务"""
        # 在实际应用中,这里会等待人类提供框架
        # 然后AI填充细节

        # 模拟: 使用人类提供的框架
        framework = context.get(
            "human_framework",
            {
                "legal_basis": "专利法第22条第3款",
                "analysis_steps": ["区别特征", "技术启示", "显而易见性"],
            },
        )

        output = {
            "framework": framework,
            "filled_details": {
                "difference_features": ["特征X", "特征Y"],
                "technical_teaching": "现有技术未给出...",
                "obviousness": "对本领域技术人员来说...",
            },
            "reasoning": f"基于{framework['legal_basis']},经分析...",
        }

        return {"output": output, "confidence": "human_guided"}


# ===============================
# 4. 人类交互接口
# ===============================


class HumanInterface:
    """人类交互接口"""

    def __init__(self):
        self.pending_reviews = {}
        self.pending_decisions = {}
        logger.info("人类交互接口初始化完成")

    def request_review(
        self, task: Task, ai_result: TaskResult, validation: dict[str, Any]]
    ) -> dict[str, Any]:
        """
        请求人类复核AI结果

        在实际应用中,这会触发UI界面,等待人类输入
        这里简化为返回模拟的人类决策
        """
        logger.info(f"⏳ 请求人类复核: {task.task_id}")
        logger.info(f"   AI置信度: {ai_result.confidence:.2%}")
        logger.info(f"   验证分数: {validation.get('score', 0):.2%}")

        # 模拟人类决策
        # 在实际应用中,这里会阻塞等待UI响应
        if ai_result.confidence >= 0.8:
            # 高置信度,人类接受
            decision = {
                "action": "accept",
                "result": ai_result.result,
                "confidence": 1.0,  # 人类确认后置信度为100%
                "comments": "AI分析合理,予以接受",
            }
        elif ai_result.confidence >= 0.6:
            # 中等置信度,人类可能修改
            decision = {
                "action": "modify",
                "result": self._modify_result(ai_result.result),
                "confidence": 0.9,  # 人类修改后提升置信度
                "comments": "对AI结果进行了小幅修正",
            }
        else:
            # 低置信度,人类重新决策
            decision = {
                "action": "reject",
                "result": self._make_new_decision(task),
                "confidence": 1.0,
                "comments": "AI结果不可接受,重新分析",
            }

        return decision

    def make_decision(self, task: Task, context: dict[str, Any]) -> dict[str, Any]:
        """
        请求人类决策

        在实际应用中,这会展示决策界面
        """
        logger.info(f"⏳ 请求人类决策: {task.task_id}")
        logger.info(f"   任务描述: {task.description}")

        # 模拟人类决策
        decision = {
            "decision": self._get_human_decision(task),
            "reasoning": "经综合分析现有技术特征...",
            "confidence": 1.0,
            "expert_signature": "专家ID: H001",
        }

        return decision

    def get_framework(self, task: Task) -> dict[str, Any]:
        """获取人类设定的分析框架"""
        logger.info(f"⏳ 请求人类设定框架: {task.task_id}")

        # 模拟人类提供的框架
        framework = {
            "legal_basis": "专利法第22条第3款",
            "key_questions": ["区别特征是什么?", "现有技术是否给出技术启示?", "是否显而易见?"],
            "analysis_structure": {
                "step1": "确定区别特征",
                "step2": "分析技术启示",
                "step3": "判断显而易见性",
            },
        }

        return framework

    def _modify_result(self, result: Any) -> Any:
        """模拟人类修改结果"""
        if isinstance(result, dict):
            # 添加人类修改标记
            result["human_modified"] = True
            result["modifications"]] = ["修正了特征描述", "补充了对比细节"]
        return result

    def _make_new_decision(self, task: Task) -> Any:
        """模拟人类重新决策"""
        return {"new_analysis": "人类专家的重新分析结果", "basis": "基于更深入的技术对比"}

    def _get_human_decision(self, task: Task) -> str:
        """模拟人类决策结果"""
        # 根据任务类型返回不同的决策
        if "conclusion" in task.task_id:
            return "专利权全部无效"
        elif "novelty" in task.task_id:
            return "具备新颖性"
        elif "creative" in task.task_id:
            return "具备创造性"
        else:
            return "维持专利权有效"


# ===============================
# 5. 任务分解器
# ===============================


class PatentTaskDecomposer:
    """专利案例任务分解器"""

    def __init__(self):
        self.task_templates = self._load_task_templates()
        logger.info("任务分解器初始化完成")

    def _load_task_templates(self) -> dict[str, list[dict]]:
        """加载任务模板"""
        return {
            "novelty": [
                {
                    "task_id": "extract_claims",
                    "task_type": TaskType.AI_AUTOMATIC,
                    "description": "提取涉案专利权利要求",
                    "validator": "ClaimsValidator",
                    "output_schema": "claims_list",
                },
                {
                    "task_id": "extract_evidence",
                    "task_type": TaskType.AI_AUTOMATIC,
                    "description": "提取对比文件证据",
                    "validator": "EvidenceValidator",
                    "output_schema": "evidence_list",
                },
                {
                    "task_id": "claim_comparison",
                    "task_type": TaskType.AI_WITH_VALIDATION,
                    "description": "权利要求与证据逐条对比",
                    "validator": "LLMScorer",
                    "output_schema": "comparison_matrix",
                },
                {
                    "task_id": "novelty_conclusion",
                    "task_type": TaskType.HUMAN_DECISION,
                    "description": "新颖性结论判断",
                    "validator": "HumanExpert",
                    "output_schema": "conclusion",
                },
            ],
            "creative": [
                {
                    "task_id": "extract_problem",
                    "task_type": TaskType.AI_WITH_VALIDATION,
                    "description": "提取发明要解决的技术问题",
                    "validator": "LLMScorer",
                    "output_schema": "problem_statement",
                },
                {
                    "task_id": "identify_differences",
                    "task_type": TaskType.AI_WITH_VALIDATION,
                    "description": "识别与现有技术的区别特征",
                    "validator": "LLMScorer",
                    "output_schema": "differences_list",
                },
                {
                    "task_id": "obviousness_analysis",
                    "task_type": TaskType.HUMAN_GUIDED_AI,
                    "description": "显而易见性分析",
                    "validator": "HumanExpert",
                    "output_schema": "analysis_report",
                },
                {
                    "task_id": "creative_conclusion",
                    "task_type": TaskType.HUMAN_DECISION,
                    "description": "创造性结论判断",
                    "validator": "HumanExpert",
                    "output_schema": "conclusion",
                },
            ],
            "disclosure": [
                {
                    "task_id": "extract_technical_solution",
                    "task_type": TaskType.AI_AUTOMATIC,
                    "description": "提取技术方案内容",
                    "validator": "ClaimsValidator",
                    "output_schema": "technical_solution",
                },
                {
                    "task_id": "check_completeness",
                    "task_type": TaskType.AI_WITH_VALIDATION,
                    "description": "检查公开是否充分",
                    "validator": "LLMScorer",
                    "output_schema": "completeness_report",
                },
                {
                    "task_id": "disclosure_conclusion",
                    "task_type": TaskType.HUMAN_DECISION,
                    "description": "充分公开结论判断",
                    "validator": "HumanExpert",
                    "output_schema": "conclusion",
                },
            ],
            "clarity": [
                {
                    "task_id": "extract_claims_for_clarity",
                    "task_type": TaskType.AI_AUTOMATIC,
                    "description": "提取权利要求用于清楚性分析",
                    "validator": "ClaimsValidator",
                    "output_schema": "claims_list",
                },
                {
                    "task_id": "check_ambiguity",
                    "task_type": TaskType.AI_WITH_VALIDATION,
                    "description": "检查权利要求是否清楚",
                    "validator": "LLMScorer",
                    "output_schema": "ambiguity_report",
                },
                {
                    "task_id": "clarity_conclusion",
                    "task_type": TaskType.HUMAN_DECISION,
                    "description": "清楚性结论判断",
                    "validator": "HumanExpert",
                    "output_schema": "conclusion",
                },
            ],
        }

    def decompose(self, case_info: dict[str, Any], case_type: str) -> list[Task]:
        """分解案例为任务序列"""
        if case_type not in self.task_templates:
            raise ValueError(f"不支持的案例类型: {case_type}")

        template = self.task_templates[case_type]
        tasks = []

        for i, task_spec in enumerate(template):
            task = Task(
                task_id=f"{case_type}_{task_spec['task_id']}",
                sequence=i,
                task_type=task_spec["task_type"],
                description=task_spec["description"],
                input_data={
                    "case_info": case_info,
                    "task_specific": self._prepare_task_input(task_spec, case_info),
                },
                output_schema=task_spec["output_schema"],
                validator_name=task_spec["validator"],
                status=TaskStatus.PENDING,
            )
            tasks.append(task)

        logger.info(f"案例 {case_info.get('case_id', 'unknown')} 分解为 {len(tasks)} 个任务")
        return tasks

    def _prepare_task_input(self, task_spec: dict, case_info: dict) -> dict[str, Any]:
        """准备任务特定输入"""
        # 根据任务类型准备特定的输入数据
        return {
            "background": case_info.get("background", ""),
            "technical_field": case_info.get("technical_field", ""),
            "patent_number": case_info.get("patent_number", ""),
        }


# ===============================
# 6. 任务执行器
# ===============================


class TaskExecutor:
    """任务执行器"""

    def __init__(self):
        self.ai_executor = AIExecutor()
        self.human_interface = HumanInterface()
        self.validator_registry = ValidatorRegistry()
        logger.info("任务执行器初始化完成")

    def execute_task(self, task: Task, context: dict[str, Any]) -> TaskResult:
        """执行单个任务"""
        task.status = TaskStatus.IN_PROGRESS

        try:
            logger.info(f"\n执行任务 [{task.sequence+1}]: {task.description}")
            logger.info(f"任务类型: {task.task_type.value}")

            if task.task_type == TaskType.AI_AUTOMATIC:
                # AI自动执行
                ai_result = self.ai_executor.execute(task, context)
                validator = self.validator_registry.get(task.validator_name)
                if validator:
                    validation = validator.validate(ai_result.result, task.output_schema)
                    ai_result.validation = validation

                logger.info(f"✓ AI完成 (置信度: {ai_result.confidence:.2%})")
                return ai_result

            elif task.task_type == TaskType.AI_WITH_VALIDATION:
                # AI执行 + 验证
                ai_result = self.ai_executor.execute(task, context)
                validator = self.validator_registry.get(task.validator_name)
                if validator:
                    validation = validator.validate(ai_result.result, task.output_schema)
                    ai_result.validation = validation

                    # 如果置信度低,请求人类复核
                    if validation["score"] < 0.7:
                        logger.info(f"⚠️ 置信度较低 ({validation['score']:.2%}),请求人类复核")
                        human_review = self.human_interface.request_review(
                            task, ai_result, validation
                        )
                        ai_result.result = human_review["result"]
                        ai_result.confidence = human_review["confidence"]
                        ai_result.human_intervention = True

                logger.info(
                    f"✓ 完成 (置信度: {ai_result.confidence:.2%}, 人类介入: {ai_result.human_intervention})"
                )
                return ai_result

            elif task.task_type == TaskType.HUMAN_GUIDED_AI:
                # 人类设定框架,AI填充
                logger.info("⏳ 等待人类设定分析框架...")
                framework = self.human_interface.get_framework(task)
                context["human_framework"] = framework

                ai_result = self.ai_executor.execute(task, context)
                ai_result.human_intervention = True

                logger.info("✓ 完成 (基于人类框架)")
                return ai_result

            elif task.task_type == TaskType.HUMAN_DECISION:
                # 人类直接决策
                logger.info("⏳ 等待人类决策...")
                decision = self.human_interface.make_decision(task, context)

                return TaskResult(
                    task_id=task.task_id,
                    result=decision,
                    confidence=1.0,
                    validation={"valid": True, "score": 1.0},
                    human_intervention=True,
                )

            else:
                raise ValueError(f"不支持的任务类型: {task.task_type}")

        except Exception as e:
            logger.error(f"✗ 任务执行失败: {e}")
            task.status = TaskStatus.FAILED
            return TaskResult(
                task_id=task.task_id,
                result=None,
                confidence=0.0,
                validation={"valid": False, "score": 0.0, "errors": [str(e)]},
                error_message=str(e),
            )


# ===============================
# 7. 结果合成器
# ===============================


class ResultSynthesizer:
    """结果合成器"""

    def __init__(self):
        logger.info("结果合成器初始化完成")

    def synthesize(
        self, case_id: str, tasks: list[Task], task_results: list[TaskResult]
    ) -> dict[str, Any]:
        """合成最终分析报告"""
        logger.info(f"\n合成案例 {case_id} 的分析报告")

        # 统计信息
        total_tasks = len(tasks)
        ai_executed = sum(1 for r in task_results if not r.human_intervention)
        human_intervened = sum(1 for r in task_results if r.human_intervention)

        # 计算平均置信度
        confidences = [r.confidence for r in task_results if isinstance(r.confidence, float)]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # 提取最终结论
        final_conclusion = self._extract_conclusion(tasks, task_results)

        # 生成置信度报告
        confidence_report = self._generate_confidence_report(task_results)

        # 生成建议
        recommendations = self._generate_recommendations(task_results)

        report = {
            "case_id": case_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "total_tasks": total_tasks,
                "ai_executed": ai_executed,
                "human_intervened": human_intervened,
                "avg_confidence": avg_confidence,
                "total_execution_time": sum(r.execution_time for r in task_results),
            },
            "task_breakdown": [
                {
                    "task_id": t.task_id,
                    "sequence": t.sequence,
                    "description": t.description,
                    "task_type": t.task_type.value,
                    "result": r.result,
                    "confidence": r.confidence,
                    "human_intervention": r.human_intervention,
                    "execution_time": r.execution_time,
                }
                for t, r in zip(tasks, task_results, strict=False)
            ],
            "final_conclusion": final_conclusion,
            "confidence_report": confidence_report,
            "recommendations": recommendations,
        }

        return report

    def _extract_conclusion(self, tasks: list[Task], results: list[TaskResult]) -> str:
        """提取最终结论"""
        # 找到最后一个决策任务
        for task, result in zip(reversed(tasks), reversed(results), strict=False):
            if "conclusion" in task.task_id:
                if isinstance(result.result, dict):
                    return result.result.get(
                        "decision", result.result.get("conclusion", "未生成结论")
                    )
                else:
                    return str(result.result)
        return "未生成最终结论"

    def _generate_confidence_report(self, results: list[TaskResult]) -> dict[str, Any]:
        """生成置信度报告"""
        high_conf = sum(
            1 for r in results if isinstance(r.confidence, float) and r.confidence > 0.8
        )
        medium_conf = sum(
            1 for r in results if isinstance(r.confidence, float) and 0.5 <= r.confidence <= 0.8
        )
        low_conf = sum(1 for r in results if isinstance(r.confidence, float) and r.confidence < 0.5)
        human_verified = sum(
            1
            for r in results
            if r.confidence in ["human_guided", "human_expert"] or r.human_intervention
        )

        return {
            "high_confidence": high_conf,
            "medium_confidence": medium_conf,
            "low_confidence": low_conf,
            "human_verified": human_verified,
        }

    def _generate_recommendations(self, results: list[TaskResult]) -> list[dict[str, str]]:
        """生成改进建议"""
        recommendations = []

        # 低置信度任务
        low_conf_tasks = [
            r for r in results if isinstance(r.confidence, float) and r.confidence < 0.6
        ]

        if low_conf_tasks:
            recommendations.append(
                {
                    "type": "low_confidence",
                    "priority": "high",
                    "message": f"发现{len(low_conf_tasks)}个低置信度任务,建议人工复核",
                    "task_ids": [r.task_id for r in low_conf_tasks],
                }
            )

        # 人类干预点
        human_tasks = [r for r in results if r.human_intervention]

        if human_tasks:
            recommendations.append(
                {
                    "type": "human_intervention",
                    "priority": "medium",
                    "message": f"{len(human_tasks)}个任务需要人类介入",
                    "task_ids": [r.task_id for r in human_tasks],
                }
            )

        # 执行时间过长
        slow_tasks = [r for r in results if r.execution_time > 30]  # 超过30秒

        if slow_tasks:
            recommendations.append(
                {
                    "type": "performance",
                    "priority": "low",
                    "message": f"{len(slow_tasks)}个任务执行时间较长,可优化",
                    "task_ids": [r.task_id for r in slow_tasks],
                }
            )

        return recommendations


# ===============================
# 8. 人机协作系统主类
# ===============================


class HumanInTheLoopSystem:
    """人机协作专利分析系统"""

    def __init__(self):
        self.decomposer = PatentTaskDecomposer()
        self.executor = TaskExecutor()
        self.synthesizer = ResultSynthesizer()
        logger.info("人机协作系统初始化完成")

    def analyze_case(self, case_info: dict[str, Any], case_type: str) -> dict[str, Any]:
        """
        分析完整的专利案例

        Args:
            case_info: 案例信息 (包含background, technical_field, patent_number等)
            case_type: 案例类型 (novelty, creative, disclosure, clarity)

        Returns:
            分析报告字典
        """
        logger.info("\n" + "=" * 70)
        logger.info("🚀 开始人机协作专利分析")
        logger.info("=" * 70)
        logger.info(f"案例ID: {case_info.get('case_id', 'unknown')}")
        logger.info(f"案例类型: {case_type}")
        logger.info("=" * 70)

        # 1. 任务分解
        logger.info("\n📋 第1步: 任务分解")
        tasks = self.decomposer.decompose(case_info, case_type)

        # 2. 执行任务
        logger.info("\n⚙️ 第2步: 任务执行")
        context = {"case_info": case_info}
        task_results = []

        for task in tasks:
            result = self.executor.execute_task(task, context)
            task_results.append(result)

            # 更新上下文
            context[f"task_{task.task_id}"] = result

            # 更新任务状态
            task.status = TaskStatus.COMPLETED

        # 3. 合成报告
        logger.info("\n📊 第3步: 合成报告")
        report = self.synthesizer.synthesize(
            case_info.get("case_id", "unknown"), tasks, task_results
        )

        # 4. 打印报告摘要
        self._print_report_summary(report)

        return report

    def _print_report_summary(self, report: dict[str, Any]) -> Any:
        """打印报告摘要"""
        logger.info("\n" + "=" * 70)
        logger.info("📋 分析报告摘要")
        logger.info("=" * 70)

        meta = report["metadata"]
        logger.info("\n执行统计:")
        logger.info(f"  总任务数: {meta['total_tasks']}")
        logger.info(f"  AI执行: {meta['ai_executed']}")
        logger.info(f"  人类介入: {meta['human_intervened']}")
        logger.info(f"  平均置信度: {meta['avg_confidence']:.2%}")
        logger.info(f"  总执行时间: {meta['total_execution_time']:.2f}秒")

        conf = report["confidence_report"]
        logger.info("\n置信度分布:")
        logger.info(f"  高置信度 (>80%): {conf['high_confidence']}")
        logger.info(f"  中置信度 (50-80%): {conf['medium_confidence']}")
        logger.info(f"  低置信度 (<50%): {conf['low_confidence']}")
        logger.info(f"  人类验证: {conf['human_verified']}")

        logger.info("\n最终结论:")
        logger.info(f"  {report['final_conclusion']}")

        if report["recommendations"]:
            logger.info("\n建议:")
            for rec in report["recommendations"]:
                logger.info(f"  - [{rec['priority'].upper()}] {rec['message']}")

        logger.info("\n" + "=" * 70)

    def batch_analyze(
        self, cases: list[dict[str, Any], case_types: list[str]
    ) -> list[dict[str, Any]]:
        """批量分析案例"""
        logger.info(f"\n🚀 开始批量分析 {len(cases)} 个案例")

        reports = []
        for i, (case_info, case_type) in enumerate(zip(cases, case_types, strict=False)):
            logger.info(f"\n\n>>> 处理案例 {i+1}/{len(cases)}")

            try:
                report = self.analyze_case(case_info, case_type)
                reports.append(report)
            except Exception as e:
                logger.error(f"案例分析失败: {e}")
                reports.append({"case_id": case_info.get("case_id", f"case_{i}"), "error": str(e)})

        # 生成批量统计
        self._print_batch_summary(reports)

        return reports

    def _print_batch_summary(self, reports: list[dict[str, Any]) -> Any]:
        """打印批量分析摘要"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 批量分析摘要")
        logger.info("=" * 70)

        successful = sum(1 for r in reports if "error" not in r)
        failed = len(reports) - successful

        logger.info("\n处理结果:")
        logger.info(f"  成功: {successful}")
        logger.info(f"  失败: {failed}")

        if successful > 0:
            avg_conf = (
                sum(r["metadata"]["avg_confidence"] for r in reports if "metadata" in r)
                / successful
            )

            total_human = sum(r["metadata"]["human_intervened"] for r in reports if "metadata" in r)

            logger.info("\n平均指标:")
            logger.info(f"  平均置信度: {avg_conf:.2%}")
            logger.info(f"  总人类介入次数: {total_human}")

        logger.info("=" * 70)


# ===============================
# 9. 使用示例
# ===============================


def main() -> None:
    """主函数 - 演示系统使用"""

    # 创建系统实例
    system = HumanInTheLoopSystem()

    # 示例案例1: 新颖性分析
    case1 = {
        "case_id": "CN202310000000.0",
        "background": """
        案由: 本专利涉及一种数据处理方法,无效宣告请求人认为:
        1. 权利要求1不具备新颖性,与证据1公开的技术方案相同
        2. 证据1为CN1234567A,公开日为2020年1月1日
        3. 本专利申请日为2023年1月1日
        """,
        "technical_field": "人工智能",
        "patent_number": "CN202310000000.0",
    }

    # 分析案例1
    print("\n\n" + "█" * 70)
    print("案例1: 新颖性分析")
    print("█" * 70)
    report1 = system.analyze_case(case1, "novelty")

    # 示例案例2: 创造性分析
    case2 = {
        "case_id": "CN202310000001.0",
        "background": """
        案由: 本专利涉及一种机器学习算法优化方法,请求人认为:
        1. 权利要求1-3不具备创造性
        2. 区别特征仅是常规手段的替换
        3. 证据1给出了技术启示
        """,
        "technical_field": "人工智能",
        "patent_number": "CN202310000001.0",
    }

    print("\n\n" + "█" * 70)
    print("案例2: 创造性分析")
    print("█" * 70)
    report2 = system.analyze_case(case2, "creative")

    # 批量分析示例
    print("\n\n" + "█" * 70)
    print("批量分析示例")
    print("█" * 70)
    system.batch_analyze([case1, case2], ["novelty", "creative"])

    # 保存报告
    output_dir = Path("/Users/xujian/Athena工作平台/core/intelligence/dspy/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "case1_report.json", "w", encoding="utf-8") as f:
        json.dump(report1, f, ensure_ascii=False, indent=2)

    with open(output_dir / "case2_report.json", "w", encoding="utf-8") as f:
        json.dump(report2, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 报告已保存到: {output_dir}")


if __name__ == "__main__":
    main()

