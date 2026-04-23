#!/usr/bin/env python3
"""
Agent认证工具 v2.0
Agent Certification Tool

自动检查Agent是否符合统一接口标准和质量要求。

新增功能（v2.0）:
- 性能认证维度 (20分)
- 安全认证维度 (10分)
- 认证分级系统（Bronze/Silver/Gold/Platinum）
- 自动徽章生成

Usage:
    python tools/agent_certifier.py --agent core.agents.xiaona.retriever_agent.RetrieverAgent
    python tools/agent_certifier.py --all
    python tools/agent_certifier.py --report certification_report.json
    python tools/agent_certifier.py --generate-badges
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import gc
import importlib
import inspect
import json
import re
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Type

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class CertificationStatus(Enum):
    """认证状态"""
    PASSED = "passed"           # 通过
    FAILED = "failed"           # 失败
    WARNING = "warning"         # 警告
    PENDING = "pending"         # 待定


class CertificationLevel(Enum):
    """认证级别"""
    BRONZE = "bronze"       # 青铜认证 (60-74分)
    SILVER = "silver"       # 白银认证 (75-84分)
    GOLD = "gold"           # 黄金认证 (85-94分)
    PLATINUM = "platinum"   # 白金认证 (95-100分)


@dataclass
class CertificationTier:
    """认证层级标准"""
    level: CertificationLevel
    name: str
    min_score: float
    required_checks: List[str]
    description: str
    badge_color: str

    @classmethod
    def get_tier(cls, level: CertificationLevel) -> "CertificationTier":
        """获取认证层级配置"""
        tiers = {
            CertificationLevel.BRONZE: CertificationTier(
                level=CertificationLevel.BRONZE,
                name="青铜认证",
                min_score=60,
                required_checks=["interface_compliance"],
                description="基础接口合规，适合实验性Agent",
                badge_color="#CD7F32",
            ),
            CertificationLevel.SILVER: CertificationTier(
                level=CertificationLevel.SILVER,
                name="白银认证",
                min_score=75,
                required_checks=["interface_compliance", "test_coverage"],
                description="基础+测试覆盖，适合内部使用Agent",
                badge_color="#C0C0C0",
            ),
            CertificationLevel.GOLD: CertificationTier(
                level=CertificationLevel.GOLD,
                name="黄金认证",
                min_score=85,
                required_checks=["interface_compliance", "test_coverage", "code_quality"],
                description="全部检查通过，适合生产环境Agent",
                badge_color="#FFD700",
            ),
            CertificationLevel.PLATINUM: CertificationTier(
                level=CertificationLevel.PLATINUM,
                name="白金认证",
                min_score=95,
                required_checks=[
                    "interface_compliance", "test_coverage", "code_quality",
                    "performance", "security"
                ],
                description="最高标准，核心关键Agent专用",
                badge_color="#E5E4E2",
            ),
        }
        return tiers.get(level, tiers[CertificationLevel.BRONZE])

    @classmethod
    def determine_level(
        cls,
        score: float,
        passed_checks: List[str],
        max_score: float = 130
    ) -> CertificationLevel:
        """根据分数和通过的检查项确定认证级别"""
        percentage = (score / max_score) * 100 if max_score > 0 else 0

        for level in reversed(list(CertificationLevel)):
            tier = cls.get_tier(level)
            if percentage >= tier.min_score:
                required = set(tier.required_checks)
                if required.issubset(set(passed_checks)):
                    return level

        return CertificationLevel.BRONZE


class CertificationResult:
    """认证结果"""

    def __init__(self, agent_name: str, max_score: float = 130):
        self.agent_name = agent_name
        self.status = CertificationStatus.PENDING
        self.level: Optional[CertificationLevel] = None
        self.checks: Dict[str, Dict[str, Any]] = {}
        self.score = 0.0
        self.max_score = max_score
        self.details: Dict[str, Any] = {}
        self.timestamp: Optional[str] = None
        self.passed_checks: List[str] = []

    def add_check(self, name: str, passed: bool, score: float, max_score: float,
                  message: str = "", details: Dict[str, Any] = None):
        """添加检查项"""
        self.checks[name] = {
            "passed": passed,
            "score": score,
            "max_score": max_score,
            "message": message,
            "details": details or {}
        }
        self.score += score
        # max_score已在初始化时设置
        if passed:
            self.passed_checks.append(name)

    def finalize(self):
        """完成认证，计算最终状态"""
        self.timestamp = datetime.now().isoformat()

        # 计算通过率
        passed_checks = sum(1 for c in self.checks.values() if c["passed"])
        total_checks = len(self.checks)

        # 确定认证级别
        self.level = CertificationTier.determine_level(
            self.score,
            self.passed_checks,
            self.max_score
        )

        # 根据分数和通过率确定状态
        percentage = (self.score / self.max_score) * 100 if self.max_score > 0 else 0

        if percentage >= 80 and passed_checks >= total_checks - 1:  # 允许1个非必需项失败
            self.status = CertificationStatus.PASSED
        elif percentage >= 60:
            self.status = CertificationStatus.WARNING
        else:
            self.status = CertificationStatus.FAILED

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        tier = CertificationTier.get_tier(self.level) if self.level else None

        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "level": self.level.value if self.level else None,
            "level_name": tier.name if tier else None,
            "score": self.score,
            "max_score": self.max_score,
            "percentage": round((self.score / self.max_score) * 100, 2) if self.max_score > 0 else 0,
            "checks": self.checks,
            "timestamp": self.timestamp
        }


class AgentCertifier:
    """Agent认证器 v2.0"""

    # 认证标准 (v2.0 - 扩展版)
    STANDARDS = {
        "interface_compliance": {"weight": 25, "required": True},
        "test_coverage": {"weight": 20, "required": True, "threshold": 0.80},
        "code_quality": {"weight": 15, "required": True},
        "documentation": {"weight": 10, "required": False},
        "best_practices": {"weight": 10, "required": False},
        "performance": {"weight": 20, "required": False},  # 新增
        "security": {"weight": 10, "required": False},    # 新增
    }

    def __init__(self, strict: bool = False, skip_performance: bool = False):
        """
        初始化认证器

        Args:
            strict: 严格模式，所有检查项都必须通过
            skip_performance: 跳过性能检查（快速模式）
        """
        self.strict = strict
        self.skip_performance = skip_performance
        self.results: List[CertificationResult] = []

    def certify_agent_class(self, agent_class: Type) -> CertificationResult:
        """
        认证单个Agent类

        Args:
            agent_class: Agent类

        Returns:
            认证结果
        """
        result = CertificationResult(agent_class.__name__, max_score=100 if self.skip_performance else 130)

        try:
            # 1. 接口合规性检查 (25分)
            self._check_interface_compliance(agent_class, result)

            # 2. 测试覆盖率检查 (20分)
            self._check_test_coverage(agent_class, result)

            # 3. 代码质量检查 (15分)
            self._check_code_quality(agent_class, result)

            # 4. 文档完整性检查 (10分)
            self._check_documentation(agent_class, result)

            # 5. 最佳实践检查 (10分)
            self._check_best_practices(agent_class, result)

            # 6. 性能检查 (20分) - 新增
            if not self.skip_performance:
                self._check_performance(agent_class, result)

            # 7. 安全检查 (10分) - 新增
            self._check_security(agent_class, result)

        except Exception as e:
            result.add_check(
                "certification_error",
                False, 0, 130,
                f"认证过程中发生错误: {str(e)}",
                {"error_type": type(e).__name__, "error_details": str(e)}
            )

        result.finalize()
        return result

    def _check_interface_compliance(self, agent_class: Type, result: CertificationResult):
        """检查接口合规性"""
        score = 0
        max_score = 25
        issues = []
        details = {}

        # 必需的方法
        required_methods = {
            "__init__": "构造函数",
            "_initialize": "初始化钩子",
            "get_capabilities": "获取能力列表",
            "get_info": "获取Agent信息",
            "get_system_prompt": "获取系统提示词",
            "execute": "执行方法",
            "validate_input": "输入验证",
        }

        # 检查必需方法
        missing_methods = []
        for method, desc in required_methods.items():
            if not hasattr(agent_class, method):
                missing_methods.append(f"{method} ({desc})")

        if missing_methods:
            issues.append(f"缺少必需方法: {', '.join(missing_methods)}")
        else:
            score += 10
            details["required_methods"] = "present"

        # 检查基类继承
        try:
            from core.agents.xiaona.base_component import BaseXiaonaComponent
            if issubclass(agent_class, BaseXiaonaComponent):
                score += 10
                details["base_class"] = "BaseXiaonaComponent"
            else:
                issues.append("未继承BaseXiaonaComponent基类")
        except ImportError:
            issues.append("无法导入BaseXiaonaComponent")

        # 检查能力注册
        try:
            # 创建临时实例检查
            instance = agent_class(agent_id="_certification_check")
            capabilities = instance.get_capabilities()

            if capabilities:
                score += 5
                details["capabilities"] = [
                    {
                        "name": cap.name,
                        "description": cap.description
                    }
                    for cap in capabilities
                ]
                details["capability_count"] = len(capabilities)
            else:
                issues.append("未注册任何能力")
        except Exception as e:
            issues.append(f"能力检查失败: {str(e)}")

        passed = score >= max_score * 0.8  # 至少80%的分数
        result.add_check(
            "interface_compliance",
            passed, score, max_score,
            f"接口合规性: {score}/{max_score}" + (f" - {', '.join(issues)}" if issues else ""),
            {"issues": issues, "details": details}
        )

    def _agent_name_to_test_filename(self, agent_name: str) -> List[str]:
        """
        将Agent类名转换为可能的测试文件名

        例如: RetrieverAgent -> [retriever_agent, retrieveragent, retriever-agent]
              XiaonuoAgentV2 -> [xiaonuo_agent_v2, xiaonuogentv2]
        """
        import re

        # 1. 在大写字母前插入下划线 (RetrieverAgent -> Retriever_Agent)
        snake_case = re.sub('([A-Z][a-z])', r'_\1', agent_name).lstrip('_')
        # 处理连续大写字母 (XiaonuoAgentV2 -> Xiaonuo_Agent_V2)
        snake_case = re.sub('([a-z])([A-Z])', r'\1_\2', snake_case)

        # 转小写
        snake_case = snake_case.lower()

        # 2. 原始小写名称
        base_name = agent_name.lower()

        # 3. 构建多种可能的命名模式
        patterns = [
            snake_case,                      # retriever_agent
            base_name,                       # retrieveragent
            snake_case.replace('_agent', ''),  # retriever
            snake_case.replace('_agent_v2', '_v2'),  # xiaonuo_v2
            snake_case.replace('_agent_v3', '_v3'),  # yunxi_v3
        ]

        # 去重并返回
        seen = set()
        result = []
        for p in patterns:
            if p not in seen:
                seen.add(p)
                result.append(p)

        return result

    def _check_test_coverage(self, agent_class: Type, result: CertificationResult):
        """检查测试覆盖率"""
        score = 0
        max_score = 20
        details = {}

        # 获取Agent名称
        agent_name = agent_class.__name__

        # 构建可能的测试文件路径（支持多种命名模式）
        possible_names = self._agent_name_to_test_filename(agent_name)

        test_paths = []
        for name in possible_names:
            test_paths.extend([
                PROJECT_ROOT / "tests" / "agents" / f"test_{name}.py",
                PROJECT_ROOT / "tests" / "agents" / f"test_{name}_extended.py",
            ])

        # 去重
        test_paths = list(dict.fromkeys(test_paths))

        test_exists = False
        for test_path in test_paths:
            if test_path.exists():
                test_exists = True
                details["test_file"] = str(test_path)

                # 简单统计测试用例数
                try:
                    content = test_path.read_text(encoding='utf-8')
                    tree = ast.parse(content)

                    test_count = sum(
                        1 for node in ast.walk(tree)
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and node.name.startswith("test_")
                    )

                    details["test_count"] = test_count

                    # 根据测试数量评分
                    if test_count >= 10:
                        score = 20
                    elif test_count >= 5:
                        score = 15
                    elif test_count >= 3:
                        score = 10
                    else:
                        score = 5

                except Exception:
                    score = 5
                break

        if test_exists:
            details["test_exists"] = True
        else:
            details["test_exists"] = False
            details["suggested_test_path"] = f"tests/agents/test_{agent_name.lower()}.py"

        passed = score >= max_score * 0.5
        result.add_check(
            "test_coverage",
            passed, score, max_score,
            f"测试覆盖: {score}/{max_score}",
            details
        )

    def _check_code_quality(self, agent_class: Type, result: CertificationResult):
        """检查代码质量"""
        score = 0
        max_score = 15
        issues = []

        # 验证可以获取源代码
        try:
            inspect.getsource(agent_class)
        except Exception:
            result.add_check(
                "code_quality",
                False, 0, max_score,
                "无法获取源代码",
                {}
            )
            return

        details = {}

        # 检查文档字符串
        has_class_docstring = agent_class.__doc__ is not None
        if has_class_docstring and len(agent_class.__doc__.strip()) > 20:
            score += 5
            details["class_docstring"] = "present"
        else:
            issues.append("缺少或过短的类文档字符串")
            details["class_docstring"] = "missing"

        # 检查方法文档
        methods_with_docstrings = 0
        total_methods = 0

        for name, method in inspect.getmembers(agent_class, predicate=inspect.isfunction):
            if not name.startswith("_") or name in ["__init__", "_initialize"]:
                total_methods += 1
                if method.__doc__ and len(method.__doc__.strip()) > 10:
                    methods_with_docstrings += 1

        if total_methods > 0:
            docstring_ratio = methods_with_docstrings / total_methods
            score += int(docstring_ratio * 5)
            details["methods_with_docs"] = methods_with_docstrings
            details["total_methods"] = total_methods
        else:
            details["methods_with_docs"] = 0
            details["total_methods"] = 0

        # 检查类型注解
        has_type_annotations = self._has_type_annotations(agent_class)
        if has_type_annotations:
            score += 5
            details["type_annotations"] = "present"
        else:
            issues.append("缺少类型注解")
            details["type_annotations"] = "missing"

        passed = score >= max_score * 0.6
        result.add_check(
            "code_quality",
            passed, score, max_score,
            f"代码质量: {score}/{max_score}" + (f" - {', '.join(issues)}" if issues else ""),
            {"issues": issues, **details}
        )

    def _check_documentation(self, agent_class: Type, result: CertificationResult):
        """检查文档完整性"""
        score = 0
        max_score = 10

        agent_name = agent_class.__name__
        details = {}

        # 使用与测试相同的命名转换逻辑
        possible_names = self._agent_name_to_test_filename(agent_name)

        # 检查README中是否有Agent说明
        readme_path = PROJECT_ROOT / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding='utf-8')
            # 检查类名或简化名称
            if any(name in content for name in [agent_name, agent_name.replace("Agent", ""), agent_name.replace("AgentV2", ""), agent_name.replace("AgentV3", "")]):
                score += 3
                details["mentioned_in_readme"] = True

        # 检查是否有专门的Agent文档（使用多种命名模式）
        doc_paths = []
        for name in possible_names:
            doc_paths.extend([
                PROJECT_ROOT / "docs" / "agents" / f"{name}.md",
                PROJECT_ROOT / "docs" / "agents" / f"{name}_guide.md",
                PROJECT_ROOT / "docs" / "guides" / f"{name}.md",
                PROJECT_ROOT / "docs" / "guides" / f"{name}_guide.md",
            ])

        for doc_path in doc_paths:
            if doc_path.exists():
                score += 7
                details["documentation_file"] = str(doc_path)
                break

        passed = score >= max_score * 0.5
        result.add_check(
            "documentation",
            passed, score, max_score,
            f"文档完整性: {score}/{max_score}",
            details
        )

    def _check_best_practices(self, agent_class: Type, result: CertificationResult):
        """检查最佳实践"""
        score = 0
        max_score = 10
        practices = []

        # 检查日志使用
        if "logger" in agent_class.__dict__ or hasattr(agent_class, "logger"):
            practices.append("使用logger")
            score += 2

        # 检查错误处理
        source = inspect.getsource(agent_class)
        if "try:" in source and "except" in source:
            practices.append("有错误处理")
            score += 2

        # 检查配置支持
        if hasattr(agent_class, "config"):
            practices.append("支持配置")
            score += 2

        # 检查状态管理
        if hasattr(agent_class, "status") or hasattr(agent_class, "_status"):
            practices.append("有状态管理")
            score += 2

        # 检查异步支持
        if inspect.iscoroutinefunction(agent_class.execute):
            practices.append("异步执行")
            score += 2

        passed = score >= max_score * 0.5
        result.add_check(
            "best_practices",
            passed, score, max_score,
            f"最佳实践: {score}/{max_score}",
            {"practices": practices}
        )

    def _check_performance(self, agent_class: Type, result: CertificationResult):
        """检查性能指标"""
        score = 0
        max_score = 20
        details = {}

        # 1. 初始化性能 (5分)
        init_times = []
        for i in range(50):
            gc.collect()
            start = time.perf_counter()
            try:
                agent = agent_class(agent_id=f"perf_test_{i}")
                _ = agent  # 使用变量
            except Exception:
                pass
            init_times.append((time.perf_counter() - start) * 1000)

        p95_init = sorted(init_times)[int(len(init_times) * 0.95)]
        details["p95_init_ms"] = round(p95_init, 2)

        if p95_init < 100:
            score += 5
            details["init_performance"] = "excellent"
        elif p95_init < 200:
            score += 3
            details["init_performance"] = "good"
        else:
            score += 1
            details["init_performance"] = "needs_improvement"

        # 2. 内存使用 (5分)
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            baseline = process.memory_info().rss / 1024 / 1024

            agents = []
            for i in range(10):
                agent = agent_class(agent_id=f"mem_test_{i}")
                agents.append(agent)

            peak = process.memory_info().rss / 1024 / 1024
            avg_memory = (peak - baseline) / 10

            details["avg_memory_mb"] = round(avg_memory, 2)

            if avg_memory < 500:
                score += 5
                details["memory_usage"] = "excellent"
            elif avg_memory < 1000:
                score += 3
                details["memory_usage"] = "acceptable"
            else:
                score += 1
                details["memory_usage"] = "high"
        except ImportError:
            score += 2  # psutil未安装，给部分分数
            details["memory_usage"] = "skipped (psutil not available)"

        # 3. 能力发现性能 (5分)
        try:
            agent = agent_class(agent_id="cap_test")
            cap_times = []
            for _ in range(100):
                start = time.perf_counter()
                _ = agent.get_capabilities()
                cap_times.append((time.perf_counter() - start) * 1000)

            p95_cap = sorted(cap_times)[int(len(cap_times) * 0.95)]
            details["p95_capability_ms"] = round(p95_cap, 2)

            if p95_cap < 5:
                score += 5
                details["capability_discovery"] = "excellent"
            elif p95_cap < 10:
                score += 3
                details["capability_discovery"] = "good"
            else:
                score += 1
                details["capability_discovery"] = "slow"
        except Exception as e:
            details["capability_discovery"] = f"error: {str(e)}"

        # 4. 吞吐量 (5分)
        try:
            start = time.perf_counter()
            ops = 0
            test_duration = 1.0  # 1秒测试

            while time.perf_counter() - start < test_duration:
                for _ in range(10):
                    _ = agent.get_capabilities()
                    ops += 1

            elapsed = time.perf_counter() - start
            throughput = ops / elapsed

            details["throughput_ops_per_sec"] = round(throughput, 2)

            if throughput >= 100:
                score += 5
                details["throughput"] = "excellent"
            elif throughput >= 50:
                score += 3
                details["throughput"] = "good"
            else:
                score += 1
                details["throughput"] = "low"
        except Exception as e:
            details["throughput"] = f"error: {str(e)}"

        passed = score >= max_score * 0.6
        result.add_check(
            "performance",
            passed, score, max_score,
            f"性能检查: {score}/{max_score}",
            details
        )

    def _check_security(self, agent_class: Type, result: CertificationResult):
        """检查安全性"""
        score = 0
        max_score = 10
        issues = []
        details = {}

        # 获取源代码
        try:
            source = inspect.getsource(agent_class)
        except Exception:
            result.add_check(
                "security",
                False, 0, max_score,
                "无法获取源代码进行安全检查",
                {}
            )
            return

        # 1. 输入验证 (3分)
        if "validate_input" in source and hasattr(agent_class, "validate_input"):
            # 检查验证逻辑
            validate_method = getattr(agent_class, "validate_input")
            if validate_method.__doc__:
                score += 3
                details["input_validation"] = "documented"
            else:
                score += 2
                details["input_validation"] = "present"
        else:
            issues.append("缺少输入验证")
            details["input_validation"] = "missing"

        # 2. 错误处理 (3分)
        try_count = source.count("try:")
        except_count = source.count("except")
        if try_count > 0 and except_count > 0:
            ratio = except_count / try_count if try_count > 0 else 0
            if ratio >= 0.8:
                score += 3
                details["error_handling"] = "excellent"
            elif ratio >= 0.5:
                score += 2
                details["error_handling"] = "good"
            else:
                score += 1
                details["error_handling"] = "basic"
        else:
            issues.append("缺少错误处理")
            details["error_handling"] = "missing"

        # 3. 敏感信息检查 (2分)
        sensitive_patterns = [
            (r"password\s*=\s*['\"][^'\"]{8,}['\"]", "password"),
            (r"api_key\s*=\s*['\"][^'\"]{16,}['\"]", "api_key"),
            (r"secret\s*=\s*['\"][^'\"]{16,}['\"]", "secret"),
            (r"token\s*=\s*['\"][^'\"]{20,}['\"]", "token"),
            (r"private_key\s*=\s*['\"]", "private_key"),
        ]

        found_secrets = []
        for pattern, secret_type in sensitive_patterns:
            if re.search(pattern, source, re.IGNORECASE):
                found_secrets.append(secret_type)

        if not found_secrets:
            score += 2
            details["hardcoded_secrets"] = "none_found"
        else:
            issues.append(f"可能包含硬编码敏感信息: {', '.join(found_secrets)}")
            details["hardcoded_secrets"] = found_secrets

        # 4. 依赖安全 (2分)
        # 检查是否使用了不安全的函数
        insecure_patterns = [
            (r"eval\s*\(", "eval使用危险"),
            (r"exec\s*\(", "exec使用危险"),
            (r"pickle\.loads?", "pickle可能不安全"),
            (r"subprocess\.call\(.*shell=True", "shell=True可能危险"),
        ]

        found_insecure = []
        for pattern, description in insecure_patterns:
            if re.search(pattern, source):
                found_insecure.append(description)

        if not found_insecure:
            score += 2
            details["insecure_functions"] = "none_found"
        else:
            issues.append(f"使用不安全函数: {', '.join(found_insecure)}")
            details["insecure_functions"] = found_insecure

        passed = score >= max_score * 0.6
        result.add_check(
            "security",
            passed, score, max_score,
            f"安全检查: {score}/{max_score}" + (f" - {', '.join(issues)}" if issues else ""),
            {"issues": issues, **details}
        )

    def _has_type_annotations(self, agent_class: Type) -> bool:
        """检查是否有类型注解"""
        try:
            source = inspect.getsource(agent_class)
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.returns:
                        return True
                    if any(arg.annotation for arg in node.args.args if arg.arg != 'self'):
                        return True
            return False
        except Exception:
            return False

    def certify_all_agents(self) -> Dict[str, CertificationResult]:
        """认证所有Agent"""
        results = {}

        # 扫描core/agents目录
        agents_dir = PROJECT_ROOT / "core" / "agents"

        for py_file in agents_dir.rglob("*agent*.py"):
            if "test" in py_file.name or py_file.name == "__init__.py":
                continue

            # 解析文件，查找Agent类
            try:
                content = py_file.read_text(encoding='utf-8')
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and "Agent" in node.name:
                        # 动态导入
                        rel_path = py_file.relative_to(PROJECT_ROOT)
                        module_path = str(rel_path.with_suffix('')).replace('/', '.')

                        try:
                            module = importlib.import_module(module_path)
                            agent_class = getattr(module, node.name)

                            # 认证
                            cert_result = self.certify_agent_class(agent_class)
                            results[node.name] = cert_result
                            self.results.append(cert_result)

                        except Exception as e:
                            print(f"Warning: Could not certify {node.name}: {e}")

            except Exception as e:
                print(f"Warning: Could not parse {py_file}: {e}")

        return results

    def generate_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """生成认证报告"""
        report = {
            "timestamp": self.results[0].timestamp if self.results else None,
            "version": "2.0",
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.status == CertificationStatus.PASSED),
                "failed": sum(1 for r in self.results if r.status == CertificationStatus.FAILED),
                "warning": sum(1 for r in self.results if r.status == CertificationStatus.WARNING),
                "by_level": {
                    "platinum": sum(1 for r in self.results if r.level == CertificationLevel.PLATINUM),
                    "gold": sum(1 for r in self.results if r.level == CertificationLevel.GOLD),
                    "silver": sum(1 for r in self.results if r.level == CertificationLevel.SILVER),
                    "bronze": sum(1 for r in self.results if r.level == CertificationLevel.BRONZE),
                }
            },
            "agents": [r.to_dict() for r in self.results],
            "standards": self.STANDARDS
        }

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
            print(f"报告已保存到: {output_path}")

        return report

    def generate_badges(self, output_dir: Optional[Path] = None):
        """生成认证徽章"""
        if output_dir is None:
            output_dir = PROJECT_ROOT / "docs" / "badges"

        output_dir.mkdir(parents=True, exist_ok=True)

        for result in self.results:
            if result.level:
                tier = CertificationTier.get_tier(result.level)
                percentage = (result.score / result.max_score) * 100

                svg = self._generate_badge_svg(
                    result.agent_name,
                    tier.name,
                    percentage,
                    tier.badge_color
                )

                badge_file = output_dir / f"{result.agent_name.lower()}_cert.svg"
                badge_file.write_text(svg, encoding='utf-8')
                print(f"徽章已生成: {badge_file}")

        # 生成整体认证徽章
        self._generate_summary_badge(output_dir)

    def _generate_badge_svg(self, agent_name: str, level_name: str, score: float, color: str) -> str:
        """生成单个徽章SVG"""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="24">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="200" height="24" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h110v24H0z"/>
    <path fill="{color}" d="M110 0h90v24H110z"/>
    <path fill="url(#b)" d="M0 0h200v24H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="55" y="17" fill="#010101" fill-opacity=".3">{agent_name}</text>
    <text x="55" y="16">{agent_name}</text>
    <text x="155" y="17" fill="#010101" fill-opacity=".3">{level_name} {score:.0f}分</text>
    <text x="155" y="16">{level_name} {score:.0f}分</text>
  </g>
</svg>'''

    def _generate_summary_badge(self, output_dir: Path):
        """生成整体认证徽章"""
        passed = sum(1 for r in self.results if r.status == CertificationStatus.PASSED)
        total = len(self.results)

        if total == 0:
            return

        percentage = (passed / total) * 100

        if percentage >= 80:
            color = "#04d622"  # green
            text = "passing"
        elif percentage >= 60:
            color = "#df7e12"  # orange
            text = "partial"
        else:
            color = "#d73a49"  # red
            text = "failing"

        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="180" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="180" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h100v20H0z"/>
    <path fill="{color}" d="M100 0h80v20H100z"/>
    <path fill="url(#b)" d="M0 0h180v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="50" y="14" fill="#010101" fill-opacity=".3">certification</text>
    <text x="50" y="13">certification</text>
    <text x="140" y="14" fill="#010101" fill-opacity=".3">{passed}/{total}</text>
    <text x="140" y="13">{passed}/{total}</text>
  </g>
</svg>'''

        badge_file = output_dir / "agent-certification.svg"
        badge_file.write_text(svg, encoding='utf-8')
        print(f"整体徽章已生成: {badge_file}")


def print_result(result: CertificationResult):
    """打印认证结果"""
    status_emoji = {
        CertificationStatus.PASSED: "✅",
        CertificationStatus.FAILED: "❌",
        CertificationStatus.WARNING: "⚠️",
        CertificationStatus.PENDING: "⏳",
    }

    level_emoji = {
        CertificationLevel.PLATINUM: "💎",
        CertificationLevel.GOLD: "🏅",
        CertificationLevel.SILVER: "🥈",
        CertificationLevel.BRONZE: "🥉",
    }

    emoji = status_emoji.get(result.status, "❓")
    level_emoji_val = level_emoji.get(result.level, "") if result.level else ""
    percentage = (result.score / result.max_score) * 100 if result.max_score > 0 else 0

    print(f"\n{emoji} {result.agent_name} {level_emoji_val}")
    print(f"   状态: {result.status.value}")
    if result.level:
        tier = CertificationTier.get_tier(result.level)
        print(f"   级别: {tier.name}")
    print(f"   得分: {result.score:.1f}/{result.max_score:.1f} ({percentage:.1f}%)")

    for check_name, check_data in result.checks.items():
        check_status = "✅" if check_data["passed"] else "❌"
        print(f"   {check_status} {check_name}: {check_data['message']}")


def main():
    parser = argparse.ArgumentParser(
        description="Agent认证工具 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --agent core.agents.xiaona.retriever_agent.RetrieverAgent
  %(prog)s --all
  %(prog)s --all --skip-performance
  %(prog)s --all --report certification_report.json
  %(prog)s --all --generate-badges
        """
    )
    parser.add_argument("--agent", help="要认证的Agent类路径")
    parser.add_argument("--all", action="store_true", help="认证所有Agent")
    parser.add_argument("--report", help="输出报告文件路径")
    parser.add_argument("--generate-badges", action="store_true", help="生成认证徽章")
    parser.add_argument("--strict", action="store_true", help="严格模式")
    parser.add_argument("--skip-performance", action="store_true", help="跳过性能检查（快速模式）")

    args = parser.parse_args()

    certifier = AgentCertifier(strict=args.strict, skip_performance=args.skip_performance)

    if args.all:
        print("🔍 认证所有Agent...\n")
        certifier.certify_all_agents()

        for result in certifier.results:
            print_result(result)

        report = certifier.generate_report(args.report)

        print(f"\n📊 认证汇总:")
        print(f"   总计: {report['summary']['total']}")
        print(f"   通过: {report['summary']['passed']}")
        print(f"   失败: {report['summary']['failed']}")
        print(f"   警告: {report['summary']['warning']}")

        print(f"\n🏆 认证级别分布:")
        print(f"   💎 白金: {report['summary']['by_level']['platinum']}")
        print(f"   🏅 黄金: {report['summary']['by_level']['gold']}")
        print(f"   🥈 白银: {report['summary']['by_level']['silver']}")
        print(f"   🥉 青铜: {report['summary']['by_level']['bronze']}")

        if args.generate_badges:
            certifier.generate_badges()

    elif args.agent:
        print(f"🔍 认证Agent: {args.agent}\n")

        try:
            module_path, class_name = args.agent.rsplit(".", 1)
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)

            result = certifier.certify_agent_class(agent_class)
            print_result(result)

            certifier.results.append(result)
            certifier.generate_report(args.report)

            if args.generate_badges:
                certifier.generate_badges()

        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
