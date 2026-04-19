#!/usr/bin/env python3
"""
DeepSeek专利专家 - 简化版真实API服务
基于现有成功模式，确保稳定运行
"""

import asyncio
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException

# 添加路径
sys.path.append('/Users/xujian/Athena工作平台/services/autonomous-control')
# 导入安全配置
import sys
from pathlib import Path

from agent_identity import (
    AgentIdentity,
    AgentType,
    format_identity_display,
    register_agent_identity,
)

sys.path.append(str(Path(__file__).parent.parent / "core"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await display_startup_identity()
    # 初始化DeepSeek客户端
    try:
        api_key = 'sk-7f0fa1165de249d0a30b62a2584bd4c5'
        app.state.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),  # 减少超时时间
            headers={
                'Authorization': f"Bearer {api_key}",
                'Content-Type': 'application/json'
            }
        )
        # 测试连接
        test_payload = {
            'model': 'deepseek-chat',
            'messages': [{'role': 'user', 'content': 'Hello'}],
            'max_tokens': 10
        }
        async with app.state.session.post('https://api.deepseek.com/v1/chat/completions', json=test_payload) as resp:
            if resp.status == 200:
                print("✅ DeepSeek API连接成功!")
            else:
                print(f"⚠️ DeepSeek API连接失败: {resp.status}")
    except Exception as e:
        print(f"⚠️ DeepSeek API初始化失败: {str(e)}")
        app.state.session = None
    yield
    # 关闭时执行
    if hasattr(app.state, 'session') and app.state.session:
        await app.state.session.close()

app = FastAPI(
    title="DeepSeek专利专家 - 简化版",
    description="基于真实DeepSeek API的简化版专利分析服务",
    lifespan=lifespan
)

# 创建DeepSeek专利专家身份
deepseek_patent_identity = AgentIdentity(
    name="DeepSeek专利专家",
    type=AgentType.PATENT,
    version="Simplified Real API 1.0",
    slogan="以数学之精确，铸就专利之完美",
    specialization="专利分析、技术方案实现",
    capabilities={
        "专利分析": "基于DeepSeek大模型的专利智能分析",
        "技术评估": "专利技术可行性与创新性评估",
        "方案设计": "基于专利技术的实现方案设计",
        "专利检索": "专利相似性与新颖性分析"
    },
    personality="严谨、精确、创新、专业",
    work_mode="真实API + 简化接口 + 快速响应",
    created_at=datetime.now()
)

# 注册身份
register_agent_identity("deepseek_patent_simplified", deepseek_patent_identity)

async def display_startup_identity():
    """启动时展示DeepSeek专利专家身份"""
    try:
        await asyncio.sleep(0.5)

        identity_display = await format_identity_display("deepseek_patent_simplified", "startup")

        print("\n" + "="*60)
        print(identity_display)
        print("\n🤖 DeepSeek专利专家 (简化版) 启动成功！")
        print("📍 服务端口: 8030")
        print("🔗 API类型: 真实DeepSeek API (简化版)")
        print("="*60 + "\n")

    except Exception as e:
        print(f"⚠️ 身份展示失败: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "DeepSeek专利专家 - 简化版真实API服务",
        "version": "Simplified Real API 1.0",
        "status": "active",
        "api_type": "real_deepseek_simplified"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    if not hasattr(app.state, 'session') or not app.state.session:
        return {
            "status": "unhealthy",
            "message": "DeepSeek API未连接",
            "service": "deepseek_patent_simplified"
        }

    return {
        "status": "healthy",
        "deepseek_api": "connected",
        "service": "deepseek_patent_simplified",
        "timestamp": datetime.now().isoformat()
    }

async def call_deepseek_api(prompt: str, max_tokens: int = 1000) -> dict[str, Any]:
    """调用DeepSeek API的简化函数"""
    try:
        if not hasattr(app.state, 'session') or not app.state.session:
            raise Exception("DeepSeek API未连接")

        payload = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'system', 'content': '你是一个专业的专利分析专家，请提供准确、专业的分析。'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': 0.1
        }

        async with app.state.session.post('https://api.deepseek.com/v1/chat/completions', json=payload) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"API请求失败: {resp.status} - {error_text}")

            result = await resp.json()
            content = result['choices'][0]['message']['content']
            tokens_used = result.get('usage', {}).get('total_tokens', 0)

            return {
                "success": True,
                "content": content,
                "tokens_used": tokens_used
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "content": "",
            "tokens_used": 0
        }

@app.post("/analyze_patent")
async def analyze_patent(request: dict):
    """使用真实DeepSeek API分析专利"""
    invention_description = request.get("invention_description", "")
    patent_type = request.get("patent_type", "invention")

    # 构建简化的分析提示
    prompt = f"""请对以下发明进行专利分析：

发明类型：{patent_type}
发明描述：{invention_description}

请从以下几个方面进行分析：
1. 技术方案的新颖性（0-1分）
2. 创造性（0-1分）
3. 实用性（0-1分）
4. 技术实现难度（0-1分）
5. 市场前景评估（0-1分）

请给出具体的分数和简要说明。
"""

    result = await call_deepseek_api(prompt, 1500)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"专利分析失败: {result['error']}")

    # 模拟分数提取（实际应用中可以用更精确的解析）
    scores = {
        "novelty_score": 0.85,
        "inventive_score": 0.78,
        "utility_score": 0.92,
        "implementation_score": 0.75,
        "market_score": 0.80,
        "overall_score": 0.82
    }

    return {
        "success": True,
        "analysis": result["content"],
        "scores": scores,
        "tokens_used": result["tokens_used"],
        "timestamp": datetime.now().isoformat(),
        "api_type": "real_deepseek_simplified"
    }

@app.post("/generate_patent_code")
async def generate_patent_code(request: dict):
    """基于专利技术方案生成实现代码"""
    invention_description = request.get("invention_description", "")
    code_language = request.get("language", "python")

    # 构建简化的代码生成提示
    prompt = f"""基于以下专利技术方案，请生成{code_language}实现代码：

技术方案：{invention_description}

要求：
1. 生成核心功能的实现代码
2. 添加必要的注释
3. 包含简单的使用示例
4. 代码应该简洁、可运行

请直接提供代码，不需要过多解释。
"""

    result = await call_deepseek_api(prompt, 2000)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"代码生成失败: {result['error']}")

    # 尝试从响应中提取代码
    content = result["content"]
    code = content
    explanation = "基于DeepSeek API生成的代码实现"

    # 简单的代码提取
    if "```" in content:
        parts = content.split("```")
        if len(parts) >= 2:
            code = parts[1]
            if "\n" in code:
                code = "\n".join(code.split("\n")[1:])  # 移除语言标识
            explanation = "\n".join(parts[::2])  # 获取解释部分

    return {
        "success": True,
        "code": code,
        "explanation": explanation,
        "language": code_language,
        "tokens_used": result["tokens_used"],
        "timestamp": datetime.now().isoformat(),
        "api_type": "real_deepseek_simplified"
    }

@app.post("/evaluate_patentability")
async def evaluate_patentability(request: dict):
    """评估专利可申请性"""
    invention_description = request.get("invention_description", "")
    prior_art = request.get("prior_art", "未提供")

    # 构建简化的可专利性评估提示
    prompt = f"""请评估以下技术的可申请性：

发明描述：{invention_description}
现有技术：{prior_art}

请评估：
1. 是否具有新颖性？
2. 是否具有创造性？
3. 是否具有实用性？
4. 是否属于专利保护范围？
5. 申请建议

请给出明确的结论和建议。
"""

    result = await call_deepseek_api(prompt, 1500)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"可专利性评估失败: {result['error']}")

    return {
        "success": True,
        "evaluation": result["content"],
        "recommendations": [
            "基于DeepSeek AI的专业分析",
            "建议进一步进行现有技术检索",
            "考虑申请策略的优化"
        ],
        "tokens_used": result["tokens_used"],
        "timestamp": datetime.now().isoformat(),
        "api_type": "real_deepseek_simplified"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8030)
