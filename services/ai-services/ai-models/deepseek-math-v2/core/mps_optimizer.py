"""
DeepSeek Math V2 GPU优化器 - Apple Silicon MPS优化
利用Apple M4 Pro的Metal Performance Shaders加速AI推理
"""

import asyncio
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
import platform
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class InferenceRequest:
    """推理请求对象"""

    request_id: str
    input_data: torch.Tensor
    priority: int = 0
    timestamp: float = 0.0


@dataclass
class InferenceResult:
    """推理结果对象"""

    request_id: str
    output_data: np.ndarray
    inference_time: float
    device_used: str


class MPSDeviceManager:
    """MPS设备管理器"""

    def __init__(self):
        self.device = self._detect_device()
        self.device_info = self._get_device_info()

    def _detect_device(self) -> torch.device:
        """检测最优计算设备"""
        system = platform.system()

        if system == 'Darwin' and torch.backends.mps.is_available():
            device = torch.device('mps')
            logger.info('🍎 检测到Apple Silicon GPU，使用MPS加速')
        elif torch.cuda.is_available():
            device = torch.device('cuda')
            logger.info(f"🚀 检测到NVIDIA GPU，使用CUDA加速: {torch.cuda.get_device_name()}")
        else:
            device = torch.device('cpu')
            logger.info('💻 使用CPU进行推理')

        return device

    def _get_device_info(self) -> Dict[str, Any]:
        """获取设备详细信息"""
        info = {
            'device_type': str(self.device),
            'platform': platform.system(),
            'architecture': platform.machine(),
        }

        if self.device.type == 'mps':
            info.update(
                {
                    'mps_available': torch.backends.mps.is_available(),
                    'metal_version': '4'
                    if platform.mac_ver()[0].startswith(('14', '15', '16'))
                    else '3',
                }
            )
        elif self.device.type == 'cuda':
            info.update(
                {
                    'cuda_available': torch.cuda.is_available(),
                    'gpu_count': torch.cuda.device_count(),
                    'gpu_name': torch.cuda.get_device_name(0),
                    'gpu_memory': torch.cuda.get_device_properties(0).total_memory,
                }
            )

        return info

    def get_optimal_batch_size(self, model_size_mb: float) -> int:
        """根据模型大小和设备内存计算最优批量大小"""
        if self.device.type == 'mps':
            # Apple Silicon统一内存架构，可以分配较大批量
            available_memory_gb = 8  # 保守估计
            model_memory_gb = model_size_mb / 1024
            optimal_batch = int((available_memory_gb * 0.7) / model_memory_gb)
            return min(max(optimal_batch, 1), 64)
        elif self.device.type == 'cuda':
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (
                1024**3
            )
            model_memory_gb = model_size_mb / 1024
            optimal_batch = int((gpu_memory_gb * 0.8) / model_memory_gb)
            return min(max(optimal_batch, 1), 128)
        else:
            return 8  # CPU批量大小


class MPSOptimizedModel:
    """MPS优化的模型包装器"""

    def __init__(self, base_model: nn.Module, device_manager: MPSDeviceManager):
        self.base_model = base_model
        self.device_manager = device_manager
        self.model = self._prepare_model()
        self.performance_stats = {
            'total_inferences': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'device_usage': {},
        }

    def _prepare_model(self) -> nn.Module:
        """准备模型以进行优化推理"""
        model = self.base_model.to(self.device_manager.device)
        model.eval()

        # 编译模型以提高性能 (PyTorch 2.0+)
        if hasattr(torch, 'compile') and self.device_manager.device.type != 'cpu':
            try:
                model = torch.compile(model, mode='max-autotune')
                logger.info('✅ 模型编译成功，启用最大优化')
            except Exception as e:
                logger.warning(f"⚠️ 模型编译失败: {e}")

        return model

    async def infer(self, input_data: torch.Tensor) -> InferenceResult:
        """执行单个推理"""
        request_id = f"req_{int(time.time() * 1000000)}"
        start_time = time.time()

        try:
            # 移动数据到设备
            if self.device_manager.device.type == 'mps':
                input_data = input_data.to(
                    self.device_manager.device, dtype=torch.float16
                )
            else:
                input_data = input_data.to(self.device_manager.device)

            # 执行推理
            with torch.no_grad():
                if self.device_manager.device.type == 'mps':
                    with torch.autocast('mps', dtype=torch.float16):
                        output = self.model(input_data)
                elif self.device_manager.device.type == 'cuda':
                    with torch.autocast('cuda', dtype=torch.float16):
                        output = self.model(input_data)
                else:
                    output = self.model(input_data)

            # 移回CPU并转换为numpy
            output_np = output.cpu().numpy()
            inference_time = time.time() - start_time

            # 更新性能统计
            self._update_stats(inference_time, str(self.device_manager.device))

            return InferenceResult(
                request_id=request_id,
                output_data=output_np,
                inference_time=inference_time,
                device_used=str(self.device_manager.device),
            )

        except Exception as e:
            logger.error(f"推理失败: {e}")
            raise

    def _update_stats(self, inference_time: float, device: str) -> Any:
        """更新性能统计"""
        self.performance_stats['total_inferences'] += 1
        self.performance_stats['total_time'] += inference_time
        self.performance_stats['avg_time'] = (
            self.performance_stats['total_time']
            / self.performance_stats['total_inferences']
        )

        if device not in self.performance_stats['device_usage']:
            self.performance_stats['device_usage'][device] = 0
        self.performance_stats['device_usage'][device] += 1


class BatchProcessor:
    """批量处理器"""

    def __init__(self, mps_model: MPSOptimizedModel, max_batch_size: int = 32):
        self.mps_model = mps_model
        self.max_batch_size = max_batch_size
        self.request_queue = asyncio.Queue()
        self.is_processing = False
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def add_request(self, request: InferenceRequest) -> InferenceResult:
        """添加推理请求到队列"""
        await self.request_queue.put(request)

        # 如果没有正在处理，启动批量处理
        if not self.is_processing:
            asyncio.create_task(self._process_batch())

        # 等待结果
        return await self._wait_for_result(request.request_id)

    async def _process_batch(self):
        """处理批量请求"""
        self.is_processing = True

        while not self.request_queue.empty():
            # 收集批量请求
            batch_requests = []
            while (
                len(batch_requests) < self.max_batch_size
                and not self.request_queue.empty()
            ):
                request = await self.request_queue.get()
                batch_requests.append(request)

            if batch_requests:
                await self._process_batch_requests(batch_requests)

        self.is_processing = False

    async def _process_batch_requests(self, requests: List[InferenceRequest]):
        """处理一批请求"""
        try:
            # 准备批量输入
            batch_inputs = torch.stack([req.input_data for req in requests])

            # 执行批量推理
            batch_results = await self._batch_infer(batch_inputs)

            # 分发结果
            for i, request in enumerate(requests):
                result = InferenceResult(
                    request_id=request.request_id,
                    output_data=batch_results[i],
                    inference_time=0.0,  # 批量处理时间单独计算
                    device_used=str(self.mps_model.device_manager.device),
                )
                # 这里应该将结果存储到某个地方供等待的请求获取

        except Exception as e:
            logger.error(f"批量处理失败: {e}")

    async def _batch_infer(self, batch_inputs: torch.Tensor) -> List[np.ndarray]:
        """执行批量推理"""
        start_time = time.time()

        device = self.mps_model.device_manager.device

        # 移动数据到设备
        if device.type == 'mps':
            batch_inputs = batch_inputs.to(device, dtype=torch.float16)
        else:
            batch_inputs = batch_inputs.to(device)

        # 执行批量推理
        with torch.no_grad():
            if device.type == 'mps':
                with torch.autocast('mps', dtype=torch.float16):
                    batch_outputs = self.mps_model.model(batch_inputs)
            elif device.type == 'cuda':
                with torch.autocast('cuda', dtype=torch.float16):
                    batch_outputs = self.mps_model.model(batch_inputs)
            else:
                batch_outputs = self.mps_model.model(batch_inputs)

        # 移回CPU并转换为numpy列表
        batch_results = batch_outputs.cpu().numpy()
        return [batch_results[i] for i in range(batch_results.shape[0])]

    async def _wait_for_result(self, request_id: str) -> InferenceResult:
        """等待特定请求的结果"""
        # 简化实现，实际应该有更复杂的结果匹配机制
        await asyncio.sleep(0.01)  # 模拟等待
        # 这里应该从结果缓存中获取对应的结果
        return InferenceResult(
            request_id=request_id,
            output_data=np.array([0.0]),  # 占位符
            inference_time=0.01,
            device_used=str(self.mps_model.device_manager.device),
        )


class GPUAccelerationProfiler:
    """GPU加速性能分析器"""

    def __init__(self):
        self.metrics = {
            'inference_times': [],
            'throughput_history': [],
            'device_utilization': {},
            'memory_usage': [],
        }

    def profile_inference(self, inference_func) -> None:
        """推理性能分析装饰器"""

        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await inference_func(*args, **kwargs)
            end_time = time.time()

            inference_time = end_time - start_time
            self.metrics['inference_times'].append(inference_time)

            logger.info(f"⚡ 推理时间: {inference_time*1000:.2f}ms")
            return result

        return wrapper

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self.metrics['inference_times']:
            return {'status': 'no_data'}

        inference_times = self.metrics['inference_times']

        return {
            'total_inferences': len(inference_times),
            'avg_inference_time_ms': np.mean(inference_times) * 1000,
            'p50_inference_time_ms': np.percentile(inference_times, 50) * 1000,
            'p95_inference_time_ms': np.percentile(inference_times, 95) * 1000,
            'p99_inference_time_ms': np.percentile(inference_times, 99) * 1000,
            'throughput_qps': len(inference_times) / sum(inference_times)
            if sum(inference_times) > 0
            else 0,
            'performance_score': self._calculate_performance_score(),
        }

    def _calculate_performance_score(self) -> float:
        """计算性能得分 (0-100)"""
        if not self.metrics['inference_times']:
            return 0.0

        avg_time = np.mean(self.metrics['inference_times'])
        # 假设10ms为满分基准
        score = max(0, min(100, 100 * (0.01 / avg_time)))
        return score


# 使用示例和测试函数
async def test_mps_optimization():
    """测试MPS优化效果"""
    logger.info('🚀 开始MPS优化测试')

    # 创建简单的测试模型
    class TestModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(768, 256)
            self.dropout = nn.Dropout(0.1)
            self.output = nn.Linear(256, 1)

        def forward(self, x) -> None:
            x = torch.relu(self.linear(x))
            x = self.dropout(x)
            return self.output(x)

    # 初始化组件
    device_manager = MPSDeviceManager()
    base_model = TestModel()
    mps_model = MPSOptimizedModel(base_model, device_manager)
    batch_processor = BatchProcessor(mps_model)
    profiler = GPUAccelerationProfiler()

    logger.info(f"📱 设备信息: {device_manager.device_info}")

    # 性能测试
    test_input = torch.randn(1, 768)

    # 单次推理测试
    result = await mps_model.infer(test_input)
    logger.info(f"✅ 单次推理完成: {result.inference_time*1000:.2f}ms")

    # 批量推理测试
    batch_size = device_manager.get_optimal_batch_size(10)  # 假设模型10MB
    logger.info(f"📊 最优批量大小: {batch_size}")

    # 生成性能报告
    report = profiler.get_performance_report()
    logger.info(f"📈 性能报告: {report}")

    return report


if __name__ == '__main__':
    # 运行测试
    asyncio.run(test_mps_optimization())
