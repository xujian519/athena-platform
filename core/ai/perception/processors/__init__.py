
"""
感知模块处理器包
包含OCR、图像处理、文件处理等
"""

# 导入实际存在的处理器

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

