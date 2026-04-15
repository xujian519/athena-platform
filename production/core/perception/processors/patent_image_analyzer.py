#!/usr/bin/env python3
"""
专利附图智能分析器
Patent Image Intelligent Analyzer

功能:
1. 图像描述生成 - 使用BLIP模型生成图像描述
2. 文本-图像对齐 - 使用CLIP模型计算图文相似度
3. OCR文字提取 - 提取附图中的文字信息
4. 图文一致性检查 - 检查专利附图与文本描述的一致性
5. 技术特征提取 - 识别附图中的技术元素

作者: Athena平台团队
创建时间: 2026-01-31
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import base64
import hashlib
import io
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from PIL import Image

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 配置常量
# ============================================================================


class BLIPConfig:
    """BLIP模型配置常量"""
    MAX_CAPTION_LENGTH = 50      # 最大描述长度
    NUM_BEAMS = 5                # 束搜索数量
    USE_EARLY_STOPPING = True    # 早停策略


class ModelPaths:
    """模型路径配置"""
    MODELSCOPE_BLIP = os.getenv(
        "MODELSCOPE_BLIP_PATH",
        "~/.cache/modelscope/cubeai/blip-image-captioning-base"
    )
    HUGGINGFACE_CACHE = os.getenv(
        "HUGGINGFACE_CACHE",
        "~/.cache/huggingface"
    )


class ImageValidation:
    """图像验证配置"""
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}


class ModelLoading:
    """模型加载配置"""
    CLIP_TIMEOUT = 120    # CLIP模型加载超时(秒)
    BLIP_TIMEOUT = 180    # BLIP模型加载超时(秒，CPU上加载近1GB模型需要更长时间)
    RETRY_DELAY = 5       # 重试延迟(秒)
    MAX_RETRIES = 2       # 最大重试次数


# ============================================================================
# 数据模型
# ============================================================================


class ImageType(str, Enum):
    """专利附图类型"""
    FIGURE = "figure"          # 示意图
    FLOWCHART = "flowchart"    # 流程图
    STRUCTURE = "structure"    # 结构图
    GRAPH = "graph"            # 图表
    TABLE = "table"            # 表格
    FORMULA = "formula"        # 公式图
    SCHEMATIC = "schematic"    # 原理图
    PHOTO = "photo"            # 实物照片
    OTHER = "other"            # 其他


@dataclass
class ImageAnalysisResult:
    """图像分析结果"""
    image_id: str
    image_type: ImageType
    caption: str = ""               # 图像描述
    ocr_text: str = ""              # OCR提取的文字
    text_regions: list[dict] = field(default_factory=list)
    technical_features: list[str] = field(default_factory=list)
    consistency_score: float = 0.0   # 图文一致性分数
    confidence: float = 0.0
    processing_time: float = 0.0
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "image_id": self.image_id,
            "image_type": self.image_type.value,
            "caption": self.caption,
            "ocr_text": self.ocr_text,
            "text_regions": self.text_regions,
            "technical_features": self.technical_features,
            "consistency_score": self.consistency_score,
            "confidence": self.confidence,
            "processing_time": self.processing_time,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


# ============================================================================
# 专利附图分析器
# ============================================================================


class PatentImageAnalyzer:
    """
    专利附图智能分析器

    功能:
    1. 图像描述生成 - 使用BLIP模型
    2. 文本-图像对齐 - 使用CLIP模型
    3. OCR文字提取
    4. 图文一致性检查
    """

    def __init__(
        self,
        clip_model: str = "openai/clip-vit-base-patch32",
        blip_model: str = "Salesforce/blip-image-captioning-base",
        device: str | None = None,
        cache_dir: str | None = None
    ):
        """
        初始化专利图像分析器

        Args:
            clip_model: CLIP模型名称
            blip_model: BLIP模型名称
            device: 运行设备 (None=自动检测, "cpu", "cuda", "mps")
            cache_dir: 模型缓存目录
        """
        self.clip_model_name = clip_model
        self.blip_model_name = blip_model

        # 自动检测最佳设备
        if device is None:
            self.device = self._detect_device()
        else:
            self.device = device

        self.cache_dir = cache_dir or os.path.expanduser(ModelPaths.HUGGINGFACE_CACHE)

        logger.info(f"使用设备: {self.device}")

        # 模型实例（延迟加载）
        self.clip_model = None
        self.clip_processor = None
        self.blip_model = None
        self.blip_processor = None

        # OCR引擎
        self._init_ocr()

        logger.info(f"PatentImageAnalyzer初始化完成 (device={device})")

    def _init_ocr(self):
        """初始化OCR引擎"""
        try:
            import pytesseract
            self.ocr_engine = pytesseract
            logger.info("OCR引擎初始化成功 (pytesseract)")
        except ImportError:
            logger.warning("pytesseract未安装，OCR功能将不可用")
            self.ocr_engine = None

    def _detect_device(self) -> str:
        """
        自动检测最佳可用设备

        优先级: MPS (Mac) > CUDA (NVIDIA) > CPU
        """
        try:
            import torch

            # 检测MPS (Apple Silicon)
            if torch.backends.mps.is_available():
                logger.info("检测到MPS设备 (Apple Silicon)，将使用GPU加速")
                return "mps"

            # 检测CUDA (NVIDIA)
            if torch.cuda.is_available():
                logger.info("检测到CUDA设备 (NVIDIA)，将使用GPU加速")
                return "cuda"

            # 使用CPU
            logger.info("未检测到GPU加速设备，将使用CPU")
            return "cpu"

        except ImportError:
            logger.warning("PyTorch未安装，将使用CPU模式")
            return "cpu"

    def _validate_image_file(self, image_path: str) -> bool:
        """
        验证图像文件安全性

        检查：
        1. 文件是否存在
        2. 文件大小是否在限制内
        3. 文件扩展名是否合法

        Args:
            image_path: 图像文件路径

        Returns:
            bool: 验证通过返回True

        Raises:
            ValueError: 验证失败时抛出
        """
        # 检查文件是否存在
        if not os.path.exists(image_path):
            raise ValueError(f"图像文件不存在: {image_path}")

        # 检查文件大小
        file_size = os.path.getsize(image_path)
        if file_size > ImageValidation.MAX_FILE_SIZE:
            raise ValueError(
                f"图像文件过大: {file_size / 1024 / 1024:.2f}MB "
                f"(最大限制: {ImageValidation.MAX_FILE_SIZE / 1024 / 1024:.0f}MB)"
            )

        # 检查文件扩展名
        file_ext = Path(image_path).suffix.lower()
        if file_ext not in ImageValidation.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"不支持的文件类型: {file_ext} "
                f"(支持的类型: {', '.join(ImageValidation.ALLOWED_EXTENSIONS)})"
            )

        return True

    def load_models(self):
        """加载模型（延迟加载，节省内存）"""
        if self.clip_model is None:
            logger.info("正在加载CLIP模型...")
            self._load_clip_model()

        if self.blip_model is None:
            logger.info("正在加载BLIP模型...")
            self._load_blip_model()

    def _load_clip_model(self):
        """加载CLIP模型（带超时控制，优先使用本地缓存）"""
        def _load():
            from transformers import CLIPModel, CLIPProcessor

            # 设置离线模式环境变量，强制使用本地缓存
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            os.environ['HF_HUB_OFFLINE'] = '1'

            self.clip_processor = CLIPProcessor.from_pretrained(
                self.clip_model_name,
                cache_dir=self.cache_dir,
                local_files_only=True  # 强制使用本地缓存
            )
            self.clip_model = CLIPModel.from_pretrained(
                self.clip_model_name,
                cache_dir=self.cache_dir,
                local_files_only=True  # 强制使用本地缓存
            ).to(self.device)
            return f"CLIP模型加载成功 (本地缓存): {self.clip_model_name}"

        try:
            result = with_timeout(
                _load,
                ModelLoading.CLIP_TIMEOUT,
                f"CLIP模型加载超时: {self.clip_model_name}"
            )
            logger.info(result)
        except TimeoutError as e:
            logger.error(str(e))
            raise
        except Exception as e:
            logger.error(f"CLIP模型加载失败: {e}")
            raise

    def _load_blip_model(self):
        """加载BLIP模型（使用ModelScope或HuggingFace，带超时控制）"""
        def _load_from_modelscope():
            """从ModelScope加载BLIP模型"""
            ms_model_path = os.path.expanduser(ModelPaths.MODELSCOPE_BLIP)
            logger.info("使用 ModelScope 本地模型加载 BLIP...")
            from transformers import BlipForConditionalGeneration, BlipProcessor

            self.blip_model = BlipForConditionalGeneration.from_pretrained(
                ms_model_path,
                trust_remote_code=True,
                local_files_only=True
            ).to(self.device)

            self.blip_processor = BlipProcessor.from_pretrained(
                ms_model_path,
                trust_remote_code=True,
                local_files_only=True
            )
            return f"BLIP模型加载成功 (ModelScope): {ms_model_path}"

        def _load_from_huggingface():
            """从HuggingFace加载BLIP模型"""
            logger.info("使用 HuggingFace 加载 BLIP...")
            from transformers import BlipForConditionalGeneration, BlipProcessor

            self.blip_processor = BlipProcessor.from_pretrained(
                self.blip_model_name,
                cache_dir=self.cache_dir
            )
            self.blip_model = BlipForConditionalGeneration.from_pretrained(
                self.blip_model_name,
                cache_dir=self.cache_dir
            ).to(self.device)
            return f"BLIP模型加载成功 (HuggingFace): {self.blip_model_name}"

        try:
            # 优先尝试使用 ModelScope 加载本地模型
            ms_model_path = os.path.expanduser(ModelPaths.MODELSCOPE_BLIP)

            if os.path.exists(ms_model_path):
                result = with_timeout(
                    _load_from_modelscope,
                    ModelLoading.BLIP_TIMEOUT,
                    f"BLIP模型加载超时 (ModelScope): {ms_model_path}"
                )
                logger.info(result)
            else:
                result = with_timeout(
                    _load_from_huggingface,
                    ModelLoading.BLIP_TIMEOUT,
                    f"BLIP模型加载超时 (HuggingFace): {self.blip_model_name}"
                )
                logger.info(result)

        except TimeoutError as e:
            logger.warning(f"{e}，将使用备用方案")
            self.blip_model = None
            self.blip_processor = None
        except Exception as e:
            logger.warning(f"BLIP模型加载失败: {e}，将使用备用方案")
            self.blip_model = None
            self.blip_processor = None

    # ========================================================================
    # 核心分析功能
    # ========================================================================

    async def analyze(
        self,
        image_input: str | bytes | Path | np.ndarray,
        reference_text: str | None = None
    ) -> ImageAnalysisResult:
        """
        分析专利附图

        Args:
            image_input: 图像输入（文件路径、字节数据、numpy数组等）
            reference_text: 参考文本（用于图文一致性检查）

        Returns:
            ImageAnalysisResult: 分析结果
        """
        import time
        start_time = time.time()

        # 生成图像ID
        image_id = self._generate_image_id(image_input)

        try:
            # 确保模型已加载
            self.load_models()

            # 加载图像
            image = self._load_image(image_input)
            if image is None:
                return ImageAnalysisResult(
                    image_id=image_id,
                    image_type=ImageType.OTHER,
                    error="无法加载图像"
                )

            # 1. 图像类型识别
            image_type = self._classify_image_type(image)

            # 2. 图像描述生成
            caption = await self._generate_caption(image)

            # 3. OCR文字提取
            ocr_text, text_regions = await self._extract_text(image)

            # 4. 技术特征提取
            technical_features = self._extract_features(image, image_type)

            # 5. 图文一致性检查（如果提供参考文本）
            consistency_score = 0.0
            if reference_text:
                consistency_score = await self._check_consistency(
                    image, reference_text, caption
                )

            processing_time = time.time() - start_time

            result = ImageAnalysisResult(
                image_id=image_id,
                image_type=image_type,
                caption=caption,
                ocr_text=ocr_text,
                text_regions=text_regions,
                technical_features=technical_features,
                consistency_score=consistency_score,
                confidence=self._calculate_confidence(
                    caption, ocr_text, technical_features
                ),
                processing_time=processing_time,
                metadata={
                    "image_size": image.size if isinstance(image, Image.Image) else None,
                    "model_versions": {
                        "clip": self.clip_model_name,
                        "blip": self.blip_model_name
                    }
                }
            )

            logger.info(f"图像分析完成: {image_id}, 耗时: {processing_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"图像分析失败: {e}")
            return ImageAnalysisResult(
                image_id=image_id,
                image_type=ImageType.OTHER,
                error=str(e),
                processing_time=time.time() - start_time
            )

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _generate_image_id(self, image_input: Any) -> str:
        """生成图像唯一ID"""
        if isinstance(image_input, (str, Path)):
            content = str(image_input).encode()
        elif isinstance(image_input, bytes):
            content = image_input
        elif isinstance(image_input, np.ndarray):
            content = image_input.tobytes()
        else:
            content = str(hash(image_input)).encode()

        return hashlib.md5(content).hexdigest()[:16]

    def _load_image(
        self,
        image_input: str | bytes | Path | np.ndarray
    ) -> Image.Image | None:
        """加载图像"""
        try:
            if isinstance(image_input, (str, Path)):
                # 验证文件安全性
                self._validate_image_file(str(image_input))
                # 从文件路径加载
                image = Image.open(image_input).convert("RGB")
            elif isinstance(image_input, bytes):
                # 从字节数据加载
                image = Image.open(io.BytesIO(image_input)).convert("RGB")
            elif isinstance(image_input, np.ndarray):
                # 从numpy数组加载
                image = Image.fromarray(image_input).convert("RGB")
            else:
                logger.error(f"不支持的图像输入类型: {type(image_input)}")
                return None

            # 调整大小（防止图像过大）
            max_size = 2048
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(s * ratio) for s in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            return image

        except Exception as e:
            logger.error(f"图像加载失败: {e}")
            return None

    def _classify_image_type(self, image: Image.Image) -> ImageType:
        """
        识别图像类型

        基于简单的启发式规则：
        - 宽高比判断（流程图通常是竖版）
        - 颜色分布判断（照片色彩丰富）
        - 边缘密度判断（图表线条密集）
        """
        # 转换为numpy数组
        img_array = np.array(image)

        # 计算宽高比
        height, width = img_array.shape[:2]
        aspect_ratio = width / height if height > 0 else 1.0

        # 计算色彩丰富度
        if len(img_array.shape) == 3:
            color_std = np.std(img_array, axis=(0, 1)).mean()
        else:
            color_std = 0

        # 计算边缘密度
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size

        # 启发式分类
        if aspect_ratio < 0.8:
            return ImageType.FLOWCHART
        elif color_std > 50:
            return ImageType.PHOTO
        elif edge_density > 0.1:
            return ImageType.GRAPH
        elif edge_density > 0.05:
            return ImageType.STRUCTURE
        else:
            return ImageType.FIGURE

    async def _generate_caption(self, image: Image.Image) -> str:
        """生成图像描述（使用BLIP）"""
        try:
            # 检查 BLIP 模型是否可用
            if self.blip_model is None or self.blip_processor is None:
                raise ValueError("BLIP 模型未加载")

            inputs = self.blip_processor(image, return_tensors="pt").to(self.device)

            with torch.no_grad():
                out = self.blip_model.generate(
                    **inputs,
                    max_length=BLIPConfig.MAX_CAPTION_LENGTH,
                    num_beams=BLIPConfig.NUM_BEAMS,
                    early_stopping=BLIPConfig.USE_EARLY_STOPPING
                )

            caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
            logger.info(f"生成图像描述: {caption}")
            return caption

        except Exception as e:
            logger.warning(f"BLIP 图像描述生成失败: {e}，使用备用方案")

            # 备用方案：基于图像类型生成简单描述
            try:
                image_type = self._classify_image_type(image)
                caption = self._generate_fallback_caption(image, image_type)
                logger.info(f"使用备用描述: {caption}")
                return caption
            except (ValueError, RuntimeError, AttributeError) as e:
                logger.warning(f"备用描述生成失败: {e}")
                return ""

    async def _extract_text(
        self,
        image: Image.Image
    ) -> tuple[str, list[dict]]:
        """提取图像中的文字（OCR）"""
        if self.ocr_engine is None:
            return "", []

        try:
            # 转换为numpy数组
            img_array = np.array(image)

            # 使用pytesseract提取文字
            text = self.ocr_engine.image_to_string(
                img_array,
                lang='chi_sim+eng',  # 中英文混合
                config='--psm 6'      # 假设单列文本块
            )

            # 提取文字区域
            data = self.ocr_engine.image_to_data(
                img_array,
                lang='chi_sim+eng',
                output_type=self.ocr_engine.Output.DICT
            )

            text_regions = []
            current_region = {}
            prev_text = ""

            for item in data['text']:
                if item.strip():
                    if not current_region:
                        current_region = {'text': item}
                    elif prev_text:
                        # 同一行
                        current_region['text'] += ' ' + item
                    prev_text = item
                else:
                    if current_region:
                        text_regions.append(current_region)
                        current_region = {}
                    prev_text = ""

            if current_region:
                text_regions.append(current_region)

            return text.strip(), text_regions

        except Exception as e:
            logger.error(f"OCR提取失败: {e}")
            return "", []

    def _extract_features(
        self,
        image: Image.Image,
        image_type: ImageType
    ) -> list[str]:
        """提取技术特征"""
        features = []

        # 基于图像类型的特征提取
        if image_type == ImageType.FLOWCHART:
            features.extend([
                "流程节点",
                "箭头连接",
                "决策分支",
                "循环结构"
            ])
        elif image_type == ImageType.STRUCTURE:
            features.extend([
                "组件模块",
                "连接关系",
                "层次结构",
                "接口定义"
            ])
        elif image_type == ImageType.GRAPH:
            features.extend([
                "数据曲线",
                "坐标轴",
                "图例标注",
                "趋势分析"
            ])

        # 通用视觉特征
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # 检测是否有网格
        edges_h = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        edges_v = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

        if np.abs(edges_h).mean() > 30 and np.abs(edges_v).mean() > 30:
            features.append("网格背景")

        # 检测是否有标注
        if np.sum(edges_v) > np.sum(edges_h) * 1.5:
            features.append("文字标注")

        return features

    async def _check_consistency(
        self,
        image: Image.Image,
        reference_text: str,
        generated_caption: str
    ) -> float:
        """检查图文一致性"""
        try:
            # 使用CLIP计算图文相似度
            inputs = self.clip_processor(
                text=[reference_text, generated_caption],
                images=image,
                return_tensors="pt",
                padding=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.clip_model(**inputs)

            # 获取图文相似度
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=-1)

            # 参考文本的相似度
            consistency_score = probs[0][0].item()

            logger.info(f"图文一致性分数: {consistency_score:.4f}")
            return consistency_score

        except Exception as e:
            logger.error(f"一致性检查失败: {e}")
            return 0.0

    def _calculate_confidence(
        self,
        caption: str,
        ocr_text: str,
        features: list[str]
    ) -> float:
        """计算分析置信度"""
        confidence = 0.0

        # 图像描述有内容
        if len(caption) > 10:
            confidence += 0.4

        # OCR有结果
        if len(ocr_text) > 0:
            confidence += 0.3

        # 提取到特征
        if len(features) > 0:
            confidence += 0.3

        return min(confidence, 1.0)

    def _generate_fallback_caption(self, image: Image.Image, image_type: ImageType) -> str:
        """生成备用图像描述（基于图像类型）"""
        captions = {
            ImageType.FIGURE: "专利附图，包含技术元件和连接关系",
            ImageType.FLOWCHART: "流程图，展示处理步骤或方法流程",
            ImageType.STRUCTURE: "结构图，展示系统或装置的组成结构",
            ImageType.GRAPH: "数据图表，包含实验结果或性能数据",
            ImageType.TABLE: "表格，包含参数或规格说明",
            ImageType.OTHER: "专利附图，包含技术信息"
        }

        base_caption = captions.get(image_type, "专利附图")

        # 尝试使用 OCR 信息增强描述
        if self.ocr_engine is not None:
            try:
                import pytesseract
                ocr_text = pytesseract.image_to_string(image)
                if len(ocr_text.strip()) > 5:
                    base_caption += f"，包含文字信息: {ocr_text.strip()[:30]}..."
            except (ValueError, RuntimeError, AttributeError) as e:
                logger.debug(f"OCR增强描述失败: {e}")

        return base_caption


# ============================================================================
# 工具函数
# ============================================================================


def with_timeout(func, timeout_seconds: int, timeout_error_msg: str):
    """
    为函数执行添加超时控制

    Args:
        func: 要执行的函数
        timeout_seconds: 超时时间(秒)
        timeout_error_msg: 超时错误消息

    Returns:
        函数执行结果

    Raises:
        TimeoutError: 超时时抛出
    """
    import queue
    import threading

    result_queue = queue.Queue()
    exception_queue = queue.Queue()

    def worker():
        try:
            result = func()
            result_queue.put(result)
        except Exception as e:
            exception_queue.put(e)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout_seconds)

    if thread.is_alive():
        # 线程仍在运行，超时
        raise TimeoutError(f"{timeout_error_msg} (超时时间: {timeout_seconds}秒)")

    # 检查是否有异常
    if not exception_queue.empty():
        raise exception_queue.get()

    # 返回结果
    if not result_queue.empty():
        return result_queue.get()


def decode_image_from_base64(base64_data: str) -> bytes:
    """从base64数据解码图像"""
    # 移除可能的数据URI前缀
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]
    return base64.b64decode(base64_data)


def encode_image_to_base64(image_path: str) -> str:
    """将图像文件编码为base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


# ============================================================================
# 主程序
# ============================================================================


if __name__ == "__main__":
    import asyncio

    import torch

    async def main():
        # 创建分析器
        analyzer = PatentImageAnalyzer(device="cpu")

        # 测试图像分析
        image_path = "/path/to/patent/figure.png"

        if os.path.exists(image_path):
            result = await analyzer.analyze(image_path)

            print("=" * 60)
            print("专利附图分析结果")
            print("=" * 60)
            print(f"图像ID: {result.image_id}")
            print(f"图像类型: {result.image_type.value}")
            print(f"图像描述: {result.caption}")
            print(f"OCR文字: {result.ocr_text[:100]}...")
            print(f"技术特征: {', '.join(result.technical_features)}")
            print(f"置信度: {result.confidence:.2f}")
            print(f"处理时间: {result.processing_time:.2f}s")
            print("=" * 60)
        else:
            print(f"测试图像不存在: {image_path}")

    # 运行测试
    asyncio.run(main())
