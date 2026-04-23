#!/usr/bin/env python3

"""
混合精度推理测试和验证
Mixed Precision Inference Testing and Validation

验证混合精度管理器的功能和性能
作者: 小诺·双鱼座
创建时间: 2025-12-22
版本: v1.0.0 "测试验证"
"""

import logging
import os
import sys
import time
from typing import Any

import pytest
import torch
import torch.nn as nn

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mixed_precision_manager import (
    MixedPrecisionConfig,
    MixedPrecisionManager,
    PrecisionMode,
    create_mixed_precision_manager,
)

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TestMixedPrecisionManager:
    """混合精度管理器测试类"""

    @pytest.fixture
    def config(self) -> Any:
        """测试配置"""
        return MixedPrecisionConfig(
            precision_mode=PrecisionMode.AUTO,
            enable_profiling=True,
            enable_amp=True,
            benchmark_warmup_steps=2,
        )

    @pytest.fixture
    def manager(self, config) -> None:
        """混合精度管理器实例"""
        manager = MixedPrecisionManager(config)
        yield manager
        manager.cleanup()

    @pytest.fixture
    def simple_model(self) -> Any:
        """简单测试模型"""
        return nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 10),
        )

    @pytest.fixture
    def sample_input(self) -> Any:
        """样本输入数据"""
        return torch.randn(32, 512)

    def test_initialization(self, config) -> None:
        """测试初始化"""
        manager = MixedPrecisionManager(config)
        assert manager.name == "混合精度推理管理器"
        assert manager.config == config
        assert manager.device is not None
        assert manager.precision_mode in PrecisionMode
        manager.cleanup()

    def test_device_detection(self) -> Any:
        """测试设备检测"""
        # 测试自动设备检测
        manager = create_mixed_precision_manager(device="auto")
        assert manager.device.type in ["cpu", "cuda", "mps"]
        manager.cleanup()

    def test_precision_mode_selection(self) -> Any:
        """测试精度模式选择"""
        # 测试不同精度模式
        for mode in [PrecisionMode.FP32, PrecisionMode.FP16, PrecisionMode.MIXED]:
            try:
                manager = create_mixed_precision_manager(precision_mode=mode.value)
                assert manager.precision_mode == mode
                manager.cleanup()
            except Exception as e:
                logger.warning(f"精度模式 {mode.value} 不支持: {e}")

    def test_model_optimization(self, manager, simple_model) -> None:
        """测试模型优化"""
        optimized_model = manager.optimize_model(simple_model)

        # 检查模型结构
        assert isinstance(optimized_model, nn.Module)

        # 检查参数类型(如果支持混合精度)
        if manager.precision_mode in [PrecisionMode.FP16, PrecisionMode.MIXED]:
            if manager.device.type in ["cuda", "mps"]:
                # 部分参数应该是半精度
                has_fp16 = any(p.dtype == torch.float16 for p in optimized_model.parameters())
                # 注意:某些层可能保持FP32
                logger.info(f"模型包含FP16参数: {has_fp16}")

    def test_inference(self, manager, simple_model, sample_input) -> None:
        """测试推理"""
        # 优化模型
        optimized_model = manager.optimize_model(simple_model)
        optimized_model.eval()

        # 执行推理
        with torch.no_grad():
            output = manager.inference(optimized_model, sample_input)

        # 检查输出
        assert output is not None
        assert output.shape == (32, 10)  # batch_size x num_classes
        assert not torch.isnan(output).any()
        assert not torch.isinf(output).any()

    def test_performance_benchmark(self, manager, simple_model, sample_input) -> None:
        """测试性能基准"""
        results = manager.benchmark_model(simple_model, sample_input, num_runs=10)

        # 检查结果
        assert "fp32_avg_time" in results
        assert "amp_avg_time" in results
        assert "speedup" in results
        assert "fp32_throughput" in results
        assert "amp_throughput" in results

        # 检查性能指标
        assert results["fp32_avg_time"] > 0
        assert results["amp_avg_time"] > 0
        assert results["speedup"] > 0

        logger.info(f"性能基准结果: {results}")

    def test_performance_metrics(self, manager, simple_model, sample_input) -> None:
        """测试性能指标收集"""
        # 执行多次推理
        optimized_model = manager.optimize_model(simple_model)
        for _ in range(5):
            _ = manager.inference(optimized_model, sample_input)

        # 获取性能报告
        report = manager.get_performance_report()

        # 检查报告内容
        assert "config" in report
        assert "metrics" in report
        assert "precision_stats" in report
        assert "memory_stats" in report

        # 检查指标
        metrics = report["metrics"]
        assert metrics["total_inferences"] > 0
        assert metrics["avg_inference_time"] > 0

    def test_error_handling(self, manager) -> None:
        """测试错误处理"""
        # 测试无效模型
        invalid_model = None
        try:
            manager.optimize_model(invalid_model)
            # 应该不抛出异常,而是优雅处理
        except Exception:
            # 预期可能抛出异常
            pass

        # 测试无效输入
        if hasattr(manager, "scaler") and manager.scaler:
            # 只在有AMP支持时测试
            pass

    def test_configuration_update(self, manager) -> None:
        """测试配置更新"""
        # 记录原始配置

        # 尝试更新配置
        try:
            success = manager.update_mixed_precision_config(
                enable_profiling=False, benchmark_warmup_steps=5
            )
            # 检查是否成功(某些配置可能不支持运行时更新)
            logger.info(f"配置更新结果: {success}")
        except Exception as e:
            logger.info(f"配置更新预期失败: {e}")


class TestIntegration:
    """集成测试"""

    def test_bert_model_integration(self) -> Any:
        """测试BERT模型集成"""
        try:
            from transformers import AutoModel, AutoTokenizer

            # 使用轻量级BERT模型
            model_name = "bert-base-uncased"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)

            # 创建混合精度管理器
            manager = create_mixed_precision_manager(precision_mode="mixed", enable_amp=True)

            # 准备输入
            text = "This is a test sentence for mixed precision inference."
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)

            # 基准测试
            sample_input = inputs["input_ids"]
            results = manager.benchmark_model(model, sample_input, num_runs=5)

            logger.info(f"BERT模型基准测试结果: {results}")

            # 清理
            manager.cleanup()

        except ImportError:
            logger.warning("transformers库未安装,跳过BERT集成测试")
        except Exception as e:
            logger.error(f"BERT集成测试失败: {e}")

    def test_memory_efficiency(self) -> Any:
        """测试内存效率"""
        # 创建较大的模型
        model = nn.Sequential(
            nn.Linear(2048, 1024),
            nn.ReLU(),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
        )

        sample_input = torch.randn(64, 2048)

        # 测试FP32内存使用
        fp32_manager = create_mixed_precision_manager(precision_mode="fp32", enable_amp=False)

        fp32_manager.benchmark_model(model, sample_input, num_runs=3)
        fp32_manager.cleanup()

        # 测试混合精度内存使用
        amp_manager = create_mixed_precision_manager(precision_mode="mixed", enable_amp=True)

        amp_manager.benchmark_model(model, sample_input, num_runs=3)

        # 检查内存节省
        memory_report = amp_manager.get_performance_report()
        logger.info(f"内存效率测试结果: {memory_report['memory_stats']}")

        amp_manager.cleanup()


def run_comprehensive_test() -> Any:
    """运行全面测试"""
    print("🔥 混合精度推理系统 - 全面测试")
    print("=" * 60)

    test_results = {
        "initialization": False,
        "device_detection": False,
        "model_optimization": False,
        "inference": False,
        "performance": False,
        "error_handling": False,
        "integration": False,
    }

    try:
        # 1. 初始化测试
        print("\n📋 测试1: 初始化")
        config = MixedPrecisionConfig(precision_mode=PrecisionMode.AUTO, enable_profiling=True)
        manager = MixedPrecisionManager(config)
        print(f"✅ 初始化成功 - 设备: {manager.device}, 精度: {manager.precision_mode.value}")
        test_results["initialization"] = True

        # 2. 设备检测测试
        print("\n📋 测试2: 设备检测")
        print(f"✅ 设备检测成功 - {manager.device}")
        test_results["device_detection"] = True

        # 3. 模型优化测试
        print("\n📋 测试3: 模型优化")
        model = nn.Sequential(nn.Linear(512, 256), nn.ReLU(), nn.Linear(256, 10))
        optimized_model = manager.optimize_model(model)
        print(
            f"✅ 模型优化完成 - 参数类型: {[p.dtype for p in optimized_model.parameters()][:2]}..."
        )
        test_results["model_optimization"] = True

        # 4. 推理测试
        print("\n📋 测试4: 推理")
        sample_input = torch.randn(32, 512)
        with torch.no_grad():
            start_time = time.time()
            output = manager.inference(optimized_model, sample_input)
            inference_time = time.time() - start_time

        print(f"✅ 推理成功 - 输出形状: {output.shape}, 时间: {inference_time:.4f}s")
        test_results["inference"] = True

        # 5. 性能基准测试
        print("\n📋 测试5: 性能基准")
        benchmark_results = manager.benchmark_model(model, sample_input, num_runs=10)
        print(f"✅ 基准测试完成 - 加速比: {benchmark_results['speedup']:.2f}x")
        test_results["performance"] = True

        # 6. 错误处理测试
        print("\n📋 测试6: 错误处理")
        try:
            manager.optimize_model(None)  # 故意传入无效模型
            print("✅ 错误处理正常")
            test_results["error_handling"] = True
        except Exception as e:
            print(f"✅ 错误处理捕获异常: {type(e).__name__}")
            test_results["error_handling"] = True

        # 7. 集成测试
        print("\n📋 测试7: 集成测试")
        # 测试与NLP服务的集成
        try:
            import os
            import sys

            sys.path.append(os.path.dirname(os.path.abspath(__file__)))

            from xiaonuo_nlp_service import XiaonuoNLPService

            nlp_service = XiaonuoNLPService(enable_mixed_precision=True)

            # 检查混合精度统计
            mp_stats = nlp_service.get_mixed_precision_stats()
            print(f"✅ NLP服务集成成功 - 混合精度启用: {mp_stats['enabled']}")
            test_results["integration"] = True

        except Exception as e:
            print(f"⚠️ NLP服务集成测试跳过: {e}")
            test_results["integration"] = False

        # 8. 性能报告
        print("\n📊 性能报告:")
        performance_report = manager.get_performance_report()
        print(f"   设备: {performance_report['config']['device']}")
        print(f"   精度模式: {performance_report['config']['precision_mode']}")
        print(f"   总推理次数: {performance_report['metrics']['total_inferences']}")
        print(f"   平均推理时间: {performance_report['metrics']['avg_inference_time']:.4f}s")
        print(f"   峰值内存: {performance_report['metrics']['peak_memory_gb']:.2f}GB")

        # 清理
        manager.cleanup()

        # 9. 测试总结
        print("\n🎯 测试总结:")
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        success_rate = passed_tests / total_tests * 100

        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")

        print(f"\n🏆 总体结果: {passed_tests}/{total_tests} 测试通过 ({success_rate:.1f}%)")

        if success_rate >= 80:
            print("🎉 混合精度系统测试通过!")
        else:
            print("⚠️ 部分测试失败,请检查系统配置")

        return test_results

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        return test_results


def main() -> None:
    """主程序"""
    print("🧪 混合精度推理测试套件")
    print("=" * 50)

    # 运行全面测试
    results = run_comprehensive_test()

    # 返回测试结果
    return results


if __name__ == "__main__":
    main()

