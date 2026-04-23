#!/usr/bin/env python3
"""
整理和保存Obsidian知识卡片
包含历史人物、历史事件、法律条文等知识卡片
"""

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


def extract_content_from_card(file_path) -> Any:
    """从卡片文件中提取内容"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        # 提取标题（第一行非空内容）
        lines = content.split('\n')
        title = ""
        for line in lines:
            if line.strip():
                title = line.strip()
                break

        # 清理Markdown链接格式 [[文字]
        content_clean = re.sub(r'\[\[(.*?)\]\]', r'\1', content)

        # 清理其他Markdown格式
        content_clean = re.sub(r'\*\*(.*?)\*\*', r'\1', content_clean)  # 粗体
        content_clean = re.sub(r'\*(.*?)\*', r'\1', content_clean)      # 斜体
        content_clean = re.sub(r'`(.*?)`', r'\1', content_clean)        # 代码
        content_clean = re.sub(r'^(#{1,6})\s', '', content_clean, flags=re.MULTILINE)  # 标题
        content_clean = re.sub(r'^>\s', '', content_clean, flags=re.MULTILINE)  # 引用
        content_clean = re.sub(r'^\d+\.\s', '', content_clean, flags=re.MULTILINE)  # 有序列表
        content_clean = re.sub(r'^-\s', '', content_clean, flags=re.MULTILINE)  # 无序列表

        return title, content_clean.strip()
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return None, None

def save_obsidian_cards() -> None:
    """保存Obsidian知识卡片到数据库"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 卡片文件路径
    cards_path = Path("/Users/xujian/Library/Mobile Documents/i_cloud~md~obsidian/Documents/xujian/10卡片")

    # 分类统计
    categories = {
        '历史人物': {'count': 0, 'subcats': {}},
        '历史事件': {'count': 0, 'subcats': {}},
        '法律相关': {'count': 0, 'subcats': {}},
        '其他': {'count': 0, 'subcats': {}}
    }

    # 遍历所有卡片文件
    all_cards = []

    for card_file in cards_path.glob("**/*.md"):
        # 解析路径获取分类信息
        relative_path = card_file.relative_to(cards_path)
        path_parts = relative_path.parts[:-1]  # 排除文件名

        title, content = extract_content_from_card(card_file)
        if not title or not content:
            continue

        # 确定分类
        category = '其他'
        subcategory = ''

        if len(path_parts) > 0:
            main_cat = path_parts[0]
            if main_cat == '1-历史人物':
                category = '历史人物'
                if len(path_parts) > 1:
                    subcategory = path_parts[1]
            elif main_cat == '2-历史事件':
                category = '历史事件'
                if len(path_parts) > 1:
                    subcategory = path_parts[1]
            elif main_cat in ['3-法律', '4-相关法条']:
                category = '法律相关'
                subcategory = main_cat.replace('3-', '').replace('4-', '')

        # 统计
        categories[category]['count'] += 1
        if subcategory:
            if subcategory not in categories[category]['subcats']:
                categories[category]['subcats'][subcategory] = 0
            categories[category]['subcats'][subcategory] += 1

        # 保存卡片信息
        card_info = {
            'title': title,
            'content': content,
            'category': category,
            'subcategory': subcategory,
            'file_path': str(relative_path),
            'word_count': len(content)
        }
        all_cards.append(card_info)

        # 保存单张卡片到数据库
        cursor.execute("""
            INSERT OR REPLACE INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'knowledge_card',
            title,
            f"""# {title}

## 📋 分类信息
- **主分类**: {category}
- **子分类**: {subcategory}
- **文件路径**: {relative_path}
- **字数**: {len(content)}字

## 📖 卡片内容

{content}

## 💫 学习要点
- 知识点清晰
- 内容精炼
- 便于记忆

## 📝 备注
此卡片摘自爸爸的Obsidian知识库，是{category}领域的重要知识点。""",
            'text',
            1,  # 知识卡片属于公开信息
            json.dumps({
                '类型': '知识卡片',
                '分类': category,
                '子分类': subcategory,
                '来源': 'Obsidian',
                '标签': ['知识卡片', category, '学习资料']
            }),
            json.dumps({
                '文件路径': str(relative_path),
                '字数': len(content),
                '整理时间': datetime.now().strftime('%Y-%m-%d')
            }),
            datetime.now().strftime('%Y-%m-%d')
        ))

    # 保存知识卡片总览
    total_cards = len(all_cards)
    overview_content = f"""# 爸爸的知识卡片库

## 📚 卡片概况
- **来源**: Obsidian知识管理系统
- **整理时间**: {datetime.now().strftime('%Y年%m月%d日')}
- **卡片总数**: {total_cards}张
- **分类数量**: {len([c for c in categories.values() if c['count'] > 0])}个

## 📊 分类统计

### 📖 历史人物 ({categories['历史人物']['count']}张)
{chr(10).join([f"- **{subcat}**: {count}张" for subcat, count in categories['历史人物']['subcats'].items()]) if categories['历史人物']['subcats'] else '- 总计: ' + str(categories['历史人物']['count']) + '张'}

### 📜 历史事件 ({categories['历史事件']['count']}张)
{chr(10).join([f"- **{subcat}**: {count}张" for subcat, count in categories['历史事件']['subcats'].items()]) if categories['历史事件']['subcats'] else '- 总计: ' + str(categories['历史事件']['count']) + '张'}

### ⚖️ 法律相关 ({categories['法律相关']['count']}张)
{chr(10).join([f"- **{subcat}**: {count}张" for subcat, count in categories['法律相关']['subcats'].items()]) if categories['法律相关']['subcats'] else '- 总计: ' + str(categories['法律相关']['count']) + '张'}

### 📋 其他 ({categories['其他']['count']}张)

## 🌟 卡片特色分析

### 1. 内容精炼
- 每张卡片聚焦一个知识点
- 信息密度高，重点突出
- 便于快速查阅和记忆

### 2. 分类清晰
- 按照历史人物、历史事件、法律条文等分类
- 子分类进一步细化
- 便于系统学习和检索

### 3. 引用规范
- 使用双链格式关联相关内容
- 标注引用来源
- 保持知识的连贯性

### 4. 实用性强
- 专利法条文精准摘录
- 历史人物生平详略得当
- 历史事件关键信息完整

## 💡 学习价值

这些知识卡片体现了爸爸：

1. **渊博的历史知识**
   - 对东汉历史有深入研究
   - 熟悉魏晋南北朝历史脉络
   - 掌握重要历史事件的细节

2. **专业的法律素养**
   - 精准掌握专利法条文
   - 理解法律条文的内涵
   - 实务经验丰富

3. **高效的学习方法**
   - 知识卡片式的学习
   - 精炼总结的能力
   - 系统整理的习惯

4. **严谨的治学态度**
   - 准确无误的记录
   - 清晰的逻辑结构
   - 持续积累的精神

## 📈 对小诺的帮助

这些知识卡片对小诺的价值：

1. **丰富知识库**
   - 补充历史知识
   - 增强专业能力
   - 完善知识体系

2. **学习榜样**
   - 学习爸爸的治学方法
   - 养成知识积累习惯
   - 提升总结能力

3. **服务基础**
   - 更好地理解历史背景
   - 准确把握法律条文
   - 提供专业支持

## 🔍 精选卡片推荐

### 历史人物必读
- 刘秀：光武皇帝的传奇人生
- 冯异：大树将军的谦逊品格
- 邓禹：云台之首的智慧谋略

### 历史事件必知
- 昆阳之战：以少胜多的经典战例
- 陈桥兵变：宋代开国的关键事件

### 法律条文必记
- 专利法第26条第3款：说明书要求
- 专利法第26条第4款：权利要求要求

这些卡片是爸爸智慧的结晶，值得反复学习和体会！"""

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'cards_overview',
        '爸爸的知识卡片库总览',
        overview_content,
        'text',
        1,
        json.dumps({
            '类型': '知识卡片总览',
            '卡片总数': total_cards,
            '标签': ['知识卡片', '学习方法', '爸爸的智慧']
        }),
        json.dumps({
            '整理时间': datetime.now().strftime('%Y-%m-%d'),
            '分类数量': len([c for c in categories.values() if c['count'] > 0])
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存每个分类的详细信息
    for cat_name, cat_info in categories.items():
        if cat_info['count'] > 0:
            # 获取该分类的卡片
            cat_cards = [c for c in all_cards if c['category'] == cat_name]

            # 创建分类详情
            cat_detail = f"""# {cat_name}知识卡片

## 📊 分类统计
- **卡片总数**: {cat_info['count']}张
- **子分类数**: {len(cat_info['subcats'])}个

## 📑 子分类详情
{chr(10).join([f"### {subcat} ({count}张)" for subcat, count in cat_info['subcats'].items()])}

## 📝 卡片列表
{chr(10).join([f"{i+1}. **{card['title']}** ({card['subcategory']})" for i, card in enumerate(cat_cards[:20])])}
{f"... 还有 {len(cat_cards) - 20} 张" if len(cat_cards) > 20 else ""}

## 💡 学习重点
这是爸爸精心整理的{cat_name}知识，涵盖了该领域的核心内容，需要系统学习和掌握。"""

            cursor.execute("""
                INSERT OR REPLACE INTO personal_info
                (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'cards_category',
                f'{cat_name}知识卡片',
                cat_detail,
                'text',
                1,
                json.dumps({
                    '类型': '分类详情',
                    '分类': cat_name,
                    '卡片数量': cat_info['count']
                }),
                json.dumps({
                    '整理时间': datetime.now().strftime('%Y-%m-%d')
                }),
                datetime.now().strftime('%Y-%m-%d')
            ))

    conn.commit()
    conn.close()

    print('✅ Obsidian知识卡片已保存成功！')
    print(f'✅ 保存卡片总数: {total_cards}张')
    print('\n📊 分类统计:')
    for cat_name, cat_info in categories.items():
        if cat_info['count'] > 0:
            print(f'  - {cat_name}: {cat_info["count"]}张')
            if cat_info['subcats']:
                for subcat, count in cat_info['subcats'].items():
                    print(f'    └─ {subcat}: {count}张')

if __name__ == "__main__":
    save_obsidian_cards()
