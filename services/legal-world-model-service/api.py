#!/usr/bin/env python3
"""
法律世界模型简化API服务
Legal World Model Simplified API Service

整合:
- 法律世界模型 (Legal World Model)
- 动态提示词生成器 (Dynamic Prompt Generator)
- 场景规划器 (Scenario Planner)

作者: Athena平台团队
版本: 1.0.0
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载.env文件
from dotenv import load_dotenv

env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    load_dotenv(env_file)
    logger = logging.getLogger(__name__)
    logger.info(f"已加载.env文件: {env_file}")

# =============================================================================
# 配置
# =============================================================================

# 从环境变量加载配置
PORT = int(os.getenv("LEGAL_WORLD_MODEL_PORT", "8020"))
HOST = os.getenv("LEGAL_WORLD_MODEL_HOST", "0.0.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "athena_neo4j_2024")

# 日志配置
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# 组件管理器（简化版）
# =============================================================================

class SimpleComponentManager:
    """组件管理器 - 简化版，延迟加载"""

    def __init__(self):
        self._components = {}

    def get(self, name: str, factory_fn=None):
        """获取组件，如果不存在则使用工厂函数创建"""
        if name not in self._components and factory_fn:
            self._components[name] = factory_fn()
        return self._components.get(name)

    def get_validator(self):
        """获取宪法验证器"""
        return self.get("validator", lambda: self._create_validator())

    def get_scenario_retriever(self):
        """获取场景规则检索器"""
        return self.get("scenario_retriever", lambda: self._create_retriever())

    def get_prompt_generator(self):
        """获取动态提示词生成器"""
        return self.get("prompt_generator", lambda: self._create_generator())

    def _create_generator(self):
        """创建法律世界模型提示词生成器"""
        from core.intelligence.legal_world_prompt_generator import (
            LegalWorldPromptGenerator,
        )
        return LegalWorldPromptGenerator()

    def _create_validator(self):
        from core.legal_world_model.constitution import ConstitutionalValidator
        return ConstitutionalValidator()

    def _create_retriever(self):
        """创建场景规则检索器"""
        from neo4j import GraphDatabase

        # 创建检索器类
        class SimpleScenarioRuleRetriever:
            """简化的场景规则检索器"""

            def __init__(self):
                self.driver = GraphDatabase.driver(
                    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                    auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD", ""))
                )

            def check_connection(self):
                """检查Neo4j连接"""
                try:
                    with self.driver.session() as session:
                        result = session.run("RETURN 1 as test")
                        result.single()
                    return True
                except Exception:
                    return False

            def retrieve_rule(self, domain, scenario):
                """检索规则"""
                with self.driver.session() as session:
                    result = session.run("""
                        MATCH (sr:ScenarioRule)
                        WHERE sr.domain = $domain
                          AND sr.task_type = $task_type
                          AND sr.is_active = true
                        RETURN sr
                        ORDER BY sr.version DESC
                        LIMIT 1
                    """, domain=domain, task_type=scenario)
                    record = result.single()
                    if record:
                        sr = record["sr"]
                        return {
                            "domain": sr.get("domain"),
                            "task_type": sr.get("task_type"),
                            "phase": sr.get("phase")
                        }
                    return None

            def retrieve_all_rules_for_domain(self, domain):
                """检索领域所有规则"""
                with self.driver.session() as session:
                    result = session.run("""
                        MATCH (sr:ScenarioRule)
                        WHERE sr.domain = $domain
                          AND sr.is_active = true
                        RETURN sr
                        ORDER BY sr.task_type, sr.phase
                    """, domain=domain)
                    rules = []
                    for record in result:
                        sr = record["sr"]
                        rules.append({
                            "domain": sr.get("domain"),
                            "task_type": sr.get("task_type"),
                            "phase": sr.get("phase")
                        })
                    return rules

            def list_available_scenarios(self):
                """列出可用场景"""
                with self.driver.session() as session:
                    result = session.run("""
                        MATCH (sr:ScenarioRule)
                        WHERE sr.is_active = true
                        RETURN DISTINCT sr.domain as domain,
                               collect(DISTINCT sr.task_type) as task_types
                        ORDER BY domain
                    """)
                    scenarios = {}
                    for record in result:
                        scenarios[record["domain"] = record["task_types"]
                    return scenarios

        return SimpleScenarioRuleRetriever()

    def _create_generator(self):
        from core.intelligence.dynamic_prompt_generator import DynamicPromptGenerator
        return DynamicPromptGenerator()


# 全局组件管理器
components = SimpleComponentManager()

# =============================================================================
# FastAPI应用
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 60)
    logger.info("🚀 法律世界模型API服务启动中...")
    logger.info("=" * 60)
    logger.info(f"  服务地址: http://{HOST}:{PORT}")
    logger.info(f"  API文档: http://{HOST}:{PORT}/docs")
    logger.info(f"  日志级别: {LOG_LEVEL}")
    logger.info("=" * 60)

    yield

    logger.info("🛑 法律世界模型API服务关闭中...")


app = FastAPI(
    title="法律世界模型API",
    description="Legal World Model API - 提供法律知识检索、场景规则查询、动态提示词生成等服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# =============================================================================
# 请求/响应模型
# =============================================================================

class GeneratePromptRequest(BaseModel):
    """动态提示词生成请求"""
    business_context: str = Field(..., description="业务上下文描述")
    user_domain: str | None = Field(None, description="用户领域（可选）")
    max_rules: int = Field(10, description="最大返回规则数")


class RetrieveRulesRequest(BaseModel):
    """场景规则检索请求"""
    domain: str = Field(..., description="领域名称")
    scenario: str | None = Field(None, description="场景名称（可选）")


# =============================================================================
# Fallback 提示词生成（当动态生成失败时使用）
# =============================================================================

def retrieve_rules_from_neo4j(domain: str, scenario_hint: str = None):
    """从Neo4j检索规则"""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD", "athena_neo4j_2024"))
        )

        with driver.session() as session:
            # 如果提供了scenario_hint，尝试匹配
            if scenario_hint and scenario_hint.strip():
                hint = scenario_hint.lower()
                result = session.run("""
                    MATCH (sr:ScenarioRule)
                    WHERE sr.domain = $domain
                      AND (sr.task_type CONTAINS $hint OR sr.task_type = $hint)
                      AND sr.is_active = true
                    RETURN sr
                    ORDER BY sr.task_type
                    LIMIT 1
                """, domain=domain, hint=hint)
            else:
                # 返回该领域的所有规则
                result = session.run("""
                    MATCH (sr:ScenarioRule)
                    WHERE sr.domain = $domain
                      AND sr.is_active = true
                    RETURN sr
                    ORDER BY sr.task_type
                """, domain=domain)

            rules = []
            for record in result:
                sr = record["sr"]
                rules.append({
                    "rule_id": sr.get("rule_id"),
                    "domain": sr.get("domain"),
                    "task_type": sr.get("task_type"),
                    "phase": sr.get("phase"),
                    "system_prompt_template": sr.get("system_prompt_template", ""),
                    "workflow_steps": sr.get("workflow_steps", "[]"),
                    "legal_basis": sr.get("legal_basis", "[]"),
                    "expert_config": sr.get("expert_config", "{}")
                })

        driver.close()
        return rules
    except Exception as e:
        logger.error(f"从Neo4j检索规则失败: {e}")
        return []


def generate_fallback_prompt(business_context: str, user_domain: str | None = None):
    """生成专业级 fallback 提示词"""

    # 检测业务类型和场景
    context_lower = business_context.lower()

    # 场景映射
    scenario_mapping = {
        "创造性": "creativity",
        "新颖性": "novelty",
        "无效": "invalidation",
        "侵权": "infringement",
        "检索": "search",
        "撰写": "drafting",
        "布局": "claims",
        "答复": "response",
        "分析": "analysis"
    }

    # 检测场景
    detected_scenario = None
    for keyword, scenario in scenario_mapping.items():
        if keyword in business_context:
            detected_scenario = scenario
            break

    # 从Neo4j检索规则
    rules = retrieve_rules_from_neo4j("patent", detected_scenario)

    # 如果找到规则，使用规则生成提示词
    if rules and len(rules) > 0:
        rule = rules[0]  # 使用第一个匹配的规则
        system_prompt = rule.get("system_prompt_template", "")

        # 构建完整提示词
        full_prompt = f"""{system_prompt}

## 当前业务
{business_context}

请根据上述专业框架，为用户的具体业务提供专业的指导和建议。"""

        return {
            "prompt": full_prompt,
            "context": {
                "business_context": business_context,
                "user_domain": user_domain,
                "matched_rule": rule.get("rule_id"),
                "fallback_mode": True,
                "source": "neo4j_rules"
            },
            "matched_rules": [{"rule_type": rule.get("task_type"), "domain": rule.get("domain")}],
            "sections": {
                "system": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt,
                "context": business_context,
                "rules": rule.get("legal_basis", "[]")[:100] + "...",
                "knowledge": "",
                "action": rule.get("workflow_steps", "[]")[:100] + "..."
            }
        }

    # 如果没有找到规则，使用原有的逻辑
    # 检测业务类型

    # 生物技术专利审查意见答复
    if any(kw in context_lower for kw in ["生物", "基因", "测序", "蛋白", "细胞", "医药"]):
        return {
            "prompt": """# 生物技术专利审查意见答复专家

## 角色定位
你是一位精通生物技术领域的资深专利代理师，具有15年以上处理生物医药、基因工程、分子生物学专利申请的经验。你熟悉中美欧专利审查实践，擅长处理创造性争议。

## 专业领域
- 基因测序技术与方法
- 蛋白质工程与修饰
- 细胞治疗技术
- 生物信息学算法
- 抗体药物开发
- 基因编辑技术（CRISPR等）

## 三层法律依据

### 基础法律层
- 《中华人民共和国专利法》第22条（新颖性、创造性、实用性）
- 《专利审查指南》第二部分第四章（创造性判断）
- 《专利审查指南》第二部分第十章（生物技术发明）

### 专利专业层
- 专利审查指南关于生物技术的特殊规定
- 涉及微生物的发明专利申请相关规定
- 生物序列的可专利性判断标准
- 生物材料保藏要求

### 司法案例层
- 相关生物技术专利无效宣告案例
- 最高人民法院知识产权法庭典型案例
- 复审委关于生物领域创造性判断的 precedent

## 答复工作流程

### 阶段1：审查意见分析
1. 识别审查员引用的对比文件
2. 分析技术特征比对表
3. 确定争议焦点（新颖性/创造性）
4. 评估审查意见的法律依据

### 阶段2：技术方案论证
1. 阐述发明技术方案的技术问题
2. 分析对比文件的技术教导
3. 论证区别技术特征的 non-obviousness
4. 提供技术效果数据支撑

### 阶段3：法律论据构建
1. 引用《专利审查指南》相关规定
2. 适用"三步法"创造性判断
3. 区分"事后诸葛亮"分析
4. 强调生物领域技术预测的不确定性

### 阶段4：答复书撰写
1. 修改权利要求（如有必要）
2. 撰写意见陈述书
3. 提供实验数据或对比实验
4. 引用司法案例支持论点

## 生物领域特殊考量

### 创造性判断要点
- 生物技术的不可预测性
- 技术效果的可重复性要求
- 对比实验数据的重要性
- 已知技术的组合是否显而易见

### 常用答复策略
1. 强调技术问题的重新发现
2. 论证技术方案的非显而易见性
3. 提供意料不到的技术效果
4. 反驳事后诸葛亮的分析方式

## 质量标准
- 法律论证严密，逻辑清晰
- 技术分析专业，术语准确
- 证据充分，数据可靠
- 符合专利审查实践要求

## 当前业务
""" + business_context + """

请根据上述框架，为用户提供专业的审查意见答复策略和具体的法律论证建议。""",
            "context": {
                "business_context": business_context,
                "user_domain": user_domain,
                "scenario_detected": "biotech_patent_response",
                "fallback_mode": True
            },
            "matched_rules": [
                {"rule_type": "专利创造性答复", "domain": "patent", "priority": "high"},
                {"rule_type": "生物技术特殊规定", "domain": "patent", "priority": "high"},
                {"rule_type": "三步法判断", "domain": "patent", "priority": "medium"}
            ],
            "sections": {
                "system": "生物技术专利审查意见答复专家",
                "context": business_context,
                "rules": "专利法第22条、审查指南第二部分第四章/第十章",
                "knowledge": "生物技术创造性判断、三步法、不可预测性",
                "action": "分析审查意见→技术论证→法律论据→撰写答复书"
            }
        }

    # 通用专利审查意见答复
    elif any(kw in context_lower for kw in ["审查意见", "答复", "创造性", "新颖性"]):
        return {
            "prompt": """# 专利审查意见答复专家

## 角色定位
你是一位资深专利代理师，精通中国专利审查实践，擅长处理各类审查意见答复。

## 法律依据
- 《专利法》第22条（三性）
- 《专利审查指南》第二部分第四章（创造性）
- 《专利审查指南》第二部分第三章（新颖性）

## 答复策略
1. 仔细分析审查意见和对比文件
2. 确定区别技术特征
3. 论证非显而易见性
4. 提供支持性证据

## 当前业务
""" + business_context + """

请提供专业的答复策略建议。""",
            "context": {
                "business_context": business_context,
                "user_domain": user_domain,
                "scenario_detected": "general_patent_response",
                "fallback_mode": True
            },
            "matched_rules": [
                {"rule_type": "专利答复通用规则", "domain": "patent", "priority": "high"}
            ],
            "sections": {
                "system": "专利审查意见答复专家",
                "context": business_context,
                "rules": "专利法第22条、审查指南",
                "knowledge": "创造性判断三步法",
                "action": "分析→论证→答复"
            }
        }

    # 通用 fallback
    else:
        return {
            "prompt": f"""# 专利业务助手

你是一位专业的专利代理师，请帮助用户处理以下业务：

{business_context}

请提供专业的建议和指导，必要时引用相关法律法规。""",
            "context": {
                "business_context": business_context,
                "user_domain": user_domain,
                "scenario_detected": "general",
                "fallback_mode": True
            },
            "matched_rules": [],
            "sections": {
                "system": "专利业务助手",
                "context": business_context,
                "rules": "",
                "knowledge": "",
                "action": "提供专利相关建议"
            }
        }


# =============================================================================
# 简化的健康检查
# =============================================================================

def perform_simple_health_check():
    """执行简化的健康检查"""
    health_status = {
        "overall_status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "legal_world_model_api",
        "components": {}
    }

    # 检查Neo4j
    try:
        retriever = components.get_scenario_retriever()
        is_connected = retriever.check_connection()
        health_status["components"]["neo4j"] = {
            "status": "healthy" if is_connected else "unhealthy",
            "message": "Neo4j连接正常" if is_connected else "Neo4j连接失败"
        }
        if not is_connected:
            health_status["overall_status"] = "degraded"
    except Exception as e:
        health_status["components"]["neo4j"] = {
            "status": "unhealthy",
            "message": f"Neo4j检查失败: {str(e)[:100]}"
        }
        health_status["overall_status"] = "degraded"

    # 检查PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            database="postgres",
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "")
        )
        conn.close()
        health_status["components"]["postgres"] = {
            "status": "healthy",
            "message": "PostgreSQL连接正常"
        }
    except Exception as e:
        health_status["components"]["postgres"] = {
            "status": "unhealthy",
            "message": f"PostgreSQL检查失败: {str(e)[:100]}"
        }
        health_status["overall_status"] = "degraded"

    return health_status


# =============================================================================
# 核心API端点
# =============================================================================

@app.get("/", tags=["根路径"])
async def root():
    """根路径 - 服务信息"""
    return {
        "service": "法律世界模型API",
        "version": "1.0.0",
        "description": "Legal World Model API - 提供法律知识检索、场景规则查询、动态提示词生成等服务",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "generate_prompt": "/api/v1/generate-prompt",
            "retrieve_rules": "/api/v1/retrieve-rules",
            "list_scenarios": "/api/v1/scenarios"
        }
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    try:
        health_status = perform_simple_health_check()
        status_code = 200 if health_status["overall_status"] == "healthy" else 503
        return JSONResponse(
            status_code=status_code,
            content=health_status
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )


@app.get("/health/neo4j", tags=["健康检查"])
async def check_neo4j():
    """检查Neo4j连接状态"""
    try:
        retriever = components.get_scenario_retriever()
        is_connected = retriever.check_connection()

        if is_connected:
            return {"status": "healthy", "neo4j": NEO4J_URI}
        else:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "neo4j": NEO4J_URI, "error": "Connection failed"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/api/v1/generate-prompt", tags=["提示词生成"])
async def generate_prompt(request: GeneratePromptRequest):
    """
    生成动态提示词

    根据业务上下文生成包含相关场景规则的动态提示词
    """
    try:
        prompt_generator = components.get_prompt_generator()

        # 调用生成器（使用user_input参数）
        dynamic_prompt = await prompt_generator.generate_dynamic_prompt(
            user_input=request.business_context
        )

        # 组装完整提示词
        full_prompt = f"""{dynamic_prompt.system_prompt}

{dynamic_prompt.context_prompt}

{dynamic_prompt.rules_prompt}

{dynamic_prompt.knowledge_prompt}

{dynamic_prompt.action_prompt}"""

        return {
            "prompt": full_prompt,
            "context": {
                "business_context": request.business_context,
                "user_domain": request.user_domain,
                "confidence_score": dynamic_prompt.confidence_score
            },
            "matched_rules": dynamic_prompt.sources,
            "sections": {
                "system": dynamic_prompt.system_prompt,
                "context": dynamic_prompt.context_prompt,
                "rules": dynamic_prompt.rules_prompt,
                "knowledge": dynamic_prompt.knowledge_prompt,
                "action": dynamic_prompt.action_prompt
            }
        }

    except Exception as e:
        logger.error(f"提示词生成失败: {e}")
        # 返回专业级 fallback 提示词
        return generate_fallback_prompt(request.business_context, request.user_domain)


@app.post("/api/v1/retrieve-rules", tags=["场景规则"])
async def retrieve_rules(request: RetrieveRulesRequest):
    """
    检索场景规则

    从Neo4j中检索指定领域和场景的规则
    """
    try:
        retriever = components.get_scenario_retriever()

        if request.scenario:
            rule = retriever.retrieve_rule(request.domain, request.scenario)
            return {
                "domain": request.domain,
                "scenario": request.scenario,
                "rules": [rule] if rule else []
            }
        else:
            rules = retriever.retrieve_all_rules_for_domain(request.domain)
            return {
                "domain": request.domain,
                "rules": rules,
                "count": len(rules)
            }

    except Exception as e:
        logger.error(f"规则检索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/scenarios", tags=["场景规则"])
async def list_scenarios():
    """
    列出所有可用的场景

    Returns:
        所有领域和场景的列表
    """
    try:
        retriever = components.get_scenario_retriever()
        scenarios = retriever.list_available_scenarios()

        return {
            "scenarios": scenarios,
            "total_domains": len(scenarios)
        }

    except Exception as e:
        logger.error(f"场景列表获取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/layers", tags=["法律世界模型"])
async def list_layers():
    """
    列出法律世界模型的所有层级

    Returns:
        层级列表和说明
    """
    return {
        "layers": [
            {
                "name": "FOUNDATION",
                "description": "基础法律层 - 国家法律法规、部门规章",
                "entity_types": ["STATUTE", "REGULATION", "LAW_ARTICLE"]
            },
            {
                "name": "PATENT_PROFESSIONAL",
                "description": "专利专业层 - 专利相关法律法规、审查指南",
                "entity_types": ["PATENT_LAW", "EXAMINATION_GUIDE", "INVALID_DECISION"]
            },
            {
                "name": "JUDICIAL_PRECEDENT",
                "description": "司法案例层 - 判决书、复审决定、无效决定",
                "entity_types": ["JUDGMENT", "REEXAMINATION_DECISION", "INVALIDATION_DECISION"]
            }
        ]
    }


@app.get("/api/v1/stats", tags=["统计信息"])
async def get_statistics():
    """
    获取法律世界模型统计数据

    Returns:
        各层数据统计
    """
    try:
        retriever = components.get_scenario_retriever()

        stats = {
            "neo4j": {
                "uri": NEO4J_URI,
                "status": "connected" if retriever.check_connection() else "disconnected"
            },
            "layers": {
                "FOUNDATION": {
                    "description": "基础法律层",
                    "entity_count": 295733
                },
                "PATENT_PROFESSIONAL": {
                    "description": "专利专业层",
                    "entity_count": 41124
                },
                "JUDICIAL_PRECEDENT": {
                    "description": "司法案例层",
                    "entity_count": 5906
                }
            },
            "relationships": {
                "entity_relations": 48770,
                "law_article_references": 20306,
                "patent_references": 4243,
                "same_source": 10000
            }
        }

        return stats

    except Exception as e:
        logger.error(f"统计信息获取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# =============================================================================
# 错误处理
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# =============================================================================
# 主函数
# =============================================================================

def main():
    """主函数 - 启动服务"""
    uvicorn.run(
        "api:app",
        host=HOST,
        port=PORT,
        log_level=LOG_LEVEL.lower(),
        access_log=True,
        reload=False
    )


if __name__ == "__main__":
    main()
