"""
多模态理解模块 - Multimodal Understanding Module

提供图片OCR、文档解析、多模态融合理解等功能
"""

from core.multimodal.multimodal_integration import (
    DocumentParseResult,
    ImageFormat,
    # 数据类
    MediaContent,
    # 枚举
    MediaType,
    MockMultimodalProcessor,
    MultimodalIntegrator,
    # 核心类
    MultimodalProcessor,
    MultimodalUnderstanding,
    OCRResult,
    batch_process_files,
    get_multimodal_integrator,
    # 便捷函数
    get_multimodal_processor,
    get_supported_formats,
    process_file,
    understand_content,
)
from core.multimodal.multimodal_real_client import (
    # 真实客户端
    RealMultimodalProcessor,
    create_multimodal_processor,
)

__all__ = [
    "DocumentParseResult",
    "ImageFormat",
    # 数据类
    "MediaContent",
    # 枚举
    "MediaType",
    "MockMultimodalProcessor",
    "MultimodalIntegrator",
    # 核心类
    "MultimodalProcessor",
    "MultimodalUnderstanding",
    "OCRResult",
    # 真实客户端
    "RealMultimodalProcessor",
    "batch_process_files",
    "create_multimodal_processor",
    "get_multimodal_integrator",
    # 便捷函数
    "get_multimodal_processor",
    "get_supported_formats",
    "process_file",
    "understand_content",
]
