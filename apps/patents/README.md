# Patents - 专利处理记录目录

> 📂 存放专利处理的历史记录和状态报告

---

## 📁 目录结构

```
patents/
├── processed/          # 当前处理报告（运行时生成）
└── archive/           # 历史归档
    └── processed_reports_2025/  # 2025年处理记录
```

---

## 🔄 归档策略

### 自动归档规则
- **频率**: 每季度一次（1月、4月、7月、10月）
- **保留期**: 当前目录保留最近3个月报告
- **归档格式**: `archive/processed_reports_YYYY/`

### 手动归档命令
```bash
cd /Users/xujian/Athena工作平台/apps/patents

# 创建年度归档目录
mkdir -p archive/processed_reports_$(date +%Y)

# 移动历史报告
mv processed/*.json archive/processed_reports_$(date +%Y)/

# 验证归档
ls -lh archive/processed_reports_$(date +%Y)/
```

---

## 📊 报告格式

### 处理报告JSON结构
```json
{
  "timestamp": "2025-12-25T04:08:59.190141",
  "total": 8,
  "success": 3,
  "failed": 5,
  "results": [
    {
      "patent_number": "US8460931B2",
      "status": "success",
      "text_length": 223316,
      "output_file": "/path/to/output.json"
    }
  ]
}
```

---

## 🔍 查询历史记录

### 按日期查询
```bash
# 查看某月的处理记录
ls -lh archive/processed_reports_2025/ | grep "202512"

# 统计成功率
cd archive/processed_reports_2025/
for file in *.json; do
  echo "$file: $(jq '.success, .failed' $file)"
done
```

### 按专利号查询
```bash
# 在所有报告中查找特定专利
grep -r "US8460931B2" archive/
```

---

## 📈 统计分析

### 生成季度报告
```python
import json
from pathlib import Path
from collections import defaultdict

def generate_quarter_report(archive_dir):
    stats = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0})

    for report_file in Path(archive_dir).glob("**/*.json"):
        with open(report_file) as f:
            data = json.load(f)
            month = report_file.stem.split("_")[1][:6]  # 提取年月
            stats[month]["total"] += data["total"]
            stats[month]["success"] += data["success"]
            stats[month]["failed"] += data["failed"]

    return stats
```

---

## 🗑️ 清理策略

### 自动清理规则
- **保留期限**: 2年
- **清理时间**: 每年1月执行
- **清理对象**: 超过2年的归档报告

### 清理命令
```bash
# 删除2年前的归档（谨慎使用！）
find archive/ -type d -name "processed_reports_*" -mtime +730 | xargs rm -rf
```

---

## ⚠️ 注意事项

1. **不可修改历史报告** - 归档后的报告文件不应再修改
2. **备份重要报告** - 关键项目的处理报告应额外备份
3. **敏感信息** - 某些报告可能包含客户信息，需注意保密

---

**维护者**: 徐健 (xujian519@gmail.com)
**文档创建**: 2026-04-22
**最后更新**: 2026-04-22
