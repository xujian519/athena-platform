#!/usr/bin/env python3
"""
数据转换工具 (Data Transformation Tool)

提供基于pandas的数据转换、清洗和格式化功能。

Author: Athena平台团队
Created: 2026-04-19
Version: v1.0.0
"""

from __future__ import annotations

import io
import logging
import os
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, field_validator

from core.logging_config import setup_logging

# 配置日志
logger = setup_logging()


class TransformationRequest(BaseModel):
    """数据转换请求模型"""

    operation: str = Field(
        ...,
        description="转换操作类型: load_csv, load_excel, to_csv, to_excel, "
        "filter, sort, group_by, merge, pivot, clean, aggregate",
    )
    data: Any = Field(None, description="输入数据(可以是DataFrame、字典、文件路径等)")
    params: dict[str, Any] = Field(default_factory=dict, description="操作参数")

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v):
        """验证操作类型"""
        valid_operations = [
            "load_csv",
            "load_excel",
            "to_csv",
            "to_excel",
            "filter",
            "sort",
            "group_by",
            "merge",
            "pivot",
            "clean",
            "aggregate",
            "transform",
            "drop_duplicates",
            "fill_na",
            "rename_columns",
            "add_column",
            "delete_column",
            "get_statistics",
            "get_info",
        ]
        if v not in valid_operations:
            raise ValueError(f"无效的操作类型: {v}. 支持的操作: {', '.join(valid_operations)}")
        return v


class TransformationResult(BaseModel):
    """数据转换结果模型"""

    success: bool = Field(..., description="操作是否成功")
    data: Any = Field(None, description="转换后的数据")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据信息")
    error: str | None = Field(None, description="错误信息")


class DataTransformationTool:
    """
    数据转换工具类

    提供常用的数据转换和格式化功能，基于pandas实现。
    """

    def __init__(self):
        """初始化工具"""
        self.name = "data_transformation"
        self.description = "数据转换和格式化工具（基于pandas）"
        self.version = "1.0.0"
        self.logger = logger

    def execute(self, request: TransformationRequest) -> TransformationResult:
        """
        执行数据转换操作

        Args:
            request: 转换请求对象

        Returns:
            转换结果对象
        """
        try:
            # 根据操作类型调用相应方法
            operation = request.operation

            if operation == "load_csv":
                result = self._load_csv(request.params)
            elif operation == "load_excel":
                result = self._load_excel(request.params)
            elif operation == "to_csv":
                result = self._to_csv(request.data, request.params)
            elif operation == "to_excel":
                result = self._to_excel(request.data, request.params)
            elif operation == "filter":
                result = self._filter(request.data, request.params)
            elif operation == "sort":
                result = self._sort(request.data, request.params)
            elif operation == "group_by":
                result = self._group_by(request.data, request.params)
            elif operation == "merge":
                result = self._merge(request.data, request.params)
            elif operation == "pivot":
                result = self._pivot(request.data, request.params)
            elif operation == "clean":
                result = self._clean(request.data, request.params)
            elif operation == "aggregate":
                result = self._aggregate(request.data, request.params)
            elif operation == "transform":
                result = self._transform(request.data, request.params)
            elif operation == "drop_duplicates":
                result = self._drop_duplicates(request.data, request.params)
            elif operation == "fill_na":
                result = self._fill_na(request.data, request.params)
            elif operation == "rename_columns":
                result = self._rename_columns(request.data, request.params)
            elif operation == "add_column":
                result = self._add_column(request.data, request.params)
            elif operation == "delete_column":
                result = self._delete_column(request.data, request.params)
            elif operation == "get_statistics":
                result = self._get_statistics(request.data)
            elif operation == "get_info":
                result = self._get_info(request.data)
            else:
                result = TransformationResult(
                    success=False, error=f"不支持的操作: {operation}"
                )

            return result

        except Exception as e:
            self.logger.error(f"数据转换失败: {e}", exc_info=True)
            return TransformationResult(success=False, error=str(e))

    def _ensure_dataframe(self, data: Any) -> pd.DataFrame:
        """确保数据是DataFrame格式"""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            return pd.DataFrame(data)
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            raise ValueError(f"不支持的数据类型: {type(data)}")

    # ==================== 数据加载操作 ====================

    def _load_csv(self, params: dict[str, Any]) -> TransformationResult:
        """加载CSV文件"""
        try:
            file_path = params.get("file_path")
            if not file_path:
                return TransformationResult(success=False, error="缺少file_path参数")

            # 读取CSV
            df = pd.read_csv(
                file_path,
                encoding=params.get("encoding", "utf-8"),
                sep=params.get("sep", ","),
                header=params.get("header", 0),
                nrows=params.get("nrows"),
            )

            return TransformationResult(
                success=True,
                data=df,
                metadata={
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist(),
                },
            )
        except Exception as e:
            return TransformationResult(success=False, error=f"加载CSV失败: {e}")

    def _load_excel(self, params: dict[str, Any]) -> TransformationResult:
        """加载Excel文件"""
        try:
            file_path = params.get("file_path")
            if not file_path:
                return TransformationResult(success=False, error="缺少file_path参数")

            # 读取Excel
            df = pd.read_excel(
                file_path,
                sheet_name=params.get("sheet_name", 0),
                header=params.get("header", 0),
                nrows=params.get("nrows"),
            )

            return TransformationResult(
                success=True,
                data=df,
                metadata={
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist(),
                },
            )
        except Exception as e:
            return TransformationResult(success=False, error=f"加载Excel失败: {e}")

    # ==================== 数据导出操作 ====================

    def _to_csv(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """导出为CSV"""
        try:
            df = self._ensure_dataframe(data)
            output_path = params.get("output_path")

            if output_path:
                # 保存到文件
                df.to_csv(output_path, index=params.get("index", False), encoding="utf-8")
                return TransformationResult(
                    success=True, metadata={"output_path": output_path, "rows": len(df)}
                )
            else:
                # 返回CSV字符串
                output = io.StringIO()
                df.to_csv(output, index=params.get("index", False))
                return TransformationResult(success=True, data=output.getvalue())

        except Exception as e:
            return TransformationResult(success=False, error=f"导出CSV失败: {e}")

    def _to_excel(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """导出为Excel"""
        try:
            df = self._ensure_dataframe(data)
            output_path = params.get("output_path")

            if not output_path:
                return TransformationResult(success=False, error="缺少output_path参数")

            df.to_excel(output_path, index=params.get("index", False))
            return TransformationResult(
                success=True, metadata={"output_path": output_path, "rows": len(df)}
            )

        except Exception as e:
            return TransformationResult(success=False, error=f"导出Excel失败: {e}")

    # ==================== 数据筛选操作 ====================

    def _filter(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """筛选数据"""
        try:
            df = self._ensure_dataframe(data)
            conditions = params.get("conditions")

            if not conditions:
                return TransformationResult(success=False, error="缺少conditions参数")

            # 支持多种筛选方式
            if isinstance(conditions, str):
                # 使用query表达式
                filtered_df = df.query(conditions)
            elif isinstance(conditions, dict):
                # 使用字典条件
                mask = pd.Series([True] * len(df))
                for col, value in conditions.items():
                    if col in df.columns:
                        mask &= df[col] == value
                filtered_df = df[mask]
            elif callable(conditions):
                # 使用函数
                filtered_df = df[df.apply(conditions, axis=1)]
            else:
                return TransformationResult(success=False, error="不支持的conditions类型")

            return TransformationResult(
                success=True,
                data=filtered_df,
                metadata={
                    "original_rows": len(df),
                    "filtered_rows": len(filtered_df),
                },
            )

        except Exception as e:
            return TransformationResult(success=False, error=f"筛选数据失败: {e}")

    def _sort(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """排序数据"""
        try:
            df = self._ensure_dataframe(data)
            columns = params.get("columns")
            ascending = params.get("ascending", True)

            if not columns:
                return TransformationResult(success=False, error="缺少columns参数")

            if isinstance(columns, str):
                columns = [columns]

            sorted_df = df.sort_values(by=columns, ascending=ascending)
            return TransformationResult(success=True, data=sorted_df)

        except Exception as e:
            return TransformationResult(success=False, error=f"排序数据失败: {e}")

    # ==================== 数据聚合操作 ====================

    def _group_by(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """分组聚合"""
        try:
            df = self._ensure_dataframe(data)
            group_by = params.get("group_by")
            agg_func = params.get("agg_func", "mean")

            if not group_by:
                return TransformationResult(success=False, error="缺少group_by参数")

            if isinstance(group_by, str):
                group_by = [group_by]

            # 只对数值列进行聚合
            numeric_df = df.select_dtypes(include=["number"])
            grouped = numeric_df.groupby(df[group_by[0]]).agg(agg_func)
            return TransformationResult(
                success=True, data=grouped, metadata={"groups": len(grouped)}
            )

        except Exception as e:
            return TransformationResult(success=False, error=f"分组聚合失败: {e}")

    def _aggregate(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """聚合操作"""
        try:
            df = self._ensure_dataframe(data)
            agg_func = params.get("agg_func")

            if not agg_func:
                return TransformationResult(success=False, error="缺少agg_func参数")

            # 只对数值列进行聚合
            numeric_df = df.select_dtypes(include=["number"])

            if isinstance(agg_func, str):
                result = numeric_df.agg(agg_func)
            elif isinstance(agg_func, dict):
                result = numeric_df.agg(agg_func)
            else:
                return TransformationResult(success=False, error="不支持的agg_func类型")

            return TransformationResult(success=True, data=result)

        except Exception as e:
            return TransformationResult(success=False, error=f"聚合操作失败: {e}")

    # ==================== 数据合并操作 ====================

    def _merge(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """合并数据"""
        try:
            df = self._ensure_dataframe(data)
            other = params.get("other")
            on = params.get("on")
            how = params.get("how", "inner")

            if other is None:
                return TransformationResult(success=False, error="缺少other参数")

            other_df = self._ensure_dataframe(other)

            if on:
                merged_df = df.merge(other_df, on=on, how=how)
            else:
                merged_df = df.merge(other_df, how=how)

            return TransformationResult(
                success=True,
                data=merged_df,
                metadata={
                    "left_rows": len(df),
                    "right_rows": len(other_df),
                    "merged_rows": len(merged_df),
                },
            )

        except Exception as e:
            return TransformationResult(success=False, error=f"合并数据失败: {e}")

    # ==================== 数据重塑操作 ====================

    def _pivot(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """透视表"""
        try:
            df = self._ensure_dataframe(data)
            index = params.get("index")
            columns = params.get("columns")
            values = params.get("values")

            if not all([index, columns, values]):
                return TransformationResult(
                    success=False, error="缺少必要参数(index, columns, values)"
                )

            pivoted_df = df.pivot_table(
                index=index, columns=columns, values=values, aggfunc="mean"
            )
            return TransformationResult(success=True, data=pivoted_df)

        except Exception as e:
            return TransformationResult(success=False, error=f"创建透视表失败: {e}")

    # ==================== 数据清洗操作 ====================

    def _clean(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """数据清洗"""
        try:
            df = self._ensure_dataframe(data)
            cleaned_df = df.copy()

            # 删除空值
            if params.get("drop_na", False):
                cleaned_df = cleaned_df.dropna()

            # 删除重复行
            if params.get("drop_duplicates", False):
                cleaned_df = cleaned_df.drop_duplicates()

            # 填充空值
            fill_value = params.get("fill_value")
            if fill_value is not None:
                cleaned_df = cleaned_df.fillna(fill_value)

            # 去除字符串空格
            strip_columns = params.get("strip_columns")
            if strip_columns:
                for col in strip_columns:
                    if col in cleaned_df.columns:
                        cleaned_df[col] = cleaned_df[col].astype(str).str.strip()

            return TransformationResult(
                success=True,
                data=cleaned_df,
                metadata={
                    "original_rows": len(df),
                    "cleaned_rows": len(cleaned_df),
                },
            )

        except Exception as e:
            return TransformationResult(success=False, error=f"数据清洗失败: {e}")

    def _drop_duplicates(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """删除重复行"""
        try:
            df = self._ensure_dataframe(data)
            subset = params.get("subset")
            keep = params.get("keep", "first")

            deduplicated_df = df.drop_duplicates(subset=subset, keep=keep)
            return TransformationResult(
                success=True,
                data=deduplicated_df,
                metadata={
                    "original_rows": len(df),
                    "removed_rows": len(df) - len(deduplicated_df),
                },
            )

        except Exception as e:
            return TransformationResult(success=False, error=f"删除重复行失败: {e}")

    def _fill_na(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """填充空值"""
        try:
            df = self._ensure_dataframe(data)
            value = params.get("value")
            method = params.get("method")

            if method:
                filled_df = df.fillna(method=method)
            elif value is not None:
                filled_df = df.fillna(value)
            else:
                return TransformationResult(success=False, error="缺少value或method参数")

            return TransformationResult(
                success=True,
                data=filled_df,
                metadata={"na_count_before": df.isna().sum().sum()},
            )

        except Exception as e:
            return TransformationResult(success=False, error=f"填充空值失败: {e}")

    # ==================== 列操作 ====================

    def _rename_columns(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """重命名列"""
        try:
            df = self._ensure_dataframe(data)
            columns = params.get("columns")

            if not columns:
                return TransformationResult(success=False, error="缺少columns参数")

            renamed_df = df.rename(columns=columns)
            return TransformationResult(success=True, data=renamed_df)

        except Exception as e:
            return TransformationResult(success=False, error=f"重命名列失败: {e}")

    def _add_column(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """添加列"""
        try:
            df = self._ensure_dataframe(data)
            column_name = params.get("column_name")
            values = params.get("values")

            if not column_name or values is None:
                return TransformationResult(success=False, error="缺少column_name或values参数")

            df[column_name] = values
            return TransformationResult(success=True, data=df)

        except Exception as e:
            return TransformationResult(success=False, error=f"添加列失败: {e}")

    def _delete_column(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """删除列"""
        try:
            df = self._ensure_dataframe(data)
            columns = params.get("columns")

            if not columns:
                return TransformationResult(success=False, error="缺少columns参数")

            if isinstance(columns, str):
                columns = [columns]

            modified_df = df.drop(columns=columns)
            return TransformationResult(success=True, data=modified_df)

        except Exception as e:
            return TransformationResult(success=False, error=f"删除列失败: {e}")

    # ==================== 数据转换操作 ====================

    def _transform(self, data: Any, params: dict[str, Any]) -> TransformationResult:
        """自定义转换"""
        try:
            df = self._ensure_dataframe(data)
            transform_func = params.get("function")

            if not transform_func:
                return TransformationResult(success=False, error="缺少function参数")

            if callable(transform_func):
                transformed_df = transform_func(df)
            else:
                return TransformationResult(success=False, error="function必须是可调用对象")

            return TransformationResult(success=True, data=transformed_df)

        except Exception as e:
            return TransformationResult(success=False, error=f"数据转换失败: {e}")

    # ==================== 数据分析操作 ====================

    def _get_statistics(self, data: Any) -> TransformationResult:
        """获取统计信息"""
        try:
            df = self._ensure_dataframe(data)
            stats = df.describe()
            return TransformationResult(
                success=True,
                data=stats.to_dict(),
                metadata={"columns_analyzed": len(stats.columns)},
            )

        except Exception as e:
            return TransformationResult(success=False, error=f"获取统计信息失败: {e}")

    def _get_info(self, data: Any) -> TransformationResult:
        """获取数据信息"""
        try:
            df = self._ensure_dataframe(data)
            info = {
                "shape": list(df.shape),  # 转换为列表以兼容JSON序列化
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "memory_usage": int(df.memory_usage(deep=True).sum()),
                "null_counts": df.isna().sum().to_dict(),
            }
            return TransformationResult(success=True, data=info)

        except Exception as e:
            return TransformationResult(success=False, error=f"获取数据信息失败: {e}")


# 创建全局工具实例
_data_transformation_tool = None


def get_data_transformation_tool() -> DataTransformationTool:
    """获取数据转换工具单例"""
    global _data_transformation_tool
    if _data_transformation_tool is None:
        _data_transformation_tool = DataTransformationTool()
    return _data_transformation_tool
