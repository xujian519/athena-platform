#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整案例推荐系统
Comprehensive Case Recommendation System

功能：
1. 多维度相似案例检索
2. 技术领域智能识别
3. 争议焦点分析
4. 胜诉率预测
5. 参考价值评估
6. 案例对比分析
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import psycopg2
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
from collections import Counter
from dotenv import load_dotenv

# GLM-4.7
from zhipuai import ZhipuAI
import os

# 加载环境变量
# 注意：此服务使用平台统一的环境变量配置
# 加载顺序：服务专用配置 -> 平台配置
service_dir = os.path.dirname(os.path.abspath(__file__))
service_env = os.path.join(service_dir, ".env.local")
platform_env = "/Users/xujian/Athena工作平台/.env"

# 先加载平台配置，再加载服务专用配置（后者优先）
load_dotenv(platform_env)
if os.path.exists(service_env):
    load_dotenv(service_env, override=True)

logging.basicConfig(level=logging.INFO)
logger = setup_logging()

if os.path.exists(service_env):
    logger.info(f"Loaded service-specific config: {service_env}")

# ============ 模块级常量 ============

# 技术领域关键词映射（用于识别）
TECHNOLOGY_FIELD_KEYWORDS = {
    '机械结构': ['机械', '结构', '装置', '设备', '连接', '固定', '组件', '零件'],
    '化学材料': ['化学', '材料', '组合物', '合金', '聚合物', '催化剂', '合成'],
    '电学通信': ['电路', '电子', '通信', '半导体', '芯片', '信号', '天线', '频率'],
    '计算机软件': ['软件', '程序', '算法', '数据处理', '计算机', '网络', '系统'],
    '医药生物': ['医药', '药物', '生物', '医疗', '治疗', '疫苗', '抗体', '基因'],
    '医疗器械': ['医疗设备', '医疗器械', '诊断', '治疗设备', '手术'],
    '光电显示': ['光学', '显示', '屏幕', 'LED', '激光', '图像'],
    '汽车制造': ['汽车', '车辆', '发动机', '制动', '转向', '驾驶'],
}

# 技术领域关键词映射（用于搜索）
FIELD_KEYWORD_MAP = {
    '机械结构': ['机械', '结构'],
    '化学材料': ['化学', '材料'],
    '电学通信': ['电学', '通信'],
    '计算机软件': ['计算机', '软件'],
    '医药生物': ['医药', '生物'],
    '医疗器械': ['医疗', '器械'],
    '光电显示': ['光电', '显示'],
    '汽车制造': ['汽车', '制造'],
}

# 争议类型关键词映射
ISSUE_KEYWORD_MAP = {
    '创造性': ['创造性', '显而易见', '技术启示', '区别技术特征', '实质性特点'],
    '新颖性': ['新颖性', '现有技术', '公开', '记载'],
    '实用性': ['实用性', '产业应用', '能够制造', '积极效果'],
    '充分公开': ['充分公开', '说明书', '实现', '清楚完整'],
    '修改超范围': ['修改超范围', '原说明书', '权利要求', '记载'],
    '单一性': ['单一性', '总的发明构思', '同类技术'],
}

# 决定结果参考价值映射
DECISION_RESULT_SCORES = {
    'all_invalid': 'high',
    'part_invalid': 'medium',
    'all_valid': 'low',
    'maintain_valid': 'low'
}

# 参考价值评分
REFERENCE_VALUE_SCORES = {'very_high': 4, 'high': 3, 'medium': 2, 'low': 1}

app = FastAPI(
    title="专利案例推荐系统",
    description="基于多维度分析的智能案例推荐系统",
    version="v1.0.0"
)

# CORS配置 - 从环境变量读取允许的来源
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库连接
pg_conn = None
pg_cursor = None

# GLM客户端
glm_client = None
GLM_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")

def init_db() -> Any:
    """
    初始化数据库连接，使用平台统一的环境变量配置

    环境变量：
        DB_HOST: 数据库主机（默认：localhost）
        DB_PORT: 数据库端口（默认：5432）
        DB_NAME: 数据库名称（默认：athena）
        DB_USER: 数据库用户（默认：xujian）
        DB_PASSWORD: 数据库密码
        DB_TABLE_DECISIONS: 无效决定表名（默认：patent_invalidation_decisions）

    注意：
        - athena数据库包含结构化的专利无效决定数据（31564条记录）
        - patent_legal_db数据库包含原始文档数据
    """
    global pg_conn, pg_cursor

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", 5432))
    # 优先使用athena数据库，它包含结构化的案例数据
    db_name = os.getenv("DB_NAME", "athena")
    db_user = os.getenv("DB_USER", "xujian")
    db_password = os.getenv("DB_PASSWORD", "")

    try:
        pg_conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        pg_cursor = pg_conn.cursor()
        logger.info(f"PostgreSQL connected: {db_host}:{db_port}/{db_name}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def get_decisions_table_name() -> str:
    """
    获取无效决定表名，支持环境变量配置

    默认使用patent_invalidation_decisions（athena数据库中的结构化表）
    """
    return os.getenv("DB_TABLE_DECISIONS", "patent_invalidation_decisions")

def init_glm() -> Any:
    global glm_client
    if GLM_API_KEY:
        glm_client = ZhipuAI(api_key=GLM_API_KEY)
        logger.info("GLM-4.7 client initialized")

@app.on_event("startup")
async def startup():
    init_db()
    init_glm()

@app.on_event("shutdown")
async def shutdown():
    if pg_cursor:
        pg_cursor.close()
    if pg_conn:
        pg_conn.close()

# ============ 数据模型 ============

class CaseRecommendationRequest(BaseModel):
    """案例推荐请求"""
    description: str = Field(..., description="技术方案/案件描述")
    technology_field: Optional[str] = Field(None, description="技术领域（自动识别）")
    issue_type: Optional[str] = Field(None, description="争议类型")
    claims: Optional[str] = Field(None, description="权利要求内容")
    prior_art: Optional[str] = Field(None, description="对比现有技术")
    top_k: int = Field(10, description="推荐案例数量", ge=1, le=50)
    analysis_depth: str = Field("standard", description="分析深度: basic/standard/deep")

class CaseAnalysis(BaseModel):
    """案例分析"""
    case_id: int
    title: str
    decision_number: str
    decision_result: str
    technology_field: str
    issue_types: List[str]
    similarity_score: float
    reference_value: str
    key_points: List[str]
    reasoning_summary: str
    outcome_prediction: str

class ComparisonResult(BaseModel):
    """案例对比结果"""
    input_case: Dict[str, Any]
    recommended_cases: List[CaseAnalysis]
    technology_analysis: Dict[str, Any]
    issue_analysis: Dict[str, Any]
    success_prediction: Dict[str, Any]
    recommendations: List[str]

# ============ 核心分析函数 ============

def identify_technology_field(text: str) -> Dict[str, Any]:
    """
    智能识别技术领域

    Args:
        text: 输入的技术描述文本

    Returns:
        包含主要领域、置信度、所有识别领域和识别方法的字典
    """
    # 计算关键词匹配
    field_scores = {}
    text_lower = text.lower()

    for field, keywords in TECHNOLOGY_FIELD_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            field_scores[field] = score

    # 返回识别结果
    if field_scores:
        sorted_fields = sorted(field_scores.items(), key=lambda x: x[1], reverse=True)
        top_field = sorted_fields[0][0]
        confidence = sorted_fields[0][1] / sum(field_scores.values())

        return {
            'primary_field': top_field,
            'confidence': round(confidence, 2),
            'all_fields': list(field_scores.keys()),
            'method': 'keyword_matching'
        }
    else:
        return {
            'primary_field': '未识别',
            'confidence': 0,
            'all_fields': [],
            'method': 'keyword_matching'
        }

def extract_issue_types(reasoning: str) -> List[str]:
    """
    从理由书中提取争议类型

    Args:
        reasoning: 无效决定理由书文本

    Returns:
        争议类型列表
    """
    issue_types = []

    reasoning_lower = reasoning.lower()

    for issue, keywords in ISSUE_KEYWORD_MAP.items():
        if any(kw in reasoning_lower for kw in keywords):
            issue_types.append(issue)

    return issue_types if issue_types else ['未分类']

def calculate_similarity(input_text: str, case_text: str) -> float:
    """
    计算两个文本之间的Jaccard相似度

    Args:
        input_text: 输入文本
        case_text: 案例文本

    Returns:
        相似度分数 (0-1)
    """
    # 简单的关键词重叠计算
    input_words = set(input_text.split())
    case_words = set(case_text.split())

    if not input_words or not case_words:
        return 0.0

    intersection = input_words & case_words
    union = input_words | case_words

    jaccard_similarity = len(intersection) / len(union) if union else 0

    return round(jaccard_similarity, 3)

def assess_reference_value(similarity: float, decision_result: str,
                          issue_types: List[str]) -> str:
    """
    评估案例的参考价值

    Args:
        similarity: 相似度分数
        decision_result: 决定结果
        issue_types: 争议类型列表

    Returns:
        参考价值等级 (very_high, high, medium, low)
    """
    base_value = DECISION_RESULT_SCORES.get(decision_result, 'medium')

    # 根据相似度和争议类型调整
    if similarity > 0.3 and base_value == 'high':
        return 'very_high'
    elif similarity > 0.2 and base_value in ['high', 'medium']:
        return 'high'
    elif similarity > 0.1:
        return 'medium'
    else:
        return 'low'

def predict_outcome(similar_cases: List[Dict]) -> Dict[str, Any]:
    """
    基于相似案例预测案件结果

    Args:
        similar_cases: 相似案例列表

    Returns:
        包含预测结果、置信度、无效宣告率等信息的字典
    """
    if not similar_cases:
        return {
            'prediction': '无法预测',
            'confidence': 0,
            'invalidation_rate': 0,
            'rationale': '没有找到相似案例'
        }

    # 统计相似案例的结果分布
    total = len(similar_cases)
    invalid_count = sum(1 for c in similar_cases
                       if 'invalid' in c.get('decision_result', '').lower())

    invalidation_rate = invalid_count / total if total > 0 else 0

    # 预测
    if invalidation_rate > 0.7:
        prediction = '高概率被无效'
        confidence = 'high'
    elif invalidation_rate > 0.4:
        prediction = '中等概率被无效'
        confidence = 'medium'
    else:
        prediction = '倾向于维持有效'
        confidence = 'medium'

    return {
        'prediction': prediction,
        'confidence': confidence,
        'invalidation_rate': round(invalidation_rate * 100, 1),
        'total_references': total,
        'invalid_count': invalid_count,
        'valid_count': total - invalid_count
    }

# ============ API端点 ============

@app.get("/")
async def root():
    return {
        "service": "专利案例推荐系统",
        "version": "v1.0.0",
        "status": "running",
        "features": [
            "多维度相似案例检索",
            "技术领域智能识别",
            "争议焦点分析",
            "胜诉率预测",
            "参考价值评估"
        ],
        "endpoints": {
            "recommend": "/api/recommend/cases",
            "analyze": "/api/analyze/case",
            "compare": "/api/compare/cases",
            "fields": "/api/fields/list",
            "health": "/health"
        }
    }

@app.get("/health")
async def health():
    """健康检查端点"""
    try:
        if pg_cursor is None:
            return {
                "status": "unhealthy",
                "database": "not_connected",
                "llm": "enabled" if glm_client else "disabled"
            }

        pg_cursor.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "llm": "enabled" if glm_client else "disabled"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "llm": "enabled" if glm_client else "disabled"
        }

@app.get("/api/fields/list")
async def list_technology_fields():
    """列出支持的技术领域"""
    fields = {
        '机械结构': '机械装置、结构组件、连接装置等',
        '化学材料': '化学合成、材料配方、催化剂等',
        '电学通信': '电路设计、通信系统、半导体等',
        '计算机软件': '软件算法、数据处理、系统架构等',
        '医药生物': '药物、生物制品、医疗方法等',
        '医疗器械': '诊断治疗设备、医疗仪器等',
        '光电显示': '光学器件、显示技术等',
        '汽车制造': '汽车零部件、整车设计等'
    }
    return {'fields': fields, 'total': len(fields)}

@app.post("/api/recommend/cases")
async def recommend_cases(request: CaseRecommendationRequest):
    """
    智能案例推荐

    基于输入的技术方案/案件描述，推荐最相关的无效决定案例
    """

    try:
        # 1. 识别技术领域
        tech_field = request.technology_field
        if not tech_field:
            field_identification = identify_technology_field(request.description)
            tech_field = field_identification['primary_field']
        else:
            field_identification = {'primary_field': tech_field, 'confidence': 1.0}

        # 2. 构建搜索查询
        search_terms = [request.description]
        if tech_field and tech_field != '未识别':
            search_terms.append(tech_field)
        if request.issue_type:
            search_terms.append(request.issue_type)

        # 3. 搜索相似案例
        query = ' '.join(search_terms)

        # 获取表名
        table_name = get_decisions_table_name()

        # 主查询
        main_sql = f"""
            SELECT
                id,
                decision_number,
                patent_title,
                reasoning,
                decision_result
            FROM {table_name}
            WHERE reasoning IS NOT NULL
        """

        # 动态添加条件
        conditions = []
        params = []

        if tech_field and tech_field != '未识别':
            # 使用预定义的关键词映射
            keywords = FIELD_KEYWORD_MAP.get(tech_field, [tech_field])

            # 为关键词构建OR条件组
            if len(keywords) > 1:
                # 多个关键词用OR连接
                or_conditions = []
                for kw in keywords:
                    if len(kw) >= 2:
                        or_conditions.append("patent_title ILIKE %s")
                        params.append(f"%{kw}%")
                if or_conditions:
                    conditions.append(f"({' OR '.join(or_conditions)})")
            else:
                # 单个关键词
                for kw in keywords:
                    if len(kw) >= 2:
                        conditions.append("patent_title ILIKE %s")
                        params.append(f"%{kw}%")
        else:
            # 如果没有指定技术领域，尝试从描述中提取关键词
            if len(request.description) > 2:
                # 提取描述中的第一个关键词（2-4个字符）
                words = request.description.split()
                for word in words:
                    if len(word) >= 2 and len(word) <= 4:
                        conditions.append("patent_title ILIKE %s")
                        params.append(f"%{word}%")
                        break

        if request.issue_type:
            conditions.append("reasoning ILIKE %s")
            params.append(f"%{request.issue_type}%")

        # 通用查询条件（仅在描述足够长时才添加）
        if len(request.description) > 10:
            conditions.append("reasoning ILIKE %s")
            params.append(f"%{request.description[:50]}%")

        # 如果没有任何条件，至少返回一些案例
        if not conditions:
            conditions.append("1=1")  # 始终为真，返回所有案例

        main_sql += " AND " + " AND ".join(conditions)
        main_sql += " ORDER BY id DESC LIMIT %s"
        params.append(request.top_k * 2)  # 获取更多候选

        logger.info(f"Executing SQL: {main_sql[:200]}... with params: {params}")

        pg_cursor.execute(main_sql, params)
        cases = pg_cursor.fetchall()

        logger.info(f"SQL returned {len(cases)} cases for query: {query}")

        # 4. 分析和排序案例
        analyzed_cases = []

        for case in cases:
            id_val, decision_num, patent_title, reasoning, result = case

            # 计算相似度
            similarity = calculate_similarity(request.description, reasoning)

            # 提取争议类型
            issue_types = extract_issue_types(reasoning)

            # 评估参考价值
            ref_value = assess_reference_value(similarity, result, issue_types)

            # 提取关键点
            key_points = []
            if '区别技术特征' in reasoning:
                key_points.append('包含区别技术特征分析')
            if '技术启示' in reasoning:
                key_points.append('包含技术启示判断')
            if '显而易见' in reasoning:
                key_points.append('包含显而易见性分析')
            if '技术效果' in reasoning or '有益效果' in reasoning:
                key_points.append('包含技术效果分析')

            # 生成理由书摘要
            reasoning_summary = reasoning[:300] + "..." if len(reasoning) > 300 else reasoning

            # 预测该案例对当前案件的启示
            if 'invalid' in result.lower():
                outcome_prediction = "该案例被宣告无效，如技术方案类似，可能有被无效风险"
            else:
                outcome_prediction = "该案例维持有效，如技术方案类似，可作为有利参考"

            analyzed_cases.append({
                'case_id': id_val,
                'title': patent_title or '未命名专利',
                'decision_number': decision_num or '',
                'decision_result': result or '未知',
                'technology_field': tech_field,
                'issue_types': issue_types,
                'similarity_score': similarity,
                'reference_value': ref_value,
                'key_points': key_points,
                'reasoning_summary': reasoning_summary,
                'outcome_prediction': outcome_prediction
            })

        # 按相似度和参考价值排序
        def sort_key(case) -> None:
            return (
                REFERENCE_VALUE_SCORES.get(case['reference_value'], 0),
                case['similarity_score']
            )

        analyzed_cases.sort(key=sort_key, reverse=True)

        # 取Top-K
        top_cases = analyzed_cases[:request.top_k]

        # 5. 生成统计分析
        outcome_stats = predict_outcome(top_cases)

        # 6. 技术领域分析
        field_distribution = Counter([c['technology_field'] for c in top_cases])

        # 7. 争议类型分析
        issue_distribution = Counter()
        for case in top_cases:
            for issue in case['issue_types']:
                issue_distribution[issue] += 1

        # 8. 生成建议
        recommendations = []

        if outcome_stats['invalidation_rate'] > 60:
            recommendations.append("⚠️ 根据相似案例，该技术方案有较高的被无效风险")
            recommendations.append("💡 建议：在撰写权利要求时，强调与现有技术的区别技术特征")
            recommendations.append("💡 建议：补充技术效果和有益效果的详细说明")
        elif outcome_stats['invalidation_rate'] < 30:
            recommendations.append("✅ 根据相似案例，该技术方案有较好的维持有效前景")
            recommendations.append("💡 可以参考维持有效案例的抗辩策略")
        else:
            recommendations.append("⚖️ 案件结果存在不确定性，建议综合各方面因素评估")

        if top_cases:
            top_case = top_cases[0]
            recommendations.append(f"📊 最相关案例：{top_case['title']}")
            recommendations.append(f"   相似度：{top_case['similarity_score']:.1%}，参考价值：{top_case['reference_value']}")

        return {
            'input_analysis': {
                'identified_field': field_identification,
                'search_query': query
            },
            'recommended_cases': top_cases,
            'statistics': {
                'total_recommended': len(top_cases),
                'outcome_prediction': outcome_stats,
                'field_distribution': dict(field_distribution),
                'issue_distribution': dict(issue_distribution)
            },
            'recommendations': recommendations
        }

    except Exception as e:
        import traceback
        logger.error(f"Error in case recommendation: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/case")
async def analyze_case(request: CaseRecommendationRequest):
    """
    深度案例分析

    对输入的技术方案进行全面分析，包括：
    - 技术领域识别
    - 争议焦点预测
    - 相似案例推荐
    - 胜诉率评估
    - 应对策略建议
    """

    try:
        # 获取推荐案例
        recommendation_result = await recommend_cases(request)
        recommended_cases = recommendation_result['recommended_cases']

        # 如果有GLM，生成深度分析
        analysis_report = None
        if glm_client and request.analysis_depth in ['standard', 'deep']:

            # 构建分析提示词
            top_cases_summary = ""
            for i, case in enumerate(recommended_cases[:5], 1):
                top_cases_summary += f"""
案例{i}: {case['title']}
- 决定结果: {case['decision_result']}
- 相似度: {case['similarity_score']:.1%}
- 争议类型: {', '.join(case['issue_types'])}
- 关键点: {', '.join(case['key_points'])}
- 理由摘要: {case['reasoning_summary'][:200]}...
"""

            analysis_prompt = f"""你是一位资深的专利代理师。请对以下技术方案进行深度分析：

【技术方案】
{request.description}

【技术领域】
{recommendation_result['input_analysis']['identified_field']}

【相似案例】
{top_cases_summary}

请提供以下分析：

1. **技术特征分析**：识别核心技术特征和创新点
2. **潜在风险点**：基于相似案例，指出可能的问题
3. **争点预测**：预测可能的争议焦点
4. **应对策略**：提供具体的建议和策略
5. **案例参考**：说明哪些案例可以作为参考

请用专业、结构化的方式回答。"""

            try:
                response = glm_client.chat.completions.create(
                    model="glm-4-flash",  # 使用更快的模型
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一位资深的专利代理师和专利审查员，精通专利无效宣告程序和案例分析。"
                        },
                        {
                            "role": "user",
                            "content": analysis_prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=3000
                )

                # 安全地访问响应内容
                if response.choices and len(response.choices) > 0:
                    analysis_report = response.choices[0].message.content
                else:
                    analysis_report = "AI模型返回空响应"

            except Exception as e:
                logger.error(f"GLM analysis error: {e}")
                analysis_report = None

        return {
            'input': {
                'description': request.description,
                'technology_field': request.technology_field,
                'issue_type': request.issue_type
            },
            'recommendation_result': recommendation_result,
            'ai_analysis': analysis_report if analysis_report else "AI深度分析未启用（需要配置GLM API Key）"
        }

    except Exception as e:
        logger.error(f"Error in case analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║              专利案例推荐系统 启动中...                          ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  核心功能:                                                         ║
    ║    ✅ 多维度相似案例检索                                          ║
    ║    ✅ 技术领域智能识别                                            ║
    ║    ✅ 争议焦点分析                                                ║
    ║    ✅ 胜诉率预测                                                  ║
    ║    ✅ 参考价值评估                                                ║
    ║    ✅ AI深度分析 (GLM-4.7)                                       ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  API端点:                                                         ║
    ║    - POST /api/recommend/cases    案例推荐                       ║
    ║    - POST /api/analyze/case       深度分析                       ║
    ║    - GET  /api/fields/list        技术领域列表                   ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host="0.0.0.0", port=8012)
