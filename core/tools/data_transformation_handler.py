#!/usr/bin/env python3
"""
数据转换工具Handler (Data Transformation Handler)

将DataTransformationTool封装为工具系统Handler。

Author: Athena平台团队
Created: 2026-04-19
Version: v1.0.0
"""

from __future__ import annotations

import json
import logging
from typing import Any

from core.logging_config import setup_logging
from core.tools.data_transformation_tool import (
    DataTransformationTool,
    TransformationRequest,
    TransformationResult,
)

# 配置日志
logger = setup_logging()


def data_transformation_handler(operation: str, **kwargs) -> dict[str, Any]:
    """
    数据转换工具Handler

    Args:
        operation: 操作类型（必需）
        **kwargs: 其他参数
            - data: 输入数据（可选）
            - params: 操作参数（可选）

    Returns:
        dict: 操作结果
            - success: bool - 操作是否成功
            - data: Any - 转换后的数据
            - metadata: dict - 元数据信息
            - error: Optional[str] - 错误信息

    Examples:
        >>> # 加载CSV文件
        >>> result = data_transformation_handler(
        ...     operation="load_csv",
        ...     params={"file_path": "/path/to/file.csv"}
        ... )

        >>> # 筛选数据
        >>> result = data_transformation_handler(
        ...     operation="filter",
        ...     data=df,  # DataFrame对象
        ...     params={"conditions": {"column_name": "value"}}
        ... )

        >>> # 数据清洗
        >>> result = data_transformation_handler(
        ...     operation="clean",
        ...     data=df,
        ...     params={"drop_na": True, "drop_duplicates": True}
        ... )
    """
    try:
        # 获取工具实例
        tool = DataTransformationTool()

        # 提取参数
        data = kwargs.get("data")
        params = kwargs.get("params", {})

        # 创建转换请求
        request = TransformationRequest(operation=operation, data=data, params=params)

        # 执行转换
        result: TransformationResult = tool.execute(request)

        # 处理DataFrame数据（转换为字典或JSON）
        response_data = None
        if result.data is not None:
            try:
                # 尝试导入pandas
                import pandas as pd

                if isinstance(result.data, pd.DataFrame):
                    # 转换DataFrame为字典
                    response_data = {
                        "type": "DataFrame",
                        "shape": list(result.data.shape),  # 转换为列表
                        "columns": result.data.columns.tolist(),
                        "data": result.data.to_dict(orient="records"),
                    }
                elif isinstance(result.data, pd.Series):
                    # 转换Series为字典
                    response_data = {
                        "type": "Series",
                        "data": result.data.to_dict(),
                    }
                else:
                    # 其他类型直接使用
                    response_data = result.data
            except ImportError:
                # pandas未安装，直接返回数据
                response_data = result.data

        # 构建响应
        response = {
            "success": result.success,
            "data": response_data,
            "metadata": result.metadata,
            "error": result.error,
            "tool": {
                "name": tool.name,
                "description": tool.description,
                "version": tool.version,
            },
        }

        # 记录日志
        if result.success:
            logger.info(f"✅ 数据转换成功: {operation}")
            if result.metadata:
                logger.debug(f"   元数据: {result.metadata}")
        else:
            logger.error(f"❌ 数据转换失败: {operation} - {result.error}")

        return response

    except Exception as e:
        logger.error(f"数据转换Handler异常: {e}", exc_info=True)
        return {
            "success": False,
            "data": None,
            "metadata": {},
            "error": f"Handler异常: {str(e)}",
            "tool": {
                "name": "data_transformation",
                "description": "数据转换和格式化工具",
                "version": "1.0.0",
            },
        }


# 创建便捷函数
def load_csv(file_path: str, **kwargs) -> dict[str, Any]:
    """加载CSV文件"""
    return data_transformation_handler(
        operation="load_csv", params={"file_path": file_path, **kwargs}
    )


def load_excel(file_path: str, **kwargs) -> dict[str, Any]:
    """加载Excel文件"""
    return data_transformation_handler(
        operation="load_excel", params={"file_path": file_path, **kwargs}
    )


def filter_data(data: Any, conditions: dict[str, Any] | str, **kwargs) -> dict[str, Any]:
    """筛选数据"""
    return data_transformation_handler(
        operation="filter", data=data, params={"conditions": conditions, **kwargs}
    )


def sort_data(data: Any, columns: str | list[str], **kwargs) -> dict[str, Any]:
    """排序数据"""
    return data_transformation_handler(
        operation="sort", data=data, params={"columns": columns, **kwargs}
    )


def clean_data(
    data: Any,
    drop_na: bool = False,
    drop_duplicates: bool = False,
    fill_value: Any = None,
    **kwargs,
) -> dict[str, Any]:
    """清洗数据"""
    return data_transformation_handler(
        operation="clean",
        data=data,
        params={
            "drop_na": drop_na,
            "drop_duplicates": drop_duplicates,
            "fill_value": fill_value,
            **kwargs,
        },
    )


def aggregate_data(data: Any, agg_func: str | dict, **kwargs) -> dict[str, Any]:
    """聚合数据"""
    return data_transformation_handler(
        operation="aggregate", data=data, params={"agg_func": agg_func, **kwargs}
    )


def merge_data(data: Any, other: Any, on: str | Optional[list[str]] = None, **kwargs) -> dict[str, Any]:
    """合并数据"""
    return data_transformation_handler(
        operation="merge", data=data, params={"other": other, "on": on, **kwargs}
    )


def get_statistics(data: Any) -> dict[str, Any]:
    """获取统计信息"""
    return data_transformation_handler(operation="get_statistics", data=data)


def get_info(data: Any) -> dict[str, Any]:
    """获取数据信息"""
    return data_transformation_handler(operation="get_info", data=data)


# 导出
__all__ = [
    "data_transformation_handler",
    "load_csv",
    "load_excel",
    "filter_data",
    "sort_data",
    "clean_data",
    "aggregate_data",
    "merge_data",
    "get_statistics",
    "get_info",
]
