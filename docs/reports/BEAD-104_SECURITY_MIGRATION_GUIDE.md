# BEAD-104: 声明式Agent迁移 - 安全指南

> **Security-Reviewer 安全指导文档**
> 创建时间: 2026-04-24
> 任务: 将9个专业代理安全迁移到新架构

---

## 📋 迁移清单

### 需要迁移的9个专业代理

| 序号 | 代理名称 | 当前位置 | 新位置 | 安全级别 |
|------|---------|---------|--------|---------|
| 1 | RetrieverAgent | `core/agents/xiaona/retriever_agent.py` | `core/unified_agents/xiaona/` | 🟢 中 |
| 2 | AnalyzerAgent | `core/agents/xiaona/analyzer_agent.py` | `core/unified_agents/xiaona/` | 🟢 中 |
| 3 | UnifiedPatentWriter | `core/agents/xiaona/unified_patent_writer.py` | `core/unified_agents/xiaona/` | 🟡 高 |
| 4 | NoveltyAnalyzerProxy | `core/agents/xiaona/novelty_analyzer_proxy.py` | `core/unified_agents/xiaona/` | 🟢 中 |
| 5 | CreativityAnalyzerProxy | `core/agents/xiaona/creativity_analyzer_proxy.py` | `core/unified_agents/xiaona/` | 🟢 中 |
| 6 | InfringementAnalyzerProxy | `core/agents/xiaona/infringement_analyzer_proxy.py` | `core/unified_agents/xiaona/` | 🟡 高 |
| 7 | InvalidationAnalyzerProxy | `core/agents/xiaona/invalidation_analyzer_proxy.py` | `core/unified_agents/xiaona/` | 🟡 高 |
| 8 | ApplicationReviewerProxy | `core/agents/xiaona/application_reviewer_proxy.py` | `core/unified_agents/xiaona/` | 🟢 中 |
| 9 | WritingReviewerProxy | `core/agents/xiaona/writing_reviewer_proxy.py` | `core/unified_agents/xiaona/` | 🟢 中 |

---

## 🚨 迁移安全风险

### 风险1: LLM调用未经验证的输入

**当前问题**: 代理直接使用用户输入构建LLM提示词

```python
# ❌ 危险示例
def build_prompt(self, user_input: str) -> str:
    return f"分析以下内容：{user_input}"  # 未验证
```

**修复方案**:

```python
# ✅ 安全示例
async def build_prompt(self, user_input: str) -> str:
    # 1. 输入验证
    await self._security_checker.security_check(user_input)

    # 2. 长度限制
    if len(user_input) > 10000:
        raise ValueError("输入过长")

    # 3. 清理危险内容
    from html import escape
    safe_input = escape(user_input)

    return f"分析以下内容：{safe_input}"
```

### 风险2: 敏感数据泄露到LLM

**当前问题**: 可能将敏感信息发送给外部LLM

```python
# ❌ 危险示例
def analyze_patent(self, patent_data: dict) -> str:
    prompt = f"分析专利：{json.dumps(patent_data)}"  # 可能包含敏感信息
    return self._llm_manager.generate(prompt)
```

**修复方案**:

```python
# ✅ 安全示例
async def analyze_patent(self, patent_data: dict) -> str:
    # 1. 数据脱敏
    safe_data = self._sanitize_patent_data(patent_data)

    # 2. 审计日志
    self._audit_logger.log_operation(
        user_id=self.session.user_id,
        operation="patent_analysis",
        resource_type="patent",
        resource_id=patent_data.get("id", ""),
        success=True
    )

    # 3. 使用脱敏数据
    prompt = f"分析专利：{json.dumps(safe_data)}"
    return await self._llm_manager.generate(prompt)

def _sanitize_patent_data(self, data: dict) -> dict:
    """脱敏专利数据"""
    sensitive_fields = ["applicant_name", "inventor_name", "address"]
    safe_data = data.copy()

    for field in sensitive_fields:
        if field in safe_data:
            # 保留前两个字，其余用*代替
            value = safe_data[field]
            if len(value) > 2:
                safe_data[field] = value[:2] + "*" * (len(value) - 2)

    return safe_data
```

### 风险3: 文件操作路径遍历

**当前问题**: 代理直接使用用户输入访问文件

```python
# ❌ 危险示例
def load_patent_document(self, file_path: str) -> str:
    with open(file_path, 'r') as f:  # 路径遍历风险
        return f.read()
```

**修复方案**:

```python
# ✅ 安全示例
def load_patent_document(self, file_path: str) -> str:
    # 1. 路径验证
    if not self._is_safe_path(file_path):
        raise SecurityError("非法文件路径")

    # 2. 限制在允许的目录
    from pathlib import Path
    allowed_dir = Path("/data/patents")
    full_path = (allowed_dir / file_path).resolve()

    if not str(full_path).startswith(str(allowed_dir)):
        raise SecurityError("路径超出允许范围")

    # 3. 读取文件
    with open(full_path, 'r') as f:
        return f.read()

def _is_safe_path(self, path: str) -> bool:
    """验证路径安全性"""
    import re

    # 检查路径遍历
    if ".." in path or path.startswith("/"):
        return False

    # 只允许安全字符
    if not re.match(r'^[\w\-./]+$', path):
        return False

    return True
```

---

## 📝 安全迁移模板

### 统一的专业代理迁移模板

```python
"""
{代理名称} - 统一架构版本

继承自UnifiedBaseAgent，集成完整的安全特性。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from core.unified_agents.base_agent import UnifiedBaseAgent, UnifiedAgentConfig
from core.context_management.validation.security_checker import SecurityChecker
from core.context_management.access_control.audit_logger import AuditLogger, ActionType

logger = logging.getLogger(__name__)


class {代理类名}(UnifiedBaseAgent):
    """
    {代理描述}

    安全特性:
    - 输入验证（SecurityChecker）
    - 审计日志（AuditLogger）
    - 速率限制（RateLimiter）
    - 数据脱敏（内置）
    """

    # 敏感字段列表（需要脱敏）
    SENSITIVE_FIELDS = ["applicant_name", "inventor_name", "address"]

    # 允许的文件操作目录
    ALLOWED_DIRECTORIES = ["/data/patents", "/data/evidence"]

    def __init__(self, config: Optional[UnifiedAgentConfig] = None):
        """
        初始化代理

        Args:
            config: 统一配置
        """
        if config is None:
            config = UnifiedAgentConfig(
                agent_id="{代理ID}",
                name="{代理名称}",
                role="patent_analyzer"
            )

        super().__init__(config)

        # 初始化安全组件
        self._security_checker = SecurityChecker()
        self._audit_logger = AuditLogger(auto_init=True)

        # 初始化代理特定配置
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """初始化代理特定配置"""
        # 注册能力
        self._register_capabilities([
            {
                "name": "{能力名称}",
                "description": "{能力描述}",
                "input_types": ["{输入类型}"],
                "output_types": ["{输出类型}"],
                "estimated_time": 10.0,
            }
        ])

    async def process(
        self,
        input_text: str,
        **kwargs
    ) -> str:
        """
        处理输入（主入口）

        安全流程:
        1. 输入验证
        2. 速率限制检查
        3. 审计日志记录
        4. 业务处理
        5. 输出过滤
        6. 审计日志记录

        Args:
            input_text: 输入文本
            **kwargs: 额外参数

        Returns:
            处理结果
        """
        session_id = kwargs.get("session_id", "unknown")

        # 1. 输入验证
        validation_context = self._create_validation_context(input_text)
        await self._security_checker.security_check(validation_context)

        if self._security_checker.has_security_issues():
            # 记录安全事件
            self._audit_logger.log(
                action=ActionType.ACCESS_DENIED,
                user_id=kwargs.get("user_id", ""),
                resource_type="agent_input",
                resource_id=self.agent_id,
                details={
                    "security_issues": [
                        issue.description for issue in self._security_checker.security_issues
                    ]
                }
            )
            raise SecurityError("输入包含非法内容")

        # 2. 速率限制检查
        if not self._rate_limiter.allow():
            self._audit_logger.log(
                action=ActionType.ACCESS_DENIED,
                user_id=kwargs.get("user_id", ""),
                resource_type="rate_limit",
                resource_id=self.agent_id,
                details={"reason": "rate_limit_exceeded"}
            )
            raise RateLimitError("请求过于频繁")

        # 3. 记录开始
        self._audit_logger.log_operation(
            user_id=kwargs.get("user_id", ""),
            operation="agent_process_start",
            resource_type="agent",
            resource_id=self.agent_id,
            details={"input_length": len(input_text)}
        )

        try:
            # 4. 业务处理
            result = await self._process_impl(input_text, **kwargs)

            # 5. 输出过滤
            result = self._sanitize_output(result)

            # 6. 记录成功
            self._audit_logger.log_operation(
                user_id=kwargs.get("user_id", ""),
                operation="agent_process_success",
                resource_type="agent",
                resource_id=self.agent_id
            )

            return result

        except Exception as e:
            # 记录失败
            self._audit_logger.log_operation(
                user_id=kwargs.get("user_id", ""),
                operation="agent_process_failed",
                resource_type="agent",
                resource_id=self.agent_id,
                success=False,
                details={"error": str(e)}
            )
            raise

    async def _process_impl(
        self,
        input_text: str,
        **kwargs
    ) -> str:
        """
        实际处理逻辑（子类实现）

        Args:
            input_text: 输入文本（已验证安全）
            **kwargs: 额外参数

        Returns:
            处理结果
        """
        # 子类实现具体逻辑
        raise NotImplementedError

    def _sanitize_output(self, output: str) -> str:
        """
        清理输出

        移除可能包含的敏感信息

        Args:
            output: 原始输出

        Returns:
            清理后的输出
        """
        # 子类可以重写此方法
        return output

    def _sanitize_input_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        脱敏输入数据

        Args:
            data: 原始数据

        Returns:
            脱敏后的数据
        """
        safe_data = data.copy()

        for field in self.SENSITIVE_FIELDS:
            if field in safe_data:
                value = str(safe_data[field])
                if len(value) > 2:
                    safe_data[field] = value[:2] + "*" * (len(value) - 2)

        return safe_data

    def _validate_file_path(self, file_path: str) -> bool:
        """
        验证文件路径安全性

        Args:
            file_path: 文件路径

        Returns:
            是否安全
        """
        import re
        from pathlib import Path

        # 检查路径遍历
        if ".." in file_path or file_path.startswith("/"):
            return False

        # 只允许安全字符
        if not re.match(r'^[\w\-./]+$', file_path):
            return False

        return True

    def _is_allowed_directory(self, file_path: str) -> bool:
        """
        检查路径是否在允许的目录内

        Args:
            file_path: 文件路径

        Returns:
            是否在允许的目录内
        """
        from pathlib import Path

        full_path = Path(file_path).resolve()

        for allowed_dir in self.ALLOWED_DIRECTORIES:
            allowed = Path(allowed_dir).resolve()
            try:
                full_path.relative_to(allowed)
                return True
            except ValueError:
                continue

        return False

    def _create_validation_context(self, input_text: str):
        """
        创建验证上下文

        Args:
            input_text: 输入文本

        Returns:
            验证上下文对象
        """
        from core.context_management.interfaces import IContext
        from datetime import datetime
        from typing import Dict, Any

        class ValidationContext(IContext):
            def __init__(self, text: str):
                self.context_id = "validation"
                self.context_type = "security_check"
                self.created_at = datetime.now()
                self.updated_at = datetime.now()
                self.metadata = {"content": text}

            async def load(self) -> bool:
                return True

            async def save(self) -> bool:
                return True

            async def delete(self) -> bool:
                return True

            def to_dict(self) -> Dict[str, Any]:
                return self.metadata

        return ValidationContext(input_text)


class SecurityError(Exception):
    """安全错误"""
    pass


class RateLimitError(Exception):
    """速率限制错误"""
    pass
```

---

## 🧪 迁移后安全测试

### 测试清单

每个迁移后的代理必须通过以下测试：

```python
# tests/security/test_migrated_agent_security.py

import pytest
import asyncio

from core.unified_agents.xiaona.{代理类名} import {代理类名}


class Test{代理类名}Security:
    """{代理类名}安全测试"""

    @pytest.fixture
    def agent(self):
        """创建代理实例"""
        return {代理类名}()

    @pytest.mark.asyncio
    async def test_sql_injection_blocked(self, agent):
        """测试SQL注入被阻止"""
        malicious_inputs = [
            "'; DROP TABLE patents; --",
            "' OR '1'='1'",
            "admin'--",
        ]

        for input_text in malicious_inputs:
            with pytest.raises(SecurityError):
                await agent.process(input_text)

    @pytest.mark.asyncio
    async def test_xss_blocked(self, agent):
        """测试XSS被阻止"""
        malicious_input = "<script>alert('XSS')</script>"

        # 应该被阻止或清理
        try:
            result = await agent.process(malicious_input)
            assert "<script>" not in result
        except SecurityError:
            pass  # 也可以直接拒绝

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, agent):
        """测试路径遍历被阻止"""
        malicious_paths = [
            "../../../etc/passwd",
            "/etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
        ]

        for path in malicious_paths:
            assert not agent._validate_file_path(path)

    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self, agent):
        """测试速率限制"""
        # 快速发送多个请求
        for _ in range(100):
            try:
                await agent.process("test")
            except RateLimitError:
                break  # 预期的速率限制
        else:
            pytest.fail("速率限制未生效")

    @pytest.mark.asyncio
    async def test_audit_log_created(self, agent):
        """测试审计日志被创建"""
        # 执行操作
        await agent.process("test input")

        # 验证审计日志
        logs = agent._audit_logger.get_user_activity(
            user_id="test_user",
            limit=10
        )

        assert len(logs) > 0

    @pytest.mark.asyncio
    async def test_sensitive_data_sanitized(self, agent):
        """测试敏感数据被脱敏"""
        data = {
            "applicant_name": "张三",
            "invention_title": "测试专利",
            "abstract": "这是一个测试"
        }

        safe_data = agent._sanitize_input_data(data)

        # 姓名应该被脱敏
        assert safe_data["applicant_name"] == "张*"
```

---

## 📊 迁移验证清单

### 每个代理迁移后必须验证

- [ ] **输入验证**: 所有输入经过SecurityChecker验证
- [ ] **输出过滤**: 敏感信息被脱敏
- [ ] **审计日志**: 所有操作被记录
- [ ] **速率限制**: DoS防护生效
- [ ] **路径安全**: 文件操作无路径遍历风险
- [ ] **数据脱敏**: 敏感字段被正确处理
- [ ] **错误处理**: 异常不泄露敏感信息
- [ ] **测试覆盖**: 安全测试用例全部通过

---

## ✅ Security-Reviewer 签名

**审查人**: Security-Reviewer (Sonnet)
**审查时间**: 2026-04-24
**状态**: 准备验证迁移结果

**下一步**: 等待Executor-Architect完成迁移后进行安全验证
