#!/usr/bin/env python3
from __future__ import annotations
"""
IPC分类API路由
IPC Classification API Routes

提供IPC分类相关的RESTful API接口
"""

import logging
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建路由器
router = APIRouter(prefix="/api/v2", tags=["IPC分类"])


# 请求模型
class IPCClassificationRequest(BaseModel):
    """IPC分类请求"""

    title: str | None = Field(None, description="专利标题")
    abstract: str | None = Field(None, description="专利摘要")
    patent_text: str = Field(..., description="专利权利要求或全文")
    top_n: int = Field(5, description="返回前N个分类结果")


class IPCSearchRequest(BaseModel):
    """IPC搜索请求"""

    query: str = Field(..., description="搜索查询")
    top_n: int = Field(10, description="返回前N个结果")
    section_filter: str | None = Field(None, description="部级筛选 (A-H)")


# IPC向量数据库单例
_ipc_vector_db = None
_ipc_domain_system = None


def get_ipc_vector_db():
    """获取IPC向量数据库单例"""
    global _ipc_vector_db
    if _ipc_vector_db is None:
        try:
            from core.patents.ipc_vector_database import IPCVectorDatabase

            # 使用更完整的IPC定义文件
            _ipc_vector_db = IPCVectorDatabase(ipc_data_path=data_path)
            _ipc_vector_db.load_ipc_data()
            logger.info("✅ IPC向量数据库已初始化")
        except Exception as e:
            logger.error(f"❌ IPC向量数据库初始化失败: {e}")
            _ipc_vector_db = None
    return _ipc_vector_db


def get_ipc_domain_system():
    """获取IPC领域匹配系统单例"""
    global _ipc_domain_system
    if _ipc_domain_system is None:
        try:
            from core.patents.ipc_domain_matching import IPCDomainMatchingSystem

            _ipc_domain_system = IPCDomainMatchingSystem()
            logger.info("✅ IPC领域匹配系统已初始化")
        except Exception as e:
            logger.error(f"❌ IPC领域匹配系统初始化失败: {e}")
            _ipc_domain_system = None
    return _ipc_domain_system


# ==================== API端点 ====================


@router.post("/ipc/classify")
async def classify_ipc(request: IPCClassificationRequest):
    """
    对专利文本进行IPC分类

    - **title**: 专利标题(可选)
    - **abstract**: 专利摘要(可选)
    - **patent_text**: 专利权利要求或全文(必需)
    - **top_n**: 返回前N个分类结果(默认5)
    """
    try:
        ipc_db = get_ipc_vector_db()
        if ipc_db is None:
            raise HTTPException(status_code=503, detail="IPC数据库服务不可用")

        # 构建完整文本
        full_text = f"{request.title or ''} {request.abstract or ''} {request.patent_text}".strip()

        # 执行分类
        classification = ipc_db.classify_patent(full_text, top_n=request.top_n)

        # 格式化结果
        results = []
        for match in classification.matched_ipcs:
            results.append(
                {
                    "code": match.ipc_entry.ipc_code,
                    "name": match.ipc_entry.ipc_name,
                    "section": match.ipc_entry.section,
                    "level": match.ipc_entry.ipc_level.value,
                    "similarity_score": round(match.similarity_score, 3),
                    "confidence": round(match.confidence, 3),
                    "match_reason": match.match_reason,
                    "keywords": match.suggested_keywords[:5],
                }
            )

        return {
            "success": True,
            "text_snippet": full_text[:200] + "..." if len(full_text) > 200 else full_text,
            "primary_classification": classification.primary_classification,
            "secondary_classifications": classification.secondary_classifications,
            "domain_suggestions": classification.domain_suggestions,
            "classifications": results,
            "negentropy_score": round(classification.negentropy_score, 3),
            "overall_confidence": round(classification.confidence, 3),
            "total_results": len(results),
        }

    except Exception as e:
        logger.error(f"IPC分类失败: {e}")
        raise HTTPException(status_code=500, detail=f"分类失败: {e!s}") from e


@router.post("/ipc/search")
async def search_ipc(request: IPCSearchRequest):
    """
    基于文本搜索IPC分类

    - **query**: 搜索查询
    - **top_n**: 返回前N个结果(默认10)
    - **section_filter**: 部级筛选 A-H(可选)
    """
    try:
        ipc_db = get_ipc_vector_db()
        if ipc_db is None:
            raise HTTPException(status_code=503, detail="IPC数据库服务不可用")

        # 执行搜索
        results = ipc_db.search_by_text(
            query_text=request.query, top_n=request.top_n, section_filter=request.section_filter
        )

        # 格式化结果
        formatted_results = []
        for match in results:
            formatted_results.append(
                {
                    "code": match.ipc_entry.ipc_code,
                    "name": match.ipc_entry.ipc_name,
                    "description": match.ipc_entry.ipc_description,
                    "section": match.ipc_entry.section,
                    "level": match.ipc_entry.ipc_level.value,
                    "similarity_score": round(match.similarity_score, 3),
                    "confidence": round(match.confidence, 3),
                    "match_reason": match.match_reason,
                    "keywords": match.suggested_keywords,
                }
            )

        return {
            "success": True,
            "query": request.query,
            "section_filter": request.section_filter,
            "total_results": len(formatted_results),
            "results": formatted_results,
        }

    except Exception as e:
        logger.error(f"IPC搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {e!s}") from e


@router.get("/ipc/details/{ipc_code}")
async def get_ipc_details(ipc_code: str):
    """
    获取指定IPC分类的详细信息

    - **ipc_code**: IPC分类号(如:G06F、A01B 1/00)
    """
    try:
        ipc_db = get_ipc_vector_db()
        if ipc_db is None:
            raise HTTPException(status_code=503, detail="IPC数据库服务不可用")

        # 获取详情
        entry = ipc_db.get_ipc_details(ipc_code)

        if entry is None:
            raise HTTPException(status_code=404, detail=f"未找到IPC分类: {ipc_code}")

        return {
            "success": True,
            "ipc_code": entry.ipc_code,
            "name": entry.ipc_name,
            "description": entry.ipc_description,
            "level": entry.ipc_level.value,
            "section": entry.section,
            "parent_code": entry.parent_code,
            "keywords": entry.keywords,
            "examples": entry.examples,
            "related_domains": entry.related_domains,
            "source": entry.source,
            "confidence": entry.confidence,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取IPC详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {e!s}") from e


@router.get("/ipc/section/{section}")
async def get_ipc_by_section(section: str):
    """
    获取指定部的所有IPC分类

    - **section**: 部代码(A-H)
    """
    try:
        # 验证部代码
        if section not in ["A", "B", "C", "D", "E", "F", "G", "H"]:
            raise HTTPException(status_code=400, detail="部代码必须是A-H之间的字母")

        ipc_db = get_ipc_vector_db()
        if ipc_db is None:
            raise HTTPException(status_code=503, detail="IPC数据库服务不可用")

        # 获取指定部的IPC
        entries = ipc_db.get_by_section(section)

        # 格式化结果
        results = []
        for entry in entries:
            results.append(
                {
                    "code": entry.ipc_code,
                    "name": entry.ipc_name,
                    "level": entry.ipc_level.value,
                    "keywords": entry.keywords,
                }
            )

        section_names = {
            "A": "人类生活必需",
            "B": "作业;运输",
            "C": "化学;冶金",
            "D": "纺织;造纸",
            "E": "固定建筑物",
            "F": "机械工程;照明;加热;武器;爆破",
            "G": "物理",
            "H": "电学",
        }

        return {
            "success": True,
            "section": section,
            "section_name": section_names.get(section, "未知"),
            "total_count": len(results),
            "classifications": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取IPC部信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {e!s}") from e


@router.get("/ipc/statistics")
async def get_ipc_statistics():
    """获取IPC数据库统计信息"""
    try:
        ipc_db = get_ipc_vector_db()
        if ipc_db is None:
            raise HTTPException(status_code=503, detail="IPC数据库服务不可用")

        stats = ipc_db.get_statistics()

        return {
            "success": True,
            "statistics": {
                "total_ipc_entries": stats["total_ipc_entries"],
                "sections": stats["sections"],
                "domains": stats["domains"],
                "keyword_index_size": stats["keyword_index_size"],
                "is_loaded": stats["is_loaded"],
            },
            "metadata": {
                "version": "2026.01",
                "data_source": "CNIPA官方数据",
                "last_updated": "2026-01-05",
            },
        }

    except Exception as e:
        logger.error(f"获取IPC统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {e!s}") from e


@router.post("/ipc/domain/analyze")
async def analyze_patent_domain(request: IPCClassificationRequest):
    """
    分析专利技术领域

    - **title**: 专利标题(可选)
    - **abstract**: 专利摘要(可选)
    - **patent_text**: 专利权利要求或全文(必需)
    """
    try:
        domain_system = get_ipc_domain_system()
        if domain_system is None:
            raise HTTPException(status_code=503, detail="IPC领域分析服务不可用")

        # 执行领域分析
        analysis = await domain_system.analyze_patent_domain(
            patent_text=request.patent_text, patent_title=request.title or ""
        )

        # 格式化结果
        recommendations = []
        for rec in analysis.domain_recommendations:
            recommendations.append(
                {
                    "domain_name": rec.domain_name,
                    "category": rec.category.value,
                    "confidence": round(rec.confidence, 3),
                    "matched_ipcs": rec.matched_ipcs,
                    "key_features": rec.key_features,
                    "market_insight": rec.market_insight,
                }
            )

        return {
            "success": True,
            "analysis_time": analysis.analysis_time,
            "primary_domain": analysis.primary_domain,
            "secondary_domains": analysis.secondary_domains,
            "primary_ipc": analysis.primary_ipc,
            "recommended_ipcs": analysis.recommended_ipcs,
            "domain_recommendations": recommendations,
            "technical_keywords": analysis.technical_keywords,
            "innovation_level": analysis.innovation_level,
            "market_potential": analysis.market_potential,
            "legal_considerations": analysis.legal_considerations,
            "overall_confidence": round(analysis.overall_confidence, 3),
        }

    except Exception as e:
        logger.error(f"IPC领域分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {e!s}") from e


# 注册路由函数
def register_ipc_routes(app):
    """
    注册IPC分类路由到FastAPI应用

    Args:
        app: FastAPI应用实例
    """
    app.include_router(router)
    logger.info("✅ IPC分类API路由已注册")


if __name__ == "__main__":
    # 测试代码
    import uvicorn

    uvicorn.run(router, host="127.0.0.1", port=8001)  # 内网通信
