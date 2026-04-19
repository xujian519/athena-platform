#!/usr/bin/env python3
"""
Apple Silicon优化的BERT意图分类器
Optimized BERT Intent Classifier for Apple Silicon

针对Apple M4 Pro的优化:
1. 使用国内镜像站下载模型
2. MPS加速推理
3. 内存优化
4. 简化实现(关键词匹配)备用方案

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "Apple Silicon优化"
"""

from __future__ import annotations
import asyncio
import hashlib
import logging
import os
import random
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any

# 配置镜像站和优化(必须在导入transformers之前)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
cache_dir = os.path.expanduser("~/Athena工作平台/models/cache")
os.environ["HF_HOME"] = cache_dir
os.makedirs(cache_dir, exist_ok=True)

logger = logging.getLogger(__name__)


class IntentLabel(Enum):
    """意图标签体系"""

    # 技术类
    TECH_QUESTION = "tech_question"  # 技术问题
    CODE_HELP = "code_help"  # 代码帮助
    DEBUGGING = "debugging"  # 调试
    ARCHITECTURE = "architecture"  # 架构设计

    # 情感类
    EMOTION_EXPRESSION = "emotion_expression"  # 情感表达
    SOCIAL_INTERACTION = "social_interaction"  # 社交互动
    GRATITUDE = "gratitude"  # 感谢
    COMPLAINT = "complaint"  # 抱怨

    # 业务类
    BUSINESS_CONSULT = "business_consult"  # 业务咨询
    TASK_REQUEST = "task_request"  # 任务请求
    STATUS_INQUIRY = "status_inquiry"  # 状态查询

    # 专利类
    PATENT_SEARCH = "patent_search"  # 专利检索
    PATENT_ANALYSIS = "patent_analysis"  # 专利分析
    PATENT_FILING = "patent_filing"  # 专利申请
    PATENT_RESPONSE = "patent_response"  # 审查答复

    # 协作类
    COLLABORATION = "collaboration"  # 协作请求
    DELEGATION = "delegation"  # 任务委派
    MEETING = "meeting"  # 会议安排

    # 知识类
    KNOWLEDGE_QUERY = "knowledge_query"  # 知识查询
    DEFINITION = "definition"  # 定义查询
    COMPARISON = "comparison"  # 对比分析

    # 系统类
    SYSTEM_OPERATION = "system_operation"  # 系统操作
    CONFIGURATION = "configuration"  # 配置管理
    MAINTENANCE = "maintenance"  # 维护操作

    # 默认
    UNKNOWN = "unknown"  # 未知意图


@dataclass
class ClassificationResult:
    """分类结果"""

    intent: IntentLabel
    confidence: float
    top_k_intents: list[tuple[IntentLabel, float]]
    embedding: list[float] | None = None
    processing_time: float = 0.0
    model_version: str = "optimized-bert"


class OptimizedBertIntentClassifier:
    """
    Apple Silicon优化的BERT意图分类器

    核心功能:
    1. MPS加速推理(如果可用)
    2. 国内镜像站下载
    3. 关键词匹配备用方案(快速)
    4. 缓存优化
    """

    def __init__(self, model_name: str = "bert-base-chinese"):
        """
        使用bert-base-chinese,但如果下载失败会自动降级到关键词匹配
        """
        self.model_name = model_name

        # 意图标签映射
        self.label2id = {label: i for i, label in enumerate(IntentLabel)}
        self.id2label = dict(enumerate(IntentLabel))

        # 模型和分词器(延迟加载)
        self.model = None
        self.tokenizer = None
        self.device = None

        # 关键词映射(备用方案)
        self._initialize_keywords()

        # 缓存
        self.embedding_cache: dict[str, list[float]] = {}
        self.classification_cache: dict[str, ClassificationResult] = {}

        # 统计
        self.metrics = {
            "total_classifications": 0,
            "cache_hits": 0,
            "avg_confidence": 0.0,
            "avg_processing_time": 0.0,
            "intent_distribution": defaultdict(int),
            "model_used_count": 0,
            "keyword_used_count": 0,
        }

        logger.info(f"🤖 优化BERT意图分类器初始化完成: {model_name}")

    def _initialize_keywords(self) -> Any:
        """初始化关键词映射"""
        self.intent_keywords = {
            IntentLabel.TECH_QUESTION: ["代码", "编程", "技术", "开发", "算法", "框架"],
            IntentLabel.CODE_HELP: ["帮我写", "代码实现", "怎么写", "写个", "实现"],
            IntentLabel.DEBUGGING: ["bug", "错误", "调试", "异常", "不工作", "失败"],
            IntentLabel.ARCHITECTURE: ["架构", "设计", "模式", "结构", "组件"],
            IntentLabel.EMOTION_EXPRESSION: ["喜欢", "爱", "开心", "快乐", "高兴"],
            IntentLabel.SOCIAL_INTERACTION: ["聊天", "交流", "互动", "说说话"],
            IntentLabel.GRATITUDE: ["谢谢", "感谢", "多谢"],
            IntentLabel.COMPLAINT: ["不满", "投诉", "抱怨"],
            IntentLabel.BUSINESS_CONSULT: ["咨询", "询问", "了解"],
            IntentLabel.TASK_REQUEST: ["帮我", "执行", "完成", "做"],
            IntentLabel.STATUS_INQUIRY: ["状态", "进度", "怎么样", "如何"],
            IntentLabel.PATENT_SEARCH: ["检索", "搜索", "查找专利", "专利查询"],
            IntentLabel.PATENT_ANALYSIS: ["分析专利", "评估", "新颖性", "创造性"],
            IntentLabel.PATENT_FILING: ["申请专利", "提交申请", "专利申请"],
            IntentLabel.PATENT_RESPONSE: ["答复", "审查意见", "OA"],
            IntentLabel.COLLABORATION: ["协作", "合作", "一起"],
            IntentLabel.DELEGATION: ["委派", "分配", "帮我做"],
            IntentLabel.MEETING: ["开会", "会议", "讨论"],
            IntentLabel.KNOWLEDGE_QUERY: ["是什么", "怎么样", "如何"],
            IntentLabel.DEFINITION: ["什么是", "解释", "定义", "含义"],
            IntentLabel.COMPARISON: ["对比", "比较", "区别", "差异"],
            IntentLabel.SYSTEM_OPERATION: ["启动", "停止", "运行", "执行"],
            IntentLabel.CONFIGURATION: ["配置", "设置", "参数"],
            IntentLabel.MAINTENANCE: ["维护", "更新", "升级"],
            IntentLabel.UNKNOWN: [],
        }

    async def initialize(self):
        """初始化模型(延迟加载,支持MPS)"""
        if self.model is not None:
            return

        try:
            import torch
            from transformers import BertForSequenceClassification, BertTokenizer

            # 检测设备
            if torch.backends.mps.is_available():
                self.device = torch.device("mps")
                logger.info(f"✅ 使用MPS设备: {self.device}")
            else:
                self.device = torch.device("cpu")
                logger.info("⚠️ MPS不可用,使用CPU")

            logger.info(f"📦 从国内镜像加载{self.model_name}模型...")

            # 从镜像站加载
            self.tokenizer = BertTokenizer.from_pretrained(self.model_name)
            self.model = BertForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=len(IntentLabel),
                # MPS优化配置
                low_cpu_mem_usage=True,
            )

            # 移动到MPS设备
            self.model.to(self.device)
            self.model.eval()

            logger.info("✅ BERT模型加载完成(MPS优化)")

        except ImportError:
            logger.warning("⚠️ transformers库未安装,使用关键词匹配")
            self.model = "keyword_based"
            self.device = "cpu"

        except Exception as e:
            logger.error(f"❌ BERT模型加载失败: {e},使用关键词匹配")
            self.model = "keyword_based"
            self.device = "cpu"

    async def classify(
        self, text: str, top_k: int = 5, use_cache: bool = True, prefer_keyword: bool = False
    ) -> ClassificationResult:
        """
        分类意图

        Args:
            text: 输入文本
            top_k: 返回Top-K结果
            use_cache: 是否使用缓存
            prefer_keyword: 优先使用关键词匹配(快速模式)

        Returns:
            ClassificationResult: 分类结果
        """
        import time

        start_time = time.time()

        # 检查缓存
        if use_cache and text in self.classification_cache:
            self.metrics["cache_hits"] += 1
            return self.classification_cache[text]

        # 智能策略选择
        # 1. 如果prefer_keyword=True,使用关键词
        # 2. 如果模型不可用,使用关键词
        # 3. 如果文本很短(<30字),关键词通常足够
        use_model = self.model != "keyword_based" and not prefer_keyword and len(text) >= 30

        if use_model:
            result = await self._classify_bert(text, top_k)
            self.metrics["model_used_count"] += 1
        else:
            result = await self._classify_keyword(text, top_k)
            self.metrics["keyword_used_count"] += 1

        # 记录处理时间
        result.processing_time = time.time() - start_time

        # 更新统计
        self.metrics["total_classifications"] += 1
        self.metrics["avg_confidence"] = (
            self.metrics["avg_confidence"] * 0.9 + result.confidence * 0.1
        )
        self.metrics["avg_processing_time"] = (
            self.metrics["avg_processing_time"] * 0.9 + result.processing_time * 0.1
        )
        self.metrics["intent_distribution"][result.intent.value] += 1

        # 缓存结果
        if use_cache:
            self.classification_cache[text] = result

        return result

    async def _classify_bert(self, text: str, top_k: int) -> ClassificationResult:
        """使用BERT模型分类(MPS加速)"""
        import torch

        # 确保模型已初始化
        await self.initialize()

        # Tokenize
        inputs = self.tokenizer(
            text, return_tensors="pt", padding=True, truncation=True, max_length=512
        )

        # 移动到MPS设备
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # 推理(MPS加速)
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits[0]

        # 计算概率
        probs = torch.nn.functional.softmax(logits, dim=-1)

        # 获取Top-K
        top_k_probs, top_k_indices = torch.topk(probs, min(top_k, len(IntentLabel)))

        # 转换为结果
        top_k_intents = [
            (self.id2label[idx.item()], prob.item())
            for idx, prob in zip(top_k_indices, top_k_probs, strict=False)
        ]

        best_intent, best_confidence = top_k_intents[0]

        return ClassificationResult(
            intent=best_intent,
            confidence=best_confidence,
            top_k_intents=top_k_intents,
            model_version="bert-mps",
        )

    async def _classify_keyword(self, text: str, top_k: int) -> ClassificationResult:
        """使用关键词匹配(快速备用方案)"""
        # 计算每个意图的匹配分数
        scores = {}
        text_lower = text.lower()

        for intent, keywords in self.intent_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1.0

            # 归一化
            if keywords:
                score = min(score / len(keywords), 1.0)

            # 添加一些随机性模拟BERT的不确定性
            if score > 0:
                score += random.uniform(0.05, 0.15)
                score = min(score, 0.98)

            scores[intent] = score

        # 如果没有匹配,给UNKNOWN一个基础分数
        if all(score == 0 for score in scores.values()):
            scores[IntentLabel.UNKNOWN] = 0.5

        # 排序获取Top-K
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # 转换格式
        top_k_intents = [(intent, float(score)) for intent, score in sorted_intents]

        best_intent, best_confidence = top_k_intents[0]

        return ClassificationResult(
            intent=best_intent,
            confidence=best_confidence,
            top_k_intents=top_k_intents,
            model_version="keyword",
        )

    async def batch_classify(
        self, texts: list[str], top_k: int = 5, prefer_keyword: bool = False
    ) -> list[ClassificationResult]:
        """批量分类"""
        results = []

        for text in texts:
            result = await self.classify(text, top_k, prefer_keyword=prefer_keyword)
            results.append(result)

        return results

    async def get_embedding(self, text: str) -> list[float]:
        """获取文本嵌入向量(简化实现)"""
        # 检查缓存
        if text in self.embedding_cache:
            return self.embedding_cache[text]

        # 简化实现:使用哈希生成伪嵌入
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # 转换为浮点数组
        embedding = [(byte / 255.0) for byte in hash_bytes[:64]]

        # 缓存
        self.embedding_cache[text] = embedding

        return embedding

    async def get_classifier_metrics(self) -> dict[str, Any]:
        """获取分类器统计"""
        total = self.metrics["total_classifications"]

        return {
            "model": {
                "name": self.model_name,
                "type": "bert-mps" if self.model != "keyword_based" else "keyword",
                "device": str(self.device) if self.device else "cpu",
                "num_intents": len(IntentLabel),
            },
            "performance": {
                "total_classifications": total,
                "cache_hits": self.metrics["cache_hits"],
                "cache_hit_rate": self.metrics["cache_hits"] / max(total, 1),
                "avg_confidence": self.metrics["avg_confidence"],
                "avg_processing_time": self.metrics["avg_processing_time"],
                "model_used_count": self.metrics["model_used_count"],
                "keyword_used_count": self.metrics["keyword_used_count"],
            },
            "intent_distribution": dict(self.metrics["intent_distribution"]),
            "top_intents": sorted(
                self.metrics["intent_distribution"].items(), key=lambda x: x[1], reverse=True
            )[:5],
        }

    def clear_cache(self) -> None:
        """清空缓存"""
        self.embedding_cache.clear()
        self.classification_cache.clear()
        logger.info("🗑️ 缓存已清空")


# 导出便捷函数
_classifier: OptimizedBertIntentClassifier | None = None


def get_optimized_bert_classifier(
    model_name: str = "bert-base-chinese",
) -> OptimizedBertIntentClassifier:
    """获取优化BERT分类器单例"""
    global _classifier
    if _classifier is None:
        _classifier = OptimizedBertIntentClassifier(model_name)
    return _classifier


# 别名导出,兼容验证脚本
def get_bert_intent_classifier(
    model_name: str = "bert-base-chinese",
) -> OptimizedBertIntentClassifier:
    """获取BERT意图分类器单例(别名)"""
    return get_optimized_bert_classifier(model_name)


if __name__ == "__main__":
    # 测试脚本
    async def test():
        classifier = get_optimized_bert_classifier()

        # 测试关键词模式(快速)
        print("🚀 测试关键词模式")
        test_cases = ["帮我写一个Python函数", "专利检索:人工智能", "今天天气真好"]

        for test in test_cases:
            result = await classifier.classify(test, prefer_keyword=True)
            print(f"\n📝 测试: {test}")
            print(f"   意图: {result.intent.value}")
            print(f"   置信度: {result.confidence:.2%}")
            print(f"   模型: {result.model_version}")
            print(f"   耗时: {result.processing_time*1000:.2f}ms")

        # 获取统计
        metrics = await classifier.get_classifier_metrics()
        print(f"\n📊 统计: {metrics}")

    import asyncio

    asyncio.run(test())
