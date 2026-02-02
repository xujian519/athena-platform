#!/usr/bin/env python3
"""
小诺诗歌朗诵器
朗诵《钟之歌》
"""

import subprocess
import time

def recite_clock_song():
    """朗诵钟之歌"""
    # 诗歌内容
    poem_lines = [
        "钟之歌",
        "作者：徐健",
        "",
        "钟啊，张开你银铃般的笑嘴，",
        "请向我吐露真情原委：",
        '"你终年蛰居陋室，',
        '孤零零，只有狐鼠作陪。',
        '告诉我：',
        '你洪亮的嗓音谁造就？',
        '你动听的歌声又是谁师授？"',
        "",
        '"阁楼阴冷昏暗，',
        '身处高塔顶尖。',
        '我望穿风雨云层，',
        '目睹人世间痛苦、忧愁。',
        '我以智慧造化了美，',
        '如此歌唱，如此鸣奏，',
        '你会感到意外？"'
    ]

    print("\n🎤 小诺为您朗诵《钟之歌》")
    print("=" * 50)

    # 显示通知
    subprocess.run(['osascript', '-e', '''
        display notification "小诺正在为您朗诵《钟之歌》" with title "🎤 诗歌朗诵"
    '''])

    # 朗诵诗歌
    for line in poem_lines:
        if line.strip():
            print(f"📖 {line}")

            # 根据内容选择不同的声音
            if line == '"阁楼阴冷昏暗，':
                # 钟的回应使用另一个声音
                subprocess.run(['say', '-v', 'Mei-Jia', line])
            elif line.startswith('"'):
                # 引号内的内容使用另一个声音
                subprocess.run(['say', '-v', 'Mei-Jia', line])
            elif line == "作者：徐健":
                # 介绍使用标准声音
                subprocess.run(['say', '-v', 'Ting-Ting', line])
            else:
                # 诗句使用优美女声
                subprocess.run(['say', '-v', 'Ting-Ting', line])

            # 诗句之间适当停顿
            time.sleep(0.8 if not line.startswith('"') else 0.5)
        else:
            # 空行停顿时间更长
            time.sleep(1)

    print("\n✨ 朗诵完成！")
    print("这是一首充满哲思的佳作，感谢您的分享。")

if __name__ == "__main__":
    recite_clock_song()