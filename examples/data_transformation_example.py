#!/usr/bin/env python3
"""
数据转换工具使用示例

演示如何使用data_transformation工具进行各种数据操作。

Author: Athena平台团队
Created: 2026-04-19
Version: v1.0.0
"""

import tempfile
from pathlib import Path

import pandas as pd

from core.tools.data_transformation_handler import (
    aggregate_data,
    clean_data,
    data_transformation_handler,
    get_info,
    get_statistics,
    load_csv,
    merge_data,
    sort_data,
)


def example_1_basic_operations():
    """示例1：基本操作"""
    print("=" * 60)
    print("示例1：基本数据操作")
    print("=" * 60)

    # 创建示例数据
    data = {
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "age": [25, 30, 35, 28, 32],
        "city": ["New York", "London", "Paris", "Tokyo", "Berlin"],
        "salary": [50000, 60000, 70000, 55000, 65000],
    }
    df = pd.DataFrame(data)

    print("\n1. 原始数据信息:")
    info = get_info(df)
    if info["success"]:
        print(f"   形状: {info['data']['shape']}")
        print(f"   列: {info['data']['columns']}")

    print("\n2. 统计信息:")
    stats = get_statistics(df)
    if stats["success"]:
        print(f"   平均年龄: {stats['data']['age']['mean']:.2f}")
        print(f"   平均薪资: {stats['data']['salary']['mean']:.2f}")

    print("\n3. 筛选数据（年龄 > 30）:")
    # 使用query表达式筛选
    filter_result = data_transformation_handler(
        operation="filter", data=df, params={"conditions": "age > 30"}
    )
    if filter_result["success"]:
        filtered_df = pd.DataFrame(filter_result["data"]["data"])
        print(f"   筛选后行数: {len(filtered_df)}")
        print(f"   筛选后数据:\n{filtered_df}")

    print("\n4. 排序（按薪资降序）:")
    sort_result = sort_data(df, "salary", ascending=False)
    if sort_result["success"]:
        sorted_df = pd.DataFrame(sort_result["data"]["data"])
        print("   排序后数据:")
        print(sorted_df[["name", "salary"])


def example_2_data_cleaning():
    """示例2：数据清洗"""
    print("\n" + "=" * 60)
    print("示例2：数据清洗")
    print("=" * 60)

    # 创建包含缺失值和重复数据的DataFrame
    data = {
        "name": ["Alice", "Bob", None, "Alice", "Charlie"],
        "age": [25, 30, 35, 25, None],
        "city": ["NY", "London", "Paris", "NY", "Tokyo"],
        "salary": [50000, None, 70000, 55000, 65000],
    }
    df = pd.DataFrame(data)

    print("\n1. 原始数据:")
    print(df)

    print("\n2. 清洗数据（删除空值和重复行）:")
    clean_result = clean_data(df, drop_na=True, drop_duplicates=True)
    if clean_result["success"]:
        clean_df = pd.DataFrame(clean_result["data"]["data"])
        print(f"   清洗前行数: {clean_result['metadata']['original_rows']}")
        print(f"   清洗后行数: {clean_result['metadata']['cleaned_rows']}")
        print(f"   清洗后数据:\n{clean_df}")


def example_3_csv_operations():
    """示例3：CSV文件操作"""
    print("\n" + "=" * 60)
    print("示例3：CSV文件操作")
    print("=" * 60)

    # 创建临时CSV文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        csv_path = f.name
        data = {
            "product": ["A", "B", "C", "D"],
            "price": [100, 200, 150, 300],
            "quantity": [10, 5, 8, 3],
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

    print(f"\n1. 创建CSV文件: {csv_path}")

    print("\n2. 加载CSV文件:")
    load_result = load_csv(csv_path)
    if load_result["success"]:
        loaded_df = pd.DataFrame(load_result["data"]["data"])
        print("   加载成功！")
        print(f"   数据:\n{loaded_df}")

    print("\n3. 计算总价（price * quantity）:")
    # 使用transform操作添加列
    transform_result = data_transformation_handler(
        operation="add_column",
        data=loaded_df,
        params={"column_name": "total", "values": loaded_df["price"] * loaded_df["quantity"]},
    )
    if transform_result["success"]:
        transformed_df = pd.DataFrame(transform_result["data"]["data"])
        print(f"   转换后数据:\n{transformed_df}")

    # 清理临时文件
    Path(csv_path).unlink()


def example_4_data_aggregation():
    """示例4：数据聚合"""
    print("\n" + "=" * 60)
    print("示例4：数据聚合")
    print("=" * 60)

    # 创建示例数据
    data = {
        "department": ["HR", "IT", "HR", "IT", "Finance", "HR"],
        "employee": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"],
        "salary": [50000, 70000, 55000, 75000, 60000, 52000],
    }
    df = pd.DataFrame(data)

    print("\n1. 原始数据:")
    print(df)

    print("\n2. 按部门分组并计算平均薪资:")
    agg_result = data_transformation_handler(
        operation="group_by", data=df, params={"group_by": "department", "agg_func": "mean"}
    )
    if agg_result["success"]:
        print("   聚合成功！")
        print(f"   分组数: {agg_result['metadata']['groups']}")
        # 注意：group_by返回的是分组后的数据
        print(f"   聚合数据类型: {type(agg_result['data'])}")

    print("\n3. 计算总体统计:")
    agg_result = aggregate_data(df, "mean")
    if agg_result["success"]:
        # aggregate返回的是Series的字典表示
        series_data = agg_result["data"]["data"]
        print(f"   平均薪资: {series_data['salary']:.2f}")


def example_5_data_merge():
    """示例5：数据合并"""
    print("\n" + "=" * 60)
    print("示例5：数据合并")
    print("=" * 60)

    # 创建两个DataFrame
    df1 = pd.DataFrame(
        {"employee_id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "dept": ["HR", "IT", "Finance"]}
    )

    df2 = pd.DataFrame(
        {"employee_id": [1, 2, 4], "salary": [50000, 60000, 70000], "city": ["NY", "London", "Paris"]}
    )

    print("\n1. 第一个表（员工信息）:")
    print(df1)

    print("\n2. 第二个表（薪资信息）:")
    print(df2)

    print("\n3. 合并两个表（inner join）:")
    merge_result = merge_data(df1, df2, on="employee_id", how="inner")
    if merge_result["success"]:
        merged_df = pd.DataFrame(merge_result["data"]["data"])
        print("   合并成功！")
        print(f"   合并后行数: {merge_result['metadata']['merged_rows']}")
        print(f"   合并后数据:\n{merged_df}")


def example_6_tool_registry():
    """示例6：从工具注册表获取工具"""
    print("\n" + "=" * 60)
    print("示例6：从工具注册表获取工具")
    print("=" * 60)

    try:
        from core.tools.unified_registry import get_unified_registry

        registry = get_unified_registry()

        # 检查工具是否已注册
        tool = registry.get("data_transformation")

        if tool:
            print("\n✅ 工具已成功注册到统一工具注册表！")
            # tool是函数，获取其元数据
            if hasattr(tool, "metadata"):
                metadata = tool.metadata
                print(f"   工具名称: {metadata.get('name', 'N/A')}")
                print(f"   工具描述: {metadata.get('description', 'N/A')}")
                print(f"   工具版本: {metadata.get('version', 'N/A')}")
                operations = metadata.get('supported_operations', [])
                print(f"   支持的操作数: {len(operations)}")
                print(f"   主要操作: {', '.join(operations[:5])}")
                if len(operations) > 5:
                    print(f"              {', '.join(operations[5:10])}")
                    if len(operations) > 10:
                        print(f"              ... (还有{len(operations)-10}个)")
            else:
                print(f"   工具对象: {tool}")
        else:
            print("\n❌ 工具未找到")

    except Exception as e:
        print(f"\n❌ 获取工具注册表失败: {e}")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("数据转换工具使用示例")
    print("=" * 60)

    try:
        example_1_basic_operations()
        example_2_data_cleaning()
        example_3_csv_operations()
        example_4_data_aggregation()
        example_5_data_merge()
        example_6_tool_registry()

        print("\n" + "=" * 60)
        print("✅ 所有示例运行完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
