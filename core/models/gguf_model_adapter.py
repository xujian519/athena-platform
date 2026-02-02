#!/usr/bin/env python3
"""
GGUF模型适配器
GGUF Model Adapter for llama.cpp

支持加载和运行GGUF格式的量化模型,兼容Metal加速
作者: 小诺·双鱼公主 v4.0
创建时间: 2025-01-09
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class GenerationResult:
    """生成结果"""

    text: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    model: str
    generation_time: float
    tokens_per_second: float


class GGUFModelAdapter:
    """GGUF模型适配器"""

    def __init__(self, model_path: str, config: dict[str, Any] | None = None):
        """
        初始化GGUF模型适配器

        Args:
            model_path: GGUF模型文件路径
            config: 模型配置
        """
        self.model_path = model_path
        self.config = config or {}
        self.model = None
        self.is_loaded = False

        # 默认配置
        self.n_ctx = self.config.get("n_ctx", 32768)
        self.n_batch = self.config.get("n_batch", 512)
        self.n_threads = self.config.get("n_threads", 8)
        self.gpu_layers = self.config.get("gpu_layers", -1)
        self.use_mmap = self.config.get("use_mmap", True)
        self.use_mlock = self.config.get("use_mlock", False)

        # 生成参数
        self.temperature = self.config.get("temperature", 0.7)
        self.top_p = self.config.get("top_p", 0.9)
        self.top_k = self.config.get("top_k", 40)
        self.repeat_penalty = self.config.get("repeat_penalty", 1.1)

        logger.info(f"🔧 GGUF模型适配器初始化: {model_path}")

    async def load(self) -> bool:
        """
        加载模型

        Returns:
            是否加载成功
        """
        try:
            if self.is_loaded:
                logger.warning("⚠️ 模型已加载")
                return True

            logger.info(f"📦 正在加载GGUF模型: {self.model_path}")

            # 动态导入llama_cpp(如果未安装会抛出 ImportError)
            try:
                from llama_cpp import Llama
            except ImportError:
                logger.error("❌ llama-cpp-python未安装")
                logger.error("   请运行: pip install llama-cpp-python")
                logger.error(
                    "   Apple Silicon加速: CMAKE_ARGS='-DLLAMA_METAL=on' pip install llama-cpp-python --no-cache-dir --force-reinstall"
                )
                return False

            # 加载模型
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_batch=self.n_batch,
                n_threads=self.n_threads,
                n_gpu_layers=self.gpu_layers,
                use_mmap=self.use_mmap,
                use_mlock=self.use_mlock,
                verbose=False,
            )

            self.is_loaded = True
            logger.info("✅ GGUF模型加载成功")
            logger.info(f"   上下文长度: {self.n_ctx:,}")
            logger.info(f"   GPU层数: {self.gpu_layers if self.gpu_layers > 0 else '全部'}")
            logger.info(f"   批处理大小: {self.n_batch}")

            return True

        except Exception as e:
            logger.error(f"❌ 加载GGUF模型失败: {e}")
            self.is_loaded = False
            return False

    async def unload(self):
        """卸载模型"""
        if self.model:
            del self.model
            self.model = None
            self.is_loaded = False
            logger.info("🔒 GGUF模型已卸载")

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        repeat_penalty: float | None = None,
        stop: list[str] | None = None,
        echo: bool = False,
    ) -> GenerationResult:
        """
        生成文本

        Args:
            prompt: 提示文本
            max_tokens: 最大生成token数
            temperature: 温度参数(覆盖默认)
            top_p: top-p采样(覆盖默认)
            top_k: top-k采样(覆盖默认)
            repeat_penalty: 重复惩罚(覆盖默认)
            stop: 停止词列表
            echo: 是否回显提示

        Returns:
            生成结果
        """
        if not self.is_loaded:
            raise RuntimeError("模型未加载,请先调用load()方法")

        import time

        start_time = time.time()

        # 使用提供的参数或默认参数
        temp = temperature if temperature is not None else self.temperature
        tp = top_p if top_p is not None else self.top_p
        tk = top_k if top_k is not None else self.top_k
        rp = repeat_penalty if repeat_penalty is not None else self.repeat_penalty

        try:
            # 调用模型生成
            output = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temp,
                top_p=tp,
                top_k=tk,
                repeat_penalty=rp,
                stop=stop or [],
                echo=echo,
            )

            # 解析结果
            generated_text = output["choices"][0]["text"]
            prompt_tokens = output.get("usage", {}).get("prompt_tokens", 0)
            completion_tokens = output.get("usage", {}).get("completion_tokens", 0)
            total_tokens = prompt_tokens + completion_tokens

            generation_time = time.time() - start_time
            tokens_per_second = completion_tokens / generation_time if generation_time > 0 else 0

            result = GenerationResult(
                text=generated_text,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model=self.model_path,
                generation_time=generation_time,
                tokens_per_second=tokens_per_second,
            )

            logger.debug(
                f"✅ 生成完成: {completion_tokens} tokens, {tokens_per_second:.2f} tokens/s"
            )

            return result

        except Exception as e:
            logger.error(f"❌ 生成失败: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        repeat_penalty: float | None = None,
    ):
        """
        流式生成文本

        Args:
            prompt: 提示文本
            max_tokens: 最大生成token数
            temperature: 温度参数(覆盖默认)
            top_p: top-p采样(覆盖默认)
            top_k: top-k采样(覆盖默认)
            repeat_penalty: 重复惩罚(覆盖默认)

        Yields:
            生成的文本片段
        """
        if not self.is_loaded:
            raise RuntimeError("模型未加载,请先调用load()方法")

        # 使用提供的参数或默认参数
        temp = temperature if temperature is not None else self.temperature
        tp = top_p if top_p is not None else self.top_p
        tk = top_k if top_k is not None else self.top_k
        rp = repeat_penalty if repeat_penalty is not None else self.repeat_penalty

        try:
            # 流式生成
            stream = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temp,
                top_p=tp,
                top_k=tk,
                repeat_penalty=rp,
                stream=True,
            )

            for chunk in stream:
                yield chunk["choices"][0]["text"]

        except Exception as e:
            logger.error(f"❌ 流式生成失败: {e}")
            raise

    def get_model_info(self) -> dict[str, Any]:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        return {
            "model_path": self.model_path,
            "is_loaded": self.is_loaded,
            "n_ctx": self.n_ctx,
            "n_batch": self.n_batch,
            "n_threads": self.n_threads,
            "gpu_layers": self.gpu_layers,
            "use_mmap": self.use_mmap,
            "use_mlock": self.use_mlock,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repeat_penalty": self.repeat_penalty,
        }


class GGUFModelManager:
    """GGUF模型管理器"""

    def __init__(self):
        """初始化模型管理器"""
        self.adapters: dict[str, GGUFModelAdapter] = {}

    async def load_model(
        self, model_id: str, model_path: str, config: dict[str, Any] | None = None
    ) -> bool:
        """
        加载模型

        Args:
            model_id: 模型ID
            model_path: 模型路径
            config: 模型配置

        Returns:
            是否加载成功
        """
        if model_id in self.adapters:
            logger.warning(f"⚠️ 模型已存在: {model_id}")
            return True

        adapter = GGUFModelAdapter(model_path, config)
        success = await adapter.load()

        if success:
            self.adapters[model_id] = adapter
            logger.info(f"✅ 模型已加载: {model_id}")

        return success

    async def unload_model(self, model_id: str):
        """
        卸载模型

        Args:
            model_id: 模型ID
        """
        if model_id in self.adapters:
            await self.adapters[model_id].unload()
            del self.adapters[model_id]
            logger.info(f"🔒 模型已卸载: {model_id}")

    def get_adapter(self, model_id: str) -> GGUFModelAdapter | None:
        """
        获取模型适配器

        Args:
            model_id: 模型ID

        Returns:
            模型适配器,不存在返回None
        """
        return self.adapters.get(model_id)

    def list_loaded_models(self) -> list[str]:
        """
        列出已加载的模型

        Returns:
            模型ID列表
        """
        return list(self.adapters.keys())


# 全局单例
_manager: GGUFModelManager | None = None


def get_gguf_manager() -> GGUFModelManager:
    """获取GGUF模型管理器单例"""
    global _manager
    if _manager is None:
        _manager = GGUFModelManager()
    return _manager


if __name__ == "__main__":
    # 测试GGUF模型适配器
    async def test():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # 模型路径
        model_path = "/Users/xujian/Athena工作平台/models/local/qwen2.5-14b-instruct-gguf/Qwen2.5-14B-Instruct-Q4_K_M.gguf"

        # 创建适配器
        adapter = GGUFModelAdapter(
            model_path,
            config={
                "n_ctx": 4096,
                "n_threads": 8,
                "gpu_layers": -1,
            },
        )

        # 加载模型
        if await adapter.load():
            print("✅ 模型加载成功")

            # 生成文本
            result = await adapter.generate(
                prompt="你好,请简单介绍一下你自己。",
                max_tokens=200,
            )

            print("\n📝 生成结果:")
            print(f"{result.text}")
            print("\n📊 统计:")
            print(f"  提示tokens: {result.prompt_tokens}")
            print(f"  生成tokens: {result.completion_tokens}")
            print(f"  总tokens: {result.tokens_used}")
            print(f"  生成时间: {result.generation_time:.2f}秒")
            print(f"  生成速度: {result.tokens_per_second:.2f} tokens/秒")

            # 卸载模型
            await adapter.unload()

    asyncio.run(test())
