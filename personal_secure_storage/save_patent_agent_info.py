#!/usr/bin/env python3
"""
保存徐健专利代理师执业信息到个人数据库
包含：基本信息、资格证信息、执业备案信息
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def save_patent_agent_info() -> None:
    """保存专利代理师执业信息到数据库"""

    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 确保表存在
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            content_type TEXT DEFAULT 'text',
            sensitivity_level INTEGER DEFAULT 2,
            tags TEXT,
            metadata TEXT,
            created_at TEXT
        )
    """)

    # 专利代理师基本信息
    agent_basic_info = {
        'name': '徐健',
        'gender': '男',
        'ethnicity': '汉族',
        'birth_date': '1978-11-02',
        'id_type': '身份证',
        'id_number': '37011219781102103X',
        'phone': '15953181155',
        'email': '9697014@qq.com'
    }

    # 资格证信息
    qualification_info = {
        'qualification_number': '3716653',
        'qualification_type': '全国',
        'issue_date': '2013-01-01',
        'professional_field': '化学'
    }

    # 执业备案信息
    practice_info = {
        'practice_registration_number': '3729716653.1',
        'first_practice_date': '2014-08-11',
        'registration_date': '2020-12-28',
        'registration_authority': '山东省知识产权局',
        'organization_name': '济南宝宸专利代理事务所(普通合伙)',
        'is_partner': True
    }

    # 完整信息Markdown格式
    full_info_md = f"""# 专利代理师执业信息

## 基本信息

| 项目 | 内容 |
|------|------|
| 姓名 | {agent_basic_info['name']} |
| 性别 | {agent_basic_info['gender']} |
| 民族 | {agent_basic_info['ethnicity']} |
| 出生日期 | {agent_basic_info['birth_date']} |
| 证件类型 | {agent_basic_info['id_type']} |
| 证件号码 | {agent_basic_info['id_number']} |
| 电话 | {agent_basic_info['phone']} |
| 电子邮箱 | {agent_basic_info['email']} |

## 资格证信息

| 项目 | 内容 |
|------|------|
| 资格证号 | {qualification_info['qualification_number']} |
| 资格证类型 | {qualification_info['qualification_type']} |
| 颁证日期 | {qualification_info['issue_date']} |
| 专业领域 | {qualification_info['professional_field']} |

## 执业备案信息

| 项目 | 内容 |
|------|------|
| 执业备案号 | {practice_info['practice_registration_number']} |
| 首次执业时间 | {practice_info['first_practice_date']} |
| 备案日期 | {practice_info['registration_date']} |
| 备案机关 | {practice_info['registration_authority']} |
| 执业机构 | {practice_info['organization_name']} |
| 合伙人/股东 | {'是' if practice_info['is_partner'] else '否'} |

## 执业年限计算

- 首次执业：{practice_info['first_practice_date']}
- 截至2026年：约12年

## 重要提示

- 本信息由国家知识产权局监制
- 资格证号：{qualification_info['qualification_number']}
- 执业备案号：{practice_info['practice_registration_number']}
"""

    # 保存基本信息
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'patent_agent',
        '专利代理师基本信息',
        json.dumps(agent_basic_info, ensure_ascii=False, indent=2),
        'json',
        3,  # 高敏感级别
        json.dumps(['专利代理师', '基本信息', '执业信息'], ensure_ascii=False),
        json.dumps({
            '来源': '国家知识产权局',
            '更新时间': datetime.now().strftime('%Y-%m-%d')
        }, ensure_ascii=False),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存资格证信息
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'patent_agent',
        '专利代理师资格证信息',
        json.dumps(qualification_info, ensure_ascii=False, indent=2),
        'json',
        3,
        json.dumps(['专利代理师', '资格证', '证书'], ensure_ascii=False),
        json.dumps({
            '来源': '国家知识产权局',
            '更新时间': datetime.now().strftime('%Y-%m-%d')
        }, ensure_ascii=False),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存执业备案信息
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'patent_agent',
        '专利代理师执业备案信息',
        json.dumps(practice_info, ensure_ascii=False, indent=2),
        'json',
        3,
        json.dumps(['专利代理师', '执业备案', '济南宝宸'], ensure_ascii=False),
        json.dumps({
            '来源': '山东省知识产权局',
            '更新时间': datetime.now().strftime('%Y-%m-%d')
        }, ensure_ascii=False),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存完整信息Markdown版本
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'patent_agent',
        '专利代理师执业信息（完整版）',
        full_info_md,
        'markdown',
        3,
        json.dumps(['专利代理师', '完整信息', '参考文档'], ensure_ascii=False),
        json.dumps({
            '用途': '快速查询',
            '更新时间': datetime.now().strftime('%Y-%m-%d')
        }, ensure_ascii=False),
        datetime.now().strftime('%Y-%m-%d')
    ))

    conn.commit()
    conn.close()

    print('✅ 专利代理师执业信息已保存到个人数据库')
    print('')
    print('📋 保存内容：')
    print('  - 基本信息（姓名、性别、联系方式等）')
    print('  - 资格证信息（资格证号：3716653）')
    print('  - 执业备案信息（执业备案号：3729716653.1）')
    print('  - 完整信息Markdown版本')
    print('')
    print('🔑 关键信息摘要：')
    print(f'  - 资格证号：{qualification_info["qualification_number"]}')
    print(f'  - 执业备案号：{practice_info["practice_registration_number"]}')
    print(f'  - 执业机构：{practice_info["organization_name"]}')
    print(f'  - 首次执业：{practice_info["first_practice_date"]}')

if __name__ == "__main__":
    save_patent_agent_info()
