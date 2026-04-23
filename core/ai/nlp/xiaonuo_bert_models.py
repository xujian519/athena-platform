#!/usr/bin/env python3

"""
小诺BERT模型管理器
使用本地已有的中文模型来增强NLP能力

本地可用模型:
1. BAAI/bge-m3 - 中文语义嵌入模型
2. uer/roberta-base-finetuned-cluener2020-chinese - 中文NER模型

作者: 小诺AI团队
日期: 2025-12-18
"""

import os
from typing import Any

import numpy as np
import torch
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoModel, AutoModelForTokenClassification, AutoTokenizer

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class XiaonuoBERTModels:
    """小诺BERT模型管理器"""

    def __init__(self):
        self.models: dict[str, Any] = {}
        self.tokenizers: dict[str, Any] = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 本地模型路径
        self.local_models = {
            "semantic": "BAAI/bge-m3",  # 语义嵌入
            "ner": "uer/roberta-base-finetuned-cluener2020-chinese",  # NER
        }

        self._load_local_models()

    def _load_local_models(self) -> Any:
        """加载本地模型"""
        for model_type, model_name in self.local_models.items():
            try:
                logger.info(f"📂 加载本地模型: {model_name}")

                # 检查模型是否在本地缓存中
                cache_path = (
                    f"/Users/xujian/.cache/huggingface/models--{model_name.replace('/', '--')}"
                )
                if os.path.exists(cache_path):
                    logger.info(f"✅ 发现本地缓存: {cache_path}")
                    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)

                    if model_type == "semantic":
                        model = AutoModel.from_pretrained(model_name, local_files_only=True)
                    elif model_type == "ner":
                        model = AutoModelForTokenClassification.from_pretrained(
                            model_name, local_files_only=True
                        )

                    model.to(self.device)
                    model.eval()

                    self.models[model_type] = model
                    self.tokenizers[model_type] = tokenizer

                    logger.info(f"✅ 成功加载模型: {model_type}")
                else:
                    logger.warning(f"⚠️ 未找到本地模型: {model_name}")

            except Exception as e:
                logger.error(f"❌ 模型加载失败 {model_name}: {e}")

        logger.info(f"🎯 已加载模型数量: {len(self.models)}")

    def encode_text(self, text: str) -> np.ndarray:
        """文本编码为向量"""
        if "semantic" not in self.models:
            logger.warning("⚠️ 语义模型未加载,返回零向量")
            return np.zeros(768)

        try:
            model = self.models["semantic"]
            tokenizer = self.tokenizers["semantic"]

            # 编码文本
            inputs = tokenizer(
                text, return_tensors="pt", truncation=True, max_length=512, padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # 获取嵌入
            with torch.no_grad():
                outputs = model(**inputs)
                # 使用[CLS]标记的嵌入
                embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()

            return embeddings[0]

        except Exception as e:
            logger.error(f"❌ 文本编码失败: {e}")
            return np.zeros(768)

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        """批量文本编码"""
        if "semantic" not in self.models:
            logger.warning("⚠️ 语义模型未加载,返回零向量")
            return np.zeros((len(texts), 768))

        try:
            model = self.models["semantic"]
            tokenizer = self.tokenizers["semantic"]

            # 批量编码
            embeddings = []
            batch_size = 8

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]
                inputs = tokenizer(
                    batch_texts, return_tensors="pt", truncation=True, max_length=512, padding=True
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = model(**inputs)
                    batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                    embeddings.extend(batch_embeddings)

            return np.array(embeddings)

        except Exception as e:
            logger.error(f"❌ 批量编码失败: {e}")
            return np.zeros((len(texts), 768))

    def extract_entities(self, text: str) -> list[tuple[str, str, float]]:
        """使用NER模型提取实体"""
        if "ner" not in self.models:
            logger.warning("⚠️ NER模型未加载,返回空列表")
            return []

        try:
            model = self.models["ner"]
            tokenizer = self.tokenizers["ner"]

            # CLUENER标签映射
            label_map = {
                0: "O",
                1: "B-ADDR",
                2: "I-ADDR",  # 地址
                3: "B-BOOK",
                4: "I-BOOK",  # 书籍
                5: "B-COMP",
                6: "I-COMP",  # 公司
                7: "B-GAME",
                8: "I-GAME",  # 游戏
                9: "B-GOV",
                10: "I-GOV",  # 政府
                11: "B-MOVIE",
                12: "I-MOVIE",  # 电影
                13: "B-NAME",
                14: "I-NAME",  # 人名
                15: "B-ORG",
                16: "I-ORG",  # 组织
                17: "B-POS",
                18: "I-POS",  # 职位
                19: "B-SCENE",
                20: "I-SCENE",  # 景点
            }

            # 编码文本
            inputs = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
                return_offsets_mapping=True,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items() if k != "offset_mapping"}

            # 预测
            with torch.no_grad():
                outputs = model(**inputs)
                predictions = torch.argmax(outputs.logits, dim=2)[0].cpu().numpy()

            # 解析实体
            entities = []
            offset_mapping = inputs["offset_mapping"][0].cpu().numpy()

            current_entity = None
            for _i, (pred_id, (start, end)) in enumerate(
                zip(predictions, offset_mapping, strict=False)
            ):
                if start == end == 0:  # [CLS], [SEP]
                    continue

                label = label_map.get(pred_id, "O")

                if label.startswith("B-"):
                    # 开始新实体
                    if current_entity:
                        entities.append(current_entity)
                    current_entity = {
                        "text": text[start:end],
                        "type": label[2:],
                        "start": start,
                        "end": end,
                        "confidence": 0.9,  # 简化置信度
                    }
                elif label.startswith("I-") and current_entity:
                    # 继续当前实体
                    current_entity["text"] += text[start:end]
                    current_entity["end"] = end
                else:
                    # 结束当前实体
                    if current_entity:
                        entities.append(current_entity)
                        current_entity = None

            if current_entity:
                entities.append(current_entity)

            # 转换为元组格式
            return [(e["text"], e["type"], e["confidence"]) for e in entities]

        except Exception as e:
            logger.error(f"❌ NER实体提取失败: {e}")
            return []

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        emb1 = self.encode_text(text1)
        emb2 = self.encode_text(text2)

        if emb1.sum() == 0 or emb2.sum() == 0:
            return 0.0

        similarity = cosine_similarity([emb1], [emb2])[0][0]
        return float(similarity)

    def search_similar(
        self, query: str, candidates: list[str], top_k: int = 5
    ) -> list[tuple[str, float]]:
        """搜索相似文本"""
        if not candidates:
            return []

        query_emb = self.encode_text(query)
        candidate_embs = self.encode_batch(candidates)

        similarities = cosine_similarity([query_emb], candidate_embs)[0]

        # 排序并返回top_k
        indexed_sims = [(candidates[i], float(similarities[i])) for i in range(len(candidates))]
        indexed_sims.sort(key=lambda x: x[1], reverse=True)

        return indexed_sims[:top_k]


def test_bert_models() -> Any:
    """测试BERT模型"""
    print("🧪 开始测试本地BERT模型...")

    # 初始化模型管理器
    bert_models = XiaonuoBERTModels()

    # 测试文本编码
    test_text = "小诺是一个智能助手"
    print(f"\n📝 测试文本: {test_text}")

    embedding = bert_models.encode_text(test_text)
    print(f"🔢 编码向量维度: {embedding.shape}")
    print(f"📊 向量范数: {np.linalg.norm(embedding):.4f}")

    # 测试NER实体识别
    ner_text = "张三在北京工作,邮箱是zhangsan@example.com"
    print(f"\n🏷️ NER测试文本: {ner_text}")

    entities = bert_models.extract_entities(ner_text)
    print(f"🎯 识别实体: {entities}")

    # 测试相似度计算
    text1 = "今天天气很好"
    text2 = "天气晴朗"
    text3 = "小诺是AI助手"

    sim1 = bert_models.calculate_similarity(text1, text2)
    sim2 = bert_models.calculate_similarity(text1, text3)

    print("\n🔍 相似度测试:")
    print(f"  '{text1}' vs '{text2}': {sim1:.4f}")
    print(f"  '{text1}' vs '{text3}': {sim2:.4f}")

    # 测试相似搜索
    query = "人工智能"
    candidates = ["机器学习", "深度学习", "天气很好", "自然语言处理", "小诺助手"]

    results = bert_models.search_similar(query, candidates, top_k=3)
    print(f"\n🔎 相似搜索: 查询='{query}'")
    for text, score in results:
        print(f"  {text}: {score:.4f}")

    print("\n✅ BERT模型测试完成!")


if __name__ == "__main__":
    test_bert_models()

