#!/usr/bin/env python3
from __future__ import annotations
"""
代理Agent适配器

将新版小娜代理类（ApplicationReviewer等）转换为可调用的工具函数。

Author: Athena平台团队
创建时间: 2026-04-21
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ProxyAgentAdapter:
    """
    代理Agent适配器

    将新版小娜代理类（继承自BaseXiaonaComponent的代理类）
    转换为可调用的函数。

    工作流程:
    1. 接收任务和参数
    2. 创建代理实例
    3. 调用代理方法
    4. 返回结果
    """

    # 代理类的方法映射
    METHOD_MAPPING = {
        "application_reviewer": {
            "class": "core.agents.xiaona.application_reviewer_proxy.ApplicationDocumentReviewerProxy",
            "methods": {
                "review_format": "review_format",
                "review_disclosure": "review_disclosure",
                "review_claims": "review_claims",
                "review_specification": "review_specification",
                "review_application": "review_application",
            }
        },
        "writing_reviewer": {
            "class": "core.agents.xiaona.writing_reviewer_proxy.WritingQualityReviewerProxy",
            "methods": {
                "review_writing": "review_writing",
                "review_legal_terminology": "review_legal_terminology",
                "review_technical_accuracy": "review_technical_accuracy",
                "review_style_consistency": "review_style_consistency",
            }
        },
        "novelty_analyzer": {
            "class": "core.agents.xiaona.novelty_analyzer_proxy.NoveltyAnalyzerProxy",
            "methods": {
                "analyze_novelty": "analyze_novelty",
                "compare_features": "compare_features",
                "judge_novelty": "judge_novelty",
            }
        },
        "creativity_analyzer": {
            "class": "core.agents.xiaona.creativity_analyzer_proxy.CreativityAnalyzerProxy",
            "methods": {
                "analyze_creativity": "analyze_creativity",
                "assess_obviousness": "assess_obviousness",
                "evaluate_inventive_step": "evaluate_inventive_step",
                "analyze_technical_advancement": "analyze_technical_advancement",
            }
        },
        "infringement_analyzer": {
            "class": "core.agents.xiaona.infringement_analyzer_proxy.InfringementAnalyzerProxy",
            "methods": {
                "analyze_infringement": "analyze_infringement",
                "interpret_claims": "interpret_claims",
                "compare_features": "compare_features_for_infringement",
                "determine_infringement": "determine_infringement",
                "assess_risk": "assess_risk",
            }
        },
        "invalidation_analyzer": {
            "class": "core.agents.xiaona.invalidation_analyzer_proxy.InvalidationAnalyzerProxy",
            "methods": {
                "analyze_invalidation": "analyze_invalidation",
                "analyze_novelty_grounds": "analyze_novelty_grounds",
                "analyze_creativity_grounds": "analyze_creativity_grounds",
                "analyze_disclosure_grounds": "analyze_disclosure_grounds",
                "develop_evidence_strategy": "develop_evidence_strategy",
            }
        },
    }

    def __init__(self, agent_name: str, method_name: Optional[str] = None):
        """
        初始化代理适配器

        Args:
            agent_name: 代理名称（如"application_reviewer"）
            method_name: 方法名称（如"review_application"）
                       如果为None，则使用代理的默认方法
        """
        self.agent_name = agent_name
        self.method_name = method_name

        # 验证代理存在
        if agent_name not in self.METHOD_MAPPING:
            raise ValueError(f"未知的代理: {agent_name}")

        agent_info = self.METHOD_MAPPING[agent_name]
        self.class_path = agent_info["class"]
        self.available_methods = agent_info["methods"]

        # 确定使用的方法
        if method_name is None:
            # 使用第一个方法作为默认方法
            self.method_name = next(iter(self.available_methods.values()))

        # 验证方法存在
        if method_name and method_name not in self.available_methods:
            raise ValueError(f"代理 {agent_name} 没有方法 {method_name}")

        logger.info(f"✅ 代理适配器创建: {agent_name}.{method_name}")

    async def __call__(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """
        调用代理处理任务

        Args:
            data: 输入数据
            **kwargs: 额外参数

        Returns:
            代理执行结果
        """
        start_time = __import__('time').time()

        try:
            logger.info(f"🤖 调用代理: {self.agent_name}.{self.method_name}")

            # 1. 动态导入代理类
            module_path, class_name = self._parse_class_path(self.class_path)
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)

            # 2. 创建代理实例
            agent_instance = agent_class(
                agent_id=f"{self.agent_name}_adapter",
                config={"llm_config": {"model": "claude-3-5-sonnet-20241022"}}
            )

            # 3. 获取方法
            method = getattr(agent_instance, self.method_name)

            # 4. 调用方法
            if __import__('inspect').iscoroutinefunction(method):
                result = await method(data, **kwargs)
            else:
                result = method(data, **kwargs)

            # 5. 添加元数据
            execution_time = __import__('time').time() - start_time
            if isinstance(result, dict):
                result["metadata"] = {
                    "agent_name": self.agent_name,
                    "method_name": self.method_name,
                    "agent_type": "proxy",
                    "execution_time": execution_time,
                    "timestamp": __import__('datetime').datetime.now().isoformat(),
                }

            logger.info(f"✅ 代理调用完成: {self.agent_name}.{self.method_name} (耗时={execution_time:.2f}s)")

            return result

        except Exception as e:
            logger.error(f"❌ 代理调用失败: {self.agent_name}.{self.method_name} - {e}")
            execution_time = __import__('time').time() - start_time

            return {
                "success": False,
                "error": str(e),
                "agent_name": self.agent_name,
                "method_name": self.method_name,
                "metadata": {
                    "agent_name": self.agent_name,
                    "method_name": self.method_name,
                    "agent_type": "proxy",
                    "execution_time": execution_time,
                }
            }

    def _parse_class_path(self, class_path: str) -> tuple[str, str]:
        """
        解析类路径

        Args:
            class_path: 类路径（如"core.agents.xiaona.ApplicationReviewerProxy"）

        Returns:
            (module_path, class_name) 元组
        """
        parts = class_path.split(".")
        class_name = parts[-1]
        module_path = ".".join(parts[:-1])

        return module_path, class_name

    def to_tool_definition(self) -> dict[str, Any]:
        """
        转换为工具定义（用于FunctionCallingSystem注册）

        Returns:
            工具定义字典
        """
        return {
            "name": f"{self.agent_name}.{self.method_name}",
            "description": f"{self.agent_name} - {self.method_name}",
            "category": "agent",
            "metadata": {
                "type": "proxy",
                "agent_name": self.agent_name,
                "method_name": self.method_name,
                "class_path": self.class_path,
                "available_methods": list(self.available_methods.keys()),
            }
        }

    @classmethod
    def list_all_proxies(cls) -> list[str]:
        """列出所有可用的代理"""
        return list(cls.METHOD_MAPPING.keys())

    @classmethod
    def get_proxy_methods(cls, agent_name: str) -> list[str]:
        """获取代理的所有可用方法"""
        if agent_name in cls.METHOD_MAPPING:
            return list(cls.METHOD_MAPPING[agent_name]["methods"].keys())
        return []
