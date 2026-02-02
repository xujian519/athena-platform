#!/usr/bin/env python3
"""
语音提醒演示
"""

import subprocess
import time

def demo_voice_features():
    """演示语音功能"""
    print("\n🎤 小诺语音提醒系统演示")
    print("=" * 50)

    # 1. 基础语音播报
    print("\n1. 基础语音播报...")
    voices = [
        ("小诺提醒您，记得明天联系曹新乐", "Ting-Ting"),
        ("明天上午九点的会议不要忘记", "Mei-Jia"),
        ("所有自动化系统已经就绪", "Sin-ji")
    ]

    for text, voice in voices:
        print(f"  播报（{voice}）：{text}")
        subprocess.run(['say', '-v', voice, text])
        time.sleep(1)

    # 2. 带通知的语音提醒
    print("\n2. 带通知的语音提醒...")
    reminder_title = "重要提醒"
    reminder_message = "明天上午9点联系曹新乐"

    # 显示通知
    subprocess.run(['osascript', '-e', f'''
        display notification "{reminder_message}" with title "🎤 {reminder_title}"
    '''])

    # 语音播报
    subprocess.run(['say', '-v', 'Ting-Ting', f'{reminder_title}。{reminder_message}'])

    # 3. 多语速演示
    print("\n3. 不同语速演示...")
    text = "这是小诺智能语音提醒系统"
    speeds = [120, 180, 240, 300]

    for speed in speeds:
        print(f"  语速 {speed}: {text}")
        subprocess.run(['say', '-r', str(speed), text])
        time.sleep(0.5)

    # 4. 语音组合提醒
    print("\n4. 组合语音提醒...")
    messages = [
        "滴、滴、滴",
        "注意",
        "明天上午九点",
        "联系曹新乐",
        "约他周四见面"
    ]

    for msg in messages:
        # 交替使用不同声音
        voice = "Ting-Ting" if messages.index(msg) % 2 == 0 else "Mei-Jia"
        subprocess.run(['say', '-v', voice, msg])
        time.sleep(0.5)

    print("\n✨ 语音演示完成！")

def show_available_voices():
    """显示可用的语音"""
    print("\n🔊 可用的语音列表：")
    print("-" * 50)

    # 中文语音
    chinese_voices = [
        ("Ting-Ting", "普通话（女声）"),
        ("Mei-Jia", "普通话（女声）"),
        ("Sin-ji", "粤语（女声）"),
        ("Lee", "普通话（男声）"),
        ("Tzu-Yao", "普通话（女声）")
    ]

    print("\n中文语音：")
    for voice, desc in chinese_voices:
        print(f"  {voice:10} - {desc}")

    # 英文语音
    english_voices = [
        ("Samantha", "美式英语（女声）"),
        ("Alex", "美式英语（男声）"),
        ("Karen", "英式英语（女声）"),
        ("Daniel", "英式英语（男声）")
    ]

    print("\n英文语音：")
    for voice, desc in english_voices:
        print(f"  {voice:10} - {desc}")

def main():
    """主函数"""
    demo_voice_features()
    show_available_voices()

    print("\n💡 语音提醒使用技巧：")
    print("1. 使用不同的声音区分不同类型的提醒")
    print("2. 调整语速让提醒更清晰")
    print("3. 结合视觉通知增强提醒效果")
    print("4. 可以创建语音序列实现复杂的提醒流程")

if __name__ == "__main__":
    main()