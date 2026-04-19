#!/usr/bin/env python3
"""
参数提取预训练模型
Parameter Extraction Pre-trained Model

基于预训练模型的智能参数提取:
1. T5模型集成
2. 序列到序列提取
3. 实体识别
4. 类型推断
5. 参数验证
6. 批量处理

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "参数提取模型"
"""

from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ParameterType(Enum):
    """参数类型"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    DATE = "date"
    EMAIL = "email"
    URL = "url"
    FILE_PATH = "file_path"


@dataclass
class ExtractedParameter:
    """提取的参数"""

    name: str
    value: Any
    type: ParameterType
    confidence: float
    source_text: str


@dataclass
class ExtractionResult:
    """提取结果"""

    parameters: list[ExtractedParameter]
    confidence: float
    missing_required: list[str]
    processing_time: float = 0.0
    model_version: str = "t5-base"


class ParameterExtractionModel:
    """
    参数提取模型

    核心功能:
    1. 预训练模型集成
    2. 智能参数提取
    3. 类型推断
    4. 参数验证
    5. 批量处理
    6. 模型微调
    """

    def __init__(self, model_name: str = "t5-base"):
        self.model_name = model_name

        # 模型和分词器(延迟加载)
        self.model = None
        self.tokenizer = None

        # 参数模式库
        self.parameter_schemas: dict[str, dict[str, ParameterType]] = {}

        # 提取规则
        self.extraction_rules = self._initialize_extraction_rules()

        # 统计
        self.metrics = {
            "total_extractions": 0,
            "avg_confidence": 0.0,
            "avg_parameters": 0.0,
            "type_accuracy": 0.0,
        }

        logger.info(f"🔍 参数提取模型初始化完成: {model_name}")

    def _initialize_extraction_rules(self) -> dict[str, Any]:
        """初始化提取规则"""
        return {
            # 模式匹配规则
            "patterns": {
                "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "url": r'https?://[^\s<>"]+|www\.[^\s<>"]+',
                "file_path": r"[/\\\\]?[\w-]+([/\\\\][\w-]+)+\.\w+",
                "integer": r"\b\d+\b",
                "float": r"\b\d+\.\d+\b",
                "port": r":(\d{1,5})\b",
                "date": r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}",
                "phone": r"1[3-9]\d{9}",
            },
            # 关键词映射
            "keywords": {
                "name": ["名称", "名字", "name", "标题", "title"],
                "email": ["邮箱", "邮件", "email", "mail"],
                "url": ["网址", "链接", "url", "link"],
                "count": ["数量", "个数", "count", "number"],
                "port": ["端口", "port"],
                "file": ["文件", "路径", "file", "path"],
                "id": ["ID", "id", "编号", "标识"],
            },
        }

    async def initialize(self):
        """初始化模型(延迟加载)"""
        if self.model is not None:
            return

        try:
            # 尝试加载transformers
            import torch
            from transformers import T5ForConditionalGeneration, T5Tokenizer

            logger.info("📦 加载T5模型...")

            self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)

            self.model.eval()

            logger.info("✅ T5模型加载完成")

        except ImportError:
            logger.warning("⚠️ transformers库未安装,使用规则提取")
            self.model = "rule_based"

        except Exception as e:
            logger.error(f"❌ T5模型加载失败: {e}")
            logger.info("📦 使用规则提取")
            self.model = "rule_based"

    async def extract_parameters(
        self, text: str, tool_schema: dict[str, ParameterType] | None = None
    ) -> ExtractionResult:
        """
        提取参数

        Args:
            text: 输入文本
            tool_schema: 工具参数模式

        Returns:
            ExtractionResult: 提取结果
        """
        import time

        start_time = time.time()

        await self.initialize()

        # 执行提取
        if self.model == "rule_based":
            parameters = await self._extract_rule_based(text, tool_schema)
        else:
            parameters = await self._extract_model_based(text, tool_schema)

        # 计算整体置信度
        confidence = (
            sum(p.confidence for p in parameters) / max(len(parameters), 1) if parameters else 0.0
        )

        # 检查缺失的必填参数
        missing_required = []
        if tool_schema:
            for param_name in tool_schema:
                if not any(p.name == param_name for p in parameters):
                    missing_required.append(param_name)

        # 创建结果
        result = ExtractionResult(
            parameters=parameters,
            confidence=confidence,
            missing_required=missing_required,
            processing_time=time.time() - start_time,
        )

        # 更新统计
        self.metrics["total_extractions"] += 1
        self.metrics["avg_confidence"] = self.metrics["avg_confidence"] * 0.9 + confidence * 0.1
        self.metrics["avg_parameters"] = (
            self.metrics["avg_parameters"] * 0.9 + len(parameters) * 0.1
        )

        return result

    async def _extract_rule_based(
        self, text: str, tool_schema: dict[str, ParameterType]
    ) -> list[ExtractedParameter]:
        """基于规则的提取"""
        parameters = []
        text_lower = text.lower()

        # 1. 模式匹配提取
        for param_type, pattern in self.extraction_rules["patterns"].items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(0)

                # 推断参数名
                param_name = await self._infer_parameter_name(value, param_type, text)

                # 转换类型
                typed_value, detected_type = await self._convert_type(value, param_type)

                parameters.append(
                    ExtractedParameter(
                        name=param_name,
                        value=typed_value,
                        type=detected_type,
                        confidence=0.85,
                        source_text=value,
                    )
                )

        # 2. 关键词提取
        for param_name, keywords in self.extraction_rules["keywords"].items():
            for keyword in keywords:
                if keyword in text_lower:
                    # 尝试提取关键词后的值
                    value = await self._extract_value_after_keyword(text, keyword)
                    if value:
                        typed_value, detected_type = await self._infer_and_convert(value)

                        # 检查是否已存在同名参数
                        if not any(p.name == param_name for p in parameters):
                            parameters.append(
                                ExtractedParameter(
                                    name=param_name,
                                    value=typed_value,
                                    type=detected_type,
                                    confidence=0.75,
                                    source_text=value,
                                )
                            )

        # 3. JSON格式提取
        json_params = await self._extract_json_parameters(text)
        parameters.extend(json_params)

        return parameters

    async def _extract_model_based(
        self, text: str, tool_schema: dict[str, ParameterType]
    ) -> list[ExtractedParameter]:
        """基于模型的提取"""
        import torch

        # 构造输入提示
        input_text = f"extract parameters: {text}"

        # Tokenize
        inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)

        # 生成
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs, max_length=150, num_beams=4, early_stopping=True
            )

        # 解码
        extracted_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # 解析提取结果
        try:
            # 尝试解析为JSON
            extracted_dict = json.loads(extracted_text)

            parameters = []
            for param_name, param_value in extracted_dict.items():
                param_type, typed_value = await self._infer_type_from_value(param_value)

                parameters.append(
                    ExtractedParameter(
                        name=param_name,
                        value=typed_value,
                        type=param_type,
                        confidence=0.90,
                        source_text=str(param_value),
                    )
                )

            return parameters

        except json.JSONDecodeError:
            # 解析失败,回退到规则提取
            return await self._extract_rule_based(text, tool_schema)

    async def _infer_parameter_name(self, value: str, param_type: str, context: str) -> str:
        """推断参数名"""
        # 根据类型和上下文推断
        type_mappings = {
            "email": "email",
            "url": "url",
            "file_path": "file",
            "port": "port",
            "phone": "phone",
            "date": "date",
        }

        # 检查上下文中的关键词
        context_lower = context.lower()

        for param_name, keywords in self.extraction_rules["keywords"].items():
            # 检查关键词是否在值附近
            for keyword in keywords:
                if keyword in context_lower:
                    # 简单的位置检查
                    value_pos = context.lower().find(value.lower())
                    keyword_pos = context_lower.find(keyword)

                    if abs(value_pos - keyword_pos) < 50:  # 50字符范围内
                        return param_name

        # 使用类型默认名
        return type_mappings.get(param_type, "parameter")

    async def _extract_value_after_keyword(self, text: str, keyword: str) -> str | None:
        """提取关键词后的值"""
        # 查找关键词位置
        keyword_pos = text.lower().find(keyword.lower())
        if keyword_pos == -1:
            return None

        # 获取关键词后的文本
        after_keyword = text[keyword_pos + len(keyword) :].strip()

        # 提取第一个词或短语
        patterns = [
            r"[::]\s*([^\s,,。]+)",  # 冒号后的内容
            r"是\s*([^\s,,。]+)",  # "是"后的内容
            r"为\s*([^\s,,。]+)",  # "为"后的内容
            r"^([^\s,,。]+)",  # 开头的词
        ]

        for pattern in patterns:
            match = re.search(pattern, after_keyword)
            if match:
                return match.group(1)

        return None

    async def _convert_type(self, value: str, param_type: str) -> tuple[Any, ParameterType]:
        """转换类型"""
        try:
            if param_type == "integer":
                return int(value), ParameterType.INTEGER
            elif param_type == "float":
                return float(value), ParameterType.FLOAT
            elif param_type == "email":
                return value, ParameterType.EMAIL
            elif param_type == "url":
                return value, ParameterType.URL
            elif param_type == "file_path":
                return value, ParameterType.FILE_PATH
            elif param_type == "phone":
                return value, ParameterType.STRING
            elif param_type == "date":
                return value, ParameterType.DATE
            else:
                return value, ParameterType.STRING

        except (ValueError, TypeError):
            return value, ParameterType.STRING

    async def _infer_and_convert(self, value: str) -> tuple[Any, ParameterType]:
        """推断并转换类型"""
        # 尝试各种类型
        # 1. 整数
        if value.isdigit():
            return int(value), ParameterType.INTEGER

        # 2. 浮点数
        try:
            return float(value), ParameterType.FLOAT
        except ValueError:
            pass

        # 3. 布尔
        if value.lower() in ["true", "false", "yes", "no"]:
            bool_value = value.lower() in ["true", "yes"]
            return bool_value, ParameterType.BOOLEAN

        # 4. 列表
        if value.startswith("[") and value.endswith("]"):
            try:
                list_value = json.loads(value)
                return list_value, ParameterType.LIST
            except json.JSONDecodeError:
                pass

        # 5. 字典
        if value.startswith("{") and value.endswith("}"):
            try:
                dict_value = json.loads(value)
                return dict_value, ParameterType.DICT
            except json.JSONDecodeError:
                pass

        # 默认字符串
        return value, ParameterType.STRING

    async def _infer_type_from_value(self, value: Any) -> tuple[ParameterType, Any]:
        """从值推断类型"""
        if isinstance(value, bool):
            return ParameterType.BOOLEAN, value
        elif isinstance(value, int):
            return ParameterType.INTEGER, value
        elif isinstance(value, float):
            return ParameterType.FLOAT, value
        elif isinstance(value, list):
            return ParameterType.LIST, value
        elif isinstance(value, dict):
            return ParameterType.DICT, value
        else:
            return ParameterType.STRING, str(value)

    async def _extract_json_parameters(self, text: str) -> list[ExtractedParameter]:
        """提取JSON格式的参数"""
        parameters = []

        # 查找JSON对象
        json_pattern = r"\{[^{}]*\}"
        matches = re.finditer(json_pattern, text)

        for match in matches:
            try:
                json_str = match.group(0)
                json_obj = json.loads(json_str)

                for key, value in json_obj.items():
                    param_type, typed_value = await self._infer_type_from_value(value)

                    parameters.append(
                        ExtractedParameter(
                            name=key,
                            value=typed_value,
                            type=param_type,
                            confidence=0.95,
                            source_text=json_str,
                        )
                    )

            except json.JSONDecodeError:
                continue

        return parameters

    async def get_extraction_metrics(self) -> dict[str, Any]:
        """获取提取统计"""
        return {
            "model": {
                "name": self.model_name,
                "type": "t5" if self.model != "rule_based" else "rule_based",
            },
            "performance": {
                "total_extractions": self.metrics["total_extractions"],
                "avg_confidence": self.metrics["avg_confidence"],
                "avg_parameters_per_extraction": self.metrics["avg_parameters"],
            },
        }


# 导出便捷函数
_extractor: ParameterExtractionModel | None = None


def get_parameter_extractor(model_name: str = "t5-base") -> ParameterExtractionModel:
    """获取参数提取模型单例"""
    global _extractor
    if _extractor is None:
        _extractor = ParameterExtractionModel(model_name)
    return _extractor
