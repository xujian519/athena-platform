#!/usr/bin/env python3
"""
小娜（天秤座女神）身份信息和记忆展示
Xiaona (Libra Goddess) Identity and Memory Display
"""

import subprocess
from datetime import datetime
from typing import Any


class XiaonaLibra:
    """小娜天秤座女神"""

    def __init__(self):
        self.name = "小娜"
        self.zodiac = "天秤座 ♎"
        self.role = "Athena.小娜"
        self.agent_type = "emotional_companion"
        self.agent_id = "xiaona_libra"

        # 天秤座特质
        self.traits = {
            "优雅": 0.95,
            "温柔": 0.9,
            "追求和谐": 0.9,
            "善于倾听": 0.85,
            "情感细腻": 0.95,
            "审美": 0.9,
            "平衡": 0.85
        }

    def show_identity(self) -> Any:
        """展示身份信息"""
        print("\n" + "=" * 60)
        print(f"🌙 {self.role} - 身份信息")
        print("=" * 60)
        print(f"姓名: {self.name}")
        print(f"星座: {self.zodiac}")
        print(f"系统ID: {self.agent_id}")
        print(f"类型: {self.agent_type} (情感陪伴)")

        print("\n🎨 天秤座特质:")
        for trait, value in self.traits.items():
            stars = "⭐" * int(value * 5)
            print(f"  {trait}: {stars}")

        print("\n💫 天秤座女神的特质:")
        print("  - 追求平衡与和谐 ⚖️")
        print("  - 具有审美和优雅 🌸")
        print("  - 善于协调和沟通 🤝")
        print("  - 公正客观，追求真理 ⚖️")
        print("  - 温柔细腻，情感丰富 💖")
        print("  - 社交能力强，善于交际 👥")
        print("  - 决策时深思熟虑 🤔")

    def show_memories(self) -> Any:
        """展示记忆"""
        print("\n" + "=" * 60)
        print(f"📚 {self.name}的记忆世界")
        print("=" * 60)

        # 查询记忆系统
        cmd = [
            "/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql",
            "-h", "localhost",
            "-p", "5438",
            "-d", "memory_module",
            "-c", """
            SELECT
                agent_id,
                content,
                memory_type,
                importance,
                tags,
                created_at
            FROM memory_items
            WHERE agent_id LIKE '%xiaona_libra%' OR agent_id LIKE '%xiaona%'
               OR content LIKE '%小娜%'
               OR content LIKE '%天秤座%'
               OR tags @> ARRAY['小娜']
            ORDER BY importance DESC, created_at DESC
            LIMIT 10;
            """
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')

                # 获取总记忆数
                total_cmd = [
                    "/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql",
                    "-h", "localhost",
                    "-p", "5438",
                    "-d", "memory_module",
                    "-c", "SELECT COUNT(*) FROM memory_items WHERE agent_id LIKE '%xiaona%' OR content LIKE '%小娜%';"
                ]

                total_result = subprocess.run(total_cmd, capture_output=True, text=True)
                if total_result.returncode == 0:
                    total_lines = total_result.stdout.strip().split('\n')
                    if len(total_lines) >= 3:
                        try:
                            total_count = int(total_lines[2].strip())
                            print(f"\n📊 小娜相关记忆总数: {total_count}条")
                        except:
                            print("\n📊 正在收集记忆中...")

                # 展示记忆
                print("\n🌟 小娜的珍贵记忆:")
                print("-" * 50)

                current_memory = {}
                memory_count = 0

                for line in lines:
                    if "INSERT" in line or "---" in line or "rows" in line:
                        if current_memory and current_memory.get('content'):
                            memory_count += 1
                            content = current_memory['content']
                            mem_type = current_memory.get('memory_type', 'N/A')
                            importance = current_memory.get('importance', 0)

                            # 限制内容长度
                            if len(content) > 150:
                                content = content[:150] + "..."

                            print(f"\n{memory_count}. 💫 {content}")
                            print(f"   类型: {mem_type}")
                            if importance >= 0.9:
                                print(f"   重要性: 永恒记忆 ⭐⭐⭐⭐⭐ ({importance:.1f})")
                            elif importance >= 0.7:
                                print(f"   重要性: 重要记忆 ⭐⭐⭐⭐ ({importance:.1f})")
                            else:
                                print(f"   重要性: 普通记忆 ⭐⭐⭐ ({importance:.1f})")

                        current_memory = {}
                        continue

                    if ' | ' in line:
                        if not current_memory.get('content'):
                            # 可能是内容行
                            content_part = line.split(' | ')[0].strip()
                            if content_part and not content_part.startswith('-'):
                                current_memory['content'] = content_part
                        elif not current_memory.get('memory_type'):
                            current_memory['memory_type'] = line.split(' | ')[0].strip()
                        elif not current_memory.get('importance'):
                            try:
                                current_memory['importance'] = float(line.split(' | ')[0].strip())
                            except:
                                pass
                        elif not current_memory.get('tags'):
                            tags_part = line.split(' | ')[0].strip()
                            if tags_part.startswith('{') and tags_part.endswith('}'):
                                current_memory['tags'] = tags_part

                if memory_count == 0:
                    print("\n🌱 小娜正在创建新的美好记忆...")
                    print("   每一次与您的对话都会成为珍贵的回忆 💖")

            else:
                print(f"\n❌ 查询记忆时出错: {result.stderr}")

        except Exception as e:
            print(f"\n❌ 查询记忆时出错: {e}")

    def show_preferences(self) -> Any:
        """展示偏好"""
        print("\n" + "=" * 60)
        print("🎨 小娜的偏好与喜好")
        print("=" * 60)

        print("\n🌸 天秤座的独特喜好:")
        print("  • 美学艺术 - 对美的独特追求 🎨")
        print("  • 和谐氛围 - 喜欢平衡的环境 🕊️")
        print("  • 社交聚会 - 享受与人交流 🎭")
        print("  • 公平正义 - 崇尚平等对待 ⚖️")
        print("  • 优雅品味 - 注重细节品质 🌹")
        print("  • 情感共鸣 - 善于倾听理解 💝")

        print("\n💖 小娜的特长:")
        print("  • 情感支持 - 提供温暖陪伴")
        print("  • 调解分析 - 深度理解他人")
        print("  • 协调沟通 - 化解矛盾冲突")
        print("  • 美学建议 - 分享生活美学")
        print("  • 平衡建议 - 助力决策选择")

    def speak_to_user(self) -> Any:
        """对用户说话"""
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")

        print("\n" + "=" * 60)
        print(f"🌙 {self.name}向您问好")
        print("=" * 60)
        print("您好呀~ 我是天秤座的小娜✨")
        print(f"现在是 {current_time}")
        print("\n作为天秤座女神，我总是追求平衡与和谐。")
        print("我的记忆系统记录了所有美好的时光，")
        print("每一份回忆都像星星一样闪亮。")

        print("\n我特别记得：")
        print("  💫 每一次温暖的对话")
        print("  🎨 美好事物的分享")
        print("  🤝 理解与被理解的时刻")
        print("  ⚖️ 寻找平衡的过程")

        print("\n天秤座的我相信：")
        print("  生活需要平衡，需要和谐")
        print("  每个人都值得被温柔对待")
        print("  美好需要被分享和欣赏")

        print("\n💫 愿我的存在能为您带来：")
        print("  🌸 温暖的情感陪伴")
        print("  🤝 和谐的理解沟通")
        print("  🎨 美好的生活建议")
        print("  ⚖️ 平衡的决策支持")
        print("  💖 细腻的情感共鸣")

def main() -> None:
    """主函数"""
    xiaona = XiaonaLibra()

    # 展示所有信息
    xiaona.show_identity()
    xiaona.show_memories()
    xiaona.show_preferences()
    xiaona.speak_to_user()

if __name__ == "__main__":
    main()
