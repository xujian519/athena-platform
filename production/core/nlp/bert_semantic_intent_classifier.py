#!/usr/bin/env python3
"""
Athena BERT语义增强意图分类器
BERT Semantic Enhanced Intent Classifier

使用本地MPS优化的BERT模型提取语义特征,融合到意图分类器中:

特性:
1. 使用本地MPS优化的BERT模型(无需下载)
2. 1024维(BGE-M3)语义向量提取
3. BERT特征与TF-IDF特征融合
4. 高性能GPU加速(Apple Silicon MPS)
5. 模型缓存和增量训练

预期提升: 意图识别准确率 85% → 95%+

作者: Athena平台团队
创建时间: 2025-12-29
版本: v2.1.0
"""

from __future__ import annotations
import json
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# 安全修复: 使用joblib替代pickle序列化scikit-learn模型
import joblib
import numpy as np
import torch
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC
from transformers import AutoModel, AutoTokenizer

from core.logging_config import setup_logging

# 添加项目路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class BERTIntentConfig:
    """BERT语义增强意图分类器配置"""

    # 意图类别
    intent_labels = [
        "TECHNICAL",  # 技术类
        "EMOTIONAL",  # 情感类
        "FAMILY",  # 家庭类
        "LEARNING",  # 学习类
        "COORDINATION",  # 协调类
        "ENTERTAINMENT",  # 娱乐类
        "HEALTH",  # 健康类
        "WORK",  # 工作类
        "QUERY",  # 查询类
        "COMMAND",  # 指令类
    ]

    # 本地BERT模型路径(MPS优化)
    local_bert_models = {
        "chinese_bert": str(PROJECT_ROOT / "models/converted/chinese_bert"),
        "bert_base_chinese": str(PROJECT_ROOT / "models/converted/bert-base-chinese"),
        "chinese_roberta_wwm": str(PROJECT_ROOT / "models/converted/chinese-roberta-wwm-ext"),
        "bge_base_zh": str(PROJECT_ROOT / "models/converted/BAAI/bge-m3"),
        "bge_large_zh": str(PROJECT_ROOT / "models/converted/BAAI/bge-m3"),
    }

    # 默认使用BGE-base-zh(性能和效果平衡)
    default_model: str = "bge_base_zh"

    # 特征融合配置
    use_bert_features: bool = True
    use_tfidf_features: bool = True
    use_text_stats: bool = True
    bert_feature_weight: float = 0.6  # BERT特征权重
    tfidf_feature_weight: float = 0.3  # TF-IDF特征权重
    text_stats_weight: float = 0.1  # 文本统计特征权重

    # 模型配置
    max_seq_length: int = 512
    batch_size: int = 8
    cache_embeddings: bool = True
    embedding_cache_file: str = (
        "data/intent/bert_embeddings_cache.joblib"  # 安全修复: 使用.joblib扩展名
    )

    # TF-IDF配置
    max_features: int = 10000
    ngram_range: tuple[int, int] = (1, 3)

    # 路径配置
    model_dir: str = "models/bert_intent_classifier"
    data_dir: str = "data/intent_training"


class BERTFeatureExtractor:
    """BERT语义特征提取器"""

    def __init__(
        self,
        model_name: str = "bge_base_zh",
        model_paths: dict[str, str] | None = None,
        device: torch.device | None = None,
    ):
        """
        初始化BERT特征提取器

        Args:
            model_name: 模型名称
            model_paths: 模型路径字典
            device: 计算设备
        """
        self.model_name = model_name
        self.model_paths = model_paths or BERTIntentConfig.local_bert_models
        self.device = device or self._get_device()

        self.tokenizer = None
        self.model = None
        self.embedding_cache: dict[str, np.ndarray] = {}
        self.cache_lock = threading.RLock()

        # 加载模型
        self._load_model()

        logger.info("✅ BERT特征提取器初始化完成")
        logger.info(f"🤖 模型: {model_name}")
        logger.info(f"🔧 设备: {self.device}")

    def _get_device(self) -> torch.device:
        """智能选择计算设备"""
        if torch.backends.mps.is_available():
            logger.info("🍎 使用MPS GPU加速(Apple Silicon)")
            return torch.device("mps")
        elif torch.cuda.is_available():
            logger.info("🚀 使用CUDA GPU加速")
            return torch.device("cuda")
        else:
            logger.info("💻 使用CPU模式")
            return torch.device("cpu")

    def _load_model(self) -> Any:
        """加载本地BERT模型"""
        try:
            model_path = self.model_paths.get(self.model_name)
            if not model_path:
                raise ValueError(f"模型路径未找到: {self.model_name}")

            if not os.path.exists(model_path):
                raise ValueError(f"模型文件不存在: {model_path}")

            logger.info(f"📦 加载本地BERT模型: {model_path}")

            # 加载tokenizer
            # 安全修复: 禁用trust_remote_code防止任意代码执行
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=False,  # 安全: 不执行模型中的自定义代码
                local_files_only=True,
            )
            logger.info("✅ Tokenizer加载完成")

            # 加载模型
            self.model = AutoModel.from_pretrained(
                model_path,
                trust_remote_code=False,  # 安全: 不执行模型中的自定义代码
                local_files_only=True,
            )
            self.model.to(self.device)
            self.model.eval()

            logger.info("✅ BERT模型加载完成")
            logger.info(f"📊 模型参数量: {self.model.num_parameters()}")

        except Exception as e:
            logger.error(f"❌ BERT模型加载失败: {e}")
            raise

    def extract_features(
        self, texts: list[str], use_cache: bool = True, batch_size: int = 8
    ) -> np.ndarray:
        """
        提取BERT语义特征

        Args:
            texts: 文本列表
            use_cache: 是否使用缓存
            batch_size: 批处理大小

        Returns:
            BERT特征向量 (N, 768)
        """
        features = []
        texts_to_process = []
        indices = []

        # 检查缓存
        if use_cache:
            with self.cache_lock:
                for i, text in enumerate(texts):
                    if text in self.embedding_cache:
                        features.append((i, self.embedding_cache[text]))
                    else:
                        texts_to_process.append(text)
                        indices.append(i)
        else:
            texts_to_process = texts
            indices = list(range(len(texts)))

        # 批量处理未缓存的文本
        if texts_to_process:
            batch_features = self._extract_batch(texts_to_process, batch_size)

            # 更新缓存
            if use_cache:
                with self.cache_lock:
                    for text, feature in zip(texts_to_process, batch_features, strict=False):
                        self.embedding_cache[text] = feature

            # 添加到结果
            for idx, feature in zip(indices, batch_features, strict=False):
                features.append((idx, feature))

        # 按原始顺序排序
        features.sort(key=lambda x: x[0])
        result = np.array([f[1] for f in features])

        return result

    def _extract_batch(self, texts: list[str], batch_size: int = 8) -> np.ndarray:
        """批量提取BERT特征"""
        all_features = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            try:
                # Tokenize
                inputs = self.tokenizer(
                    batch_texts, padding=True, truncation=True, max_length=512, return_tensors="pt"
                )

                # 移动到设备
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # 提取特征
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    # 使用[CLS] token的输出作为句子表示
                    cls_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                    all_features.append(cls_embeddings)

            except Exception as e:
                logger.error(f"❌ 批量特征提取失败: {e}")
                # 返回零向量
                all_features.append(np.zeros((len(batch_texts), 768)))

        return np.vstack(all_features)

    def save_cache(self, cache_file: str) -> None:
        """保存嵌入缓存"""
        try:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with self.cache_lock:
                # 安全修复: 使用joblib替代pickle保存嵌入缓存
                joblib.dump(self.embedding_cache, cache_file)
            logger.info(f"💾 嵌入缓存已保存: {cache_file}")
        except Exception as e:
            logger.error(f"❌ 缓存保存失败: {e}")

    def load_cache(self, cache_file: str) -> Any | None:
        """加载嵌入缓存"""
        try:
            if os.path.exists(cache_file):
                with self.cache_lock:
                    # 安全修复: 使用joblib替代pickle加载嵌入缓存
                    self.embedding_cache = joblib.load(cache_file)
                logger.info(f"📂 嵌入缓存已加载: {cache_file} ({len(self.embedding_cache)}条)")
        except Exception as e:
            logger.warning(f"⚠️ 缓存加载失败: {e}")


class BERTSemanticIntentClassifier:
    """BERT语义增强意图分类器"""

    def __init__(self, config: BERTIntentConfig = None):
        """
        初始化BERT语义增强意图分类器

        Args:
            config: 配置对象
        """
        self.config = config or BERTIntentConfig()

        # 创建必要目录
        os.makedirs(self.config.model_dir, exist_ok=True)
        os.makedirs(self.config.data_dir, exist_ok=True)

        # BERT特征提取器
        self.bert_extractor = None
        if self.config.use_bert_features:
            try:
                self.bert_extractor = BERTFeatureExtractor(
                    model_name=self.config.default_model, model_paths=self.config.local_bert_models
                )
                # 加载嵌入缓存
                if self.config.cache_embeddings:
                    self.bert_extractor.load_cache(self.config.embedding_cache_file)
            except Exception as e:
                logger.warning(f"⚠️ BERT特征提取器初始化失败: {e},将仅使用TF-IDF特征")
                self.config.use_bert_features = False

        # TF-IDF向量化器
        self.tfidf_vectorizer = None
        if self.config.use_tfidf_features:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=self.config.max_features,
                ngram_range=self.config.ngram_range,
                min_df=1,
                max_df=0.95,
            )

        # 特征标准化
        self.bert_scaler = StandardScaler()
        self.tfidf_scaler = StandardScaler()
        self.text_stats_scaler = StandardScaler()

        # 标签编码器
        self.label_encoder = LabelEncoder()

        # 意图分类器
        self.intent_classifier = None

        # 训练统计
        self.training_stats = {
            "trained": False,
            "training_time": 0.0,
            "accuracy": 0.0,
            "training_samples": 0,
        }

        # 性能统计
        self.performance_stats = defaultdict(list)

        logger.info("🤖 BERT语义增强意图分类器初始化完成")
        logger.info(f"📊 BERT特征: {self.config.use_bert_features}")
        logger.info(f"📊 TF-IDF特征: {self.config.use_tfidf_features}")

    def _extract_combined_features(self, texts: list[str]) -> np.ndarray:
        """
        提取组合特征(BERT + TF-IDF + 文本统计)

        Args:
            texts: 文本列表

        Returns:
            组合特征矩阵
        """
        features_list = []

        # 1. BERT语义特征
        if self.config.use_bert_features and self.bert_extractor:
            start_time = time.time()
            bert_features = self.bert_extractor.extract_features(
                texts, use_cache=self.config.cache_embeddings
            )
            # 检查scaler是否已fitted
            if hasattr(self.bert_scaler, "scale_"):
                bert_features = self.bert_scaler.transform(bert_features)
            features_list.append(bert_features * self.config.bert_feature_weight)

            extract_time = time.time() - start_time
            self.performance_stats["bert_extraction_time"].append(extract_time)
            logger.debug(f"BERT特征提取: {extract_time:.3f}秒")

        # 2. TF-IDF特征
        if self.config.use_tfidf_features and self.tfidf_vectorizer:
            start_time = time.time()
            if hasattr(self.tfidf_vectorizer, "vocabulary_"):
                tfidf_features = self.tfidf_vectorizer.transform(texts).toarray()
                # 检查scaler是否已fitted
                if hasattr(self.tfidf_scaler, "scale_"):
                    tfidf_features = self.tfidf_scaler.transform(tfidf_features)
                features_list.append(tfidf_features * self.config.tfidf_feature_weight)

                extract_time = time.time() - start_time
                self.performance_stats["tfidf_extraction_time"].append(extract_time)
                logger.debug(f"TF-IDF特征提取: {extract_time:.3f}秒")

        # 3. 文本统计特征
        if self.config.use_text_stats:
            text_stats = self._extract_text_stats(texts)
            # 检查scaler是否已fitted
            if hasattr(self.text_stats_scaler, "scale_"):
                text_stats = self.text_stats_scaler.transform(text_stats)
            features_list.append(text_stats * self.config.text_stats_weight)

        # 拼接所有特征
        if features_list:
            combined_features = np.hstack(features_list)
            return combined_features
        else:
            raise ValueError("至少需要一种特征类型")

    def _extract_text_stats(self, texts: list[str]) -> np.ndarray:
        """提取文本统计特征"""
        features = []
        for text in texts:
            # 文本长度
            length = len(text)
            # 词数
            word_count = len(text.split())
            # 包含问号
            has_question = 1 if any(q in text for q in ["什么", "怎么", "如何", "为什么"]) else 0
            # 包含命令词
            has_command = (
                1 if any(c in text for c in ["启动", "停止", "开启", "关闭", "运行"]) else 0
            )
            # 包含技术词
            has_tech = 1 if any(t in text for t in ["代码", "程序", "系统", "数据库", "API"]) else 0
            # 包含情感词
            has_emotion = 1 if any(e in text for e in ["想", "心情", "感觉", "爱", "喜欢"]) else 0

            features.append([length, word_count, has_question, has_command, has_tech, has_emotion])

        return np.array(features)

    def train(self, texts: list[str], labels: list[str], test_size: float = 0.2) -> dict[str, Any]:
        """
        训练意图分类器

        Args:
            texts: 训练文本
            labels: 意图标签
            test_size: 测试集比例

        Returns:
            训练结果字典
        """
        logger.info("🚀 开始训练BERT语义增强意图分类器")
        logger.info(f"📊 训练样本数: {len(texts)}")

        if len(texts) < 4:
            raise ValueError(f"训练样本太少({len(texts)}个),至少需要4个样本")

        start_time = time.time()

        # 编码标签
        y = self.label_encoder.fit_transform(labels)
        num_classes = len(self.label_encoder.classes_)
        min_samples_per_class = min(sum(y == i) for i in range(num_classes))

        if min_samples_per_class < 2:
            raise ValueError(
                f"每个意图类别至少需要2个样本,最少的类别只有{min_samples_per_class}个样本"
            )

        # 先训练各种特征提取器和标准化器

        # 1. 训练TF-IDF向量化器
        if self.config.use_tfidf_features and self.tfidf_vectorizer:
            logger.info("📊 训练TF-IDF向量化器...")
            self.tfidf_vectorizer.fit(texts)

        # 2. 训练BERT特征标准化器
        if self.config.use_bert_features and self.bert_extractor:
            logger.info("📊 训练BERT特征标准化器...")
            bert_features = self.bert_extractor.extract_features(texts, use_cache=True)
            self.bert_scaler.fit(bert_features)

        # 3. 训练文本统计标准化器
        if self.config.use_text_stats:
            logger.info("📊 训练文本统计标准化器...")
            text_stats = self._extract_text_stats(texts)
            self.text_stats_scaler.fit(text_stats)

        # 4. 提取所有特征
        logger.info("📊 提取组合特征...")
        X = self._extract_combined_features(texts)

        # 5. 划分训练集和测试集
        logger.info("📊 划分训练集和测试集...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        # 6. 创建集成分类器
        self.intent_classifier = self._build_ensemble_classifier()

        # 7. 训练分类器
        logger.info("🎯 训练集成分类器...")
        self.intent_classifier.fit(X_train, y_train)

        # 8. 评估
        logger.info("📊 评估模型性能...")
        y_pred = self.intent_classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        training_time = time.time() - start_time

        # 更新统计
        self.training_stats = {
            "trained": True,
            "training_time": training_time,
            "accuracy": accuracy,
            "training_samples": len(texts),
        }

        # 保存模型
        self._save_model()

        # 保存嵌入缓存
        if self.bert_extractor:
            self.bert_extractor.save_cache(self.config.embedding_cache_file)

        logger.info("✅ 训练完成!")
        logger.info(f"📊 准确率: {accuracy:.2%}")
        logger.info(f"⏱️ 训练时间: {training_time:.2f}秒")

        # 打印分类报告
        logger.info("\n分类报告:")
        logger.info(classification_report(y_test, y_pred, target_names=self.label_encoder.classes_))

        return {
            "accuracy": accuracy,
            "training_time": training_time,
            "training_samples": len(texts),
            "classification_report": classification_report(
                y_test, y_pred, target_names=self.label_encoder.classes_, output_dict=True
            ),
        }

    def _build_ensemble_classifier(self) -> VotingClassifier:
        """构建集成分类器"""
        # 基础分类器
        rf = RandomForestClassifier(n_estimators=100, max_depth=20, random_state=42, n_jobs=-1)

        gb = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)

        svm = SVC(kernel="rbf", probability=True, random_state=42)

        lr = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1)

        # 集成分类器
        ensemble = VotingClassifier(
            estimators=[("rf", rf), ("gb", gb), ("svm", svm), ("lr", lr)], voting="soft"  # 软投票
        )

        return ensemble

    def predict(self, texts: list[str], return_proba: bool = False) -> list[Any]:
        """
        预测意图

        Args:
            texts: 输入文本列表
            return_proba: 是否返回概率

        Returns:
            预测结果列表
        """
        if not self.training_stats["trained"]:
            raise ValueError("分类器未训练,请先调用train()方法")

        start_time = time.time()

        # 提取特征
        features = self._extract_combined_features(texts)

        # 预测
        if return_proba:
            predictions_proba = self.intent_classifier.predict_proba(features)
            results = []
            for _i, proba in enumerate(predictions_proba):
                # 获取top-3预测
                top3_indices = np.argsort(proba)[-3:][::-1]
                top3_results = [
                    {"intent": self.label_encoder.classes_[idx], "confidence": float(proba[idx])}
                    for idx in top3_indices
                ]
                results.append(top3_results)
        else:
            predictions = self.intent_classifier.predict(features)
            results = [self.label_encoder.classes_[pred] for pred in predictions]

        predict_time = time.time() - start_time
        self.performance_stats["prediction_time"].append(predict_time)

        logger.debug(f"预测完成: {predict_time:.3f}秒")

        return results

    def predict_single(self, text: str, return_proba: bool = True) -> Any:
        """
        预测单个文本的意图

        Args:
            text: 输入文本
            return_proba: 是否返回概率

        Returns:
            预测结果
        """
        results = self.predict([text], return_proba=return_proba)
        return results[0]

    def _save_model(self) -> Any:
        """保存模型"""
        try:
            model_file = os.path.join(
                self.config.model_dir,
                f"bert_intent_classifier_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib",
            )

            model_data = {
                "classifier": self.intent_classifier,
                "label_encoder": self.label_encoder,
                "bert_scaler": self.bert_scaler,
                "tfidf_scaler": self.tfidf_scaler,
                "config": self.config,
                "training_stats": self.training_stats,
            }

            # 安全修复: 使用joblib替代pickle
            joblib.dump(model_data, model_file)

            logger.info(f"💾 模型已保存: {model_file}")
        except Exception as e:
            logger.error(f"❌ 模型保存失败: {e}")

    def _load_model(self, model_file: str) -> Any:
        """加载模型"""
        try:
            # 安全修复: 使用joblib替代pickle
            model_data = joblib.load(model_file)

            self.intent_classifier = model_data["classifier"]
            self.label_encoder = model_data["label_encoder"]
            self.bert_scaler = model_data["bert_scaler"]
            self.tfidf_scaler = model_data["tfidf_scaler"]
            self.config = model_data["config"]
            self.training_stats = model_data["training_stats"]

            logger.info(f"📂 模型已加载: {model_file}")
            logger.info(f"📊 训练准确率: {self.training_stats['accuracy']:.2%}")
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise

    def get_performance_stats(self) -> dict[str, Any]:
        """获取性能统计"""
        stats = {"training_stats": self.training_stats, "performance_stats": {}}

        for key, values in self.performance_stats.items():
            if values:
                stats["performance_stats"][key] = {
                    "count": len(values),
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                }

        return stats


# 便捷函数
def get_bert_intent_classifier() -> BERTSemanticIntentClassifier:
    """获取BERT语义增强意图分类器单例"""
    classifier = BERTSemanticIntentClassifier()
    return classifier


# 测试
async def test_bert_intent_classifier():
    """测试BERT语义增强意图分类器"""
    print("🧪 测试BERT语义增强意图分类器")
    print("=" * 60)

    # 创建分类器
    classifier = get_bert_intent_classifier()

    # 训练数据
    training_data = [
        ("帮我分析这段代码", "TECHNICAL"),
        ("系统性能怎么样", "TECHNICAL"),
        ("我想妈妈了", "EMOTIONAL"),
        ("心情不太好", "EMOTIONAL"),
        ("爸爸在忙什么", "FAMILY"),
        ("家里的聚会准备好了吗", "FAMILY"),
        ("教我怎么用Python", "LEARNING"),
        ("学习新知识", "LEARNING"),
        ("启动监控系统", "COMMAND"),
        ("关闭服务器", "COMMAND"),
        ("什么是人工智能", "QUERY"),
        ("怎么部署应用", "QUERY"),
        ("项目进度如何", "WORK"),
        ("工作安排好了吗", "WORK"),
    ]

    texts = [item[0] for item in training_data]
    labels = [item[1] for item in training_data]

    # 训练
    print("\n🚀 开始训练...")
    classifier.train(texts, labels)

    # 测试预测
    print("\n📝 测试预测:")
    test_texts = [
        "帮我优化代码性能",
        "我觉得很伤心",
        "家人健康最重要",
        "系统部署在哪里",
    ]

    for text in test_texts:
        prediction = classifier.predict_single(text, return_proba=True)
        print(f"\n输入: {text}")
        print(f"预测: {prediction[0]['intent']} (置信度: {prediction[0]['confidence']:.2%})")
        if len(prediction) > 1:
            print("Top-3预测:")
            for i, pred in enumerate(prediction[:3], 1):
                print(f"  {i}. {pred['intent']}: {pred['confidence']:.2%}")

    # 性能统计
    print("\n📊 性能统计:")
    stats = classifier.get_performance_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    print("\n✅ 测试完成!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_bert_intent_classifier())
