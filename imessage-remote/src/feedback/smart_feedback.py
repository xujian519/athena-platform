"""
智能反馈机制
根据任务复杂度生成适当的反馈摘要
"""

import time
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

from ..core.command_router import ExecutionResult, ExecutionStatus

logger = logging.getLogger(__name__)


class FeedbackMode(Enum):
    """反馈模式"""
    SIMPLE = "simple"       # 极简：仅状态+链接
    STANDARD = "standard"   # 标准：状态+关键数据+链接
    DETAILED = "detailed"   # 详细：完整摘要+数据+链接+建议
    SMART = "smart"         # 智能：根据复杂度自动选择


@dataclass
class FeedbackConfig:
    """反馈配置"""
    mode: FeedbackMode = FeedbackMode.SMART
    summary_max_length: int = 500
    include_file_links: bool = True
    include_suggestions: bool = True
    smart_thresholds: Dict[str, float] = None

    def __post_init__(self):
        if self.smart_thresholds is None:
            self.smart_thresholds = {
                "simple": 30,      # 简单任务：< 30秒
                "standard": 120,   # 标准任务：30-120秒
                "detailed": 300    # 详细任务：> 120秒
            }


class SmartFeedbackGenerator:
    """
    智能反馈生成器

    根据任务复杂度和执行结果生成适当的反馈
    """

    def __init__(self, config: FeedbackConfig):
        """
        初始化反馈生成器

        Args:
            config: 反馈配置
        """
        self.config = config

    def generate(
        self,
        result: ExecutionResult,
        obsidian_file: str = None
    ) -> str:
        """
        生成反馈消息

        Args:
            result: 执行结果
            obsidian_file: Obsidian 文件路径

        Returns:
            格式化的反馈消息
        """
        # 确定反馈模式
        mode = self._determine_mode(result)

        # 根据模式生成反馈
        if mode == FeedbackMode.SIMPLE:
            return self._generate_simple(result, obsidian_file)
        elif mode == FeedbackMode.STANDARD:
            return self._generate_standard(result, obsidian_file)
        elif mode == FeedbackMode.DETAILED:
            return self._generate_detailed(result, obsidian_file)
        else:
            return self._generate_smart(result, obsidian_file)

    def _determine_mode(self, result: ExecutionResult) -> FeedbackMode:
        """
        确定反馈模式

        Args:
            result: 执行结果

        Returns:
            反馈模式
        """
        if self.config.mode != FeedbackMode.SMART:
            return self.config.mode

        # 智能模式：根据任务时长和状态确定
        duration = result.duration

        if duration < self.config.smart_thresholds["simple"]:
            return FeedbackMode.SIMPLE
        elif duration < self.config.smart_thresholds["standard"]:
            return FeedbackMode.STANDARD
        else:
            return FeedbackMode.DETAILED

    def _generate_simple(
        self,
        result: ExecutionResult,
        obsidian_file: str = None
    ) -> str:
        """
        生成极简反馈

        Args:
            result: 执行结果
            obsidian_file: Obsidian 文件路径

        Returns:
            反馈消息
        """
        # 状态图标
        icon = "✅" if result.status == ExecutionStatus.COMPLETED else "❌"

        message = f"{icon} {result.summary}\n"

        # 添加文件链接
        if self.config.include_file_links and obsidian_file:
            message += f"详情：📁 {obsidian_file}"

        return message

    def _generate_standard(
        self,
        result: ExecutionResult,
        obsidian_file: str = None
    ) -> str:
        """
        生成标准反馈

        Args:
            result: 执行结果
            obsidian_file: Obsidian 文件路径

        Returns:
            反馈消息
        """
        # 状态图标
        icon = "✅" if result.status == ExecutionStatus.COMPLETED else "❌"

        message = f"{icon} {result.summary}\n\n"

        # 添加关键数据
        key_data = self._extract_key_data(result.details)
        if key_data:
            message += "📊 关键数据：\n"
            for key, value in key_data.items():
                message += f"- {key}: {value}\n"
            message += "\n"

        # 添加文件链接
        if self.config.include_file_links and obsidian_file:
            message += f"📁 详细报告：{obsidian_file}\n"

        return message

    def _generate_detailed(
        self,
        result: ExecutionResult,
        obsidian_file: str = None
    ) -> str:
        """
        生成详细反馈

        Args:
            result: 执行结果
            obsidian_file: Obsidian 文件路径

        Returns:
            反馈消息
        """
        # 状态图标
        icon = "✅" if result.status == ExecutionStatus.COMPLETED else "❌"

        message = f"{icon} {result.summary}\n\n"

        # 执行摘要
        if result.details:
            message += "📋 执行摘要：\n"
            summary_text = self._generate_execution_summary(result.details)
            message += summary_text + "\n\n"

        # 关键发现
        key_findings = self._extract_key_findings(result.details)
        if key_findings:
            message += "🎯 关键发现：\n"
            for i, finding in enumerate(key_findings[:5], 1):
                message += f"{i}. {finding}\n"
            message += "\n"

        # 文件链接
        if self.config.include_file_links and obsidian_file:
            message += f"📁 详细报告：{obsidian_file}\n"

        # 后续建议
        if self.config.include_suggestions:
            suggestions = self._generate_suggestions(result)
            if suggestions:
                message += "\n💡 后续建议：\n"
                for suggestion in suggestions:
                    message += f"- {suggestion}\n"

        return message

    def _generate_smart(
        self,
        result: ExecutionResult,
        obsidian_file: str = None
    ) -> str:
        """
        生成智能反馈（根据复杂度自动选择）

        Args:
            result: 执行结果
            obsidian_file: Obsidian 文件路径

        Returns:
            反馈消息
        """
        # 智能模式下，根据时长选择合适的详细程度
        duration = result.duration

        if duration < self.config.smart_thresholds["simple"]:
            return self._generate_simple(result, obsidian_file)
        elif duration < self.config.smart_thresholds["standard"]:
            return self._generate_standard(result, obsidian_file)
        else:
            return self._generate_detailed(result, obsidian_file)

    def _extract_key_data(self, details: Dict[str, Any]) -> Dict[str, str]:
        """
        提取关键数据

        Args:
            details: 详细结果

        Returns:
            关键数据字典
        """
        key_data = {}

        # 专利检索
        if "result_count" in details:
            key_data["结果数量"] = f"{details['result_count']} 件"

        # 专利分析
        if "creativity_score" in details:
            key_data["创造性评分"] = f"{details['creativity_score']}/100"

        # 信息查询
        if "name" in details:
            key_data["姓名"] = details["name"]
        if "phone" in details:
            key_data["电话"] = details["phone"]

        # 复杂分析
        if "confidence" in details:
            key_data["置信度"] = f"{details['confidence']}%"

        return key_data

    def _generate_execution_summary(self, details: Dict[str, Any]) -> str:
        """
        生成执行摘要

        Args:
            details: 详细结果

        Returns:
            摘要文本
        """
        # 专利检索
        if "query" in details and "patents" in details:
            query = details["query"]
            count = details.get("result_count", len(details.get("patents", [])))
            return f"完成关键词「{query}」的检索，共找到 {count} 件相关专利。"

        # 专利分析
        if "patent_number" in details and "creativity_score" in details:
            patent = details["patent_number"]
            score = details["creativity_score"]
            return f"完成专利 {patent} 的创造性分析，评分为 {score}/100。"

        # 复杂分析
        if "analysis_result" in details:
            return details["analysis_result"][:200] + "..."

        return "任务执行完成。"

    def _extract_key_findings(self, details: Dict[str, Any]) -> list:
        """
        提取关键发现

        Args:
            details: 详细结果

        Returns:
            关键发现列表
        """
        findings = []

        # 专利分析的创新点
        if "innovation_points" in details:
            findings.extend(details["innovation_points"])

        # 复杂分析的关键发现
        if "key_findings" in details:
            findings.extend(details["key_findings"])

        # 对比专利
        if "comparison_with_prior_art" in details:
            prior_art = details["comparison_with_prior_art"]
            if prior_art:
                findings.append(f"找到 {len(prior_art)} 件对比专利")

        return findings

    def _generate_suggestions(self, result: ExecutionResult) -> list:
        """
        生成后续建议

        Args:
            result: 执行结果

        Returns:
            建议列表
        """
        suggestions = []

        # 根据任务类型生成建议
        details = result.details

        # 专利分析建议
        if "creativity_score" in details:
            score = details["creativity_score"]
            if score < 50:
                suggestions.append("创造性评分较低，建议补充实验数据或技术对比")
            elif score < 70:
                suggestions.append("创造性评分中等，建议强化创新点描述")

        # 专利检索建议
        if "result_count" in details:
            count = details["result_count"]
            if count == 0:
                suggestions.append("未找到相关专利，建议调整检索关键词")
            elif count < 10:
                suggestions.append("相关专利较少，建议扩大检索范围")
            else:
                suggestions.append(f"找到 {count} 件专利，建议进行相关性排序")

        # 复杂分析建议
        if "confidence" in details:
            confidence = details["confidence"]
            if confidence < 70:
                suggestions.append("分析置信度较低，建议补充更多背景信息")

        return suggestions


# 测试代码
def test_smart_feedback():
    """测试智能反馈生成器"""
    from ..core.command_router import ExecutionResult, ExecutionStatus
    from ..core.command_parser import AgentType

    config = FeedbackConfig(mode=FeedbackMode.SMART)
    generator = SmartFeedbackGenerator(config)

    # 测试不同时长的任务
    test_cases = [
        {
            "name": "简单任务",
            "duration": 20,
            "expected_mode": FeedbackMode.SIMPLE
        },
        {
            "name": "标准任务",
            "duration": 60,
            "expected_mode": FeedbackMode.STANDARD
        },
        {
            "name": "详细任务",
            "duration": 200,
            "expected_mode": FeedbackMode.DETAILED
        }
    ]

    for test_case in test_cases:
        result = ExecutionResult(
            task_id=f"test_{test_case['duration']}",
            status=ExecutionStatus.COMPLETED,
            agent=AgentType.XIAONUO,
            summary=f"✅ 专利检索完成",
            details={
                "query": "人工智能",
                "result_count": 23
            },
            obsidian_file=None,
            duration=test_case["duration"]
        )

        feedback = generator.generate(result, "test.md")
        print(f"\n{test_case['name']} ({test_case['duration']}s):")
        print(feedback)
        print("-" * 50)


if __name__ == "__main__":
    test_smart_feedback()
