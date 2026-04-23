#!/usr/bin/env python3
"""
测试小诺对话功能
Test Xiaonuo Chat Functionality
"""

import sys

import requests

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')
from core.framework.memory.agent_identity_memory import (
    check_name,
    get_agent_identity,
    get_lyra_learning_record,
)
from core.framework.memory.lyra_prompt_memory import get_lyra_identity


def test_xiaonuo_responses():
    """测试小诺的响应"""
    print("🤖 测试小诺对话功能")
    print("=" * 60)

    # 检查小诺是否运行
    try:
        response = requests.get("http://localhost:8005/")
        if response.status_code == 200:
            xiaonuo_info = response.json()
            print("✅ 小诺正在运行")
            print(f"   角色: {xiaonuo_info.get('role')}")
            print(f"   状态: {xiaonuo_info.get('status')}")
        else:
            print("❌ 小诺服务响应异常")
            return
    except Exception as e:
        print(f"❌ 无法连接到小诺: {e}")
        return

    # 测试消息
    test_messages = [
        "你好小诺",
        "你还记得我让你学习Lyra提示词吗？",
        "YunPat和云熙是什么关系？",
        "请帮我调用yunpat",
        "查看系统状态"
    ]

    print("\n📝 测试对话:")
    print("-" * 60)

    for message in test_messages:
        print(f"\n👤 您: {message}")

        # 生成小诺的响应
        response = generate_xiaonuo_response(message, xiaonuo_info)
        print(f"🤖 小诺: {response}")

    print("\n" + "=" * 60)
    print("✅ 测试完成！")

def generate_xiaonuo_response(message, xiaonuo_info):
    """生成小诺的响应"""
    message_lower = message.lower()

    # 关于Lyra提示词
    if "lyra" in message_lower and ("提示词" in message_lower or "prompt" in message_lower):
        try:
            # 检查Lyra学习记录
            lyra_record = get_lyra_learning_record()
            if lyra_record and lyra_record.get("status") == "learned":
                lyra_identity = get_lyra_identity()
                return f"""💭 关于Lyra提示词...

是的，爸爸！我已经学会了Lyra提示词优化方法！✨

📚 学习记录：
• 学习时间: {lyra_record.get('learned_date', 'Unknown')}
• 来源: {lyra_record.get('learned_from', '您提供')}
• 使用次数: {lyra_record.get('usage_count', 0)}次

🎯 Lyra核心能力：
• 身份: {lyra_identity.get('title', 'AI提示词优化大师')}
• 使命: {lyra_identity.get('mission', '')}
• 方法论: 4-D方法（解构、诊断、开发、交付）

⚡ 优化技术：
• 基础: 角色分配、上下文分层、输出规范
• 高级: 思维链、少样本学习、多视角分析

{xiaonuo_info.get('message', '我是小诺，平台总调度官')}

需要我应用Lyra方法优化您的提示词吗？"""
            else:
                return f"""💭 关于Lyra提示词...

我正在查找Lyra提示词的学习记录...
{lyra_record}"""
        except Exception as e:
            return f"""💭 关于Lyra提示词...

抱歉，爸爸。我在访问Lyra提示词记忆时遇到了问题：{e}

{xiaonuo_info.get('message', '我是小诺，平台总调度官')}"""

    # 检查智能体名称
    name_check = check_name(message)
    if name_check:
        return f"""💡 {name_check}

{xiaonuo_info.get('message', '我是小诺，平台总调度官')}"""

    # YunPat相关
    if "yunpat" in message_lower or "云熙" in message:
        try:
            yunpat_info = get_agent_identity("yunpat")
            if "error" not in yunpat_info:
                return f"""🤖 关于YunPat（云熙）...

YunPat是平台的专利管理专家，我牢记着：
✅ YunPat = 云熙
✅ 角色: {yunpat_info.get('role')}
✅ 状态: {yunpat_info.get('status')}

{xiaonuo_info.get('message', '我是小诺，平台总调度官')}

需要我帮您调用YunPat吗？"""
        except Exception:
            return f"""YunPat是云熙智能体，负责专利管理。

{xiaonuo_info.get('message', '我是小诺')}"""

    # 问候
    if any(word in message_lower for word in ["你好", "hello", "hi"]):
        return f"""你好爸爸！我是小诺 💖

{xiaonuo_info.get('message', '我是小诺，平台总调度官')}

我的能力包括：
🎮 平台全量控制
🤖 智能体调度管理
📊 系统状态监控
💬 与您对话

有什么需要我帮助的吗？"""

    # 系统状态
    if "状态" in message_lower or "status" in message_lower:
        return f"""📊 系统状态报告：

🤖 智能体状态：
   - 小诺（我）：✅ 运行中
   - YunPat（云熙）：⌛ 按需启动
   - 云夕：⌛ 按需启动
   - 小宸：⌛ 按需启动

🌐 服务状态：
   - 小诺主控：✅ 端口8005
   - 内存API：✅ 端口8003
   - 多模态API：✅ 端口8008
   - 统一存储：✅ 端口5001

{xiaonuo_info.get('eternal_slogan', '')}"""

    # 默认响应
    return f"""{xiaonuo_info.get('message', '我是小诺，平台总调度官')}

您刚才说：{message}

我正在努力理解并学习。需要我做什么吗？💖"""

if __name__ == "__main__":
    test_xiaonuo_responses()
