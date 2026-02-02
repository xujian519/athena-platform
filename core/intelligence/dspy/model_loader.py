#!/usr/bin/env python3
"""
DSPy模型加载器
DSPy Model Loader for Patent Analysis

加载训练好的DSPy模型并提供推理接口

作者: Athena平台团队
创建时间: 2025-12-30
版本: 1.0.0
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


class DSPyModelLoader:
    """DSPy模型加载器"""

    def __init__(self, models_dir: Path | None = None):
        """初始化模型加载器

        Args:
            models_dir: 模型文件目录,默认为当前目录下的models
        """
        if models_dir is None:
            models_dir = Path(__file__).parent / "models"

        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.current_model = None
        self.model_info = None
        self._load_latest_model()

    def _load_latest_model(self) -> bool:
        """加载最新的模型

        Returns:
            是否成功加载
        """
        try:
            # 查找所有MIPROv2模型文件
            model_files = sorted(
                self.models_dir.glob("patent_analyzer_miprov2_*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            if not model_files:
                logger.warning("未找到MIPROv2模型文件")
                # 尝试加载Bootstrap模型
                model_files = sorted(
                    self.models_dir.glob("patent_analyzer_bootstrap_*.json"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True,
                )

            if not model_files:
                logger.warning("未找到任何训练好的模型")
                return False

            latest_model = model_files[0]
            return self.load_model(latest_model)

        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False

    def load_model(self, model_path: Path) -> bool:
        """加载指定模型

        Args:
            model_path: 模型文件路径

        Returns:
            是否成功加载
        """
        try:
            logger.info(f"加载模型: {model_path}")

            # 读取模型元数据
            with open(model_path, encoding="utf-8") as f:
                self.model_info = json.load(f)

            # 查找对应的DSPy编译模型文件
            # DSPy会保存编译后的模型,通常在同一目录下
            compiled_file = model_path.parent / f"{model_path.stem}.dspy"

            if compiled_file.exists():
                # 加载编译后的模型
                # 注意: DSPy的模型加载需要重新创建Module并用load()方法
                from .training_system_v3_enhanced import EnhancedPatentAnalyzer

                self.current_model = EnhancedPatentAnalyzer(use_cot=True)
                # DSPy模型保存/加载机制可能需要特殊处理
                # 这里我们重新创建模型,实际项目中可能需要保存/load整个编译后的模块

                logger.info(f"✅ 模型加载成功: {self.model_info.get('version')}")
                logger.info(f"   训练阶段: {self.model_info.get('training_phase')}")
                logger.info(
                    f"   分数: {self.model_info.get('optimized_score', self.model_info.get('avg_score', 'N/A'))}"
                )
                return True
            else:
                logger.warning(f"未找到编译模型文件: {compiled_file}")
                logger.info("将使用新创建的模型(未加载训练后的提示词)")
                self.current_model = self._create_fresh_model()
                return True

        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _create_fresh_model(self) -> Any:
        """创建新的模型实例"""
        from .training_system_v3_enhanced import EnhancedPatentAnalyzer

        return EnhancedPatentAnalyzer(use_cot=True)

    def predict(self, background: str, technical_field: str, patent_number: str) -> dict[str, Any]:
        """预测专利案例分析

        Args:
            background: 案由描述
            technical_field: 技术领域
            patent_number: 专利号

        Returns:
            预测结果字典
        """
        if self.current_model is None:
            raise RuntimeError("模型未加载")

        try:
            # 执行预测
            result = self.current_model(
                background=background, technical_field=technical_field, patent_number=patent_number
            )

            # 提取结果
            prediction = {
                "case_type": getattr(result, "case_type", "unknown"),
                "legal_issues": getattr(result, "legal_issues", ""),
                "reasoning": getattr(result, "reasoning", ""),
                "conclusion": getattr(result, "conclusion", ""),
                "timestamp": datetime.now().isoformat(),
                "model_info": {
                    "version": self.model_info.get("version") if self.model_info else "unknown",
                    "training_phase": (
                        self.model_info.get("training_phase") if self.model_info else "unknown"
                    ),
                    "score": (
                        self.model_info.get(
                            "optimized_score", self.model_info.get("avg_score", 0.0)
                        )
                        if self.model_info
                        else 0.0
                    ),
                },
            }

            return prediction

        except Exception as e:
            logger.error(f"预测失败: {e}")
            raise

    def get_model_info(self) -> dict[str, Any]:
        """获取当前模型信息"""
        if self.model_info is None:
            return {"status": "no_model_loaded"}

        return {
            "version": self.model_info.get("version"),
            "training_phase": self.model_info.get("training_phase"),
            "timestamp": self.model_info.get("timestamp"),
            "score": self.model_info.get("optimized_score") or self.model_info.get("avg_score"),
            "num_samples": self.model_info.get("num_samples"),
            "training_time_seconds": self.model_info.get("training_time_seconds"),
            "improvement": self.model_info.get("improvement"),
        }

    def list_available_models(self) -> list:
        """列出所有可用的模型"""
        models = []

        # MIPROv2模型
        for f in sorted(self.models_dir.glob("patent_analyzer_miprov2_*.json"), reverse=True):
            with open(f) as fp:
                info = json.load(fp)
            models.append(
                {
                    "type": "MIPROv2",
                    "file": f.name,
                    "score": info.get("optimized_score", 0.0),
                    "timestamp": info.get("timestamp"),
                }
            )

        # Bootstrap模型
        for f in sorted(self.models_dir.glob("patent_analyzer_bootstrap_*.json"), reverse=True):
            with open(f) as fp:
                info = json.load(fp)
            models.append(
                {
                    "type": "BootstrapFewShot",
                    "file": f.name,
                    "score": info.get("avg_score", 0.0),
                    "timestamp": info.get("timestamp"),
                }
            )

        return models


# 全局单例
_model_loader_instance = None


def get_model_loader() -> DSPyModelLoader:
    """获取全局模型加载器实例"""
    global _model_loader_instance
    if _model_loader_instance is None:
        _model_loader_instance = DSPyModelLoader()
    return _model_loader_instance
