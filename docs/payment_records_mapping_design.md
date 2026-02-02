# 专利官费缴费记录数据库映射设计方案

## 📋 数据源分析

### Excel文件信息
- **文件路径**: `/Users/xujian/工作/10_归档文件/2025年专利官费缴费记录(1).xlsx`
- **总记录数**: 1,758条
- **总字段数**: 16个

### 核心字段映射

| Excel字段 | 数据库字段 | 数据类型 | 处理逻辑 | 备注 |
|---------|----------|---------|---------|------|
| 申请号/专利号 | case_id | VARCHAR(50) | 通过申请号/专利号匹配cases表 | 需要去掉'.'，统一格式 |
| 缴费日期 | record_date | DATE | 提取日期部分 | 格式如20250108 |
| 费用金额（人民币） | amount | NUMERIC(10,2) | 直接使用 | 实际缴费金额 |
| 费用种类 | type | financial_type_enum | 映射为RECEIPT | 官费缴费收据 |
| 业务归属 | 无 | VARCHAR(50) | 记录在description中 | 济南等地区 |
| 票据抬头 | 无 | VARCHAR(500) | 记录在description中 | 缴费单位名称 |
| 缴费-流水号 | 无 | VARCHAR(50) | 记录在description中 | 缴费流水号 |
| 备注/提交人 | notes | TEXT | 直接使用 | 提交人信息 |

## 🎯 关键设计要点

### 1. 专利号处理策略
```python
def normalize_patent_number(patent_number):
    """统一专利号格式，去掉小数点"""
    if pd.isna(patent_number):
        return None
    # 去掉小数点，如2024232638636.0 -> 2024232638636
    clean_number = str(patent_number).replace('.', '').strip()
    return clean_number if clean_number else None
```

### 2. 日期解析策略
```python
def parse_payment_date(date_str):
    """解析缴费日期"""
    if pd.isna(date_str):
        return None
    # 提取8位数字作为日期，如从"20250108济南..."中提取20250108
    import re
    date_match = re.search(r'(20\d{6})', str(date_str))
    if date_match:
        date_str = date_match.group(1)
        return datetime.strptime(date_str, '%Y%m%d').date()
    return None
```

### 3. 费用种类映射
```python
def map_fee_type(fee_type):
    """映射费用种类到财务类型"""
    fee_type_lower = str(fee_type).lower()
    if '申请费' in fee_type or '年费' in fee_type:
        return 'RECEIPT'  # 官费缴费收据
    elif '代理费' in fee_type:
        return 'INVOICE'  # 代理费发票
    else:
        return 'RECEIPT'  # 默认为收据
```

## 🔗 表关联关系

### 主要关联逻辑
1. **通过申请号/专利号匹配cases表**:
   - 标准化专利号格式（去掉小数点）
   - 同时匹配application_number和patent_number字段

2. **关联到项目和客户**:
   - 通过cases表关联到projects和clients
   - 获取完整的业务上下文

3. **设置付款状态**:
   - 所有缴费记录标记为PAID（已付款）
   - 设置paid_date为缴费日期

## 📊 数据质量检查

### 必要字段验证
- ✅ 申请号/专利号：不能为空，必须能匹配到案卷
- ✅ 缴费日期：必须能解析为有效日期
- ✅ 缴费金额：必须为有效数字

### 数据一致性检查
- 检查专利号格式一致性
- 验证缴费日期合理性
- 确认金额数值有效性

## 🎨 字段填充策略

### description字段组合
```
description = f"费用种类: {fee种类}\n缴费归属: {业务归属}\n票据抬头: {票据抬头}\n流水号: {缴费-流水号}"
```

### 其他字段处理
- **tenant_id**: 'yunpat-main'
- **status**: 'PAID' (已付款)
- **payment_method**: 银行转账/网上支付
- **auto_created**: true (系统创建)

## 🔄 导入流程

1. **数据预处理**
   - 读取Excel文件
   - 数据清洗和格式化
   - 必要字段验证

2. **专利号匹配**
   - 标准化专利号格式
   - 匹配cases表获取case_id
   - 记录匹配失败的专利号

3. **财务记录生成**
   - 构建financial_records对象
   - 设置关联关系
   - 填充描述信息

4. **批量导入**
   - 使用事务处理
   - 批量插入数据库
   - 错误处理和回滚

## 📈 后续处理

### 专利状态更新
缴费记录导入完成后，根据缴费情况更新相关专利的法律状态：
- 有近期缴费记录的专利标记为"有效"
- 长期无缴费记录的专利标记为可能失效

### 报表生成
- 缴费统计报表
- 专利有效性分析
- 缴费趋势分析

---

**设计完成时间**: 2025年12月22日
**设计人员**: 小诺·双鱼座 (平台总调度官)
**状态**: ✅ 设计完成，可开始实现