#!/usr/bin/env python3
"""
数据转换工具测试

Author: Athena平台团队
Created: 2026-04-19
Version: v1.0.0
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from core.tools.data_transformation_handler import (
    aggregate_data,
    clean_data,
    data_transformation_handler,
    filter_data,
    get_info,
    get_statistics,
    load_csv,
    load_excel,
    merge_data,
    sort_data,
)
from core.tools.data_transformation_tool import (
    DataTransformationTool,
    TransformationRequest,
)


@pytest.fixture
def sample_dataframe():
    """创建示例DataFrame"""
    return pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "Alice", None],
            "age": [25, 30, 35, 25, 40],
            "city": ["New York", "London", "Paris", "New York", "Tokyo"],
            "salary": [50000, 60000, 70000, 55000, None],
        }
    )


@pytest.fixture
def sample_csv_file(sample_dataframe, tmp_path):
    """创建示例CSV文件"""
    csv_file = tmp_path / "sample.csv"
    sample_dataframe.to_csv(csv_file, index=False)
    return str(csv_file)


@pytest.fixture
def sample_excel_file(sample_dataframe, tmp_path):
    """创建示例Excel文件"""
    excel_file = tmp_path / "sample.xlsx"
    sample_dataframe.to_excel(excel_file, index=False)
    return str(excel_file)


class TestDataTransformationTool:
    """测试DataTransformationTool类"""

    def test_tool_initialization(self):
        """测试工具初始化"""
        tool = DataTransformationTool()
        assert tool.name == "data_transformation"
        assert tool.description == "数据转换和格式化工具（基于pandas）"
        assert tool.version == "1.0.0"

    def test_load_csv(self, sample_csv_file):
        """测试加载CSV文件"""
        tool = DataTransformationTool()
        request = TransformationRequest(operation="load_csv", params={"file_path": sample_csv_file})
        result = tool.execute(request)

        assert result.success
        assert result.data is not None
        assert result.metadata["rows"] == 5
        assert result.metadata["columns"] == 4
        assert len(result.data) == 5

    def test_load_excel(self, sample_excel_file):
        """测试加载Excel文件"""
        tool = DataTransformationTool()
        request = TransformationRequest(
            operation="load_excel", params={"file_path": sample_excel_file}
        )
        result = tool.execute(request)

        assert result.success
        assert result.data is not None
        assert result.metadata["rows"] == 5
        assert result.metadata["columns"] == 4

    def test_filter_data(self, sample_dataframe):
        """测试筛选数据"""
        tool = DataTransformationTool()
        request = TransformationRequest(
            operation="filter", data=sample_dataframe, params={"conditions": {"city": "New York"}}
        )
        result = tool.execute(request)

        assert result.success
        assert len(result.data) == 2
        assert all(result.data["city"] == "New York")

    def test_sort_data(self, sample_dataframe):
        """测试排序数据"""
        tool = DataTransformationTool()
        request = TransformationRequest(
            operation="sort", data=sample_dataframe, params={"columns": "age", "ascending": False}
        )
        result = tool.execute(request)

        assert result.success
        assert result.data["age"].tolist() == [40, 35, 30, 25, 25]

    def test_clean_data(self, sample_dataframe):
        """测试数据清洗"""
        tool = DataTransformationTool()
        request = TransformationRequest(
            operation="clean", data=sample_dataframe, params={"drop_na": True, "drop_duplicates": True}
        )
        result = tool.execute(request)

        assert result.success
        # 应该删除包含None的行和重复行
        assert result.metadata["cleaned_rows"] < result.metadata["original_rows"]

    def test_aggregate_data(self, sample_dataframe):
        """测试数据聚合"""
        tool = DataTransformationTool()
        # 只对数值列进行聚合，避免字符串列的错误
        request = TransformationRequest(
            operation="aggregate", data=sample_dataframe, params={"agg_func": "mean"}
        )
        result = tool.execute(request)

        assert result.success
        assert result.data is not None

    def test_get_statistics(self, sample_dataframe):
        """测试获取统计信息"""
        tool = DataTransformationTool()
        request = TransformationRequest(operation="get_statistics", data=sample_dataframe)
        result = tool.execute(request)

        assert result.success
        assert result.data is not None
        assert isinstance(result.data, dict)

    def test_get_info(self, sample_dataframe):
        """测试获取数据信息"""
        tool = DataTransformationTool()
        request = TransformationRequest(operation="get_info", data=sample_dataframe)
        result = tool.execute(request)

        assert result.success
        assert result.data is not None
        assert "shape" in result.data
        assert "columns" in result.data
        assert result.data["shape"] == [5, 4]  # shape现在是列表

    def test_rename_columns(self, sample_dataframe):
        """测试重命名列"""
        tool = DataTransformationTool()
        request = TransformationRequest(
            operation="rename_columns",
            data=sample_dataframe,
            params={"columns": {"name": "full_name", "age": "years"}},
        )
        result = tool.execute(request)

        assert result.success
        assert "full_name" in result.data.columns
        assert "years" in result.data.columns
        assert "name" not in result.data.columns

    def test_add_column(self, sample_dataframe):
        """测试添加列"""
        tool = DataTransformationTool()
        request = TransformationRequest(
            operation="add_column",
            data=sample_dataframe,
            params={"column_name": "bonus", "values": [5000] * len(sample_dataframe)},
        )
        result = tool.execute(request)

        assert result.success
        assert "bonus" in result.data.columns
        assert len(result.data.columns) == 5

    def test_delete_column(self, sample_dataframe):
        """测试删除列"""
        tool = DataTransformationTool()
        request = TransformationRequest(
            operation="delete_column", data=sample_dataframe, params={"columns": "salary"}
        )
        result = tool.execute(request)

        assert result.success
        assert "salary" not in result.data.columns
        assert len(result.data.columns) == 3


class TestDataTransformationHandler:
    """测试数据转换Handler"""

    def test_handler_load_csv(self, sample_csv_file):
        """测试Handler加载CSV"""
        result = load_csv(sample_csv_file)

        assert result["success"]
        assert result["data"] is not None
        assert result["data"]["type"] == "DataFrame"
        assert result["data"]["shape"] == [5, 4]  # shape现在是列表
        assert result["tool"]["name"] == "data_transformation"

    def test_handler_filter_data(self, sample_dataframe):
        """测试Handler筛选数据"""
        result = filter_data(sample_dataframe, {"city": "New York"})

        assert result["success"]
        assert result["data"]["type"] == "DataFrame"
        assert result["data"]["shape"] == [2, 4]  # shape现在是列表

    def test_handler_sort_data(self, sample_dataframe):
        """测试Handler排序数据"""
        result = sort_data(sample_dataframe, "age", ascending=False)

        assert result["success"]
        assert result["data"]["type"] == "DataFrame"

    def test_handler_clean_data(self, sample_dataframe):
        """测试Handler清洗数据"""
        result = clean_data(sample_dataframe, drop_na=True, drop_duplicates=True)

        assert result["success"]
        assert result["data"]["type"] == "DataFrame"

    def test_handler_aggregate_data(self, sample_dataframe):
        """测试Handler聚合数据"""
        result = aggregate_data(sample_dataframe, "mean")

        assert result["success"]

    def test_handler_get_statistics(self, sample_dataframe):
        """测试Handler获取统计信息"""
        result = get_statistics(sample_dataframe)

        assert result["success"]
        assert result["data"] is not None

    def test_handler_get_info(self, sample_dataframe):
        """测试Handler获取信息"""
        result = get_info(sample_dataframe)

        assert result["success"]
        assert "shape" in result["data"]
        assert result["data"]["shape"] == [5, 4]  # shape现在是列表

    def test_handler_merge_data(self, sample_dataframe):
        """测试Handler合并数据"""
        # 创建第二个DataFrame
        df2 = pd.DataFrame({"name": ["Alice", "Bob"], "department": ["HR", "IT"]})

        result = merge_data(sample_dataframe, df2, on="name")

        assert result["success"]
        assert result["data"]["type"] == "DataFrame"

    def test_handler_invalid_operation(self, sample_dataframe):
        """测试Handler无效操作"""
        result = data_transformation_handler(operation="invalid_operation", data=sample_dataframe)

        assert not result["success"]
        assert result["error"] is not None


class TestDataTransformationIntegration:
    """集成测试：测试完整的数据转换流程"""

    def test_complete_workflow(self, sample_dataframe, tmp_path):
        """测试完整工作流：清洗 -> 筛选 -> 排序 -> 导出"""
        # 1. 清洗数据
        clean_result = clean_data(sample_dataframe, drop_na=True, drop_duplicates=True)
        assert clean_result["success"]

        # 2. 筛选数据（筛选特定城市）
        # 注意：clean_result["data"]是字典，需要重建DataFrame
        import pandas as pd

        clean_df = pd.DataFrame(clean_result["data"]["data"])
        filter_result = filter_data(clean_df, {"city": "London"})
        assert filter_result["success"]

        # 3. 排序
        filter_df = pd.DataFrame(filter_result["data"]["data"])
        sort_result = sort_data(filter_df, "age", ascending=False)
        assert sort_result["success"]

        # 4. 导出为CSV
        sort_df = pd.DataFrame(sort_result["data"]["data"])
        csv_file = tmp_path / "output.csv"
        export_result = data_transformation_handler(
            operation="to_csv",
            data=sort_df,
            params={"output_path": str(csv_file)},
        )
        assert export_result["success"]
        assert csv_file.exists()

    def test_statistics_workflow(self, sample_dataframe):
        """测试统计分析工作流"""
        # 获取统计信息
        stats = get_statistics(sample_dataframe)
        assert stats["success"]

        # 获取数据信息
        info = get_info(sample_dataframe)
        assert info["success"]
        assert info["data"]["shape"] == [5, 4]  # shape现在是列表

        # 验证统计信息
        assert "data" in stats
        assert isinstance(stats["data"], dict)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
