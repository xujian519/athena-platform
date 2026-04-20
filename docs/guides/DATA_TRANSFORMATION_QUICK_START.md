# 数据转换工具快速入门

**版本**: v1.0.0
**更新日期**: 2026-04-19

---

## 什么是数据转换工具？

`data_transformation`是Athena平台内置的数据处理工具，基于pandas提供强大的数据转换、清洗和分析能力。

### 核心特性

- 🚀 **19种数据操作**: 加载、清洗、筛选、排序、聚合、合并等
- ⚡ **高性能**: 基于pandas 3.0，处理速度快
- 🔒 **类型安全**: Pydantic v2数据验证
- 🎯 **易于使用**: 简洁的API设计
- 📊 **多格式支持**: CSV、Excel、JSON等

---

## 快速开始

### 1. 导入工具

```python
# 方式1：使用Handler（推荐）
from core.tools.data_transformation_handler import (
    load_csv,
    filter_data,
    sort_data,
    clean_data,
    get_statistics,
)

# 方式2：直接使用Handler
from core.tools.data_transformation_handler import data_transformation_handler
```

### 2. 加载数据

```python
# 加载CSV文件
result = load_csv("/path/to/file.csv")

if result["success"]:
    data = result["data"]
    print(f"数据形状: {data['shape']}")  # [100, 5]
    print(f"列名: {data['columns']}")

    # 转换为pandas DataFrame
    import pandas as pd
    df = pd.DataFrame(data["data"])
```

### 3. 数据清洗

```python
# 删除空值和重复行
result = clean_data(
    df,
    drop_na=True,         # 删除包含空值的行
    drop_duplicates=True  # 删除重复行
)

if result["success"]:
    clean_df = pd.DataFrame(result["data"]["data"])
    print(f"清洗前: {result['metadata']['original_rows']}行")
    print(f"清洗后: {result['metadata']['cleaned_rows']}行")
```

### 4. 数据筛选

```python
# 方式1：使用字典条件
result = filter_data(df, {"city": "New York"})

# 方式2：使用query表达式
result = filter_data(df, "age > 30 and salary > 50000")

# 获取筛选后的数据
if result["success"]:
    filtered_df = pd.DataFrame(result["data"]["data"])
```

### 5. 数据排序

```python
# 单列排序
result = sort_data(df, "salary", ascending=False)

# 多列排序
result = data_transformation_handler(
    operation="sort",
    data=df,
    params={"columns": ["department", "salary"], "ascending": [True, False]}
)
```

### 6. 数据聚合

```python
# 计算统计信息
result = get_statistics(df)
if result["success"]:
    stats = result["data"]
    print(f"平均年龄: {stats['age']['mean']:.2f}")
    print(f"平均薪资: {stats['salary']['mean']:.2f}")

# 分组聚合
result = data_transformation_handler(
    operation="group_by",
    data=df,
    params={"group_by": "department", "agg_func": "mean"}
)
```

### 7. 数据合并

```python
from core.tools.data_transformation_handler import merge_data

# 合并两个表
result = merge_data(
    df1,           # 第一个表
    df2,           # 第二个表
    on="id",       # 连接键
    how="inner"    # 连接方式: inner/outer/left/right
)

if result["success"]:
    merged_df = pd.DataFrame(result["data"]["data"])
    print(f"合并后: {result['metadata']['merged_rows']}行")
```

---

## 常用操作速查表

| 操作 | 函数 | 说明 |
|-----|------|------|
| 加载CSV | `load_csv(path)` | 读取CSV文件 |
| 加载Excel | `load_excel(path)` | 读取Excel文件 |
| 筛选数据 | `filter_data(df, conditions)` | 条件筛选 |
| 排序数据 | `sort_data(df, columns)` | 排序 |
| 清洗数据 | `clean_data(df, ...)` | 删除空值/重复 |
| 聚合数据 | `aggregate_data(df, func)` | 聚合计算 |
| 合并数据 | `merge_data(df1, df2, on)` | 表连接 |
| 统计信息 | `get_statistics(df)` | 描述性统计 |
| 数据信息 | `get_info(df)` | 数据概况 |
| 导出CSV | `to_csv(df, path)` | 保存为CSV |

---

## 高级用法

### 1. 自定义转换

```python
# 使用自定义函数
result = data_transformation_handler(
    operation="transform",
    data=df,
    params={
        "function": lambda x: x.assign(
            total_salary=x["salary"] * 1.2  # 计算含税薪资
        )
    }
)
```

### 2. 列操作

```python
# 添加列
result = data_transformation_handler(
    operation="add_column",
    data=df,
    params={
        "column_name": "bonus",
        "values": df["salary"] * 0.1  # 奖金为薪资的10%
    }
)

# 重命名列
result = data_transformation_handler(
    operation="rename_columns",
    data=df,
    params={"columns": {"old_name": "new_name"}}
)

# 删除列
result = data_transformation_handler(
    operation="delete_column",
    data=df,
    params={"columns": ["col1", "col2"]}
)
```

### 3. 数据透视

```python
# 创建透视表
result = data_transformation_handler(
    operation="pivot",
    data=df,
    params={
        "index": "department",    # 行
        "columns": "city",        # 列
        "values": "salary"        # 值
    }
)
```

### 4. 处理空值

```python
# 删除空值
result = data_transformation_handler(
    operation="drop_duplicates",
    data=df,
    params={"subset": ["col1", "col2"], "keep": "first"}
)

# 填充空值
result = data_transformation_handler(
    operation="fill_na",
    data=df,
    params={"value": 0}  # 或使用method="fffill"/"bfill"
)
```

---

## 完整示例

```python
import pandas as pd
from core.tools.data_transformation_handler import (
    load_csv,
    clean_data,
    filter_data,
    sort_data,
    aggregate_data,
    get_statistics,
    get_info,
)

# 1. 加载数据
result = load_csv("/path/to/employees.csv")
if not result["success"]:
    print(f"加载失败: {result['error']}")
    exit(1)

df = pd.DataFrame(result["data"]["data"])

# 2. 查看数据信息
info = get_info(df)
print(f"数据形状: {info['data']['shape']}")
print(f"列名: {info['data']['columns']}")

# 3. 数据清洗
clean_result = clean_data(
    df,
    drop_na=True,
    drop_duplicates=True
)
if clean_result["success"]:
    df = pd.DataFrame(clean_result["data"]["data"])
    print(f"清洗后: {clean_result['metadata']['cleaned_rows']}行")

# 4. 筛选数据
filter_result = filter_data(df, "salary > 50000")
if filter_result["success"]:
    df = pd.DataFrame(filter_result["data"]["data"])

# 5. 排序
sort_result = sort_data(df, "salary", ascending=False)
if sort_result["success"]:
    df = pd.DataFrame(sort_result["data"]["data"])

# 6. 统计分析
stats = get_statistics(df)
print(f"平均薪资: {stats['data']['salary']['mean']:.2f}")

# 7. 分组聚合
agg_result = aggregate_data(df, "mean")
print(f"总体平均: {agg_result['data']['data']['salary']:.2f}")
```

---

## 错误处理

所有操作都返回统一的结果格式：

```python
{
    "success": bool,      # 操作是否成功
    "data": Any,         # 返回数据
    "metadata": dict,    # 元数据信息
    "error": str | None, # 错误信息（失败时）
    "tool": dict         # 工具信息
}
```

### 错误处理示例

```python
result = load_csv("/path/to/file.csv")

if result["success"]:
    # 处理成功情况
    df = pd.DataFrame(result["data"]["data"])
else:
    # 处理错误情况
    print(f"操作失败: {result['error']}")
    print(f"错误详情: {result.get('metadata', {})}")
```

---

## 性能建议

### 小数据集（<1000行）

```python
# 直接操作，无需优化
result = clean_data(df, drop_na=True)
```

### 中等数据集（1000-10000行）

```python
# 使用query表达式筛选
result = filter_data(df, "age > 30 and city == 'New York'")
```

### 大数据集（>10000行）

```python
# 分批处理
chunk_size = 5000
for i in range(0, len(df), chunk_size):
    chunk = df[i:i+chunk_size]
    result = clean_data(chunk, drop_na=True)
    # 处理结果...
```

---

## 常见问题

### Q1: 如何处理大文件？

```python
# 使用chunksize参数
result = load_csv(
    "/path/to/large.csv",
    nrows=1000  # 只读取前1000行
)
```

### Q2: 如何保存处理后的数据？

```python
# 保存为CSV
result = data_transformation_handler(
    operation="to_csv",
    data=df,
    params={"output_path": "/path/to/output.csv"}
)
```

### Q3: 如何处理Excel文件？

```python
from core.tools.data_transformation_handler import load_excel

result = load_excel(
    "/path/to/file.xlsx",
    sheet_name="Sheet1",  # 工作表名称
    header=0              # 标题行
)
```

### Q4: 如何获取工具的详细信息？

```python
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()
tool = registry.get("data_transformation")

print(tool.metadata)
```

---

## 相关资源

- **完整文档**: `docs/reports/DATA_TRANSFORMATION_TOOL_VERIFICATION_REPORT_20260419.md`
- **测试代码**: `tests/test_data_transformation_tool.py`
- **使用示例**: `examples/data_transformation_example.py`
- **API文档**: `docs/api/DATA_TRANSFORMATION_API.md`

---

**需要帮助？**

- 查看示例代码: `examples/data_transformation_example.py`
- 运行测试: `pytest tests/test_data_transformation_tool.py -v`
- 查看日志: 日志级别设置为DEBUG查看详细操作信息

---

**最后更新**: 2026-04-19
**维护者**: Athena平台团队
