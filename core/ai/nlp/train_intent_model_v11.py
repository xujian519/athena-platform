#!/usr/bin/env python3

"""
改进版意图识别模型训练脚本
Enhanced Intent Recognition Model Training Script

使用平台所有可用训练数据,采用更优的算法
"""

import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.svm import SVC

from core.logging_config import setup_logging

# 配置
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

MODEL_SAVE_DIR = Path("/Users/xujian/Athena工作平台/models/intent_model_v11")


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
                continue

            # 标准化数据格式
            normalized = []
            for item in samples:
                if isinstance(item, dict) and "text" in item and "intent" in item:
                    normalized.append(
                        {"text": str(item["text"]).strip(), "intent": str(item["intent"]).strip()}
                    )

            all_data.extend(normalized)
            logger.info(f"   ✅ 加载 {len(normalized)} 条样本")

        except Exception as e:
            logger.warning(f"   ⚠️ 加载失败: {e}")

    logger.info(f"✅ 总计加载 {len(all_data)} 条训练样本")
    return all_data


def optimize_training_data(raw_data: list[dict], min_threshold: int = 30) -> list[dict[str, Any]]:
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
        if len(text) >= 5:
            cleaned_data.append({"text": text, "intent": item["intent"]})

    logger.info(f"   清洗后: {len(cleaned_data)} 条样本")

    # 意图分布统计
    intent_counts = {}
    for item in cleaned_data:
        intent = item["intent"]
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    # 过滤低频类别
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


def train_ensemble_model(training_data: list[dict]) -> dict[str, Any]:
    """训练集成模型"""
    logger.info("🚀 开始训练集成意图识别模型...")

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
        texts, label_ids, test_size=0.2, random_state=42, stratify=label_ids
    )

    logger.info(f"   训练集: {len(X_train)}")
    logger.info(f"   测试集: {len(X_test)}")

    # 创建优化的向量化器
    logger.info("   创建TF-IDF向量化器...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=5000,
        min_df=1,
        max_df=0.85,
        sublinear_tf=True,
        analyzer="char_wb",  # 使用字符级n-gram,对中文更友好
    )

    # 转换数据
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    logger.info(f"   特征维度: {X_train_vec.shape[1]}")

    # 创建集成分类器
    logger.info("   创建集成分类器...")

    # 基分类器
    clf_lr = LogisticRegression(max_iter=1000, C=1.0, random_state=42, n_jobs=-1)

    clf_svc = SVC(
        C=1.0, kernel="linear", probability=True, max_iter=2000, random_state=42  # 启用概率预测
    )

    clf_rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=25,
        min_samples_split=3,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1,
    )

    clf_gb = GradientBoostingClassifier(
        n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
    )

    # 创建投票分类器
    ensemble = VotingClassifier(
        estimators=[("lr", clf_lr), ("svc", clf_svc), ("rf", clf_rf), ("gb", clf_gb)],
        voting="soft",  # 使用软投票
        n_jobs=-1,
    )

    # 训练模型
    logger.info("   开始训练...")
    ensemble.fit(X_train_vec, y_train)

    # 评估模型
    logger.info("   评估模型...")
    y_pred = ensemble.predict(X_test_vec)

    accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"   测试集准确率: {accuracy:.2%}")

    # 详细分类报告
    unique_labels_test = sorted(set(y_test) | set(y_pred))
    target_names = [unique_intents[i] for i in unique_labels_test]

    report = classification_report(
        y_test, y_pred, labels=unique_labels_test, target_names=target_names, zero_division=0.0
    )
    logger.info(f"   分类报告:\n{report}")

    # 交叉验证
    logger.info("   执行5折交叉验证...")
    cv_scores = cross_val_score(ensemble, X_train_vec, y_train, cv=5, n_jobs=-1)
    logger.info(f"   交叉验证准确率: {cv_scores.mean():.2%} (+/- {cv_scores.std() * 2:.2%})")

    # 保存模型
    MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)

    with open(MODEL_SAVE_DIR / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

    with open(MODEL_SAVE_DIR / "classifier.pkl", "wb") as f:
        pickle.dump(ensemble, f)

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
        "total_samples": len(training_data),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "num_intents": len(unique_intents),
        "accuracy": float(accuracy),
        "cv_accuracy_mean": float(cv_scores.mean()),
        "cv_accuracy_std": float(cv_scores.std() * 2),
        "intents": unique_intents,
        "feature_dim": int(X_train_vec.shape[1]),
    }

    with open(MODEL_SAVE_DIR / "training_info.json", "w", encoding="utf-8") as f:
        json.dump(training_info, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 模型已保存到: {MODEL_SAVE_DIR}")

    return {"accuracy": accuracy, "cv_accuracy": cv_scores.mean(), "training_info": training_info}


def main() -> None:
    """主函数"""
    logger.info("🎯 改进版意图识别模型训练")
    logger.info("=" * 60)

    # 1. 加载所有训练数据
    all_data = load_all_training_data()

    # 2. 优化训练数据
    optimized_data = optimize_training_data(all_data, min_threshold=30)

    # 3. 训练集成模型
    results = train_ensemble_model(optimized_data)

    # 4. 输出总结
    logger.info("=" * 60)
    logger.info("✅ 训练完成!")
    logger.info(f"测试集准确率: {results['accuracy']:.2%}")
    logger.info(f"交叉验证准确率: {results['cv_accuracy']:.2%}")
    logger.info(f"训练样本数: {results['training_info']['total_samples']}")
    logger.info(f"意图类别数: {results['training_info']['num_intents']}")
    logger.info(f"模型保存位置: {MODEL_SAVE_DIR}")


if __name__ == "__main__":
    main()

