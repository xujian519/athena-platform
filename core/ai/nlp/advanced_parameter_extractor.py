#!/usr/bin/env python3

"""
高级参数提取器 - 第一阶段优化
Advanced Parameter Extractor - Phase 1 Optimization

优化重点:
1. 嵌套参数结构识别
2. 参数关系图构建
3. 参数完整性检查
4. 槽位填充优化

作者: 小诺·双鱼公主
版本: v1.0.0 "参数提取增强"
创建: 2026-01-12
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ParamType(Enum):
    """参数类型"""

    SCALAR = "scalar"  # 标量参数
    LIST = "list"  # 列表参数
    DICT = "dict"  # 字典参数
    NESTED = "nested"  # 嵌套结构
    REFERENCE = "reference"  # 引用参数


@dataclass
class ParamNode:
    """参数节点"""

    name: str
    param_type: ParamType
    value: Any
    children: dict[str, ParamNode] = field(default_factory=dict)
    required: bool = True
    extracted: bool = False
    confidence: float = 0.0
    source: str = ""  # 提取来源


@dataclass
class ParamRelation:
    """参数关系"""

    param_a: str
    param_b: str
    relation_type: str  # dependency, mutually_exclusive, complementary
    strength: float  # 关系强度 0-1


@dataclass
class ExtractionResult:
    """提取结果"""

    success: bool
    parameters: dict[str, ParamNode]
    missing_params: list[str]
    confidence: float
    extraction_time: float
    relations: list[ParamRelation]


class AdvancedParameterExtractor:
    """高级参数提取器"""

    def __init__(self):
        self.name = "高级参数提取器 v1.0"
        self.version = "1.0.0"

        # 参数模式库
        self.param_patterns = self._init_patterns()

        # 参数关系图
        self.relation_graph: dict[str, list[ParamRelation] = {}

        # 统计信息
        self.stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "avg_confidence": 0.0,
            "nested_params_extracted": 0,
            "avg_extraction_time": 0.0,
        }

        logger.info(f"🔍 {self.name} 初始化完成")

    def _init_patterns(self) -> dict[str, list[dict[str, Any]]]:
        """初始化参数模式库"""
        return {
            "patent_analysis": [
                {
                    "name": "patent_number",
                    "pattern": r"(?:专利号?|申请号?|公开号?)[::]?\s*([A-Z]{0,2}\d{9,13})",
                    "type": ParamType.SCALAR,
                    "required": True,
                },
                {
                    "name": "analysis_depth",
                    "pattern": r"(?:分析深度|详细程度)[::]?\s*(基本|详细|完整)",
                    "type": ParamType.SCALAR,
                    "required": False,
                    "default": "basic",
                },
                {
                    "name": "aspects",
                    "pattern": r"(?:分析[方面项]|考察[方面项])[::]?\s*([^,,。.]+(?:[,,、]|(?:以及|和)\s*[^,,。.]+)*",
                    "type": ParamType.LIST,
                    "required": False,
                },
            ],
            "patent_drafting": [
                {
                    "name": "invention_title",
                    "pattern": r"(?:发明名称|名称|题目)[::]\s*([^\n]+)",
                    "type": ParamType.SCALAR,
                    "required": True,
                },
                {
                    "name": "technical_field",
                    "pattern": r"(?:技术领域|所属领域)[::]\s*([^\n]+)",
                    "type": ParamType.SCALAR,
                    "required": True,
                },
                {
                    "name": "embodiments",
                    "pattern": r"(?:实施例|具体实施方式)[::]",
                    "type": ParamType.NESTED,
                    "required": False,
                    "nested_params": ["description", "advantages"],
                },
            ],
            "coding_assistant": [
                {
                    "name": "language",
                    "pattern": r"(?:编程语言|语言|使用|用)\s*(Python|Java|JavaScript|TypeScript|Go|Rust|C\+\+|C#?)",
                    "type": ParamType.SCALAR,
                    "required": False,
                    "default": "Python",
                },
                {
                    "name": "framework",
                    "pattern": r"(?:框架|使用)\s*([A-Za-z]+)(?:\.(?:js|ts|py))?",
                    "type": ParamType.SCALAR,
                    "required": False,
                },
                {
                    "name": "requirements",
                    "pattern": r"(?:需求|要求|功能)[::]",
                    "type": ParamType.NESTED,
                    "required": True,
                },
            ],
        }

    async def extract(
        self, text: str, intent: str, context: Optional[dict[str, Any]] = None
    ) -> ExtractionResult:
        """
        提取参数

        Args:
            text: 输入文本
            intent: 用户意图
            context: 上下文信息

        Returns:
            ExtractionResult: 提取结果
        """
        import time

        start_time = time.time()

        # 1. 获取参数定义
        param_defs = self.param_patterns.get(intent, [])

        # 2. 提取标量参数
        parameters: dict[str, ParamNode] = {}
        for param_def in param_defs:
            if param_def["type"] in [ParamType.SCALAR, ParamType.LIST]:
                node = self._extract_scalar_param(text, param_def)
                if node:
                    parameters[node.name] = node

        # 3. 提取嵌套参数
        for param_def in param_defs:
            if param_def["type"] == ParamType.NESTED:
                nested_node = self._extract_nested_param(text, param_def)
                if nested_node:
                    parameters[nested_node.name] = nested_node

        # 4. 从上下文补充参数
        if context:
            self._fill_from_context(parameters, context)

        # 5. 检查完整性
        missing_params = [
            p["name"]
            for p in param_defs
            if p.get("required", False) and p["name"] not in parameters
        ]

        # 6. 计算置信度
        confidence = self._calculate_confidence(parameters, param_defs)

        # 7. 构建参数关系图
        relations = self._build_relations(parameters, param_defs)

        # 8. 更新统计
        extraction_time = time.time() - start_time
        self._update_stats(parameters, confidence, extraction_time)

        return ExtractionResult(
            success=len(missing_params) == 0 or len(parameters) > 0,
            parameters=parameters,
            missing_params=missing_params,
            confidence=confidence,
            extraction_time=extraction_time,
            relations=relations,
        )

    def _extract_scalar_param(self, text: str, param_def: dict) -> Optional[ParamNode]:
        """提取标量/列表参数"""
        pattern = param_def["pattern"]
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            value = match.group(1) if match.groups() else match.group(0)

            # 根据参数类型转换
            if param_def["type"] == ParamType.LIST:
                # 分割列表
                value = self._parse_list_value(value)

            return ParamNode(
                name=param_def["name"],
                param_type=param_def["type"],
                value=value,
                required=param_def.get("required", False),
                extracted=True,
                confidence=0.9,
                source="regex_match",
            )

        return None

    def _extract_nested_param(self, text: str, param_def: dict) -> Optional[ParamNode]:
        """提取嵌套参数"""
        name = param_def["name"]
        nested_param_names = param_def.get("nested_params", [])

        # 查找嵌套参数的开始位置
        pattern = param_def["pattern"]
        start_match = re.search(pattern, text, re.IGNORECASE)

        if not start_match:
            return None

        # 提取嵌套内容
        start_pos = start_match.end()
        nested_text = text[start_pos : start_pos + 500]  # 限制范围

        # 提取子参数
        children = {}
        for nested_name in nested_param_names:
            # 简化的子参数提取
            sub_pattern = f"{nested_name}[::](.*?)(?=\\n|$|{'|'.join(nested_param_names)})"
            sub_match = re.search(sub_pattern, nested_text, re.IGNORECASE)
            if sub_match:
                children[nested_name] = ParamNode(
                    name=nested_name,
                    param_type=ParamType.SCALAR,
                    value=sub_match.group(1).strip(),
                    extracted=True,
                    confidence=0.8,
                    source="nested_extraction",
                )

        if children:
            return ParamNode(
                name=name,
                param_type=ParamType.NESTED,
                value={k: v.value for k, v in children.items()},
                children=children,
                required=param_def.get("required", False),
                extracted=True,
                confidence=0.85,
                source="nested_extraction",
            )

        return None

    def _parse_list_value(self, value: str) -> list[str]:
        """解析列表值"""
        # 分隔符: 中文逗号、英文逗号、顿号、以及、和
        separators = r"[,,、、]|(?:以及|和)\s*"
        items = re.split(separators, value)
        return [item.strip() for item in items if item.strip()]

    def _fill_from_context(self, parameters: dict[str, ParamNode], context: dict[str, Any]):
        """从上下文补充参数"""
        for key, value in context.items():
            if key not in parameters:
                parameters[key] = ParamNode(
                    name=key,
                    param_type=ParamType.SCALAR,
                    value=value,
                    required=False,
                    extracted=True,
                    confidence=0.7,
                    source="context",
                )

    def _calculate_confidence(
        self, parameters: dict[str, ParamNode], param_defs: list[dict[str, Any]]
    ) -> float:
        """计算提取置信度"""
        if not parameters:
            return 0.0

        # 基于提取参数的置信度加权平均
        total_confidence = 0.0
        total_weight = 0.0

        for param_node in parameters.values():
            weight = 2.0 if param_node.required else 1.0
            total_confidence += param_node.confidence * weight
            total_weight += weight

        return total_confidence / total_weight if total_weight > 0 else 0.0

    def _build_relations(
        self, parameters: dict[str, ParamNode], param_defs: list[dict[str, Any]]
    ) -> list[ParamRelation]:
        """构建参数关系"""
        relations = []

        # 简化的关系检测
        param_names = list(parameters.keys())

        for i, name_a in enumerate(param_names):
            for name_b in param_names[i + 1 :]:
                # 检测互补关系(一个必需,一个可选)
                if parameters[name_a].required != parameters[name_b].required:
                    relations.append(
                        ParamRelation(
                            param_a=name_a,
                            param_b=name_b,
                            relation_type="complementary",
                            strength=0.7,
                        )
                    )

        return relations

    def _update_stats(
        self, parameters: dict[str, ParamNode], confidence: float, extraction_time: float
    ):
        """更新统计"""
        self.stats["total_extractions"] += 1

        if parameters:
            self.stats["successful_extractions"] += 1

        # 更新平均置信度
        n = self.stats["total_extractions"]
        old_avg = self.stats["avg_confidence"]
        self.stats["avg_confidence"] = (old_avg * (n - 1) + confidence) / n

        # 更新平均提取时间
        old_time = self.stats["avg_extraction_time"]
        self.stats["avg_extraction_time"] = (old_time * (n - 1) + extraction_time) / n

        # 统计嵌套参数
        nested_count = sum(1 for p in parameters.values() if p.param_type == ParamType.NESTED)
        self.stats["nested_params_extracted"] += nested_count

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


# 全局实例
_extractor_instance: Optional[AdvancedParameterExtractor] = None


def get_advanced_parameter_extractor() -> AdvancedParameterExtractor:
    """获取高级参数提取器单例"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = AdvancedParameterExtractor()
    return _extractor_instance

