#!/usr/bin/env python3

"""
验证器框架 - Minitap式质量保证
Verification Framework - Minitap-Style Quality Assurance

为每个执行步骤提供验证标准，确保输出质量。

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ========== 验证结果 ==========


class VerificationStatus(Enum):
    """验证状态"""
    PASSED = "passed"  # 验证通过
    FAILED = "failed"  # 验证失败
    WARNING = "warning"  # 警告（有瑕疵但可接受）
    SKIPPED = "skipped"  # 跳过验证


@dataclass
class VerificationIssue:
    """验证问题"""
    code: str  # 问题代码
    message: str  # 问题描述
    severity: str  # 严重程度: error/warning/info
    location: Optional[str] = None  # 问题位置
    suggestion: Optional[str] = None  # 修复建议


@dataclass
class VerificationResult:
    """验证结果"""
    status: VerificationStatus
    issues: list[VerificationIssue] = field(default_factory=list)
    score: float = 0.0  # 验证分数 0-100
    details: dict[str, Any] = field(default_factory=dict)
    verified_at: datetime = field(default_factory=datetime.now)

    @property
    def passed(self) -> bool:
        """是否通过验证"""
        return self.status == VerificationStatus.PASSED

    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return self.status == VerificationStatus.WARNING

    @property
    def failed(self) -> bool:
        """是否失败"""
        return self.status == VerificationStatus.FAILED

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "score": self.score,
            "issues": [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "severity": issue.severity,
                    "location": issue.location,
                    "suggestion": issue.suggestion,
                }
                for issue in self.issues
            ],
            "details": self.details,
            "verified_at": self.verified_at.isoformat(),
        }


# ========== 验证标准 ==========


@dataclass
class VerificationCriteria:
    """验证标准"""
    name: str  # 验证标准名称
    description: str  # 描述
    required_fields: list[str] = field(default_factory=list)  # 必需字段
    forbidden_patterns: list[str] = field(default_factory=list)  # 禁止模式
    validation_rules: list[Callable] = field(default_factory=list)  # 验证规则
    min_score: float = 60.0  # 最低分数
    strict_mode: bool = False  # 严格模式（任何警告都视为失败）


# ========== 验证器基类 ==========


class Verifier(ABC):
    """
    验证器基类

    所有验证器都必须继承此类并实现 verify 方法
    """

    def __init__(self, criteria: Optional[VerificationCriteria] = None):
        """
        初始化验证器

        Args:
            criteria: 验证标准
        """
        self.criteria = criteria or self._default_criteria()
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def verify(self, data: dict[str, Any]) -> VerificationResult:
        """
        执行验证

        Args:
            data: 要验证的数据（通常是Agent的输出）

        Returns:
            VerificationResult: 验证结果
        """
        pass

    def _default_criteria(self) -> VerificationCriteria:
        """获取默认验证标准"""
        return VerificationCriteria(
            name="default",
            description="默认验证标准",
        )

    def _create_issue(
        self,
        code: str,
        message: str,
        severity: str = "error",
        location: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> VerificationIssue:
        """创建验证问题"""
        return VerificationIssue(
            code=code,
            message=message,
            severity=severity,
            location=location,
            suggestion=suggestion,
        )

    def _calculate_score(
        self,
        total_checks: int,
        passed_checks: int,
        warning_count: int = 0,
    ) -> float:
        """计算验证分数"""
        if total_checks == 0:
            return 100.0

        # 基础分数
        base_score = (passed_checks / total_checks) * 100

        # 警告扣分
        warning_penalty = (warning_count / total_checks) * 10

        return max(0, min(100, base_score - warning_penalty))


# ========== 通用验证器 ==========


class RequiredFieldsVerifier(Verifier):
    """
    必需字段验证器

    验证数据中是否包含所有必需字段
    """

    async def verify(self, data: dict[str, Any]) -> VerificationResult:
        """验证必需字段"""
        issues = []
        missing_fields = []

        for field_name in self.criteria.required_fields:
            if field_name not in data:
                missing_fields.append(field_name)
                issues.append(
                    self._create_issue(
                        code="MISSING_FIELD",
                        message=f"缺少必需字段: {field_name}",
                        severity="error",
                        suggestion=f"请确保数据中包含 {field_name} 字段",
                    )
                )

        if missing_fields:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                issues=issues,
                score=0.0,
                details={"missing_fields": missing_fields},
            )

        return VerificationResult(
            status=VerificationStatus.PASSED,
            issues=[],
            score=100.0,
            details={"verified_fields": list(self.criteria.required_fields)},
        )


class DataQualityVerifier(Verifier):
    """
    数据质量验证器

    验证数据的完整性、准确性等质量指标
    """

    async def verify(self, data: dict[str, Any]) -> VerificationResult:
        """验证数据质量"""
        issues = []
        total_checks = 0
        passed_checks = 0
        warning_count = 0

        # 检查1: 空值检查
        total_checks += 1
        empty_fields = self._check_empty_values(data)
        if empty_fields:
            warning_count += len(empty_fields)
            for field_name in empty_fields:
                issues.append(
                    self._create_issue(
                        code="EMPTY_VALUE",
                        message=f"字段 {field_name} 的值为空",
                        severity="warning",
                        location=field_name,
                    )
                )
        else:
            passed_checks += 1

        # 检查2: 禁止模式检查
        total_checks += 1
        forbidden_matches = self._check_forbidden_patterns(data)
        if forbidden_matches:
            for pattern, location in forbidden_matches:
                issues.append(
                    self._create_issue(
                        code="FORBIDDEN_PATTERN",
                        message=f"包含禁止模式: {pattern}",
                        severity="error",
                        location=location,
                    )
                )
        else:
            passed_checks += 1

        # 检查3: 数据类型检查
        total_checks += 1
        type_issues = self._check_data_types(data)
        if type_issues:
            for type_issue in type_issues:
                if type_issue["severity"] == "error":
                    issues.append(self._create_issue(**type_issue))
                else:
                    warning_count += 1
                    issues.append(self._create_issue(**type_issue))
        else:
            passed_checks += 1

        # 计算分数
        score = self._calculate_score(total_checks, passed_checks, warning_count)

        # 确定状态
        if score < self.criteria.min_score:
            status = VerificationStatus.FAILED
        elif warning_count > 0:
            status = VerificationStatus.WARNING
        else:
            status = VerificationStatus.PASSED

        return VerificationResult(
            status=status,
            issues=issues,
            score=score,
            details={
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "warning_count": warning_count,
            },
        )

    def _check_empty_values(self, data: dict[str, Any]) -> list[str]:
        """检查空值"""
        empty_fields = []
        for key, value in data.items():
            if value is None or value == "" or value == []:
                empty_fields.append(key)
        return empty_fields

    def _check_forbidden_patterns(
        self,
        data: dict[str, Any],
    ) -> list[tuple[str, Optional[str]]]:
        """检查禁止模式"""
        matches = []

        # 将数据转换为字符串
        data_str = json.dumps(data, ensure_ascii=False)

        for pattern in self.criteria.forbidden_patterns:
            if pattern in data_str:
                # 尝试找到位置
                location = None
                for key, value in data.items():
                    value_str = str(value)
                    if pattern in value_str:
                        location = key
                        break

                matches.append((pattern, location))

        return matches

    def _check_data_types(
        self,
        data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """检查数据类型"""
        issues = []

        # 这里可以添加自定义的类型验证规则
        # 当前实现为基础检查
        for rule in self.criteria.validation_rules:
            result = rule(data)
            if isinstance(result, dict):
                issues.append(result)

        return issues


# ========== 专利领域验证器 ==========


class PatentSearchVerifier(Verifier):
    """
    专利检索验证器

    验证专利检索结果的质量
    """

    def _default_criteria(self) -> VerificationCriteria:
        """获取专利检索验证标准"""
        return VerificationCriteria(
            name="patent_search",
            description="专利检索验证标准",
            required_fields=["results", "query", "total_count"],
            min_score=70.0,
        )

    async def verify(self, data: dict[str, Any]) -> VerificationResult:
        """验证专利检索结果"""
        issues = []
        total_checks = 0
        passed_checks = 0

        # 检查1: 必需字段
        total_checks += 1
        required_verifier = RequiredFieldsVerifier(self.criteria)
        required_result = await required_verifier.verify(data)
        if required_result.failed:
            issues.extend(required_result.issues)
        else:
            passed_checks += 1

        # 检查2: 结果数量合理性
        total_checks += 1
        total_count = data.get("total_count", 0)
        results = data.get("results", [])

        if total_count < 0:
            issues.append(
                self._create_issue(
                    code="INVALID_COUNT",
                    message=f"检索结果数量无效: {total_count}",
                    severity="error",
                    suggestion="total_count 应该 >= 0"
                )
            )
        elif total_count == 0:
            issues.append(
                self._create_issue(
                    code="NO_RESULTS",
                    message="未找到任何结果",
                    severity="warning",
                    suggestion="尝试调整检索关键词",
                )
            )
        elif total_count != len(results):
            issues.append(
                self._create_issue(
                    code="COUNT_MISMATCH",
                    message=f"total_count({total_count}) 与 results长度({len(results)}) 不匹配",
                    severity="error",
                )
            )
        else:
            passed_checks += 1

        # 检查3: 结果完整性
        total_checks += 1
        if results:
            incomplete = 0
            for i, result in enumerate(results):
                if not isinstance(result, dict):
                    incomplete += 1
                    continue

                # 检查必需字段
                if "title" not in result and "patent_id" not in result:
                    issues.append(
                        self._create_issue(
                            code="INCOMPLETE_RESULT",
                            message=f"结果 {i} 缺少标题或专利号",
                            severity="warning",
                            location=f"results[{i}]",
                        )
                    )
                    incomplete += 1

            if incomplete == 0:
                passed_checks += 1
            elif incomplete < len(results) / 2:
                passed_checks += 1  # 部分通过
        else:
            passed_checks += 1  # 没有结果时跳过检查

        # 计算分数
        score = self._calculate_score(total_checks, passed_checks, len(issues))

        # 确定状态
        if score < self.criteria.min_score:
            status = VerificationStatus.FAILED
        elif any(issue.severity == "error" for issue in issues):
            status = VerificationStatus.FAILED
        elif any(issue.severity == "warning" for issue in issues):
            status = VerificationStatus.WARNING
        else:
            status = VerificationStatus.PASSED

        return VerificationResult(
            status=status,
            issues=issues,
            score=score,
            details={
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "result_count": total_count,
            },
        )


class PatentAnalysisVerifier(Verifier):
    """
    专利分析验证器

    验证专利分析结果的质量
    """

    def _default_criteria(self) -> VerificationCriteria:
        """获取专利分析验证标准"""
        return VerificationCriteria(
            name="patent_analysis",
            description="专利分析验证标准",
            required_fields=["analysis", "patent_id"],
            min_score=60.0,
        )

    async def verify(self, data: dict[str, Any]) -> VerificationResult:
        """验证专利分析结果"""
        issues = []
        total_checks = 0
        passed_checks = 0

        # 检查1: 必需字段
        total_checks += 1
        required_verifier = RequiredFieldsVerifier(self.criteria)
        required_result = await required_verifier.verify(data)
        if required_result.failed:
            issues.extend(required_result.issues)
        else:
            passed_checks += 1

        # 检查2: 分析内容长度
        total_checks += 1
        analysis = data.get("analysis", "")
        if isinstance(analysis, str):
            analysis_length = len(analysis.strip())
            if analysis_length < 50:
                issues.append(
                    self._create_issue(
                        code="ANALYSIS_TOO_SHORT",
                        message=f"分析内容过短: {analysis_length} 字符",
                        severity="warning",
                        suggestion="分析内容应该至少包含50个字符",
                    )
                )
            else:
                passed_checks += 1
        else:
            issues.append(
                self._create_issue(
                    code="INVALID_ANALYSIS_TYPE",
                    message="分析内容应该是字符串类型",
                    severity="error",
                )
            )

        # 检查3: 结构完整性
        total_checks += 1
        has_conclusion = "conclusion" in data or "结论" in str(analysis)
        has_technical_points = "technical_points" in data or any(
            keyword in str(analysis).lower()
            for keyword in ["技术方案", "技术特点", "创新点", "技术要点"]
        )

        if has_conclusion and has_technical_points:
            passed_checks += 1
        elif has_conclusion or has_technical_points:
            issues.append(
                self._create_issue(
                    code="INCOMPLETE_STRUCTURE",
                    message="分析结构不完整",
                    severity="warning",
                    suggestion="应该包含技术要点和结论",
                )
            )
        else:
            issues.append(
                self._create_issue(
                    code="NO_STRUCTURE",
                    message="分析缺少结构化内容",
                    severity="warning",
                    suggestion="建议添加技术要点和结论",
                )
            )
            passed_checks += 1  # 仍然通过，只是警告

        # 计算分数
        score = self._calculate_score(total_checks, passed_checks, len(issues))

        # 确定状态
        if score < self.criteria.min_score:
            status = VerificationStatus.FAILED
        elif any(issue.severity == "error" for issue in issues):
            status = VerificationStatus.FAILED
        elif any(issue.severity == "warning" for issue in issues):
            status = VerificationStatus.WARNING
        else:
            status = VerificationStatus.PASSED

        return VerificationResult(
            status=status,
            issues=issues,
            score=score,
            details={
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "analysis_length": analysis_length if isinstance(analysis, str) else 0,
            },
        )


class ClaimDraftingVerifier(Verifier):
    """
    权利要求撰写验证器

    验证生成的权利要求质量
    """

    def _default_criteria(self) -> VerificationCriteria:
        """获取权利要求撰写验证标准"""
        return VerificationCriteria(
            name="claim_drafting",
            description="权利要求撰写验证标准",
            required_fields=["claims"],
            min_score=70.0,
        )

    async def verify(self, data: dict[str, Any]) -> VerificationResult:
        """验证权利要求质量"""
        issues = []
        total_checks = 0
        passed_checks = 0

        # 检查1: 必需字段
        total_checks += 1
        required_verifier = RequiredFieldsVerifier(self.criteria)
        required_result = await required_verifier.verify(data)
        if required_result.failed:
            issues.extend(required_result.issues)
        else:
            passed_checks += 1

        # 检查2: 权利要求内容
        total_checks += 1
        claims = data.get("claims", "")
        if isinstance(claims, str):
            claims_length = len(claims.strip())
            if claims_length < 100:
                issues.append(
                    self._create_issue(
                        code="CLAIMS_TOO_SHORT",
                        message=f"权利要求过短: {claims_length} 字符",
                        severity="error",
                        suggestion="权利要求应该至少包含100个字符",
                    )
                )
            else:
                passed_checks += 1

            # 检查关键词
            required_keywords = ["所述", "其特征在于", "其中"]
            missing_keywords = [
                kw for kw in required_keywords if kw not in claims
            ]

            if missing_keywords:
                issues.append(
                    self._create_issue(
                        code="MISSING_KEYWORDS",
                        message=f"缺少权利要求常用关键词: {', '.join(missing_keywords)}",
                        severity="warning",
                        suggestion="使用标准权利要求措辞",
                    )
                )
        else:
            issues.append(
                self._create_issue(
                    code="INVALID_CLAIMS_TYPE",
                    message="权利要求应该是字符串类型",
                    severity="error",
                )
            )

        # 检查3: 结构检查
        total_checks += 1
        has_independent_claim = "1." in str(claims) or claims.startswith("1.")
        has_dependent_claims = any(
            f"{i}." in str(claims) for i in range(2, 10)
        )

        if has_independent_claim:
            passed_checks += 1
        else:
            issues.append(
                self._create_issue(
                    code="NO_INDEPENDENT_CLAIM",
                    message="未找到独立权利要求（权利要求1）",
                    severity="error",
                    suggestion="权利要求应该从独立权利要求开始",
                )
            )

        # 计算分数
        score = self._calculate_score(total_checks, passed_checks, len(issues))

        # 确定状态
        if score < self.criteria.min_score:
            status = VerificationStatus.FAILED
        elif any(issue.severity == "error" for issue in issues):
            status = VerificationStatus.FAILED
        elif any(issue.severity == "warning" for issue in issues):
            status = VerificationStatus.WARNING
        else:
            status = VerificationStatus.PASSED

        return VerificationResult(
            status=status,
            issues=issues,
            score=score,
            details={
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "has_independent_claim": has_independent_claim,
                "has_dependent_claims": has_dependent_claims,
            },
        )


# ========== 验证器工厂 ==========


class VerifierFactory:
    """
    验证器工厂

    根据任务类型创建对应的验证器
    """

    _verifiers: dict[str, type[Verifier]] = {
        "patent_search": PatentSearchVerifier,
        "patent_analyze": PatentAnalysisVerifier,
        "patent_analysis": PatentAnalysisVerifier,
        "claim_draft": ClaimDraftingVerifier,
        "claim_drafting": ClaimDraftingVerifier,
        "patent_classification": PatentAnalysisVerifier,  # 复用分析验证器
    }

    @classmethod
    def register_verifier(cls, action: str, verifier_class: type[Verifier]) -> None:
        """注册验证器"""
        cls._verifiers[action] = verifier_class
        logger.info(f"✅ 注册验证器: {action} -> {verifier_class.__name__}")

    @classmethod
    def create_verifier(
        cls,
        action: str,
        criteria: Optional[VerificationCriteria] = None,
    ) -> Optional[Verifier]:
        """
        创建验证器

        Args:
            action: Agent操作类型
            criteria: 自定义验证标准

        Returns:
            Verifier: 验证器实例，如果不支持则返回None
        """
        verifier_class = cls._verifiers.get(action)
        if verifier_class:
            return verifier_class(criteria)

        logger.warning(f"⚠️ 未找到验证器: {action}")
        return None

    @classmethod
    def get_supported_actions(cls) -> list[str]:
        """获取支持的操作类型列表"""
        return list(cls._verifiers.keys())


# ========== 导出 ==========


__all__ = [
    "VerificationStatus",
    "VerificationIssue",
    "VerificationResult",
    "VerificationCriteria",
    "Verifier",
    "RequiredFieldsVerifier",
    "DataQualityVerifier",
    "PatentSearchVerifier",
    "PatentAnalysisVerifier",
    "ClaimDraftingVerifier",
    "VerifierFactory",
]

