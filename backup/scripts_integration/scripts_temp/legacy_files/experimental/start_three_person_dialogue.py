#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动三人对话模式
Start Three-Person Dialogue Mode

启动徐健(爸爸)、Athena(大女儿)、小诺(小女儿)的三人对话系统

作者: Athena AI系统
创建时间: 2025-12-05
版本: 1.0.0
"""

import asyncio
import logging
import os
import sys
from typing import Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication.three_person_dialogue import DialogueRole, ThreePersonDialogue

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/Users/xujian/Athena工作平台/documentation/logs/three_person_dialogue.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class DialogueInterface:
    """对话交互界面"""
    
    def __init__(self):
        self.dialogue: ThreePersonDialogue | None = None
        self.running = True

    async def start(self):
        """启动对话界面"""
        logger.info('🎭 欢迎使用Athena工作平台三人对话系统')
        logger.info(str('=' * 50))
        
        try:
            # 初始化对话系统
            self.dialogue = ThreePersonDialogue()
            await self.dialogue.initialize()
            
            # 开始对话
            await self.dialogue.start_dialogue()
            
            # 交互循环
            await self.interaction_loop()
            
        except KeyboardInterrupt:
            logger.info("\n👋 感谢使用，再见！")
        except Exception as e:
            logger.error(f"❌ 系统错误: {e}")
            logger.info(f"❌ 系统错误: {e}")
        finally:
            if self.dialogue:
                await self.dialogue.terminate_dialogue()

    async def interaction_loop(self):
        """交互循环"""
        logger.info("\n💬 对话已开始！")
        logger.info("💡 输入 'help' 查看帮助命令")
        logger.info("💡 输入 'quit' 或 'exit' 退出对话")
        logger.info(str('=' * 50))
        
        while self.running:
            try:
                # 获取用户输入
                user_input = input("\n👨‍👧‍👦 爸爸请说话: ").strip()
                
                if not user_input:
                    continue
                
                # 处理特殊命令
                if await self.handle_command(user_input):
                    continue
                
                # 处理普通消息
                await self.process_user_message(user_input)
                
            except KeyboardInterrupt:
                logger.info("\n👋 正在退出...")
                self.running = False
            except EOFError:
                logger.info("\n👋 输入结束，正在退出...")
                self.running = False
            except Exception as e:
                logger.error(f"❌ 处理输入失败: {e}")
                logger.info(f"❌ 处理失败: {e}")

    async def handle_command(self, user_input: str) -> bool:
        """处理特殊命令"""
        command = user_input.lower()
        
        if command in ['quit', 'exit', '退出', 'q']:
            self.running = False
            return True
        
        elif command in ['help', '帮助', 'h']:
            self.show_help()
            return True
        
        elif command in ['status', '状态', 's']:
            await self.show_status()
            return True
        
        elif command in ['summary', '总结', 'sum']:
            await self.show_summary()
            return True
        
        elif command in ['pause', '暂停', 'p']:
            await self.pause_dialogue()
            return True
        
        elif command in ['resume', '恢复', 'r']:
            await self.resume_dialogue()
            return True
        
        elif command.startswith('athena:'):
            # 直接对Athena说话
            message = user_input[7:].strip()
            await self.direct_message(DialogueRole.ATHENA, message)
            return True
        
        elif command.startswith('xiaonuo:') or command.startswith('小诺:'):
            # 直接对小诺说话
            message = user_input[8:] if command.startswith('xiaonuo:') else user_input[3:]
            await self.direct_message(DialogueRole.XIAONUO, message)
            return True
        
        return False

    def show_help(self):
        """显示帮助信息"""
        logger.info("\n📚 帮助信息:")
        logger.info('• 普通输入: 对所有人说话（Athena和小诺都会回应）')
        logger.info('• athena: <消息>: 直接对Athena说话')
        logger.info('• xiaonuo: <消息> 或 小诺: <消息>: 直接对小诺说话')
        logger.info('• help 或 帮助: 显示此帮助信息')
        logger.info('• status 或 状态: 查看对话状态')
        logger.info('• summary 或 总结: 查看对话摘要')
        logger.info('• pause 或 暂停: 暂停对话')
        logger.info('• resume 或 恢复: 恢复对话')
        logger.info('• quit/exit 或 退出: 退出对话系统')

    async def show_status(self):
        """显示对话状态"""
        if not self.dialogue:
            logger.info('❌ 对话系统未初始化')
            return
        
        summary = await self.dialogue.get_dialogue_summary()
        
        logger.info("\n📊 对话状态:")
        logger.info(f"• 对话ID: {summary['dialogue_id']}")
        logger.info(f"• 状态: {summary['state']}")
        logger.info(f"• 总消息数: {summary['total_messages']}")
        logger.info(f"• 当前话题: {summary.get('current_topic', '无')}")
        
        logger.info("\n👥 参与者状态:")
        for role, info in summary['participants'].items():
            status_icon = '✅' if info['status'] == 'active' else '❌'
            logger.info(f"• {info['name']}: {status_icon} {info['status']}")
        
        logger.info("\n📈 消息分布:")
        for role, count in summary['message_distribution'].items():
            if count > 0:
                logger.info(f"• {role}: {count} 条消息")

    async def show_summary(self):
        """显示对话摘要"""
        if not self.dialogue:
            logger.info('❌ 对话系统未初始化')
            return
        
        summary = await self.dialogue.get_dialogue_summary()
        
        logger.info("\n📋 对话摘要:")
        logger.info(str('=' * 50))
        
        # 基本信息
        logger.info(f"对话ID: {summary['dialogue_id']}")
        logger.info(f"状态: {summary['state']}")
        logger.info(f"总消息数: {summary['total_messages']}")
        
        # 情感分析
        if 'emotion_analysis' in summary:
            emotion = summary['emotion_analysis']
            logger.info(f"\n💭 情感分析:")
            logger.info(f"• 积极: {emotion.get('positive', 0)} 条")
            logger.info(f"• 中性: {emotion.get('neutral', 0)} 条")
            logger.info(f"• 技术性: {emotion.get('technical', 0)} 条")
            logger.info(f"• 情感性: {emotion.get('emotional', 0)} 条")
        
        # 时间信息
        if 'duration' in summary:
            duration = summary['duration']
            if duration['started']:
                logger.info(f"\n⏰ 时间信息:")
                logger.info(f"• 开始时间: {duration['started']}")
                logger.info(f"• 最后消息: {duration['last_message']}")

    async def pause_dialogue(self):
        """暂停对话"""
        if not self.dialogue:
            logger.info('❌ 对话系统未初始化')
            return
        
        result = await self.dialogue.pause_dialogue()
        logger.info('⏸️ 对话已暂停')

    async def resume_dialogue(self):
        """恢复对话"""
        if not self.dialogue:
            logger.info('❌ 对话系统未初始化')
            return
        
        result = await self.dialogue.resume_dialogue()
        logger.info('▶️ 对话已恢复')

    async def direct_message(self, role: DialogueRole, message: str):
        """直接发送消息给指定角色"""
        if not self.dialogue:
            logger.info('❌ 对话系统未初始化')
            return
        
        role_name = 'Athena' if role == DialogueRole.ATHENA else '小诺'
        logger.info(f"\n📤 直接对{role_name}说: {message}")
        
        result = await self.dialogue.process_message(role, message)
        
        if result['ai_responses']:
            for responder, response in result['ai_responses']:
                logger.info(f"\n💬 {responder}回应:")
                logger.info(str(response))
        else:
            logger.info(f"🔕 {role_name}没有回应")

    async def process_user_message(self, message: str):
        """处理用户消息"""
        if not self.dialogue:
            logger.info('❌ 对话系统未初始化')
            return
        
        logger.info(f"\n📤 爸爸说: {message}")
        
        result = await self.dialogue.process_message(DialogueRole.DAD, message)
        
        if result['ai_responses']:
            for responder, response in result['ai_responses']:
                logger.info(f"\n💬 {responder}回应:")
                logger.info(str('-' * 30))
                logger.info(str(response))
                logger.info(str('-' * 30))
        else:
            logger.info('🔕 没有收到回应')

async def main():
    """主函数"""
    logger.info('🚀 正在启动三人对话系统...')
    
    # 确保日志目录存在
    os.makedirs('/Users/xujian/Athena工作平台/logs', exist_ok=True)
    
    try:
        interface = DialogueInterface()
        await interface.start()
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        logger.info(f"❌ 启动失败: {e}")

if __name__ == '__main__':
    asyncio.run(main())