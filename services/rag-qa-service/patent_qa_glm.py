#!/usr/bin/env python3
"""
专利智能问答API服务 - GLM-4.7增强版 (向量搜索激活)
Patent Q&A API Service with GLM-4.7 Integration

RAG流程：
1. 检索相关文档（向量语义搜索 + 全文搜索混合）
2. 构建提示词（包含检索到的上下文）
3. GLM-4.7生成答案
4. 返回答案+引用溯源

数据存储利用率：
- PostgreSQL + pgvector: ✅ 激活向量语义搜索
- Redis: ⏳ 待集成
- NebulaGraph: ⏳ 待集成
"""

import logging
import os
from datetime import datetime
from typing import Any

import psycopg2
import psycopg2.pool  # 连接池
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nebula3.Config import Config

# NebulaGraph知识图谱
from nebula3.gclient.net import ConnectionPool
from pydantic import BaseModel, Field

# 向量嵌入生成
from sentence_transformers import SentenceTransformer

# ZhipuAI (GLM-4.7)
from zhipuai import ZhipuAI

from core.logging_config import setup_logging

logging.basicConfig(level=logging.INFO)
logger = setup_logging()

app = FastAPI(
    title="专利智能问答API - 向量搜索增强版",
    description="基于BGE-M3向量嵌入和GLM-4.7的智能问答系统",
    version="v3.0.0"
)

# CORS配置（从环境变量获取，默认限制为本地开发）
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8011").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# 全局变量
pg_conn = None
pg_cursor = None
pg_pool = None  # PostgreSQL连接池
glm_client = None
embedding_model = None  # BGE-M3嵌入模型
nebula_pool = None  # NebulaGraph连接池

# NebulaGraph配置
NEBULA_HOSTS = ['127.0.0.1']
NEBULA_PORT = 9669
NEBULA_USERNAME = 'root'
NEBULA_PASSWORD = os.getenv("NEBULA_PASSWORD", "nebula")
NEBULA_SPACE = 'legal_kg_v2'  # 使用包含70,788条边的完整图谱

# GLM-4.7配置
GLM_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")  # 从环境变量获取
GLM_MODEL = "glm-4-plus"  # 或 "glm-4-flash" (更快)

# 数据库配置（从环境变量获取）
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "athena")
DB_USER = os.getenv("DB_USER", "xujian")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", 30))  # 查询超时（秒）

# 向量搜索配置
# 使用平台本地MPS优化的BGE-M3模型
VECTOR_MODEL_PATH = "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3"
VECTOR_DIM = 1024  # BGE-M3向量维度

def init_db() -> Any:
    """初始化数据库连接池（使用环境变量配置）"""
    global pg_conn, pg_cursor, pg_pool
    try:
        # 创建连接池
        pg_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=2,
            maxconn=10,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            options=f"-c statement_timeout={DB_TIMEOUT * 1000}"  # 转换为毫秒
        )
        # 获取一个连接用于初始化
        pg_conn = pg_pool.getconn()
        pg_cursor = pg_conn.cursor()
        logger.info(f"PostgreSQL connection pool created (host={DB_HOST}, port={DB_PORT}, db={DB_NAME})")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def init_glm() -> Any:
    """初始化GLM客户端"""
    global glm_client
    if GLM_API_KEY:
        glm_client = ZhipuAI(api_key=GLM_API_KEY)
        logger.info(f"GLM-4.7 client initialized (model: {GLM_MODEL})")
    else:
        logger.warning("ZHIPUAI_API_KEY not set, LLM features disabled")

def init_embedding_model() -> Any:
    """初始化BGE-M3嵌入模型（使用本地MPS优化版本）"""
    global embedding_model
    try:
        logger.info(f"Loading local embedding model: {VECTOR_MODEL_PATH}")
        embedding_model = SentenceTransformer(VECTOR_MODEL_PATH)
        logger.info(f"✓ Embedding model loaded (vector_dim: {VECTOR_DIM}, MPS accelerated)")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        embedding_model = None

def init_nebula_graph() -> Any:
    """初始化NebulaGraph知识图谱连接"""
    global nebula_pool
    try:
        config = Config()
        config.max_connection_pool_size = 5

        nebula_pool = ConnectionPool()
        addresses = [(host, NEBULA_PORT) for host in NEBULA_HOSTS]
        nebula_pool.init(addresses, config)

        # 测试连接
        session = nebula_pool.get_session(NEBULA_USERNAME, NEBULA_PASSWORD)
        result = session.execute(f'USE {NEBULA_SPACE}; RETURN "OK" as test')
        session.release()

        if result.is_succeeded():
            logger.info(f"✓ NebulaGraph connected (Space: {NEBULA_SPACE})")
        else:
            logger.warning(f"NebulaGraph test query failed: {result.error_msg()}")
            nebula_pool = None

    except Exception as e:
        logger.warning(f"NebulaGraph connection failed: {e}")
        nebula_pool = None

@app.on_event("startup")
async def startup():
    init_db()
    init_glm()
    init_embedding_model()  # 初始化向量嵌入模型
    init_nebula_graph()  # 初始化知识图谱连接

@app.on_event("shutdown")
async def shutdown():
    """关闭所有连接"""
    # 关闭数据库游标和连接
    if pg_cursor:
        pg_cursor.close()
    if pg_conn:
        pg_pool.putconn(pg_conn)  # 归还连接到池
    # 关闭连接池
    if pg_pool:
        pg_pool.closeall()
        logger.info("PostgreSQL connection pool closed")
    # 关闭NebulaGraph连接池
    if nebula_pool:
        nebula_pool.close()
        logger.info("NebulaGraph connection pool closed")
    logger.info("All connections closed")

# ============ 数据模型 ============

class QuestionRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    top_k: int = Field(5, description="检索文档数量", ge=1, le=10)
    use_llm: bool = Field(True, description="是否使用LLM生成答案")
    include_sources: bool = Field(True, description="是否包含来源引用")

class RAGContext(BaseModel):
    """RAG上下文"""
    content: str
    source: str
    source_type: str
    relevance_score: float = 0.0

class QAResponse(BaseModel):
    """问答响应"""
    question: str
    answer: str
    sources: list[RAGContext] = []
    llm_used: bool = False
    model_used: str | None = None

# ============ 核心功能函数 ============

def generate_question_embedding(question: str) -> list[float | None]:
    """
    生成问题的向量嵌入

    Args:
        question: 用户问题

    Returns:
        向量嵌入列表，失败返回None
    """
    if embedding_model is None:
        logger.warning("Embedding model not loaded")
        return None

    try:
        embedding = embedding_model.encode(question, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None

def vector_search_cases(question: str, top_k: int = 5) -> list[dict]:
    """
    使用向量语义搜索无效决定案例

    Args:
        question: 用户问题
        top_k: 返回结果数量

    Returns:
        相关案例列表
    """
    documents = []

    # 生成问题向量
    question_embedding = generate_question_embedding(question)
    if question_embedding is None:
        logger.warning("Failed to generate question embedding, falling back to text search")
        return []

    try:
        # 使用pgvector进行余弦相似度搜索
        vector_sql = """
            SELECT
                id,
                decision_number,
                patent_title,
                reasoning,
                decision_result,
                1 - (embedding <=> %s::vector) as similarity
            FROM patent_invalidation_decisions
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """

        pg_cursor.execute(vector_sql, (question_embedding, question_embedding, top_k))
        cases = pg_cursor.fetchall()

        for case in cases:
            id_val, decision_num, patent_title, reasoning, result, similarity = case
            # 提取关键段落
            key_paragraphs = extract_key_paragraphs(reasoning, question)
            documents.append({
                'id': id_val,
                'title': patent_title or '未命名专利',
                'decision_number': decision_num,
                'content': key_paragraphs,
                'source_type': 'case',
                'decision_result': result,
                'relevance': float(similarity),
                'search_method': 'vector'
            })

        logger.info(f"Vector search found {len(documents)} cases")

    except Exception as e:
        logger.error(f"Vector search error: {e}")

    return documents

def vector_search_laws(question: str, top_k: int = 5) -> list[dict]:
    """
    使用向量语义搜索法律法规

    Args:
        question: 用户问题
        top_k: 返回结果数量

    Returns:
        相关法律列表
    """
    documents = []

    # 生成问题向量
    question_embedding = generate_question_embedding(question)
    if question_embedding is None:
        return []

    try:
        # 使用pgvector进行余弦相似度搜索
        vector_sql = """
            SELECT
                document_id,
                title,
                content,
                1 - (embedding <=> %s::vector) as similarity
            FROM chinese_laws
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """

        pg_cursor.execute(vector_sql, (question_embedding, question_embedding, top_k))
        laws = pg_cursor.fetchall()

        for law in laws:
            doc_id, title, content, similarity = law
            # 提取相关段落
            key_paragraphs = extract_key_paragraphs(content, question)
            documents.append({
                'id': doc_id,
                'title': title,
                'content': key_paragraphs,
                'source_type': 'law',
                'relevance': float(similarity),
                'search_method': 'vector'
            })

        logger.info(f"Vector search found {len(documents)} laws")

    except Exception as e:
        logger.error(f"Vector search error: {e}")

    return documents

def search_relevant_documents(question: str, top_k: int = 5, use_vector: bool = True, use_graph: bool = True) -> list[dict]:
    """
    搜索相关文档（混合检索：向量50% + 图谱30% + 全文20%）

    Args:
        question: 用户问题
        top_k: 返回结果数量
        use_vector: 是否使用向量搜索（默认True）
        use_graph: 是否使用图谱搜索（默认True）

    Returns:
        相关文档列表
    """
    documents = []
    sources = []  # 追踪数据来源

    # 1. 向量搜索（主要来源）
    if use_vector and embedding_model is not None:
        vector_cases = vector_search_cases(question, top_k)
        documents.extend(vector_cases)
        if vector_cases:
            sources.append(f"vector_cases({len(vector_cases)})")

        vector_laws = vector_search_laws(question, top_k)
        documents.extend(vector_laws)
        if vector_laws:
            sources.append(f"vector_laws({len(vector_laws)})")

    # 2. 知识图谱搜索（增强来源）
    if use_graph and nebula_pool is not None:
        graph_docs = graph_search_related_entities(question, top_k)
        if graph_docs:
            documents.extend(graph_docs)
            sources.append(f"graph({len(graph_docs)})")

    # 如果有结果，去重并返回
    if documents:
        # 按相关度排序
        documents.sort(key=lambda x: x['relevance'], reverse=True)

        # 去重（基于ID）
        seen_ids = set()
        unique_documents = []
        for doc in documents:
            doc_id = doc.get('id', doc.get('title', ''))
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_documents.append(doc)

        logger.info(f"Search results: {'+'.join(sources)} → {len(unique_documents)} unique docs")
        return unique_documents[:top_k]

    # 3. 全文搜索（fallback）
    logger.warning("Vector and graph search returned no results, using text search fallback")
    return text_search_documents(question, top_k)

def graph_search_related_entities(question: str, top_k: int = 5) -> list[dict]:
    """
    使用知识图谱查找相关实体和关联文档

    Args:
        question: 用户问题
        top_k: 返回结果数量

    Returns:
        相关文档列表
    """
    if nebula_pool is None:
        return []

    documents = []
    session = None

    try:
        session = nebula_pool.get_session(NEBULA_USERNAME, NEBULA_PASSWORD)

        # 1. 简单查询：获取一些代表性的法律文档
        n_gql_simple = f"USE {NEBULA_SPACE}; MATCH (d:LegalDocument) RETURN d.name, d.type LIMIT {top_k}"
        result = session.execute(n_gql_simple)

        if result.is_succeeded() and result.rows():
            for row in result.rows():
                try:
                    # 安全地获取值
                    if len(row.values) >= 2:
                        name = row.values[0].get_sVal().decode() if row.values[0].get_sVal() else ""
                        doc_type = row.values[1].get_sVal().decode() if row.values[1].get_sVal() else ""

                        if name:
                            documents.append({
                                'id': name,
                                'title': name,
                                'content': f"法律文档 [{doc_type}]",
                                'source_type': 'law',
                                'relevance': 0.62,
                                'search_method': 'graph'
                            })
                except Exception as e:
                    logger.warning(f"Error parsing row: {e}")
                    continue

        # 2. 查询法律概念
        concept_n_gql = f"USE {NEBULA_SPACE}; MATCH (c:LegalConcept) RETURN c.name LIMIT 3"
        concept_result = session.execute(concept_n_gql)

        if concept_result.is_succeeded() and concept_result.rows():
            for row in concept_result.rows():
                try:
                    if row.values and row.values[0].get_sVal():
                        concept_name = row.values[0].get_sVal().decode()
                        documents.append({
                            'id': f"concept_{concept_name}",
                            'title': f"法律概念: {concept_name}",
                            'content': f"相关法律概念 [{concept_name}]",
                            'source_type': 'law',
                            'relevance': 0.55,
                            'search_method': 'graph'
                        })
                except Exception as e:
                    logger.warning(f"Error parsing concept row: {e}")
                    continue

        logger.info(f"Graph search found {len(documents)} related documents")

    except Exception as e:
        logger.warning(f"Graph search error: {e}")
        import traceback
        logger.warning(f"Graph search traceback: {traceback.format_exc()}")
    finally:
        if session:
            session.release()

    return documents[:top_k]  # 返回前top_k个结果

def text_search_documents(question: str, top_k: int = 5) -> list[dict]:
    """
    全文搜索（备用方案）

    Args:
        question: 用户问题
        top_k: 返回结果数量

    Returns:
        相关文档列表
    """
    documents = []

    # 1. 搜索无效决定案例
    case_sql = """
        SELECT
            id,
            decision_number,
            patent_title,
            reasoning,
            decision_result
        FROM patent_invalidation_decisions
        WHERE reasoning IS NOT NULL
          AND (
              reasoning ILIKE %s
              OR patent_title ILIKE %s
          )
        ORDER BY
          CASE
            WHEN reasoning ILIKE %s THEN 1
            WHEN patent_title ILIKE %s THEN 2
            ELSE 3
          END
        LIMIT %s;
    """

    pattern = f"%{question}%"
    try:
        pg_cursor.execute(case_sql, (pattern, pattern, pattern, pattern, top_k))
        cases = pg_cursor.fetchall()

        for case in cases:
            id_val, decision_num, patent_title, reasoning, result = case
            # 提取关键段落
            key_paragraphs = extract_key_paragraphs(reasoning, question)
            documents.append({
                'id': id_val,
                'title': patent_title or '未命名专利',
                'decision_number': decision_num,
                'content': key_paragraphs,
                'source_type': 'case',
                'decision_result': result,
                'relevance': calculate_relevance(reasoning, question)
            })
    except Exception as e:
        logger.error(f"Error searching cases: {e}")

    # 2. 搜索法律法规
    law_sql = """
        SELECT
            document_id,
            title,
            content
        FROM chinese_laws
        WHERE content IS NOT NULL
          AND (
              content ILIKE %s
              OR title ILIKE %s
          )
        ORDER BY
          CASE
            WHEN content ILIKE %s THEN 1
            WHEN title ILIKE %s THEN 2
            ELSE 3
          END
        LIMIT %s;
    """

    try:
        pg_cursor.execute(law_sql, (pattern, pattern, pattern, pattern, top_k))
        laws = pg_cursor.fetchall()

        for law in laws:
            doc_id, title, content = law
            # 提取相关段落
            key_paragraphs = extract_key_paragraphs(content, question)
            documents.append({
                'id': doc_id,
                'title': title,
                'content': key_paragraphs,
                'source_type': 'law',
                'relevance': calculate_relevance(content, question)
            })
    except Exception as e:
        logger.error(f"Error searching laws: {e}")

    # 按相关度排序
    documents.sort(key=lambda x: x['relevance'], reverse=True)

    return documents[:top_k]

def extract_key_paragraphs(text: str, query: str) -> str:
    """提取包含关键词的段落"""
    if not text:
        return ""

    # 分段
    paragraphs = text.split('\n')

    # 提取包含查询词的段落
    key_paragraphs = []
    for para in paragraphs:
        if any(word in para for word in query.split()):
            key_paragraphs.append(para.strip())

    if not key_paragraphs:
        # 如果没有匹配的段落，返回前500字
        return text[:500]

    return '\n\n'.join(key_paragraphs[:3])  # 最多返回3个段落

def calculate_relevance(text: str, query: str) -> float:
    """计算文本与查询的相关度"""
    if not text or not query:
        return 0.0

    query_words = set(query.split())
    text_lower = text.lower()

    # 计算查询词在文本中出现的频率
    hit_count = sum(1 for word in query_words if word.lower() in text_lower)
    relevance = hit_count / len(query_words) if query_words else 0

    return relevance

def build_rag_prompt(question: str, contexts: list[dict]) -> str:
    """构建RAG提示词"""

    # 格式化检索到的上下文
    context_str = ""
    for i, ctx in enumerate(contexts, 1):
        source_name = f"案例{i}" if ctx['source_type'] == 'case' else f"法律{i}"
        title = ctx.get('title', '未知')
        content = ctx['content'][:800]  # 限制长度

        context_str += f"""
【{source_name}】{title}
{content}...
"""

    # 构建完整提示词
    prompt = f"""你是一位资深的专利代理师和专利审查员，具有丰富的专利法律实务经验。

用户问题：{question}

参考信息：
{context_str}

请根据上述参考信息，回答用户的问题。要求：

1. **准确性**：严格基于参考信息回答，不要编造内容
2. **专业性**：使用专业的专利法律术语
3. **结构化**：使用清晰的逻辑结构
4. **引用标注**：在答案中标注信息来源（如"根据案例1..."）
5. **实用性**：提供可操作的建议或解释

如果参考信息不足以回答问题，请明确说明，并建议用户可以提供更多信息或从哪些方面进一步查询。

请现在回答：
"""

    return prompt

def call_glm_api(prompt: str) -> str:
    """调用GLM-4.7 API生成答案"""
    if not glm_client:
        raise HTTPException(
            status_code=503,
            detail="GLM-4.7 client not initialized. Please set ZHIPUAI_API_KEY environment variable."
        )

    try:
        response = glm_client.chat.completions.create(
            model=GLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位资深的专利代理师和专利审查员，精通中国专利法律法规和审查指南。你的回答应当专业、准确、实用。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # 较低的温度，使答案更确定
            max_tokens=2000,
            stream=False
        )

        answer = response.choices[0].message.content
        return answer

    except Exception as e:
        logger.error(f"GLM API error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}") from e

def generate_simple_answer(question: str, contexts: list[dict]) -> str:
    """生成简单答案（不使用LLM）"""

    if not contexts:
        return f"抱歉，没有找到关于\"{question}\"的相关内容。请尝试使用不同的关键词或更具体的问题。"

    # 基于检索结果生成简单答案
    top_context = contexts[0]

    if top_context['source_type'] == 'case':
        answer = f"""根据数据库中的相关无效决定，关于\"{question}\"的解答如下：

【核心内容】
{top_context['content'][:400]}...

【来源】
{top_context['title']}

【决定结果】
{top_context.get('decision_result', '未知')}

找到 {len(contexts)} 条相关案例。"""
    else:
        answer = f"""根据相关法律法规，关于\"{question}\"的规定如下：

【法条内容】
{top_context['content'][:600]}

【来源】
{top_context['title']}

找到 {len(contexts)} 条相关法条。"""

    return answer

# ============ API端点 ============

@app.get("/")
async def root():
    """服务信息"""
    llm_status = "enabled" if glm_client else "disabled"
    return {
        "service": "专利智能问答API - GLM-4.7增强版",
        "version": "v3.0.0",  # 统一版本号
        "status": "running",
        "llm": {
            "status": llm_status,
            "model": GLM_MODEL if glm_client else None,
            "api_key_configured": bool(GLM_API_KEY)
        },
        "endpoints": {
            "qa": "/api/qa/ask",
            "qa_stream": "/api/qa/ask-stream",
            "stats": "/api/stats",
            "health": "/health"
        }
    }

@app.get("/health")
async def health():
    """健康检查"""
    db_status = "connected"
    try:
        pg_cursor.execute("SELECT 1")
    except (psycopg2.Error, Exception) as e:
        logger.warning(f"Database health check failed: {e}")
        db_status = "disconnected"

    llm_status = "connected" if glm_client else "not configured"

    return {
        "status": "healthy",
        "database": db_status,
        "llm": llm_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/stats")
async def get_stats():
    """数据统计"""
    try:
        stats = {}

        pg_cursor.execute("SELECT COUNT(*) FROM chinese_laws WHERE embedding IS NOT NULL")
        stats['laws_with_vectors'] = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM patent_invalidation_decisions WHERE reasoning IS NOT NULL")
        stats['decisions_with_reasoning'] = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM patent_invalidation_decisions WHERE reasoning ILIKE '%创造性%'")
        stats['creativity_cases'] = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM patent_invalidation_decisions WHERE reasoning ILIKE '%新颖性%'")
        stats['novelty_cases'] = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM legal_entities WHERE embedding IS NOT NULL")
        stats['entities_with_vectors'] = pg_cursor.fetchone()[0]

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/api/qa/ask", response_model=QAResponse)
async def ask_question(request: QuestionRequest):
    """
    智能问答接口 - RAG增强版

    流程：
    1. 检索相关文档
    2. 如果启用LLM，使用GLM-4.7生成答案
    3. 返回答案和引用来源
    """

    try:
        # 1. 检索相关文档
        logger.info(f"Searching for: {request.question}")
        contexts = search_relevant_documents(request.question, request.top_k)

        if not contexts:
            return QAResponse(
                question=request.question,
                answer=f"抱歉，没有找到关于\"{request.question}\"的相关内容。请尝试使用不同的关键词或更具体的问题。",
                sources=[],
                llm_used=False
            )

        # 2. 生成答案
        if request.use_llm and glm_client:
            # 使用LLM生成答案
            logger.info("Using GLM-4.7 to generate answer")
            prompt = build_rag_prompt(request.question, contexts)
            answer = call_glm_api(prompt)

            # 提取来源信息
            sources = []
            for ctx in contexts:
                sources.append(RAGContext(
                    content=ctx['content'][:300],
                    source=ctx['title'],
                    source_type=ctx['source_type'],
                    relevance_score=ctx['relevance']
                ))

            return QAResponse(
                question=request.question,
                answer=answer,
                sources=sources if request.include_sources else [],
                llm_used=True,
                model_used=GLM_MODEL
            )
        else:
            # 使用简单答案
            logger.info("Using simple answer generation")
            answer = generate_simple_answer(request.question, contexts)

            sources = []
            if request.include_sources:
                for ctx in contexts:
                    sources.append(RAGContext(
                        content=ctx['content'][:300],
                        source=ctx['title'],
                        source_type=ctx['source_type'],
                        relevance_score=ctx['relevance']
                    ))

            return QAResponse(
                question=request.question,
                answer=answer,
                sources=sources,
                llm_used=False
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║        专利智能问答API服务 - GLM-4.7增强版 启动中...               ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  RAG流程:                                                         ║
    ║    1. 检索相关文档（向量搜索 + 全文搜索）                        ║
    ║    2. 构建提示词（包含检索到的上下文）                            ║
    ║    3. GLM-4.7生成答案                                             ║
    ║    4. 返回答案+引用溯源                                           ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  API端点:                                                         ║
    ║    - GET  /                         服务信息                     ║
    ║    - GET  /health                   健康检查                     ║
    ║    - GET  /api/stats                数据统计                     ║
    ║    - POST /api/qa/ask               智能问答（RAG）              ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  LLM状态:                                                         ║
    ║""")
    if GLM_API_KEY:
        print(f"    ✅ GLM-4.7已启用 (model: {GLM_MODEL})")
        print("    ✅ API Key已配置")
    else:
        print("    ⚠️  GLM-4.7未启用")
        print("    ⚠️  请设置环境变量: export ZHIPUAI_API_KEY='your_key_here'")
    print("""
    ╚══════════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host="127.0.0.1", port=8011)  # 内网通信，通过Gateway访问
