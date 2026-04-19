#!/usr/bin/env python3
"""
保存任亮律师信息到小娜记忆系统
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def save_lawyer_info() -> None:
    """保存律师信息"""
    # 连接数据库
    db_path = Path("/Users/xujian/Athena工作平台/personal_secure_storage/personal_info.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 保存律师基本信息
    lawyer_content = """# 任亮律师详细档案

## 基本信息
- **姓名**: 任亮
- **执业机构**: 北京市东卫（济南）律师事务所
- **执业证号**: 13701200410772552
- **执业状态**: 正常执业
- **执业年限**: 20年（截至2024年）
- **职位**: 高级合伙人

## 教育背景
- **法学学士**: 中国海洋大学
- **法律硕士**: 山东大学
- **工商管理硕士(MBA)**: 美国密苏里州立大学

## 工作经历
- **2024年1月-至今**: 北京市东卫（济南）律师事务所 | 高级合伙人
- **2019年3月-2023年12月**: 北京德恒律师事务所 | 高级合伙人
- **2004年7月-2019年3月**: 山东中诚清泰律师事务所 | 执业律师、高级合伙人

## 专业领域
公司法律事务、金融证券法律事务、并购重组法律事务、重大商事诉讼仲裁、破产重整法律事务、常年法律顾问

## 专业荣誉
- 济南市优秀律师
- 全国服务中小企业先进个人
- 山东省优秀律师

## 代表性案例
- 某上市公司40亿元公司债券交易纠纷案
- 某国有企业20亿元并购重组项目
- 某民营企业集团破产重整案
- 多起重大商事仲裁案件

## 社会职务
- 济南市律师协会教育培训委员会副主任
- 山东省律师协会公司法律专业委员会委员
- 济南仲裁委员会仲裁员
- 烟台仲裁委员会仲裁员

## 联系方式
- **办公地址**: 山东省济南市历下区经十东路9777号鲁商国奥城3号楼23层
- **联系电话**: 0531-88752288（总机）

## 曹立贞案件匹配度
- **案件标的**: 200万元投资款追回
- **专业匹配**: ★★★★★（重大商事诉讼领域专家）
- **经验匹配**: ★★★★★（20年执业经验，处理过亿级案件）
- **时效匹配**: ★★★★★（可快速响应，应对接近诉讼时效的案件）
"""

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'lawyer_profile',
        '任亮律师-北京市东卫（济南）律师事务所',
        lawyer_content,
        'text',
        1,
        json.dumps({
            'type': '律师档案',
            'name': '任亮',
            'law_firm': '北京市东卫（济南）律师事务所',
            'practice_years': 20,
            'tags': ['律师', '商事诉讼', '金融证券', '并购重组']
        }),
        json.dumps({
            'record_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': '官方公开信息',
            'verified': True,
            'case_relevance': '曹立贞投资款追回案候选律师'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    # 保存案件匹配分析
    case_analysis = """# 任亮律师代理曹立贞案件的优势分析

## 案件基本情况
- **委托人**: 曹立贞
- **案件类型**: 投资款追回纠纷
- **争议金额**: 200万元人民币
- **案件状态**: 接近诉讼时效，需紧急处理

## 律师匹配度分析

### 专业匹配度：★★★★★
任亮律师专业领域完全契合：
- 重大商事诉讼仲裁（核心领域）
- 金融证券法律事务（投资款纠纷）
- 公司法律事务（投资主体相关）

### 经验匹配度：★★★★★
- 20年执业经验，资深律师
- 处理过40亿元级别大案
- 对大额商事纠纷经验丰富

### 时效紧急性匹配度：★★★★★
- 资深律师可快速响应
- 具备紧急案件处理能力
- 能制定高效的诉讼策略

## 代理策略建议
1. **立即行动**: 鉴于接近诉讼时效，应立即采取法律行动
2. **证据保全**: 尽快申请诉前保全，防止对方转移资产
3. **谈判协商**: 可先发送律师函，尝试协商解决
4. **诉讼准备**: 同步准备诉讼材料，必要时快速立案

## 预期效果
基于任亮律师的专业能力和经验：
- 胜诉概率较高
- 可有效维护当事人合法权益
- 能专业处理诉讼过程中的各种问题

## 下周行动建议
如委托任亮律师，建议：
1. 尽快签署委托代理合同
2. 准备完整的证据材料
3. 配合律师制定详细的诉讼方案
4. 做好庭审准备
"""

    cursor.execute("""
        INSERT OR REPLACE INTO personal_info
        (category, title, content, content_type, sensitivity_level, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'case_lawyer_match',
        '任亮律师-曹立贞投资款追回案匹配分析',
        case_analysis,
        'text',
        2,
        json.dumps({
            'type': '案件匹配分析',
            'lawyer': '任亮',
            'case': '曹立贞投资款追回案',
            'tags': ['案件分析', '律师匹配', '投资款追回']
        }),
        json.dumps({
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'case_amount': '200万元',
            'urgency': '高',
            'recommendation': '强烈推荐'
        }),
        datetime.now().strftime('%Y-%m-%d')
    ))

    conn.commit()
    conn.close()

    print('✅ 任亮律师信息已成功保存到小娜记忆系统')
    print('✅ 保存内容包括：')
    print('  - 律师详细档案')
    print('  - 与曹立贞案件的匹配分析')
    print('  - 代理策略建议')

if __name__ == "__main__":
    save_lawyer_info()
