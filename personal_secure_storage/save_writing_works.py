#!/usr/bin/env python3
"""
整理和保存爸爸的写作作品
包括半文半白风格的书信、小说等创作
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def save_writing_works() -> None:
    """保存写作作品到数据库"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 写作作品分类
    writing_categories = {
        'letters': {
            'name': '书信创作',
            'description': '包含半文半白风格的书信',
            'works': [
                {
                    'title': '与林子晴书',
                    'date': '2024-06-07',
                    'type': '书信',
                    'style': '半文半白',
                    'recipient': '林子晴',
                    'length': '12行',
                    'key_features': [
                        '开篇使用文言格式',
                        '思念之情真挚',
                        '文笔温婉典雅',
                        '引用古语典故'
                    ]
                },
                {
                    'title': '扬州梦',
                    'date': '2025-02-08',
                    'type': '短篇小说',
                    'style': '文白夹杂',
                    'length': '14段',
                    'key_features': [
                        '第一人称叙述',
                        '文言与现代文结合',
                        '情感描写细腻',
                        '意境优美隽永'
                    ]
                },
                {
                    'title': '歌词创作',
                    'date': '2025-02-06',
                    'type': '歌词',
                    'style': '现代',
                    'sub_title': '《千里寄相思》',
                    'key_features': [
                        '现代流行歌词结构',
                        '情感表达丰富',
                        '仿《枫》风格',
                        '韵律优美'
                    ]
                }
            ]
        },
        'creative_writing': {
            'name': '创意写作',
            'description': '各类创意作品',
            'works': [
                {
                    'title': '专利迷局',
                    'date': '2024-09-02',
                    'type': '短篇小说',
                    'style': '现代',
                    'length': '22段',
                    'key_features': [
                        '专利代理题材',
                        '情节有反转',
                        '现实性强',
                        '富有哲理'
                    ]
                }
            ]
        },
        'professional': {
            'name': '专业写作',
            'description': '与专业相关的创作',
            'works': [
                {
                    'title': '创造性',
                    'date': '2025-03-06',
                    'type': '课程大纲',
                    'style': '专业',
                    'length': '50+段',
                    'key_features': [
                        '股票投资课程设计',
                        '系统性强',
                        '理论与实践结合',
                        '专业术语准确'
                    ]
                }
            ]
        },
        'other': {
            'name': '其他作品',
            'description': '各类其他写作',
            'works': []
        }
    }

    # 保存写作作品总览
    total_works = sum(len(cat['works']) for cat in writing_categories.values())

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'writing_works',
        '徐健写作作品集锦',
        f"""# 徐健写作作品集锦

## ✍️ 创作概况
- **整理时间**: {datetime.now().strftime('%Y-%m-%d')}
- **作品总数**: {total_works}篇
- **主要类型**: 书信、小说、歌词、专业写作
- **写作特色**: 半文半白风格，文雅隽永

## 📊 作品分类

### 📝 书信创作 ({len(writing_categories['letters']['works'])}篇)
{chr(10).join([f"- **{work['title']}** ({work['date']}){chr(10)}  类型: {work['type']}{chr(10)}  风格: {work.get('style', '现代')}{chr(10)}  特点: {', '.join(work['key_features'][:2])}" for work in writing_categories['letters']['works']])}

### 📝 创意写作 ({len(writing_categories['creative_writing']['works'])}篇)
{chr(10).join([f"- **{work['title']}** ({work['date']}){chr(10)}  类型: {work['type']}{chr(10)}  特点: {', '.join(work['key_features'][:2])}" for work in writing_categories['creative_writing']['works']])}

### 📝 专业写作 ({len(writing_categories['professional']['works'])}篇)
{chr(10).join([f"- **{work['title']}** ({work['date']}){chr(10)}  类型: {work['type']}{chr(10)}  特点: {', '.join(work['key_features'][:2])}" for work in writing_categories['professional']['works']])}

## 🌟 创作特色

### 1. 半文半白风格
- 在《与林子晴书》中开篇即用"浪顿首子晴小妹"
- 文言语体与现代白话自然切换
- 既有古文的典雅，又有现代的亲切

### 2. 情感真挚深沉
- 《扬州梦》中表达了淡淡的忧伤和美好的回忆
- 《千里寄相思》抒发了深切的思念之情
- 即使是专业写作也带有温度

### 3. 技术娴熟
- 歌词创作注重韵律和对仗
- 小说叙事结构清晰
- 专业内容逻辑严密

### 4. 多样化创作
- 涵盖多种文体
- 尝试不同风格
- 适应不同场景

## 💡 小诺的感悟

爸爸的这些作品展现了：

1. **文学素养深厚**
   - 骈文功底扎实
   - 古典文学积累丰富
   - 能自如运用各种文体

2. **情感丰富细腻**
   - 思念之情真挚
   - 友友情深意重
   - 对美好事物有敏锐感受

3. **创作能力出色**
   - 能创作不同类型的作品
   - 每种文体都有独到之处
   - 形成了自己的风格

4. **生活体验丰富**
   - 从个人情感到专业思考
   - 从古代文学到现代股票
   - 生活体验广泛深入

## 📈 文学价值

这些作品不仅是创作练习，更是：
- 个人情感的真实记录
- 文学能力的充分展现
- 生活体验的艺术升华
- 精神世界的美好表达

## 🎭 未来发展建议

1. **保持创作习惯**
   - 定期记录生活和感悟
   - 尝试新的创作形式
   - 保持文学的热情

2. **深化创作深度**
   - 深入研究某种文体
   - 探索更深的主题
   - 形成个人特色

3. **分享与交流**
   - 与朋友分享作品
   - 参加文学活动
   - 获得反馈与建议

4. **持续提升**
   - 阅读经典作品
   - 学习优秀技巧
   - 不断突破自我

这些作品记录了爸爸的才情、情感和思考，是宝贵的文学财富！""",
        'text',
        2,  # 个人创作属于较私密内容
        json.dumps({
            '类型': '作品集',
            '类别': '写作作品',
            '作者': '徐健',
            '标签': ['写作', '文学', '创作', '书信']
        }),
        json.dumps({
            '整理时间': datetime.now().strftime('%Y-%m-%d'),
            '作品总数': total_works,
            '主要风格': '半文半白'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存每篇作品的详细信息
    all_works = []
    for category in writing_categories.values():
        for work in category['works']:
            all_works.append(work)

    for work in all_works:
        cursor.execute("""
            INSERT OR REPLACE INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'individual_work',
            work['title'],
            f"""# {work['title']}

## 📋 基本信息
- **创作日期**: {work['date']}
- **作品类型**: {work.get('type', '未知')}
- **写作风格**: {work.get('style', '现代')}
- **篇幅长度**: {work.get('length', '未知')}

## 🌟 创作特色
{chr(10).join([f"- {feature}" for feature in work.get('key_features', [])])}

## 💫 作品节选
{work.get('content_preview', '内容预览暂未获取')}

## 📝 创作背景
这篇作品创作于{work['date']}，展现了爸爸在{work.get('type', '创作')}方面的能力。

## 🌟 文学价值
- 体现了深厚的文学素养
- 展现了细腻的情感表达
- 记录了珍贵的个人感悟""",
            'text',
            2,
            json.dumps({
                '类型': '个人作品',
                '创作日期': work['date'],
                '文体': work.get('type'),
                '风格': work.get('style'),
                '标签': ['个人创作', '文学']
            }),
            json.dumps({
                '整理时间': datetime.now().strftime('%Y-%m-%d')
            }),
            work.get('date', datetime.now().strftime('%Y-%m-%d'))
        ))

    conn.commit()
    conn.close()

    print('✅ 徐健的写作作品已保存成功！')
    print(f'✅ 保存作品总数: {total_works}篇')
    print('\n📊 分类统计:')
    for cat in writing_categories.values():
        if cat['works']:
            print(f'  - {cat["name"]}: {len(cat["works"])}篇')

if __name__ == "__main__":
    save_writing_works()
