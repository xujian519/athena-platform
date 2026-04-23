#!/usr/bin/env python3

"""
增强专利感知模块
Enhanced Patent Perception Module

专门针对专利应用的感知优化,支持专利文档、图纸、技术特征等的专业分析

作者: Athena AI系统
创建时间: 2025-12-07
版本: 1.0.0
"""

import base64
import json
import logging
import os
import re
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
import requests
from PIL import Image

from .processors.image_processor import ImageProcessor
from .processors.multimodal_processor import MultiModalProcessor
from .processors.text_processor import TextProcessor
from .types import PatentPerceptionResult

logger = logging.getLogger(__name__)


class PatentInputType(Enum):
    """专利输入类型"""

    PATENT_TEXT = "patent_text"
    PATENT_IMAGE = "patent_image"
    PATENT_DRAWING = "patent_drawing"
    TECHNICAL_DIAGRAM = "technical_diagram"
    CLAIMS_TEXT = "claims_text"
    SPECIFICATION = "specification"
    PRIOR_ART = "prior_art"
    INVALIDATION_EVIDENCE = "invalidation_evidence"
    MULTIMODAL_PATENT = "multimodal_patent"


class PatentTechnicalExtractor:
    """专利技术特征提取器"""

    def __init__(self):
        # 技术术语词典
        self.technical_terms = self._load_technical_dictionary()

        # IPC分类映射
        self.ipc_mapping = self._load_ipc_mapping()

        # 技术特征模式
        self.feature_patterns = [
            r"包括[::]\s*([^,。;;\n]+)",  # 包括:xxx
            r"由[::]\s*([^,。;;\n]+)",  # 由:xxx
            r"具有[::]\s*([^,。;;\n]+)",  # 具有:xxx
            r"设置[::]\s*([^,。;;\n]+)",  # 设置:xxx
            r"配备[::]\s*([^,。;;\n]+)",  # 配备:xxx
            r"安装[::]\s*([^,。;;\n]+)",  # 安装:xxx
        ]

    def _load_technical_dictionary(self) -> dict[str, list[str]]:
        """加载技术术语词典

        词典加载优先级:
        1. 环境变量 PATENT_TECHNICAL_DICT_PATH 指定的路径
        2. 项目根目录下的 data/technical_dictionary.json
        3. 当前目录下的 data/technical_dictionary.json
        4. 默认内置词典(兜底)
        """
        dict_path = None

        # 1. 尝试从环境变量获取
        env_path = os.getenv("PATENT_TECHNICAL_DICT_PATH")
        if env_path:
            dict_path = Path(env_path)
            if dict_path.exists():
                try:
                    with open(dict_path, encoding="utf-8") as f:
                        logger.info(f"从环境变量加载技术词典: {dict_path}")
                        return json.load(f)
                except Exception as e:
                    logger.warning(f"从环境变量路径加载词典失败: {e}")

        # 2. 尝试从项目根目录获取
        try:
            # 获取当前文件的目录
            current_dir = Path(__file__).parent
            # 向上查找项目根目录(包含pyproject.toml的目录)
            root_dir = current_dir
            for _ in range(5):  # 最多向上查找5层
                if (root_dir / "pyproject.toml").exists():
                    break
                root_dir = root_dir.parent

            dict_path = root_dir / "data" / "technical_dictionary.json"
            if dict_path.exists():
                with open(dict_path, encoding="utf-8") as f:
                    logger.info(f"从项目根目录加载技术词典: {dict_path}")
                    return json.load(f)
        except Exception as e:
            logger.warning(f"从项目根目录加载技术词典失败: {e}")

        # 默认技术词典
        return {
            "机械": ["齿轮", "轴承", "传动", "发动机", "泵", "阀门", "管道", "连接件"],
            "电子": ["芯片", "电路", "传感器", "控制器", "处理器", "存储器", "显示器", "天线"],
            "化学": ["化合物", "聚合物", "催化剂", "反应器", "分离", "纯化", "合成", "配方"],
            "通信": ["基站", "天线", "信号", "协议", "编码", "调制", "网络", "传输"],
            "材料": ["合金", "复合材料", "纳米材料", "涂层", "薄膜", "纤维", "陶瓷", "塑料"],
        }

    def _load_ipc_mapping(self) -> dict[str, str]:
        """加载IPC分类映射"""
        return {
            "A": "人类生活必需",
            "B": "作业;运输",
            "C": "化学;冶金",
            "D": "纺织;造纸",
            "E": "固定建筑物",
            "F": "机械工程;照明;加热;武器;爆破",
            "G": "物理",
            "H": "电学",
        }

    def extract_technical_features(self, text: str) -> dict[str, Any]:
        """提取技术特征"""
        features = {
            "components": [],
            "structures": [],
            "functions": [],
            "materials": [],
            "parameters": [],
        }

        # 使用模式匹配提取特征
        for pattern in self.feature_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                feature = match.strip()
                if len(feature) > 2:  # 过滤太短的匹配
                    features["components"].append(feature)

        # 提取技术参数
        param_patterns = [
            r"(\d+(?:\.\d+)?)\s*[mmcmμm%℃]",
            r"(\d+(?:\.\d+)?)\s*[k_kg_gm][wh_wh]",
            r"(\d+(?:\.\d+)?)\s*[VvAa]",
            r"(\d+(?:\.\d+)?)\s*[Hh]z",
        ]

        for pattern in param_patterns:
            matches = re.findall(pattern, text)
            features["parameters"].extend(matches)

        # 识别技术领域
        for tech_field, terms in self.technical_terms.items():
            for term in terms:
                if term in text:
                    features["technical_field"] = tech_field
                    break

        return features


class PatentDrawingAnalyzer:
    """专利图纸分析器"""

    def __init__(self):
        self.drawing_patterns = {
            "reference_numbers": r"(\d+)",  # 参考数字
            "dimensions": r"(\d+\.?\d*)\s*[mmcm]",  # 尺寸标注
            "view_labels": r"[A-Za-z]\s*[-–—]\s*[A-Za-z]",  # 视图标签
        }

    def analyze_drawing(self, image_data: np.ndarray) -> dict[str, Any]:
        """分析专利图纸"""
        try:
            # 转换为灰度图
            if len(image_data.shape) == 3:
                gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
            else:
                gray = image_data

            # 检测线条
            edges = cv2.Canny(gray, 50, 150)

            # 检测轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 分析图像特征
            analysis = {
                "contour_count": len(contours),
                "line_density": np.sum(edges) / (edges.shape[0] * edges.shape[1]),
                "symmetry_score": self._calculate_symmetry(gray),
                "drawing_type": self._classify_drawing_type(edges, contours),
                "elements": self._extract_drawing_elements(gray),
            }

            return analysis

        except Exception as e:
            logger.error(f"图纸分析失败: {e}")
            return {"error": str(e)}

    def _calculate_symmetry(self, gray: np.ndarray) -> float:
        """计算对称性分数"""
        try:
            _h, w = gray.shape
            left_half = gray[:, : w // 2]
            right_half = np.fliplr(gray[:, w // 2 :])

            # 计算左右对称性
            if left_half.shape == right_half.shape:
                diff = np.abs(left_half.astype(float) - right_half.astype(float))
                symmetry = 1.0 - (np.mean(diff) / 255.0)
                return max(0, symmetry)
            return 0.0
        except Exception:
            return 0.0

    def _classify_drawing_type(self, edges: np.ndarray, contours: list) -> str:
        """分类图纸类型"""
        contour_count = len(contours)
        edge_density = np.sum(edges) / (edges.shape[0] * edges.shape[1])

        if contour_count > 100 and edge_density > 0.1:
            return "complex_mechanical"
        elif contour_count > 50:
            return "schematic"
        elif edge_density > 0.05:
            return "technical_drawing"
        else:
            return "simple_diagram"

    def _extract_drawing_elements(self, gray: np.ndarray) -> list[dict[str, Any]]:
        """提取图纸元素"""
        elements = []

        try:
            # 检测圆形(参考数字通常用圆圈标注)
            circles = cv2.HoughCircles(
                gray, cv2.HOUGH_GRADIENT, 1, 20, param1=50, param2=30, min_radius=5, max_radius=20
            )

            if circles is not None:
                circles = np.uint16(np.around(circles))
                for i, (x, y, r) in enumerate(circles[0, :]):
                    elements.append(
                        {
                            "type": "reference_circle",
                            "position": [int(x), int(y)],
                            "radius": int(r),
                            "id": f"ref_{i}",
                        }
                    )

            # 检测矩形
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for i, contour in enumerate(contours[:20]):  # 限制数量
                area = cv2.contourArea(contour)
                if area > 100:  # 过滤太小的轮廓
                    x, y, w, h = cv2.boundingRect(contour)
                    elements.append(
                        {"type": "rectangle", "bbox": [x, y, w, h], "area": area, "id": f"rect_{i}"}
                    )

        except Exception as e:
            logger.error(f"图纸元素提取失败: {e}")

        return elements


class PatentNoveltyAnalyzer:
    """专利新颖性分析器"""

    def __init__(self):
        self.prior_art_keywords = [
            "现有技术",
            "背景技术",
            "prior art",
            "background art",
            "已知",
            "常规",
            "传统",
            "conventional",
            "traditional",
        ]

        self.novelty_indicators = [
            "首次提出",
            "创新",
            "突破",
            "改进",
            "优化",
            "new",
            "novel",
            "improved",
            "enhanced",
            "innovative",
        ]

    def analyze_novelty(
        self, patent_text: str, prior_art_text: Optional[str] = None
    ) -> dict[str, Any]:
        """分析新颖性"""
        novelty_score = 0.0
        novelty_features = []

        # 检查新颖性指标
        for indicator in self.novelty_indicators:
            if indicator.lower() in patent_text.lower():
                novelty_score += 0.1
                novelty_features.append(indicator)

        # 检查区别于现有技术的声明
        if any(keyword in patent_text for keyword in self.prior_art_keywords):
            novelty_score += 0.2

        # 技术独特性分析
        unique_phrases = self._extract_unique_phrases(patent_text)
        novelty_score += min(0.3, len(unique_phrases) * 0.05)

        # 如果有对比文件,进行相似度分析
        if prior_art_text:
            similarity = self._calculate_similarity(patent_text, prior_art_text)
            novelty_score = max(0, novelty_score - similarity * 0.5)

        return {
            "novelty_score": min(1.0, novelty_score),
            "novelty_features": novelty_features,
            "unique_phrases": unique_phrases,
            "similarity_to_prior_art": similarity if prior_art_text else None,
            "assessment": self._assess_novelty_level(novelty_score),
        }

    def _extract_unique_phrases(self, text: str) -> list[str]:
        """提取独特短语"""
        # 简单实现:提取包含技术术语的长短语
        unique_phrases = []
        sentences = re.split(r"[。;;]", text)

        for sentence in sentences:
            if len(sentence) > 20 and any(
                tech in sentence for tech in ["装置", "系统", "方法", "结构"]
            ):
                unique_phrases.append(sentence.strip())

        return unique_phrases[:5]  # 返回前5个

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        # 简单实现:基于词汇重叠度
        words1 = set(re.findall(r"\w+", text1.lower()))
        words2 = set(re.findall(r"\w+", text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _assess_novelty_level(self, score: float) -> str:
        """评估新颖性等级"""
        if score >= 0.8:
            return "high_novelty"
        elif score >= 0.5:
            return "moderate_novelty"
        elif score >= 0.2:
            return "low_novelty"
        else:
            return "no_novelty"


class EnhancedPatentPerceptionEngine:
    """增强专利感知引擎"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False

        # 初始化子组件
        self.technical_extractor = PatentTechnicalExtractor()
        self.drawing_analyzer = PatentDrawingAnalyzer()
        self.novelty_analyzer = PatentNoveltyAnalyzer()

        # 基础处理器
        self.text_processor = None
        self.image_processor = None
        self.multimodal_processor = None

        # 专利数据库连接
        self.patent_db_config = self.config.get("patent_db", {})

        logger.info("🔍 创建增强专利感知引擎")

    async def initialize(self):
        """初始化专利感知引擎"""
        if self.initialized:
            return

        logger.info("🚀 启动增强专利感知引擎")

        try:
            # 初始化基础处理器
            self.text_processor = TextProcessor("patent_text", self.config.get("text", {}))
            self.image_processor = ImageProcessor("patent_image", self.config.get("image", {}))
            self.multimodal_processor = MultiModalProcessor(
                "patent_multimodal", self.config.get("multimodal", {})
            )

            await self.text_processor.initialize()
            await self.image_processor.initialize()
            await self.multimodal_processor.initialize()

            # 连接专利向量数据库
            await self._connect_patent_databases()

            self.initialized = True
            logger.info("✅ 增强专利感知引擎启动完成")

        except Exception as e:
            logger.error(f"❌ 专利感知引擎启动失败: {e}")
            raise

    async def _connect_patent_databases(self):
        """连接专利数据库"""
        try:
            # 检查向量数据库连接
            vector_db_url = self.patent_db_config.get("vector_db_url", "http://localhost:6333")

            try:
                response = requests.get(f"{vector_db_url}/health", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ 专利向量数据库连接成功")
                else:
                    logger.warning("⚠️ 专利向量数据库响应异常")
            except Exception:
                logger.warning("⚠️ 专利向量数据库连接失败")

            # 检查知识图谱连接
            kg_endpoint = self.patent_db_config.get("kg_endpoint", "http://localhost:8017")

            try:
                response = requests.get(f"{kg_endpoint}/health", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ 专利知识图谱连接成功")
                else:
                    logger.warning("⚠️ 专利知识图谱响应异常")
            except Exception:
                logger.warning("⚠️ 专利知识图谱连接失败")

        except Exception as e:
            logger.error(f"专利数据库连接检查失败: {e}")

    async def process_patent_text(
        self, text: str, patent_id: Optional[str] = None
    ) -> PatentPerceptionResult:
        """处理专利文本"""
        if not self.initialized:
            raise RuntimeError("专利感知引擎未初始化")

        try:
            logger.info(f"📄 处理专利文本: {patent_id or 'unknown'}")

            # 使用基础文本处理器
            text_result = await self.text_processor.process(text, "text")

            # 提取专利特定特征
            technical_features = self.technical_extractor.extract_technical_features(text)

            # 分析新颖性
            novelty_analysis = self.novelty_analyzer.analyze_novelty(text)

            # 构建专利感知结果
            result = PatentPerceptionResult(
                input_type=PatentInputType.PATENT_TEXT.value,
                patent_id=patent_id,
                key_features=technical_features,
                novelty_analysis=novelty_analysis,
                confidence=text_result.confidence,
                metadata=text_result.metadata,
                raw_content=text,
                structured_content=technical_features,
            )

            # 提取标题和摘要
            result.title = self._extract_title(text)
            result.abstract = self._extract_abstract(text)
            result.technical_field = technical_features.get("technical_field")

            logger.info(f"✅ 专利文本处理完成: {patent_id}")
            return result

        except Exception as e:
            logger.error(f"❌ 专利文本处理失败: {e}")
            raise

    async def process_patent_drawing(
        self, image_data: np.ndarray | bytes | Optional[str] = None, patent_id: Optional[str] = None
    ) -> PatentPerceptionResult:
        """处理专利图纸"""
        if not self.initialized:
            raise RuntimeError("专利感知引擎未初始化")

        try:
            logger.info(f"🖼️ 处理专利图纸: {patent_id or 'unknown'}")

            # 处理图像数据
            if isinstance(image_data, str):
                # URL或文件路径
                image_data = await self._load_image_from_path(image_data)
            elif isinstance(image_data, bytes):
                # base64编码的图像数据
                image_data = np.array(Image.open(BytesIO(base64.b64decode(image_data))))

            # 使用基础图像处理器
            image_result = await self.image_processor.process(image_data, "image")

            # 专利图纸特定分析
            drawing_analysis = self.drawing_analyzer.analyze_drawing(image_data)

            # 构建专利感知结果
            result = PatentPerceptionResult(
                input_type=PatentInputType.PATENT_DRAWING.value,
                patent_id=patent_id,
                drawing_elements=drawing_analysis.get("elements", []),
                confidence=image_result.confidence,
                metadata={**image_result.metadata, "drawing_analysis": drawing_analysis},
                raw_content=image_data,
                structured_content=drawing_analysis,
            )

            logger.info(f"✅ 专利图纸处理完成: {patent_id}")
            return result

        except Exception as e:
            logger.error(f"❌ 专利图纸处理失败: {e}")
            raise

    async def process_multimodal_patent(
        self, text: str, images: list[np.ndarray], patent_id: Optional[str] = None
    ) -> PatentPerceptionResult:
        """处理多模态专利"""
        if not self.initialized:
            raise RuntimeError("专利感知引擎未初始化")

        try:
            logger.info(f"🔄 处理多模态专利: {patent_id or 'unknown'}")

            # 处理文本部分
            text_result = await self.process_patent_text(text, patent_id)

            # 处理图像部分
            drawing_results = []
            for i, image in enumerate(images):
                drawing_result = await self.process_patent_drawing(image, f"{patent_id}_img_{i}")
                drawing_results.append(drawing_result)

            # 合并所有图纸元素
            all_drawing_elements = []
            for drawing_result in drawing_results:
                all_drawing_elements.extend(drawing_result.drawing_elements)

            # 计算平均置信度
            avg_drawing_confidence = (
                sum(dr.confidence for dr in drawing_results) / len(drawing_results)
                if drawing_results
                else 0
            )

            # 构建多模态专利感知结果
            result = PatentPerceptionResult(
                input_type=PatentInputType.MULTIMODAL_PATENT.value,
                patent_id=patent_id,
                title=text_result.title,
                abstract=text_result.abstract,
                technical_field=text_result.technical_field,
                key_features=text_result.key_features,
                novelty_analysis=text_result.novelty_analysis,
                drawing_elements=all_drawing_elements,
                confidence=(
                    (text_result.confidence + avg_drawing_confidence) / 2
                    if drawing_results
                    else text_result.confidence
                ),
                metadata={
                    "text_result": text_result.metadata,
                    "image_count": len(images),
                    "drawing_analyses": drawing_results,
                },
                raw_content={"text": text, "image_count": len(images)},
                structured_content={
                    "text_analysis": text_result.structured_content,
                    "drawing_analyses": drawing_results,
                },
            )

            logger.info(f"✅ 多模态专利处理完成: {patent_id}")
            return result

        except Exception as e:
            logger.error(f"❌ 多模态专利处理失败: {e}")
            raise

    def _extract_title(self, text: str) -> Optional[str]:
        """提取专利标题"""
        lines = text.split("\n")
        for line in lines[:10]:  # 通常标题在前10行
            line = line.strip()
            # 简单启发式:检查是否像标题
            if (
                line
                and len(line) > 5
                and len(line) < 100
                and not any(char in line for char in "。,;;!?")
            ):
                return line
        return None

    def _extract_abstract(self, text: str) -> Optional[str]:
        """提取摘要"""
        # 查找摘要关键词
        abstract_keywords = ["摘要", "abstract", "发明内容", "技术领域"]

        lines = text.split("\n")
        abstract_lines = []
        found_abstract = False

        for line in lines:
            line = line.strip()

            # 检查是否开始摘要
            if any(keyword in line.lower() for keyword in abstract_keywords):
                found_abstract = True
                continue

            # 收集摘要内容
            if found_abstract and line:
                if len(abstract_lines) < 10:  # 限制摘要长度
                    abstract_lines.append(line)
                else:
                    break

        return " ".join(abstract_lines) if abstract_lines else None

    async def _load_image_from_path(self, path: str) -> np.ndarray:
        """从路径加载图像"""
        if path.startswith("http"):
            # URL
            response = requests.get(path)
            image = Image.open(BytesIO(response.content))
            return np.array(image)
        else:
            # 本地文件路径
            image = Image.open(path)
            return np.array(image)

    async def search_similar_patents(
        self, query_text: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """搜索相似专利"""
        try:
            # 向量化查询文本
            vector_result = await self.text_processor.process(query_text, "text")
            query_vector = vector_result.features.get("vector")

            if not query_vector:
                logger.warning("无法生成查询向量")
                return []

            # 在专利向量数据库中搜索
            search_url = f"{self.patent_db_config.get('vector_db_url', 'http://localhost:6333')}/collections/patent_vectors/points/search"

            search_data = {
                "vector": query_vector,
                "limit": limit,
                "with_payload": True,
                "with_vector": False,
            }

            response = requests.post(search_url, json=search_data)
            if response.status_code == 200:
                results = response.json()
                return results.get("result", [])
            else:
                logger.error(f"相似专利搜索失败: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"相似专利搜索异常: {e}")
            return []

    async def get_status(self) -> dict[str, Any]:
        """获取专利感知引擎状态"""
        return {
            "engine_initialized": self.initialized,
            "text_processor_ready": self.text_processor is not None
            and self.text_processor.initialized,
            "image_processor_ready": self.image_processor is not None
            and self.image_processor.initialized,
            "multimodal_processor_ready": self.multimodal_processor is not None
            and self.multimodal_processor.initialized,
            "technical_dictionary_loaded": bool(self.technical_extractor.technical_terms),
            "patent_db_configured": bool(self.patent_db_config),
            "supported_input_types": [t.value for t in PatentInputType],
        }

    async def shutdown(self):
        """关闭专利感知引擎"""
        logger.info("🔄 关闭增强专利感知引擎")

        try:
            if self.text_processor:
                await self.text_processor.cleanup()
            if self.image_processor:
                await self.image_processor.cleanup()
            if self.multimodal_processor:
                await self.multimodal_processor.cleanup()

            self.initialized = False
            logger.info("✅ 增强专利感知引擎已关闭")

        except Exception as e:
            logger.error(f"❌ 专利感知引擎关闭失败: {e}")


# 导出类
__all__ = [
    "EnhancedPatentPerceptionEngine",
    "PatentDrawingAnalyzer",
    "PatentInputType",
    "PatentNoveltyAnalyzer",
    "PatentPerceptionResult",
    "PatentTechnicalExtractor",
]

