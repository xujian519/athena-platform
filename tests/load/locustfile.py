"""
Prompt System 压测脚本（性能基线版本）

用法示例:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 -u 10 -r 2 -t 10m

环境变量:
    LOCUST_HOST          -- 目标服务地址（默认 http://localhost:8000）
    LOCUST_USERS         -- 并发用户数（默认 10）
    LOCUST_RUN_TIME      -- 持续时间（默认 10m）

任务权重:
    - office_action:         50%  OA 解读请求
    - creativity_analysis:   30%  创造性分析请求
    - novelty_analysis:      20%  新颖性分析请求
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path

from locust import HttpUser, between, task


def _load_payloads(filename: str) -> list[dict]:
    """从 payloads 目录加载压测数据集。"""
    base_dir = Path(__file__).parent / "payloads"
    filepath = base_dir / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Payload file not found: {filepath}")
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


class PromptSystemUser(HttpUser):
    """模拟调用 Prompt System 主链路 API 的压测用户。"""

    wait_time = between(1, 3)

    # 预加载压测数据集
    _oa_payloads = _load_payloads("oa_analysis.json")
    _inventive_payloads = _load_payloads("inventive_analysis.json")
    _novelty_payloads = _load_payloads("novelty_analysis.json")

    def on_start(self):
        """预热：每个用户启动时发送 1 条 OA 解读请求填充缓存。"""
        payload = random.choice(self._oa_payloads)
        with self.client.post(
            "/api/v1/prompt-system/prompt/generate",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                # 预热失败标记为 warning，不计入压测核心指标
                response.warning(f"Warmup failed: {response.status_code}")

    @task(50)
    def office_action(self):
        """OA 解读请求（高权重，核心业务流程）。"""
        payload = random.choice(self._oa_payloads)
        self.client.post(
            "/api/v1/prompt-system/prompt/generate",
            json=payload,
            name="POST /api/v1/prompt-system/prompt/generate [office_action]",
        )

    @task(30)
    def creativity_analysis(self):
        """创造性分析请求（中等权重）。"""
        payload = random.choice(self._inventive_payloads)
        self.client.post(
            "/api/v1/prompt-system/prompt/generate",
            json=payload,
            name="POST /api/v1/prompt-system/prompt/generate [creativity_analysis]",
        )

    @task(20)
    def novelty_analysis(self):
        """新颖性分析请求（低权重）。"""
        payload = random.choice(self._novelty_payloads)
        self.client.post(
            "/api/v1/prompt-system/prompt/generate",
            json=payload,
            name="POST /api/v1/prompt-system/prompt/generate [novelty_analysis]",
        )
