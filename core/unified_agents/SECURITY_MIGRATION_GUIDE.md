# 兼容层安全指南

> **Security-Reviewer建议文档**
> 创建时间: 2026-04-24
> 目标: 确保兼容层不会引入新的安全风险

---

## 🚨 兼容层安全原则

### 原则1: 最小权限

兼容层应该只提供**必要的重定向**，不应该：
- ❌ 修改参数
- ❌ 捕获并隐藏异常
- ❌ 添加额外逻辑
- ❌ 绕过安全检查

### 原则2: 透明性

所有兼容层调用必须：
- ✅ 记录到审计日志
- ✅ 使用相同的输入验证
- ✅ 使用相同的权限检查

---

## 📝 安全的兼容层实现

### ✅ 推荐实现

```python
# core/agents/base_agent.py
"""
向后兼容层 - 安全实现

此文件提供向后兼容性，重定向到新的统一架构。
所有安全检查由UnifiedBaseAgent执行。
"""

from __future__ import annotations

import logging
import warnings

from core.unified_agents.base_agent import (
    UnifiedBaseAgent,
    UnifiedAgentConfig,
    GatewayClientConfig,
    AgentType
)

logger = logging.getLogger(__name__)

# 安全的兼容：直接重定向，不添加额外逻辑
BaseAgent = UnifiedBaseAgent

# 导出其他类型
__all__ = [
    "BaseAgent",
    "UnifiedBaseAgent",  # 也导出新名称
]

# 保留旧类名的别名（用于类型检查）
class LegacyBaseAgent(UnifiedBaseAgent):
    """
    旧BaseAgent的别名类

    警告: 此类仅为向后兼容保留。
    新代码应使用UnifiedBaseAgent。
    """

    def __init__(self, *args, **kwargs):
        # 记录使用旧API的情况
        logger.warning(
            f"使用LegacyBaseAgent已弃用。"
            f"请迁移到UnifiedBaseAgent。"
            f"调用位置: {self._get_caller_info()}"
        )

        # 调用父类（无额外逻辑）
        super().__init__(*args, **kwargs)

        # 记录到审计日志（如果可用）
        self._log_deprecation_warning()

    def _get_caller_info(self) -> str:
        """获取调用者信息（用于日志）"""
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            return f"{frame.f_back.f_code.co_filename}:{frame.f_back.f_lineno}"
        return "unknown"

    def _log_deprecation_warning(self):
        """记录弃用警告到审计日志"""
        try:
            from core.context_management.access_control.audit_logger import AuditLogger

            audit = AuditLogger(auto_init=False)
            audit.log_operation(
                user_id="system",
                operation="deprecated_api_usage",
                resource_type="BaseAgent",
                details={"agent_name": self.name, "warning": "LegacyBaseAgent is deprecated"}
            )
        except Exception:
            # 审计日志失败不应影响功能
            pass
```

### ❌ 不安全的实现（不要使用）

```python
# 危险：修改参数
class BaseAgent(UnifiedBaseAgent):
    def process(self, input_text: str, **kwargs):
        # ❌ 不安全：绕过输入验证
        return super().process(input_text, **kwargs)

# 危险：隐藏异常
class BaseAgent(UnifiedBaseAgent):
    def process(self, input_text: str, **kwargs):
        try:
            return super().process(input_text, **kwargs)
        except Exception:
            # ❌ 不安全：隐藏所有异常
            return "错误"

# 危险：添加额外逻辑
class BaseAgent(UnifiedBaseAgent):
    def __init__(self, *args, **kwargs):
        # ❌ 不安全：修改配置
        kwargs.pop("enable_security", None)  # 移除安全选项
        super().__init__(*args, **kwargs)
```

---

## 🔒 兼容层安全检查清单

### 创建兼容层时必须验证

- [ ] **无参数修改**: 兼容层不修改任何参数
- [ ] **无异常隐藏**: 所有异常正常传播
- [ ] **完整审计日志**: 兼容层调用被记录
- [ ] **相同安全检查**: 使用相同的安全验证
- [ ] **性能影响<5%**: 兼容层不应显著影响性能

### 部署前必须验证

- [ ] **安全测试通过**: 所有安全测试用例通过
- [ ] **渗透测试通过**: 通过外部渗透测试
- [ ] **依赖扫描通过**: 无新的漏洞依赖

---

## 🧪 兼容层安全测试

```python
# tests/security/test_compatibility_layer_security.py

import unittest
from unittest.mock import patch, MagicMock

from core.agents.base_agent import BaseAgent, LegacyBaseAgent


class TestCompatibilityLayerSecurity(unittest.TestCase):
    """兼容层安全测试"""

    def test_compatibility_does_not_modify_input(self):
        """测试兼容层不修改输入"""
        agent = BaseAgent(name="test", role="test")

        # 模拟恶意输入
        malicious_input = "<script>alert('XSS')</script>"

        # 兼容层应该转发到UnifiedBaseAgent
        # UnifiedBaseAgent会进行安全检查
        with patch.object(agent, '_process_impl') as mock_process:
            mock_process.return_value = "safe"

            result = agent.process(malicious_input)

            # 验证输入未被修改
            mock_process.assert_called_once()
            call_args = mock_process.call_args[0]
            self.assertEqual(call_args[0], malicious_input)

    def test_compatibility_propagates_exceptions(self):
        """测试兼容层传播异常"""
        agent = BaseAgent(name="test", role="test")

        # 模拟异常
        with patch.object(agent, '_process_impl', side_effect=ValueError("test error")):
            with self.assertRaises(ValueError):
                agent.process("input")

    def test_legacy_agent_logs_deprecation(self):
        """测试LegacyBaseAgent记录弃用警告"""
        with self.assertLogs('core.agents.base_agent', level='WARNING') as log:
            agent = LegacyBaseAgent(name="test", role="test")

            # 应该有弃用警告
            self.assertTrue(
                any("LegacyBaseAgent已弃用" in message for message in log.output)
            )

    def test_compatibility_uses_same_security_checker(self):
        """测试兼容层使用相同的安全检查器"""
        agent = BaseAgent(name="test", role="test")

        # 验证安全检查器存在
        self.assertIsNotNone(agent._security_checker)

        # 验证是正确类型
        from core.context_management.validation.security_checker import SecurityChecker
        self.assertIsInstance(agent._security_checker, SecurityChecker)


class TestCompatibilityLayerIntegrity(unittest.TestCase):
    """兼容层完整性测试"""

    def test_base_agent_is_unified_base_agent(self):
        """测试BaseAgent确实是UnifiedBaseAgent"""
        from core.unified_agents.base_agent import UnifiedBaseAgent
        from core.agents.base_agent import BaseAgent

        # 应该是同一个类
        self.assertIs(BaseAgent, UnifiedBaseAgent)

    def test_all_methods_available(self):
        """测试所有方法都可用"""
        from core.agents.base_agent import BaseAgent

        # 检查关键方法存在
        self.assertTrue(hasattr(BaseAgent, 'process'))
        self.assertTrue(hasattr(BaseAgent, 'process_task'))
        self.assertTrue(hasattr(BaseAgent, 'connect_gateway'))
        self.assertTrue(hasattr(BaseAgent, 'save_memory'))

    def test_type_annotations_preserved(self):
        """测试类型注解被保留"""
        from core.agents.base_agent import BaseAgent
        import inspect

        # 检查process方法的签名
        sig = inspect.signature(BaseAgent.process)
        self.assertIn('input_text', sig.parameters)
        self.assertIn('return', sig.annotations)
```

---

## 📊 兼容层性能影响评估

### 目标

兼容层性能开销应 **< 5%**

### 测试方法

```python
import timeit

def test_compatibility_overhead():
    """测试兼容层性能开销"""

    # 新架构
    new_setup = """
from core.unified_agents.base_agent import UnifiedBaseAgent
agent = UnifiedBaseAgent(name="test", role="test")
"""

    new_time = timeit.timeit(
        'agent.process("test input")',
        setup=new_setup,
        number=1000
    )

    # 兼容层
    compat_setup = """
from core.agents.base_agent import BaseAgent
agent = BaseAgent(name="test", role="test")
"""

    compat_time = timeit.timeit(
        'agent.process("test input")',
        setup=compat_setup,
        number=1000
    )

    # 计算开销
    overhead = (compat_time - new_time) / new_time * 100

    print(f"新架构: {new_time:.4f}秒")
    print(f"兼容层: {compat_time:.4f}秒")
    print(f"开销: {overhead:.2f}%")

    # 验证开销 < 5%
    assert overhead < 5, f"兼容层开销过大: {overhead:.2f}%"
```

---

## 🔍 安全审查要点

### Test-Coordinator 需要验证

1. **输入验证一致性**
   - 旧API和新API使用相同的输入验证
   - 所有恶意输入都被拒绝

2. **审计日志完整性**
   - 通过兼容层的调用也被记录
   - 日志中能识别使用的是兼容层

3. **异常处理正确性**
   - 所有异常正确传播
   - 没有敏感信息泄露

### Performance-Executor 需要验证

1. **性能开销 < 5%**
2. **内存开销 < 10%**
3. **无内存泄漏**

---

## 📝 迁移安全建议

### 对于使用旧API的代码

```python
# 旧代码
from core.agents.base_agent import BaseAgent

agent = BaseAgent(name="test", role="test")
result = agent.process("input")

# 新代码（推荐）
from core.unified_agents.base_agent import UnifiedBaseAgent

agent = UnifiedBaseAgent(
    name="test",
    role="test",
    enable_security=True  # 显式启用安全
)
result = await agent.process("input")  # 注意是async
```

### 迁移步骤

1. **第一步**: 更新import语句
   ```python
   # 旧
   from core.agents.base_agent import BaseAgent

   # 新
   from core.unified_agents.base_agent import UnifiedBaseAgent as BaseAgent
   ```

2. **第二步**: 更新构造函数
   ```python
   # 旧
   agent = BaseAgent(name="test", role="test")

   # 新
   from core.unified_agents.base_agent import UnifiedAgentConfig
   config = UnifiedAgentConfig(name="test", role="test")
   agent = UnifiedBaseAgent(config)
   ```

3. **第三步**: 更新方法调用
   ```python
   # 旧（同步）
   result = agent.process("input")

   # 新（异步）
   result = await agent.process("input")
   ```

---

## ✅ 安全审查签名

**Security-Reviewer**: ✅ 已审查
**审查时间**: 2026-04-24
**状态**: 兼容层可以安全实现

**关键要求**:
- 兼容层必须是简单重定向
- 不添加任何额外逻辑
- 所有安全检查由新架构执行
- 审计日志记录兼容层使用
