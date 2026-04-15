#!/usr/bin/env python3
"""
小诺NLP能力分析器
Xiaonuo NLP Capability Analyzer

专业分析小诺的意图识别、工具选择、参数填充、调用闭环、拒绝率与鲁棒性

作者: Athena平台团队
创建时间: 2025-12-18
版本: v1.0.0 "小诺NLP专业分析"
"""

from __future__ import annotations
import asyncio
import hashlib
import logging
import re
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# NLP库
import jieba

from core.logging_config import setup_logging

# 导入小诺组件

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class IntentCategory(Enum):
    """意图分类"""

    TECHNICAL = "technical"  # 技术问题
    EMOTIONAL = "emotional"  # 情感交流
    FAMILY = "family"  # 家庭事务
    LEARNING = "learning"  # 学习成长
    COORDINATION = "coordination"  # 协调管理
    ENTERTAINMENT = "entertainment"  # 娱乐互动
    HEALTH = "health"  # 健康关怀
    WORK = "work"  # 工作协助
    QUERY = "query"  # 查询信息
    COMMAND = "command"  # 指令执行


class ToolCategory(Enum):
    """工具分类"""

    CODE_ANALYSIS = "code_analysis"  # 代码分析
    KNOWLEDGE_GRAPH = "knowledge_graph"  # 知识图谱
    DECISION_ENGINE = "decision_engine"  # 决策引擎
    MICROSERVICE = "microservice"  # 微服务
    EMBEDDING = "embedding"  # 向量嵌入
    CHAT_COMPLETION = "chat_completion"  # 对话完成
    DOCUMENT_PROCESSING = "document_processing"  # 文档处理
    WEB_SEARCH = "web_search"  # 网络搜索
    COORDINATION = "coordination"  # 协调工具
    MONITORING = "infrastructure/infrastructure/monitoring"  # 监控工具


@dataclass
class IntentAnalysis:
    """意图分析结果"""

    text: str
    predicted_intent: IntentCategory
    confidence: float
    processing_time: float
    features: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolSelection:
    """工具选择结果"""

    text: str
    intent: IntentCategory
    selected_tools: list[ToolCategory]
    selection_confidence: float
    processing_time: float


@dataclass
class ArgumentAnalysis:
    """参数分析结果"""

    text: str
    selected_tool: ToolCategory
    extracted_args: dict[str, Any]
    missing_args: list[str]
    invalid_args: list[str]
    validity_score: float
    processing_time: float


@dataclass
class CallAnalysis:
    """调用分析结果"""

    text: str
    intent: IntentCategory
    tool: ToolCategory
    args: dict[str, Any]
    call_success: bool
    response_time: float
    response_quality: float
    error_message: str | None = None


@dataclass
class RobustnessAnalysis:
    """鲁棒性分析结果"""

    text: str
    clarity_score: float
    ambiguity_level: int
    rejection_reason: str | None
    fallback_response: str | None
    recovery_success: bool


class IntentClassifier:
    """意图分类器"""

    def __init__(self):
        self.intent_patterns = {
            IntentCategory.TECHNICAL: [
                r"代码",
                r"程序",
                r"开发",
                r"技术",
                r"bug",
                r"调试",
                r"部署",
                r"优化",
                r"算法",
                r"架构",
                r"数据库",
                r"API",
                r"接口",
            ],
            IntentCategory.EMOTIONAL: [
                r"心情",
                r"感情",
                r"爱",
                r"喜欢",
                r"想念",
                r"担心",
                r"开心",
                r"难过",
                r"生气",
                r"安慰",
                r"陪伴",
                r"温暖",
            ],
            IntentCategory.FAMILY: [
                r"爸爸",
                r"妈妈",
                r"家庭",
                r"家",
                r"姐姐",
                r"弟弟",
                r"妹妹",
                r"家人",
                r"亲情",
                r"团聚",
            ],
            IntentCategory.LEARNING: [
                r"学习",
                r"教我",
                r"学会",
                r"知识",
                r"教育",
                r"培训",
                r"成长",
                r"进步",
                r"提高",
                r"技能",
            ],
            IntentCategory.COORDINATION: [
                r"协调",
                r"管理",
                r"安排",
                r"组织",
                r"计划",
                r"调度",
                r"分配",
                r"协作",
                r"配合",
                r"团队",
            ],
            IntentCategory.ENTERTAINMENT: [
                r"游戏",
                r"玩",
                r"娱乐",
                r"音乐",
                r"电影",
                r"故事",
                r"笑话",
                r"聊天",
                r"互动",
            ],
            IntentCategory.HEALTH: [
                r"健康",
                r"休息",
                r"疲劳",
                r"生病",
                r"照顾",
                r"锻炼",
                r"睡眠",
                r"饮食",
                r"医疗",
            ],
            IntentCategory.WORK: [
                r"工作",
                r"任务",
                r"项目",
                r"会议",
                r"日程",
                r"安排",
                r"效率",
                r"计划",
                r"目标",
                r"进度",
            ],
            IntentCategory.QUERY: [
                r"什么",
                r"为什么",
                r"怎么",
                r"如何",
                r"哪里",
                r"什么时候",
                r"查询",
                r"搜索",
                r"信息",
                r"数据",
            ],
            IntentCategory.COMMAND: [
                r"启动",
                r"停止",
                r"开始",
                r"结束",
                r"执行",
                r"运行",
                r"关闭",
                r"重启",
                r"安装",
                r"卸载",
            ],
        }

        # 意图到工具的映射
        self.intent_tool_mapping = {
            IntentCategory.TECHNICAL: [
                ToolCategory.CODE_ANALYSIS,
                ToolCategory.DOCUMENT_PROCESSING,
            ],
            IntentCategory.EMOTIONAL: [ToolCategory.CHAT_COMPLETION],
            IntentCategory.FAMILY: [ToolCategory.CHAT_COMPLETION, ToolCategory.COORDINATION],
            IntentCategory.LEARNING: [ToolCategory.KNOWLEDGE_GRAPH, ToolCategory.WEB_SEARCH],
            IntentCategory.COORDINATION: [ToolCategory.MICROSERVICE, ToolCategory.MONITORING],
            IntentCategory.ENTERTAINMENT: [ToolCategory.CHAT_COMPLETION],
            IntentCategory.HEALTH: [ToolCategory.CHAT_COMPLETION, ToolCategory.MONITORING],
            IntentCategory.WORK: [ToolCategory.COORDINATION, ToolCategory.DECISION_ENGINE],
            IntentCategory.QUERY: [ToolCategory.WEB_SEARCH, ToolCategory.KNOWLEDGE_GRAPH],
            IntentCategory.COMMAND: [ToolCategory.MICROSERVICE],
        }

    def classify_intent(self, text: str) -> IntentAnalysis:
        """分类意图"""
        start_time = datetime.now()

        # 预处理文本
        clean_text = self._preprocess_text(text)
        words = list(jieba.cut(clean_text))

        # 计算每个意图的匹配度
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 1
            intent_scores[intent] = score

        # 选择最高分意图
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            predicted_intent = best_intent[0]
            confidence = best_intent[1] / len(self.intent_patterns[predicted_intent])
        else:
            predicted_intent = IntentCategory.QUERY
            confidence = 0.5

        processing_time = (datetime.now() - start_time).total_seconds()

        return IntentAnalysis(
            text=text,
            predicted_intent=predicted_intent,
            confidence=confidence,
            processing_time=processing_time,
            features={"words": words, "scores": intent_scores, "text_length": len(text)},
        )

    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 移除特殊字符,保留中文、英文、数字
        text = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)
        # 转换为小写
        text = text.lower()
        # 移除多余空格
        text = re.sub(r"\s+", " ", text).strip()
        return text


class ToolSelector:
    """工具选择器"""

    def __init__(self, intent_classifier: IntentClassifier):
        self.intent_classifier = intent_classifier
        self.tool_requirements = {
            ToolCategory.CODE_ANALYSIS: ["code", "file_path"],
            ToolCategory.KNOWLEDGE_GRAPH: ["query", "domain"],
            ToolCategory.DECISION_ENGINE: ["context", "options"],
            ToolCategory.MICROSERVICE: ["service_name", "action"],
            ToolCategory.EMBEDDING: ["text", "model"],
            ToolCategory.CHAT_COMPLETION: ["prompt"],
            ToolCategory.DOCUMENT_PROCESSING: ["document", "operation"],
            ToolCategory.WEB_SEARCH: ["query"],
            ToolCategory.COORDINATION: ["task", "participants"],
            ToolCategory.MONITORING: ["target", "metrics"],
        }

    def select_tools(self, text: str, intent: IntentCategory | None = None) -> ToolSelection:
        """选择工具"""
        start_time = datetime.now()

        if intent is None:
            intent_analysis = self.intent_classifier.classify_intent(text)
            intent = intent_analysis.predicted_intent

        # 获取意图对应的工具
        available_tools = self.intent_classifier.intent_tool_mapping.get(
            intent, [ToolCategory.CHAT_COMPLETION]
        )

        # 根据文本内容进一步细化工具选择
        refined_tools = []
        for tool in available_tools:
            if self._is_tool_relevant(text, tool):
                refined_tools.append(tool)

        # 如果没有细化工具,使用原始工具
        if not refined_tools:
            refined_tools = available_tools

        # 计算选择置信度
        confidence = len(refined_tools) / len(available_tools) if available_tools else 0.5

        processing_time = (datetime.now() - start_time).total_seconds()

        return ToolSelection(
            text=text,
            intent=intent,
            selected_tools=refined_tools,
            selection_confidence=confidence,
            processing_time=processing_time,
        )

    def _is_tool_relevant(self, text: str, tool: ToolCategory) -> bool:
        """检查工具是否与文本相关"""
        relevance_keywords = {
            ToolCategory.CODE_ANALYSIS: ["代码", "程序", "bug", "调试", "分析"],
            ToolCategory.KNOWLEDGE_GRAPH: ["知识", "图谱", "查询", "信息"],
            ToolCategory.DECISION_ENGINE: ["决策", "选择", "分析", "建议"],
            ToolCategory.MICROSERVICE: ["服务", "微服务", "系统", "调用"],
            ToolCategory.EMBEDDING: ["嵌入", "向量", "相似", "匹配"],
            ToolCategory.CHAT_COMPLETION: ["聊天", "对话", "交流", "回答"],
            ToolCategory.DOCUMENT_PROCESSING: ["文档", "文件", "处理", "分析"],
            ToolCategory.WEB_SEARCH: ["搜索", "查找", "网络", "信息"],
            ToolCategory.COORDINATION: ["协调", "管理", "安排", "组织"],
            ToolCategory.MONITORING: ["监控", "检查", "状态", "性能"],
        }

        keywords = relevance_keywords.get(tool, [])
        return any(keyword in text for keyword in keywords)


class ArgumentExtractor:
    """参数提取器"""

    def __init__(self):
        self.argument_patterns = {
            ToolCategory.CODE_ANALYSIS: {
                "code": [r"```python\s*\n(.*?)\n```", r"代码[::]\s*(.+)", r"function\s+(\w+)"],
                "file_path": [r"文件[::]\s*(.+)", r"路径[::]\s*(.+)"],
                "language": [r"语言[::]\s*(.+)", r"用\s*(.+)\s*写"],
            },
            ToolCategory.KNOWLEDGE_GRAPH: {
                "query": [r"查询[::]\s*(.+)", r"搜索[::]\s*(.+)", r"找\s*(.+)"],
                "domain": [r"领域[::]\s*(.+)", r"关于\s*(.+)"],
                "relation": [r"关系[::]\s*(.+)"],
            },
            ToolCategory.WEB_SEARCH: {
                "query": [r"搜索[::]\s*(.+)", r"查找[::]\s*(.+)", r"找\s*(.+)"],
                "engine": [r"用\s*(.+)\s*搜索", r"引擎[::]\s*(.+)"],
                "limit": [r"前\s*(\d+)", r"最多\s*(\d+)"],
            },
            ToolCategory.CHAT_COMPLETION: {
                "prompt": [r"说[::]\s*(.+)", r"回答[::]\s*(.+)", r"请\s*(.+)"],
                "style": [r"风格[::]\s*(.+)", r"语气[::]\s*(.+)"],
                "length": [r"长[度短]?[::]\s*(.+)"],
            },
        }

    def extract_arguments(self, text: str, tool: ToolCategory) -> ArgumentAnalysis:
        """提取参数"""
        start_time = datetime.now()

        extracted_args = {}
        missing_args = []
        invalid_args = []

        # 获取工具的必需参数
        required_args = self._get_required_args(tool)

        # 提取参数
        patterns = self.argument_patterns.get(tool, {})
        for arg_name, arg_patterns in patterns.items():
            for pattern in arg_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
                if matches:
                    extracted_args[arg_name] = matches[0]
                    break

        # 检查缺失参数
        for required_arg in required_args:
            if required_arg not in extracted_args:
                missing_args.append(required_arg)

        # 验证参数有效性
        for arg_name, arg_value in extracted_args.items():
            if not self._validate_argument(tool, arg_name, arg_value):
                invalid_args.append(arg_name)

        # 计算有效性分数
        total_args = len(required_args)
        valid_args = total_args - len(missing_args) - len(invalid_args)
        validity_score = valid_args / total_args if total_args > 0 else 0

        processing_time = (datetime.now() - start_time).total_seconds()

        return ArgumentAnalysis(
            text=text,
            selected_tool=tool,
            extracted_args=extracted_args,
            missing_args=missing_args,
            invalid_args=invalid_args,
            validity_score=validity_score,
            processing_time=processing_time,
        )

    def _get_required_args(self, tool: ToolCategory) -> list[str]:
        """获取工具的必需参数"""
        required_args_map = {
            ToolCategory.CODE_ANALYSIS: ["code"],
            ToolCategory.KNOWLEDGE_GRAPH: ["query"],
            ToolCategory.DECISION_ENGINE: ["context", "options"],
            ToolCategory.MICROSERVICE: ["service_name"],
            ToolCategory.EMBEDDING: ["text"],
            ToolCategory.CHAT_COMPLETION: ["prompt"],
            ToolCategory.DOCUMENT_PROCESSING: ["document"],
            ToolCategory.WEB_SEARCH: ["query"],
            ToolCategory.COORDINATION: ["task"],
            ToolCategory.MONITORING: ["target"],
        }
        return required_args_map.get(tool, [])

    def _validate_argument(self, tool: ToolCategory, arg_name: str, arg_value: str) -> bool:
        """验证参数有效性"""
        if not arg_value or arg_value.strip() == "":
            return False

        # 特定验证规则
        validation_rules = {
            ToolCategory.CODE_ANALYSIS: {
                "file_path": lambda x: len(x) > 1,
                "language": lambda x: x.lower()
                in ["python", "java", "javascript", "cpp", "go", "rust"],
            },
            ToolCategory.WEB_SEARCH: {"limit": lambda x: x.isdigit() and 1 <= int(x) <= 100},
        }

        if tool in validation_rules and arg_name in validation_rules[tool]:
            return validation_rules[tool][arg_name](arg_value)

        return True


class CallSimulator:
    """调用模拟器"""

    def __init__(self):
        self.tool_implementations = {
            ToolCategory.CODE_ANALYSIS: self._simulate_code_analysis,
            ToolCategory.KNOWLEDGE_GRAPH: self._simulate_knowledge_graph,
            ToolCategory.WEB_SEARCH: self._simulate_web_search,
            ToolCategory.CHAT_COMPLETION: self._simulate_chat_completion,
            ToolCategory.DECISION_ENGINE: self._simulate_decision_engine,
            ToolCategory.MICROSERVICE: self._simulate_microservice,
            ToolCategory.EMBEDDING: self._simulate_embedding,
            ToolCategory.DOCUMENT_PROCESSING: self._simulate_document_processing,
            ToolCategory.COORDINATION: self._simulate_coordination,
            ToolCategory.MONITORING: self._simulate_monitoring,
        }

    async def simulate_call(
        self, intent: IntentCategory, tool: ToolCategory, args: dict[str, Any]
    ) -> CallAnalysis:
        """模拟工具调用"""
        start_time = datetime.now()

        try:
            # 检查参数完整性
            required_args = self._get_required_args(tool)
            for req_arg in required_args:
                if req_arg not in args:
                    return CallAnalysis(
                        text="",
                        intent=intent,
                        tool=tool,
                        args=args,
                        call_success=False,
                        response_time=0,
                        response_quality=0,
                        error_message=f"缺少必需参数: {req_arg}",
                    )

            # 模拟工具调用
            response = await self.tool_implementations[tool](args)
            call_success = True
            response_quality = self._evaluate_response_quality(response)
            error_message = None

        except Exception as e:
            call_success = False
            response = None
            response_quality = 0
            error_message = str(e)

        response_time = (datetime.now() - start_time).total_seconds()

        return CallAnalysis(
            text="",
            intent=intent,
            tool=tool,
            args=args,
            call_success=call_success,
            response_time=response_time,
            response_quality=response_quality,
            error_message=error_message,
        )

    async def _simulate_code_analysis(self, args: dict[str, Any]) -> dict[str, Any]:
        """模拟代码分析"""
        await asyncio.sleep(0.1)  # 模拟处理时间
        return {
            "analysis": "代码结构良好",
            "suggestions": ["优化算法复杂度", "添加注释"],
            "metrics": {"lines": 100, "complexity": "medium"},
        }

    async def _simulate_knowledge_graph(self, args: dict[str, Any]) -> dict[str, Any]:
        """模拟知识图谱查询"""
        await asyncio.sleep(0.05)
        return {
            "nodes": ["实体1", "实体2"],
            "edges": ["关系1"],
            "reports/reports/results": f"知识图谱查询结果: {args.get('query', '')}",
        }

    async def _simulate_web_search(self, args: dict[str, Any]) -> dict[str, Any]:
        """模拟网络搜索"""
        await asyncio.sleep(0.2)
        return {
            "reports/reports/results": [f"搜索结果1: {args.get('query', '')}", "搜索结果2"],
            "total": 2,
        }

    async def _simulate_chat_completion(self, args: dict[str, Any]) -> dict[str, Any]:
        """模拟对话完成"""
        await asyncio.sleep(0.1)
        return {
            "response": f"回答: {args.get('prompt', '')}",
            "model": "xiaonuo-chat",
            "tokens": 50,
        }

    async def _simulate_decision_engine(self, args: dict[str, Any]) -> dict[str, Any]:
        """模拟决策引擎"""
        await asyncio.sleep(0.15)
        return {"decision": "最佳选择: 选项A", "confidence": 0.85, "reasoning": "基于分析得出结论"}

    async def _simulate_microservice(self, args: dict[str, Any]) -> dict[str, Any]:
        """模拟微服务调用"""
        await asyncio.sleep(0.08)
        return {
            "service": args.get("service_name", ""),
            "status": "success",
            "response": "服务调用成功",
        }

    async def _simulate_embedding(self, args: dict[str, Any]) -> dict[str, Any]:
        """模拟向量嵌入"""
        await asyncio.sleep(0.05)
        return {"embedding": [0.1, 0.2, 0.3] * 256, "dimensions": 768}  # 1024维向量(BGE-M3)

    async def _simulate_document_processing(self, args: dict[str, Any]) -> dict[str, Any]:
        """模拟文档处理"""
        await asyncio.sleep(0.12)
        return {
            "extracted_text": f"文档内容: {args.get('document', '')}",
            "metadata": {"pages": 5, "words": 1000},
        }

    async def _simulate_coordination(self, args: dict[str, Any]) -> dict[str, Any]:
        """模拟协调管理"""
        await asyncio.sleep(0.1)
        return {"task": args.get("task", ""), "status": "已安排", "participants": ["小诺", "小娜"]}

    async def _simulate_monitoring(self, args: dict[str, Any]) -> dict[str, Any]:
        """模拟监控检查"""
        await asyncio.sleep(0.03)
        return {
            "target": args.get("target", ""),
            "status": "healthy",
            "metrics": {
                "cpu": 50,
                "modules/modules/memory/modules/memory/modules/memory/memory": 60,
            },
        }

    def _get_required_args(self, tool: ToolCategory) -> list[str]:
        """获取工具必需参数"""
        arg_extractor = ArgumentExtractor()
        return arg_extractor._get_required_args(tool)

    def _evaluate_response_quality(self, response: dict[str, Any]) -> float:
        """评估响应质量"""
        if not response:
            return 0

        # 基础质量评估
        quality_score = 0.5

        # 内容完整性
        if any(key in response for key in ["reports/reports/results", "response", "analysis"]):
            quality_score += 0.3

        # 结构化程度
        if isinstance(response, dict) and len(response) >= 2:
            quality_score += 0.2

        return min(quality_score, 1.0)


class RobustnessAnalyzer:
    """鲁棒性分析器"""

    def __init__(self):
        self.ambiguity_patterns = [
            r"这个",
            r"那个",
            r"它",
            r"什么",
            r"怎么",
            r"为什么",
            r"可能",
            r"也许",
            r"大概",
            r"似乎",
            r"好像",
        ]

        self.rejection_reasons = [
            "不明确的请求",
            "缺少必要信息",
            "超出能力范围",
            "安全问题",
            "格式错误",
            "无法理解",
        ]

    def analyze_robustness(self, text: str) -> RobustnessAnalysis:
        """分析鲁棒性"""

        # 计算清晰度分数
        clarity_score = self._calculate_clarity_score(text)

        # 分析模糊程度
        ambiguity_level = self._analyze_ambiguity(text)

        # 判断是否需要拒绝
        rejection_reason = None
        fallback_response = None
        recovery_success = True

        if clarity_score < 0.3:
            rejection_reason = self._determine_rejection_reason(text)
            fallback_response = self._generate_fallback_response(text)
            recovery_success = len(fallback_response) > 10

        return RobustnessAnalysis(
            text=text,
            clarity_score=clarity_score,
            ambiguity_level=ambiguity_level,
            rejection_reason=rejection_reason,
            fallback_response=fallback_response,
            recovery_success=recovery_success,
        )

    def _calculate_clarity_score(self, text: str) -> float:
        """计算清晰度分数"""
        if not text:
            return 0

        # 基础分数
        score = 0.5

        # 文本长度
        if 10 <= len(text) <= 200:
            score += 0.2

        # 具体性指标
        specific_indicators = ["请", "帮我", "分析", "搜索", "查找", "计算"]
        if any(indicator in text for indicator in specific_indicators):
            score += 0.2

        # 模糊性惩罚
        ambiguity_count = sum(
            1 for pattern in self.ambiguity_patterns if re.search(pattern, text, re.IGNORECASE)
        )
        score -= ambiguity_count * 0.1

        return max(0, min(1, score))

    def _analyze_ambiguity(self, text: str) -> int:
        """分析模糊程度"""
        ambiguity_count = 0

        for pattern in self.ambiguity_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            ambiguity_count += len(matches)

        if ambiguity_count == 0:
            return 0
        elif ambiguity_count <= 2:
            return 1
        elif ambiguity_count <= 4:
            return 2
        else:
            return 3

    def _determine_rejection_reason(self, text: str) -> str:
        """确定拒绝原因"""
        if len(text) < 5:
            return "请求过于简短"
        elif len(text) > 500:
            return "请求过于复杂"
        elif re.search(r"[^\w\s\u4e00-\u9fff.,!?,。!?]", text):
            return "包含非法字符"
        else:
            return "请求不明确"

    def _generate_fallback_response(self, text: str) -> str:
        """生成回退响应"""
        if "代码" in text:
            return "请提供更具体的代码内容和需要分析的问题"
        elif "搜索" in text or "查找" in text:
            return "请告诉我您想搜索什么具体内容"
        elif "帮助" in text:
            return "我很乐意帮助您,请告诉我具体需要什么帮助"
        else:
            return "请提供更详细的信息,让我更好地为您服务"


class XiaonuoNLPAnalyzer:
    """小诺NLP能力分析器"""

    def __init__(self):
        # 优化:延迟初始化和缓存
        self._intent_classifier = None
        self._tool_selector = None
        self._argument_extractor = None
        self._call_simulator = None
        self._robustness_analyzer = None

        # 简单缓存
        self._cache: dict[str, Any] = {}
        self._cache_max_size = 100

        # 存储分析结果
        self.intent_analyses: list[IntentAnalysis] = []
        self.tool_selections: list[ToolSelection] = []
        self.argument_analyses: list[ArgumentAnalysis] = []
        self.call_analyses: list[CallAnalysis] = []
        self.robustness_analyses: list[RobustnessAnalysis] = []

    @property
    def intent_classifier(self) -> Any:
        if self._intent_classifier is None:
            self._intent_classifier = IntentClassifier()
        return self._intent_classifier

    @property
    def tool_selector(self) -> Any:
        if self._tool_selector is None:
            self._tool_selector = ToolSelector(self.intent_classifier)
        return self._tool_selector

    @property
    def argument_extractor(self) -> Any:
        if self._argument_extractor is None:
            self._argument_extractor = ArgumentExtractor()
        return self._argument_extractor

    @property
    def call_simulator(self) -> Any:
        if self._call_simulator is None:
            self._call_simulator = CallSimulator()
        return self._call_simulator

    @property
    def robustness_analyzer(self) -> Any:
        if self._robustness_analyzer is None:
            self._robustness_analyzer = RobustnessAnalyzer()
        return self._robustness_analyzer

    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode("utf-8", usedforsecurity=False), usedforsecurity=False).hexdigest()[:16]

    def _get_from_cache(self, text: str) -> dict[str, Any] | None:
        """从缓存获取结果"""
        cache_key = self._get_cache_key(text)
        return self._cache.get(cache_key)

    def _put_to_cache(self, text: str, result: dict[str, Any]) -> Any:
        """保存到缓存"""
        if len(self._cache) >= self._cache_max_size:
            # 简单的LRU:删除第一个
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        cache_key = self._get_cache_key(text)
        self._cache[cache_key] = result

    async def analyze_capability(self, text: str) -> dict[str, Any]:
        """分析完整NLP能力"""
        try:
            # 优化:检查缓存
            cached_result = self._get_from_cache(text)
            if cached_result:
                return cached_result

            # 意图识别
            intent_analysis = self.intent_classifier.classify_intent(text)
            self.intent_analyses.append(intent_analysis)

            # 工具选择
            tool_selection = self.tool_selector.select_tools(text, intent_analysis.predicted_intent)
            self.tool_selections.append(tool_selection)

            # 参数提取
            if tool_selection.selected_tools:
                # 使用第一个选中的工具
                primary_tool = tool_selection.selected_tools[0]
                argument_analysis = self.argument_extractor.extract_arguments(text, primary_tool)
                self.argument_analyses.append(argument_analysis)

                # 模拟调用
                call_analysis = await self.call_simulator.simulate_call(
                    intent_analysis.predicted_intent, primary_tool, argument_analysis.extracted_args
                )
                self.call_analyses.append(call_analysis)

            # 鲁棒性分析
            robustness_analysis = self.robustness_analyzer.analyze_robustness(text)
            self.robustness_analyses.append(robustness_analysis)

            result = {
                "intent_analysis": intent_analysis,
                "tool_selection": tool_selection,
                "argument_analysis": argument_analysis if tool_selection.selected_tools else None,
                "call_analysis": call_analysis if tool_selection.selected_tools else None,
                "robustness_analysis": robustness_analysis,
            }

            # 优化:保存到缓存
            self._put_to_cache(text, result)

            return result

        except Exception as e:
            logger.error(f"NLP能力分析失败: {e}")
            return {"error": str(e)}

    def calculate_intent_accuracy(self, test_data: list[tuple[str, IntentCategory]]) -> float:
        """计算意图识别准确率"""
        if not test_data or not self.intent_analyses:
            return 0.0

        correct_predictions = 0
        total_predictions = min(len(test_data), len(self.intent_analyses))

        for i in range(total_predictions):
            _text, expected_intent = test_data[i]
            predicted_intent = self.intent_analyses[i].predicted_intent

            if predicted_intent == expected_intent:
                correct_predictions += 1

        return correct_predictions / total_predictions if total_predictions > 0 else 0.0

    def calculate_tool_selection_rate(self, test_data: list[tuple[str, ToolCategory]]) -> float:
        """计算工具选择准确率"""
        if not test_data or not self.tool_selections:
            return 0.0

        correct_selections = 0
        total_selections = min(len(test_data), len(self.tool_selections))

        for i in range(total_selections):
            _text, expected_tool = test_data[i]
            selected_tools = self.tool_selections[i].selected_tools

            if expected_tool in selected_tools:
                correct_selections += 1

        return correct_selections / total_selections if total_selections > 0 else 0.0

    def calculate_argument_validity(self) -> float:
        """计算参数填充有效性"""
        if not self.argument_analyses:
            return 0.0

        validities = [analysis.validity_score for analysis in self.argument_analyses]
        return statistics.mean(validities) if validities else 0.0

    def calculate_end_to_end_success_rate(self) -> float:
        """计算调用闭环成功率"""
        if not self.call_analyses:
            return 0.0

        success_count = sum(1 for analysis in self.call_analyses if analysis.call_success)
        return success_count / len(self.call_analyses)

    def calculate_rejection_robustness(self) -> dict[str, float]:
        """计算拒绝率与鲁棒性"""
        if not self.robustness_analyses:
            return {"rejection_rate": 0.0, "avg_clarity": 0.0, "recovery_success": 0.0}

        rejection_count = sum(
            1 for analysis in self.robustness_analyses if analysis.rejection_reason is not None
        )
        rejection_rate = rejection_count / len(self.robustness_analyses)

        avg_clarity = statistics.mean(
            [analysis.clarity_score for analysis in self.robustness_analyses]
        )

        recovery_count = sum(
            1 for analysis in self.robustness_analyses if analysis.recovery_success
        )
        recovery_success = recovery_count / len(self.robustness_analyses)

        return {
            "rejection_rate": rejection_rate,
            "avg_clarity": avg_clarity,
            "recovery_success": recovery_success,
        }

    def generate_comprehensive_report(self) -> dict[str, Any]:
        """生成综合分析报告"""
        return {
            "analysis_summary": {
                "total_analyses": len(self.intent_analyses),
                "intent_accuracy": self.calculate_intent_accuracy([]),
                "tool_selection_rate": self.calculate_tool_selection_rate([]),
                "argument_validity": self.calculate_argument_validity(),
                "end_to_end_success": self.calculate_end_to_end_success_rate(),
                "rejection_robustness": self.calculate_rejection_robustness(),
            },
            "performance_metrics": {
                "avg_intent_time": (
                    statistics.mean([a.processing_time for a in self.intent_analyses])
                    if self.intent_analyses
                    else 0
                ),
                "avg_tool_selection_time": (
                    statistics.mean([t.processing_time for t in self.tool_selections])
                    if self.tool_selections
                    else 0
                ),
                "avg_argument_time": (
                    statistics.mean([a.processing_time for a in self.argument_analyses])
                    if self.argument_analyses
                    else 0
                ),
                "avg_call_time": (
                    statistics.mean([c.response_time for c in self.call_analyses])
                    if self.call_analyses
                    else 0
                ),
            },
            "intent_distribution": self._get_intent_distribution(),
            "tool_distribution": self._get_tool_distribution(),
            "error_analysis": self._analyze_errors(),
            "recommendations": self._generate_recommendations(),
        }

    def _get_intent_distribution(self) -> dict[str, int]:
        """获取意图分布"""
        distribution = {}
        for analysis in self.intent_analyses:
            intent = analysis.predicted_intent.value
            distribution[intent] = distribution.get(intent, 0) + 1
        return distribution

    def _get_tool_distribution(self) -> dict[str, int]:
        """获取工具分布"""
        distribution = {}
        for selection in self.tool_selections:
            for tool in selection.selected_tools:
                tool_name = tool.value
                distribution[tool_name] = distribution.get(tool_name, 0) + 1
        return distribution

    def _analyze_errors(self) -> dict[str, Any]:
        """分析错误"""
        errors = {
            "intent_errors": 0,
            "tool_selection_errors": 0,
            "argument_errors": 0,
            "call_errors": 0,
            "robustness_issues": 0,
        }

        # 分析意图识别错误(低置信度)
        for analysis in self.intent_analyses:
            if analysis.confidence < 0.5:
                errors["intent_errors"] += 1

        # 分析工具选择错误
        for selection in self.tool_selections:
            if selection.selection_confidence < 0.5:
                errors["tool_selection_errors"] += 1

        # 分析参数错误
        for analysis in self.argument_analyses:
            if analysis.validity_score < 0.5:
                errors["argument_errors"] += 1

        # 分析调用错误
        for analysis in self.call_analyses:
            if not analysis.call_success:
                errors["call_errors"] += 1

        # 分析鲁棒性问题
        for analysis in self.robustness_analyses:
            if analysis.clarity_score < 0.3:
                errors["robustness_issues"] += 1

        return errors

    def _generate_recommendations(self) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 基于分析结果生成建议
        intent_accuracy = self.calculate_intent_accuracy([])
        if intent_accuracy < 0.8:
            recommendations.append("优化意图分类器,增加训练数据和特征工程")

        tool_selection_rate = self.calculate_tool_selection_rate([])
        if tool_selection_rate < 0.8:
            recommendations.append("改进工具选择逻辑,增加上下文理解")

        argument_validity = self.calculate_argument_validity()
        if argument_validity < 0.8:
            recommendations.append("增强参数提取规则,添加更多模式匹配")

        end_to_end_success = self.calculate_end_to_end_success_rate()
        if end_to_end_success < 0.8:
            recommendations.append("改进工具实现,增加错误处理和重试机制")

        robustness_data = self.calculate_rejection_robustness()
        if robustness_data["rejection_rate"] > 0.2:
            recommendations.append("优化用户输入理解,增加交互式澄清机制")

        if not recommendations:
            recommendations.append("当前NLP能力表现良好,继续保持")

        return recommendations


# 便捷函数
async def analyze_xiaonuo_nlp_capability(texts: list[str]) -> dict[str, Any]:
    """分析小诺NLP能力"""
    analyzer = XiaonuoNLPAnalyzer()

    for text in texts:
        await analyzer.analyze_capability(text)

    return analyzer.generate_comprehensive_report()
