#!/usr/bin/env python3
from __future__ import annotations
"""
增强意图识别引擎 - 第一阶段优化版本(重构版)
Enhanced Intent Recognition Engine - Phase 1 Optimization (Refactored)

优化内容:
1. 扩展关键词库覆盖常见场景 (+3-4%)
2. 增加语义相似度匹配
3. 优化权重计算算法
4. 增强上下文感知

作者: Athena AI系统
创建时间: 2025-12-23
版本: 2.0.0 "重构为继承体系"
"""

import asyncio
import logging
import re
from collections import defaultdict
from datetime import datetime
from typing import Any

from core.intent.base_engine import (
    BaseIntentEngine,
    ComplexityLevel,
    IntentCategory,
    IntentResult,
    IntentType,
    infer_category_from_intent,
)

logger = logging.getLogger(__name__)


class EnhancedIntentRecognitionEngine(BaseIntentEngine):
    """
    增强意图识别引擎 - 第一阶段优化版(重构版)

    继承自BaseIntentEngine,实现关键词+模式+语义的混合匹配。
    """

    # 类级别配置
    engine_name = "enhanced_keyword_engine"
    engine_version = "2.0.0"
    supported_intents = {
        IntentType.INFORMATION_QUERY,
        IntentType.DEFINITION_QUERY,
        IntentType.EXPLANATION_QUERY,
        IntentType.ANALYSIS_REQUEST,
        IntentType.COMPARISON_REQUEST,
        IntentType.EVALUATION_REQUEST,
        IntentType.TASK_EXECUTION,
        IntentType.PROBLEM_SOLVING,
        IntentType.RECOMMENDATION_REQUEST,
        IntentType.CODE_GENERATION,
        IntentType.DATA_ANALYSIS,
        IntentType.DOCUMENT_PROCESSING,
        IntentType.PATENT_SEARCH,
        IntentType.OPINION_RESPONSE,
        IntentType.PATENT_DRAFTING,
        IntentType.INFRINGEMENT_ANALYSIS,
        IntentType.CREATIVE_WRITING,
        IntentType.SYSTEM_COMMAND,
        IntentType.CONFIGURATION_CHANGE,
        IntentType.HEALTH_CHECK,
        IntentType.SYSTEM_MONITORING,
        IntentType.TECHNICAL_EVALUATION,
        IntentType.CONVERSATION,
        IntentType.QUESTION_ANSWERING,
        IntentType.GENERAL_CHAT,
        IntentType.UNKNOWN,
    }

    def __init__(self, config: dict | None = None):
        """初始化引擎"""
        super().__init__(config)

        # 扩展的意图模式库
        self.intent_patterns = self._initialize_enhanced_patterns()

        # 语义相似度缓存
        self.semantic_cache = {}

        # 用户历史记录(用于上下文感知)
        self.user_history = defaultdict(list)

        self.logger.info("🧠 增强意图识别引擎初始化完成 (v2.0.0)")

    def _initialize(self) -> None:
        """初始化引擎(由BaseIntentEngine调用)"""
        # 模式库已在__init__中初始化
        pass

    def recognize_intent(self, text: str, context: dict | None = None) -> IntentResult:
        """
        识别意图(同步版本)

        Args:
            text: 输入文本
            context: 上下文信息

        Returns:
            意图识别结果
        """
        # 验证输入
        self._validate_input(text)

        # 预处理
        text_normalized = self._normalize_text(text)

        # 1. 关键词匹配
        keyword_scores = self._keyword_matching(text_normalized)

        # 2. 模式匹配
        pattern_scores = self._pattern_matching(text_normalized)

        # 3. 语义相似度计算(简化版)
        semantic_scores = self._semantic_similarity(text_normalized)

        # 4. 上下文增强
        context_boost = self._context_analysis(text_normalized, context, None)

        # 5. 综合评分
        final_scores = self._combine_scores(
            keyword_scores, pattern_scores, semantic_scores, context_boost
        )

        # 6. 选择最佳意图
        best_intent, confidence = self._select_best_intent(final_scores)

        # 7. 确定复杂度
        complexity = self._determine_complexity(text_normalized, best_intent)

        # 8. 推断类别
        category = infer_category_from_intent(best_intent)

        # 9. 提取实体和概念
        entities = self._extract_entities(text_normalized)
        key_concepts = self._extract_key_concepts(text_normalized)

        # 10. 计算处理时间
        processing_time = self._estimate_processing_time(text_normalized, complexity)

        # 11. 更新统计
        self._update_stats(success=True, processing_time_ms=processing_time, cache_hit=False)

        # 12. 返回结果
        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            category=category,
            raw_text=text,
            processing_time_ms=processing_time,
            model_version=self.engine_version,
            entities=entities,
            key_concepts=key_concepts,
            complexity=complexity,
            semantic_similarity=semantic_scores.get(best_intent, 0.0),
            suggested_tools=self._get_suggested_tools(best_intent),
            processing_strategy=self._get_processing_strategy(best_intent),
            estimated_time=self._estimate_time(complexity),
            metadata={},
        )

    async def recognize_intent_async(
        self, text: str, context: dict[str, Any] | None = None, user_id: str | None = None
    ) -> IntentResult:
        """
        异步识别意图

        Args:
            text: 用户输入文本
            context: 上下文信息
            user_id: 用户ID(用于历史记录)

        Returns:
            意图识别结果
        """
        return await self._recognize_intent_async(text, context, user_id)

    async def _recognize_intent_async(
        self, text: str, context: dict[str, Any] | None = None, user_id: str | None = None
    ) -> IntentResult:
        """内部异步识别方法"""
        start_time = datetime.now()
        self._stats.total_requests += 1

        try:
            # 预处理
            text_normalized = self._normalize_text(text)

            # 1. 关键词匹配
            keyword_scores = self._keyword_matching(text_normalized)

            # 2. 模式匹配
            pattern_scores = self._pattern_matching(text_normalized)

            # 3. 语义相似度计算(简化版)
            semantic_scores = self._semantic_similarity(text_normalized)

            # 4. 上下文增强
            context_boost = self._context_analysis(text_normalized, context, user_id)

            # 5. 综合评分
            final_scores = self._combine_scores(
                keyword_scores, pattern_scores, semantic_scores, context_boost
            )

            # 6. 选择最佳意图
            best_intent, confidence = self._select_best_intent(final_scores)

            # 7. 确定复杂度
            complexity = self._determine_complexity(text_normalized, best_intent)

            # 8. 提取关键信息
            key_entities = self._extract_entities(text_normalized)
            key_concepts = self._extract_concepts(text_normalized)

            # 9. 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # 10. 推断类别
            category = infer_category_from_intent(best_intent)

            # 11. 更新统计(使用基类方法签名)
            self._update_stats(success=True, processing_time_ms=processing_time, cache_hit=False)

            # 12. 更新用户历史
            if user_id:
                self.user_history[user_id].append(
                    {
                        "timestamp": datetime.now(),
                        "text": text,
                        "intent": best_intent,
                        "confidence": confidence,
                    }
                )

            result = IntentResult(
                intent=best_intent,
                confidence=confidence,
                category=category,
                raw_text=text,
                processing_time_ms=processing_time,
                model_version=self.engine_version,
                complexity=complexity,
                entities=key_entities,
                key_concepts=key_concepts,
                semantic_similarity=semantic_scores.get(best_intent, 0.0),
                estimated_time=self._estimate_time(complexity),
            )

            self.logger.info(
                f"✅ 意图识别: {best_intent.value} (置信度: {confidence:.3f}, "
                f"耗时: {processing_time:.1f}ms)"
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ 意图识别失败: {e}")
            return self._create_fallback_result(text, str(e))

    def _create_fallback_result(self, text: str, error_msg: str) -> IntentResult:
        """创建回退结果"""
        return IntentResult(
            intent=IntentType.CONVERSATION,
            confidence=0.5,
            category=IntentCategory.GENERAL,
            raw_text=text,
            processing_time_ms=0.0,
            model_version=self.engine_version,
            complexity=ComplexityLevel.SIMPLE,
            metadata={"error": error_msg},
        )

    # ==================== 意图模式库 ====================

    def _initialize_enhanced_patterns(self) -> dict[IntentType, list[dict]]:
        """初始化增强的意图模式库"""

        return {
            # 基础查询类
            IntentType.INFORMATION_QUERY: [
                {
                    "keywords": ["是什么", "what is", "定义", "definition", "什么是", "啥是"],
                    "weight": 1.0,
                },
                {
                    "keywords": ["信息", "information", "资料", "data", "资料", "情报"],
                    "weight": 0.9,
                },
                {
                    "keywords": ["告诉我", "请问", "想了解", "想问", "知道", "了解", "介绍一下"],
                    "weight": 0.85,
                },
                {
                    "keywords": ["解释", "说明", "阐述", "描述", "解释一下", "说明一下"],
                    "weight": 0.8,
                },
                {
                    "patterns": [r".*是什么.*", r".*是什么意思.*", r".*what is.*", r".*怎么理解.*"],
                    "weight": 0.85,
                },
            ],
            IntentType.DEFINITION_QUERY: [
                {
                    "keywords": ["定义", "definition", "概念", "concept", "含义", "意义"],
                    "weight": 1.0,
                },
                {"keywords": ["术语", "名词", "专业术语", "技术术语", "行业术语"], "weight": 0.9},
                {"keywords": ["标准定义", "官方定义", "学术定义", "权威定义"], "weight": 0.8},
                {"keywords": ["解释一下", "说明白", "讲清楚"], "weight": 0.75},
            ],
            IntentType.EXPLANATION_QUERY: [
                {"keywords": ["为什么", "why", "如何", "how", "怎么", "怎样"], "weight": 1.0},
                {"keywords": ["原理", "机制", "工作原理", "运作机制", "底层原理"], "weight": 0.9},
                {"keywords": ["详细说明", "详细解释", "深入解释", "深度解析"], "weight": 0.85},
                {"keywords": ["原因", "理由", "根据", "依据", "缘由"], "weight": 0.8},
                {"keywords": ["过程", "流程", "步骤", "方法", "方式"], "weight": 0.75},
            ],
            # 分析类
            IntentType.ANALYSIS_REQUEST: [
                {"keywords": ["分析", "analysis", "解析", "分析一下", "analyze"], "weight": 1.0},
                {"keywords": ["研究", "research", "调查", "survey", "研究一下"], "weight": 0.9},
                {
                    "keywords": ["深度分析", "深入分析", "全面分析", "综合分析", "多角度分析"],
                    "weight": 0.85,
                },
                {"keywords": ["剖析", "拆解", "解构", "探索", "探讨"], "weight": 0.8},
                {
                    "patterns": [r".*分析.*", r".*解析.*", r".*研究.*", r".*深度.*分析.*"],
                    "weight": 0.9,
                },
            ],
            IntentType.COMPARISON_REQUEST: [
                {"keywords": ["比较", "对比", "compare", "comparison", "比较一下"], "weight": 1.0},
                {"keywords": ["差异", "区别", "difference", "不同", "不同点"], "weight": 0.95},
                {
                    "keywords": ["优缺点", "优势劣势", "优劣", "对比分析", "横向对比"],
                    "weight": 0.85,
                },
                {"keywords": ["哪个好", "哪个更好", "选择哪个", "推荐哪个"], "weight": 0.8},
                {
                    "patterns": [
                        r".*和.*比较.*",
                        r".*与.*对比.*",
                        r".*compare.*and.*",
                        r".*哪个.*好.*",
                    ],
                    "weight": 0.9,
                },
            ],
            IntentType.EVALUATION_REQUEST: [
                {"keywords": ["评估", "evaluation", "评价", "评价一下", "assess"], "weight": 1.0},
                {"keywords": ["判断", "判定", "鉴定", "审定", "审核"], "weight": 0.85},
                {"keywords": ["效果如何", "表现如何", "性能如何", "质量如何"], "weight": 0.8},
                {"keywords": ["可行性", "有效性", "可靠性", "适用性"], "weight": 0.75},
            ],
            # 操作类
            IntentType.TASK_EXECUTION: [
                {"keywords": ["执行", "运行", "execute", "run", "启动"], "weight": 1.0},
                {"keywords": ["完成", "实现", "implement", "complete", "完成一下"], "weight": 0.9},
                {"keywords": ["帮我", "请帮我", "麻烦你", "帮我处理", "帮我弄"], "weight": 0.70},
                {"keywords": ["操作", "处理", "执行任务", "完成任务", "开始执行"], "weight": 0.8},
                {"patterns": [r".*执行.*", r".*运行.*", r".*启动.*"], "weight": 0.9},
                # 负面模式:排除包含领域特定关键词的查询
                {
                    "negative_keywords": [
                        "检索",
                        "搜索",
                        "查",
                        "专利",
                        "写代码",
                        "生成代码",
                        "分析",
                        "答复",
                        "侵权",
                        "起草",
                        "翻译",
                    ],
                    "weight": -0.5,
                },
            ],
            IntentType.PROBLEM_SOLVING: [
                {"keywords": ["解决", "solve", "修复", "fix", "处理"], "weight": 1.0},
                {"keywords": ["问题", "problem", "错误", "error", "故障", "bug"], "weight": 0.95},
                {"keywords": ["报错", "异常", "失败", "崩溃", "卡死", "死机"], "weight": 0.9},
                {
                    "keywords": ["怎么解决", "如何解决", "解决办法", "解决方案", "修复方法"],
                    "weight": 0.85,
                },
                {"keywords": ["排查", "调试", "debug", "故障排查", "问题诊断"], "weight": 0.8},
                {
                    "patterns": [
                        r".*解决.*问题.*",
                        r".*修复.*错误.*",
                        r".*怎么解决.*",
                        r".*无法.*",
                    ],
                    "weight": 0.9,
                },
            ],
            IntentType.RECOMMENDATION_REQUEST: [
                {
                    "keywords": ["推荐", "recommend", "建议", "suggestion", "推荐一下"],
                    "weight": 1.0,
                },
                {"keywords": ["选择", "choose", "哪个", "which", "选哪个"], "weight": 0.9},
                {"keywords": ["最好的", "最佳", "首选", "第一选择", "首选推荐"], "weight": 0.85},
                {"keywords": ["建议使用", "推荐使用", "应该选", "适合"], "weight": 0.8},
                {"patterns": [r".*推荐.*", r".*建议.*", r".*应该.*", r".*最好的.*"], "weight": 0.9},
            ],
            # 专业类
            IntentType.CODE_GENERATION: [
                {
                    "keywords": ["代码", "code", "编程", "program", "写代码", "代码生成"],
                    "weight": 1.0,
                },
                {"keywords": ["函数", "function", "类", "class", "算法"], "weight": 0.9},
                {"keywords": ["Python", "Java", "JavaScript", "C++", "Go", "Rust"], "weight": 0.9},
                {"keywords": ["帮我写", "生成代码", "实现", "写个", "开发"], "weight": 0.85},
                {
                    "patterns": [r".*写.*代码.*", r".*实现.*函数.*", r".*生成.*代码.*"],
                    "weight": 0.95,
                },
                {
                    "negative_keywords": [
                        "故事",
                        "小说",
                        "诗歌",
                        "文案",
                        "剧本",
                        "文章内容",
                        "创意内容",
                    ],
                    "weight": -0.6,
                },
            ],
            IntentType.DATA_ANALYSIS: [
                {"keywords": ["数据", "data", "分析", "analysis", "统计"], "weight": 1.0},
                {"keywords": ["报告", "report", "图表", "chart", "可视化"], "weight": 0.9},
                {"keywords": ["统计报告", "分析报告", "数据报告", "统计图表"], "weight": 0.85},
                {"keywords": ["趋势分析", "相关性", "数据挖掘", "机器学习"], "weight": 0.8},
                {"keywords": ["生成图表", "生成统计", "生成报表", "生成可视化"], "weight": 0.95},
                {
                    "negative_keywords": ["故事", "小说", "诗歌", "文案", "剧本", "创作文学"],
                    "weight": -0.5,
                },
            ],
            IntentType.DOCUMENT_PROCESSING: [
                {"keywords": ["文档", "document", "文件", "file", "处理"], "weight": 1.0},
                {"keywords": ["总结", "summary", "提取", "extract", "格式化"], "weight": 0.9},
                {"keywords": ["摘要", "概括", "归纳", "提炼", "总结一下"], "weight": 0.85},
                {"keywords": ["PDF", "Word", "Excel", "PPT", "Markdown"], "weight": 0.85},
                {
                    "patterns": [r".*处理.*文档.*", r".*总结.*内容.*", r".*提取.*信息.*"],
                    "weight": 0.9,
                },
            ],
            # 专利专业类
            IntentType.PATENT_SEARCH: [
                {
                    "keywords": ["检索", "搜索", "查新", "现有技术", "对比文件", "patent search"],
                    "weight": 1.0,
                },
                {"keywords": ["专利检索", "专利搜索", "专利数据库", "查专利"], "weight": 0.95},
                {
                    "keywords": ["专利数据库", "Google Patents", "USPTO", "EPO", "WIPO"],
                    "weight": 0.9,
                },
                {"keywords": ["新颖性", "创造性", "专利性分析", "现有技术检索"], "weight": 0.85},
                {"keywords": ["查新", "新创性", "先检索", "预检索"], "weight": 0.8},
                {"keywords": ["对比文件", "对比专利", "相关专利", "近似专利"], "weight": 0.75},
            ],
            IntentType.OPINION_RESPONSE: [
                {"keywords": ["审查意见", "审查员", "通知书", "答复", "补正"], "weight": 1.0},
                {"keywords": ["审查意见答复", "答复审查意见", "审查员意见"], "weight": 0.95},
                {
                    "keywords": ["专利法第26条", "专利法第33条", "不清楚", "不支持", "公开不充分"],
                    "weight": 0.9,
                },
                {"keywords": ["驳回", "修改", "权利要求", "修改权利要求"], "weight": 0.85},
                {"keywords": ["答复模板", "答复策略", "答复技巧"], "weight": 0.8},
                {"keywords": ["一通答复", "二通答复", "OA答复"], "weight": 0.75},
            ],
            IntentType.PATENT_DRAFTING: [
                {"keywords": ["撰写", "申请", "权利要求", "说明书", "技术交底"], "weight": 1.0},
                {"keywords": ["专利撰写", "申请撰写", "撰写专利", "专利起草"], "weight": 0.95},
                {"keywords": ["专利申请文档", "申请文件", "提交"], "weight": 0.9},
                {"keywords": ["发明点", "技术特征", "保护范围", "技术方案"], "weight": 0.85},
                {"keywords": ["权利要求书", "说明书", "摘要", "附图"], "weight": 0.8},
                {"keywords": ["独立权利要求", "从属权利要求", "技术效果"], "weight": 0.75},
            ],
            IntentType.INFRINGEMENT_ANALYSIS: [
                {"keywords": ["侵权", "infringement", "侵权分析", "侵权风险"], "weight": 1.0},
                {"keywords": ["侵权判定", "侵权评估", "侵权检测"], "weight": 0.9},
                {"keywords": ["FTO", "Freedom to Operate", "自由实施", "防侵权"], "weight": 0.85},
                {"keywords": ["侵权比对", "权利要求比对", "技术方案比对"], "weight": 0.8},
                {"keywords": ["侵权风险分析", "侵权预警", "侵权排查"], "weight": 0.75},
            ],
            # 创意类
            IntentType.CREATIVE_WRITING: [
                {"keywords": ["写作", "创作", "故事", "文案", "创意"], "weight": 1.0},
                {"keywords": ["小说", "诗歌", "剧本", "营销文案"], "weight": 0.9},
                {"keywords": ["写个故事", "编故事", "创作故事", "故事创作"], "weight": 0.85},
                {"keywords": ["文案写作", "广告文案", "宣传文案", "推广文案"], "weight": 0.8},
                {"keywords": ["创意", "灵感", "想象力", "创意构思"], "weight": 0.75},
                {
                    "negative_keywords": ["统计", "图表", "数据", "报表", "分析", "可视化"],
                    "weight": -0.5,
                },
            ],
            # 系统类
            IntentType.SYSTEM_COMMAND: [
                {"keywords": ["启动", "停止", "重启", "restart", "shutdown"], "weight": 1.0},
                {"keywords": ["部署", "deploy", "更新", "update", "配置"], "weight": 0.9},
                {"keywords": ["开启", "关闭", "暂停", "恢复"], "weight": 0.8},
                {
                    "patterns": [r".*启动.*服务.*", r".*停止.*系统.*", r".*部署.*应用.*"],
                    "weight": 0.9,
                },
            ],
            IntentType.CONFIGURATION_CHANGE: [
                {"keywords": ["配置", "config", "设置", "setting", "修改配置"], "weight": 1.0},
                {"keywords": ["调整", "修改", "变更", "更改", "改变"], "weight": 0.85},
                {"keywords": ["参数", "选项", "配置项", "设置项"], "weight": 0.8},
            ],
            IntentType.HEALTH_CHECK: [
                {"keywords": ["健康检查", "health check", "健康状态", "运行状态"], "weight": 1.0},
                {"keywords": ["状态检查", "系统状态", "服务状态"], "weight": 0.9},
                {"keywords": ["诊断", "check", "检测", "检查"], "weight": 0.8},
                {"keywords": ["可用性", "存活", "存活检查"], "weight": 0.75},
            ],
            IntentType.SYSTEM_MONITORING: [
                {"keywords": ["监控", "monitor", "monitoring", "监视"], "weight": 1.0},
                {"keywords": ["健康检查", "系统状态", "性能"], "weight": 0.9},
                {"keywords": ["性能监控", "资源监控", "日志监控"], "weight": 0.85},
                {"keywords": ["日志", "错误", "故障", "优化"], "weight": 0.8},
                {"keywords": ["CPU", "内存", "磁盘", "网络", "流量"], "weight": 0.75},
            ],
            IntentType.TECHNICAL_EVALUATION: [
                {"keywords": ["评估", "evaluation", "评价", "技术方案", "可行性"], "weight": 1.0},
                {"keywords": ["技术优势", "创新性", "市场前景"], "weight": 0.8},
                {"keywords": ["技术评审", "技术审核", "技术论证"], "weight": 0.75},
                {"keywords": ["技术难点", "解决方案", "技术路径"], "weight": 0.7},
            ],
            # 交互类
            IntentType.CONVERSATION: [
                {"keywords": ["聊天", "chat", "对话", "conversation", "交流"], "weight": 1.0},
                {"keywords": ["你好", "嗨", "hello", "hi", "早上好", "下午好"], "weight": 0.9},
                {"keywords": ["谢谢", "感谢", "thank"], "weight": 0.85},
                {"keywords": ["再见", "拜拜", "goodbye"], "weight": 0.8},
                {"keywords": ["无聊", "聊聊", "闲聊", "聊天"], "weight": 0.75},
            ],
            IntentType.QUESTION_ANSWERING: [
                {"keywords": ["问答", "Q&A", "提问", "问题"], "weight": 1.0},
                {"keywords": ["疑问", "解惑", "解答", "答疑"], "weight": 0.85},
                {"keywords": ["不知道", "不懂", "不明白", "不清楚"], "weight": 0.8},
                {"keywords": ["?", "?", "怎么", "如何"], "weight": 0.75},
            ],
        }

    # ==================== 内部处理方法 ====================

    def _normalize_text(self, text: str) -> str:
        """文本标准化"""
        if not text:
            return ""
        text = text.lower()
        text = " ".join(text.split())
        return text

    def _keyword_matching(self, text: str) -> dict[IntentType, float]:
        """关键词匹配"""
        scores = defaultdict(float)

        for intent_type, pattern_groups in self.intent_patterns.items():
            for pattern_group in pattern_groups:
                # 正向关键词匹配
                if "keywords" in pattern_group:
                    keywords = pattern_group["keywords"]
                    weight = pattern_group["weight"]

                    for keyword in keywords:
                        if keyword.lower() in text:
                            scores[intent_type] += weight

                # 负向关键词匹配
                if "negative_keywords" in pattern_group:
                    neg_keywords = pattern_group["negative_keywords"]
                    neg_weight = pattern_group.get("weight", -0.5)

                    for neg_keyword in neg_keywords:
                        if neg_keyword.lower() in text:
                            scores[intent_type] += neg_weight

        return dict(scores)

    def _pattern_matching(self, text: str) -> dict[IntentType, float]:
        """模式匹配(正则表达式)"""
        scores = defaultdict(float)

        for intent_type, pattern_groups in self.intent_patterns.items():
            for pattern_group in pattern_groups:
                if "patterns" in pattern_group:
                    patterns = pattern_group["patterns"]
                    weight = pattern_group["weight"]

                    for pattern in patterns:
                        if re.search(pattern, text, re.IGNORECASE):
                            scores[intent_type] += weight
                            break

        return dict(scores)

    def _semantic_similarity(self, text: str) -> dict[IntentType, float]:
        """语义相似度计算(简化版)"""
        similarity_scores = {}

        semantic_keywords = {
            IntentType.CODE_GENERATION: ["编程", "开发", "脚本", "算法", "函数", "类"],
            IntentType.PATENT_SEARCH: ["专利", "检索", "查找", "搜索", "查询"],
            IntentType.PROBLEM_SOLVING: ["问题", "错误", "故障", "异常", "修复"],
            IntentType.CREATIVE_WRITING: ["创意", "创作", "想象", "故事", "艺术"],
        }

        text_words = set(text.split())

        for intent_type, keywords in semantic_keywords.items():
            overlap = len(text_words.intersection(set(keywords)))
            if overlap > 0:
                similarity_scores[intent_type] = min(0.3, overlap * 0.1)

        return similarity_scores

    def _context_analysis(
        self, text: str, context: dict[str, Any] | None = None, user_id: str | None = None
    ) -> dict[IntentType, float]:
        """上下文分析"""
        boost = defaultdict(float)

        # 基于历史记录的上下文增强
        if user_id and user_id in self.user_history:
            history = self.user_history[user_id]
            if len(history) > 0:
                recent = history[-3:]
                intent_counts = defaultdict(int)
                for record in recent:
                    intent_counts[record["intent"]] += 1

                for intent, count in intent_counts.items():
                    if count >= 2:
                        boost[intent] += 0.1 * count

        # 基于显式上下文的增强
        if context:
            if context.get("domain") == "patent":
                patent_intents = [
                    IntentType.PATENT_SEARCH,
                    IntentType.OPINION_RESPONSE,
                    IntentType.PATENT_DRAFTING,
                    IntentType.INFRINGEMENT_ANALYSIS,
                ]
                for intent in patent_intents:
                    boost[intent] += 0.15

            if context.get("previous_intent"):
                prev_intent = context["previous_intent"]
                boost[prev_intent] += 0.1

        return dict(boost)

    def _combine_scores(
        self, keyword_scores: dict, pattern_scores: dict, semantic_scores: dict, context_boost: dict
    ) -> dict[IntentType, float]:
        """综合评分"""
        combined = defaultdict(float)

        # 关键词匹配(权重50%)
        for intent, score in keyword_scores.items():
            combined[intent] += score * 0.5

        # 模式匹配(权重30%)
        for intent, score in pattern_scores.items():
            combined[intent] += score * 0.3

        # 语义相似度(权重15%)
        for intent, score in semantic_scores.items():
            combined[intent] += score * 0.15

        # 上下文增强(直接加分)
        for intent, score in context_boost.items():
            combined[intent] += score

        return dict(combined)

    def _select_best_intent(self, scores: dict[IntentType, float]) -> tuple[IntentType, float]:
        """选择最佳意图"""
        if not scores:
            return IntentType.CONVERSATION, 0.3

        best_intent = max(scores.items(), key=lambda x: x[1])

        best_score = best_intent[1]
        max(scores.values())
        total_score = sum(scores.values())

        # 计算置信度
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) >= 2:
            score_gap = sorted_scores[0] - sorted_scores[1]
            gap_confidence = min(0.95, 0.5 + score_gap * 2)
        else:
            gap_confidence = 0.5

        relative_confidence = best_score / total_score if total_score > 0 else 0.5
        absolute_confidence = min(0.95, best_score)

        confidence = gap_confidence * 0.5 + relative_confidence * 0.3 + absolute_confidence * 0.2

        confidence = max(0.2, min(0.98, confidence))

        return best_intent[0], confidence

    def _determine_complexity(self, text: str, intent: IntentType) -> ComplexityLevel:
        """确定复杂度"""
        word_count = len(text.split())

        complex_indicators = ["深度", "全面", "综合", "详细", "系统"]
        simple_indicators = ["简单", "快速", "基础", "基本"]

        has_complex = any(ind in text for ind in complex_indicators)
        has_simple = any(ind in text for ind in simple_indicators)

        high_complexity_intents = [
            IntentType.EVALUATION_REQUEST,
            IntentType.INFRINGEMENT_ANALYSIS,
            IntentType.OPINION_RESPONSE,
        ]

        if has_simple or word_count < 10:
            return ComplexityLevel.SIMPLE
        elif has_complex or intent in high_complexity_intents or word_count > 50:
            return ComplexityLevel.COMPLEX
        elif word_count > 30:
            return ComplexityLevel.EXPERT
        else:
            return ComplexityLevel.MEDIUM

    def _extract_entities(self, text: str) -> list[str]:
        """提取实体"""
        entities = []

        tech_patterns = [r"\b[A-Z]{2,}\b", r"\b\w+\.\w+\b", r"\b\d+\.\d+\b"]

        for pattern in tech_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches[:3])

        return list(set(entities))

    def _extract_key_concepts(self, text: str) -> list[str]:
        """提取关键概念(别名方法)"""
        return self._extract_concepts(text)

    def _estimate_processing_time(self, text: str, complexity: ComplexityLevel) -> float:
        """估算处理时间"""
        return self._estimate_time(complexity)

    def _get_suggested_tools(self, intent: IntentType) -> list[str]:
        """获取建议使用的工具"""
        tool_map = {
            IntentType.PATENT_SEARCH: ["patent_search", "patent_database"],
            IntentType.PATENT_ANALYSIS: ["patent_analyzer", "nlp_processor"],
            IntentType.CODE_GENERATION: ["code_generator", "linter"],
            IntentType.OPINION_RESPONSE: ["legal_analyzer", "template_manager"],
            IntentType.DATA_ANALYSIS: ["data_processor", "visualizer"],
        }
        return tool_map.get(intent, [])

    def _get_processing_strategy(self, intent: IntentType) -> str:
        """获取处理策略描述"""
        strategy_map = {
            IntentType.PATENT_SEARCH: "使用混合检索策略(关键词+向量+图谱)",
            IntentType.PATENT_ANALYSIS: "使用深度分析策略(NLP+规则引擎)",
            IntentType.CODE_GENERATION: "使用模板生成策略",
            IntentType.OPINION_RESPONSE: "使用法律推理策略",
        }
        return strategy_map.get(intent, "使用标准处理流程")

    def _extract_concepts(self, text: str) -> list[str]:
        """提取概念"""
        concepts = []

        concept_patterns = [
            r"(机器学习|深度学习|人工智能|神经网络)",
            r"(数据库|API|云计算|大数据)",
            r"(专利|权利要求|说明书|审查意见)",
            r"(算法|函数|类|对象|接口)",
        ]

        for pattern in concept_patterns:
            matches = re.findall(pattern, text)
            concepts.extend(matches)

        return list(set(concepts))

    def _estimate_time(self, complexity: ComplexityLevel) -> float:
        """估算处理时间"""
        time_map = {
            ComplexityLevel.SIMPLE: 1.0,
            ComplexityLevel.MEDIUM: 3.0,
            ComplexityLevel.COMPLEX: 8.0,
            ComplexityLevel.EXPERT: 15.0,
        }
        return time_map.get(complexity, 3.0)


# ========================================================================
# 工厂函数
# ========================================================================


def create_enhanced_intent_engine(config: dict | None = None) -> EnhancedIntentRecognitionEngine:
    """
    创建增强意图识别引擎

    Args:
        config: 配置字典

    Returns:
        引擎实例
    """
    return EnhancedIntentRecognitionEngine(config)


# 注册到工厂
from core.intent.base_engine import IntentEngineFactory

IntentEngineFactory.register("enhanced", EnhancedIntentRecognitionEngine)
IntentEngineFactory.register("enhanced_keyword", EnhancedIntentRecognitionEngine)


# ========================================================================
# 全局实例和便捷函数
# ========================================================================

_enhanced_intent_engine = None


def get_enhanced_intent_engine() -> EnhancedIntentRecognitionEngine:
    """获取增强意图识别引擎实例"""
    global _enhanced_intent_engine
    if _enhanced_intent_engine is None:
        _enhanced_intent_engine = EnhancedIntentRecognitionEngine()
    return _enhanced_intent_engine


# 便捷函数
def recognize_intent(
    text: str, context: dict | None = None, user_id: str | None = None
) -> IntentResult:
    """便捷函数:识别意图(同步)"""
    engine = get_enhanced_intent_engine()
    return engine.recognize_intent(text, context)


async def recognize_intent_async(
    text: str, context: dict | None = None, user_id: str | None = None
) -> IntentResult:
    """便捷函数:识别意图(异步)"""
    engine = get_enhanced_intent_engine()
    return await engine.recognize_intent_async(text, context, user_id)


if __name__ == "__main__":
    # 测试
    async def test():
        engine = get_enhanced_intent_engine()

        test_cases = [
            "帮我写一个Python函数",
            "专利202311334091.8的审查意见怎么答复",
            "分析一下这个方案的可行性",
            "我要检索机器学习相关的专利",
            "系统出错了,帮我看看",
            "有什么推荐的好用的AI工具",
            "你好,在吗?",
        ]

        for test in test_cases:
            print(f"\n输入: {test}")
            result = await engine.recognize_intent_async(test)
            print(f"意图: {result.intent.value}")
            print(f"置信度: {result.confidence:.3f}")
            print(f"复杂度: {result.complexity.value}")

    asyncio.run(test())
