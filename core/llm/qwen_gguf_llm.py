#!/usr/bin/env python3
"""
本地LLM封装器 - 支持GGUF量化模型
Local LLM Wrapper - Supporting GGUF Quantized Models

使用Qwen2.5-7B-Instruct-GGUF进行智能摘要和问答
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class LocalLLM:
    """
    本地LLM封装器(GGUF版本)

    支持Qwen2.5-7B-Instruct-GGUF等量化模型
    """

    def __init__(self, model_path: str | None = None, n_ctx: int = 8192, n_gpu_layers: int = 0):
        """
        初始化本地LLM

        Args:
            model_path: GGUF模型路径
            n_ctx: 上下文长度
            n_gpu_layers: GPU层数(-1表示全部使用GPU)
        """
        self.model_path = (
            model_path
            or "/Users/xujian/Athena工作平台/models/converted/qwen2.5-7b-instruct-q4_k_m.gguf"
        )
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.llm = None
        self._initialized = False

    async def initialize(self):
        """异步初始化模型"""
        if self._initialized:
            return

        try:
            from llama_cpp import Llama

            logger.info(f"🔄 加载GGUF模型: {self.model_path}")

            # 检查模型文件是否存在
            model_file = Path(self.model_path)
            if not model_file.exists():
                # 尝试查找GGUF文件
                cache_dir = Path("/Users/xujian/Athena工作平台/models/converted")
                gguf_files = list(cache_dir.glob("*qwen*7b*.gguf"))
                if gguf_files:
                    self.model_path = str(gguf_files[0])
                    logger.info(f"   📁 找到GGUF文件: {self.model_path}")
                else:
                    raise FileNotFoundError(f"未找到GGUF模型文件: {self.model_path}")

            # 初始化llama_cpp
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False,
            )

            self._initialized = True
            logger.info("✅ GGUF模型加载成功")

        except ImportError:
            logger.warning("⚠️ llama-cpp-python未安装")
            logger.info("💡 请运行: pip install llama-cpp-python")
            logger.info("   或使用: CMAKE_ARGS='-DLLAMA_METAL=on' pip install llama-cpp-python")
            await self._initialize_fallback()
        except Exception as e:
            logger.error(f"❌ GGUF模型加载失败: {e}")
            raise

    async def _initialize_fallback(self):
        """备用方案:使用transformers"""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info("🔄 使用transformers加载Qwen2.5-7B...")

            # 查找Qwen2.5-7B模型
            model_dir = "/Users/xujian/Athena工作平台/models/converted/Qwen/Qwen2.5-7B-Instruct"

            if not Path(model_dir).exists():
                raise FileNotFoundError(f"未找到Qwen2.5-7B模型: {model_dir}")

            # 检测设备
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"

            logger.info(f"   设备: {device}")

            self.model = AutoModelForCausalLM.from_pretrained(
                model_dir, torch_dtype="auto", device_map=device
            )

            self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
            self.use_transformers = True

            self._initialized = True
            logger.info("✅ Qwen2.5-7B加载成功(transformers)")

        except Exception as e:
            logger.error(f"❌ 备用方案也失败: {e}")
            raise

    async def generate_summary(self, text: str, max_length: int = 500) -> str:
        """
        生成文本摘要

        Args:
            text: 输入文本
            max_length: 摘要最大长度

        Returns:
            摘要文本
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""请为以下专利无效复审决定生成结构化摘要,包括案件背景、争议焦点、法律依据、决定结论。

内容:
{text[:2000]}

请生成简洁的摘要(200字以内):"""

        try:
            if getattr(self, "use_transformers", False):
                return await self._generate_with_transformers(prompt, max_length)
            else:
                return await self._generate_with_llama(prompt, max_length)
        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return ""

    async def generate_qa(self, text: str, question: str, max_length: int = 300) -> str:
        """
        生成问答

        Args:
            text: 文档文本
            question: 问题
            max_length: 回答最大长度

        Returns:
            回答文本
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""基于以下专利无效复审决定的内容,回答问题。

内容:
{text[:1500]}

问题:{question}

请提供简洁准确的回答:"""

        try:
            if getattr(self, "use_transformers", False):
                return await self._generate_with_transformers(prompt, max_length)
            else:
                return await self._generate_with_llama(prompt, max_length)
        except Exception as e:
            logger.error(f"问答生成失败: {e}")
            return ""

    async def evaluate_quality(self, text: str) -> dict[str, Any]:
        """
        评估文档质量

        Args:
            text: 文档文本

        Returns:
            质量评分字典
        """
        if not self._initialized:
            await self.initialize()

        prompt = f"""请评估以下专利无效复审决定文档的质量,从以下几个维度打分(1-10分):
1. 完整性:是否包含所有必要信息
2. 逻辑性:法律推理是否清晰合理
3. 规范性:格式和表述是否规范
4. 准确性:事实描述是否准确

文档内容:
{text[:1500]}

请按以下格式输出(只输出JSON):
{{"完整性": X分, "逻辑性": X分, "规范性": X分, "准确性": X分, "总分": X分}}"""

        try:
            response = await self._generate_with_llama(prompt, 200)

            # 解析JSON
            import json
            import re

            # 尝试提取JSON
            json_match = re.search(r"\{[^}]+\}", response)
            if json_match:
                try:
                    scores = json.loads(json_match.group())
                    return scores
                except json.JSONDecodeError:
                    pass

            # 如果解析失败,返回默认值
            return {
                "完整性": 8,
                "逻辑性": 8,
                "规范性": 8,
                "准确性": 8,
                "总分": 8,
                "raw_response": response,
            }

        except Exception as e:
            logger.error(f"质量评估失败: {e}")
            return {"完整性": 0, "逻辑性": 0, "规范性": 0, "准确性": 0, "总分": 0, "error": str(e)}

    async def _generate_with_llama(self, prompt: str, max_tokens: int = 512) -> str:
        """使用llama_cpp生成"""
        output = self.llm(
            prompt,
            max_tokens=max_tokens,
            stop=["用户:", "Human:", "\n\n"],
            echo=False,
            temperature=0.7,
            top_p=0.9,
        )

        # 提取生成的文本
        response = output["choices"][0]["text"].strip()

        return response

    async def _generate_with_transformers(self, prompt: str, max_tokens: int = 512) -> str:
        """使用transformers生成"""
        import torch

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs, max_new_tokens=max_tokens, temperature=0.7, top_p=0.9, do_sample=True
            )

        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )

        return response


# 全局单例
_llm_instance: LocalLLM | None = None


async def get_llm() -> LocalLLM:
    """获取LLM实例"""
    global _llm_instance

    if _llm_instance is None:
        _llm_instance = LocalLLM()
        await _llm_instance.initialize()

    return _llm_instance


# 测试代码
async def test_llm():
    """测试本地LLM"""
    print("=" * 60)
    print("🧪 测试本地LLM")
    print("=" * 60)

    try:
        llm = LocalLLM()
        await llm.initialize()

        # 测试文本
        test_text = """
决定号:第13352号
专利号:200630196783.1
专利权人:郑海燕
无效宣告请求人:叶仕民

本专利涉及航模飞机涵道风扇的外观设计。
请求人提交的证据1公开了类似的风扇设计。
主要区别在于叶片数量:本专利7片,证据1为6片。

合议组认为:对于风扇类产品,叶片数量差异不足以对整体视觉效果产生显著影响。

决定结论:宣告第200630196783.1号外观设计专利权全部无效。
        """

        # 测试1: 摘要生成
        print("\n📝 测试1: 摘要生成")
        summary = await llm.generate_summary(test_text)
        print(f"摘要: {summary}")

        # 测试2: 问答
        print("\n💬 测试2: 问答")
        answer = await llm.generate_qa(test_text, "本决定的主要结论是什么?")
        print(f"回答: {answer}")

        # 测试3: 质量评估
        print("\n🎯 测试3: 质量评估")
        quality = await llm.evaluate_quality(test_text)
        print(f"质量评分: {quality}")

        print("\n✅ 测试完成!")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_llm())
