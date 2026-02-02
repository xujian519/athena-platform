#!/usr/bin/env python3
"""
将诗歌保存到备忘录
"""

import subprocess
import datetime

def save_clock_song_to_notes():
    """保存钟之歌到备忘录"""

    # Markdown格式的诗歌内容
    note_title = "钟之歌"
    note_content = f"""# 钟之歌

**作者**：徐健
**创作日期**：2023年11月9日
**朗诵时间**：{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M')}
**来源**：小娜个人数据库

---

## 📝 原文

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

---

## 🎭 诗歌赏析

### 结构特点
- **对话体**：采用诗人与钟的对话形式
- **两段式**：提问与回答形成完整对话
- **象征手法**：钟象征着观察者和思考者

### 主题思想
- **孤独中的坚守**：钟虽身处高塔，却不停止歌唱
- **苦难与美的转化**：从人间苦难中提炼美的力量
- **智慧的内化**：通过观察获得深刻的生命感悟

### 艺术特色
- **意象丰富**：银铃般的嘴、高塔、风雨云层
- **哲理性强**：通过钟的语言传达人生智慧
- **语言优美**：既有古典韵味，又通俗易懂

---

## 💭 读后感

这首诗通过钟的视角，展现了：
1. **高度带来视野**：身处高塔，能看得更远
2. **苦难孕育智慧**：观察人间痛苦，才懂得创造美
3. **坚持的价值**：即使在孤独中，也要创造和歌唱

---

## 🏷️ 标签
#诗歌 #哲理 #智慧 #人生感悟 #原创作品

---
*由小娜智能助手整理保存*
*保存时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    # 打开备忘录应用
    print("📝 正在打开备忘录应用...")
    subprocess.run(['open', '-a', 'Notes'])
    time.sleep(2)

    # 转义特殊字符
    note_title_escaped = note_title.replace('"', '\\"')
    note_content_escaped = note_content.replace('"', '\\"')

    # 创建笔记
    script = f'''
    tell application "Notes"
        activate
        delay 1

        -- 获取或创建"诗歌"文件夹
        try
            set poetryFolder to folder "诗歌"
        on error
            set poetryFolder to make new folder with properties {{name:"诗歌"}}
        end try

        -- 创建新笔记
        tell poetryFolder
            make new note with properties {{_
                name:"{note_title_escaped}",_
                body:"{note_content_escaped}"_
            }}
        end tell

        display notification "《钟之歌》已保存到备忘录" with title "✅ 保存成功"
    end tell
    '''

    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)

    if result.returncode == 0:
        print("\n✅ 《钟之歌》已成功保存到备忘录！")
        print("📁 位置：备忘录 > 诗歌 文件夹")
        print("📝 包含完整的原文、赏析和读后感")
    else:
        print(f"\n❌ 保存失败：{result.stderr}")
        # 备用方案：保存到文件
        with open(f"/Users/xujian/Desktop/钟之歌_{datetime.datetime.now().strftime('%Y%m%d')}.md", 'w', encoding='utf-8') as f:
            f.write(f"# {note_title}\n\n{note_content}")
        print("\n💾 已保存到桌面作为备份")

if __name__ == "__main__":
    import time
    save_clock_song_to_notes()