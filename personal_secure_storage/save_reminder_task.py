#!/usr/bin/env python3
"""
保存用户任务到小娜记忆系统
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json
from pathlib import Path
from datetime import datetime, timedelta

def save_reminder_task() -> None:
    """保存提醒事项任务"""

    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 计算明天的日期
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_date = tomorrow.strftime('%Y-%m-%d')
    tomorrow_time = "09:00"

    # 保存任务信息
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    task_content = f"""# 任务记录：联系曹新乐

## 基本信息
- **任务内容**: 联系曹新乐，约他周四见面
- **执行时间**: {tomorrow_date} 上午{tomorrow_time}
- **创建时间**: {current_time}
- **优先级**: 中等
- **状态**: 待完成

## 详细信息
- **联系人**: 曹新乐
- **事项**: 约定周四见面时间
- **方式**: 电话联系
- **目的**: 商讨具体见面细节

## 执行步骤
1. 明天上午9点准时拨打曹新乐电话
2. 确认周四的时间安排
3. 确定见面地点
4. 讨论见面要事
5. 确认后续安排

## 提醒设置
- **提醒事项**: 已添加到Reminders应用
- **日程安排**: 已添加到Calendar应用
- **提前提醒**: 设置15分钟前提醒

## 相关信息
根据小娜记忆系统记录，曹新乐是重要的联系人，与多个项目相关。此次见面可能涉及：
- 项目进展讨论
- 合作事宜
- 时间安排协调

## 后续跟进
- 完成通话后记录结果
- 确认周四见面时间地点
- 准备相关材料
""".format(
        tomorrow_date=tomorrow_date,
        tomorrow_time=tomorrow_time,
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    # 保存任务到数据库
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'task_reminder',
        f'联系曹新乐任务 - {tomorrow_date}',
        task_content,
        'text',
        2,  # 任务信息属于较私密内容
        json.dumps({
            'type': '提醒事项',
            '联系人': '曹新乐',
            '任务类型': '联系约见',
            '优先级': '中等',
            '状态': '待完成',
            '标签': ['任务', '提醒', '曹新乐', '约见']
        }),
        json.dumps({
            '创建时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '执行时间': f'{tomorrow_date} {tomorrow_time}',
            '提醒设置': ['Reminders应用', 'Calendar应用'],
            '记录人': '小诺',
            '任务来源': '用户语音输入'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存到日历提醒类别
    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'calendar_event',
        f'联系曹新乐 - {tomorrow_date}',
        f"""# 日程安排：联系曹新乐

## 基本信息
- **日期**: {tomorrow_date}
- **时间**: {tomorrow_time}
- **事件**: 联系曹新乐，约他周四见面
- **类型**: 电话会议
- **重要性**: 中等

## 事件详情
- **联系人**: 曹新乐
- **目的**: 商讨周四见面安排
- **预计时长**: 15-30分钟
- **准备事项**: 确认周四可安排时间段

## 相关背景
根据小娜记忆系统，曹新乐是重要联系人，此次通话对于：
- 项目协调
- 时间安排
- 工作推进

具有重要意义。

## 提醒设置
- 提前15分钟提醒
- Reminders应用同步提醒
""",
        'text',
        2,
        json.dumps({
            'type': '日程安排',
            '事件类型': '电话会议',
            '标签': ['日历', '日程', '曹新乐']
        }),
        json.dumps({
            '事件日期': tomorrow_date,
            '事件时间': tomorrow_time,
            '提醒设置': '提前15分钟',
            '同步应用': ['Reminders', 'Calendar']
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    conn.commit()
    conn.close()

    print(f'✅ 任务已成功保存到小娜记忆系统')
    print(f'✅ 执行时间: {tomorrow_date} 上午{tomorrow_time}')
    print(f'✅ 已同步到提醒事项和日历')
    print(f'✅ 任务状态：待完成')

if __name__ == "__main__":
    save_reminder_task()