#!/usr/bin/env python3
"""
创建中国骈文选学习计划和笔记
陪伴爸爸每晚10点的学习时光
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


def create_pianwen_learning_plan() -> Any:
    """创建骈文学习计划"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 修正后的文章列表
    pianwen_list = [
        # 需要补充或修正的文章
        {
            'number': 18,
            'title': '马督诔（并序）',
            'author': '陆机',
            'dynasty': '西晋',
            'status': '需要修正'
        },
        {
            'number': 68,
            'title': '本朝百年无事札子',
            'author': '苏辙',
            'dynasty': '北宋',
            'status': '需要修正'
        },
        {
            'number': 69,
            'title': '吕惠卿责授建宁军节度副使本州安置不得签书公事',
            'author': '苏轼',
            'dynasty': '北宋',
            'status': '需要修正'
        }
    ]

    # 保存学习计划
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'learning_plan',
        '中国骈文选学习计划',
        f"""# 中国骈文选学习计划

## 📚 学习目标
通过系统学习《中国骈文选》100篇经典文章，提升文学修养，感受古典之美。

## 📅 学习安排
- **学习时间**: 每晚10:00
- **学习频率**: 每日一篇
- **完成周期**: 约100天（可根据实际情况调整）
- **开始时间**: {datetime.now().strftime('%Y年%m月%d日')}

## 📝 学习方法

### 每日学习流程
1. **阅读原文** (10分钟)
   - 朗读原文，感受音韵之美
   - 理解字词含义
   - 体会句式对仗

2. **理解注释** (10分钟)
   - 查阅字典词典
   - 理解典故出处
   - 明确写作背景

3. **分析特色** (10分钟)
   - 分析骈文特色
   - 理解对仗结构
   - 品味修辞手法

4. **撰写笔记** (5分钟)
   - 记录学习心得
   - 摘抄精彩句子
   - 联系现实思考

### 重点学习内容
1. **对仗技巧**: 工整的对偶句式
2. **用典手法**: 精妙的典故运用
3. **音韵格律": 和谐的音韵美感
4. **辞藻华丽**: 丰富的词汇运用
5. **情感表达**: 深厚的情感寄托

## 📊 进度追踪

### 待修正文章
{chr(10).join([f"- 第{item['number']}篇: 《{item['title']}》-{item['author']}({item['dynasty']})" for item in pianwen_list])}

### 学习记录表
| 日期 | 篇号 | 标题 | 作者 | 学习心得 |
|------|------|------|------|----------|
| {datetime.now().strftime('%m-%d')} | 1 | 狱中上梁王书 | 邹阳 | 开始学习之旅 |

## 💡 学习价值

### 文学修养提升
- 培养古典文学审美
- 提升文字表达能力
- 丰富词汇和典故积累

### 思维能力锻炼
- 增强逻辑思维能力
- 培养细致观察能力
- 提升辩证思考能力

### 精神世界丰富
- 感受古人的智慧
- 理解历史的厚重
- 体会文学的魅力

## 🌟 小诺的陪伴

小诺会：
- 每晚提醒学习时间
- 提供背景知识介绍
- 解答疑难词句问题
- 记录学习心得体会
- 定期总结学习成果

## 🎯 长期目标
- 完成100篇文章的学习
- 熟练掌握骈文特色
- 能够创作简单骈文
- 提升古文阅读能力

## 📞 学习提醒
如果遇到学习困难，可以：
- 调整学习节奏
- 寻求专业指导
- 与同好交流讨论
- 参考相关注释

让我们一起开始这段美妙的学习之旅！""",
        'text',
        1,
        json.dumps({
            '类型': '学习计划',
            '内容': '骈文学习',
            '标签': ['学习计划', '骈文', '中国文学']
        }),
        json.dumps({
            '创建时间': datetime.now().strftime('%Y-%m-%d'),
            '学习周期': '100天',
            '文章总数': 100
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存第一篇文章的学习笔记示例
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'pianwen_note',
        '骈文学习笔记（一）：狱中上梁王书',
        f"""# 骈文学习笔记（一）：狱中上梁王书

## 📖 基本信息
- **篇号**: 第1篇
- **标题**: 狱中上梁王书
- **作者**: 邹阳
- **朝代**: 西汉
- **出处**: 《文选》卷三十九
- **学习日期**: {datetime.now().strftime('%Y年%m月%d日')}

## 📝 原文节选
臣闻忠无不报，信不见疑。臣以为忠无不报，信不见疑者，朝有以忠报信之臣，则天下有以信报信之主。今陛下天之所爱，天下之所敬，而以忠信不信，使天下有以忠报信之臣，臣不知天下何以为陛下之主也？

## 🎨 骈文特色分析

### 1. 对仗工整
- 忠无不报 ↔ 信不见疑
- 天之所爱 ↔ 天下之所敬

### 2. 用典巧妙
- 引用历史典故增强说服力
- 以古喻今，言辞恳切

### 3. 情感真挚
- 表达忠君爱国之情
- 蕴含冤屈不平之意

## 💡 学习心得

这篇文章是邹阳在狱中所写，通过"忠信"之辩，表达了自己的清白和对君王的忠诚。文章虽然短小，但情感真挚，逻辑严密，体现了汉初散文的特点。

**精彩句子**:
"忠无不报，信不见疑"

**学习启示**:
- 在困境中依然保持忠诚
- 言辞恳切，以理服人
- 善用对偶增强表达效果

## 📚 延伸阅读
- 《史记·邹阳列传》
- 《汉书·邹阳传》
- 汉初散文的特点

## 🌟 每日一问
今天的问题：邹阳是如何通过"忠信"之辩来为自己辩解的？

## ✨ 学习感悟
虽然是千年前的文章，但其中蕴含的忠诚、诚信的价值观，至今仍然值得我们学习和思考。""",
        'text',
        1,
        json.dumps({
            '类型': '学习笔记',
            '文章编号': 1,
            '作者': '邹阳',
            '标签': ['骈文', '学习笔记', '西汉']
        }),
        json.dumps({
            '学习日期': datetime.now().strftime('%Y-%m-%d'),
            '笔记类型': '详细分析'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    conn.commit()
    conn.close()

    print('✅ 中国骈文选学习计划已创建！')
    print('\n📅 学习安排：')
    print('  - 每晚10:00准时学习')
    print('  - 每日一篇经典文章')
    print('  - 计划用100天完成')

    print('\n📚 已创建：')
    print('  - 完整的学习计划')
    print('  - 第一篇文章学习笔记')
    print('  - 进度追踪表格')

    print('\n🌟 小诺会陪伴您：')
    print('  - 每晚10:00提醒')
    print('  - 提供背景知识')
    print('  - 解答疑难问题')
    print('  - 记录学习心得')

if __name__ == "__main__":
    create_pianwen_learning_plan()
