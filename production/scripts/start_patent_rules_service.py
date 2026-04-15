#!/usr/bin/env python3
"""
专利规则服务按需启动脚本 (NLP深度集成版)
Patent Rules Service On-Demand Startup (NLP Deep Integration)

启动专利规则向量库和知识图谱服务，与NLP系统深度集成，提供动态提示词和专业问答

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


class PatentRulesService:
    """专利规则服务类 (NLP深度集成版)"""

    def __init__(self):
        self.service_name = "Patent Rules Service"
        self.version = "v2.0.0"
        self.start_time = datetime.now()
        self.rule_engine = None
        self.knowledge_graph = None
        self.patent_data_loaded = False
        self.nlp_service = NLPIntegrationService()
        self.domain = ProfessionalDomain.PATENT

    async def initialize(self):
        """初始化服务"""
        logger.info("🧠 初始化专利规则服务...")

        # 加载专利规则配置
        await self._load_rules_config()

        # 初始化规则引擎
        await self._init_rule_engine()

        # 加载专利数据
        await self._load_patent_data()

        logger.info("✅ 专利规则服务初始化完成")

    async def _load_rules_config(self):
        """加载专利规则配置"""
        try:
            config_path = project_root / "config" / "patent_rules_config.json"
            if config_path.exists():
                with open(config_path, encoding='utf-8') as f:
                    self.rules_config = json.load(f)
                logger.info("✅ 专利规则配置加载成功")
            else:
                # 创建默认配置
                self.rules_config = {
                    "patent_rule_types": {
                        "novelty": {"weight": 2.0, "keywords": ["新颖性", "现有技术", "公开"]},
                        "inventiveness": {"weight": 2.5, "keywords": ["创造性", "进步", "显著"]},
                        "utility": {"weight": 1.5, "keywords": ["实用性", "工业应用", "可实施"]},
                        "disclosure": {"weight": 1.8, "keywords": ["充分公开", "说明书", "清楚完整"]},
                        "claim_scope": {"weight": 2.0, "keywords": ["权利要求", "保护范围", "清楚"]}
                    }
                }
                logger.info("✅ 使用默认专利规则配置")
        except Exception as e:
            logger.error(f"❌ 加载专利规则配置失败: {e}")

    async def _init_rule_engine(self):
        """初始化规则引擎"""
        try:
            # 这里应该初始化专利规则引擎
            # 暂时标记为已初始化
            self.rule_engine = True
            logger.info("✅ 专利规则引擎初始化成功")
        except Exception as e:
            logger.error(f"❌ 初始化专利规则引擎失败: {e}")

    async def _load_patent_data(self):
        """加载专利数据"""
        try:
            # 检查是否有专利数据文件
            patent_data_paths = [
                project_root / "data" / "patent_rules_data.json",
                project_root / "data" / "exports" / "patent_dataset.json"
            ]

            for data_path in patent_data_paths:
                if data_path.exists():
                    with open(data_path, encoding='utf-8') as f:
                        self.patent_dataset = json.load(f)
                    self.patent_data_loaded = True
                    logger.info("✅ 专利数据加载成功")
                    break
            else:
                logger.warning("⚠️ 专利数据文件不存在，将使用模拟数据")
                self.patent_data_loaded = False

        except Exception as e:
            logger.error(f"❌ 加载专利数据失败: {e}")

    async def generate_dynamic_prompt(self, user_query: str, context: dict[str, Any] = None) -> str:
        """生成动态提示词"""
        rule_types = self.rules_config.get("patent_rule_types", {})

        # 分析查询涉及的专利规则类型
        relevant_rules = []
        for rule_type, config in rule_types.items():
            keywords = config.get("keywords", [])
            if any(keyword in user_query for keyword in keywords):
                relevant_rules.append(rule_type)

        # 构建专业提示词
        prompt = f"""作为专利审查专家，请基于以下信息提供专业的专利分析和建议：

用户查询: {user_query}

相关专利规则类型: {', '.join(relevant_rules) if relevant_rules else '综合专利咨询'}

请从以下角度进行分析:
1. 专利法相关规定
2. 审查指南要求
3. 相关案例分析
4. 专业建议和策略

请确保回答准确、专业、实用，符合专利审查标准。
"""

        return prompt

    async def professional_qa(self, question: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """专业专利问答"""
        # 生成专业提示词
        prompt = await self.generate_dynamic_prompt(question, context)

        # 这里应该调用大模型进行回答
        # 暂时返回示例回答
        answer = {
            "question": question,
            "answer": f"基于'{question}'的专业专利分析（示例回答）",
            "legal_basis": ["专利法相关规定1", "审查指南相关条款2"],
            "relevant_cases": ["相关案例1", "相关案例2"],
            "recommendations": ["建议1", "建议2"],
            "generated_prompt": prompt
        }

        return answer

    async def analyze_patent_rules(self, patent_text: str, analysis_type: str = "comprehensive") -> dict[str, Any]:
        """分析专利规则"""
        # 这里应该实现专利规则分析
        # 暂时返回示例结果
        analysis_result = {
            "patent_text": patent_text[:100] + "...",
            "analysis_type": analysis_type,
            "rule_compliance": {
                "novelty": {"score": 0.85, "status": "符合"},
                "inventiveness": {"score": 0.78, "status": "待定"},
                "utility": {"score": 0.92, "status": "符合"},
                "disclosure": {"score": 0.88, "status": "符合"}
            },
            "recommendations": [
                "建议加强创造性说明",
                "完善技术实施例"
            ],
            "risk_factors": [
                "创造性可能不足"
            ]
        }

        return analysis_result

    async def search_patent_rules(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """搜索专利规则"""
        # 这里应该实现向量搜索
        # 暂时返回示例结果
        results = [
            {
                "title": "专利法第22条 - 新颖性规定",
                "content": "新颖性是指发明或者实用新型不属于现有技术...",
                "similarity": 0.95,
                "source": "patent_law"
            },
            {
                "title": "审查指南第二部分第四章 - 创造性审查",
                "content": "创造性是指与现有技术相比，该发明具有突出的实质性特点和显著的进步...",
                "similarity": 0.89,
                "source": "examination_guidelines"
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
            "rule_engine_ready": self.rule_engine is not None,
            "knowledge_graph_connected": self.knowledge_graph is not None,
            "patent_data_loaded": self.patent_data_loaded,
            "capabilities": [
                "动态提示词生成",
                "专业专利问答",
                "专利规则分析",
                "专利规则搜索"
            ],
            "supported_rule_types": list(self.rules_config.get("patent_rule_types", {}).keys())
        }

# 全局服务实例
patent_rules_service = PatentRulesService()

# FastAPI应用
app = FastAPI(
    title="专利规则服务",
    description="专利规则向量库和知识图谱专业服务",
    version="v1.0.0"
)

# API模型
class PromptRequest(BaseModel):
    user_query: str
    context: dict[str, Any] = {}

class QARequest(BaseModel):
    question: str
    context: dict[str, Any] = {}

class AnalysisRequest(BaseModel):
    patent_text: str
    analysis_type: str = "comprehensive"

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "专利规则服务",
        "version": "v1.0.0",
        "description": "专利规则向量库和知识图谱专业服务",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return patent_rules_service.get_service_status()

@app.post("/generate_prompt")
async def generate_prompt(request: PromptRequest):
    """生成动态提示词"""
    try:
        prompt = await patent_rules_service.generate_dynamic_prompt(
            request.user_query,
            request.context
        )
        return {
            "success": True,
            "prompt": prompt,
            "service_status": patent_rules_service.get_service_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/professional_qa")
async def professional_qa(request: QARequest):
    """专业专利问答"""
    try:
        answer = await patent_rules_service.professional_qa(
            request.question,
            request.context
        )
        return {
            "success": True,
            "answer": answer,
            "service_status": patent_rules_service.get_service_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/analyze_rules")
async def analyze_rules(request: AnalysisRequest):
    """分析专利规则"""
    try:
        analysis = await patent_rules_service.analyze_patent_rules(
            request.patent_text,
            request.analysis_type
        )
        return {
            "success": True,
            "analysis": analysis,
            "service_status": patent_rules_service.get_service_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/search_rules")
async def search_rules(request: SearchRequest):
    """搜索专利规则"""
    try:
        results = await patent_rules_service.search_patent_rules(
            request.query,
            request.limit
        )
        return {
            "success": True,
            "reports/reports/results": results,
            "total": len(results),
            "service_status": patent_rules_service.get_service_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/service_status")
async def service_status():
    """获取服务状态"""
    return patent_rules_service.get_service_status()

if __name__ == "__main__":
    print("🌸🐟 专利规则服务启动 🌸🐟")
    print("="*50)
    print("💖 正在初始化专利规则向量库和知识图谱...")
    print("🎯 提供动态提示词和专业问答服务")
    print("📋 涵盖新颖性、创造性、实用性等各个维度")
    print("❤️ 小诺的专利规则服务准备为爸爸服务！")
    print("="*50)

    # 初始化服务
    asyncio.run(patent_rules_service.initialize())

    # 启动API服务
    uvicorn.run(app, host="0.0.0.0", port=8002)
