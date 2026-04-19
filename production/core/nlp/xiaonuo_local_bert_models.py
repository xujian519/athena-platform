#!/usr/bin/env python3
from __future__ import annotations
"""
小诺本地BERT模型管理器
使用本地缓存的高质量中文模型来升级NLP系统

本地可用模型:
1. BAAI/bge-m3 (141MB) - 中文语义嵌入模型
2. uer/roberta-base-finetuned-cluener2020-chinese (388MB) - 中文NER模型

功能:
1. 语义相似度计算
2. 中文实体识别
3. 文本嵌入生成
4. 模型性能监控

作者: 小诺AI团队
日期: 2025-12-18
"""

import hashlib
import json
import os
import threading
import time
from functools import lru_cache
from typing import Any

import numpy as np
import torch
from transformers import AutoModel, AutoModelForTokenClassification, AutoTokenizer

from core.logging_config import setup_logging

from .apple_silicon_optimizer import get_apple_silicon_optimizer
from .error_handler import (
    FallbackStrategy,
    get_error_handler,
    robust_retry,
)
from .model_manager import get_model_manager
from .performance_monitor import get_performance_monitor

# 设置Transformers离线模式
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_OFFLINE"] = "1"

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class XiaonuoLocalBERTModels:
    """小诺本地BERT模型管理器 - Phase 2优化版"""

    def __init__(self, enable_cache: bool = True, cache_size: int = 1000):
        self.models = {}
        self.tokenizers = {}
        self.enable_cache = enable_cache
        self.cache_size = cache_size

        # 性能监控
        self.performance_stats = {
            "inference_times": [],
            "memory_usage": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "total_requests": 0,
            "errors": [],
        }

        # 模型统计
        self.model_stats: dict[str, Any] = {
            "inference_time": {},
            "cache_hit_rate": 0.0,
            "total_requests": 0,
        }

        # 线程安全锁
        self._lock = threading.RLock()

        # 设备检测
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        # 初始化智能模型管理器
        self.model_manager = get_model_manager()
        self.model_manager.optimize_for_device()

        # 初始化性能监控器
        self.performance_monitor = get_performance_monitor()

        # 初始化错误处理器
        self.error_handler = get_error_handler()

        # 初始化Apple Silicon优化器
        self.apple_optimizer = get_apple_silicon_optimizer()

        # 缓存系统
        self._cache = {}
        self._cache_access_order = []

        # 本地模型路径配置
        self.local_models = {
            "semantic": {
                "path": "BAAI/bge-m3",
                "class": AutoModel,
                "priority": 1,  # 高优先级,常驻内存
            },
            "ner": {
                "path": "uer/roberta-base-finetuned-cluener2020-chinese",
                "class": AutoModelForTokenClassification,
                "priority": 2,  # 中等优先级
            },
        }

        # 注册模型到管理器
        self._register_models()

        # 预加载高优先级模型
        self._preload_high_priority_models()

        logger.info("🚀 XiaonuoLocalBERTModels初始化完成 (Phase 2)")
        logger.info(f"🔧 设备: {self.device}")
        logger.info(f"💾 缓存: {'启用' if enable_cache else '禁用'} ({cache_size}条)")

    def _register_models(self) -> Any:
        """注册模型到智能管理器"""
        for model_type, config in self.local_models.items():
            try:
                # 获取实际模型路径
                model_path = self._get_local_model_path(model_type, config["path"])

                self.model_manager.register_model(
                    name=f"xiaonuo_{model_type}", model_path=model_path, model_class=config["class"]
                )

                logger.info(f"📝 已注册模型: {model_type} -> {model_path}")

            except Exception as e:
                logger.error(f"❌ 模型注册失败 {model_type}: {e}")

    def _get_local_model_path(self, model_type: str, model_name: str) -> str:
        """获取本地模型路径"""
        base_path = "/Users/xujian/Athena工作平台/models"

        # 检查项目本地模型目录
        if model_type == "semantic":
            local_path = os.path.join(base_path, "BAAI/bge-m3")
        elif model_type == "ner":
            local_path = os.path.join(base_path, "roberta-base-finetuned-cluener2020-chinese")
        else:
            local_path = os.path.join(base_path, model_name.replace("/", "--"))

        if os.path.exists(local_path):
            return local_path
        else:
            logger.warning(f"⚠️ 未找到本地模型: {local_path},使用缓存路径")
            return model_name

    def _preload_high_priority_models(self) -> Any:
        """预加载高优先级模型"""
        try:
            for model_type, config in self.local_models.items():
                if config.get("priority", 10) <= 1:  # 高优先级
                    logger.info(f"🔄 预加载高优先级模型: {model_type}")
                    self._get_model(model_type)
        except Exception as e:
            logger.error(f"❌ 预加载失败: {e}")

    def _get_model(self, model_type: str) -> Any:
        """获取模型(使用智能管理器)"""
        try:
            with self._lock:
                # 先尝试从管理器获取
                model = self.model_manager.get_model(f"xiaonuo_{model_type}")

                # 同步到本地缓存
                if model_type not in self.models:
                    # 获取对应的tokenizer
                    model_path = self._get_local_model_path(
                        model_type, self.local_models[model_type]["path"]
                    )
                    # 安全修复: 禁用trust_remote_code防止任意代码执行
                    tokenizer = AutoTokenizer.from_pretrained(
                        model_path,
                        trust_remote_code=False,  # 安全: 不执行模型中的自定义代码
                        local_files_only=True,
                    )

                    self.models[model_type] = model
                    self.tokenizers[model_type] = tokenizer

                return model

        except Exception as e:
            logger.error(f"❌ 获取模型失败 {model_type}: {e}")
            raise

    def _get_cache_key(self, text: str, operation: str) -> str:
        """生成缓存键"""
        text_hash = hashlib.md5(text.encode("utf-8", usedforsecurity=False), usedforsecurity=False).hexdigest()
        return f"{operation}_{text_hash}"

    def _update_cache(self, key: str, value: Any) -> Any:
        """更新缓存 (LRU策略)"""
        if not self.enable_cache:
            return

        # 如果缓存已满,删除最旧的条目
        if len(self._cache) >= self.cache_size and key not in self._cache:
            oldest_key = self._cache_access_order.pop(0)
            del self._cache[oldest_key]

        # 更新缓存
        self._cache[key] = value
        if key in self._cache_access_order:
            self._cache_access_order.remove(key)
        self._cache_access_order.append(key)

    def _get_from_cache(self, key: str) -> Any | None:
        """从缓存获取"""
        if not self.enable_cache or key not in self._cache:
            return None

        # 更新访问顺序
        self._cache_access_order.remove(key)
        self._cache_access_order.append(key)

        self.performance_stats["cache_hits"] += 1
        return self._cache[key]

    def _record_performance(self, operation: str, duration: float, success: bool = True) -> Any:
        """记录性能指标"""
        self.performance_stats["total_requests"] += 1
        self.performance_stats["inference_times"].append(
            {
                "operation": operation,
                "duration": duration,
                "timestamp": time.time(),
                "success": success,
            }
        )

        # 保持最近1000条记录
        if len(self.performance_stats["inference_times"]) > 1000:
            self.performance_stats["inference_times"] = self.performance_stats["inference_times"][
                -1000:
            ]

        if not success:
            self.performance_stats["cache_misses"] += 1
            self.performance_stats["errors"].append(
                {"operation": operation, "error": "Inference failed", "timestamp": time.time()}
            )

    @robust_retry(max_attempts=3, fallback_strategy=FallbackStrategy.CACHE_FALLBACK)
    def encode_text(self, text: str) -> np.ndarray:
        """文本编码为向量 (Phase 2优化版)"""
        # 生成缓存键
        cache_key = self._get_cache_key(text, "encode")

        # 尝试从缓存获取
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result

        # 缓存未命中,执行推理
        start_time = time.time()

        try:
            with self._lock:
                # 使用智能管理器获取模型
                model = self._get_model("semantic")
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

                result = embeddings[0]

                # Apple Silicon优化
                result = self.apple_optimizer.optimize_embedding_operations(result.reshape(1, -1))[
                    0
                ]

                # 更新缓存
                self._update_cache(cache_key, result.copy())

                # 记录性能到性能监控器
                duration = time.time() - start_time
                self.performance_monitor.record_inference_time("encode_text", duration, True)
                self._record_performance("encode_text", duration, True)

                # 记录缓存命中率
                if self.enable_cache:
                    hit_rate = self.performance_stats["cache_hits"] / max(
                        1, self.performance_stats["total_requests"]
                    )
                    self.performance_monitor.record_cache_hit_rate("xiaonuo_encode", hit_rate)

                return result

        except Exception as e:
            duration = time.time() - start_time
            self.performance_monitor.record_inference_time("encode_text", duration, False)
            self._record_performance("encode_text", duration, False)

            # 使用错误处理器处理
            try:
                error_context = {
                    "operation": "encode_text",
                    "text_length": len(text),
                    "text_preview": text[:50],
                }
                return self.error_handler.handle_error(e, error_context)
            except Exception:
                logger.error(f"❌ 文本编码失败: {e}")
                return np.zeros(768)

    @lru_cache(maxsize=500)
    def encode_text_fast(self, text: str) -> np.ndarray:
        """快速文本编码(内置LRU缓存)"""
        return self.encode_text(text)

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        """批量文本编码 (Phase 2优化版)"""
        if not texts:
            return np.array([])

        # 对于单个文本,使用单次编码(可以利用缓存)
        if len(texts) == 1:
            return np.array([self.encode_text(texts[0])])

        start_time = time.time()

        try:
            with self._lock:
                # 使用智能管理器获取模型
                model = self._get_model("semantic")
                tokenizer = self.tokenizers["semantic"]

                # 批量编码 - 动态批处理大小
                batch_size = self._get_optimal_batch_size(len(texts))
                embeddings = []

                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i : i + batch_size]
                    batch_embeddings = self._encode_batch_internal(batch_texts, model, tokenizer)
                    embeddings.extend(batch_embeddings)

                result = np.array(embeddings)

                # 记录性能
                duration = time.time() - start_time
                self._record_performance("encode_batch", duration, True)

                return result

        except Exception as e:
            duration = time.time() - start_time
            self._record_performance("encode_batch", duration, False)
            logger.error(f"❌ 批量编码失败: {e}")
            return np.zeros((len(texts), 768))

    def _get_optimal_batch_size(self, num_texts: int) -> int:
        """根据设备类型和文本数量动态确定最优批处理大小"""
        if self.device.type == "mps":
            # MPS设备优化
            if num_texts <= 4:
                return 4
            elif num_texts <= 16:
                return 8
            else:
                return 16
        else:
            # CPU/CUDA设备
            if num_texts <= 8:
                return num_texts
            else:
                return 8

    def _encode_batch_internal(self, batch_texts: list[str], model, tokenizer) -> list[np.ndarray]:
        """内部批处理编码方法"""
        inputs = tokenizer(
            batch_texts, return_tensors="pt", truncation=True, max_length=512, padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()

        return list(batch_embeddings)

    def extract_entities(self, text: str) -> list[tuple[str, str, float]]:
        """使用NER模型提取实体"""
        if "ner" not in self.models:
            logger.warning("⚠️ NER模型未加载,返回空列表")
            return []

        try:
            start_time = time.time()
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

            # 处理输入张量
            input_tensors = {
                k: v.to(self.device) for k, v in inputs.items() if k != "offset_mapping"
            }

            # 预测
            with torch.no_grad():
                outputs = model(**input_tensors)
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
                        "confidence": 0.9,
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

            inference_time = time.time() - start_time
            if "ner" not in self.model_stats["inference_time"]:
                self.model_stats["inference_time"]["ner"] = []
            self.model_stats["inference_time"]["ner"].append(inference_time)

            # 转换为元组格式
            return [(e["text"], e["type"], e["confidence"]) for e in entities]

        except Exception as e:
            logger.error(f"❌ NER实体提取失败: {e}")
            logger.error(f"   错误类型: {type(e).__name__}")
            return []

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度 (Apple Silicon优化版)"""
        emb1 = self.encode_text(text1)
        emb2 = self.encode_text(text2)

        if emb1.sum() == 0 or emb2.sum() == 0:
            return 0.0

        # 使用Apple Silicon优化器进行批量相似度计算
        embeddings = np.array([emb1, emb2])
        similarities = self.apple_optimizer.batch_similarity_computation(
            embeddings[:1], embeddings[1:], batch_size=1
        )

        return float(similarities[0][0])

    def search_similar(
        self, query: str, candidates: list[str], top_k: int = 5
    ) -> list[tuple[str, float]]:
        """搜索相似文本 (Apple Silicon优化版)"""
        if not candidates:
            return []

        query_emb = self.encode_text(query)
        candidate_embs = self.encode_batch(candidates)

        # 使用Apple Silicon优化器进行批量相似度计算
        similarities = self.apple_optimizer.batch_similarity_computation(
            query_emb.reshape(1, -1), candidate_embs, batch_size=32
        )[0]

        # 排序并返回top_k
        indexed_sims = [(candidates[i], float(similarities[i])) for i in range(len(candidates))]
        indexed_sims.sort(key=lambda x: x[1], reverse=True)

        return indexed_sims[:top_k]

    def get_performance_stats(self) -> dict[str, Any]:
        """获取详细性能统计 (Phase 2优化版)"""
        stats = {
            "device": str(self.device),
            "loaded_models": list(self.models.keys()),
            "cache_enabled": self.enable_cache,
            "cache_size": self.cache_size,
            "cache_stats": {
                "current_size": len(self._cache),
                "max_size": self.cache_size,
                "hit_count": self.performance_stats["cache_hits"],
                "miss_count": self.performance_stats["cache_misses"],
                "total_requests": self.performance_stats["total_requests"],
            },
            "inference_stats": self._calculate_inference_stats(),
            "model_manager_stats": self.model_manager.get_performance_stats(),
            "apple_silicon_stats": self.apple_optimizer.get_optimization_report(),
        }

        # 计算缓存命中率
        total = stats["cache_stats"]["hit_count"] + stats["cache_stats"]["miss_count"]
        if total > 0:
            stats["cache_stats"]["hit_rate"] = stats["cache_stats"]["hit_count"] / total
        else:
            stats["cache_stats"]["hit_rate"] = 0.0

        return stats

    def _calculate_inference_stats(self) -> dict[str, Any]:
        """计算推理统计"""
        if not self.performance_stats["inference_times"]:
            return {}

        # 按操作类型分组
        operations = {}
        for record in self.performance_stats["inference_times"]:
            op = record["operation"]
            if op not in operations:
                operations[op] = []
            operations[op].append(record["duration"])

        # 计算统计指标
        stats = {}
        for op, times in operations.items():
            stats[op] = {
                "count": len(times),
                "avg_time": np.mean(times),
                "min_time": np.min(times),
                "max_time": np.max(times),
                "total_time": np.sum(times),
                "success_rate": sum(
                    1
                    for t in self.performance_stats["inference_times"]
                    if t["operation"] == op and t["success"]
                )
                / len(times),
            }

        return stats

    def clear_cache(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._cache_access_order.clear()
            logger.info("🗑️ 缓存已清空")

    def optimize_memory(self) -> Any:
        """优化内存使用"""
        with self._lock:
            # 清空缓存
            self.clear_cache()

            # 使用模型管理器优化内存
            self.model_manager.optimize_for_device()

            # 清理Python缓存
            import gc

            gc.collect()

            logger.info("🧹 内存优化完成")

    def is_model_available(self, model_type: str) -> bool:
        """检查模型是否可用"""
        return model_type in self.local_models

    def get_model_stats(self) -> dict[str, Any]:
        """获取模型统计信息"""
        return self.model_stats

    def get_model_info(self, model_type: str) -> dict[str, Any]:
        """获取模型详细信息"""
        if model_type not in self.local_models:
            return {"error": "模型不存在"}

        config = self.local_models[model_type]
        return {
            "type": model_type,
            "path": config["path"],
            "class": config["class"].__name__,
            "priority": config.get("priority", 10),
            "loaded": model_type in self.models,
            "manager_name": f"xiaonuo_{model_type}",
        }


def test_local_bert_models() -> Any:
    """测试本地BERT模型"""
    print("🧪 开始测试本地BERT模型...")

    # 初始化模型管理器
    bert_models = XiaonuoLocalBERTModels()

    # 检查模型状态
    print("\n📊 模型状态:")
    print(f"  语义模型可用: {bert_models.is_model_available('semantic')}")
    print(f"  NER模型可用: {bert_models.is_model_available('ner')}")

    if bert_models.is_model_available("semantic"):
        # 测试文本编码
        test_text = "小诺是一个智能助手"
        print(f"\n📝 测试文本编码: {test_text}")

        embedding = bert_models.encode_text(test_text)
        print(f"🔢 编码向量维度: {embedding.shape}")
        print(f"📊 向量范数: {np.linalg.norm(embedding):.4f}")

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

    if bert_models.is_model_available("ner"):
        # 测试NER实体识别
        ner_text = "张三在北京工作,邮箱是zhangsan@example.com"
        print(f"\n🏷️ NER测试文本: {ner_text}")

        entities = bert_models.extract_entities(ner_text)
        print(f"🎯 识别实体: {entities}")

    # 显示性能统计
    stats = bert_models.get_model_stats()
    print("\n📈 性能统计:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    print("\n✅ 本地BERT模型测试完成!")


if __name__ == "__main__":
    test_local_bert_models()
