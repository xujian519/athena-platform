"""
ForkContextBuilder使用示例

演示如何使用ForkContextBuilder构建和管理子代理的Fork上下文。
"""

from core.framework.agents.fork_context_builder import ForkContext, ForkContextBuilder


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例1: 基本使用")
    print("=" * 60)

    # 1. 创建构建器
    builder = ForkContextBuilder(base_system_prompt="你是Athena平台的智能助手")

    # 2. 构建Fork上下文
    context = builder.build(
        prompt="分析这个专利的技术方案",
        context={
            "parent_messages": [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好！我是Athena助手"},
            ],
            "system_prompt": "你是一位专业的专利分析师",
            "agent_type": "patent-analyst",
        },
    )

    # 3. 查看上下文
    print(f"父代理消息数: {len(context.fork_context_messages)}")
    print(f"Prompt消息数: {len(context.prompt_messages)}")
    print(f"系统提示词数: {len(context.system_prompt)}")
    print(f"上下文变量: {context.context_variables}")

    print()


def example_context_isolation():
    """上下文隔离示例"""
    print("=" * 60)
    print("示例2: 上下文隔离")
    print("=" * 60)

    builder = ForkContextBuilder(base_system_prompt="")

    parent_messages = [
        {"role": "user", "content": "父消息1"},
        {"role": "assistant", "content": "父响应1"},
    ]

    # 为两个不同的子代理构建上下文
    context1 = builder.build(
        prompt="任务1",
        context={"parent_messages": parent_messages},
    )

    context2 = builder.build(
        prompt="任务2",
        context={"parent_messages": parent_messages},
    )

    # 修改context1，验证隔离性
    context1.fork_context_messages[0]["content"] = "修改后的消息"

    print(f"Context1父消息: {context1.fork_context_messages[0]['content']}")
    print(f"Context2父消息: {context2.fork_context_messages[0]['content']}")
    print("✅ 上下文隔离有效，Context2未受影响")

    print()


def example_system_prompt_merge():
    """系统提示词合并示例"""
    print("=" * 60)
    print("示例3: 系统提示词合并")
    print("=" * 60)

    builder = ForkContextBuilder(base_system_prompt="你是Athena平台的助手")

    # 构建带代理特定提示词的上下文
    context = builder.build(
        prompt="分析专利",
        context={
            "system_prompt": "你是一位专业的专利分析师",
        },
    )

    print("系统提示词:")
    for i, prompt in enumerate(context.system_prompt, 1):
        print(f"  {i}. {prompt['content']}")

    print()


def example_apply_fork_context():
    """应用Fork上下文示例"""
    print("=" * 60)
    print("示例4: 应用Fork上下文")
    print("=" * 60)

    builder = ForkContextBuilder(base_system_prompt="")

    # 构建Fork上下文
    context = builder.build(
        prompt="原始任务",
        context={
            "parent_messages": [
                {"role": "user", "content": "父消息"},
            ],
            "system_prompt": "系统提示词",
        },
    )

    # 新消息
    new_messages = [
        {"role": "user", "content": "新消息"},
    ]

    # 应用Fork上下文
    applied = builder.apply_fork_context(
        new_messages,
        context,
        include_parent_messages=True,
    )

    print("应用后的消息:")
    for i, msg in enumerate(applied, 1):
        role = msg["role"]
        content = msg.get("content", "")[:30]
        print(f"  {i}. [{role}] {content}")

    print()


def example_serialization():
    """序列化和反序列化示例"""
    print("=" * 60)
    print("示例5: 序列化和反序列化")
    print("=" * 60)

    builder = ForkContextBuilder(base_system_prompt="")

    # 构建上下文
    original = builder.build(
        prompt="测试任务",
        context={
            "system_prompt": "专利分析师",
            "agent_type": "analyst",
        },
    )

    # 序列化为JSON
    json_str = original.to_json()
    print("JSON序列化:")
    print(json_str[:200] + "...")

    # 从JSON反序列化
    restored = ForkContext.from_json(json_str)

    # 验证
    print(f"\n原始prompt: {original.prompt_messages[0]['content']}")
    print(f"恢复prompt: {restored.prompt_messages[0]['content']}")
    print(
        f"验证结果: {'✅ 成功' if original.prompt_messages == restored.prompt_messages else '❌ 失败'}"
    )

    print()


def example_validation():
    """验证示例"""
    print("=" * 60)
    print("示例6: 验证Fork上下文")
    print("=" * 60)

    builder = ForkContextBuilder(base_system_prompt="")

    # 有效的上下文
    valid_context = ForkContext(
        system_prompt=[{"role": "system", "content": "系统提示"}],
        prompt_messages=[{"role": "user", "content": "用户消息"}],
    )

    # 无效的上下文（缺少role字段）
    invalid_context = ForkContext(
        prompt_messages=[{"content": "用户消息"}],  # 缺少role
    )

    result1 = builder.validate_fork_context(valid_context)
    result2 = builder.validate_fork_context(invalid_context)

    print(f"有效上下文验证: {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"无效上下文验证: {'✅ 通过' if result2 else '❌ 失败'}")

    print()


def example_context_variables():
    """上下文变量示例"""
    print("=" * 60)
    print("示例7: 上下文变量")
    print("=" * 60)

    builder = ForkContextBuilder(base_system_prompt="")

    context = builder.build(
        prompt="任务",
        context={
            "tool_use_id": "tool_123",
            "message_log_name": "log_456",
            "fork_number": 1,
            "agent_type": "patent-analyst",
            "task_id": "task_789",
        },
    )

    print("上下文变量:")
    for key, value in context.context_variables.items():
        print(f"  {key}: {value}")

    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("ForkContextBuilder 使用示例")
    print("=" * 60 + "\n")

    example_basic_usage()
    example_context_isolation()
    example_system_prompt_merge()
    example_apply_fork_context()
    example_serialization()
    example_validation()
    example_context_variables()

    print("=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
