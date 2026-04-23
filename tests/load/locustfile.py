"""
Prompt System 压测脚本（基础版本）

用法示例:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 -u 10 -r 2 -t 10m

环境变量:
    LOCUST_HOST          -- 目标服务地址（默认 http://localhost:8000）
    LOCUST_USERS         -- 并发用户数（默认 10）
    LOCUST_RUN_TIME      -- 持续时间（默认 10m）
"""

from __future__ import annotations

import os

from locust import HttpUser, between, task


class PromptSystemUser(HttpUser):
    """模拟调用 Prompt System 的压测用户。"""

    wait_time = between(1, 3)

    @task(3)
    def generate_prompt_oa(self):
        """OA 解读请求（高权重，更接近真实业务比例）。"""
        self.client.post(
            "/api/v1/prompt-system/prompt/generate",
            json={
                "user_input": "分析这个审查意见，申请号 CN20231001",
                "additional_context": {"application_number": "CN20231001"},
            },
        )

    @task(1)
    def generate_prompt_inventive(self):
        """创造性分析请求（低权重）。"""
        self.client.post(
            "/api/v1/prompt-system/prompt/generate",
            json={
                "user_input": "评估这个方案的创造性",
            },
        )
