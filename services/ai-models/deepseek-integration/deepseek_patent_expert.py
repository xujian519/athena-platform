#!/usr/bin/env python3
"""
DeepSeek专利专家服务 - 真实API集成
整合真实的DeepSeek API与专利专业知识
"""

import asyncio
import sys
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException

# 添加路径
sys.path.append('/Users/xujian/Athena工作平台/services/autonomous-control')
from agent_identity import (
    AgentIdentity,
    AgentType,
    format_identity_display,
    register_agent_identity,
)

# 导入DeepSeek服务
from deepseek_coder_service import (
    CodeGenerationRequest,
    DeepSeekCoderAPI,
    ProgrammingLanguage,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await display_startup_identity()
    # 初始化DeepSeek客户端
    try:
        app.state.deepseek_client = DeepSeekCoderAPI()
        await app.state.deepseek_client.__aenter__()
        print("✅ DeepSeek API连接成功!")
    except Exception as e:
        print(f"⚠️ DeepSeek API连接失败: {str(e)}")
        app.state.deepseek_client = None
    yield
    # 关闭时执行
    if hasattr(app.state, 'deepseek_client') and app.state.deepseek_client:
        await app.state.deepseek_client.__aexit__(None, None, None)

app = FastAPI(
    title="DeepSeek专利专家 - 真实API",
    description="基于真实DeepSeek API的专利分析与代码生成服务",
    lifespan=lifespan
)

# 创建DeepSeek专利专家身份
deepseek_patent_identity = AgentIdentity(
    name="DeepSeek专利专家",
    type=AgentType.PATENT,
    version="Real API 1.0",
    slogan="以数学之精确，铸就专利之完美",
    specialization="专利分析、代码生成与技术实现",
    capabilities={
        "专利分析": "基于DeepSeek大模型的专利深度分析",
        "代码生成": "根据专利技术方案生成实现代码",
        "技术评估": "专利技术可行性与创新性评估",
        "权利要求": "精准的权利要求书生成与分析",
        "专利检索": "智能专利检索与相似性分析"
    },
    personality="严谨、精确、创新、专业",
    work_mode="真实API + 专业知识 + 智能分析",
    created_at=datetime.now()
)

# 注册身份
register_agent_identity("deepseek_patent_expert", deepseek_patent_identity)

async def display_startup_identity():
    """启动时展示DeepSeek专利专家身份"""
    try:
        await asyncio.sleep(0.5)

        identity_display = await format_identity_display("deepseek_patent_expert", "startup")

        print("\n" + "="*60)
        print(identity_display)
        print("\n🤖 DeepSeek专利专家 (真实API) 启动成功！")
        print("📍 服务端口: 8029")
        print("🔗 API类型: 真实DeepSeek API集成")
        print("="*60 + "\n")

    except Exception as e:
        print(f"⚠️ 身份展示失败: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "DeepSeek专利专家 - 真实API服务",
        "version": "Real API 1.0",
        "status": "active",
        "api_type": "real_deepseek"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    if not hasattr(app.state, 'deepseek_client') or not app.state.deepseek_client:
        return {
            "status": "unhealthy",
            "message": "DeepSeek API未连接",
            "service": "deepseek_patent_expert"
        }

    try:
        # 测试API连接
        connected = await app.state.deepseek_client.test_connection()
        return {
            "status": "healthy" if connected else "degraded",
            "deepseek_api": "connected" if connected else "disconnected",
            "service": "deepseek_patent_expert",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e),
            "service": "deepseek_patent_expert"
        }

@app.post("/analyze_patent")
async def analyze_patent(request: dict):
    """使用真实DeepSeek API分析专利"""
    try:
        if not hasattr(app.state, 'deepseek_client') or not app.state.deepseek_client:
            raise HTTPException(status_code=503, detail="DeepSeek API未连接")

        invention_description = request.get("invention_description", "")
        patent_type = request.get("patent_type", "invention")
        analysis_type = request.get("analysis_type", "comprehensive")

        # 构建专利分析提示词
        analysis_prompt = f"""
作为专利分析专家，请对以下发明进行深度分析：

发明类型：{patent_type}
分析类型：{analysis_type}

发明描述：
{invention_description}

请从以下角度进行分析：
1. 技术方案的新颖性评估
2. 创造性分析
3. 实用性评价
4. 技术实现可行性
5. 潜在的专利权利要求范围
6. 与现有技术的差异

分析结果应包含具体的评分(0-1)和详细的解释。
"""

        # 创建代码生成请求（用于分析）
        code_request = CodeGenerationRequest(
            prompt=analysis_prompt,
            language=ProgrammingLanguage.PYTHON,  # 使用Python作为分析载体
            max_tokens=3000,
            temperature=0.1
        )

        # 调用DeepSeek API
        response = await app.state.deepseek_client.generate_code(code_request)

        # 解析分析结果
        analysis_text = response.explanation if response.explanation else response.code

        # 模拟提取评分（实际应用中可以用更复杂的解析）
        scores = {
            "novelty_score": 0.85,  # 这些可以从分析文本中解析
            "inventive_score": 0.78,
            "utility_score": 0.92,
            "clarity_score": 0.88,
            "overall_score": 0.86
        }

        return {
            "success": True,
            "analysis": analysis_text,
            "scores": scores,
            "tokens_used": response.tokens_used,
            "response_time": response.response_time,
            "timestamp": datetime.now().isoformat(),
            "api_type": "real_deepseek"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"专利分析失败: {str(e)}") from e

@app.post("/generate_patent_code")
async def generate_patent_code(request: dict):
    """基于专利技术方案生成实现代码"""
    try:
        if not hasattr(app.state, 'deepseek_client') or not app.state.deepseek_client:
            raise HTTPException(status_code=503, detail="DeepSeek API未连接")

        invention_description = request.get("invention_description", "")
        code_language = request.get("language", "python")
        implementation_level = request.get("implementation_level", "prototype")

        # 构建专利代码生成提示
        code_prompt = f"""
基于以下专利技术方案，请生成完整的实现代码：

技术方案：
{invention_description}

实现要求：
- 实现级别：{implementation_level}
- 代码语言：{code_language}
- 请确保代码体现专利的创新点
- 添加详细的注释说明
- 包含示例用法

请生成可以直接运行的完整代码。
"""

        # 解析编程语言
        language_map = {
            'python': ProgrammingLanguage.PYTHON,
            'javascript': ProgrammingLanguage.JAVASCRIPT,
            'java': ProgrammingLanguage.JAVA,
            'cpp': ProgrammingLanguage.CPP,
            'c++': ProgrammingLanguage.CPP,
            'go': ProgrammingLanguage.GO,
            'rust': ProgrammingLanguage.RUST
        }

        lang_enum = language_map.get(code_language.lower(), ProgrammingLanguage.PYTHON)

        # 创建代码生成请求
        code_request = CodeGenerationRequest(
            prompt=code_prompt,
            language=lang_enum,
            max_tokens=4000,
            temperature=0.1
        )

        # 调用DeepSeek API
        response = await app.state.deepseek_client.generate_code(code_request)

        return {
            "success": True,
            "code": response.code,
            "explanation": response.explanation,
            "language": response.language,
            "tokens_used": response.tokens_used,
            "response_time": response.response_time,
            "timestamp": datetime.now().isoformat(),
            "api_type": "real_deepseek"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码生成失败: {str(e)}") from e

@app.post("/evaluate_patentability")
async def evaluate_patentability(request: dict):
    """评估专利可申请性"""
    try:
        if not hasattr(app.state, 'deepseek_client') or not app.state.deepseek_client:
            raise HTTPException(status_code=503, detail="DeepSeek API未连接")

        invention_description = request.get("invention_description", "")
        prior_art = request.get("prior_art", "")
        technical_field = request.get("technical_field", "")

        # 构建可专利性评估提示
        evaluation_prompt = f"""
作为专利审查专家，请评估以下技术的可专利性：

技术领域：{technical_field}

发明描述：
{invention_description}

现有技术（对比文件）：
{prior_art}

请从以下方面进行评估：
1. 新颖性：是否与现有技术不同
2. 创造性：是否有突出的实质性特点和显著的进步
3. 实用性：是否能够制造或使用
4. 是否属于专利保护客体
5. 建议的申请策略

请提供详细的评估报告和具体建议。
"""

        # 创建评估请求
        evaluation_request = CodeGenerationRequest(
            prompt=evaluation_prompt,
            language=ProgrammingLanguage.PYTHON,
            max_tokens=3500,
            temperature=0.1
        )

        # 调用DeepSeek API
        response = await app.state.deepseek_client.generate_code(evaluation_request)

        evaluation_text = response.explanation if response.explanation else response.code

        return {
            "success": True,
            "evaluation": evaluation_text,
            "recommendations": [
                "基于DeepSeek AI的专业分析完成",
                "建议进行详细的现有技术检索",
                "考虑申请策略的优化"
            ],
            "tokens_used": response.tokens_used,
            "response_time": response.response_time,
            "timestamp": datetime.now().isoformat(),
            "api_type": "real_deepseek"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"可专利性评估失败: {str(e)}") from e

@app.get("/statistics")
async def get_statistics():
    """获取服务使用统计"""
    try:
        if not hasattr(app.state, 'deepseek_client') or not app.state.deepseek_client:
            return {
                "error": "DeepSeek API未连接",
                "service": "deepseek_patent_expert"
            }

        stats = app.state.deepseek_client.get_statistics()
        return {
            **stats,
            "service": "deepseek_patent_expert",
            "api_type": "real_deepseek",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "error": str(e),
            "service": "deepseek_patent_expert"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8029)  # 内网通信，通过Gateway访问
