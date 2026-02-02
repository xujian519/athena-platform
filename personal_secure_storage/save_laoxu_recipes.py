#!/usr/bin/env python3
"""
保存老徐家菜谱（去重处理）
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json
from pathlib import Path
from datetime import datetime

def save_laoxu_recipes() -> None:
    """保存老徐家菜谱到数据库，去除重复内容"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 老徐家菜谱内容（根据思维导图提取）
    laoxu_recipes = {
        'source': '老徐家菜谱思维导图',
        'update_date': '2024-08-06',
        'categories': {
            '肉类与主食类': [
                '炖鸡腿',
                '西红柿鸡蛋面',
                '炖羊排',
                '红汤羊肉',
                '沾水羊肉',
                '红烧清江鱼',
                '番茄鱼片',
                '白菜饼',
                '香煎豆腐',
                '豆腐丸子'
            ],
            '牛肉相关菜品': [
                '西红柿炖牛腩',
                '酱牛肉',
                '牛肉丸',
                '牛肉面',
                '萝卜水饺馅'
            ],
            '汤品': [
                '虾滑紫菜汤',
                '山药碎汤',
                '鲫鱼萝卜汤',
                '牛肉汤'
            ]
        },
        'special_recipes': {
            '牛肉馅饺子': {
                'ingredients': {
                    '主料': '牛肉500g',
                    '蔬菜': '菜400g',
                    '调料': {
                        '盐': '9g',
                        '鸡精': '6g',
                        '十三香': '2g',
                        '酱油': '30g',
                        '生抽': '15g',
                        '葱末': '15g',
                        '姜末': '15g',
                        '香油': '30g'
                    },
                    '液体': '清水260',
                    '特色': '葱油'
                },
                'category': '饺子类'
            }
        }
    }

    # 检查数据库中已有的菜谱
    cursor.execute("""
        SELECT title FROM personal_info
        WHERE category = 'recipe' OR title LIKE '%菜谱%' OR title LIKE '%菜%'
    """)
    existing_titles = [row[0] for row in cursor.fetchall()]

    # 提取已有的菜品名称
    existing_dishes = set()
    for title in existing_titles:
        if '虾滑紫菜汤' in title:
            existing_dishes.add('虾滑紫菜汤')
        elif '番茄鱼片' in title:
            existing_dishes.add('番茄鱼片')
        elif '山药碎汤' in title:
            existing_dishes.add('山药碎汤')

    # 统计新菜品
    all_dishes = []
    for category, dishes in laoxu_recipes['categories'].items():
        all_dishes.extend(dishes)
    all_dishes.append('牛肉馅饺子')

    new_dishes = [dish for dish in all_dishes if dish not in existing_dishes]

    print(f"数据库中已有菜品：{len(existing_dishes)}个")
    print(f"老徐家菜谱总计：{len(all_dishes)}个")
    print(f"需要新增菜品：{len(new_dishes)}个")

    # 保存菜谱总览
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'recipe_collection',
        '老徐家菜谱集锦',
        f"""# 老徐家菜谱集锦

## 🏠 菜谱概况
- **来源**: {laoxu_recipes['source']}
- **更新时间**: {laoxu_recipes['update_date']}
- **菜品总数**: {len(all_dishes)}个
- **分类数量**: {len(laoxu_recipes['categories'])}大类

## 📋 菜品分类

### 🥩 肉类与主食类 ({len(laoxu_recipes['categories']['肉类与主食类'])}个)
{chr(10).join([f"- {dish}" for dish in laoxu_recipes['categories']['肉类与主食类']])}

### 🐂 牛肉相关菜品 ({len(laoxu_recipes['categories']['牛肉相关菜品'])}个)
{chr(10).join([f"- {dish}" for dish in laoxu_recipes['categories']['牛肉相关菜品']])}

### 🍲 汤品类 ({len(laoxu_recipes['categories']['汤品'])}个)
{chr(10).join([f"- {dish}" for dish in laoxu_recipes['categories']['汤品']])}

### 🥟 特色菜品
- **牛肉馅饺子** (含详细配料)

## ✨ 菜谱特色

1. **家常美味**: 都是适合家庭制作的经典菜品
2. **营养均衡**: 荤素搭配，汤品丰富
3. **易于制作**: 制作方法相对简单
4. **口味多样**: 涵盖多种口味和烹饪方式

## 📝 更新记录
- 新增菜品: {len(new_dishes)}个
- 重复已去重: {len(existing_dishes)}个
- 最后更新: {datetime.now().strftime('%Y-%m-%d')}""",
        'text',
        1,  # 菜谱属于普通信息
        json.dumps({
            '类型': '菜谱合集',
            '来源': '老徐家',
            '标签': ['菜谱', '家常菜', '美食']
        }),
        json.dumps({
            '菜品总数': len(all_dishes),
            '新增数量': len(new_dishes),
            '整理时间': datetime.now().strftime('%Y-%m-%d')
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存特色菜品详细配方
    recipe = laoxu_recipes['special_recipes']['牛肉馅饺子']
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'recipe',
        '老徐家特色：牛肉馅饺子',
        f"""# 老徐家特色：牛肉馅饺子

## 🥟 配料表

### 主料
- 牛肉：{recipe['ingredients']['主料']}
- 蔬菜：{recipe['ingredients']['蔬菜']}

### 调料
{chr(10).join([f"- {key}：{value}" for key, value in recipe['ingredients']['调料'].items()])}

### 其他
- 液体：{recipe['ingredients']['液体']}
- 特色调料：{recipe['ingredients']['特色']}

## 📝 制作要点
1. 牛肉要选用新鲜优质的部位
2. 蔬菜要新鲜，保持水分
3. 调料比例要精准
4. 清水要分次加入，顺一个方向搅拌
5. 葱油的加入是提香的关键

## 💡 小贴士
- 馅料调制好后可冷藏1小时，味道更佳
- 包饺子时要注意封口，避免煮制时破皮
- 可根据个人口味调整调料用量

## 🏷️ 分类
{recipe['category']}""",
        'text',
        1,
        json.dumps({
            '类型': '菜谱',
            '分类': '饺子',
            '特色': '老徐家秘制',
            '标签': ['饺子', '牛肉馅', '家常菜']
        }),
        json.dumps({
            '整理时间': datetime.now().strftime('%Y-%m-%d'),
            '复杂度': '中等',
            '准备时间': '1小时'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存新增的简单菜谱记录（对于没有详细配方的菜品）
    for dish in new_dishes:
        if dish != '牛肉馅饺子':  # 这个已经单独保存了
            # 确定菜品分类
            category = '其他'
            for cat_name, dishes in laoxu_recipes['categories'].items():
                if dish in dishes:
                    category = cat_name
                    break

            cursor.execute("""
                INSERT OR REPLACE INTO personal_info
                (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'recipe',
                f'老徐家菜谱：{dish}',
                f"""# 老徐家菜谱：{dish}

## 🍽️ 菜品信息
- **菜名**: {dish}
- **分类**: {category}
- **菜系**: 家常菜
- **难度**: 待补充
- **口味**: 待补充

## 📝 备注
这是老徐家菜谱中的经典菜品，具体制作方法和用料可以进一步整理完善。

## 🏷️ 标签
家常菜, 老徐家, {category}""",
                'text',
                1,
                json.dumps({
                    '类型': '菜谱',
                    '分类': category,
                    '标签': ['家常菜', '老徐家']
                }),
                json.dumps({
                    '记录时间': datetime.now().strftime('%Y-%m-%d'),
                    '状态': '待完善'
                }),
                datetime.now().strftime('%Y-%m-%d')
            ))

    conn.commit()
    conn.close()

    print('\n✅ 老徐家菜谱保存完成！')
    print(f'✅ 新增菜品 {len(new_dishes)} 个')
    print(f'✅ 菜谱总数 {len(all_dishes)} 个')
    print(f'✅ 去重 {len(existing_dishes)} 个重复菜品')

    if new_dishes:
        print('\n📋 新增菜品清单：')
        for dish in new_dishes:
            print(f'  - {dish}')

if __name__ == "__main__":
    save_laoxu_recipes()