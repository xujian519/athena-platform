#!/usr/bin/env python3
"""
创建中国骈文选数据库结构
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


def create_pianwen_database() -> Any:
    """创建骈文数据库结构"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 创建专门的骈文表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pianwen_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number INTEGER UNIQUE,
            title TEXT,
            author TEXT,
            dynasty TEXT,
            content TEXT,
            content_length INTEGER,
            source_url TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # 100篇文章的标题列表
    pianwen_list = [
        # 1-10
        {"number": 1, "title": "狱中上梁王书", "author": "邹阳", "dynasty": "西汉"},
        {"number": 2, "title": "上书谏吴王", "author": "枚乘", "dynasty": "西汉"},
        {"number": 3, "title": "喻巴蜀檄", "author": "司马相如", "dynasty": "西汉"},
        {"number": 4, "title": "为幽州牧与彭宠书", "author": "班固", "dynasty": "东汉"},
        {"number": 5, "title": "郭有道碑", "author": "蔡邕", "dynasty": "东汉"},
        {"number": 6, "title": "为袁绍檄豫州", "author": "陈琳", "dynasty": "东汉"},
        {"number": 7, "title": "典论论文", "author": "曹丕", "dynasty": "三国"},
        {"number": 8, "title": "与吴质书", "author": "曹丕", "dynasty": "三国"},
        {"number": 9, "title": "与杨德祖书", "author": "曹丕", "dynasty": "三国"},
        {"number": 10, "title": "求自试表", "author": "曹植", "dynasty": "三国"},
        # 11-20
        {"number": 11, "title": "博弈论", "author": "应璩", "dynasty": "三国"},
        {"number": 12, "title": "与山巨源绝交书", "author": "嵇康", "dynasty": "三国"},
        {"number": 13, "title": "陈情表", "author": "李密", "dynasty": "西晋"},
        {"number": 14, "title": "酒德颂", "author": "刘伶", "dynasty": "西晋"},
        {"number": 15, "title": "东方朔画赞", "author": "夏侯湛", "dynasty": "西晋"},
        {"number": 16, "title": "剑阁铭", "author": "张载", "dynasty": "西晋"},
        {"number": 17, "title": "马督诔（并序）", "author": "陆机", "dynasty": "西晋"},
        {"number": 18, "title": "钱神论", "author": "鲁褒", "dynasty": "西晋"},
        {"number": 19, "title": "吊魏武帝文", "author": "陆机", "dynasty": "西晋"},
        {"number": 20, "title": "演连珠", "author": "陆机", "dynasty": "西晋"},
        # 21-30
        {"number": 21, "title": "答卢谌书", "author": "刘琨", "dynasty": "西晋"},
        {"number": 22, "title": "晋纪总论", "author": "干宝", "dynasty": "东晋"},
        {"number": 23, "title": "兰亭集序", "author": "王羲之", "dynasty": "东晋"},
        {"number": 24, "title": "与子俨等疏", "author": "陶渊明", "dynasty": "东晋"},
        {"number": 25, "title": "归去来兮辞", "author": "陶渊明", "dynasty": "东晋"},
        {"number": 26, "title": "陶征士诔", "author": "颜延之", "dynasty": "南朝宋"},
        {"number": 27, "title": "登大雷岸与妹书", "author": "鲍照", "dynasty": "南朝宋"},
        {"number": 28, "title": "芜城赋", "author": "鲍照", "dynasty": "南朝宋"},
        {"number": 29, "title": "别赋", "author": "江淹", "dynasty": "南朝齐"},
        {"number": 30, "title": "北山移文", "author": "孔稚圭", "dynasty": "南朝齐"},
        # 31-40
        {"number": 31, "title": "物色", "author": "刘勰", "dynasty": "南朝梁"},
        {"number": 32, "title": "情采", "author": "刘勰", "dynasty": "南朝梁"},
        {"number": 33, "title": "答谢中书书", "author": "陶弘景", "dynasty": "南朝梁"},
        {"number": 34, "title": "奏弹曹景宗", "author": "任昉", "dynasty": "南朝梁"},
        {"number": 35, "title": "广绝交论", "author": "刘峻", "dynasty": "南朝梁"},
        {"number": 36, "title": "送桔启", "author": "吴均", "dynasty": "南朝梁"},
        {"number": 37, "title": "与陈伯之书", "author": "丘迟", "dynasty": "南朝梁"},
        {"number": 38, "title": "与顾章书", "author": "吴均", "dynasty": "南朝梁"},
        {"number": 39, "title": "文选序", "author": "萧统", "dynasty": "南朝梁"},
        {"number": 40, "title": "郑众论", "author": "萧统", "dynasty": "南朝梁"},
        # 41-50
        {"number": 41, "title": "文章（节录）", "author": "萧统", "dynasty": "南朝梁"},
        {"number": 42, "title": "在北齐与杨仆射书", "author": "颜之推", "dynasty": "北齐"},
        {"number": 43, "title": "与周处士书", "author": "颜之推", "dynasty": "北齐"},
        {"number": 44, "title": "哀江南赋序", "author": "庾信", "dynasty": "北周"},
        {"number": 45, "title": "思旧铭", "author": "庾信", "dynasty": "北周"},
        {"number": 46, "title": "为李密檄洛州文", "author": "庾信", "dynasty": "北周"},
        {"number": 47, "title": "谏太宗十思疏", "author": "魏征", "dynasty": "唐"},
        {"number": 48, "title": "与博昌父老书", "author": "骆宾王", "dynasty": "唐"},
        {"number": 49, "title": "代李敬业传檄天下文", "author": "骆宾王", "dynasty": "唐"},
        {"number": 50, "title": "滕王阁序", "author": "王勃", "dynasty": "唐"},
        # 51-60
        {"number": 51, "title": "宋公遗爱碑颂", "author": "王勃", "dynasty": "唐"},
        {"number": 52, "title": "请诛安禄山疏", "author": "颜真卿", "dynasty": "唐"},
        {"number": 53, "title": "送秘书晁监还日本国诗序", "author": "王维", "dynasty": "唐"},
        {"number": 54, "title": "春夜宴从弟桃花园序", "author": "李白", "dynasty": "唐"},
        {"number": 55, "title": "吊古战场文", "author": "李白", "dynasty": "唐"},
        {"number": 56, "title": "奉天请罢琼林大盈二库状", "author": "陆贽", "dynasty": "唐"},
        {"number": 57, "title": "奉天改元大赦制", "author": "陆贽", "dynasty": "唐"},
        {"number": 58, "title": "论两河及淮西利害状（节选）", "author": "陆贽", "dynasty": "唐"},
        {"number": 59, "title": "睢阳庙碑并序", "author": "韩愈", "dynasty": "唐"},
        {"number": 60, "title": "陋室铭", "author": "刘禹锡", "dynasty": "唐"},
        # 61-70
        {"number": 61, "title": "阿房宫赋", "author": "杜牧", "dynasty": "唐"},
        {"number": 62, "title": "上河东公启", "author": "杜牧", "dynasty": "唐"},
        {"number": 63, "title": "上令狐相公状", "author": "杜牧", "dynasty": "唐"},
        {"number": 64, "title": "会昌一品集序", "author": "李商隐", "dynasty": "唐"},
        {"number": 65, "title": "祭小侄女寄寄文", "author": "李商隐", "dynasty": "唐"},
        {"number": 66, "title": "又玄集序", "author": "皮日休", "dynasty": "唐"},
        {"number": 67, "title": "祭王平甫文", "author": "王安石", "dynasty": "北宋"},
        {"number": 68, "title": "本朝百年无事札子", "author": "苏辙", "dynasty": "北宋"},
        {"number": 69, "title": "吕惠卿责授建宁军节度副使本州安置不得签书公事", "author": "苏轼", "dynasty": "北宋"},
        {"number": 70, "title": "隆佑太后告天下手书", "author": "苏轼", "dynasty": "北宋"},
        # 71-80
        {"number": 71, "title": "瘗鹤铭", "author": "苏轼", "dynasty": "北宋"},
        {"number": 72, "title": "黄州快哉亭记", "author": "苏轼", "dynasty": "北宋"},
        {"number": 73, "title": "滕王阁赋", "author": "苏轼", "dynasty": "北宋"},
        {"number": 74, "title": "祭陈同甫文", "author": "苏轼", "dynasty": "北宋"},
        {"number": 75, "title": "贺赵侍郎月山启", "author": "苏轼", "dynasty": "北宋"},
        {"number": 76, "title": "杂说", "author": "苏轼", "dynasty": "北宋"},
        {"number": 77, "title": "与王元羲先生书", "author": "黄庭坚", "dynasty": "北宋"},
        {"number": 78, "title": "东方大中集题辞", "author": "黄庭坚", "dynasty": "北宋"},
        {"number": 79, "title": "复郎廷佐书", "author": "黄庭坚", "dynasty": "北宋"},
        {"number": 80, "title": "复沈九康成书", "author": "黄庭坚", "dynasty": "北宋"},
        # 81-90
        {"number": 81, "title": "上龚芝麓先生书", "author": "黄庭坚", "dynasty": "北宋"},
        {"number": 82, "title": "三芝集序", "author": "黄庭坚", "dynasty": "北宋"},
        {"number": 83, "title": "聊斋自志", "author": "蒲松龄", "dynasty": "清"},
        {"number": 84, "title": "席方平・判词", "author": "蒲松龄", "dynasty": "清"},
        {"number": 85, "title": "寄所亲书", "author": "蒲松龄", "dynasty": "清"},
        {"number": 86, "title": "芙蓉女儿诔", "author": "曹雪芹", "dynasty": "清"},
        {"number": 87, "title": "与蒋苕生书", "author": "袁枚", "dynasty": "清"},
        {"number": 88, "title": "余杭诸葛武侯庙碑", "author": "袁枚", "dynasty": "清"},
        {"number": 89, "title": "哀盐船文并序", "author": "袁枚", "dynasty": "清"},
        {"number": 90, "title": "经旧苑吊马守贞文", "author": "袁枚", "dynasty": "清"},
        # 91-100
        {"number": 91, "title": "汉土琴台之铭并序", "author": "袁枚", "dynasty": "清"},
        {"number": 92, "title": "狐父之盗颂", "author": "袁枚", "dynasty": "清"},
        {"number": 93, "title": "冬青树乐府序", "author": "袁枚", "dynasty": "清"},
        {"number": 94, "title": "与孙季逑书", "author": "袁枚", "dynasty": "清"},
        {"number": 95, "title": "七招", "author": "袁枚", "dynasty": "清"},
        {"number": 96, "title": "答张水屋书", "author": "袁枚", "dynasty": "清"},
        {"number": 97, "title": "洪稚存同年机声灯影图序", "author": "袁枚", "dynasty": "清"},
        {"number": 98, "title": "为胜国阎陈二公征诗启", "author": "袁枚", "dynasty": "清"},
        {"number": 99, "title": "四六丛话后序", "author": "袁枚", "dynasty": "清"},
        {"number": 100, "title": "秋醒词序", "author": "袁枚", "dynasty": "清"}
    ]

    # 批量插入文章信息
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for article in pianwen_list:
        cursor.execute("""
            INSERT OR REPLACE INTO pianwen_articles
            (number, title, author, dynasty, content_length, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            article['number'],
            article['title'],
            article['author'],
            article['dynasty'],
            0,  # 初始长度为0，获取内容后更新
            current_time,
            current_time
        ))

    conn.commit()
    conn.close()

    print('✅ 中国骈文选数据库已创建！')
    print(f'✅ 预设了 {len(pianwen_list)} 篇文章的信息')
    print('\n📊 朝代分布：')
    dynasties = {}
    for article in pianwen_list:
        dynasty = article['dynasty']
        dynasties[dynasty] = dynasties.get(dynasty, 0) + 1

    for dynasty, count in sorted(dynasties.items()):
        print(f'  - {dynasty}: {count}篇')

if __name__ == "__main__":
    create_pianwen_database()
