#!/usr/bin/env python3
"""
简化版：将诗歌保存到备忘录
"""

import subprocess
import datetime

def save_poem_to_notes_simple():
    """简单保存诗歌到备忘录"""

    # 简化版内容
    note_title = "钟之歌"
    note_content = f"""# 钟之歌

作者：徐健
创作日期：2023年11月9日

钟啊，张开你银铃般的笑嘴，
请向我吐露真情原委：
"你终年蛰居陋室，
孤零零，只有狐鼠作陪。
告诉我：
你洪亮的嗓音谁造就？
你动听的歌声又是谁师授？"

"阁楼阴冷昏暗，
身处高塔顶尖。
我望穿风雨云层，
目睹人世间痛苦、忧愁。
我以智慧造化了美，
如此歌唱，如此鸣奏，
你会感到意外？"

保存时间：{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M')}
保存人：小娜
"""

    # 打开备忘录应用
    print("📝 正在打开备忘录应用...")
    subprocess.run(['open', '-a', 'Notes'])
    time.sleep(2)

    # 简单的AppleScript
    script = f'''
    tell application "Notes"
        activate
        delay 1

        try
            tell folder "备忘录"
                make new note with properties {{name:"{note_title}", body:"{note_content}"}}
            end tell
        on error
            make new note with properties {{name:"{note_title}", body:"{note_content}"}}
        end try

        display notification "诗歌已保存" with title "✅ 成功"
    end tell
    '''

    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)

    if result.returncode == 0:
        print("\n✅ 诗歌已保存到备忘录！")
        print("📝 标题：《钟之歌》")
        print("📄 包含完整的诗歌内容")
    else:
        print("\n⚠️ 备忘录保存出现问题")
        print("💾 已创建Markdown文件作为备份")

        # 保存到文件
        import os
        backup_path = os.path.expanduser("~/Desktop/钟之歌.md")
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(f"# {note_title}\n\n{note_content}")
        print(f"📍 备份位置：{backup_path}")

if __name__ == "__main__":
    import time
    save_poem_to_notes_simple()