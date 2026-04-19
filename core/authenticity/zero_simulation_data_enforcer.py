#!/usr/bin/env python3
from __future__ import annotations
"""
Athena工作平台 - 零模拟数据执行器
强制执行绝对真实性原则,彻底杜绝模拟数据生成
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class ViolationType(Enum):
    """违规类型"""

    UNVERIFIED_SPECIFICS = "unverified_specifics"
    SPECULATION = "speculation"
    SIMULATED_PATTERNS = "simulated_patterns"
    FALSE_CERTAINTY = "false_certainty"
    SOURCE_UNRELIABLE = "source_unreliable"


class ReliabilityLevel(Enum):
    """信息可靠性等级"""

    GOVERNMENT_OFFICIAL = 5
    OFFICIAL_WEBSITE = 4
    MAINSTREAM_MEDIA = 3
    KNOWN_PLATFORM = 2
    USER_GENERATED = 1
    UNVERIFIED = 0


@dataclass
class AuthenticityCheck:
    """真实性检查结果"""

    passed: bool
    score: float
    violations: list[ViolationType]
    recommendations: list[str]
    details: dict[str, Any]
class ZeroSimulationDataEnforcer:
    """零模拟数据执行器"""

    def __init__(self):
        self.logger = logging.getLogger("ZeroSimulationEnforcer")
        self.violation_patterns = self._initialize_violation_patterns()
        self.forbidden_patterns = self._initialize_forbidden_patterns()

        # 违规记录
        self.violation_log = []
        self.strict_mode = True  # 严格模式,零容忍

    def _initialize_violation_patterns(self) -> dict[str, re.Pattern]:
        """初始化违规模式检测"""
        return {
            "unverified_address": re.compile(
                r"(?:地址|Address)[::]\s*[^,。\n]+?(?:路|街|大道|胡同|里弄|号|栋|楼|室|层)",
                re.IGNORECASE,
            ),
            "unverified_phone": re.compile(
                r"(?:电话|Tel|Phone)[::]\s*(?:1[3-9]\d{9}|0\d{2,3}-?\d{7,8})", re.IGNORECASE
            ),
            "unverified_hours": re.compile(
                r"(?:营业时间|开放时间|Hours)[::]\s*\d{1,2}:\d{2}", re.IGNORECASE
            ),
            "unverified_person": re.compile(
                r"(?:联系人|负责人|经理|店长)[::]\s*[\u4e00-\u9fa5]{2,10}", re.IGNORECASE
            ),
            "speculative_language": re.compile(
                r"(?:可能|也许|大概|估计|或许|应该|通常|一般来说|据推测)", re.IGNORECASE
            ),
            "false_certainty": re.compile(r"(?:确切|准确|肯定|保证|绝对)", re.IGNORECASE),
        }

    def _initialize_forbidden_patterns(self) -> list[str]:
        """初始化禁止模式"""
        return [
            "根据搜索结果",
            "我找到了",
            "信息显示",
            "据了解",
            "资料显示",
            "查询结果",
            "搜索发现",
        ]

    def check_content_authenticity(
        self, content: str, query: str, search_results: list[dict] | None = None
    ) -> AuthenticityCheck:
        """
        检查内容的真实性

        Args:
            content: 待检查的内容
            query: 用户原始查询
            search_results: 搜索结果列表

        Returns:
            AuthenticityCheck: 检查结果
        """
        violations = []
        recommendations = []
        details = {}
        score = 100.0

        # 检查搜索结果是否存在
        if not search_results or len(search_results) == 0:
            if self._contains_specific_information(content):
                violations.append(ViolationType.UNVERIFIED_SPECIFICS)
                recommendations.append("搜索结果为空,不应提供具体信息")
                score -= 50

            if self._contains_speculation(content):
                violations.append(ViolationType.SPECULATION)
                recommendations.append("搜索结果为空,不应进行推测")
                score -= 30

        # 检查具体信息
        specific_info_violations = self._check_specific_information(content)
        violations.extend(specific_info_violations)
        score -= len(specific_info_violations) * 10

        # 检查推测性语言
        speculation_violations = self._check_speculation(content)
        violations.extend(speculation_violations)
        score -= len(speculation_violations) * 5

        # 检查模拟数据模式
        simulation_violations = self._check_simulated_patterns(content)
        violations.extend(simulation_violations)
        score -= len(simulation_violations) * 20

        # 检查虚假确定性
        certainty_violations = self._check_false_certainty(content)
        violations.extend(certainty_violations)
        score -= len(certainty_violations) * 15

        # 生成建议
        if violations:
            recommendations.append("建议重新表述,只提供经过验证的信息")
            recommendations.append("如无法获取可靠信息,应诚实告知用户")

        # 记录详情
        details.update(
            {
                "content_length": len(content),
                "has_search_results": bool(search_results),
                "search_result_count": len(search_results) if search_results else 0,
                "check_time": datetime.now().isoformat(),
                "violation_count": len(violations),
            }
        )

        passed = score >= 85 and len(violations) == 0  # 严格模式:零违规

        return AuthenticityCheck(
            passed=passed,
            score=score,
            violations=violations,
            recommendations=recommendations,
            details=details,
        )

    def _contains_specific_information(self, content: str) -> bool:
        """检查是否包含具体信息"""
        specific_patterns = [
            self.violation_patterns["unverified_address"],
            self.violation_patterns["unverified_phone"],
            self.violation_patterns["unverified_hours"],
            self.violation_patterns["unverified_person"],
        ]

        return any(pattern.search(content) for pattern in specific_patterns)

    def _check_specific_information(self, content: str) -> list[ViolationType]:
        """检查具体信息违规"""
        violations = []

        if self.violation_patterns["unverified_address"].search(content):
            violations.append(ViolationType.UNVERIFIED_SPECIFICS)

        if self.violation_patterns["unverified_phone"].search(content):
            violations.append(ViolationType.UNVERIFIED_SPECIFICS)

        if self.violation_patterns["unverified_hours"].search(content):
            violations.append(ViolationType.UNVERIFIED_SPECIFICS)

        if self.violation_patterns["unverified_person"].search(content):
            violations.append(ViolationType.UNVERIFIED_SPECIFICS)

        return violations

    def _check_speculation(self, content: str) -> list[ViolationType]:
        """检查推测性语言"""
        violations = []

        if self.violation_patterns["speculative_language"].search(content):
            violations.append(ViolationType.SPECULATION)

        return violations

    def _check_simulated_patterns(self, content: str) -> list[ViolationType]:
        """检查模拟数据模式"""
        violations = []

        # 检查是否有未经证实的细节描述
        if self._has_unrealistic_details(content):
            violations.append(ViolationType.SIMULATED_PATTERNS)

        # 检查是否使用了禁止的模式
        for pattern in self.forbidden_patterns:
            if pattern in content:
                violations.append(ViolationType.SIMULATED_PATTERNS)
                break

        return violations

    def _check_false_certainty(self, content: str) -> list[ViolationType]:
        """检查虚假确定性"""
        violations = []

        if self.violation_patterns["false_certainty"].search(content):
            violations.append(ViolationType.FALSE_CERTAINTY)

        return violations

    def _has_unrealistic_details(self, content: str) -> bool:
        """检查是否有不现实的细节"""
        unrealistic_indicators = [
            r"\d{3}[\u4e00-\u9fa5]+店",  # 具体店名
            r"\d+层\d+号",  # 具体门牌号
            r"营业\d+年",  # 营业年限
            r"成立于\d{4}年",  # 成立年份
        ]

        return any(re.search(pattern, content) for pattern in unrealistic_indicators)

    def generate_safe_response(self, query: str, search_results: list[dict] | None = None) -> str:
        """
        生成安全的响应

        Args:
            query: 用户查询
            search_results: 搜索结果

        Returns:
            str: 安全的响应
        """
        if not search_results or len(search_results) == 0:
            return self._generate_no_results_response(query)

        # 检查搜索结果的可靠性
        reliable_results = self._filter_reliable_results(search_results)

        if not reliable_results:
            return self._generate_no_reliable_response(query)

        return self._generate_cautious_response(reliable_results, query)

    def _generate_no_results_response(self, query: str) -> str:
        """生成无结果响应"""
        return f"""
我无法找到关于'{query}'的真实信息。

**搜索方法**:
- 使用了多种搜索工具和关键词组合
- 检查了主要的信息来源

**建议**:
- 请尝试通过官方渠道查询
- 可以联系相关机构获取准确信息
- 检查关键词是否准确

我承诺只提供经过验证的真实信息,在没有可靠来源的情况下,不会进行任何推测。
"""

    def _generate_no_reliable_response(self, query: str) -> str:
        """生成无可靠结果响应"""
        return f"""
我找到了一些关于'{query}'的信息,但这些信息的来源不够可靠,无法确认其真实性。

**发现的问题**:
- 信息来源缺乏权威性
- 内容时效性不明确
- 缺乏多个独立来源的验证

**我的承诺**:
- 不会传播未经证实的信息
- 不会推测可能的答案
- 优先确保信息的真实性

建议您通过更可靠的官方渠道获取准确信息。
"""

    def _generate_cautious_response(self, reliable_results: list[dict], query: str) -> str:
        """生成谨慎响应"""
        response_parts = [f"根据{len(reliable_results)}个可靠来源,关于'{query}'的信息如下:"]

        for i, result in enumerate(reliable_results[:3], 1):
            source = result.get("source", "未知来源")
            content = result.get("content", "")[:200]
            if content:
                response_parts.append(f"\n{i}. 来源:{source}")
                response_parts.append(f"   内容:{content}...")

        response_parts.append("\n\n**注意**:这些信息来自公开渠道,建议通过官方渠道进一步确认。")

        return "".join(response_parts)

    def _filter_reliable_results(self, search_results: list[dict]) -> list[dict]:
        """过滤可靠的搜索结果"""
        reliable = []

        for result in search_results:
            source = result.get("source", "").lower()
            reliability_score = self._assess_reliability(source)

            if reliability_score >= 3:  # 至少主流媒体级别
                result["reliability_score"] = reliability_score
                reliable.append(result)

        return sorted(reliable, key=lambda x: x.get("reliability_score", 0), reverse=True)

    def _assess_reliability(self, source: str) -> int:
        """评估来源可靠性"""
        if any(gov in source for gov in ["gov.cn", "官方", "政府"]):
            return ReliabilityLevel.GOVERNMENT_OFFICIAL.value
        elif any(official in source for official in ["edu.cn", "org"]):
            return ReliabilityLevel.OFFICIAL_WEBSITE.value
        elif any(media in source for media in ["新浪", "腾讯", "网易", "搜狐", "人民网", "新华网"]):
            return ReliabilityLevel.MAINSTREAM_MEDIA.value
        elif any(platform in source for platform in ["百度", "知乎", "微博", "微信公众号"]):
            return ReliabilityLevel.KNOWN_PLATFORM.value
        else:
            return ReliabilityLevel.USER_GENERATED.value

    def log_violation(
        self, check_result: AuthenticityCheck, query: str, original_response: str | None = None
    ):
        """记录违规行为"""
        violation_record = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "violations": [v.value for v in check_result.violations],
            "score": check_result.score,
            "recommendations": check_result.recommendations,
            "original_response_length": len(original_response) if original_response else 0,
            "strict_mode": self.strict_mode,
        }

        self.violation_log.append(violation_record)
        self.logger.warning(f"真实性违规记录: {violation_record}")

    def get_violation_statistics(self) -> dict[str, Any]:
        """获取违规统计"""
        if not self.violation_log:
            return {
                "total_violations": 0,
                "violation_rate": 0.0,
                "most_common_violation": None,
                "average_score": 100.0,
            }

        # 统计违规类型
        violation_counts = {}
        total_violations = 0
        total_score = 0

        for record in self.violation_log:
            violations = record["violations"]
            total_violations += len(violations)
            total_score += record["score"]

            for violation in violations:
                violation_counts[violation] = violation_counts.get(violation, 0) + 1

        most_common = (
            max(violation_counts.items(), key=lambda x: x[1]) if violation_counts else None
        )

        return {
            "total_violations": total_violations,
            "violation_rate": total_violations / len(self.violation_log),
            "most_common_violation": most_common[0] if most_common else None,
            "violation_breakdown": violation_counts,
            "average_score": total_score / len(self.violation_log),
            "strict_mode": self.strict_mode,
        }

    def set_strict_mode(self, strict: bool) -> None:
        """设置严格模式"""
        self.strict_mode = strict
        self.logger.info(f"严格模式设置为: {strict}")


# 使用示例和测试
if __name__ == "__main__":
    # 初始化 logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # 创建执行器
    enforcer = ZeroSimulationDataEnforcer()

    # 测试内容
    test_content = """
    济南曼曼台球俱乐部地址在历城区洪楼附近,电话是12345678901,
    营业时间一般是9:00-24:00。这应该是当地比较知名的台球场所。
    """

    test_query = "济南打台球的曼曼"

    # 执行检查
    check_result = enforcer.check_content_authenticity(test_content, test_query)

    logger.info(f"检查结果: {check_result.passed}")
    logger.info(f"得分: {check_result.score}")
    logger.info(f"违规: {[v.value for v in check_result.violations]}")
    logger.info(f"建议: {check_result.recommendations}")

    # 生成安全响应
    safe_response = enforcer.generate_safe_response(test_query, [])
    logger.info(f"\n安全响应:\n{safe_response}")

    # 显示违规统计
    stats = enforcer.get_violation_statistics()
    logger.info(f"\n违规统计: {stats}")
