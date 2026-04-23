#!/usr/bin/env python3
"""
保存爸爸的知识产权专业读书笔记到数据库
包含最高院知识产权审判案例指导的学习笔记
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def _build_case_section(cases, start_idx):
    """构建案例部分的字符串"""
    lines = []
    for i, case in enumerate(cases):
        lines.append(f"#### 案例{start_idx + i}: {case.get('reference', '')} - {case.get('title', '')}")
        key_points = case.get('key_points', [])
        if key_points:
            points_str = "; ".join(key_points[:3])
            lines.append(f"- **要点**: {points_str}")
        if case.get('insights'):
            lines.append(f"- **启示**: {case['insights'][0] if case['insights'] else ''}")
    return chr(10).join(lines)


def _build_list_section(items):
    """构建列表部分的字符串"""
    return chr(10).join([f"- {item}" for item in items])


def save_ip_studies() -> None:
    """保存知识产权学习笔记到数据库"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 核心学习内容
    ip_studies = {
        'source': '最高院知识产权审判案例指导',
        'study_date': '2020-05-24至2020-06-02',
        'total_volumes': 10,
        'current_focus': '第10辑',
        'main_categories': [
            '专利民事案件',
            '专利行政案件',
            '认证程序与证据'
        ]
    }

    # 第10辑详细案例学习记录
    volume_10_cases = [
        {
            'case_number': '1.1',
            'reference': '(2017)最高法民申1826号',
            'title': '适用禁止反悔原则的限制条件',
            'key_points': [
                '权利人对保护范围有修改或放弃，可导致禁止反悔原则不适用',
                '否定性意思表示必须以明示方式作出，不能推定',
                '需全面比对专利权和被诉侵权技术特征',
                '着重审查权利要求中技术特征的限定作用'
            ],
            'legal_basis': '专利法相关条文',
            'insights': [
                '内部证据优先：说明书及附图对权利要求的支撑作用',
                '本领域普通技术人员的理解标准',
                '专利复审委员会需明确评价创造性'
            ]
        },
        {
            'case_number': '1.2',
            'reference': '(2017)最高法民申3712号',
            'title': '形似而神非案（实用新型）',
            'key_points': [
                '实用新型保护形状、构造及其结合的技术方案',
                '现有技术抗辩以本领域普通技术人员知晓为标准',
                '需证明整体技术方案是否公知'
            ],
            'legal_basis': '实用新型专利保护范围',
            'insights': [
                '现有技术抗辩不能扩大至规避专利权保护范围',
                '物理组合与有机结合的区别认定',
                '国家标准符合性的证据要求'
            ]
        },
        {
            'case_number': '1.3',
            'reference': '(2017)最高法民再122号',
            'title': '短型减速顶案',
            'key_points': ['技术特征比对', '等同侵权认定'],
            'category': '民事案件'
        },
        {
            'case_number': '1.4',
            'reference': '(2017)最高法民申3802号',
            'title': '曲轴小拐水单元案（最小技术单元）',
            'key_points': ['最小技术单元原则', '技术方案整体性'],
            'category': '民事案件'
        },
        {
            'case_number': '2.1',
            'reference': '(2017)最高法行再84号',
            'title': '榆林市知识产权局换执法员案',
            'key_points': ['行政执法程序', '执法人员资格'],
            'category': '行政案件'
        },
        {
            'case_number': '2.2',
            'reference': '(2017)最高法行申2778号',
            'title': '行政诉讼期限起算点',
            'key_points': ['诉讼期限计算', '起算点认定'],
            'category': '行政案件'
        },
        {
            'case_number': '2.3',
            'reference': '(2016)最高法行再95号',
            'title': '说明书错误更正',
            'key_points': ['说明书修改', '错误更正程序'],
            'category': '行政案件'
        },
        {
            'case_number': '2.4',
            'reference': '(2016)最高法行再19号',
            'title': '权利要求书以说明书为依据',
            'key_points': ['权利要求书', '说明书支撑', '得到支持原则'],
            'category': '行政案件'
        },
        {
            'case_number': '3.1',
            'reference': '(2016)最高法民辖终107号',
            'title': '网络购物收货地不宜作为侵权行为地',
            'key_points': ['管辖权', '侵权行为地认定', '网络购物特殊情形'],
            'category': '管辖权问题'
        },
        {
            'case_number': '3.2',
            'reference': '(2017)最高法民申3918号',
            'title': '涉及市场统计调查的公证书证据',
            'key_points': ['公证书证据采信', '市场统计调查', '证据审查标准'],
            'category': '证据规则'
        }
    ]

    # 学习方法论和心得
    learning_insights = {
        'study_method': [
            '案例导向学习：通过具体案例理解法律适用',
            '分类整理：按案件类型（民事、行政、程序）系统学习',
            '要点提炼：每个案例总结3-5个核心要点',
            '法条链接：将案例与具体法条对应'
        ],
        'professional_gains': [
            '深化了对专利侵权判定标准的理解',
            '掌握了禁止反悔原则的适用条件',
            '提升了现有技术抗辩的运用能力',
            '增强了知识产权行政程序的认知'
        ],
        'practice_applications': [
            '指导专利申请文件的撰写策略',
            '优化专利侵权风险防控方案',
            '提升专利无效宣告代理水平',
            '加强知识产权诉讼应对能力'
        ]
    }

    # 保存主要学习记录
    # 预构建案例部分字符串，避免 f-string 嵌套导致的 Python 3.10 兼容性问题
    _civil_cases = chr(10).join([
        f'#### 案例{i+1}: {case.get("reference", "")} - {case.get("title", "")}\n'
        f'- **要点**: {"; ".join(case.get("key_points", [])[:3])}\n'
        f'- **启示**: {case.get("insights", [""])[0] if case.get("insights") else ""}'
        for i, case in enumerate(volume_10_cases[:5])
    ])
    _admin_cases = chr(10).join([
        f'#### 案例{i+6}: {case.get("reference", "")} - {case.get("title", "")}\n'
        f'- **要点**: {"; ".join(case.get("key_points", [])[:3])}'
        for i, case in enumerate(volume_10_cases[5:9])
    ])
    _procedure_cases = chr(10).join([
        f'#### 案例{i+10}: {case.get("reference", "")} - {case.get("title", "")}\n'
        f'- **要点**: {"; ".join(case.get("key_points", [])[:3])}'
        for i, case in enumerate(volume_10_cases[9:])
    ])

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'professional_studies',
        '最高院知识产权审判案例指导学习笔记',
        f"""# 最高院知识产权审判案例指导学习笔记

## 📚 学习概况
- **学习资料**: {ip_studies['source']}
- **学习时间**: {ip_studies['study_date']}
- **涵盖卷数**: {ip_studies['total_volumes']}辑
- **当前重点**: 第{ip_studies['current_focus']}辑

## 🏛️ 三大学习领域
{chr(10).join([f"{i+1}. **{category}**" for i, category in enumerate(ip_studies['main_categories'])])}

## 📋 第10辑核心案例精选

### 专利民事案件
{_civil_cases}

### 专利行政案件
{_admin_cases}

### 程序与证据
{_procedure_cases}

## 💡 学习心得

### 学习方法
{chr(10).join([f"- {method}" for method in learning_insights['study_method'])}

### 专业收获
{chr(10).join([f"- {gain}" for gain in learning_insights['professional_gains'])}

### 实践应用
{chr(10).join([f"- {app}" for app in learning_insights['practice_applications'])}

## 🎯 小诺的学习总结

爸爸的这些学习笔记展现了：
1. **系统性**: 覆盖知识产权审判的各个方面
2. **专业性**: 深入理解法律适用和裁判要旨
3. **实用性**: 注重案例对实务工作的指导
4. **前瞻性**: 跟踪最新司法实践发展

这些专业知识对小诺理解知识产权领域非常有价值！""",
        'text',
        2,  # 专业学习笔记，具有一定私密性
        json.dumps({
            '类型': '专业学习',
            '领域': '知识产权',
            '资料来源': '最高院案例指导',
            '标签': ['学习笔记', '知识产权', '案例分析']
        }),
        json.dumps({
            '学习周期': ip_studies['study_date'],
            '案例数量': len(volume_10_cases),
            '专业价值': '高'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存每个案例的详细学习笔记
    for case in volume_10_cases:
        cursor.execute("""
            INSERT OR REPLACE INTO personal_info
            (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'case_study',
            f"{case.get('reference', '')} - {case.get('title', '')}",
            f"""# {case.get('reference', '')}

## 案件标题
{case.get('title', '')}

## 案件编号
{case['case_number']}

## 核心要点
{chr(10).join([f"- {point}" for point in case['key_points'])}

## 法律依据
{case.get('legal_basis', '待补充')}

## 学习启示
{chr(10).join([f"- {insight}" for insight in case.get('insights', ['待深入学习'])])}

## 案件类别
{case.get('category', '待分类')}

## 学习笔记时间
{datetime.now().strftime('%Y-%m-%d')}""",
            'text',
            2,
            json.dumps({
                '类型': '案例学习',
                '编号': case.get("reference", ""),
                '标签': ['案例', '知识产权', '专业学习']
            }),
            json.dumps({
                '案例编号': case['case_number'],
                '学习日期': datetime.now().strftime('%Y-%m-%d')
            }),
            datetime.now().strftime('%Y-%m-%d')
        ))

    # 创建专业成长记录
    professional_growth = """# 徐健知识产权专业成长记录

## 📈 专业学习轨迹

### 学习体系
- **核心资料**: 最高院知识产权审判案例指导（第7-10辑）
- **学习方法**: 案例导向、分类整理、要点提炼
- **学习频率**: 持续跟踪，及时更新

### 专业能力提升

#### 1. 专利实体法理解深化
- 禁止反悔原则的精确适用
- 现有技术抗辩的认定标准
- 最小技术单元原则的运用
- 等同侵权判定规则

#### 2. 专利程序法掌握
- 专利复审与无效程序
- 行政诉讼要点
- 证据规则运用
- 管辖权确定

#### 3. 实务技能增强
- 专利申请撰写策略
- 侵权风险分析
- 诉讼应对技巧
- 客户咨询能力

## 🎯 专业特色

1. **案例驱动**: 深度研读权威案例，理解裁判思路
2. **系统思维**: 构建完整的知识产权知识体系
3. **实务导向**: 注重理论与实践的结合
4. **持续更新**: 跟进最新司法实践和发展

## 📊 学习成果

- **案例研读**: 50+典型案例深入分析
- **要点总结**: 200+核心要点提炼
- **实践应用**: 指导多个专利项目成功实施
- **知识传授**: 通过培训和演讲分享经验

## 💫 未来展望

继续深耕知识产权领域，特别是在：
- 新兴技术领域的专利保护
- 知识产权与企业战略结合
- 国际知识产权保护实践
- 知识产权管理体系的完善"""

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'professional_growth',
        '知识产权专业成长记录',
        professional_growth,
        'text',
        1,
        json.dumps({
            '类型': '成长记录',
            '领域': '知识产权专业',
            '标签': ['专业成长', '学习轨迹', '能力提升']
        }),
        json.dumps({
            '记录时间': datetime.now().strftime('%Y-%m-%d'),
            '专业领域': '知识产权',
            '成长阶段': '持续提升'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    conn.commit()
    conn.close()
    print('✅ 知识产权专业学习笔记已保存到个人数据库')
    print(f'✅ 已保存 {len(volume_10_cases)} 个案例的学习笔记')
    print('✅ 已创建专业成长记录')
    print('\n📚 小诺的专业学习收获：')
    print('  - 理解了禁止反悔原则的精确适用')
    print('  - 掌握了现有技术抗辩的认定标准')
    print('  - 学习了专利行政程序的关键要点')
    print('  - 提升了对知识产权审判的理解')

if __name__ == "__main__":
    save_ip_studies()
