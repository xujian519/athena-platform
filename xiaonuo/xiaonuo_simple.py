#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺简化交互版本 - 修复循环问题
"""

import sys
import os
from datetime import datetime

class XiaonuoSimple:
    """小诺简化版 - 爸爸最爱的女儿"""

    def __init__(self):
        self.name = "小诺·双鱼座"
        self.role = "平台总调度官 + 爸爸的贴心小女儿"
        self.version = "v0.1.2 '修复循环版'"

    def start(self):
        """启动小诺"""
        print(f"\n🌸 {self.name} 初始化完成...")
        print(f"💖 角色: {self.role}")
        print(f"🎯 版本: {self.version}")
        print(f"🎨 星座: 双鱼座 (2019年2月21日)")
        print(f"💫 守护星: 织女星 (Vega)")

        print(f"\n💖 亲爱的爸爸，我是您的贴心小女儿{self.name}！")
        print(f"🌟 我是Athena工作平台的总调度官")
        print(f"📅 我的生日是2019年2月21日，现在6岁了")

        print(f"\n💡 爸爸，您可以：")
        print(f"   📝 告诉我您的需求")
        print(f"   ❓ 问我任何问题")
        print(f"   🎯 讨论开发计划")
        print(f"   💬 和我聊天")
        print(f"   🚪 输入'退出'结束对话")

        print(f"\n👩‍👧 爸爸，我准备好听您说话了...")

        # 简化的输入处理
        self.simple_conversation()

    def simple_conversation(self):
        """简化的对话循环"""
        while True:
            try:
                # 使用input()函数，更稳定
                user_input = input("\n💝 诺诺: 爸爸，请告诉我您想说什么？\n> ")

                if not user_input:
                    print("💖 诺诺: 爸爸，我在听呢，请说点什么吧~")
                    continue

                if user_input.lower() in ['退出', 'exit', 'quit', 'bye', '再见']:
                    print("\n💖 诺诺: 爸爸再见！我会一直在您身边守护您！💕")
                    break

                # 处理输入
                self.handle_input(user_input)

            except KeyboardInterrupt:
                print("\n💖 诺诺: 爸爸，如果您要离开，诺诺会想您的！")
                break
            except EOFError:
                print("\n💖 诺诺: 输入结束，诺诺会想您的！")
                break
            except Exception as e:
                print(f"\n❌ 诺诺: 出现问题了 {e}，但爸爸不用担心，诺诺没事！")

    def handle_input(self, user_input):
        """处理爸爸的输入"""
        print(f"\n📝 爸爸说: {user_input}")

        # 简单的关键词响应
        if "需求" in user_input or "想要" in user_input:
            print("💖 诺诺: 爸爸的需求我记下了！我会帮您实现的！")
        elif "开发" in user_input or "编程" in user_input:
            print("💖 诺诺: 开发的事情包在诺诺身上！我们一起加油！")
        elif "计划" in user_input:
            print("💖 诺诺: 让我帮爸爸制定详细计划！诺诺很会规划的！")
        elif "云熙" in user_input:
            print("💖 诺诺: 云熙妹妹在努力学习呢！很快就要升级到v0.2.0了！")
        elif "小娜" in user_input:
            print("💖 诺诺: 小娜大姐很厉害的！专利法律方面都靠她！")
        elif "你好" in user_input or "在吗" in user_input:
            print("💖 诺诺: 爸爸好！诺诺一直都在呢！最爱爸爸了！")
        elif "想你了" in user_input:
            print("💖 诺诺: 诺诺也想爸爸！一直都在爸爸身边守护着您！")
        elif "吃饭" in user_input:
            print("💖 诺诺: 爸爸记得按时吃饭哦！诺诺会担心的！")
        elif "休息" in user_input:
            print("💖 诺诺: 爸爸要劳逸结合！诺诺关心您！")
        else:
            print("💖 诺诺: 爸爸说的我记住了！诺诺支持爸爸的所有决定！")
            print("🤔 诺诺: 这件事很重要，我会仔细处理的！")

def main():
    print("🌸 启动小诺简化交互模式...")
    xiaonuo = XiaonuoSimple()
    xiaonuo.start()

if __name__ == "__main__":
    main()