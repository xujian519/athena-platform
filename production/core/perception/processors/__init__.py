"""
感知模块处理器包
包含OCR、图像处理、文件处理等
"""

# 导入实际存在的处理器
from __future__ import annotations
from .audio_processor import AudioProcessor
from .enhanced_multimodal_processor import EnhancedMultiModalProcessor
from .image_processor import ImageProcessor
from .multimodal_processor import MultiModalProcessor
from .text_processor import TextProcessor
from .video_processor import VideoProcessor

# 可选导入 - 可能不存在
try:
    from .tesseract_ocr import TesseractOCRProcessor
except ImportError:
    TesseractOCRProcessor = None

try:
    from .opencv_image_processor import OpenCVImageProcessor
except ImportError:
    OpenCVImageProcessor = None

__all__ = [
    'AudioProcessor',
    'EnhancedMultiModalProcessor',
    'ImageProcessor',
    'MultiModalProcessor',
    'TextProcessor',
    'VideoProcessor',
]
