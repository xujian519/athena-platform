#!/usr/bin/env python3
from __future__ import annotations
"""
Excel表格解析和导出模块 - Athena平台集成版
Excel Table Parser and Export Module - Athena Platform Integration

提供Excel相关的功能:
1. Markdown表格转Excel
2. 数据分析结果导出
3. 表格格式化

集成时间: 2025-12-24
版本: v1.0.0 "深度集成"
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Excel导出器"""

    def __init__(self, output_dir: str | None = None):
        """
        初始化Excel导出器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir or "/tmp"
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def export_markdown_table(
        self,
        markdown_table: str,
        sheet_name: str = "Sheet1",
        output_filename: str | None = None,
        keep_formatting: bool = True,
    ) -> str | None:
        """
        导出Markdown表格到Excel

        Args:
            markdown_table: Markdown格式的表格
            sheet_name: 工作表名称
            output_filename: 输出文件名
            keep_formatting: 是否保留格式(粗体、代码等)

        Returns:
            生成的Excel文件路径
        """
        try:
            pass
        except ImportError:
            logger.error("❌ 需要安装pandas: pip install pandas openpyxl")
            return None

        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"table_{timestamp}"

        output_path = Path(self.output_dir) / f"{output_filename}.xlsx"

        try:
            # 解析Markdown表格
            table_data = self._parse_markdown_table(markdown_table)
            if not table_data:
                logger.error("❌ 无法解析Markdown表格")
                return None

            # 创建DataFrame
            headers = table_data[0]
            rows = table_data[1:] if len(table_data) > 1 else []

            df = pd.DataFrame(rows, columns=headers)

            # 导出到Excel
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # 如果需要保留格式,添加格式化
                if keep_formatting:
                    self._apply_formatting(writer, df)

            logger.info(f"✅ 表格导出成功: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"❌ 表格导出失败: {e}")
            return None

    def _parse_markdown_table(self, markdown_table: str) -> list[list[str | None]]:
        """
        解析Markdown表格

        Args:
            markdown_table: Markdown表格字符串

        Returns:
            解析后的表格数据(二维列表)
        """
        lines = markdown_table.strip().split("\n")
        data = []

        for line in lines:
            line = line.strip()
            if not line.startswith("|"):
                continue

            # 移除首尾的|,分割单元格
            cells = [cell.strip() for cell in line.strip("|").split("|")]

            # 过滤分隔行
            if cells and all(cell.startswith("---") for cell in cells if cell):
                continue

            if cells:
                data.append(cells)

        return data if len(data) >= 2 else None

    def _apply_formatting(self, writer, df) -> None:
        """
        应用格式化到Excel

        Args:
            writer: ExcelWriter对象
            df: DataFrame对象
        """
        try:
            from openpyxl.styles import Font, PatternFill

            # 获取工作簿和工作表
            book = writer.book
            sheet = book.active

            # 设置表头格式
            header_fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            header_font = Font(bold=True)

            for cell in sheet[1]:
                cell.fill = header_fill
                cell.font = header_font

        except Exception as e:
            logger.warning(f"⚠️  格式化失败(非关键错误): {e}")

    def export_data_analysis(
        self,
        data: list[dict] | dict | str,
        output_filename: str | None = None,
        sheet_name: str = "数据分析",
    ) -> str | None:
        """
        导出数据分析结果到Excel

        Args:
            data: 数据(字典列表、字典或JSON字符串)
            output_filename: 输出文件名
            sheet_name: 工作表名称

        Returns:
            生成的Excel文件路径
        """
        try:
            pass
        except ImportError:
            logger.error("❌ 需要安装pandas: pip install pandas openpyxl")
            return None

        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"analysis_{timestamp}"

        output_path = Path(self.output_dir) / f"{output_filename}.xlsx"

        try:
            # 解析数据
            if isinstance(data, str):
                # JSON字符串
                parsed_data = json.loads(data)
                if isinstance(parsed_data, list):
                    df = pd.DataFrame(parsed_data)
                elif isinstance(parsed_data, dict):
                    df = pd.DataFrame([parsed_data])
                else:
                    logger.error("❌ 不支持的JSON数据格式")
                    return None
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                logger.error("❌ 不支持的数据格式")
                return None

            # 导出到Excel
            df.to_excel(output_path, sheet_name=sheet_name, index=False, engine="openpyxl")

            logger.info(f"✅ 数据分析导出成功: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"❌ 数据分析导出失败: {e}")
            return None

    def export_multiple_sheets(
        self, sheets_data: dict[str, list[dict] | str | None], output_filename: str | None = None
    ) -> str | None:
        """
        导出多个工作表到一个Excel文件

        Args:
            sheets_data: {工作表名: 数据}
            output_filename: 输出文件名

        Returns:
            生成的Excel文件路径
        """
        try:
            pass
        except ImportError:
            logger.error("❌ 需要安装pandas: pip install pandas openpyxl")
            return None

        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"multi_sheet_{timestamp}"

        output_path = Path(self.output_dir) / f"{output_filename}.xlsx"

        try:
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                for sheet_name, data in sheets_data.items():
                    # 解析数据
                    if isinstance(data, str):
                        data = json.loads(data)
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    elif isinstance(data, dict):
                        df = pd.DataFrame([data])
                    else:
                        continue

                    # 导出到工作表
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            logger.info(f"✅ 多工作表导出成功: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"❌ 多工作表导出失败: {e}")
            return None


# 单例实例
_excel_exporter_instance = None


def get_excel_exporter(output_dir: str | None | None = None) -> ExcelExporter:
    """获取Excel导出器单例"""
    global _excel_exporter_instance
    if _excel_exporter_instance is None:
        _excel_exporter_instance = ExcelExporter(output_dir)
    return _excel_exporter_instance


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Excel导出器测试")
    print("=" * 60)

    exporter = ExcelExporter()

    # 测试Markdown表格
    test_table = """
| 专利号 | 标题 | 状态 |
|--------|------|------|
| CN123456 | 一种新型装置 | 审中 |
| CN789012 | 智能控制系统 | 已授权 |
"""

    print("\n📊 测试表格导出...")
    result = exporter.export_markdown_table(test_table)
    if result:
        print(f"✅ 导出成功: {result}")

    print("\n" + "=" * 60)
