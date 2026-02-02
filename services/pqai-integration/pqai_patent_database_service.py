#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PQAI专利分析服务 - 接入PostgreSQL专利数据库
Real Patent Analysis Service with PostgreSQL Integration
"""

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import uvicorn
from core.async_main import async_main
from datetime import datetime, timedelta
import asyncio
import sys
import os
import json
from core.database.unified_connection import get_postgres_pool
from typing import Dict, List, Optional, Any, Tuple
import re

# 添加路径
sys.path.append('/Users/xujian/Athena工作平台/services/autonomous-control')
from agent_identity import AgentIdentity, AgentType, register_agent_identity, format_identity_display

# 数据库配置
PATENT_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'patent_db',
    'min_size': 5,
    'max_size': 20
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await display_startup_identity()
    # 初始化数据库连接池
    try:
        app.state.db_db = await get_postgres_pool(**PATENT_DB_CONFIG)
        print("✅ PostgreSQL专利数据库连接成功!")

        # 测试数据库连接和数据量
        async with app.state.db_pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM patents WHERE application_number IS NOT NULL")
            print(f"📊 专利数据库总量: {count:,} 件")

    except Exception as e:
        print(f"⚠️ 数据库连接失败: {str(e)}")
        app.state.db_pool = None
    yield
    # 关闭时执行
    if hasattr(app.state, 'db_pool') and app.state.db_pool:
        await app.state.db_pool.close()
        print("🛑 数据库连接已关闭")

app = FastAPI(
    title="PQAI专利分析 - PostgreSQL集成版",
    description="基于真实专利数据库的专业检索分析服务",
    lifespan=lifespan
)

# 创建PQAI分析师身份
pqai_identity = AgentIdentity(
    name="PQAI专利检索专家",
    type=AgentType.PATENT,
    version="PostgreSQL 2.0",
    slogan="洞悉专利价值，数据驱动创新",
    specialization="专利检索与新颖性分析",
    capabilities={
        "专利检索": "基于PostgreSQL的实时专利数据库检索",
        "相似性分析": "专利相似度专业评估与排序",
        "侵权分析": "专利侵权风险预警与判断",
        "价值评估": "专利商业价值与技术价值评估",
        "新颖性分析": "基于真实数据的新颖性判断"
    },
    personality="专业、敏锐、客观、精准",
    work_mode="真实数据库 + 智能算法 + 实时分析",
    created_at=datetime.now()
)

# 注册身份
register_agent_identity("pqai_patent_database", pqai_identity)

async def display_startup_identity():
    """启动时展示PQAI身份"""
    try:
        await asyncio.sleep(0.5)

        identity_display = await format_identity_display("pqai_patent_database", "startup")

        print("\n" + "="*60)
        print(identity_display)
        print(f"\n🔍 PQAI专利检索专家 (PostgreSQL版) 启动成功！")
        print("📍 服务端口: 8031")
        print("🗄️ 数据源: PostgreSQL专利数据库")
        print("="*60 + "\n")

    except Exception as e:
        print(f"⚠️ 身份展示失败: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "PQAI专利检索专家 - PostgreSQL集成版",
        "version": "PostgreSQL 2.0",
        "status": "active",
        "database": "patent_db (PostgreSQL)"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    if not hasattr(app.state, 'db_pool') or not app.state.db_pool:
        return {
            "status": "unhealthy",
            "message": "数据库未连接",
            "service": "pqai_patent_database"
        }

    try:
        async with app.state.db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "service": "pqai_patent_database",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "message": str(e),
            "service": "pqai_patent_database"
        }

@app.get("/status")
async def status():
    """详细状态信息"""
    if not hasattr(app.state, 'db_pool') or not app.state.db_pool:
        return {"status": "inactive", "service": "pqai_patent_database"}

    try:
        async with app.state.db_pool.acquire() as conn:
            # 获取数据库统计信息
            total_patents = await conn.fetchval(
                "SELECT COUNT(*) FROM patents WHERE application_number IS NOT NULL"
            )

            recent_patents = await conn.fetchval(
                "SELECT COUNT(*) FROM patents WHERE application_date >= CURRENT_DATE - INTERVAL '1 year'"
            )

            ipc_classes = await conn.fetchval(
                "SELECT COUNT(DISTINCT ipc_main_class) FROM patents WHERE ipc_main_class IS NOT NULL"
            )

        return {
            "status": "active",
            "service": "pqai_patent_database",
            "database": {
                "total_patents": total_patents,
                "recent_patents": recent_patents,
                "ipc_classes": ipc_classes,
                "connection_pool": "active"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "pqai_patent_database",
            "error": str(e)
        }

async def search_similar_patents(db_pool, query_text: str, limit: int = 10) -> List[Dict]:
    """执行相似专利检索"""
    try:
        async with db_pool.acquire() as conn:
            # 构建检索SQL - 使用全文检索和相似度排序
            sql = """
                WITH search_query AS (
                    SELECT plainto_tsquery('chinese', $1) as query
                )
                SELECT
                    p.application_number,
                    p.patent_name,
                    p.applicant,
                    p.abstract,
                    p.ipc_main_class,
                    p.application_date,
                    p.publication_number,
                    ts_rank(p.search_vector, q.query) as similarity
                FROM patents p, search_query q
                WHERE p.search_vector @@ q.query
                ORDER BY
                    similarity DESC,
                    p.application_date DESC
                LIMIT $2
            """

            results = await conn.fetch(sql, query_text, limit)

            similar_patents = []
            for row in results:
                similar_patents.append({
                    "id": row['application_number'],
                    "publication_number": row['publication_number'],
                    "title": row['patent_name'],
                    "applicant": row['applicant'],
                    "abstract": row['abstract'][:200] + "..." if row['abstract'] and len(row['abstract']) > 200 else row['abstract'],
                    "ipc_class": row['ipc_main_class'],
                    "application_date": row['application_date'].isoformat() if row['application_date'] else None,
                    "similarity": float(row['similarity'])
                })

            return similar_patents

    except Exception as e:
        print(f"专利检索错误: {str(e)}")
        return []

def calculate_patentability(similar_patents: List[Dict]) -> Tuple[float, Dict[str, float]]:
    """基于相似专利计算可申请性"""

    if not similar_patents:
        return 0.95, {"novelty": 0.95, "inventive": 0.90, "utility": 0.95}

    # 最高相似度
    max_similarity = max([p['similarity'] for p in similar_patents])

    # 最近3年的相似专利数量
    recent_date = datetime.now() - timedelta(days=3*365)
    recent_count = len([p for p in similar_patents
                      if p['application_date'] and
                      datetime.fromisoformat(p['application_date']) > recent_date])

    # 同一技术领域的专利密度
    ipc_density = {}
    for p in similar_patents:
        ipc = p.get('ipc_class', '')
        if ipc:
            ipc_density[ipc[:3]] = ipc_density.get(ipc[:3], 0) + 1
    max_ipc_density = max(ipc_density.values()) if ipc_density else 0

    # 计算各项指标
    novelty_score = max(0.0, 1.0 - max_similarity * 1.2)
    inventive_score = max(0.0, 0.8 - recent_count * 0.1 - max_similarity * 0.5)
    utility_score = max(0.0, 0.9 - max_ipc_density * 0.05)

    # 综合评分
    overall_score = (novelty_score * 0.4 + inventive_score * 0.4 + utility_score * 0.2)

    return min(1.0, overall_score), {
        "novelty": novelty_score,
        "inventive": inventive_score,
        "utility": utility_score
    }

def extract_technical_field(text: str, ipc_classes: List[str]) -> str:
    """基于IPC分类和关键词提取技术领域"""

    # IPC分类映射
    ipc_mapping = {
        'G06K': '图像识别/字符识别',
        'G06F': '数据处理/计算',
        'G06N': '人工智能/神经网络',
        'H04L': '通信网络/数据传输',
        'H04N': '图像通信/电视',
        'A61B': '医疗诊断/设备',
        'C07D': '有机化学/医药',
        'G01N': '测量/测试',
        'B23Q': '机床/加工',
        'H01L': '半导体/集成电路'
    }

    # 关键词检测
    keywords_lower = text.lower()

    if any(kw in keywords_lower for kw in ['图像', '视觉', '识别', '检测', 'camera', 'vision']):
        return 'Computer Vision / AI'
    elif any(kw in keywords_lower for kw in ['网络', '通信', '传输', 'network', 'communication']):
        return 'Network Communications'
    elif any(kw in keywords_lower for kw in ['医疗', '诊断', '治疗', 'medical', 'diagnosis']):
        return 'Medical Technology'
    elif any(kw in keywords_lower for kw in ['机器', '加工', '制造', 'manufacturing', 'machine']):
        return 'Manufacturing'
    else:
        return 'Information Technology'

@app.post("/analyze")
async def analyze(request: dict):
    """专利分析主接口"""
    text = request.get("text", "")

    if not text.strip():
        raise HTTPException(status_code=400, detail="分析文本不能为空")

    if not hasattr(app.state, 'db_pool') or not app.state.db_pool:
        raise HTTPException(status_code=503, detail="数据库连接不可用")

    try:
        # 1. 执行相似专利检索
        similar_patents = await search_similar_patents(app.state.db_pool, text, limit=10)

        # 2. 计算可申请性
        overall_patentability, detail_scores = calculate_patentability(similar_patents)

        # 3. 提取技术领域
        ipc_classes = [p.get('ipc_class', '') for p in similar_patents if p.get('ipc_class')]
        technical_field = extract_technical_field(text, ipc_classes)

        # 4. 主要IPC分类
        main_ipc = ipc_classes[0][:10] if ipc_classes else "G06F"

        return {
            "success": True,
            "patentability": round(overall_patentability, 3),
            "detail_scores": {k: round(v, 3) for k, v in detail_scores.items()},
            "technical_field": technical_field,
            "classification": main_ipc,
            "similar_patents_count": len(similar_patents),
            "similar_patents": similar_patents[:5],  # 返回前5个最相似的
            "analysis_summary": {
                "high_similarity_count": len([p for p in similar_patents if p['similarity'] > 0.8]),
                "recent_patents": len([p for p in similar_patents
                                    if p['application_date'] and
                                    datetime.fromisoformat(p['application_date']) > datetime.now() - timedelta(days=365*3)]),
                "analysis_time": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@app.post("/search")
async def patent_search(request: dict):
    """纯专利检索接口"""
    query = request.get("query", "")
    limit = request.get("limit", 20)

    if not query.strip():
        raise HTTPException(status_code=400, detail="检索关键词不能为空")

    if not hasattr(app.state, 'db_pool') or not app.state.db_pool:
        raise HTTPException(status_code=503, detail="数据库连接不可用")

    try:
        similar_patents = await search_similar_patents(app.state.db_pool, query, limit)

        return {
            "success": True,
            "query": query,
            "total_results": len(similar_patents),
            "patents": similar_patents,
            "search_time": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")

@app.get("/database/stats")
async def database_statistics():
    """数据库统计信息"""
    if not hasattr(app.state, 'db_pool') or not app.state.db_pool:
        raise HTTPException(status_code=503, detail="数据库连接不可用")

    try:
        async with app.state.db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_patents,
                    COUNT(DISTINCT applicant) as unique_applicants,
                    COUNT(DISTINCT ipc_main_class) as ipc_classes,
                    COUNT(DISTINCT source_year) as years_covered,
                    COUNT(*) FILTER (WHERE application_date >= CURRENT_DATE - INTERVAL '1 year') as recent_patents
                FROM patents
                WHERE application_number IS NOT NULL
            """)

            # 按年份统计
            yearly_stats = await conn.fetch("""
                SELECT source_year, COUNT(*) as count
                FROM patents
                WHERE source_year IS NOT NULL AND source_year >= 2010
                GROUP BY source_year
                ORDER BY source_year DESC
                LIMIT 10
            """)

            return {
                "overview": dict(stats),
                "yearly_distribution": [
                    {"year": row['source_year'], "patents": row['count']}
                    for row in yearly_stats
                ]
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8031)