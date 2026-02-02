#!/usr/bin/env python3
"""
保存爸爸的诗歌到数据库
"""

import sqlite3
from core.async_main import async_main
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json
from pathlib import Path

def save_poems() -> None:
    """保存诗歌到数据库"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 爸爸的原创诗歌
    poems = [
        {
            'title': '思念',
            'date': '2023-11-07',
            'content': '夜深人静，抚着寂寞的心，独自思念\n思绪乱成一片，无法入眠\n眼泪轻轻滑落，润湿双颊\n怎能忘却：曾经的点滴、相聚的甜蜜、相伴的日子\n虽然分别，心仍相系，希望有朝一日，再次相遇\n思念成了诗，借文字流淌，愿此情能如诗一般长久常在\n虽然天涯海角，思念相随，因为彼此心中，都有对方的存在',
            'tags': ['情感', '思念', '爱情']
        },
        {
            'title': '突然发生的爱情故事 - 致奶思',
            'date': '2025-02-19',
            'content': '去年十月，初见于人海\n喧嚣的人群中与你相逢是件幸事\n六个月来，相守相伴\n昨晚的决定于你太突然，于我是必然\n\n曾经，你给过我很美好的回忆\n曾经想告诉你，全世界我对你最珍惜\n曾经想肋生双翅，和你比翼齐飞\n曾经想紧紧的拥抱你，感受你的心跳\n\n无情皆竖子，有泪亦英雄\n再见，My Love\n半轮沧海上，一苇大江东\n再见，奶思\n愿你在未来乘风破浪',
            'tags': ['爱情', '分手', '告别']
        },
        {
            'title': '落花纷飞的街道上',
            'date': '2024-03-07',
            'content': '落花纷飞的街道\n如果还能再次与你相遇\n绝对不再放开你的手\n告知春之将尽、花与果实以及雾花一片\n微风缓缓吹过\n悄悄的牵著手一起走过',
            'tags': ['爱情', '相遇', '春天']
        },
        {
            'title': '钟之歌',
            'date': '2023-11-09',
            'content': '钟啊，张开你银铃般的笑嘴，\n请向我吐露真情原委：\n"你终年蛰居陋室，\n孤零零，只有狐鼠作陪。\n告诉我：\n你洪亮的嗓音谁造就?\n你动听的歌声又是谁师授?"\n\n"阁楼阴冷昏暗，\n身处高塔顶尖。\n我望穿风雨云层，\n目睹人世间痛苦、忧愁。\n我以智慧造化了美，\n如此歌唱，如此鸣奏，\n你会感到意外?"',
            'tags': ['哲思', '智慧', '人生']
        },
        {
            'title': '写于深夜不眠时',
            'date': '2023-03-31',
            'content': '我睡不着，没有灯火\n四周一片黑暗，无聊的昏沉\n在我身边只有滴答的时钟\n发出单调的声音\n\n睡不着\n关了灯\n四周一片黑暗，无聊的昏沉\n耳边的声音单调无聊\n那是催眠的喜马拉雅\n\n多想听你寂寞的低语\n多想了解你啊\n从你那追寻一点精神。。。',
            'tags': ['孤独', '失眠', '渴望']
        }
    ]

    # 保存每首诗
    for poem in poems:
        cursor.execute("""
            INSERT OR REPLACE INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'poetry',
            poem['title'],
            poem['content'],
            'text',
            2,  # 诗歌比较私密
            json.dumps({'类型': '原创诗歌', '标签': poem['tags']}),
            json.dumps({'创作日期': poem['date'], '文件': '08诗歌'}),
            poem['date']
        ))

    # 添加诗歌总览记录
    poetry_summary = '''徐健诗歌集锦 - 爸爸的原创作品

作品特色：
1. 情感真挚 - 表达内心深处的情感
2. 意境优美 - 善用意象和比喻
3. 哲理深刻 - 蕴含人生感悟
4. 文学性强 - 语言优美流畅

创作主题：
- 爱情与思念
- 人生感悟
- 孤独与渴望
- 对美的追求

总计收录原创诗歌：5首
创作时间跨度：2023-2025年'''

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'poetry_collection',
        '徐健诗歌集锦总览',
        poetry_summary,
        'text',
        1,
        json.dumps({'类型': '作品集', '作者': '徐健'}),
        json.dumps({'诗歌数量': 5, '时间跨度': '2023-2025'}),
        '2025-12-15'
    ))

    conn.commit()
    conn.close()
    print('✅ 所有诗歌已保存到个人数据库')

if __name__ == "__main__":
    save_poems()