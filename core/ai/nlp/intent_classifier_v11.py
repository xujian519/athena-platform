#!/usr/bin/env python3

"""
意图识别模型V11分类器
Intent Recognition Model V11 Classifier

使用改进的集成学习模型
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class IntentClassifierV11:
    """
    意图识别分类器 V11

    使用集成学习模型,准确率达到92.93%
    """

    def __init__(self, model_dir: Optional[str] = None):
        """
        初始化分类器

        Args:
            model_dir: 模型目录路径
        """
        self.model_dir = Path(model_dir or "/Users/xujian/Athena工作平台/models/intent_model_v11")

        # 模型组件
        self.vectorizer = None
        self.classifier = None
        self.label_map = None

        # 模型信息
        self.model_info = None
        self.intents = []

        # 初始化
        self._load_model()

    def _load_model(self) -> Any:
        """加载模型组件"""
        try:
            logger.info(f"🔄 加载V11模型: {self.model_dir}")

            # 加载向量化器
            with open(self.model_dir / "vectorizer.pkl", "rb") as f:
                self.vectorizer = pickle.load(f)

            # 加载分类器
            with open(self.model_dir / "classifier.pkl", "rb") as f:
                self.classifier = pickle.load(f)

            # 加载标签映射
            with open(self.model_dir / "label_map.json", encoding="utf-8") as f:
                self.label_map = json.load(f)

            # 加载训练信息
            with open(self.model_dir / "training_info.json", encoding="utf-8") as f:
                self.model_info = json.load(f)

            self.intents = self.label_map["intents"]
            self.id_to_intent = {int(k): v for k, v in self.label_map["id_to_intent"].items()}

            logger.info("✅ V11模型加载成功")
            logger.info(f"   意图类别数: {len(self.intents)}")
            logger.info(f"   模型准确率: {self.model_info['accuracy']:.2%}")

        except Exception as e:
            logger.error(f"❌ V11模型加载失败: {e}")
            raise

    def predict(self, text: str, return_probabilities: bool = False) -> dict[str, Any]:
        """
        预测意图

        Args:
            text: 输入文本
            return_probabilities: 是否返回概率分布

        Returns:
            预测结果字典
        """
        try:
            # 特征提取
            X = self.vectorizer.transform([text])

            # 预测
            pred_idx = self.classifier.predict(X)[0]
            pred_intent = self.id_to_intent[pred_idx]

            # 获取概率
            probabilities = None
            confidence = 0.0

            if hasattr(self.classifier, "predict_proba"):
                proba = self.classifier.predict_proba(X)[0]
                confidence = float(proba[pred_idx])

                if return_probabilities:
                    probabilities = {
                        self.id_to_intent[i]: float(prob) for i, prob in enumerate(proba)
                    }
            else:
                confidence = 0.8

            return {
                "intent": pred_intent,
                "confidence": confidence,
                "probabilities": probabilities,
                "model_version": 11,
                "model_type": "ensemble",
                "intents_count": len(self.intents),
            }

        except Exception as e:
            logger.error(f"❌ 预测失败: {e}")
            return {"intent": "UNKNOWN", "confidence": 0.0, "error": str(e), "model_version": 11}

    def get_model_info(self) -> dict[str, Any]:
        """获取模型信息"""
        return {
            "version": 11,
            "type": "ensemble",
            "accuracy": self.model_info.get("accuracy", 0),
            "cv_accuracy_mean": self.model_info.get("cv_accuracy_mean", 0),
            "num_intents": len(self.intents),
            "feature_dim": self.model_info.get("feature_dim", 0),
            "training_date": self.model_info.get("training_date", ""),
            "intents": self.intents,
        }


# 单例模式
_classifier_instance: IntentClassifierV11 = None


def get_classifier_v11() -> IntentClassifierV11:
    """获取V11分类器单例"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntentClassifierV11()
    return _classifier_instance

