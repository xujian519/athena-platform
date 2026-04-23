#!/usr/bin/env python3

"""
小诺智能工具选择系统
Xiaonuo Intelligent Tool Selection System

基于上下文、用户偏好和适用性评分的智能工具选择算法

作者: Athena平台团队
创建时间: 2025-12-18
版本: v1.0.0 "智能工具选择95%+"
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import numpy as np

from core.logging_config import setup_logging

# 安全序列化和模型加载
try:
    import joblib

except ImportError:
    import json

    def serialize_for_cache(obj) -> None:
        return json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")

    def deserialize_from_cache(data) -> None:
        return json.loads(data.decode("utf-8"))


import jieba
from sklearn.ensemble import GradientBoostingClassifier

# 机器学习库
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class ToolCategory(Enum):
    """工具类别"""

    CODE_ANALYSIS = "code_analysis"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    DECISION_ENGINE = "decision_engine"
    MICROSERVICE = "microservice"
    EMBEDDING = "embedding"
    CHAT_COMPLETION = "chat_completion"
    DOCUMENT_PROCESSING = "document_processing"
    WEB_SEARCH = "web_search"
    COORDINATION = "coordination"
    MONITORING = "infrastructure/infrastructure/monitoring"


class IntentCategory(Enum):
    """意图类别"""

    TECHNICAL = "technical"
    EMOTIONAL = "emotional"
    FAMILY = "family"
    LEARNING = "learning"
    COORDINATION = "coordination"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    WORK = "work"
    QUERY = "query"
    COMMAND = "command"


@dataclass
class Tool:
    """工具定义"""

    name: str
    category: ToolCategory
    description: str
    required_params: list[str]
    optional_params: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    performance_score: float = 0.8  # 基础性能分数
    complexity: int = 1  # 复杂度 1-5


@dataclass
class UserPreference:
    """用户偏好"""

    user_id: str
    tool_preferences: dict[str, float] = field(default_factory=dict)
    intent_tool_patterns: dict[str, list[str] = field(default_factory=dict)
    context_preferences: dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ToolSelectionConfig:
    """工具选择配置"""

    # 模型配置
    max_features: int = 5000
    n_estimators: int = 100
    context_weight: float = 0.3
    preference_weight: float = 0.2
    performance_weight: float = 0.3
    suitability_weight: float = 0.2

    # 阈值配置
    min_confidence: float = 0.5
    max_tools_per_intent: int = 3

    # 路径配置
    model_dir: str = "models/intelligent_tool_selector"
    data_dir: str = "data/tool_selection"


class XiaonuoIntelligentToolSelector:
    """小诺智能工具选择器"""

    def __init__(self, config: ToolSelectionConfig = None):
        self.config = config or ToolSelectionConfig()

        # 创建必要目录
        os.makedirs(self.config.model_dir, exist_ok=True)
        os.makedirs(self.config.data_dir, exist_ok=True)

        # 初始化组件
        self.tools: dict[str, Any] = {}
        self.user_preferences: dict[str, Any] = {}
        self.tool_suitability_matrix: dict[str, Any] = {}
        self.intent_tool_mapping: dict[str, Any] = {}

        # 机器学习模型
        self.feature_vectorizer = None
        self.tool_classifier = None
        self.scaler = None
        self.label_encoder = None

        # 初始化
        self._init_tools()
        self._init_jieba()

        logger.info("🛠️ 小诺智能工具选择器初始化完成")
        logger.info(f"🔧 可用工具数量: {len(self.tools)}")

    def _init_tools(self) -> Any:
        """初始化工具库"""
        self.tools = {
            # 技术类工具
            "code_analyzer": Tool(
                name="code_analyzer",
                category=ToolCategory.CODE_ANALYSIS,
                description="代码分析和质量检查工具",
                required_params=["code"],
                optional_params=["language", "style"],
                capabilities=["静态分析", "代码质量检查", "性能分析"],
                performance_score=0.9,
                complexity=3,
            ),
            "api_tester": Tool(
                name="api_tester",
                category=ToolCategory.CODE_ANALYSIS,
                description="API接口测试工具",
                required_params=["endpoint"],
                optional_params=["method", "headers", "body"],
                capabilities=["API测试", "性能测试", "接口文档"],
                performance_score=0.85,
                complexity=2,
            ),
            "performance_profiler": Tool(
                name="performance_profiler",
                category=ToolCategory.CODE_ANALYSIS,
                description="性能分析和优化工具",
                required_params=["target"],
                optional_params=["metrics", "duration"],
                capabilities=["性能监控", "瓶颈分析", "优化建议"],
                performance_score=0.88,
                complexity=4,
            ),
            # 知识图谱工具
            "knowledge_graph": Tool(
                name="knowledge_graph",
                category=ToolCategory.KNOWLEDGE_GRAPH,
                description="知识图谱查询和分析",
                required_params=["query"],
                optional_params=["domain", "depth"],
                capabilities=["知识查询", "关系分析", "图谱可视化"],
                performance_score=0.85,
                complexity=3,
            ),
            "entity_extractor": Tool(
                name="entity_extractor",
                category=ToolCategory.KNOWLEDGE_GRAPH,
                description="实体识别和抽取",
                required_params=["text"],
                optional_params=["entity_types"],
                capabilities=["实体识别", "关系抽取", "知识链接"],
                performance_score=0.82,
                complexity=2,
            ),
            # 决策引擎工具
            "decision_engine": Tool(
                name="decision_engine",
                category=ToolCategory.DECISION_ENGINE,
                description="智能决策支持引擎",
                required_params=["context", "options"],
                optional_params=["criteria", "weights"],
                capabilities=["多属性决策", "风险评估", "方案排序"],
                performance_score=0.87,
                complexity=4,
            ),
            "risk_analyzer": Tool(
                name="risk_analyzer",
                category=ToolCategory.DECISION_ENGINE,
                description="风险分析和评估",
                required_params=["scenario"],
                optional_params=["risk_factors"],
                capabilities=["风险识别", "概率计算", "影响评估"],
                performance_score=0.83,
                complexity=3,
            ),
            # 微服务工具
            "service_orchestrator": Tool(
                name="service_orchestrator",
                category=ToolCategory.MICROSERVICE,
                description="微服务编排和管理",
                required_params=["services"],
                optional_params=["workflow", "dependencies"],
                capabilities=["服务编排", "负载均衡", "故障恢复"],
                performance_score=0.89,
                complexity=5,
            ),
            "api_gateway": Tool(
                name="api_gateway",
                category=ToolCategory.MICROSERVICE,
                description="API网关和路由",
                required_params=["routes"],
                optional_params=["middleware", "policies"],
                capabilities=["请求路由", "认证授权", "流量控制"],
                performance_score=0.86,
                complexity=4,
            ),
            # 嵌入和向量化工具
            "text_embedding": Tool(
                name="text_embedding",
                category=ToolCategory.EMBEDDING,
                description="文本向量化和嵌入",
                required_params=["text"],
                optional_params=["model", "dimension"],
                capabilities=["文本向量化", "语义相似度", "聚类分析"],
                performance_score=0.84,
                complexity=2,
            ),
            "semantic_search": Tool(
                name="semantic_search",
                category=ToolCategory.EMBEDDING,
                description="语义搜索和检索",
                required_params=["query"],
                optional_params=["corpus", "top_k"],
                capabilities=["语义检索", "相似度搜索", "结果排序"],
                performance_score=0.86,
                complexity=3,
            ),
            # 聊天完成工具
            "chat_companion": Tool(
                name="chat_companion",
                category=ToolCategory.CHAT_COMPLETION,
                description="智能聊天伴侣",
                required_params=["message"],
                optional_params=["style", "context"],
                capabilities=["对话生成", "情感回应", "知识问答"],
                performance_score=0.91,
                complexity=2,
            ),
            "emotional_support": Tool(
                name="emotional_support",
                category=ToolCategory.CHAT_COMPLETION,
                description="情感支持和安慰",
                required_params=["emotion"],
                optional_params=["intensity", "context"],
                capabilities=["情感识别", "心理支持", "安慰回应"],
                performance_score=0.88,
                complexity=2,
            ),
            # 文档处理工具
            "document_parser": Tool(
                name="document_parser",
                category=ToolCategory.DOCUMENT_PROCESSING,
                description="文档解析和处理",
                required_params=["document"],
                optional_params=["format", "extraction_type"],
                capabilities=["文档解析", "信息抽取", "格式转换"],
                performance_score=0.83,
                complexity=3,
            ),
            "content_summarizer": Tool(
                name="content_summarizer",
                category=ToolCategory.DOCUMENT_PROCESSING,
                description="内容摘要和总结",
                required_params=["content"],
                optional_params=["length", "style"],
                capabilities=["文本摘要", "要点提取", "内容总结"],
                performance_score=0.85,
                complexity=2,
            ),
            # 网络搜索工具
            "web_search": Tool(
                name="web_search",
                category=ToolCategory.WEB_SEARCH,
                description="网络搜索和信息获取",
                required_params=["query"],
                optional_params=["source", "limit"],
                capabilities=["网络搜索", "信息聚合", "结果排序"],
                performance_score=0.87,
                complexity=2,
            ),
            "research_assistant": Tool(
                name="research_assistant",
                category=ToolCategory.WEB_SEARCH,
                description="研究助理和资料收集",
                required_params=["topic"],
                optional_params=["depth", "sources"],
                capabilities=["资料收集", "文献综述", "知识整合"],
                performance_score=0.84,
                complexity=3,
            ),
            # 协调工具
            "project_manager": Tool(
                name="project_manager",
                category=ToolCategory.COORDINATION,
                description="项目管理协调工具",
                required_params=["project"],
                optional_params=["timeline", "resources"],
                capabilities=["项目规划", "任务分配", "进度跟踪"],
                performance_score=0.86,
                complexity=4,
            ),
            "team_collaborator": Tool(
                name="team_collaborator",
                category=ToolCategory.COORDINATION,
                description="团队协作和沟通",
                required_params=["team"],
                optional_params=["task", "deadline"],
                capabilities=["任务协调", "团队沟通", "协作管理"],
                performance_score=0.83,
                complexity=3,
            ),
            # 监控工具
            "system_monitor": Tool(
                name="system_monitor",
                category=ToolCategory.MONITORING,
                description="系统监控和告警",
                required_params=["target"],
                optional_params=["metrics", "threshold"],
                capabilities=["性能监控", "异常检测", "告警通知"],
                performance_score=0.88,
                complexity=3,
            ),
            "health_checker": Tool(
                name="health_checker",
                category=ToolCategory.MONITORING,
                description="健康检查和诊断",
                required_params=["component"],
                optional_params=["check_type"],
                capabilities=["健康检查", "故障诊断", "状态报告"],
                performance_score=0.85,
                complexity=2,
            ),
        }

        logger.info(f"✅ 初始化了 {len(self.tools)} 个工具")

    def _init_jieba(self) -> Any:
        """初始化jieba分词"""
        # 添加工具相关词汇
        tool_words = [
            "代码分析",
            "性能测试",
            "知识图谱",
            "决策引擎",
            "微服务",
            "API网关",
            "文本向量化",
            "语义搜索",
            "聊天伴侣",
            "文档解析",
            "网络搜索",
            "项目管理",
            "团队协作",
            "系统监控",
            "健康检查",
        ]

        for word in tool_words:
            jieba.add_word(word, freq=1000)

    def create_tool_training_data(self) -> list[dict[str, Any]]:
        """创建工具选择训练数据"""
        logger.info("📚 创建工具选择训练数据集...")

        # 意图到工具的映射数据
        training_data = []

        # 技术类意图对应的工具选择
        technical_examples = [
            ("帮我分析这段代码", ["code_analyzer", "performance_profiler"]),
            ("测试这个API接口", ["api_tester", "code_analyzer"]),
            ("程序性能优化建议", ["performance_profiler", "code_analyzer"]),
            ("代码质量检查", ["code_analyzer", "performance_profiler"]),
            ("接口压力测试", ["api_tester", "performance_profiler"]),
            ("系统架构分析", ["performance_profiler", "code_analyzer"]),
            ("数据库查询优化", ["performance_profiler", "code_analyzer"]),
            ("代码重构建议", ["code_analyzer", "performance_profiler"]),
            ("部署服务监控", ["system_monitor", "performance_profiler"]),
            ("安全漏洞扫描", ["code_analyzer", "risk_analyzer"]),
        ]

        # 情感类意图对应的工具选择
        emotional_examples = [
            ("心情不太好想聊天", ["chat_companion", "emotional_support"]),
            ("需要一些安慰", ["emotional_support", "chat_companion"]),
            ("感觉有些焦虑", ["emotional_support", "chat_companion"]),
            ("感到很孤独", ["chat_companion", "emotional_support"]),
            ("需要情感支持", ["emotional_support", "chat_companion"]),
            ("想找人聊聊", ["chat_companion", "emotional_support"]),
            ("心情很激动", ["chat_companion", "emotional_support"]),
            ("被你感动了", ["chat_companion", "emotional_support"]),
            ("感觉很温暖", ["chat_companion", "emotional_support"]),
            ("需要鼓励", ["emotional_support", "chat_companion"]),
        ]

        # 家庭类意图对应的工具选择
        family_examples = [
            ("家庭聚会怎么安排", ["project_manager", "team_collaborator"]),
            ("准备爸爸的生日礼物", ["web_search", "research_assistant"]),
            ("家庭旅行计划", ["project_manager", "web_search"]),
            ("关心家人健康", ["health_checker", "emotional_support"]),
            ("家庭财务规划", ["decision_engine", "risk_analyzer"]),
            ("亲子活动安排", ["project_manager", "team_collaborator"]),
            ("家庭聚餐组织", ["project_manager", "team_collaborator"]),
            ("家庭照片整理", ["document_parser", "content_summarizer"]),
            ("家庭健康管理", ["health_checker", "infrastructure/infrastructure/monitoring"]),
            ("家庭应急计划", ["risk_analyzer", "decision_engine"]),
        ]

        # 学习类意图对应的工具选择
        learning_examples = [
            ("学习Python编程", ["research_assistant", "web_search"]),
            ("了解AI技术发展", ["knowledge_graph", "research_assistant"]),
            ("制定学习计划", ["decision_engine", "project_manager"]),
            ("查找学习资料", ["web_search", "knowledge_graph"]),
            ("知识体系构建", ["knowledge_graph", "content_summarizer"]),
            ("技能提升路径", ["decision_engine", "research_assistant"]),
            ("在线课程推荐", ["web_search", "research_assistant"]),
            ("学习笔记整理", ["content_summarizer", "document_parser"]),
            ("学习进度跟踪", ["project_manager", "infrastructure/infrastructure/monitoring"]),
            ("实践项目推荐", ["research_assistant", "web_search"]),
        ]

        # 协调类意图对应的工具选择
        coordination_examples = [
            ("管理多个项目", ["project_manager", "service_orchestrator"]),
            ("团队协作优化", ["team_collaborator", "project_manager"]),
            ("安排工作计划", ["project_manager", "decision_engine"]),
            ("资源分配优化", ["decision_engine", "project_manager"]),
            ("工作流程改进", ["project_manager", "service_orchestrator"]),
            ("跨部门协调", ["team_collaborator", "project_manager"]),
            ("敏捷开发实践", ["project_manager", "team_collaborator"]),
            ("会议安排管理", ["project_manager", "team_collaborator"]),
            ("任务优先级管理", ["decision_engine", "project_manager"]),
            ("绩效评估系统", ["infrastructure/infrastructure/monitoring", "decision_engine"]),
        ]

        # 娱乐类意图对应的工具选择
        entertainment_examples = [
            ("推荐一些电影", ["web_search", "research_assistant"]),
            ("听音乐放松", ["chat_companion", "web_search"]),
            ("玩个游戏", ["chat_companion", "web_search"]),
            ("讲个笑话", ["chat_companion", "web_search"]),
            ("轻松话题聊天", ["chat_companion", "web_search"]),
            ("推荐书籍", ["web_search", "research_assistant"]),
            ("兴趣爱好培养", ["research_assistant", "web_search"]),
            ("休闲活动建议", ["web_search", "chat_companion"]),
            ("放松心情", ["emotional_support", "chat_companion"]),
            ("娱乐资讯获取", ["web_search", "content_summarizer"]),
        ]

        # 健康类意图对应的工具选择
        health_examples = [
            ("健康生活建议", ["web_search", "research_assistant"]),
            ("压力缓解方法", ["emotional_support", "web_search"]),
            ("运动健身计划", ["project_manager", "research_assistant"]),
            ("健康检查提醒", ["health_checker", "infrastructure/infrastructure/monitoring"]),
            ("心理健康咨询", ["emotional_support", "chat_companion"]),
            ("营养饮食建议", ["web_search", "research_assistant"]),
            ("作息时间优化", ["decision_engine", "project_manager"]),
            ("亚健康状态改善", ["health_checker", "web_search"]),
            ("疲劳恢复指导", ["health_checker", "emotional_support"]),
            ("体检报告分析", ["document_parser", "health_checker"]),
        ]

        # 工作类意图对应的工具选择
        work_examples = [
            ("工作效率提升", ["decision_engine", "project_manager"]),
            ("会议安排管理", ["project_manager", "team_collaborator"]),
            ("职业发展规划", ["decision_engine", "research_assistant"]),
            ("工作汇报准备", ["content_summarizer", "document_parser"]),
            ("团队沟通协调", ["team_collaborator", "project_manager"]),
            ("工作目标设定", ["decision_engine", "project_manager"]),
            ("绩效改进计划", ["decision_engine", "infrastructure/infrastructure/monitoring"]),
            ("职场技能提升", ["research_assistant", "web_search"]),
            ("时间管理技巧", ["decision_engine", "project_manager"]),
            ("工作压力管理", ["emotional_support", "health_checker"]),
        ]

        # 查询类意图对应的工具选择
        query_examples = [
            ("查找技术资料", ["web_search", "knowledge_graph"]),
            ("行业报告查询", ["research_assistant", "web_search"]),
            ("知识库搜索", ["knowledge_graph", "semantic_search"]),
            ("技术文档查找", ["web_search", "document_parser"]),
            ("最新研究进展", ["research_assistant", "web_search"]),
            ("专业术语解释", ["knowledge_graph", "web_search"]),
            ("数据查询服务", ["web_search", "knowledge_graph"]),
            ("信息检索需求", ["semantic_search", "web_search"]),
            ("专利信息查询", ["web_search", "research_assistant"]),
            ("市场调研报告", ["research_assistant", "web_search"]),
        ]

        # 指令类意图对应的工具选择
        command_examples = [
            ("启动系统服务", ["system_monitor", "api_gateway"]),
            ("停止运行程序", ["system_monitor", "service_orchestrator"]),
            ("重启服务器", ["system_monitor", "service_orchestrator"]),
            ("系统状态检查", ["health_checker", "system_monitor"]),
            ("清理系统缓存", ["system_monitor", "document_parser"]),
            ("备份数据文件", ["document_parser", "system_monitor"]),
            ("更新系统配置", ["service_orchestrator", "api_gateway"]),
            ("监控系统日志", ["system_monitor", "document_parser"]),
            ("网络配置管理", ["api_gateway", "service_orchestrator"]),
            ("用户权限管理", ["api_gateway", "service_orchestrator"]),
        ]

        # 组合所有训练数据
        all_examples = [
            (IntentCategory.TECHNICAL, technical_examples),
            (IntentCategory.EMOTIONAL, emotional_examples),
            (IntentCategory.FAMILY, family_examples),
            (IntentCategory.LEARNING, learning_examples),
            (IntentCategory.COORDINATION, coordination_examples),
            (IntentCategory.ENTERTAINMENT, entertainment_examples),
            (IntentCategory.HEALTH, health_examples),
            (IntentCategory.WORK, work_examples),
            (IntentCategory.QUERY, query_examples),
            (IntentCategory.COMMAND, command_examples),
        ]

        for intent, examples in all_examples:
            for text, tools in examples:
                training_data.append(
                    {
                        "text": text,
                        "intent": intent.value,
                        "selected_tools": tools,
                        "context_features": self._extract_context_features(text, intent.value),
                    }
                )

        logger.info(f"✅ 训练数据集创建完成,总计: {len(training_data)}条")

        return training_data

    def _extract_context_features(self, text: str, intent: str) -> dict[str, Any]:
        """提取上下文特征"""
        # 基础文本特征
        words = list(jieba.cut(text))
        word_count = len(words)
        char_count = len(text)

        # 关键词特征
        technical_keywords = ["代码", "程序", "系统", "API", "数据库", "算法", "架构"]
        emotional_keywords = ["心情", "感觉", "情绪", "想", "爱", "喜欢", "开心", "难过"]
        action_keywords = ["启动", "停止", "运行", "开始", "结束", "执行", "操作"]
        query_keywords = ["什么", "如何", "怎么", "为什么", "查找", "搜索", "查询"]

        tech_score = sum(1 for word in technical_keywords if word in text)
        emotion_score = sum(1 for word in emotional_keywords if word in text)
        action_score = sum(1 for word in action_keywords if word in text)
        query_score = sum(1 for word in query_keywords if word in text)

        return {
            "word_count": word_count,
            "char_count": char_count,
            "tech_score": tech_score,
            "emotion_score": emotion_score,
            "action_score": action_score,
            "query_score": query_score,
            "has_question": 1 if any(q in text for q in ["?", "?", "什么", "怎么", "如何"]) else 0,
            "has_command": (
                1 if any(c in text for c in ["启动", "停止", "开始", "结束", "执行"]) else 0
            ),
            "urgency_level": 1 if any(u in text for u in ["紧急", "马上", "立即", "快"]) else 0,
        }

    def train_tool_selection_model(self) -> Any:
        """训练工具选择模型"""
        logger.info("🚀 开始训练智能工具选择模型...")

        # 获取训练数据
        training_data = self.create_tool_training_data()

        # 准备特征和标签
        X_text = [data["text"] for data in training_data]
        y_tools = [
            data["selected_tools"][0] for data in training_data
        ]  # 使用第一个选择的工具作为主要标签
        X_context = [list(data["context_features"].values()) for data in training_data]

        # 文本向量化
        self.feature_vectorizer = TfidfVectorizer(
            max_features=self.config.max_features, ngram_range=(1, 2), min_df=1, max_df=0.95
        )

        X_text_vec = self.feature_vectorizer.fit_transform(X_text).toarray()

        # 特征缩放
        self.scaler = StandardScaler()
        X_context_scaled = self.scaler.fit_transform(X_context)

        # 特征组合
        X_combined = np.hstack([X_text_vec, X_context_scaled])

        # 标签编码
        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y_tools)

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X_combined, y_encoded, test_size=0.2, random_state=42
        )

        # 训练集成模型
        self.tool_classifier = GradientBoostingClassifier(
            n_estimators=self.config.n_estimators, learning_rate=0.1, max_depth=5, random_state=42
        )

        self.tool_classifier.fit(X_train, y_train)

        # 评估模型
        y_pred = self.tool_classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        logger.info(f"🎯 工具选择模型准确率: {accuracy:.4f}")

        if accuracy >= 0.95:
            logger.info("🎉 工具选择准确率达到95%+目标!")
        elif accuracy >= 0.90:
            logger.info("👍 工具选择性能优秀!")
        else:
            logger.info(f"📈 当前准确率: {accuracy:.4f},继续优化")

        # 保存模型
        self.save_models()

        return accuracy

    def select_tools(
        self,
        text: str,
        intent: str,
        context: Optional[dict[str, Any]] = None,
        user_id: str = "default",
    ) -> list[tuple[str, float]]:
        """智能选择工具"""
        if self.tool_classifier is None:
            raise ValueError("模型尚未训练,请先调用train_tool_selection_model()")

        # 提取特征
        context_features = self._extract_context_features(text, intent)
        X_text_vec = self.feature_vectorizer.transform([text]).toarray()
        X_context_scaled = self.scaler.transform([list(context_features.values())])
        X_combined = np.hstack([X_text_vec, X_context_scaled])

        # 预测工具
        tool_probs = self.tool_classifier.predict_proba(X_combined)[0]
        tool_names = self.label_encoder.classes_

        # 获取所有工具的概率
        tool_scores = list(zip(tool_names, tool_probs, strict=False))

        # 应用各种评分因子
        enhanced_scores = self._enhance_tool_scores(tool_scores, text, intent, context, user_id)

        # 排序并返回top-k
        enhanced_scores.sort(key=lambda x: x[1], reverse=True)
        return enhanced_scores[: self.config.max_tools_per_intent]

    def _enhance_tool_scores(
        self,
        base_scores: list[tuple[str, float],
        text: str,
        intent: str,
        context: dict[str, Any],        user_id: str,
    ) -> list[tuple[str, float]]:
        """增强工具评分"""
        enhanced_scores = []

        for tool_name, base_score in base_scores:
            tool = self.tools.get(tool_name)
            if not tool:
                continue

            # 获取用户偏好
            user_pref = self._get_user_preference(user_id, tool_name)

            # 计算上下文相关性
            context_score = self._calculate_context_relevance(tool, intent, context)

            # 计算工具适用性
            suitability_score = self._calculate_tool_suitability(tool, text, intent)

            # 综合评分
            final_score = (
                base_score * self.config.performance_weight
                + tool.performance_score * self.config.performance_weight
                + user_pref * self.config.preference_weight
                + context_score * self.config.context_weight
                + suitability_score * self.config.suitability_weight
            )

            enhanced_scores.append((tool_name, min(final_score, 1.0)))

        return enhanced_scores

    def _get_user_preference(self, user_id: str, tool_name: str) -> float:
        """获取用户偏好"""
        if user_id not in self.user_preferences:
            return 0.5  # 默认中等偏好

        user_pref = self.user_preferences[user_id]
        return user_pref.tool_preferences.get(tool_name, 0.5)

    def _calculate_context_relevance(
        self, tool: Tool, intent: str, context: dict[str, Any]]
    ) -> float:
        """计算上下文相关性"""
        # 工具类别与意图的匹配度
        category_intent_match = {
            ToolCategory.CODE_ANALYSIS: [IntentCategory.TECHNICAL, IntentCategory.WORK],
            ToolCategory.KNOWLEDGE_GRAPH: [IntentCategory.LEARNING, IntentCategory.QUERY],
            ToolCategory.DECISION_ENGINE: [IntentCategory.WORK, IntentCategory.COORDINATION],
            ToolCategory.MICROSERVICE: [IntentCategory.TECHNICAL, IntentCategory.COMMAND],
            ToolCategory.EMBEDDING: [IntentCategory.LEARNING, IntentCategory.QUERY],
            ToolCategory.CHAT_COMPLETION: [
                IntentCategory.EMOTIONAL,
                IntentCategory.FAMILY,
                IntentCategory.ENTERTAINMENT,
            ],
            ToolCategory.DOCUMENT_PROCESSING: [IntentCategory.WORK, IntentCategory.LEARNING],
            ToolCategory.WEB_SEARCH: [IntentCategory.QUERY, IntentCategory.LEARNING],
            ToolCategory.COORDINATION: [
                IntentCategory.WORK,
                IntentCategory.COORDINATION,
                IntentCategory.FAMILY,
            ],
            ToolCategory.MONITORING: [
                IntentCategory.TECHNICAL,
                IntentCategory.HEALTH,
                IntentCategory.COMMAND,
            ],
        }

        matching_intents = category_intent_match.get(tool.category, [])
        relevance = 1.0 if IntentCategory(intent) in matching_intents else 0.3

        # 考虑上下文特征
        if context:
            if context.get("urgency_level", 0) > 0 and tool.category == ToolCategory.MONITORING:
                relevance += 0.2
            if context.get("has_question", 0) > 0 and tool.category in [
                ToolCategory.WEB_SEARCH,
                ToolCategory.KNOWLEDGE_GRAPH,
            ]:
                relevance += 0.2
            if context.get("has_command", 0) > 0 and tool.category in [
                ToolCategory.MICROSERVICE,
                ToolCategory.MONITORING,
            ]:
                relevance += 0.2

        return min(relevance, 1.0)

    def _calculate_tool_suitability(self, tool: Tool, text: str, intent: str) -> float:
        """计算工具适用性"""
        # 基于文本内容的匹配度
        text_lower = text.lower()
        tool_desc_lower = tool.description.lower()
        capability_match = 0

        for capability in tool.capabilities:
            if any(word in text_lower for word in capability.lower().split()):
                capability_match += 1

        capability_score = min(capability_match / len(tool.capabilities), 1.0)

        # 文本描述匹配度
        description_match = len(set(text_lower.split()) & set(tool_desc_lower.split())) / len(
            tool_desc_lower.split()
        )

        # 综合适用性评分
        suitability = capability_score * 0.7 + description_match * 0.3

        return min(suitability, 1.0)

    def update_user_feedback(
        self, user_id: str, selected_tool: str, success: bool, satisfaction: float
    ):
        """更新用户反馈"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreference(user_id=user_id)

        user_pref = self.user_preferences[user_id]

        # 更新工具偏好
        current_pref = user_pref.tool_preferences.get(selected_tool, 0.5)
        if success:
            # 成功则增加偏好
            new_pref = min(current_pref + satisfaction * 0.1, 1.0)
        else:
            # 失败则减少偏好
            new_pref = max(current_pref - (1 - satisfaction) * 0.1, 0.0)

        user_pref.tool_preferences[selected_tool] = new_pref
        user_pref.last_updated = datetime.now()

        logger.info(f"💾 更新用户偏好: {user_id} - {selected_tool}: {new_pref:.3f}")

    def save_models(self) -> None:
        """保存模型"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(self.config.model_dir, f"tool_selector_{timestamp}.pkl")

        model_data = {
            "feature_vectorizer": self.feature_vectorizer,
            "tool_classifier": self.tool_classifier,
            "scaler": self.scaler,
            "label_encoder": self.label_encoder,
            "dev/tools": self.tools,
            "user_preferences": self.user_preferences,
            "config": self.config,
        }

        with open(model_path, "wb") as f:
            # ❌ 修复前: f.write(serialize_for_cache(model_data))
            # ✅ 修复后: 使用joblib保存模型
            import joblib

            joblib.dump(model_data, f)

        # 保存最新模型
        latest_path = os.path.join(self.config.model_dir, "latest_tool_selector.pkl")
        with open(latest_path, "wb") as f:
            # ❌ 修复前: f.write(serialize_for_cache(model_data))
            # ✅ 修复后: 使用joblib保存模型
            import joblib

            joblib.dump(model_data, f)

        logger.info(f"💾 工具选择模型已保存: {model_path}")

    def load_models(self, model_path: Optional[str] = None) -> Optional[Any]:
        """加载模型"""
        if model_path is None:
            model_path = os.path.join(self.config.model_dir, "latest_tool_selector.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        with open(model_path, "rb") as f:
            # ❌ 修复前: model_data = deserialize_from_cache(f.read() if hasattr(f, \'read\') else f)
            # ✅ 修复后: 使用joblib加载模型
            import joblib

            joblib.load(f)

        model_data = joblib.load(open(model_path, "rb"))
        self.feature_vectorizer = model_data["feature_vectorizer"]
        self.tool_classifier = model_data["tool_classifier"]
        self.scaler = model_data["scaler"]
        self.label_encoder = model_data["label_encoder"]
        self.tools = model_data["dev/tools"]
        self.user_preferences = model_data.get("user_preferences", {})
        self.config = model_data["config"]

        logger.info(f"✅ 工具选择模型已加载: {model_path}")


def main() -> None:
    """主函数"""
    logger.info("🛠️ 小诺智能工具选择器训练开始")

    # 创建配置
    config = ToolSelectionConfig()

    # 创建工具选择器
    tool_selector = XiaonuoIntelligentToolSelector(config)

    # 训练模型
    try:
        accuracy = tool_selector.train_tool_selection_model()

        # 测试工具选择
        test_cases = [
            ("帮我分析这段Python代码", "technical"),
            ("爸爸,今天心情不太好", "emotional"),
            ("启动系统监控服务", "command"),
            ("查询AI技术发展趋势", "query"),
            ("安排团队项目计划", "coordination"),
        ]

        logger.info("\n🧪 智能工具选择测试:")
        for text, intent in test_cases:
            selected_tools = tool_selector.select_tools(text, intent)
            logger.info(f"  输入: {text}")
            logger.info(f"  意图: {intent}")
            logger.info("  推荐工具:")
            for tool, score in selected_tools:
                logger.info(f"    - {tool}: {score:.4f}")
            logger.info("")

        if accuracy >= 0.95:
            logger.info("🎉 工具选择准确率达到95%+目标!Phase 2圆满完成!")
        elif accuracy >= 0.90:
            logger.info("👍 工具选择性能优秀!")
        else:
            logger.info(f"📈 当前准确率: {accuracy:.4f},继续优化以达到95%目标")

    except Exception as e:
        logger.error(f"❌ 训练失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

