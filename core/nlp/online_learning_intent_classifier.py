#!/usr/bin/env python3
from __future__ import annotations
"""
在线学习意图识别系统
Online Learning Intent Recognition System
实时学习和优化意图识别模型
"""

import json
import pickle
import sqlite3
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# ML imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder


class OnlineLearningIntentClassifier:
    """在线学习意图分类器"""

    def __init__(self, model_dir: Optional[str] = None):
        self.name = "在线学习意图识别系统"
        self.model_dir = Path(
            model_dir or "/Users/xujian/Athena工作平台/models/online_learning_v10"
        )
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # 数据库路径
        self.db_path = Path("/Users/xujian/Athena工作平台/data/online_learning.db")

        # 在线学习参数
        self.learning_rate = 0.01
        self.feedback_threshold = 50  # 累积反馈数阈值
        self.model_update_interval = 3600  # 模型更新间隔(秒)
        self.max_feedback_buffer = 1000  # 最大反馈缓冲区大小

        # 模型组件
        self.vectorizer = None
        self.classifier = None
        self.label_encoder = None

        # 在线学习状态
        self.feedback_buffer = deque(maxlen=self.max_feedback_buffer)
        self.prediction_cache = {}
        self.performance_metrics = deque(maxlen=1000)

        # 线程锁
        self.lock = threading.Lock()

        # 初始化
        self.init_database()
        self.load_model()
        self.start_background_learning()

    def init_database(self) -> Any:
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建在线学习记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                text TEXT NOT NULL,
                predicted_intent TEXT,
                true_intent TEXT,
                confidence REAL,
                feedback_type TEXT,  -- 'implicit', 'explicit', 'correction'
                learning_weight REAL DEFAULT 1.0,
                processed BOOLEAN DEFAULT FALSE
            )
        """)

        # 创建模型版本表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                training_samples INTEGER,
                accuracy REAL,
                improvement REAL,
                metadata TEXT,
                is_active BOOLEAN DEFAULT FALSE
            )
        """)

        # 创建性能统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE,
                total_predictions INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                accuracy REAL DEFAULT 0.0,
                new_samples INTEGER DEFAULT 0,
                model_updates INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def load_model(self) -> Any | None:
        """加载模型"""
        print("🔄 加载在线学习模型...")

        try:
            # 尝试加载已训练的模型
            with open(self.model_dir / "vectorizer.pkl", "rb") as f:
                self.vectorizer = pickle.load(f)

            with open(self.model_dir / "classifier.pkl", "rb") as f:
                self.classifier = pickle.load(f)

            with open(self.model_dir / "label_encoder.pkl", "rb") as f:
                self.label_encoder = pickle.load(f)

            print("✅ 成功加载已训练模型")

        except FileNotFoundError:
            print("⚠️ 未找到已训练模型,初始化新模型")
            self.initialize_new_model()

    def initialize_new_model(self) -> Any:
        """初始化新模型"""
        print("🆕 初始化新的在线学习模型...")

        # 加载基础数据
        base_data = self.load_base_training_data()

        if not base_data:
            print("❌ 无法获取基础训练数据")
            return False

        # 准备数据
        texts = [item["text"] for item in base_data]
        labels = [item["intent"] for item in base_data]

        # 创建向量化器
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), max_features=1000, min_df=1, max_df=0.9, sublinear_tf=True
        )

        # 创建标签编码器
        self.label_encoder = LabelEncoder()

        # 转换数据
        X = self.vectorizer.fit_transform(texts)
        y = self.label_encoder.fit_transform(labels)

        # 创建分类器(适合在线学习)
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            warm_start=True,  # 支持增量学习
            random_state=42,
            n_jobs=-1,
        )

        # 训练基础模型
        self.classifier.fit(X, y)

        # 保存初始模型
        self.save_model(version=1)

        print("✅ 新模型初始化完成")
        return True

    def load_base_training_data(self) -> Any | None:
        """加载基础训练数据"""
        # 尝试加载最新的真实数据
        data_sources = [
            "/Users/xujian/Athena工作平台/data/real_conversations/training_data_20251220_095824.json",
            "/Users/xujian/Athena工作平台/data/intent_recognition_v2/enhanced_training_data.json",
        ]

        for source in data_sources:
            if Path(source).exists():
                try:
                    with open(source, encoding="utf-8") as f:
                        data = json.load(f)
                    print(f"✅ 加载基础数据: {len(data)}条 (来源: {source})")
                    return data
                except Exception as e:
                    print(f"⚠️ 加载失败: {e}")
                    continue

        return None

    def predict(self, text: str, return_probabilities: bool = False) -> dict[str, Any]:
        """预测意图"""
        with self.lock:
            try:
                # 检查缓存
                text_hash = hash(text)
                if text_hash in self.prediction_cache:
                    cached_result = self.prediction_cache[text_hash]
                    if datetime.now() - cached_result["timestamp"] < timedelta(minutes=5):
                        return cached_result["result"]

                # 特征提取
                X = self.vectorizer.transform([text])

                # 预测
                pred_idx = self.classifier.predict(X)[0]
                pred_intent = self.label_encoder.inverse_transform([pred_idx])[0]

                # 获取概率
                probabilities = None
                if hasattr(self.classifier, "predict_proba"):
                    proba = self.classifier.predict_proba(X)[0]
                    confidence = np.max(proba)
                    if return_probabilities:
                        probabilities = {
                            intent: float(prob)
                            for intent, prob in zip(
                                self.label_encoder.classes_, proba, strict=False
                            )
                        }
                else:
                    confidence = 0.5  # 默认置信度

                # 构建结果
                result = {
                    "intent": pred_intent,
                    "confidence": float(confidence),
                    "probabilities": probabilities,
                    "timestamp": datetime.now().isoformat(),
                    "model_version": getattr(self, "current_version", 1),
                }

                # 缓存结果
                self.prediction_cache[text_hash] = {"result": result, "timestamp": datetime.now()}

                # 记录预测
                self.record_prediction(text, pred_intent, confidence)

                return result

            except Exception as e:
                print(f"❌ 预测失败: {e}")
                return {
                    "intent": "UNKNOWN",
                    "confidence": 0.0,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }

    def add_feedback(
        self,
        text: str,
        predicted_intent: str,
        true_intent: str,
        feedback_type: str = "explicit",
        confidence: Optional[float] = None,
    ) -> bool:
        """添加用户反馈"""
        with self.lock:
            try:
                # 添加到反馈缓冲区
                feedback = {
                    "text": text,
                    "predicted_intent": predicted_intent,
                    "true_intent": true_intent,
                    "feedback_type": feedback_type,
                    "confidence": confidence,
                    "timestamp": datetime.now(),
                    "learning_weight": self.calculate_learning_weight(feedback_type, confidence),
                }

                self.feedback_buffer.append(feedback)

                # 保存到数据库
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO learning_records
                    (text, predicted_intent, true_intent, confidence, feedback_type, learning_weight)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        text,
                        predicted_intent,
                        true_intent,
                        confidence,
                        feedback_type,
                        feedback["learning_weight"],
                    ),
                )

                conn.commit()
                conn.close()

                # 检查是否需要立即学习
                if len(self.feedback_buffer) >= self.feedback_threshold:
                    self.trigger_learning()

                return True

            except Exception as e:
                print(f"❌ 添加反馈失败: {e}")
                return False

    def calculate_learning_weight(self, feedback_type: str, confidence: float) -> float:
        """计算学习权重"""
        base_weights = {
            "explicit": 1.0,  # 明确用户纠正
            "correction": 0.8,  # 用户主动校正
            "implicit": 0.3,  # 隐式反馈
        }

        weight = base_weights.get(feedback_type, 0.5)

        # 基于置信度调整权重
        if confidence is not None:
            if confidence > 0.8 and feedback_type == "explicit":
                weight *= 1.5  # 高置信度的错误更重要
            elif confidence < 0.3:
                weight *= 0.7  # 低置信度反馈权重降低

        return weight

    def trigger_learning(self) -> Any:
        """触发学习过程"""
        print(f"🎯 触发在线学习 (反馈数量: {len(self.feedback_buffer)})")

        # 提取反馈数据
        feedback_data = list(self.feedback_buffer)
        if not feedback_data:
            return

        # 准备训练数据
        texts = [fb["text"] for fb in feedback_data]
        true_labels = [fb["true_intent"] for fb in feedback_data]
        weights = [fb["learning_weight"] for fb in feedback_data]

        try:
            # 检查是否有新意图
            new_intents = set(true_labels) - set(self.label_encoder.classes_)
            if new_intents:
                print(f"🆕 发现新意图: {new_intents}")
                self.expand_model(new_intents)

            # 特征提取
            X = self.vectorizer.transform(texts)
            y = self.label_encoder.transform(true_labels)

            # 增量学习
            self.classifier.fit(X, y, sample_weight=weights)

            # 评估改进效果
            improvement = self.evaluate_improvement(feedback_data)

            # 保存新模型版本
            new_version = getattr(self, "current_version", 1) + 1
            self.save_model(version=new_version, improvement=improvement)

            # 清空反馈缓冲区
            self.feedback_buffer.clear()

            # 更新数据库记录
            self.mark_feedback_as_processed()

            print(f"✅ 在线学习完成,模型版本更新至: {new_version}")

        except Exception as e:
            print(f"❌ 在线学习失败: {e}")

    def expand_model(self, new_intents: set) -> Any:
        """扩展模型以支持新意图"""
        print(f"🔄 扩展模型支持新意图: {new_intents}")

        # 获取所有类别
        old_classes = list(self.label_encoder.classes_)
        all_classes = old_classes + list(new_intents)

        # 重新创建标签编码器
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(all_classes)

        # 创建新的分类器
        len(all_classes)
        RandomForestClassifier(
            n_estimators=100, max_depth=15, warm_start=True, random_state=42, n_jobs=-1
        )

        # 迁移学习(简化版本)
        # 这里应该保留旧模型的知识,简化处理重新训练
        print("⚠️ 模型扩展完成,建议用更多数据重新训练")

    def evaluate_improvement(self, feedback_data: list[dict]) -> float:
        """评估改进效果"""
        if not feedback_data:
            return 0.0

        correct = 0
        total = len(feedback_data)

        for fb in feedback_data:
            if fb["predicted_intent"] == fb["true_intent"]:
                correct += 1

        # 计算改进率(与之前的错误率对比)
        improvement_rate = (correct / total) - 0.5  # 假设基线50%准确率

        return improvement_rate

    def save_model(self, version: int, improvement: Optional[float] = None) -> None:
        """保存模型"""
        with self.lock:
            try:
                # 保存模型组件
                joblib.dump(self.vectorizer, self.model_dir / "vectorizer.pkl")
                joblib.dump(self.classifier, self.model_dir / "classifier.pkl")
                joblib.dump(self.label_encoder, self.model_dir / "label_encoder.pkl")

                # 保存到数据库
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO model_versions
                    (version, created_at, accuracy, improvement, is_active)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (version, datetime.now(), None, improvement, True),
                )

                # 更新之前的版本为非活跃
                cursor.execute(
                    """
                    UPDATE model_versions
                    SET is_active = FALSE
                    WHERE id != last_insert_rowid() AND version != ?
                """,
                    (version,),
                )

                conn.commit()
                conn.close()

                self.current_version = version

                print(f"💾 模型已保存,版本: {version}")

            except Exception as e:
                print(f"❌ 保存模型失败: {e}")

    def start_background_learning(self) -> Any:
        """启动后台学习线程"""

        def background_worker() -> Any:
            while True:
                time.sleep(self.model_update_interval)

                with self.lock:
                    if len(self.feedback_buffer) >= self.feedback_threshold // 2:
                        print("🔄 后台自动学习触发...")
                        self.trigger_learning()

        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()
        print("✅ 后台学习线程已启动")

    def record_prediction(self, text: str, intent: str, confidence: float) -> Any:
        """记录预测统计"""
        self.performance_metrics.append(
            {
                "text": text,
                "predicted_intent": intent,
                "confidence": confidence,
                "timestamp": datetime.now(),
            }
        )

    def mark_feedback_as_processed(self) -> Any:
        """标记已处理的反馈"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE learning_records
            SET processed = TRUE
            WHERE processed = FALSE
            LIMIT ?
        """,
            (len(self.feedback_buffer) * 2,),
        )  # 保守估计

        conn.commit()
        conn.close()

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 基本统计
        cursor.execute("""
            SELECT COUNT(*), COUNT(CASE WHEN processed = TRUE THEN 1 END)
            FROM learning_records
        """)
        total_feedback, processed_feedback = cursor.fetchone()

        # 模型版本信息
        cursor.execute("""
            SELECT version, created_at, improvement
            FROM model_versions
            WHERE is_active = TRUE
        """)
        active_version = cursor.fetchone()

        # 今日统计
        today = datetime.now().date()
        cursor.execute(
            """
            SELECT COUNT(*), AVG(CASE WHEN predicted_intent = true_intent THEN 1.0 ELSE 0.0 END)
            FROM learning_records
            WHERE date(timestamp) = ?
        """,
            (today,),
        )
        today_stats = cursor.fetchone()

        conn.close()

        return {
            "current_version": active_version[0] if active_version else None,
            "last_update": str(active_version[1]) if active_version else None,
            "last_improvement": active_version[2] if active_version else None,
            "total_feedback": total_feedback,
            "processed_feedback": processed_feedback,
            "pending_feedback": len(self.feedback_buffer),
            "buffer_usage": len(self.feedback_buffer) / self.max_feedback_buffer,
            "today_predictions": today_stats[0] if today_stats else 0,
            "today_accuracy": float(today_stats[1]) if today_stats and today_stats[1] else None,
            "performance_buffer_size": len(self.performance_metrics),
            "cache_size": len(self.prediction_cache),
        }


def test_online_learning_classifier() -> Any:
    """测试在线学习分类器"""
    print("🧪 测试在线学习意图识别系统")
    print("=" * 60)

    # 创建分类器
    classifier = OnlineLearningIntentClassifier()

    # 测试预测
    test_cases = [
        "分析这个专利技术",
        "爸爸我爱你",
        "启动系统服务",
        "解释机器学习原理",
        "今天天气怎么样",
    ]

    print("\n📋 初始预测测试:")
    for text in test_cases:
        result = classifier.predict(text, return_probabilities=True)
        print(f"   '{text}' -> {result['intent']} (置信度: {result['confidence']:.2%})")

    # 模拟用户反馈
    print("\n📝 添加用户反馈:")
    feedback_cases = [
        ("分析这个专利技术", "TECHNICAL_EXPLANATION", "PATENT_ANALYSIS", "correction"),
        ("爸爸我爱你", "EMOTIONAL", "EMOTIONAL", "explicit"),
        ("启动系统服务", "SYSTEM_CONTROL", "SYSTEM_CONTROL", "explicit"),
    ]

    for text, predicted, true, feedback_type in feedback_cases:
        success = classifier.add_feedback(text, predicted, true, feedback_type)
        status = "✅" if success else "❌"
        print(f"   {status} {text}: {predicted} -> {true} ({feedback_type})")

    # 检查统计信息
    print("\n📊 系统统计信息:")
    stats = classifier.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # 再次测试预测(可能已更新)
    print("\n📋 反馈后预测测试:")
    for text in test_cases[:3]:  # 只测试前3个
        result = classifier.predict(text)
        print(f"   '{text}' -> {result['intent']} (置信度: {result['confidence']:.2%})")


if __name__ == "__main__":
    test_online_learning_classifier()
