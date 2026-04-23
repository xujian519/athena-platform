#!/usr/bin/env python3
from __future__ import annotations
"""
高级参数提取器 (Advanced Parameter Extractor)
提取复杂参数结构、嵌套参数和隐式参数

作者: 小诺·双鱼公主
版本: v2.0.0
优化目标: 参数填充有效性 85% → 93%
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ParameterType(str, Enum):
    """参数类型"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    DATE = "date"
    ENUM = "enum"


@dataclass
class ParameterSchema:
    """参数模式"""

    name: str
    param_type: ParameterType
    required: bool = True
    default: Any = None
    enum_values: list[str] = None
    format: Optional[str] = None  # 如 email, url, date
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""


@dataclass
class ExtractedParameter:
    """提取的参数"""

    name: str
    value: Any
    confidence: float  # 提取置信度 (0-1)
    source: str  # 来源 (explicit, implicit, inferred)
    completeness: float  # 完整性 (0-1)
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class ParameterRelation:
    """参数关系"""

    param1: str
    param2: str
    relation_type: str  # depends, mutex, implies
    confidence: float


class AdvancedParameterExtractor:
    """
    高级参数提取器

    功能:
    1. 嵌套参数识别
    2. 参数关系图构建
    3. 参数完整性检查
    4. 槽位填充算法优化
    5. 隐式参数推理
    """

    def __init__(self):
        self.name = "高级参数提取器"
        self.version = "2.0.0"
        self.extraction_history: list[dict[str, Any]] = []

        # 参数模式注册表
        self.schemas: dict[str, list[ParameterSchema]] = {}

        # 参数关系图
        self.relations: list[ParameterRelation] = []

        # 统计信息
        self.stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "avg_completeness": 0.0,
            "avg_confidence": 0.0,
        }

        logger.info(f"✅ {self.name} 初始化完成")

    def register_schema(self, intent: str, parameters: list[ParameterSchema]):
        """注册参数模式"""
        self.schemas[intent] = parameters
        logger.debug(f"📝 注册参数模式: {intent} ({len(parameters)}个参数)")

    async def extract_parameters(
        self,
        query: str,
        intent: str,
        context: Optional[dict[str, Any]] = None,
        conversation_history: list[dict[str, Any]] | None = None,
    ) -> list[ExtractedParameter]:
        """
        提取参数

        Args:
            query: 用户查询
            intent: 意图类型
            context: 上下文信息
            conversation_history: 对话历史

        Returns:
            提取的参数列表
        """
        self.stats["total_extractions"] += 1

        # 1. 获取参数模式
        schema = self.schemas.get(intent, [])

        if not schema:
            logger.warning(f"未找到意图的参数模式: {intent}")
            return []

        # 2. 显式参数提取(从查询中)
        explicit_params = await self._extract_explicit_parameters(query, schema)

        # 3. 隐式参数推理
        implicit_params = await self._infer_implicit_parameters(
            query, schema, explicit_params, context, conversation_history
        )

        # 4. 合并参数
        all_params = explicit_params + implicit_params

        # 5. 构建参数关系图
        self._build_parameter_relations(all_params, schema)

        # 6. 验证参数完整性
        validated_params = self._validate_parameters(all_params, schema)

        # 7. 计算完整性和置信度
        for param in validated_params:
            param.completeness = self._compute_completeness(param, schema)
            param.confidence = self._compute_confidence(param, schema)

        # 更新统计
        self.stats["successful_extractions"] += 1
        self.stats["avg_completeness"] = (
            self.stats["avg_completeness"] * (self.stats["successful_extractions"] - 1)
            + sum(p.completeness for p in validated_params) / len(validated_params)
        ) / self.stats["successful_extractions"]
        self.stats["avg_confidence"] = (
            self.stats["avg_confidence"] * (self.stats["successful_extractions"] - 1)
            + sum(p.confidence for p in validated_params) / len(validated_params)
        ) / self.stats["successful_extractions"]

        return validated_params

    async def _extract_explicit_parameters(
        self, query: str, schema: list[ParameterSchema]
    ) -> list[ExtractedParameter]:
        """提取显式参数"""
        params = []

        for param_schema in schema:
            # 尝试各种提取模式
            value = None

            # 尝试正则匹配
            value = self._try_regex_extraction(query, param_schema)

            # 尝试关键词匹配
            if value is None:
                value = self._try_keyword_extraction(query, param_schema)

            # 尝试范围匹配
            if value is None:
                value = self._try_range_extraction(query, param_schema)

            if value is not None:
                params.append(
                    ExtractedParameter(
                        name=param_schema.name,
                        value=value,
                        confidence=0.9,
                        source="explicit",
                        completeness=1.0,
                    )
                )

        return params

    def _try_regex_extraction(self, query: str, schema: ParameterSchema) -> Any | None:
        """尝试正则表达式提取"""
        # 基于参数类型定义正则模式
        patterns = {
            ParameterType.INTEGER: r"\b\d+\b",
            ParameterType.FLOAT: r"\b\d+\.\d+\b",
            ParameterType.BOOLEAN: r"\b(?:true|false|yes|no|是|否|真|假)\b",
            ParameterType.DATE: r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
            ParameterType.STRING: r'(?:"([^"]*)"|\'([^\']*)\'|\b([^\s,。]+)\b)',
        }

        pattern = patterns.get(schema.param_type)
        if not pattern:
            return None

        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            # 转换类型
            raw_value = matches[0]
            if isinstance(raw_value, tuple):
                raw_value = raw_value[0]

            return self._convert_type(raw_value, schema.param_type)

        return None

    def _try_keyword_extraction(self, query: str, schema: ParameterSchema) -> Any | None:
        """尝试关键词提取"""
        # 在查询中查找参数名附近的值
        keywords = [schema.name, schema.description]

        for keyword in keywords:
            if keyword.lower() in query.lower():
                # 查找关键词后面的值
                idx = query.lower().find(keyword.lower())
                remaining = query[idx + len(keyword) :]

                # 提取第一个有意义的词
                match = re.search(r"\b(\w+)\b", remaining)
                if match:
                    value = match.group(1)
                    return self._convert_type(value, schema.param_type)

        return None

    def _try_range_extraction(self, query: str, schema: ParameterSchema) -> Any | None:
        """尝试范围提取(用于枚举类型)"""
        if schema.enum_values:
            for enum_val in schema.enum_values:
                if str(enum_val).lower() in query.lower():
                    return enum_val

        return None

    def _convert_type(self, value: str, target_type: ParameterType) -> Any:
        """转换类型"""
        try:
            if target_type == ParameterType.INTEGER:
                return int(value)
            elif target_type == ParameterType.FLOAT:
                return float(value)
            elif target_type == ParameterType.BOOLEAN:
                return value.lower() in ["true", "yes", "是", "真", "1"]
            elif target_type == ParameterType.DATE:
                return value  # 简化,实际应该解析
            else:
                return value
        except (ValueError, TypeError):
            return value

    async def _infer_implicit_parameters(
        self,
        query: str,
        schema: list[ParameterSchema],
        explicit_params: list[ExtractedParameter],
        context: dict[str, list[dict[str, Any]],
        conversation_history: list[dict[str, Any]] | None = None,
    ) -> list[ExtractedParameter]:
        """推理隐式参数"""
        implicit_params = []

        # 找出缺失的必需参数
        extracted_names = {p.name for p in explicit_params}
        missing_params = [s for s in schema if s.required and s.name not in extracted_names]

        for param_schema in missing_params:
            # 从上下文中推理
            if context:
                value = self._infer_from_context(param_schema, context)
                if value is not None:
                    implicit_params.append(
                        ExtractedParameter(
                            name=param_schema.name,
                            value=value,
                            confidence=0.6,
                            source="implicit_context",
                            completeness=0.7,
                        )
                    )
                    continue

            # 从对话历史中推理
            if conversation_history:
                value = self._infer_from_history(param_schema, conversation_history)
                if value is not None:
                    implicit_params.append(
                        ExtractedParameter(
                            name=param_schema.name,
                            value=value,
                            confidence=0.5,
                            source="implicit_history",
                            completeness=0.6,
                        )
                    )
                    continue

            # 使用默认值
            if param_schema.default is not None:
                implicit_params.append(
                    ExtractedParameter(
                        name=param_schema.name,
                        value=param_schema.default,
                        confidence=0.4,
                        source="default",
                        completeness=0.5,
                    )
                )

        return implicit_params

    def _infer_from_context(
        self, schema: ParameterSchema, context: dict[str, Any]
    ) -> Any | None:
        """从上下文中推理参数"""
        # 检查上下文是否有相同名称的字段
        if schema.name in context:
            return context[schema.name]

        # 检查相关的上下文字段
        for key, value in context.items():
            if schema.name.lower() in key.lower() or key.lower() in schema.name.lower():
                return value

        return None

    def _infer_from_history(
        self, schema: ParameterSchema, history: list[dict[str, Any]]) -> Any | None:
        """从历史对话中推理参数"""
        # 搜索最近的值
        for turn in reversed(history[-5:]):  # 查看最近5轮
            content = turn.get("content", "")
            user_msg = turn.get("user", "")

            for msg in [content, user_msg]:
                if schema.name.lower() in msg.lower():
                    # 尝试提取值
                    extracted = self._try_regex_extraction(msg, schema)
                    if extracted is not None:
                        return extracted

        return None

    def _build_parameter_relations(
        self, params: list[ExtractedParameter], schema: list[ParameterSchema]
    ):
        """构建参数关系图"""
        # 清空旧关系
        self.relations.clear()

        # 基于参数名称和值检测关系
        for i, p1 in enumerate(params):
            for p2 in params[i + 1 :]:
                # 检测依赖关系
                if self._are_params_dependent(p1, p2):
                    self.relations.append(
                        ParameterRelation(
                            param1=p1.name, param2=p2.name, relation_type="depends", confidence=0.7
                        )
                    )

    def _are_params_dependent(self, p1: ExtractedParameter, p2: ExtractedParameter) -> bool:
        """检查参数是否相互依赖"""
        # 简化版:基于名称相似度
        name1_parts = set(p1.name.lower().split("_"))
        name2_parts = set(p2.name.lower().split("_"))

        # 如果有共同的词根,可能相关
        intersection = name1_parts & name2_parts
        return len(intersection) > 0 and len(intersection) < len(name1_parts)

    def _validate_parameters(
        self, params: list[ExtractedParameter], schema: list[ParameterSchema]
    ) -> list[ExtractedParameter]:
        """验证参数"""
        validated = []

        for param in params:
            # 找到对应的模式
            param_schema = next((s for s in schema if s.name == param.name), None)

            if not param_schema:
                continue

            validation_errors = []

            # 验证类型
            if param_schema.param_type == ParameterType.INTEGER:
                if not isinstance(param.value, int):
                    validation_errors.append(f"应为整数,实际为{type(param.value).__name__}")

            elif param_schema.param_type == ParameterType.FLOAT:
                try:
                    float(param.value)
                except (TypeError, ValueError):
                    validation_errors.append("应为浮点数")

            # 验证范围
            if param_schema.min_value is not None:
                try:
                    if float(param.value) < param_schema.min_value:
                        validation_errors.append(f"应 >= {param_schema.min_value}")
                except (TypeError, ValueError):
                    pass

            if param_schema.max_value is not None:
                try:
                    if float(param.value) > param_schema.max_value:
                        validation_errors.append(f"应 <= {param_schema.max_value}")
                except (TypeError, ValueError):
                    pass

            # 验证枚举
            if param_schema.enum_values and param.value not in param_schema.enum_values:
                validation_errors.append(f"应为以下之一: {param_schema.enum_values}")

            # 验证格式
            if param_schema.format:
                if param_schema.format == "email":
                    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", str(param.value)):
                        validation_errors.append("应为有效的邮箱地址")
                elif param_schema.format == "url":
                    if not re.match(r"^https?://", str(param.value)):
                        validation_errors.append("应为有效的URL")

            param.validation_errors = validation_errors

            # 只保留没有严重错误的参数
            if len(validation_errors) == 0 or all("应为" not in e for e in validation_errors):
                validated.append(param)

        return validated

    def _compute_completeness(
        self, param: ExtractedParameter, schema: list[ParameterSchema]
    ) -> float:
        """计算参数完整性"""
        param_schema = next((s for s in schema if s.name == param.name), None)

        if not param_schema:
            return 0.5

        completeness = 0.0

        # 值存在
        if param.value is not None:
            completeness += 0.4

        # 类型匹配
        if (param_schema.param_type == ParameterType.INTEGER and isinstance(param.value, int)) or (param_schema.param_type == ParameterType.FLOAT and isinstance(
            param.value, (int, float)
        )):
            completeness += 0.3

        # 没有验证错误
        if len(param.validation_errors) == 0:
            completeness += 0.3

        return min(1.0, completeness)

    def _compute_confidence(
        self, param: ExtractedParameter, schema: list[ParameterSchema]
    ) -> float:
        """计算参数置信度"""
        confidence = param.confidence

        # 根据完整性调整
        confidence *= param.completeness

        # 根据验证错误调整
        if param.validation_errors:
            confidence *= 0.7

        return min(1.0, confidence)

    def get_missing_parameters(
        self, params: list[ExtractedParameter], schema: list[ParameterSchema]
    ) -> list[str]:
        """获取缺失的参数"""
        extracted_names = {p.name for p in params}
        return [s.name for s in schema if s.required and s.name not in extracted_names]

    def get_status(self) -> dict[str, Any]:
        """获取提取器状态"""
        return {
            "name": self.name,
            "version": self.version,
            "registered_schemas": len(self.schemas),
            "parameter_relations": len(self.relations),
            "extraction_stats": self.stats,
        }


# 全局单例
_extractor_instance: AdvancedParameterExtractor | None = None


def get_advanced_parameter_extractor() -> AdvancedParameterExtractor:
    """获取高级参数提取器实例"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = AdvancedParameterExtractor()
        _register_default_schemas(_extractor_instance)
    return _extractor_instance


def _register_default_schemas(extractor: AdvancedParameterExtractor) -> Any:
    """注册默认参数模式"""
    # 专利搜索模式
    extractor.register_schema(
        "patent_search",
        [
            ParameterSchema("query", ParameterType.STRING, True, description="搜索关键词"),
            ParameterSchema(
                "limit", ParameterType.INTEGER, False, default=10, min_value=1, max_value=100
            ),
            ParameterSchema("sort_by", ParameterType.STRING, False, default="relevance"),
            ParameterSchema("date_range", ParameterType.OBJECT, False),
            ParameterSchema("assignee", ParameterType.STRING, False),
        ],
    )

    # 代码生成模式
    extractor.register_schema(
        "code_generation",
        [
            ParameterSchema("language", ParameterType.STRING, True),
            ParameterSchema("description", ParameterType.STRING, True),
            ParameterSchema("framework", ParameterType.STRING, False),
            ParameterSchema("style", ParameterType.STRING, False),
        ],
    )
