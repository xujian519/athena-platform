#!/usr/bin/env python3
"""
保存爸爸的演讲稿到数据库
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def save_speeches() -> None:
    """保存演讲稿到数据库"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 演讲稿内容（根据提取的内容整理）
    speeches = [
        {
            'title': '构建企业知识产权护城河',
            'date': '2007-06-30',
            'venue': '未知',
            'audience': '企业代表、相关专业人士',
            'main_points': [
                '知识产权护城河的概念与价值',
                '技术生命周期与知识产权布局策略',
                '高质量专利申请的重要性',
                '企业知识产权战略制定',
                '案例分析与实战经验'
            ],
            'key_concepts': [
                '知识产权护城河：利用知识产权构建企业垄断优势',
                '技术生命周期：萌芽期、成长期、成熟期、饱和期',
                '专利布局策略：质重于量、快速部署、外围专利',
                '头部集中效应：知识产权向领先企业集中',
                '动态护城河：根据竞争态势调整知识产权战略'
            ],
            'case_studies': [
                '智慧矿灯专利布局案例（2020年）',
                '某互感器生产企业专利与商标组合案例',
                '京东方年专利申请8000+件的行业领先策略'
            ],
            'quotes': [
                '执业多年我的体会之一是，知识产权越来越向头部企业集中，即越是行业领先者其知识产权数量越多。',
                '要想行业领先，条件之一是知识产权的数量要领先。',
                '对于追赶者而言，要想企业低位超越，其知识产权数量一定会在先超越。'
            ]
        },
        {
            'title': '企业生产经营过程中的知识产权风险识别与控制',
            'date': '2007-06-30',
            'venue': '未知',
            'audience': '企业管理者、法务人员',
            'main_points': [
                '知识产权获取中的风险识别',
                '人力资源管理中的知识产权风险',
                '专利、商标、版权申请及布局',
                '商业秘密体系的构建',
                '知识产权诉讼案例解析'
            ],
            'key_concepts': [
                '风险识别：提前发现知识产权风险点',
                '先申请原则：知识产权申请的时机把握',
                '专利组合：发明、实用新型、外观设计的交叉布局',
                '知识产权与合同管理',
                '知识产权保护的全景式管理'
            ],
            'case_studies': [
                '博山真空设备厂诉万明泵业案',
                '临沂为民机械诉胜大机械案',
                '时风集团招标专利纠纷案',
                '油气分离器专利无效案'
            ],
            'quotes': [
                '知识产权目前在企业生产经营中越来越重要',
                '知识产权会贯穿生产经营的各种方面',
                '高质量申请会代替低质量申请，实现全国的知识产权组合的优化'
            ]
        }
    ]

    # 个人简介信息
    personal_info = {
        'name': '徐健',
        'title': '济南宝宸专利代理事务所',
        'qualifications': [
            '全国代理人协会向最高人民法院推荐的诉讼代理人',
            'IPMS（知识产权管理体系）技术专家'
        ],
        'background': {
            'education': '化学材料专业',
            'early_career': '制药企业工作5年，负责药品质量管理体系',
            'current_role': '专利代理工作，专注知识产权全链条服务'
        },
        'experience': {
            'years_in_ip': '15年',
            'litigation_cases': '代理各类知识产权诉讼150余件（2011年至今）',
            'expertise': '专利申请、复审、无效、诉讼、知识产权管理体系'
        }
    }

    # 保存每个演讲稿
    for speech in speeches:
        # 保存演讲稿正文
        cursor.execute("""
            INSERT OR REPLACE INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'speech',
            speech['title'],
            f"""# {speech['title']}

## 📅 基本信息
- **演讲时间**: {speech['date']}
- **演讲地点**: {speech['venue']}
- **听众**: {speech['audience']}

## 🎯 主要内容

### 核心观点
{chr(10).join([f"{i+1}. {point}" for i, point in enumerate(speech['main_points'])])}

### 关键概念
{chr(10).join([f"- **{concept}**: {speech['key_concepts'][i]}" for i, concept in enumerate(speech['key_concepts'])])}

### 案例研究
{chr(10).join([f"{i+1}. {case}" for i, case in enumerate(speech['case_studies'])])}

### 精彩语录
{chr(10).join([f"> {quote}" for quote in speech['quotes'])}

## 💡 演讲价值
展现了徐健先生在知识产权领域的深厚专业知识和丰富的实战经验，为企业构建知识产权护城河提供了系统性的指导和实用的策略建议。""",
            'text',
            2,  # 演讲稿内容属于中等私密
            json.dumps({
                '类型': '演讲稿',
                '标签': ['知识产权', '企业管理', '风险控制', '专利布局'],
                '演讲时间': speech['date']
            }),
            json.dumps({
                '要点数量': len(speech['main_points']),
                '案例数量': len(speech['case_studies']),
                '演讲类型': '专业分享'
            }),
            speech['date']
        ))

    # 保存个人简介
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'professional_profile',
        '徐健 - 知识产权专家简介',
        f"""# 徐健 - 知识产权专家

## 🏢 基本信息
- **工作单位**: {personal_info['title']}
- **专业领域**: 知识产权全链条服务

## 🎖️ 专业资质
{chr(10).join([f"- {qualification}" for qualification in personal_info['qualifications'])}

## 📚 教育与职业背景
- **专业背景**: {personal_info['background']['education']}
- **早期经历**: {personal_info['background']['early_career']}
- **当前角色**: {personal_info['background']['current_role']}

## 💼 专业经验
- **从业年限**: {personal_info['experience']['years_in_ip']}
- **诉讼经验**: {personal_info['experience']['litigation_cases']}
- **专业特长**: {personal_info['experience']['expertise']}

## 🌟 专业成就
- 15年知识产权从业经验，覆盖全产业链
- 处理150+知识产权诉讼案件
- 为多家企业提供知识产权战略咨询
- 在构建企业知识产权护城河方面有独特见解

## 📋 服务范围
1. 专利申请与布局
2. 专利复审与无效
3. 知识产权诉讼
4. 企业知识产权管理体系建设
5. 知识产权战略咨询""",
        'text',
        1,  # 公开的个人简介
        json.dumps({
            '类型': '职业简介',
            '标签': ['知识产权', '专利代理', '专家', '诉讼代理人']
        }),
        json.dumps({
            '更新日期': datetime.now().strftime('%Y-%m-%d'),
            '服务年限': 15
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 创建演讲合集
    speech_collection = """# 徐健演讲稿合集

## 📚 演讲主题概述

徐健先生作为资深的知识产权专家，通过多年的实务经验，形成了系统的知识产权服务理念和实战方法论。他的演讲主要围绕以下核心主题：

### 🎯 两大核心主题

#### 1. 构建企业知识产权护城河
- **核心理念**: 利用知识产权为企业建立持续竞争优势
- **方法论**: 动态护城河理论，根据企业发展阶段调整策略
- **实践案例**: 智慧矿灯、互感器生产等真实案例

#### 2. 企业生产经营中的知识产权风险识别与控制
- **重点领域**: 知识产权获取、人力资源管理、合同管理
- **风险类型**: 专利风险、商标风险、商业秘密风险
- **解决方案**: 全景式管理体系构建

### 💡 核心观点总结

1. **知识产权向头部集中**: 领先企业必须拥有领先的知识产权数量和质量
2. **技术生命周期管理**: 不同阶段采取不同的知识产权策略
3. **质量优于数量**: 未来中国专利申请必将向高质量转变
4. **动态战略调整**: 根据竞争态势和技术发展持续优化

### 🌟 专业特色

- **实战导向**: 所有理论都有真实案例支撑
- **系统思维**: 从战略高度构建知识产权体系
- **前瞻性**: 预判行业发展趋势和变革方向
- **可操作性**: 提供具体可执行的解决方案

## 📊 数据统计
- **演讲数量**: 2篇
- **涉及案例**: 7个
- **从业经验**: 15年
- **处理案件**: 150+件

这些演讲展现了徐健先生作为知识产权专家的专业深度和实践智慧，为企业知识产权管理提供了宝贵的指导。"""

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'speech_collection',
        '徐健演讲稿合集',
        speech_collection,
        'text',
        1,
        json.dumps({
            '类型': '演讲合集',
            '作者': '徐健',
            '标签': ['演讲合集', '知识产权', '专业分享']
        }),
        json.dumps({
            '演讲数量': 2,
            '整理时间': datetime.now().strftime('%Y-%m-%d'),
            '专业领域': '知识产权'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    conn.commit()
    conn.close()
    print('✅ 演讲稿已保存到个人数据库')
    print(f'✅ 已保存 {len(speeches)} 个演讲稿')
    print('✅ 已保存个人专业简介')
    print('✅ 已创建演讲合集')
    print('\n📝 保存的演讲稿：')
    for speech in speeches:
        print(f'  - 《{speech["title"]}》')

if __name__ == "__main__":
    save_speeches()
