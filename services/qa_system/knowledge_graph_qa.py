#!/usr/bin/env python3
"""
Athena平台知识图谱智能问答系统
集成大语言模型，提供基于知识图谱的智能问答服务
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp
import uvicorn

# FastAPI imports
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain.chains import RetrievalQA

# LangChain imports
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.vectorstores import FAISS
from pydantic import BaseModel

from core.logging_config import setup_logging
from core.security.auth import ALLOWED_ORIGINS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xujian/Athena工作平台/logs/qa_system.log'),
        logging.StreamHandler()
    ]
)
logger = setup_logging()

@dataclass
class QAContext:
    """问答上下文"""
    user_id: str
    session_id: str
    history: list[dict[str, str]]
    current_query: str
    retrieved_knowledge: list[dict]
    timestamp: datetime

class KnowledgeGraphQA:
    """知识图谱智能问答系统"""

    def __init__(self):
        self.platform_root = Path("/Users/xujian/Athena工作平台")
        self.config_path = self.platform_root / "config" / "qa_config.json"

        # 初始化模型
        self.llm = None
        self.embeddings = None
        self.vector_store = None
        self.qa_chain = None

        # 会话管理
        self.sessions: dict[str, QAContext] = {}

        # 知识库缓存
        self.knowledge_cache = {}

        # 加载配置
        self._load_config()

    def _load_config(self) -> Any:
        """加载问答系统配置"""
        default_config = {
            "model": {
                "provider": "openai",
                "model_name": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "embeddings": {
                "provider": "openai",
                "model": "text-embedding-ada-002"
            },
            "retrieval": {
                "top_k": 5,
                "similarity_threshold": 0.7,
                "include_metadata": True
            },
            "context": {
                "max_history_length": 10,
                "context_window_size": 4000
            },
            "knowledge_graph": {
                "api_url": "http://localhost:8080",
                "timeout": 30,
                "max_retries": 3
            },
            "response": {
                "include_sources": True,
                "include_confidence": True,
                "format": "structured"
            }
        }

        if self.config_path.exists():
            with open(self.config_path, encoding='utf-8') as f:
                loaded_config = json.load(f)
                self.config = {**default_config, **loaded_config}
        else:
            self.config = default_config
            # 创建配置文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)

        logger.info("✅ 问答系统配置已加载")

    async def initialize(self):
        """初始化问答系统"""
        logger.info("🔧 初始化智能问答系统...")

        try:
            # 1. 初始化语言模型
            await self._initialize_llm()

            # 2. 初始化向量嵌入
            await self._initialize_embeddings()

            # 3. 初始化知识检索
            await self._initialize_knowledge_retrieval()

            # 4. 创建问答链
            await self._create_qa_chain()

            logger.info("✅ 问答系统初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 问答系统初始化失败: {e}")
            return False

    async def _initialize_llm(self):
        """初始化语言模型"""
        provider = self.config["model"]["provider"]

        if provider == "openai":
            # 注意：需要设置OPENAI_API_KEY环境变量
            self.llm = ChatOpenAI(
                model_name=self.config["model"]["model_name"],
                temperature=self.config["model"]["temperature"],
                max_tokens=self.config["model"]["max_tokens"]
            )
            logger.info("✅ OpenAI模型已初始化")
        else:
            # 这里可以添加其他模型提供商
            logger.error(f"❌ 不支持的模型提供商: {provider}")
            raise ValueError(f"Unsupported model provider: {provider}")

    async def _initialize_embeddings(self):
        """初始化向量嵌入"""
        provider = self.config["embeddings"]["provider"]

        if provider == "openai":
            self.embeddings = OpenAIEmbeddings(
                model=self.config["embeddings"]["model"]
            )
            logger.info("✅ OpenAI嵌入已初始化")
        else:
            logger.error(f"❌ 不支持的嵌入提供商: {provider}")
            raise ValueError(f"Unsupported embeddings provider: {provider}")

    async def _initialize_knowledge_retrieval(self):
        """初始化知识检索"""
        # 构建知识库
        knowledge_texts = await self._build_knowledge_base()

        # 创建向量存储
        self.vector_store = FAISS.from_texts(
            texts=knowledge_texts,
            embedding=self.embeddings
        )

        logger.info(f"✅ 知识库已初始化，包含 {len(knowledge_texts)} 条知识")

    async def _build_knowledge_base(self) -> list[str]:
        """构建知识库"""
        knowledge_texts = []

        # 1. 从知识图谱获取实体和关系
        try:
            kg_data = await self._fetch_knowledge_graph_data()
            for entity in kg_data.get("entities", []):
                knowledge_texts.append(f"实体: {entity.get('label')} - {entity.get('description', '')}")

            for relation in kg_data.get("relations", []):
                knowledge_texts.append(
                    f"关系: {relation.get('source')} -{relation.get('type')}-> {relation.get('target')}"
                )

        except Exception as e:
            logger.warning(f"⚠️ 无法从知识图谱获取数据: {e}")

        # 2. 添加领域知识
        domain_knowledge = [
            "专利是保护发明创造的法律制度，授予专利权人在一定期限内的独占权",
            "发明专利保护期是20年，实用新型和外观设计保护期是10年",
            "专利侵权需要满足全面覆盖原则，即被控侵权技术方案包含了专利权利要求的所有技术特征",
            "专利新颖性是指在申请日之前，该技术不属于现有技术",
            "专利创造性是指与现有技术相比，该发明具有突出的实质性特点和显著的进步",
            "专利实用性是指该发明能够制造或者使用，并且能够产生积极效果"
        ]

        knowledge_texts.extend(domain_knowledge)

        return knowledge_texts

    async def _fetch_knowledge_graph_data(self) -> dict:
        """从知识图谱获取数据"""
        api_url = self.config["knowledge_graph"]["api_url"]

        async with aiohttp.ClientSession() as session:
            try:
                # 获取实体示例
                async with session.get(
                    f"{api_url}/api/v1/search/hybrid",
                    params={"query": "专利", "limit": 10}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "entities": data.get("results", []),
                            "relations": []
                        }
            except Exception as e:
                logger.error(f"获取知识图谱数据失败: {e}")

        return {"entities": [], "relations": []}

    async def _create_qa_chain(self):
        """创建问答链"""
        # 定义提示模板
        template = """
你是一个专业的专利知识图谱问答助手。请根据提供的上下文信息回答用户的问题。

上下文信息：
{context}

用户问题：
{question}

请提供准确、专业的回答。如果上下文中没有相关信息，请诚实地说明，并根据你的专业知识提供帮助。

回答格式：
1. 直接回答问题
2. 引用相关的知识来源
3. 如果适用，提供相关的专利或法律建议

回答：
"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

        # 创建问答链
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_kwargs={
                    "k": self.config["retrieval"]["top_k"]
                }
            ),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=self.config["response"]["include_sources"]
        )

        logger.info("✅ 问答链已创建")

    async def ask_question(
        self,
        question: str,
        user_id: str,
        session_id: str | None = None,
        search_kg: bool = True
    ) -> dict:
        """回答问题"""
        logger.info(f"❓ 收到问题: {question} (用户: {user_id})")

        try:
            # 创建或获取会话
            if not session_id:
                session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            if session_id not in self.sessions:
                self.sessions[session_id] = QAContext(
                    user_id=user_id,
                    session_id=session_id,
                    history=[],
                    current_query=question,
                    retrieved_knowledge=[],
                    timestamp=datetime.now()
                )

            context = self.sessions[session_id]
            context.current_query = question

            # 1. 从知识图谱检索相关信息
            kg_results = []
            if search_kg:
                kg_results = await self._search_knowledge_graph(question)

            # 2. 使用问答链生成回答
            qa_result = await self._generate_answer(question, context.history)

            # 3. 增强回答（结合知识图谱信息）
            enhanced_answer = await self._enhance_answer(
                qa_result, kg_results, question
            )

            # 4. 更新会话历史
            context.history.append({
                "question": question,
                "answer": enhanced_answer["answer"],
                "timestamp": datetime.now().isoformat(),
                "sources": enhanced_answer.get("sources", [])
            })

            # 限制历史长度
            if len(context.history) > self.config["context"]["max_history_length"]:
                context.history = context.history[-self.config["context"]["max_history_length"]:]

            # 构建响应
            response = {
                "answer": enhanced_answer["answer"],
                "session_id": session_id,
                "sources": enhanced_answer.get("sources", []),
                "confidence": enhanced_answer.get("confidence", 0.8),
                "kg_results": kg_results,
                "related_questions": await self._generate_related_questions(question),
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"✅ 生成回答: {response['answer'][:100]}...")
            return response

        except Exception as e:
            logger.error(f"❌ 问答处理失败: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def _search_knowledge_graph(self, query: str) -> list[dict]:
        """在知识图谱中搜索相关信息"""
        try:
            api_url = self.config["knowledge_graph"]["api_url"]

            async with aiohttp.ClientSession() as session:
                # 使用混合搜索
                async with session.post(
                    f"{api_url}/api/v1/search/hybrid",
                    json={
                        "query": query,
                        "limit": 5,
                        "entity_types": ["Patent", "Company", "Technology", "LegalCase"]
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("results", [])

        except Exception as e:
            logger.warning(f"⚠️ 知识图谱搜索失败: {e}")

        return []

    async def _generate_answer(self, question: str, history: list[dict]) -> dict:
        """使用问答链生成回答"""
        try:
            # 构建上下文
            context_str = "\n".join([
                f"Q: {item['question']}\n_a: {item['answer']}"
                for item in history[-3:]  # 只使用最近3次对话
            ])

            # 调用问答链
            result = self.qa_chain({
                "query": question,
                "context": context_str
            })

            return {
                "answer": result["result"],
                "sources": [
                    doc.page_content for doc in result.get("source_documents", [])
                ]
            }

        except Exception as e:
            logger.error(f"❌ 生成回答失败: {e}")
            # 返回默认回答
            return {
                "answer": "抱歉，我目前无法回答这个问题。请尝试重新提问或联系技术支持。",
                "sources": []
            }

    async def _enhance_answer(
        self,
        qa_result: dict,
        kg_results: list[dict],
        question: str
    ) -> dict:
        """增强回答（结合知识图谱信息）"""
        enhanced = qa_result.copy()

        if kg_results:
            # 添加知识图谱信息到回答
            kg_info = "\n\n基于知识图谱的相关信息：\n"
            for i, result in enumerate(kg_results[:3], 1):
                if result.get("title"):
                    kg_info += f"{i}. {result.get('title')}"
                    if result.get("type"):
                        kg_info += f" ({result.get('type')})"
                    kg_info += "\n"

            enhanced["answer"] += kg_info
            enhanced["sources"].extend([r.get("title", "") for r in kg_results])

        # 计算置信度
        confidence = 0.8  # 基础置信度
        if kg_results:
            confidence += 0.1  # 有知识图谱结果增加置信度
        if qa_result.get("sources"):
            confidence += 0.1  # 有检索来源增加置信度

        enhanced["confidence"] = min(confidence, 1.0)

        return enhanced

    async def _generate_related_questions(self, question: str) -> list[str]:
        """生成相关问题"""
        # 简单实现：基于关键词生成相关问题
        keywords = ["专利", "申请", "侵权", "审查", "有效期", "费用"]
        related = []

        for keyword in keywords:
            if keyword not in question.lower():
                related.append(f"{keyword}相关的{keyword}如何办理？")

        return related[:5]

# FastAPI应用
app = FastAPI(
    title="Athena知识图谱智能问答系统",
    description="基于大语言模型和知识图谱的智能问答服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class QuestionRequest(BaseModel):
    question: str
    user_id: str
    session_id: str | None = None
    search_kg: bool = True

class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: str | None = None

# 全局问答系统实例
qa_system = None

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    global qa_system
    qa_system = KnowledgeGraphQA()
    await qa_system.initialize()

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Athena知识图谱智能问答系统",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/api/v1/ask")
async def ask_question(request: QuestionRequest):
    """问答接口"""
    try:
        result = await qa_system.ask_question(
            question=request.question,
            user_id=request.user_id,
            session_id=request.session_id,
            search_kg=request.search_kg
        )
        return result
    except Exception as e:
        logger.error(f"问答失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """聊天接口（更友好的对话接口）"""
    # 转换为问答请求
    qa_request = QuestionRequest(
        question=request.message,
        user_id=request.user_id,
        session_id=request.session_id,
        search_kg=True
    )

    result = await qa_system.ask_question(
        question=qa_request.question,
        user_id=qa_request.user_id,
        session_id=qa_request.session_id,
        search_kg=qa_request.search_kg
    )

    # 返回聊天格式的响应
    return {
        "reply": result["answer"],
        "session_id": result["session_id"],
        "metadata": {
            "confidence": result["confidence"],
            "sources": result["sources"],
            "related_questions": result["related_questions"]
        }
    }

@app.get("/api/v1/session/{session_id}")
async def get_session(session_id: str):
    """获取会话信息"""
    if session_id in qa_system.sessions:
        context = qa_system.sessions[session_id]
        return {
            "session_id": session_id,
            "user_id": context.user_id,
            "history": context.history,
            "created_at": context.timestamp.isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """WebSocket聊天接口"""
    await websocket.accept()

    session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            message = data.get("message", "")

            if message.lower() in ["exit", "quit", "退出"]:
                await websocket.send_json({
                    "type": "system",
                    "message": "会话已结束"
                })
                break

            # 处理问题
            result = await qa_system.ask_question(
                question=message,
                user_id=user_id,
                session_id=session_id
            )

            # 发送回答
            await websocket.send_json({
                "type": "answer",
                "reply": result["answer"],
                "metadata": {
                    "confidence": result["confidence"],
                    "sources": result["sources"]
                }
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "qa_system": qa_system is not None,
            "llm": qa_system.llm is not None if qa_system else False,
            "embeddings": qa_system.embeddings is not None if qa_system else False,
            "vector_store": qa_system.vector_store is not None if qa_system else False
        }
    }

if __name__ == "__main__":
    import os

    # 设置OpenAI API密钥（需要用户自己设置）
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️ 未设置OPENAI_API_KEY环境变量")
        logger.info("💡 请设置: export OPENAI_API_KEY=your_api_key")

    uvicorn.run(
        "knowledge_graph_qa:app",
        host="0.0.0.0",
        port=8082,
        reload=True,
        log_level="info"
    )
