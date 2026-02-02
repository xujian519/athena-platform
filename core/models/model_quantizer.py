#!/usr/bin/env python3
"""
M4模型量化器 - 阶段4优化
实现模型INT8量化,减少模型大小75%,保持精度损失<1%

作者: 小诺·双鱼公主 🌊✨
创建时间: 2025-12-27
版本: v1.0.0
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.quantization as quant

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class QuantizationConfig:
    """量化配置"""

    # 量化精度
    precision: str = "int8"  # 'int8', 'mixed', 'dynamic'

    # INT8量化配置
    enable_static_quantization: bool = True
    enable_dynamic_quantization: bool = True
    enable_qat: bool = False  # 量化感知训练(需要训练数据)

    # 混合精度配置
    mixed_precision_layers: list = None  # 保持FP32的层名称列表

    # 验证配置
    verify_accuracy: bool = True
    accuracy_threshold: float = 0.01  # 精度损失阈值1%

    # 性能优化
    enable_fusion: bool = True  # 算子融合
    backend: str = "default"  # 量化后端


class M4ModelQuantizer:
    """Apple M4 Pro模型量化器"""

    def __init__(self, config: QuantizationConfig = None):
        self.config = config or QuantizationConfig()
        self.device = self._select_device()

        logger.info("⚡ M4模型量化器初始化完成")
        logger.info(f"🎯 量化精度: {self.config.precision}")

    def _select_device(self) -> torch.device:
        """选择最优设备"""
        if torch.backends.mps.is_available():
            return torch.device("mps")
        elif torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")

    def quantize_model(
        self, model: nn.Module, calibration_data: torch.utils.data.DataLoader] | None = None
    ) -> nn.Module:
        """
        量化模型

        Args:
            model: 待量化的模型
            calibration_data: 校准数据(静态量化需要)

        Returns:
            量化后的模型
        """
        logger.info("🔄 开始量化模型...")
        start_time = time.time()

        original_size = self._get_model_size_mb(model)
        logger.info(f"📦 原始模型大小: {original_size:.2f}MB")

        # 根据配置选择量化方式
        if self.config.precision == "int8":
            quantized_model = self._quantize_int8(model, calibration_data)
        elif self.config.precision == "mixed":
            quantized_model = self._quantize_mixed_precision(model)
        elif self.config.precision == "dynamic":
            quantized_model = self._quantize_dynamic(model)
        else:
            logger.warning(f"⚠️ 未知量化精度: {self.config.precision},使用动态量化")
            quantized_model = self._quantize_dynamic(model)

        quantized_size = self._get_model_size_mb(quantized_model)
        compression_ratio = original_size / quantized_size

        quantization_time = time.time() - start_time

        logger.info("✅ 量化完成!")
        logger.info(f"📦 量化后大小: {quantized_size:.2f}MB")
        logger.info(f"📊 压缩比: {compression_ratio:.2f}x")
        logger.info(f"⏱️ 量化耗时: {quantization_time:.2f}秒")

        return quantized_model

    def _quantize_int8(
        self, model: nn.Module, calibration_data: torch.utils.data.DataLoader]
    ) -> nn.Module:
        """INT8静态量化"""
        logger.info("🎯 执行INT8静态量化...")

        # 设置为评估模式
        model.eval()

        # 算子融合(提升性能)
        if self.config.enable_fusion:
            model = self._fuse_modules(model)

        # 静态量化需要校准数据
        if self.config.enable_static_quantization and calibration_data is not None:
            logger.info("📊 使用校准数据进行静态量化...")

            # 配置量化
            model.qconfig = quant.get_default_qconfig(self.config.backend)
            quantized_model = quant.prepare(model, inplace=True)

            # 校准
            self._calibrate_model(quantized_model, calibration_data)

            # 转换为量化模型
            quantized_model = quant.convert(quantized_model, inplace=True)

        # 如果没有校准数据,使用动态量化
        elif self.config.enable_dynamic_quantization:
            logger.info("⚠️ 无校准数据,使用动态量化...")
            quantized_model = self._quantize_dynamic(model)

        else:
            logger.warning("⚠️ 量化失败,返回原始模型")
            return model

        return quantized_model.to(self.device)

    def _quantize_dynamic(self, model: nn.Module) -> nn.Module:
        """动态量化"""
        logger.info("⚡ 执行动态量化...")

        # 动态量化配置
        dynamo_config = {
            nn.Linear: torch.quantization.default_dynamic_qconfig,
            nn.LSTM: torch.quantization.default_dynamic_qconfig,
            nn.GRU: torch.quantization.default_dynamic_qconfig,
        }

        # 应用动态量化
        quantized_model = torch.quantization.quantize_dynamic(
            model, dynamo_config, dtype=torch.qint8
        )

        return quantized_model.to(self.device)

    def _quantize_mixed_precision(self, model: nn.Module) -> nn.Module:
        """混合精度量化"""
        logger.info("🎨 执行混合精度量化...")

        model = model.to(self.device)

        # 转换为FP16(除了指定层)
        for name, module in model.named_modules():
            if self.config.mixed_precision_layers and name in self.config.mixed_precision_layers:
                # 保持FP32
                logger.info(f"🔒 保持FP32: {name}")
                continue

            if isinstance(module, (nn.Linear, nn.Conv1d, nn.Conv2d)):
                # 转换为FP16
                module.half()

        logger.info("✅ 混合精度转换完成")
        return model

    def _fuse_modules(self, model: nn.Module) -> nn.Module:
        """融合模块以提升性能"""
        logger.info("🔗 融合模块...")

        # 定义融合模式
        fusion_patterns = [
            # Conv + BN + ReLU
            (nn.Conv2d, nn.BatchNorm2d, nn.ReLU),
            (nn.Conv2d, nn.BatchNorm2d),
            # Linear + ReLU
            (nn.Linear, nn.ReLU),
            # LSTM
            (nn.LSTM, nn.ReLU),
        ]

        fused_model = model
        for pattern in fusion_patterns:
            try:
                fused_model = torch.quantization.fuse_modules(
                    fused_model, list(pattern), inplace=True
                )
            except Exception:
                # 跳过不支持的融合
                pass

        logger.info("✅ 模块融合完成")
        return fused_model

    def _calibrate_model(self, model: nn.Module, calibration_data: torch.utils.data.DataLoader):
        """校准量化模型"""
        logger.info("📊 校准模型...")

        model.eval()
        with torch.no_grad():
            for batch_idx, (inputs, *_) in enumerate(calibration_data):
                if isinstance(inputs, (tuple, list)):
                    inputs = inputs[0]

                # 移动到设备
                if isinstance(inputs, torch.Tensor):
                    inputs = inputs.to(self.device)
                elif isinstance(inputs, dict):
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # 前向传播
                try:
                    _ = model(inputs)
                except Exception as e:
                    logger.warning(f"⚠️ 校准批次{batch_idx}失败: {e}")
                    continue

                # 限制校准批次数
                if batch_idx >= 10:
                    break

        logger.info("✅ 校准完成")

    def verify_quantization(
        self,
        original_model: nn.Module,
        quantized_model: nn.Module,
        test_data: torch.utils.data.DataLoader,
        metric_fn: callable | None = None,
    ) -> dict[str, Any]:
        """
        验证量化模型的精度

        Args:
            original_model: 原始模型
            quantized_model: 量化模型
            test_data: 测试数据
            metric_fn: 评估函数(可选)

        Returns:
            验证结果
        """
        logger.info("🔍 验证量化精度...")

        original_model.eval()
        quantized_model.eval()

        original_score = self._evaluate_model(original_model, test_data, metric_fn)
        quantized_score = self._evaluate_model(quantized_model, test_data, metric_fn)

        accuracy_loss = abs(original_score - quantized_score)
        accuracy_loss_percent = (accuracy_loss / original_score) * 100

        logger.info(f"📊 原始模型得分: {original_score:.4f}")
        logger.info(f"📊 量化模型得分: {quantized_score:.4f}")
        logger.info(f"📊 精度损失: {accuracy_loss_percent:.2f}%")

        # 检查是否在可接受范围内
        passed = accuracy_loss_percent <= (self.config.accuracy_threshold * 100)

        result = {
            "original_score": original_score,
            "quantized_score": quantized_score,
            "accuracy_loss": accuracy_loss,
            "accuracy_loss_percent": accuracy_loss_percent,
            "passed": passed,
            "within_threshold": passed,
        }

        if passed:
            logger.info(
                f"✅ 量化验证通过(精度损失{accuracy_loss_percent:.2f}% < {self.config.accuracy_threshold*100}%)"
            )
        else:
            logger.warning(
                f"⚠️ 量化验证失败(精度损失{accuracy_loss_percent:.2f}% > {self.config.accuracy_threshold*100}%)"
            )

        return result

    def _evaluate_model(
        self,
        model: nn.Module,
        test_data: torch.utils.data.DataLoader,
        metric_fn: callable | None = None,
    ) -> float:
        """评估模型性能"""
        model.eval()

        if metric_fn is not None:
            # 使用自定义评估函数
            return metric_fn(model, test_data)

        # 默认:计算准确率
        correct = 0
        total = 0

        with torch.no_grad():
            for batch in test_data:
                if isinstance(batch, (tuple, list)):
                    inputs, labels = batch[0], batch[1]
                else:
                    inputs = batch
                    labels = None

                # 移动到设备
                if isinstance(inputs, torch.Tensor):
                    inputs = inputs.to(self.device)
                elif isinstance(inputs, dict):
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}

                if labels is not None:
                    labels = labels.to(self.device)

                # 前向传播
                outputs = model(inputs)

                # 计算准确率
                if labels is not None:
                    if isinstance(outputs, torch.Tensor):
                        predictions = outputs.argmax(dim=-1)
                    else:
                        predictions = outputs[0].argmax(dim=-1)

                    correct += (predictions == labels).sum().item()
                    total += labels.size(0)

        return correct / total if total > 0 else 0.0

    def _get_model_size_mb(self, model: nn.Module) -> float:
        """获取模型大小(MB)"""
        param_size = 0
        buffer_size = 0

        for param in model.parameters():
            param_size += param.numel() * param.element_size()

        for buffer in model.buffers():
            buffer_size += buffer.numel() * buffer.element_size()

        total_size = param_size + buffer_size
        return total_size / (1024 * 1024)

    def save_quantized_model(self, model: nn.Module, save_path: str):
        """保存量化模型"""
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存模型
        torch.save(model.state_dict(), save_path)

        model_size_mb = save_path.stat().st_size / (1024 * 1024)
        logger.info(f"💾 模型已保存: {save_path} ({model_size_mb:.2f}MB)")

    def load_quantized_model(self, model_class: nn.Module, load_path: str) -> nn.Module:
        """加载量化模型"""
        model = model_class.to(self.device)
        state_dict = torch.load(load_path, map_location=self.device)
        model.load_state_dict(state_dict)

        logger.info(f"📂 模型已加载: {load_path}")
        return model


# 全局单例
_quantizer: M4ModelQuantizer | None = None


def get_model_quantizer() -> M4ModelQuantizer:
    """获取全局模型量化器实例"""
    global _quantizer
    if _quantizer is None:
        _quantizer = M4ModelQuantizer()
    return _quantizer


def quantize_model(
    model: nn.Module,
    precision: str = "int8",
    calibration_data: torch.utils.data.DataLoader | None = None,
) -> nn.Module:
    """便捷函数:量化模型"""
    quantizer = get_model_quantizer()
    quantizer.config.precision = precision
    return quantizer.quantize_model(model, calibration_data)


if __name__ == "__main__":
    # 测试模型量化器
    # setup_logging()  # 日志配置已移至模块导入

    # 创建测试模型
    class TestModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear1 = nn.Linear(768, 512)
            self.relu = nn.ReLU()
            self.linear2 = nn.Linear(512, 128)
            self.linear3 = nn.Linear(128, 10)

        def forward(self, x) -> None:
            x = self.linear1(x)
            x = self.relu(x)
            x = self.linear2(x)
            x = self.relu(x)
            x = self.linear3(x)
            return x

    print("=" * 60)
    print("🧪 测试M4模型量化器")
    print("=" * 60)

    model = TestModel()
    print(f"\n📦 原始模型: {sum(p.numel() for p in model.parameters())} 参数")

    quantizer = M4ModelQuantizer()

    # 测试动态量化
    print("\n📊 测试动态量化...")
    quantized_model = quantizer.quantize_model(model, precision="dynamic")

    # 性能对比
    import torch.utils.data as data

    class DummyDataset(data.Dataset):
        def __len__(self):
            return 100

        def __getitem__(self, idx):
            return torch.randn(768), torch.randint(0, 10, (1,)).item()

    test_dataset = DummyDataset()
    test_loader = data.DataLoader(test_dataset, batch_size=16)

    result = quantizer.verify_quantization(model, quantized_model, test_loader)

    print("\n✅ 量化结果:")
    print(f"  精度损失: {result['accuracy_loss_percent']:.2f}%")
    print(f"  验证通过: {'是' if result['passed'] else '否'}")
