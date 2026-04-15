#!/usr/bin/env python3
"""
整理个人导图文档，分类保存并去重
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


def organize_personal_mindmaps() -> Any:
    """整理个人导图文档"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 检查数据库中已有的内容
    cursor.execute("""
        SELECT category, title, created_at FROM personal_info
        WHERE category IN ('reading_notes', 'stock_learning', 'recipe', 'personal_hobby')
    """)
    existing_records = cursor.fetchall()

    # 提取已有的内容用于去重
    existing_titles = set()
    existing_categories = {}
    for category, title, _created_at in existing_records:
        existing_titles.add(title)
        if category not in existing_categories:
            existing_categories[category] = []
        existing_categories[category].append(title)

    print("数据库中已有内容：")
    for cat, titles in existing_categories.items():
        print(f"  - {cat}: {len(titles)}条")

    # 个人导图文件列表
    mindmaps = [
        {
            'file_name': '缠中说禅.emmx',
            'title': '缠中说禅股票学习',
            'date': '2021-05-06',
            'category': 'stock_learning',
            'size': '41.7KB',
            'description': '缠中说禅股票理论的学习笔记'
        },
        {
            'file_name': '股票代码汇总.emmx',
            'title': '股票代码汇总',
            'date': '2021-06-16',
            'category': 'stock_learning',
            'size': '14.9KB',
            'description': '关注的股票代码整理汇总'
        },
        {
            'file_name': '老徐家菜谱.emmx',
            'title': '老徐家菜谱',
            'date': '2024-05-21',
            'category': 'recipe',
            'size': '13.3KB',
            'description': '家庭菜谱整理'
        },
        {
            'file_name': '人类简史.emmx',
            'title': '人类简史读书笔记',
            'date': '2024-12-15',
            'category': 'reading_notes',
            'size': '199.1KB',
            'description': '《人类简史》的阅读笔记和思考'
        },
        {
            'file_name': '2019年9-12月工作日志.emmx',
            'title': '2019年9-12月工作日志',
            'date': '2020-03-17',
            'category': 'work_log',
            'size': '55.5KB',
            'description': '2019年第四季度的工作记录'
        },
        {
            'file_name': '茶具.emmx',
            'title': '茶具收藏与鉴赏',
            'date': '2022-03-19',
            'category': 'personal_hobby',
            'size': '2.4MB',
            'description': '茶具的收藏心得和鉴赏知识'
        },
        {
            'file_name': '茶叶.emmx',
            'title': '茶叶品鉴与收藏',
            'date': '2024-07-16',
            'category': 'personal_hobby',
            'size': '2.2MB',
            'description': '各类茶叶的品鉴方法和收藏经验'
        }
    ]

    # 饮茶相关的图片资料
    tea_images = [
        '碧螺春.png', '茶壶.png', '茶艺六君子.png',
        '大红袍.png', '黄山毛峰.png', '铁观音.png', '雨花茶.png'
    ]

    # 去重处理
    new_records = []
    duplicates = []
    for mm in mindmaps:
        # 检查是否已存在类似内容
        is_duplicate = False
        for existing_title in existing_titles:
            if (mm['title'] in existing_title or existing_title in mm['title'] or
                any(keyword in existing_title for keyword in ['缠中说禅', '缠论']) and '缠中说禅' in mm['title']):
                is_duplicate = True
                duplicates.append(mm)
                break

        if not is_duplicate:
            new_records.append(mm)

    print("\n去重结果：")
    print(f"  - 总计: {len(mindmaps)}个文件")
    print(f"  - 新增: {len(new_records)}个文件")
    print(f"  - 重复: {len(duplicates)}个文件")

    if duplicates:
        print("\n重复的文件：")
        for dup in duplicates:
            print(f"  - {dup['title']}")

    # 保存整理报告
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'organization_report',
        '个人导图文档整理报告',
        f"""# 个人导图文档整理报告

## 📊 整理概况
- **整理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **整理目录**: /Users/xujian/Nutstore Files/08-思维导图/个人导图
- **文件总数**: {len(mindmaps)}个
- **新增记录**: {len(new_records)}个
- **重复记录**: {len(duplicates)}个

## 📂 文件分类统计

### 读书笔记类
- 《人类简史》读书笔记 ({mindmaps[3]['size']})

### 股票学习类
- 缠中说禅股票学习 ({mindmaps[0]['size']})
- 股票代码汇总 ({mindmaps[1]['size']})

### 菜谱类
- 老徐家菜谱 ({mindmaps[2]['size']})

### 个人爱好类
- 茶具收藏与鉴赏 ({mindmaps[4]['size']})
- 茶叶品鉴与收藏 ({mindmaps[5]['size']})

### 工作记录类
- 2019年9-12月工作日志 ({mindmaps[6]['size']})

## 🍵 饮茶文化资料
- 图片文件: {len(tea_images)}个
- 包含品种: 碧螺春、大红袍、黄山毛峰、铁观音、雨花茶等

## ✅ 整理结果

1. **成功去重**: 避免了重复内容的保存
2. **分类清晰**: 按照内容性质进行了合理分类
3. **便于查找**: 每个文件都有详细的描述信息
4. **系统完整**: 形成了个人知识体系的重要补充

## 📈 数据库现状
整理后数据库中：
- 读书笔记: {len(existing_categories.get('reading_notes', []))} + 1 = {len(existing_categories.get('reading_notes', [])) + 1}条
- 股票学习: {len(existing_categories.get('stock_learning', []))} + {sum(1 for mm in new_records if mm['category'] == 'stock_learning')} = {len(existing_categories.get('stock_learning', [])) + sum(1 for mm in new_records if mm['category'] == 'stock_learning')}条
- 菜谱: {len(existing_categories.get('recipe', []))} + {sum(1 for mm in new_records if mm['category'] == 'recipe')} = {len(existing_categories.get('recipe', [])) + sum(1 for mm in new_records if mm['category'] == 'recipe')}条
- 个人爱好: {len(existing_categories.get('personal_hobby', []))} + {sum(1 for mm in new_records if mm['category'] == 'personal_hobby')} = {len(existing_categories.get('personal_hobby', [])) + sum(1 for mm in new_records if mm['category'] == 'personal_hobby')}条""",
        'text',
        1,
        json.dumps({
            '类型': '整理报告',
            '内容': '个人文档',
            '标签': ['整理报告', '文档管理', '去重']
        }),
        json.dumps({
            '整理时间': datetime.now().strftime('%Y-%m-%d'),
            '处理文件数': len(mindmaps)
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存新增的记录
    for mm in new_records:
        cursor.execute("""
            INSERT OR REPLACE INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mm['category'],
            mm['title'],
            f"""# {mm['title']}

## 📄 文件信息
- **文件名**: {mm['file_name']}
- **创建日期**: {mm['date']}
- **文件大小**: {mm['size']}
- **文件格式**: EMMX思维导图

## 📝 内容简介
{mm['description']}

## 🎯 使用建议
- 建议使用思维导图软件打开查看
- 可以根据需要进行更新和补充
- 定期回顾和整理相关内容

## 📂 文件位置
/Users/xujian/Nutstore Files/08-思维导图/个人导图/{mm['file_name']}""",
            'text',
            2 if mm['category'] == 'stock_learning' else 1,
            json.dumps({
                '类型': '思维导图',
                '分类': mm['category'],
                '文件格式': 'EMMX',
                '标签': ['思维导图', '个人文档']
            }),
            json.dumps({
                '创建日期': mm['date'],
                '文件大小': mm['size']
            }),
            mm['date']
        ))

    # 保存茶文化专题
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'personal_hobby',
        '茶文化收藏集锦',
        f"""# 茶文化收藏集锦

## 🍵 藏品概述
- **收藏时间**: 2020年5月
- **收藏类别**: 茶叶、茶具、茶艺相关
- **图片总数**: {len(tea_images)}张

## 📖 茶叶收藏
1. **碧螺春** - 中国十大名茶之一，产于江苏太湖
2. **大红袍** - 武夷岩茶之王，福建特产
3. **黄山毛峰** - 安徽黄山名茶，形似雀舌
4. **铁观音** - 安溪铁观音，乌龙茶代表
5. **雨花茶** - 南京特产，针形名茶

## 🫖 茶具收藏
1. **茶壶** - 紫砂壶、陶瓷壶等各类茶壶
2. **茶艺六君子** - 茶道六用：茶则、茶针、茶漏、茶夹、茶匙、茶筒

## 💝 收藏心得
- 注重茶叶品质和产地
- 关注茶具的工艺和年代
- 学习茶艺，提升品茶境界
- 以茶会友，分享茶文化

## 📚 学习资源
- 详细的思维导图：《茶具收藏与鉴赏》、《茶叶品鉴与收藏》
- 大量实拍图片资料
- 实践经验的总结和记录

## 🌟 文化价值
这些茶文化收藏不仅展现了中华茶文化的博大精深，也体现了收藏者的文化修养和生活品味。""",
        'text',
        1,
        json.dumps({
            '类型': '收藏集锦',
            '主题': '茶文化',
            '标签': ['茶文化', '收藏', '茶叶', '茶具']
        }),
        json.dumps({
            '图片数量': len(tea_images),
            '整理时间': datetime.now().strftime('%Y-%m-%d')
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    conn.commit()
    conn.close()

    print("\n✅ 个人导图文档整理完成！")
    print(f"✅ 新增保存: {len(new_records)}个文件")
    print(f"✅ 跳过重复: {len(duplicates)}个文件")
    print(f"✅ 茶文化图片: {len(tea_images)}张")
    print("\n📂 分类保存情况：")
    for cat in ['reading_notes', 'stock_learning', 'recipe', 'personal_hobby', 'work_log']:
        count = sum(1 for mm in new_records if mm['category'] == cat)
        if count > 0:
            print(f"  - {cat}: {count}个")

if __name__ == "__main__":
    organize_personal_mindmaps()
