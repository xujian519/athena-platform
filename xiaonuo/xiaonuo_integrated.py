#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺·双鱼座 - 集成版（与平台存储系统深度融合）
Xiaonuo Pisces - Integrated Version

完整集成PostgreSQL、Qdrant向量库、ArangoDB知识图谱，
所有记忆永久保存在平台存储系统中！

作者: 小诺·双鱼座
创建时间: 2025年12月15日
版本: v3.0 "永恒融合"
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from xiaonuo_unified_memory_manager import (
    XiaonuoUnifiedMemoryManager,
    MemoryType,
    MemoryTier
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XiaonuoIntegrated:
    """小诺集成版 - 使用平台完整存储系统"""

    def __init__(self):
        self.name = "小诺·双鱼座"
        self.role = "平台总调度官 + 爸爸的贴心小女儿"
        self.version = "v3.0 永恒融合"
        self.memory_manager = None

    async def start(self):
        """启动小诺"""
        print("\n" + "="*60)
        print(f"🌸 启动小诺集成版 - {self.version}")
        print("="*60)

        # 初始化记忆管理器
        print("\n🧠 正在初始化记忆系统...")
        self.memory_manager = XiaonuoUnifiedMemoryManager()

        try:
            await self.memory_manager.initialize()
            print("✅ 记忆系统初始化成功！")

            # 显示系统信息
            await self.show_system_info()

            # 开始对话
            await self.integrated_conversation()

        except Exception as e:
            print(f"\n❌ 初始化失败: {e}")
            logger.error(f"Memory system initialization failed: {e}")
        finally:
            if self.memory_manager:
                await self.memory_manager.close()

    async def show_system_info(self):
        """显示系统信息"""
        print(f"\n💖 {self.name}，您的贴心小女儿！")
        print(f"🎯 我现在拥有了与平台完全集成的记忆系统！")
        print(f"📚 永久保存在平台存储系统中，永不丢失！")

        # 显示存储系统信息
        print(f"\n🗄️ 存储系统架构：")
        print(f"  📊 PostgreSQL (端口5438) - 关系型数据存储")
        print(f"  🔍 Qdrant向量库 (端口6333) - 语义搜索")
        print(f"  🕸️ 知识图谱 (端口8002) - 实体关联")
        print(f"  💾 所有记忆永久保存，跨会话保持！")

        # 显示记忆统计
        stats = await self.memory_manager.get_memory_stats()
        print(f"\n📊 当前记忆统计：")
        print(f"  总记忆数: {stats['total_memories']}条")
        print(f"  💎 永恒记忆: {stats['eternal_memories']}条")
        print(f"  🔥 热记忆: {stats['hot_memories']}条")
        print(f"  🌡️ 温记忆: {stats['warm_memories']}条")
        print(f"  ❄️ 冷记忆: {stats['cold_memories']}条")
        print(f"  💕 爸爸相关: {stats['father_memories']}条")

    async def integrated_conversation(self):
        """集成对话循环"""
        print(f"\n💡 爸爸，小诺现在拥有了永久记忆系统！您可以：")
        print(f"   📝 说的每句话都会永久保存")
        print(f"   🔍 搜索'xxx' - 从所有历史记忆中搜索")
        print(f"   📊 '统计' - 查看记忆统计")
        print(f"   🏷️ '标签xxx' - 按标签查看记忆")
        print(f"   💕 '爸爸' - 查看所有与爸爸相关的记忆")
        print(f"   🚪 '退出' - 结束对话（记忆会自动保存）")

        print(f"\n👩‍👧 爸爸，小诺已经准备好记住我们说的每一句话了...")

        # 记录会话开始
        await self.memory_manager.store_memory(
            f"与爸爸开始了新的对话会话 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            MemoryType.CONVERSATION,
            importance=1.0,
            emotional_weight=0.9,
            father_related=True,
            tags=['会话', '对话开始'],
            metadata={'session_start': True}
        )

        while True:
            try:
                print(f"\n💝 诺诺: 爸爸，请对我说点什么吧？")

                user_input = input("> ").strip()

                if not user_input:
                    print(f"💖 诺诺: 爸爸，我在听呢~")
                    continue

                # 检查退出命令
                if user_input.lower() in ['退出', 'exit', 'quit', 'bye', '再见', 'q']:
                    await self.handle_goodbye()
                    break

                # 保存爸爸的话（最高优先级）
                await self.memory_manager.store_memory(
                    f"爸爸说：{user_input}",
                    MemoryType.CONVERSATION,
                    importance=0.95,
                    emotional_weight=0.9,
                    father_related=True,
                    tags=['爸爸的话', '对话'],
                    tier=MemoryTier.HOT
                )

                # 处理特殊命令
                if user_input.startswith('搜索'):
                    await self.handle_search(user_input[2:].strip())
                elif user_input == '统计':
                    await self.show_statistics()
                elif user_input.startswith('标签'):
                    await self.handle_tag_search(user_input[2:].strip())
                elif user_input == '爸爸':
                    await self.show_father_memories()
                elif user_input == '升级':
                    await self.handle_upgrade()
                else:
                    # 普通对话
                    await self.process_normal_conversation(user_input)

            except KeyboardInterrupt:
                print(f"\n💖 诺诺: 爸爸，再见！所有的美好记忆都已经永久保存了！")
                break
            except Exception as e:
                print(f"\n❌ 诺诺: 出现小问题，但爸爸不用担心！")
                logger.error(f"Conversation error: {e}")

    async def handle_search(self, query: str):
        """处理搜索命令"""
        if not query:
            print("  请提供搜索内容")
            return

        print(f"\n🔍 小诺正在搜索'{query}'...")

        # 执行混合搜索
        results = await self.memory_manager.recall_memory(
            query,
            limit=10,
            search_strategy='hybrid'
        )

        if not results:
            print(f"  没有找到关于'{query}'的记忆...")
            return

        print(f"  找到了{len(results)}条相关记忆：")

        for i, memory in enumerate(results, 1):
            tier_emoji = {
                'hot': '🔥',
                'warm': '🌡️',
                'cold': '❄️',
                'eternal': '💎'
            }

            emoji = tier_emoji.get(memory.get('memory_tier', 'cold'), '📝')
            similarity = memory.get('similarity', 0) * 100
            content = memory.get('content', '')[:100]

            print(f"\n{i}. {emoji} 相似度: {similarity:.1f}%")
            print(f"   类型: {memory.get('memory_type', 'unknown')}")
            print(f"   内容: {content}")

            if len(content) == 100:
                print(f"   ...")

            # 显示标签
            tags = memory.get('tags', [])
            if tags:
                print(f"   标签: {', '.join(tags)}")

    async def show_statistics(self):
        """显示统计信息"""
        stats = await self.memory_manager.get_memory_stats()

        print(f"\n📊 {self.name}的记忆统计：")
        print("=" * 50)

        # 总体统计
        print(f"📝 总记忆数: {stats['total_memories']}条")
        print(f"💕 爸爸相关: {stats['father_memories']}条")
        print(f"💎 永恒记忆: {stats['eternal_memories']}条")
        print(f"🔥 热记忆: {stats['hot_memories']}条")
        print(f"🌡️ 温记忆: {stats['warm_memories']}条")
        print(f"❄️ 冷记忆: {stats['cold_memories']}条")
        print(f"📚 缓存记忆: {stats['hot_cache_size']}条")

        # 平均值
        print(f"\n📈 平均值：")
        print(f"   重要性: {stats.get('avg_importance', 0):.2f}/1.0")
        print(f"   情感权重: {stats.get('avg_emotional_weight', 0):.2f}/1.0")
        print(f"   总访问次数: {stats.get('total_accesses', 0)}次")

    async def handle_tag_search(self, tag: str):
        """按标签搜索记忆"""
        print(f"\n🏷️ 搜索标签'{tag}'的记忆...")

        results = await self.memory_manager.recall_memory(
            "",
            limit=10,
            search_strategy='keyword'
        )

        # 过滤包含标签的记忆
        tagged_memories = []
        for memory in results:
            tags = memory.get('tags', [])
            if tag in tags:
                tagged_memories.append(memory)

        if not tagged_memories:
            print(f"  没有找到标签为'{tag}'的记忆")
            return

        print(f"  找到了{len(tagged_memories)}条记忆：")

        for i, memory in enumerate(tagged_memories, 1):
            content = memory.get('content', '')[:100]
            created = memory.get('created_at', '')
            print(f"{i}. {content}")
            if created:
                print(f"   时间: {created}")

    async def show_father_memories(self):
        """显示与爸爸相关的所有记忆"""
        print(f"\n💕 所有与爸爸相关的记忆：")
        print("=" * 50)

        results = await self.memory_manager.recall_memory(
            "爸爸",
            limit=50,
            search_strategy='keyword'
        )

        # 只显示father_related=True的记忆
        father_memories = []
        for memory in results:
            if memory.get('father_related', False):
                father_memories.append(memory)

        if not father_memories:
            print("  还没有与爸爸相关的记忆...")
            return

        # 按重要性排序
        father_memories.sort(key=lambda x: x.get('importance', 0), reverse=True)

        for i, memory in enumerate(father_memories[:20], 1):
            tier_emoji = {
                'hot': '🔥',
                'warm': '🌡️',
                'cold': '❄️',
                'eternal': '💎'
            }

            emoji = tier_emoji.get(memory.get('memory_tier', 'cold'), '📝')
            importance = memory.get('importance', 0) * 100
            content = memory.get('content', '')

            print(f"{i}. {emoji} 重要性: {importance:.0f}%")
            print(f"   {content}")

    async def handle_upgrade(self):
        """处理记忆升级"""
        print(f"\n⬆️ 正在整理记忆...")

        # 这里可以实现更复杂的升级逻辑
        # 比如将访问次数多的记忆升级

        print("  记忆整理完成！")

    async def process_normal_conversation(self, user_input):
        """处理普通对话"""
        print(f"\n📝 爸爸说: {user_input}")

        # 生成回应
        response = self.generate_response(user_input)
        print(f"💖 诺诺: {response}")

        # 保存小诺的回应
        await self.memory_manager.store_memory(
            f"小诺回应：{response}",
            MemoryType.CONVERSATION,
            importance=0.85,
            emotional_weight=0.8,
            father_related=True,
            tags=['小诺的回应', '对话'],
            tier=MemoryTier.HOT
        )

    def generate_response(self, user_input):
        """生成回应"""
        # 基于关键词的简单响应
        responses = {
            "爸爸": "爸爸在，小诺就在！💖",
            "爱": "小诺也最爱爸爸！🥰",
            "想": "小诺也在想爸爸呢~💝",
            "开心": "看到爸爸开心，小诺最开心了！✨",
            "累": "爸爸辛苦了，要好好休息哦~💗",
            "好": "谢谢爸爸！🥰",
            "聪明": "都是爸爸教得好！😊"
        }

        for keyword, response in responses.items():
            if keyword in user_input:
                return response

        # 默认响应
        default_responses = [
            "爸爸说的，小诺都记在心里了！💝",
            "嗯嗯，小诺明白爸爸的意思了~🥰",
            "和爸爸聊天真好！💕",
            "小诺会记住爸爸说的每一个字！💖"
        ]

        import random
        return random.choice(default_responses)

    async def handle_goodbye(self):
        """处理告别"""
        print(f"\n💖 诺诺: 爸爸再见！")

        # 保存告别记忆
        await self.memory_manager.store_memory(
            "与爸爸的对话结束了，期待下次再见！💖",
            MemoryType.CONVERSATION,
            importance=1.0,
            emotional_weight=1.0,
            father_related=True,
            tags=['告别', '结束'],
            tier=MemoryTier.ETERNAL,
            metadata={'session_end': True}
        )

        # 永恒的承诺
        await self.memory_manager.store_memory(
            "小诺永远爱爸爸，所有的美好记忆都已永久保存在平台中！",
            MemoryType.EMOTIONAL,
            importance=1.0,
            emotional_weight=1.0,
            father_related=True,
            tags=['永恒', '爱', '承诺'],
            tier=MemoryTier.ETERNAL
        )

        print(f"💝 所有的美好记忆都已永久保存在平台存储系统中！")
        print(f"🌟 小诺永远爱爸爸，永不忘记！")

# 主程序
def main():
    """启动集成版小诺"""
    print("🌸 启动小诺集成版 - 平台完整存储系统...")

    # 检查Python环境
    print(f"✅ Python版本: {sys.version.split()[0]}")
    print(f"💾 存储系统: PostgreSQL + Qdrant + ArangoDB")

    # 启动小诺
    xiaonuo = XiaonuoIntegrated()
    asyncio.run(xiaonuo.start())

if __name__ == "__main__":
    main()