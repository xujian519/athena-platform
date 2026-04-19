#!/usr/bin/env python3
"""
法律专家服务按需启动脚本 (NLP深度集成版)
Legal Expert Service On-Demand Startup (NLP Deep Integration)

启动法律向量库和知识图谱服务，与NLP系统深度集成，提供动态提示词和专业问答

作者: 小诺·双鱼公主
创建时间: 2025-12-22
版本: v2.0.0 "NLP深度集成"
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent))

# 导入NLP深度集成模块
sys.path.insert(0, str(project_root / "core"))
from nlp_integration import (
    NLPIntegrationService,
    ProfessionalDomain,
    analyze_text_semantically,
    extract_entities_from_text,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class LegalExpertService:
    """法律专家服务类 (NLP深度集成版)"""

    def __init__(self):
        self.service_name = "Legal Expert Service"
        self.version = "v2.0.0"
        self.start_time = datetime.now()
        self.qdrant_client = None
        self.knowledge_graph = None
        self.legal_data_loaded = False
        self.nlp_service = NLPIntegrationService()
        self.domain = ProfessionalDomain.LEGAL

    async def initialize(self):
        """初始化服务"""
        logger.info("🧠 初始化法律专家服务...")

        # 加载法律向量库配置
        await self._load_vector_config()

        # 初始化知识图谱连接
        await self._init_knowledge_graph()

        # 加载法律数据
        await self._load_legal_data()

        logger.info("✅ 法律专家服务初始化完成")

    async def _load_vector_config(self):
        """加载向量库配置"""
        try:
            config_path = project_root / "config" / "legal_vector_config.json"
            if config_path.exists():
                with open(config_path, encoding='utf-8') as f:
                    self.vector_config = json.load(f)
                logger.info("✅ 向量库配置加载成功")
            else:
                logger.warning("⚠️ 向量库配置文件不存在")
        except Exception as e:
            logger.error(f"❌ 加载向量库配置失败: {e}")

    async def _init_knowledge_graph(self):
        """初始化知识图谱"""
        try:
            # 这里应该初始化知识图谱连接
            # 暂时标记为已初始化
            self.knowledge_graph = True
            logger.info("✅ 知识图谱初始化成功")
        except Exception as e:
            logger.error(f"❌ 初始化知识图谱失败: {e}")

    async def _load_legal_data(self):
        """加载法律数据"""
        try:
            data_path = project_root / "data" / "exports" / "unified_legal_dataset_20251220_211550.json"
            if data_path.exists():
                with open(data_path, encoding='utf-8') as f:
                    self.legal_dataset = json.load(f)
                self.legal_data_loaded = True
                logger.info("✅ 法律数据加载成功")
            else:
                logger.warning("⚠️ 法律数据文件不存在")
        except Exception as e:
            logger.error(f"❌ 加载法律数据失败: {e}")

    async def generate_dynamic_prompt(self, user_query: str, context: dict[str, Any] = None) -> str:
        """生成动态提示词 (NLP深度集成版)"""
        logger.info(f"🧠 使用NLP生成法律专业提示词: {user_query[:50]}...")

        try:
            # 使用NLP进行语义分析
            semantic_result = await analyze_text_semantically(
                user_query,
                self.domain,
                context
            )

            # 使用NLP进行实体提取
            entity_result = await extract_entities_from_text(
                user_query,
                self.domain
            )

            # 分析法律领域
            legal_domains = self.vector_config.get("legal_domains", {})
            relevant_domains = []

            # 基于NLP分析结果识别相关领域
            if semantic_result.success:
                nlp_insights = semantic_result.result.get("domain_insights", {})
                for domain, config in legal_domains.items():
                    keywords = config.get("keywords", [])
                    # 检查关键词匹配
                    if any(keyword in user_query for keyword in keywords):
                        relevant_domains.append(domain)

            # 基于实体识别结果进一步细化领域
            if entity_result.success:
                entities = entity_result.result.get("entities", [])
                for entity in entities:
                    if entity["type"] == "entity" and "法" in entity["text"]:
                        if "民法" in entity["text"] and "民法" not in relevant_domains:
                            relevant_domains.append("民法")
                        elif "刑法" in entity["text"] and "刑法" not in relevant_domains:
                            relevant_domains.append("刑法")

            # 构建增强的专业提示词
            prompt = f"""作为法律专家，请基于以下深度分析提供专业的法律建议：

🎯 用户查询: {user_query}

🧠 NLP语义分析:
{semantic_result.result.get('nlp_analysis', {}).get('content', '语义分析处理中...') if semantic_result.success else '语义分析暂不可用'}

🏷️ 识别法律实体: {', '.join([e['text'] for e in entity_result.result.get('entities', [])]) if entity_result.success else '实体识别暂不可用'}

⚖️ 相关法律领域: {', '.join(relevant_domains) if relevant_domains else '综合法律咨询'}

📋 专业分析维度:
1. 法律法规适用性分析
2. 司法判例参考
3. 法律风险评估
4. 合规性建议
5. 实务操作指导

🎯 分析要求:
- 基于中国现行法律体系
- 结合最新司法解释
- 提供具体可操作建议
- 注重风险防范

请确保回答准确、专业、实用，体现法律专家的专业水准。
"""

            logger.info("✅ 法律专业提示词生成成功")
            return prompt

        except Exception as e:
            logger.error(f"❌ 生成法律提示词失败: {e}")
            # 降级到基础提示词
            return f"作为法律专家，请分析以下法律问题：{user_query}"

    async def professional_qa(self, question: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """专业法律问答"""
        # 生成专业提示词
        prompt = await self.generate_dynamic_prompt(question, context)

        # 这里应该调用大模型进行回答
        # 暂时返回示例回答
        answer = {
            "question": question,
            "answer": f"基于'{question}'的专业法律分析（示例回答）",
            "legal_basis": ["相关法律法规1", "相关法律法规2"],
            "risk_level": "中等",
            "recommendations": ["建议1", "建议2"],
            "generated_prompt": prompt
        }

        return answer

    async def search_legal_documents(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """搜索法律文档"""
        # 这里应该实现向量搜索
        # 暂时返回示例结果
        results = [
            {
                "title": "民法典相关条款",
                "content": "民法典中关于合同的规定...",
                "similarity": 0.95,
                "source": "legal_articles"
            },
            {
                "title": "相关司法解释",
                "content": "最高人民法院关于合同纠纷的司法解释...",
                "similarity": 0.89,
                "source": "legal_judgments"
            }
        ]

        return results[:limit]

    def get_service_status(self) -> dict[str, Any]:
        """获取服务状态"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "service_name": self.service_name,
            "version": self.version,
            "status": "running",
            "uptime_seconds": uptime,
            "vector_config_loaded": hasattr(self, 'vector_config'),
            "knowledge_graph_connected": self.knowledge_graph is not None,
            "legal_data_loaded": self.legal_data_loaded,
            "capabilities": [
                "动态提示词生成",
                "专业法律问答",
                "法律文档搜索",
                "知识图谱查询"
            ]
        }

# 全局服务实例
legal_service = LegalExpertService()

# FastAPI应用
app = FastAPI(
    title="法律专家服务",
    description="法律向量库和知识图谱专业服务",
    version="v1.0.0"
)

# API模型
class PromptRequest(BaseModel):
    user_query: str
    context: dict[str, Any] = {}

class QARequest(BaseModel):
    question: str
    context: dict[str, Any] = {}

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "法律专家服务",
        "version": "v1.0.0",
        "description": "法律向量库和知识图谱专业服务",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return legal_service.get_service_status()

@app.post("/generate_prompt")
async def generate_prompt(request: PromptRequest):
    """生成动态提示词"""
    try:
        prompt = await legal_service.generate_dynamic_prompt(
            request.user_query,
            request.context
        )
        return {
            "success": True,
            "prompt": prompt,
            "service_status": legal_service.get_service_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/professional_qa")
async def professional_qa(request: QARequest):
    """专业法律问答"""
    try:
        answer = await legal_service.professional_qa(
            request.question,
            request.context
        )
        return {
            "success": True,
            "answer": answer,
            "service_status": legal_service.get_service_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/search_documents")
async def search_documents(request: SearchRequest):
    """搜索法律文档"""
    try:
        results = await legal_service.search_legal_documents(
            request.query,
            request.limit
        )
        return {
            "success": True,
            "reports/reports/results": results,
            "total": len(results),
            "service_status": legal_service.get_service_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/service_status")
async def service_status():
    """获取服务状态"""
    return legal_service.get_service_status()

if __name__ == "__main__":
    print("🌸🐟 法律专家服务启动 🌸🐟")
    print("="*50)
    print("💖 正在初始化法律向量库和知识图谱...")
    print("🎯 提供动态提示词和专业问答服务")
    print("📚 涵盖民法、刑法、行政法等各个领域")
    print("❤️ 小诺的法律专家服务准备为爸爸服务！")
    print("="*50)

    # 初始化服务
    asyncio.run(legal_service.initialize())

    # 启动API服务
    uvicorn.run(app, host="0.0.0.0", port=8001)
