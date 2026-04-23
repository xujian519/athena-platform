#!/usr/bin/env python3

"""
意图识别模型训练脚本
Intent Recognition Model Training Script

使用平台已有的训练数据进行模型训练
"""

import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from core.logging_config import setup_logging

# 配置
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 数据源配置
AGGREGATED_DATA_PATH = (
    "/Users/xujian/Athena工作平台/data/training/aggregated_training_data_20260115_191513.json"
)
MEMORY_DB_PATH = "/Users/xujian/Athena工作平台/data/online_learning.db"
MODEL_SAVE_DIR = Path("/Users/xujian/Athena工作平台/models/online_learning_v10")


def load_aggregated_training_data() -> list[dict[str, Any]]:
    """加载聚合训练数据"""
    logger.info("📂 加载聚合训练数据...")

    with open(AGGREGATED_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    training_data = data.get("data", [])
    logger.info(f"✅ 加载了 {len(training_data)} 条训练样本")
    logger.info(f"   意图类别数: {data.get('total_intents', 0)}")

    return training_data


def load_memory_conversations() -> list[dict[str, Any]]:
    """从记忆服务加载历史对话数据"""
    logger.info("📂 从记忆服务加载历史对话...")

    memory_data = []

    try:
        # 尝试从记忆服务的PostgreSQL数据库中提取数据
        import asyncio

        import asyncpg

        async def extract_from_memory_db():
            try:
                conn = await asyncpg.connect(
                    host="localhost", port=5432, database="athena", user="xujian"
                )

                # 查询记忆数据
                rows = await conn.fetch("""
                    SELECT
                        content,
                        memory_type,
                        tags,
                        importance
                    FROM agent_memories
                    WHERE is_archived = FALSE
                    ORDER BY created_at DESC
                    LIMIT 1000
                """)

                await conn.close()

                # 转换为训练数据格式
                for row in rows:
                    content = row["content"]
                    memory_type = row["memory_type"]
                    tags = row["tags"] or []

                    # 根据记忆类型和标签推断意图
                    intent = infer_intent_from_memory(content, memory_type, tags)
                    if intent:
                        memory_data.append(
                            {
                                "text": content,
                                "intent": intent,
                                "source": "memory_service",
                                "metadata": {
                                    "memory_type": memory_type,
                                    "importance": row["importance"],
                                },
                            }
                        )

                logger.info(f"✅ 从记忆服务提取了 {len(memory_data)} 条样本")
                return memory_data

            except Exception as e:
                logger.warning(f"⚠️ 从记忆服务提取失败: {e}")
                return []

        # 运行异步函数
        memory_data = asyncio.run(extract_from_memory_db())

    except ImportError:
        logger.warning("⚠️ asyncpg未安装,跳过记忆服务数据提取")

    return memory_data


def infer_intent_from_memory(content: str, memory_type: str, tags: list[str]) -> str:
    """从记忆数据推断意图"""
    content_lower = content.lower()

    # 根据记忆类型推断
    intent_mapping = {
        "conversation": "daily_chat",
        "emotional": "EMOTIONAL",
        "knowledge": "knowledge_graph",
        "family": "life_assistant",
        "professional": "LEGAL_QUERY",
        "learning": "knowledge_graph",
        "schedule": "PROBLEM_SOLVING",
        "preference": "life_assistant",
    }

    # 如果有标签,从标签推断
    tag_keywords = {
        "patent_search": ["专利", "搜索", "检索"],
        "patent_analysis": ["分析", "专利"],
        "patent_drafting": ["撰写", "申请"],
        "legal_query": ["法律", "咨询"],
        "daily_chat": ["聊天", "日常"],
        "EMOTIONAL": ["开心", "难过", "爱"],
    }

    # 标签匹配
    for tag in tags:
        for intent, keywords in tag_keywords.items():
            if any(kw in tag for kw in keywords):
                return intent

    # 记忆类型映射
    if memory_type in intent_mapping:
        return intent_mapping[memory_type]

    # 关键词匹配
    if any(kw in content_lower for kw in ["专利", "检索", "搜索"]):
        return "patent_search"
    elif any(kw in content_lower for kw in ["分析", "评估"]):
        return "patent_analysis"
    elif any(kw in content_lower for kw in ["撰写", "申请", "起草"]):
        return "PATENT_DRAFTING"
    elif any(kw in content_lower for kw in ["法律", "咨询"]):
        return "legal_query"
    elif any(kw in content_lower for kw in ["开心", "难过", "爸爸"]):
        return "EMOTIONAL"

    return None


def optimize_training_data(
    aggregated_data: list[dict], memory_data: list[dict]
) -> list[dict[str, Any]]:
    """优化和合并训练数据"""
    logger.info("🔧 优化训练数据...")

    # 合并数据
    combined_data = aggregated_data + memory_data
    logger.info(f"   合并后总计: {len(combined_data)} 条样本")

    # 去重
    seen = set()
    unique_data = []
    for item in combined_data:
        text_hash = hash(item["text"])
        if text_hash not in seen:
            seen.add(text_hash)
            unique_data.append(item)

    logger.info(f"   去重后: {len(unique_data)} 条样本")

    # 数据清洗
    cleaned_data = []
    for item in unique_data:
        text = item["text"].strip()
        if len(text) > 5:  # 过滤过短文本
            item["text"] = text
            cleaned_data.append(item)

    logger.info(f"   清洗后: {len(cleaned_data)} 条样本")

    # 意图分布统计
    intent_counts = {}
    for item in cleaned_data:
        intent = item["intent"]
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    logger.info(f"   意图类别数: {len(intent_counts)}")

    # 只保留高频意图类别(样本数≥20)以提高模型性能
    min_samples_threshold = 20
    valid_intents = {
        intent for intent, count in intent_counts.items() if count >= min_samples_threshold
    }
    filtered_data = [item for item in cleaned_data if item["intent"] in valid_intents]

    removed_count = len(cleaned_data) - len(filtered_data)
    removed_intents = len(intent_counts) - len(valid_intents)
    logger.info(
        f"   只保留样本数≥{min_samples_threshold}的高频类别: 移除{removed_intents}个类别,{removed_count}条样本"
    )

    # 重新统计过滤后的意图分布
    filtered_intent_counts = {}
    for item in filtered_data:
        intent = item["intent"]
        filtered_intent_counts[intent] = filtered_intent_counts.get(intent, 0) + 1

    logger.info(f"   过滤后意图类别数: {len(filtered_intent_counts)}")
    logger.info(f"   平均每类样本数: {len(filtered_data) / len(filtered_intent_counts):.1f}")

    # 显示高频意图
    top_intents = sorted(filtered_intent_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    logger.info("   高频意图 Top10:")
    for intent, count in top_intents:
        logger.info(f"      {intent}: {count}")

    return filtered_data


def train_model(training_data: list[dict[str, Any]) -> dict[str, Any]]:
    """训练意图识别模型"""
    logger.info("🚀 开始训练意图识别模型...")

    # 准备数据
    texts = [item["text"] for item in training_data]
    labels = [item["intent"] for item in training_data]

    logger.info(f"   训练样本数: {len(texts)}")
    logger.info(f"   意图类别数: {len(set(labels))}")

    # 划分训练集和测试集
    X_train_texts, X_test_texts, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    logger.info(f"   训练集: {len(X_train_texts)}")
    logger.info(f"   测试集: {len(X_test_texts)}")

    # 创建向量化器
    logger.info("   创建TF-IDF向量化器...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), max_features=3000, min_df=1, max_df=0.85, sublinear_tf=True
    )

    # 创建标签编码器
    label_encoder = LabelEncoder()

    # 转换数据
    X_train = vectorizer.fit_transform(X_train_texts)
    X_test = vectorizer.transform(X_test_texts)
    y_train = label_encoder.fit_transform(y_train)
    y_test = label_encoder.transform(y_test)

    # 创建分类器
    logger.info("   创建随机森林分类器...")
    classifier = RandomForestClassifier(
        n_estimators=200,
        max_depth=25,
        min_samples_split=3,
        min_samples_leaf=1,
        warm_start=True,  # 支持在线学习
        random_state=42,
        n_jobs=-1,
        verbose=1,
    )

    # 训练模型
    logger.info("   开始训练...")
    classifier.fit(X_train, y_train)

    # 评估模型
    logger.info("   评估模型...")
    y_pred = classifier.predict(X_test)

    accuracy = (y_pred == y_test).mean()
    logger.info(f"   测试集准确率: {accuracy:.2%}")

    # 分类报告 - 获取测试集中实际出现的类别
    unique_labels = sorted(set(y_test) | set(y_pred))
    target_names = [label_encoder.classes_[i] for i in unique_labels]
    report = classification_report(
        y_test, y_pred, labels=unique_labels, target_names=target_names, zero_division=0.0
    )
    logger.info(f"   分类报告:\n{report}")

    # 保存模型
    MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)

    with open(MODEL_SAVE_DIR / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

    with open(MODEL_SAVE_DIR / "classifier.pkl", "wb") as f:
        pickle.dump(classifier, f)

    with open(MODEL_SAVE_DIR / "label_encoder.pkl", "wb") as f:
        pickle.dump(label_encoder, f)

    # 保存训练信息
    training_info = {
        "training_date": datetime.now().isoformat(),
        "total_samples": len(training_data),
        "train_samples": len(X_train_texts),
        "test_samples": len(X_test_texts),
        "num_intents": len(set(labels)),
        "accuracy": float(accuracy),
        "intents": label_encoder.classes_.tolist(),
        "intent_distribution": {
            intent: int(sum(1 for lbl in labels if lbl == intent))
            for intent in label_encoder.classes_
        },
    }

    with open(MODEL_SAVE_DIR / "training_info.json", "w", encoding="utf-8") as f:
        json.dump(training_info, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 模型已保存到: {MODEL_SAVE_DIR}")

    return {"accuracy": accuracy, "training_info": training_info}


def main() -> None:
    """主函数"""
    logger.info("🎯 意图识别模型训练脚本")
    logger.info("=" * 50)

    # 1. 加载聚合训练数据
    aggregated_data = load_aggregated_training_data()

    # 2. 加载记忆服务历史数据
    memory_data = load_memory_conversations()

    # 3. 优化和合并训练数据
    optimized_data = optimize_training_data(aggregated_data, memory_data)

    # 4. 训练模型
    results = train_model(optimized_data)

    # 5. 输出总结
    logger.info("=" * 50)
    logger.info("✅ 训练完成!")
    logger.info(f"准确率: {results['accuracy']:.2%}")
    logger.info(f"训练样本数: {results['training_info']['total_samples']}")
    logger.info(f"意图类别数: {results['training_info']['num_intents']}")
    logger.info(f"模型保存位置: {MODEL_SAVE_DIR}")


if __name__ == "__main__":
    main()

