# YunxiIPAgentV3 - 云熙·IP管家

## 概述

YunxiIPAgentV3（云熙·IP管家V3）是Athena平台的知识产权管理专家，负责客户关系、项目管理和时限跟踪。

## 核心能力

| 能力名称 | 描述 | 输入类型 | 输出类型 |
|---------|-----|---------|---------|
| client_management | 客户管理 | 客户信息 | 客户档案 |
| project_management | 项目管理 | 项目信息 | 项目状态 |
| deadline_tracking | 期限跟踪 | 项目列表 | 到期提醒 |
| report_generation | 报告生成 | 统计参数 | 管理报告 |

## 使用示例

```python
from core.yunxi.yunxi_ip_agent_v3 import YunxiIPAgentV3

# 创建IP管家
agent = YunxiIPAgentV3(agent_id="yunxi_001")

# 创建客户
request = {
    "action": "create_client",
    "data": {
        "name": "示例科技有限公司",
        "contact": "ip@example.com"
    }
}

result = agent.execute(request)
```

## 管理功能

1. **客户管理**: 客户档案、联系历史、合同管理
2. **项目跟踪**: 专利申请、复审、无效宣告项目
3. **时限提醒**: 官费缴纳、答复期限、年费期限
4. **报告生成**: 工作量统计、费用报表、进度报告

## 认证状态

- **认证级别**: 🥉 Bronze
- **总分**: 73/100
- **接口合规性**: ✅ 25/25
- **测试覆盖率**: ✅ 20/20
- **代码质量**: ✅ 14/15

## 相关链接

- 源代码: `core/yunxi/yunxi_ip_agent_v3.py`
- 测试文件: `tests/agents/test_yunxi_ip_agent_v3.py`
