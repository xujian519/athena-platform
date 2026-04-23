#!/usr/bin/env python3
from __future__ import annotations
"""
PasteMD核心模块 - Athena平台深度集成版
PasteMD Core Module - Deep Integration for Athena Platform

基于PasteMD项目核心功能的抽取和封装,为Athena平台提供:
1. Markdown转Word/WPS文档
2. AI对话内容导出
3. 表格数据导出到Excel
4. 公式、代码高亮完美保留

原作者: RICHQAQ (https://github.com/RICHQAQ/PasteMD)
Athena平台集成: 小诺·双鱼公主
集成时间: 2025-12-24
版本: v1.0.0 "深度集成"
"""

import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class PasteMDCore:
    """PasteMD核心功能类"""

    def __init__(self, config: dict | None = None):
        """
        初始化PasteMD核心模块

        Args:
            config: 配置字典,包含pandoc路径、输出目录等
        """
        # 默认配置
        self.config = {
            "pandoc_path": "pandoc",  # Pandoc可执行文件路径
            "output_dir": tempfile.gettempdir(),  # 默认输出目录
            "keep_files": False,  # 是否保留生成的中间文件
            "enable_formula": True,  # 是否启用公式转换
            "enable_code_highlight": True,  # 是否启用代码高亮
            "reference_docx": None,  # 参考模板文档
            "language": "zh",  # 界面语言
        }

        # 合并用户配置
        if config:
            self.config.update(config)

        # 确保输出目录存在
        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)

        logger.info("✅ PasteMD核心模块初始化完成")

    def _check_pandoc(self) -> bool:
        """检查Pandoc是否可用"""
        try:
            result = subprocess.run(
                [self.config["pandoc_path"], "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"✅ Pandoc检测成功: {version}")
                return True
        except Exception as e:
            logger.error(f"❌ Pandoc检测失败: {e}")
            return False

    def markdown_to_docx(
        self,
        markdown_content: str,
        output_filename: Optional[str] = None,
        reference_docx: Optional[str] = None,
    ) -> Optional[str]:
        """
        将Markdown内容转换为DOCX格式

        Args:
            markdown_content: Markdown格式的内容
            output_filename: 输出文件名(不含扩展名)
            reference_docx: 参考模板文档路径

        Returns:
            生成的DOCX文件路径,失败返回None
        """
        if not self._check_pandoc():
            logger.error("❌ Pandoc不可用,无法转换")
            return None

        # 生成输出文件名
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"athena_export_{timestamp}"

        output_path = Path(self.config["output_dir"]) / f"{output_filename}.docx"

        # 生成输入文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as md_file:
            md_file.write(markdown_content)
            md_file_path = md_file.name

        try:
            # 构建Pandoc命令
            cmd = [
                self.config["pandoc_path"],
                "-f",
                "markdown",  # 输入格式
                "-t",
                "docx",  # 输出格式
                "-o",
                str(output_path),  # 输出文件
                md_file_path,  # 输入文件
            ]

            # 添加参考文档(如果提供)
            ref_doc = reference_docx or self.config.get("reference_docx")
            if ref_doc and Path(ref_doc).exists():
                cmd.extend(["--reference-doc", ref_doc])

            # 执行转换
            logger.info("🔄 正在转换Markdown到DOCX...")
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, encoding="utf-8"
            )

            if result.returncode == 0:
                logger.info(f"✅ 转换成功: {output_path}")
                return str(output_path)
            else:
                logger.error(f"❌ 转换失败: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"❌ 转换过程出错: {e}")
            return None

        finally:
            # 清理临时文件
            if Path(md_file_path).exists():
                Path(md_file_path).unlink()

    def html_to_docx(
        self, html_content: str, output_filename: Optional[str] = None
    ) -> Optional[str]:
        """
        将HTML富文本转换为DOCX格式

        Args:
            html_content: HTML格式的内容
            output_filename: 输出文件名(不含扩展名)

        Returns:
            生成的DOCX文件路径,失败返回None
        """
        if not self._check_pandoc():
            return None

        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"athena_html_export_{timestamp}"

        output_path = Path(self.config["output_dir"]) / f"{output_filename}.docx"

        # 生成输入文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as html_file:
            html_file.write(html_content)
            html_file_path = html_file.name

        try:
            cmd = [
                self.config["pandoc_path"],
                "-f",
                "html",
                "-t",
                "docx",
                "-o",
                str(output_path),
                html_file_path,
            ]

            logger.info("🔄 正在转换HTML到DOCX...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                logger.info(f"✅ HTML转换成功: {output_path}")
                return str(output_path)
            else:
                logger.error(f"❌ HTML转换失败: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"❌ HTML转换出错: {e}")
            return None

        finally:
            if Path(html_file_path).exists():
                Path(html_file_path).unlink()

    def markdown_table_to_excel(
        self, markdown_table: str, output_filename: Optional[str] = None
    ) -> Optional[str]:
        """
        将Markdown表格转换为Excel格式

        Args:
            markdown_table: Markdown格式的表格
            output_filename: 输出文件名(不含扩展名)

        Returns:
            生成的Excel文件路径,失败返回None
        """
        try:
            pass
        except ImportError:
            logger.error("❌ 需要安装pandas和openpyxl: pip install pandas openpyxl")
            return None

        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"athena_table_{timestamp}"

        output_path = Path(self.config["output_dir"]) / f"{output_filename}.xlsx"

        try:
            # 解析Markdown表格
            lines = markdown_table.strip().split("\n")
            data = []
            for line in lines:
                if line.strip().startswith("|"):
                    # 移除首尾的|,然后分割
                    cells = [cell.strip() for cell in line.strip().split("|")]
                    # 过滤掉空单元格(表头分隔行等)
                    if cells and not all(c.startswith("---") for c in cells if c):
                        data.append([cell for cell in cells if True])

            if not data:
                logger.error("❌ 无法解析Markdown表格")
                return None

            # 第一行作为表头
            headers = data[0] if data else []
            rows = data[1:] if len(data) > 1 else []

            # 创建DataFrame
            df = pd.DataFrame(rows, columns=headers if len(headers) == len(rows[0]) else None)

            # 保存为Excel
            df.to_excel(output_path, index=False, engine="openpyxl")

            logger.info(f"✅ 表格导出成功: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"❌ 表格转换出错: {e}")
            return None

    def export_ai_conversation(
        self,
        conversation_content: str,
        content_type: str = "markdown",
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        导出AI对话内容到Word文档

        Args:
            conversation_content: 对话内容
            content_type: 内容类型 (markdown/html)
            output_filename: 输出文件名

        Returns:
            生成的文档路径
        """
        if content_type == "html":
            return self.html_to_docx(conversation_content, output_filename)
        else:
            return self.markdown_to_docx(conversation_content, output_filename)


class AthenaDocumentExporter:
    """Athena平台文档导出服务"""

    def __init__(self, config: dict | None = None):
        """
        初始化文档导出服务

        Args:
            config: PasteMD配置
        """
        self.pastemd = PasteMDCore(config)
        self.export_history = []

    def export_patent_report(
        self, patent_data: dict[str, Any], analysis_result: str, include_raw_data: bool = False
    ) -> Optional[str]:
        """
        导出专利分析报告

        Args:
            patent_data: 专利数据
            analysis_result: 分析结果(Markdown格式)
            include_raw_data: 是否包含原始数据

        Returns:
            导出的文档路径
        """
        # 构建完整的报告内容
        report_content = self._build_patent_report(patent_data, analysis_result, include_raw_data)

        # 生成文件名
        patent_id = patent_data.get("patent_id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"patent_analysis_{patent_id}_{timestamp}"

        # 导出
        doc_path = self.pastemd.markdown_to_docx(report_content, filename)

        if doc_path:
            self.export_history.append(
                {
                    "type": "patent_report",
                    "patent_id": patent_id,
                    "file_path": doc_path,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return doc_path

    def _build_patent_report(
        self, patent_data: dict[str, Any], analysis_result: str, include_raw_data: bool
    ) -> str:
        """构建专利分析报告内容"""
        report = []

        # 报告标题
        report.append("# 专利分析报告")
        report.append("")
        report.append(f"**专利号**: {patent_data.get('patent_id', 'N/A')}")
        report.append(f"**标题**: {patent_data.get('title', 'N/A')}")
        report.append(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("**分析人员**: 小娜·天秤女神")
        report.append("")

        # 分析结果
        report.append("## 分析结果")
        report.append("")
        report.append(analysis_result)
        report.append("")

        # 原始数据(可选)
        if include_raw_data:
            report.append("## 原始数据")
            report.append("")
            report.append("```json")
            report.append(json.dumps(patent_data, ensure_ascii=False, indent=2))
            report.append("```")
            report.append("")

        return "\n".join(report)

    def export_conversation_to_word(
        self,
        conversation_id: str,
        messages: list[dict[str, str]],
        output_filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        导出对话记录到Word文档

        Args:
            conversation_id: 对话ID
            messages: 消息列表
            output_filename: 输出文件名

        Returns:
            导出的文档路径
        """
        # 构建对话内容
        content = self._build_conversation_content(conversation_id, messages)

        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"conversation_{conversation_id}_{timestamp}"

        doc_path = self.pastemd.markdown_to_docx(content, output_filename)

        if doc_path:
            self.export_history.append(
                {
                    "type": "conversation",
                    "conversation_id": conversation_id,
                    "file_path": doc_path,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return doc_path

    def _build_conversation_content(
        self, conversation_id: str, messages: list[dict[str, str]]) -> str:
        """构建对话内容"""
        content = []
        content.append("# 对话记录")
        content.append("")
        content.append(f"**对话ID**: {conversation_id}")
        content.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")

        for msg in messages:
            role = msg.get("role", "unknown")
            text = msg.get("content", "")

            if role == "user":
                content.append("## 👤 用户")
            elif role == "assistant":
                content.append("## 🤖 AI助手")
            else:
                content.append(f"## {role}")

            content.append("")
            content.append(text)
            content.append("")
            content.append("---")
            content.append("")

        return "\n".join(content)

    def export_data_analysis_to_excel(
        self, data: list[dict] | dict, table_name: str = "数据分析结果"
    ) -> Optional[str]:
        """
        导出数据分析到Excel

        Args:
            data: 数据(字典列表或单个字典)
            table_name: 表格名称

        Returns:
            导出的Excel文件路径
        """
        try:
            pass
        except ImportError:
            logger.error("❌ 需要安装pandas: pip install pandas")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_analysis_{timestamp}"
        output_path = Path(self.pastemd.config["output_dir"]) / f"{filename}.xlsx"

        try:
            # 转换为DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                logger.error("❌ 不支持的数据格式")
                return None

            # 保存到Excel
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name=table_name, index=False)

            logger.info(f"✅ 数据导出成功: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"❌ 数据导出失败: {e}")
            return None

    def get_export_history(self) -> list[dict]:
        """获取导出历史"""
        return self.export_history


# 单例实例
_exporter_instance = None


def get_document_exporter(config: dict | None | None = None) -> AthenaDocumentExporter:
    """获取文档导出服务单例"""
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = AthenaDocumentExporter(config)
    return _exporter_instance


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PasteMD核心模块测试")
    print("=" * 60)

    # 创建核心实例
    core = PasteMDCore()

    # 测试Markdown转换
    test_markdown = """# 测试文档

这是一个测试文档,用于验证PasteMD核心功能。

## 功能列表

- 支持Markdown转DOCX
- 支持HTML转DOCX
- 支持表格导出Excel

## 代码示例

```python
def hello_world():
    print("Hello, PasteMD!")
```

## 数学公式

$E = mc^2$

## 表格

| 功能 | 状态 |
|------|------|
| Markdown转换 | ✅ |
| HTML转换 | ✅ |
| 表格导出 | ✅ |
"""

    print("\n🔄 测试Markdown转换...")
    result = core.markdown_to_docx(test_markdown, "test_output")
    if result:
        print(f"✅ 转换成功: {result}")
    else:
        print("❌ 转换失败")

    print("\n" + "=" * 60)
