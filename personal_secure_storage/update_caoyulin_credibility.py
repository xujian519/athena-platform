#!/usr/bin/env python3
"""
更新曹玉琳档案的可信度评级
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def update_caoyulin_credibility() -> None:
    """更新曹玉琳的可信度评级"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 添加可信度评估记录
    credibility_content = """# 曹玉琳 - 可信度评估记录

## 信用评级
- **可信度等级**: ⚠️ 较低 (2/5星)
- **评估日期**: 2025-12-16
- **评估人**: 徐健 (系统所有者)

## 评估依据

### ⚠️ 风险标记
- **商业诚信**: 存在疑问
- **专业能力**: 基本具备但可能夸大
- **合作风险**: 需要谨慎对待

### 具体观察点
1. **信息真实性**: 部分信息可能存在水分
2. **专业背景**: 基础资质真实，但影响力可能被夸大
3. **合作态度**: 需要进一步观察和验证
4. **商业信誉**: 建议保持距离，谨慎合作

### 建议措施
- ✗ **不建议深度合作**
- ✗ **重要项目谨慎考虑**
- ✓ **可维持表面关系**
- ✓ **需要时专业咨询可考虑，但需验证信息**

## 系统标记
- **标签**: `#可信度较低` `#需要谨慎` `#商业合作风险`
- **提醒**: 在涉及商业合作或重要决策时，此人的建议和承诺需要多方验证
- **建议**: 寻找更可靠的替代合作伙伴

---

**重要提醒**: 此评估基于个人经验和直觉判断，请结合实际情况独立评估。
**更新时间**: 2025-12-16
**下次评估**: 建议3-6个月后重新评估
"""

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'credibility_assessment',
        '曹玉琳-可信度评估（较低）',
        credibility_content,
        'text',
        3,  # 信用评级信息，设为高私密
        json.dumps({
            'type': '可信度评估',
            'name': '曹玉琳',
            'credibility_level': 2,  # 2/5星，较低
            'risk_level': '中高',
            'tags': ['可信度较低', '需要谨慎', '商业合作风险', '曹玉琳'],
            'assessment_date': '2025-12-16',
            'recommendation': '谨慎合作，保持距离'
        }),
        json.dumps({
            'record_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'assessor': '徐健',
            'reason': '基于个人经验和商业直觉判断',
            'next_review': '建议3-6个月后重新评估',
            'warning_level': 'medium-high'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 更新原有记录的标签，添加可信度标记
    cursor.execute("""
        UPDATE personal_info
        SET tags = json_patch(
            json(tags),
            '{"credibility_warning": "⚠️ 可信度较低", "caution_level": "需要谨慎对待"}'
        )
        WHERE title LIKE '%曹玉琳%'
    """)

    conn.commit()
    conn.close()

    print('✅ 曹玉琳的可信度评估已更新')
    print('⚠️ 可信度等级: 较低 (2/5星)')
    print('🏷️ 已添加标记: #可信度较低 #需要谨慎 #商业合作风险')
    print('💡 建议: 在商业合作中保持谨慎，重要决策需多方验证')

if __name__ == "__main__":
    update_caoyulin_credibility()
