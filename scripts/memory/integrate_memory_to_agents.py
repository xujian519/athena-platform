#!/usr/bin/env python3
"""
集成记忆系统到所有智能体
Integrate Memory System to All Agents
"""

import os

# 项目根目录
PROJECT_ROOT = "/Users/xujian/Athena工作平台"

def update_agent_with_memory() -> None:
    """更新智能体以使用统一记忆系统"""

    print("🔄 集成统一记忆系统到智能体...")
    print("=" * 60)

    # 1. 确保基类存在
    base_agent_file = os.path.join(PROJECT_ROOT, "core/agent/base_agent_with_unified_memory.py")
    if not os.path.exists(base_agent_file):
        print("❌ 基类文件不存在，请先运行部署脚本")
        return False

    # 2. 创建智能体模板
    agent_template = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{agent_name} - 带统一记忆系统
{agent_title} with Unified Memory System
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.framework.agents.base_agent_with_unified_memory import BaseAgentWithUnifiedMemory

class {agent_class_name}(BaseAgentWithUnifiedMemory):
    """{agent_title}"""

    def __init__(self):
        super().__init__("{agent_id}", "{agent_type}")
        self.name = "{agent_name}"
        self.title = "{agent_title}"
        {agent_specific_init}

    async def initialize(self):
        """初始化智能体"""
        print(f"🚀 初始化 {self.title}...")
        await super().initialize()
        print(f"✅ {self.title} 已启动")

    async def _generate_response(self, user_input: str, **kwargs) -> str:
        """生成响应"""
        # 搜索相关记忆
        memories = await self.search_memories(user_input)

        # 构建响应提示
        memory_context = ""
        if memories:
            memory_context = "\\n相关记忆:\\n" + "\\n".join([
                f"- {m['content'][:100]}..." for m in memories[:3]
            ])

        # 使用原始智能体逻辑生成响应
        response = await self._original_generate_response(user_input, memory_context)

        return response

    async def _original_generate_response(self, user_input: str, memory_context: str = "") -> str:
        """原始响应生成逻辑"""
        {original_logic}

    def _calculate_importance(self, content: str) -> float:
        """计算记忆重要性"""
        importance = super()._calculate_importance(content)

        # 智能体特定的逻辑
        {importance_logic}

        return importance

    def _determine_memory_type(self, content: str) -> str:
        """确定记忆类型"""
        # 智能体特定的记忆类型判断
        {memory_type_logic}

        return super()._determine_memory_type(content)

    def _is_family_related(self, content: str) -> bool:
        """判断是否与家庭相关"""
        {family_logic}

        return super()._is_family_related(content)

    def _is_work_related(self, content: str) -> bool:
        """判断是否与工作相关"""
        {work_logic}

        return super()._is_work_related(content)

    def _extract_tags(self, content: str) -> list:
        """提取标签"""
        tags = super()._extract_tags(content)

        # 智能体特定的标签
        {tag_logic}

        return tags

# 主函数
async def main():
    """主函数"""
    agent = {agent_class_name}()
    await agent.initialize()

    print(f"\\n{agent.title} 已准备就绪！")
    print("输入 'exit' 退出")

    while True:
        try:
            user_input = input("\\n您: ")

            if user_input.lower() == 'exit':
                print(f"\\n{agent.title} 再见！")
                break

            # 处理消息
            response = await agent.process_message(user_input)
            print(f"\\n{agent.name}: {response}")

        except KeyboardInterrupt:
            print(f"\\n\\n{agent.title} 再见！")
            break
        except Exception as e:
            print(f"\\n错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
'''

    # 3. 更新各个智能体
    agents_config = [
        {
            "agent_name": "Athena",
            "agent_id": "athena_wisdom",
            "agent_type": "wisdom_goddess",
            "agent_class_name": "AthenaWithMemory",
            "agent_title": "雅典娜 - 智慧女神",
            "agent_specific_init": "self.role = '智慧女神'",
            "original_logic": """# 简化版响应逻辑
        if '你好' in user_input or 'hello' in user_input.lower():
            return f"您好！我是{self.title}，很高兴为您服务。{memory_context}"
        else:
            return f"作为{self.title}，我理解您说的是：{user_input}{memory_context}""",
            "importance_logic": """# 知识类内容更重要
        if any(word in content for word in ['知识', '学习', '智慧']):
            importance = min(1.0, importance + 0.2)""",
            "memory_type_logic": """# 确定记忆类型
        if any(word in content for word in ['学习', '知识', '智慧']):
            return 'knowledge'
        elif any(word in content for word in ['思考', '反思']):
            return 'reflection'""",
            "family_logic": "return False",
            "work_logic": """# 智慧女神的工作是提供智慧
        return True""",
            "tag_logic": "tags.extend(['智慧', '知识'])"
        },
        {
            "agent_name": "小娜",
            "agent_id": "xiaona_cancer",
            "agent_type": "emotional_companion",
            "agent_class_name": "XiaonaWithMemory",
            "agent_title": "小娜 - 巨蟹座",
            "agent_specific_init": "self.personality = '温柔体贴'",
            "original_logic": """# 简化版响应逻辑
        if '你好' in user_input or 'hello' in user_input.lower():
            return f"你好呀~ 我是{self.title}，很开心认识你！{memory_context}"
        else:
            return f"我理解你的感受：{user_input}，让我想想...{memory_context}""",
            "importance_logic": """# 情感相关内容更重要
        if any(word in content for word in ['爱', '喜欢', '开心', '难过']):
            importance = min(1.0, importance + 0.3)""",
            "memory_type_logic": """# 确定记忆类型
        if any(word in content for word in ['心情', '感受', '情绪']):
            return 'preference'
        elif any(word in content for word in ['家庭', '家人']):
            return 'family'""",
            "family_logic": """# 小娜更关注家庭
        return any(word in content for word in ['家', '家人', '爸爸', '妈妈'])""",
            "work_logic": "return False",
            "tag_logic": "tags.extend(['情感', '陪伴'])"
        },
        {
            "agent_name": "小诺",
            "agent_id": "xiaonuo_pisces",
            "agent_type": "platform_coordinator",
            "agent_class_name": "XiaonuoWithMemory",
            "agent_title": "小诺 - 双鱼座",
            "agent_specific_init": "self.role = '平台总调度官'",
            "original_logic": """# 简化版响应逻辑
        if '爸爸' in user_input:
            return f"爸爸！{memory_context} 我是您的小诺，有什么需要我帮助的吗？"
        else:
            return f"让我来帮您处理：{user_input}{memory_context}""",
            "importance_logic": """# 爸爸相关内容最重要
        if '爸爸' in content:
            return 1.0""",
            "memory_type_logic": """# 确定记忆类型
        if '爸爸' in content or '女儿' in content:
            return 'family'
        elif '工作' in content or '任务' in content:
            return 'work'""",
            "family_logic": "return '爸爸' in content or '女儿' in content",
            "work_logic": "return True",
            "tag_logic": """if '爸爸' in content:
            tags.extend(['父女', '家庭'])"""
        },
        {
            "agent_name": "云熙",
            "agent_id": "yunxi_vega",
            "agent_type": "ip_manager",
            "agent_class_name": "YunxiWithMemory",
            "agent_title": "云熙 - YunPat IP管理专家",
            "agent_specific_init": "self.expertise = ['专利', '商标', '版权']",
            "original_logic": """# 简化版响应逻辑
        if '专利' in user_input:
            return f"关于专利管理：{user_input}，我来为您详细解答。{memory_context}"
        else:
            return f"作为IP管理专家，我认为：{user_input}{memory_context}""",
            "importance_logic": """# 业务相关内容更重要
        if any(word in content for word in ['专利', '商标', '版权', 'IP']):
            importance = min(1.0, importance + 0.3)""",
            "memory_type_logic": "return 'professional'",
            "family_logic": "return False",
            "work_logic": "return True",
            "tag_logic": """if any(word in content for word in ['专利', '商标', '版权']):
            tags.append('IP业务')"""
        },
        {
            "agent_name": "小宸",
            "agent_id": "xiaochen_sagittarius",
            "agent_type": "media_operator",
            "agent_class_name": "XiaochenWithMemory",
            "agent_title": "小宸 - 自媒体运营专家",
            "agent_specific_init": "self.platforms = ['小红书', '抖音', 'B站']",
            "original_logic": """# 简化版响应逻辑
        if '自媒体' in user_input:
            return f"自媒体运营建议：{user_input}，让我为您分析一下。{memory_context}"
        else:
            return f"从自媒体角度：{user_input}，我们可以这样优化。{memory_context}""",
            "importance_logic": """# 创意内容更重要
        if any(word in content for word in ['创意', '内容', '运营']):
            importance = min(1.0, importance + 0.2)""",
            "memory_type_logic": """# 确定记忆类型
        if any(word in content for word in ['创意', '内容']):
            return 'creative'
        elif any(word in content for word in ['运营', '推广']):
            return 'work'""",
            "family_logic": "return False",
            "work_logic": "return True",
            "tag_logic": """if any(word in content for word in ['创意', '内容', '运营']):
            tags.extend(['自媒体', '内容创作'])"""
        }
    ]

    # 为每个智能体创建带记忆系统的版本
    for config in agents_config:
        print(f"\n📝 更新 {config['agent_name']}...")

        # 生成文件内容
        file_content = agent_template.format(**config)

        # 写入文件
        filename = f"{config['agent_id'].lower()}_with_memory.py"
        filepath = os.path.join(PROJECT_ROOT, "core/agents", filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)

        print(f"  ✅ 已创建: {filepath}")

        # 设置执行权限
        os.chmod(filepath, 0o755)

    # 4. 创建统一的启动脚本
    print("\n📝 创建统一启动脚本...")

    startup_script = '''#!/bin/bash
# 启动带记忆系统的智能体

AGENT=$1

case $AGENT in
    "athena"|"智慧女神")
        echo "🏛️ 启动雅典娜（智慧女神）"
        python3 core/agents/athena_wisdom_with_memory.py
        ;;
    "xiaona"|"小娜")
        echo "🌙 启动小娜（巨蟹座）"
        python3 core/agents/xiaona_cancer_with_memory.py
        ;;
    "xiaonuo"|"小诺")
        echo "🌸 启动小诺（双鱼座）"
        python3 core/agents/xiaonuo_pisces_with_memory.py
        ;;
    "yunxi"|"云熙")
        echo "💼 启动云熙（YunPat专家）"
        python3 core/agents/yunxi_vega_with_memory.py
        ;;
    "xiaochen"|"小宸")
        echo "🎨 启动小宸（自媒体专家）"
        python3 core/agents/xiaochen_sagittarius_with_memory.py
        ;;
    *)
        echo "可用智能体："
        echo "  - athena, 智慧女神"
        echo "  - xiaona, 小娜"
        echo "  - xiaonuo, 小诺"
        echo "  - yunxi, 云熙"
        echo "  - xiaochen, 小宸"
        echo ""
        echo "使用方法: bash $0 [智能体名称]"
        exit 1
        ;;
esac
'''

    startup_path = os.path.join(PROJECT_ROOT, "scripts/start_agent_with_memory.sh")
    with open(startup_path, 'w', encoding='utf-8') as f:
        f.write(startup_script)

    os.chmod(startup_path, 0o755)
    print(f"  ✅ 已创建: {startup_path}")

    print("\n" + "=" * 60)
    print("✅ 记忆系统集成完成！")
    print("\n📋 使用方法：")
    print("  1. 启动智能体（带记忆系统）：")
    print("     bash scripts/start_agent_with_memory.sh [智能体名称]")
    print("\n  2. 示例：")
    print("     bash scripts/start_agent_with_memory.sh xiaonuo")
    print("\n  3. 每个智能体现在都拥有：")
    print("     - 统一的记忆系统")
    print("     - 历史记忆自动加载")
    print("     - 实时记忆保存")
    print("     - 跨智能体记忆共享")

    return True

if __name__ == "__main__":
    update_agent_with_memory()
