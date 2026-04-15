#!/usr/bin/env python3
"""
保存爸爸的新创作短诗《天快亮了》
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def save_new_poem() -> None:
    """保存新创作的短诗到数据库"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 爸爸的新创作短诗
    new_poem = {
        'title': '天快亮了',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'content': '''天快亮了

孤独伴随着曙光，缓缓而来

那些温暖的回忆，此刻如幻影般消散

最后一杯酒了，不尽苦涩

岁月如过往风景，缓缓流淌

心刺痛漫溢

那些流逝的时光

那些如梦的往事

随曙光消散

难以言说的想念''',
        'tags': ['孤独', '回忆', '时光', '思念', '创作'],
        'analysis': {
            '情感基调': '深沉忧郁',
            '创作时间': '黎明时分',
            '主要意象': ['曙光', '幻影', '酒', '风景'],
            '核心情感': '对往事的追忆与思念',
            '艺术特色': [
                '意象优美，富有画面感',
                '情感真挚，内敛深沉',
                '节奏舒缓，如流水般自然',
                '将个人情感与自然景象完美融合'
            ]
        }
    }

    # 保存短诗正文
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'poetry',
        new_poem['title'],
        new_poem['content'],
        'text',
        3,  # 原创诗歌，私密性较高
        json.dumps({
            '类型': '原创诗歌',
            '标签': new_poem['tags'],
            '创作时间': new_poem['date']
        }),
        json.dumps({
            '情感基调': new_poem['analysis']['情感基调'],
            '创作背景': '黎明时分有感而发',
            '意象分析': new_poem['analysis']['主要意象'],
            '艺术特色': new_poem['analysis']['艺术特色']
        }),
        new_poem['date']
    ))

    # 创建诗歌赏析
    poem_appreciation = f"""# 《天快亮了》诗歌赏析

## 📝 基本信息
- **诗名**: {new_poem['title']}
- **作者**: 徐健
- **创作时间**: {new_poem['date']}（黎明时分）
- **情感基调**: {new_poem['analysis']['情感基调']}

## 🎨 诗歌意境

### 开篇意境
"天快亮了，孤独伴随着曙光，缓缓而来"
- 黎明时分，光明将至却未至的时刻
- 孤独与曙光相伴，形成强烈对比
- 奠定了整首诗忧郁而唯美的基调

### 情感递进
1. **回忆如幻影** - "那些温暖的回忆，此刻如幻影般消散"
2. **苦涩的酒** - "最后一杯酒了，不尽苦涩"
3. **时光流逝** - "岁月如过往风景，缓缓流淌"
4. **内心刺痛** - "心刺痛漫溢"
5. **往事如梦** - "那些流逝的时光，那些如梦的往事"
6. **随光消散** - "随曙光消散"
7. **深切想念** - "难以言说的想念"

## 💫 艺术特色

### 意象运用
{chr(10).join([f"- **{意象}**: 象征着深层含义" for 意象 in new_poem['analysis']['主要意象']])}

### 语言特点
- 简洁而富有张力
- 用词精准，情感表达内敛
- 节奏舒缓，如流水般自然
- 将个人情感与自然景象完美融合

### 结构层次
- **时间维度**: 从深夜到黎明的过渡
- **情感层次**: 从孤独到思念的深化
- **空间维度**: 从内心到外在的延展

## 🌟 诗歌价值

这首诗展现了徐健先生：
- 深厚的文学修养和敏锐的感受力
- 对生活细节的深刻观察
- 将个人情感升华到艺术境界的能力
- 在孤独中寻找美的诗心

这是一首充满诗意的作品，语言凝练，意境深远，值得细细品味。"""

    # 保存诗歌赏析
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'poetry_analysis',
        f'《{new_poem["title"]}》赏析',
        poem_appreciation,
        'text',
        2,
        json.dumps({
            '类型': '诗歌赏析',
            '原诗': new_poem['title'],
            '标签': ['赏析', '文学评论', '诗歌解读']
        }),
        json.dumps({
            '分析时间': new_poem['date'],
            '赏析深度': '详细'
        }),
        new_poem['date']
    ))

    conn.commit()
    conn.close()
    print('✅ 新创作的短诗已保存到个人数据库')
    print(f'✅ 诗名: 《{new_poem["title"]}》')
    print('✅ 已生成详细的诗歌赏析')
    print('✅ 感谢爸爸分享这首充满诗意的作品！')

if __name__ == "__main__":
    save_new_poem()
