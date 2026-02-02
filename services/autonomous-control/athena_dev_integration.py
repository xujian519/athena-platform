#!/usr/bin/env python3
"""
Athena开发助手集成模块
将开发助手功能集成到Athena主服务
"""

from fastapi import APIRouter
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import sys
from pathlib import Path

# 添加路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# 导入工具
from athena_dev_assistant.tools.patent_writing_tool import AthenaPatentWritingTool
from athena_dev_assistant.tools.examination_response_tool import AthenaExaminationResponseTool


# 全局工具实例
writing_tool = None
response_tool = None


def get_writing_tool() -> Any | None:
    """获取专利写作工具实例"""
    global writing_tool
    if writing_tool is None:
        writing_tool = AthenaPatentWritingTool()
    return writing_tool


def get_response_tool() -> Any | None:
    """获取审查答复工具实例"""
    global response_tool
    if response_tool is None:
        response_tool = AthenaExaminationResponseTool()
    return response_tool


# 创建API路由
router = APIRouter(
    prefix="/api/v1/athena/dev",
    tags=["Athena开发助手"]
)


@router.post("/patent/analyze")
async def analyze_invention(data: dict):
    """分析技术交底书"""
    tool = get_writing_tool()
    analysis = tool.analyze_invention_disclosure(data.get("disclosure", ""))
    return {
        "success": True,
        "analysis": analysis
    }


@router.post("/patent/draft_claims")
async def draft_patent_claims(data: dict):
    """起草权利要求"""
    tool = get_writing_tool()

    # 先分析
    analysis = data.get("analysis")
    if not analysis:
        analysis = tool.analyze_invention_disclosure(data.get("disclosure", ""))

    # 生成权利要求
    claim_type = data.get("claim_type", "产品")
    claims = tool.draft_claims(analysis, claim_type)

    return {
        "success": True,
        "claims": claims
    }


@router.post("/patent/check_law26")
async def check_patent_law_26(data: dict):
    """检查专利法第26条符合性"""
    tool = get_writing_tool()

    specification = data.get("specification", "")
    check_result = tool.check_patent_law_26(specification)

    return {
        "success": True,
        "check_result": check_result
    }


@router.post("/examination/analyze")
async def analyze_examination_opinion(data: dict):
    """分析审查意见"""
    tool = get_response_tool()
    analysis = tool.analyze_examination_opinion(data.get("opinion", ""))

    return {
        "success": True,
        "analysis": analysis
    }


@router.post("/examination/draft_response")
async def draft_examination_response(data: dict):
    """起草审查答复"""
    tool = get_response_tool()

    # 先分析
    analysis = data.get("analysis")
    if not analysis:
        analysis = tool.analyze_examination_opinion(data.get("opinion", ""))

    # 起草答复
    patent_info = data.get("patent_info", {})
    response = tool.draft_response(analysis, patent_info)

    return {
        "success": True,
        "response": response
    }


@router.post("/examination/suggest_amendments")
async def suggest_amendments(data: dict):
    """生成修改建议"""
    tool = get_response_tool()

    # 先分析
    analysis = data.get("analysis")
    if not analysis:
        analysis = tool.analyze_examination_opinion(data.get("opinion", ""))

    # 生成建议
    suggestions = tool.generate_amendment_suggestions(analysis)

    return {
        "success": True,
        "suggestions": suggestions
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "Athena开发助手",
        "tools": ["patent_writing", "examination_response"]
    }


# 与主服务集成的便捷函数
async def integrate_with_athena_server(app):
    """集成到Athena主服务"""
    app.include_router(router)
    print("✅ Athena开发助手已集成到主服务")
    print("🏛️ 为爸爸的专利工作提供专业支持")


# 导出供其他模块使用
__all__ = [
    "router",
    "get_writing_tool",
    "get_response_tool",
    "integrate_with_athena_server"
]