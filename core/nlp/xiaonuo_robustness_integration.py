#!/usr/bin/env python3
from __future__ import annotations
"""
小诺鲁棒性模块集成器
Xiaonuo Robustness Module Integration

将所有Phase 5鲁棒性模块集成到统一接口中

功能:
1. 集成模糊输入预处理
2. 集成噪声处理
3. 集成多语言支持
4. 集成容错机制
5. 集成输入验证和安全检查

作者: 小诺AI团队
日期: 2025-12-18
"""

import json
import os
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.logging_config import setup_logging

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入Phase 5模块
from xiaonuo_fault_tolerance import ErrorType, FaultToleranceManager
from xiaonuo_fuzzy_input_preprocessor import FuzzyInputPreprocessor, InputQualityLevel
from xiaonuo_input_validator import InputValidator, ThreatLevel, ValidationLevel, ValidationStatus
from xiaonuo_multilingual_processor import MultilingualProcessor
from xiaonuo_noise_processor import NoiseProcessor

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class RobustnessConfig:
    """鲁棒性配置"""

    enable_fuzzy_preprocessing: bool = True
    enable_noise_processing: bool = True
    enable_multilingual: bool = True
    enable_fault_tolerance: bool = True
    enable_validation: bool = True

    # 详细配置
    preprocessing_quality_threshold: float = 0.3
    noise_aggressive_mode: bool = False
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    auto_degradation: bool = True
    max_processing_time: float = 5.0  # 秒


@dataclass
class RobustnessResult:
    """鲁棒性处理结果"""

    original_input: str
    processed_input: str
    quality_assessment: dict[str, Any]
    processing_stages: list[dict[str, Any]]
    security_analysis: dict[str, Any]
    performance_metrics: dict[str, Any]
    warnings: list[str]
    errors: list[str]
    processing_time_ms: float
    degradation_applied: bool
    final_status: str


class RobustnessManager:
    """鲁棒性管理器"""

    def __init__(self, config: RobustnessConfig | None = None):
        """初始化鲁棒性管理器"""
        self.config = config if config is not None else RobustnessConfig()

        # 初始化各模块
        self.fuzzy_preprocessor = FuzzyInputPreprocessor()
        self.noise_processor = NoiseProcessor()
        self.multilingual_processor = MultilingualProcessor()
        self.fault_tolerance_manager = FaultToleranceManager()
        self.input_validator = InputValidator(self.config.validation_level)

        # 设置容错机制
        self._setup_fault_tolerance()

        # 处理统计
        self.processing_stats: dict[str, Any] = {
            "total_processed": 0,
            "successful_processing": 0,
            "degradation_applied": 0,
            "security_blocked": 0,
            "avg_processing_time": 0.0,
            "quality_distribution": {},
            "threat_distribution": {},
        }

        # 缓存
        self.processing_cache: dict[str, RobustnessResult] = {}
        self.cache_lock = threading.Lock()

        logger.info("🚀 鲁棒性管理器初始化完成")

    def _setup_fault_tolerance(self) -> Any:
        """设置容错机制"""
        # 注册降级策略
        self.fault_tolerance_manager.register_degradation_strategy(
            ErrorType.PROCESSING_ERROR, self._degrade_processing
        )

        self.fault_tolerance_manager.register_degradation_strategy(
            ErrorType.TIMEOUT_ERROR, self._timeout_fallback
        )

        # 注册重试配置
        from xiaonuo_fault_tolerance import RetryConfig

        self.fault_tolerance_manager.register_retry_config(
            "robustness_processing", RetryConfig(max_attempts=3, base_delay=0.1)
        )

        # 注册健康检查
        self.fault_tolerance_manager.register_health_check("robustness_modules", self._health_check)

    def process_input(
        self, input_text: str, context: Optional[dict[str, Any]] = None
    ) -> RobustnessResult:
        """处理输入(集成所有鲁棒性功能)"""
        start_time = datetime.now()
        processing_stages: list[dict[str, Any]] = []
        warnings: list[str] = []
        errors: list[str] = []
        quality_assessment: dict[str, Any] = {}
        security_analysis: dict[str, Any] = {}
        degradation_applied = False

        # 初始化变量避免未绑定错误
        processed_text = input_text
        validation_result = None

        try:
            # 检查缓存
            cache_key = self._get_cache_key(input_text, context)
            if cache_key in self.processing_cache:
                cached_result = self.processing_cache[cache_key]
                cached_result.processing_time_ms = (
                    datetime.now() - start_time
                ).total_seconds() * 1000
                return cached_result

            # 阶段1: 输入验证和安全检查
            if self.config.enable_validation:
                validation_result = self._validate_input(input_text, context)
                processing_stages.append(
                    {
                        "stage": "validation",
                        "status": validation_result.status.value,
                        "threat_level": validation_result.threat_level.value,
                        "issues_count": len(validation_result.issues),
                        "warnings_count": len(validation_result.warnings),
                    }
                )

                if validation_result.status == ValidationStatus.BLOCKED:
                    self.processing_stats["security_blocked"] += 1
                    return self._create_blocked_result(input_text, validation_result, start_time)

                warnings.extend(validation_result.warnings)
                security_analysis = {
                    "status": validation_result.status.value,
                    "threat_level": validation_result.threat_level.value,
                    "security_issues": [
                        {
                            "type": threat.threat_type,
                            "description": threat.description,
                            "severity": threat.severity.value,
                        }
                        for threat in validation_result.security_issues
                    ],
                }

            # 阶段2: 模糊输入预处理
            if self.config.enable_fuzzy_preprocessing:
                preprocessing_result = self._preprocess_input(processed_text)
                processing_stages.append(
                    {
                        "stage": "preprocessing",
                        "quality_level": preprocessing_result.quality_level.value,
                        "quality_score": preprocessing_result.quality_score,
                        "input_type": preprocessing_result.input_type.value,
                    }
                )

                quality_assessment = {
                    "quality_level": preprocessing_result.quality_level.value,
                    "quality_score": preprocessing_result.quality_score,
                    "input_type": preprocessing_result.input_type.value,
                    "issues": preprocessing_result.issues,
                }

                # 质量过低则使用降级策略
                if (
                    preprocessing_result.quality_score < self.config.preprocessing_quality_threshold
                    and self.config.auto_degradation
                ):
                    processed_text = self._apply_quality_degradation(preprocessing_result)
                    degradation_applied = True
                else:
                    processed_text = preprocessing_result.standardized_text

            # 阶段3: 噪声处理
            if self.config.enable_noise_processing:
                noise_result = self._process_noise(processed_text)
                processing_stages.append(
                    {
                        "stage": "noise_processing",
                        "noise_types_detected": [nt.value for nt in noise_result.noise_types],
                        "noise_ratio": noise_result.noise_ratio,
                        "cleanable": noise_result.cleanable,
                    }
                )

                processed_text = (
                    noise_result.cleaned_text if noise_result.cleanable else processed_text
                )

            # 阶段4: 多语言处理
            if self.config.enable_multilingual:
                language_result = self._process_multilingual(processed_text)
                processing_stages.append(
                    {
                        "stage": "multilingual",
                        "primary_language": language_result.primary_language.value,
                        "confidence": language_result.confidence,
                        "is_mixed": language_result.is_code_switched,
                        "dialects": [(d.value, s) for d, s in language_result.dialects],
                    }
                )

                # 标准化混合语言
                if language_result.is_code_switched:
                    processed_text = self.multilingual_processor.normalize_mixed_text(
                        processed_text, language_result.primary_language
                    )

            # 性能指标
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            performance_metrics = {
                "total_time_ms": processing_time,
                "stages_completed": len(processing_stages),
                "degradation_applied": degradation_applied,
                "cache_hit": False,
            }

            # 最终状态
            final_status = self._determine_final_status(
                validation_result if self.config.enable_validation else None,
                quality_assessment,
                security_analysis,
            )

            # 构建结果
            result = RobustnessResult(
                original_input=input_text,
                processed_input=processed_text,
                quality_assessment=quality_assessment,
                processing_stages=processing_stages,
                security_analysis=security_analysis,
                performance_metrics=performance_metrics,
                warnings=warnings,
                errors=errors,
                processing_time_ms=processing_time,
                degradation_applied=degradation_applied,
                final_status=final_status,
            )

            # 更新统计
            self._update_stats(result)

            # 缓存结果(仅缓存成功的结果)
            if final_status in ["success", "warning"]:
                with self.cache_lock:
                    if len(self.processing_cache) < 1000:
                        self.processing_cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"❌ 鲁棒性处理失败: {e}")
            errors.append(f"处理异常: {e!s}")

            # 使用容错机制
            if self.config.enable_fault_tolerance:
                try:
                    fallback_result = self.fault_tolerance_manager.execute_with_fallback(
                        lambda: self._simple_fallback(input_text),
                        lambda: {"text": input_text, "status": "fallback"},
                    )
                    processed_text = fallback_result.get("text", input_text)
                except Exception:
                    processed_text = input_text

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return RobustnessResult(
                original_input=input_text,
                processed_input=processed_text or input_text,
                quality_assessment={},
                processing_stages=processing_stages,
                security_analysis={},
                performance_metrics={"total_time_ms": processing_time},
                warnings=warnings,
                errors=errors,
                processing_time_ms=processing_time,
                degradation_applied=True,
                final_status="error",
            )

    def _validate_input(self, text: str, context: Optional[dict[str, Any]] = None) -> Any:
        """验证输入"""
        return self.input_validator.validate_input(text, context)

    def _preprocess_input(self, text: str) -> Any:
        """预处理输入"""
        return self.fuzzy_preprocessor.preprocess(text)

    def _process_noise(self, text: str) -> Any:
        """处理噪声"""
        return self.noise_processor.clean_noise(text, self.config.noise_aggressive_mode)

    def _process_multilingual(self, text: str) -> Any:
        """处理多语言"""
        return self.multilingual_processor.detect_language(text)

    def _apply_quality_degradation(self, preprocessing_result: Any) -> str:
        """应用质量降级"""
        # 简单的降级策略:返回清理后的文本
        if preprocessing_result.cleaned_text:
            return preprocessing_result.cleaned_text
        else:
            return preprocessing_result.original_text[:100]  # 截断

    def _degrade_processing(self, context: dict[str, Any]) -> dict[str, Any]:
        """处理降级策略"""
        return {
            "text": context.get("original_input", ""),
            "status": "degraded",
            "message": "处理降级,返回简化结果",
        }

    def _timeout_fallback(self, context: dict[str, Any]) -> dict[str, Any]:
        """超时降级"""
        return {
            "text": context.get("original_input", ""),
            "status": "timeout",
            "message": "处理超时",
        }

    def _health_check(self) -> Any:
        """健康检查"""
        return {
            "status": "healthy",
            "modules": {
                "preprocessor": "ok",
                "noise_processor": "ok",
                "multilingual": "ok",
                "validator": "ok",
                "fault_tolerance": "ok",
            },
        }

    def _simple_fallback(self, input_text: str) -> Any:
        """简单降级处理"""
        return {"text": input_text, "status": "simple"}

    def _determine_final_status(
        self,
        validation_result: Any,
        quality_assessment: dict[str, Any],        security_analysis: dict[str, Any],    ) -> str:
        """确定最终状态"""
        # 安全问题
        if validation_result:
            if validation_result.status == ValidationStatus.INVALID:
                return "blocked"
            elif validation_result.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                return "security_warning"

        # 质量问题
        if quality_assessment:
            quality_level = quality_assessment.get("quality_level")
            if quality_level in [InputQualityLevel.POOR.value, InputQualityLevel.INVALID.value]:
                return "quality_warning"
            elif quality_level == InputQualityLevel.FAIR.value:
                return "quality_caution"

        return "success"

    def _create_blocked_result(
        self, input_text: str, validation_result: Any, start_time: datetime
    ) -> RobustnessResult:
        """创建被阻止的结果"""
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return RobustnessResult(
            original_input=input_text,
            processed_input="",  # 不返回任何内容
            quality_assessment={},
            processing_stages=[
                {"stage": "validation", "status": "blocked", "issues": validation_result.issues}
            ],
            security_analysis={
                "status": "blocked",
                "threat_level": validation_result.threat_level.value,
                "security_issues": validation_result.security_issues,
            },
            performance_metrics={"total_time_ms": processing_time},
            warnings=validation_result.warnings,
            errors=validation_result.issues,
            processing_time_ms=processing_time,
            degradation_applied=False,
            final_status="blocked",
        )

    def _get_cache_key(self, text: str, context: Optional[dict[str, Any]] = None) -> str:
        """生成缓存键"""
        import hashlib

        content = text + json.dumps(context or {}, sort_keys=True)
        return hashlib.md5(content.encode("utf-8", usedforsecurity=False), usedforsecurity=False).hexdigest()[:16]

    def _update_stats(self, result: RobustnessResult) -> Any:
        """更新统计"""
        self.processing_stats["total_processed"] += 1

        if result.final_status == "success":
            self.processing_stats["successful_processing"] += 1

        if result.degradation_applied:
            self.processing_stats["degradation_applied"] += 1

        # 更新平均处理时间
        current_avg = self.processing_stats["avg_processing_time"]
        count = self.processing_stats["total_processed"]
        self.processing_stats["avg_processing_time"] = (
            current_avg * (count - 1) + result.processing_time_ms
        ) / count

        # 更新质量分布
        quality = result.quality_assessment.get("quality_level", "unknown")
        self.processing_stats["quality_distribution"][quality] = (
            self.processing_stats["quality_distribution"].get(quality, 0) + 1
        )

        # 更新威胁分布
        threat = result.security_analysis.get("threat_level", "none")
        self.processing_stats["threat_distribution"][threat] = (
            self.processing_stats["threat_distribution"].get(threat, 0) + 1
        )

    def batch_process(
        self, inputs: list[str], context: Optional[dict[str, Any]] = None
    ) -> list[RobustnessResult]:
        """批量处理"""
        return [self.process_input(text, context) for text in inputs]

    def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        # 获取各模块状态
        preprocessor_stats = self.fuzzy_preprocessor.get_processing_stats()
        noise_stats = self.noise_processor.get_processing_stats()
        multilingual_stats = self.multilingual_processor.get_processing_stats()
        fault_tolerance_stats = self.fault_tolerance_manager.get_system_health()
        validation_stats = self.input_validator.get_validation_stats()

        # 计算整体健康分数
        health_score = self._calculate_health_score()

        return {
            "overall_health": health_score,
            "processing_stats": self.processing_stats,
            "module_stats": {
                "preprocessor": preprocessor_stats,
                "noise_processor": noise_stats,
                "multilingual": multilingual_stats,
                "fault_tolerance": fault_tolerance_stats,
                "validator": validation_stats,
            },
            "cache_size": len(self.processing_cache),
            "config": {
                "fuzzy_preprocessing": self.config.enable_fuzzy_preprocessing,
                "noise_processing": self.config.enable_noise_processing,
                "multilingual": self.config.enable_multilingual,
                "fault_tolerance": self.config.enable_fault_tolerance,
                "validation": self.config.enable_validation,
            },
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_health_score(self) -> float:
        """计算健康分数"""
        score = 100.0

        # 成功率影响
        if self.processing_stats["total_processed"] > 0:
            success_rate = (
                self.processing_stats["successful_processing"]
                / self.processing_stats["total_processed"]
            )
            score = score * success_rate

        # 降级率影响
        if self.processing_stats["total_processed"] > 0:
            degradation_rate = (
                self.processing_stats["degradation_applied"]
                / self.processing_stats["total_processed"]
            )
            score = score * (1 - degradation_rate * 0.5)

        # 安全阻止率影响(过多阻止表示过于严格)
        if self.processing_stats["total_processed"] > 0:
            block_rate = (
                self.processing_stats["security_blocked"] / self.processing_stats["total_processed"]
            )
            if block_rate > 0.1:  # 超过10%的阻止率
                score = score * 0.9

        return max(0.0, min(100.0, score))

    def clear_cache(self) -> None:
        """清理缓存"""
        with self.cache_lock:
            self.processing_cache.clear()
        logger.info("🧹 鲁棒性处理缓存已清理")

    def update_config(self, new_config: RobustnessConfig) -> None:
        """更新配置"""
        self.config = new_config
        self.input_validator = InputValidator(new_config.validation_level)
        logger.info("🔧 鲁棒性配置已更新")


# 使用示例
if __name__ == "__main__":
    print("🧪 测试鲁棒性模块集成器...")

    # 创建鲁棒性管理器
    config = RobustnessConfig(
        enable_fuzzy_preprocessing=True,
        enable_noise_processing=True,
        enable_multilingual=True,
        enable_fault_tolerance=True,
        enable_validation=True,
        validation_level=ValidationLevel.STANDARD,
    )

    manager = RobustnessManager(config)

    # 测试输入
    test_inputs = [
        "正常输入:帮我查询人工智能的发展历史",  # 正常输入
        "Hello 世界!这是一个 mixed language 的测试",  # 混合语言
        "包含噪声的输入!!!????   \t\n",  # 噪声输入
        "包含<script>alert('xss')</script>的恶意输入",  # XSS攻击
        "SELECT * FROM users WHERE id = 1 OR 1=1",  # SQL注入
        "雷猴,我想查嘢",  # 方言
        "",  # 空输入
        "a" * 1000,  # 长输入
        "包含零宽字符\u200b的输入",  # 零宽字符
        "URL编码的输入:%E4%B8%AD%E6%96%87",  # URL编码
    ]

    for i, text in enumerate(test_inputs):
        print(f"\n📝 测试 {i+1}: {text[:50]!r}")

        result = manager.process_input(text)

        print(f"   最终状态: {result.final_status}")
        print(f"   处理时间: {result.processing_time_ms:.1f}ms")
        print(f"   降级应用: {'是' if result.degradation_applied else '否'}")

        if result.processing_stages:
            print(
                f"   处理阶段: {', '.join([stage['stage'] for stage in result.processing_stages])}"
            )

        if result.warnings:
            print(f"   警告: {', '.join(result.warnings[:2])}")

        if result.errors:
            print(f"   错误: {', '.join(result.errors[:2])}")

        if result.quality_assessment:
            quality = result.quality_assessment
            print(
                f"   质量评估: {quality.get('quality_level', 'unknown')} "
                f"({quality.get('quality_score', 0):.2f})"
            )

        if result.security_analysis:
            security = result.security_analysis
            print(
                f"   安全分析: {security.get('status', 'unknown')} "
                f"(威胁: {security.get('threat_level', 'unknown')})"
            )

        if result.processed_input != result.original_input:
            print(f"   处理后: {result.processed_input[:50]!r}")

    # 显示系统状态
    print("\n📊 系统状态:")
    status = manager.get_system_status()
    print(f"   整体健康分数: {status['overall_health']:.1f}")
    print(f"   总处理数: {status['processing_stats']['total_processed']}")
    print(f"   成功处理: {status['processing_stats']['successful_processing']}")
    print(f"   降级应用: {status['processing_stats']['degradation_applied']}")
    print(f"   安全阻止: {status['processing_stats']['security_blocked']}")
    print(f"   平均处理时间: {status['processing_stats']['avg_processing_time']:.1f}ms")

    print("\n✅ 鲁棒性模块集成器测试完成!")
