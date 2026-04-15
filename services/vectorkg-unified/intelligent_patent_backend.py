#!/usr/bin/env python3
"""
智能专利后端服务
Intelligent Patent Backend Service

基于向量库+知识图谱的统一智能后端，为专利等专业应用提供智能响应

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from vector_knowledge_infrastructure import get_vector_knowledge_infrastructure

from core.logging_config import setup_logging
from core.security.auth import ALLOWED_ORIGINS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="智能专利后端服务",
    description="基于向量库+知识图谱的统一智能后端",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局基础设施实例
infrastructure = None

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global infrastructure
    logger.info("正在初始化智能专利后端...")
    infrastructure = await get_vector_knowledge_infrastructure()
    logger.info("✅ 智能专利后端初始化完成")

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    global infrastructure
    if infrastructure:
        infrastructure.close()
    logger.info("智能专利后端服务已关闭")

# API端点

@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "智能专利后端服务",
        "architecture": "Vector + Knowledge Graph",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "vector_search": True,
            "graph_traversal": True,
            "hybrid_search": True,
            "domain_expertise": [
                "patent_law",
                "technical_analysis",
                "novelty_assessment",
                "creativity_evaluation"
            ]
        }
    }

@app.get("/infrastructure/stats")
async def get_infrastructure_stats():
    """获取基础设施统计"""
    if not infrastructure:
        raise HTTPException(status_code=503, detail="Infrastructure not initialized")

    stats = await infrastructure.get_infrastructure_stats()
    return stats

@app.post("/search/hybrid")
async def hybrid_search(request: dict):
    """
    混合搜索：向量检索 + 知识图谱推理

    请求体：
    {
        "query": "查询文本",
        "vector_threshold": 0.7,
        "max_vector_results": 10,
        "max_graph_paths": 5,
        "collections": ["patent_legal_vectors_1024", "patent_guideline"]
    }
    """
    if not infrastructure:
        raise HTTPException(status_code=503, detail="Infrastructure not initialized")

    try:
        # 提取参数
        query_text = request.get('query', '')
        vector_threshold = request.get('vector_threshold', 0.7)
        max_vector_results = request.get('max_vector_results', 10)
        max_graph_paths = request.get('max_graph_paths', 5)
        collections = request.get('collections')

        # 执行混合搜索
        results = await infrastructure.hybrid_search(
            query_text=query_text,
            vector_threshold=vector_threshold,
            max_vector_results=max_vector_results,
            max_graph_paths=max_graph_paths,
            collections=collections
        )

        # 添加元数据
        results['query_metadata'] = {
            "query_length": len(query_text),
            "search_time": datetime.now().isoformat(),
            "parameters": {
                "vector_threshold": vector_threshold,
                "max_vector_results": max_vector_results,
                "max_graph_paths": max_graph_paths
            }
        }

        return results

    except Exception as e:
        logger.error(f"混合搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}") from e

@app.post("/search/vector")
async def vector_search(request: dict):
    """纯向量搜索"""
    if not infrastructure:
        raise HTTPException(status_code=503, detail="Infrastructure not initialized")

    try:
        query_text = request.get('query', '')
        threshold = request.get('threshold', 0.7)
        max_results = request.get('max_results', 10)
        collections = request.get('collections')

        # 仅向量搜索
        vector_results = await infrastructure._vector_search(
            query_text=query_text,
            collections=collections,
            threshold=threshold,
            max_results=max_results
        )

        return {
            "results": vector_results,
            "total_found": len(vector_results),
            "metadata": {
                "search_type": "vector_only",
                "threshold": threshold,
                "max_results": max_results
            }
        }

    except Exception as e:
        logger.error(f"向量搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}") from e

@app.post("/search/graph")
async def graph_search(request: dict):
    """知识图谱搜索"""
    if not infrastructure:
        raise HTTPException(status_code=503, detail="Infrastructure not initialized")

    try:
        query_text = request.get('query', '')
        max_paths = request.get('max_paths', 5)
        request.get('graphs', [])

        # 图谱搜索
        graph_results = await infrastructure._graph_search(
            query_text=query_text,
            max_paths=max_paths
        )

        return {
            "results": graph_results,
            "total_found": len(graph_results),
            "metadata": {
                "search_type": "graph_only",
                "max_paths": max_paths
            }
        }

    except Exception as e:
        logger.error(f"图谱搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Graph search failed: {str(e)}") from e

@app.post("/analyze/patent")
async def analyze_patent(request: dict):
    """
    专利综合分析

    分析维度：
    - 新颖性评估
    - 创造性评估
    - 技术先进性
    - 法律风险评估
    - 市场价值分析
    """
    if not infrastructure:
        raise HTTPException(status_code=503, detail="Infrastructure not initialized")

    patent_text = request.get('patent_text', '')
    patent_title = request.get('title', '')
    request.get('ipc_classification', '')

    if not patent_text and not patent_title:
        raise HTTPException(status_code=400, detail="Patent text or title is required")

    # 构建分析查询
    analysis_results = {}

    # 1. 新颖性分析
    novelty_query = "评估专利的新颖性要求，判断是否属于现有技术"
    if patent_title:
        novelty_query += f"，专利标题：{patent_title}"

    novelty_results = await infrastructure.hybrid_search(
        query_text=novelty_query + " " + patent_text,
        context_type="novelty_assessment"
    )
    analysis_results['novelty'] = {
        "assessment": _extract_assessment(novelty_results),
        "key_points": _extract_key_points(novelty_results, "novelty"),
        "confidence": _calculate_confidence(novelty_results)
    }

    # 2. 创造性分析
    creativity_results = await infrastructure.hybrid_search(
        query_text="评估专利的创造性，包括技术进步性和非显而易见性" + patent_text,
        context_type="creativity_assessment"
    )
    analysis_results['creativity'] = {
        "assessment": _extract_assessment(creativity_results),
        "key_points": _extract_key_points(creativity_results, "creativity"),
        "confidence": _calculate_confidence(creativity_results)
    }

    # 3. 技术先进性
    tech_results = await infrastructure.hybrid_search(
        query_text="分析专利技术的先进性和创新程度" + patent_text,
        context_type="technical_analysis"
    )
    analysis_results['technical'] = {
        "assessment": _extract_assessment(tech_results),
        "key_points": _extract_key_points(tech_results, "technical"),
        "confidence": _calculate_confidence(tech_results)
    }

    # 4. 综合评分
    analysis_results['overall'] = {
        "novelty_score": analysis_results['novelty']['confidence'],
        "creativity_score": analysis_results['creativity']['confidence'],
        "technical_score": analysis_results['technical']['confidence'],
        "combined_score": _calculate_overall_score(analysis_results),
        "recommendations": _generate_recommendations(analysis_results)
    }

    return analysis_results

def _extract_assessment(self, search_results: dict) -> str:
    """从搜索结果中提取评估"""
    assessments = []

    # 从向量结果提取
    for result in search_results.get('vector_results', [])[:3]:
        content = result.get('content', '')
        if content:
            assessments.append(content[:200] + "...")

    # 从图谱结果提取
    for result in search_results.get('graph_results', [])[:3]:
        node_desc = result['node'].get('description', '')
        if node_desc:
            assessments.append(node_desc[:200] + "...")

    return " | ".join(assessments) if assessments else "暂无相关评估"

def _extract_key_points(self, search_results: dict, focus_area: str) -> list[str]:
    """提取关键点"""
    key_points = []

    # 根据关注领域提取特定关键词
    if focus_area == "novelty":
        novelty_keywords = ["现有技术", "申请日", "公开", "抵触申请", "不属于现有技术"]
    elif focus_area == "creativeity":
        pass
    else:
        novelty_keywords = ["创新", "技术方案", "技术效果"]

    # 从内容中提取
    all_content = " ".join([
        r.get('content', '') for r in search_results.get('vector_results', [])
    ])

    for keyword in novelty_keywords:
        if keyword.lower() in all_content.lower():
            # 获取上下文
            start = all_content.lower().find(keyword.lower())
            context_start = max(0, start - 50)
            context_end = min(len(all_content), start + len(keyword) + 100)
            context = all_content[context_start:context_end]
            key_points.append(f"- {keyword}: {context.strip()}")

    return key_points[:5]  # 限制数量

def _calculate_confidence(self, search_results: dict) -> float:
    """计算置信度"""
    vector_score = sum(r.get('score', 0) for r in search_results.get('vector_results', [])) / len(search_results.get('vector_results', [1]))

    graph_score = min(1.0, len(search_results.get('graph_results', [])) / 10.0)

    # 加权平均
    return vector_score * 0.7 + graph_score * 0.3

def _calculate_overall_score(self, analysis_results: dict) -> float:
    """计算综合评分"""
    novelty_score = analysis_results['novelty']['confidence']
    creativity_score = analysis_results['creativity']['confidence']
    technical_score = analysis_results['technical']['confidence']

    # 根据专利类型调整权重
    weights = {
        "novelty": 0.4,
        "creativity": 0.4,
        "technical": 0.2
    }

    return (novelty_score * weights['novelty'] +
            creativity_score * weights['creativity'] +
            technical_score * weights['technical'])

def _generate_recommendations(self, analysis_results: dict) -> list[str]:
    """生成建议"""
    recommendations = []

    overall_score = analysis_results['overall']['combined_score']

    if overall_score >= 0.8:
        recommendations.append("✅ 专利具有较高的可专利性，建议申请")
    elif overall_score >= 0.6:
        recommendations.append("⚠️ 专利有一定价值，建议完善技术方案后再申请")
    else:
        recommendations.append("❌ 专利可专利性较低，建议进行技术改进或考虑其他保护方式")

    # 根据具体分析结果给出建议
    if analysis_results['novelty']['confidence'] < 0.6:
        recommendations.append("- 建议进行现有技术检索，避免重复申请")

    if analysis_results['creativity']['confidence'] < 0.6:
        recommendations.append("- 建议进一步挖掘技术创新点，突出进步性")

    if analysis_results['technical']['confidence'] < 0.6:
        recommendations.append("- 建议提供更详细的技术实施例，确保可实施性")

    return recommendations

@app.post("/chat/intelligent")
async def intelligent_chat(request: dict):
    """
    智能对话接口
    """
    query = request.get('query', '')
    context = request.get('context', {})
    request.get('conversation_id')

    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    # 根据上下文和查询意图选择处理策略
    intent = _classify_intent(query, context)

    try:
        if intent == "search":
            return await _handle_search_intent(query, context)
        elif intent == "analysis":
            return await _handle_analysis_intent(query, context)
        elif intent == "guidance":
            return await _handle_guidance_intent(query, context)
        else:
            return await _provide_general_guidance(query, context)
    except Exception as e:
        logger.error(f"智能对话处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}") from e

async def _handle_search_intent(query: str, context: dict) -> dict:
    """处理搜索意图"""
    # 执行混合搜索
    search_results = await infrastructure.hybrid_search(
        query_text=query,
        collections=context.get('collections', [])
    )

    return {
        "type": "search_results",
        "results": search_results,
        "response": f"基于您的查询'{query}'，我找到了{len(search_results['vector_results'])}个相关文档和{len(search_results['graph_results'])}个知识点"
    }

async def _handle_analysis_intent(query: str, context: dict) -> dict:
    """处理分析意图"""
    # 检查是否有专利文本
    patent_text = context.get('patent_text')

    if patent_text:
        # 执行专利分析
        analysis = await analyze_patent({
            "patent_text": patent_text,
            "title": context.get('title'),
            "ipc_classification": context.get('ipc_classification')
        })

        return {
            "type": "patent_analysis",
            "analysis": analysis,
            "response": f"我已完成对您的专利的综合分析，整体评分{analysis['overall']['combined_score']:.2f}"
        }
    else:
        return {
            "type": "request_info",
            "message": "请提供专利文本以进行分析",
            "response": "请提供专利文本或技术方案描述"
        }

async def _handle_guidance_intent(query: str, context: dict) -> dict:
    """处理指导意图"""
    # 基于查询类型提供专业指导
    if "审查" in query:
        return await _provide_review_guidance(query, context)
    elif "申请" in query:
        return await _provide_filing_guidance(query, context)
    elif "侵权" in query:
        return await _provide_infringement_guidance(query, context)
    else:
        return await _provide_general_guidance(query, context)

async def _provide_review_guidance(query: str, context: dict) -> dict:
    """提供审查指导"""
    # 搜索审查相关的规则和案例
    search_results = await infrastructure.hybrid_search(
        query_text=f"专利审查标准和流程 {query}",
        max_vector_results=5
    )

    return {
        "type": "review_guidance",
        "guidance": _extract_guidance(search_results),
        "response": "根据专利审查要求，我为您找到了相关指导"
    }

async def _provide_filing_guidance(query: str, context: dict) -> dict:
    """提供申请指导"""
    search_results = await infrastructure.hybrid_search(
        query_text=f"专利申请流程和要求 {query}",
        max_vector_results=5
    )

    return {
        "type": "filing_guidance",
        "guidance": _extract_guidance(search_results),
        "response": "根据专利申请要求，我为您提供申请指导"
    }

async def _provide_infringement_guidance(query: str, context: dict) -> dict:
    """提供侵权指导"""
    search_results = await infrastructure.hybrid_search(
        query_text=f"专利侵权判断和风险评估 {query}",
        max_vector_results=5
    )

    return {
        "type": "infringement_guidance",
        "guidance": _extract_guidance(search_results),
        "response": "基于知识产权法律，我为您提供侵权风险分析"
    }

async def _provide_general_guidance(query: str, context: dict) -> dict:
    """提供一般指导"""
    search_results = await infrastructure.hybrid_search(
        query_text=f"专利相关指导 {query}",
        max_vector_results=5
    )

    return {
        "type": "general_guidance",
        "guidance": _extract_guidance(search_results),
        "response": "我为您提供专利相关的专业指导"
    }

def _extract_guidance(search_results: dict) -> str:
    """从搜索结果中提取指导"""
    guidance_points = []

    for result in search_results.get('vector_results', [])[:3]:
        content = result.get('content', '')
        if content:
            guidance_points.append(content[:150] + "...")

    return "\n\n".join(guidance_points) if guidance_points else "暂无相关指导信息"

def _classify_intent(query: str, context: dict) -> str:
    """分类用户意图"""
    query_lower = query.lower()

    # 关键词映射
    intent_keywords = {
        "search": ["搜索", "查找", "检索", "寻找", "相似"],
        "analysis": ["分析", "评估", "判断", "评价", "检查"],
        "guidance": ["指导", "建议", "如何", "怎么", "怎么办"],
        "filing": ["申请", "提交", "撰写", "准备"]
    }

    for intent, keywords in intent_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            return intent

    return "general"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
