#!/usr/bin/env python3
"""
法律文献分析工具处理器

整合法律分析能力模块，提供法律文献检索、分析和咨询功能。

Author: Athena平台团队
Created: 2026-04-19
Version: v1.0.0
"""

from __future__ import annotations

import logging
import time
from typing import Any

from core.tools.base import ToolDefinition

logger = logging.getLogger(__name__)


async def legal_analysis_handler(
    query: str,
    context: Optional[dict[str, Any]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    法律文献分析处理器

    提供专利、商标、版权等知识产权法律咨询和分析服务。

    Args:
        query: 法律查询文本
        context: 上下文信息（可选）
        **kwargs: 其他参数

    Returns:
        分析结果字典，包含：
        - status: 执行状态 (success/error)
        - result: 分析结果文本
        - legal_need: 识别的法律需求类型
        - execution_time: 执行时间（秒）

    Raises:
        ValueError: 如果query为空
        Exception: 其他处理异常

    Examples:
        >>> result = await legal_analysis_handler("如何申请发明专利?")
        >>> print(result['result'])
        关于您的专利咨询:\\n\\n🔍 专利基础知识:\\n...

        >>> result = await legal_analysis_handler("商标注册流程")
        >>> print(result['legal_need'])
        trademark_inquiry
    """
    start_time = time.time()

    try:
        # 参数验证
        if not query or not isinstance(query, str):
            raise ValueError("query必须是非空字符串")

        # 动态导入法律分析模块（避免循环依赖）
        from core.agents.athena.capabilities.legal_analysis import LegalAnalysisModule

        # 初始化模块
        legal_module = LegalAnalysisModule()

        # 执行分析
        logger.info(f"🔍 开始法律分析: {query[:100]}...")
        result_text = await legal_module.analyze(query, context)

        # 识别法律需求类型
        legal_need = legal_module._analyze_legal_need(query)

        execution_time = time.time() - start_time

        logger.info(
            f"✅ 法律分析完成: need={legal_need}, time={execution_time:.2f}s"
        )

        return {
            "status": "success",
            "result": result_text,
            "legal_need": legal_need,
            "execution_time": execution_time,
            "module_info": legal_module.get_info(),
        }

    except ValueError as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ 法律分析参数错误: {e}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": "ValueError",
            "execution_time": execution_time,
        }

    except ImportError as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ 法律分析模块导入失败: {e}")
        return {
            "status": "error",
            "error": f"法律分析模块不可用: {e}",
            "error_type": "ImportError",
            "execution_time": execution_time,
        }

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ 法律分析执行失败: {e}", exc_info=True)
        return {
            "status": "error",
            "error": f"法律分析执行失败: {e}",
            "error_type": type(e).__name__,
            "execution_time": execution_time,
        }


# 创建工具定义（用于注册）
def create_legal_analysis_tool_definition() -> ToolDefinition:
    """
    创建法律分析工具定义

    Returns:
        ToolDefinition对象
    """
    from core.tools.base import (
        ToolCapability,
        ToolCategory,
        ToolDefinition,
        ToolPriority,
    )

    return ToolDefinition(
        tool_id="legal_analysis",
        name="法律文献分析",
        description="法律文献分析工具 - 提供专利、商标、版权等知识产权法律咨询和分析服务",
        category=ToolCategory.LEGAL_ANALYSIS,
        priority=ToolPriority.MEDIUM,
        capability=ToolCapability(
            input_types=["query", "text"],
            output_types=["legal_analysis", "advice", "strategy"],
            domains=["legal", "patent", "trademark", "copyright", "intellectual_property"],
            task_types=["analyze", "consult", "advise", "research"],
            features={
                "patent_law": True,  # 专利法
                "trademark_law": True,  # 商标法
                "copyright_law": True,  # 版权法
                "legal_strategy": True,  # 法律策略
                "case_analysis": True,  # 案件分析
                "risk_assessment": True,  # 风险评估
                "offline": True,  # 离线可用
                "no_api_required": True,  # 无需API
            }
        ),
        required_params=["query"],
        optional_params=["context"],
        handler=legal_analysis_handler,
        timeout=30.0,
        enabled=True,
    )


__all__ = [
    "legal_analysis_handler",
    "create_legal_analysis_tool_definition",
]
