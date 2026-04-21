#!/usr/bin/env python3
"""
测试配置管理

管理端到端测试的配置和参数
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class TestConfig:
    """测试配置类"""

    # 基本配置
    test_mode: str = "e2e"  # e2e, unit, integration
    mock_data: bool = True
    verbose: bool = False

    # 性能阈值
    performance_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "agent_init_ms": 100,      # Agent初始化时间阈值（ms）
        "single_task_ms": 5000,    # 单个任务执行时间阈值（ms）
        "complete_workflow_ms": 15000,  # 完整工作流执行时间阈值（ms）
        "qps_min": 10,              # QPS最小值
        "memory_usage_mb": 500,     # 内存使用阈值（MB）
        "cpu_usage_percent": 80     # CPU使用阈值（%）
    })

    # 重试配置
    retry_config: Dict[str, Any] = field(default_factory=lambda: {
        "max_attempts": 3,
        "delay_seconds": 1,
        "backoff_factor": 2
    })

    # 超时配置
    timeout_config: Dict[str, float] = field(default_factory=lambda: {
        "agent_init": 10,      # Agent初始化超时（秒）
        "single_task": 30,     # 单个任务超时（秒）
        "complete_workflow": 60,  # 完整工作流超时（秒）
        "health_check": 5      # 健康检查超时（秒）
    })

    # 测试数据配置
    test_data: Dict[str, Any] = field(default_factory=lambda: {
        "patent": {
            "id": "CN123456789A",
            "title": "一种结合拟人驾驶行为的自动驾驶掉头路段脱困规划方法",
            "abstract": "本发明涉及自动驾驶技术领域...",
            "inventor": ["张三", "李四"],
            "assignee": "某科技有限公司"
        },
        "workflow": {
            "retriever_timeout": 15,
            "analyzer_timeout": 20,
            "writer_timeout": 25
        }
    })

    # 输出配置
    output_config: Dict[str, Any] = field(default_factory=lambda: {
        "report_format": ["json", "markdown"],
        "output_dir": "test_results/e2e",
        "keep_raw_logs": True,
        "generate_html": False
    })

    # 环境配置
    env_config: Dict[str, str] = field(default_factory=lambda: {
        "POSTGRES_USER": os.getenv("POSTGRES_USER", "athena"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "athena123"),
        "POSTGRES_DB": os.getenv("POSTGRES_DB", "athena_test"),
        "REDIS_PASSWORD": os.getenv("REDIS_PASSWORD", "redis123"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO")
    })

    # CI/CD配置
    cicd_config: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "min_pass_rate": 0.8,  # 80%通过率
        "performance_gate": True,
        "security_scan": False,
        "deploy_on_success": False
    })

    @classmethod
    def from_env(cls) -> "TestConfig":
        """从环境变量加载配置"""
        config = cls()

        # 从环境变量覆盖配置
        if os.getenv("MOCK_DATA", "true").lower() == "false":
            config.mock_data = False

        if os.getenv("VERBOSE", "false").lower() == "true":
            config.verbose = True

        # 性能阈值覆盖
        if os.getenv("QPS_MIN"):
            config.performance_thresholds["qps_min"] = float(os.getenv("QPS_MIN"))

        if os.getenv("MAX_WORKFLOW_TIME"):
            config.performance_thresholds["complete_workflow_ms"] = float(os.getenv("MAX_WORKFLOW_TIME")) * 1000

        # CI/CD配置覆盖
        if os.getenv("MIN_PASS_RATE"):
            config.cicd_config["min_pass_rate"] = float(os.getenv("MIN_PASS_RATE"))

        return config

    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 验证性能阈值
            for key, value in self.performance_thresholds.items():
                if value <= 0:
                    raise ValueError(f"Invalid performance threshold: {key}={value}")

            # 验证超时配置
            for key, value in self.timeout_config.items():
                if value <= 0:
                    raise ValueError(f"Invalid timeout: {key}={value}")

            # 验证CI/CD配置
            if not (0 <= self.cicd_config["min_pass_rate"] <= 1):
                raise ValueError(f"Invalid pass rate: {self.cicd_config['min_pass_rate']}")

            return True

        except ValueError as e:
            print(f"Configuration validation failed: {e}")
            return False

    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """获取特定Agent的配置"""
        base_config = {
            "timeout": self.timeout_config["single_task"],
            "retry": self.retry_config,
            "performance_threshold": self.performance_thresholds
        }

        # 根据Agent类型添加特定配置
        if agent_type == "retriever":
            base_config["timeout"] = self.test_data["workflow"]["retriever_timeout"]
        elif agent_type == "analyzer":
            base_config["timeout"] = self.test_data["workflow"]["analyzer_timeout"]
        elif agent_type == "writer":
            base_config["timeout"] = self.test_data["workflow"]["writer_timeout"]

        return base_config

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "test_mode": self.test_mode,
            "mock_data": self.mock_data,
            "verbose": self.verbose,
            "performance_thresholds": self.performance_thresholds,
            "retry_config": self.retry_config,
            "timeout_config": self.timeout_config,
            "test_data": self.test_data,
            "output_config": self.output_config,
            "env_config": self.env_config,
            "cicd_config": self.cicd_config
        }


# 全局配置实例
test_config = TestConfig.from_env()


def get_test_config() -> TestConfig:
    """获取测试配置"""
    return test_config


def update_config(**kwargs) -> TestConfig:
    """更新配置"""
    global test_config
    for key, value in kwargs.items():
        if hasattr(test_config, key):
            setattr(test_config, key, value)
    return test_config