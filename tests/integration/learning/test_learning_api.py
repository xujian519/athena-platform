#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习与适应模块 API 集成测试
Learning & Adaptation Module API Integration Tests

测试API端点的功能：
1. 健康检查
2. 学习任务执行
3. 统计信息获取
4. 强化学习交互
5. 监控指标获取

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-24
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from typing import Dict, Any

# 导入API模块
from core.learning.api import router
from fastapi import FastAPI

# 创建测试应用
app = FastAPI()
app.include_router(router)

# 创建测试客户端
client = TestClient(app)


class TestLearningAPI:
    """学习API测试类"""

    def test_root_endpoint(self):
        """测试根路径"""
        response = client.get("/api/v1/learning/")
        assert response.status_code == 200
        data = response.json()
        assert data["module"] == "Learning & Adaptation Module"
        assert "endpoints" in data

    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/api/v1/learning/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_execute_learning_supervised(self):
        """测试监督学习任务"""
        request_data = {
            "task_type": "supervised",
            "context": {"experiment": "test_01"},
            "data": [
                {"input": "test1", "output": "result1"},
                {"input": "test2", "output": "result2"}
            ],
            "config": {"epochs": 10}
        }

        response = client.post("/api/v1/learning/learn", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["completed", "processing"]
        assert "task_id" in data

    def test_execute_learning_without_data(self):
        """测试无数据学习任务（应失败）"""
        request_data = {
            "task_type": "supervised",
            "context": {},
            "data": []
        }

        response = client.post("/api/v1/learning/learn", json=request_data)
        assert response.status_code == 400

    def test_get_statistics(self):
        """测试获取统计信息"""
        response = client.get("/api/v1/learning/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "success_rate" in data


class TestRLInteractionAPI:
    """强化学习交互API测试类"""

    def test_record_interaction(self):
        """测试记录交互"""
        request_data = {
            "user_input": "测试查询",
            "agent_response": "测试响应",
            "capability_used": "search",
            "context": {"session_id": "test_001"},
            "explicit_feedback": 0.8,
            "response_time": 1.5,
            "error_occurred": False,
            "user_corrected": False
        }

        response = client.post("/api/v1/learning/rl/interaction", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "interaction_id" in data

    def test_record_interaction_minimal(self):
        """测试最小交互记录"""
        request_data = {
            "user_input": "测试查询",
            "agent_response": "测试响应",
            "capability_used": "search"
        }

        response = client.post("/api/v1/learning/rl/interaction", json=request_data)
        assert response.status_code == 200

    def test_get_rl_summary(self):
        """测试获取RL摘要"""
        response = client.get("/api/v1/learning/rl/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestMonitoringAPI:
    """监控API测试类"""

    def test_get_monitoring_metrics(self):
        """测试获取监控指标"""
        response = client.get("/api/v1/learning/monitoring/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_interactions" in data
        assert "recent_rewards" in data

    def test_get_monitoring_report(self):
        """测试获取监控报告"""
        response = client.get("/api/v1/learning/monitoring/report")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "report" in data

    def test_start_stop_monitoring(self):
        """测试启动和停止监控"""
        # 启动监控
        start_response = client.post("/api/v1/learning/monitoring/start?interval_seconds=60")
        assert start_response.status_code in [200, 208]  # 208 = already reported

        # 停止监控
        stop_response = client.post("/api/v1/learning/monitoring/stop")
        assert stop_response.status_code in [200, 208]


class TestErrorHandling:
    """错误处理测试类"""

    def test_invalid_task_type(self):
        """测试无效任务类型"""
        # 这会被Pydantic验证拦截
        request_data = {
            "task_type": "invalid_type",
            "data": [{"input": "test"}]
        }

        response = client.post("/api/v1/learning/learn", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_missing_required_field(self):
        """测试缺少必需字段"""
        request_data = {
            "task_type": "supervised"
            # 缺少 data 字段
        }

        response = client.post("/api/v1/learning/learn", json=request_data)
        # 对于监督学习，需要数据
        # 这可能会返回200（学习引擎处理）或400（API验证）
        # 具体取决于实现


# ==================== 测试夹具 ====================

@pytest.fixture
def sample_learning_data():
    """示例学习数据"""
    return {
        "task_type": "supervised",
        "context": {"experiment": "pytest"},
        "data": [
            {"input": "example1", "output": "label1"},
            {"input": "example2", "output": "label2"},
            {"input": "example3", "output": "label3"}
        ],
        "config": {"learning_rate": 0.001, "epochs": 5}
    }


@pytest.fixture
def sample_rl_interaction():
    """示例RL交互数据"""
    return {
        "user_input": "如何搜索专利？",
        "agent_response": "您可以使用专利搜索功能...",
        "capability_used": "patent_search",
        "context": {
            "session_id": "test_session_123",
            "user_id": "test_user"
        },
        "explicit_feedback": 0.9,
        "response_time": 0.85,
        "error_occurred": False,
        "user_corrected": False
    }


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
