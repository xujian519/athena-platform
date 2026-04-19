#!/usr/bin/env python3
from __future__ import annotations
"""
统一LLM层 - MLX Gemma4适配器
适配本地MLX框架的Gemma4模型（31B参数，4-bit量化）

作者: Claude Code
日期: 2026-04-04
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Any

from core.llm.base import (
    BaseLLMAdapter,
    DeploymentType,
    LLMRequest,
    LLMResponse,
    ModelCapability,
    ModelType,
)

logger = logging.getLogger(__name__)


class MLXGemma4Adapter(BaseLLMAdapter):
    """
    MLX Gemma4适配器

    适配本地部署的MLX框架
    支持Gemma4-31B-4bit模型，使用subprocess调用mlx_vlm.generate
    """

    def __init__(
        self,
        model_id: str,
        capability: ModelCapability,
        model_path: str = "/Users/xujian/models/gemma-4-31b-it-4bit-mlx",
        max_tokens: int = 300,
        timeout: int = 300,
    ):
        """
        初始化MLX Gemma4适配器

        Args:
            model_id: 模型ID
            capability: 模型能力定义
            model_path: MLX模型路径
            max_tokens: 最大生成token数
            timeout: 超时时间（秒）
        """
        super().__init__(model_id, capability)
        self.model_path = model_path
        self.max_tokens = max_tokens
        self.timeout = timeout

        # 检查MLX VLM是否可用
        self.mlx_available = self._check_mlx_vlm()

    def _check_mlx_vlm(self) -> bool:
        """检查MLX VLM是否安装"""
        try:
            import mlx_vlm

            logger.info("✅ MLX VLM已安装")
            return True
        except ImportError:
            logger.warning("⚠️ MLX VLM未安装，请运行: pip install mlx-vlm")
            return False
        except Exception as e:
            logger.warning(f"⚠️ MLX VLM检查失败: {e}")
            return False

    async def initialize(self) -> bool:
        """
        初始化MLX Gemma4适配器

        Returns:
            bool: 初始化是否成功
        """
        try:
            # 检查MLX VLM
            if not self.mlx_available:
                logger.error("❌ MLX VLM不可用")
                return False

            # 检查模型路径
            model_path = Path(self.model_path)
            if not model_path.exists():
                logger.error(f"❌ 模型路径不存在: {self.model_path}")
                return False

            # 检查必要文件
            required_files = ["config.json", "tokenizer.json"]
            for file_name in required_files:
                file_path = model_path / file_name
                if not file_path.exists():
                    logger.error(f"❌ 缺少必要文件: {file_path}")
                    return False

            logger.info(f"✅ MLX Gemma4适配器初始化完成: {self.model_id}")
            logger.info(f"   模型路径: {self.model_path}")
            logger.info(f"   最大tokens: {self.max_tokens}")
            logger.info(f"   超时: {self.timeout}秒")
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"❌ MLX Gemma4适配器初始化失败: {e}")
            self._initialized = False
            return False

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成响应

        Args:
            request: LLM请求

        Returns:
            LLMResponse: LLM响应
        """
        start_time = time.time()

        # 验证请求
        if not await self.validate_request(request):
            return LLMResponse(
                content="请求参数不合法",
                model_used=self.model_id,
                processing_time=time.time() - start_time,
            )

        try:
            # 检查MLX是否可用
            if not self.mlx_available:
                raise RuntimeError("MLX VLM不可用，请先安装: pip install mlx-vlm")

            # 构建提示词
            prompt = request.message
            if request.context.get("system_prompt"):
                prompt = f"{request.context['system_prompt']}\n\n{request.message}"

            # 构建MLX命令
            cmd = [
                "python",
                "-m",
                "mlx_vlm.generate",
                "--model",
                self.model_path,
                "--prompt",
                prompt,
                "--max-tokens",
                str(request.max_tokens or self.max_tokens),
                "--kv-bits",
                "4",
                "--kv-quant-scheme",
                "turboquant",
                "--quantized-kv-start",
                "0",
            ]

            # 处理图片（如果存在）
            if request.context.get("image_path"):
                cmd.extend(["--image", request.context["image_path"]])

            logger.info(f"🔄 执行MLX命令: {' '.join(cmd[:6])}...")

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            # 检查执行结果
            if result.returncode != 0:
                logger.error(f"❌ MLX生成失败 (退出码: {result.returncode})")
                logger.error(f"   错误输出: {result.stderr}")
                raise RuntimeError(f"MLX生成错误: {result.stderr}")

            # 提取生成的文本
            response_text = result.stdout.strip()

            # 计算处理时间
            processing_time = time.time() - start_time

            logger.info(f"✅ MLX生成成功，耗时: {processing_time:.2f}秒")
            logger.debug(f"   生成文本长度: {len(response_text)}")

            # 返回响应
            return LLMResponse(
                content=response_text,
                model_used=self.model_id,
                tokens_used=len(response_text),  # 估算
                processing_time=processing_time,
                cost=0.0,  # 本地模型免费
                quality_score=self.capability.quality_score,
            )

        except subprocess.TimeoutExpired:
            logger.error(f"❌ MLX生成超时 (>{self.timeout}秒)")
            return LLMResponse(
                content=f"生成超时（{self.timeout}秒）",
                model_used=self.model_id,
                processing_time=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"❌ MLX生成失败: {e}", exc_info=True)
            return LLMResponse(
                content=f"生成失败: {str(e)}",
                model_used=self.model_id,
                processing_time=time.time() - start_time,
            )

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 模型是否健康可用
        """
        try:
            # 检查MLX VLM
            if not self.mlx_available:
                return False

            # 检查模型路径
            model_path = Path(self.model_path)
            if not model_path.exists():
                return False

            # 检查必要文件
            required_files = ["config.json", "tokenizer.json"]
            for file_name in required_files:
                if not (model_path / file_name).exists():
                    return False

            return True

        except Exception as e:
            logger.warning(f"⚠️ MLX健康检查失败: {e}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息字典
        """
        return {
            "model_id": self.model_id,
            "initialized": self._initialized,
            "capability": self.capability.to_dict(),
            "model_path": self.model_path,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "mlx_available": self.mlx_available,
        }


# 便捷函数：创建MLX Gemma4模型配置
def create_mlx_gemma4_capability() -> ModelCapability:
    """
    创建MLX Gemma4模型的能力配置

    Returns:
        ModelCapability: MLX Gemma4的能力定义
    """
    return ModelCapability(
        model_id="mlx-gemma4",
        model_type=ModelType.MULTIMODAL,  # 多模态模型
        deployment=DeploymentType.LOCAL,
        max_context=8192,  # MLX支持的上下文长度
        supports_streaming=False,  # MLX命令不支持流式
        supports_function_call=False,  # MLX VLM不支持函数调用
        supports_vision=True,  # 支持图像
        supports_thinking=False,  # MLX VLM不支持思考模式
        avg_latency_ms=1200.0,  # 31B参数，较慢
        throughput_tps=30.0,  # 31B参数，吞吐量较低
        cost_per_1k_tokens=0.0,  # 本地免费
        quality_score=0.96,  # 31B参数，质量最高
        suitable_tasks=[
            "high_quality",  # 最高质量输出
            "complex_reasoning",  # 复杂推理
            "multimodal",  # 多模态处理
            "image_analysis",  # 图像分析
            "document_analysis",  # 文档分析
            "ocr",  # OCR文字识别
            "visual_reasoning",  # 视觉推理
            "patent_analysis",  # 专利分析
            "legal_analysis",  # 法律分析
        ],
    )
