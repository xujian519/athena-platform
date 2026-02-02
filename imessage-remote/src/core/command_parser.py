"""
命令解析器
解析自然语言命令，提取任务信息
"""

import re
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型枚举"""
    PATENT_SEARCH = "patent_search"       # 专利检索
    PATENT_ANALYSIS = "patent_analysis"   # 专利分析
    INFO_QUERY = "info_query"             # 信息查询
    COMPLEX_ANALYSIS = "complex_analysis" # 复杂分析
    REMINDER = "reminder"                 # 提醒事项
    UNKNOWN = "unknown"                   # 未知类型


class AgentType(Enum):
    """智能体类型枚举"""
    XIAONUO = "xiaonuo"
    ATHENA = "athena"


@dataclass
class ParsedCommand:
    """解析后的命令数据结构"""
    raw_text: str                # 原始命令文本
    agent: AgentType             # 目标智能体
    task_type: TaskType          # 任务类型
    intent: str                  # 用户意图
    parameters: Dict[str, Any]   # 提取的参数
    confidence: float            # 解析置信度 (0-1)

    # 具体参数（便捷访问）
    query: Optional[str] = None          # 搜索查询
    patent_number: Optional[str] = None  # 专利号
    target_entity: Optional[str] = None  # 目标实体


class CommandParser:
    """
    命令解析器

    将自然语言命令解析为结构化的任务信息
    支持自然语言和语音指令
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化命令解析器

        Args:
            config_path: 命令模式配置文件路径
        """
        self.patterns = self._load_patterns(config_path)
        self._compile_patterns()

    def _load_patterns(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载命令模式配置"""
        # 默认命令模式
        default_patterns = {
            "patent_search": {
                "keywords": ["检索", "搜索", "查找", "search"],
                "patterns": [
                    r"(检索|搜索|查找).*(?:专利|patent)",
                    r"(?:专利|patent).*(?:检索|搜索|查找)",
                    r"search.*patent",
                ],
                "agent": "xiaonuo"
            },
            "patent_analysis": {
                "keywords": ["分析", "评估", "创造性", "analysis"],
                "patterns": [
                    r"(分析|评估).*(?:专利|patent)",
                    r"(?:专利|patent).*(?:分析|评估|创造性)",
                    r"(?:创造性|novelty).*(?:分析|评估)",
                ],
                "agent": "xiaonuo"
            },
            "complex_analysis": {
                "keywords": ["深度", "复杂", "推理"],
                "patterns": [
                    r"@Athena.*(?:分析|研究)",
                    r"(?:深度|复杂).*(?:分析|研究)",
                ],
                "agent": "athena"
            },
            "info_query": {
                "keywords": ["查询", "找", "联系", "query"],
                "patterns": [
                    r"查询.*联系",
                    r"找.*(?:电话|邮箱|联系)",
                    r"(?:电话|邮箱|联系).*(?:多少|是什么)",
                ],
                "agent": "xiaonuo"
            },
            "reminder": {
                "keywords": ["提醒", "记住", "remember"],
                "patterns": [
                    r"提醒.*(?:我|记得)",
                    r"(?:记得|记住).*(?:提醒|通知)",
                ],
                "agent": "xiaonuo"
            }
        }

        # TODO: 从配置文件加载自定义模式
        return default_patterns

    def _compile_patterns(self) -> None:
        """编译正则表达式模式"""
        for task_type, config in self.patterns.items():
            compiled_patterns = []
            for pattern in config.get("patterns", []):
                try:
                    compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
                except re.error as e:
                    logger.warning(f"Failed to compile pattern '{pattern}': {e}")
            config["compiled_patterns"] = compiled_patterns

    def parse(self, command_text: str) -> ParsedCommand:
        """
        解析命令文本

        Args:
            command_text: 原始命令文本

        Returns:
            ParsedCommand 对象
        """
        # 1. 检测目标智能体
        agent = self._detect_agent(command_text)

        # 2. 检测任务类型
        task_type, confidence = self._detect_task_type(command_text, agent)

        # 3. 提取用户意图
        intent = self._extract_intent(command_text, task_type)

        # 4. 提取参数
        parameters = self._extract_parameters(command_text, task_type)

        return ParsedCommand(
            raw_text=command_text,
            agent=agent,
            task_type=task_type,
            intent=intent,
            parameters=parameters,
            confidence=confidence,
            query=parameters.get("query"),
            patent_number=parameters.get("patent_number"),
            target_entity=parameters.get("target_entity")
        )

    def _detect_agent(self, text: str) -> AgentType:
        """
        检测目标智能体

        Args:
            text: 命令文本

        Returns:
            AgentType 枚举
        """
        text_lower = text.lower()

        # 检查明确的智能体指定
        athena_patterns = [
            r"@athena",
            r"@雅典娜",
            r"athena[:\s,]",
            r"雅典娜[:\s,]",
        ]

        xiaonuo_patterns = [
            r"@小诺",
            r"@xiaonuo",
            r"小诺[:\s,]",
            r"xiaonuo[:\s,]",
        ]

        # 检查 Athena 指定
        for pattern in athena_patterns:
            if re.search(pattern, text_lower):
                return AgentType.ATHENA

        # 检查小诺指定
        for pattern in xiaonuo_patterns:
            if re.search(pattern, text_lower):
                return AgentType.XIAONUO

        # 默认使用小诺
        return AgentType.XIAONUO

    def _detect_task_type(
        self,
        text: str,
        agent: AgentType
    ) -> tuple[TaskType, float]:
        """
        检测任务类型

        Args:
            text: 命令文本
            agent: 目标智能体

        Returns:
            (TaskType, confidence) 元组
        """
        text_lower = text.lower()
        best_match = TaskType.UNKNOWN
        best_confidence = 0.0

        # 遍历所有任务类型模式
        for task_type_str, config in self.patterns.items():
            # 跳过与当前智能体不匹配的任务
            if agent == AgentType.XIAONUO and config.get("agent") == "athena":
                continue
            if agent == AgentType.ATHENA and config.get("agent") == "xiaonuo":
                continue

            # 使用编译的模式进行匹配
            for pattern in config.get("compiled_patterns", []):
                match = pattern.search(text_lower)
                if match:
                    # 计算匹配置信度
                    confidence = self._calculate_confidence(match, text_lower)
                    if confidence > best_confidence:
                        best_match = TaskType(task_type_str)
                        best_confidence = confidence

        return best_match, best_confidence

    def _calculate_confidence(self, match: re.Match, text: str) -> float:
        """
        计算匹配置信度

        Args:
            match: 正则匹配对象
            text: 原始文本

        Returns:
            置信度 (0-1)
        """
        base_confidence = 0.7  # 基础置信度

        # 根据匹配长度调整
        match_length = len(match.group(0))
        text_length = len(text)
        length_ratio = match_length / text_length

        # 匹配占比越高，置信度越高
        confidence = base_confidence + (length_ratio * 0.3)

        # 检查是否有明确的关键词
        keywords = ["专利", "patent", "分析", "检索", "查询"]
        keyword_count = sum(1 for kw in keywords if kw in text.lower())
        confidence += min(keyword_count * 0.05, 0.2)

        return min(confidence, 1.0)

    def _extract_intent(self, text: str, task_type: TaskType) -> str:
        """
        提取用户意图

        Args:
            text: 命令文本
            task_type: 任务类型

        Returns:
            意图描述
        """
        # 移除智能体前缀
        text = re.sub(r"[@\w]+[:\s,]", "", text)

        # 根据任务类型提取核心意图
        if task_type == TaskType.PATENT_SEARCH:
            # 提取检索关键词
            match = re.search(r"(?:检索|搜索|查找).*(?:关于|关于)?(.{2,50}?)(?:的专利|$)", text)
            if match:
                return f"检索关于'{match.group(1)}'的专利"
            return "专利检索"

        elif task_type == TaskType.PATENT_ANALYSIS:
            # 提取专利号
            patent_match = re.search(r"(CN\d+|US\d+|EP\d+|WO\d+)", text)
            if patent_match:
                return f"分析专利 {patent_match.group(1)}"
            return "专利分析"

        elif task_type == TaskType.INFO_QUERY:
            # 提取查询对象
            entity_match = re.search(r"(?:查询|找|联系)(.{2,20}?)(?:的|的)", text)
            if entity_match:
                return f"查询{entity_match.group(1)}的联系信息"
            return "信息查询"

        else:
            # 默认返回清理后的文本
            return text.strip()

    def _extract_parameters(
        self,
        text: str,
        task_type: TaskType
    ) -> Dict[str, Any]:
        """
        提取命令参数

        Args:
            text: 命令文本
            task_type: 任务类型

        Returns:
            参数字典
        """
        params = {}

        if task_type == TaskType.PATENT_SEARCH:
            # 提取检索关键词
            match = re.search(r"(?:检索|搜索|查找).*(?:关于|关键词)?(.{2,100}?)(?:的专利|$)", text)
            if match:
                params["query"] = match.group(1).strip()
            else:
                # 如果没有明确关键词，提取整个文本
                params["query"] = text

        elif task_type == TaskType.PATENT_ANALYSIS:
            # 提取专利号
            patent_match = re.search(r"(CN\d+[\dA-Z]*|US\d+|EP\d+[A-Z]*|WO\d+[A-Z]*)", text)
            if patent_match:
                params["patent_number"] = patent_match.group(1)

        elif task_type == TaskType.INFO_QUERY:
            # 提取查询对象
            entity_match = re.search(r"(?:查询|找)(.{2,20}?)(?:的|的电话|的邮箱|的联系)", text)
            if entity_match:
                params["target_entity"] = entity_match.group(1).strip()

        elif task_type == TaskType.COMPLEX_ANALYSIS:
            # 提取分析主题
            match = re.search(r"(?:分析|研究|分析)(.{2,100}?)", text)
            if match:
                params["query"] = match.group(1).strip()

        return params


# 测试代码
async def test_command_parser():
    """测试命令解析器"""
    parser = CommandParser()

    test_commands = [
        "小诺，帮我检索关于人工智能的专利",
        "@Athena 分析这个专利的创造性：CN202310123456.7",
        "查询曹新乐的联系信息",
        "小诺，搜索量子计算相关的专利",
        "找傅玉秀的电话",
    ]

    for cmd in test_commands:
        parsed = parser.parse(cmd)
        print(f"\n原始命令: {parsed.raw_text}")
        print(f"智能体: {parsed.agent.value}")
        print(f"任务类型: {parsed.task_type.value}")
        print(f"意图: {parsed.intent}")
        print(f"参数: {parsed.parameters}")
        print(f"置信度: {parsed.confidence:.2f}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_command_parser())
