"""
ForkContextBuilder单元测试

测试ForkContextBuilder的所有功能，包括：
- 上下文构建
- 系统提示词合并
- 上下文应用
- 序列化和反序列化
- 边界条件和错误处理
"""

import json
import unittest
from unittest.mock import patch

from core.agents.fork_context_builder import ForkContext, ForkContextBuilder


class TestForkContext(unittest.TestCase):
    """ForkContext数据类测试"""

    def test_init_empty(self):
        """测试空ForkContext初始化"""
        context = ForkContext()

        self.assertEqual(context.fork_context_messages, [])
        self.assertEqual(context.prompt_messages, [])
        self.assertEqual(context.context_variables, {})
        self.assertEqual(context.system_prompt, [])

    def test_init_with_data(self):
        """测试带数据的ForkContext初始化"""
        parent_messages = [{"role": "user", "content": "父消息"}]
        prompt_messages = [{"role": "user", "content": "当前消息"}]
        context_variables = {"key": "value"}
        system_prompt = [{"role": "system", "content": "系统提示"}]

        context = ForkContext(
            fork_context_messages=parent_messages,
            prompt_messages=prompt_messages,
            context_variables=context_variables,
            system_prompt=system_prompt,
        )

        self.assertEqual(context.fork_context_messages, parent_messages)
        self.assertEqual(context.prompt_messages, prompt_messages)
        self.assertEqual(context.context_variables, context_variables)
        self.assertEqual(context.system_prompt, system_prompt)

    def test_to_dict(self):
        """测试转换为字典"""
        context = ForkContext(
            prompt_messages=[{"role": "user", "content": "测试"}],
        )

        result = context.to_dict()

        self.assertIsInstance(result, dict)
        self.assertIn("fork_context_messages", result)
        self.assertIn("prompt_messages", result)
        self.assertIn("context_variables", result)
        self.assertIn("system_prompt", result)
        self.assertEqual(result["prompt_messages"], context.prompt_messages)

    def test_to_json(self):
        """测试转换为JSON"""
        context = ForkContext(
            prompt_messages=[{"role": "user", "content": "测试中文"}],
        )

        json_str = context.to_json()

        self.assertIsInstance(json_str, str)
        self.assertIn("测试中文", json_str)

        # 验证JSON可以解析
        parsed = json.loads(json_str)
        self.assertEqual(parsed["prompt_messages"], context.prompt_messages)

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "fork_context_messages": [{"role": "user", "content": "父消息"}],
            "prompt_messages": [{"role": "user", "content": "当前消息"}],
            "context_variables": {"key": "value"},
            "system_prompt": [{"role": "system", "content": "系统提示"}],
        }

        context = ForkContext.from_dict(data)

        self.assertEqual(context.fork_context_messages, data["fork_context_messages"])
        self.assertEqual(context.prompt_messages, data["prompt_messages"])
        self.assertEqual(context.context_variables, data["context_variables"])
        self.assertEqual(context.system_prompt, data["system_prompt"])

    def test_from_json(self):
        """测试从JSON创建"""
        original = ForkContext(
            prompt_messages=[{"role": "user", "content": "测试中文"}],
        )

        json_str = original.to_json()
        restored = ForkContext.from_json(json_str)

        self.assertEqual(restored.prompt_messages, original.prompt_messages)
        self.assertEqual(restored.context_variables, original.context_variables)

    def test_serialization_roundtrip(self):
        """测试序列化往返"""
        original = ForkContext(
            fork_context_messages=[
                {"role": "user", "content": "消息1"},
                {"role": "assistant", "content": "响应1"},
            ],
            prompt_messages=[{"role": "user", "content": "消息2"}],
            context_variables={"task_id": "123", "agent_type": "analyst"},
            system_prompt=[{"role": "system", "content": "系统提示"}],
        )

        # 序列化
        json_str = original.to_json()

        # 反序列化
        restored = ForkContext.from_json(json_str)

        # 验证所有字段
        self.assertEqual(restored.fork_context_messages, original.fork_context_messages)
        self.assertEqual(restored.prompt_messages, original.prompt_messages)
        self.assertEqual(restored.context_variables, original.context_variables)
        self.assertEqual(restored.system_prompt, original.system_prompt)


class TestForkContextBuilder(unittest.TestCase):
    """ForkContextBuilder类测试"""

    def setUp(self):
        """测试前的设置"""
        self.builder = ForkContextBuilder(base_system_prompt="基础系统提示词")

    def test_init(self):
        """测试初始化"""
        builder = ForkContextBuilder()

        self.assertEqual(builder.base_system_prompt, "")

        builder = ForkContextBuilder(base_system_prompt="测试提示词")
        self.assertEqual(builder.base_system_prompt, "测试提示词")

    def test_build_empty(self):
        """测试构建空上下文"""
        # 使用空的base_system_prompt
        empty_builder = ForkContextBuilder(base_system_prompt="")

        context = empty_builder.build(
            prompt="测试任务",
            context={},
        )

        self.assertIsInstance(context, ForkContext)
        self.assertEqual(context.fork_context_messages, [])
        self.assertEqual(len(context.prompt_messages), 1)
        self.assertEqual(context.prompt_messages[0]["role"], "user")
        self.assertEqual(context.prompt_messages[0]["content"], "测试任务")
        self.assertEqual(context.system_prompt, [])

    def test_build_with_parent_messages(self):
        """测试构建带父代理消息的上下文"""
        parent_messages = [
            {"role": "user", "content": "父消息1"},
            {"role": "assistant", "content": "父响应1"},
        ]

        context = self.builder.build(
            prompt="测试任务",
            context={"parent_messages": parent_messages},
        )

        self.assertEqual(len(context.fork_context_messages), 2)
        self.assertEqual(context.fork_context_messages[0]["content"], "父消息1")
        self.assertEqual(context.fork_context_messages[1]["content"], "父响应1")

    def test_build_with_system_prompt(self):
        """测试构建带系统提示词的上下文"""
        # 使用空的base_system_prompt
        empty_builder = ForkContextBuilder(base_system_prompt="")

        context = empty_builder.build(
            prompt="测试任务",
            context={"system_prompt": "专利分析师提示词"},
        )

        self.assertEqual(len(context.system_prompt), 1)
        self.assertEqual(context.system_prompt[0]["role"], "system")
        self.assertEqual(context.system_prompt[0]["content"], "专利分析师提示词")

    def test_build_with_context_variables(self):
        """测试构建带上下文变量的上下文"""
        context = self.builder.build(
            prompt="测试任务",
            context={
                "tool_use_id": "tool_123",
                "message_log_name": "log_456",
                "fork_number": 1,
                "agent_type": "analyst",
            },
        )

        self.assertEqual(context.context_variables["tool_use_id"], "tool_123")
        self.assertEqual(context.context_variables["message_log_name"], "log_456")
        self.assertEqual(context.context_variables["fork_number"], 1)
        self.assertEqual(context.context_variables["agent_type"], "analyst")

    def test_build_complete(self):
        """测试构建完整上下文"""
        # 使用空的base_system_prompt
        empty_builder = ForkContextBuilder(base_system_prompt="")

        parent_messages = [{"role": "user", "content": "父消息"}]

        context = empty_builder.build(
            prompt="测试任务",
            context={
                "parent_messages": parent_messages,
                "system_prompt": "专利分析师",
                "tool_use_id": "tool_123",
            },
            tool_use_id="tool_456",
        )

        self.assertEqual(len(context.fork_context_messages), 1)
        self.assertEqual(len(context.prompt_messages), 1)
        self.assertEqual(len(context.system_prompt), 1)
        self.assertEqual(context.context_variables["tool_use_id"], "tool_123")

    def test_build_prompt_messages(self):
        """测试构建prompt消息"""
        messages = self.builder.build_prompt_messages(
            prompt="分析这个专利",
            tool_use_id="tool_123",
        )

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "分析这个专利")

    def test_build_prompt_messages_empty(self):
        """测试构建空prompt消息"""
        messages = self.builder.build_prompt_messages(prompt="")

        self.assertEqual(messages, [])

    def test_build_system_prompt_base_only(self):
        """测试构建仅基础系统提示词"""
        messages = self.builder.build_system_prompt(
            agent_system_prompt="",
            base_system_prompt="基础提示词",
        )

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "基础提示词")

    def test_build_system_prompt_agent_only(self):
        """测试构建仅代理系统提示词"""
        messages = self.builder.build_system_prompt(
            agent_system_prompt="专利分析师",
            base_system_prompt="",
        )

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "专利分析师")

    def test_build_system_prompt_both(self):
        """测试构建合并系统提示词"""
        messages = self.builder.build_system_prompt(
            agent_system_prompt="专利分析师",
            base_system_prompt="基础提示词",
        )

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "基础提示词")
        self.assertEqual(messages[1]["role"], "system")
        self.assertEqual(messages[1]["content"], "专利分析师")

    def test_apply_fork_context_without_parent(self):
        """测试应用Fork上下文（不包含父代理消息）"""
        fork_context = ForkContext(
            system_prompt=[{"role": "system", "content": "系统提示"}],
            prompt_messages=[{"role": "user", "content": "用户消息"}],
        )

        messages = [
            {"role": "user", "content": "新消息"},
        ]

        result = self.builder.apply_fork_context(
            messages,
            fork_context,
            include_parent_messages=False,
        )

        self.assertEqual(len(result), 2)  # 系统提示 + 新消息
        self.assertEqual(result[0]["role"], "system")
        self.assertEqual(result[1]["role"], "user")
        self.assertEqual(result[1]["content"], "新消息")

    def test_apply_fork_context_with_parent(self):
        """测试应用Fork上下文（包含父代理消息）"""
        fork_context = ForkContext(
            system_prompt=[{"role": "system", "content": "系统提示"}],
            fork_context_messages=[
                {"role": "user", "content": "父消息"},
            ],
        )

        messages = [
            {"role": "user", "content": "新消息"},
        ]

        result = self.builder.apply_fork_context(
            messages,
            fork_context,
            include_parent_messages=True,
        )

        self.assertEqual(len(result), 3)  # 系统提示 + 父消息 + 新消息
        self.assertEqual(result[0]["role"], "system")
        self.assertEqual(result[1]["content"], "父消息")
        self.assertEqual(result[2]["content"], "新消息")

    def test_merge_system_prompts(self):
        """测试合并系统提示词"""
        merged = self.builder.merge_system_prompts(
            prompt1="提示词1",
            prompt2="提示词2",
        )

        self.assertIn("提示词1", merged)
        self.assertIn("提示词2", merged)

    def test_merge_system_prompts_empty_first(self):
        """测试合并系统提示词（第一个为空）"""
        merged = self.builder.merge_system_prompts(
            prompt1="",
            prompt2="提示词2",
        )

        self.assertEqual(merged, "提示词2")

    def test_merge_system_prompts_empty_second(self):
        """测试合并系统提示词（第二个为空）"""
        merged = self.builder.merge_system_prompts(
            prompt1="提示词1",
            prompt2="",
        )

        self.assertEqual(merged, "提示词1")

    def test_validate_fork_context_valid(self):
        """测试验证有效的Fork上下文"""
        context = ForkContext(
            system_prompt=[{"role": "system", "content": "系统提示"}],
            prompt_messages=[{"role": "user", "content": "用户消息"}],
        )

        result = self.builder.validate_fork_context(context)

        self.assertTrue(result)

    def test_validate_fork_context_invalid_type(self):
        """测试验证无效类型的Fork上下文"""
        result = self.builder.validate_fork_context("not a ForkContext")

        self.assertFalse(result)

    def test_validate_fork_context_missing_role(self):
        """测试验证缺少role字段的Fork上下文"""
        context = ForkContext(
            prompt_messages=[{"content": "用户消息"}],  # 缺少role
        )

        result = self.builder.validate_fork_context(context)

        self.assertFalse(result)

    def test_validate_fork_context_missing_content(self):
        """测试验证缺少content字段的Fork上下文"""
        context = ForkContext(
            prompt_messages=[{"role": "user"}],  # 缺少content
        )

        result = self.builder.validate_fork_context(context)

        self.assertFalse(result)

    def test_context_isolation(self):
        """测试上下文隔离"""
        parent_messages = [
            {"role": "user", "content": "父消息"},
            {"role": "assistant", "content": "父响应"},
        ]

        context1 = self.builder.build(
            prompt="任务1",
            context={"parent_messages": parent_messages},
        )

        context2 = self.builder.build(
            prompt="任务2",
            context={"parent_messages": parent_messages},
        )

        # 修改context1的父代理消息
        context1.fork_context_messages[0]["content"] = "修改后的消息"

        # context2不应该受到影响
        self.assertEqual(
            context2.fork_context_messages[0]["content"],
            "父消息",
        )

    @patch("core.agents.fork_context_builder.logger")
    def test_logging(self, mock_logger):
        """测试日志记录"""
        self.builder.build(
            prompt="测试",
            context={"parent_messages": [{"role": "user", "content": "消息"}]},
        )

        # 验证日志被调用
        self.assertTrue(mock_logger.debug.called)

    def test_unicode_support(self):
        """测试Unicode支持"""
        # 使用空的base_system_prompt
        empty_builder = ForkContextBuilder(base_system_prompt="")

        context = empty_builder.build(
            prompt="分析中文专利🔍",
            context={"system_prompt": "系统提示词🎯"},
        )

        self.assertEqual(context.prompt_messages[0]["content"], "分析中文专利🔍")
        self.assertEqual(context.system_prompt[0]["content"], "系统提示词🎯")

        # 测试序列化
        json_str = context.to_json()
        self.assertIn("分析中文专利🔍", json_str)
        self.assertIn("系统提示词🎯", json_str)

        # 测试反序列化
        restored = ForkContext.from_json(json_str)
        self.assertEqual(
            restored.prompt_messages[0]["content"],
            "分析中文专利🔍",
        )


class TestForkContextBuilderIntegration(unittest.TestCase):
    """ForkContextBuilder集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建构建器（使用空的base_system_prompt）
        builder = ForkContextBuilder(base_system_prompt="")

        # 2. 构建上下文
        parent_messages = [
            {"role": "user", "content": "分析专利CN123456"},
            {"role": "assistant", "content": "好的，我将分析这个专利"},
        ]

        context = builder.build(
            prompt="请详细分析这个专利的技术方案",
            context={
                "parent_messages": parent_messages,
                "system_prompt": "你是一位专业的专利分析师",
                "tool_use_id": "tool_123",
                "agent_type": "patent-analyst",
            },
        )

        # 3. 验证上下文
        self.assertEqual(len(context.fork_context_messages), 2)
        self.assertEqual(len(context.prompt_messages), 1)
        self.assertEqual(len(context.system_prompt), 1)
        self.assertEqual(context.context_variables["agent_type"], "patent-analyst")

        # 4. 应用上下文
        new_messages = [
            {"role": "user", "content": "继续分析"},
        ]

        applied = builder.apply_fork_context(
            new_messages,
            context,
            include_parent_messages=True,
        )

        self.assertEqual(len(applied), 4)  # 系统提示 + 2个父消息 + 新消息

        # 5. 序列化
        json_str = context.to_json()

        # 6. 反序列化
        restored = ForkContext.from_json(json_str)

        # 7. 验证往返
        self.assertEqual(
            restored.prompt_messages[0]["content"],
            context.prompt_messages[0]["content"],
        )


if __name__ == "__main__":
    unittest.main()
