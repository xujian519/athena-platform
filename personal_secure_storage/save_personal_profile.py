#!/usr/bin/env python3
"""
保存徐健正式个人简介到数据库
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json
from pathlib import Path
from datetime import datetime

def save_personal_profile() -> None:
    """保存正式个人简介到数据库"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 从Pages文件中提取的个人信息
    personal_profile = {
        'name': '徐健',
        'title': '济南宝宸专利代理事务所执行合伙人',
        'qualifications': [
            '最高人民法院推荐的诉讼代理人',
            '知识产权管理体系认证专家（IPMS技术专家）'
        ],
        'education': {
            'university': '青岛科技大学',
            'graduation_date': '2001年7月',
            'major': '化学材料专业'  # 根据之前信息补充
        },
        'early_career': [
            '新华制药股份有限公司',
            '深圳海普瑞药业集团'
        ],
        'current_work': {
            'company': '济南宝宸专利代理事务所',
            'duration': '2005年至今',
            'scope': [
                '专利申请与布局',
                '专利复审与无效',
                '知识产权诉讼'
            ]
        },
        'experience': {
            'total_cases': '180余件',
            'case_types': [
                '专利民事诉讼',
                '行政诉讼',
                '其他知识产权相关案件'
            ]
        },
        'typical_cases': [
            {
                'name': '舒学章诉济宁环保锅炉厂专利侵权案',
                'significance': '2010年中国十大知识产权案件之一',
                'type': '发明专利侵权案'
            },
            {
                'name': '崔金涛专利行政案',
                'process': '历经中山中院、山东省高院、专利复审委员会、北京一中院等全部程序',
                'result': '最终胜诉',
                'duration': '历时7年'
            },
            {
                'name': '大厂菲斯曼供热技术公司诉王昆玉专利权属纠纷案',
                'value': '设备纠纷，涉及金额1050万',
                'significance': '河北省近几年最大标的额专利案件'
            },
            {
                'name': '山东义丰机械工程有限公司专利维权案',
                'parties': '涉及广药集团、利沃隆食品公司、"王老吉"与"加多宝"商标异议案',
                'note': '与美国派拉蒙公司涉及"Forrest Gump"、"阿甘正传"商标案'
            },
            {
                'name': '多氟多化工公司商业秘密转让合同案',
                'value': '涉及金额55亿元',
                'type': '商业秘密转让'
            }
        ]
    }

    # 保存正式个人简介
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'personal_profile',
        '徐健个人简介（正式版）',
        f"""# 徐健个人简介

## 👤 基本信息
- **姓名**: {personal_profile['name']}
- **职务**: {personal_profile['title']}
- **专业资质**: {'、'.join(personal_profile['qualifications'])}

## 🎓 教育背景
- **毕业院校**: {personal_profile['education']['university']}
- **毕业时间**: {personal_profile['education']['graduation_date']}
- **专业**: {personal_profile['education']['major']}

## 💼 职业经历

### 早期经历（2005年前）
{chr(10).join([f"- {company}" for company in personal_profile['early_career']])}

### 现任职务（2005年至今）
- **工作单位**: {personal_profile['current_work']['company']}
- **主要业务**: {'、'.join(personal_profile['current_work']['scope'])}
- **案件数量**: {personal_profile['experience']['total_cases']}
- **案件类型**: {'、'.join(personal_profile['experience']['case_types'])}

## 🏆 典型案例

### 1. {personal_profile['typical_cases'][0]['name']}
- **案件类型**: {personal_profile['typical_cases'][0]['type']}
- **重要意义**: {personal_profile['typical_cases'][0]['significance']}
- **案件价值**: 该案是2010年中国十大知识产权案件之一

### 2. {personal_profile['typical_cases'][1]['name']}
- **审理程序**: {personal_profile['typical_cases'][1]['process']}
- **案件结果**: {personal_profile['typical_cases'][1]['result']}
- **持续时间**: {personal_profile['typical_cases'][1]['duration']}

### 3. {personal_profile['typical_cases'][2]['name']}
- **涉及金额**: {personal_profile['typical_cases'][2]['value']}
- **行业影响**: {personal_profile['typical_cases'][2]['significance']}

### 4. 其他重大案件
- **山东义丰机械案**: 涉及"王老吉"与"加多宝"商标争议
- **多氟多化工案**: 商业秘密转让，金额55亿元
- **国际商标案**: 与美国派拉蒙公司商标纠纷

## 📈 专业成就
- 从业15年，处理各类知识产权案件180余件
- 成功处理多起具有全国影响力的重大案件
- 在专利诉讼、行政程序等领域有丰富经验
- 为企业知识产权保护提供专业支持

## 🎯 专业特色
- **技术背景**: 化学材料专业背景，便于理解技术方案
- **诉讼经验**: 丰富的诉讼实务经验
- **专业认证**: IPMS技术专家，具备体系化管理能力
- **权威认可**: 最高人民法院推荐诉讼代理人""",
        'text',
        1,  # 个人公开信息
        json.dumps({
            '类型': '个人简介',
            '版本': '正式版',
            '用途': '商务场合',
            '标签': ['个人简介', '专业资质', '职业经历', '典型案例']
        }),
        json.dumps({
            '更新时间': datetime.now().strftime('%Y-%m-%d'),
            '案件数量': 180,
            '从业年限': 15
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 创建简历版本（简化版）
    resume_version = f"""# 徐健 - 简历

## 个人信息
- **姓名**: 徐健
- **现任**: 济南宝宸专利代理事务所执行合伙人
- **专业**: 专利代理、知识产权诉讼
- **经验**: 15年知识产权从业经验

## 核心资质
- 最高人民法院推荐诉讼代理人
- IPMS知识产权管理体系认证专家
- 专利代理人、律师资格

## 教育背景
青岛科技大学化学材料专业（2001年毕业）

## 工作经历
### 2005年至今
济南宝宸专利代理事务所 执行合伙人
- 专利申请与布局
- 专利复审与无效
- 知识产权诉讼

### 2001-2005年
- 新华制药股份有限公司
- 深圳海普瑞药业集团
（质量管理体系相关工作）

## 专业成就
- 处理知识产权案件180余件
- 代理多起最高人民法院案件
- 成功处理多个亿元级知识产权纠纷
- 2010年中国十大知识产权案件代理人

## 专业领域
- 专利申请与布局策略
- 专利侵权分析与诉讼
- 专利无效宣告程序
- 知识产权管理体系建设
- 商业秘密保护
- 商标及版权事务"""

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'personal_profile',
        '徐健简历（简化版）',
        resume_version,
        'text',
        1,
        json.dumps({
            '类型': '简历',
            '版本': '简化版',
            '用途': '快速了解',
            '标签': ['简历', '职业经历', '专业资质']
        }),
        json.dumps({
            '创建时间': datetime.now().strftime('%Y-%m-%d'),
            '适用场景': '商务合作、项目介绍'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    conn.commit()
    conn.close()

    print('✅ 徐健个人简介已保存到个人数据库')
    print('✅ 保存内容：')
    print('  - 正式版个人简介（完整版）')
    print('  - 简化版简历')
    print('\n📋 主要信息摘要：')
    print(f'  - 执业年限：15年')
    print(f'  - 处理案件：180余件')
    print(f'  - 典型案例：5个重大案例')
    print(f'  - 专业资质：最高人民法院推荐')

if __name__ == "__main__":
    save_personal_profile()