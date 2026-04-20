#!/usr/bin/env python3
"""
PQAI专利检索测试服务
Test Service for Patent Search with PostgreSQL
"""

import asyncio
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import psycopg2
import uvicorn
from fastapi import FastAPI, HTTPException
from psycopg2.extras import RealDictCursor

# 添加路径
sys.path.append('/Users/xujian/Athena工作平台/services/autonomous-control')
from agent_identity import (
    AgentIdentity,
    AgentType,
    format_identity_display,
    register_agent_identity,
)

# 数据库配置
PATENT_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'patent_db'
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await display_startup_identity()
    # 测试数据库连接
    try:
        conn = psycopg2.connect(**PATENT_DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patents WHERE application_number IS NOT NULL")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print("✅ PostgreSQL专利数据库连接成功!")
        print(f"📊 专利数据库总量: {count:,} 件")
        app.state.db_available = True
    except Exception as e:
        print(f"⚠️ 数据库连接失败: {str(e)}")
        app.state.db_available = False
    yield
    # 关闭时执行
    print("🛑 PQAI专利检索专家服务已关闭")

app = FastAPI(
    title="PQAI专利检索测试服务",
    description="基于真实专利数据库的检索测试",
    lifespan=lifespan
)

# 创建PQAI分析师身份
pqai_identity = AgentIdentity(
    name="PQAI专利检索专家",
    type=AgentType.PATENT,
    version="Test 1.0",
    slogan="洞悉专利价值，数据驱动创新",
    specialization="专利检索与新颖性分析",
    capabilities={
        "专利检索": "基于PostgreSQL的实时专利数据库检索",
        "相似性分析": "专利相似度专业评估与排序",
        "测试验证": "服务功能验证与性能测试"
    },
    personality="专业、敏锐、客观、精准",
    work_mode="真实数据库 + 快速测试 + 验证功能",
    created_at=datetime.now()
)

# 注册身份
register_agent_identity("pqai_test", pqai_identity)

async def display_startup_identity():
    """启动时展示PQAI身份"""
    try:
        await asyncio.sleep(0.5)

        identity_display = await format_identity_display("pqai_test", "startup")

        print("\n" + "="*60)
        print(identity_display)
        print("\n🔍 PQAI专利检索专家 (测试版) 启动成功！")
        print("📍 服务端口: 8032")
        print("🗄️ 数据源: PostgreSQL专利数据库")
        print("="*60 + "\n")

    except Exception as e:
        print(f"⚠️ 身份展示失败: {str(e)}")

def get_db_connection() -> Any | None:
    """获取数据库连接"""
    try:
        conn = psycopg2.connect(**PATENT_DB_CONFIG)
        return conn
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        return None

def search_patents_simple(query_text: str, limit: int = 10) -> list[dict]:
    """简单的专利检索"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 使用简单的LIKE查询进行测试
        sql = """
            SELECT
                application_number,
                patent_name,
                applicant,
                abstract,
                ipc_main_class,
                application_date,
                publication_number
            FROM patents
            WHERE
                patent_name ILIKE %s OR
                abstract ILIKE %s OR
                applicant ILIKE %s
            ORDER BY application_date DESC
            LIMIT %s
        """

        search_pattern = f"%{query_text}%"
        cursor.execute(sql, (search_pattern, search_pattern, search_pattern, limit))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        patents = []
        for row in results:
            patents.append({
                "id": row['application_number'],
                "publication_number": row['publication_number'],
                "title": row['patent_name'],
                "applicant": row['applicant'],
                "abstract": row['abstract'][:200] + "..." if row['abstract'] and len(row['abstract']) > 200 else row['abstract'],
                "ipc_class": row['ipc_main_class'],
                "application_date": row['application_date'].isoformat() if row['application_date'] else None,
                "similarity": 0.8  # 固定相似度用于测试
            })

        return patents

    except Exception as e:
        print(f"专利检索错误: {str(e)}")
        return []

def calculate_simple_patentability(search_results: list[dict], query_text: str) -> tuple[float, dict[str, float]]:
    """简单的可申请性计算"""

    if not search_results:
        return 0.95, {"novelty": 0.95, "inventive": 0.90, "utility": 0.95}

    result_count = len(search_results)

    # 基于结果数量计算相似度影响
    novelty_score = max(0.3, 1.0 - result_count * 0.1)
    inventive_score = max(0.4, 1.0 - result_count * 0.08)
    utility_score = max(0.7, 1.0 - result_count * 0.05)

    overall_score = (novelty_score * 0.4 + inventive_score * 0.4 + utility_score * 0.2)

    return overall_score, {
        "novelty": novelty_score,
        "inventive": inventive_score,
        "utility": utility_score
    }

@app.get("/")
async def root():
    return {
        "message": "PQAI专利检索专家 - 测试版",
        "version": "Test 1.0",
        "status": "active",
        "database": "patent_db (PostgreSQL)",
        "note": "这是连接真实专利数据库的测试版本"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    if not app.state.db_available:
        return {
            "status": "unhealthy",
            "message": "数据库连接不可用",
            "service": "pqai_test"
        }

    # 再次测试数据库连接
    conn = get_db_connection()
    if conn:
        conn.close()
        return {
            "status": "healthy",
            "database": "connected",
            "service": "pqai_test",
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "status": "degraded",
            "message": "数据库连接异常",
            "service": "pqai_test"
        }

@app.get("/status")
async def status():
    """详细状态信息"""
    if not app.state.db_available:
        return {"status": "inactive", "service": "pqai_test"}

    conn = get_db_connection()
    if not conn:
        return {"status": "error", "service": "pqai_test"}

    try:
        cursor = conn.cursor()

        # 获取统计信息
        cursor.execute("SELECT COUNT(*) FROM patents WHERE application_number IS NOT NULL")
        total_patents = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT ipc_main_class) FROM patents WHERE ipc_main_class IS NOT NULL")
        ipc_classes = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            "status": "active",
            "service": "pqai_test",
            "database": {
                "total_patents": total_patents,
                "ipc_classes": ipc_classes,
                "connection": "active"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "pqai_test",
            "error": str(e)
        }

@app.post("/analyze")
async def analyze(request: dict):
    """专利分析测试接口"""
    text = request.get("text", "")

    if not text.strip():
        raise HTTPException(status_code=400, detail="分析文本不能为空")

    if not app.state.db_available:
        raise HTTPException(status_code=503, detail="数据库连接不可用")

    try:
        # 1. 执行专利检索
        similar_patents = search_patents_simple(text, limit=10)

        # 2. 计算可申请性
        overall_patentability, detail_scores = calculate_simple_patentability(similar_patents, text)

        # 3. 提取技术领域
        keywords_lower = text.lower()
        if any(kw in keywords_lower for kw in ['图像', '视觉', '识别', '检测', 'camera']):
            technical_field = 'Computer Vision / AI'
        elif any(kw in keywords_lower for kw in ['网络', '通信', '传输']):
            technical_field = 'Network Communications'
        elif any(kw in keywords_lower for kw in ['医疗', '诊断', '治疗']):
            technical_field = 'Medical Technology'
        else:
            technical_field = 'Information Technology'

        # 4. 主要IPC分类
        main_ipc = "G06F"  # 默认分类
        if similar_patents and similar_patents[0].get('ipc_class'):
            main_ipc = similar_patents[0]['ipc_class'][:10]

        return {
            "success": True,
            "patentability": round(overall_patentability, 3),
            "detail_scores": {k: round(v, 3) for k, v in detail_scores.items()},
            "technical_field": technical_field,
            "classification": main_ipc,
            "similar_patents_count": len(similar_patents),
            "similar_patents": similar_patents[:5],
            "analysis_summary": {
                "high_similarity_count": len(similar_patents),  # 测试版本简化
                "search_method": "LIKE查询（测试版）",
                "analysis_time": datetime.now().isoformat()
            },
            "note": "这是测试版本，使用简化的检索算法"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}") from e

@app.post("/search")
async def patent_search(request: dict):
    """纯专利检索测试接口"""
    query = request.get("query", "")
    limit = request.get("limit", 20)

    if not query.strip():
        raise HTTPException(status_code=400, detail="检索关键词不能为空")

    if not app.state.db_available:
        raise HTTPException(status_code=503, detail="数据库连接不可用")

    try:
        patents = search_patents_simple(query, limit)

        return {
            "success": True,
            "query": query,
            "total_results": len(patents),
            "patents": patents,
            "search_method": "LIKE查询（测试版）",
            "search_time": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}") from e

@app.get("/test/sample")
async def get_sample_patents():
    """获取样本专利数据用于测试"""
    if not app.state.db_available:
        raise HTTPException(status_code=503, detail="数据库连接不可用")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="无法连接数据库")

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                application_number,
                patent_name,
                applicant,
                ipc_main_class,
                application_date
            FROM patents
            WHERE patent_name IS NOT NULL AND applicant IS NOT NULL
            ORDER BY application_date DESC
            LIMIT 10
        """)

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        sample_patents = []
        for row in results:
            sample_patents.append({
                "application_number": row['application_number'],
                "patent_name": row['patent_name'][:100] + "..." if len(row['patent_name']) > 100 else row['patent_name'],
                "applicant": row['applicant'],
                "ipc_main_class": row['ipc_main_class'],
                "application_date": row['application_date'].isoformat() if row['application_date'] else None
            })

        return {
            "success": True,
            "sample_count": len(sample_patents),
            "sample_patents": sample_patents,
            "note": "这些是数据库中的真实专利样本"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取样本失败: {str(e)}") from e

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8032)  # 内网通信，通过Gateway访问
