#!/usr/bin/env python3
"""
端到端测试配置

提供测试所需的fixture和配置
"""

import asyncio
from pathlib import Path
from typing import Any

import pytest

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
import sys

sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config() -> dict[str, Any]:
    """测试配置"""
    return {
        "test_mode": True,
        "mock_data": True,
        "max_execution_time": 30,  # 最大执行时间（秒）
        "retry_attempts": 3,
        "timeout": 10,
        "log_level": "INFO"
    }


@pytest.fixture
def test_patent_data() -> dict[str, Any]:
    """测试专利数据"""
    return {
        "target_patent": {
            "id": "CN123456789A",
            "title": "一种结合拟人驾驶行为的自动驾驶掉头路段脱困规划方法",
            "abstract": "本发明涉及自动驾驶技术领域，具体提供了一种结合拟人驾驶行为的车...",
            "inventor": ["张三", "李四", "王五"],
            "assignee": "某科技有限公司",
            "filing_date": "2023-01-15",
            "publication_date": "2023-07-20",
            "ipc_classes": ["G08G 1/00", "G08G 6/00"],
            "claims_count": 10,
            "description_pages": 8
        },
        "comparison_patents": [
            {
                "id": "CN987654321B",
                "title": "自动驾驶系统的路径规划方法",
                "abstract": "本发明公开了一种自动驾驶系统的路径规划方法...",
                "filing_date": "2022-03-10"
            },
            {
                "id": "CN112233445C",
                "title": "基于AI的车辆决策系统",
                "abstract": "本发明提供了一种基于人工智能的车辆决策系统...",
                "filing_date": "2024-02-20"
            }
        ],
        "technical_fields": [
            "自动驾驶",
            "路径规划",
            "人工智能",
            "车辆控制"
        ]
    }


@pytest.fixture
def test_workflow_scenarios() -> dict[str, Any]:
    """测试场景"""
    return {
        "patent_analysis": {
            "name": "专利分析场景",
            "input": "我需要申请一项专利，技术方案是：结合拟人驾驶行为的自动驾驶掉头路段脱困规划方法。请帮我进行专利检索、技术分析和专利撰写。",
            "expected_steps": ["检索", "分析", "撰写"],
            "expected_agents": ["retriever", "analyzer", "writer"]
        },
        "invalidity_analysis": {
            "name": "无效宣告场景",
            "input": "我需要分析专利CN123456789A的无效性，请检索相关对比文件并分析其新颖性和创造性。",
            "expected_steps": ["检索", "分析"],
            "expected_agents": ["retriever", "analyzer"]
        },
        "infringement_analysis": {
            "name": "侵权分析场景",
            "input": "我想分析某公司的自动驾驶产品是否侵犯了我的专利CN123456789A，请帮我进行侵权分析。",
            "expected_steps": ["检索", "分析"],
            "expected_agents": ["retriever", "analyzer"]
        },
        "oa_response": {
            "name": "答复审查意见场景",
            "input": "我收到了针对专利CN123456789A的审查意见通知书，需要准备答复意见。",
            "expected_steps": ["检索", "分析", "撰写"],
            "expected_agents": ["retriever", "analyzer", "writer"]
        }
    }


@pytest.fixture
def performance_metrics() -> dict[str, Any]:
    """性能指标"""
    return {
        "thresholds": {
            "agent_init": 100,      # Agent初始化时间阈值（ms）
            "single_task": 5000,    # 单个任务执行时间阈值（ms）
            "complete_workflow": 15000,  # 完整工作流执行时间阈值（ms）
            "qps": 10,              # QPS阈值（查询/秒）
            "memory_usage": 500,    # 内存使用阈值（MB）
            "cpu_usage": 80         # CPU使用阈值（%）
        },
        "alerts": {
            "warning": {
                "agent_init": 200,
                "single_task": 8000,
                "complete_workflow": 20000,
                "qps": 5
            },
            "critical": {
                "agent_init": 500,
                "single_task": 15000,
                "complete_workflow": 30000,
                "qps": 1
            }
        }
    }
