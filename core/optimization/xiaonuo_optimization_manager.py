#!/usr/bin/env python3
from __future__ import annotations
"""
小诺优化管理器
Xiaonuo Optimization Manager

统一管理从Athena提取的三大优化能力:
1. 轻量级工具发现 - 优化工具选择
2. 轻量级参数验证 - 实时参数验证
3. 轻量级错误预测 - 预测性错误检测

提供统一的API接口和配置管理,简化小诺的集成。

作者: Athena平台团队
创建时间: 2025-12-27
版本: v1.0.0
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# 导入监控模块
try:
    from core.monitoring.optimization_monitor import OptimizationMonitor, get_optimization_monitor
except ImportError:
    OptimizationMonitor = None
    logger.warning("监控模块导入失败")


# 导入三个轻量级模块
try:
    from core.tools.enhanced_tool_discovery_module import LightweightToolDiscovery, SemanticMatch
except ImportError:
    LightweightToolDiscovery = None
    logger.warning("工具发现模块导入失败")

try:
    from core.validation.realtime_validator_module import (
        LightweightRealtimeValidator,
        ParameterSchema,
        ValidationResult,
    )
except ImportError:
    LightweightRealtimeValidator = None
    logger.warning("参数验证模块导入失败")

try:
    from core.prediction.enhanced_predictor_module import (
        ErrorPattern,
        LightweightErrorPredictor,
        PredictionResult,
        RiskLevel,
    )
except ImportError:
    LightweightErrorPredictor = None
    logger.warning("错误预测模块导入失败")


@dataclass
class OptimizationConfig:
    """优化配置"""

    # 是否启用各模块
    enable_tool_discovery: bool = True
    enable_parameter_validation: bool = True
    enable_error_prediction: bool = True

    # 工具发现配置
    tool_discovery_config: dict | None = None

    # 参数验证配置
    validation_config: dict | None = None

    # 错误预测配置
    prediction_config: dict | None = None

    # 降级策略
    fallback_on_error: bool = True

    # 监控配置
    enable_monitoring: bool = True
    monitoring_config: dict | None = None

    @classmethod
    def from_yaml(cls, config_path: str) -> "OptimizationConfig":
        """
        从YAML文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            OptimizationConfig实例
        """
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"配置文件不存在: {config_path},使用默认配置")
            return cls()

        with open(config_file, encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        # 解析optimizations部分
        optimizations = config_data.get("optimizations", {})
        tool_discovery = config_data.get("tool_discovery", {})
        parameter_validation = config_data.get("parameter_validation", {})
        error_prediction = config_data.get("error_prediction", {})
        monitoring = config_data.get("monitoring", {})

        return cls(
            enable_tool_discovery=tool_discovery.get("enabled", True),
            enable_parameter_validation=parameter_validation.get("enabled", True),
            enable_error_prediction=error_prediction.get("enabled", True),
            tool_discovery_config=tool_discovery.get("config"),
            validation_config=parameter_validation.get("config"),
            prediction_config=error_prediction.get("config"),
            fallback_on_error=optimizations.get("fallback_on_error", True),
            enable_monitoring=monitoring.get("enabled", True),
            monitoring_config={
                "enabled": monitoring.get("enabled", True),
                "stats_interval_seconds": monitoring.get("stats_interval_seconds", 60),
                "log_metrics": monitoring.get("log_metrics", True),
                "alerts": config_data.get("alerts", {}),
            },
        )


@dataclass
class OptimizationResult:
    """优化结果"""

    success: bool
    message: str

    # 工具发现结果
    selected_tools: list[str] = None
    tool_matches: list[str] = None

    # 参数验证结果
    validation_results: dict[str, ValidationResult] | None = None

    # 错误预测结果
    error_predictions: list[str] = None

    # 性能指标
    processing_time: float = 0.0
    timestamp: datetime = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "message": self.message,
            "processing_time": self.processing_time,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "tools_selected": len(self.selected_tools) if self.selected_tools else 0,
            "validation_errors": len(
                [r for r in (self.validation_results or {}).values() if not r.is_valid()]
            ),
            "high_risk_predictions": len(
                [
                    p
                    for p in (self.error_predictions or [])
                    if p.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                ]
            ),
        }


class XiaonuoOptimizationManager:
    """
    小诺优化管理器

    统一封装从Athena提取的三大优化能力,提供简化的API接口。

    核心特性:
    1. 统一的API入口
    2. 配置驱动的模块启用/禁用
    3. 自动降级策略
    4. 统计信息汇总
    """

    def __init__(self, config: OptimizationConfig = None):
        """
        初始化优化管理器

        Args:
            config: 优化配置
        """
        self.config = config or OptimizationConfig()

        # 初始化各模块
        self.tool_discovery: LightweightToolDiscovery | None = None
        self.validator: LightweightRealtimeValidator | None = None
        self.predictor: LightweightErrorPredictor | None = None

        # 初始化监控器
        self.monitor: OptimizationMonitor | None = None
        if self.config.enable_monitoring and OptimizationMonitor:
            try:
                self.monitor = get_optimization_monitor(self.config.monitoring_config)
                logger.info("✅ 监控模块已启用")
            except Exception as e:
                logger.warning(f"监控模块初始化失败: {e}")

        # 统计信息
        self.stats = {
            "total_optimizations": 0,
            "tool_discovery_calls": 0,
            "validation_calls": 0,
            "prediction_calls": 0,
            "fallbacks": 0,
            "errors": 0,
        }

        # 初始化模块
        self._initialize_modules()

        logger.info("🚀 小诺优化管理器初始化完成")
        logger.info(f"   工具发现: {'启用' if self.tool_discovery else '禁用'}")
        logger.info(f"   参数验证: {'启用' if self.validator else '禁用'}")
        logger.info(f"   错误预测: {'启用' if self.predictor else '禁用'}")
        logger.info(f"   监控功能: {'启用' if self.monitor else '禁用'}")

    def _initialize_modules(self) -> Any:
        """初始化各模块"""
        # 工具发现模块
        if self.config.enable_tool_discovery and LightweightToolDiscovery:
            try:
                self.tool_discovery = LightweightToolDiscovery(self.config.tool_discovery_config)
                logger.info("✅ 工具发现模块已启用")
            except Exception as e:
                logger.error(f"❌ 工具发现模块初始化失败: {e}")
                if not self.config.fallback_on_error:
                    raise

        # 参数验证模块
        if self.config.enable_parameter_validation and LightweightRealtimeValidator:
            try:
                self.validator = LightweightRealtimeValidator(self.config.validation_config)
                logger.info("✅ 参数验证模块已启用")
            except Exception as e:
                logger.error(f"❌ 参数验证模块初始化失败: {e}")
                if not self.config.fallback_on_error:
                    raise

        # 错误预测模块
        if self.config.enable_error_prediction and LightweightErrorPredictor:
            try:
                self.predictor = LightweightErrorPredictor(self.config.prediction_config)
                logger.info("✅ 错误预测模块已启用")
            except Exception as e:
                logger.error(f"❌ 错误预测模块初始化失败: {e}")
                if not self.config.fallback_on_error:
                    raise

    async def optimize_task_execution(
        self,
        task_description: str,
        parameters: dict[str, Any],        available_tools: list[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> OptimizationResult:
        """
        优化任务执行(一站式API)

        按顺序执行:错误预测 → 工具发现 → 参数验证

        Args:
            task_description: 任务描述
            parameters: 参数字典
            available_tools: 可用工具列表
            context: 上下文信息

        Returns:
            优化结果
        """
        start_time = datetime.now()
        result = OptimizationResult(success=True, message="优化完成", timestamp=start_time)

        try:
            # 1. 错误预测
            await self._perform_error_prediction(context, result)

            # 2. 工具发现
            await self._perform_tool_discovery(task_description, available_tools, context, result)

            # 3. 参数验证
            await self._perform_parameter_validation(parameters, result)

            # 计算处理时间和记录统计
            result.processing_time = (datetime.now() - start_time).total_seconds()
            self.stats["total_optimizations"] += 1

            # 记录监控指标
            await self._record_monitoring_metrics(result, success=True)

        except Exception as e:
            logger.error(f"优化失败: {e}")
            result.success = False
            result.message = f"优化失败: {e!s}"
            result.processing_time = (datetime.now() - start_time).total_seconds()
            self.stats["errors"] += 1

            # 记录失败监控指标
            await self._record_monitoring_metrics(result, success=False)

        return result

    async def _perform_error_prediction(
        self, context: dict[str, Any], result: OptimizationResult
    ) -> None:
        """执行错误预测"""
        if self.predictor and context:
            try:
                result.error_predictions = await self.predictor.predict(context, top_k=5)
                self.stats["prediction_calls"] += 1

                # 检查高风险预测
                high_risk_count = sum(
                    1
                    for p in result.error_predictions
                    if p.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                )
                if high_risk_count > 0:
                    result.message = f"预测到{high_risk_count}个高风险错误"
                    logger.warning(f"⚠️ {result.message}")

            except Exception as e:
                logger.error(f"错误预测失败: {e}")
                if self.config.fallback_on_error:
                    self.stats["fallbacks"] += 1
                else:
                    raise

    async def _perform_tool_discovery(
        self,
        task_description: str,
        available_tools: list[Any],
        context: dict[str, Any],        result: OptimizationResult,
    ) -> None:
        """执行工具发现"""
        if self.tool_discovery and available_tools:
            try:
                tool_matches = await self.tool_discovery.discover_tools(
                    task_description=task_description,
                    available_tools=available_tools,
                    context=context,
                    top_k=5,
                )
                result.tool_matches = tool_matches
                result.selected_tools = [
                    tool
                    for tool in available_tools
                    if getattr(tool, "tool_id", str(id(tool))) in [m.tool_id for m in tool_matches]
                ]
                self.stats["tool_discovery_calls"] += 1

            except Exception as e:
                logger.error(f"工具发现失败: {e}")
                if self.config.fallback_on_error:
                    self.stats["fallbacks"] += 1
                    # 降级:返回所有工具
                    result.selected_tools = available_tools
                else:
                    raise

    async def _perform_parameter_validation(
        self, parameters: dict[str, Any], result: OptimizationResult
    ) -> None:
        """执行参数验证"""
        if self.validator and parameters:
            try:
                result.validation_results = await self.validator.validate(parameters=parameters)
                self.stats["validation_calls"] += 1

                # 检查验证错误
                invalid_count = sum(
                    1 for r in result.validation_results.values() if not r.is_valid()
                )
                if invalid_count > 0:
                    result.success = False
                    result.message = f"发现{invalid_count}个参数验证错误"
                    logger.warning(f"⚠️ {result.message}")

            except Exception as e:
                logger.error(f"参数验证失败: {e}")
                if self.config.fallback_on_error:
                    self.stats["fallbacks"] += 1
                else:
                    raise

    async def _record_monitoring_metrics(self, result: OptimizationResult, success: bool) -> None:
        """记录监控指标"""
        if self.monitor:
            cache_hit = (
                (
                    result.validation_results
                    and any(
                        r.metadata.get("cache_hit", False)
                        for r in result.validation_results.values()
                    )
                )
                if result.validation_results
                else False
            )

            self.monitor.record_request(
                optimized=True,
                success=success,
                processing_time=result.processing_time,
                cache_hit=cache_hit,
            )

    async def discover_best_tools(
        self,
        task_description: str,
        available_tools: list[Any],
        context: Optional[dict[str, Any]] = None,
        top_k: int = 5,
    ) -> list[Any]:
        """
        发现最佳工具(仅工具发现)

        Args:
            task_description: 任务描述
            available_tools: 可用工具列表
            context: 上下文信息
            top_k: 返回top-k个工具

        Returns:
            选中的工具列表
        """
        if not self.tool_discovery:
            logger.debug("工具发现模块未启用,返回所有工具")
            return available_tools[:top_k]

        try:
            matches = await self.tool_discovery.discover_tools(
                task_description=task_description,
                available_tools=available_tools,
                context=context,
                top_k=top_k,
            )

            # 提取工具对象
            selected_tools = []
            tool_ids = [m.tool_id for m in matches]

            for tool in available_tools:
                tool_id = getattr(tool, "tool_id", str(id(tool)))
                if tool_id in tool_ids:
                    selected_tools.append(tool)

            self.stats["tool_discovery_calls"] += 1
            return selected_tools

        except Exception as e:
            logger.error(f"工具发现失败: {e}")
            if self.config.fallback_on_error:
                self.stats["fallbacks"] += 1
                return available_tools[:top_k]
            raise

    async def validate_parameters(
        self, parameters: dict[str, Any], callback: Callable | None = None
    ) -> dict[str, ValidationResult]:
        """
        验证参数(仅参数验证)

        Args:
            parameters: 参数字典
            callback: 实时反馈回调

        Returns:
            验证结果字典
        """
        if not self.validator:
            logger.debug("参数验证模块未启用")
            return {}

        try:
            results = await self.validator.validate(parameters=parameters, callback=callback)
            self.stats["validation_calls"] += 1
            return results

        except Exception as e:
            logger.error(f"参数验证失败: {e}")
            if self.config.fallback_on_error:
                self.stats["fallbacks"] += 1
                return {}
            raise

    async def predict_errors(
        self, context: dict[str, Any], top_k: int = 5
    ) -> list[PredictionResult]:
        """
        预测错误(仅错误预测)

        Args:
            context: 上下文信息
            top_k: 返回top-k个预测

        Returns:
            预测结果列表
        """
        if not self.predictor:
            logger.debug("错误预测模块未启用")
            return []

        try:
            predictions = await self.predictor.predict(context=context, top_k=top_k)
            self.stats["prediction_calls"] += 1
            return predictions

        except Exception as e:
            logger.error(f"错误预测失败: {e}")
            if self.config.fallback_on_error:
                self.stats["fallbacks"] += 1
                return []
            raise

    def register_parameter_schema(self, schema: ParameterSchema) -> bool:
        """注册参数模式"""
        if self.validator:
            return self.validator.register_schema(schema)
        logger.warning("参数验证模块未启用")
        return False

    def register_tool(self, tool: Any) -> Any:
        """注册工具到发现模块"""
        if self.tool_discovery:
            return asyncio.create_task(self.tool_discovery.register_tool(tool))
        logger.warning("工具发现模块未启用")
        return asyncio.sleep(0)

    async def record_tool_usage(
        self, tool_id: str, task_description: str, success: bool, execution_time: float
    ) -> None:
        """记录工具使用(用于学习)"""
        if self.tool_discovery:
            await self.tool_discovery.record_tool_usage(
                tool_id, task_description, success, execution_time
            )

    async def record_error(
        self, error_pattern: ErrorPattern, context: dict[str, Any], recovery_time: float
    ):
        """记录错误(用于学习)"""
        if self.predictor:
            await self.predictor.record_error(error_pattern, context, recovery_time)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        module_stats = {}

        if self.tool_discovery:
            module_stats["tool_discovery"] = self.tool_discovery.get_analytics()

        if self.validator:
            module_stats["validation"] = self.validator.get_stats()

        if self.predictor:
            module_stats["prediction"] = self.predictor.get_stats()

        return {**self.stats, "modules": module_stats}

    def get_module_status(self) -> dict[str, bool]:
        """获取模块状态"""
        return {
            "tool_discovery_enabled": self.tool_discovery is not None,
            "validation_enabled": self.validator is not None,
            "prediction_enabled": self.predictor is not None,
            "monitoring_enabled": self.monitor is not None,
        }

    def get_monitoring_summary(self) -> dict[str, Any]:
        """
        获取监控摘要

        Returns:
            监控摘要字典
        """
        if not self.monitor:
            return {"enabled": False}

        return self.monitor.get_metrics_summary()

    def get_health_status(self) -> dict[str, Any]:
        """
        获取健康状态

        Returns:
            健康状态字典
        """
        health = {
            "status": "healthy",
            "modules": self.get_module_status(),
            "stats": {
                "total_optimizations": self.stats["total_optimizations"],
                "total_failures": self.stats["errors"],
                "fallbacks": self.stats["fallbacks"],
            },
        }

        if self.monitor:
            monitor_health = self.monitor.get_health_status()
            health["monitoring"] = monitor_health

            # 根据监控状态调整整体健康状态
            if monitor_health.get("status") == "critical":
                health["status"] = "critical"
            elif monitor_health.get("status") == "warning":
                health["status"] = "warning"

        # 检查错误率
        if self.stats["total_optimizations"] > 0:
            error_rate = self.stats["errors"] / self.stats["total_optimizations"]
            if error_rate > 0.1:  # 10%以上错误率
                health["status"] = "critical"
            elif error_rate > 0.05:  # 5%以上错误率
                health["status"] = "warning"

        return health

    def check_alerts(self) -> list[dict[str, Any]]:
        """
        检查告警

        Returns:
            触发的告警列表
        """
        if not self.monitor:
            return []

        return self.monitor.check_alerts()

    def log_monitoring_summary(self) -> None:
        """记录监控摘要到日志"""
        if self.monitor:
            self.monitor.log_metrics_summary()


# 便捷函数
_manager_instance: XiaonuoOptimizationManager | None = None


def get_optimization_manager(
    config: OptimizationConfig | None = None, config_path: Optional[str] = None
) -> XiaonuoOptimizationManager:
    """
    获取优化管理器单例

    Args:
        config: 优化配置对象
        config_path: 配置文件路径(YAML)

    Returns:
        优化管理器实例
    """
    global _manager_instance

    if _manager_instance is None:
        # 如果提供了配置文件路径,从文件加载
        if config_path and not config:
            config = OptimizationConfig.from_yaml(config_path)

        _manager_instance = XiaonuoOptimizationManager(config)

    return _manager_instance


def reset_optimization_manager() -> None:
    """重置优化管理器单例(主要用于测试)"""
    global _manager_instance
    _manager_instance = None


# 使用示例
async def main():
    """演示函数"""
    print("=" * 60)
    print("小诺优化管理器演示")
    print("=" * 60)

    # 创建优化管理器
    config = OptimizationConfig(
        enable_tool_discovery=True,
        enable_parameter_validation=True,
        enable_error_prediction=True,
        fallback_on_error=True,
    )

    manager = XiaonuoOptimizationManager(config)

    # 模拟工具
    class MockTool:
        def __init__(self, tool_id, name, description, capabilities):
            self.tool_id = tool_id
            self.name = name
            self.description = description
            self.capabilities = capabilities

    available_tools = [
        MockTool("patent_search", "专利搜索", "搜索专利数据库", ["专利搜索", "数据库查询"]),
        MockTool("legal_analysis", "法律分析", "分析法律文档", ["法律分析", "文档处理"]),
    ]

    # 模拟参数
    parameters = {"patent_id": "CN1234567", "max_results": 10}

    # 模拟上下文
    context = {
        "cpu_usage": 0.75,
        "memory_usage": 0.68,
        "request_rate": 50,
        "concurrent_requests": 100,
    }

    # 执行优化
    print("\n🚀 执行任务优化...")
    result = await manager.optimize_task_execution(
        task_description="搜索专利CN1234567",
        parameters=parameters,
        available_tools=available_tools,
        context=context,
    )

    print(f"\n结果: {result.message}")
    print(f"成功: {result.success}")
    print(f"处理时间: {result.processing_time*1000:.2f}ms")

    if result.selected_tools:
        print(f"选中工具: {len(result.selected_tools)}个")
        for tool in result.selected_tools:
            print(f"  - {tool.name}")

    if result.validation_results:
        print(f"验证结果: {len(result.validation_results)}个参数")
        for param_name, validation in result.validation_results.items():
            print(f"  - {param_name}: {validation.status.value}")

    if result.error_predictions:
        print(f"错误预测: {len(result.error_predictions)}个")
        for pred in result.error_predictions[:3]:
            if pred.probability > 0.2:
                print(f"  - {pred.error_pattern.value}: {pred.probability:.1%}")

    # 统计信息
    print("\n📊 统计信息:")
    stats = manager.get_stats()
    print(f"   总优化次数: {stats['total_optimizations']}")
    print(f"   工具发现调用: {stats['tool_discovery_calls']}")
    print(f"   参数验证调用: {stats['validation_calls']}")
    print(f"   错误预测调用: {stats['prediction_calls']}")

    print("\n✅ 演示完成")


# 入口点: @async_main装饰器已添加到main函数
