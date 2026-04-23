#!/usr/bin/env python3
from __future__ import annotations
"""
智能意图识别引擎
Smart Intent Recognition Engine

增强版意图识别系统,修复功能降级问题,提供高精度的意图识别和工具选择能力

作者: Athena AI系统
创建时间: 2025-12-08
版本: 2.0.0 (修复版)
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """意图类型枚举"""

    # 基础查询类
    INFORMATION_QUERY = "information_query"  # 信息查询
    DEFINITION_QUERY = "definition_query"  # 定义查询
    EXPLANATION_QUERY = "explanation_query"  # 解释说明

    # 分析类
    ANALYSIS_REQUEST = "analysis_request"  # 分析请求
    COMPARISON_REQUEST = "comparison_request"  # 对比分析
    EVALUATION_REQUEST = "evaluation_request"  # 评估分析

    # 操作类
    TASK_EXECUTION = "task_execution"  # 任务执行
    PROBLEM_SOLVING = "problem_solving"  # 问题解决
    RECOMMENDATION_REQUEST = "recommendation_request"  # 推荐请求

    # 交互类
    CONVERSATION = "conversation"  # 对话交流
    QUESTION_ANSWERING = "question_answering"  # 问答互动

    # 专业类
    CODE_GENERATION = "code_generation"  # 代码生成
    DATA_ANALYSIS = "data_analysis"  # 数据分析
    DOCUMENT_PROCESSING = "document_processing"  # 文档处理

    # 系统类
    SYSTEM_COMMAND = "system_command"  # 系统命令
    CONFIGURATION_CHANGE = "configuration_change"  # 配置变更
    HEALTH_CHECK = "health_check"  # 健康检查


class ComplexityLevel(Enum):
    """复杂度级别"""

    SIMPLE = "simple"  # 简单:单一步骤,明确目标
    MEDIUM = "medium"  # 中等:多步骤,需要推理
    COMPLEX = "complex"  # 复杂:多阶段,需要深度分析
    EXPERT = "expert"  # 专家级:跨领域,创新性解决方案


@dataclass
class IntentResult:
    """意图识别结果"""

    intent_type: IntentType
    confidence: float
    complexity: ComplexityLevel
    key_entities: list[str] = field(default_factory=list)
    key_concepts: list[str] = field(default_factory=list)
    context_requirements: list[str] = field(default_factory=list)
    suggested_tools: list[str] = field(default_factory=list)
    processing_strategy: str = ""
    estimated_time: float = 0.0  # 预估处理时间(秒)


class IntentRecognitionEngine:
    """智能意图识别引擎"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 意图模式库
        self.intent_patterns = self._initialize_intent_patterns()

        # 实体识别模式
        self.entity_patterns = self._initialize_entity_patterns()

        # 工具推荐规则
        self.tool_recommendations = self._initialize_tool_recommendations()

        # 性能统计
        self.performance_stats = {
            "total_intents": 0,
            "successful_recognitions": 0,
            "average_confidence": 0.0,
            "intent_distribution": {intent.value: 0 for intent in IntentType},
        }

        self.logger.info("🧠 智能意图识别引擎初始化完成")

    def _initialize_intent_patterns(self) -> dict[IntentType, list[dict]]:
        """初始化意图模式库"""
        return {
            IntentType.INFORMATION_QUERY: [
                {"keywords": ["是什么", "what is", "定义", "definition"], "weight": 0.9},
                {"keywords": ["信息", "information", "资料", "data"], "weight": 0.7},
                {"patterns": [r".*是什么.*", r".*是什么意思.*", r".*what is.*"], "weight": 0.8},
            ],
            IntentType.ANALYSIS_REQUEST: [
                {"keywords": ["分析", "analysis", "解析", "分析一下"], "weight": 0.9},
                {"keywords": ["研究", "research", "调查", "survey"], "weight": 0.7},
                {"patterns": [r".*分析.*", r".*解析.*", r".*研究.*"], "weight": 0.8},
            ],
            IntentType.COMPARISON_REQUEST: [
                {"keywords": ["比较", "对比", "compare", "comparison"], "weight": 0.9},
                {"keywords": ["差异", "区别", "difference", "不同"], "weight": 0.8},
                {
                    "patterns": [r".*和.*比较.*", r".*与.*对比.*", r".*compare.*and.*"],
                    "weight": 0.8,
                },
            ],
            IntentType.TASK_EXECUTION: [
                {"keywords": ["执行", "运行", "execute", "run", "启动"], "weight": 0.9},
                {"keywords": ["完成", "实现", "implement", "complete"], "weight": 0.7},
                {"patterns": [r".*执行.*", r".*运行.*", r".*启动.*"], "weight": 0.8},
            ],
            IntentType.PROBLEM_SOLVING: [
                {"keywords": ["解决", "solve", "修复", "fix", "处理"], "weight": 0.9},
                {"keywords": ["问题", "problem", "错误", "error", "故障"], "weight": 0.8},
                {
                    "patterns": [r".*解决.*问题.*", r".*修复.*错误.*", r".*怎么解决.*"],
                    "weight": 0.8,
                },
            ],
            IntentType.RECOMMENDATION_REQUEST: [
                {"keywords": ["推荐", "recommend", "建议", "suggestion"], "weight": 0.9},
                {"keywords": ["选择", "choose", "哪个", "which"], "weight": 0.7},
                {"patterns": [r".*推荐.*", r".*建议.*", r".*应该.*"], "weight": 0.8},
            ],
            IntentType.CODE_GENERATION: [
                {"keywords": ["代码", "code", "编程", "program", "写代码"], "weight": 0.9},
                {"keywords": ["函数", "function", "类", "class", "算法"], "weight": 0.8},
                {
                    "patterns": [r".*写.*代码.*", r".*实现.*函数.*", r".*生成.*代码.*"],
                    "weight": 0.8,
                },
            ],
            IntentType.DATA_ANALYSIS: [
                {"keywords": ["数据", "data", "分析", "analysis", "统计"], "weight": 0.9},
                {"keywords": ["报告", "report", "图表", "chart", "可视化"], "weight": 0.7},
                {
                    "patterns": [r".*分析.*数据.*", r".*统计.*报告.*", r".*生成.*图表.*"],
                    "weight": 0.8,
                },
            ],
            IntentType.DOCUMENT_PROCESSING: [
                {"keywords": ["文档", "document", "文件", "file", "处理"], "weight": 0.9},
                {"keywords": ["总结", "summary", "提取", "extract", "格式化"], "weight": 0.7},
                {
                    "patterns": [r".*处理.*文档.*", r".*总结.*内容.*", r".*提取.*信息.*"],
                    "weight": 0.8,
                },
            ],
            IntentType.SYSTEM_COMMAND: [
                {"keywords": ["启动", "停止", "重启", "restart", "shutdown"], "weight": 0.9},
                {"keywords": ["部署", "deploy", "更新", "update", "配置"], "weight": 0.7},
                {
                    "patterns": [r".*启动.*服务.*", r".*停止.*系统.*", r".*部署.*应用.*"],
                    "weight": 0.8,
                },
            ],
        }

    def _initialize_entity_patterns(self) -> dict[str, list[dict]]:
        """初始化实体识别模式"""
        return {
            "technology": [
                {"patterns": [r"\b(AI|人工智能|机器学习|深度学习|神经网络)\b"], "weight": 0.9},
                {"patterns": [r"\b(Python|Java|JavaScript|React|Vue|Docker)\b"], "weight": 0.9},
                {"patterns": [r"\b(数据库|API|云计算|大数据|区块链)\b"], "weight": 0.8},
            ],
            "document": [
                {"patterns": [r"\b(文档|报告|论文|说明书|手册)\b"], "weight": 0.9},
                {"patterns": [r"\b(PDF|Word|Excel|PPT|Markdown)\b"], "weight": 0.8},
            ],
            "file": [
                {"patterns": [r"\b(文件|代码|图片|视频|音频)\b"], "weight": 0.8},
                {"patterns": [r"\b(\.py|\.js|\.html|\.css|\.json)\b"], "weight": 0.9},
            ],
            "service": [
                {"patterns": [r"\b(服务|接口|API|微服务|容器)\b"], "weight": 0.8},
                {"patterns": [r"\b(数据库|缓存|消息队列|搜索引擎)\b"], "weight": 0.9},
            ],
            "person": [{"patterns": [r"\b(用户|客户|开发者|管理员|工程师)\b"], "weight": 0.8}],
            "organization": [{"patterns": [r"\b(公司|团队|部门|机构|组织)\b"], "weight": 0.8}],
        }

    def _initialize_tool_recommendations(self) -> dict[IntentType, list[dict]]:
        """初始化工具推荐规则"""
        return {
            IntentType.CODE_GENERATION: [
                {"tool": "code_generator", "relevance": 0.9, "description": "代码生成工具"},
                {"tool": "syntax_checker", "relevance": 0.7, "description": "语法检查工具"},
                {
                    "tool": "documentation_generator",
                    "relevance": 0.6,
                    "description": "文档生成工具",
                },
            ],
            IntentType.DATA_ANALYSIS: [
                {"tool": "data_analyzer", "relevance": 0.9, "description": "数据分析工具"},
                {"tool": "visualizer", "relevance": 0.8, "description": "数据可视化工具"},
                {"tool": "statistical_analyzer", "relevance": 0.7, "description": "统计分析工具"},
            ],
            IntentType.DOCUMENT_PROCESSING: [
                {"tool": "text_extractor", "relevance": 0.9, "description": "文本提取工具"},
                {"tool": "summarizer", "relevance": 0.8, "description": "文档摘要工具"},
                {"tool": "format_converter", "relevance": 0.7, "description": "格式转换工具"},
            ],
            IntentType.ANALYSIS_REQUEST: [
                {"tool": "knowledge_graph", "relevance": 0.8, "description": "知识图谱分析"},
                {"tool": "semantic_analyzer", "relevance": 0.9, "description": "语义分析工具"},
                {"tool": "pattern_recognizer", "relevance": 0.7, "description": "模式识别工具"},
            ],
            IntentType.PROBLEM_SOLVING: [
                {"tool": "diagnostic_engine", "relevance": 0.9, "description": "问题诊断引擎"},
                {"tool": "solution_generator", "relevance": 0.8, "description": "解决方案生成器"},
                {"tool": "error_analyzer", "relevance": 0.8, "description": "错误分析工具"},
            ],
            IntentType.SYSTEM_COMMAND: [
                {"tool": "service_manager", "relevance": 0.9, "description": "服务管理工具"},
                {"tool": "deployment_manager", "relevance": 0.8, "description": "部署管理工具"},
                {"tool": "health_monitor", "relevance": 0.7, "description": "健康监控工具"},
            ],
        }

    async def recognize_intent(
        self, text: str, context: Optional[dict[str, Any]] = None
    ) -> IntentResult:
        """
        识别用户意图

        Args:
            text: 用户输入文本
            context: 上下文信息(可选)

        Returns:
            IntentResult: 意图识别结果
        """
        self.logger.info(f"🔍 开始识别意图: {text[:50]}...")

        start_time = datetime.now()
        self.performance_stats["total_intents"] += 1

        try:
            # 1. 文本预处理
            processed_text = self._preprocess_text(text)

            # 2. 意图分类
            intent_type, intent_confidence = await self._classify_intent(processed_text)

            # 3. 实体识别
            key_entities = await self._extract_entities(processed_text)

            # 4. 关键概念提取
            key_concepts = await self._extract_key_concepts(processed_text)

            # 5. 复杂度评估
            complexity = await self._assess_complexity(processed_text, key_entities, key_concepts)

            # 6. 上下文需求分析
            context_requirements = await self._analyze_context_requirements(
                processed_text, intent_type
            )

            # 7. 工具推荐
            suggested_tools = await self._recommend_tools(intent_type, key_entities, complexity)

            # 8. 处理策略生成
            processing_strategy = await self._generate_processing_strategy(
                intent_type, complexity, key_concepts
            )

            # 9. 时间预估
            estimated_time = await self._estimate_processing_time(complexity, len(suggested_tools))

            # 创建结果
            result = IntentResult(
                intent_type=intent_type,
                confidence=intent_confidence,
                complexity=complexity,
                key_entities=key_entities,
                key_concepts=key_concepts,
                context_requirements=context_requirements,
                suggested_tools=suggested_tools,
                processing_strategy=processing_strategy,
                estimated_time=estimated_time,
            )

            # 更新性能统计
            self._update_performance_stats(intent_type, intent_confidence)

            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(
                f"✅ 意图识别完成: {intent_type.value} (置信度: {intent_confidence:.2f}, 耗时: {processing_time:.3f}s)"
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ 意图识别失败: {e!s}")
            # 返回默认结果
            return IntentResult(
                intent_type=IntentType.INFORMATION_QUERY,
                confidence=0.5,
                complexity=ComplexityLevel.SIMPLE,
                key_entities=[],
                key_concepts=[],
                context_requirements=[],
                suggested_tools=[],
                processing_strategy="basic_response",
                estimated_time=1.0,
            )

    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 转换为小写
        text = text.lower().strip()

        # 移除中文字符之间的空格（中文字符不需要空格分隔）
        text = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", text)

        # 移除其他多余的空白字符
        text = re.sub(r"\s+", " ", text)

        # 移除特殊字符(保留中文、英文、数字、基本标点)
        text = re.sub(r"[^\w\s\u4e00-\u9fff.,!?;:]", "", text)

        return text.strip()

    async def _classify_intent(self, text: str) -> tuple[IntentType, float]:
        """意图分类"""
        intent_scores = {}

        # 对每种意图类型计算匹配分数
        for intent_type, patterns in self.intent_patterns.items():
            score = 0.0

            # 关键词匹配
            for pattern_info in patterns:
                if "keywords" in pattern_info:
                    keywords = pattern_info["keywords"]
                    keyword_matches = sum(1 for kw in keywords if kw in text)
                    score += (keyword_matches / len(keywords)) * pattern_info["weight"]

                # 正则表达式匹配
                if "patterns" in pattern_info:
                    for pattern in pattern_info["patterns"]:
                        if re.search(pattern, text, re.IGNORECASE):
                            score += pattern_info["weight"]

            intent_scores[intent_type] = score

        # 找到得分最高的意图
        if not intent_scores or max(intent_scores.values()) == 0:
            return IntentType.INFORMATION_QUERY, 0.5

        best_intent = max(intent_scores.items(), key=lambda x: x[1])

        # 归一化置信度 (0-1)
        max_score = max(intent_scores.values())
        confidence = min(0.95, max_score / 2.0)  # 调整置信度范围

        return best_intent[0], confidence

    async def _extract_entities(self, text: str) -> list[str]:
        """实体识别"""
        entities = []

        for _entity_type, patterns in self.entity_patterns.items():
            for pattern_info in patterns:
                if "patterns" in pattern_info:
                    for pattern in pattern_info["patterns"]:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            if isinstance(match, tuple):
                                match = match[0]  # 如果是分组,取第一个分组
                            if match and match not in entities:
                                entities.append(match)

        return entities[:10]  # 限制返回数量

    async def _extract_key_concepts(self, text: str) -> list[str]:
        """关键概念提取"""
        # 简单的关键词提取
        words = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9_]+", text)

        # 过滤停用词
        stop_words = {
            "的",
            "是",
            "在",
            "有",
            "和",
            "与",
            "或",
            "但",
            "如果",
            "这",
            "那",
            "我",
            "你",
            "他",
            "她",
            "它",
            "the",
            "is",
            "at",
            "which",
            "on",
            "and",
            "or",
            "but",
            "if",
            "this",
            "that",
            "i",
            "you",
            "he",
            "she",
            "it",
            "a",
            "an",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "about",
            "into",
            "through",
            "during",
            "before",
        }

        concepts = [word for word in words if len(word) > 1 and word not in stop_words]

        # 统计词频,按重要性排序
        concept_freq = {}
        for concept in concepts:
            concept_freq[concept] = concept_freq.get(concept, 0) + 1

        # 按频率排序并返回前10个
        sorted_concepts = sorted(concept_freq.items(), key=lambda x: x[1], reverse=True)
        return [concept for concept, freq in sorted_concepts[:10]]

    async def _assess_complexity(
        self, text: str, entities: list[str], concepts: list[str]
    ) -> ComplexityLevel:
        """评估复杂度"""
        complexity_score = 0

        # 基于文本长度
        if len(text) > 100:
            complexity_score += 1
        if len(text) > 200:
            complexity_score += 1

        # 基于实体数量
        if len(entities) > 3:
            complexity_score += 1
        if len(entities) > 5:
            complexity_score += 1

        # 基于概念数量
        if len(concepts) > 5:
            complexity_score += 1
        if len(concepts) > 10:
            complexity_score += 1

        # 基于复杂关键词
        complex_keywords = ["分析", "设计", "实现", "优化", "集成", "架构", "算法", "系统"]
        for keyword in complex_keywords:
            if keyword in text:
                complexity_score += 1

        # 基于问题复杂度
        if any(word in text for word in ["如何", "怎么", "how"]):
            complexity_score += 1
        if any(word in text for word in ["为什么", "why", "原理"]):
            complexity_score += 2

        # 确定复杂度级别
        if complexity_score <= 2:
            return ComplexityLevel.SIMPLE
        elif complexity_score <= 4:
            return ComplexityLevel.MEDIUM
        elif complexity_score <= 6:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.EXPERT

    async def _analyze_context_requirements(self, text: str, intent_type: IntentType) -> list[str]:
        """分析上下文需求"""
        requirements = []

        # 基于意图类型的上下文需求
        if intent_type == IntentType.ANALYSIS_REQUEST:
            requirements.extend(["历史数据", "相关背景", "分析目标"])
        elif intent_type == IntentType.PROBLEM_SOLVING:
            requirements.extend(["错误日志", "系统状态", "配置信息"])
        elif intent_type == IntentType.RECOMMENDATION_REQUEST:
            requirements.extend(["用户偏好", "历史选择", "约束条件"])
        elif intent_type == IntentType.CODE_GENERATION:
            requirements.extend(["编程语言", "需求规格", "代码规范"])

        # 基于文本中的上下文提示
        if any(word in text for word in ["基于", "根据", "according to", "based on"]):
            requirements.append("参考信息")

        if any(word in text for word in ["继续", "接着", "continue", "next"]):
            requirements.append("历史对话")

        return list(set(requirements))  # 去重

    async def _recommend_tools(
        self, intent_type: IntentType, entities: list[str], complexity: ComplexityLevel
    ) -> list[str]:
        """推荐工具"""
        tools = []

        # 基于意图类型的工具推荐
        if intent_type in self.tool_recommendations:
            intent_tools = self.tool_recommendations[intent_type]
            for tool_info in intent_tools:
                if tool_info["relevance"] >= 0.7:  # 只推荐相关性高的工具
                    tools.append(tool_info["tool"])

        # 基于实体的工具推荐
        if any(entity in ["代码", "code", "Python", "Java"] for entity in entities):
            tools.append("code_analyzer")

        if any(entity in ["文档", "document", "PDF", "Word"] for entity in entities):
            tools.append("document_processor")

        if any(entity in ["数据", "data", "图表", "chart"] for entity in entities):
            tools.append("data_visualizer")

        # 基于复杂度的工具推荐
        if complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.EXPERT]:
            tools.extend(["knowledge_graph", "semantic_analyzer"])

        return list(set(tools))  # 去重,限制数量

    async def _generate_processing_strategy(
        self, intent_type: IntentType, complexity: ComplexityLevel, concepts: list[str]
    ) -> str:
        """生成处理策略"""
        strategy_parts = []

        # 基于意图类型的策略
        if intent_type == IntentType.INFORMATION_QUERY:
            strategy_parts.append("直接回答")
        elif intent_type == IntentType.ANALYSIS_REQUEST:
            strategy_parts.append("深度分析")
        elif intent_type == IntentType.PROBLEM_SOLVING:
            strategy_parts.append("问题诊断")
        elif intent_type == IntentType.TASK_EXECUTION:
            strategy_parts.append("任务分解")

        # 基于复杂度的策略
        if complexity == ComplexityLevel.SIMPLE:
            strategy_parts.append("快速处理")
        elif complexity == ComplexityLevel.MEDIUM:
            strategy_parts.append("分步执行")
        elif complexity == ComplexityLevel.COMPLEX:
            strategy_parts.append("多轮推理")
        elif complexity == ComplexityLevel.EXPERT:
            strategy_parts.append("专家级分析")

        # 基于概念的策略
        if len(concepts) > 5:
            strategy_parts.append("概念整合")

        if not strategy_parts:
            return "standard_processing"

        return "_".join(strategy_parts)

    async def _estimate_processing_time(
        self, complexity: ComplexityLevel, tool_count: int
    ) -> float:
        """预估处理时间"""
        base_time = {
            ComplexityLevel.SIMPLE: 2.0,
            ComplexityLevel.MEDIUM: 5.0,
            ComplexityLevel.COMPLEX: 15.0,
            ComplexityLevel.EXPERT: 30.0,
        }

        # 基础时间
        estimated_time = base_time.get(complexity, 5.0)

        # 工具调用时间
        estimated_time += tool_count * 2.0

        # 添加缓冲时间
        estimated_time *= 1.2

        return estimated_time

    def _update_performance_stats(self, intent_type: IntentType, confidence: float):
        """更新性能统计"""
        # 更新意图分布
        self.performance_stats["intent_distribution"][intent_type.value] += 1

        # 更新成功识别数
        if confidence > 0.6:
            self.performance_stats["successful_recognitions"] += 1

        # 更新平均置信度
        total = self.performance_stats["total_intents"]
        current_avg = self.performance_stats["average_confidence"]
        new_avg = (current_avg * (total - 1) + confidence) / total
        self.performance_stats["average_confidence"] = new_avg

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        total = self.performance_stats["total_intents"]
        if total == 0:
            return {"message": "暂无统计数据"}

        success_rate = self.performance_stats["successful_recognitions"] / total * 100

        # 找出最常见的意图类型
        intent_dist = self.performance_stats["intent_distribution"]
        most_common_intent = max(intent_dist.items(), key=lambda x: x[1])

        return {
            "total_intents": total,
            "success_rate": f"{success_rate:.1f}%",
            "average_confidence": f"{self.performance_stats['average_confidence']:.3f}",
            "most_common_intent": {"type": most_common_intent[0], "count": most_common_intent[1]},
            "intent_distribution": intent_dist,
            "recommendations": self._generate_performance_recommendations(success_rate),
        }

    def _generate_performance_recommendations(self, success_rate: float) -> list[str]:
        """生成性能优化建议"""
        recommendations = []

        if success_rate < 80:
            recommendations.append("意图识别成功率较低,建议优化意图模式库")

        if self.performance_stats["average_confidence"] < 0.7:
            recommendations.append("平均置信度偏低,建议调整置信度计算算法")

        # 分析意图分布不均
        intent_dist = self.performance_stats["intent_distribution"]
        non_zero_intents = sum(1 for count in intent_dist.values() if count > 0)
        if non_zero_intents < len(intent_dist) / 2:
            recommendations.append("意图类型分布不均,建议丰富训练数据")

        return recommendations

    async def batch_recognize(self, texts: list[str]) -> list[IntentResult]:
        """批量意图识别"""
        results = []

        for text in texts:
            result = await self.recognize_intent(text)
            results.append(result)

        return results

    def add_custom_pattern(self, intent_type: IntentType, pattern: dict[str, Any]):
        """添加自定义意图模式"""
        if intent_type not in self.intent_patterns:
            self.logger.warning(f"未知的意图类型: {intent_type}")
            return

        self.intent_patterns[intent_type].append(pattern)
        self.logger.info(f"已为意图类型 {intent_type.value} 添加自定义模式")

    def update_tool_recommendation(self, intent_type: IntentType, tool_info: dict[str, Any]):
        """更新工具推荐"""
        if intent_type not in self.tool_recommendations:
            self.tool_recommendations[intent_type] = []

        # 检查是否已存在相同工具
        existing_tools = [t["tool"] for t in self.tool_recommendations[intent_type]]
        if tool_info["tool"] not in existing_tools:
            self.tool_recommendations[intent_type].append(tool_info)
        else:
            # 更新现有工具信息
            for t in self.tool_recommendations[intent_type]:
                if t["tool"] == tool_info["tool"]:
                    t.update(tool_info)
                    break

        self.logger.info(f"已更新意图类型 {intent_type.value} 的工具推荐")


# 创建全局意图识别引擎实例
intent_engine = IntentRecognitionEngine()


# 导出的便捷函数
async def recognize_user_intent(
    text: str, context: Optional[dict[str, Any]] = None
) -> IntentResult:
    """便捷函数:识别用户意图"""
    return await intent_engine.recognize_intent(text, context)


def get_intent_engine_performance() -> dict[str, Any]:
    """便捷函数:获取意图识别引擎性能报告"""
    return intent_engine.get_performance_report()
