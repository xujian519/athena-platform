#!/usr/bin/env python3
from __future__ import annotations
"""
稳定语义相似度匹配算法
Stable Semantic Similarity Matching Algorithm

解决第二阶段SVD数值不稳定问题,使用更稳定的TF-IDF余弦相似度

作者: Athena AI系统
创建时间: 2025-12-23
版本: v3.0.0 "稳定语义计算"
"""

import logging
from dataclasses import dataclass
from typing import Any

import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class StableSemanticConfig:
    """稳定语义配置 - 优化短文本识别"""

    max_features: int = 3000  # 降低特征数量以提升短文本匹配
    ngram_range: tuple[int, int] = (1, 2)  # 保留unigram和bigram
    min_df: int = 1  # 允许单个文档出现
    max_df: float = 0.98  # 提高阈值
    sublinear_tf: bool = False  # 关闭次线性TF,增强短文本权重
    norm: str = "l2"


class StableSemanticSimilarity:
    """稳定语义相似度匹配器

    使用纯TF-IDF余弦相似度,避免SVD数值不稳定问题
    """

    def __init__(self, config: StableSemanticConfig = None):
        self.config = config or StableSemanticConfig()
        self.tfidf_vectorizer = None
        self.intent_examples = {}
        self.is_trained = False

        logger.info("🧠 稳定语义相似度匹配器初始化完成")

    def add_intent_examples(self, intent_type: str, examples: list[str]) -> None:
        """添加意图示例"""
        if intent_type not in self.intent_examples:
            self.intent_examples[intent_type] = []
        self.intent_examples[intent_type].extend(examples)
        # 添加新示例后需要重新训练
        self.is_trained = False

    def train(self) -> Any:
        """训练TF-IDF模型"""
        logger.info("🚀 开始训练语义相似度模型...")

        # 准备训练语料
        all_examples = []
        for _intent, examples in self.intent_examples.items():
            all_examples.extend(examples)

        if not all_examples:
            logger.warning("⚠️ 没有训练数据,使用默认示例")
            self._init_default_examples()
            for _intent, examples in self.intent_examples.items():
                all_examples.extend(examples)

        # 预处理
        processed_examples = [self._preprocess(text) for text in all_examples]

        # 训练TF-IDF向量化器
        logger.info(f"🔧 训练TF-IDF向量化器 ({len(processed_examples)}个样本)...")
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=self.config.max_features,
            ngram_range=self.config.ngram_range,
            min_df=self.config.min_df,
            max_df=self.config.max_df,
            sublinear_tf=self.config.sublinear_tf,
            norm=self.config.norm,
        )

        self.tfidf_vectorizer.fit(processed_examples)

        self.is_trained = True
        logger.info("✅ 语义模型训练完成")

    def _init_default_examples(self) -> Any:
        """初始化默认示例 - 使用snake_case格式与IntentType匹配"""
        self.intent_examples = {
            "patent_search": [
                "检索人工智能相关专利",
                "搜索机器学习现有技术",
                "查新区块链技术专利",
                "查找深度学习相关专利",
                "专利数据库检索",
            ],
            "opinion_response": [
                "审查意见怎么答复",
                "如何回复审查员意见",
                "审查意见通知书答复",
                "专利审查意见答复策略",
            ],
            "patent_drafting": [
                "撰写发明专利申请",
                "写专利申请文件",
                "专利权利要求书撰写",
                "专利说明书撰写",
            ],
            "infringement_analysis": [
                "分析产品是否侵权",
                "专利侵权风险评估",
                "技术方案侵权分析",
                "产品侵权比对",
            ],
            "code_generation": [
                "帮我写代码",
                "生成Python函数",
                "编写算法实现",
                "创建代码框架",
            ],
            "creative_writing": [
                "帮我写个故事",
                "创作文案内容",
                "编写创意内容",
                "生成文章内容",
            ],
            "explanation_query": [
                "解释一下机器学习",
                "说明深度学习的原理",
                "详细介绍这个概念",
                "讲清楚这个技术",
            ],
            "problem_solving": [
                "系统启动不了了",
                "程序有错误",
                "系统崩溃修复",
                "代码调试问题",
            ],
            "data_analysis": [
                "分析数据报告",
                "统计分析结果",
                "数据可视化",
                "生成数据图表",
            ],
        }

    def _preprocess(self, text: str) -> str:
        """预处理文本 - 优化短文本语义识别"""
        # jieba分词
        words = jieba.cut(text)
        # 更宽松的停用词列表 - 保留更多语义信息
        # 只过滤纯虚词,保留"写"、"解释"等重要动词
        stopwords = {
            "的",
            "了",
            "和",
            "是",
            "在",
            "我",
            "有",
            "就",
            "不",
            "人",
            "都",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "自己",
            "这",
            "那",
            "吗",
            "呢",
            "吧",
            "啊",
            "呀",
        }
        words = [w for w in words if w not in stopwords and len(w) >= 1]  # 允许单字
        return " ".join(words)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        if not self.is_trained:
            self.train()

        try:
            # 预处理
            text1_proc = self._preprocess(text1)
            text2_proc = self._preprocess(text2)

            # 向量化
            vec1 = self.tfidf_vectorizer.transform([text1_proc])
            vec2 = self.tfidf_vectorizer.transform([text2_proc])

            # 计算余弦相似度
            similarity = cosine_similarity(vec1, vec2)[0][0]

            return float(similarity)

        except Exception as e:
            logger.error(f"❌ 相似度计算失败: {e}")
            return 0.0

    def find_best_intent(self, text: str, intent_list: list[str]) -> tuple[str, float]:
        """从给定的意图列表中找到最佳匹配"""
        if not self.is_trained:
            self.train()

        best_intent = None
        best_score = 0.0

        for intent in intent_list:
            # 计算与该意图所有示例的最大相似度
            examples = self.intent_examples.get(intent, [])
            if not examples:
                continue

            max_sim_for_intent = 0.0
            for example in examples:
                sim = self.calculate_similarity(text, example)
                max_sim_for_intent = max(max_sim_for_intent, sim)

            if max_sim_for_intent > best_score:
                best_score = max_sim_for_intent
                best_intent = intent

        return best_intent, best_score

    def rank_intents_by_similarity(self, text: str, top_k: int = 5) -> list[tuple[str, float]]:
        """根据相似度对所有意图进行排序"""
        if not self.is_trained:
            self.train()

        results = []

        for intent, examples in self.intent_examples.items():
            # 计算与该意图的最大相似度
            max_sim = 0.0
            for example in examples:
                sim = self.calculate_similarity(text, example)
                max_sim = max(max_sim, sim)

            results.append((intent, max_sim))

        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]


# 全局实例
_stable_semantic = None


def get_stable_semantic_similarity() -> StableSemanticSimilarity:
    """获取稳定语义相似度实例"""
    global _stable_semantic
    if _stable_semantic is None:
        _stable_semantic = StableSemanticSimilarity()
    return _stable_semantic


if __name__ == "__main__":
    # 测试
    sim = get_stable_semantic_similarity()

    # 添加示例
    sim.add_intent_examples(
        "CREATIVE_WRITING",
        [
            "帮我写个故事",
            "创作文案内容",
            "编写创意内容",
            "生成文章内容",
        ],
    )

    sim.train()

    # 测试相似度
    test_cases = [
        ("帮我写个故事", "创作文案内容"),
        ("帮我写个故事", "分析数据报告"),
        ("系统启动不了了", "程序有错误"),
    ]

    print("🧪 相似度测试:")
    for t1, t2 in test_cases:
        sim_score = sim.calculate_similarity(t1, t2)
        print(f'  "{t1}" vs "{t2}": {sim_score:.4f}')

    # 测试意图排序
    print("\n🎯 意图排序测试:")
    text = "帮我写个故事"
    results = sim.rank_intents_by_similarity(text, top_k=3)
    for intent, score in results:
        print(f"  {intent}: {score:.4f}")
