#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PQAI专利检索 - 简化测试版
Simplified Patent Search Test Service
"""

from fastapi import FastAPI, HTTPException
import uvicorn
from datetime import datetime
import asyncio
import sys
import os
from typing import Dict, List
import json

# 添加路径
sys.path.append('/Users/xujian/Athena工作平台/services/autonomous-control')
from agent_identity import AgentIdentity, AgentType, register_agent_identity, format_identity_display

app = FastAPI(title="PQAI专利检索 - 简化测试")

# 创建身份
pqai_identity = AgentIdentity(
    name="PQAI专利检索测试",
    type=AgentType.PATENT,
    version="Simple Test 1.0",
    slogan="简化测试，验证功能",
    specialization="专利检索功能测试",
    capabilities={
        "功能测试": "验证专利检索接口",
        "数据验证": "检查数据库连接",
        "接口测试": "测试API响应"
    },
    personality="测试、验证、简单",
    work_mode="模拟数据 + 接口测试",
    created_at=datetime.now()
)

register_agent_identity("pqai_simple_test", pqai_identity)

# 模拟专利数据库（用于测试）
MOCK_PATENT_DB = [
    {
        "application_number": "CN202310123456.7",
        "patent_name": "基于深度学习的图像识别方法及系统",
        "applicant": "北京科技大学",
        "abstract": "本发明公开了一种基于深度学习的图像识别方法...",
        "ipc_main_class": "G06K",
        "application_date": "2023-03-15",
        "publication_number": "CN116567890A"
    },
    {
        "application_number": "CN202310234567.8",
        "patent_name": "智能语音识别系统的优化方法",
        "applicant": "清华大学",
        "abstract": "本发明涉及人工智能技术领域，提供了一种智能语音识别系统...",
        "ipc_main_class": "G10L",
        "application_date": "2023-04-20",
        "publication_number": "CN116678901A"
    },
    {
        "application_number": "CN202310345678.9",
        "patent_name": "基于神经网络的机器学习算法",
        "applicant": "上海交通大学",
        "abstract": "本发明涉及机器学习技术领域，特别是神经网络优化算法...",
        "ipc_main_class": "G06N",
        "application_date": "2023-05-10",
        "publication_number": "CN116789012A"
    },
    {
        "application_number": "CN202310456789.0",
        "patent_name": "数据加密传输的安全系统",
        "applicant": "深圳大学",
        "abstract": "本发明涉及信息安全技术领域，提供了一种数据加密传输的安全系统...",
        "ipc_main_class": "H04L",
        "application_date": "2023-06-15",
        "publication_number": "CN116890123A"
    },
    {
        "application_number": "CN202310567890.1",
        "patent_name": "物联网设备的智能控制系统",
        "applicant": "浙江大学",
        "abstract": "本发明涉及物联网技术领域，提供了一种物联网设备的智能控制系统...",
        "ipc_main_class": "H04L",
        "application_date": "2023-07-20",
        "publication_number": "CN116901234A"
    }
]

async def display_startup_identity():
    """启动时展示身份"""
    try:
        await asyncio.sleep(0.5)
        identity_display = await format_identity_display("pqai_simple_test", "startup")
        print("\n" + "="*50)
        print(identity_display)
        print(f"\n🔍 PQAI专利检索测试服务启动成功！")
        print("📍 服务端口: 8033")
        print("📋 数据来源: 模拟专利数据（测试用）")
        print("="*50 + "\n")
    except Exception as e:
        print(f"⚠️ 身份展示失败: {str(e)}")

@app.on_event("startup")
async def startup_event():
    await display_startup_identity()

@app.get("/")
async def root():
    return {
        "message": "PQAI专利检索测试服务",
        "version": "Simple Test 1.0",
        "status": "active",
        "data_source": "模拟数据（测试版）"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "pqai_simple_test",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def status():
    return {
        "status": "active",
        "service": "pqai_simple_test",
        "mock_data_count": len(MOCK_PATENT_DB),
        "available_tests": ["analyze", "search", "sample"]
    }

@app.post("/analyze")
async def analyze(request: dict):
    """专利分析测试接口"""
    text = request.get("text", "")

    if not text.strip():
        raise HTTPException(status_code=400, detail="分析文本不能为空")

    # 简单的关键词匹配
    keywords_lower = text.lower()
    matched_patents = []

    for patent in MOCK_PATENT_DB:
        score = 0
        patent_text = f"{patent['patent_name']} {patent['abstract']}".lower()

        # 计算匹配分数
        for keyword in keywords_lower.split():
            if keyword in patent_text:
                score += 1

        if score > 0:
            patent_copy = patent.copy()
            patent_copy['similarity'] = min(0.9, score * 0.2)
            matched_patents.append(patent_copy)

    # 排序
    matched_patents.sort(key=lambda x: x['similarity'], reverse=True)

    # 计算可申请性
    if matched_patents:
        max_similarity = matched_patents[0]['similarity']
        patentability = max(0.3, 1.0 - max_similarity * 0.8)
    else:
        patentability = 0.95

    # 技术领域判断
    if any(kw in keywords_lower for kw in ['图像', '视觉', '识别', '检测']):
        technical_field = 'Computer Vision / AI'
    elif any(kw in keywords_lower for kw in ['语音', '声音', '音频']):
        technical_field = 'Audio Processing'
    elif any(kw in keywords_lower for kw in ['网络', '通信', '传输']):
        technical_field = 'Network Communications'
    else:
        technical_field = 'Information Technology'

    return {
        "success": True,
        "patentability": round(patentability, 3),
        "technical_field": technical_field,
        "classification": matched_patents[0]['ipc_main_class'] if matched_patents else "G06F",
        "similar_patents_count": len(matched_patents),
        "similar_patents": matched_patents[:3],
        "analysis_summary": {
            "match_method": "关键词匹配（测试版）",
            "analysis_time": datetime.now().isoformat()
        },
        "note": "这是测试版本，使用模拟数据和简化算法"
    }

@app.post("/search")
async def search(request: dict):
    """专利检索测试接口"""
    query = request.get("query", "")
    limit = request.get("limit", 10)

    if not query.strip():
        raise HTTPException(status_code=400, detail="检索关键词不能为空")

    # 关键词匹配
    keywords_lower = query.lower()
    results = []

    for patent in MOCK_PATENT_DB:
        patent_text = f"{patent['patent_name']} {patent['abstract']} {patent['applicant']}".lower()

        if any(keyword in patent_text for keyword in keywords_lower.split()):
            patent_copy = patent.copy()
            patent_copy['relevance'] = 0.8  # 固定相关性分数
            results.append(patent_copy)

    return {
        "success": True,
        "query": query,
        "total_results": len(results),
        "patents": results[:limit],
        "search_method": "关键词匹配（测试版）",
        "search_time": datetime.now().isoformat()
    }

@app.get("/test/sample")
async def get_sample():
    """获取样本数据"""
    return {
        "success": True,
        "sample_count": len(MOCK_PATENT_DB),
        "patents": MOCK_PATENT_DB,
        "note": "这是模拟的专利数据，用于测试服务功能"
    }

@app.get("/test/db-connection")
async def test_db_connection():
    """测试真实数据库连接"""
    try:
        import asyncpg

        # 尝试连接真实数据库
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='patent_db'
        )

        count = await conn.fetchval('SELECT COUNT(*) FROM patents WHERE application_number IS NOT NULL')
        await conn.close()

        return {
            "success": True,
            "database": "patent_db",
            "patent_count": count,
            "message": "成功连接到真实PostgreSQL专利数据库"
        }

    except ImportError:
        return {
            "success": False,
            "error": "asyncpg模块未安装",
            "message": "无法测试数据库连接"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "数据库连接失败"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8033)