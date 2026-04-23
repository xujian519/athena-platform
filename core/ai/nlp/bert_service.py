#!/usr/bin/env python3

"""
BERT服务管理器
BERT Service Manager for Athena Platform

管理多个BERT模型,提供统一的文本理解和分析能力

作者: 小诺·双鱼座
创建时间: 2025-12-16
"""

# Numpy兼容性导入
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import torch
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

from config.numpy_compatibility import array

# 导入优化器
from .bert_optimizer import BERTOptimizer, get_optimal_device, setup_bert_optimization

logger = logging.getLogger(__name__)


@dataclass
class BERTModelConfig:
    """BERT模型配置"""

    name: str
    model_path: str
    tokenizer_path: Optional[str] = None
    task_type: str = "feature_extraction"  # feature_extraction, classification, ner
    max_length: int = 512
    device: str = "cpu"
    cache_dir: Optional[str] = None
    use_fast: bool = True


@dataclass
class BERTResult:
    """BERT处理结果"""

    embeddings: np.Optional[ndarray] = None  # [hidden_size] or [batch, hidden_size]
    pooler_output: np.Optional[ndarray] = None  # [hidden_size]
    hidden_states: Optional[list[np.ndarray]] = None
    attentions: Optional[list[np.ndarray]] = None
    predictions: np.Optional[ndarray] = None  # for classification
    confidence: Optional[float] = None
    processing_time: float = 0.0
    model_name: str = ""


class BERTService:
    """BERT服务管理器"""

    def __init__(self):
        self.name = "BERT服务管理器"
        self.version = "1.0.0"
        self.logger = logging.getLogger(self.name)

        # 启用优化
        setup_bert_optimization()

        # 模型存储
        self.models: dict[str, dict[str, Any] = {}
        self.model_configs: dict[str, BERTModelConfig] = {}

        # 缓存目录
        self.cache_dir = "/Users/xujian/Athena工作平台/models/bert_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

        # 优化缓存配置
        BERTOptimizer.optimize_cache_config(self.cache_dir)

        # 统计信息
        self.stats = {"total_requests": 0, "model_usage": {}, "total_processing_time": 0.0}

        # 初始化模型配置
        self._init_model_configs()

    def _init_model_configs(self) -> Any:
        """初始化BERT模型配置(优先使用本地已有模型)"""
        # 1. 首先使用本地已有的模型
        # 1.1 中文BERT Base(使用本地完整路径)
        self.model_configs["chinese_base"] = BERTModelConfig(
            name="BERT-Base-Chinese",
            model_path="/Users/xujian/.cache/huggingface/hub/models--bert-base-chinese/snapshots/8f23c25b06e129b6c986331a13d8d025a92cf0ea",
            task_type="feature_extraction",
            max_length=512,
            device="cpu",
        )

        # 1.2 RoBERTa ChinaNews(使用本地完整路径)
        self.model_configs["roberta_chinanews"] = BERTModelConfig(
            name="RoBERTa-ChinaNews",
            model_path="/Users/xujian/.cache/huggingface/hub/models--uer--roberta-base-finetuned-chinanews-chinese/snapshots/638100ab2773a8c3d0afceb9387eb88fe707fbe1",
            task_type="feature_extraction",
            max_length=512,
            device="cpu",
        )

        # 1.3 中文法律ELECTRA(使用本地完整路径)
        self.model_configs["legal_electra"] = BERTModelConfig(
            name="Chinese-Legal-ELECTRA",
            model_path="/Users/xujian/.cache/huggingface/hub/models--hfl--chinese-legal-electra-base-discriminator/snapshots/ffd97a559532e03a0073d2cdfede81a8a7f6d361",
            task_type="feature_extraction",
            max_length=512,
            device="cpu",
        )

        # 2. 使用本地MacBERT(如果有)
        local_macbert_path = "/Users/xujian/.cache/huggingface/hub/models--hfl--chinese-macbert-base/snapshots/183bb99aa7af74355fb58d16edf8c13ae7c5433e"
        if os.path.exists(local_macbert_path):
            self.model_configs["local_chinese"] = BERTModelConfig(
                name="Chinese-MacBERT",
                model_path=local_macbert_path,
                task_type="feature_extraction",
                max_length=512,
                device="cpu",
            )

        # 3. 魔搭社区模型(需要下载,标记为可选)
        # 3.1 Lawformer - 法律领域专用
        self.model_configs["legal"] = BERTModelConfig(
            name="Lawformer",
            model_path="THUDM/Lawformer",
            task_type="feature_extraction",
            max_length=512,
            cache_dir=self.cache_dir,
            device="cpu",
        )

        # 3.2 Chinese-RoBERTa-WWM-Ext - 通用中文增强
        self.model_configs["general"] = BERTModelConfig(
            name="Chinese-RoBERTa-WWM-Ext",
            model_path="hfl/chinese-roberta-wwm-ext-ext",
            task_type="feature_extraction",
            max_length=512,
            cache_dir=self.cache_dir,
            device="cpu",
        )

        # 5. Chinese-DeBERTa-V3 - 更好的中文理解模型(魔搭社区,待下载)
        self.model_configs["chinese_deberta"] = BERTModelConfig(
            name="Chinese-DeBERTa-V3",
            model_path="hfl/chinese-deberta-v3-base",
            task_type="feature_extraction",
            max_length=512,
            cache_dir=self.cache_dir,
            device="cpu",
        )

    async def initialize_model(self, model_key: str):
        """初始化指定模型"""
        if model_key in self.models and self.models[model_key]["loaded"]:
            return True

        config = self.model_configs[model_key]

        try:
            print(f"🔄 正在加载BERT模型: {config.name}")
            start_time = asyncio.get_event_loop().time()

            # 在线程池中加载模型
            loop = asyncio.get_event_loop()
            tokenizer, model = await loop.run_in_executor(None, self._load_model_sync, config)

            load_time = asyncio.get_event_loop().time() - start_time

            # 存储模型
            self.models[model_key]] = {
                "tokenizer": tokenizer,
                "model": model,
                "config": config,
                "loaded": True,
                "load_time": load_time,
            }

            print(f"✅ {config.name} 加载成功!")
            print(f"   - 加载时间: {load_time:.2f}秒")
            print(f"   - 设备: {config.device}")

            return True

        except Exception as e:
            print(f"❌ {config.name} 加载失败: {e}")
            self.logger.error(f"模型加载失败 [{model_key}]: {e}")
            return False

    def _load_model_sync(self, config: BERTModelConfig) -> tuple[Any, Any]:
        """同步加载模型(优先使用本地路径)"""
        try:
            # 检查是否是本地路径
            is_local_path = os.path.exists(config.model_path)

            if is_local_path:
                print(f"   📁 使用本地模型: {config.model_path}")

                # 从本地路径加载
                tokenizer = AutoTokenizer.from_pretrained(
                    config.model_path,
                    local_files_only=True,  # 强制只使用本地文件
                    use_fast=config.use_fast,
                )

                if config.task_type == "classification":
                    model = AutoModelForSequenceClassification.from_pretrained(
                        config.model_path, local_files_only=True
                    )
                else:
                    model = AutoModel.from_pretrained(config.model_path, local_files_only=True)
            else:
                # 网络加载(设置魔搭镜像)
                os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

                tokenizer = AutoTokenizer.from_pretrained(
                    config.model_path,
                    cache_dir=config.cache_dir,
                    use_fast=config.use_fast,
                    trust_remote_code=True,
                )

                if config.task_type == "classification":
                    model = AutoModelForSequenceClassification.from_pretrained(
                        config.model_path, cache_dir=config.cache_dir, trust_remote_code=True
                    )
                else:
                    model = AutoModel.from_pretrained(
                        config.model_path, cache_dir=config.cache_dir, trust_remote_code=True
                    )

            # 设置设备(使用优化器)
            device = get_optimal_device()
            if device != "cpu":
                model = model.to(device)
                print(f"   ✅ 已移动到设备: {device}")

            # 优化模型性能
            model = BERTOptimizer.optimize_model_loading(model)

            # 优化tokenizer
            tokenizer = BERTOptimizer.optimize_tokenizer(tokenizer)

            model.eval()
            return tokenizer, model

        except Exception as e:
            if is_local_path:
                self.logger.error(f"本地模型加载失败 [{config.model_path}]: {e}")
                raise e
            else:
                # 如果魔搭下载失败,尝试使用HuggingFace官方源
                self.logger.warning(f"魔搭下载失败,尝试使用HuggingFace官方源: {e}")
                os.environ.pop("HF_ENDPOINT", None)

                try:
                    tokenizer = AutoTokenizer.from_pretrained(
                        config.model_path, cache_dir=config.cache_dir, use_fast=config.use_fast
                    )

                    if config.task_type == "classification":
                        model = AutoModelForSequenceClassification.from_pretrained(
                            config.model_path, cache_dir=config.cache_dir
                        )
                    else:
                        model = AutoModel.from_pretrained(
                            config.model_path, cache_dir=config.cache_dir
                        )

                    model.eval()
                    return tokenizer, model
                except Exception as e2:
                    self.logger.error(f"所有下载方式都失败: {e2}")
                    raise e2

    async def encode(
        self,
        texts: str | list[str],
        model_key: str = "general",
        return_pooler: bool = True,
        return_attention: bool = False,
    ) -> BERTResult:
        """
        文本编码

        Args:
            texts: 文本或文本列表
            model_key: 模型键名
            return_pooler: 是否返回pooler输出
            return_attention: 是否返回attention

        Returns:
            BERT结果
        """
        await self.initialize_model(model_key)

        # 标准化输入
        if isinstance(texts, str):
            texts = [texts]
            single_text = True
        else:
            single_text = False

        model_info = self.models[model_key]
        tokenizer = model_info["tokenizer"]
        model = model_info["model"]

        start_time = asyncio.get_event_loop().time()

        try:
            # 在线程池中执行推理
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._encode_sync,
                texts,
                tokenizer,
                model,
                model_info["config"],
                return_pooler,
                return_attention,
            )

            # 计算处理时间
            processing_time = asyncio.get_event_loop().time() - start_time

            # 更新统计
            self.stats["total_requests"] += 1
            self.stats["total_processing_time"] += processing_time
            if model_key not in self.stats["model_usage"]:
                self.stats["model_usage"][model_key] = 0
            self.stats["model_usage"][model_key] += 1

            # 处理单个文本情况
            if single_text:
                for key, value in result.items():
                    if isinstance(value, np.ndarray) and value.ndim > 1:
                        result[key] = value[0]

            result["processing_time"] = processing_time
            result["model_name"] = model_info["config"].name

            return BERTResult(**result)

        except Exception as e:
            self.logger.error(f"编码失败 [{model_key}]: {e}")
            raise e

    def _encode_sync(
        self,
        texts: list[str],
        tokenizer,
        model,
        config: BERTModelConfig,
        return_pooler: bool,
        return_attention: bool,
    ) -> dict[str, Any]:
        """同步编码(在线程池中执行)"""
        # Tokenization
        inputs = tokenizer(
            texts, padding=True, truncation=True, max_length=config.max_length, return_tensors="pt"
        )

        # Move to device
        if hasattr(model, "device"):
            device = next(model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}

        # Model inference
        with torch.no_grad():
            if isinstance(model, AutoModelForSequenceClassification):
                outputs = model(**inputs)
                logits = outputs.logits
                predictions = torch.softmax(logits, dim=-1)
                result = {
                    "predictions": predictions.cpu().numpy(),
                    "confidence": torch.max(predictions, dim=-1)[0].cpu().numpy().mean(),
                }
            else:
                outputs = model(
                    **inputs, output_hidden_states=True, output_attentions=return_attention
                )

                result = {
                    "embeddings": outputs.last_hidden_state.cpu().numpy(),
                    "hidden_states": (
                        [h.cpu().numpy() for h in outputs.hidden_states]
                        if outputs.hidden_states
                        else None
                    ),
                }

                if return_pooler and hasattr(outputs, "pooler_output"):
                    result["pooler_output"] = outputs.pooler_output.cpu().numpy()

                if return_attention and outputs.attentions:
                    result["attentions"]] = [a.cpu().numpy() for a in outputs.attentions]

        return result

    async def classify_text(
        self, text: str, model_key: str = "legal", labels: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """
        文本分类

        Args:
            text: 输入文本
            model_key: 模型键名
            labels: 标签列表

        Returns:
            分类结果
        """
        # 使用通用模型进行特征提取
        result = await self.encode(text, model_key, return_pooler=True)

        if result.pooler_output is not None:
            # 简单的分类逻辑(实际应用中应该使用专门的分类模型)
            embedding = result.pooler_output

            # 这里可以添加分类逻辑
            classification = {
                "text": text,
                "embedding": embedding.tolist(),
                "model_used": result.model_name,
                "confidence": 0.8,  # 示例值
            }

            if labels:
                # 简单的标签匹配逻辑
                classification["labels"] = labels
                # TODO: 实际的分类逻辑

            return classification

        return {"error": "无法生成分类结果"}

    async def extract_features(
        self, texts: str | list[str], model_key: str = "general", layer: int = -1
    ) -> np.ndarray:
        """
        提取特征向量

        Args:
            texts: 输入文本
            model_key: 模型键名
            layer: 提取的层数(-1表示最后一层)

        Returns:
            特征向量
        """
        result = await self.encode(texts, model_key, return_pooler=False, return_attention=False)

        if result.embeddings is not None:
            # 提取指定层
            if layer == -1:
                return result.embeddings
            elif result.hidden_states and len(result.hidden_states) > abs(layer):
                return result.hidden_states[layer]
            else:
                return result.embeddings

        return array([])

    def get_model_info(self, model_key: Optional[str] = None) -> dict[str, Any]:
        """获取模型信息"""
        if model_key:
            if model_key in self.models:
                config = self.models[model_key]["config"]
                return {
                    "name": config.name,
                    "model_path": config.model_path,
                    "task_type": config.task_type,
                    "max_length": config.max_length,
                    "device": config.device,
                    "loaded": self.models[model_key]["loaded"],
                    "load_time": self.models[model_key].get("load_time", 0),
                }
            else:
                return {"error": f"模型 {model_key} 不存在"}
        else:
            return {key: self.get_model_info(key) for key in self.model_configs}

    def get_statistics(self) -> dict[str, Any]:
        """获取使用统计"""
        return {
            "total_requests": self.stats["total_requests"],
            "model_usage": self.stats["model_usage"],
            "avg_processing_time": (
                self.stats["total_processing_time"] / max(self.stats["total_requests"], 1)
            ),
            "available_models": list(self.model_configs.keys()),
            "loaded_models": [k for k, v in self.models.items() if v.get("loaded", False)],
        }

    async def preload_all_models(self):
        """预加载所有模型"""
        print("🔄 开始预加载所有BERT模型...")

        for model_key in self.model_configs:
            await self.initialize_model(model_key)

        print("✅ 所有BERT模型预加载完成!")

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        health = {"status": "healthy", "models": {}}

        for model_key in self.model_configs:
            try:
                # 简单测试
                test_text = "健康检查测试"
                result = await self.encode(test_text, model_key)
                health["models"][model_key]] = {
                    "status": "healthy",
                    "embedding_dim": (
                        len(result.embeddings[0]) if result.embeddings is not None else None
                    ),
                }
            except Exception as e:
                health["models"][model_key]] = {"status": "unhealthy", "error": str(e)}
                health["status"] = "degraded"

        return health


# 全局实例
_bert_service = None


async def get_bert_service() -> BERTService:
    """获取BERT服务实例"""
    global _bert_service
    if _bert_service is None:
        _bert_service = BERTService()
    return _bert_service


# 便捷函数
async def encode_with_legal_bert(texts: str | list[str]) -> BERTResult:
    """使用法律BERT编码"""
    service = await get_bert_service()
    return await service.encode(texts, "legal")


async def encode_with_general_bert(texts: str | list[str]) -> BERTResult:
    """使用通用BERT编码"""
    service = await get_bert_service()
    return await service.encode(texts, "general")


async def encode_with_multimodal_bert(texts: str | list[str]) -> BERTResult:
    """使用多模态BERT编码"""
    service = await get_bert_service()
    return await service.encode(texts, "multimodal")


# 导出
__all__ = [
    "BERTModelConfig",
    "BERTResult",
    "BERTService",
    "encode_with_general_bert",
    "encode_with_legal_bert",
    "encode_with_multimodal_bert",
    "get_bert_service",
]

