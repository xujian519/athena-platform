#!/usr/bin/env python3
"""
Phase 2: 本地BGE意图识别系统(Transformers直接加载)
Local BGE Intent Recognition System using Transformers

直接使用Transformers库加载本地BGE模型,避免Sentence Transformers兼容性问题

本地模型: models/converted/BAAI/bge-m3/

作者: 小诺·双鱼公主
版本: v2.0.0-fixed
创建: 2025-12-29
"""
import numpy as np

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
from transformers import AutoModel, AutoTokenizer

from core.async_main import async_main
from core.logging_config import setup_logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class LocalBGEPhase2Classifier:
    """本地BGE Phase 2意图识别器(直接使用Transformers)"""

    def __init__(self, use_local_model: bool = True):
        """初始化分类器

        Args:
            use_local_model: 是否使用本地优化模型
        """
        self.use_local_model = use_local_model

        # 本地模型路径 - 使用存在的BGE-M3模型
        if use_local_model:
            # 使用bge-m3模型(实际存在的模型)
            self.model_path = str(project_root / "models/converted/BAAI/bge-m3")
            logger.info(f"📂 使用本地BGE-M3模型: {self.model_path}")
        else:
            # 使用HuggingFace上的bge-m3模型
            self.model_path = "BAAI/bge-m3"
            logger.info(f"🌐 使用HuggingFace模型: {self.model_path}")

        self.device = self._select_device()
        self.tokenizer = None
        self.model = None
        self.classifier = None
        self.label_encoder = LabelEncoder()

        # 性能统计
        self.stats = {"encode_time": [], "predict_time": [], "total_predictions": 0}

        # 初始化模型
        self._initialize_model()

        logger.info("✅ Phase 2 BGE分类器初始化完成")
        logger.info(f"📊 设备: {self.device}")

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

    def _initialize_model(self) -> Any:
        """初始化BGE模型 - MPS优化版本"""
        try:
            logger.info("🤖 加载BGE-M3模型(使用MPS优化)...")

            # 加载tokenizer
            logger.info("📝 加载tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

            # 加载模型 - 使用低内存模式和MPS优化
            logger.info("🧠 加载模型权重(4.3GB,请耐心等待)...")

            with torch.no_grad():  # 禁用梯度计算以加速加载
                self.model = AutoModel.from_pretrained(
                    self.model_path,
                    low_cpu_mem_usage=True,  # 使用低CPU内存模式
                    torch_dtype=(
                        torch.float16 if self.device.type == "mps" else torch.float32
                    ),  # MPS使用FP16加速
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
            logger.error(f"❌ BGE模型加载失败: {e}")
            raise

    def encode_texts(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """编码文本为向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            np.ndarray: 嵌入矩阵 (N x 768)
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

                # 编码
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    # 使用[CLS] token的嵌入
                    batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()

                embeddings.extend(batch_embeddings)

            except Exception as e:
                logger.error(f"❌ 批量编码失败: {e}")
                # 使用零向量填充
                embeddings.extend([np.zeros(768)] * len(batch_texts))

        return np.array(embeddings)

    def train(
        self,
        training_data: list[dict[str, Any]],        test_size: float = 0.2,
        use_cross_validation: bool = True,
    ) -> dict[str, Any]:
        """训练意图分类器

        Args:
            training_data: 训练数据
            test_size: 测试集比例
            use_cross_validation: 是否使用交叉验证

        Returns:
            Dict: 训练结果
        """
        logger.info(f"🎯 开始训练,数据量: {len(training_data)}")

        # 1. 准备数据
        texts = [item["text"] for item in training_data]
        intents = [item["intent"] for item in training_data]

        logger.info("🔄 生成BGE嵌入...")
        start = time.time()
        X = self.encode_texts(texts, batch_size=32)
        encode_time = time.time() - start
        logger.info(f"✅ 嵌入生成完成 ({encode_time:.2f}s)")

        # 2. 编码标签
        y = self.label_encoder.fit_transform(intents)

        logger.info(f"🏷️ 意图类别: {len(self.label_encoder.classes_)}")
        logger.info(f"   {list(self.label_encoder.classes_)}")

        # 3. 划分数据集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        logger.info(f"📊 训练集: {len(X_train)}, 测试集: {len(X_test)}")

        # 4. 交叉验证
        if use_cross_validation:
            logger.info("🔄 5折交叉验证...")
            cv_classifier = RandomForestClassifier(
                n_estimators=100, max_depth=20, random_state=42, n_jobs=-1
            )
            cv_scores = cross_val_score(cv_classifier, X_train, y_train, cv=5)
            logger.info(
                f"📊 交叉验证准确率: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})"
            )

        # 5. 训练最终分类器
        logger.info("🌲 训练RandomForest分类器...")
        train_start = time.time()

        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )

        self.classifier.fit(X_train, y_train)

        train_time = time.time() - train_start
        logger.info(f"✅ 训练完成 ({train_time:.2f}s)")

        # 6. 评估
        logger.info("📈 评估模型...")
        y_pred_train = self.classifier.predict(X_train)
        y_pred_test = self.classifier.predict(X_test)

        train_acc = accuracy_score(y_train, y_pred_train)
        test_acc = accuracy_score(y_test, y_pred_test)
        test_f1 = f1_score(y_test, y_pred_test, average="weighted")

        logger.info(f"📊 训练集准确率: {train_acc:.4f}")
        logger.info(f"📊 测试集准确率: {test_acc:.4f}")
        logger.info(f"📊 测试集F1分数: {test_f1:.4f}")

        # 7. 详细报告
        report = classification_report(
            y_test, y_pred_test, target_names=self.label_encoder.classes_, output_dict=True
        )

        return {
            "train_accuracy": train_acc,
            "test_accuracy": test_acc,
            "test_f1": test_f1,
            "classification_report": report,
            "intent_classes": list(self.label_encoder.classes_),
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "encode_time": encode_time,
            "train_time": train_time,
            "cross_val_scores": cv_scores.tolist() if use_cross_validation else None,
        }

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
            embedding = self.encode_texts([text])[0]

            # 预测
            if self.classifier is None:
                return {"intent": "UNKNOWN", "confidence": 0.0, "error": "Model not trained"}

            prediction = self.classifier.predict([embedding])[0]
            probabilities = self.classifier.predict_proba([embedding])[0]

            # 解码
            intent_label = self.label_encoder.inverse_transform([prediction])[0]
            confidence = float(np.max(probabilities))

            # Top-k
            topk_indices = np.argsort(probabilities)[-top_k:][::-1]
            topk_intents = self.label_encoder.inverse_transform(topk_indices)
            topk_probs = probabilities[topk_indices]

            inference_time = time.time() - start

            return {
                "intent": intent_label,
                "confidence": confidence,
                "inference_time": inference_time,
                "top_k": [
                    {"intent": intent, "probability": float(prob)}
                    for intent, prob in zip(topk_intents, topk_probs, strict=False)
                ],
            }

        except Exception as e:
            logger.error(f"❌ 预测失败: {e}")
            return {"intent": "UNKNOWN", "confidence": 0.0, "error": str(e)}

    def predict_intent(self, text: str, top_k: int = 3) -> dict[str, Any]:
        """预测意图(统一接口方法)

        这是predict()方法的包装器,提供统一的接口格式,
        兼容xiaonuo_unified_gateway.py的调用方式。

        Args:
            text: 输入文本
            top_k: 返回top-k结果

        Returns:
            Dict: {
                'success': bool,
                'intent': str,
                'confidence': float,
                'top_k': list[Dict],
                'inference_time': float,
                'method': str
            }
        """
        try:
            result = self.predict(text, top_k=top_k)

            # 检查是否有错误
            if "error" in result:
                return {
                    "success": False,
                    "intent": "UNKNOWN",
                    "confidence": 0.0,
                    "top_k": [],
                    "inference_time": result.get("inference_time", 0.0),
                    "error": result.get("error"),
                    "method": "bge_phase2",
                }

            # 统一返回格式
            return {
                "success": True,
                "intent": result["intent"],
                "confidence": result["confidence"],
                "top_k": result["top_k"],
                "inference_time": result["inference_time"],
                "method": "bge_phase2",
            }

        except Exception as e:
            logger.error(f"❌ predict_intent调用失败: {e}")
            return {
                "success": False,
                "intent": "UNKNOWN",
                "confidence": 0.0,
                "top_k": [],
                "inference_time": 0.0,
                "error": str(e),
                "method": "bge_phase2",
            }

    def load(self, model_dir: str) -> bool:
        """加载已训练的分类器

        Args:
            model_dir: 模型目录路径

        Returns:
            bool: 是否成功加载
        """
        import joblib

        model_dir = Path(model_dir)

        try:
            # 检查必要文件是否存在
            classifier_file = model_dir / "classifier.joblib"
            encoder_file = model_dir / "label_encoder.joblib"
            config_file = model_dir / "config.json"

            if not all([classifier_file.exists(), encoder_file.exists(), config_file.exists()]):
                logger.warning(f"⚠️ 模型文件不完整: {model_dir}")
                return False

            # 加载分类器和标签编码器
            logger.info(f"📂 加载已训练的分类器: {model_dir}")
            self.classifier = joblib.load(classifier_file)
            self.label_encoder = joblib.load(encoder_file)

            # 加载配置
            with open(config_file, encoding="utf-8") as f:
                json.load(f)

            logger.info("✅ 分类器加载成功")
            logger.info(f"📊 意图类别数: {len(self.label_encoder.classes_)}")
            logger.info(f"🏷️ 类别: {list(self.label_encoder.classes_)}")

            return True

        except Exception as e:
            logger.error(f"❌ 加载分类器失败: {e}")
            return False

    def save(self, model_dir: str) -> Any:
        """保存模型"""
        import joblib

        model_dir = Path(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.classifier, model_dir / "classifier.joblib")
        joblib.dump(self.label_encoder, model_dir / "label_encoder.joblib")

        config = {
            "model_path": self.model_path,
            "device": str(self.device),
            "intent_classes": list(self.label_encoder.classes_),
            "saved_at": datetime.now().isoformat(),
        }

        with open(model_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 模型已保存: {model_dir}")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_predictions": self.stats["total_predictions"],
            "avg_encode_time": (
                np.mean(self.stats["encode_time"]) if self.stats["encode_time"] else 0
            ),
            "avg_predict_time": (
                np.mean(self.stats["predict_time"]) if self.stats["predict_time"] else 0
            ),
        }


@async_main
async def main():
    """主程序"""
    print("🎯 Phase 2: 本地BGE意图识别系统")
    print("=" * 70)

    # 1. 加载数据
    print("\n📂 加载训练数据...")
    training_file = project_root / "data/intent_recognition/training_data.json"

    with open(training_file, encoding="utf-8") as f:
        training_data = json.load(f)

    print(f"✅ 数据加载完成: {len(training_data)} 条")

    # 2. 初始化分类器
    print("\n🤖 初始化本地BGE分类器...")
    classifier = LocalBGEPhase2Classifier(use_local_model=True)

    # 3. 训练
    print("\n🎯 开始训练...")
    train_result = classifier.train(training_data, use_cross_validation=True)

    print("\n📊 训练结果:")
    print(f"  交叉验证准确率: {np.mean(train_result['cross_val_scores']):.2%}")
    print(f"  训练集准确率: {train_result['train_accuracy']:.2%}")
    print(f"  测试集准确率: {train_result['test_accuracy']:.2%}")
    print(f"  测试集F1分数: {train_result['test_f1']:.2%}")
    print(f"  嵌入生成时间: {train_result['encode_time']:.2f}s")
    print(f"  训练时间: {train_result['train_time']:.2f}s")

    # 4. 测试预测
    print("\n🧪 测试预测:")
    test_cases = [
        ("分析这个专利", "PATENT_ANALYSIS"),
        ("检索人工智能专利", "PATENT_SEARCH"),
        ("帮我写Python代码", "CODE_GENERATION"),
        ("谢谢爸爸", "EMOTIONAL"),
        ("启动服务", "SYSTEM_CONTROL"),
        ("审查意见怎么答复", "OPINION_RESPONSE"),
        ("撰写发明专利", "PATENT_DRAFTING"),
        ("分析数据报告", "DATA_ANALYSIS"),
    ]

    correct = 0
    for text, expected in test_cases:
        result = classifier.predict(text)
        is_correct = result["intent"] == expected
        if is_correct:
            correct += 1

        status = "✅" if is_correct else "❌"
        print(f"  {status} '{text}'")
        print(f"     预期: {expected}")
        print(f"     实际: {result['intent']}")
        print(f"     置信度: {result['confidence']:.2%}")
        print(f"     耗时: {result['inference_time']*1000:.1f}ms")

    print(f"\n  测试准确率: {correct}/{len(test_cases)} = {correct/len(test_cases):.2%}")

    # 5. 保存模型
    print("\n💾 保存模型...")
    model_dir = project_root / "models/intent_recognition/unified_classifier"
    classifier.save(model_dir)

    # 6. 总结
    print("\n" + "=" * 70)
    print("🎯 Phase 2 完成总结")
    print("=" * 70)
    print(f"📊 测试集准确率: {train_result['test_accuracy']:.2%}")
    print("🎯 目标准确率: 85%")
    print(f"📈 状态: {'✅ 达标' if train_result['test_accuracy'] >= 0.85 else '⚠️ 接近目标'}")

    improvement = train_result["test_accuracy"] - 0.375  # 从37.5%基线
    print(f"🚀 相比基线提升: +{improvement:.2%}")

    print(f"\n💾 模型保存位置: {model_dir}")
    print("\n下一步:")
    print("  1. 集成到小诺主系统")
    print("  2. 实现在线学习")
    print("  3. 添加知识图谱增强")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
