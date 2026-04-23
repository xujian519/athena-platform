#!/usr/bin/env python3
from __future__ import annotations
"""
混合精度推理管理器
Mixed Precision Inference Manager

提供torch.cuda.amp混合精度推理支持,优化NLP模型性能
作者: 小诺·双鱼座
创建时间: 2025-12-22
版本: v1.0.0 "AMP优化"
"""

import gc
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import psutil
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class PrecisionMode(Enum):
    """精度模式枚举"""
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    MIXED = "mixed"
    AUTO = "auto"

class DeviceType(Enum):
    """设备类型枚举"""
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Metal Performance Shaders
    AUTO = "auto"

@dataclass
class MixedPrecisionConfig:
    """混合精度配置"""
    # 基础配置
    precision_mode: PrecisionMode = PrecisionMode.AUTO
    device_type: DeviceType = DeviceType.AUTO

    # AMP配置
    enable_amp: bool = True
    use_bf16: bool = False  # 使用BFloat16 (如果硬件支持)
    autocast_enabled: bool = True

    # 优化设置
    gradient_clipping: bool = True
    max_grad_norm: float = 1.0
    loss_scaling: bool = True  # 自动损失缩放

    # 内存优化
    enable_memory_efficient_attention: bool = True
    use_flash_attention: bool = True  # 如果可用
    enable_checkpointing: bool = True

    # 批处理优化
    dynamic_batch_size: bool = True
    max_batch_size: int = 32
    min_batch_size: int = 1

    # 性能监控
    enable_profiling: bool = True
    log_memory_usage: bool = True
    benchmark_warmup_steps: int = 3

    # 错误处理
    fallback_to_fp32: bool = True
    overflow_check: bool = True

@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_inferences: int = 0
    avg_inference_time: float = 0.0
    peak_memory_usage: float = 0.0
    amp_speedup: float = 0.0
    overflow_count: int = 0
    fallback_count: int = 0

    # 详细统计
    fp32_inferences: int = 0
    fp16_inferences: int = 0
    mixed_inferences: int = 0

    # 内存统计
    baseline_memory: float = 0.0
    optimized_memory: float = 0.0
    memory_savings: float = 0.0

class MixedPrecisionManager:
    """混合精度推理管理器"""

    def __init__(self, config: MixedPrecisionConfig | None = None):
        self.name = "混合精度推理管理器"
        self.version = "v1.0.0 AMP优化"

        # 配置
        self.config = config or MixedPrecisionConfig()

        # 设备检测和配置
        self.device = self._detect_device()
        self.precision_mode = self._determine_precision_mode()

        # AMP相关
        self.scaler = None
        self.autocast_context = None

        # 性能统计
        self.metrics = PerformanceMetrics()
        self.baseline_metrics = {}

        # 设置日志
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.set_formatter(formatter)
            self.logger.add_handler(handler)
            self.logger.set_level(logging.INFO)

        # 初始化组件
        self._initialize_amp_components()

        # 预热
        if self.config.enable_profiling:
            self._warmup()

    def _detect_device(self) -> torch.device:
        """检测最优计算设备"""
        if self.config.device_type != DeviceType.AUTO:
            device_map = {
                DeviceType.CPU: "cpu",
                DeviceType.CUDA: "cuda",
                DeviceType.MPS: "mps"
            }
            return torch.device(device_map[self.config.device_type])

        # 自动检测最佳设备
        device = None

        if torch.cuda.is_available():
            device = torch.device("cuda")
            if hasattr(self, 'logger'):
                self._log(f"检测到CUDA设备: {torch.cuda.get_device_name()}")
                self._log(f"CUDA版本: {torch.version.cuda}")
                self._log(f"GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = torch.device("mps")
            if hasattr(self, 'logger'):
                self._log("检测到Apple Metal Performance Shaders (MPS)")
        else:
            device = torch.device("cpu")
            if hasattr(self, 'logger'):
                self._log("使用CPU设备")

        return device

    def _determine_precision_mode(self) -> PrecisionMode:
        """确定最佳精度模式"""
        if self.config.precision_mode != PrecisionMode.AUTO:
            return self.config.precision_mode

        # 自动选择最佳精度模式
        if self.device.type == "cuda":
            if torch.cuda.get_device_capability()[0] >= 8:  # Ampere+
                if self.config.use_bf16:
                    mode = PrecisionMode.BF16
                    if hasattr(self, 'logger'):
                        self._log("使用BFloat16精度 (Ampere+ GPU)")
                else:
                    mode = PrecisionMode.MIXED
                    if hasattr(self, 'logger'):
                        self._log("使用混合精度 (CUDA)")
            else:
                mode = PrecisionMode.MIXED
                if hasattr(self, 'logger'):
                    self._log("使用混合精度 (Volta/Turing GPU)")
        elif self.device.type == "mps":
            mode = PrecisionMode.FP16
            if hasattr(self, 'logger'):
                self._log("使用FP16精度 (Apple Silicon)")
        else:
            mode = PrecisionMode.FP32
            if hasattr(self, 'logger'):
                self._log("使用FP32精度 (CPU)")

        return mode

    def _initialize_amp_components(self):
        """初始化AMP组件"""
        if not self.config.enable_amp or self.device.type not in ["cuda", "mps"]:
            if hasattr(self, 'logger'):
                self._log("AMP已禁用或不支持当前设备")
            return

        try:
            if self.device.type == "cuda":
                # CUDA AMP
                from torch.cuda.amp import GradScaler, autocast
                self.scaler = GradScaler(enabled=self.config.loss_scaling)
                self.autocast_context = autocast(enabled=self.config.autocast_enabled)

                # 检查BF16支持
                bf16_supported = torch.cuda.get_device_capability()[0] >= 8
                if bf16_supported and self.config.use_bf16:
                    if hasattr(self, 'logger'):
                        self._log("启用BFloat16混合精度")
                else:
                    if hasattr(self, 'logger'):
                        self._log("启用FP16混合精度")

            elif self.device.type == "mps":
                # MPS使用FP16
                if hasattr(self, 'logger'):
                    self._log("MPS使用FP16优化")
                # 设置MPS精度
                torch.backends.mps.allow_tf32 = True

        except Exception as e:
            if hasattr(self, 'logger'):
                self._log(f"AMP初始化失败: {e}")
            if self.config.fallback_to_fp32:
                self.precision_mode = PrecisionMode.FP32
                if hasattr(self, 'logger'):
                    self._log("回退到FP32模式")


    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(f"[混合精度] {message}")

    def _warmup(self):
        """预热模型"""
        if hasattr(self, 'logger'):
            self._log("开始混合精度预热...")

        # 创建简单模型进行预热
        model = nn.Linear(512, 256).to(self.device)
        dummy_input = torch.randn(1, 512).to(self.device)

        with self.get_autocast_context():
            for _i in range(self.config.benchmark_warmup_steps):
                output = model(dummy_input)
                if self.scaler:
                    loss = output.sum()
                    self.scaler.scale(loss).backward()
                    self.scaler.step(torch.optim.SGD(model.parameters(), lr=0.01))
                    self.scaler.update()
                    model.zero_grad()

        if hasattr(self, 'logger'):
            self._log("混合精度预热完成")

        # 清理
        del model, dummy_input
        gc.collect()
        if self.device.type == "cuda":
            torch.cuda.empty_cache()

    def get_autocast_context(self):
        """获取autocast上下文"""
        if self.autocast_context:
            return self.autocast_context
        else:
            # 返回空的上下文管理器
            from contextlib import nullcontext
            return nullcontext()

    def optimize_model(self, model: nn.Module) -> nn.Module:
        """优化模型以支持混合精度"""
        self._log(f"优化模型: {model.__class__.__name__}")

        # 半精度转换
        if self.precision_mode in [PrecisionMode.FP16, PrecisionMode.MIXED]:
            if self.device.type in ["cuda", "mps"]:
                try:
                    model = model.half()
                    self._log("模型转换为半精度 (FP16)")
                except Exception as e:
                    self._log(f"半精度转换失败: {e}")
                    if self.config.fallback_to_fp32:
                        self._log("保持FP32精度")

        # 启用内存高效注意力
        if self.config.enable_memory_efficient_attention:
            try:
                if hasattr(model, 'gradient_checkpointing_enable'):
                    model.gradient_checkpointing_enable()
                    self._log("启用梯度检查点")
            except Exception as e:
                logger.warning(f'操作失败: {e}')

        # 设置优化后端
        if self.device.type == "cuda":
            try:
                # 启用TF32 (Ampere+)
                if torch.cuda.get_device_capability()[0] >= 8:
                    torch.backends.cuda.matmul.allow_tf32 = True
                    torch.backends.cudnn.allow_tf32 = True
                    self._log("启用TF32加速")
            except Exception as e:
                logger.warning(f'操作失败: {e}')

        return model

    def inference(self,
                  model: nn.Module,
                  inputs: torch.Tensor,
                  return_fp32: bool = True) -> torch.Tensor:
        """执行混合精度推理"""
        self.metrics.total_inferences += 1
        start_time = time.time()

        # 记录基准内存
        if self.metrics.total_inferences == 1:
            self.metrics.baseline_memory = self._get_memory_usage()

        try:
            with self.get_autocast_context():
                outputs = model(inputs)

                # 返回FP32结果(如果需要)
                if return_fp32 and outputs.dtype != torch.float32:
                    outputs = outputs.float()

                # 记录精度统计
                if outputs.dtype == torch.float16 or outputs.dtype == torch.bfloat16:
                    self.metrics.fp16_inferences += 1
                else:
                    self.metrics.fp32_inferences += 1

                # 检查溢出
                if self.config.overflow_check:
                    if torch.isnan(outputs).any() or torch.isinf(outputs).any():
                        self.metrics.overflow_count += 1
                        self._log("检测到数值溢出", "WARNING")

        except Exception as e:
            self.metrics.fallback_count += 1
            self._log(f"混合精度推理失败: {e}", "ERROR")

            if self.config.fallback_to_fp32:
                self._log("回退到FP32推理")
                with torch.cuda.amp.autocast(enabled=False):
                    outputs = model(inputs)

        # 更新统计
        inference_time = time.time() - start_time
        self._update_metrics(inference_time)

        return outputs

    def _update_metrics(self, inference_time: float):
        """更新性能指标"""
        # 更新平均推理时间
        self.metrics.avg_inference_time = (
            (self.metrics.avg_inference_time * (self.metrics.total_inferences - 1) + inference_time)
            / self.metrics.total_inferences
        )

        # 记录峰值内存
        current_memory = self._get_memory_usage()
        if current_memory > self.metrics.peak_memory_usage:
            self.metrics.peak_memory_usage = current_memory

        # 计算内存节省
        if self.metrics.total_inferences == 1:
            self.metrics.optimized_memory = current_memory
            self.metrics.memory_savings = (
                (self.metrics.baseline_memory - self.metrics.optimized_memory)
                / self.metrics.baseline_memory * 100
            )

    def _get_memory_usage(self) -> float:
        """获取内存使用量 (GB)"""
        if self.device.type == "cuda":
            return torch.cuda.memory_allocated() / 1024**3
        else:
            process = psutil.Process()
            return process.memory_info().rss / 1024**3

    def train_step(self,
                   model: nn.Module,
                   inputs: torch.Tensor,
                   targets: torch.Tensor,
                   optimizer: torch.optim.Optimizer,
                   criterion: nn.Module,
                   clip_grad_norm: Optional[float] = None) -> dict[str, float]:
        """执行混合精度训练步骤"""
        if not self.scaler:
            # 非AMP训练
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()

            if clip_grad_norm or self.config.gradient_clipping:
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    self.config.max_grad_norm
                )

            optimizer.step()
            return {"loss": loss.item()}

        # AMP训练
        optimizer.zero_grad()

        with self.get_autocast_context():
            outputs = model(inputs)
            loss = criterion(outputs, targets)

        # 缩放损失
        scaled_loss = self.scaler.scale(loss)
        scaled_loss.backward()

        # 梯度裁剪
        if clip_grad_norm or self.config.gradient_clipping:
            self.scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                self.config.max_grad_norm
            )

        # 优化器步骤
        self.scaler.step(optimizer)
        self.scaler.update()

        return {"loss": loss.item(), "scaled_loss": scaled_loss.item()}

    def benchmark_model(self,
                       model: nn.Module,
                       sample_input: torch.Tensor,
                       num_runs: int = 100) -> dict[str, float]:
        """基准测试模型性能"""
        self._log(f"开始基准测试 ({num_runs}次运行)...")

        # FP32基准
        fp32_times = []
        model.eval()

        with torch.no_grad():
            for _ in range(num_runs):
                start_time = time.time()
                _ = model(sample_input.float())
                fp32_times.append(time.time() - start_time)

        # 混合精度测试
        amp_times = []
        optimized_model = self.optimize_model(model)

        with torch.no_grad():
            for _ in range(num_runs):
                start_time = time.time()
                _ = self.inference(optimized_model, sample_input)
                amp_times.append(time.time() - start_time)

        # 计算性能指标
        avg_fp32_time = sum(fp32_times) / len(fp32_times)
        avg_amp_time = sum(amp_times) / len(amp_times)
        speedup = avg_fp32_time / avg_amp_time

        self.metrics.amp_speedup = speedup

        results = {
            "fp32_avg_time": avg_fp32_time,
            "amp_avg_time": avg_amp_time,
            "speedup": speedup,
            "fp32_throughput": 1.0 / avg_fp32_time,
            "amp_throughput": 1.0 / avg_amp_time
        }

        self._log(f"基准测试完成 - 加速比: {speedup:.2f}x")
        return results

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        return {
            "config": {
                "precision_mode": self.precision_mode.value,
                "device": str(self.device),
                "amp_enabled": self.config.enable_amp,
                "use_bf16": self.config.use_bf16
            },
            "metrics": {
                "total_inferences": self.metrics.total_inferences,
                "avg_inference_time": self.metrics.avg_inference_time,
                "peak_memory_gb": self.metrics.peak_memory_usage,
                "amp_speedup": self.metrics.amp_speedup,
                "overflow_count": self.metrics.overflow_count,
                "fallback_count": self.metrics.fallback_count
            },
            "precision_stats": {
                "fp32_inferences": self.metrics.fp32_inferences,
                "fp16_inferences": self.metrics.fp16_inferences,
                "mixed_inferences": self.metrics.mixed_inferences
            },
            "memory_stats": {
                "baseline_gb": self.metrics.baseline_memory,
                "optimized_gb": self.metrics.optimized_memory,
                "savings_percent": self.metrics.memory_savings
            }
        }

    def reset_metrics(self):
        """重置性能指标"""
        self.metrics = PerformanceMetrics()
        self._log("性能指标已重置")

    def cleanup(self):
        """清理资源"""
        self._log("清理混合精度管理器资源...")

        if self.device.type == "cuda":
            torch.cuda.empty_cache()

        gc.collect()
        self._log("资源清理完成")

# 便捷函数
def create_mixed_precision_manager(precision_mode: str = "auto",
                                  device: str = "auto",
                                  enable_amp: bool = True) -> MixedPrecisionManager:
    """创建混合精度管理器"""
    config = MixedPrecisionConfig(
        precision_mode=PrecisionMode(precision_mode),
        device_type=DeviceType(device),
        enable_amp=enable_amp
    )
    return MixedPrecisionManager(config)

def benchmark_model_with_amp(model: nn.Module,
                           sample_input: torch.Tensor,
                           num_runs: int = 100) -> dict[str, float]:
    """便捷的模型基准测试函数"""
    manager = MixedPrecisionManager()
    return manager.benchmark_model(model, sample_input, num_runs)

def main():
    """主程序 - 演示混合精度管理器"""
    print("🔥 混合精度推理管理器演示")
    print("=" * 50)

    # 创建管理器
    config = MixedPrecisionConfig(
        precision_mode=PrecisionMode.AUTO,
        enable_profiling=True,
        enable_amp=True
    )

    manager = MixedPrecisionManager(config)

    # 创建测试模型
    model = nn.Sequential(
        nn.Linear(512, 256),
        nn.ReLU(),
        nn.Linear(256, 128),
        nn.ReLU(),
        nn.Linear(128, 10)
    )

    sample_input = torch.randn(32, 512)

    # 基准测试
    results = manager.benchmark_model(model, sample_input, num_runs=50)

    print("\n📊 性能测试结果:")
    print(f"FP32平均时间: {results['fp32_avg_time']:.4f}s")
    print(f"AMP平均时间: {results['amp_avg_time']:.4f}s")
    print(f"加速比: {results['speedup']:.2f}x")

    # 性能报告
    report = manager.get_performance_report()
    print(f"\n🎯 设备: {report['config']['device']}")
    print(f"🎯 精度模式: {report['config']['precision_mode']}")
    print(f"🎯 峰值内存: {report['metrics']['peak_memory_gb']:.2f}GB")

    # 清理
    manager.cleanup()

if __name__ == "__main__":
    main()
