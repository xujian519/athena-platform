#!/usr/bin/env python3
from __future__ import annotations
"""
Phase 3: 本地BGE意图识别系统 - 专利代理大规模增强版
Local BGE Intent Recognition System - Patent Agent Large-Scale Enhanced (Phase 3)

基于308,888复审无效决定、5,906专利判决书、14,968审查指南训练
支持50个细粒度意图类别,覆盖专利代理全流程

当前使用: BGE-M3 API服务 (http://127.0.0.1:8766/v1/embeddings)
统一模型: models/intent_recognition/unified_classifier (统一意图分类器)

作者: Athena平台团队
版本: v3.1.0-patent-enhanced
创建: 2026-01-13
更新: 2026-01-13 (切换到大规模生产模型)
"""
import json
import sys
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from core.async_main import async_main
from core.logging_config import setup_logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class LocalBGEPhase3Classifier:
    """本地BGE Phase 3意图识别器(法律语料增强版)"""

    def __init__(self, model_dir: str | None = None):
        """初始化分类器并加载训练好的模型

        Args:
            model_dir: 训练好的模型目录路径,默认使用大规模专利增强模型
        """
        if model_dir is None:
            # 默认使用统一意图分类器 (50类别,覆盖全面)
            model_dir = str(project_root / "models/intent_recognition/unified_classifier")

        self.model_dir = Path(model_dir)
        self.device = self._select_device()

        # BGE模型路径
        self.bge_model_path = "http://127.0.0.1:8766/v1/embeddings"

        self.tokenizer = None
        self.model = None
        self.classifier = None
        self.label_encoder = None

        # 性能统计
        self.stats = {"total_predictions": 0, "total_encode_time": 0, "total_predict_time": 0}

        # 加载模型
        self._load_models()

        logger.info("✅ Phase 3 BGE分类器初始化完成")
        logger.info(f"📊 设备: {self.device}")
        logger.info(f"📂 模型目录: {self.model_dir}")

    def _select_device(self) -> torch.device:
        """选择计算设备"""
        if torch.backends.mps.is_available():
            logger.info("🍎 使用MPS GPU加速(Apple Silicon)")
            return torch.device("mps")
        elif torch.cuda.is_available():
            logger.info("✅ 使用CUDA GPU加速")
            return torch.device("cuda")
        else:
            logger.info("⚠️ 使用CPU模式")
            return torch.device("cpu")

    def _load_models(self) -> Any:
        """加载训练好的模型和配置"""
        try:
            # 1. 加载配置
            config_file = self.model_dir / "config.json"
            if config_file.exists():
                with open(config_file, encoding="utf-8") as f:
                    self.config = json.load(f)
                logger.info("📋 模型配置加载成功")
                logger.info(f"   - 意图类别数: {self.config['num_classes']}")
                logger.info(f"   - 训练时间: {self.config['saved_at']}")
            else:
                raise FileNotFoundError(f"配置文件不存在: {config_file}")

            # 2. 加载分类器和标签编码器
            classifier_file = self.model_dir / "classifier.joblib"
            encoder_file = self.model_dir / "label_encoder.joblib"

            if not classifier_file.exists():
                raise FileNotFoundError(f"分类器文件不存在: {classifier_file}")
            if not encoder_file.exists():
                raise FileNotFoundError(f"编码器文件不存在: {encoder_file}")

            logger.info("📦 加载RandomForest分类器...")
            self.classifier = joblib.load(classifier_file)

            logger.info("🏷️ 加载标签编码器...")
            self.label_encoder = joblib.load(encoder_file)

            logger.info(f"✅ 已支持意图类别: {len(self.label_encoder.classes_)} 个")
            for intent in self.label_encoder.classes_:
                logger.info(f"   - {intent}")

            # 3. 加载BGE模型
            logger.info("🤖 加载BGE-M3模型(使用MPS优化)...")
            logger.info(f"   模型路径: {self.bge_model_path}")

            logger.info("📝 加载tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.bge_model_path)

            logger.info("🧠 加载模型权重...")
            with torch.no_grad():
                self.model = AutoModel.from_pretrained(
                    self.bge_model_path,
                    low_cpu_mem_usage=True,
                    torch_dtype=torch.float16 if self.device.type == "mps" else torch.float32,
                )

                logger.info(f"🔄 将模型移动到 {self.device}...")
                self.model = self.model.to(self.device)
                self.model.eval()

            logger.info("✅ BGE-M3模型加载成功")
            logger.info("📊 向量维度: 1024 (BGE-M3)")
            logger.info(
                f"⚡ 设备: {self.device} ({'FP16加速' if self.device.type == 'mps' else 'FP32'})"
            )

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise

    def _mean_pooling(self, token_embeddings, attention_mask) -> None:
        """平均池化"""
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )

    def encode_texts(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """编码文本为向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            np.ndarray: 嵌入矩阵 (N x 1024)
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            try:
                # Tokenize
                inputs = self.tokenizer(
                    batch_texts, padding=True, truncation=True, max_length=512, return_tensors="pt"
                )

                # 移动到设备
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # 编码 - 使用平均池化
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    # 使用平均池化而非[CLS] token
                    batch_embeddings = self._mean_pooling(
                        outputs.last_hidden_state, inputs["attention_mask"]
                    )
                    batch_embeddings = batch_embeddings.cpu().numpy()

                embeddings.extend(batch_embeddings)

            except Exception as e:
                logger.error(f"❌ 批量编码失败: {e}")
                # 使用零向量填充
                embeddings.extend([np.zeros(1024)] * len(batch_texts))

        return np.array(embeddings)

    def predict(self, text: str, top_k: int = 3) -> dict[str, Any]:
        """预测意图

        Args:
            text: 输入文本
            top_k: 返回top-k结果

        Returns:
            Dict: 预测结果
        """
        start = time.time()
        self.stats["total_predictions"] += 1

        try:
            # 编码
            encode_start = time.time()
            embedding = self.encode_texts([text])[0]
            encode_time = time.time() - encode_start

            # 预测
            predict_start = time.time()
            if self.classifier is None:
                return {"intent": "UNKNOWN", "confidence": 0.0, "error": "Model not loaded"}

            prediction = self.classifier.predict([embedding])[0]
            probabilities = self.classifier.predict_proba([embedding])[0]
            predict_time = time.time() - predict_start

            # 解码
            intent_label = self.label_encoder.inverse_transform([prediction])[0]
            confidence = float(np.max(probabilities))

            # Top-k
            topk_indices = np.argsort(probabilities)[-top_k:][::-1]
            topk_intents = self.label_encoder.inverse_transform(topk_indices)
            topk_probs = probabilities[topk_indices]

            inference_time = time.time() - start

            # 更新统计
            self.stats["total_encode_time"] += encode_time
            self.stats["total_predict_time"] += predict_time

            return {
                "intent": str(intent_label),
                "confidence": float(confidence),
                "inference_time": float(inference_time),
                "encode_time": float(encode_time),
                "predict_time": float(predict_time),
                "top_k": [
                    {"intent": str(intent), "probability": float(prob)}
                    for intent, prob in zip(topk_intents, topk_probs, strict=False)
                ],
            }

        except Exception as e:
            logger.error(f"❌ 预测失败: {e}")
            return {"intent": "UNKNOWN", "confidence": 0.0, "error": str(e)}

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_predictions": self.stats["total_predictions"],
            "avg_encode_time": (
                self.stats["total_encode_time"] / self.stats["total_predictions"]
                if self.stats["total_predictions"] > 0
                else 0
            ),
            "avg_predict_time": (
                self.stats["total_predict_time"] / self.stats["total_predictions"]
                if self.stats["total_predictions"] > 0
                else 0
            ),
            "supported_intents": len(self.label_encoder.classes_) if self.label_encoder else 0,
            "intent_classes": list(self.label_encoder.classes_) if self.label_encoder else [],
        }

    def get_model_info(self) -> dict[str, Any]:
        """获取模型信息"""
        return {
            "version": "Phase 3 - Legal Corpus Enhanced",
            "model_dir": str(self.model_dir),
            "device": str(self.device),
            "bge_model": self.bge_model_path,
            "num_classes": self.config.get("num_classes", 0),
            "intent_classes": self.config.get("intent_classes", []),
            "saved_at": self.config.get("saved_at", ""),
            "model_type": self.config.get("model_type", ""),
        }


# 测试代码
@async_main
async def main():
    """主程序 - 测试模型"""
    print("🎯 Phase 3: 本地BGE意图识别系统 - 法律语料增强版")
    print("=" * 70)

    # 1. 初始化分类器
    print("\n🤖 初始化Phase 3分类器...")
    classifier = LocalBGEPhase3Classifier()

    # 2. 显示模型信息
    print("\n📋 模型信息:")
    model_info = classifier.get_model_info()
    print(f"  版本: {model_info['version']}")
    print(f"  设备: {model_info['device']}")
    print(f"  意图类别数: {model_info['num_classes']}")

    # 3. 测试预测
    print("\n🧪 测试预测 (法律相关意图):")
    test_cases = [
        ("查询盗窃罪的法律规定", "LEGAL_QUERY"),
        ("搜索发明专利的无效案例", "CASE_SEARCH_INVALIDATION"),
        ("分析这个故意伤害案例", "CRIME_ANALYSIS"),
        ("预测醉驾案件的判决结果", "JUDGMENT_PREDICTION"),
        ("研究正当防卫的法律理论", "LEGAL_RESEARCH"),
        ("检索人工智能专利", "PATENT_SEARCH"),
        ("帮我写Python代码", "CODE_GENERATION"),
        ("分析数据报告", "DATA_ANALYSIS"),
    ]

    correct = 0
    for text, expected in test_cases:
        result = classifier.predict(text)
        is_correct = result["intent"] == expected
        if is_correct:
            correct += 1
            status = "✅"
        else:
            status = "❌"

        print(f"{status} '{text}'")
        print(f"   预期: {expected}")
        print(f"   实际: {result['intent']} (置信度: {result['confidence']:.2%})")
        print(f"   耗时: {result['inference_time']*1000:.1f}ms")
        print()

    accuracy = correct / len(test_cases)
    print(f"\n📊 测试准确率: {accuracy:.2%} ({correct}/{len(test_cases)})")

    # 4. 统计信息
    stats = classifier.get_stats()
    print("\n📈 统计信息:")
    print(f"  总预测数: {stats['total_predictions']}")
    print(f"  平均编码时间: {stats['avg_encode_time']*1000:.2f}ms")
    print(f"  平均预测时间: {stats['avg_predict_time']*1000:.2f}ms")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
