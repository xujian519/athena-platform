#!/usr/bin/env python3
"""
技术趋势分析演示服务
Technology Trend Analysis Demo
基于真实专利数据的技术发展趋势分析演示
"""

import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, HTTPException

from core.database.unified_connection import get_postgres_pool

logger = logging.getLogger(__name__)

# 添加路径
sys.path.append('/Users/xujian/Athena工作平台/services/autonomous-control')
from agent_identity import AgentIdentity, AgentType, register_agent_identity

# 数据库配置
PATENT_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'infrastructure/infrastructure/database': 'patent_db'
}

app = FastAPI(title="技术趋势分析演示服务")

# 创建分析师身份
trend_analyzer_identity = AgentIdentity(
    name="技术趋势分析演示",
    type=AgentType.PATENT,
    version="Demo 1.0",
    slogan="基于真实数据的趋势洞察",
    specialization="专利技术趋势演示分析",
    capabilities={
        "IPC趋势分析": "基于IPC分类的技术趋势分析",
        "申请人分析": "主要申请人竞争态势分析",
        "时间序列分析": "专利申请的时间分布分析",
        "技术热点识别": "高增长技术领域识别"
    },
    personality="数据驱动、分析导向、专业",
    work_mode="真实数据 + 统计分析 + 趋势洞察",
    created_at=datetime.now()
)

register_agent_identity("trend_demo", trend_analyzer_identity)

# 全局数据库连接
db_pool = None

@app.on_event("startup")
async def startup_event():
    global db_pool
    try:
        await get_postgres_pool(**PATENT_DB_CONFIG)
        print("✅ 数据库连接成功!")
        print("🔍 技术趋势分析演示服务启动成功！")
        print("📍 服务端口: 8036")
    except Exception as e:
        print(f"⚠️ 数据库连接失败: {str(e)}")
        db_pool = None

@app.on_event("shutdown")
async def shutdown_event():
    global db_pool
    if db_pool:
        await db_pool.close()
        print("🛑 数据库连接已关闭")

async def get_ipc_trend_analysis(ipc_class: str, years: int = 5) -> dict:
    """分析特定IPC分类的技术趋势"""
    if not db_pool:
        return {"error": "数据库未连接"}

    async with db_pool.acquire() as conn:
        # 获取时间序列数据
        cutoff_date = datetime.now() - timedelta(days=years * 365)

        yearly_data = await conn.fetch("""
            SELECT
                EXTRACT(YEAR FROM application_date) as year,
                COUNT(*) as patent_count,
                COUNT(DISTINCT applicant) as applicant_count
            FROM patents
            WHERE ipc_main_class LIKE $1 || '%'
                AND application_date >= $2
                AND application_number IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM application_date)
            ORDER BY year
        """, ipc_class, cutoff_date)

        if not yearly_data:
            return {"error": f"未找到IPC分类 {ipc_class} 的专利数据"}

        # 计算趋势指标
        [row['year'] for row in yearly_data]
        counts = [row['patent_count'] for row in yearly_data]

        # 计算增长率
        if len(counts) >= 2:
            recent_growth = ((counts[-1] - counts[0]) / max(counts[0], 1)) * 100
        else:
            recent_growth = 0

        # 获取主要申请人
        top_applicants = await conn.fetch("""
            SELECT applicant, COUNT(*) as count
            FROM patents
            WHERE ipc_main_class LIKE $1 || '%'
                AND application_date >= $2
                AND applicant IS NOT NULL
            GROUP BY applicant
            ORDER BY count DESC
            LIMIT 5
        """, ipc_class, cutoff_date)

        return {
            "ipc_class": ipc_class,
            "analysis_period": f"最近{years}年",
            "yearly_trend": [
                {"year": int(row['year']), "apps/apps/patents": row['patent_count'], "applicants": row['applicant_count']}
                for row in yearly_data
            ],
            "growth_rate": round(recent_growth, 2),
            "total_patents": sum(counts),
            "top_applicants": [
                {"name": row['applicant'], "patent_count": row['count']}
                for row in top_applicants
            ],
            "trend_assessment": "快速增长" if recent_growth > 50 else "稳定增长" if recent_growth > 0 else "下降趋势"
        }

async def get_overall_trends(years: int = 5) -> dict:
    """获取整体技术趋势"""
    if not db_pool:
        return {"error": "数据库未连接"}

    async with db_pool.acquire() as conn:
        cutoff_date = datetime.now() - timedelta(days=years * 365)

        # 主要技术领域趋势
        top_ipc_trends = await conn.fetch("""
            SELECT
                ipc_main_class,
                EXTRACT(YEAR FROM application_date) as year,
                COUNT(*) as count
            FROM patents
            WHERE application_date >= $1
                AND ipc_main_class IS NOT NULL
                AND ipc_main_class != ''
            GROUP BY ipc_main_class, EXTRACT(YEAR FROM application_date)
            ORDER BY ipc_main_class, year
        """, cutoff_date)

        # 按IPC分类组织数据
        ipc_data = defaultdict(list)
        for row in top_ipc_trends:
            ipc_data[row['ipc_main_class']].append({
                "year": int(row['year']),
                "count": row['count']
            })

        # 计算每个领域的增长率
        growth_rates = {}
        for ipc, data in ipc_data.items():
            if len(data) >= 2:
                counts = [d['count'] for d in data]
                growth = ((counts[-1] - counts[0]) / max(counts[0], 1)) * 100
                growth_rates[ipc] = growth

        # 找出增长最快的技术领域
        top_growth = sorted(growth_rates.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "analysis_period": f"最近{years}年",
            "top_growth_technologies": [
                {
                    "ipc_class": ipc,
                    "growth_rate": round(growth, 2),
                    "technology_name": get_technology_name(ipc)
                }
                for ipc, growth in top_growth
            ],
            "technology_summary": {
                ipc: {
                    "total_patents": sum(d['count'] for d in data),
                    "years_covered": len(data),
                    "latest_year": max(d['year'] for d in data) if data else None,
                    "growth_rate": round(growth_rates.get(ipc, 0), 2)
                }
                for ipc, data in list(ipc_data.items())[:20]  # 限制返回数量
            }
        }

def get_technology_name(ipc_class: str) -> str:
    """获取IPC分类对应的技术名称"""
    tech_mapping = {
        "G06F": "计算机技术/数据处理",
        "G06N": "人工智能/机器学习",
        "G06K": "数据识别/图像处理",
        "H04L": "通信网络/数据传输",
        "H04W": "无线通信",
        "A61B": "医疗诊断/设备",
        "A61K": "医学/制药",
        "B01D": "分离技术",
        "B65G": "搬运/输送设备",
        "C02F": "水处理",
        "C07": "有机化学",
        "H01M": "电池技术",
        "H02J": "电力系统"
    }
    return tech_mapping.get(ipc_class[:4], f"技术领域({ipc_class[:4]})")

@app.get("/")
async def root():
    return {
        "message": "技术趋势分析演示服务",
        "version": "Demo 1.0",
        "status": "active",
        "description": "基于真实专利数据库的技术趋势分析演示"
    }

@app.get("/health")
async def health():
    if not db_pool:
        return {"status": "unhealthy", "message": "数据库未连接"}

    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "infrastructure/infrastructure/database": "connected"}
    except Exception as e:
        logger.debug(f"空except块已触发: {e}")
        return {"status": "degraded", "message": "数据库连接异常"}

@app.post("/analyze_ipc_trend")
async def analyze_ipc_trend(request: dict):
    """分析特定IPC分类的趋势"""
    ipc_class = request.get("ipc_class", "")
    years = request.get("years", 5)

    if not ipc_class:
        raise HTTPException(status_code=400, detail="IPC分类不能为空")

    try:
        analysis = await get_ipc_trend_analysis(ipc_class, years)

        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])

        return {
            "success": True,
            "analysis": analysis,
            "analysis_time": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}") from e

@app.post("/get_overall_trends")
async def get_overall_trends_api(request: dict):
    """获取整体技术趋势"""
    years = request.get("years", 5)

    try:
        trends = await get_overall_trends(years)

        if "error" in trends:
            raise HTTPException(status_code=500, detail=trends["error"])

        return {
            "success": True,
            "trends": trends,
            "analysis_time": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势失败: {str(e)}") from e

@app.get("/get_sample_trends")
async def get_sample_trends():
    """获取样本趋势分析"""
    sample_ipc_classes = ["G06F", "H04L", "A61B", "G01N", "A61K"]

    try:
        results = []
        for ipc in sample_ipc_classes:
            analysis = await get_ipc_trend_analysis(ipc, 5)
            if "error" not in analysis:
                results.append(analysis)

        return {
            "success": True,
            "sample_count": len(results),
            "sample_trends": results,
            "note": f"分析了{len(sample_ipc_classes)}个主要技术领域"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取样本失败: {str(e)}") from e

@app.post("/analyze_competition")
async def analyze_competition(request: dict):
    """分析竞争格局"""
    ipc_class = request.get("ipc_class", "")
    years = request.get("years", 5)

    if not ipc_class:
        raise HTTPException(status_code=400, detail="IPC分类不能为空")

    if not db_pool:
        raise HTTPException(status_code=503, detail="数据库未连接")

    try:
        cutoff_date = datetime.now() - timedelta(days=years * 365)

        async with db_pool.acquire() as conn:
            # 获取申请人竞争分析
            competition_data = await conn.fetch("""
                SELECT
                    applicant,
                    COUNT(*) as patent_count,
                    COUNT(DISTINCT EXTRACT(YEAR FROM application_date)) as active_years,
                    MIN(EXTRACT(YEAR FROM application_date)) as first_year,
                    MAX(EXTRACT(YEAR FROM application_date)) as last_year
                FROM patents
                WHERE ipc_main_class LIKE $1 || '%'
                    AND application_date >= $2
                    AND applicant IS NOT NULL
                GROUP BY applicant
                HAVING COUNT(*) >= 10
                ORDER BY patent_count DESC
                LIMIT 20
            """, ipc_class, cutoff_date)

            # 计算市场集中度
            total_patents = sum(row['patent_count'] for row in competition_data)
            top5_share = sum(row['patent_count'] for row in competition_data[:5]) / max(total_patents, 1) * 100

            # 分析竞争激烈程度
            if top5_share > 60:
                competition_level = "高度集中"
            elif top5_share > 40:
                competition_level = "中等集中"
            else:
                competition_level = "充分竞争"

            return {
                "success": True,
                "ipc_class": ipc_class,
                "technology_name": get_technology_name(ipc_class),
                "competition_analysis": {
                    "total_competitors": len(competition_data),
                    "total_patents": total_patents,
                    "top5_market_share": round(top5_share, 2),
                    "competition_level": competition_level,
                    "top_competitors": [
                        {
                            "rank": i + 1,
                            "name": row['applicant'],
                            "patent_count": row['patent_count'],
                            "market_share": round(row['patent_count'] / max(total_patents, 1) * 100, 2),
                            "active_years": int(row['active_years']),
                            "year_span": int(row['last_year'] - row['first_year']) + 1 if row['first_year'] and row['last_year'] else 0
                        }
                        for i, row in enumerate(competition_data[:10])
                    ]
                },
                "analysis_time": datetime.now().isoformat()
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"竞争分析失败: {str(e)}") from e

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8036)
