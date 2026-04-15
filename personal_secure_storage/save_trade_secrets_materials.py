#!/usr/bin/env python3
"""
保存商业秘密思维导图学习资料
作为平台的学习资料使用
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def save_trade_secrets_materials() -> None:
    """保存商业秘密学习资料到数据库"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 商业秘密学习资料列表
    materials = [
        {
            'file_name': '商业秘密保护体系工作内容.emmx',
            'title': '商业秘密保护体系工作内容',
            'date': '2020-06-03',
            'category': '体系构建',
            'description': '详细阐述商业秘密保护体系的具体工作内容和实施步骤',
            'size': '27.4KB'
        },
        {
            'file_name': '商业秘密保护项目轴.emmx',
            'title': '商业秘密保护项目轴',
            'date': '2020-05-13',
            'category': '项目管理',
            'description': '商业秘密保护项目的执行轴线和关键节点',
            'size': '15.1KB'
        },
        {
            'file_name': '商业秘密管理体系之创建-（图书）.emmx',
            'title': '商业秘密管理体系之创建',
            'date': '2020-03-18',
            'category': '体系创建',
            'description': '商业秘密管理体系的创建方法和步骤（图书资料）',
            'size': '93.6KB'
        },
        {
            'file_name': '商业秘密信息保护方式.emmx',
            'title': '商业秘密信息保护方式',
            'date': '2020-05-07',
            'category': '保护方法',
            'description': '各种商业秘密信息的保护方式和技术手段',
            'size': '30.1KB'
        },
        {
            'file_name': '商业秘密与专利布局保护-污废水资源化及水生态修复项目.emmx',
            'title': '商业秘密与专利布局保护',
            'subtitle': '以污废水资源化及水生态修复项目为例',
            'date': '2020-05-14',
            'category': '案例研究',
            'description': '通过具体项目案例说明商业秘密与专利布局的结合保护',
            'size': '35.7KB'
        },
        {
            'file_name': '我的服务项目.emmx',
            'title': '商业秘密保护服务项目',
            'date': '2020-05-19',
            'category': '服务内容',
            'description': '商业秘密保护相关的服务项目介绍',
            'size': '20.4KB'
        },
        {
            'file_name': '专利侵权诉讼攻防策略.emmx',
            'title': '专利侵权诉讼攻防策略',
            'date': '2020-06-07',
            'category': '诉讼策略',
            'description': '专利侵权诉讼中的攻防策略和应对方案',
            'size': '29.5KB'
        }
    ]

    # 按分类统计
    materials_by_category = {}
    for material in materials:
        cat = material['category']
        if cat not in materials_by_category:
            materials_by_category[cat] = []
        materials_by_category[cat].append(material)

    # 保存商业秘密学习资料总览
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'learning_materials',
        '商业秘密保护学习资料合集',
        f"""# 商业秘密保护学习资料合集

## 📚 资料概况
- **资料来源**: 高泽传专家整理
- **资料总数**: {len(materials)}份
- **文件格式**: EMMX思维导图
- **整理时间**: 2020年3月-6月

## 📊 内容分类

{chr(10).join([f"### {category} ({len(mats)}份){chr(10)}" + chr(10).join([f"- **{mat['title']}** ({mat['date']}, {mat['size']})" for mat in mats]) for category, mats in sorted(materials_by_category.items())])}

## 🎯 核心内容概述

### 1. 体系构建类
- 商业秘密保护体系的整体框架
- 具体工作内容和实施步骤
- 管理体系的创建方法

### 2. 实务操作类
- 信息保护的具体方式
- 项目管理的执行要点
- 专利布局的攻防策略

### 3. 案例研究类
- 污废水资源化项目案例
- 专利侵权诉讼实例
- 商业秘密与专利的结合保护

### 4. 服务提供类
- 专业服务项目介绍
- 客户需求解决方案
- 服务内容展示

## 💡 学习价值

### 理论价值
1. **系统性**: 形成完整的商业秘密保护知识体系
2. **专业性**: 体现专家级别的专业见解
3. **实用性**: 紧贴实际工作需求

### 实践价值
1. **指导性强**: 提供具体的操作指南
2. **案例丰富**: 通过实例加深理解
3. **可操作**: 易于在实际工作中应用

## 📈 适用对象

1. **企业管理者**: 了解商业秘密保护的重要性和方法
2. **IP从业者**: 提升商业秘密保护的专业能力
3. **法务人员**: 掌握商业秘密相关的法律实务
4. **创业者**: 学习如何保护企业核心机密

## 🔄 使用建议

1. **系统学习**: 按照体系构建→保护方法→案例研究的顺序学习
2. **重点突破**: 根据实际需要选择重点内容深入学习
3. **实践应用**: 将所学知识应用到实际工作中
4. **持续更新**: 结合最新法律法规更新知识体系

## 📝 学习路径推荐

### 初级路径
1. 商业秘密管理体系之创建
2. 商业秘密信息保护方式
3. 我的服务项目

### 中级路径
1. 商业秘密保护体系工作内容
2. 商业秘密保护项目轴
3. 专利侵权诉讼攻防策略

### 高级路径
1. 商业秘密与专利布局保护（案例）
2. 结合企业实际情况制定保护方案""",
        'text',
        1,  # 学习资料，可公开
        json.dumps({
            '类型': '学习资料',
            '来源': '高泽传',
            '专业领域': '商业秘密',
            '标签': ['商业秘密', '思维导图', '学习资料', '知识产权']
        }),
        json.dumps({
            '资料数量': len(materials),
            '文件格式': 'EMMX',
            '整理时间': '2020年'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存每个资料的详细信息
    for material in materials:
        cursor.execute("""
            INSERT OR REPLACE INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'trade_secret_material',
            material['title'],
            f"""# {material['title']}

## 📄 资料信息
- **文件名**: {material['file_name']}
- **创建日期**: {material['date']}
- **资料分类**: {material['category']}
- **文件大小**: {material['size']}
- **文件格式**: EMMX思维导图

## 📝 内容简介
{material['description']}

## 🎯 学习要点

通过本思维导图可以学习到：
- {material['category']}相关的核心知识
- 实际操作的方法和技巧
- 专业的实践经验总结

## 📚 相关资料
同类学习资料推荐：
{chr(10).join([f"- {mat['title']}" for mat in materials_by_category.get(material['category'], []) if mat['title'] != material['title']])}

## 💡 使用提示
- 建议使用XMind等思维导图软件打开
- 可以根据实际需要进行修改和完善
- 结合实际案例进行学习效果更佳

## 📖 学习建议
- 先理解整体框架，再深入细节
- 结合企业实际情况进行应用
- 定期回顾和更新知识""",
            'text',
            1,
            json.dumps({
                '类型': '学习资料',
                '分类': material['category'],
                '来源': '高泽传',
                '标签': ['商业秘密', material['category']]
            }),
            json.dumps({
                '创建日期': material['date'],
                '文件大小': material['size'],
                '文件类型': '思维导图'
            }),
            material['date']
        ))

    # 保存学习指南
    learning_guide = """# 商业秘密保护学习指南

## 🎯 学习目标

通过系统学习本资料，您将能够：
1. 掌握商业秘密保护的基本理论和方法
2. 了解商业秘密管理体系的构建步骤
3. 学会结合专利布局保护商业秘密
4. 掌握商业秘密侵权的应对策略

## 📚 学习内容结构

### 第一部分：基础理论
1. 商业秘密的定义和法律特征
2. 商业秘密与专利的区别与联系
3. 商业秘密保护的重要性

### 第二部分：体系建设
1. 商业秘密管理体系的创建
2. 保护体系的工作内容
3. 项目管理的执行要点

### 第三部分：保护方法
1. 信息保护的具体方式
2. 技术保护手段
3. 管理制度建设

### 第四部分：实务应用
1. 商业秘密与专利布局
2. 侵权诉讼攻防策略
3. 典型案例分析

## 📅 学习计划

### 第1周：基础理论学习
- 学习商业秘密的基本概念
- 了解相关法律法规
- 掌握保护的基本原则

### 第2周：体系构建
- 学习管理体系的创建
- 了解工作内容安排
- 制定保护计划

### 第3周：保护方法
- 学习各种保护方式
- 了解技术手段
- 制定保护措施

### 第4周：实务应用
- 研究典型案例
- 学习诉讼策略
- 实践应用练习

## 📝 学习方法

1. **思维导图学习法**
   - 先看整体框架
   - 再看具体分支
   - 深入理解细节

2. **案例学习法**
   - 分析典型案例
   - 总结经验教训
   - 应用到实践

3. **实践应用法**
   - 结合企业实际
   - 制定保护方案
   - 持续改进优化

## 💡 学习技巧

1. **做好笔记**: 记录重点和心得
2. **定期复习**: 巩固所学知识
3. **交流讨论**: 与同行交流心得
4. **实践检验**: 在实践中验证所学

## 📞 联系方式
如需专业服务，可联系：
- 整理者：高泽传专家
- 相关领域：商业秘密保护、专利布局

## 📈 进阶学习

完成基础学习后，可进一步研究：
1. 国际商业秘密保护制度
2. 行业特殊保护要求
3. 最新法律政策解读
4. 技术发展趋势分析"""

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'learning_guide',
        '商业秘密保护学习指南',
        learning_guide,
        'text',
        1,
        json.dumps({
            '类型': '学习指南',
            '内容': '商业秘密',
            '用途': '学习指导',
            '标签': ['学习指南', '商业秘密', '知识产权']
        }),
        json.dumps({
            '制定时间': datetime.now().strftime('%Y-%m-%d'),
            '学习周期': '4周',
            '难度': '中级'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    conn.commit()
    conn.close()

    print('✅ 商业秘密保护学习资料已保存到数据库')
    print(f'✅ 保存资料总数: {len(materials)}份')
    print('\n📊 分类统计:')
    for category, mats in sorted(materials_by_category.items()):
        print(f'  - {category}: {len(mats)}份')
    print('\n💡 学习建议:')
    print('  - 按照基础理论→体系建设→保护方法→实务应用的顺序学习')
    print('  - 结合实际案例加深理解')
    print('  - 定期回顾和更新知识')

if __name__ == "__main__":
    save_trade_secrets_materials()
