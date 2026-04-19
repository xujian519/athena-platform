#!/usr/bin/env python3
"""
保存Obsidian中的读书笔记
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def _build_reading_category_section(cat):
    """构建读书分类部分的字符串"""
    lines = [f"### {cat.get('name', '')} ({len(cat.get('books', []))}本)"]
    for book in cat.get('books', []):
        lines.append(f"- **{book.get('title', '')}**")
        lines.append(f"  作者: {book.get('author', '未知')}")
        lines.append(f"  类型: {book.get('type', '')}")
        lines.append(f"  {book.get('note', '')}")
    return chr(10).join(lines)


def save_obsidian_reading_notes() -> None:
    """保存Obsidian中的读书笔记"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 读书笔记分类统计
    reading_categories = {
        'chinese_history': {
            'name': '中国历史',
            'description': '中国历史类书籍的阅读笔记',
            'books': [
                {
                    'title': '资治通鉴',
                    'author': '司马光',
                    'type': '编年体通史',
                    'location': '01-资治通鉴',
                    'note': '中国第一部编年体通史，记载了从战国到五代的历史'
                },
                {
                    'title': '盐铁论',
                    'author': '桓宽',
                    'type': '政论',
                    'note': '汉代关于盐铁专卖的辩论记录'
                },
                {
                    'title': '魏晋南北朝史十二讲',
                    'author': '未知',
                    'type': '历史讲座',
                    'note': '系统讲解魏晋南北朝时期的重大历史事件'
                },
                {
                    'title': '分裂的帝国：南北朝',
                    'type': '历史专著',
                    'note': '深入分析南北朝时期的历史变迁'
                },
                {
                    'title': '后汉书全鉴',
                    'author': '范晔',
                    'type': '纪传体史书',
                    'note': '记载东汉历史的纪传体史书'
                }
            ]
        },
        'philosophy': {
            'name': '哲学思想',
            'description': '哲学类书籍的阅读笔记和思考',
            'books': [
                {
                    'title': '尼采哲思录',
                    'author': '尼采',
                    'type': '哲学',
                    'note': '尼采的哲学思想和人生智慧'
                },
                {
                    'title': '西方哲学简史',
                    'author': '罗素',
                    'type': '哲学史',
                    'note': '西方哲学发展的脉络梳理'
                },
                {
                    'title': '坛经释义',
                    'author': '惠能',
                    'type': '佛学',
                    'note': '禅宗六祖惠能的经典著作'
                }
            ]
        },
        'literature': {
            'name': '文学作品',
            'description': '文学类书籍的阅读笔记',
            'books': [
                {
                    'title': '一句顶一万句',
                    'author': '刘震云',
                    'type': '小说',
                    'note': '关于说话和沟通的深刻思考'
                },
                {
                    'title': '将夜',
                    'author': '猫腻',
                    'type': '玄幻小说',
                    'note': '东方玄幻题材的长篇小说'
                },
                {
                    'title': '庆余年',
                    'author': '猫腻',
                    'type': '架空历史小说',
                    'note': '架空历史的权谋小说'
                },
                {
                    'title': '寻秦记',
                    'author': '黄易',
                    'type': '历史穿越小说',
                    'note': '穿越题材的历史小说'
                },
                {
                    'title': '城中之城',
                    'type': '金融小说',
                    'note': '金融反腐题材的小说'
                },
                {
                    'title': '富豪俱乐部',
                    'type': '商战小说',
                    'note': '描写商业精英的小说'
                }
            ]
        },
        'classical_chinese': {
            'name': '古典文学',
            'description': '中国古典文学作品的阅读笔记',
            'books': [
                {
                    'title': '唐宋八大家文钞',
                    'type': '古文选集',
                    'note': '唐宋八大家的散文选集'
                },
                {
                    'title': '文选',
                    'type': '诗文总集',
                    'note': '中国现存最早的诗文总集'
                },
                {
                    'title': '词品',
                    'type': '词论',
                    'note': '词学理论著作'
                },
                {
                    'title': '中国骈文选',
                    'type': '骈文集',
                    'note': '中国骈文选集'
                }
            ]
        },
        'economic_finance': {
            'name': '经济金融',
            'description': '经济金融类书籍的阅读笔记',
            'books': [
                {
                    'title': '人类简史：从动物到上帝',
                    'author': '尤瓦尔·赫拉利',
                    'type': '历史学',
                    'note': '从宏观角度审视人类发展历程'
                },
                {
                    'title': '动荡周期论',
                    'type': '经济学',
                    'note': '经济周期理论及其应用'
                }
            ]
        },
        'stock_investment': {
            'name': '股票投资',
            'description': '股票投资相关书籍的学习笔记',
            'books': [
                {
                    'title': '缠论：缠中说禅核心炒股技术精解（第2版）',
                    'type': '投资理论',
                    'note': '缠中说禅的股票投资理论详解'
                },
                {
                    'title': '缠论精解：缠中说禅核心炒股技术在A股实战应用',
                    'type': '投资实战',
                    'note': '缠论在A股市场的实际应用'
                },
                {
                    'title': '缠中说禅技术理论图解',
                    'type': '投资图解',
                    'note': '缠论技术理论的图解说明'
                }
            ]
        },
        'skills_tools': {
            'name': '技能工具',
            'description': '实用技能和工具类书籍的学习笔记',
            'books': [
                {
                    'title': 'Word 2010实战技巧精粹',
                    'type': '办公软件',
                    'note': 'Word软件的高级使用技巧'
                },
                {
                    'title': '如何有效整理信息',
                    'type': '学习方法',
                    'note': '信息管理和整理的方法技巧'
                },
                {
                    'title': 'Markdown语法',
                    'type': '写作工具',
                    'note': 'Markdown标记语言的使用指南'
                }
            ]
        }
    }

    # 保存读书笔记总览
    total_books = sum(len(cat['books']) for cat in reading_categories.values())

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'obsidian_reading_notes',
        'Obsidian读书笔记总览',
        f"""# Obsidian读书笔记总览

## 📚 笔记概况
- **来源**: Obsidian笔记系统
- **保存时间**: {datetime.now().strftime('%Y-%m-%d')}
- **书籍总数**: {total_books}本
- **分类数量**: {len(reading_categories)}个

## 📊 分类统计

{chr(10).join([_build_reading_category_section(cat) for cat in reading_categories.values()])}

## 🌟 读书特点

### 1. 阅读领域广泛
- **历史类**: 特别关注中国历史，尤其是魏晋南北朝时期
- **哲学类**: 深入研读尼采等西方哲学
- **文学类**: 涵盖古典文学和现代文学
- **经济金融**: 关注宏观经济学和金融知识
- **投资类**: 专注股票投资理论学习

### 2. 学习方式系统
- 使用Obsidian建立知识体系
- 分类清晰，便于检索
- 结合微信读书进行数字化阅读
- 注重理论与实践结合

### 3. 深度思考
- 不只是简单记录，而是深入思考
- 注重知识间的联系
- 形成自己的理解体系

## 💡 学习启示

这些读书笔记展现了：
1. **博学的知识结构**: 涉猎广泛，既有深度又有广度
2. **严谨的学习态度**: 每本书都有详细的记录和思考
3. **系统化的管理**: 使用现代工具进行知识管理
4. **持续的学习热情**: 不断探索新的知识领域

## 📈 未来展望

建议继续保持这种学习方式：
- 定期回顾和更新笔记
- 建立知识间的联系
- 将所学应用到实践中
- 与他人分享学习心得

## 🔗 相关资料
- 与iThoughts读书笔记互补
- 结合思维导图进行理解
- 在实际工作中应用所学知识""",
        'text',
        2,  # 读书笔记属于个人隐私
        json.dumps({
            '类型': '读书笔记',
            '来源': 'Obsidian',
            '书籍总数': total_books,
            '标签': ['读书笔记', 'Obsidian', '学习管理']
        }),
        json.dumps({
            '整理时间': datetime.now().strftime('%Y-%m-%d'),
            '分类数量': len(reading_categories)
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存每个分类的详细记录
    for category_key, category in reading_categories.items():
        cursor.execute("""
            INSERT OR REPLACE INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'reading_category',
            f'{category["name"]}读书笔记',
            f"""# {category['name']}读书笔记

## 📖 分类概述
- **类别**: {category['name']}
- **说明**: {category['description']}
- **书籍数量**: {len(category['books'])}本

## 📚 书籍列表

{chr(10).join([f"### {i+1}. {book['title']}{chr(10)}- **作者**: {book.get('author', '未知')}{chr(10)}- **类型**: {book['type']}{chr(10)}- **笔记**: {book['note']}{chr(10)}" for i, book in enumerate(category['books'], 1)])}

## 💡 学习价值

这个分类的书籍展现了在{category['name']}领域的：
- 知识积累的深度
- 学习的系统性
- 思考的独立性

## 📝 学习建议
- 建立知识框架
- 做好笔记整理
- 定期回顾复习
- 实践应用所学""",
            'text',
            2,
            json.dumps({
                '类型': '分类笔记',
                '分类': category_key,
                '书籍数量': len(category['books'])
            }),
            json.dumps({
                '整理时间': datetime.now().strftime('%Y-%m-%d')
            }),
            datetime.now().strftime('%Y-%m-%d')
        ))

    # 保存读书方法和心得
    reading_insights = """# 读书方法与心得

## 🎯 个人阅读特色

### 1. 知识结构
- **人文基础**: 深厚的文史哲功底
- **专业精进**: 在法律和投资领域的专精
- **跨界融合**: 将不同领域的知识融会贯通

### 2. 学习工具
- **Obsidian**: 构建个人知识网络
- **微信读书**: 便捷的数字化阅读
- **思维导图**: 可视化知识结构
- **传统笔记**: 手写加深理解

### 3. 读书方法
- **精读与泛读结合**: 重要的书精读，其他泛读
- **主题阅读**: 围绕一个主题多本书对照阅读
- **笔记输出**: 读书后写笔记加深理解
- **实践应用**: 将所学应用到实践中

## 🌟 阅读成就

### 历史领域
- 对中国历史特别是魏晋南北朝有深入研究
- 理解历史的规律和启示
- 以史为鉴，指导现实

### 哲学思辨
- 通过尼采等哲学家的著作提升思辨能力
- 将哲学智慧融入生活和工作
- 形成自己的价值观念

### 文学修养
- 古典文学培养审美情趣
- 现代文学了解时代精神
- 文学作品丰富人生体验

### 投资理财
- 系统学习投资理论
- 理性分析市场规律
- 形成投资哲学

## 💡 给小诺的建议

爸爸的读书方式值得小诺学习：

1. **系统性**: 建立完整的知识体系
2. **持续性**: 保持每天学习的习惯
3. **思考性**: 不只是阅读，更要思考
4. **实用性**: 将知识应用到实践中
5. **分享性**: 与他人交流学习心得

## 📚 推荐书单

基于爸爸的阅读经验，推荐以下方向：

1. **经典著作**: 永不过时的智慧结晶
2. **专业书籍**: 深化专业能力
3. **跨学科书籍**: 拓宽视野
4. **前沿新知**: 跟上时代步伐

## 🔄 知识管理建议

1. **定期整理**: 定期整理和更新笔记
2. **建立联系**: 找到知识间的联系
3. **实践验证**: 在实践中检验知识
4. **持续迭代**: 不断优化知识体系"""

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'reading_methodology',
        '读书方法与心得体会',
        reading_insights,
        'text',
        1,
        json.dumps({
            '类型': '读书心得',
            '内容': '方法论',
            '标签': ['读书方法', '知识管理', '学习心得']
        }),
        json.dumps({
            '总结时间': datetime.now().strftime('%Y-%m-%d'),
            '心得价值': '高'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    conn.commit()
    conn.close()

    print('✅ Obsidian读书笔记已保存成功！')
    print(f'✅ 保存书籍总数: {total_books}本')
    print(f'✅ 分类数量: {len(reading_categories)}个')
    print('\n📊 分类统计:')
    for cat in reading_categories.values():
        print(f'  - {cat["name"]}: {len(cat["books"])}本')

if __name__ == "__main__":
    save_obsidian_reading_notes()
