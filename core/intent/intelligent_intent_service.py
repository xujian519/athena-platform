#!/usr/bin/env python3
"""
智能意图识别服务
Intelligent Intent Recognition Service

整合Athena平台多种AI能力,构建多层意图识别系统:

架构层次:
┌─────────────────────────────────────────────────────────┐
│  第一层: 快速分类 (规则 + 关键词)                        │
│  - 基于规则的快速匹配                                    │
│  - 关键词触发识别                                        │
│  - 响应时间: <5ms                                       │
├─────────────────────────────────────────────────────────┤
│  第二层: 语义理解 (BGE-M3嵌入)                           │
│  - 语义向量相似度匹配                                    │
│  - 意图模板库匹配                                        │
│  - 响应时间: <50ms                                      │
├─────────────────────────────────────────────────────────┤
│  第三层: 深度分析 (NER + 推理引擎编排)                    │
│  - BERT-NER实体识别                                      │
│  - 推理引擎自动选择                                      │
│  - 任务画像构建                                          │
│  - 响应时间: <500ms                                     │
└─────────────────────────────────────────────────────────┘

作者: Athena AI Team
版本: 1.0.0
创建: 2026-01-23
"""

import asyncio
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from core.logging_config import setup_logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = setup_logging()


class IntentLayer(Enum):
    """意图识别层次"""

    L1_RULES = "l1_rules"  # 第一层:规则匹配
    L2_SEMANTIC = "l2_semantic"  # 第二层:语义理解
    L3_DEEP = "l3_deep"  # 第三层:深度分析


class IntentCategory(Enum):
    """意图类别(扩展版)"""

    # 专利相关
    PATENT_SEARCH = "patent_search"  # 专利检索
    PATENT_DRAFTING = "patent_drafting"  # 专利撰写
    PATENT_ANALYSIS = "patent_analysis"  # 专利分析
    NOVELTY_ANALYSIS = "novelty_analysis"  # 新颖性分析
    INVENTIVENESS_ANALYSIS = "inventiveness_analysis"  # 创造性分析
    INVALIDITY_REQUEST = "invalidity_request"  # 无效宣告

    # 法律相关
    LEGAL_QUERY = "legal_query"  # 法律咨询
    LEGAL_RESEARCH = "legal_research"  # 法律检索
    CONTRACT_ANALYSIS = "contract_analysis"  # 合同分析
    COMPLIANCE_CHECK = "compliance_check"  # 合规检查

    # 技术相关
    CODE_GENERATION = "code_generation"  # 代码生成
    DATA_ANALYSIS = "data_analysis"  # 数据分析
    TECHNICAL_RESEARCH = "technical_research"  # 技术研究

    # 通用任务
    PROBLEM_SOLVING = "problem_solving"  # 问题解决
    DECISION_SUPPORT = "decision_support"  # 决策支持
    CREATIVE_WRITING = "creative_writing"  # 创意写作

    # 系统相关
    SYSTEM_CONTROL = "system_control"  # 系统控制
    KNOWLEDGE_QUERY = "knowledge_query"  # 知识查询

    # 情感交互
    EMOTIONAL = "emotional"  # 情感表达
    CHITCHAT = "chitchat"  # 闲聊


@dataclass
class IntentRecognitionResult:
    """意图识别结果"""

    # 识别的意图
    intent: IntentCategory
    confidence: float

    # 识别层次
    matched_at_layer: IntentLayer

    # 推理引擎推荐
    recommended_engine: str | None = None
    engine_reason: str | None = None
    bypass_super_reasoning: bool = False

    # 提取的实体
    entities: dict[str, list[str]] = field(default_factory=dict)

    # 任务画像
    task_profile: dict[str, Any] | None = None

    # 思维协议追踪(可选)
    thought_trace: dict[str, Any] | None = None

    # 元数据
    processing_time_ms: float = 0.0
    methods_used: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "matched_at_layer": self.matched_at_layer.value,
            "recommended_engine": self.recommended_engine,
            "engine_reason": self.engine_reason,
            "bypass_super_reasoning": self.bypass_super_reasoning,
            "entities": self.entities,
            "task_profile": self.task_profile,
            "thought_trace": self.thought_trace,
            "processing_time_ms": self.processing_time_ms,
            "methods_used": self.methods_used,
            "timestamp": self.timestamp.isoformat(),
        }


class Layer1RuleMatcher:
    """
    第一层:规则匹配器

    基于关键词和规则的快速匹配,用于常见意图的快速识别。
    优点:速度快、准确性高(对于常见模式)

    新增功能:文件/链接检测与上下文权重提升
    """

    def __init__(self):
        """初始化规则匹配器"""
        self._build_rules()
        self._build_file_patterns()
        logger.info("✅ L1规则匹配器初始化完成")

    def _build_rules(self):
        """构建匹配规则"""
        # 关键词规则
        self.keyword_rules = {
            IntentCategory.PATENT_SEARCH: [
                "检索",
                "搜索",
                "查找",
                "查询专利",
                "patent search",
                "找专利",
                "现有技术",
                "prior art",
            ],
            IntentCategory.PATENT_DRAFTING: [
                "撰写",
                "起草",
                "写专利",
                "专利申请",
                "patent drafting",
                "撰写权利要求",
                "申请文件",
            ],
            IntentCategory.NOVELTY_ANALYSIS: [
                "新颖性",
                "是否新颖",
                "查新",
                "novelty",
                "现有技术对比",
                "区别特征",
            ],
            IntentCategory.INVENTIVENESS_ANALYSIS: [
                "创造性",
                "非显而易见",
                "inventive",
                "inventiveness",
                "技术贡献",
                "进步",
            ],
            IntentCategory.LEGAL_QUERY: [
                "法律咨询",
                "是否侵权",
                "侵权风险",
                "legal",
                "是否合法",
                "法律问题",
            ],
            IntentCategory.CODE_GENERATION: [
                "代码",
                "编程",
                "实现",
                "写代码",
                "code",
                "函数",
                "类",
                "算法",
            ],
            IntentCategory.DATA_ANALYSIS: [
                "分析数据",
                "统计",
                "数据可视化",
                "图表",
                "数据分析",
                "报告",
            ],
            IntentCategory.PROBLEM_SOLVING: [
                "怎么解决",
                "如何处理",
                "解决方案",
                "遇到问题",
                "故障排查",
            ],
            IntentCategory.KNOWLEDGE_QUERY: [
                "什么是",
                "解释",
                "定义",
                "原理",
                "how",
                "what",
                "explain",
            ],
        }

        # 正则表达式规则
        self.regex_rules = {
            IntentCategory.PATENT_SEARCH: [
                r"检索.*专利|搜索.*专利|查找.*专利",
                r"CN\d+|US\d+|EP\d+",  # 专利号模式
            ],
            IntentCategory.CODE_GENERATION: [
                r"写.*函数|实现.*算法|生成.*代码",
                r"python|java|javascript|代码",
            ],
            IntentCategory.LEGAL_QUERY: [r"是否.*侵权|侵权.*风险|法律.*责任"],
        }

    def _build_file_patterns(self):
        """构建文件和链接检测模式"""
        # 文件扩展名模式(按类型分组)
        self.file_patterns = {
            # 文档类型
            "document": [
                r"\.(pdf|doc|docx|txt|rtf|odt|tex|md|markdown|pages)\b",
                r"\.(ppt|pptx|key|odp)\b",  # 演示文稿
                r"\.(xls|xlsx|csv|numbers|ods)\b",  # 表格
            ],
            # 图片类型
            "image": [
                r"\.(jpg|jpeg|png|gif|bmp|svg|webp|ico|tiff|psd|raw|heic)\b",
                r"\.(ai|eps|ps|pdf)\b",  # 设计文件
            ],
            # 音频类型
            "audio": [
                r"\.(mp3|wav|flac|aac|ogg|wma|m4a|opus|aiff|ape)\b",
            ],
            # 视频类型
            "video": [
                r"\.(mp4|avi|mkv|mov|wmv|flv|webm|m4v|3gp|rmvb)\b",
            ],
            # 代码类型
            "code": [
                r"\.(py|js|ts|jsx|tsx|java|cpp|c|h|cs|go|rs|php|rb|swift|kt|scala)\b",
                r"\.(html|css|scss|less|sass|xml|json|yaml|yml|toml)\b",
            ],
            # 压缩文件
            "archive": [
                r"\.(zip|rar|7z|tar|gz|bz2|xz|cab|iso)\b",
            ],
            # 数据库文件
            "database": [
                r"\.(db|sqlite|sql|mdb|accdb)\b",
            ],
        }

        # 链接模式
        self.link_patterns = {
            # URL链接
            "url": [
                r"https?://[^\s]+",  # HTTP/HTTPS链接
                r"www\.[^\s]+",  # www链接
            ],
            # 文件路径
            "file_path": [
                r"[A-Za-z]:\\[^\s]+",  # Windows路径
                r"/[^\s]*[^\s\.]+\.[^\s]+",  # Unix路径
                r"\./[^\s]+",  # 相对路径
                r"\.\./[^\s]+",  # 父目录相对路径
                r"~/[^\s]+",  # Home目录路径
            ],
            # 云存储链接
            "cloud": [
                r"(drive\.google\.com|docs\.google\.com)[^\s]*",
                r"(dropbox\.com)[^\s]*",
                r"(onedrive\.live\.com)[^\s]*",
                r"(icloud\.com)[^\s]*",
                r"(wetransfer\.com)[^\s]*",
            ],
            # 文件夹/目录
            "folder": [
                r"[A-Za-z]:\\[^\\\s]+(\\[^\\\s]*)*\\?",  # Windows目录
                r"/[^/\s]+(/[^/\s]*)*/?",  # Unix目录
            ],
        }

        # 文件处理相关关键词
        self.file_keywords = [
            "文件",
            "文档",
            "图片",
            "照片",
            "音频",
            "视频",
            "链接",
            "附件",
            "上传",
            "下载",
            "打开",
            "读取",
            "分析",
            "处理",
            "识别",
            "提取",
            "转换",
            "格式",
            "file",
            "document",
            "image",
            "audio",
            "video",
            "link",
            "attachment",
            "upload",
            "download",
        ]

        # 上下文权重配置
        self.context_weights = {
            "document": 1.3,  # 文档权重提升30%
            "image": 1.4,  # 图片权重提升40%
            "audio": 1.2,  # 音频权重提升20%
            "video": 1.2,  # 视频权重提升20%
            "code": 1.5,  # 代码权重提升50%
            "archive": 1.1,  # 压缩文件权重提升10%
            "database": 1.2,  # 数据库权重提升20%
            "url": 1.25,  # URL链接权重提升25%
            "file_path": 1.3,  # 文件路径权重提升30%
            "cloud": 1.35,  # 云存储链接权重提升35%
        }

    def detect_files_and_links(self, text: str) -> dict[str, Any]:
        """
        检测文本中的文件和链接

        Args:
            text: 输入文本

        Returns:
            检测结果字典,包含:
            - has_files: 是否包含文件
            - has_links: 是否包含链接
            - file_types: 检测到的文件类型列表
            - link_types: 检测到的链接类型列表
            - matches: 匹配到的内容
            - weight_multiplier: 权重乘数
        """
        result = {
            "has_files": False,
            "has_links": False,
            "file_types": [],
            "link_types": [],
            "matches": {"files": [], "links": []},
            "weight_multiplier": 1.0,
            "detected_items": [],
        }

        # 检测文件
        for file_type, patterns in self.file_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    result["has_files"] = True
                    if file_type not in result["file_types"]:
                        result["file_types"].append(file_type)
                    result["matches"]["files"].extend(
                        [{"type": file_type, "content": m} for m in matches]
                    )

        # 检测链接
        for link_type, patterns in self.link_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    result["has_links"] = True
                    if link_type not in result["link_types"]:
                        result["link_types"].append(link_type)
                    result["matches"]["links"].extend(
                        [{"type": link_type, "content": m} for m in matches]
                    )

        # 检测文件相关关键词
        keyword_matches = [kw for kw in self.file_keywords if kw.lower() in text.lower()]
        if keyword_matches:
            result["has_file_keywords"] = True
            result["file_keyword_matches"] = keyword_matches

        # 计算权重乘数
        weight_multiplier = 1.0

        # 根据检测到的文件类型提升权重
        for file_type in result["file_types"]:
            if file_type in self.context_weights:
                weight_multiplier = max(weight_multiplier, self.context_weights[file_type])

        # 根据检测到的链接类型提升权重
        for link_type in result["link_types"]:
            if link_type in self.context_weights:
                weight_multiplier = max(weight_multiplier, self.context_weights[link_type])

        # 如果同时有文件和链接,额外提升
        if result["has_files"] and result["has_links"]:
            weight_multiplier *= 1.1

        # 如果有文件关键词,额外提升
        if keyword_matches:
            weight_multiplier *= 1.05

        # 限制最大权重为2.0
        result["weight_multiplier"] = min(weight_multiplier, 2.0)

        # 构建检测项目列表(用于后续处理)
        detected_items = []
        for match in result["matches"]["files"]:
            detected_items.append(
                {"type": "file", "category": match["type"], "content": match["content"]}
            )
        for match in result["matches"]["links"]:
            detected_items.append(
                {"type": "link", "category": match["type"], "content": match["content"]}
            )
        result["detected_items"] = detected_items

        return result

    def match(self, text: str) -> tuple[IntentCategory, float, dict[str, Any] | None]:
        """
        匹配意图

        Args:
            text: 输入文本

        Returns:
            (意图类别, 置信度, 上下文信息) 或 None
        """
        text_lower = text.lower()

        # ========== 第一步:检测文件和链接 ==========
        file_link_detection = self.detect_files_and_links(text)
        weight_multiplier = file_link_detection["weight_multiplier"]

        # ========== 第二步:关键词匹配 ==========
        best_match = None
        best_score = 0.0
        matched_keywords = []

        for intent, keywords in self.keyword_rules.items():
            score = 0.0
            intent_matched_keywords = []

            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 1.0
                    intent_matched_keywords.append(keyword)

            if score > best_score:
                best_score = score
                matched_keywords = intent_matched_keywords
                best_match = intent

        # ========== 第三步:正则表达式匹配(提高置信度)==========
        confidence = 0.0
        if best_match:
            confidence = min(best_score * 0.3, 0.95)  # 基础置信度

            # 应用权重乘数(文件/链接提升)
            confidence = min(confidence * weight_multiplier, 0.99)

            # 正则表达式额外提升
            if best_match in self.regex_rules:
                for pattern in self.regex_rules[best_match]:
                    if re.search(pattern, text):
                        confidence = min(confidence + 0.1, 0.98)
                        break

        # ========== 第四步:构建上下文信息 ==========
        context_info = {
            "file_link_detection": file_link_detection,
            "matched_keywords": matched_keywords,
            "weight_applied": weight_multiplier,
            "has_files_or_links": file_link_detection["has_files"]
            or file_link_detection["has_links"],
        }

        # 置信度阈值
        if best_match and confidence >= 0.3:
            return (best_match, confidence, context_info)

        return None


class Layer2SemanticMatcher:
    """
    第二层:语义匹配器

    使用BGE-M3嵌入模型进行语义相似度匹配,
    识别更复杂的意图表达。
    """

    def __init__(self):
        """初始化语义匹配器"""
        self.vector_manager = None
        self.intent_templates = self._build_intent_templates()
        self._initialize()
        logger.info("✅ L2语义匹配器初始化完成")

    def _build_intent_templates(self) -> dict[IntentCategory, list[str]:
        """构建意图模板库"""
        return {
            IntentCategory.PATENT_SEARCH: [
                "我想查找关于人工智能的专利",
                "检索一下深度学习相关的现有技术",
                "搜索计算机视觉领域的专利文献",
            ],
            IntentCategory.PATENT_DRAFTING: [
                "帮我撰写一个关于新发明的专利申请",
                "起草一份软件专利的权利要求书",
                "写一个技术方案的专利文档",
            ],
            IntentCategory.NOVELTY_ANALYSIS: [
                "分析这项技术方案的新颖性",
                "评估该发明是否具有新颖性",
                "对比现有技术,找出区别特征",
            ],
            IntentCategory.INVENTIVENESS_ANALYSIS: [
                "判断这个发明的创造性高度",
                "评估技术方案的非显而易见性",
                "分析发明的技术贡献",
            ],
            IntentCategory.LEGAL_QUERY: [
                "这个产品会侵犯专利权吗",
                "使用这项技术需要获得授权吗",
                "评估实施这个方案的法律风险",
            ],
            IntentCategory.CODE_GENERATION: [
                "写一个Python函数来实现这个算法",
                "生成处理数据的JavaScript代码",
                "帮我编写这个功能的代码实现",
            ],
            IntentCategory.DATA_ANALYSIS: [
                "分析这些专利数据的发展趋势",
                "统计某个技术领域的专利分布",
                "可视化展示技术演进路径",
            ],
        }

    def _initialize(self):
        """初始化向量管理器"""
        try:
            from core.vector import UnifiedVectorManager

            self.vector_manager = UnifiedVectorManager()
            # 使用已有的BGE-M3模型
            asyncio.run(self.vector_manager.initialize())

            logger.info("✅ 向量管理器已加载 (BGE-M3)")
        except Exception as e:
            logger.warning(f"⚠️ 向量管理器初始化失败: {e}")
            self.vector_manager = None

    async def match(
        self, text: str, threshold: float = 0.75
    ) -> tuple[IntentCategory, float | None]:
        """
        语义匹配意图

        Args:
            text: 输入文本
            threshold: 相似度阈值

        Returns:
            (意图类别, 置信度) 或 None
        """
        if not self.vector_manager:
            return None

        try:
            # 获取输入文本的向量
            query_result = await self.vector_manager.embed_text(text)
            query_vector = query_result.get("vector")

            if not query_vector:
                return None

            best_match = None
            best_similarity = 0.0

            # 与每个意图的模板进行匹配
            for intent, templates in self.intent_templates.items():
                for template in templates:
                    # 获取模板的向量(使用缓存)
                    template_result = await self.vector_manager.embed_text(template)
                    template_vector = template_result.get("vector")

                    if template_vector:
                        # 计算余弦相似度
                        similarity = self._cosine_similarity(query_vector, template_vector)

                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = intent

            if best_match and best_similarity >= threshold:
                return (best_match, best_similarity)

        except Exception as e:
            logger.error(f"L2语义匹配失败: {e}")

        return None

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """计算余弦相似度"""
        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)


class Layer3DeepAnalyzer:
    """
    第三层:深度分析器

    使用NER实体识别和推理引擎编排,进行深度意图理解。
    """

    def __init__(self):
        """初始化深度分析器"""
        self.ner_service = None
        self.orchestrator = None
        self._initialize()
        logger.info("✅ L3深度分析器初始化完成")

    def _initialize(self):
        """初始化组件"""
        # 初始化NER服务
        try:
            from core.nlp.xiaonuo_enhanced_ner import XiaonuoEnhancedNER

            self.ner_service = XiaonuoEnhancedNER()
            logger.info("✅ NER服务已加载")
        except Exception as e:
            logger.warning(f"⚠️ NER服务初始化失败: {e}")

        # 初始化推理引擎编排器
        try:
            from core.reasoning.unified_reasoning_orchestrator import UnifiedReasoningOrchestrator

            self.orchestrator = UnifiedReasoningOrchestrator()
            logger.info("✅ 推理引擎编排器已加载")
        except Exception as e:
            logger.warning(f"⚠️ 推理引擎编排器初始化失败: {e}")

    def extract_entities(self, text: str) -> dict[str, list[str]]:
        """
        提取实体

        Args:
            text: 输入文本

        Returns:
            实体字典 {类型: [实体列表]}
        """
        if not self.ner_service:
            return {}

        try:
            entities = self.ner_service.extract_entities(text)

            # 按类型分组
            entity_dict = {}
            for entity in entities:
                entity_type = entity.entity_type
                if entity_type not in entity_dict:
                    entity_dict[entity_type] = []
                entity_dict[entity_type].append(entity.text)

            return entity_dict

        except Exception as e:
            logger.error(f"实体提取失败: {e}")
            return {}

    def build_task_profile(
        self, text: str, entities: dict[str, list[str]
    ) -> dict[str, Any] | None:
        """
        构建任务画像

        Args:
            text: 输入文本
            entities: 提取的实体

        Returns:
            任务画像字典
        """
        if not self.orchestrator:
            return None

        try:
            # 分析任务特征
            task_features = self._analyze_task_features(text, entities)

            # 使用编排器推荐引擎
            # 注意:这里简化了调用,实际可能需要更复杂的逻辑

            return {
                "domain": task_features.get("domain"),
                "complexity": task_features.get("complexity"),
                "requires_reasoning": task_features.get("requires_reasoning", False),
                "is_legal_task": task_features.get("is_legal", False),
                "entities": entities,
                "keywords": task_features.get("keywords", []),
            }

        except Exception as e:
            logger.error(f"任务画像构建失败: {e}")
            return None

    @staticmethod
    def _analyze_task_features(text: str, entities: dict[str, list[str]) -> dict[str, Any]:
        """分析任务特征"""
        features = {
            "domain": "general",
            "complexity": "medium",
            "requires_reasoning": False,
            "is_legal": False,
            "keywords": [],
        }

        # 检测领域
        domain_keywords = {
            "patent": ["专利", "发明", "权利要求", "技术方案"],
            "legal": ["法律", "侵权", "合规", "合同"],
            "technical": ["技术", "算法", "系统", "实现"],
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in text for kw in keywords):
                features["domain"] = domain
                if domain in ["patent", "legal"]:
                    features["is_legal"] = True
                    features["requires_reasoning"] = True
                break

        # 检测复杂度
        complexity_indicators = {
            "high": ["分析", "评估", "判断", "推理"],
            "medium": ["查找", "搜索", "检索"],
            "low": ["是什么", "什么是", "解释"],
        }

        for complexity, indicators in complexity_indicators.items():
            if any(ind in text for ind in indicators):
                features["complexity"] = complexity
                break

        # 提取关键词(简单版)
        words = re.findall(r"[\w]+", text)
        features["keywords"] = [w for w in words if len(w) > 2][:10]

        return features


class IntelligentIntentRecognitionService:
    """
    智能意图识别服务

    整合三层识别能力,提供强大的意图识别功能。
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化服务

        Args:
            config: 配置字典
                - enable_l1: 启用第一层(默认True)
                - enable_l2: 启用第二层(默认True)
                - enable_l3: 启用第三层(默认True)
                - enable_thinking_protocol: 启用思维协议(默认True)
                - l2_threshold: L2相似度阈值(默认0.75)
        """
        self.config = config or {}

        # 初始化各层识别器
        self.l1_matcher = None
        self.l2_matcher = None
        self.l3_analyzer = None
        self.thinking_analyzer = None

        if self.config.get("enable_l1", True):
            self.l1_matcher = Layer1RuleMatcher()

        if self.config.get("enable_l2", True):
            self.l2_matcher = Layer2SemanticMatcher()

        if self.config.get("enable_l3", True):
            self.l3_analyzer = Layer3DeepAnalyzer()

        # 初始化思维协议分析器(增强L3)
        if self.config.get("enable_thinking_protocol", True) and self.l3_analyzer:
            try:
                from core.intent.thinking_protocol_analyzer import ThinkingProtocolAnalyzer

                self.thinking_analyzer = ThinkingProtocolAnalyzer()
                logger.info("✅ 思维协议分析器已启用")
            except Exception as e:
                logger.warning(f"⚠️ 思维协议分析器初始化失败: {e}")

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "l1_matches": 0,
            "l2_matches": 0,
            "l3_matches": 0,
            "thinking_protocol_used": 0,
            "no_match": 0,
        }

        logger.info("🎯 智能意图识别服务初始化完成")
        logger.info(f"   - L1规则匹配: {'✅' if self.l1_matcher else '❌'}")
        logger.info(f"   - L2语义理解: {'✅' if self.l2_matcher else '❌'}")
        logger.info(f"   - L3深度分析: {'✅' if self.l3_analyzer else '❌'}")
        logger.info(f"   - 思维协议增强: {'✅' if self.thinking_analyzer else '❌'}")

    async def recognize_intent(
        self, text: str, context: dict[str, Any] | None = None
    ) -> IntentRecognitionResult:
        """
        识别意图

        Args:
            text: 用户输入文本
            context: 上下文信息

        Returns:
            意图识别结果
        """
        start_time = datetime.now()
        self.stats["total_requests"] += 1

        methods_used = []

        # ========== 第一层:规则匹配 ==========
        if self.l1_matcher:
            l1_result = self.l1_matcher.match(text)
            if l1_result:
                intent, confidence, context_info = l1_result
                self.stats["l1_matches"] += 1
                methods_used.append("L1规则匹配")

                # 如果检测到文件/链接,添加到方法列表
                if context_info["has_files_or_links"]:
                    methods_used.append(f"文件/链接增强(权重x{context_info['weight_applied']:.2f})")

                processing_time = (datetime.now() - start_time).total_seconds() * 1000

                return IntentRecognitionResult(
                    intent=intent,
                    confidence=confidence,
                    matched_at_layer=IntentLayer.L1_RULES,
                    processing_time_ms=processing_time,
                    methods_used=methods_used,
                    # 添加文件/链接检测信息到metadata
                    task_profile={
                        "file_link_detection": context_info["file_link_detection"],
                        "matched_keywords": context_info["matched_keywords"],
                        "context_weight": context_info["weight_applied"],
                    },
                )

        # ========== 第二层:语义匹配 ==========
        if self.l2_matcher:
            l2_result = await self.l2_matcher.match(
                text, threshold=self.config.get("l2_threshold", 0.75)
            )
            if l2_result:
                intent, confidence = l2_result
                self.stats["l2_matches"] += 1
                methods_used.append("L2语义匹配")

                processing_time = (datetime.now() - start_time).total_seconds() * 1000

                return IntentRecognitionResult(
                    intent=intent,
                    confidence=confidence,
                    matched_at_layer=IntentLayer.L2_SEMANTIC,
                    processing_time_ms=processing_time,
                    methods_used=methods_used,
                )

        # ========== 第三层:深度分析 ==========
        if self.l3_analyzer:
            methods_used.append("L3深度分析")

            # 提取实体
            entities = self.l3_analyzer.extract_entities(text)

            # 构建任务画像
            task_profile = self.l3_analyzer.build_task_profile(text, entities)

            # 基于实体和画像推断意图
            intent = self._infer_intent_from_entities(text, entities, task_profile)

            # 使用思维协议分析器增强分析(如果启用)
            thought_trace_dict = None
            if self.thinking_analyzer and context and context.get("return_thought_trace"):
                try:
                    trace = await self.thinking_analyzer.analyze_with_thinking_protocol(
                        text, context, entities
                    )
                    thought_trace_dict = {
                        "phase": trace.phase.value,
                        "thoughts": trace.thoughts,
                        "hypotheses": [
                            {
                                "intent": h.intent.value,
                                "confidence": h.confidence,
                                "reasoning": h.reasoning,
                            }
                            for h in trace.hypotheses
                        ],
                        "insights": trace.insights,
                        "decisions": trace.decisions,
                        "timestamp": trace.timestamp.isoformat(),
                    }
                    methods_used.append("思维协议增强")
                    self.stats["thinking_protocol_used"] += 1
                except Exception as e:
                    logger.warning(f"⚠️ 思维协议分析失败: {e}")

            self.stats["l3_matches"] += 1

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return IntentRecognitionResult(
                intent=intent,
                confidence=0.7,  # L3的置信度相对较低
                matched_at_layer=IntentLayer.L3_DEEP,
                entities=entities,
                task_profile=task_profile,
                thought_trace=thought_trace_dict,
                processing_time_ms=processing_time,
                methods_used=methods_used,
            )

        # ========== 无匹配 ==========
        self.stats["no_match"] += 1
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return IntentRecognitionResult(
            intent=IntentCategory.CHITCHAT,
            confidence=0.5,
            matched_at_layer=IntentLayer.L1_RULES,
            processing_time_ms=processing_time,
            methods_used=["默认回退"],
        )

    @staticmethod
    def _infer_intent_from_entities(
        text: str, entities: dict[str, list[str], task_profile: dict[str, Any]
    ) -> IntentCategory:
        """从实体推断意图"""
        # 如果有任务画像,使用画像信息
        if task_profile:
            domain = task_profile.get("domain")
            is_legal = task_profile.get("is_legal", False)

            if domain == "patent" and is_legal:
                # 专利法律任务
                if "分析" in text or "评估" in text:
                    return IntentCategory.PATENT_ANALYSIS
                return IntentCategory.PATENT_SEARCH

            elif domain == "legal":
                return IntentCategory.LEGAL_QUERY

            elif domain == "technical":
                if "代码" in text or "实现" in text:
                    return IntentCategory.CODE_GENERATION
                return IntentCategory.TECHNICAL_RESEARCH

        # 基于实体类型推断
        if "PATENT_NUMBER" in entities or "APPLICATION_NUMBER" in entities:
            return IntentCategory.PATENT_SEARCH

        if "LAW_ARTICLE" in entities or "REGULATION" in entities:
            return IntentCategory.LEGAL_QUERY

        # 默认返回知识查询
        return IntentCategory.KNOWLEDGE_QUERY

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total = self.stats["total_requests"]
        if total == 0:
            return self.stats

        return {
            **self.stats,
            "l1_rate": self.stats["l1_matches"] / total,
            "l2_rate": self.stats["l2_matches"] / total,
            "l3_rate": self.stats["l3_matches"] / total,
            "no_match_rate": self.stats["no_match"] / total,
        }


# =============================================================================
# 全局服务实例
# =============================================================================

_global_service: IntelligentIntentRecognitionService | None = None


def get_intelligent_intent_service(
    config: dict[str, Any] | None = None,
) -> IntelligentIntentRecognitionService:
    """
    获取智能意图识别服务实例(单例)

    Args:
        config: 配置字典

    Returns:
        服务实例
    """
    global _global_service

    if _global_service is None:
        _global_service = IntelligentIntentRecognitionService(config)

    return _global_service


# =============================================================================
# 测试代码
# =============================================================================


async def main():
    """测试主函数"""
    # 配置日志
    # setup_logging()  # 日志配置已移至模块导入

    # 创建服务
    service = IntelligentIntentRecognitionService()

    # 测试用例(包含文件/链接检测测试)
    test_cases = [
        "帮我检索人工智能领域的专利",
        "分析这项发明的新颖性",
        "这个方案会侵权吗",
        "写一个Python函数实现快速排序",
        "什么是深度学习",
        "今天天气怎么样",
        # 文件/链接检测测试用例
        "请分析这个PDF文件中的专利内容: /path/to/document.pdf",
        "查看这张图片的设计思路: https://example.com/design.jpg",
        "帮我处理这个视频文件: demo.mp4",
        "读取这个CSV数据文件: data.csv并生成报告",
        "分析这个代码文件: src/main.py",
        "下载这个Google Drive链接的文件: https://drive.google.com/file/d/xxx",
    ]

    print("\n" + "=" * 60)
    print("🎯 智能意图识别服务测试")
    print("=" * 60 + "\n")

    for text in test_cases:
        print(f"📝 输入: {text}")

        result = await service.recognize_intent(text)

        print(f"   意图: {result.intent.value}")
        print(f"   置信度: {result.confidence:.2f}")
        print(f"   匹配层次: {result.matched_at_layer.value}")
        print(f"   处理时间: {result.processing_time_ms:.2f}ms")
        print(f"   方法: {', '.join(result.methods_used)}")

        if result.entities:
            print(f"   实体: {result.entities}")

        # 显示文件/链接检测信息
        if result.task_profile and "file_link_detection" in result.task_profile:
            detection = result.task_profile["file_link_detection"]
            print("   📎 文件/链接检测:")
            print(f"      - 包含文件: {detection['has_files']}")
            print(f"      - 包含链接: {detection['has_links']}")
            print(f"      - 文件类型: {detection['file_types']}")
            print(f"      - 链接类型: {detection['link_types']}")
            print(f"      - 权重乘数: x{detection['weight_multiplier']:.2f}")
            if detection.get("detected_items"):
                print(f"      - 检测项: {len(detection['detected_items'])}个")
            print(f"      - 上下文权重: {result.task_profile.get('context_weight', 1.0):.2f}")

        if result.task_profile and "matched_keywords" in result.task_profile:
            keywords = result.task_profile["matched_keywords"]
            if keywords:
                print(f"   🔑 匹配关键词: {', '.join(keywords)}")

        print()

    # 打印统计信息
    print("=" * 60)
    print("📊 统计信息")
    print("=" * 60)
    stats = service.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")


# =============================================================================
# 单独测试文件/链接检测功能
# =============================================================================


async def test_file_link_detection():
    """单独测试文件/链接检测功能"""
    from core.intent.intelligent_intent_service import Layer1RuleMatcher

    print("\n" + "=" * 60)
    print("🔍 文件/链接检测功能测试")
    print("=" * 60 + "\n")

    matcher = Layer1RuleMatcher()

    # 测试用例
    test_cases = [
        "分析这个PDF文件的内容",
        "查看这个图片: photo.png",
        "读取这个Excel表格: report.xlsx",
        "访问这个链接: https://example.com/doc",
        "打开这个本地文件: /Users/user/document.pdf",
        "播放这个音频文件: song.mp3",
        "运行这个Python代码: script.py",
        "从这个Google Drive链接下载: https://drive.google.com/xxx",
        "分析这个压缩包中的数据: archive.zip",
        "查看这个文件夹的内容: C:\\Projects\\MyProject",
        "请帮我分析 https://example.com/image.jpg 这个图片",
        "读取 ~/Documents/data.csv 这个文件",
        "分析相对路径 ./data/input.json 的内容",
        # 多文件组合测试
        "对比这两个文件: doc1.pdf 和 doc2.pdf",
        "分析包含这些链接的内容: https://site1.com 和 www.site2.com",
    ]

    for text in test_cases:
        result = matcher.detect_files_and_links(text)

        print(f"📝 输入: {text}")
        print(f"   检测到文件: {result['has_files']}")
        print(f"   检测到链接: {result['has_links']}")

        if result["has_files"]:
            print(f"   文件类型: {result['file_types']}")
        if result["has_links"]:
            print(f"   链接类型: {result['link_types']}")

        print(f"   权重乘数: x{result['weight_multiplier']:.2f}")

        if result.get("detected_items"):
            print("   检测项:")
            for item in result["detected_items"][:5]:  # 只显示前5个
                print(f"      - [{item['type']}] {item['category']}: {item['content'][:50]}...")

        print()

    print("=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)


# 入口点: @async_main装饰器已添加到main函数
