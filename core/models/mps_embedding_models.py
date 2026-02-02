#!/usr/bin/env python3
"""
MPS加速的嵌入模型管理器
 MPS-Accelerated Embedding Model Manager for mac_os

专为Apple Silicon优化的嵌入模型管理
作者: 小诺·双鱼公主 v4.0
创建时间: 2025-01-09
"""

import asyncio
import logging
from dataclasses import dataclass

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class EmbeddingResult:
    """嵌入结果"""

    embeddings: list[list[float]]  # 嵌入向量列表
    model_name: str
    dimension: int
    generation_time: float
    tokens_per_second: float
    device: str  # mps/cpu/cuda


class MPSEmbeddingModel:
    """MPS加速的嵌入模型基类"""

    def __init__(self, model_name: str, device: str = "mps"):
        """
        初始化MPS嵌入模型

        Args:
            model_name: 模型名称或路径
            device: 设备类型 (mps/cpu/cuda)
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.is_loaded = False

        # 检查MPS可用性
        if device == "mps":
            import torch

            if not torch.backends.mps.is_available():
                logger.warning("⚠️ MPS不可用,自动切换到CPU")
                self.device = "cpu"

        logger.info(f"🔧 MPS嵌入模型初始化: {model_name} (device: {self.device})")

    async def load(self) -> bool:
        """
        加载模型

        Returns:
            是否加载成功
        """
        try:
            import time

            start_time = time.time()

            if self.device == "mps":
                await self._load_with_mps()
            else:
                await self._load_with_cpu()

            self.is_loaded = True
            load_time = time.time() - start_time

            logger.info(f"✅ 模型加载成功 ({load_time:.2f}秒)")
            logger.info(f"   设备: {self.device}")
            return True

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            self.is_loaded = False
            return False

    async def _load_with_mps(self):
        """使用MPS加载模型"""
        raise NotImplementedError("子类必须实现此方法")

    async def _load_with_cpu(self):
        """使用CPU加载模型"""
        raise NotImplementedError("子类必须实现此方法")

    async def encode(
        self,
        texts: str | list[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> EmbeddingResult:
        """
        编码文本为嵌入向量

        Args:
            texts: 文本或文本列表
            batch_size: 批处理大小
            show_progress: 是否显示进度

        Returns:
            嵌入结果
        """
        if not self.is_loaded:
            raise RuntimeError("模型未加载,请先调用load()方法")

        import time

        start_time = time.time()

        # 确保输入是列表
        if isinstance(texts, str):
            texts = [texts]

        try:
            # 执行编码
            embeddings = await self._encode_texts(texts, batch_size, show_progress)

            generation_time = time.time() - start_time

            # 获取维度
            dimension = len(embeddings[0]) if embeddings else 0

            # 计算速度
            total_tokens = sum(len(text.split()) for text in texts)
            tokens_per_second = total_tokens / generation_time if generation_time > 0 else 0

            return EmbeddingResult(
                embeddings=embeddings,
                model_name=self.model_name,
                dimension=dimension,
                generation_time=generation_time,
                tokens_per_second=tokens_per_second,
                device=self.device,
            )

        except Exception as e:
            logger.error(f"❌ 编码失败: {e}")
            raise

    async def _encode_texts(
        self,
        texts: list[str],
        batch_size: int,
        show_progress: bool,
    ) -> list[list[float]]:
        """编码文本列表"""
        raise NotImplementedError("子类必须实现此方法")

    async def unload(self):
        """卸载模型"""
        if self.model:
            del self.model
            self.model = None
            self.is_loaded = False
            logger.info("🔒 模型已卸载")


class BGE_M3_Model(MPSEmbeddingModel):
    """BGE-M3模型 (MPS优化)"""

    async def _load_with_mps(self):
        """使用MPS加载BGE-M3"""
        try:
            import torch
            from sentence_transformers import SentenceTransformer

            # 加载模型
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
            )

            logger.info("✅ BGE-M3模型已加载到MPS")
            logger.info(f"   模型: {self.model_name}")
            logger.info(f"   设备: {self.device}")

        except Exception as e:
            logger.error(f"❌ MPS加载失败: {e}")
            raise

    async def _load_with_cpu(self):
        """使用CPU加载BGE-M3"""
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(self.model_name, device=self.device)
        logger.info("✅ BGE-M3模型已加载到CPU")

    async def _encode_texts(
        self,
        texts: list[str],
        batch_size: int,
        show_progress: bool,
    ) -> list[list[float]]:
        """编码文本"""
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

        # 转换为列表
        return embeddings.tolist()


class GTE_Qwen2_Model(MPSEmbeddingModel):
    """GTE-Qwen2-1.5B模型 (MPS优化)"""

    async def _load_with_mps(self):
        """使用MPS加载GTE-Qwen2"""
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # 加载模型到MPS
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)

            logger.info("✅ GTE-Qwen2模型已加载到MPS")
            logger.info(f"   模型: {self.model_name}")

        except Exception as e:
            logger.error(f"❌ MPS加载失败: {e}")
            raise

    async def _load_with_cpu(self):
        """使用CPU加载GTE-Qwen2"""
        from transformers import AutoModel, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        logger.info("✅ GTE-Qwen2模型已加载到CPU")

    async def _encode_texts(
        self,
        texts: list[str],
        batch_size: int,
        show_progress: bool,
    ) -> list[list[float]]:
        """编码文本"""
        import torch

        all_embeddings = []

        # 批处理
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            # Tokenize
            inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                return_tensors="pt",
            ).to(self.device)

            # 获取嵌入
            with torch.no_grad():
                outputs = self.model(**inputs)
                # 使用[CLS] token的嵌入作为句子嵌入
                embeddings = outputs.last_hidden_state[:, 0, :]

            # 转换为列表
            all_embeddings.extend(embeddings.cpu().tolist())

        return all_embeddings


class MPSEmbeddingManager:
    """MPS嵌入模型管理器"""

    def __init__(self):
        """初始化管理器"""
        self.models: dict[str, MPSEmbeddingModel] = {}
        self.default_device = "mps"  # 默认使用MPS

        # 检查MPS可用性
        import torch

        if not torch.backends.mps.is_available():
            logger.warning("⚠️ MPS不可用,使用CPU")
            self.default_device = "cpu"
        else:
            logger.info(f"✅ MPS加速可用 (device: {self.default_device})")

    async def load_model(
        self,
        model_id: str,
        model_name: str,
        model_type: str = "bge-m3",
    ) -> bool:
        """
        加载模型

        Args:
            model_id: 模型ID
            model_name: 模型名称或路径
            model_type: 模型类型 (bge-m3/gte-qwen2)

        Returns:
            是否加载成功
        """
        try:
            if model_type == "bge-m3":
                model = BGE_M3_Model(model_name, device=self.default_device)
            elif model_type == "gte-qwen2":
                model = GTE_Qwen2_Model(model_name, device=self.default_device)
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")

            success = await model.load()

            if success:
                self.models[model_id] = model
                logger.info(f"✅ 模型已加载: {model_id}")

            return success

        except Exception as e:
            logger.error(f"❌ 加载模型失败: {e}")
            return False

    async def encode(
        self,
        model_id: str,
        texts: str | list[str],
        batch_size: int = 32,
    ) -> EmbeddingResult:
        """
        编码文本

        Args:
            model_id: 模型ID
            texts: 文本或文本列表
            batch_size: 批处理大小

        Returns:
            嵌入结果
        """
        if model_id not in self.models:
            raise ValueError(f"模型未加载: {model_id}")

        model = self.models[model_id]
        return await model.encode(texts, batch_size)

    def get_loaded_models(self) -> list[str]:
        """获取已加载的模型列表"""
        return list(self.models.keys())

    async def unload_model(self, model_id: str):
        """
        卸载模型

        Args:
            model_id: 模型ID
        """
        if model_id in self.models:
            await self.models[model_id].unload()
            del self.models[model_id]
            logger.info(f"🔒 模型已卸载: {model_id}")


# 全局单例
_manager: MPSEmbeddingManager | None = None


def get_mps_embedding_manager() -> MPSEmbeddingManager:
    """获取MPS嵌入模型管理器单例"""
    global _manager
    if _manager is None:
        _manager = MPSEmbeddingManager()
    return _manager


# 预配置的模型
async def load_preset_mps_models():
    """加载预配置的MPS模型"""
    manager = get_mps_embedding_manager()

    # BGE-M3
    await manager.load_model(
        model_id="bge-m3-zh",
        model_name="BAAI/bge-m3",
        model_type="bge-m3",
    )

    # GTE-Qwen2-1.5B
    await manager.load_model(
        model_id="gte-qwen2-zh",
        model_name="iic/gte_Qwen2-1.5B-instruct",
        model_type="gte-qwen2",
    )

    logger.info("✅ 预配置MPS模型已加载")


if __name__ == "__main__":
    # 测试MPS嵌入模型
    async def test():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        manager = get_mps_embedding_manager()

        # 测试BGE-M3
        print("\n🧪 测试BGE-M3模型")
        print("=" * 80)

        success = await manager.load_model(
            model_id="bge-m3-zh",
            model_name="BAAI/bge-m3",
            model_type="bge-m3",
        )

        if success:
            result = await manager.encode(
                "bge-m3-zh",
                ["你好,世界!", "这是一个测试。"],
                batch_size=32,
            )

            print("\n📊 编码结果:")
            print(f"模型: {result.model_name}")
            print(f"维度: {result.dimension}")
            print(f"设备: {result.device}")
            print(f"耗时: {result.generation_time:.2f}秒")
            print(f"速度: {result.tokens_per_second:.2f} tokens/秒")
            print(f"向量数量: {len(result.embeddings)}")

    asyncio.run(test())
