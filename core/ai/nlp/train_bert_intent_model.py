#!/usr/bin/env python3

"""
基于BERT的意图识别模型训练脚本
BERT-based Intent Recognition Model Training Script

使用预训练BERT模型进行迁移学习
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset

from core.logging_config import setup_logging

# 配置
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 设置使用国内镜像源
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 配置
MODEL_SAVE_DIR = Path("/Users/xujian/Athena工作平台/models/bert_intent_v1")
MAX_LENGTH = 128
BATCH_SIZE = 16
NUM_EPOCHS = 3
LEARNING_RATE = 2e-5

# 使用中文BERT预训练模型
BERT_MODEL_NAME = "hfl/chinese-bert-wwm-ext"  # 使用哈工大的中文BERT


def load_all_training_data() -> list[dict[str, Any]]:
    """加载所有可用的训练数据"""
    logger.info("📂 加载所有训练数据...")

    all_data = []

    # 数据源列表
    data_sources = [
        "/Users/xujian/Athena工作平台/data/training/aggregated_training_data_20260115_191513.json",
        "/Users/xujian/Athena工作平台/data/intent_recognition/training_data_unified_invalidation_v1.json",
        "/Users/xujian/Athena工作平台/data/intent_recognition/training_data_patent_enhanced_v2.json",
        "/Users/xujian/Athena工作平台/data/intent_recognition/training_data_augmented.json",
        "/Users/xujian/Athena工作平台/data/intent_recognition/enhanced_training_data.json",
    ]

    for source_path in data_sources:
        if not Path(source_path).exists():
            logger.info(f"   跳过不存在的文件: {source_path}")
            continue

        try:
            with open(source_path, encoding="utf-8") as f:
                data = json.load(f)

            # 处理不同的数据格式
            if isinstance(data, dict) and "data" in data:
                samples = data["data"]
            elif isinstance(data, list):
                samples = data
            else:
                logger.warning(f"   未知格式: {source_path}")
                continue

            # 标准化数据格式
            normalized = []
            for item in samples:
                if isinstance(item, dict) and "text" in item and "intent" in item:
                    normalized.append(
                        {"text": str(item["text"]).strip(), "intent": str(item["intent"]).strip()}
                    )

            all_data.extend(normalized)
            logger.info(f"   ✅ 加载 {len(normalized)} 条样本 (来源: {Path(source_path).name})")

        except Exception as e:
            logger.warning(f"   ⚠️ 加载失败 {source_path}: {e}")

    logger.info(f"✅ 总计加载 {len(all_data)} 条训练样本")
    return all_data


def optimize_training_data(raw_data: list[dict]) -> list[dict[str, Any]]:
    """优化训练数据"""
    logger.info("🔧 优化训练数据...")

    # 去重
    seen = set()
    unique_data = []
    for item in raw_data:
        text_hash = hash(item["text"])
        if text_hash not in seen:
            seen.add(text_hash)
            unique_data.append(item)

    logger.info(f"   去重后: {len(unique_data)} 条样本")

    # 数据清洗
    cleaned_data = []
    for item in unique_data:
        text = item["text"].strip()
        if len(text) >= 5:  # 过滤过短文本
            cleaned_data.append({"text": text, "intent": item["intent"]})

    logger.info(f"   清洗后: {len(cleaned_data)} 条样本")

    # 意图分布统计
    intent_counts = {}
    for item in cleaned_data:
        intent = item["intent"]
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    logger.info(f"   意图类别数: {len(intent_counts)}")

    # 过滤低频类别(样本数≥50)
    min_threshold = 50
    valid_intents = {intent for intent, count in intent_counts.items() if count >= min_threshold}
    filtered_data = [item for item in cleaned_data if item["intent"] in valid_intents]

    removed = len(cleaned_data) - len(filtered_data)
    removed_intents = len(intent_counts) - len(valid_intents)
    logger.info(f"   过滤样本数<{min_threshold}: 移除{removed_intents}个类别,{removed}条样本")

    # 重新统计
    filtered_counts = {}
    for item in filtered_data:
        intent = item["intent"]
        filtered_counts[intent] = filtered_counts.get(intent, 0) + 1

    logger.info(f"   最终样本数: {len(filtered_data)}")
    logger.info(f"   最终类别数: {len(filtered_counts)}")
    logger.info(f"   平均每类: {len(filtered_data) / len(filtered_counts):.1f}")

    # 显示高频意图
    top_intents = sorted(filtered_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    logger.info("   高频意图 Top15:")
    for intent, count in top_intents:
        logger.info(f"      {intent}: {count}")

    return filtered_data


class IntentDataset(Dataset):
    """意图识别数据集"""

    def __init__(
        self, texts: list[str], labels: list[int], tokenizer, max_length: int = MAX_LENGTH
    ):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor(label, dtype=torch.long),
        }


def train_bert_model_pytorch(training_data: list[dict]) -> dict[str, Any]:
    """使用PyTorch训练BERT意图识别模型"""
    logger.info("🚀 开始训练BERT意图识别模型(PyTorch原生实现)...")

    # 准备数据
    texts = [item["text"] for item in training_data]
    labels = [item["intent"] for item in training_data]

    # 创建标签映射
    unique_intents = sorted(set(labels))
    intent_to_id = {intent: idx for idx, intent in enumerate(unique_intents)}
    id_to_intent = {idx: intent for intent, idx in intent_to_id.items()}

    # 转换标签为ID
    label_ids = [intent_to_id[label] for label in labels]

    logger.info(f"   训练样本数: {len(texts)}")
    logger.info(f"   意图类别数: {len(unique_intents)}")

    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        texts, label_ids, test_size=0.15, random_state=42, stratify=label_ids
    )

    logger.info(f"   训练集: {len(X_train)}")
    logger.info(f"   测试集: {len(X_test)}")

    # 检查设备
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"   使用设备: {device}")

    # 加载tokenizer和模型
    logger.info(f"   加载预训练模型: {BERT_MODEL_NAME}")

    try:
        from torch.optim import AdamW
        from tqdm import tqdm
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL_NAME, trust_remote_code=True)

        model = AutoModelForSequenceClassification.from_pretrained(
            BERT_MODEL_NAME, num_labels=len(unique_intents), trust_remote_code=True
        )

        model = model.to(device)

        # 创建数据集和数据加载器
        train_dataset = IntentDataset(X_train, y_train, tokenizer)
        test_dataset = IntentDataset(X_test, y_test, tokenizer)

        train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE * 2)

        # 优化器
        optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)

        # 训练循环
        logger.info(f"   开始训练 ({NUM_EPOCHS} 轮)...")

        best_accuracy = 0.0

        for epoch in range(NUM_EPOCHS):
            model.train()
            total_loss = 0

            for batch in tqdm(train_loader, desc=f"Epoch {epoch + 1}/{NUM_EPOCHS}"):
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels_batch = batch["labels"].to(device)

                model.zero_grad()

                outputs = model(
                    input_ids=input_ids, attention_mask=attention_mask, labels=labels_batch
                )

                loss = outputs.loss
                total_loss += loss.item()

                loss.backward()
                optimizer.step()

            avg_loss = total_loss / len(train_loader)
            logger.info(f"   Epoch {epoch + 1}: 平均损失 = {avg_loss:.4f}")

            # 评估
            model.eval()
            predictions = []
            true_labels = []

            with torch.no_grad():
                for batch in test_loader:
                    input_ids = batch["input_ids"].to(device)
                    attention_mask = batch["attention_mask"].to(device)
                    labels_batch = batch["labels"].to(device)

                    outputs = model(input_ids=input_ids, attention_mask=attention_mask)

                    preds = torch.argmax(outputs.logits, dim=-1)

                    predictions.extend(preds.cpu().numpy())
                    true_labels.extend(labels_batch.cpu().numpy())

            accuracy = accuracy_score(true_labels, predictions)
            logger.info(f"   Epoch {epoch + 1}: 测试集准确率 = {accuracy:.2%}")

            # 保存最佳模型
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)
                model.save_pretrained(str(MODEL_SAVE_DIR))
                tokenizer.save_pretrained(str(MODEL_SAVE_DIR))
                logger.info(f"   ✅ 保存最佳模型 (准确率: {accuracy:.2%})")

        # 最终评估
        logger.info("   最终评估...")

        # 在最终测试集上评估
        model.eval()
        final_predictions = []
        final_true_labels = []

        with torch.no_grad():
            for batch in test_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels_batch = batch["labels"].to(device)

                outputs = model(input_ids=input_ids, attention_mask=attention_mask)

                preds = torch.argmax(outputs.logits, dim=-1)

                final_predictions.extend(preds.cpu().numpy())
                final_true_labels.extend(labels_batch.cpu().numpy())

        unique_labels_test = sorted(set(final_true_labels))
        target_names = [unique_intents[i] for i in unique_labels_test]

        report = classification_report(
            final_true_labels,
            final_predictions,
            labels=unique_labels_test,
            target_names=target_names,
            zero_division=0.0,
        )
        logger.info(f"   分类报告:\n{report}")

        # 保存标签映射
        label_map = {
            "intent_to_id": intent_to_id,
            "id_to_intent": id_to_intent,
            "intents": unique_intents,
        }

        with open(MODEL_SAVE_DIR / "label_map.json", "w", encoding="utf-8") as f:
            json.dump(label_map, f, ensure_ascii=False, indent=2)

        # 保存训练信息
        training_info = {
            "training_date": datetime.now().isoformat(),
            "model_name": BERT_MODEL_NAME,
            "total_samples": len(training_data),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "num_intents": len(unique_intents),
            "accuracy": float(best_accuracy),
            "intents": unique_intents,
        }

        with open(MODEL_SAVE_DIR / "training_info.json", "w", encoding="utf-8") as f:
            json.dump(training_info, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 模型已保存到: {MODEL_SAVE_DIR}")

        return {"accuracy": best_accuracy, "training_info": training_info}

    except ImportError as e:
        logger.error(f"❌ 缺少依赖库: {e}")
        logger.info("   请安装: pip install transformers torch")
        return None


def main() -> None:
    """主函数"""
    logger.info("🎯 BERT意图识别模型训练")
    logger.info("=" * 60)

    # 1. 加载所有训练数据
    all_data = load_all_training_data()

    # 2. 优化训练数据
    optimized_data = optimize_training_data(all_data)

    # 3. 训练BERT模型
    results = train_bert_model_pytorch(optimized_data)

    if results:
        # 4. 输出总结
        logger.info("=" * 60)
        logger.info("✅ 训练完成!")
        logger.info(f"准确率: {results['accuracy']:.2%}")
        logger.info(f"训练样本数: {results['training_info']['total_samples']}")
        logger.info(f"意图类别数: {results['training_info']['num_intents']}")
        logger.info(f"模型保存位置: {MODEL_SAVE_DIR}")
    else:
        logger.error("❌ 训练失败,请检查依赖库是否安装")


if __name__ == "__main__":
    main()

