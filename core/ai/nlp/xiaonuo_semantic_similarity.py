#!/usr/bin/env python3

"""
小诺语义相似度匹配算法
Xiaonuo Semantic Similarity Matching Algorithm

实现高精度的语义相似度计算,支持意图候选重排序和上下文理解

作者: Athena平台团队
创建时间: 2025-12-18
版本: v1.0.0 "高精度语义匹配"
"""

import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import numpy as np

from core.logging_config import setup_logging

# 安全序列化和模型加载
try:
    import joblib

except ImportError:
    import json

    def serialize_for_cache(obj: Any) -> bytes:
        return json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")

    def deserialize_from_cache(data: bytes) -> Any:
        return json.loads(data.decode("utf-8"))


import jieba
from sklearn.decomposition import TruncatedSVD

# 机器学习库
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class SemanticConfig:
    """语义相似度配置"""

    # 向量维度
    vector_dim: int = 768
    # TF-IDF特征数
    max_features: int = 10000
    # n-gram范围
    ngram_range: tuple[int, int] = (1, 3)
    # 相似度阈值
    similarity_threshold: float = 0.3
    # 路径配置
    model_dir: str = "models/semantic_similarity"
    cache_dir: str = "cache/semantic"


class XiaonuoSemanticSimilarity:
    """小诺语义相似度匹配器"""

    def __init__(self, config: Optional[SemanticConfig] = None):
        self.config = config if config is not None else SemanticConfig()

        # 创建必要目录
        os.makedirs(self.config.model_dir, exist_ok=True)
        os.makedirs(self.config.cache_dir, exist_ok=True)

        # 初始化组件
        self.tfidf_vectorizer = None
        self.svd_model = None
        self.intent_examples = {}
        self.word_vectors = {}

        # 初始化jieba
        self._init_jieba()

        logger.info("🧠 小诺语义相似度匹配器初始化完成")
        logger.info(f"📏 向量维度: {self.config.vector_dim}")

    def _init_jieba(self) -> Any:
        """初始化jieba分词"""
        # 添加小诺专用词汇
        xiaonuo_words = [
            "爸爸",
            "小诺",
            "小娜",
            "Athena",
            "工作平台",
            "代码分析",
            "性能优化",
            "系统架构",
            "微服务",
            "分布式系统",
            "机器学习",
            "深度学习",
            "人工智能",
            "AI",
            "神经网络",
            "情感识别",
            "智能问答",
            "知识图谱",
            "向量检索",
            "自然语言处理",
            "API设计",
            "数据库优化",
            "算法分析",
            "项目管理",
            "团队协作",
            "负载均衡",
            "消息队列",
            "容器化",
            "DevOps",
            "持续集成",
        ]

        for word in xiaonuo_words:
            jieba.add_word(word, freq=1000)

    def create_intent_examples(self) -> dict[str, list[str]]:
        """创建意图示例库"""
        logger.info("📚 创建意图示例库...")

        intent_examples = {
            "TECHNICAL": [
                "帮我分析代码",
                "程序有bug需要调试",
                "优化数据库性能",
                "系统架构设计",
                "API接口开发",
                "算法复杂度分析",
                "前端性能调优",
                "后端服务部署",
                "分布式系统设计",
                "微服务架构",
                "缓存策略实现",
                "安全漏洞检查",
            ],
            "EMOTIONAL": [
                "爸爸我想你了",
                "心情不太好",
                "需要安慰和鼓励",
                "感到很孤独",
                "谢谢你的帮助",
                "感觉很温暖",
                "心情很激动",
                "被你感动了",
                "感到很幸福",
                "有点焦虑",
                "情绪低落",
                "充满希望",
            ],
            "FAMILY": [
                "我们家今天有什么计划",
                "给家人准备礼物",
                "家庭聚会安排",
                "和爸爸聊天",
                "关心妈妈身体",
                "周末家庭活动",
                "家庭聚餐",
                "亲子时光",
                "家庭旅行",
                "家庭氛围营造",
                "家人健康",
                "亲情交流",
            ],
            "LEARNING": [
                "教我学习编程",
                "提高技术能力",
                "了解AI技术",
                "制定学习计划",
                "推荐学习资源",
                "学习方法指导",
                "技能提升路径",
                "知识体系构建",
                "在线课程推荐",
                "技术栈选择",
                "学习效率提升",
                "实践项目推荐",
            ],
            "COORDINATION": [
                "协调团队工作",
                "管理多个项目",
                "安排工作计划",
                "提高团队效率",
                "项目进度跟踪",
                "资源分配",
                "团队协作",
                "工作流程优化",
                "任务管理",
                "跨部门协调",
                "会议安排",
                "敏捷开发",
            ],
            "ENTERTAINMENT": [
                "玩游戏吧",
                "讲个笑话",
                "听个故事",
                "推荐电影",
                "音乐分享",
                "轻松聊天",
                "娱乐活动",
                "推荐书籍",
                "放松心情",
                "兴趣爱好",
                "休闲时光",
                "趣味互动",
            ],
            "HEALTH": [
                "感觉很累",
                "保持身体健康",
                "缓解工作压力",
                "改善睡眠",
                "健康饮食",
                "运动健身",
                "心理健康",
                "疲劳恢复",
                "养生保健",
                "健康检查",
                "工作压力管理",
                "健康生活方式",
            ],
            "WORK": [
                "今天工作计划",
                "提高工作效率",
                "项目管理建议",
                "时间管理技巧",
                "工作目标设定",
                "职业发展规划",
                "工作汇报",
                "团队沟通",
                "工作与生活平衡",
                "职场技巧",
                "工作效率提升",
                "职业发展",
            ],
            "QUERY": [
                "什么是机器学习",
                "技术发展趋势",
                "查找资料信息",
                "了解新技术",
                "行业报告查询",
                "技术文档",
                "最新研究",
                "知识获取",
                "信息搜索",
                "数据查询",
                "技术调研",
                "知识检索",
            ],
            "COMMAND": [
                "启动系统服务",
                "停止任务",
                "重启程序",
                "清理缓存",
                "备份数据",
                "监控系统状态",
                "执行命令",
                "系统管理",
                "服务控制",
                "进程管理",
                "配置管理",
                "运行脚本",
            ],
        }

        # 数据增强:添加更多表达方式
        for intent, examples in intent_examples.items():
            augmented_examples = self._augment_examples(examples)
            intent_examples[intent].extend(augmented_examples)

        self.intent_examples = intent_examples

        logger.info("✅ 意图示例库创建完成")
        for intent, examples in intent_examples.items():
            logger.info(f"  - {intent}: {len(examples)}个示例")

        return intent_examples

    def _augment_examples(self, examples: list[str]) -> list[str]:
        """增强示例表达"""
        augmented = []

        # 前缀变换
        prefixes = ["请", "帮我", "我想", "可以", "能否", "麻烦"]

        for example in examples[:5]:  # 只对前5个进行增强
            for prefix in prefixes:
                if not example.startswith(prefix):
                    new_example = f"{prefix}{example}"
                    augmented.append(new_example)

        # 句式变换
        transformations: list[Callable[[str], str]] = [
            lambda x: f"{x},好吗",
            lambda x: f"{x},谢谢",
            lambda x: f"{x},麻烦了",
        ]

        for example in examples[:3]:
            for transform in transformations:
                augmented.append(transform(example))

        return augmented

    def train_semantic_models(self) -> Any:
        """训练语义模型"""
        logger.info("🚀 开始训练语义相似度模型...")

        # 创建意图示例库
        self.create_intent_examples()

        # 准备训练语料
        all_examples = []
        intent_labels = []

        for intent, examples in self.intent_examples.items():
            for example in examples:
                all_examples.append(example)
                intent_labels.append(intent)

        # 预处理文本
        processed_examples = [self._preprocess_text(text) for text in all_examples]

        # 训练TF-IDF向量化器
        logger.info("🔧 训练TF-IDF向量化器...")
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=self.config.max_features,
            ngram_range=self.config.ngram_range,
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
        )

        tfidf_matrix = self.tfidf_vectorizer.fit_transform(processed_examples)

        # 训练SVD降维模型
        logger.info("📉 训练SVD降维模型...")
        self.svd_model = TruncatedSVD(
            n_components=min(self.config.vector_dim, tfidf_matrix.shape[1] - 1),  # type: ignore[index]
            random_state=42,
        )

        self.svd_model.fit(tfidf_matrix)

        logger.info("✅ 语义模型训练完成")
        logger.info(f"📊 TF-IDF特征维度: {tfidf_matrix.shape}")  # type: ignore[attr-defined]
        logger.info(f"📏 SVD降维后维度: {self.svd_model.components_.shape}")  # type: ignore[attr-defined]

        # 保存模型
        self.save_models()

        return tfidf_matrix, self.svd_model

    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 标准化
        text = text.strip().lower()

        # 分词
        words = jieba.cut(text)

        # 过滤和组合
        filtered_words = []
        for word in words:
            if len(word) > 1 and word.strip():
                filtered_words.append(word)

        return " ".join(filtered_words)

    def encode_text(self, text: str) -> np.ndarray:
        """编码文本为语义向量"""
        if self.tfidf_vectorizer is None or self.svd_model is None:
            raise ValueError("模型尚未训练,请先调用train_semantic_models()")

        # 预处理
        processed_text = self._preprocess_text(text)

        # TF-IDF向量化
        tfidf_vector = self.tfidf_vectorizer.transform([processed_text])

        # SVD降维
        semantic_vector = self.svd_model.transform(tfidf_vector)

        return semantic_vector.flatten()

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的语义相似度"""
        # 编码文本
        vector1 = self.encode_text(text1)
        vector2 = self.encode_text(text2)

        # 计算余弦相似度
        similarity = cosine_similarity([vector1], [vector2])[0][0]

        return float(similarity)

    def find_similar_intents(self, text: str, top_k: int = 3) -> list[tuple[str, float]]:
        """查找与文本最相似的意图"""
        similarities = []

        # 计算与每个意图的相似度
        for intent, examples in self.intent_examples.items():
            max_similarity = 0

            # 计算与该意图所有示例的最大相似度
            for example in examples:
                similarity = self.calculate_similarity(text, example)
                max_similarity = max(max_similarity, similarity)

            similarities.append((intent, max_similarity))

        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)  # type: ignore[arg-type]

        # 返回top-k
        return similarities[:top_k]

    def rerank_intent_candidates(self, text: str, candidates: list[str]) -> list[tuple[str, float]]:
        """重排序意图候选"""
        scored_candidates = []

        for intent in candidates:
            # 计算与该意图的相似度
            similarity_score = self._calculate_intent_similarity(text, intent)

            scored_candidates.append((intent, similarity_score))

        # 按分数排序
        scored_candidates.sort(key=lambda x: x[1], reverse=True)  # type: ignore[arg-type]

        return scored_candidates

    def _calculate_intent_similarity(self, text: str, intent: str) -> float:
        """计算文本与特定意图的相似度"""
        if intent not in self.intent_examples:
            return 0.0

        examples = self.intent_examples[intent]
        similarities = []

        for example in examples:
            similarity = self.calculate_similarity(text, example)
            similarities.append(similarity)

        # 使用多种聚合策略
        max_sim = max(similarities)  # 最大相似度
        avg_sim = np.mean(similarities)  # 平均相似度
        top3_sim = np.mean(sorted(similarities, reverse=True)[:3])  # 前3平均

        # 加权组合
        final_score = 0.5 * max_sim + 0.3 * top3_sim + 0.2 * avg_sim

        return final_score

    def semantic_search(
        self, query: str, examples: list[str], top_k: int = 5
    ) -> list[tuple[str, float]]:
        """语义搜索"""
        query_vector = self.encode_text(query)

        similarities = []
        for example in examples:
            example_vector = self.encode_text(example)
            similarity = cosine_similarity([query_vector], [example_vector])[0][0]
            similarities.append((example, float(similarity)))

        # 按相似度排序并返回top-k
        similarities.sort(key=lambda x: x[1], reverse=True)  # type: ignore[arg-type]
        return similarities[:top_k]

    def save_models(self) -> None:
        """保存模型"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(self.config.model_dir, f"semantic_models_{timestamp}.pkl")

        model_data = {
            "tfidf_vectorizer": self.tfidf_vectorizer,
            "svd_model": self.svd_model,
            "intent_examples": self.intent_examples,
            "config": self.config,
        }

        with open(model_path, "wb") as f:
            # ❌ 修复前: f.write(serialize_for_cache(model_data))
            # ✅ 修复后: 使用joblib保存模型
            import joblib

            joblib.dump(model_data, f)

        # 保存最新模型
        latest_path = os.path.join(self.config.model_dir, "latest_semantic_models.pkl")
        with open(latest_path, "wb") as f:
            # ❌ 修复前: f.write(serialize_for_cache(model_data))
            # ✅ 修复后: 使用joblib保存模型
            import joblib

            joblib.dump(model_data, f)

        logger.info(f"💾 语义模型已保存: {model_path}")

    def load_models(self, model_path: Optional[str] = None) -> Optional[Any]:
        """加载模型"""
        if model_path is None:
            model_path = os.path.join(self.config.model_dir, "latest_semantic_models.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        with open(model_path, "rb") as f:
            # 使用joblib加载模型
            import joblib

            model_data = joblib.load(f)

        self.tfidf_vectorizer = model_data["tfidf_vectorizer"]
        self.svd_model = model_data["svd_model"]
        self.intent_examples = model_data["intent_examples"]
        self.config = model_data["config"]

        logger.info(f"✅ 语义模型已加载: {model_path}")

    def evaluate_performance(self, test_cases: list[tuple[str, str]) -> dict[str, float]]:
        """评估语义相似度性能"""
        logger.info("📊 评估语义相似度性能...")

        correct_predictions = 0
        total_cases = len(test_cases)
        similarity_scores = []

        for text, expected_intent in test_cases:
            # 获取相似意图
            similar_intents = self.find_similar_intents(text, top_k=1)
            predicted_intent, similarity = similar_intents[0]

            similarity_scores.append(similarity)

            # 检查预测是否正确
            if predicted_intent == expected_intent:
                correct_predictions += 1

        accuracy = float(correct_predictions / total_cases)
        avg_similarity = float(np.mean(similarity_scores))

        results: dict[str, float] = {
            "accuracy": accuracy,
            "avg_similarity": avg_similarity,
            "total_cases": float(total_cases),
            "correct_predictions": float(correct_predictions),
        }

        logger.info(f"🎯 语义匹配准确率: {accuracy:.4f}")
        logger.info(f"📈 平均相似度: {avg_similarity:.4f}")

        return results


def main() -> None:
    """主函数"""
    logger.info("🧠 小诺语义相似度匹配器训练开始")

    # 创建配置
    config = SemanticConfig()

    # 创建语义匹配器
    semantic_matcher = XiaonuoSemanticSimilarity(config)

    # 训练模型
    try:
        _tfidf_matrix, _svd_model = semantic_matcher.train_semantic_models()

        # 测试语义相似度计算
        test_pairs = [
            ("帮我分析代码", "优化程序性能"),
            ("爸爸我想你了", "需要情感支持"),
            ("启动监控系统", "系统管理操作"),
            ("学习新技术", "技能提升培训"),
            ("团队项目协调", "工作流程管理"),
        ]

        logger.info("🧪 语义相似度测试:")
        for text1, text2 in test_pairs:
            similarity = semantic_matcher.calculate_similarity(text1, text2)
            logger.info(f"  '{text1}' vs '{text2}': {similarity:.4f}")

        # 测试意图相似度查找
        test_queries = [
            "程序出现bug需要调试",
            "今天心情不太好",
            "我们周末去哪里玩",
            "如何提高工作效率",
            "重启数据库服务",
        ]

        logger.info("\n🔍 意图相似度查找测试:")
        for query in test_queries:
            similar_intents = semantic_matcher.find_similar_intents(query, top_k=3)
            logger.info(f"  查询: {query}")
            for intent, similarity in similar_intents:
                logger.info(f"    - {intent}: {similarity:.4f}")
            logger.info("")

        # 性能评估
        test_cases = [
            ("分析代码性能", "TECHNICAL"),
            ("想念爸爸", "EMOTIONAL"),
            ("安排家庭聚会", "FAMILY"),
            ("学习Python编程", "LEARNING"),
            ("管理团队项目", "COORDINATION"),
            ("推荐一部电影", "ENTERTAINMENT"),
            ("感觉很疲劳", "HEALTH"),
            ("今天工作计划", "WORK"),
            ("查询AI技术", "QUERY"),
            ("启动系统服务", "COMMAND"),
        ]

        performance = semantic_matcher.evaluate_performance(test_cases)

        if performance["accuracy"] >= 0.90:
            logger.info("🎉 语义匹配性能优秀!")
        elif performance["accuracy"] >= 0.80:
            logger.info("👍 语义匹配性能良好!")
        else:
            logger.info("📈 语义匹配性能需要进一步优化")

    except Exception as e:
        logger.error(f"❌ 训练失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

