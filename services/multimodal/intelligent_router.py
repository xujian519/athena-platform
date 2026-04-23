#!/usr/bin/env python3
"""
智能多模态处理路由器
Intelligent Multimodal Processing Router

根据场景自动选择最优处理方案（MCP vs 本地）
"""

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from ai.ai_processor import ProcessingType

# 导入本地处理器
from ai.audio_processor_enhanced import get_audio_processor


class ProcessingMethod(Enum):
    """处理方法"""
    MCP = "mcp"          # 使用MCP工具
    LOCAL = "local"      # 使用本地系统
    HYBRID = "hybrid"    # 混合模式

class ProcessingPriority(Enum):
    """处理优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class DataSensitivity(Enum):
    """数据敏感度"""
    PUBLIC = 1          # 公开数据
    INTERNAL = 2        # 内部数据
    CONFIDENTIAL = 3    # 机密数据
    SECRET = 4          # 绝密数据

@dataclass
class ProcessingRequest:
    """处理请求"""
    request_id: str
    file_path: str
    file_type: str
    priority: ProcessingPriority = ProcessingPriority.NORMAL
    sensitivity: DataSensitivity = DataSensitivity.PUBLIC
    require_high_quality: bool = False
    batch_size: int = 1
    deadline: datetime | None = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProcessingResult:
    """处理结果"""
    request_id: str
    method_used: ProcessingMethod
    success: bool
    result_data: dict[str, Any]
    processing_time: float
    cost: float
    quality_score: float
    error_message: str | None = None

class IntelligentRouter:
    """智能路由器"""

    def __init__(self):
        """初始化路由器"""
        self.mcp_available = True  # MCP工具是否可用
        self.local_available = True  # 本地系统是否可用
        self.processing_history: list[dict] = []

        # 成本配置
        self.cost_config = {
            'mcp_per_request': 0.05,  # 每次请求成本
            'local_per_hour': 0.5,   # 本地处理每小时成本
            'gpu_cost_per_hour': 1.0  # GPU使用成本
        }

        # 性能配置
        self.performance_config = {
            'mcp_avg_time': 5.0,      # MCP平均处理时间（秒）
            'local_avg_time': 3.0,    # 本地平均处理时间（秒）
            'network_delay': 1.0      # 网络延迟
        }

    def choose_optimal_method(self, request: ProcessingRequest) -> ProcessingMethod:
        """
        根据请求特征选择最优处理方法

        决策逻辑：
        1. 绝密数据 -> 本地
        2. 紧急任务 -> MCP
        3. 大批量 -> 本地
        4. 高质量要求 -> MCP
        5. 默认 -> MCP
        """

        # 规则1：数据敏感度决策
        if request.sensitivity in [DataSensitivity.CONFIDENTIAL, DataSensitivity.SECRET]:
            print("🔒 敏感数据，选择本地处理")
            return ProcessingMethod.LOCAL

        # 规则2：紧急程度决策
        if request.priority in [ProcessingPriority.HIGH, ProcessingPriority.URGENT]:
            print("⚡ 紧急任务，选择MCP处理")
            return ProcessingMethod.MCP

        # 规则3：批量大小决策
        if request.batch_size > 100:
            print(f"📦 大批量处理（{request.batch_size}个），选择本地系统")
            return ProcessingMethod.LOCAL

        # 规则4：质量要求决策
        if request.require_high_quality:
            print("🎯 高质量要求，选择MCP处理")
            return ProcessingMethod.MCP

        # 规则5：成本敏感决策
        estimated_mcp_cost = request.batch_size * self.cost_config['mcp_per_request']
        estimated_local_cost = (request.batch_size * self.performance_config['local_avg_time'] / 3600) * self.cost_config['local_per_hour']

        if estimated_mcp_cost > estimated_local_cost * 3:
            print(f"💰 成本敏感，选择本地系统（MCP: ${estimated_mcp_cost:.2f}, 本地: ${estimated_local_cost:.2f}）")
            return ProcessingMethod.LOCAL

        # 默认选择MCP
        print("🚀 使用MCP处理（默认高质量选择）")
        return ProcessingMethod.MCP

    async def process_request(self, request: ProcessingRequest) -> ProcessingResult:
        """处理请求"""
        start_time = time.time()

        # 选择处理方法
        method = self.choose_optimal_method(request)

        try:
            if method == ProcessingMethod.MCP:
                result = await self._process_with_mcp(request)
            elif method == ProcessingMethod.LOCAL:
                result = await self._process_with_local(request)
            else:  # HYBRID
                result = await self._process_with_hybrid(request)

            processing_time = time.time() - start_time

            # 记录处理历史
            self._log_processing(request, method, processing_time, result)

            return ProcessingResult(
                request_id=request.request_id,
                method_used=method,
                success=result.get('success', False),
                result_data=result,
                processing_time=processing_time,
                cost=self._calculate_cost(method, processing_time),
                quality_score=self._calculate_quality(result)
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                request_id=request.request_id,
                method_used=method,
                success=False,
                result_data={},
                processing_time=processing_time,
                cost=0.0,
                quality_score=0.0,
                error_message=str(e)
            )

    async def _process_with_mcp(self, request: ProcessingRequest) -> dict[str, Any]:
        """使用MCP工具处理"""
        print(f"📡 通过MCP处理: {request.file_path}")

        # 根据文件类型调用相应的MCP工具
        if request.file_type == "image":
            return await self._mcp_analyze_image(request)
        elif request.file_type == "audio":
            return await self._mcp_transcribe_audio(request)
        elif request.file_type == "document":
            return await self._mcp_parse_document(request)
        else:
            return {"success": False, "error": f"不支持的文件类型: {request.file_type}"}

    async def _process_with_local(self, request: ProcessingRequest) -> dict[str, Any]:
        """使用本地系统处理"""
        print(f"🏠 本地处理: {request.file_path}")

        # 根据文件类型调用相应的本地处理器
        if request.file_type == "image":
            return await self._local_analyze_image(request)
        elif request.file_type == "audio":
            return await self._local_transcribe_audio(request)
        elif request.file_type == "document":
            return await self._local_parse_document(request)
        else:
            return {"success": False, "error": f"不支持的文件类型: {request.file_type}"}

    async def _process_with_hybrid(self, request: ProcessingRequest) -> dict[str, Any]:
        """混合模式处理"""
        print(f"🔄 混合模式处理: {request.file_path}")

        # 先用本地快速处理，再用MCP进行深度分析
        local_result = await self._process_with_local(request)

        # 如果本地处理失败或质量不足，使用MCP
        if not local_result.get('success') or request.require_high_quality:
            mcp_result = await self._process_with_mcp(request)
            # 合并结果
            return {
                "success": True,
                "local_result": local_result,
                "mcp_result": mcp_result,
                "method": "hybrid"
            }

        return local_result

    async def _mcp_analyze_image(self, request: ProcessingRequest) -> dict[str, Any]:
        """MCP图像分析"""
        try:
            # 这里应该调用实际的MCP工具
            # 示例调用
            from mcp__zai_mcp_server import analyze_image

            result = await analyze_image(
                image_source=request.file_path,
                prompt="请详细分析这张图片的内容，包括文字、对象、场景等信息"
            )

            return {
                "success": True,
                "analysis": result,
                "method": "mcp_vision"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _mcp_transcribe_audio(self, request: ProcessingRequest) -> dict[str, Any]:
        """MCP音频转录"""
        # MCP可能不直接支持音频，可以先用本地转换，再发送
        local_result = await self._local_transcribe_audio(request)

        # 如果需要更高的质量，可以将文本发送给MCP进行优化
        if request.require_high_quality and local_result.get('success'):
            # 发送给MCP优化转录结果
            optimized_text = await self._optimize_transcription_with_mcp(
                local_result.get('text', '')
            )
            local_result['optimized_text'] = optimized_text
            local_result['method'] = 'local_plus_mcp'

        return local_result

    async def _local_transcribe_audio(self, request: ProcessingRequest) -> dict[str, Any]:
        """本地音频转录"""
        try:
            audio_processor = get_audio_processor()
            result = await audio_processor.transcribe_with_timestamps(
                request.file_path,
                "zh"
            )

            return {
                "success": result["success"],
                "text": result.get("text", ""),
                "segments": result.get("segments", []),
                "model": result.get("model", "whisper"),
                "method": "local_whisper"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _local_analyze_image(self, request: ProcessingRequest) -> dict[str, Any]:
        """本地图像分析"""
        try:
            from ai.ai_processor import AIProcessor
            processor = AIProcessor()
            await processor.start()

            task_id = await processor.submit_processing_task(
                file_id=request.request_id,
                file_path=request.file_path,
                processing_type=ProcessingType.IMAGE_ANALYSIS,
                options={'analyze_colors': True, 'analyze_quality': True}
            )

            # 等待处理完成
            await asyncio.sleep(3)

            result = await processor.get_processing_result(task_id)

            return {
                "success": True,
                "analysis": result.result if result else {},
                "task_id": task_id,
                "method": "local_ai_processor"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _local_parse_document(self, request: ProcessingRequest) -> dict[str, Any]:
        """本地文档解析"""
        try:
            from ai.ai_processor import AIProcessor
            processor = AIProcessor()
            await processor.start()

            task_id = await processor.submit_processing_task(
                file_id=request.request_id,
                file_path=request.file_path,
                processing_type=ProcessingType.DOCUMENT_PARSING,
                options={}
            )

            # 等待处理完成
            await asyncio.sleep(3)

            result = await processor.get_processing_result(task_id)

            return {
                "success": True,
                "parsed_content": result.result if result else {},
                "task_id": task_id,
                "method": "local_ai_processor"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _optimize_transcription_with_mcp(self, text: str) -> str:
        """使用MCP优化转录文本"""
        try:
            # 这里应该调用MCP的文本处理能力
            # 示例：优化转录文本的语法和表达
            optimized = text  # 实际应该调用MCP
            return optimized
        except (TimeoutError, asyncio.CancelledError, Exception):
            return text

    def _calculate_cost(self, method: ProcessingMethod, processing_time: float) -> float:
        """计算处理成本"""
        if method == ProcessingMethod.MCP:
            return self.cost_config['mcp_per_request']
        elif method == ProcessingMethod.LOCAL:
            return (processing_time / 3600) * self.cost_config['local_per_hour']
        else:  # HYBRID
            return self.cost_config['mcp_per_request'] + (processing_time / 3600) * self.cost_config['local_per_hour']

    def _calculate_quality(self, result: dict[str, Any]) -> float:
        """计算质量分数（0-1）"""
        if not result.get('success'):
            return 0.0

        method = result.get('method', '')
        if 'mcp' in method:
            return 0.95  # MCP高质量
        elif 'local' in method:
            return 0.85  # 本地中等质量
        else:
            return 0.75  # 其他

    def _log_processing(self, request: ProcessingRequest, method: ProcessingMethod,
                       processing_time: float, result: dict):
        """记录处理日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request.request_id,
            "file_type": request.file_type,
            "method": method.value,
            "processing_time": processing_time,
            "success": result.get('success', False),
            "priority": request.priority.value,
            "sensitivity": request.sensitivity.value,
            "batch_size": request.batch_size
        }

        self.processing_history.append(log_entry)

        # 保持历史记录在合理范围内
        if len(self.processing_history) > 1000:
            self.processing_history = self.processing_history[-1000:]

    def get_statistics(self) -> dict[str, Any]:
        """获取路由统计信息"""
        if not self.processing_history:
            return {"message": "暂无处理记录"}

        total = len(self.processing_history)
        mcp_count = sum(1 for h in self.processing_history if h['method'] == 'mcp')
        local_count = sum(1 for h in self.processing_history if h['method'] == 'local')
        success_count = sum(1 for h in self.processing_history if h['success'])

        avg_time = sum(h['processing_time'] for h in self.processing_history) / total

        return {
            "total_requests": total,
            "mcp_usage": mcp_count,
            "local_usage": local_count,
            "mcp_ratio": f"{(mcp_count/total*100):.1f}%",
            "local_ratio": f"{(local_count/total*100):.1f}%",
            "success_rate": f"{(success_count/total*100):.1f}%",
            "average_processing_time": f"{avg_time:.2f}s",
            "total_saved_costs": self._calculate_total_savings()
        }

    def _calculate_total_savings(self) -> float:
        """计算通过智能路由节省的成本"""
        all_mcp_cost = len(self.processing_history) * self.cost_config['mcp_per_request']
        actual_cost = 0

        for entry in self.processing_history:
            if entry['method'] == 'mcp':
                actual_cost += self.cost_config['mcp_per_request']
            else:
                actual_cost += (entry['processing_time'] / 3600) * self.cost_config['local_per_hour']

        return all_mcp_cost - actual_cost

# 全局路由器实例
_router = None

def get_intelligent_router() -> IntelligentRouter:
    """获取智能路由器实例"""
    global _router
    if _router is None:
        _router = IntelligentRouter()
    return _router

# 便捷函数
async def process_file_intelligently(
    file_path: str,
    file_type: str,
    priority: str = "normal",
    sensitivity: str = "public",
    high_quality: bool = False,
    batch_size: int = 1
) -> dict[str, Any]:
    """智能处理文件的便捷函数"""

    router = get_intelligent_router()

    request = ProcessingRequest(
        request_id=str(int(time.time() * 1000)),
        file_path=file_path,
        file_type=file_type,
        priority=ProcessingPriority[priority.upper()],
        sensitivity=DataSensitivity[sensitivity.upper()],
        require_high_quality=high_quality,
        batch_size=batch_size
    )

    result = await router.process_request(request)

    return {
        "success": result.success,
        "method_used": result.method_used.value,
        "processing_time": result.processing_time,
        "cost": result.cost,
        "quality_score": result.quality_score,
        "data": result.result_data,
        "error": result.error_message
    }

if __name__ == "__main__":
    # 测试代码
    async def test_router():
        router = get_intelligent_router()

        # 测试不同场景
        test_cases = [
            {
                "name": "紧急图片分析",
                "request": ProcessingRequest(
                    request_id="test1",
                    file_path="/test/image.jpg",
                    file_type="image",
                    priority=ProcessingPriority.URGENT
                )
            },
            {
                "name": "机密音频转录",
                "request": ProcessingRequest(
                    request_id="test2",
                    file_path="/test/secret.amr",
                    file_type="audio",
                    sensitivity=DataSensitivity.SECRET
                )
            },
            {
                "name": "大批量文档处理",
                "request": ProcessingRequest(
                    request_id="test3",
                    file_path="/test/batch.pdf",
                    file_type="document",
                    batch_size=500
                )
            },
            {
                "name": "高质量图片分析",
                "request": ProcessingRequest(
                    request_id="test4",
                    file_path="/test/high_res.jpg",
                    file_type="image",
                    require_high_quality=True
                )
            }
        ]

        for test in test_cases:
            print(f"\n测试场景: {test['name']}")
            method = router.choose_optimal_method(test['request'])
            print(f"推荐方法: {method.value}")

        # 显示统计
        print("\n" + "="*50)
        print("路由统计:")
        print(json.dumps(router.get_statistics(), indent=2, ensure_ascii=False))

    asyncio.run(test_router())
