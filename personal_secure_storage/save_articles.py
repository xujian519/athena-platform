#!/usr/bin/env python3
"""
保存爸爸的专业文章到数据库
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def save_articles() -> None:
    """保存专业文章到数据库"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 文章列表和信息
    articles = [
        {
            'file_name': '关于假冒专利的刑事责任 .pages',
            'title': '关于假冒专利的刑事责任',
            'date': '2020-06-27',
            'category': '专利刑法',
            'keywords': ['假冒专利', '刑事责任', '专利法'],
            'description': '探讨假冒专利行为的刑事责任认定和相关法律适用问题'
        },
        {
            'file_name': '判决要点摘编.pages',
            'title': '判决要点摘编',
            'date': '2020-05-20',
            'category': '案例研究',
            'keywords': ['判决要点', '案例分析', '司法实践'],
            'description': '知识产权相关判决的要点总结和提炼'
        },
        {
            'file_name': '朋友圈发布信息是否构成专利法中的现有技术.pages',
            'title': '朋友圈发布信息是否构成专利法中的现有技术',
            'date': '2020-04-28',
            'category': '专利现有技术',
            'keywords': ['朋友圈', '现有技术', '社交媒体', '专利新颖性'],
            'description': '分析社交媒体信息对专利新颖性的影响'
        },
        {
            'file_name': '以"揉面机案"为例，再谈专利撰写 .pages',
            'title': '以"揉面机案"为例，再谈专利撰写',
            'date': '2020-05-18',
            'category': '专利撰写',
            'keywords': ['揉面机案', '专利撰写', '案例分析', '权利要求'],
            'description': '通过具体案例深入讲解专利撰写的要点和技巧'
        },
        {
            'file_name': '专利布局之布局层次.pages',
            'title': '专利布局之布局层次',
            'date': '2020-05-13',
            'category': '专利布局',
            'keywords': ['专利布局', '布局层次', '专利战略', '知识产权管理'],
            'description': '系统阐述专利布局的不同层次和实施策略'
        },
        {
            'file_name': '专利布局之甲方与乙方 .pages',
            'title': '专利布局之甲方与乙方',
            'date': '2020-05-13',
            'category': '专利布局',
            'keywords': ['专利布局', '甲方乙方', '客户需求', '服务提供'],
            'description': '从甲方和乙方两个角度分析专利布局的实施要点'
        },
        {
            'file_name': '专利行政诉讼的起诉期限 .pages',
            'title': '专利行政诉讼的起诉期限',
            'date': '2020-05-01',
            'category': '行政诉讼',
            'keywords': ['行政诉讼', '起诉期限', '专利复审', '专利无效'],
            'description': '详细分析专利行政诉讼中的起诉期限问题'
        },
        {
            'file_name': '苹方简.pages',
            'title': '苹方简',
            'date': '2021-01-30',
            'category': '其他',
            'keywords': ['苹方', '字体', '简体'],
            'description': '关于苹方简体的相关说明'
        }
    ]

    # 按年份统计
    articles_by_year = {}
    for article in articles:
        year = article['date'][:4]
        if year not in articles_by_year:
            articles_by_year[year] = []
        articles_by_year[year].append(article)

    # 按分类统计
    articles_by_category = {}
    for article in articles:
        cat = article['category']
        if cat not in articles_by_category:
            articles_by_category[cat] = []
        articles_by_category[cat].append(article)

    # 保存文章总览
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'articles',
        '徐健专业文章合集',
        f"""# 徐健专业文章合集

## 📚 文章概况
- **文章总数**: {len(articles)}篇
- **时间跨度**: 2020年-2021年
- **主要领域**: 专利法律实务、专利布局、案例分析

## 📊 年度分布
{chr(10).join([f"### {year}年 ({len(arts)}篇){chr(10)}" + chr(10).join([f"- {art['title']}" for art in arts]) for year, arts in sorted(articles_by_year.items())])}

## 🏷️ 分类汇总

{chr(10).join([f"### {category} ({len(arts)}篇){chr(10)}" + chr(10).join([f"- **{art['title']}** ({art['date']})" for art in arts]) for category, arts in sorted(articles_by_category.items())])}

## 🌟 文章特色

1. **实务导向**: 所有文章都源于实际案例和工作经验
2. **深度分析**: 对法律问题进行深入剖析
3. **案例丰富**: 结合具体案例讲解法律适用
4. **系统性强**: 涵盖专利申请、布局、诉讼等各个环节

## 💡 专业价值

这些文章展现了徐健先生：
- 深厚的法律理论基础
- 丰富的实务经验
- 敏锐的实务洞察力
- 系统的专业知识体系

## 📈 创作时间线
- **2020年**: {len(articles_by_year.get('2020', []))}篇文章，专业创作的高产期
- **2021年**: {len(articles_by_year.get('2021', []))}篇文章，持续深入研究

这些专业文章是徐健先生知识产权专业智慧的重要结晶。""",
        'text',
        2,  # 专业文章，具有一定私密性
        json.dumps({
            '类型': '文章合集',
            '作者': '徐健',
            '专业领域': '知识产权',
            '标签': ['专业文章', '知识产权', '专利法律']
        }),
        json.dumps({
            '文章数量': len(articles),
            '时间跨度': '2020-2021',
            '专业价值': '高'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存每篇文章的详细信息
    for article in articles:
        cursor.execute("""
            INSERT OR REPLACE INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'article',
            article['title'],
            f"""# {article['title']}

## 📄 文章信息
- **创作时间**: {article['date']}
- **专业分类**: {article['category']}
- **关键词**: {'、'.join(article['keywords'])}

## 📝 文章简介
{article['description']}

## 📁 文件信息
- **文件名**: {article['file_name']}
- **文件格式**: Pages文档
- **存储位置**: i_cloud Pages文档

## 🎯 文章价值
这篇文章体现了徐健先生在{article['category']}领域的专业见解和实践经验，具有重要的实务指导价值。

## 📚 相关阅读
同类主题文章推荐：
{chr(10).join([f"- {art['title']}" for art in articles_by_category.get(article['category'], []) if art['title'] != article['title'][:3])}""",
            'text',
            2,
            json.dumps({
                '类型': '专业文章',
                '分类': article['category'],
                '作者': '徐健',
                '标签': article['keywords']
            }),
            json.dumps({
                '创作时间': article['date'],
                '文件格式': 'pages',
                '字数': '待统计'
            }),
            article['date']
        ))

    # 保存专业成就总结
    achievement_summary = f"""# 徐健专业写作成就总结

## 📊 写作统计
- **文章总数**: {len(articles)}篇
- **主要创作年份**: 2020年（{len(articles_by_year.get('2020', []))}篇）
- **专业领域**: 知识产权法律实务

## 🎯 创作特色

### 1. 实务导向
所有文章都紧贴实务工作，解决实际工作中的法律问题。如：
- 《以"揉面机案"为例，再谈专利撰写》
- 《朋友圈发布信息是否构成专利法中的现有技术》

### 2. 案例丰富
大量使用真实案例说明法律适用，增强文章的实践指导价值。

### 3. 系统性强
形成完整的知识体系，涵盖：
- 专利申请与撰写
- 专利布局策略
- 行政与诉讼程序
- 刑事责任认定

### 4. 前瞻性
关注新兴问题，如社交媒体对专利的影响，体现了对行业发展的敏锐洞察。

## 🌟 代表文章

### 重点推荐
1. **专利布局系列**（《专利布局之布局层次》、《专利布局之甲方与乙方》）
   - 系统阐述专利布局理论
   - 从不同角度分析实施要点

2. **案例研究类**（《以"揉面机案"为例，再谈专利撰写》）
   - 通过具体案例深入浅出
   - 实用性强，指导性高

3. **前沿问题探讨**（《朋友圈发布信息是否构成专利法中的现有技术》）
   - 关注新技术、新业态
   - 具有前瞻性和创新性

## 💡 专业价值体现

1. **理论与实践结合**: 将深厚的理论基础与丰富的实务经验相结合
2. **问题导向**: 针对实务中的热点难点问题提供解决方案
3. **体系化思考**: 构建了完整的知识产权实务知识体系
4. **持续创新**: 不断探索新问题、新思路

## 📈 影响力

这些专业文章：
- 为同行提供了实务参考
- 促进了专业知识的传播
- 展现了作者的专业水准
- 对行业发展具有积极意义"""

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'professional_achievement',
        '徐健专业写作成就总结',
        achievement_summary,
        'text',
        1,
        json.dumps({
            '类型': '成就总结',
            '内容': '专业写作',
            '作者': '徐健',
            '标签': ['专业成就', '写作', '知识产权']
        }),
        json.dumps({
            '统计时间': datetime.now().strftime('%Y-%m-%d'),
            '文章总数': len(articles)
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    conn.commit()
    conn.close()

    print('✅ 徐健的专业文章已保存到个人数据库')
    print(f'✅ 保存文章总数: {len(articles)}篇')
    print('\n📚 文章分类统计:')
    for category, arts in sorted(articles_by_category.items()):
        print(f'  - {category}: {len(arts)}篇')
    print('\n📅 年度分布:')
    for year, arts in sorted(articles_by_year.items()):
        print(f'  - {year}年: {len(arts)}篇')

if __name__ == "__main__":
    save_articles()
