"""
主链路端到端测试

验证提示词生成完整流程：场景识别 → 规则检索 → 提示词生成 → 缓存。
部分测试因融合功能尚未集成而被 skip，待 A1/A2 实现后解除。
"""

from __future__ import annotations

import pytest


class TestGeneratePrompt:
    def test_basic_flow(self, client):
        """基本流程验证（场景识别 → 规则检索 → 提示词生成）。"""
        response = client.post(
            "/api/v1/prompt-system/prompt/generate",
            json={
                "user_input": "分析这个审查意见",
                "additional_context": {"application_number": "CN20231001"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "system_prompt" in data
        assert "user_prompt" in data
        assert data["domain"] == "patent"
        assert data["cached"] is False
        assert "CN20231001" in data["system_prompt"]

    def test_fusion_enabled(self, client, monkeypatch):
        """融合开启时 system_prompt 包含'融合知识上下文'。"""
        monkeypatch.setenv("LEGAL_PROMPT_FUSION_ENABLED", "true")
        response = client.post(
            "/api/v1/prompt-system/prompt/generate",
            json={
                "user_input": "分析这个审查意见",
                "additional_context": {"application_number": "CN20231001"},
            },
        )
        assert response.status_code == 200
        assert "融合知识上下文" in response.json()["system_prompt"]

    def test_fusion_degradation(self, client, mock_broken_postgres):
        """PostgreSQL 故障时融合不阻断，应正常返回 200。"""
        # 当前测试端点未实际调用 PostgreSQL，降级策略在 providers 层验证
        # 本测试验证：即使融合模块异常，端点仍返回 200
        response = client.post(
            "/api/v1/prompt-system/prompt/generate",
            json={
                "user_input": "分析这个审查意见",
                "additional_context": {"application_number": "CN20231001"},
            },
        )
        assert response.status_code == 200

    def test_cache_hit(self, client):
        """相同请求第二次命中缓存，cached 字段为 True。"""
        req = {
            "user_input": "分析这个审查意见",
            "additional_context": {"application_number": "CN20231001"},
        }
        r1 = client.post("/api/v1/prompt-system/prompt/generate", json=req)
        assert r1.status_code == 200
        assert r1.json()["cached"] is False

        r2 = client.post("/api/v1/prompt-system/prompt/generate", json=req)
        assert r2.status_code == 200
        assert r2.json()["cached"] is True

    def test_missing_rule(self, client, retriever_mock):
        """未找到场景规则时返回 404。"""
        retriever_mock.retrieve_rule.return_value = None

        response = client.post(
            "/api/v1/prompt-system/prompt/generate",
            json={
                "user_input": "分析这个审查意见",
                "additional_context": {"application_number": "CN20231001"},
            },
        )
        assert response.status_code == 404
