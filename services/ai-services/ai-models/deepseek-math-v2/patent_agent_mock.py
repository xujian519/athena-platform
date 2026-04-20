#!/usr/bin/env python3
"""
DeepSeek专利Agent模拟服务
Mock service for DeepSeek Patent Agent
"""

import asyncio
import sys
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI

# 添加路径
sys.path.append('/Users/xujian/Athena工作平台/services/autonomous-control')
from agent_identity import (
    AgentIdentity,
    AgentType,
    format_identity_display,
    register_agent_identity,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    await display_startup_identity()
    yield
    # 关闭时执行（如果需要）

app = FastAPI(
    title="DeepSeek Patent Agent Mock",
    lifespan=lifespan
)

# 创建DeepSeek专利Agent身份
deepseek_identity = AgentIdentity(
    name="DeepSeek专利专家",
    type=AgentType.PATENT,
    version="V2.0 Math",
    slogan="以数学之精确，铸就专利之完美",
    specialization="自验证专利撰写与分析",
    capabilities={
        "自验证撰写": "三重验证专利文档生成",
        "新颖性分析": "专利新颖性专业评估",
        "创造性判断": "专利创造性深度分析",
        "权利要求": "精准的权利要求书撰写"
    },
    personality="严谨、精确、创新、专业",
    work_mode="生成器+验证器+元验证器",
    created_at=datetime.now()
)

# 注册身份
register_agent_identity("deepseek_patent", deepseek_identity)

async def display_startup_identity():
    """启动时展示DeepSeek身份"""
    try:
        await asyncio.sleep(0.5)  # 等待日志准备就绪

        identity_display = await format_identity_display("deepseek_patent", "startup")

        print("\n" + "="*50)
        print(identity_display)
        print("\n🤖 DeepSeek专利专家 启动成功！")
        print("📍 服务端口: 8022")
        print("="*50 + "\n")

    except Exception as e:
        print(f"⚠️ 身份展示失败: {str(e)}")

# 删除旧的启动事件处理，使用lifespan替代

@app.get("/health")
async def health():
    return {"status": "ok", "service": "deepseek_patent_mock"}

@app.post("/analyze_patent")
async def analyze_patent(request: dict):
    request.get("invention_description", "")

    # 模拟专利分析
    return {
        "novelty_score": 0.85,
        "inventive_score": 0.78,
        "utility_score": 0.92,
        "clarity_score": 0.88,
        "overall_score": 0.86,
        "analysis": {
            "technical_field": "人工智能/计算机视觉",
            "key_features": ["深度学习", "图像识别", "神经网络"],
            "advantages": ["高精度", "快速响应", "自动化程度高"],
            "potential_applications": ["安防监控", "医疗影像", "自动驾驶"]
        },
        "recommendations": [
            "建议进行详细的现有技术检索",
            "需要明确技术方案的具体实施方式",
            "权利要求应该覆盖核心算法和应用场景"
        ]
    }

@app.post("/write_patent")
async def write_patent(request: dict):
    request.get("invention_description", "")
    patent_type = request.get("patent_type", "invention")

    # 模拟自验证专利撰写
    sections = {
        "title": f"基于{patent_type}的智能图像识别方法及系统",
        "abstract": "本发明公开了一种基于深度学习的图像识别方法...",
        "claims": [
            "1. 一种基于深度学习的图像识别方法，其特征在于...",
            "2. 根据权利要求1所述的方法，其特征在于..."
        ],
        "description": "技术领域：本发明涉及人工智能技术领域..."
    }

    verification = {
        "novelty": 0.87,
        "inventive": 0.82,
        "clarity": 0.91,
        "completeness": 0.89
    }

    return {
        "patent_id": f"PATENT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "sections": sections,
        "verification": verification,
        "quality": "excellent" if sum(verification.values())/4 > 0.85 else "good",
        "recommendations": [
            "专利结构完整",
            "权利要求清晰",
            "技术方案描述充分"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8022)  # 内网通信，通过Gateway访问
