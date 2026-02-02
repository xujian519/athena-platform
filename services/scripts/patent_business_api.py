#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利业务智能服务API
提供专利撰写、分析、检索、评估等全套专利业务的智能服务

作者：小娜
日期：2025-12-07
"""

import json
from core.async_main import async_main
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from patent_business_knowledge_base import PatentBusinessKnowledgeBase
from pydantic import BaseModel

# 创建FastAPI应用
app = FastAPI(
    title='专利业务智能服务API',
    description='提供专利撰写、分析、检索、评估等全套专利业务的智能服务',
    version='1.0.0'
)

# 初始化知识库
kb = PatentBusinessKnowledgeBase()

# 请求模型
class WritingRequest(BaseModel):
    patent_type: str  # 发明、实用新型、外观设计
    tech_field: str
    background: str
    problem: str
    solution: str
    benefits: str

class AnalysisRequest(BaseModel):
    patent_number: str
    patent_type: str  # 新颖性、创造性、侵权分析
    patent_data: Dict[str, Any]

class SearchRequest(BaseModel):
    search_type: str  # 查新、无效、侵权
    tech_keywords: List[str]
    ipc_codes: List[str]
    date_range: str | None = None

class EvaluationRequest(BaseModel):
    patent_number: str
    evaluation_type: str  # 技术价值、经济价值
    patent_data: Dict[str, Any]

class StrategyRequest(BaseModel):
    business_goal: str  # 防御型、进攻型、货币化
    company_info: Dict[str, Any]
    tech_domain: str


@app.get('/')
async def root():
    """API根路径"""
    return {
        'message': '专利业务智能服务API',
        'version': '1.0.0',
        'endpoints': [
            '/patent/writing - 专利撰写服务',
            '/patent/analysis - 专利分析服务',
            '/patent/search - 专利检索服务',
            '/patent/evaluation - 专利评估服务',
            '/patent/strategy - 专利策略服务'
        ]
    }


@app.post('/patent/writing')
async def patent_writing(request: WritingRequest):
    """专利撰写服务"""
    try:
        # 获取撰写助手
        tech_info = {
            'tech_field': request.tech_field,
            'background': request.background,
            'problem': request.problem,
            'solution': request.solution,
            'benefits': request.benefits
        }

        assistant = kb.get_writing_assistant(request.patent_type, tech_info)

        # 生成技术方案描述
        tech_solution_prompt = assistant['提示词']['技术方案描述'].format(**tech_info)

        # 生成权利要求书
        claims_prompt = assistant['提示词']['权利要求书']

        # 生成实施例
        example_prompt = assistant['提示词']['实施例']

        # 返回撰写指导
        return {
            'status': 'success',
            'patent_type': request.patent_type,
            'template': assistant['template'],
            'rules': assistant['rules'],
            'suggestions': assistant['建议'],
            'prompts': {
                '技术方案': tech_solution_prompt,
                '权利要求书': claims_prompt,
                '实施例': example_prompt
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/patent/analysis')
async def patent_analysis(request: AnalysisRequest):
    """专利分析服务"""
    try:
        # 获取分析助手
        assistant = kb.get_analysis_assistant(request.patent_type)

        # 生成分析提示词
        analysis_prompt = assistant['提示词'].get(request.patent_type, '')

        if analysis_prompt:
            # 格式化提示词
            formatted_prompt = analysis_prompt.format(**request.patent_data)
        else:
            formatted_prompt = f"请对专利 {request.patent_number} 进行 {request.patent_type} 分析"

        return {
            'status': 'success',
            'patent_number': request.patent_number,
            'analysis_type': request.patent_type,
            'rules': assistant['rules'],
            'prompt': formatted_prompt,
            'case_references': assistant['案例参考']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/patent/search')
async def patent_search(request: SearchRequest):
    """专利检索服务"""
    try:
        # 获取检索助手
        assistant = kb.get_search_assistant(request.search_type)

        # 构建检索方案
        search_plan = {
            'keywords': request.tech_keywords,
            'ipc_codes': request.ipc_codes,
            'strategies': assistant['检索策略'],
            'notes': assistant['注意事项'],
            'prompt': assistant['提示词'].format(
                tech_points=', '.join(request.tech_keywords),
                keywords=', '.join(request.tech_keywords),
                ipc=', '.join(request.ipc_codes)
            )
        }

        return {
            'status': 'success',
            'search_type': request.search_type,
            'search_plan': search_plan
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/patent/evaluation')
async def patent_evaluation(request: EvaluationRequest):
    """专利评估服务"""
    try:
        # 获取评估助手
        assistant = kb.get_evaluation_assistant(request.evaluation_type)

        # 生成评估提示词
        eval_prompt = assistant['提示词'].get(request.evaluation_type, '')
        if eval_prompt:
            formatted_prompt = eval_prompt.format(**request.patent_data)
        else:
            formatted_prompt = f"请对专利 {request.patent_number} 进行 {request.evaluation_type} 评估"

        return {
            'status': 'success',
            'patent_number': request.patent_number,
            'evaluation_type': request.evaluation_type,
            'prompt': formatted_prompt,
            'standards': assistant['评估标准'],
            'metrics': assistant['参考指标']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/patent/strategy')
async def patent_strategy(request: StrategyRequest):
    """专利策略服务"""
    try:
        # 获取策略建议
        strategy_map = {
            '防御型': {
                'goal': '构建专利护城河，防止竞争对手进入',
                'key_actions': [
                    '围绕核心产品申请基础专利',
                    '在改进技术上形成外围专利',
                    '建立防御性公开机制'
                ],
                "prompt": f"""
作为专利防御策略顾问，为以下企业制定专利防御方案：

公司信息：{request.company_info}
技术领域：{request.tech_domain}

请制定包括专利布局、风险防控、侵权规避在内的完整防御策略。
                """
            },
            '进攻型': {
                'goal': '通过专利布局抢占技术制高点',
                'key_actions': [
                    '在关键技术节点提前布局',
                    '申请标准必要专利',
                    '构建专利诉讼威慑'
                ],
                "prompt": f"""
作为专利进攻策略顾问，为以下企业制定进攻型专利策略：

公司信息：{request.company_info}
技术领域：{request.tech_domain}

请制定包括基础专利布局、标准参与、竞争壁垒在内的进攻策略。
                """
            },
            '货币化': {
                'goal': '通过专利实现商业价值最大化',
                'key_actions': [
                    '筛选高价值专利',
                    '制定许可策略',
                    '探索专利运营模式'
                ],
                "prompt": f"""
作为专利货币化专家，为以下企业制定专利变现策略：

公司信息：{request.company_info}
技术领域：{request.tech_domain}

请制定包括专利许可、转让、运营、金融化在内的货币化方案。
                """
            }
        }

        strategy = strategy_map.get(request.business_goal, {})

        return {
            'status': 'success',
            'business_goal': request.business_goal,
            'strategy': strategy
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/patent/knowledge/rules')
async def get_patent_rules():
    """获取专利规则"""
    return {
        'status': 'success',
        'rules': kb.rules
    }


@app.get('/patent/knowledge/templates')
async def get_patent_templates():
    """获取专利模板"""
    return {
        'status': 'success',
        'templates': kb.templates
    }


@app.get('/patent/knowledge/cases')
async def get_case_law():
    """获取案例法"""
    return {
        'status': 'success',
        'case_law': kb.case_law
    }


@app.get('/health')
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'knowledge_base': 'loaded'
    }


@app.post('/patent/knowledge/export')
async def export_knowledge_base():
    """导出知识库"""
    try:
        output_path = f"/tmp/patent_knowledge_base_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        exported_file = kb.export_knowledge_base(output_path)

        return {
            'status': 'success',
            'exported_file': exported_file,
            'message': '知识库导出成功'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 启动服务
if __name__ == '__main__':
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8090,
        log_level='info'
    )