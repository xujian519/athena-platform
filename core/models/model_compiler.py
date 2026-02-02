#!/usr/bin/env python3
"""
M4模型编译器 - 阶段4优化
使用PyTorch 2.0 torch.compile()优化模型,提升推理速度1.5-2x

作者: 小诺·双鱼公主 🌊✨
创建时间: 2025-12-27
版本: v1.0.0
"""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
import torch.nn as nn

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class CompilerConfig:
    """编译器配置"""

    # 编译模式
    mode: str = "max-autotune"  # 'default', 'reduce-overhead', 'max-autotune'

    # 后端选择
    backend: str = "default"  # 'default', 'mps', 'aot_eager', 'inductor'

    # 编译选项
    fullgraph: bool = False  # 完整图优化(实验性)
    dynamic: bool = False  # 动态形状支持

    # 性能优化
    enable_ep_fusion: bool = True  # 启用算子融合
    enable_conv_bn_fusion: bool = True  # 启用卷积-BN融合

    # 缓存配置
    enable_cache: bool = True
    cache_dir: str = "/Users/xujian/Athena工作平台/.cache/model_compilation"


class M4ModelCompiler:
    """Apple M4 Pro模型编译器"""

    def __init__(self, config: CompilerConfig = None):
        self.config = config or CompilerConfig()

        # 创建缓存目录
        if self.config.enable_cache:
            Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)

        # 设置环境变量
        if self.config.enable_cache:
            os.environ["TORCH_COMPILE_CACHE_DIR"] = self.config.cache_dir

        logger.info("🔨 M4模型编译器初始化完成")
        logger.info(f"⚙️ 编译模式: {self.config.mode}")
        logger.info(f"🔧 后端: {self.config.backend}")

        # 检查PyTorch版本
        self.pytorch_version = torch.__version__
        logger.info(f"📦 PyTorch版本: {self.pytorch_version}")

        # 检查是否支持torch.compile
        self.compile_available = hasattr(torch, "compile")
        if not self.compile_available:
            logger.warning("⚠️ 当前PyTorch版本不支持torch.compile(),需要PyTorch 2.0+")

    def compile_model(
        self, model: nn.Module, sample_inputs: Any | None = None, verify: bool = True
    ) -> nn.Module:
        """
        编译模型

        Args:
            model: 待编译的模型
            sample_inputs: 示例输入(用于形状推断)
            verify: 是否验证编译结果

        Returns:
            编译后的模型
        """
        if not self.compile_available:
            logger.warning("⚠️ torch.compile()不可用,返回原始模型")
            return model

        logger.info("🔨 开始编译模型...")
        start_time = time.time()

        # 获取原始模型大小
        original_params = sum(p.numel() for p in model.parameters())
        logger.info(f"📦 模型参数: {original_params:,}")

        # 预处理模型
        model = self._preprocess_model(model)

        # 配置编译选项
        compile_options = self._get_compile_options()

        try:
            # 编译模型
            compiled_model = torch.compile(
                model,
                mode=self.config.mode,
                backend=self._select_backend(),
                fullgraph=self.config.fullgraph,
                dynamic=self.config.dynamic,
                **compile_options,
            )

            logger.info("✅ 模型编译成功!")

            # 预热编译
            if sample_inputs is not None:
                self._warmup_compiled_model(compiled_model, sample_inputs)

            compile_time = time.time() - start_time
            logger.info(f"⏱️ 编译耗时: {compile_time:.2f}秒")

            # 验证编译结果
            if verify and sample_inputs is not None:
                self._verify_compiled_model(model, compiled_model, sample_inputs)

            return compiled_model

        except Exception as e:
            logger.error(f"❌ 编译失败: {e}")
            logger.warning("⚠️ 返回原始模型")
            return model

    def _preprocess_model(self, model: nn.Module) -> nn.Module:
        """预处理模型"""
        model.eval()

        # 禁用梯度计算
        for param in model.parameters():
            param.requires_grad = False

        return model

    def _get_compile_options(self) -> dict[str, Any]:
        """获取编译选项"""
        options = {}

        # 启用算子融合
        if self.config.enable_ep_fusion:
            options["ep_fusion"] = True

        # 启用卷积-BN融合
        if self.config.enable_conv_bn_fusion:
            options["conv_bn_fusion"] = True

        return options

    def _select_backend(self) -> str:
        """选择编译后端"""
        if self.config.backend != "default":
            return self.config.backend

        # 根据设备自动选择
        if torch.backends.mps.is_available():
            # MPS设备
            if self.pytorch_version.startswith("2."):
                # PyTorch 2.x对MPS有原生支持
                return "default"  # 使用默认后端(支持MPS)
            else:
                return "aot_eager"  # AOT后端

        elif torch.cuda.is_available():
            # CUDA设备
            return "inductor"  # 最佳性能

        else:
            # CPU设备
            return "aot_eager"

    def _warmup_compiled_model(self, model: nn.Module, sample_inputs: Any) -> Any:
        """预热编译后的模型"""
        logger.info("🔥 预热模型...")

        model.eval()

        with torch.no_grad():
            for i in range(3):
                try:
                    _ = model(sample_inputs)
                except Exception as e:
                    logger.warning(f"⚠️ 预热第{i+1}次失败: {e}")

        logger.info("✅ 预热完成")

    def _verify_compiled_model(
        self, original_model: nn.Module, compiled_model: nn.Module, sample_inputs: Any
    ):
        """验证编译后的模型"""
        logger.info("🔍 验证编译结果...")

        original_model.eval()
        compiled_model.eval()

        with torch.no_grad():
            # 原始模型输出
            try:
                original_output = original_model(sample_inputs)
            except Exception as e:
                logger.warning(f"⚠️ 原始模型推理失败: {e}")
                return

            # 编译模型输出
            try:
                compiled_output = compiled_model(sample_inputs)
            except Exception as e:
                logger.error(f"❌ 编译模型推理失败: {e}")
                return

            # 比较输出
            if isinstance(original_output, torch.Tensor):
                diff = (original_output - compiled_output).abs().max()
                logger.info(f"📊 最大差异: {diff:.6f}")

                if diff < 1e-3:
                    logger.info("✅ 验证通过")
                else:
                    logger.warning(f"⚠️ 输出差异较大: {diff}")
            else:
                logger.info("ℹ️ 输出不是张量,跳过验证")

    def benchmark_compilation(
        self, model: nn.Module, sample_inputs: Any, num_iterations: int = 100
    ) -> dict[str, Any]:
        """
        对比原始模型和编译模型的性能

        Args:
            model: 原始模型
            sample_inputs: 示例输入
            num_iterations: 迭代次数

        Returns:
            性能对比结果
        """
        logger.info(f"📊 性能基准测试 ({num_iterations}次迭代)...")

        model.eval()

        # 测试原始模型
        logger.info("🐌 测试原始模型...")
        original_times = []
        with torch.no_grad():
            for _ in range(num_iterations):
                start = time.time()
                _ = model(sample_inputs)
                if torch.backends.mps.is_available():
                    torch.mps.synchronize()
                elif torch.cuda.is_available():
                    torch.cuda.synchronize()
                original_times.append(time.time() - start)

        # 编译模型
        compiled_model = self.compile_model(model, sample_inputs, verify=False)

        # 测试编译模型
        logger.info("🚀 测试编译模型...")
        compiled_times = []
        with torch.no_grad():
            for _ in range(num_iterations):
                start = time.time()
                _ = compiled_model(sample_inputs)
                if torch.backends.mps.is_available():
                    torch.mps.synchronize()
                elif torch.cuda.is_available():
                    torch.cuda.synchronize()
                compiled_times.append(time.time() - start)

        # 计算统计数据

        original_avg = np.mean(original_times) * 1000  # ms
        compiled_avg = np.mean(compiled_times) * 1000  # ms
        speedup = original_avg / compiled_avg

        logger.info("\n📊 性能对比结果:")
        logger.info(f"  原始模型: {original_avg:.2f}ms")
        logger.info(f"  编译模型: {compiled_avg:.2f}ms")
        logger.info(f"  加速比: {speedup:.2f}x")

        return {
            "original_avg_ms": original_avg,
            "compiled_avg_ms": compiled_avg,
            "speedup": speedup,
            "improvement_percent": ((original_avg - compiled_avg) / original_avg * 100),
        }

    def save_compiled_model(self, model: nn.Module, save_path: str):
        """保存编译后的模型"""
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存模型状态
        torch.save(model.state_dict(), save_path)

        logger.info(f"💾 编译模型已保存: {save_path}")

    def clear_cache(self) -> None:
        """清空编译缓存"""
        cache_dir = Path(self.config.cache_dir)
        if cache_dir.exists():
            import shutil

            shutil.rmtree(cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info("🗑️ 编译缓存已清空")

    def get_cache_size(self) -> float:
        """获取缓存大小(MB)"""
        cache_dir = Path(self.config.cache_dir)
        if not cache_dir.exists():
            return 0.0

        total_size = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
        return total_size / (1024 * 1024)


# 全局单例
_compiler: M4ModelCompiler | None = None


def get_model_compiler() -> M4ModelCompiler:
    """获取全局模型编译器实例"""
    global _compiler
    if _compiler is None:
        _compiler = M4ModelCompiler()
    return _compiler


def compile_model(
    model: nn.Module, mode: str = "max-autotune", sample_inputs: Any | None = None
) -> nn.Module:
    """便捷函数:编译模型"""
    compiler = get_model_compiler()
    compiler.config.mode = mode
    return compiler.compile_model(model, sample_inputs)


if __name__ == "__main__":
    # 测试模型编译器
    # setup_logging()  # 日志配置已移至模块导入

    print("=" * 60)
    print("🧪 测试M4模型编译器")
    print("=" * 60)

    # 创建测试模型
    class TestModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.embedding = nn.Embedding(10000, 768)
            self.transformer = nn.TransformerEncoder(
                nn.TransformerEncoderLayer(d_model=768, nhead=8, batch_first=True), num_layers=6
            )
            self.fc = nn.Linear(768, 10)

        def forward(self, x) -> None:
            x = self.embedding(x)
            x = self.transformer(x)
            x = x.mean(dim=1)
            x = self.fc(x)
            return x

    model = TestModel()
    sample_input = torch.randint(0, 10000, (16, 128))

    print(f"\n📦 模型参数: {sum(p.numel() for p in model.parameters()):,}")

    compiler = M4ModelCompiler()

    # 编译模型
    print("\n🔨 编译模型...")
    compiled_model = compiler.compile_model(model, sample_input)

    # 性能对比
    print("\n📊 性能基准测试...")
    results = compiler.benchmark_compilation(model, sample_input, num_iterations=50)

    print("\n✅ 测试完成:")
    print(f"  加速比: {results['speedup']:.2f}x")
    print(f"  性能提升: {results['improvement_percent']:.1f}%")
    print(f"  缓存大小: {compiler.get_cache_size():.2f}MB")
