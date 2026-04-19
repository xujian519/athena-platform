from __future__ import annotations
"""
双模型协同推理系统

主推理引擎: GLM-4.7 (智谱AI)
交叉验证引擎: DeepSeek-R1 (DeepSeek)

用于数学、物理、化学、生物等理科推理任务的质量保证
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

# 导入理科分类器和提示词
try:
    from core.nlp.science_classifier import ClassificationResult, get_science_classifier
    from core.nlp.science_prompts import SciencePromptTemplates, ScienceTopic
except ImportError:
    get_science_classifier = None
    SciencePromptTemplates = None
    ScienceTopic = None

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """验证状态"""

    PENDING = "pending"
    VALIDATED = "validated"
    CONFLICT = "conflict"
    ERROR = "error"


@dataclass
class ValidationResult:
    """验证结果"""

    status: ValidationStatus
    primary_answer: str
    validator_answer: str
    confidence: float
    discrepancy_details: dict[str, Any] | None = None
    recommendation: str = ""


class DualModelCoordinator:
    """双模型协同推理协调器"""

    def __init__(
        self,
        primary_model: str = "glm-4.7",
        validator_model: str = "deepseek-reasoner",
        config_path: str | None = None,
    ):
        self.primary_model = primary_model
        self.validator_model = validator_model
        self.config = self._load_config(config_path)

        # 初始化理科分类器
        self.classifier = get_science_classifier() if get_science_classifier else None
        self.prompt_templates = SciencePromptTemplates() if SciencePromptTemplates else None

        logger.info("✅ 双模型协同系统初始化完成(支持理科扩展)")
        logger.info(f"   主推理引擎: {self.primary_model}")
        logger.info(f"   交叉验证引擎: {self.validator_model}")
        if self.classifier:
            logger.info("   理科分类器: 已启用")

    def _load_config(self, config_path: str,) -> dict[str, Any]:
        """加载配置"""
        if config_path:
            try:
                with open(config_path, encoding="utf-8") as f:
                    import yaml

                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"配置文件加载失败: {e},使用默认配置")

        return {
            "cross_validation": {
                "enabled": True,
                "trigger_conditions": {
                    "math_reasoning": True,
                    "sequence_problems": True,
                    "complex_proof": True,
                },
            },
            "performance": {"temperature": 0.1, "max_tokens": 4000},
        }

    def should_cross_validate(self, task_type: str, confidence: float = 0.0) -> bool:
        """判断是否需要交叉验证"""
        if not self.config.get("cross_validation", {}).get("enabled", False):
            return False

        trigger_conditions = self.config.get("cross_validation", {}).get("trigger_conditions", {})

        # 数学问答题总是验证
        if task_type in ["math_reasoning", "sequence_problems", "complex_proof"]:
            return trigger_conditions.get(task_type, False)

        # 低置信度时验证
        return confidence < 0.8

    async def dual_reasoning(
        self,
        problem: str,
        task_type: str = "math_reasoning",
        primary_confidence: float = 1.0,
        auto_classify: bool = True,
    ) -> ValidationResult:
        """
        双模型协同推理(支持理科自动分类)

        Args:
            problem: 理科问题
            task_type: 任务类型(可选,如不指定则自动分类)
            primary_confidence: 主模型的置信度
            auto_classify: 是否自动分类科目

        Returns:
            ValidationResult: 验证结果
        """
        logger.info("🔄 开始双模型协同推理")
        logger.info(f"   任务类型: {task_type}")

        # 自动分类(如果启用)
        if auto_classify and self.classifier:
            classification = self.classifier.classify(problem)
            logger.info(f"   自动分类: {classification.subject.value} - {classification.topic}")
            logger.info(f"   分类置信度: {classification.confidence:.2f}")

            # 如果自动分类置信度高,使用分类结果
            if classification.confidence > 0.7:
                task_type = classification.topic

        logger.info(f"   最终任务类型: {task_type}")
        logger.info(f"   问题: {problem[:100]}...")

        # 判断是否需要交叉验证
        if not self.should_cross_validate(task_type, primary_confidence):
            logger.info("⏭️  跳过交叉验证(不满足触发条件)")
            return ValidationResult(
                status=ValidationStatus.PENDING,
                primary_answer="",
                validator_answer="",
                confidence=primary_confidence,
                recommendation="使用主模型答案",
            )

        # 并行推理
        logger.info("🚀 启动双模型并行推理...")
        try:
            primary_result, validator_result = await asyncio.gather(
                self._query_primary_model(problem, task_type),
                self._query_validator_model(problem, task_type),
                return_exceptions=True,
            )

            # 处理异常
            if isinstance(primary_result, Exception):
                logger.error(f"❌ 主模型推理失败: {primary_result}")
                primary_result = {"answer": "", "confidence": 0.0}

            if isinstance(validator_result, Exception):
                logger.error(f"❌ 验证模型推理失败: {validator_result}")
                validator_result = {"answer": "", "confidence": 0.0}

            # 比较结果
            return self._compare_results(primary_result, validator_result, problem)

        except Exception as e:
            logger.error(f"❌ 双模型推理异常: {e}")
            return ValidationResult(
                status=ValidationStatus.ERROR,
                primary_answer="",
                validator_answer="",
                confidence=0.0,
                recommendation=f"推理过程出错: {e!s}",
            )

    async def _query_primary_model(
        self, problem: str, task_type: str = "general"
    ) -> dict[str, Any]:
        """查询主模型(GLM-4.7)"""
        logger.info("📡 查询主模型 GLM-4.7...")

        try:
            from core.llm.glm_client import get_glm_client

            client = get_glm_client()

            response = await client.reason(
                problem=problem, task_type=task_type, temperature=0.3, max_tokens=4000
            )

            return {
                "answer": response.answer,
                "confidence": response.confidence,
                "reasoning": response.reasoning,
                "tokens_used": response.tokens_used,
            }

        except Exception as e:
            logger.error(f"❌ GLM-4.7调用失败: {e}")
            return {
                "answer": f"GLM-4.7调用失败: {e!s}",
                "confidence": 0.0,
                "reasoning": "",
                "error": str(e),
            }

    async def _query_validator_model(
        self, problem: str, task_type: str = "math_reasoning"
    ) -> dict[str, Any]:
        """查询验证模型(DeepSeek-R1)"""
        logger.info("📡 查询验证模型 DeepSeek-R1...")

        try:
            from core.llm.deepseek_client import get_deepseek_client

            client = get_deepseek_client()

            response = await client.reason(
                problem=problem, task_type=task_type, temperature=0.1, max_tokens=4000
            )

            return {
                "answer": response.answer,
                "confidence": response.confidence,
                "reasoning": response.reasoning,
                "tokens_used": response.tokens_used,
            }

        except Exception as e:
            logger.error(f"❌ DeepSeek-R1调用失败: {e}")
            return {
                "answer": f"DeepSeek-R1调用失败: {e!s}",
                "confidence": 0.0,
                "reasoning": "",
                "error": str(e),
            }

    def _compare_results(
        self,
        primary_result: dict[str, Any],        validator_result: dict[str, Any],        original_problem: str,
    ) -> ValidationResult:
        """比较两个模型的结果"""
        primary_answer = primary_result.get("answer", "")
        validator_answer = validator_result.get("answer", "")

        logger.info("🔍 比较模型结果...")
        logger.info(f"   GLM-4.7: {primary_answer[:100]}...")
        logger.info(f"   DeepSeek-R1: {validator_answer[:100]}...")

        # 简单的字符串相似度检查
        # TODO: 实现更复杂的答案比较逻辑
        similarity = self._calculate_answer_similarity(primary_answer, validator_answer)

        if similarity > 0.9:
            logger.info("✅ 答案一致,验证通过")
            return ValidationResult(
                status=ValidationStatus.VALIDATED,
                primary_answer=primary_answer,
                validator_answer=validator_answer,
                confidence=(
                    primary_result.get("confidence", 0.5) + validator_result.get("confidence", 0.5)
                )
                / 2,
                recommendation="✅ 双模型答案一致,可以使用",
            )
        else:
            logger.warning("⚠️  答案存在分歧")
            return ValidationResult(
                status=ValidationStatus.CONFLICT,
                primary_answer=primary_answer,
                validator_answer=validator_answer,
                confidence=0.5,
                discrepancy_details={
                    "similarity": similarity,
                    "primary_confidence": primary_result.get("confidence", 0.0),
                    "validator_confidence": validator_result.get("confidence", 0.0),
                    "primary_reasoning": primary_result.get("reasoning", ""),
                    "validator_reasoning": validator_result.get("reasoning", ""),
                },
                recommendation="⚠️  双模型答案不一致,建议人工审核",
            )

    def _calculate_answer_similarity(self, answer1: str, answer2: str) -> float:
        """计算答案相似度"""
        # 简单实现:使用编辑距离
        # TODO: 使用更复杂的语义相似度计算

        if not answer1 or not answer2:
            return 0.0

        # 简化的相似度计算
        len1, len2 = len(answer1), len(answer2)
        if len1 == 0 and len2 == 0:
            return 1.0

        # 使用最长公共子序列
        lcs = self._longest_common_subsequence(answer1, answer2)
        max_len = max(len1, len2)

        return lcs / max_len if max_len > 0 else 0.0

    def _longest_common_subsequence(self, s1: str, s2: str) -> int:
        """计算最长公共子序列长度"""
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return dp[m][n]

    def format_validation_report(self, result: ValidationResult) -> str:
        """格式化验证报告"""
        report = []
        report.append("=" * 60)
        report.append("📊 双模型交叉验证报告")
        report.append("=" * 60)
        report.append(f"验证状态: {result.status.value}")
        report.append(f"推荐意见: {result.recommendation}")
        report.append("")
        report.append("📌 GLM-4.7 (主推理引擎):")
        report.append(f"   答案: {result.primary_answer[:200]}...")
        report.append("")
        report.append("📌 DeepSeek-R1 (交叉验证):")
        report.append(f"   答案: {result.validator_answer[:200]}...")
        report.append("")

        if result.discrepancy_details:
            report.append("⚠️  分歧详情:")
            report.append(f"   相似度: {result.discrepancy_details.get('similarity', 0):.2%}")
            report.append(
                f"   置信度对比: {result.discrepancy_details.get('primary_confidence', 0):.2%} vs {result.discrepancy_details.get('validator_confidence', 0):.2%}"
            )

        report.append("=" * 60)

        return "\n".join(report)


# 单例
_dual_model_coordinator: DualModelCoordinator | None = None


def get_dual_model_coordinator() -> DualModelCoordinator:
    """获取双模型协调器单例"""
    global _dual_model_coordinator
    if _dual_model_coordinator is None:
        _dual_model_coordinator = DualModelCoordinator()
    return _dual_model_coordinator


# 使用示例
async def example_usage():
    """使用示例"""
    coordinator = get_dual_model_coordinator()

    # 数列递推题
    problem = """
    已知 a1 = 2, a2 = 5/2, 递推关系式为 a_{n+1} = a_n(a_{n-1}^2 - 2) - 5/2,求 a_n。
    """

    result = await coordinator.dual_reasoning(
        problem=problem, task_type="sequence_problems", primary_confidence=0.85
    )

    print(coordinator.format_validation_report(result))


if __name__ == "__main__":
    asyncio.run(example_usage())
