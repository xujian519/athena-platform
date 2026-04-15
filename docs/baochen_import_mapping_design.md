# 宝宸专利档案导入映射设计方案

## 一、数据结构对比分析

### Excel表结构（21个有效字段）
```
1. 信息备注      - 备注/说明信息
2. 序号         - 内部序号
3. 档案号        - 案卷编号
4. 申请号        - 专利申请号
5. 专利名称      - 发明名称
6. 案源人        - 客户名称
7. 代理人        - 专利代理人
8. 类型         - 专利类型
9. 申请日        - 申请日期
10. 空白列       - 无数据
11. 地址         - 客户地址
12. 缴费联系人及电话 - 联系信息
13. 法律状态      - 案件状态
14. 审查意见      - 审查意见内容
15. 授权日        - 授权日期
16. 档案存放      - 档案存储位置
17. 申请方式      - 申请途径
18. 缴费通知      - 缴费通知记录
19. 专利权终止通知 - 终止通知
20. 通知客户      - 客户通知记录
21. 备注         - 备注信息
```

### 云熙数据库表结构

#### 1. 客户表（clients）
```
核心字段：
- name (客户名称) ← Excel: 案源人
- type (客户类型) ← 智能判断
- address (地址) ← Excel: 地址
- contact_person (联系人) ← Excel: 缴费联系人及电话 (拆分)
- contact_phone (联系电话) ← Excel: 缴费联系人及电话 (拆分)
- source (数据来源) ← 'baochen_archive_import'
- notes (备注) ← Excel: 信息备注 + 备注
```

#### 2. 项目表（projects）
```
核心字段：
- client_id (客户ID) ← 通过客户名称关联
- name (项目名称) ← 智能生成：客户名 + "专利项目"
- contact_person (项目联系人) ← Excel: 案源人 或 Excel: 缴费联系人
- agent (代理人) ← Excel: 代理人
- description (项目描述) ← 智能生成
- status (状态) ← 'ACTIVE'
```

#### 3. 案卷表（cases）
```
核心字段：
- case_number (案卷号) ← Excel: 档案号 或 智能生成
- title (案卷标题) ← Excel: 专利名称
- application_number (申请号) ← Excel: 申请号
- type (专利类型) ← Excel: 类型 (标准化)
- applicant (申请人) ← Excel: 案源人
- contact_person (联系人) ← Excel: 缴费联系人
- filing_date (申请日) ← Excel: 申请日
- legal_status (法律状态) ← Excel: 法律状态 (标准化)
- grant_date (授权日) ← Excel: 授权日
- examiner (审查员) ← 从审查意见提取
```

#### 4. 任务表（tasks）
```
可创建的任务：
- 审查意见处理任务
- 缴费通知任务
- 专利权终止通知任务
- 客户通知任务
```

#### 5. 财务记录表（financial_records）
```
可创建的财务记录：
- 代理费记录
- 官费记录
- 年费记录
```

#### 6. 审查意见表（review_opinions）
```
核心字段：
- case_id (案卷ID) ← 关联案卷
- review_type (审查类型) ← 智能判断
- review_date (审查日期) ← 从申请日推算
- content (审查内容) ← Excel: 审查意见
- status (状态) ← 'PENDING'
```

## 二、数据映射优先级

### 高优先级（必须导入）
```
客户表:
✓ name ← 案源人
✓ address ← 地址
✓ contact_person, contact_phone ← 缴费联系人及电话

案卷表:
✓ case_number ← 档案号
✓ title ← 专利名称
✓ application_number ← 申请号
✓ type ← 类型
✓ applicant ← 案源人
✓ filing_date ← 申请日
✓ legal_status ← 法律状态
✓ grant_date ← 授权日
```

### 中优先级（建议导入）
```
项目表:
✓ client_id ← 关联客户
✓ name ← 智能生成
✓ agent ← 代理人

审查意见表:
✓ content ← 审查意见
✓ review_date ← 申请日推算
```

### 低优先级（可选导入）
```
任务表、财务记录表（需要复杂业务逻辑）
文档表（档案信息）
```

## 三、数据处理规则

### 1. 数据标准化规则

#### 专利类型标准化
```python
type_mapping = {
    '发明': 'INVENTION',
    '实用新型': 'UTILITY_MODEL',
    '实用': 'UTILITY_MODEL',
    '外观设计': 'DESIGN',
    '外观': 'DESIGN'
}
```

#### 法律状态标准化
```python
status_mapping = {
    '已拿证': 'GRANTED',
    '授权': 'GRANTED',
    '拿证': 'GRANTED',
    '申请中': 'PENDING',
    '审查中': 'UNDER_REVIEW',
    '驳回': 'REJECTED',
    '撤回': 'WITHDRAWN',
    '放弃': 'WITHDRAWN'
}
```

#### 客户类型判断
```python
def determine_client_type(name):
    if '公司' in name or '有限' in name or '集团' in name:
        return 'COMPANY'
    elif '大学' in name or '学院' in name:
        return 'UNIVERSITY'
    elif '研究院' in name or '研究所' in name:
        return 'RESEARCH_INSTITUTE'
    else:
        return 'INDIVIDUAL'
```

### 2. 数据清洗规则

#### 申请号清洗
```python
def clean_application_number(app_num):
    # 过滤日期格式 (20201222)
    if re.match(r'^20\d{6}$', str(app_num)):
        return None

    # 只保留数字
    cleaned = re.sub(r'[^\d]', '', str(app_num))

    # 长度检查
    return cleaned if len(cleaned) >= 8 else None
```

#### 联系人信息拆分
```python
def parse_contact_info(contact_str):
    # 示例: "张健敏15315526366" 或 "18654665519张建平"

    # 提取电话号码
    phone = re.search(r'\d{11}', str(contact_str))
    phone = phone.group() if phone else ''

    # 提取姓名
    name = re.sub(r'\d+', '', str(contact_str))
    name = name.strip()

    return name, phone
```

### 3. 数据生成规则

#### 案卷号生成
```python
def generate_case_number(record):
    # 优先使用原始档案号
    if record.get('档案号'):
        return str(record['档案号'])

    # 基于申请号生成
    if record.get('申请号'):
        return f"BC{record['申请号'][:8]}"

    # 基于客户和时间生成
    client = record.get('案源人', '')[:4]
    filing_date = record.get('申请日', datetime.now())
    date_str = filing_date.strftime('%Y%m')
    return f"BC{client}{date_str}"
```

#### 项目名称生成
```python
def generate_project_name(client_name):
    return f"{client_name}专利项目"
```

## 四、导入流程设计

### 阶段1：基础数据导入
1. 导入客户信息（去重）
2. 导入案卷信息（关联客户）
3. 生成项目信息（关联客户）

### 阶段2：业务数据导入
1. 导入审查意见（关联案卷）
2. 生成任务记录（可选）

### 阶段3：增强数据导入
1. 导入财务记录（可选）
2. 导入文档记录（可选）

## 五、数据质量保证

### 1. 必填字段验证
```
客户表：name必填
案卷表：title必填
项目表：client_id, name必填
```

### 2. 数据唯一性
```
客户名称：唯一索引
案卷号：唯一索引
申请号：可为空，但需格式正确
```

### 3. 关联完整性
```
案卷必须关联客户
任务必须关联案卷
财务记录必须关联案卷
```

## 六、实施建议

### 1. 分步实施
- 第一步：只导入核心字段（客户、案卷）
- 第二步：导入业务数据（审查意见、任务）
- 第三步：导入辅助数据（财务、文档）

### 2. 错误处理
- 记录导入失败的原因
- 提供数据修复建议
- 支持增量导入

### 3. 性能优化
- 批量处理（每批100-200条）
- 事务处理保证一致性
- 进度显示和日志记录

## 七、预期结果

导入完成后将获得：
- 约5000条专利案卷记录
- 约100-500个客户记录（去重后）
- 约500-1000条审查意见记录
- 完整的客户-案卷关联关系
- 标准化的专利类型和法律状态

这将为宝宸事务所建立一个完整的专利业务管理基础数据库。