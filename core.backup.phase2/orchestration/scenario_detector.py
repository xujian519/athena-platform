"""
场景识别器

根据用户输入自动识别业务场景，并返回需要的智能体组合。
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)


class Scenario(Enum):
    """业务场景枚举"""
    PATENT_SEARCH = "patent_search"           # 专利检索
    PATENT_ANALYSIS = "patent_analysis"       # 专利分析
    CREATIVITY_ANALYSIS = "creativity_analysis"  # 创造性分析
    PATENT_WRITING = "patent_writing"         # 专利撰写
    OFFICE_ACTION_RESPONSE = "office_action_response"  # 审查意见答复
    INVALIDATION = "invalidation"             # 无效宣告
    TRANSLATION = "translation"               # 翻译
    UNKNOWN = "unknown"                       # 未知场景


@dataclass
class ScenarioConfig:
    """场景配置"""
    scenario: Scenario                         # 场景类型
    name: str                                  # 场景名称
    description: str                           # 场景描述
    keywords: List[str]                        # 关键词列表
    required_agents: List[str]                 # 需要的智能体
    optional_agents: List[str]                 # 可选的智能体
    execution_mode: str                        # 执行模式（sequential/parallel/iterative）


class ScenarioDetector:
    """
    场景识别器

    通过关键词匹配和语义分析识别用户意图。
    """

    def __init__(self):
        # 场景配置
        self.scenarios: Dict[Scenario, ScenarioConfig] = {
            Scenario.PATENT_SEARCH: ScenarioConfig(
                scenario=Scenario.PATENT_SEARCH,
                name="专利检索",
                description="检索相关专利文献",
                keywords=["检索", "搜索", "查询", "找", "相关专利", "现有技术"],
                required_agents=["xiaona_retriever"],
                optional_agents=[],
                execution_mode="sequential"
            ),

            Scenario.PATENT_ANALYSIS: ScenarioConfig(
                scenario=Scenario.PATENT_ANALYSIS,
                name="专利分析",
                description="分析专利技术特征和法律状态",
                keywords=["分析", "评估", "对比", "技术方案", "权利要求"],
                required_agents=["xiaona_retriever", "xiaona_analyzer"],
                optional_agents=["xiaona_planner"],
                execution_mode="sequential"
            ),

            Scenario.CREATIVITY_ANALYSIS: ScenarioConfig(
                scenario=Scenario.CREATIVITY_ANALYSIS,
                name="创造性分析",
                description="分析专利的创造性高度",
                keywords=["创造性", "新颖性", "显而易见", "区别特征", "技术启示"],
                required_agents=["xiaona_planner", "xiaona_retriever", "xiaona_analyzer", "xiaona_rule"],
                optional_agents=[],
                execution_mode="sequential"
            ),

            Scenario.PATENT_WRITING: ScenarioConfig(
                scenario=Scenario.PATENT_WRITING,
                name="专利撰写",
                description="撰写专利申请文件",
                keywords=["撰写", "写", "起草", "权利要求书", "说明书", "交底书"],
                required_agents=["xiaona_planner", "xiaona_retriever", "xiaona_analyzer",
                               "xiaona_rule", "xiaona_writer", "xiaona_polisher"],
                optional_agents=[],
                execution_mode="hybrid"  # 并行+串行混合
            ),

            Scenario.OFFICE_ACTION_RESPONSE: ScenarioConfig(
                scenario=Scenario.OFFICE_ACTION_RESPONSE,
                name="审查意见答复",
                description="答复审查意见",
                keywords=["审查意见", "答复", "意见陈述", "驳回", "补正"],
                required_agents=["xiaona_planner", "xiaona_retriever", "xiaona_analyzer",
                               "xiaona_rule", "xiaona_writer"],
                optional_agents=["xiaona_polisher"],
                execution_mode="sequential"
            ),

            Scenario.INVALIDATION: ScenarioConfig(
                scenario=Scenario.INVALIDATION,
                name="无效宣告",
                description="无效宣告请求或答辩",
                keywords=["无效", "无效宣告", "请求书", "答辩", "专利权无效"],
                required_agents=["xiaona_planner", "xiaona_retriever", "xiaona_analyzer",
                               "xiaona_rule", "xiaona_writer", "xiaona_polisher"],
                optional_agents=[],
                execution_mode="sequential"
            ),

            Scenario.TRANSLATION: ScenarioConfig(
                scenario=Scenario.TRANSLATION,
                name="专利翻译",
                description="专利文献翻译",
                keywords=["翻译", "英文", "English", "译文"],
                required_agents=["xiaona_translator"],
                optional_agents=["xiaona_polisher"],
                execution_mode="sequential"
            ),
        }

        self.logger = logging.getLogger(__name__)

    def detect(self, user_input: str) -> Scenario:
        """
        识别业务场景

        Args:
            user_input: 用户输入

        Returns:
            识别的场景
        """
        if not user_input:
            return Scenario.UNKNOWN

        # 关键词匹配
        scores = {}
        for scenario, config in self.scenarios.items():
            score = 0
            for keyword in config.keywords:
                if keyword in user_input:
                    score += 1
            if score > 0:
                scores[scenario] = score

        # 返回得分最高的场景
        if scores:
            detected_scenario = max(scores, key=scores.get)
            self.logger.info(
                f"场景识别: {detected_scenario.value} "
                f"(匹配关键词数: {scores[detected_scenario]})"
            )
            return detected_scenario

        return Scenario.UNKNOWN

    def get_required_agents(self, scenario: Scenario) -> List[str]:
        """
        获取场景需要的智能体

        Args:
            scenario: 场景类型

        Returns:
            智能体ID列表
        """
        config = self.scenarios.get(scenario)
        if config:
            return config.required_agents.copy()
        return []

    def get_optional_agents(self, scenario: Scenario) -> List[str]:
        """
        获取场景可选的智能体

        Args:
            scenario: 场景类型

        Returns:
            智能体ID列表
        """
        config = self.scenarios.get(scenario)
        if config:
            return config.optional_agents.copy()
        return []

    def get_execution_mode(self, scenario: Scenario) -> str:
        """
        获取场景的执行模式

        Args:
            scenario: 场景类型

        Returns:
            执行模式（sequential/parallel/iterative/hybrid）
        """
        config = self.scenarios.get(scenario)
        if config:
            return config.execution_mode
        return "sequential"

    def get_scenario_config(self, scenario: Scenario) -> Optional[ScenarioConfig]:
        """
        获取场景配置

        Args:
            scenario: 场景类型

        Returns:
            场景配置，如果不存在返回None
        """
        return self.scenarios.get(scenario)

    def list_all_scenarios(self) -> List[ScenarioConfig]:
        """
        列出所有场景

        Returns:
            场景配置列表
        """
        return list(self.scenarios.values())
