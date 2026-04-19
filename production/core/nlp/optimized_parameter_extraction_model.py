#!/usr/bin/env python3
from __future__ import annotations
"""
Apple Silicon优化的参数提取模型
Optimized Parameter Extraction for Apple Silicon

针对Apple M4 Pro的优化:
1. 使用国内镜像站下载模型
2. MPS加速推理
3. 内存优化
4. 规则+模型混合策略

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.1.0 "Apple Silicon优化"
"""

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

# 配置镜像站和优化(必须在导入transformers之前)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
cache_dir = os.path.expanduser("~/Athena工作平台/models/cache")
os.environ["HF_HOME"] = cache_dir
os.makedirs(cache_dir, exist_ok=True)

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
    model_version: str = "optimized-t5-base"
    device: str = "cpu"


class OptimizedParameterExtractionModel:
    """
    Apple Silicon优化的参数提取模型

    核心功能:
    1. MPS加速推理
    2. 规则+模型混合策略
    3. 自动回退到规则提取
    4. 内存优化
    """

    def __init__(self, model_name: str = "t5-small"):
        """
        使用t5-small而非t5-base,原因:
        1. 更小更快,适合MPS推理
        2. 参数提取任务不需要太大模型
        3. 从国内镜像下载更快
        """
        self.model_name = model_name

        # 模型和分词器(延迟加载)
        self.model = None
        self.tokenizer = None
        self.device = None

        # 参数模式库
        self.parameter_schemas: dict[str, dict[str, ParameterType]] = {}

        # 提取规则
        self.extraction_rules = self._initialize_extraction_rules()

        # 统计
        self.metrics = {
            "total_extractions": 0,
            "avg_confidence": 0.0,
            "avg_parameters": 0.0,
            "model_used_count": 0,
            "rule_used_count": 0,
        }

        logger.info(f"🔍 优化参数提取模型初始化完成: {model_name}")

    def _initialize_extraction_rules(self) -> dict[str, Any]:
        """初始化提取规则(增强版)"""
        return {
            # 模式匹配规则
            "patterns": {
                "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "url": r'https?://[^\s<>"]+|www\.[^\s<>"]+',
                "file_path": r"[/\\\\]?[\w-]+([/\\\\][\w-]+)*\.\w+",
                "integer": r"\b\d+\b",
                "float": r"\b\d+\.\d+\b",
                "port": r":(\d{1,5})\b",
                "date": r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}",
                "phone": r"1[3-9]\d{9}",
                "ipv4": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
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
                "host": ["主机", "host", "服务器", "server"],
            },
        }

    async def initialize(self):
        """初始化模型 - 使用本地MPS优化模型或规则提取"""
        if self.model is not None:
            return

        # 尝试使用本地模型
        try:
            from pathlib import Path

            import torch
            from transformers import T5ForConditionalGeneration, T5Tokenizer

            # 检测设备
            if torch.backends.mps.is_available():
                self.device = torch.device("mps")
                logger.info(f"✅ 使用MPS设备: {self.device}")
            else:
                self.device = torch.device("cpu")
                logger.info("⚠️ MPS不可用,使用CPU")

            # 尝试本地模型路径
            local_model_paths = [
                Path("/Users/xujian/Athena工作平台/models/converted/t5-small"),
                Path("/Users/xujian/Athena工作平台/models/t5-small"),
                Path("/Users/xujian/Athena工作平台/models/cache/t5-small"),
            ]

            model_loaded = False
            for model_path in local_model_paths:
                if model_path.exists():
                    try:
                        logger.info(f"📦 从本地加载T5模型: {model_path}")
                        self.tokenizer = T5Tokenizer.from_pretrained(
                            str(model_path), local_files_only=True
                        )
                        self.model = T5ForConditionalGeneration.from_pretrained(
                            str(model_path), local_files_only=True, low_cpu_mem_usage=True
                        )
                        self.model.to(self.device)
                        self.model.eval()
                        model_loaded = True
                        logger.info("✅ 本地T5模型加载完成(MPS优化)")
                        break
                    except Exception as e:
                        logger.warning(f"⚠️ 从 {model_path} 加载失败: {e}")
                        continue

            if not model_loaded:
                logger.warning("⚠️ 本地T5模型不可用,使用增强规则提取")
                self.model = "rule_based"
                self.device = "cpu"

        except ImportError:
            logger.warning("⚠️ transformers库未安装,使用增强规则提取")
            self.model = "rule_based"
            self.device = "cpu"

        except Exception as e:
            logger.error(f"❌ T5模型加载失败: {e},使用规则提取")
            self.model = "rule_based"
            self.device = "cpu"

    async def extract_parameters(
        self, text: str, tool_schema: dict[str, ParameterType] | None = None
    ) -> ExtractionResult:
        """
        提取参数(优先使用规则,必要时使用模型)

        Args:
            text: 输入文本
            tool_schema: 工具参数模式

        Returns:
            ExtractionResult: 提取结果
        """
        import time

        start_time = time.time()

        await self.initialize()

        # 智能策略选择:
        # 1. 简单提取用规则(快速且准确)
        # 2. 复杂场景用模型(需要理解语义)
        use_model = await self._should_use_model(text, tool_schema)

        if use_model and self.model != "rule_based":
            parameters = await self._extract_model_based(text, tool_schema)
            self.metrics["model_used_count"] += 1
        else:
            parameters = await self._extract_rule_based(text, tool_schema)
            self.metrics["rule_used_count"] += 1

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
            device=str(self.device) if self.device else "cpu",
        )

        # 更新统计
        self.metrics["total_extractions"] += 1
        self.metrics["avg_confidence"] = self.metrics["avg_confidence"] * 0.9 + confidence * 0.1
        self.metrics["avg_parameters"] = (
            self.metrics["avg_parameters"] * 0.9 + len(parameters) * 0.1
        )

        return result

    async def _should_use_model(
        self, text: str, tool_schema: dict[str, ParameterType]
    ) -> bool:
        """判断是否应该使用模型"""
        # 如果模型不可用,使用规则
        if self.model == "rule_based":
            return False

        # 如果文本很短(<50字),规则通常足够
        if len(text) < 50:
            return False

        # 如果包含明确的参数格式(JSON、key:value等),规则足够
        if "{" in text or "=" in text or ":" in text:
            return False

        # 复杂场景使用模型
        return True

    async def _extract_rule_based(
        self, text: str, tool_schema: dict[str, ParameterType]
    ) -> list[ExtractedParameter]:
        """基于规则的提取(增强版)"""
        parameters = []
        text_lower = text.lower()
        seen_values = set()  # 避免重复

        # 1. 模式匹配提取
        for param_type, pattern in self.extraction_rules["patterns"].items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(0)

                # 避免重复
                if value in seen_values:
                    continue
                seen_values.add(value)

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
                    if value and value not in seen_values:
                        seen_values.add(value)
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
        for param in json_params:
            if param.value not in seen_values:
                seen_values.add(param.value)
                parameters.append(param)

        return parameters

    async def _extract_model_based(
        self, text: str, tool_schema: dict[str, ParameterType]
    ) -> list[ExtractedParameter]:
        """基于模型的提取(MPS优化)"""
        import torch

        # 构造输入提示
        input_text = f"extract parameters: {text}"

        # Tokenize
        inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)

        # 移动到MPS设备
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # 生成(MPS加速)
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
            logger.info("模型输出解析失败,回退到规则提取")
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
            "ipv4": "host",
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
                "type": "t5-mps" if self.model != "rule_based" else "rule_based",
                "device": str(self.device) if self.device else "cpu",
            },
            "performance": {
                "total_extractions": self.metrics["total_extractions"],
                "model_used_count": self.metrics["model_used_count"],
                "rule_used_count": self.metrics["rule_used_count"],
                "avg_confidence": self.metrics["avg_confidence"],
                "avg_parameters_per_extraction": self.metrics["avg_parameters"],
            },
        }


# 导出便捷函数
_extractor: OptimizedParameterExtractionModel | None = None


def get_optimized_parameter_extractor(
    model_name: str = "t5-small",
) -> OptimizedParameterExtractionModel:
    """获取优化参数提取模型单例"""
    global _extractor
    if _extractor is None:
        _extractor = OptimizedParameterExtractionModel(model_name)
    return _extractor


if __name__ == "__main__":
    # 测试脚本
    async def test():
        extractor = get_optimized_parameter_extractor()

        # 测试规则提取
        test_cases = [
            "发送邮件到test@example.com",
            "连接到host:192.168.1.1, port:8080",
            '{"name":"测试", "count":5}',
        ]

        for test in test_cases:
            print(f"\n测试: {test}")
            result = await extractor.extract_parameters(test)
            print(f"参数: {[(p.name, p.value, p.type.value) for p in result.parameters]}")
            print(f"设备: {result.device}")
            print(f"耗时: {result.processing_time:.3f}秒")

        # 获取统计
        metrics = await extractor.get_extraction_metrics()
        print(f"\n统计: {metrics}")

    import asyncio

    asyncio.run(test())
