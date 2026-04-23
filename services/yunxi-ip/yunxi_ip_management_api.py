#!/usr/bin/env python3
"""
云熙IP管理API服务
Yunxi IP Management API

提供专业的知识产权管理服务
"""

import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# 导入身份管理器
from core.utils.agent_identity_manager import identity_manager

app = FastAPI(
    title="云熙IP管理API",
    description="专业知识产权管理服务",
    version="v2.0.0"
)

# 获取云熙身份信息
yunxi_identity = identity_manager.get_agent_identity("yunxi")
if not yunxi_identity:
    # 使用默认身份
    yunxi_identity = {
        "name": "云熙",
        "full_name": "云熙·织女星",
        "role": "YunPat IP管理专家",
        "title": "知识产权管理执行官",
        "slogan": "如织女般精心编织每一份知识产权的保护网，让创新之星在银河中璀璨生辉。",
        "motto": "织梦成网，护创新星",
        "color": "✨"
    }

@app.get("/")
async def root():
    """主页 - 展示身份信息"""
    service_info = identity_manager.get_service_info("yunxi") or {
        "service": f"{yunxi_identity['color']} {yunxi_identity['full_name']} - {yunxi_identity['title']}",
        "name": yunxi_identity["name"],
        "role": yunxi_identity["role"],
        "expert": f"我是{yunxi_identity['name']}，{yunxi_identity['title']}",
        "slogan": yunxi_identity["slogan"],
        "motto": yunxi_identity["motto"],
        "version": "v2.0 Enhanced",
        "port": 8007,
        "message": "云熙已就位，守护您的每一份创新！💫",
        "capabilities": [
            "📋 IP组合管理",
            "🔍 专利监控预警",
            "📊 价值评估分析",
            "💰 维权费用优化",
            "🌐 全球IP布局"
        ],
        "status": "运行中",
        "timestamp": datetime.now().isoformat()
    }
    return service_info

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "yunxi-ip-management",
        "agent": yunxi_identity["name"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v2/ip/portfolio")
async def get_ip_portfolio():
    """获取IP组合概览"""
    return {
        "agent": yunxi_identity["name"],
        "role": yunxi_identity["role"],
        "portfolio_summary": {
            "total_patents": 156,
            "total_trademarks": 42,
            "total_copyrights": 89,
            "pending_applications": 18,
            "active_protections": 267
        },
        "value_breakdown": {
            "estimated_value": "¥5,680,000",
            "high_value_assets": 23,
            "growth_potential": "+35%"
        },
        "protection_status": {
            "fully_protected": 195,
            "partial_protection": 58,
            "monitoring_needed": 14,
            "renewal_due": 12
        },
        "motto": yunxi_identity["motto"]
    }

class PatentRequest(BaseModel):
    title: str
    technology_field: str
    priority: str = "normal"

@app.post("/api/v2/ip/analyze")
async def analyze_ip_potential(request: PatentRequest):
    """分析IP潜力"""
    return {
        "agent": yunxi_identity["name"],
        "analysis": {
            "patent_title": request.title,
            "technology_field": request.technology_field,
            "protection_recommendations": [
                {
                    "type": "发明专利",
                    "probability": "高",
                    "protection_scope": "方法+产品",
                    "estimated_value": "¥80-120万"
                },
                {
                    "type": "实用新型",
                    "probability": "中",
                    "protection_scope": "产品结构",
                    "estimated_value": "¥20-40万"
                }
            ],
            "risk_assessment": {
                "infringement_risk": "低",
                "freedom_to_operate": "良好",
                "monitoring_needed": ["核心算法", "关键组件"]
            }
        },
        "next_steps": [
            "进行专利检索",
            "准备技术交底书",
            "评估PCT申请可能性"
        ],
        "slogan": yunxi_identity["slogan"]
    }

@app.get("/api/v2/ip/alerts")
async def get_ip_alerts():
    """获取IP预警信息"""
    return {
        "agent": yunxi_identity["name"],
        "alerts": [
            {
                "type": "缴费提醒",
                "title": "专利CN202310123456.5年费即将到期",
                "deadline": "2025-01-15",
                "priority": "高",
                "action": "需要缴费维持专利权"
            },
            {
                "type": "侵权监控",
                "title": "发现疑似侵权产品",
                "platform": "某电商平台",
                "detection_time": "2025-12-14 10:30",
                "priority": "中",
                "action": "建议进行侵权比对分析"
            }
        ],
        "total_alerts": 5,
        "urgent_actions": 1,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # 显示启动信息
    print(identity_manager.display_identity("yunxi"))

    # 启动服务
    print("🚀 云熙IP管理API启动中...")
    print("📍 端口: 8007")
    print(f"💫 Slogan: {yunxi_identity['slogan']}")

    uvicorn.run(app, host="127.0.0.1", port=8007)  # 内网通信，通过Gateway访问
