#!/usr/bin/env python3
"""
保存爸爸的股票理论学习笔记到数据库
"""

import json
import sqlite3
from pathlib import Path


def save_stock_learning_notes() -> None:
    """保存股票理论学习笔记到数据库"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 股票理论学习笔记内容
    stock_learning_content = {
        'title': '缠中说缠股票理论学习笔记',
        'date': '2007-06-30',  # 从文件日期推断
        'source': 'OmniOutliner学习笔记',
        'main_theory': '缠中说缠',
        'core_principle': '"知幻即离，离幻即觉" - 出自《圆觉经》',
        'key_theorems': [
            {
                'number': 1,
                'content': '不会赢钱的经济人，只是废人！',
                'category': '核心理念'
            },
            {
                'number': 2,
                'content': '没有庄家，有的只是赢家和输家！',
                'category': '市场认知'
            },
            {
                'number': 3,
                'content': '你的喜好，你的死亡陷阱！',
                'category': '投资心态',
                'advice': '多看，多思考，慢下手。'
            },
            {
                'number': 4,
                'content': '什么是理性？今早买N中工就是理性！',
                'category': '理性判断'
            },
            {
                'number': 5,
                'content': '市场无须分析，只要看和干！',
                'category': '操作方法',
                'advice': '更多关注点应该在当下，不要被股评家和自我迷惑。'
            },
            {
                'number': 6,
                'content': '本ID如何在五粮液、包钢权证上提款的！',
                'category': '实战案例'
            },
            {
                'number': 7,
                'content': '给赚了指数亏了钱的一些忠告',
                'category': '经验教训'
            }
        ],
        'investment_philosophy': [
            '股票是打猎思维，你死我活',
            '看准机会，往死里干才能赚钱'
        ],
        'learning_points': [
            {
                'point': '禅理与投资结合',
                'description': '将《圆觉经》的智慧应用于股票投资'
            },
            {
                'point': '实战经验分享',
                'description': '包含五粮液、包钢权证等具体操作案例'
            },
            {
                'point': '理性投资理念',
                'description': '强调理性判断和独立思考的重要性'
            }
        ]
    }

    # 保存主要内容
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'investment_learning',
        stock_learning_content['title'],
        f"""# {stock_learning_content['title']}

## 📖 基本信息
- **学习时间**: {stock_learning_content['date']}
- **理论体系**: {stock_learning_content['main_theory']}
- **核心原理**: {stock_learning_content['core_principle']}
- **来源**: {stock_learning_content['source']}

## 🎯 七大核心定理

### 定理1: 经济人本质
{stock_learning_content['key_theorems'][0]['content']}
- **类别**: {stock_learning_content['key_theorems'][0]['category']}

### 定理2: 市场本质
{stock_learning_content['key_theorems'][1]['content']}
- **类别**: {stock_learning_content['key_theorems'][1]['category']}

### 定理3: 投资心态
{stock_learning_content['key_theorems'][2]['content']}
- **类别**: {stock_learning_content['key_theorems'][2]['category']}
- **建议**: {stock_learning_content['key_theorems'][2]['advice']}

### 定理4: 理性判断
{stock_learning_content['key_theorems'][3]['content']}
- **类别**: {stock_learning_content['key_theorems'][3]['category']}

### 定理5: 操作方法
{stock_learning_content['key_theorems'][4]['content']}
- **类别**: {stock_learning_content['key_theorems'][4]['category']}
- **建议**: {stock_learning_content['key_theorems'][4]['advice']}

### 定理6: 实战案例
{stock_learning_content['key_theorems'][5]['content']}
- **类别**: {stock_learning_content['key_theorems'][5]['category']}

### 定理7: 经验教训
{stock_learning_content['key_theorems'][6]['content']}
- **类别**: {stock_learning_content['key_theorems'][6]['category']}

## 💡 投资哲学
{chr(10).join([f"- {philosophy}" for philosophy in stock_learning_content['investment_philosophy']])}

## 📚 学习要点
{chr(10).join([f"### {point['point']}{chr(10)}{point['description']}" for point in stock_learning_content['learning_points']])}""",
        'text',
        2,  # 投资学习比较私密
        json.dumps({
            '类型': '股票理论学习',
            '理论': '缠中说缠',
            '标签': ['投资', '股票', '缠论', '学习笔记']
        }),
        json.dumps({
            '学习日期': stock_learning_content['date'],
            '文件': '股票理论学习.ooutline',
            '要点数量': len(stock_learning_content['key_theorems'])
        }),
        stock_learning_content['date']
    ))

    # 保存投资哲学金句
    for i, philosophy in enumerate(stock_learning_content['investment_philosophy']):
        cursor.execute("""
            INSERT OR REPLACE INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'investment_quotes',
            f'投资哲学金句 {i+1}',
            philosophy,
            'quote',
            2,
            json.dumps({
                '类型': '投资哲学',
                '来源': '缠中说缠',
                '标签': ['投资哲学', '股票心法']
            }),
            json.dumps({
                '学习日期': stock_learning_content['date'],
                '序号': i+1
            }),
            stock_learning_content['date']
        ))

    # 创建学习总结
    learning_summary = """缠中说缠理论学习总结 - 徐健的投资修行

理论特色：
1. 禅理与投资的完美结合
   - 以《圆觉经》智慧指导投资实践
   - 强调"知幻即离"的投资境界
   - 追求内心平静与理性判断

2. 实战导向的七大定理
   - 从市场本质到操作方法
   - 覆盖心态、分析、实战全方位
   - 每条定理都蕴含深刻智慧

3. 独特的投资哲学
   - "打猎思维"的投资理念
   - 强调果断和精准
   - 追求实战效果

学习价值：
- 建立正确的投资认知
- 培养理性的投资心态
- 掌握实用的操作方法
- 提升实战投资能力

学习时间：2007年6月
理论体系：缠中说缠
学习状态：深度学习与实践"""

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'investment_summary',
        '缠中说缠理论学习总结',
        learning_summary,
        'text',
        1,
        json.dumps({
            '类型': '学习总结',
            '作者': '徐健',
            '标签': ['学习总结', '投资理论', '缠论']
        }),
        json.dumps({
            '学习日期': stock_learning_content['date'],
            '理论': '缠中说缠',
            '定理数量': 7
        }),
        stock_learning_content['date']
    ))

    conn.commit()
    conn.close()
    print('✅ 股票理论学习笔记已保存到个人数据库')
    print(f'✅ 已保存 {len(stock_learning_content["key_theorems"])} 个核心定理')
    print(f'✅ 已保存 {len(stock_learning_content["investment_philosophy"])} 条投资哲学')
    print('✅ 已创建学习总结')

if __name__ == "__main__":
    save_stock_learning_notes()
