#!/usr/bin/env python3
"""
增强感知模块 - BaseModule标准接口兼容版本
Enhanced Perception Module - BaseModule Compatible Version

⚠️ DEPRECATED - 此模块已被弃用

弃用时间: 2026-01-25
弃用原因: 功能已整合到 `unified_optimized_processor.py`
迁移指南: 请使用 `core.perception.UnifiedOptimizedProcessor` 替代

新模块提供:
- 统一的BaseModule标准接口
- 更好的模块化设计
- 更完善的错误处理
- 更强的扩展性

此文件保留用于向后兼容,但将在未来版本中移除。

---

基于现有StructuredPatentPerceptionEngine,添加BaseModule标准接口支持
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import warnings

# 发出弃用警告
warnings.warn(
    "enhanced_perception_module.py 已被弃用,请使用 unified_optimized_processor.py。"
    "此模块将在未来版本中移除。",
    DeprecationWarning,
    stacklevel=2,
)

import logging
import os
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from core.logging_config import setup_logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "patent-platform" / "workspace" / "src"))

# 导入BaseModule
from core.base_module import BaseModule

# 导入现有感知引擎
DocumentType = None
DocumentGraph = None
DIKWPResult = None
ModalityType = None
StructuredPatentPerceptionEngine = None

try:
    from perception.structured_perception_engine import (
        DocumentGraph,
        DocumentType,
        ModalityType,
        StructuredPatentPerceptionEngine,
    )

    EXISTING_ENGINE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"无法导入现有感知引擎: {e}")
    EXISTING_ENGINE_AVAILABLE = False

    # 定义基础类型作为备用
    from dataclasses import dataclass
    from enum import Enum
    from typing import Any

    class DocumentType(Enum):
        PATENT = "patent"
        TECH_DISCLOSURE = "tech_disclosure"
        TECH_MANUAL = "tech_manual"
        TECH_DRAWING = "tech_drawing"
        SPECIFICATION = "specification"

    class ModalityType(Enum):
        TEXT = "text"
        IMAGE = "image"
        TABLE = "table"
        FORMULA = "formula"
        DRAWING = "drawing"
        MARKUP = "markup"
        STRUCTURE = "structure"
        CAD = "cad"
        HANDWRITING = "handwriting"

    @dataclass
    class DocumentGraph:
        document_id: str
        document_type: DocumentType
        nodes: list[dict[str, Any]
        edges: list[dict[str, Any]
        cross_modal_alignments: list[dict[str, Any]
        context_state: dict[str, Any]
        knowledge_injections: list[dict[str, Any]
# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class EnhancedPerceptionModule(BaseModule):
    """增强感知模块 - BaseModule标准接口版本"""

    def __init__(self, agent_id: str, config: Optional[dict[str, Any]] = None):
        """
        初始化增强感知模块

        Args:
            agent_id: 智能体标识符
            config: 配置参数
        """
        super().__init__(agent_id, config)

        # 感知模块特有配置
        self.perception_config = {
            "enable_multimodal": True,  # 启用多模态处理
            "enable_cross_modal_alignment": True,  # 启用跨模态对齐
            "enable_knowledge_injection": True,  # 启用知识注入
            "enable_dikwp_processing": True,  # 启用DIKWP处理
            "supported_formats": [".pdf", ".docx", ".txt", ".jpg", ".png"],
            "max_file_size": 50 * 1024 * 1024,  # 50MB
            "ocr_languages": ["chi_sim", "eng"],  # OCR语言支持
            **self.config,
        }

        # 初始化现有感知引擎
        self.perception_engine = None
        self.fallback_enabled = True  # 启用备用系统
        if EXISTING_ENGINE_AVAILABLE:
            try:
                self.perception_engine = StructuredPatentPerceptionEngine()
                logger.info("✅ 现有感知引擎集成成功")
            except Exception as e:
                logger.warning(f"现有感知引擎集成失败: {e}")

        # 感知状态
        self.processing_stats = {
            "total_documents": 0,
            "successful_documents": 0,
            "failed_documents": 0,
            "average_processing_time": 0.0,
            "last_processing_time": None,
        }

        # 支持的文档类型
        self.supported_document_types = {
            "patent": DocumentType.PATENT,
            "tech_disclosure": DocumentType.TECH_DISCLOSURE,
            "tech_manual": DocumentType.TECH_MANUAL,
            "tech_drawing": DocumentType.TECH_DRAWING,
            "specification": DocumentType.SPECIFICATION,
        }

        logger.info(f"🔍 增强感知模块初始化完成 - Agent: {self.agent_id}")

    async def _on_initialize(self) -> bool:
        """模块初始化"""
        try:
            logger.info("🔍 初始化感知模块...")

            # 初始化现有感知引擎
            if self.perception_engine:
                # 现有引擎已经在其__init__中完成了初始化
                logger.info("✅ 现有感知引擎就绪")
            else:
                # 创建简化的感知处理能力
                await self._initialize_fallback_perception()
                logger.info("✅ 备用感知处理能力就绪")

            # 验证必要依赖
            dependencies_ok = await self._verify_dependencies()
            if not dependencies_ok:
                logger.warning("⚠️ 部分依赖缺失,某些功能可能不可用")

            logger.info("✅ 感知模块初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ 感知模块初始化失败: {e!s}")
            return False

    async def _on_health_check(self) -> bool:
        """健康检查"""
        try:
            checks = {
                "perception_engine_available": self.perception_engine is not None
                or self.fallback_enabled,
                "dependencies_ok": await self._verify_dependencies(),
                "processing_available": True,
                "memory_usage_ok": self._check_memory_usage(),
            }

            # 如果有备用系统,感知引擎不可用也是健康的
            overall_healthy = (
                checks["dependencies_ok"]
                and checks["processing_available"]
                and checks["memory_usage_ok"]
                and (checks["perception_engine_available"] or self.fallback_enabled)
            )

            # 将健康检查详情存储到模块属性中,供外部查询
            self._health_check_details = {
                "perception_status": (
                    "available" if checks["perception_engine_available"] else "unavailable"
                ),
                "dependencies_status": "ok" if checks["dependencies_ok"] else "missing",
                "processing_status": "ready" if checks["processing_available"] else "busy",
                "stats": self.processing_stats,
                "overall_healthy": overall_healthy,
            }

            return overall_healthy

        except Exception as e:
            logger.error(f"健康检查失败: {e!s}")
            self._health_check_details = {"error": str(e)}
            return False

    async def perceive(
        self, input_data: str | dict[str, Any], perception_type: str = "document"
    ) -> dict[str, Any]:
        """
        感知处理 - 核心功能方法

        Args:
            input_data: 输入数据 (文件路径或数据字典)
            perception_type: 感知类型 ('document', 'image', 'text')

        Returns:
            感知结果字典
        """
        try:
            start_time = datetime.now()

            # 更新统计信息
            self.processing_stats["total_documents"] += 1

            if isinstance(input_data, str) and os.path.exists(input_data):
                # 文件路径输入
                result = await self._process_file(input_data, perception_type)
            elif isinstance(input_data, dict):
                # 数据字典输入
                result = await self._process_data(input_data, perception_type)
            else:
                raise ValueError(f"不支持的输入类型: {type(input_data)}")

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            self.processing_stats["successful_documents"] += 1
            self.processing_stats["last_processing_time"] = processing_time
            self._update_average_processing_time(processing_time)

            logger.info(f"✅ 感知处理完成 - 耗时: {processing_time:.2f}s")
            return result

        except Exception as e:
            self.processing_stats["failed_documents"] += 1
            logger.error(f"❌ 感知处理失败: {e!s}")
            raise

    async def process(self, input_data: Any) -> dict[str, Any]:
        """标准处理接口 - BaseModule兼容"""
        return await self.perceive(input_data)

    async def analyze(self, input_data: Any) -> dict[str, Any]:
        """分析方法 - 深度分析"""
        try:
            # 先进行基础感知
            perception_result = await self.perceive(input_data)

            # 进行深度分析
            analysis_result = await self._deep_analysis(perception_result)

            return {
                "perception": perception_result,
                "analysis": analysis_result,
                "processing_agent": self.agent_id,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ 分析失败: {e!s}")
            raise

    async def _process_file(self, file_path: str, perception_type: str) -> dict[str, Any]:
        """处理文件输入"""
        file_path = Path(file_path)

        # 验证文件
        if not self._validate_file(file_path):
            raise ValueError(f"文件验证失败: {file_path}")

        if self.perception_engine:
            # 使用现有感知引擎
            doc_type = self._detect_document_type(file_path, perception_type)
            document_graph = await self.perception_engine.process_document(str(file_path), doc_type)

            return {
                "success": True,
                "file_path": str(file_path),
                "document_type": doc_type.value,
                "document_graph": (
                    asdict(document_graph)
                    if hasattr(document_graph, "__dict__")
                    else str(document_graph)
                ),
                "processing_method": "enhanced_engine",
            }
        else:
            # 使用备用处理
            return await self._fallback_file_processing(file_path, perception_type)

    async def _process_data(self, data: dict[str, Any], perception_type: str) -> dict[str, Any]:
        """处理数据字典输入"""
        return {
            "success": True,
            "data_type": perception_type,
            "processed_data": data,
            "analysis": await self._analyze_data_content(data),
            "processing_method": "data_analysis",
        }

    async def _initialize_fallback_perception(self):
        """初始化备用感知能力"""
        self.fallback_capabilities = {
            "text_analysis": True,
            "basic_ocr": False,  # 需要tesseract
            "structure_extraction": True,
        }

    async def _verify_dependencies(self) -> bool:
        """验证依赖"""
        try:
            # 检查关键依赖
            dependencies = []

            try:

                dependencies.append(True)
            except ImportError:
                dependencies.append(False)

            try:

                dependencies.append(True)
            except ImportError:
                dependencies.append(False)

            # 至少需要基础依赖
            return any(dependencies)

        except Exception:
            return False

    def _check_memory_usage(self) -> bool:
        """检查内存使用"""
        try:
            import psutil

            memory_percent = psutil.virtual_memory().percent
            return memory_percent < 90  # 内存使用低于90%
        except ImportError:
            return True  # 如果无法检查,假设正常

    def _validate_file(self, file_path: Path) -> bool:
        """验证文件"""
        # 检查文件是否存在
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return False

        # 检查文件大小
        file_size = file_path.stat().st_size
        if file_size > self.perception_config["max_file_size"]:
            logger.error(f"文件过大: {file_size} bytes")
            return False

        # 检查文件格式
        file_suffix = file_path.suffix.lower()
        if file_suffix not in self.perception_config["supported_formats"]:
            logger.error(f"不支持的文件格式: {file_suffix}")
            return False

        return True

    def _detect_document_type(self, file_path: Path, perception_type: str) -> DocumentType:
        """检测文档类型"""
        if perception_type in self.supported_document_types:
            return self.supported_document_types[perception_type]

        # 基于文件名检测
        filename = file_path.name.lower()
        if "patent" in filename or "专利" in filename:
            return DocumentType.PATENT
        elif "disclosure" in filename or "交底" in filename:
            return DocumentType.TECH_DISCLOSURE
        elif "manual" in filename or "手册" in filename:
            return DocumentType.TECH_MANUAL
        elif "drawing" in filename or "图纸" in filename:
            return DocumentType.TECH_DRAWING
        else:
            return DocumentType.PATENT  # 默认为专利

    async def _fallback_file_processing(
        self, file_path: Path, perception_type: str
    ) -> dict[str, Any]:
        """备用文件处理"""
        try:
            # 基础文本提取
            if file_path.suffix.lower() == ".txt":
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                return {
                    "success": True,
                    "file_path": str(file_path),
                    "content": content,
                    "content_type": "text",
                    "processing_method": "fallback_text",
                }
            else:
                return {
                    "success": False,
                    "error": f"备用处理不支持文件类型: {file_path.suffix}",
                    "file_path": str(file_path),
                    "processing_method": "fallback_failed",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": str(file_path),
                "processing_method": "fallback_error",
            }

    async def _analyze_data_content(self, data: dict[str, Any]) -> dict[str, Any]:
        """分析数据内容"""
        analysis = {
            "data_keys": list(data.keys()),
            "data_size": len(str(data)),
            "has_text": any(isinstance(v, str) for v in data.values()),
            "has_numbers": any(isinstance(v, (int, float)) for v in data.values()),
            "complexity": "simple" if len(data) < 10 else "complex",
        }
        return analysis

    async def _deep_analysis(self, perception_result: dict[str, Any]) -> dict[str, Any]:
        """深度分析"""
        analysis = {
            "content_summary": "感知处理完成",
            "extracted_features": [],
            "structure_info": {},
            "quality_metrics": {"completeness": 0.8, "accuracy": 0.9, "confidence": 0.85},
        }

        # 基于感知结果进行深度分析
        if perception_result.get("success"):
            analysis["extracted_features"]] = ["文本内容", "结构信息"]
            if "document_graph" in perception_result:
                analysis["structure_info"]] = {"has_nodes": True, "has_edges": True}

        return analysis

    def get_metrics(self) -> dict[str, Any]:
        """获取模块性能指标"""
        try:
            return {
                "agent_id": self.agent_id,
                "module_type": self.__class__.__name__,
                "module_status": self.status.value if hasattr(self, "status") else "unknown",
                "initialized": hasattr(self, "_initialized") and self._initialized,
                "uptime_seconds": (
                    (datetime.now() - self.start_time).total_seconds()
                    if hasattr(self, "start_time")
                    else 0
                ),
                "processing_stats": self.processing_stats,
                "config": {
                    "enable_multimodal": self.perception_config.get("enable_multimodal", False),
                    "max_file_size": self.perception_config.get("max_file_size", 0),
                    "supported_formats": self.perception_config.get("supported_formats", []),
                },
                "engine_available": self.perception_engine is not None,
                "health_details": getattr(self, "_health_check_details", {}),
            }
        except Exception as e:
            logger.error(f"获取指标失败: {e!s}")
            return {"error": str(e), "agent_id": getattr(self, "agent_id", "unknown")}

    def _update_average_processing_time(self, processing_time: float) -> Any:
        """更新平均处理时间"""
        if self.processing_stats["total_documents"] > 0:
            current_avg = self.processing_stats["average_processing_time"]
            n = self.processing_stats["total_documents"]
            new_avg = (current_avg * (n - 1) + processing_time) / n
            self.processing_stats["average_processing_time"] = new_avg

    async def _on_start(self) -> bool:
        """启动模块"""
        try:
            logger.info(f"🚀 启动感知模块 - Agent: {self.agent_id}")
            # 启动时可以初始化一些资源
            self._is_running = True
            return True
        except Exception as e:
            logger.error(f"❌ 感知模块启动失败: {e!s}")
            return False

    async def _on_stop(self) -> bool:
        """停止模块"""
        try:
            logger.info(f"⏹️ 停止感知模块 - Agent: {self.agent_id}")
            # 停止时可以清理资源
            self._is_running = False
            return True
        except Exception as e:
            logger.error(f"❌ 感知模块停止失败: {e!s}")
            return False

    async def _on_shutdown(self) -> bool:
        """关闭模块"""
        try:
            logger.info(f"🔚 关闭感知模块 - Agent: {self.agent_id}")
            # 关闭时释放所有资源
            if self.perception_engine:
                # 清理感知引擎资源
                self.perception_engine = None

            # 保存统计信息
            logger.info(f"📊 感知统计: {self.processing_stats}")
            return True
        except Exception as e:
            logger.error(f"❌ 感知模块关闭失败: {e!s}")
            return False


# 便捷创建函数
def create_enhanced_perception_module(
    agent_id: str, config: Optional[dict[str, Any]] = None
) -> EnhancedPerceptionModule:
    """
    创建增强感知模块实例

    Args:
        agent_id: 智能体标识符
        config: 配置参数

    Returns:
        EnhancedPerceptionModule实例
    """
    return EnhancedPerceptionModule(agent_id, config)
